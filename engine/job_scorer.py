"""
engine/job_scorer.py

Scores each job against the user profile using rule-based logic.

Scoring breakdown:
  Skill match:        +20 per matched skill
  Experience match:   +25 exact/within range | +10 slightly high | -20 too high
  Location match:     +15 same city | +10 remote
  Education match:    +15 exact | +10 overqualified | -10 underqualified
  Fresher bonus:      +30 intern role | +20 junior role
  Role level bonus:   +10 preferred level matched
"""

import re
import logging

logger = logging.getLogger(__name__)

# Education hierarchy: higher index = higher level
EDU_HIERARCHY = ["high_school", "diploma", "bachelor", "master", "phd"]


def _parse_exp_years(exp_text: str) -> tuple[float, float]:
    """
    Parse an experience requirement string into (min_years, max_years).
    Returns (0, 0) if not specified, (0, 0.5) for fresher/intern.
    """
    if not exp_text or exp_text.lower() in ("not specified", "n/a", ""):
        return 0.0, 100.0  # Unknown → don't penalize

    text = exp_text.lower()

    # 1-3 years
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)", text)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    # 2+ years  /  minimum 2 years
    plus_match = re.search(r"(\d+(?:\.\d+)?)\s*\+", text)
    if plus_match:
        val = float(plus_match.group(1))
        return val, val + 10  # open-ended upper bound

    # Any single number
    single = re.search(r"(\d+(?:\.\d+)?)", text)
    if single:
        val = float(single.group(1))
        return val, val

    return 0.0, 100.0


def score_job(job: dict, profile: dict) -> int:
    """
    Compute a match score for the given job against the user profile.
    Returns an integer score.
    """
    score = 0
    user_skills = [s.lower() for s in profile.get("skills", [])]
    user_exp = profile.get("years_of_experience", 0)
    user_edu = profile.get("education", "bachelor").lower()
    user_location = profile.get("preferred_location", "").lower()
    remote_ok = profile.get("remote_allowed", False)
    is_fresher = profile.get("is_fresher", False)

    job_skills = [s.lower() for s in job.get("skills_detected", [])]
    job_exp_text = job.get("experience_required", "Not specified")
    job_edu = job.get("education_required", "Not specified").lower()
    job_role = job.get("role_level", "mid").lower()
    job_location = job.get("location", "").lower()

    # ── 1. SKILL MATCH ──────────────────────────────────
    matched_skills = 0
    for user_skill in user_skills:
        for job_skill in job_skills:
            if user_skill in job_skill or job_skill in user_skill:
                matched_skills += 1
                break
    skill_score = matched_skills * 20
    score += skill_score
    logger.debug("  Skills: +%d (%d matched)", skill_score, matched_skills)

    # ── 2. EXPERIENCE MATCH ──────────────────────────────
    min_exp, max_exp = _parse_exp_years(job_exp_text)

    if min_exp == 0.0 and max_exp == 100.0:
        # Unknown requirement → neutral
        exp_score = 0
    elif min_exp <= user_exp <= max_exp:
        exp_score = 25   # Perfect range
    elif user_exp < min_exp:
        gap = min_exp - user_exp
        if gap <= 1:
            exp_score = 10   # Slightly under
        else:
            exp_score = -20  # Too little experience
    else:  # user_exp > max_exp
        exp_score = 5    # Overqualified is not penalized heavily

    score += exp_score
    logger.debug("  Experience: %+d (user=%.1f, required=%.1f–%.1f)", exp_score, user_exp, min_exp, max_exp)

    # ── 3. LOCATION MATCH ────────────────────────────────
    location_score = 0
    if user_location and user_location in job_location:
        location_score = 15
    elif "remote" in job_location or "work from home" in job_location or "wfh" in job_location:
        if remote_ok:
            location_score = 10
    elif "anywhere" in job_location or "pan india" in job_location:
        location_score = 8
    score += location_score
    logger.debug("  Location: +%d", location_score)

    # ── 4. EDUCATION MATCH ───────────────────────────────
    edu_score = 0
    try:
        job_edu_norm = "Not specified"
        for level in EDU_HIERARCHY:
            if level in job_edu:
                job_edu_norm = level
                break

        if job_edu_norm == "Not specified":
            edu_score = 5   # No requirement stated
        else:
            user_rank = EDU_HIERARCHY.index(user_edu) if user_edu in EDU_HIERARCHY else 2
            job_rank = EDU_HIERARCHY.index(job_edu_norm)
            if user_rank == job_rank:
                edu_score = 15
            elif user_rank > job_rank:
                edu_score = 10  # Overqualified
            else:
                edu_score = -10  # Underqualified
    except (ValueError, Exception) as e:
        logger.debug("  Education scoring error: %s", e)
    score += edu_score
    logger.debug("  Education: %+d", edu_score)

    # ── 5. FRESHER BONUS ─────────────────────────────────
    fresher_score = 0
    if is_fresher:
        if job_role == "intern":
            fresher_score = 30
        elif job_role == "junior":
            fresher_score = 20
    score += fresher_score
    logger.debug("  Fresher bonus: +%d", fresher_score)

    # ── 6. TITLE KEYWORD BONUS ───────────────────────────
    keyword = profile.get("job_keyword", "").lower()
    title = job.get("job_title", "").lower()
    if keyword and keyword in title:
        score += 15
        logger.debug("  Title keyword match: +15")

    logger.debug("  TOTAL SCORE: %d", score)
    return score
