from models.database import db
from models.disease import Disease
from sqlalchemy import or_


def search_diseases(query, limit=20):
    """Fuzzy search diseases by name, ICD code, category, or synonym."""
    if not query or len(query.strip()) < 2:
        return []

    q = f'%{query.strip().lower()}%'

    # Primary search: name, ICD code, category
    results = Disease.query.filter(
        or_(
            Disease.name.ilike(q),
            Disease.icd_code.ilike(q),
            Disease.category.ilike(q),
        )
    ).order_by(Disease.name).limit(limit).all()

    # Secondary search: synonyms (JSON field)
    if len(results) < limit:
        existing_ids = {d.id for d in results}
        all_diseases = Disease.query.all()
        for d in all_diseases:
            if d.id in existing_ids:
                continue
            if d.synonyms:
                for syn in d.synonyms:
                    if query.strip().lower() in syn.lower():
                        results.append(d)
                        existing_ids.add(d.id)
                        break
            if len(results) >= limit:
                break

    return results


def get_disease_by_id(disease_id):
    """Get full disease detail by ID."""
    return Disease.query.get(disease_id)


def get_disease_hierarchy(disease_id):
    """Get disease with its ancestor chain and children."""
    disease = Disease.query.get(disease_id)
    if not disease:
        return None

    return {
        'disease': disease.to_dict(),
        'ancestors': disease.get_ancestors(),
        'children': [c.to_dict_brief() for c in disease.children],
    }


def get_root_categories():
    """Get top-level disease categories (no parent)."""
    return Disease.query.filter_by(parent_id=None).order_by(Disease.name).all()


def get_diseases_by_category(category):
    """Get all diseases in a category."""
    return Disease.query.filter(Disease.category.ilike(f'%{category}%')).order_by(Disease.name).all()


def get_category_counts():
    """Get disease count per category."""
    results = db.session.query(
        Disease.category,
        db.func.count(Disease.id)
    ).filter(Disease.parent_id.isnot(None))\
     .group_by(Disease.category)\
     .order_by(Disease.category).all()
    return {cat: count for cat, count in results}


def map_name_to_disease(name):
    """Try to match a raw disease name to our ontology (exact → synonym → partial)."""
    if not name:
        return None

    cleaned = name.strip()

    # 1. Exact match (case-insensitive)
    disease = Disease.query.filter(Disease.name.ilike(cleaned)).first()
    if disease:
        return disease

    # 2. Synonym match
    all_diseases = Disease.query.all()
    for d in all_diseases:
        if d.synonyms:
            for syn in d.synonyms:
                if syn.lower() == cleaned.lower():
                    return d

    # 3. Partial match
    disease = Disease.query.filter(Disease.name.ilike(f'%{cleaned}%')).first()
    return disease


def get_all_diseases():
    """Get all diseases ordered by category then name."""
    return Disease.query.order_by(Disease.category, Disease.name).all()


def get_disease_stats():
    """Get overall ontology statistics."""
    total = Disease.query.count()
    categories = Disease.query.filter_by(parent_id=None).count()
    with_icd = Disease.query.filter(Disease.icd_code.isnot(None), Disease.icd_code != '').count()
    return {
        'total_diseases': total,
        'categories': categories,
        'with_icd_codes': with_icd,
    }
