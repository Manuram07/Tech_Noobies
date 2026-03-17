from flask import Blueprint, render_template, request, jsonify
from services import disease_service

diseases_bp = Blueprint('diseases', __name__, url_prefix='/diseases')


@diseases_bp.route('/')
def search():
    """Disease search and taxonomy browser."""
    q = request.args.get('q', '')
    category = request.args.get('category', '')

    results = []
    if q:
        results = disease_service.search_diseases(q)
    elif category:
        results = disease_service.get_diseases_by_category(category)

    categories = disease_service.get_root_categories()
    all_diseases = disease_service.get_all_diseases() if not q and not category else []

    return render_template('diseases/search.html',
        query=q,
        category=category,
        results=results,
        categories=categories,
        all_diseases=all_diseases,
    )


@diseases_bp.route('/<int:disease_id>')
def detail(disease_id):
    """Disease classification detail page."""
    hierarchy = disease_service.get_disease_hierarchy(disease_id)
    if not hierarchy:
        return render_template('diseases/detail.html', error='Disease not found'), 404

    disease = hierarchy['disease']
    return render_template('diseases/detail.html',
        disease=disease,
        ancestors=hierarchy['ancestors'],
        children=hierarchy['children'],
    )


# ── JSON API ────────────────────────────────────────────────────────────

@diseases_bp.route('/api/search')
def api_search():
    """JSON API for disease autocomplete/search."""
    q = request.args.get('q', '')
    results = disease_service.search_diseases(q, limit=10)
    return jsonify([d.to_dict_brief() for d in results])
