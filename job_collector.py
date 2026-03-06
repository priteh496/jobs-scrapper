# job_collector.py
"""
Orchestrates all scrapers and the company career crawler.
Returns a unified flat list of raw job dicts.
"""

from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from scrapers.linkedin_scraper import scrape_linkedin
from scrapers.indeed_scraper import scrape_indeed
from scrapers.naukri_scraper import scrape_naukri
from scrapers.internshala_scraper import scrape_internshala
from scrapers.glassdoor_scraper import scrape_glassdoor
from scrapers.wellfound_scraper import scrape_wellfound
from scrapers.monster_scraper import scrape_monster
from scrapers.simplyhired_scraper import scrape_simplyhired

from crawler.company_career_crawler import crawl_company_careers

logger = logging.getLogger(__name__)

# ── Scraper registry ─────────────────────────────────────────────────────────
ALL_SCRAPERS: dict[str, Callable] = {
    "LinkedIn": scrape_linkedin,
    "Indeed": scrape_indeed,
    "Naukri": scrape_naukri,
    "Internshala": scrape_internshala,
    "Glassdoor": scrape_glassdoor,
    "Wellfound": scrape_wellfound,
    "Monster": scrape_monster,
    "SimplyHired": scrape_simplyhired,
}

# Internshala is always included for fresher mode
FRESHER_PRIORITY = ["Internshala", "LinkedIn", "Indeed", "Naukri"]


def collect_jobs(
    keyword: str,
    location: str = "",
    fresher_mode: bool = False,
    max_per_source: int = 40,
    enabled_sources: list[str] | None = None,
    include_company_crawler: bool = True,
    workers: int = 4,
) -> list[dict]:
    """
    Run all (or selected) scrapers in parallel and return a merged job list.
    """

    sources = enabled_sources or list(ALL_SCRAPERS.keys())

    if fresher_mode:
        sources = sorted(
            sources,
            key=lambda s: (0 if s in FRESHER_PRIORITY else 1, s),
        )

    selected: dict[str, Callable] = {
        name: fn for name, fn in ALL_SCRAPERS.items() if name in sources
    }

    all_jobs: list[dict] = []

    def _run_scraper(name: str, fn: Callable) -> tuple[str, list[dict]]:
        try:
            jobs = fn(keyword=keyword, location=location, max_jobs=max_per_source)

            # Ensure jobs is always a list
            if jobs is None:
                jobs = []

            if not isinstance(jobs, list):
                logger.warning(
                    "[Collector] %s returned unexpected type (%s)",
                    name,
                    type(jobs).__name__,
                )
                jobs = []

            return name, jobs

        except Exception as exc:
            logger.warning("[Collector] %s failed: %s", name, exc)
            return name, []

    # ── Parallel scraping ─────────────────────────────────────────────────
    logger.info(
        "🚀  Launching %d scrapers with %d workers …",
        len(selected),
        workers,
    )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_scraper, name, fn): name
            for name, fn in selected.items()
        }

        for future in as_completed(futures):
            name, jobs = future.result()

            if jobs is None:
                jobs = []

            logger.info("  ✓  %-15s → %d jobs", name, len(jobs))

            all_jobs.extend(jobs)

    # ── Company career crawler (sequential to be polite) ──────────────────
    if include_company_crawler:
        logger.info("🏢  Crawling company career pages …")

        try:
            company_jobs = crawl_company_careers(keyword)

            if company_jobs is None:
                company_jobs = []

            logger.info("  ✓  Company pages → %d jobs", len(company_jobs))

            all_jobs.extend(company_jobs)

        except Exception as exc:
            logger.warning("[Collector] Company crawler failed: %s", exc)

    logger.info("📦  Total raw jobs collected: %d", len(all_jobs))

    return all_jobs