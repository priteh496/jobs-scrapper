#!/usr/bin/env python3
# main.py
"""
Local AI Job Intelligence Agent
================================
Collects jobs from multiple portals, analyses them, scores against
the user profile and exports a ranked CSV.

Run:
    python main.py
"""

from __future__ import annotations
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

# ── Local imports ─────────────────────────────────────────────────────────────
from profile_input        import collect_profile
from job_collector        import collect_jobs
from parser.description_parser import parse_job_description
from engine.freshness_filter   import apply_freshness_filter
from engine.duplicate_filter   import remove_duplicates
from engine.job_scorer         import rank_jobs
from export.csv_writer         import export_to_csv, print_top_jobs

# ── Constants ─────────────────────────────────────────────────────────────────
DESCRIPTION_WORKERS = 6   # threads for parallel description fetching
MAX_DESCRIPTION_JOBS = 80  # cap how many job pages we fully parse


def _parse_descriptions(jobs: list[dict], user_skills: list[str]) -> list[dict]:
    """Fetch & parse job descriptions in parallel."""
    # Only parse up to MAX_DESCRIPTION_JOBS to avoid excessive network use
    to_parse = jobs[:MAX_DESCRIPTION_JOBS]
    rest     = jobs[MAX_DESCRIPTION_JOBS:]

    enriched: list[dict] = []

    print(f"\n🔍  Analysing {len(to_parse)} job descriptions (parallel, {DESCRIPTION_WORKERS} threads) …")

    with ThreadPoolExecutor(max_workers=DESCRIPTION_WORKERS) as pool:
        futures = {
            pool.submit(parse_job_description, job, user_skills): job
            for job in to_parse
        }
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                enriched.append(result)
                if i % 10 == 0 or i == len(to_parse):
                    print(f"   … {i}/{len(to_parse)} parsed", end="\r", flush=True)
            except Exception as exc:
                # On error, keep original job without enrichment
                original = futures[future]
                enriched.append(original)
                logger.debug("Parse failed: %s", exc)

    print()   # newline after progress

    # Attach minimal defaults for un-parsed jobs
    for job in rest:
        job.setdefault("required_exp_min", 0)
        job.setdefault("required_exp_max", 0)
        job.setdefault("skills_detected", [])
        job.setdefault("education_required", "not specified")
        job.setdefault("job_level", "not specified")
        job.setdefault("fresher_friendly", False)
        job.setdefault("description_length", 0)
        enriched.append(job)

    return enriched


def _banner(text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def main() -> None:
    start_time = time.time()

    # ── Step 1: Profile ───────────────────────────────────────────────────────
    profile = collect_profile()
    keyword  = profile["job_keyword"]
    location = profile["preferred_location"]
    freshness_days = profile["freshness_days"]
    user_skills    = profile["skills"]
    fresher_mode   = profile["fresher_mode"]

    # ── Step 2: Collect raw jobs ──────────────────────────────────────────────
    _banner(f"STEP 1/5 — COLLECTING JOBS  |  keyword: '{keyword}'  |  location: '{location or 'any'}'")
    raw_jobs = collect_jobs(
        keyword=keyword,
        location=location,
        fresher_mode=fresher_mode,
        max_per_source=40,
        include_company_crawler=True,
        workers=4,
    )
    print(f"  ✅  Collected {len(raw_jobs)} raw listings")

    if not raw_jobs:
        print("\n⚠  No jobs found. Try a broader keyword or different location.\n")
        return

    # ── Step 3: Freshness filter ──────────────────────────────────────────────
    _banner(f"STEP 2/5 — FRESHNESS FILTER  |  last {freshness_days} days")
    fresh_jobs = apply_freshness_filter(raw_jobs, freshness_days)
    print(f"  ✅  {len(fresh_jobs)} jobs within the freshness window")

    # ── Step 4: Deduplication ─────────────────────────────────────────────────
    _banner("STEP 3/5 — DEDUPLICATION")
    unique_jobs = remove_duplicates(fresh_jobs)
    print(f"  ✅  {len(unique_jobs)} unique jobs after deduplication")

    # ── Step 5: Description parsing (NLP) ────────────────────────────────────
    _banner("STEP 4/5 — JOB DESCRIPTION ANALYSIS (rule-based NLP)")
    enriched_jobs = _parse_descriptions(unique_jobs, user_skills)
    print(f"  ✅  Enriched {len(enriched_jobs)} jobs")

    # ── Step 6: Scoring & ranking ─────────────────────────────────────────────
    _banner("STEP 5/5 — SCORING & RANKING")
    ranked_jobs = rank_jobs(enriched_jobs, profile)
    print(f"  ✅  Ranked {len(ranked_jobs)} jobs")

    # ── Output ────────────────────────────────────────────────────────────────
    csv_path = export_to_csv(ranked_jobs)
    print_top_jobs(ranked_jobs, n=10)

    elapsed = time.time() - start_time
    print(f"\n🎉  Done in {elapsed:.1f}s")
    print(f"📄  Full results saved to: {csv_path}")
    print(f"📋  Log saved to: job_agent.log\n")


if __name__ == "__main__":
    main()
