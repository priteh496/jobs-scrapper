"""
parser/description_parser.py

Rule-based NLP parser.
Extracts: experience_required, skills_detected, education_required, role_level
from a raw job description string.
"""

import re
import logging
import time
import random

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# SKILLS DATABASE
# ──────────────────────────────────────────────
SKILLS_DB = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "r", "scala",
    "ruby", "php", "go", "rust", "swift", "kotlin", "matlab",
    # Data / Analytics
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "oracle",
    "excel", "tableau", "power bi", "looker", "qlik", "metabase",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    # ML / AI
    "machine learning", "deep learning", "natural language processing",
    "nlp", "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "hugging face", "transformers", "opencv",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "linux", "unix", "bash", "shell scripting", "git", "github", "gitlab",
    "ci/cd", "jenkins", "ansible",
    # Web
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask",
    "fastapi", "spring boot", "rest api", "graphql",
    # Data Engineering
    "spark", "hadoop", "kafka", "airflow", "dbt", "etl", "snowflake",
    "redshift", "bigquery", "databricks",
    # Soft / Other
    "communication", "teamwork", "agile", "scrum", "jira", "confluence",
    "ms office", "google workspace", "project management", "excel",
]

# Compile patterns once for performance
_SKILL_PATTERNS = [(skill, re.compile(r"\b" + skill + r"\b", re.IGNORECASE)) for skill in SKILLS_DB]

# ──────────────────────────────────────────────
# EXPERIENCE PATTERNS
# ──────────────────────────────────────────────
_EXP_PATTERNS = [
    re.compile(r"(\d+)\s*[-–to]+\s*(\d+)\s*\+?\s*years?", re.IGNORECASE),        # 1-3 years
    re.compile(r"(\d+)\s*\+\s*years?", re.IGNORECASE),                            # 2+ years
    re.compile(r"minimum\s+(\d+)\s*\+?\s*years?", re.IGNORECASE),                 # minimum 2 years
    re.compile(r"at\s+least\s+(\d+)\s*\+?\s*years?", re.IGNORECASE),              # at least 2 years
    re.compile(r"(\d+)\s*years?\s+(?:of\s+)?(?:work\s+)?experience", re.IGNORECASE),  # 5 years experience
    re.compile(r"experience\s+of\s+(\d+)\s*\+?\s*years?", re.IGNORECASE),
    re.compile(r"(\d+)\s*years?\s+(?:relevant|industry|professional)", re.IGNORECASE),
]

# ──────────────────────────────────────────────
# EDUCATION PATTERNS
# ──────────────────────────────────────────────
_EDU_KEYWORDS = {
    "phd": re.compile(r"\bph\.?d\.?\b|\bdoctorate\b", re.IGNORECASE),
    "master": re.compile(r"\bmaster[s]?\b|\bm\.?s\.?\b|\bm\.?tech\b|\bmba\b|\bm\.?e\b", re.IGNORECASE),
    "bachelor": re.compile(r"\bbachelor[s]?\b|\bb\.?e\.?\b|\bb\.?tech\b|\bb\.?s\.?\b|\bb\.?sc\b|\bdegree\b", re.IGNORECASE),
    "diploma": re.compile(r"\bdiploma\b", re.IGNORECASE),
    "high_school": re.compile(r"\bhigh school\b|\b12th\b|\bhsc\b|\bssc\b", re.IGNORECASE),
}

# ──────────────────────────────────────────────
# ROLE LEVEL PATTERNS
# ──────────────────────────────────────────────
_ROLE_LEVELS = {
    "intern": re.compile(r"\bintern(ship)?\b|\btrainee\b", re.IGNORECASE),
    "junior": re.compile(r"\bjunior\b|\bassociate\b|\bentry.?level\b|\bfresher\b|\bgraduate\b", re.IGNORECASE),
    "mid": re.compile(r"\bmid.?level\b|\bintermediate\b|\b2[-–]5\s*years\b", re.IGNORECASE),
    "senior": re.compile(r"\bsenior\b|\bsr\.\b|\blead\b|\bprincipal\b|\bstaff\b", re.IGNORECASE),
    "manager": re.compile(r"\bmanager\b|\bdirector\b|\bvp\b|\bhead\s+of\b", re.IGNORECASE),
}


# ──────────────────────────────────────────────
# PAGE FETCHER
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_job_description(url: str, retries: int = 2) -> str:
    """Fetch raw text content of a job page."""
    for attempt in range(retries + 1):
        try:
            time.sleep(random.uniform(1.0, 2.5))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Remove script/style noise
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                tag.decompose()

            # Try common job description containers first
            for selector in [
                "div#jobDescriptionText",         # Indeed
                "div.job-description",
                "div[class*='description']",
                "div[class*='job-desc']",
                "section[class*='description']",
                "article",
                "main",
            ]:
                container = soup.select_one(selector)
                if container:
                    return container.get_text(separator=" ", strip=True)

            return soup.get_text(separator=" ", strip=True)

        except requests.RequestException as e:
            if attempt < retries:
                logger.debug("Retry %d for %s: %s", attempt + 1, url, e)
                time.sleep(random.uniform(2.0, 4.0))
            else:
                logger.warning("Failed to fetch job page %s: %s", url, e)
                return ""

    return ""


# ──────────────────────────────────────────────
# EXPERIENCE EXTRACTOR
# ──────────────────────────────────────────────
def extract_experience(text: str) -> str:
    """Return the first experience range found or 'Not specified'."""
    for pattern in _EXP_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return "Not specified"


# ──────────────────────────────────────────────
# SKILLS EXTRACTOR
# ──────────────────────────────────────────────
def extract_skills(text: str) -> list[str]:
    """Return list of skills found in description text."""
    found = []
    for skill_name, pattern in _SKILL_PATTERNS:
        if pattern.search(text):
            # Use clean display name (remove regex escapes)
            display = skill_name.replace("\\+\\+", "++").replace("\\.", ".")
            found.append(display)
    return list(dict.fromkeys(found))  # deduplicate preserving order


# ──────────────────────────────────────────────
# EDUCATION EXTRACTOR
# ──────────────────────────────────────────────
def extract_education(text: str) -> str:
    """Return the highest education requirement detected."""
    priority = ["phd", "master", "bachelor", "diploma", "high_school"]
    for level in priority:
        if _EDU_KEYWORDS[level].search(text):
            return level
    return "Not specified"


# ──────────────────────────────────────────────
# ROLE LEVEL DETECTOR
# ──────────────────────────────────────────────
def detect_role_level(text: str, job_title: str = "") -> str:
    """Detect seniority level from description and title."""
    combined = f"{job_title} {text}"
    # Check in priority order
    priority = ["intern", "junior", "senior", "manager", "mid"]
    for level in priority:
        if _ROLE_LEVELS[level].search(combined):
            return level
    return "mid"


# ──────────────────────────────────────────────
# MAIN PARSE FUNCTION
# ──────────────────────────────────────────────
def parse_job_description(url: str, job_title: str = "") -> dict:
    """
    Fetch job page and extract structured fields.

    Returns dict with:
        description_text, experience_required, skills_detected,
        education_required, role_level
    """
    text = fetch_job_description(url)

    if not text:
        return {
            "description_text": "",
            "experience_required": "Not specified",
            "skills_detected": [],
            "education_required": "Not specified",
            "role_level": "mid",
        }

    return {
        "description_text": text[:500],  # Store short preview
        "experience_required": extract_experience(text),
        "skills_detected": extract_skills(text),
        "education_required": extract_education(text),
        "role_level": detect_role_level(text, job_title),
    }
