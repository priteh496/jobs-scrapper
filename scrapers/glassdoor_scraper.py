# scrapers/glassdoor_scraper.py
"""Scrape Glassdoor job listings via their public search endpoint."""

from __future__ import annotations
import logging
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .base_scraper import make_session, safe_get, rotate_agent

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.glassdoor.com/Job/jobs.htm"


def _parse_age(text: str) -> str:
    now = datetime.utcnow()
    text = text.lower()
    try:
        n = int(re.search(r"\d+", text).group())
        if "hour" in text:
            return (now - timedelta(hours=n)).strftime("%Y-%m-%d")
        if "day" in text:
            return (now - timedelta(days=n)).strftime("%Y-%m-%d")
        if "month" in text:
            return (now - timedelta(days=n * 30)).strftime("%Y-%m-%d")
    except (AttributeError, ValueError):
        pass
    if "today" in text or "just" in text:
        return now.strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


def scrape_glassdoor(keyword: str, location: str = "", max_jobs: int = 50) -> list[dict]:
    session = make_session()
    session.headers.update({"Referer": "https://www.glassdoor.com/"})
    jobs: list[dict] = []
    page = 1

    logger.info("[Glassdoor] Searching: %s in %s", keyword, location or "any")

    while len(jobs) < max_jobs:
        params = {
            "sc.keyword": keyword,
            "locT": "C" if location else "",
            "locName": location,
            "p": page,
        }
        resp = safe_get(session, SEARCH_URL, params=params)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.find_all("li", class_=re.compile(r"react-job-listing|JobsList"))

        if not cards:
            # Try alternate selectors
            cards = soup.find_all("div", attrs={"data-test": "jobListing"})

        if not cards:
            break

        for card in cards:
            try:
                title_el = card.find("a", class_=re.compile(r"job-title|jobLink|jobTitle"))
                company_el = card.find(["div", "span"], class_=re.compile(r"employer-name|companyName"))
                loc_el = card.find(["div", "span"], class_=re.compile(r"location|jobLocation"))
                date_el = card.find(["div", "span"], class_=re.compile(r"date|posted|listing-age"))

                title = title_el.get_text(strip=True) if title_el else ""
                href = title_el["href"] if title_el and title_el.has_attr("href") else ""
                link = f"https://www.glassdoor.com{href}" if href.startswith("/") else href
                company = company_el.get_text(strip=True) if company_el else ""
                loc = loc_el.get_text(strip=True) if loc_el else location
                date_str = _parse_age(date_el.get_text(strip=True)) if date_el else \
                    datetime.utcnow().strftime("%Y-%m-%d")

                if title:
                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": link,
                        "posting_date": date_str,
                        "source": "Glassdoor",
                    })
            except Exception as exc:
                logger.debug("Glassdoor card error: %s", exc)

        if len(cards) < 10:
            break
        page += 1
        rotate_agent(session)

    logger.info("[Glassdoor] Found %d jobs", len(jobs))
    return jobs[:max_jobs]
