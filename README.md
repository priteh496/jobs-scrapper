# 🤖 Local AI Job Intelligence Agent

A fully local, no-API, Python-powered job scraping and matching system.
Scrapes Indeed, Internshala, and Wellfound — then scores every job against your profile.

---

## 📁 Project Structure

```
job_agent/
├── main.py                    ← Entry point
├── profile_input.py           ← Collects your profile
├── job_collector.py           ← Orchestrates all steps
├── requirements.txt
│
├── scrapers/
│   ├── indeed_scraper.py
│   ├── internshala_scraper.py
│   └── wellfound_scraper.py
│
├── parser/
│   └── description_parser.py  ← Rule-based NLP
│
├── engine/
│   ├── job_scorer.py          ← Scoring engine
│   ├── freshness_filter.py    ← Date filter
│   └── duplicate_filter.py    ← Deduplication
│
├── export/
│   └── csv_writer.py
│
└── output/
    └── jobs.csv               ← Generated output
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- pip

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the agent
```bash
python main.py
```

---

## 💻 Example Terminal Session

```
══════════════════════════════════════════════════════
   🤖  LOCAL AI JOB INTELLIGENCE AGENT  🤖
══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
       LOCAL AI JOB INTELLIGENCE AGENT
═══════════════════════════════════════════════════════
Please fill in your profile to find the best jobs.

Education levels: high_school | bachelor | master | phd | diploma
Your highest education level: bachelor

Your skills (comma-separated, e.g. python, sql, excel): python, sql, pandas, tableau

Years of experience (enter 0 if fresher): 1

Preferred job location (city/country, e.g. Mumbai): Bangalore

Are you open to remote jobs? (yes/no): yes

Freshness filter options: 1 | 3 | 7 | 30 (days)
Show jobs posted within how many days? [7]: 7

Job title or keyword to search (e.g. Data Analyst): Data Analyst

🔍 Scraping job sources...
  → Indeed...    found 18 jobs
  → Internshala... found 12 jobs
  → Wellfound...   found 9 jobs

📦 Total raw jobs collected: 39
🧹 After deduplication: 31 jobs
📅 After freshness filter (7 days): 28 jobs

🤖 Analyzing 28 job descriptions (this may take a minute)...
   Analyzed 28/28 jobs...

📊 Scoring jobs...

🏆 Top score: 145

──────────────────────────────────────────────────────
RANK  SCORE   TITLE                               COMPANY                   SOURCE
──────────────────────────────────────────────────────
1     145     Data Analyst                        Infosys                   Indeed
2     130     Junior Data Analyst                 TCS                       Internshala
3     125     Data Analyst - Remote               Razorpay                  Wellfound
4     115     Business Analyst                    Wipro                     Indeed
5     110     Data Analyst Intern                 PhonePe                   Internshala
...
──────────────────────────────────────────────────────

✅ Full results exported to: output/jobs.csv
   Total jobs found: 28
```

---

## 📊 Example CSV Output

| title | company | location | experience | skills | education | role_level | score | posting_date | source | apply_link |
|-------|---------|----------|------------|--------|-----------|------------|-------|-------------|--------|-----------|
| Data Analyst | Infosys | Bangalore | 1-3 years | python, sql, pandas | bachelor | junior | 145 | 2024-05-10 | Indeed | https://... |
| Junior Data Analyst | TCS | Remote | 0-2 years | sql, excel | bachelor | junior | 130 | 2024-05-09 | Internshala | https://... |

---

## 🔧 Configuration

### Adjust scoring weights
Edit `engine/job_scorer.py` — each rule is clearly documented.

### Add more skills to detect
Edit the `SKILLS_DB` list in `parser/description_parser.py`.

### Change number of pages scraped
Edit `MAX_JOBS_PER_SOURCE` in `job_collector.py`.

### Enable debug logging
```bash
LOG_LEVEL=DEBUG python main.py
```

---

## ⚠️ Important Notes

- **Web scraping**: Job websites may change their HTML structure. If a scraper returns 0 results, the site's layout may have been updated.
- **Rate limiting**: Random delays are built in to avoid getting blocked. Do not reduce them aggressively.
- **JavaScript-heavy sites**: Wellfound and some Indeed pages render via JavaScript. Static scraping may return fewer results. Consider adding Selenium for those sources if needed.
- **No API keys required**: This project is 100% local and offline-capable (except for fetching live job pages).

---

## 🛠 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `0 jobs found` | Site structure may have changed; check logs |
| Slow execution | Reduce `MAX_JOBS_PER_SOURCE` in `job_collector.py` |
| CSV not created | Check write permissions on `output/` directory |
