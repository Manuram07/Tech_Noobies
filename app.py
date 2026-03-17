import os
import json
import logging
from flask import Flask
from config import Config
from models.database import db
from models.therapeutics import Therapeutic
from models.disease import Disease
from models.database import db

def seed_therapeutics():

    if Therapeutic.query.count() > 0:
        return

    tb = Disease.query.filter(Disease.name.ilike("%Tuberculosis%")).first()

    drugs = [
        Therapeutic(
            disease_id=tb.id,
            drug_name="Rifampicin",
            drug_class="Antibiotic",
            mechanism="RNA polymerase inhibitor",
            target_gene="rpoB",
            approval_status="Approved"
        ),
        Therapeutic(
            disease_id=tb.id,
            drug_name="Isoniazid",
            drug_class="Antibiotic",
            mechanism="Mycolic acid synthesis inhibitor",
            target_gene="katG",
            approval_status="Approved"
        ),
        Therapeutic(
            disease_id=tb.id,
            drug_name="Ethambutol",
            drug_class="Antibiotic",
            mechanism="Cell wall synthesis inhibitor",
            target_gene="embB",
            approval_status="Approved"
        )
    ]

    db.session.add_all(drugs)
    db.session.commit()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def seed_diseases():
    """Seed the disease ontology from JSON file."""
    from models.disease import Disease

    if Disease.query.count() > 0:
        logger.info('Disease ontology already seeded.')
        return

    seed_path = os.path.join(os.path.dirname(__file__), 'seed_data', 'icd10_diseases.json')
    if not os.path.exists(seed_path):
        logger.warning(f'Seed file not found: {seed_path}')
        return

    with open(seed_path, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    count = 0
    for cat in categories:
        # Create parent category
        parent = Disease(
            name=cat['name'],
            icd_code=cat.get('icd_code', ''),
            category=cat.get('category', ''),
            description=cat.get('description', ''),
            synonyms=cat.get('synonyms', []),
            subtypes=cat.get('subtypes', []),
        )
        db.session.add(parent)
        db.session.flush()  # Get parent.id
        count += 1

        # Create children
        for child_data in cat.get('children', []):
            child = Disease(
                name=child_data['name'],
                icd_code=child_data.get('icd_code', ''),
                category=child_data.get('category', ''),
                parent_id=parent.id,
                description=child_data.get('description', ''),
                synonyms=child_data.get('synonyms', []),
                subtypes=child_data.get('subtypes', []),
            )
            db.session.add(child)
            count += 1

    db.session.commit()
    logger.info(f'Seeded {count} diseases into ontology.')


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        # Create tables
        db.create_all()

        # Seed data
        seed_diseases()

        # Seed outbreak alerts
        from services.data_ingestion import ingest_sample_outbreak_alerts
        ingest_sample_outbreak_alerts()

    # Register blueprints
    from routes.main import main_bp
    from routes.diseases import diseases_bp
    from routes.surveillance import surveillance_bp
    from routes.genomics import genomics_bp
    from routes.future import future_bp
    from routes.visual import visual_bp
    app.register_blueprint(visual_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(diseases_bp)
    app.register_blueprint(surveillance_bp)
    app.register_blueprint(genomics_bp)
    app.register_blueprint(future_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
