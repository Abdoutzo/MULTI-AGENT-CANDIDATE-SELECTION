"""Prétraitement du texte (nettoyage, normalisation)."""
import re
from typing import List


def clean_text(text: str) -> str:
    """Nettoie et normalise le texte."""
    if not text:
        return ""
    
    # Remplace les retours chariot multiples par des espaces
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    
    # Supprime les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    # Supprime les caractères spéciaux indésirables (garde lettres, chiffres, ponctuation de base)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
    
    return text.strip()


def normalize_skill(skill: str) -> str:
    """Normalise une compétence (lowercase, suppression espaces)."""
    return skill.lower().strip()


def extract_years_of_experience(text: str) -> int:
    """Extrait le nombre d'années d'expérience depuis un texte."""
    patterns = [
        r'(\d+)\s*ans?\s*d[\' ]?exp',
        r'(\d+)\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*ans?',
        r'expérience\s*:\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return 0


def extract_education_level(text: str) -> str:
    """Extrait le niveau d'éducation depuis un texte."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['doctorat', 'phd', 'ph.d']):
        return 'doctorat'
    elif any(word in text_lower for word in ['master', 'm2', 'm1', 'msc', 'ms']):
        return 'master'
    elif any(word in text_lower for word in ['licence', 'bachelor', 'bsc', 'l3']):
        return 'licence'
    elif any(word in text_lower for word in ['bac', 'baccalauréat', 'high school']):
        return 'bac'
    
    return 'unknown'


def tokenize_text(text: str) -> List[str]:
    """Tokenise un texte en mots."""
    cleaned = clean_text(text)
    tokens = re.findall(r'\b\w+\b', cleaned.lower())
    return tokens


def remove_stopwords(tokens: List[str], custom_stopwords: List[str] = None) -> List[str]:
    """Supprime les mots vides."""
    default_stopwords = {
        'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que',
        'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas',
        'tout', 'plus', 'par', 'grand', 'en', 'une', 'ce', 'aux', 'de', 'des',
        'les', 'du', 'la', 'le', 'et', 'à', 'un', 'il', 'être', 'et', 'en',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    }
    
    stopwords = default_stopwords
    if custom_stopwords:
        stopwords.update(custom_stopwords)
    
    return [token for token in tokens if token not in stopwords]
