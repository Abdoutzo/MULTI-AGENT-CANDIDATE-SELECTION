"""Point d'entrée : exécution du pipeline multi-agent."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.agents.agent_rh import AgentRH
from src.agents.agent_profil import AgentProfil
from src.agents.agent_technique import AgentTechnique
from src.agents.agent_softskills import AgentSoftSkills
from src.agents.agent_decideur import AgentDecideur
from src.rag.query_index import RAGQueryEngine
from src.utils.data_utils import PARSED_DIR, extract_text
from src.config import DATA_DIR


class MultiAgentPipeline:
    """Pipeline principal qui orchestre tous les agents."""
    
    def __init__(self, llm: Any = None):
        """
        Args:
            llm: Modèle LLM optionnel pour tous les agents
        """
        self.llm = llm
        
        # Initialisation des agents
        self.agent_rh = AgentRH(llm=llm)
        self.agent_profil = AgentProfil(llm=llm)
        self.agent_technique = AgentTechnique(llm=llm)
        self.agent_softskills = AgentSoftSkills(llm=llm)
        self.agent_decideur = AgentDecideur(llm=llm)
        
        # RAG Query Engine
        self.rag_engine = None
    
    def initialize_rag(self):
        """Initialise le moteur RAG."""
        try:
            self.rag_engine = RAGQueryEngine()
            self.rag_engine.initialize()
            print("[OK] RAG initialisé")
        except Exception as e:
            print(f"[WARNING] RAG non disponible: {e}")
            self.rag_engine = None
    
    def process_job_offer(
        self,
        job_description: str,
        criteres: Optional[Dict] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Traite une offre d'emploi et retourne les candidats classés.
        
        Args:
            job_description: Description de l'offre d'emploi
            criteres: Critères supplémentaires du recruteur
            use_rag: Utiliser RAG pour pré-filtrer les candidats
        
        Returns:
            Dict avec:
            - job_profile: Profil structuré de l'offre
            - candidates_evaluated: Liste des candidats évalués et classés
            - report: Rapport final
        """
        print("\n" + "="*60)
        print("DÉMARRAGE DU PIPELINE MULTI-AGENT")
        print("="*60 + "\n")
        
        # Étape 1: Agent RH - Analyse de l'offre
        print("[1/5] Agent RH: Analyse de l'offre...")
        job_profile = self.agent_rh.analyser_offre(job_description, criteres)
        print(f"     Poste détecté: {job_profile.get('poste', 'N/A')}")
        print(f"     Compétences requises: {', '.join(job_profile.get('skills_obligatoires', [])[:5])}")
        
        # Étape 2: RAG - Recherche de candidats pertinents
        candidates_to_evaluate = []
        
        if use_rag and self.rag_engine:
            print("\n[2/5] RAG: Recherche de candidats pertinents...")
            rag_results = self.rag_engine.query_by_job_profile(job_profile, top_k=10)
            print(f"     {len(rag_results)} candidat(s) trouvé(s) via RAG")
            
            # Charger les candidats depuis les fichiers parsés
            for rag_result in rag_results:
                candidate_id = rag_result["candidate_id"]
                candidate_file = PARSED_DIR / f"{candidate_id}.json"
                if candidate_file.exists():
                    with open(candidate_file, 'r', encoding='utf-8') as f:
                        candidates_to_evaluate.append(json.load(f))
        else:
            # Fallback: charger tous les candidats
            print("\n[2/5] Chargement de tous les candidats (RAG désactivé)...")
            candidates_to_evaluate = self._load_all_candidates()
            print(f"     {len(candidates_to_evaluate)} candidat(s) chargé(s)")
        
        if not candidates_to_evaluate:
            print("\n[ERREUR] Aucun candidat à évaluer")
            return {
                "job_profile": job_profile,
                "candidates_evaluated": [],
                "report": {"error": "Aucun candidat trouvé"}
            }
        
        # Étape 3-5: Évaluation de chaque candidat
        print(f"\n[3-5/5] Évaluation de {len(candidates_to_evaluate)} candidat(s)...")
        evaluations = []
        
        for i, candidate in enumerate(candidates_to_evaluate, 1):
            print(f"\n  Candidat {i}/{len(candidates_to_evaluate)}: {candidate.get('id', 'N/A')}")
            
            evaluation = self._evaluate_candidate(candidate, job_profile)
            evaluations.append(evaluation)
        
        # Étape 6: Agent Décideur - Classement final
        print("\n[6/6] Agent Décideur: Classement final...")
        evaluations_classees = self.agent_decideur.classer_candidats(evaluations)
        report = self.agent_decideur.generer_rapport_final(
            evaluations_classees,
            job_profile
        )
        
        print("\n" + "="*60)
        print("PIPELINE TERMINÉ")
        print("="*60)
        print(f"\nTop 3 candidats:")
        for i, cand in enumerate(evaluations_classees[:3], 1):
            print(f"  {i}. {cand.get('candidate_id', 'N/A')} - "
                  f"Score: {cand.get('score_global', 0):.1f}/100 - "
                  f"{cand.get('recommandation', 'N/A')}")
        
        return {
            "job_profile": job_profile,
            "candidates_evaluated": evaluations_classees,
            "report": report
        }
    
    def _evaluate_candidate(
        self,
        candidate: Dict,
        job_profile: Dict
    ) -> Dict[str, Any]:
        """Évalue un candidat avec tous les agents."""
        
        candidate_id = candidate.get("id", "unknown")
        cv_text = candidate.get("raw_text", "")
        lettre_motivation = candidate.get("lettre_motivation", "")
        experience_text = candidate.get("experience_text", "")
        skills_list = candidate.get("skills_list", [])
        
        # Agent Profil
        profil_result = self.agent_profil.analyser_profil(
            cv_text,
            lettre_motivation,
            job_profile
        )
        
        # Agent Technique
        technique_result = self.agent_technique.evaluer_technique(
            skills_list,
            job_profile.get("skills_obligatoires", []),
            job_profile.get("skills_optionnelles", []),
            experience_text
        )
        
        # Agent Soft Skills
        softskills_result = self.agent_softskills.evaluer_softskills(
            lettre_motivation,
            experience_text,
            cv_text,
            job_profile.get("mots_cles", [])
        )
        
        # Agent Décideur
        decision = self.agent_decideur.prendre_decision(
            candidate_id,
            profil_result["score_profil"],
            technique_result["score_technique"],
            softskills_result["score_softskills"],
            profil_result["commentaire"],
            technique_result["commentaire_technique"],
            softskills_result["commentaire_softskills"],
            profil_result["profil_structuré"],
            job_profile
        )
        
        return decision
    
    def _load_all_candidates(self) -> List[Dict]:
        """Charge tous les candidats depuis les fichiers parsés."""
        candidates = []
        
        if not PARSED_DIR.exists():
            return candidates
        
        json_files = list(PARSED_DIR.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    candidate = json.load(f)
                    candidates.append(candidate)
            except Exception as e:
                print(f"[ERROR] Erreur lors du chargement de {json_file}: {e}")
        
        return candidates


def main():
    """Fonction principale pour test en ligne de commande."""
    import sys
    
    # Exemple d'utilisation
    job_description = """
    Data Scientist
    
    Nous recherchons un Data Scientist avec 2 ans d'expérience minimum.
    Compétences requises: Python, Machine Learning, Power BI.
    Langues: Français, Anglais.
    """
    
    if len(sys.argv) > 1:
        # Lire la description depuis un fichier
        job_file = Path(sys.argv[1])
        if job_file.exists():
            job_description = extract_text(job_file)
    
    # Initialisation du pipeline
    pipeline = MultiAgentPipeline()
    pipeline.initialize_rag()
    
    # Traitement
    results = pipeline.process_job_offer(job_description)
    
    # Affichage des résultats
    print("\n" + "="*60)
    print("RÉSULTATS FINAUX")
    print("="*60)
    print(results["report"]["resume"])


if __name__ == "__main__":
    main()
