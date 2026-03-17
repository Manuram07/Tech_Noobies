import logging
from models.database import db
from models.genomics import GeneAssociation
from models.disease import Disease
from config import Config
from services.utils import resilient_post, resilient_get, cached, safe_json

logger = logging.getLogger(__name__)


# ── Open Targets GraphQL API ────────────────────────────────────────────

OPEN_TARGETS_SEARCH_QUERY = """
query SearchDisease($queryString: String!) {
  search(queryString: $queryString, entityNames: ["disease"], page: {size: 5, index: 0}) {
    hits {
      id
      name
      entity
    }
  }
}
"""

OPEN_TARGETS_ASSOCIATIONS_QUERY = """
query DiseaseAssociations($diseaseId: String!) {
  disease(efoId: $diseaseId) {
    id
    name
    associatedTargets(page: {size: 25, index: 0}) {
      rows {
        target {
          id
          approvedSymbol
          approvedName
        }
        score
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""


@cached(timeout=7200)
def search_open_targets_disease(disease_name):
    """Search Open Targets for a disease by name, returns disease ID (cached 2hrs)."""
    resp = resilient_post(
        Config.OPEN_TARGETS_BASE,
        json_data={
            'query': OPEN_TARGETS_SEARCH_QUERY,
            'variables': {'queryString': disease_name},
        },
    )
    data = safe_json(resp)
    if not data:
        return None
    hits = data.get('data', {}).get('search', {}).get('hits', [])
    disease_hits = [h for h in hits if h.get('entity') == 'disease']
    return disease_hits[0] if disease_hits else None


@cached(timeout=7200)
def fetch_open_targets_associations(disease_efo_id):
    """Fetch gene-disease associations from Open Targets (cached 2hrs)."""
    resp = resilient_post(
        Config.OPEN_TARGETS_BASE,
        json_data={
            'query': OPEN_TARGETS_ASSOCIATIONS_QUERY,
            'variables': {'diseaseId': disease_efo_id},
        },
    )
    data = safe_json(resp)
    if not data:
        return []

    disease_data = data.get('data', {}).get('disease', {})
    if not disease_data:
        return []

    rows = disease_data.get('associatedTargets', {}).get('rows', [])
    associations = []
    for row in rows:
        target = row.get('target', {})
        associations.append({
            'gene_symbol': target.get('approvedSymbol', ''),
            'gene_name': target.get('approvedName', ''),
            'evidence_score': round(row.get('score', 0), 4),
            'association_type': 'overall',
            'source': 'OpenTargets',
            'source_url': f'https://platform.opentargets.org/target/{target.get("id", "")}',
        })
    return associations


# ── NCBI E-utilities Integration ────────────────────────────────────────

@cached(timeout=7200)
def fetch_ncbi_gene_info(gene_symbol):
    """Fetch gene summary from NCBI E-utilities using the provided API key."""
    api_key = Config.API_KEYS.get('NCBI_API_KEY', '')
    if not api_key:
        return None

    # Step 1: Search for the gene
    search_url = f'{Config.NCBI_EUTILS_BASE}/esearch.fcgi'
    params = {
        'db': 'gene',
        'term': f'{gene_symbol}[Gene Name] AND Homo sapiens[Organism]',
        'retmode': 'json',
        'retmax': 1,
        'api_key': api_key,
    }
    resp = resilient_get(search_url, params=params)
    data = safe_json(resp)
    if not data:
        return None

    id_list = data.get('esearchresult', {}).get('idlist', [])
    if not id_list:
        return None

    gene_id = id_list[0]

    # Step 2: Fetch gene summary
    summary_url = f'{Config.NCBI_EUTILS_BASE}/esummary.fcgi'
    params = {
        'db': 'gene',
        'id': gene_id,
        'retmode': 'json',
        'api_key': api_key,
    }
    resp = resilient_get(summary_url, params=params)
    data = safe_json(resp)
    if not data:
        return None

    result = data.get('result', {})
    gene_data = result.get(gene_id, {})

    if gene_data:
        return {
            'ncbi_gene_id': gene_id,
            'symbol': gene_data.get('name', gene_symbol),
            'full_name': gene_data.get('description', ''),
            'chromosome': gene_data.get('chromosome', ''),
            'location': gene_data.get('maplocation', ''),
            'summary': gene_data.get('summary', ''),
            'ncbi_url': f'https://www.ncbi.nlm.nih.gov/gene/{gene_id}',
        }
    return None


@cached(timeout=7200)
def fetch_ncbi_disease_genes(disease_name):
    """Search NCBI for genes associated with a disease."""
    api_key = Config.API_KEYS.get('NCBI_API_KEY', '')
    if not api_key:
        return []

    search_url = f'{Config.NCBI_EUTILS_BASE}/esearch.fcgi'
    params = {
        'db': 'gene',
        'term': f'{disease_name}[All Fields] AND Homo sapiens[Organism]',
        'retmode': 'json',
        'retmax': 15,
        'api_key': api_key,
    }
    resp = resilient_get(search_url, params=params)
    data = safe_json(resp)
    if not data:
        return []

    id_list = data.get('esearchresult', {}).get('idlist', [])
    if not id_list:
        return []

    # Fetch summaries for all genes
    summary_url = f'{Config.NCBI_EUTILS_BASE}/esummary.fcgi'
    params = {
        'db': 'gene',
        'id': ','.join(id_list),
        'retmode': 'json',
        'api_key': api_key,
    }
    resp = resilient_get(summary_url, params=params)
    data = safe_json(resp)
    if not data:
        return []

    result = data.get('result', {})
    genes = []
    for gene_id in id_list:
        gene_data = result.get(gene_id, {})
        if gene_data and isinstance(gene_data, dict):
            genes.append({
                'gene_symbol': gene_data.get('name', ''),
                'gene_name': gene_data.get('description', ''),
                'chromosome': gene_data.get('chromosome', ''),
                'location': gene_data.get('maplocation', ''),
                'ncbi_gene_id': gene_id,
                'source': 'NCBI',
                'source_url': f'https://www.ncbi.nlm.nih.gov/gene/{gene_id}',
            })
    return genes


# ── Combined Gene Associations ──────────────────────────────────────────

def get_gene_associations(disease_id, from_db=True, from_api=True):
    """Get gene associations combining DB cache, Open Targets, and NCBI data."""
    results = []
    seen_genes = set()

    # From database (cached results)
    if from_db:
        db_records = GeneAssociation.query.filter_by(disease_id=disease_id)\
            .order_by(GeneAssociation.evidence_score.desc()).all()
        for r in db_records:
            results.append(r.to_dict())
            seen_genes.add(r.gene_symbol.upper())

    # From Open Targets API (if no DB records)
    if from_api and not results:
        disease = Disease.query.get(disease_id)
        if disease:
            ot_disease = search_open_targets_disease(disease.name)
            if ot_disease:
                api_results = fetch_open_targets_associations(ot_disease['id'])

                # Enrich with NCBI data and store in DB
                for assoc in api_results:
                    gene_key = assoc['gene_symbol'].upper()
                    if gene_key in seen_genes:
                        continue
                    seen_genes.add(gene_key)

                    # Enrich with NCBI info
                    ncbi_info = fetch_ncbi_gene_info(assoc['gene_symbol'])
                    if ncbi_info:
                        assoc['chromosome'] = ncbi_info.get('chromosome', '')
                        assoc['location'] = ncbi_info.get('location', '')
                        assoc['ncbi_url'] = ncbi_info.get('ncbi_url', '')
                        if ncbi_info.get('full_name'):
                            assoc['gene_name'] = ncbi_info['full_name']

                    # Store in DB for caching
                    existing = GeneAssociation.query.filter_by(
                        disease_id=disease_id,
                        gene_symbol=assoc['gene_symbol']
                    ).first()
                    if not existing:
                        new_assoc = GeneAssociation(
                            disease_id=disease_id,
                            gene_symbol=assoc['gene_symbol'],
                            gene_name=assoc['gene_name'],
                            evidence_score=assoc['evidence_score'],
                            association_type=assoc['association_type'],
                            source=assoc['source'],
                            source_url=assoc['source_url'],
                        )
                        db.session.add(new_assoc)

                    results.append(assoc)

                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f'Failed to cache gene associations: {e}')

    # Sort by evidence score descending
    results.sort(key=lambda x: x.get('evidence_score', 0), reverse=True)
    return results


def rank_genes(associations):
    """Rank and annotate gene associations by evidence strength."""
    for assoc in associations:
        score = assoc.get('evidence_score', 0)
        if score >= 0.8:
            assoc['strength'] = 'Strong'
            assoc['strength_color'] = '#22c55e'
        elif score >= 0.5:
            assoc['strength'] = 'Moderate'
            assoc['strength_color'] = '#eab308'
        elif score >= 0.2:
            assoc['strength'] = 'Weak'
            assoc['strength_color'] = '#f97316'
        else:
            assoc['strength'] = 'Minimal'
            assoc['strength_color'] = '#ef4444'
    return associations
