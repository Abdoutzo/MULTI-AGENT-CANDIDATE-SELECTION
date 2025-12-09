"""AgentDécideur : décision finale avec pondération multi-critères."""
from typing import Any, Dict, List, Optional, Tuple

from src.config import WEIGHT_PROFIL, WEIGHT_TECHNIQUE, WEIGHT_SOFTSKILLS


class AgentDecideur:
    """
    Agent qui agrège les avis des autres agents et génère un classement final.
    
    Tâches:
    - Agrégation des scores (pondération)
    - Classification: "fortement recommandé / recommandé / à rejeter"
    - Classement final des candidats + rapport explicable
    """
    
    def __init__(self, llm: Any = None):
        """
        Args:
            llm: Modèle LLM optionnel pour justification avancée
        """
        self.llm = llm
        self.weight_profil = WEIGHT_PROFIL
        self.weight_technique = WEIGHT_TECHNIQUE
        self.weight_softskills = WEIGHT_SOFTSKILLS
    
    def prendre_decision(
        self,
        candidate_id: str,
        score_profil: float,
        score_technique: float,
        score_softskills: float,
        commentaire_profil: str = "",
        commentaire_technique: str = "",
        commentaire_softskills: str = "",
        profil_structuré: Optional[Dict] = None,
        job_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Prend une décision finale pour un candidat.
        
        Args:
            candidate_id: Identifiant du candidat
            score_profil: Score de profil (0-100)
            score_technique: Score technique (0-100)
            score_softskills: Score soft skills (0-100)
            commentaire_profil: Commentaire de l'agent profil
            commentaire_technique: Commentaire de l'agent technique
            commentaire_softskills: Commentaire de l'agent soft skills
            profil_structuré: Profil structuré du candidat
            job_profile: Profil de l'offre
        
        Returns:
            Dict avec:
            - score_global: score agrégé (0-100)
            - recommandation: "fortement recommandé" / "recommandé" / "à rejeter"
            - justification: texte explicatif complet
        """
        # Calcul du score global avec pondération
        score_global = (
            score_profil * self.weight_profil +
            score_technique * self.weight_technique +
            score_softskills * self.weight_softskills
        )
        
        # Classification
        recommandation = self._classifier(score_global)
        
        # Génération de la justification
        justification = self._generer_justification(
            candidate_id,
            score_global,
            score_profil,
            score_technique,
            score_softskills,
            commentaire_profil,
            commentaire_technique,
            commentaire_softskills,
            recommandation,
            profil_structuré,
            job_profile
        )
        
        return {
            "candidate_id": candidate_id,
            "score_global": score_global,
            "score_profil": score_profil,
            "score_technique": score_technique,
            "score_softskills": score_softskills,
            "recommandation": recommandation,
            "justification": justification
        }
    
    def _classifier(self, score_global: float) -> str:
        """Classifie le candidat selon son score global."""
        if score_global >= 80:
            return "fortement recommandé"
        elif score_global >= 60:
            return "recommandé"
        elif score_global >= 40:
            return "à considérer"
        else:
            return "à rejeter"
    
    def _generer_justification(
        self,
        candidate_id: str,
        score_global: float,
        score_profil: float,
        score_technique: float,
        score_softskills: float,
        commentaire_profil: str,
        commentaire_technique: str,
        commentaire_softskills: str,
        recommandation: str,
        profil_structuré: Optional[Dict],
        job_profile: Optional[Dict]
    ) -> str:
        """Génère une justification complète."""
        
        if self.llm:
            return self._generer_justification_llm(
                candidate_id, score_global, score_profil, score_technique, score_softskills,
                commentaire_profil, commentaire_technique, commentaire_softskills,
                recommandation, profil_structuré, job_profile
            )
        
        # Justification basique sans LLM
        justification_parts = [
            f"Candidat: {candidate_id}",
            f"Score global: {score_global:.1f}/100",
            f"Recommandation: {recommandation.upper()}",
            "",
            "Détail des scores:",
            f"- Profil: {score_profil:.1f}/100",
            f"- Technique: {score_technique:.1f}/100",
            f"- Soft Skills: {score_softskills:.1f}/100",
            "",
            "Justifications:",
        ]
        
        if commentaire_profil:
            justification_parts.append(f"Profil: {commentaire_profil}")
        if commentaire_technique:
            justification_parts.append(f"Technique: {commentaire_technique}")
        if commentaire_softskills:
            justification_parts.append(f"Soft Skills: {commentaire_softskills}")
        
        return "\n".join(justification_parts)
    
    def _generer_justification_llm(
        self,
        candidate_id: str,
        score_global: float,
        score_profil: float,
        score_technique: float,
        score_softskills: float,
        commentaire_profil: str,
        commentaire_technique: str,
        commentaire_softskills: str,
        recommandation: str,
        profil_structuré: Optional[Dict],
        job_profile: Optional[Dict]
    ) -> str:
        """Génère une justification avec LLM."""
        prompt = f"""
Tu es un agent décideur RH expert. Génère un rapport de décision complet et justifié
pour le candidat {candidate_id}.

Score global: {score_global:.1f}/100
Recommandation: {recommandation}

Détail des scores:
- Profil: {score_profil:.1f}/100
- Technique: {score_technique:.1f}/100
- Soft Skills: {score_softskills:.1f}/100

Commentaires des agents:
- Profil: {commentaire_profil}
- Technique: {commentaire_technique}
- Soft Skills: {commentaire_softskills}

Génère un rapport structuré (4-5 phrases) expliquant la décision finale de manière claire
et professionnelle.
"""
        try:
            response = self.llm(prompt)
            return response if isinstance(response, str) else str(response)
        except Exception:
            return self._generer_justification(
                candidate_id, score_global, score_profil, score_technique, score_softskills,
                commentaire_profil, commentaire_technique, commentaire_softskills,
                recommandation, profil_structuré, job_profile
            )  # Fallback
    
    def classer_candidats(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classe une liste de candidats par score global décroissant.
        
        Args:
            evaluations: Liste de dicts avec les clés de prendre_decision
        
        Returns:
            Liste triée par score_global décroissant
        """
        return sorted(
            evaluations,
            key=lambda x: x.get("score_global", 0),
            reverse=True
        )
    
    def generer_rapport_final(
        self,
        evaluations_classees: List[Dict[str, Any]],
        job_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Génère un rapport final avec le top N candidats.
        
        Args:
            evaluations_classees: Liste de candidats classés
            job_profile: Profil de l'offre
        
        Returns:
            Dict avec:
            - top_candidats: top 3 ou 5
            - resume: résumé global
            - statistiques: stats sur les candidats
        """
        top_n = min(5, len(evaluations_classees))
        top_candidats = evaluations_classees[:top_n]
        
        # Statistiques
        scores_globaux = [e.get("score_global", 0) for e in evaluations_classees]
        moyenne = sum(scores_globaux) / len(scores_globaux) if scores_globaux else 0
        max_score = max(scores_globaux) if scores_globaux else 0
        min_score = min(scores_globaux) if scores_globaux else 0
        
        resume = f"""
Rapport de sélection - {len(evaluations_classees)} candidat(s) évalué(s)

Top {top_n} candidats:
"""
        for i, cand in enumerate(top_candidats, 1):
            resume += f"\n{i}. {cand.get('candidate_id', 'N/A')} - Score: {cand.get('score_global', 0):.1f}/100"
            resume += f" ({cand.get('recommandation', 'N/A')})"
        
        resume += f"\n\nStatistiques:"
        resume += f"\n- Score moyen: {moyenne:.1f}/100"
        resume += f"\n- Score max: {max_score:.1f}/100"
        resume += f"\n- Score min: {min_score:.1f}/100"
        
        return {
            "top_candidats": top_candidats,
            "resume": resume,
            "statistiques": {
                "total_candidats": len(evaluations_classees),
                "score_moyen": moyenne,
                "score_max": max_score,
                "score_min": min_score
            }
        }
