from pathlib import Path
from typing import List, Dict
import json
import re
import csv

from src.utils.parsing import parse_cv_text

# 📌 Chemins du projet
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "DATA"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = PROCESSED_DIR / "parsed"

# 📌 Création dossiers si besoin
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)


def list_raw_files(extensions: tuple = (".txt", ".pdf")) -> List[Path]:
    if not RAW_DIR.exists():
        return []
    return [
        p for p in RAW_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions
    ]


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() == ".pdf":
        import pdfplumber
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts)

    return ""


def clean_text(text: str) -> str:
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_candidate_id(path: Path) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", path.stem.lower()).strip("_")


def parse_raw_file(path: Path) -> Dict:
    text = extract_text(path)
    cleaned = clean_text(text)
    cid = build_candidate_id(path)

def parse_raw_file(path: Path) -> Dict:
    """
    Lit un fichier brut, extrait et nettoie le texte,
    renvoie un dict représentant un candidat enrichi.
    """
    raw_text = extract_text(path)
    cleaned = clean_text(raw_text)
    candidate_id = build_candidate_id(path)

    # 🔹 Parsing intelligent : compétences, expérience, formation, etc.
    parsed_struct = parse_cv_text(cleaned)

    base = {
        "id": candidate_id,
        "source_file": str(path.relative_to(REPO_ROOT)),
        "raw_text": cleaned,
        "n_chars": len(cleaned),
        "n_words": len(cleaned.split()),
    }

    # On ajoute les champs extraits (email, skills_list, experience_text, etc.)
    base.update(parsed_struct)
    return base




def save_candidate_json(cand: Dict) -> Path:
    out = PARSED_DIR / f"{cand['id']}.json"
    out.write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def save_candidates_csv(candidates: List[Dict]) -> Path:
    """
    Sauvegarde un CSV simple avec les infos de base des candidats + quelques champs utiles.
    """
    csv_path = PROCESSED_DIR / "candidates.csv"

    fieldnames = [
        "id",
        "source_file",
        "n_chars",
        "n_words",
        "email",
        "phone",
        "skills_text",
        "experience_text",
        "education_text",
        # si tu veux : "languages_text"
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cand in candidates:
            row = {k: cand.get(k, "") for k in fieldnames}
            writer.writerow(row)

    return csv_path



def preprocess_all_raw() -> List[Dict]:
    print(f"[INFO] Chemin RAW : {RAW_DIR}")
    files = list_raw_files()

    if not files:
        print("[INFO] Aucun fichier brut trouvé.")
        return []

    print(f"[INFO] {len(files)} fichier(s) trouvé(s).")

    cands: List[Dict] = []

    for p in files:
        cand = parse_raw_file(p)
        save_candidate_json(cand)
        cands.append(cand)
        print(f"[OK] {p.name} → {cand['id']}")

    save_candidates_csv(cands)
    print("[INFO] CSV généré 👍")
    print(f"[INFO] JSON générés dans : {PARSED_DIR}")

    return cands
