from flask import Blueprint, render_template, request
from services import therapeutics_service

future_bp = Blueprint("future", __name__)


def get_mock_trend_data(disease):

    if disease.lower() == "malaria":
        return {
            "labels": ["Jan","Feb","Mar","Apr","May","Jun"],
            "values": [1200,1500,1900,1750,2100,2500]
        }

    elif disease.lower() == "tuberculosis":
        return {
            "labels": ["Jan","Feb","Mar","Apr","May","Jun"],
            "values": [800,900,1100,1050,1300,1500]
        }

    return {
        "labels": ["Jan","Feb","Mar","Apr","May","Jun"],
        "values": [500,600,800,750,900,1100]
    }



def get_mock_map_data(disease):

    if disease.lower() == "malaria":

        return [
            {"name":"Nigeria","lat":9.08,"lng":8.67,"cases":50000},
            {"name":"DR Congo","lat":-4.03,"lng":21.75,"cases":35000},
            {"name":"India","lat":20.59,"lng":78.96,"cases":15000}
        ]

    return [
        {"name":"Brazil","lat":-14.23,"lng":-51.92,"cases":20000},
        {"name":"USA","lat":37.09,"lng":-95.71,"cases":18000},
        {"name":"Mexico","lat":23.63,"lng":-102.55,"cases":12000}
    ]


@future_bp.route("/visual-intelligence")
def visual_intelligence():

    disease = request.args.get("disease")

    therapeutics = []
    trend_data = None
    map_data = None
    network = None

    if disease:

        therapeutics = therapeutics_service.get_therapeutics_for_disease(disease)

        trend_data = get_mock_trend_data(disease)

        map_data = get_mock_map_data(disease)

        network = {
            "nodes":[
                {"id":disease},
                {"id":"Artemisinin"},
                {"id":"Chloroquine"},
                {"id":"PfCRT"},
                {"id":"Kelch13"}
            ],
            "links":[
                {"source":disease,"target":"Artemisinin"},
                {"source":disease,"target":"Chloroquine"},
                {"source":"Artemisinin","target":"Kelch13"},
                {"source":"Chloroquine","target":"PfCRT"}
            ]
        }

    return render_template(
        "future/visual.html",
        disease=disease,
        therapeutics=therapeutics,
        trend_data=trend_data,
        map_data=map_data,
        network=network
    )
@future_bp.route("/therapeutics")
def therapeutics():

    disease_name = request.args.get("disease")

    drugs = []

    if disease_name:
        drugs = therapeutics_service.get_therapeutics_for_disease(disease_name)

    return render_template(
        "future/therapeutics.html",
        drugs=drugs
    )