from flask import Blueprint, render_template, request, jsonify
from services import epi_service, disease_service
from services.data_ingestion import ingest_disease_sh_historical_country

surveillance_bp = Blueprint('surveillance', __name__, url_prefix='/surveillance')


@surveillance_bp.route('/')
def dashboard():
    """Epidemiology surveillance dashboard."""
    disease_name = request.args.get('disease', '')
    country = request.args.get('country', '')

    disease = None
    epi_data = []
    epi_summary = None
    anomalies = []
    countries = epi_service.get_available_countries()

    if disease_name:
        disease = disease_service.map_name_to_disease(disease_name)

    if disease and country:
        # Try to fetch fresh data if none exists
        records = epi_service.get_epi_stats(disease.id, country)
        if not records and disease.name.lower() in ['covid-19', 'coronavirus disease 2019']:
            ingest_disease_sh_historical_country(country, days=90)
            records = epi_service.get_epi_stats(disease.id, country)

        epi_data = [r.to_dict() for r in records[-180:]]
        epi_summary = epi_service.get_epi_summary(disease.id, country)
        anomalies = epi_service.detect_anomalies(records)
    elif disease:
        records = epi_service.get_epi_stats(disease.id)
        epi_data = [r.to_dict() for r in records[-180:]]
        epi_summary = epi_service.get_epi_summary(disease.id)

    all_diseases = disease_service.get_all_diseases()

    return render_template('surveillance/dashboard.html',
        disease=disease,
        disease_name=disease_name,
        country=country,
        countries=countries,
        epi_data=epi_data,
        epi_summary=epi_summary,
        anomalies=anomalies,
        all_diseases=all_diseases,
    )


@surveillance_bp.route('/alerts')
def alerts():
    """Outbreak alert feed."""
    disease_name = request.args.get('disease', '')
    country = request.args.get('country', '')

    disease = None
    if disease_name:
        disease = disease_service.map_name_to_disease(disease_name)

    alert_list = epi_service.get_outbreak_alerts(
        disease_id=disease.id if disease else None,
        country=country if country else None,
        limit=50,
    )

    return render_template('surveillance/alerts.html',
        alerts=alert_list,
        disease_name=disease_name,
        country=country,
    )


# ── JSON API ────────────────────────────────────────────────────────────

@surveillance_bp.route('/api/stats')
def api_stats():
    """JSON API for epidemiological stats."""
    disease_name = request.args.get('disease', '')
    country = request.args.get('country', '')
    
    disease = disease_service.map_name_to_disease(disease_name)
    if not disease:
        return jsonify({'error': 'Disease not found'}), 404

    records = epi_service.get_epi_stats(disease.id, country if country else None)
    summary = epi_service.get_epi_summary(disease.id, country if country else None)
    
    return jsonify({
        'summary': summary,
        'records': [r.to_dict() for r in records[-90:]],
        'anomalies': epi_service.detect_anomalies(records),
    })
