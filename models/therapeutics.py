from models.database import db
from datetime import datetime

class Therapeutic(db.Model):
    __tablename__ = "therapeutics"

    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), index=True)

    drug_name = db.Column(db.String(200), nullable=False)
    drug_class = db.Column(db.String(200))
    mechanism = db.Column(db.Text)

    target_gene = db.Column(db.String(100))
    approval_status = db.Column(db.String(50))

    source = db.Column(db.String(100))
    source_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "drug_name": self.drug_name,
            "drug_class": self.drug_class,
            "mechanism": self.mechanism,
            "target_gene": self.target_gene,
            "approval_status": self.approval_status
        }