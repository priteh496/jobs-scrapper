"""
export/csv_writer.py

Exports the final ranked job list to output/jobs.csv
"""

import os
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "jobs.csv")

COLUMNS = [
    "title",
    "company",
    "location",
    "experience",
    "skills",
    "education",
    "role_level",
    "score",
    "posting_date",
    "source",
    "apply_link",
]


def _format_date(dt) -> str:
    if dt is None:
        return "Unknown"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return str(dt)


def export_to_csv(jobs: list[dict], output_path: str = OUTPUT_FILE) -> str:
    """
    Write jobs list to CSV sorted by score (descending).
    Returns the output file path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rows = []
    for job in jobs:
        skills_list = job.get("skills_detected", [])
        rows.append({
            "title": job.get("job_title", "N/A"),
            "company": job.get("company", "N/A"),
            "location": job.get("location", "N/A"),
            "experience": job.get("experience_required", "Not specified"),
            "skills": ", ".join(skills_list) if skills_list else "N/A",
            "education": job.get("education_required", "Not specified"),
            "role_level": job.get("role_level", "N/A"),
            "score": job.get("score", 0),
            "posting_date": _format_date(job.get("posting_date")),
            "source": job.get("source", "N/A"),
            "apply_link": job.get("job_link", "N/A"),
        })

    df = pd.DataFrame(rows, columns=COLUMNS)
    df.sort_values("score", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)

    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Exported %d jobs to %s", len(df), output_path)
    print(f"\n✅ Results saved to: {output_path}")
    return output_path
