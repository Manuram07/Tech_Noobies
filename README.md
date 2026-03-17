# 🧬 MEDFUSION — Disease Surveillance Intelligence Dashboard

> **Unified multi-source disease intelligence platform** integrating epidemiological surveillance, disease classification, genomic associations, and outbreak monitoring from WHO, CDC, Disease.sh, Open Targets, and NCBI.

Built for **Hackfest 2026**.

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone <your-repo-url>
cd MEDFUSION

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open in browser
# → http://127.0.0.1:5000
```

The database (`medfusion.db`) is automatically created and seeded with **35 diseases** and **8 outbreak alerts** on first run.

---

## 📋 Features

| Feature | Status | Description |
|---------|--------|-------------|
| **A. Disease Classification** | ✅ Active | ICD-10/11 ontology with hierarchical taxonomy, synonyms, subtypes, search |
| **B. Epidemiological Surveillance** | ✅ Active | Disease.sh + WHO GHO APIs, time-series charts, anomaly detection |
| **C. Genomic Associations** | ✅ Active | Open Targets GraphQL + NCBI E-utilities, evidence scoring |
| **D. Therapeutic Insights** | 🏗️ Designed | Architecture spec for PubChem + WHO Essential Medicines integration |
| **E. Visual Intelligence** | 🏗️ Designed | Architecture spec for heatmaps, timelines, network graphs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Jinja2)                 │
│    Dashboard │ Diseases │ Surveillance │ Genomics    │
├─────────────────────────────────────────────────────┤
│                  Flask Routes (API)                  │
│       main │ diseases │ surveillance │ genomics      │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│  disease_service │ epi_service │ genomics_service    │
│              data_ingestion │ utils                  │
├─────────────────────────────────────────────────────┤
│                    Data Sources                      │
│  Disease.sh │ WHO GHO │ Open Targets │ NCBI E-utils │
├─────────────────────────────────────────────────────┤
│               SQLite + SQLAlchemy                    │
│    Diseases │ EpiRecords │ Alerts │ GeneAssociations │
└─────────────────────────────────────────────────────┘
```

---

## 🔌 Data Sources

| Source | Type | Auth | Status |
|--------|------|------|--------|
| [Disease.sh](https://disease.sh/) | REST API | None | ✅ Integrated |
| [WHO GHO](https://ghoapi.azureedge.net/api/) | OData API | None | ✅ Integrated |
| [Open Targets](https://platform.opentargets.org/) | GraphQL | None | ✅ Integrated |
| [NCBI E-utilities](https://eutils.ncbi.nlm.nih.gov/) | REST API | API Key | ✅ Integrated |
| CDC SODA | REST API | App Token | 🔧 Planned |
| HealthMap | API | Key | 🔧 Planned |
| ProMED Mail | RSS | Scraping | 🔧 Planned |
| ECDC | CSV | Download | 🔧 Planned |

---

## 🗄️ Database Schema

- **Disease** — ICD-10 coded ontology with self-referential hierarchy
- **EpiRecord** — Time-series epidemiological data (cases, deaths, recovered)
- **OutbreakAlert** — Structured alerts with severity (LOW → CRITICAL)
- **GeneAssociation** — Gene-disease associations with evidence scores

---

## 🧪 Key Endpoints

| Route | Description |
|-------|-------------|
| `/` | Dashboard with unified search |
| `/query?disease=X&country=Y` | Multi-layer analysis (A+B+C combined) |
| `/diseases` | Disease taxonomy browser |
| `/diseases/<id>` | Disease classification detail |
| `/surveillance?disease=X&country=Y` | Epidemiology dashboard |
| `/surveillance/alerts` | Outbreak alert feed |
| `/genomics?disease=X` | Gene-disease associations |
| `/therapeutics` | Feature D architecture design |
| `/visual-intelligence` | Feature E architecture design |
| `/diseases/api/search?q=X` | JSON autocomplete API |

---

## ⚡ Technical Highlights

- **Resilient HTTP** — Automatic retry with exponential backoff for all API calls
- **In-Memory Caching** — TTL-based cache to avoid redundant API calls
- **Z-Score Anomaly Detection** — Statistical anomaly detection on case trends
- **NCBI Gene Enrichment** — Chromosome, location, and summary data from NCBI
- **Unified Query Engine** — Single search aggregates classification + epidemiology + genomics

---

## 📁 Project Structure

```
MEDFUSION/
├── app.py                 # Flask app factory + DB seeding
├── config.py              # API keys, DB config
├── models/                # SQLAlchemy models
├── services/              # Business logic + API integrations
├── routes/                # Flask blueprints
├── templates/             # Jinja2 HTML templates
├── static/                # CSS + JS
├── seed_data/             # ICD-10 ontology JSON
├── Procfile               # Render deployment
└── requirements.txt
```

---

## 🚢 Deployment (Render)

1. Push to GitHub
2. Create a new **Web Service** on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`
5. Add env vars for API keys if needed

---

## 👤 Team
project by **[Tech Noobies]**
Nookala Manuram Reddy
Vadla Pranav
Gummadi Nishanth Reddy
P. Shashi Preetham Reddy
Sai Krishna Yadav
    — Hackfest 2026

---

## 📜 License

MIT License — Built for educational and hackathon purposes.
