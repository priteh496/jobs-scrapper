# crawler/company_career_crawler.py
"""
Discover and crawl company career pages to extract job listings directly
from company websites, bypassing aggregators entirely.
"""

from __future__ import annotations
import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scrapers.base_scraper import make_session, safe_get
from config.company_list import COMPANY_LIST, CAREER_PATH_CANDIDATES

logger = logging.getLogger(__name__)

# Patterns that indicate a link is a job listing
JOB_LINK_PATTERNS = re.compile(
    r"(job|career|position|opening|vacancy|role|opportunity|apply|hiring)",
    re.IGNORECASE,
)

# Patterns that indicate text is a job title
TITLE_TAGS = ["h1", "h2", "h3", "h4"]


def _detect_career_url(session, domain: str) -> str | None:
    """Try candidate paths until one returns a 200 response."""
    for path in CAREER_PATH_CANDIDATES:
        url = domain.rstrip("/") + path
        resp = safe_get(session, url, delay=(0.5, 1.5))
        if resp and resp.status_code == 200:
            logger.debug("Career page found: %s", url)
            return url
    return None


def _extract_jobs_from_page(html: str, base_url: str, company_name: str) -> list[dict]:
    """Parse a career page HTML and extract job listings."""
    soup = BeautifulSoup(html, "lxml")
    jobs = []

    # Remove navigation / footer noise
    for tag in soup.find_all(["nav", "footer", "header", "script", "style"]):
        tag.decompose()

    # Strategy 1 — find anchors that look like job links
    anchors = soup.find_all("a", href=True)
    for a in anchors:
        href = a["href"]
        text = a.get_text(strip=True)

        if not text or len(text) < 5 or len(text) > 120:
            continue
        if not JOB_LINK_PATTERNS.search(href) and not JOB_LINK_PATTERNS.search(text):
            continue

        full_url = href if href.startswith("http") else urljoin(base_url, href)

        # Try to grab a nearby company / location hint
        parent = a.find_parent(["li", "div", "tr", "article", "section"])
        location_hint = ""
        if parent:
            loc_el = parent.find(
                string=re.compile(r"(remote|hybrid|onsite|bangalore|mumbai|delhi|hyderabad|chennai|pune|usa|uk|india)", re.I)
            )
            if loc_el:
                location_hint = loc_el.strip()[:80]

        jobs.append({
            "job_title": text,
            "company": company_name,
            "location": location_hint or "See job page",
            "job_link": full_url,
            "posting_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": f"Company:{company_name}",
        })

    # Strategy 2 — heading tags on the page (fallback)
    if not jobs:
        for heading in soup.find_all(TITLE_TAGS):
            text = heading.get_text(strip=True)
            if 5 < len(text) < 120 and JOB_LINK_PATTERNS.search(text):
                jobs.append({
                    "job_title": text,
                    "company": company_name,
                    "location": "See company website",
                    "job_link": base_url,
                    "posting_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "source": f"Company:{company_name}",
                })

    return jobs


def crawl_company_careers(keyword: str, max_per_company: int = 10) -> list[dict]:
    """
    Crawl all configured company career pages and filter by keyword.
    Returns a flat list of job dicts.
    """
    session = make_session()
    all_jobs: list[dict] = []
    keyword_lower = keyword.lower()

    for company in COMPANY_LIST:
        name = company["name"]
        domain = company["domain"]
        # Use the configured path first, then auto-detect
        career_url = domain.rstrip("/") + company.get("path", "")

        resp = safe_get(session, career_url, delay=(1.0, 3.0))
        if not resp:
            # Auto-detect fallback
            career_url = _detect_career_url(session, domain)
            if career_url:
                resp = safe_get(session, career_url)

        if not resp:
            logger.info("[Crawler] Could not reach %s — skipping", name)
            continue

        logger.info("[Crawler] Scanning %s careers page …", name)
        jobs = _extract_jobs_from_page(resp.text, career_url, name)

        # Filter by keyword relevance
        relevant = [
            j for j in jobs
            if keyword_lower in j["job_title"].lower()
            or any(w in j["job_title"].lower() for w in keyword_lower.split())
        ]

        all_jobs.extend(relevant[:max_per_company])

    logger.info("[Crawler] Total company-page jobs: %d", len(all_jobs))
    return all_jobs


def crawl_custom_domain(domain: str, company_name: str, keyword: str) -> list[dict]:
    """
    Crawl a single custom company domain not in the predefined list.
    Usage:  crawl_custom_domain("https://example.com", "ExampleCorp", "sales manager")
    """
    session = make_session()
    career_url = _detect_career_url(session, domain)
    if not career_url:
        logger.warning("[Crawler] No career page found for %s", domain)
        return []

    resp = safe_get(session, career_url)
    if not resp:
        return []

    jobs = _extract_jobs_from_page(resp.text, career_url, company_name)
    keyword_lower = keyword.lower()
    return [
        j for j in jobs
        if keyword_lower in j["job_title"].lower()
        or any(w in j["job_title"].lower() for w in keyword_lower.split())
    ]
