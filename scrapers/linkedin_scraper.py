# scrapers/linkedin_scraper.py
"""Scrape public LinkedIn Jobs listings (no login required)."""

from __future__ import annotations
import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .base_scraper import make_session, safe_get, rotate_agent

logger = logging.getLogger(__name__)

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"


def _parse_age(time_str: str) -> str:
    """Convert 'X hours/days/weeks ago' → ISO date string (best-effort)."""
    now = datetime.utcnow()

    try:
        parts = time_str.lower().split()
        n = int(parts[0])

        if "hour" in parts[1]:
            return (now - timedelta(hours=n)).strftime("%Y-%m-%d")

        if "day" in parts[1]:
            return (now - timedelta(days=n)).strftime("%Y-%m-%d")

        if "week" in parts[1]:
            return (now - timedelta(weeks=n)).strftime("%Y-%m-%d")

        if "month" in parts[1]:
            return (now - timedelta(days=n * 30)).strftime("%Y-%m-%d")

    except (IndexError, ValueError):
        pass

    return now.strftime("%Y-%m-%d")


def scrape_linkedin(keyword: str, location: str = "", max_jobs: int = 50) -> list[dict]:
    """Return a list of job dicts scraped from LinkedIn public job search."""

    session = make_session()
    jobs: list[dict] = []
    start = 0
    page_size = 25

    params_base = {
        "keywords": keyword,
        "location": location,
        "f_TPR": "r86400",   # posted last 24 h
        "position": 1,
        "pageNum": 0,
    }

    logger.info("[LinkedIn] Searching: %s in %s", keyword, location or "any")

    while len(jobs) < max_jobs:

        if start > 200:
            break

        params = {**params_base, "start": start}

        rotate_agent(session)
        resp = safe_get(session, BASE_URL, params=params)

        if not resp:
            break

        if "captcha" in resp.text.lower():
            logger.warning("[LinkedIn] CAPTCHA detected — stopping scraper")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        cards = soup.select("div.base-card")

        if not cards:
            cards = soup.select("li.result-card")

        if not cards:
            break

        for card in cards:
            try:

                title_el = card.find("h3", class_="base-search-card__title")
                company_el = card.find("h4", class_="base-search-card__subtitle")
                location_el = card.find("span", class_="job-search-card__location")
                time_el = card.find("time")
                link_el = card.find("a", class_="base-card__full-link")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                loc = location_el.get_text(strip=True) if location_el else ""

                if time_el and time_el.has_attr("datetime"):
                    date_str = time_el["datetime"]
                elif time_el:
                    date_str = _parse_age(time_el.get_text(strip=True))
                else:
                    date_str = datetime.utcnow().strftime("%Y-%m-%d")

                if link_el and link_el.has_attr("href"):
                    link = link_el["href"].split("?")[0]
                else:
                    link = ""

                if title and link not in [j["job_link"] for j in jobs]:
                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": link,
                        "posting_date": date_str,
                        "source": "LinkedIn",
                    })

            except Exception as exc:
                logger.debug("Card parse error: %s", exc)

        if len(cards) < page_size:
            break

        start += page_size

    logger.info("[LinkedIn] Found %d jobs", len(jobs))

    return jobs[:max_jobs]