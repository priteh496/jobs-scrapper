"""
scrapers/internshala_scraper.py
Scrapes job/internship listings from Internshala.
"""

import time
import random
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://internshala.com/",
}


def _parse_internshala_date(date_text: str) -> datetime | None:
    today = datetime.now()
    date_text = date_text.lower().strip()
    try:
        if "today" in date_text or "just" in date_text:
            return today
        if "yesterday" in date_text:
            return today - timedelta(days=1)
        match = re.search(r"(\d+)\s+day", date_text)
        if match:
            return today - timedelta(days=int(match.group(1)))
        match_date = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", date_text)
        if match_date:
            return datetime.strptime(match_date.group(1), "%d %B %Y")
    except Exception:
        pass
    return None


def scrape_internshala(keyword: str, location: str = "", is_fresher: bool = False) -> list[dict]:
    """
    Scrape Internshala for jobs/internships.
    For freshers, also scrapes internships section.
    """
    jobs = []
    keyword_slug = quote_plus(keyword.lower().replace(" ", "-"))

    urls_to_scrape = [
        f"https://internshala.com/jobs/keywords-{keyword_slug}/",
    ]
    if is_fresher:
        intern_slug = quote_plus(keyword.lower().replace(" ", "-"))
        urls_to_scrape.append(f"https://internshala.com/internships/keywords-{intern_slug}/")

    for url in urls_to_scrape:
        try:
            time.sleep(random.uniform(1.5, 3.0))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Internshala listing cards
            cards = soup.select("div.individual_internship") or soup.select("div.internship_meta")

            if not cards:
                logger.warning("Internshala: No cards found at %s", url)
                continue

            for card in cards:
                try:
                    title_el = card.select_one("h3.job-internship-name a") or card.select_one("a.job-title-href")
                    company_el = card.select_one("p.company-name") or card.select_one("div.company_name a")
                    location_el = card.select_one("div.location_link a") or card.select_one("p.locations")
                    date_el = card.select_one("div.status-info span.status-recently-posted") or \
                              card.select_one("div.posted_by_container")

                    title = title_el.get_text(strip=True) if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    loc = location_el.get_text(strip=True) if location_el else (location or "N/A")
                    date_text = date_el.get_text(strip=True) if date_el else ""
                    posting_date = _parse_internshala_date(date_text)

                    href = title_el.get("href", "") if title_el else ""
                    job_link = ("https://internshala.com" + href) if href.startswith("/") else href

                    if title == "N/A" or not job_link:
                        continue

                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": job_link,
                        "posting_date": posting_date,
                        "source": "Internshala",
                    })
                except Exception as e:
                    logger.debug("Internshala card parse error: %s", e)
                    continue

        except requests.RequestException as e:
            logger.error("Internshala scrape failed: %s", e)
            continue

    logger.info("Internshala: collected %d jobs", len(jobs))
    return jobs
