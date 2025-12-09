"""AgentProfil : évalue l'adéquation du profil du candidat."""
import json
from typing import Any, Dict, List, Optional
import re

from src.utils.parsing import parse_cv_text
from src.utils.preprocessing import extract_years_of_experience, extract_education_level
from src.utils.scoring import calculate_profile_score


class AgentProfil:
    """
    Agent qui analyse le profil d'un candidat à partir de son CV et lettre de motivation.
    
    Tâches:
    - Extraction d'infos (NER: nom, école, diplômes, expériences, dates)
    - Extraction/normalisation des compétences
    - Calcul d'un score global de matching profil ↔ offre
    """
    
    def __init__(self, llm: Any = None):
        """
        Args:
            llm: Modèle LLM optionnel pour extraction avancée
        """
        self.llm = llm
    
    def analyser_profil(
        self,
        cv_text: str,
        lettre_motivation: str = "",
        job_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyse le profil d'un candidat et retourne une structure enrichie.
        
        Args:
            cv_text: Texte brut du CV
            lettre_motivation: Texte de la lettre de motivation (optionnel)
            job_profile: Profil cible de l'offre (pour scoring)
        
        Returns:
            Dict avec:
            - profil_structuré: informations extraites
            - score_profil: score de matching (0-100)
            - commentaire: justification textuelle
        """
        # Parsing du CV
        parsed_cv = parse_cv_text(cv_text)
        
        # Extraction d'informations supplémentaires
        profil_structuré = self._enrichir_profil(parsed_cv, cv_text, lettre_motivation)
        
        # Calcul du score si profil cible fourni
        score_profil = 0.0
        commentaire = ""
        
        if job_profile:
            score_profil = calculate_profile_score(profil_structuré, job_profile)
            commentaire = self._generer_commentaire(profil_structuré, job_profile, score_profil)
        
        return {
            "profil_structuré": profil_structuré,
            "score_profil": score_profil,
            "commentaire": commentaire
        }
    
    def _enrichir_profil(
        self,
        parsed_cv: Dict,
        cv_text: str,
        lettre_motivation: str
    ) -> Dict[str, Any]:
        """Enrichit le profil avec des informations supplémentaires."""
        
        # Extraction années d'expérience
        years_exp = extract_years_of_experience(cv_text)
        
        # Extraction niveau d'éducation
        education_level = extract_education_level(parsed_cv.get("education_text", ""))
        
        # Extraction nom (première ligne souvent)
        nom = self._extract_name(cv_text)
        
        # Extraction diplômes
        diplomes = self._extract_diplomas(parsed_cv.get("education_text", ""))
        
        # Extraction expériences structurées
        experiences = self._extract_experiences(parsed_cv.get("experience_text", ""))
        
        # Compétences normalisées
        skills_list = [s.strip() for s in parsed_cv.get("skills_list", [])]
        
        profil = {
            "id": parsed_cv.get("id", ""),
            "nom": nom,
            "email": parsed_cv.get("email", ""),
            "phone": parsed_cv.get("phone", ""),
            "years_experience": years_exp,
            "education_level": education_level,
            "diplomes": diplomes,
            "experiences": experiences,
            "skills_list": skills_list,
            "skills_text": parsed_cv.get("skills_text", ""),
            "experience_text": parsed_cv.get("experience_text", ""),
            "education_text": parsed_cv.get("education_text", ""),
            "languages_text": parsed_cv.get("languages_text", ""),
            "lettre_motivation": lettre_motivation,
            "raw_cv_text": cv_text,
        }
        
        return profil
    
    def _extract_name(self, text: str) -> str:
        """Extrait le nom depuis le début du CV."""
        lines = text.split('\n')[:5]  # Premières lignes
        for line in lines:
            line = line.strip()
            # Pattern: nom en majuscules ou première ligne significative
            if len(line) > 3 and len(line) < 50:
                # Supprime les emails, téléphones
                if '@' not in line and not re.search(r'\d{10}', line):
                    return line
        return ""
    
    def _extract_diplomas(self, education_text: str) -> List[Dict[str, str]]:
        """Extrait les diplômes depuis le texte d'éducation."""
        if not education_text:
            return []
        
        diplomes = []
        lines = education_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Détection de patterns de diplômes
            diploma_types = ['master', 'licence', 'bachelor', 'doctorat', 'phd', 'bts', 'dut', 'ingénieur']
            for diploma_type in diploma_types:
                if diploma_type.lower() in line.lower():
                    diplomes.append({
                        "type": diploma_type,
                        "description": line
                    })
                    break
        
        return diplomes
    
    def _extract_experiences(self, experience_text: str) -> List[Dict[str, Any]]:
        """Extrait les expériences professionnelles structurées."""
        if not experience_text:
            return []
        
        experiences = []
        # Découpage par lignes ou par dates
        lines = experience_text.split('\n')
        
        current_exp = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_exp:
                    experiences.append(current_exp)
                    current_exp = {}
                continue
            
            # Détection de dates (années)
            year_match = re.search(r'(19|20)\d{2}', line)
            if year_match:
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    "date": year_match.group(0),
                    "description": line
                }
            elif current_exp:
                current_exp["description"] += " " + line
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def _generer_commentaire(
        self,
        profil: Dict,
        job_profile: Dict,
        score: float
    ) -> str:
        """Génère un commentaire justificatif."""
        
        if self.llm:
            return self._generer_commentaire_llm(profil, job_profile, score)
        
        # Commentaire basique sans LLM
        commentaire_parts = []
        
        # Compétences
        candidate_skills = set(s.lower() for s in profil.get("skills_list", []))
        required_skills = set(s.lower() for s in job_profile.get("skills_obligatoires", []))
        matched_skills = candidate_skills & required_skills
        
        if matched_skills:
            commentaire_parts.append(
                f"Compétences correspondantes: {', '.join(list(matched_skills)[:5])}"
            )
        
        # Expérience
        years_exp = profil.get("years_experience", 0)
        exp_min = job_profile.get("exp_min")
        if exp_min:
            if years_exp >= exp_min:
                commentaire_parts.append(f"Expérience adéquate ({years_exp} ans)")
            else:
                commentaire_parts.append(f"Expérience insuffisante ({years_exp} ans requis: {exp_min})")
        
        # Score global
        if score >= 80:
            niveau = "excellent"
        elif score >= 60:
            niveau = "bon"
        elif score >= 40:
            niveau = "moyen"
        else:
            niveau = "faible"
        
        commentaire_parts.append(f"Score global: {score:.1f}/100 ({niveau})")
        
        return ". ".join(commentaire_parts) + "."
    
    def _generer_commentaire_llm(
        self,
        profil: Dict,
        job_profile: Dict,
        score: float
    ) -> str:
        """Génère un commentaire avec LLM."""
        prompt = f"""
Tu es un agent RH expert. Analyse le profil suivant et génère un commentaire justificatif
pour un score de {score:.1f}/100.

Profil candidat:
- Expérience: {profil.get('years_experience', 0)} ans
- Compétences: {', '.join(profil.get('skills_list', [])[:10])}
- Éducation: {profil.get('education_level', 'N/A')}

Profil requis:
- Poste: {job_profile.get('poste', 'N/A')}
- Expérience min: {job_profile.get('exp_min', 'N/A')} ans
- Compétences requises: {', '.join(job_profile.get('skills_obligatoires', [])[:10])}

Génère un commentaire concis (2-3 phrases) expliquant le score.
"""
        try:
            response = self.llm(prompt)
            return response if isinstance(response, str) else str(response)
        except Exception:
            return self._generer_commentaire(profil, job_profile, score)  # Fallback
