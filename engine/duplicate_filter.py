"""
engine/duplicate_filter.py

Removes duplicate job listings based on:
  1. Exact title + company match
  2. Near-identical job titles at the same company (fuzzy normalization)
"""

import re
import logging

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation/whitespace for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def remove_duplicates(jobs: list[dict]) -> list[dict]:
    """
    Deduplicate job list.
    Strategy:
      - Primary key: normalized(title) + normalized(company)
      - Secondary key: same apply_link URL
    """
    seen_keys: set = set()
    seen_links: set = set()
    unique = []
    duplicates = 0

    for job in jobs:
        title_key = _normalize(job.get("job_title", ""))
        company_key = _normalize(job.get("company", ""))
        composite_key = f"{title_key}|{company_key}"

        link = job.get("job_link", "").strip().lower()

        if composite_key in seen_keys:
            duplicates += 1
            continue
        if link and link in seen_links:
            duplicates += 1
            continue

        seen_keys.add(composite_key)
        if link:
            seen_links.add(link)
        unique.append(job)

    logger.info("Duplicate filter: kept %d / removed %d duplicates", len(unique), duplicates)
    return unique
