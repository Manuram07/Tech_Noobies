from models.database import db
from datetime import datetime


class GeneAssociation(db.Model):
    """Gene-disease association from genomic databases."""
    __tablename__ = 'gene_associations'

    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=False, index=True)
    gene_symbol = db.Column(db.String(50), nullable=False, index=True)
    gene_name = db.Column(db.String(200))
    evidence_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    association_type = db.Column(db.String(100))  # e.g., "genetic_association", "somatic_mutation"
    source = db.Column(db.String(100), default='OpenTargets')
    source_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_gene_disease', 'disease_id', 'gene_symbol'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'disease_id': self.disease_id,
            'gene_symbol': self.gene_symbol,
            'gene_name': self.gene_name,
            'evidence_score': self.evidence_score,
            'association_type': self.association_type,
            'source': self.source,
            'source_url': self.source_url,
        }

    @property
    def strength_label(self):
        if self.evidence_score >= 0.8:
            return 'Strong'
        elif self.evidence_score >= 0.5:
            return 'Moderate'
        elif self.evidence_score >= 0.2:
            return 'Weak'
        return 'Minimal'

    @property
    def strength_color(self):
        if self.evidence_score >= 0.8:
            return '#22c55e'
        elif self.evidence_score >= 0.5:
            return '#eab308'
        elif self.evidence_score >= 0.2:
            return '#f97316'
        return '#ef4444'
