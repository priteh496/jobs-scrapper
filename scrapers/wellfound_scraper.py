"""
scrapers/wellfound_scraper.py
Scrapes job listings from Wellfound (formerly AngelList Talent).
Uses their public jobs search page.
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
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_wellfound_date(date_text: str) -> datetime | None:
    today = datetime.now()
    date_text = date_text.lower().strip()
    try:
        if "today" in date_text or "just" in date_text or "hour" in date_text:
            return today
        if "yesterday" in date_text:
            return today - timedelta(days=1)
        match = re.search(r"(\d+)\s+day", date_text)
        if match:
            return today - timedelta(days=int(match.group(1)))
        match = re.search(r"(\d+)\s+week", date_text)
        if match:
            return today - timedelta(weeks=int(match.group(1)))
        match = re.search(r"(\d+)\s+month", date_text)
        if match:
            return today - timedelta(days=int(match.group(1)) * 30)
    except Exception:
        pass
    return None


def scrape_wellfound(keyword: str, location: str = "", remote_allowed: bool = False) -> list[dict]:
    """
    Scrape Wellfound job listings.
    """
    jobs = []
    keyword_encoded = quote_plus(keyword)
    location_encoded = quote_plus(location) if location else ""

    urls = []
    if location:
        urls.append(f"https://wellfound.com/jobs?q={keyword_encoded}&l={location_encoded}")
    if remote_allowed:
        urls.append(f"https://wellfound.com/jobs?q={keyword_encoded}&remote=true")
    if not urls:
        urls.append(f"https://wellfound.com/jobs?q={keyword_encoded}")

    for url in urls:
        try:
            time.sleep(random.uniform(2.0, 4.0))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Wellfound uses JS-rendered content; try static HTML selectors
            cards = (
                soup.select("div[class*='JobListing']") or
                soup.select("div[data-test='JobListing']") or
                soup.select("div.styles_component__Ey28k") or
                soup.select("li[class*='job']")
            )

            if not cards:
                logger.warning("Wellfound: No job cards found. Site may require JS rendering.")
                # Fallback: parse any <a> tags that look like job links
                for link in soup.find_all("a", href=re.compile(r"/jobs/\d+")):
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue
                    job_link = "https://wellfound.com" + href if href.startswith("/") else href
                    jobs.append({
                        "job_title": title,
                        "company": "N/A",
                        "location": location or "Remote",
                        "job_link": job_link,
                        "posting_date": datetime.now(),
                        "source": "Wellfound",
                    })
                continue

            for card in cards:
                try:
                    title_el = (
                        card.select_one("a[class*='title']") or
                        card.select_one("h2 a") or
                        card.select_one("a[data-test='job-title']")
                    )
                    company_el = (
                        card.select_one("a[class*='company']") or
                        card.select_one("span[class*='company']")
                    )
                    location_el = (
                        card.select_one("span[class*='location']") or
                        card.select_one("div[class*='location']")
                    )
                    date_el = card.select_one("span[class*='date']") or card.select_one("time")

                    title = title_el.get_text(strip=True) if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    loc = location_el.get_text(strip=True) if location_el else (location or "N/A")
                    date_text = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""
                    posting_date = _parse_wellfound_date(date_text)

                    href = title_el.get("href", "") if title_el else ""
                    job_link = ("https://wellfound.com" + href) if href.startswith("/") else href

                    if title == "N/A" or not job_link:
                        continue

                    jobs.append({
                        "job_title": title,
                        "company": company,
                        "location": loc,
                        "job_link": job_link,
                        "posting_date": posting_date,
                        "source": "Wellfound",
                    })
                except Exception as e:
                    logger.debug("Wellfound card parse error: %s", e)
                    continue

        except requests.RequestException as e:
            logger.error("Wellfound scrape failed: %s", e)
            continue

    logger.info("Wellfound: collected %d jobs", len(jobs))
    return jobs
