"""
scrapers/indeed_scraper.py
Scrapes job listings from Indeed.
Returns a list of job dicts with standardized fields.
"""

import time
import random
import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _parse_indeed_date(date_text: str) -> datetime | None:
    """Convert Indeed relative date strings to datetime objects."""
    today = datetime.now()
    date_text = date_text.lower().strip()
    try:
        if "just posted" in date_text or "today" in date_text:
            return today
        if "hour" in date_text:
            return today
        match = re.search(r"(\d+)\s+day", date_text)
        if match:
            return today - timedelta(days=int(match.group(1)))
        if "30+" in date_text:
            return today - timedelta(days=31)
    except Exception:
        pass
    return None


def scrape_indeed(keyword: str, location: str, max_pages: int = 2) -> list[dict]:
    """
    Scrape Indeed for jobs matching keyword + location.
    Returns list of job dicts.
    """
    jobs = []
    base_url = "https://www.indeed.com/jobs"

    for page in range(max_pages):
        params = {
            "q": keyword,
            "l": location,
            "start": page * 10,
            "fromage": "30",
        }
        try:
            time.sleep(random.uniform(1.5, 3.5))
            resp = requests.get(base_url, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Indeed card selectors (may change with site updates)
            cards = soup.select("div.job_seen_beacon") or soup.select("div.jobsearch-SerpJobCard")

            if not cards:
                logger.warning("Indeed: No job cards found on page %d. Site structure may have changed.", page)
                break

            for card in cards:
                try:
                    title_el = card.select_one("h2.jobTitle span[title]") or card.select_one("h2.jobTitle")
                    company_el = card.select_one("span.companyName") or card.select_one("[data-testid='company-name']")
                    location_el = card.select_one("div.companyLocation") or card.select_one("[data-testid='text-location']")
                    date_el = card.select_one("span.date") or card.select_one("[data-testid='myJobsStateDate']")
                    link_el = card.select_one("a[id^='job_']") or card.select_one("a.jcs-JobTitle")

                    title = title_el.get_text(strip=True) if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    loc = location_el.get_text(strip=True) if location_el else "N/A"
                    date_text = date_el.get_text(strip=True) if date_el else ""
                    posting_date = _parse_indeed_date(date_text)

                    href = link_el.get("href", "") if link_el else ""
                    job_link = "https://www.indeed.com" + href if href.startswith("/") else href

                    if title == "N/A" or not job_link:
                        continue

                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": job_link,
                        "posting_date": posting_date,
                        "source": "Indeed",
                    })
                except Exception as e:
                    logger.debug("Indeed card parse error: %s", e)
                    continue

        except requests.RequestException as e:
            logger.error("Indeed scrape failed (page %d): %s", page, e)
            break

    logger.info("Indeed: collected %d jobs", len(jobs))
    return jobs
