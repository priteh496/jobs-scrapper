# scrapers/monster_scraper.py
"""Scrape Monster.com job listings."""

from __future__ import annotations
import logging
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .base_scraper import make_session, safe_get, rotate_agent

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.monster.com/jobs/search"


def _parse_age(text: str) -> str:
    now = datetime.utcnow()
    text = text.lower()
    try:
        n = int(re.search(r"\d+", text).group())
        if "hour" in text:
            return (now - timedelta(hours=n)).strftime("%Y-%m-%d")
        if "day" in text:
            return (now - timedelta(days=n)).strftime("%Y-%m-%d")
        if "week" in text:
            return (now - timedelta(weeks=n)).strftime("%Y-%m-%d")
    except (AttributeError, ValueError):
        pass
    return now.strftime("%Y-%m-%d")


def scrape_monster(keyword: str, location: str = "", max_jobs: int = 50) -> list[dict]:
    session = make_session()
    jobs: list[dict] = []
    page = 1

    logger.info("[Monster] Searching: %s in %s", keyword, location or "any")

    while len(jobs) < max_jobs:
        params = {
            "q": keyword,
            "where": location,
            "page": page,
        }
        resp = safe_get(session, SEARCH_URL, params=params)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.find_all(["section", "div"], class_=re.compile(
            r"card-content|job-cardstyle|job-listing"
        ))

        if not cards:
            break

        for card in cards:
            try:
                title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"title|jobTitle"))
                company_el = card.find(["span", "div"], class_=re.compile(r"company|org"))
                loc_el = card.find(["span", "div"], class_=re.compile(r"location|loc"))
                date_el = card.find(["time", "span"], class_=re.compile(r"date|posted|time"))
                link_el = card.find("a", href=re.compile(r"/job-openings/|/jobs/"))

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                loc = loc_el.get_text(strip=True) if loc_el else location
                date_str = _parse_age(date_el.get_text(strip=True)) if date_el else \
                    datetime.utcnow().strftime("%Y-%m-%d")
                href = link_el["href"] if link_el and link_el.has_attr("href") else ""
                link = f"https://www.monster.com{href}" if href.startswith("/") else href

                if title:
                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": link,
                        "posting_date": date_str,
                        "source": "Monster",
                    })
            except Exception as exc:
                logger.debug("Monster card error: %s", exc)

        if len(cards) < 10:
            break
        page += 1
        rotate_agent(session)

    logger.info("[Monster] Found %d jobs", len(jobs))
    return jobs[:max_jobs]
