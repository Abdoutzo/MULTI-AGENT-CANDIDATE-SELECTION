"""
Job description parsing: reads TXT/PDF offers, extracts a lightweight structured JSON,
and mirrors the CV preprocessing pipeline (listing files under DATA/jobs, saving JSON/CSV in DATA/processed).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from src.utils.data_utils import (
    DATA_DIR,
    PROCESSED_DIR,
    build_candidate_id,
    clean_text,
    extract_text,
)

# Directories for job descriptions
JOBS_DIR = DATA_DIR / "jobs"
JOBS_PARSED_DIR = PROCESSED_DIR / "jobs_parsed"
JOBS_PARSED_DIR.mkdir(parents=True, exist_ok=True)

# Common section headings in job descriptions (en/fr)
SECTION_TOKENS = {
    "responsibilities": [
        "responsibilities",
        "missions",
        "responsabilites",
        "responsabilités",
        "votre rôle",
        "votre role",
        "vos missions",
    ],
    "requirements": [
        "requirements",
        "profil",
        "requis",
        "qualifications",
        "prerequis",
        "prérequis",
    ],
    "skills": [
        "skills",
        "competences",
        "compétences",
        "competences techniques",
        "hard skills",
        "technical skills",
        "compétences requises",
        "compétences clés",
    ],
    "soft_skills": ["soft skills", "qualites", "qualités humaines", "savoir être", "savoir-être"],
    "benefits": ["benefits", "avantages", "perks"],
    "company": ["about us", "a propos", "à propos", "a propos de nous", "company"],
}


def _inject_newlines_for_headings(text: str) -> str:
    updated = text
    for tokens in SECTION_TOKENS.values():
        for token in tokens:
            pattern = rf"(?i)\b({re.escape(token)})\b"
            updated = re.sub(pattern, r"\n\1\n", updated)
    return updated


def _detect_section_name(line: str) -> str | None:
    norm = line.lower().strip(" :-\t")
    for name, tokens in SECTION_TOKENS.items():
        for tok in tokens:
            if norm.startswith(tok.lower()):
                return name
    return None


def _split_sections(text: str) -> Dict[str, str]:
    text = _inject_newlines_for_headings(text)
    sections: Dict[str, List[str]] = {}
    current: str | None = None

    for line in text.splitlines():
        if not line.strip():
            continue
        sec = _detect_section_name(line)
        if sec:
            current = sec
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_numbers(desc: str, patterns: List[str]) -> List[int]:
    nums = []
    for pat in patterns:
        for m in re.finditer(pat, desc):
            try:
                nums.append(int(m.group(1)))
            except ValueError:
                continue
    return nums


def parse_job_description_text(text: str) -> Dict[str, Any]:
    """
    Parse raw job description text into a structured dict.
    """
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned = clean_text(text)
    lowered = cleaned.lower()
    sections = _split_sections(cleaned)

    # Experience: take the minimum found
    exp_years = _extract_numbers(lowered, [r"(\d+)\s*ans? d[' ]exp", r"(\d+)\s*years?"])
    exp_min = min(exp_years) if exp_years else None

    # Salary: approximate if numbers are present
    salaire_matches = _extract_numbers(lowered, [r"(\d{2,3})\s*k", r"(\d{2,3})\s*ke", r"(\d+)\s*euros"])
    salaire_min = min(salaire_matches) * 1000 if salaire_matches else None
    salaire_max = max(salaire_matches) * 1000 if salaire_matches else None

    # Contract type
    contrat = ""
    if "cdi" in lowered:
        contrat = "CDI"
    elif "cdd" in lowered:
        contrat = "CDD"
    elif "stage" in lowered or "intern" in lowered:
        contrat = "Stage"
    elif "alternance" in lowered or "apprentissage" in lowered:
        contrat = "Alternance"
    elif "freelance" in lowered or "indep" in lowered or "independant" in lowered:
        contrat = "Freelance"

    # Location
    m_lieu = re.search(
        r"(paris|lyon|lille|nantes|bordeaux|remote|teletravail|télétravail|idf|ile-de-france|levallois(?:-|\\s)?perret)",
        lowered,
    )
    lieu = m_lieu.group(1) if m_lieu else ""

    # Languages
    langues = []
    if "anglais" in lowered or "english" in lowered:
        langues.append("anglais")
    if "francais" in lowered or "français" in lowered or "french" in lowered:
        langues.append("francais")
    if "espagnol" in lowered or "spanish" in lowered:
        langues.append("espagnol")
    if "allemand" in lowered or "german" in lowered:
        langues.append("allemand")

    # Job title heuristic: scan raw lines for role keywords, fallback first raw line
    titre = ""
    role_keywords = [
        "engineer",
        "developer",
        "manager",
        "analyst",
        "designer",
        "scientist",
        "lead",
        "architect",
        "owner",
        "intern",
        "stagiaire",
        "logistique",
        "supply chain",
        "performance",
        "projet",
    ]
    for line in raw_lines:
        low = line.lower()
        if any(k in low for k in role_keywords):
            titre = line.strip()
            break
    if not titre and raw_lines:
        titre = raw_lines[0]
    if len(titre) > 200:
        titre = titre[:200]

    # Skills list heuristic: split bullets "•"/\u2022 or newlines from skills section
    skills_list: List[str] = []
    skills_section = sections.get("skills", "")
    bullet_sep_pattern = r"[•\u2022\n]"
    if skills_section:
        for bullet in re.split(bullet_sep_pattern, skills_section):
            b = bullet.strip(" :-\t")
            if len(b) < 3:
                continue
            if b.lower().startswith(("que vous", "dont vous", "si vous pensez")):
                continue
            if b not in skills_list:
                skills_list.append(b)

    return {
        "job_title": titre,
        "raw_text": cleaned,
        "sections": sections,
        "skills_list": skills_list,
        "exp_min": exp_min,
        "exp_max": None,
        "salaire_min": salaire_min,
        "salaire_max": salaire_max,
        "contrat": contrat,
        "lieu": lieu,
        "langues": langues,
    }


def parse_job_description_file(path: Path) -> Dict[str, Any]:
    """
    Read a job description file (txt/pdf) and return structured JSON-ready dict.
    """
    raw_text = extract_text(path)
    parsed = parse_job_description_text(raw_text)
    job_id = build_candidate_id(path)
    parsed["job_id"] = job_id
    parsed["source_file"] = str(path.relative_to(DATA_DIR.parent))
    return parsed


# --- Pipeline: list offers under DATA/jobs and save processed outputs --------

def list_job_files(extensions: tuple = (".txt", ".pdf")) -> List[Path]:
    if not JOBS_DIR.exists():
        return []
    return [
        p for p in JOBS_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions
    ]


def save_job_json(job: Dict[str, Any]) -> Path:
    out = JOBS_PARSED_DIR / f"{job['job_id']}.json"
    out.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def save_jobs_csv(jobs: List[Dict[str, Any]]) -> Path:
    csv_path = PROCESSED_DIR / "jobs.csv"
    fieldnames = [
        "job_id",
        "source_file",
        "job_title",
        "exp_min",
        "exp_max",
        "salaire_min",
        "salaire_max",
        "contrat",
        "lieu",
        "langues",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            row = {k: job.get(k, "") for k in fieldnames}
            writer.writerow(row)
    return csv_path


def preprocess_all_jobs() -> List[Dict[str, Any]]:
    print(f"[INFO] Chemin JOBS : {JOBS_DIR}")
    files = list_job_files()
    if not files:
        print("[INFO] Aucun fichier d'offre trouvé.")
        return []

    print(f"[INFO] {len(files)} offre(s) trouvée(s).")
    jobs: List[Dict[str, Any]] = []
    for p in files:
        job = parse_job_description_file(p)
        save_job_json(job)
        jobs.append(job)
        print(f"[OK] {p.name} -> {job['job_id']}")

    save_jobs_csv(jobs)
    print("[INFO] CSV généré.")
    print(f"[INFO] JSON générés dans : {JOBS_PARSED_DIR}")
    return jobs
