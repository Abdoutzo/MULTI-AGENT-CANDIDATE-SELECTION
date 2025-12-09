"""Calcul des scores multi-critères (profil, technique, soft skills)."""
from typing import Dict, List, Set
import re


def calculate_skill_match_score(
    candidate_skills: List[str],
    required_skills: List[str],
    optional_skills: List[str] = None
) -> float:
    """
    Calcule un score de matching des compétences (0-100).
    
    Args:
        candidate_skills: Liste des compétences du candidat
        required_skills: Compétences obligatoires
        optional_skills: Compétences optionnelles
    
    Returns:
        Score entre 0 et 100
    """
    optional_skills = optional_skills or []
    
    # Normalisation
    candidate_set = {s.lower().strip() for s in candidate_skills}
    required_set = {s.lower().strip() for s in required_skills}
    optional_set = {s.lower().strip() for s in optional_skills}
    
    if not required_set:
        return 50.0  # Si aucune compétence requise, score neutre
    
    # Score pour compétences obligatoires (70% du score)
    matched_required = len(candidate_set & required_set)
    required_score = (matched_required / len(required_set)) * 70 if required_set else 0
    
    # Score pour compétences optionnelles (30% du score)
    matched_optional = len(candidate_set & optional_set)
    optional_score = (matched_optional / len(optional_set)) * 30 if optional_set else 0
    
    total_score = required_score + optional_score
    return min(100.0, max(0.0, total_score))


def calculate_experience_score(
    candidate_years: int,
    required_min: int = None,
    required_max: int = None
) -> float:
    """
    Calcule un score basé sur l'expérience (0-100).
    
    Args:
        candidate_years: Années d'expérience du candidat
        required_min: Expérience minimale requise
        required_max: Expérience maximale requise
    
    Returns:
        Score entre 0 et 100
    """
    if required_min is None:
        return 50.0  # Score neutre si pas de critère
    
    if candidate_years < required_min:
        # Pénalité si en dessous du minimum
        return max(0.0, 50.0 - (required_min - candidate_years) * 10)
    
    if required_max and candidate_years > required_max:
        # Légère pénalité si trop d'expérience (surqualifié)
        excess = candidate_years - required_max
        return max(70.0, 100.0 - excess * 5)
    
    # Score optimal si dans la fourchette
    return 100.0


def calculate_language_match_score(
    candidate_languages: List[str],
    required_languages: List[str]
) -> float:
    """
    Calcule un score de matching des langues (0-100).
    """
    if not required_languages:
        return 100.0
    
    candidate_set = {lang.lower().strip() for lang in candidate_languages}
    required_set = {lang.lower().strip() for lang in required_languages}
    
    matched = len(candidate_set & required_set)
    return (matched / len(required_set)) * 100 if required_set else 0.0


def calculate_profile_score(
    candidate: Dict,
    job_profile: Dict
) -> float:
    """
    Calcule un score global de profil (0-100).
    
    Combine:
    - Matching des compétences (50%)
    - Expérience (30%)
    - Langues (20%)
    """
    # Compétences
    candidate_skills = candidate.get("skills_list", [])
    required_skills = job_profile.get("skills_obligatoires", [])
    optional_skills = job_profile.get("skills_optionnelles", [])
    
    skill_score = calculate_skill_match_score(
        candidate_skills, required_skills, optional_skills
    )
    
    # Expérience
    candidate_exp = candidate.get("years_experience", 0)
    required_exp_min = job_profile.get("exp_min")
    required_exp_max = job_profile.get("exp_max")
    
    exp_score = calculate_experience_score(
        candidate_exp, required_exp_min, required_exp_max
    )
    
    # Langues
    candidate_langs = candidate.get("languages_text", "").split(",") if candidate.get("languages_text") else []
    required_langs = job_profile.get("langues", [])
    
    lang_score = calculate_language_match_score(candidate_langs, required_langs)
    
    # Pondération
    total_score = (
        skill_score * 0.5 +
        exp_score * 0.3 +
        lang_score * 0.2
    )
    
    return min(100.0, max(0.0, total_score))


def calculate_technical_score(
    candidate_skills: List[str],
    required_technical_skills: List[str]
) -> float:
    """
    Calcule un score technique spécifique (0-100).
    """
    return calculate_skill_match_score(
        candidate_skills,
        required_technical_skills,
        []
    )


def calculate_soft_skills_score(
    motivation_text: str,
    experience_text: str = "",
    keywords: List[str] = None
) -> float:
    """
    Calcule un score basé sur les soft skills détectés dans le texte (0-100).
    
    Analyse:
    - Mots-clés de soft skills dans la lettre de motivation
    - Ton et structure du texte
    - Indicateurs de motivation
    """
    keywords = keywords or []
    
    if not motivation_text:
        return 50.0  # Score neutre si pas de lettre
    
    text_lower = (motivation_text + " " + experience_text).lower()
    
    # Soft skills communs
    soft_skills_keywords = {
        'teamwork': ['équipe', 'collaboration', 'teamwork', 'collaborer'],
        'communication': ['communication', 'communiquer', 'présenter', 'expliquer'],
        'leadership': ['lead', 'leader', 'diriger', 'management', 'gérer'],
        'autonomy': ['autonome', 'autonomie', 'indépendant', 'indépendance'],
        'problem_solving': ['résoudre', 'solution', 'problème', 'challenge'],
        'adaptability': ['adaptable', 'flexible', 'changement', 'évolution'],
        'motivation': ['motivé', 'motivation', 'passion', 'intéressé', 'enthousiaste'],
    }
    
    # Compter les occurrences
    detected_skills = set()
    for skill_type, terms in soft_skills_keywords.items():
        for term in terms:
            if term in text_lower:
                detected_skills.add(skill_type)
                break
    
    # Score de base basé sur le nombre de soft skills détectés
    base_score = (len(detected_skills) / len(soft_skills_keywords)) * 60
    
    # Bonus pour mots-clés spécifiques du recruteur
    keyword_bonus = 0
    if keywords:
        matched_keywords = sum(1 for kw in keywords if kw.lower() in text_lower)
        keyword_bonus = (matched_keywords / len(keywords)) * 40 if keywords else 0
    
    # Bonus pour longueur et structure (indicateur d'effort)
    length_bonus = min(10, len(motivation_text.split()) / 50)
    
    total_score = base_score + keyword_bonus + length_bonus
    return min(100.0, max(0.0, total_score))
