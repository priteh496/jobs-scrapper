"""
engine/freshness_filter.py

Filters jobs older than the user's selected freshness window.
Also handles jobs with missing/unknown posting dates gracefully.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def filter_by_freshness(jobs: list[dict], freshness_days: int) -> list[dict]:
    """
    Remove jobs posted before the freshness cutoff.

    Jobs with unknown (None) posting dates are KEPT by default,
    because we cannot confirm they are stale.
    """
    if freshness_days <= 0:
        return jobs

    cutoff = datetime.now() - timedelta(days=freshness_days)
    filtered = []
    removed = 0

    for job in jobs:
        posting_date = job.get("posting_date")

        if posting_date is None:
            # Unknown date → include with a flag
            job["date_unknown"] = True
            filtered.append(job)
            continue

        if isinstance(posting_date, str):
            try:
                posting_date = datetime.fromisoformat(posting_date)
            except ValueError:
                job["date_unknown"] = True
                filtered.append(job)
                continue

        if posting_date >= cutoff:
            filtered.append(job)
        else:
            removed += 1

    logger.info(
        "Freshness filter (%d days): kept %d / removed %d jobs",
        freshness_days, len(filtered), removed,
    )
    return filtered
