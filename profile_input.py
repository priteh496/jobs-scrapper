# profile_input.py
"""Interactive CLI to collect user job-search profile."""

from __future__ import annotations
import sys


def _ask(prompt: str, default: str = "") -> str:
    try:
        answer = input(prompt).strip()
        return answer if answer else default
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def _ask_int(prompt: str, default: int = 0) -> int:
    while True:
        raw = _ask(prompt, str(default))
        try:
            return int(raw)
        except ValueError:
            print("  ⚠  Please enter a whole number.")


def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
    choices_str = "/".join(choices)
    while True:
        answer = _ask(f"{prompt} [{choices_str}]: ", default).lower()
        if answer in [c.lower() for c in choices]:
            return answer
        print(f"  ⚠  Choose one of: {choices_str}")


def collect_profile() -> dict:
    print("\n" + "═" * 60)
    print("  🤖  LOCAL AI JOB INTELLIGENCE AGENT")
    print("  Tell me about yourself and I'll find the best jobs for you.")
    print("═" * 60 + "\n")

    # ── Education ────────────────────────────────────────────────────────────
    print("📚  EDUCATION")
    edu_levels = ["high school", "diploma", "bachelor", "master", "phd", "other"]
    print("  Levels: " + " | ".join(edu_levels))
    education_level = _ask("  Your level: ", "bachelor")

    degree_field = _ask("  Degree / field of study (e.g. Computer Science, MBA, Nursing): ", "")

    # ── Skills ───────────────────────────────────────────────────────────────
    print("\n🛠  SKILLS")
    skills_raw = _ask("  List your skills (comma-separated, e.g. Python, Excel, Sales): ", "")
    skills = [s.strip().lower() for s in skills_raw.split(",") if s.strip()]

    # ── Experience ───────────────────────────────────────────────────────────
    print("\n💼  EXPERIENCE")
    years_exp = _ask_int("  Years of experience (0 = fresher/student): ", 0)
    fresher_mode = years_exp == 0
    if fresher_mode:
        print("  ✅  Fresher mode enabled — internship & entry-level jobs will be prioritised.")

    # ── Job target ───────────────────────────────────────────────────────────
    print("\n🎯  JOB TARGET")
    job_keyword = _ask("  Job title / keyword (e.g. accountant, nurse, python developer): ", "software engineer")

    preferred_location = _ask("  Preferred location (city, or leave blank for any): ", "")

    remote_ans = _ask_choice("  Are you open to remote work?", ["yes", "no"], "yes")
    remote_ok = remote_ans == "yes"

    # ── Freshness ────────────────────────────────────────────────────────────
    print("\n📅  FRESHNESS FILTER")
    print("  Show jobs posted within the last …")
    freshness_map = {"1": 1, "3": 3, "7": 7, "30": 30}
    while True:
        days_str = _ask("  Days [1 / 3 / 7 / 30]: ", "7")
        if days_str in freshness_map:
            freshness_days = freshness_map[days_str]
            break
        print("  ⚠  Enter 1, 3, 7, or 30.")

    profile = {
        "education_level": education_level,
        "degree_field": degree_field,
        "skills": skills,
        "years_experience": years_exp,
        "fresher_mode": fresher_mode,
        "job_keyword": job_keyword,
        "preferred_location": preferred_location,
        "remote_ok": remote_ok,
        "freshness_days": freshness_days,
    }

    print("\n" + "─" * 60)
    print("  ✅  Profile captured. Starting job search …")
    print("─" * 60 + "\n")
    return profile


if __name__ == "__main__":
    import json
    p = collect_profile()
    print(json.dumps(p, indent=2))
