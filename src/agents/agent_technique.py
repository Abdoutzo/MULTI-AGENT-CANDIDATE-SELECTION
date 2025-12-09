"""AgentTechnique : analyse des compétences techniques."""
from typing import Any, Dict, List, Optional

from src.utils.scoring import calculate_technical_score


class AgentTechnique:
    """
    Agent qui évalue les compétences techniques d'un candidat.
    
    Tâches:
    - Vérification des compétences techniques requises (Python, ML, Cloud, etc.)
    - Scoring technique (0-100) + justification textuelle
    """
    
    def __init__(self, llm: Any = None):
        """
        Args:
            llm: Modèle LLM optionnel pour évaluation avancée
        """
        self.llm = llm
    
    def evaluer_technique(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        optional_skills: List[str] = None,
        candidate_experience: str = ""
    ) -> Dict[str, Any]:
        """
        Évalue les compétences techniques d'un candidat.
        
        Args:
            candidate_skills: Liste des compétences du candidat
            required_skills: Compétences techniques requises
            optional_skills: Compétences optionnelles
            candidate_experience: Texte de l'expérience (pour contexte)
        
        Returns:
            Dict avec:
            - score_technique: score (0-100)
            - commentaire_technique: justification
            - skills_matched: compétences correspondantes
            - skills_missing: compétences manquantes
        """
        optional_skills = optional_skills or []
        
        # Normalisation
        candidate_set = {s.lower().strip() for s in candidate_skills}
        required_set = {s.lower().strip() for s in required_skills}
        optional_set = {s.lower().strip() for s in optional_skills}
        
        # Calcul du score
        score_technique = calculate_technical_score(
            list(candidate_set),
            list(required_set)
        )
        
        # Détection des compétences correspondantes et manquantes
        skills_matched = list(candidate_set & required_set)
        skills_missing = list(required_set - candidate_set)
        skills_bonus = list(candidate_set & optional_set)
        
        # Génération du commentaire
        commentaire_technique = self._generer_commentaire(
            skills_matched,
            skills_missing,
            skills_bonus,
            score_technique,
            required_skills
        )
        
        return {
            "score_technique": score_technique,
            "commentaire_technique": commentaire_technique,
            "skills_matched": skills_matched,
            "skills_missing": skills_missing,
            "skills_bonus": skills_bonus,
            "coverage": len(skills_matched) / len(required_set) if required_set else 0.0
        }
    
    def _generer_commentaire(
        self,
        skills_matched: List[str],
        skills_missing: List[str],
        skills_bonus: List[str],
        score: float,
        required_skills: List[str]
    ) -> str:
        """Génère un commentaire justificatif."""
        
        if self.llm:
            return self._generer_commentaire_llm(
                skills_matched, skills_missing, skills_bonus, score
            )
        
        # Commentaire basique sans LLM
        commentaire_parts = []
        
        if skills_matched:
            commentaire_parts.append(
                f"Compétences techniques maîtrisées: {', '.join(skills_matched[:5])}"
            )
        
        if skills_missing:
            commentaire_parts.append(
                f"Compétences manquantes: {', '.join(skills_missing[:5])}"
            )
        
        if skills_bonus:
            commentaire_parts.append(
                f"Compétences bonus: {', '.join(skills_bonus[:3])}"
            )
        
        # Évaluation globale
        coverage = len(skills_matched) / len(required_skills) if required_skills else 0
        
        if coverage >= 0.8:
            niveau = "excellent"
        elif coverage >= 0.6:
            niveau = "bon"
        elif coverage >= 0.4:
            niveau = "moyen"
        else:
            niveau = "insuffisant"
        
        commentaire_parts.append(
            f"Score technique: {score:.1f}/100 ({niveau}, {len(skills_matched)}/{len(required_skills)} compétences)"
        )
        
        return ". ".join(commentaire_parts) + "."
    
    def _generer_commentaire_llm(
        self,
        skills_matched: List[str],
        skills_missing: List[str],
        skills_bonus: List[str],
        score: float
    ) -> str:
        """Génère un commentaire avec LLM."""
        prompt = f"""
Tu es un expert technique en recrutement. Analyse l'évaluation suivante et génère
un commentaire justificatif pour un score technique de {score:.1f}/100.

Compétences maîtrisées: {', '.join(skills_matched) if skills_matched else 'Aucune'}
Compétences manquantes: {', '.join(skills_missing) if skills_missing else 'Aucune'}
Compétences bonus: {', '.join(skills_bonus) if skills_bonus else 'Aucune'}

Génère un commentaire technique concis (2-3 phrases) expliquant le score.
"""
        try:
            response = self.llm(prompt)
            return response if isinstance(response, str) else str(response)
        except Exception:
            return self._generer_commentaire(
                skills_matched, skills_missing, skills_bonus, score, []
            )  # Fallback
