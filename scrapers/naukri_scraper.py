# scrapers/naukri_scraper.py
"""Scrape Naukri.com job listings (India-focused)."""

from __future__ import annotations
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base_scraper import make_session, safe_get, rotate_agent

logger = logging.getLogger(__name__)

BASE_URL = "https://www.naukri.com/{keyword}-jobs"
SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"


def _parse_naukri_age(text: str) -> str:
    now = datetime.utcnow()
    text = text.lower().strip()
    try:
        n = int(re.search(r"\d+", text).group())
        if "day" in text:
            return (now - timedelta(days=n)).strftime("%Y-%m-%d")
        if "hour" in text:
            return (now - timedelta(hours=n)).strftime("%Y-%m-%d")
        if "month" in text:
            return (now - timedelta(days=n * 30)).strftime("%Y-%m-%d")
    except (AttributeError, ValueError):
        pass
    if "today" in text or "few" in text:
        return now.strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


def scrape_naukri(keyword: str, location: str = "", max_jobs: int = 50) -> list[dict]:
    session = make_session()
    # Naukri requires specific headers to avoid blocks
    session.headers.update({
        "Referer": "https://www.naukri.com/",
        "appid": "109",
        "systemid": "109",
    })

    jobs: list[dict] = []
    keyword_slug = keyword.replace(" ", "-").lower()
    page = 1

    logger.info("[Naukri] Searching: %s in %s", keyword, location or "India")

    while len(jobs) < max_jobs:
        params = {
            "noOfResults": 20,
            "urlType": "search_by_keyword",
            "searchType": "adv",
            "keyword": keyword,
            "location": location,
            "pageNo": page,
            "sort": "r",
            "areaTypeID": 0,
            "searchid": "",
        }
        resp = safe_get(session, SEARCH_URL, params=params)
        if resp:
            try:
                data = resp.json()
                job_list = data.get("jobDetails", [])
                for job in job_list:
                    jobs.append({
                        "job_title": job.get("title", ""),
                        "company": job.get("companyName", ""),
                        "location": ", ".join(job.get("placeholders", [{}])[0].get("label", "").split(",")[:2])
                            if job.get("placeholders") else location,
                        "job_link": job.get("jdURL", ""),
                        "posting_date": _parse_naukri_age(
                            str(job.get("footerPlaceholderLabel", "Today"))
                        ),
                        "source": "Naukri",
                    })
                if len(job_list) < 20:
                    break
                page += 1
                rotate_agent(session)
                continue
            except Exception:
                pass  # fall through to HTML scraper

        # ── HTML fallback ─────────────────────────────────────────────────
        url = f"https://www.naukri.com/{keyword_slug}-jobs" + (
            f"-in-{location.lower().replace(' ', '-')}" if location else ""
        ) + f"?pageNo={page}"
        resp = safe_get(session, url)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.find_all("article", class_=re.compile(r"jobTuple|job-container"))
        if not cards:
            break

        for card in cards:
            try:
                title_el = card.find("a", class_=re.compile(r"title|jobTitle"))
                company_el = card.find(["a", "span"], class_=re.compile(r"comp-name|company"))
                loc_el = card.find("li", class_=re.compile(r"location|loc"))
                date_el = card.find("span", class_=re.compile(r"date|time"))

                title = title_el.get_text(strip=True) if title_el else ""
                link = title_el["href"] if title_el and title_el.has_attr("href") else ""
                company = company_el.get_text(strip=True) if company_el else ""
                loc = loc_el.get_text(strip=True) if loc_el else location
                date_str = _parse_naukri_age(date_el.get_text(strip=True)) if date_el else \
                    datetime.utcnow().strftime("%Y-%m-%d")

                if title:
                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": link,
                        "posting_date": date_str,
                        "source": "Naukri",
                    })
            except Exception as exc:
                logger.debug("Naukri card error: %s", exc)

        if len(cards) < 10:
            break
        page += 1
        rotate_agent(session)

    logger.info("[Naukri] Found %d jobs", len(jobs))
    return jobs[:max_jobs]
