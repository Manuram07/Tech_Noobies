from models.database import db
from datetime import datetime


class Disease(db.Model):
    """Disease ontology model based on ICD-10/ICD-11 taxonomy."""
    __tablename__ = 'diseases'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    icd_code = db.Column(db.String(20), index=True)
    category = db.Column(db.String(100), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=True)
    description = db.Column(db.Text)
    synonyms = db.Column(db.JSON, default=list)        # ["Flu", "Seasonal Influenza"]
    subtypes = db.Column(db.JSON, default=list)         # ["H1N1", "H3N2"]
    ontology_refs = db.Column(db.JSON, default=dict)    # {"SNOMED": "...", "MeSH": "..."}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    therapeutics = db.relationship('Therapeutic',backref='disease',lazy='dynamic')
    # Self-referential relationship for hierarchy
    parent = db.relationship('Disease', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    # Relationships
    epi_records = db.relationship('EpiRecord', backref='disease', lazy='dynamic')
    outbreak_alerts = db.relationship('OutbreakAlert', backref='disease', lazy='dynamic')
    gene_associations = db.relationship('GeneAssociation', backref='disease', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icd_code': self.icd_code,
            'category': self.category,
            'parent_id': self.parent_id,
            'description': self.description,
            'synonyms': self.synonyms or [],
            'subtypes': self.subtypes or [],
            'ontology_refs': self.ontology_refs or {},
            'children': [c.to_dict_brief() for c in self.children],
        }

    def to_dict_brief(self):
        return {
            'id': self.id,
            'name': self.name,
            'icd_code': self.icd_code,
            'category': self.category,
        }

    def get_ancestors(self):
        """Return the ancestor chain up to root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current.to_dict_brief())
            current = current.parent
        ancestors.reverse()
        return ancestors

    def __repr__(self):
        return f'<Disease {self.name} ({self.icd_code})>'
