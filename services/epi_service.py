import logging
from datetime import datetime, date
from models.database import db
from models.epidemiology import EpiRecord, OutbreakAlert
from models.disease import Disease
from config import Config
from services.utils import resilient_get, cached, safe_json, validate_positive_int, validate_country_name

logger = logging.getLogger(__name__)


# ── Disease.sh API (COVID-19 data) ──────────────────────────────────────

@cached(timeout=1800)
def fetch_disease_sh_historical(country, days=365):
    """Fetch historical COVID-19 data from Disease.sh with caching."""
    country = validate_country_name(country)
    if not country:
        return []

    url = f'{Config.DISEASE_SH_BASE}/historical/{country}?lastdays={days}'
    resp = resilient_get(url)
    data = safe_json(resp)
    if not data:
        return []

    timeline = data.get('timeline', {})
    cases_tl = timeline.get('cases', {})
    deaths_tl = timeline.get('deaths', {})
    recovered_tl = timeline.get('recovered', {})

    records = []
    for date_str, case_count in cases_tl.items():
        try:
            dt = datetime.strptime(date_str, '%m/%d/%y').date()
        except ValueError:
            continue
        records.append({
            'date': dt,
            'cases': validate_positive_int(case_count),
            'deaths': validate_positive_int(deaths_tl.get(date_str, 0)),
            'recovered': validate_positive_int(recovered_tl.get(date_str, 0)),
            'source': 'DISEASE_SH',
        })
    return records


@cached(timeout=3600)
def fetch_disease_sh_countries():
    """Fetch current COVID-19 stats for all countries (cached 1hr)."""
    url = f'{Config.DISEASE_SH_BASE}/countries?sort=cases'
    resp = resilient_get(url)
    data = safe_json(resp)
    return data if isinstance(data, list) else []


@cached(timeout=1800)
def fetch_disease_sh_country(country):
    """Fetch current COVID-19 stats for a specific country."""
    country = validate_country_name(country)
    url = f'{Config.DISEASE_SH_BASE}/countries/{country}'
    resp = resilient_get(url)
    data = safe_json(resp)
    return data if isinstance(data, dict) else {}


# ── WHO GHO OData API ───────────────────────────────────────────────────

@cached(timeout=7200)
def fetch_who_indicators():
    """Fetch list of available WHO GHO indicators (cached 2hrs)."""
    url = f'{Config.WHO_GHO_BASE}/Indicator'
    resp = resilient_get(url)
    data = safe_json(resp)
    if not data:
        return []
    return data.get('value', [])


@cached(timeout=3600)
def fetch_who_data(indicator_code, country_code=None):
    """Fetch data for a specific WHO indicator, optionally filtered by country."""
    url = f'{Config.WHO_GHO_BASE}/{indicator_code}'
    params = {}
    if country_code:
        params['$filter'] = f"SpatialDim eq '{country_code}'"
    resp = resilient_get(url, params=params)
    data = safe_json(resp)
    if not data:
        return []
    return data.get('value', [])


# ── WHO Disease-Specific Indicators ─────────────────────────────────────

WHO_DISEASE_INDICATORS = {
    'Tuberculosis': {
        'incidence': 'MDG_0000000020',
        'mortality': 'MDG_0000000021',
        'prevalence': 'TB_e_prev_num',
    },
    'Malaria': {
        'incidence': 'MALARIA_EST_INCIDENCE',
        'mortality': 'MALARIA_EST_DEATHS',
    },
    'HIV/AIDS': {
        'incidence': 'HIV_0000000026',
        'prevalence': 'HIV_0000000001',
    },
    'Cholera': {
        'cases': 'CHOLERA_0000000001',
        'deaths': 'CHOLERA_0000000002',
    },
    'Measles': {
        'cases': 'WHS3_41',
    },
}


@cached(timeout=3600)
def fetch_who_disease_data(disease_name, country_code=None):
    """Fetch WHO indicators for a specific disease."""
    indicators = WHO_DISEASE_INDICATORS.get(disease_name, {})
    result = {}
    for metric, indicator_code in indicators.items():
        data = fetch_who_data(indicator_code, country_code)
        if data:
            result[metric] = data
    return result


# ── Epidemiological Stats from Database ─────────────────────────────────

def get_epi_stats(disease_id, country=None, start_date=None, end_date=None):
    """Query epidemiological records from the database."""
    query = EpiRecord.query.filter_by(disease_id=disease_id)

    if country:
        country = validate_country_name(country)
        query = query.filter(EpiRecord.country.ilike(f'%{country}%'))
    if start_date:
        query = query.filter(EpiRecord.date >= start_date)
    if end_date:
        query = query.filter(EpiRecord.date <= end_date)

    records = query.order_by(EpiRecord.date).all()
    return records


def get_epi_summary(disease_id, country=None):
    """Get summary statistics for a disease with validation."""
    records = get_epi_stats(disease_id, country)
    if not records:
        return {
            'total_cases': 0,
            'total_deaths': 0,
            'total_recovered': 0,
            'mortality_rate': 0,
            'record_count': 0,
            'date_range': None,
            'data_sources': [],
        }

    total_cases = max((r.cases or 0) for r in records)
    total_deaths = max((r.deaths or 0) for r in records)
    total_recovered = max((r.recovered or 0) for r in records)
    sources = list(set(r.source for r in records if r.source))

    return {
        'total_cases': total_cases,
        'total_deaths': total_deaths,
        'total_recovered': total_recovered,
        'mortality_rate': round((total_deaths / total_cases * 100), 2) if total_cases > 0 else 0,
        'record_count': len(records),
        'date_range': {
            'start': records[0].date.isoformat(),
            'end': records[-1].date.isoformat(),
        } if records else None,
        'data_sources': sources,
    }


def get_outbreak_alerts(disease_id=None, country=None, limit=20):
    """Get recent outbreak alerts with optional filtering."""
    query = OutbreakAlert.query

    if disease_id:
        query = query.filter_by(disease_id=disease_id)
    if country:
        country = validate_country_name(country)
        query = query.filter(OutbreakAlert.country.ilike(f'%{country}%'))

    return query.order_by(OutbreakAlert.reported_date.desc()).limit(limit).all()


def detect_anomalies(records, threshold=2.0):
    """Z-score anomaly detection on case count changes.
    
    Returns anomalies where the daily change exceeds `threshold` standard deviations.
    """
    if len(records) < 10:
        return []

    cases = [r.cases or 0 for r in records]
    changes = [cases[i] - cases[i-1] for i in range(1, len(cases))]
    if not changes:
        return []

    mean_change = sum(changes) / len(changes)
    variance = sum((c - mean_change) ** 2 for c in changes) / len(changes)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return []

    anomalies = []
    for i, change in enumerate(changes):
        z_score = (change - mean_change) / std_dev
        if abs(z_score) > threshold:
            anomalies.append({
                'date': records[i + 1].date.isoformat(),
                'cases': records[i + 1].cases,
                'change': change,
                'z_score': round(z_score, 2),
                'type': 'spike' if z_score > 0 else 'drop',
            })

    return anomalies


def get_available_countries():
    """Get list of countries with epidemiological data."""
    countries = db.session.query(EpiRecord.country).distinct().order_by(EpiRecord.country).all()
    return [c[0] for c in countries if c[0]]


def get_disease_country_summary():
    """Get summary of available data by disease-country combinations."""
    results = db.session.query(
        EpiRecord.disease_id,
        EpiRecord.country,
        db.func.count(EpiRecord.id),
        db.func.max(EpiRecord.cases),
    ).group_by(EpiRecord.disease_id, EpiRecord.country).all()

    return [{
        'disease_id': r[0],
        'country': r[1],
        'record_count': r[2],
        'max_cases': r[3],
    } for r in results]
