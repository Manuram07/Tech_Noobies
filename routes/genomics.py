from flask import Blueprint, render_template, request, jsonify
from services import genomics_service, disease_service

genomics_bp = Blueprint('genomics', __name__, url_prefix='/genomics')


@genomics_bp.route('/')
def associations():
    """Gene-disease association explorer."""
    disease_name = request.args.get('disease', '')
    disease = None
    gene_data = []

    if disease_name:
        disease = disease_service.map_name_to_disease(disease_name)
        if disease:
            gene_data = genomics_service.get_gene_associations(disease.id)
            gene_data = genomics_service.rank_genes(gene_data)

    all_diseases = disease_service.get_all_diseases()

    return render_template('genomics/associations.html',
        disease=disease,
        disease_name=disease_name,
        gene_data=gene_data[:25],
        all_diseases=all_diseases,
    )


# ── JSON API ────────────────────────────────────────────────────────────

@genomics_bp.route('/api/associations')
def api_associations():
    """JSON API for gene-disease associations."""
    disease_name = request.args.get('disease', '')

    disease = disease_service.map_name_to_disease(disease_name)
    if not disease:
        return jsonify({'error': 'Disease not found'}), 404

    gene_data = genomics_service.get_gene_associations(disease.id)
    gene_data = genomics_service.rank_genes(gene_data)

    return jsonify({
        'disease': disease.to_dict_brief(),
        'associations': gene_data[:25],
    })
