from models.database import db
from datetime import datetime


class EpiRecord(db.Model):
    """Epidemiological surveillance record — time-series case data."""
    __tablename__ = 'epi_records'

    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False, index=True)
    country = db.Column(db.String(100), nullable=False, index=True)
    region = db.Column(db.String(100), nullable=True)
    date = db.Column(db.Date, nullable=False, index=True)
    cases = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    recovered = db.Column(db.Integer, default=0)
    prevalence = db.Column(db.Float, nullable=True)
    incidence = db.Column(db.Float, nullable=True)
    source = db.Column(db.String(50), nullable=False)  # CDC, WHO, DISEASE_SH, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_epi_disease_country_date', 'disease_id', 'country', 'date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'disease_id': self.disease_id,
            'country': self.country,
            'region': self.region,
            'date': self.date.isoformat() if self.date else None,
            'cases': self.cases,
            'deaths': self.deaths,
            'recovered': self.recovered,
            'prevalence': self.prevalence,
            'incidence': self.incidence,
            'source': self.source,
        }


class OutbreakAlert(db.Model):
    """Outbreak alert from surveillance feeds."""
    __tablename__ = 'outbreak_alerts'

    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    country = db.Column(db.String(100), index=True)
    region = db.Column(db.String(100))
    severity = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH, CRITICAL
    source = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    reported_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'disease_id': self.disease_id,
            'title': self.title,
            'description': self.description,
            'country': self.country,
            'region': self.region,
            'severity': self.severity,
            'source': self.source,
            'source_url': self.source_url,
            'reported_date': self.reported_date.isoformat() if self.reported_date else None,
        }

    @property
    def severity_color(self):
        return {
            'LOW': '#4ade80',
            'MEDIUM': '#fbbf24',
            'HIGH': '#f97316',
            'CRITICAL': '#ef4444',
        }.get(self.severity, '#94a3b8')
