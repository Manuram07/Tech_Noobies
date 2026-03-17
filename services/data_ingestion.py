import logging
from datetime import datetime, date
from models.database import db
from models.disease import Disease
from models.epidemiology import EpiRecord, OutbreakAlert
from services.epi_service import fetch_disease_sh_countries
from services.utils import validate_positive_int

logger = logging.getLogger(__name__)


def ingest_disease_sh_global():
    """Ingest current COVID-19 data from Disease.sh for all countries."""
    logger.info('Ingesting Disease.sh global data...')
    countries_data = fetch_disease_sh_countries()

    covid = Disease.query.filter(Disease.name.ilike('%COVID-19%')).first()
    if not covid:
        logger.warning('COVID-19 not found in disease ontology. Skipping ingestion.')
        return 0

    count = 0
    for c in countries_data:
        country_name = c.get('country', '')
        if not country_name:
            continue

        today = date.today()
        existing = EpiRecord.query.filter_by(
            disease_id=covid.id,
            country=country_name,
            date=today,
            source='DISEASE_SH'
        ).first()

        cases = validate_positive_int(c.get('cases', 0))
        deaths = validate_positive_int(c.get('deaths', 0))
        recovered = validate_positive_int(c.get('recovered', 0))

        if existing:
            existing.cases = cases
            existing.deaths = deaths
            existing.recovered = recovered
        else:
            record = EpiRecord(
                disease_id=covid.id,
                country=country_name,
                date=today,
                cases=cases,
                deaths=deaths,
                recovered=recovered,
                source='DISEASE_SH',
            )
            db.session.add(record)
        count += 1

    try:
        db.session.commit()
        logger.info(f'Ingested {count} country records from Disease.sh')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Disease.sh ingestion commit failed: {e}')
        count = 0

    return count


def ingest_disease_sh_historical_country(country, days=90):
    """Ingest historical COVID-19 data for a specific country."""
    from services.epi_service import fetch_disease_sh_historical

    covid = Disease.query.filter(Disease.name.ilike('%COVID-19%')).first()
    if not covid:
        return 0

    records = fetch_disease_sh_historical(country, days)
    count = 0
    for r in records:
        existing = EpiRecord.query.filter_by(
            disease_id=covid.id,
            country=country,
            date=r['date'],
            source='DISEASE_SH'
        ).first()

        if not existing:
            new_record = EpiRecord(
                disease_id=covid.id,
                country=country,
                date=r['date'],
                cases=r['cases'],
                deaths=r['deaths'],
                recovered=r['recovered'],
                source='DISEASE_SH',
            )
            db.session.add(new_record)
            count += 1

    try:
        db.session.commit()
        logger.info(f'Ingested {count} historical records for {country}')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Historical ingestion error: {e}')
        count = 0

    return count


def ingest_sample_outbreak_alerts():
    """Seed sample outbreak alerts for demonstration."""
    alerts_data = [
        {
            'title': 'COVID-19 Surge in Southeast Asia',
            'description': 'Multiple countries in Southeast Asia reporting increased COVID-19 cases with new variant concerns. Health authorities are monitoring for potential new waves.',
            'country': 'Thailand',
            'region': 'Southeast Asia',
            'severity': 'HIGH',
            'source': 'WHO',
            'source_url': 'https://www.who.int/emergencies/diseases/novel-coronavirus-2019',
            'reported_date': date(2024, 12, 15),
            'disease_name': 'COVID-19',
        },
        {
            'title': 'Dengue Outbreak — Brazil Records Over 5 Million Cases',
            'description': 'Brazil reports record dengue cases in 2024, with over 5 million confirmed cases across multiple states. Emergency measures have been declared in several municipalities.',
            'country': 'Brazil',
            'region': 'South America',
            'severity': 'CRITICAL',
            'source': 'PAHO',
            'source_url': 'https://www.paho.org',
            'reported_date': date(2024, 11, 20),
            'disease_name': 'Dengue Fever',
        },
        {
            'title': 'Cholera Resurgence in Sub-Saharan Africa',
            'description': 'Several African nations battling cholera outbreaks linked to flooding and inadequate water infrastructure. WHO has deployed rapid response teams.',
            'country': 'Mozambique',
            'region': 'Sub-Saharan Africa',
            'severity': 'HIGH',
            'source': 'CDC',
            'source_url': 'https://www.cdc.gov/cholera/',
            'reported_date': date(2024, 10, 5),
            'disease_name': 'Cholera',
        },
        {
            'title': 'Influenza Season Alert — Northern Hemisphere',
            'description': 'Early start to influenza season in the Northern Hemisphere with H3N2 dominant strain. Vaccination campaigns underway across North America and Europe.',
            'country': 'United States',
            'region': 'North America',
            'severity': 'MEDIUM',
            'source': 'CDC FluView',
            'source_url': 'https://www.cdc.gov/flu/weekly/',
            'reported_date': date(2024, 11, 1),
            'disease_name': 'Influenza',
        },
        {
            'title': 'Malaria Vaccine Rollout Shows Promising Results',
            'description': 'WHO reports significant reduction in malaria cases in regions where the RTS,S vaccine has been deployed. Kenya and Ghana show 30% reduction in hospitalizations.',
            'country': 'Kenya',
            'region': 'East Africa',
            'severity': 'LOW',
            'source': 'WHO',
            'source_url': 'https://www.who.int/news-room/fact-sheets/detail/malaria',
            'reported_date': date(2024, 9, 15),
            'disease_name': 'Malaria',
        },
        {
            'title': 'Multi-Drug Resistant Tuberculosis Alert — South Asia',
            'description': 'Rising MDR-TB cases reported across South Asia, particularly in India. WHO recommends enhanced surveillance and updated treatment protocols.',
            'country': 'India',
            'region': 'South Asia',
            'severity': 'HIGH',
            'source': 'WHO',
            'source_url': 'https://www.who.int/teams/global-tuberculosis-programme',
            'reported_date': date(2024, 8, 22),
            'disease_name': 'Tuberculosis',
        },
        {
            'title': 'Measles Outbreak in Europe — Vaccination Gaps Identified',
            'description': 'Rising measles cases across Eastern Europe linked to pandemic-era vaccination disruptions. ECDC calls for catch-up vaccination campaigns.',
            'country': 'Romania',
            'region': 'Europe',
            'severity': 'MEDIUM',
            'source': 'ECDC',
            'source_url': 'https://www.ecdc.europa.eu',
            'reported_date': date(2024, 7, 10),
            'disease_name': 'Measles',
        },
        {
            'title': 'Hepatitis B Screening Campaign — Western Pacific',
            'description': 'WHO Western Pacific region launches enhanced Hepatitis B screening program targeting high-prevalence populations.',
            'country': 'Philippines',
            'region': 'Western Pacific',
            'severity': 'LOW',
            'source': 'WHO',
            'source_url': 'https://www.who.int/westernpacific',
            'reported_date': date(2024, 6, 5),
            'disease_name': 'Hepatitis B',
        },
    ]

    count = 0
    for alert_info in alerts_data:
        disease = Disease.query.filter(Disease.name.ilike(f'%{alert_info["disease_name"]}%')).first()
        existing = OutbreakAlert.query.filter_by(title=alert_info['title']).first()
        if not existing:
            alert = OutbreakAlert(
                disease_id=disease.id if disease else None,
                title=alert_info['title'],
                description=alert_info['description'],
                country=alert_info['country'],
                region=alert_info['region'],
                severity=alert_info['severity'],
                source=alert_info['source'],
                source_url=alert_info['source_url'],
                reported_date=alert_info['reported_date'],
            )
            db.session.add(alert)
            count += 1

    try:
        db.session.commit()
        logger.info(f'Seeded {count} outbreak alerts')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert seeding error: {e}')

    return count


def ingest_all():
    """Run all data ingestion pipelines."""
    results = {
        'disease_sh_global': ingest_disease_sh_global(),
        'outbreak_alerts': ingest_sample_outbreak_alerts(),
    }
    return results
