from flask import Blueprint, render_template, request

visual_bp = Blueprint("visual", __name__)


@visual_bp.route("/visual")
def visual_dashboard():

    disease = request.args.get("disease", "Malaria")

    # Mock outbreak timeline data
    timeline = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "values": [1200, 1500, 1700, 1600, 2100, 2500]
    }

    # Mock geographic outbreak data
    map_data = [
        {"name": "India", "lat": 20.59, "lng": 78.96, "cases": 15000},
        {"name": "Brazil", "lat": -14.23, "lng": -51.92, "cases": 12000},
        {"name": "Nigeria", "lat": 9.08, "lng": 8.67, "cases": 20000}
    ]

    # Gene-drug-disease network data
    network = {
        "nodes": [
            {"id": "Malaria", "group": "disease"},
            {"id": "Artemisinin", "group": "drug"},
            {"id": "Chloroquine", "group": "drug"},
            {"id": "PfCRT", "group": "gene"},
            {"id": "Kelch13", "group": "gene"}
        ],
        "links": [
            {"source": "Malaria", "target": "Artemisinin"},
            {"source": "Malaria", "target": "Chloroquine"},
            {"source": "Artemisinin", "target": "Kelch13"},
            {"source": "Chloroquine", "target": "PfCRT"}
        ]
    }

    return render_template(
        "visual/dashboard.html",
        disease=disease,
        timeline=timeline,
        map_data=map_data,
        network=network
    )