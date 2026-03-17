from flask import Blueprint, render_template, request, jsonify
from services import disease_service
from services import epi_service
from services import genomics_service

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page with unified search."""
    categories = disease_service.get_root_categories()
    alerts = epi_service.get_outbreak_alerts(limit=5)
    return render_template('index.html', categories=categories, alerts=alerts)


@main_bp.route('/query', methods=['GET', 'POST'])
def unified_query():
    """Unified query endpoint — aggregates results from A + B + C."""
    disease_name = request.args.get('disease') or request.form.get('disease', '')
    country = request.args.get('country') or request.form.get('country', '')

    if not disease_name:
        return render_template('query/results.html', error='Please enter a disease name.')

    # A. Disease Classification
    disease = disease_service.map_name_to_disease(disease_name)
    classification = None
    if disease:
        classification = disease_service.get_disease_hierarchy(disease.id)

    # B. Epidemiological Data
    epi_data = None
    epi_summary = None
    alerts = []
    if disease:
        epi_summary = epi_service.get_epi_summary(disease.id, country if country else None)
        epi_records = epi_service.get_epi_stats(disease.id, country if country else None)
        epi_data = [r.to_dict() for r in epi_records[-90:]]  # Last 90 records
        alerts = [a.to_dict() for a in epi_service.get_outbreak_alerts(disease.id, country if country else None)]

    # C. Genomic Associations
    genomic_data = []
    if disease:
        genomic_data = genomics_service.get_gene_associations(disease.id)
        genomic_data = genomics_service.rank_genes(genomic_data)

    return render_template('query/results.html',
        query_disease=disease_name,
        query_country=country,
        disease=disease,
        classification=classification,
        epi_summary=epi_summary,
        epi_data=epi_data,
        alerts=alerts,
        genomic_data=genomic_data[:15],
    )
