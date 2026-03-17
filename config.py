import os

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'medfusion-dev-secret-key-change-in-production')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "medfusion.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── API Keys ─────────────────────────────────────────────────────────
    # Fill in your keys or set as environment variables
    API_KEYS = {
        'CDC_APP_TOKEN': os.environ.get('CDC_APP_TOKEN', ''),
        'HEALTHMAP_KEY': os.environ.get('HEALTHMAP_KEY', ''),
        'NCBI_API_KEY': os.environ.get('NCBI_API_KEY', '729757e574a97ceb455f2a2e27ac06249608'),
    }

    # ── External API Base URLs ───────────────────────────────────────────
    DISEASE_SH_BASE = 'https://disease.sh/v3/covid-19'
    WHO_GHO_BASE = 'https://ghoapi.azureedge.net/api'
    CDC_BASE = 'https://data.cdc.gov/resource'
    OPEN_TARGETS_BASE = 'https://api.platform.opentargets.org/api/v4/graphql'
    NCBI_EUTILS_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'

    # ── Data Ingestion Settings ──────────────────────────────────────────
    CACHE_TIMEOUT = 3600       # 1 hour cache for API responses
    REQUEST_TIMEOUT = 30       # seconds per request
    MAX_RETRIES = 3            # retry failed API calls
    RETRY_DELAY = 1            # seconds between retries
