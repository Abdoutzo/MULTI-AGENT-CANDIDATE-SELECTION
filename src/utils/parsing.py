"""
Outils de parsing "intelligent" de CV à partir de texte brut.

Objectif : à partir de raw_text, extraire :
- sections (skills / experience / education / languages)
- liste de compétences (skills_list)
- email, téléphone
"""

from __future__ import annotations

from typing import Dict, List
import re

# --- Définition des tokens de sections ---------------------------------------

SECTION_TOKENS = {
    "skills": ["compétences", "skills", "compétences techniques", "technical skills"],
    "experience": ["expérience professionnelle", "expériences", "experience", "work experience"],
    "education": ["formation", "éducation", "education", "studies"],
    "languages": ["langues", "languages"],
}

# --- Helpers basiques --------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalisation simple pour la détection de sections."""
    return text.lower()


def _extract_email(text: str) -> str:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    # Très simple, à raffiner au besoin
    match = re.search(r"(?:\+?\d[\d .-]{7,}\d)", text)
    return match.group(0) if match else ""


def _inject_newlines_for_headings(text: str) -> str:
    """
    Insère des retours à la ligne autour des mots-clés de section
    pour faciliter la détection des sections dans les PDF où tout est collé.
    """
    updated = text
    for tokens in SECTION_TOKENS.values():
        for token in tokens:
            # (?i) = case-insensitive, \b = frontière de mot
            pattern = rf"(?i)\b({re.escape(token)})\b"
            # On met le titre sur une ligne seule
            updated = re.sub(pattern, r"\n\1\n", updated)
    return updated


# --- Détection de sections ---------------------------------------------------


SECTION_PATTERNS = {
    "skills": [
        r"^compétences?\b",
        r"^skills?\b",
        r"^compétences techniques\b",
        r"^technical skills?\b",
    ],
    "experience": [
        r"^expérience professionnelle\b",
        r"^expériences?\b",
        r"^experience\b",
        r"^work experience\b",
    ],
    "education": [
        r"^formation\b",
        r"^éducation\b",
        r"^education\b",
        r"^studies\b",
    ],
    "languages": [
        r"^langues?\b",
        r"^languages?\b",
    ],
}


def _detect_section_name(line: str) -> str | None:
    """Retourne le nom de section ('skills', 'experience', ...) si la ligne matche."""
    norm = _normalize(line).strip(" :-•\t")
    for section, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if re.match(pat, norm):
                return section
    return None


def split_into_sections(text: str) -> Dict[str, str]:
    """
    Découpe un CV brut en sections textuelles basées sur des titres.

    Retourne un dict : section_name -> texte complet de la section.
    """

    # 🔹 On insère des \n autour des titres (EXPERIENCE, EDUCATION, SKILLS, LANGUAGES, ...)
    text = _inject_newlines_for_headings(text)

    sections: Dict[str, List[str]] = {}
    current_section: str | None = None

    lines = text.splitlines()

    for line in lines:
        if not line.strip():
            continue

        sec_name = _detect_section_name(line)
        if sec_name is not None:
            current_section = sec_name
            if current_section not in sections:
                sections[current_section] = []
            continue

        if current_section is not None:
            sections[current_section].append(line)

    # On joint les lignes par section
    joined: Dict[str, str] = {
        name: "\n".join(content).strip()
        for name, content in sections.items()
    }
    return joined


# --- Parsing des compétences -------------------------------------------------


def parse_skills(skills_text: str) -> List[str]:
    """
    A partir d'un bloc de texte de compétences, renvoie une liste de compétences nettoyées.
    """
    if not skills_text:
        return []

    # On remplace les retours à la ligne par des virgules pour uniformiser
    tmp = skills_text.replace("\n", ",")
    raw_items = re.split(r"[;,•\u2022\-]\s*", tmp)
    cleaned: List[str] = []

    for item in raw_items:
        it = item.strip()
        if len(it) < 2:
            continue
        # On enlève des doublons simples
        if it not in cleaned:
            cleaned.append(it)

    return cleaned


# --- Fonction principale de parsing -----------------------------------------


def parse_cv_text(raw_text: str) -> Dict:
    """
    Prend un texte brut de CV et renvoie un dict avec :
    - email
    - phone
    - sections: skills_text, experience_text, education_text, languages_text
    - skills_list: liste des compétences
    """
    raw_text = raw_text or ""
    sections = split_into_sections(raw_text)

    skills_text = sections.get("skills", "")
    experience_text = sections.get("experience", "")
    education_text = sections.get("education", "")
    languages_text = sections.get("languages", "")

    skills_list = parse_skills(skills_text)

    email = _extract_email(raw_text)
    phone = _extract_phone(raw_text)

    return {
        "email": email,
        "phone": phone,
        "skills_text": skills_text,
        "skills_list": skills_list,
        "experience_text": experience_text,
        "education_text": education_text,
        "languages_text": languages_text,
    }
