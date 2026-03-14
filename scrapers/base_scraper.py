# scrapers/base_scraper.py
"""Shared HTTP utilities used by every scraper."""

from __future__ import annotations
import time
import random
import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── Rotating User-Agents ─────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

TIMEOUT = 20  # seconds per request
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5


def make_session() -> requests.Session:
    """Create a requests Session with retry logic and a random User-Agent."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(BASE_HEADERS)
    session.headers["Referer"] = "https://www.google.com/"
    session.headers["User-Agent"] = random.choice(USER_AGENTS)
    return session


def safe_get(session: requests.Session, url: str, params: dict | None = None,
             delay: tuple[float, float] = (1.5, 4.0)) -> Optional[requests.Response]:

    time.sleep(random.uniform(*delay))

    # rotate user agent
    session.headers["User-Agent"] = random.choice(USER_AGENTS)

    try:
        resp = session.get(
            url,
            params=params,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if resp.status_code == 200:
            return resp

        logger.warning("HTTP %s for %s", resp.status_code, url)
        return None

    except requests.RequestException as exc:
        logger.warning("Request failed for %s: %s", url, exc)
        return None


def rotate_agent(session: requests.Session) -> None:
    """Swap the User-Agent mid-session to reduce fingerprinting."""
    session.headers["User-Agent"] = random.choice(USER_AGENTS)
