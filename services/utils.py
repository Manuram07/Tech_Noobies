"""Shared utilities: HTTP client with retry logic, caching, and rate limiting."""

import time
import logging
import requests
from functools import wraps
from config import Config

logger = logging.getLogger(__name__)

# ── In-Memory Cache ──────────────────────────────────────────────────────
_cache = {}
_cache_timestamps = {}


def cached(timeout=None):
    """Simple in-memory cache decorator with TTL."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ttl = timeout or Config.CACHE_TIMEOUT
            key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Check cache
            if key in _cache and key in _cache_timestamps:
                elapsed = time.time() - _cache_timestamps[key]
                if elapsed < ttl:
                    logger.debug(f'Cache HIT: {func.__name__}')
                    return _cache[key]

            # Cache miss — call function
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_timestamps[key] = time.time()
            logger.debug(f'Cache MISS: {func.__name__}')
            return result
        return wrapper
    return decorator


def clear_cache():
    """Clear the entire in-memory cache."""
    _cache.clear()
    _cache_timestamps.clear()
    logger.info('Cache cleared.')


# ── HTTP Client with Retry ──────────────────────────────────────────────

def resilient_get(url, params=None, headers=None, timeout=None, max_retries=None):
    """HTTP GET with automatic retry, timeout, and error handling."""
    _timeout = timeout or Config.REQUEST_TIMEOUT
    _retries = max_retries or Config.MAX_RETRIES

    for attempt in range(1, _retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=_timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            logger.warning(f'Timeout on attempt {attempt}/{_retries}: {url}')
        except requests.exceptions.ConnectionError:
            logger.warning(f'Connection error on attempt {attempt}/{_retries}: {url}')
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 'unknown'
            logger.warning(f'HTTP {status} on attempt {attempt}/{_retries}: {url}')
            if status == 429:  # Rate limited
                time.sleep(Config.RETRY_DELAY * attempt * 2)
                continue
            if 400 <= (status if isinstance(status, int) else 500) < 500:
                break  # Don't retry client errors
        except Exception as e:
            logger.error(f'Unexpected error on attempt {attempt}/{_retries}: {url} — {e}')

        if attempt < _retries:
            time.sleep(Config.RETRY_DELAY * attempt)

    logger.error(f'All {_retries} attempts failed for: {url}')
    return None


def resilient_post(url, json_data=None, headers=None, timeout=None, max_retries=None):
    """HTTP POST with automatic retry, timeout, and error handling."""
    _timeout = timeout or Config.REQUEST_TIMEOUT
    _retries = max_retries or Config.MAX_RETRIES

    for attempt in range(1, _retries + 1):
        try:
            resp = requests.post(url, json=json_data, headers=headers, timeout=_timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            logger.warning(f'POST timeout on attempt {attempt}/{_retries}: {url}')
        except requests.exceptions.ConnectionError:
            logger.warning(f'POST connection error on attempt {attempt}/{_retries}: {url}')
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 'unknown'
            logger.warning(f'POST HTTP {status} on attempt {attempt}/{_retries}: {url}')
            if 400 <= (status if isinstance(status, int) else 500) < 500:
                break
        except Exception as e:
            logger.error(f'POST unexpected error on attempt {attempt}/{_retries}: {url} — {e}')

        if attempt < _retries:
            time.sleep(Config.RETRY_DELAY * attempt)

    logger.error(f'All {_retries} POST attempts failed for: {url}')
    return None


# ── Data Validation Helpers ──────────────────────────────────────────────

def validate_positive_int(value, default=0):
    """Ensure value is a non-negative integer."""
    try:
        val = int(value)
        return val if val >= 0 else default
    except (TypeError, ValueError):
        return default


def validate_country_name(name):
    """Basic country name sanitization."""
    if not name or not isinstance(name, str):
        return ''
    cleaned = name.strip().title()
    # Common corrections
    corrections = {
        'Usa': 'USA',
        'Uk': 'UK',
        'Us': 'USA',
    }
    return corrections.get(cleaned, cleaned)


def safe_json(response):
    """Safely parse JSON from a response object."""
    if response is None:
        return None
    try:
        return response.json()
    except (ValueError, AttributeError):
        logger.error('Failed to parse JSON response')
        return None
