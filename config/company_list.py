# config/company_list.py
# Company domains for direct career-page crawling
# Add more entries freely — the crawler handles discovery automatically.

COMPANY_LIST = [
    # Big Tech
    {"name": "Google",        "domain": "https://careers.google.com",        "path": "/jobs/results/"},
    {"name": "Microsoft",     "domain": "https://careers.microsoft.com",      "path": "/us/en/search-results"},
    {"name": "Amazon",        "domain": "https://www.amazon.jobs",            "path": "/en/search"},
    {"name": "Meta",          "domain": "https://www.metacareers.com",        "path": "/jobs"},
    {"name": "Apple",         "domain": "https://jobs.apple.com",             "path": "/en-us/search"},

    # Indian IT Giants
    {"name": "TCS",           "domain": "https://ibegin.tcs.com",            "path": "/jobs"},
    {"name": "Infosys",       "domain": "https://career.infosys.com",        "path": "/jobdescription"},
    {"name": "Wipro",         "domain": "https://careers.wipro.com",         "path": "/careers/jobs"},
    {"name": "Accenture",     "domain": "https://www.accenture.com",         "path": "/us-en/careers/jobsearch"},
    {"name": "HCL",           "domain": "https://www.hcltech.com",           "path": "/careers/job-listings"},

    # Consulting
    {"name": "Deloitte",      "domain": "https://apply.deloitte.com",        "path": "/careers/SearchJobs"},
    {"name": "McKinsey",      "domain": "https://www.mckinsey.com",          "path": "/careers/search-jobs"},
    {"name": "PwC",           "domain": "https://jobs.pwc.com",              "path": "/search"},

    # E-Commerce / Startups
    {"name": "Flipkart",      "domain": "https://www.flipkartcareers.com",   "path": "/jobs"},
    {"name": "Zomato",        "domain": "https://www.zomato.com",            "path": "/careers"},
    {"name": "Swiggy",        "domain": "https://careers.swiggy.com",       "path": "/"},

    # Finance
    {"name": "HDFC Bank",     "domain": "https://www.hdfcbank.com",         "path": "/content/bbp/repositories/723fb80a-2dde-42a3-9793-7ae1be57c87f"},
    {"name": "JP Morgan",     "domain": "https://careers.jpmorgan.com",     "path": "/careers/jobs"},
]

# Auto-detect career page paths (tried in order)
CAREER_PATH_CANDIDATES = [
    "/careers",
    "/jobs",
    "/careers/jobs",
    "/join-us",
    "/work-with-us",
    "/about/careers",
    "/en/careers",
    "/company/careers",
    "/opportunities",
    "/open-positions",
]
