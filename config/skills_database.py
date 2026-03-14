# config/skills_database.py
# Master skill database covering multiple industries

SKILLS_DATABASE = {
    # ── Technology ──────────────────────────────────────────────────────────
    "tech": [
        "python", "java", "javascript", "typescript", "c++", "c#", "golang", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "spring", "express", "next.js", "nuxt",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "git", "ci/cd", "jenkins", "github actions", "linux", "bash",
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "data analysis", "data science", "big data", "spark", "hadoop",
        "rest api", "graphql", "microservices", "devops", "agile", "scrum",
        "cybersecurity", "networking", "cloud computing", "sap", "salesforce",
    ],

    # ── Finance & Accounting ─────────────────────────────────────────────────
    "finance": [
        "accounting", "bookkeeping", "financial analysis", "auditing", "taxation",
        "tally", "quickbooks", "xero", "sap fi", "oracle financials",
        "gst", "ifrs", "gaap", "budget forecasting", "cost accounting",
        "accounts payable", "accounts receivable", "payroll", "reconciliation",
        "investment analysis", "equity research", "portfolio management",
        "financial modelling", "valuation", "risk management", "derivatives",
        "banking", "credit analysis", "loan processing", "kyd", "aml",
        "excel", "power bi", "tableau", "bloomberg", "reuters",
    ],

    # ── Marketing & Sales ────────────────────────────────────────────────────
    "marketing": [
        "digital marketing", "seo", "sem", "social media marketing",
        "content marketing", "email marketing", "ppc", "google ads",
        "facebook ads", "instagram", "linkedin marketing", "influencer marketing",
        "brand management", "market research", "consumer insights",
        "crm", "hubspot", "salesforce crm", "zoho crm",
        "sales", "business development", "lead generation", "cold calling",
        "b2b sales", "b2c sales", "account management", "negotiation",
        "copywriting", "content writing", "adobe analytics", "google analytics",
    ],

    # ── Healthcare & Medical ─────────────────────────────────────────────────
    "healthcare": [
        "nursing", "patient care", "clinical research", "pharmacology",
        "medical coding", "icd-10", "cpt coding", "ehr", "emr",
        "phlebotomy", "radiology", "laboratory", "pathology",
        "first aid", "bls", "acls", "cpr", "surgery assistance",
        "public health", "epidemiology", "health informatics",
        "medical writing", "regulatory affairs", "clinical trials",
        "physical therapy", "occupational therapy", "psychology",
    ],

    # ── HR & Administration ──────────────────────────────────────────────────
    "hr": [
        "recruitment", "talent acquisition", "onboarding", "hrms",
        "performance management", "employee relations", "payroll management",
        "labor law", "compliance", "training and development",
        "organizational development", "succession planning",
        "workday", "bamboohr", "sap hr", "oracle hcm",
        "microsoft office", "data entry", "administrative support",
        "office management", "calendar management", "travel coordination",
    ],

    # ── Design & Creative ────────────────────────────────────────────────────
    "design": [
        "ui design", "ux design", "graphic design", "web design",
        "adobe photoshop", "adobe illustrator", "adobe xd", "figma",
        "sketch", "invision", "prototyping", "wireframing",
        "video editing", "after effects", "premiere pro", "final cut pro",
        "motion graphics", "animation", "3d modeling", "blender",
        "photography", "brand identity", "typography", "color theory",
    ],

    # ── Operations & Logistics ───────────────────────────────────────────────
    "operations": [
        "supply chain", "logistics", "warehouse management", "inventory control",
        "procurement", "vendor management", "lean", "six sigma",
        "project management", "pmp", "prince2", "ms project",
        "quality assurance", "quality control", "iso", "process improvement",
        "erp", "sap mm", "oracle scm", "jira", "confluence",
        "operations management", "facility management", "fleet management",
    ],

    # ── Education & Training ─────────────────────────────────────────────────
    "education": [
        "teaching", "curriculum development", "lesson planning",
        "e-learning", "lms", "moodle", "blackboard",
        "student counselling", "academic advising", "research",
        "academic writing", "grant writing", "instructional design",
    ],

    # ── Legal ────────────────────────────────────────────────────────────────
    "legal": [
        "legal research", "contract drafting", "litigation",
        "corporate law", "intellectual property", "compliance",
        "mergers and acquisitions", "due diligence", "legal writing",
        "paralegal", "case management", "westlaw", "lexisnexis",
    ],

    # ── Soft Skills ──────────────────────────────────────────────────────────
    "soft_skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "critical thinking", "time management", "adaptability",
        "customer service", "presentation", "multitasking",
        "attention to detail", "analytical skills", "decision making",
    ],
}

# Flat list for quick membership checks
ALL_SKILLS = sorted({skill for skills in SKILLS_DATABASE.values() for skill in skills})


def get_skills_for_keyword(keyword: str) -> list[str]:
    """Return the most relevant skill subset for a given job keyword."""
    keyword = keyword.lower()
    mapping = {
        ("python", "developer", "engineer", "software", "data", "ml", "ai",
         "devops", "cloud", "backend", "frontend", "fullstack"): "tech",
        ("account", "finance", "audit", "tax", "banking", "investment"): "finance",
        ("marketing", "sales", "seo", "brand", "content", "digital"): "marketing",
        ("nurse", "doctor", "medical", "clinical", "health", "pharma"): "healthcare",
        ("hr", "human resource", "recruiter", "talent", "admin"): "hr",
        ("design", "ui", "ux", "graphic", "creative", "video"): "design",
        ("operations", "supply chain", "logistics", "warehouse", "quality"): "operations",
        ("teach", "education", "tutor", "training", "instructor"): "education",
        ("legal", "law", "compliance", "contract", "paralegal"): "legal",
    }
    for keys, category in mapping.items():
        if any(k in keyword for k in keys):
            return SKILLS_DATABASE.get(category, []) + SKILLS_DATABASE["soft_skills"]
    return ALL_SKILLS  # return everything if no match
