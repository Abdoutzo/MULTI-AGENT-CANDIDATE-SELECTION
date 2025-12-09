"""AgentSoftSkills : évaluation des soft skills via LLM."""
from typing import Any, Dict, List, Optional

from src.utils.scoring import calculate_soft_skills_score


class AgentSoftSkills:
    """
    Agent qui évalue les soft skills d'un candidat.
    
    Tâches:
    - Analyse de ton (motivation, clarté, cohérence)
    - Extraction d'indices sur soft skills
    - Scoring soft skills (0-100) + justification
    """
    
    def __init__(self, llm: Any = None):
        """
        Args:
            llm: Modèle LLM optionnel pour analyse avancée
        """
        self.llm = llm
    
    def evaluer_softskills(
        self,
        lettre_motivation: str,
        experience_text: str = "",
        cv_text: str = "",
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Évalue les soft skills d'un candidat.
        
        Args:
            lettre_motivation: Texte de la lettre de motivation
            experience_text: Texte de l'expérience professionnelle
            cv_text: Texte complet du CV (pour contexte)
            keywords: Mots-clés de soft skills recherchés par le recruteur
        
        Returns:
            Dict avec:
            - score_softskills: score (0-100)
            - commentaire_softskills: justification
            - soft_skills_detected: liste des soft skills détectés
        """
        keywords = keywords or []
        
        # Calcul du score basique
        score_softskills = calculate_soft_skills_score(
            lettre_motivation,
            experience_text,
            keywords
        )
        
        # Détection des soft skills
        soft_skills_detected = self._detect_soft_skills(
            lettre_motivation + " " + experience_text
        )
        
        # Génération du commentaire
        commentaire_softskills = self._generer_commentaire(
            lettre_motivation,
            experience_text,
            soft_skills_detected,
            score_softskills,
            keywords
        )
        
        return {
            "score_softskills": score_softskills,
            "commentaire_softskills": commentaire_softskills,
            "soft_skills_detected": soft_skills_detected
        }
    
    def _detect_soft_skills(self, text: str) -> List[str]:
        """Détecte les soft skills mentionnés dans le texte."""
        text_lower = text.lower()
        
        soft_skills_map = {
            "teamwork": ["équipe", "collaboration", "teamwork", "collaborer", "coopération"],
            "communication": ["communication", "communiquer", "présenter", "expliquer", "oral", "écrit"],
            "leadership": ["lead", "leader", "diriger", "management", "gérer", "encadrer"],
            "autonomy": ["autonome", "autonomie", "indépendant", "indépendance", "initiative"],
            "problem_solving": ["résoudre", "solution", "problème", "challenge", "défi", "analyser"],
            "adaptability": ["adaptable", "flexible", "changement", "évolution", "agile"],
            "motivation": ["motivé", "motivation", "passion", "intéressé", "enthousiaste", "désireux"],
            "creativity": ["créatif", "créativité", "innovation", "imagination", "original"],
            "organization": ["organisé", "organisation", "planification", "méthodique", "structuré"],
            "stress_management": ["stress", "pression", "sous pression", "calme", "sérénité"],
        }
        
        detected = []
        for skill_name, keywords_list in soft_skills_map.items():
            if any(keyword in text_lower for keyword in keywords_list):
                detected.append(skill_name)
        
        return detected
    
    def _generer_commentaire(
        self,
        lettre_motivation: str,
        experience_text: str,
        soft_skills_detected: List[str],
        score: float,
        keywords: List[str]
    ) -> str:
        """Génère un commentaire justificatif."""
        
        if self.llm:
            return self._generer_commentaire_llm(
                lettre_motivation, experience_text, soft_skills_detected, score, keywords
            )
        
        # Commentaire basique sans LLM
        commentaire_parts = []
        
        if soft_skills_detected:
            commentaire_parts.append(
                f"Soft skills détectés: {', '.join(soft_skills_detected[:5])}"
            )
        
        # Analyse de la lettre de motivation
        if lettre_motivation:
            word_count = len(lettre_motivation.split())
            if word_count > 200:
                commentaire_parts.append("Lettre de motivation détaillée et structurée")
            elif word_count > 100:
                commentaire_parts.append("Lettre de motivation correcte")
            else:
                commentaire_parts.append("Lettre de motivation courte")
        else:
            commentaire_parts.append("Aucune lettre de motivation fournie")
        
        # Mots-clés recherchés
        if keywords:
            text_lower = (lettre_motivation + " " + experience_text).lower()
            matched_keywords = [kw for kw in keywords if kw.lower() in text_lower]
            if matched_keywords:
                commentaire_parts.append(
                    f"Mots-clés recherchés trouvés: {', '.join(matched_keywords[:3])}"
                )
        
        # Évaluation globale
        if score >= 80:
            niveau = "excellent"
        elif score >= 60:
            niveau = "bon"
        elif score >= 40:
            niveau = "moyen"
        else:
            niveau = "faible"
        
        commentaire_parts.append(f"Score soft skills: {score:.1f}/100 ({niveau})")
        
        return ". ".join(commentaire_parts) + "."
    
    def _generer_commentaire_llm(
        self,
        lettre_motivation: str,
        experience_text: str,
        soft_skills_detected: List[str],
        score: float,
        keywords: List[str]
    ) -> str:
        """Génère un commentaire avec LLM."""
        prompt = f"""
Tu es un expert RH spécialisé dans l'évaluation des soft skills. Analyse le profil suivant
et génère un commentaire justificatif pour un score de soft skills de {score:.1f}/100.

Lettre de motivation (extrait): {lettre_motivation[:500] if lettre_motivation else 'Non fournie'}
Expérience: {experience_text[:300] if experience_text else 'Non fournie'}
Soft skills détectés: {', '.join(soft_skills_detected) if soft_skills_detected else 'Aucun'}
Mots-clés recherchés: {', '.join(keywords) if keywords else 'Aucun'}

Génère un commentaire concis (2-3 phrases) sur les soft skills du candidat.
"""
        try:
            response = self.llm(prompt)
            return response if isinstance(response, str) else str(response)
        except Exception:
            return self._generer_commentaire(
                lettre_motivation, experience_text, soft_skills_detected, score, keywords
            )  # Fallback
