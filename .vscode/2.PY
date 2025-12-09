"""
Utilitaires pour la gestion des données candidats.

- Parcours des fichiers bruts dans DATA/raw
- Extraction de texte (.txt et .pdf)
- Nettoyage du texte
- Sauvegarde en JSON dans DATA/processed/parsed
- Construction d'un CSV simple (candidates.csv)
"""

from pathlib import Path
from typing import List, Dict
import json
import re
import csv

# Localisation du dossier DATA à partir du repo
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../MULTI-AGENT-CANDIDATE-SELECTION
DATA_DIR = REPO_ROOT / "DATA"

# ⚠️ attention : dossiers en minuscules, comme dans ta capture VS Code
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = PROCESSED_DIR / "parsed"

# On crée les dossiers si besoin
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)


def list_raw_files(extensions: tuple = (".txt", ".pdf")) -> List[Path]:
    """
    Liste tous les fichiers bruts dans DATA/raw avec les extensions données.
    """
    files: List[Path] = []

    if not RAW_DIR.exists():
        # Normalement on ne passe plus ici car on le crée plus haut,
        # mais on garde un message clair au cas où.
        print(f"Le dossier RAW n'existe pas, il a été créé : {RAW_DIR}")
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        return []

    for path in RAW_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            files.append(path)
    return files


def _extract_text_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_text_pdf(path: Path) -> str:
    """
    Extraction simple de texte depuis un PDF.
    Nécessite pdfplumber installé : pip install pdfplumber
    """
    try:
        import pdfplumber  # type: ignore
    except ImportError as e:
        raise ImportError(
            "Le module pdfplumber est requis pour lire les PDF. "
            "Installe-le avec : pip install pdfplumber"
        ) from e

    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text(path: Path) -> str:
    """
    Routeur selon le type de fichier.
    """
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return _extract_text_txt(path)
    if suffix == ".pdf":
        return _extract_text_pdf(path)
    raise ValueError(f"Type de fichier non supporté pour {path}")


def clean_text(text: str) -> str:
    """
    Nettoyage minimal du texte :
    - suppression des \r
    - normalisation des sauts de ligne
    - réduction des espaces multiples
    """
    text = text.replace("\r", " ")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def build_candidate_id(path: Path) -> str:
    """
    Construit un identifiant de candidat à partir du nom de fichier.
    Exemple : 'CV_Dupont_Jean.pdf' -> 'cv_dupont_jean'
    """
    return re.sub(r"[^a-z0-9_]+", "_", path.stem.lower()).strip("_")


def parse_raw_file(path: Path) -> Dict:
    """
    Lit un fichier brut, extrait et nettoie le texte,
    renvoie un dict représentant un candidat.
    """
    raw_text = extract_text(path)
    cleaned = clean_text(raw_text)
    candidate_id = build_candidate_id(path)

    return {
        "id": candidate_id,
        "source_file": str(path.relative_to(REPO_ROOT)),
        "raw_text": cleaned,
        "n_chars": len(cleaned),
        "n_words": len(cleaned.split()),
    }


def save_candidate_json(candidate: Dict) -> Path:
    """
    Sauvegarde un candidat au format JSON dans DATA/processed/parsed.
    """
    out_path = PARSED_DIR / f"{candidate['id']}.json"
    out_path.write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def save_candidates_csv(candidates: List[Dict]) -> Path:
    """
    Sauvegarde un CSV simple avec les infos de base des candidats.
    """
    csv_path = PROCESSED_DIR / "candidates.csv"
    fieldnames = ["id", "source_file", "n_chars", "n_words"]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cand in candidates:
            writer.writerow({k: cand[k] for k in fieldnames})

    return csv_path


def preprocess_all_raw() -> List[Dict]:
    """
    Pipeline complet :
    - liste les fichiers RAW
    - parse chacun
    - sauvegarde JSON individuels
    - sauvegarde un CSV récapitulatif
    """
    raw_files = list_raw_files()
    if not raw_files:
        print(f"Aucun fichier brut trouvé dans {RAW_DIR}")
        return []

    candidates: List[Dict] = []
    for path in raw_files:
        try:
            candidate = parse_raw_file(path)
            save_candidate_json(candidate)
            candidates.append(candidate)
            print(f"[OK] {path.name} -> id={candidate['id']}")
        except Exception as e:  # pragma: no cover
            print(f"[ERREUR] Impossible de traiter {path}: {e}")

    save_candidates_csv(candidates)
    print(f"\nPrétraitement terminé. {len(candidates)} candidats traités.")
    return candidates


if __name__ == "__main__":
    # Permet de lancer directement : python -m src.utils.data_utils
    preprocess_all_raw()
