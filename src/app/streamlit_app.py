"""Interface utilisateur Streamlit pour la sélection de candidats."""
import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Any

from src.main import MultiAgentPipeline
from src.rag.build_index import build_index
from src.utils.data_utils import extract_text, list_raw_files
from src.config import DATA_DIR, JOBS_DIR


# Configuration de la page
st.set_page_config(
    page_title="Système Multi-Agents - Sélection de Candidats",
    page_icon="🤖",
    layout="wide"
)

# Titre principal
st.title("🤖 Système Multi-Agents pour la Sélection Intelligente des Candidats")
st.markdown("---")

# Initialisation de l'état de session
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "rag_initialized" not in st.session_state:
    st.session_state.rag_initialized = False


def initialize_pipeline():
    """Initialise le pipeline multi-agent."""
    if st.session_state.pipeline is None:
        with st.spinner("Initialisation du pipeline..."):
            st.session_state.pipeline = MultiAgentPipeline()
            try:
                st.session_state.pipeline.initialize_rag()
                st.session_state.rag_initialized = True
                st.success("Pipeline initialisé avec succès!")
            except Exception as e:
                st.warning(f"RAG non disponible: {e}. Le système fonctionnera sans pré-filtrage RAG.")
                st.session_state.rag_initialized = False


# Sidebar pour la configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Bouton d'initialisation
    if st.button("🔄 Initialiser le Pipeline", use_container_width=True):
        initialize_pipeline()
    
    st.markdown("---")
    
    # Section RAG
    st.subheader("📚 Index RAG")
    if st.button("🔨 Construire/Rebuild l'Index", use_container_width=True):
        with st.spinner("Construction de l'index RAG..."):
            try:
                builder = build_index(rebuild=True)
                st.success("Index RAG construit avec succès!")
                st.session_state.rag_initialized = True
            except Exception as e:
                st.error(f"Erreur: {e}")
    
    st.markdown("---")
    
    # Statistiques
    st.subheader("📊 Statistiques")
    if PARSED_DIR.exists():
        num_candidates = len(list(PARSED_DIR.glob("*.json")))
        st.metric("Candidats indexés", num_candidates)
    
    if JOBS_DIR.exists():
        num_jobs = len(list(JOBS_DIR.glob("*.pdf"))) + len(list(JOBS_DIR.glob("*.txt")))
        st.metric("Offres disponibles", num_jobs)


# Interface principale
tab1, tab2, tab3 = st.tabs(["🎯 Évaluation de Candidats", "📄 Gestion des Données", "ℹ️ À propos"])

with tab1:
    st.header("Évaluation de Candidats")
    
    if st.session_state.pipeline is None:
        st.info("👈 Veuillez initialiser le pipeline depuis la sidebar avant de continuer.")
        initialize_pipeline()
    
    # Sélection de l'offre d'emploi
    st.subheader("1️⃣ Description de l'Offre d'Emploi")
    
    # Option: fichier ou texte manuel
    input_method = st.radio(
        "Méthode de saisie",
        ["📝 Texte manuel", "📄 Fichier"],
        horizontal=True
    )
    
    job_description = ""
    
    if input_method == "📄 Fichier":
        # Liste des fichiers disponibles
        job_files = []
        if JOBS_DIR.exists():
            job_files = list(JOBS_DIR.glob("*.pdf")) + list(JOBS_DIR.glob("*.txt"))
        
        if job_files:
            selected_file = st.selectbox(
                "Sélectionner un fichier",
                [f.name for f in job_files]
            )
            if selected_file:
                file_path = JOBS_DIR / selected_file
                job_description = extract_text(file_path)
        else:
            st.warning("Aucun fichier d'offre trouvé dans DATA/jobs/")
    
    # Zone de texte pour la description
    job_description_input = st.text_area(
        "Description de l'offre d'emploi",
        value=job_description,
        height=200,
        placeholder="Exemple:\nData Scientist\n\nNous recherchons un Data Scientist avec 2 ans d'expérience minimum.\nCompétences requises: Python, Machine Learning, Power BI.\nLangues: Français, Anglais."
    )
    
    # Critères supplémentaires (optionnel)
    with st.expander("➕ Critères supplémentaires (optionnel)"):
        col1, col2 = st.columns(2)
        with col1:
            exp_min = st.number_input("Expérience minimale (années)", min_value=0, value=0)
            salaire_min = st.number_input("Salaire minimum", min_value=0, value=0)
        with col2:
            exp_max = st.number_input("Expérience maximale (années)", min_value=0, value=0)
            salaire_max = st.number_input("Salaire maximum", min_value=0, value=0)
        
        lieu = st.text_input("Lieu", placeholder="ex: Paris, Remote")
        contrat = st.selectbox("Type de contrat", ["", "CDI", "CDD", "Stage", "Alternance", "Freelance"])
    
    criteres = {}
    if exp_min > 0:
        criteres["exp_min"] = exp_min
    if exp_max > 0:
        criteres["exp_max"] = exp_max
    if salaire_min > 0:
        criteres["salaire_min"] = salaire_min
    if salaire_max > 0:
        criteres["salaire_max"] = salaire_max
    if lieu:
        criteres["lieu"] = lieu
    if contrat:
        criteres["contrat"] = contrat
    
    # Bouton d'évaluation
    st.markdown("---")
    if st.button("🚀 Lancer l'Évaluation", type="primary", use_container_width=True):
        if not job_description_input.strip():
            st.error("Veuillez saisir une description d'offre d'emploi.")
        else:
            with st.spinner("Évaluation en cours... Cela peut prendre quelques minutes."):
                try:
                    results = st.session_state.pipeline.process_job_offer(
                        job_description_input,
                        criteres if criteres else None,
                        use_rag=st.session_state.rag_initialized
                    )
                    
                    st.session_state.results = results
                    st.success("Évaluation terminée!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'évaluation: {e}")
    
    # Affichage des résultats
    if "results" in st.session_state:
        results = st.session_state.results
        
        st.markdown("---")
        st.subheader("📊 Résultats de l'Évaluation")
        
        # Profil de l'offre
        with st.expander("📋 Profil de l'Offre Analysé"):
            job_profile = results["job_profile"]
            st.json(job_profile)
        
        # Tableau des candidats
        candidates = results["candidates_evaluated"]
        
        if candidates:
            st.subheader(f"🏆 Classement des Candidats ({len(candidates)} évalué(s))")
            
            # Filtre par recommandation
            filter_rec = st.selectbox(
                "Filtrer par recommandation",
                ["Tous", "Fortement recommandé", "Recommandé", "À considérer", "À rejeter"]
            )
            
            filtered_candidates = candidates
            if filter_rec != "Tous":
                filtered_candidates = [
                    c for c in candidates
                    if c.get("recommandation", "").lower() == filter_rec.lower()
                ]
            
            # Affichage du tableau
            for i, candidate in enumerate(filtered_candidates[:10], 1):  # Top 10
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        rec_color = {
                            "fortement recommandé": "🟢",
                            "recommandé": "🟡",
                            "à considérer": "🟠",
                            "à rejeter": "🔴"
                        }.get(candidate.get("recommandation", "").lower(), "⚪")
                        
                        st.markdown(f"**{rec_color} {i}. {candidate.get('candidate_id', 'N/A')}**")
                    
                    with col2:
                        st.metric("Score Global", f"{candidate.get('score_global', 0):.1f}")
                    
                    with col3:
                        st.metric("Technique", f"{candidate.get('score_technique', 0):.1f}")
                    
                    with col4:
                        st.metric("Soft Skills", f"{candidate.get('score_softskills', 0):.1f}")
                    
                    # Détails expandable
                    with st.expander(f"📝 Détails - {candidate.get('candidate_id', 'N/A')}"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Score Profil", f"{candidate.get('score_profil', 0):.1f}")
                        with col_b:
                            st.metric("Score Technique", f"{candidate.get('score_technique', 0):.1f}")
                        with col_c:
                            st.metric("Score Soft Skills", f"{candidate.get('score_softskills', 0):.1f}")
                        
                        st.markdown("**Justification:**")
                        st.text_area(
                            "Justification complète",
                            value=candidate.get("justification", ""),
                            height=150,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    
                    st.markdown("---")
            
            # Rapport final
            st.subheader("📈 Rapport Final")
            report = results["report"]
            st.text(report.get("resume", ""))
            
            # Statistiques
            stats = report.get("statistiques", {})
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Candidats", stats.get("total_candidats", 0))
                with col2:
                    st.metric("Score Moyen", f"{stats.get('score_moyen', 0):.1f}")
                with col3:
                    st.metric("Score Max", f"{stats.get('score_max', 0):.1f}")
                with col4:
                    st.metric("Score Min", f"{stats.get('score_min', 0):.1f}")
        else:
            st.warning("Aucun candidat évalué.")


with tab2:
    st.header("Gestion des Données")
    
    st.subheader("📁 Structure des Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Candidats")
        if PARSED_DIR.exists():
            candidates = list(PARSED_DIR.glob("*.json"))
            st.metric("Candidats parsés", len(candidates))
            
            if candidates:
                st.markdown("**Fichiers disponibles:**")
                for cand_file in candidates[:10]:
                    st.text(f"  • {cand_file.name}")
                if len(candidates) > 10:
                    st.text(f"  ... et {len(candidates) - 10} autres")
        else:
            st.warning("Dossier des candidats parsés non trouvé.")
    
    with col2:
        st.markdown("### Offres d'Emploi")
        if JOBS_DIR.exists():
            jobs = list(JOBS_DIR.glob("*.pdf")) + list(JOBS_DIR.glob("*.txt"))
            st.metric("Offres disponibles", len(jobs))
            
            if jobs:
                st.markdown("**Fichiers disponibles:**")
                for job_file in jobs[:10]:
                    st.text(f"  • {job_file.name}")
                if len(jobs) > 10:
                    st.text(f"  ... et {len(jobs) - 10} autres")
        else:
            st.warning("Dossier des offres non trouvé.")


with tab3:
    st.header("À propos")
    
    st.markdown("""
    ## 🤖 Système Multi-Agents pour la Sélection Intelligente des Candidats
    
    Ce système utilise une architecture multi-agents pour automatiser et expliquer 
    le processus de sélection des candidats à partir de CV, lettres de motivation 
    et profils LinkedIn.
    
    ### Architecture
    
    Le système comprend 5 agents spécialisés:
    
    1. **Agent RH** 📋
       - Lit les descriptions de poste et les critères du recruteur
       - Génère un profil cible structuré
    
    2. **Agent Profil** 👤
       - Analyse les CV et lettres de motivation
       - Extraction d'informations (NER, compétences, expérience)
       - Calcul d'un score de matching profil
    
    3. **Agent Technique** 💻
       - Évalue les compétences techniques
       - Vérifie l'adéquation avec les exigences du poste
    
    4. **Agent Soft Skills** 🤝
       - Évalue les qualités interpersonnelles
       - Analyse la motivation et l'adéquation culturelle
    
    5. **Agent Décideur** ⚖️
       - Agrège les avis de tous les agents
       - Génère un classement final justifié
    
    ### Technologies
    
    - **Framework agentique**: LangChain
    - **NLP**: spaCy, Transformers, Sentence Transformers
    - **RAG**: ChromaDB pour la recherche vectorielle
    - **LLM**: GPT-4/3.5, Mistral, Claude (optionnel)
    - **Interface**: Streamlit
    
    ### Utilisation
    
    1. Placez vos CV dans `DATA/raw/`
    2. Placez vos offres dans `DATA/jobs/`
    3. Exécutez le prétraitement pour parser les documents
    4. Construisez l'index RAG
    5. Utilisez l'interface Streamlit pour évaluer les candidats
    """)


if __name__ == "__main__":
    # Pour lancer depuis la ligne de commande:
    # streamlit run src/app/streamlit_app.py
    pass
