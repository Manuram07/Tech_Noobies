import requests
import logging

logger = logging.getLogger(__name__)

WHO_ESSENTIAL = {
    "Rifampicin",
    "Isoniazid",
    "Ethambutol",
    "Pyrazinamide",
    "Artemisinin",
    "Chloroquine",
    "Amoxicillin",
    "Metformin",
    "Insulin",
    "Paracetamol"
}


def get_therapeutics_for_disease(disease_name):

    if not disease_name:
        return []

    logger.info(f"Fetching therapeutics for {disease_name}")

    query = f"{disease_name} drug"

    search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/cids/JSON?name_type=word"

    try:

        response = requests.get(search_url, timeout=10)

        if response.status_code != 200:
            return fallback_data(disease_name)

        data = response.json()

        compound_ids = data.get("IdentifierList", {}).get("CID", [])

        if not compound_ids:
            return fallback_data(disease_name)

        top_cids = compound_ids[:5]

        cids_str = ",".join(map(str, top_cids))

    except Exception:
        return fallback_data(disease_name)

    drugs_list = []

    try:

        details_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids_str}/description/JSON"

        response = requests.get(details_url, timeout=10)

        if response.status_code != 200:
            return fallback_data(disease_name)

        descriptions = response.json().get("InformationList", {}).get("Information", [])

        for item in descriptions:

            cid = item.get("CID")
            name = item.get("Title", "Unknown Drug")

            description = item.get("Description", "")
            mechanism = description[:150] + "..." if description else "No mechanism available"

            who_status = "Yes" if name in WHO_ESSENTIAL else "No"

            source_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"

            drugs_list.append({
                "drug_name": name,
                "mechanism": mechanism,
                "approval_status": who_status,
                "source_url": source_url
            })

    except Exception:
        return fallback_data(disease_name)

    return drugs_list


def fallback_data(disease_name):

    disease = disease_name.lower()

    if disease == "tuberculosis":

        return [

            {
                "drug_name": "Rifampicin",
                "mechanism": "RNA polymerase inhibitor",
                "approval_status": "Yes",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/5381226"
            },

            {
                "drug_name": "Isoniazid",
                "mechanism": "Mycolic acid synthesis inhibitor",
                "approval_status": "Yes",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/3767"
            },

            {
                "drug_name": "Ethambutol",
                "mechanism": "Cell wall synthesis inhibitor",
                "approval_status": "Yes",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/3279"
            }

        ]

    if disease == "malaria":

        return [

            {
                "drug_name": "Chloroquine",
                "mechanism": "Inhibits parasite heme detoxification",
                "approval_status": "Yes",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/2719"
            },

            {
                "drug_name": "Artemisinin",
                "mechanism": "Produces free radicals damaging parasite",
                "approval_status": "Yes",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/68827"
            }

        ]

    return []