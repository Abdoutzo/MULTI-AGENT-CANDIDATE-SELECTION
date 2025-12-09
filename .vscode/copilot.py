"""
You are GitHub Copilot helping me scaffold a Python project.

Context:
- This file is located at the root of the repository MULTI-AGENT-CANDIDATE-SELECTION.
- I want a clean folder/file architecture for a multi-agent candidate selection system
  (multi-agent LLM + RAG + Streamlit app).

Goal:
Write Python code in this file that will create, IF THEY DO NOT ALREADY EXIST, the
following folders and files relative to the project root:

Folders:
- data/raw
- data/processed
- src
- src/agents
- src/rag
- src/utils
- src/app
- notebooks

Files (with minimal boilerplate and docstrings):
- src/__init__.py
- src/config.py
- src/main.py
- src/agents/__init__.py
- src/agents/agent_rh.py          -> class AgentRH
- src/agents/agent_profil.py      -> class AgentProfil
- src/agents/agent_technique.py   -> class AgentTechnique
- src/agents/agent_softskills.py  -> class AgentSoftSkills
- src/agents/agent_decideur.py    -> class AgentDecideur
- src/rag/__init__.py
- src/rag/build_index.py
- src/rag/query_index.py
- src/utils/__init__.py
- src/utils/parsing.py
- src/utils/preprocessing.py
- src/utils/scoring.py
- src/app/__init__.py
- src/app/streamlit_app.py
- notebooks/.gitkeep
- requirements.txt

Constraints:
- Use Python (os / pathlib) to create folders and files.
- Do NOT overwrite existing content: if a file already exists, keep it as is or only
  append missing docstrings/placeholders safely.
- Each Python file must contain at least a top-level docstring explaining its role.
- The script must be executable with: `python setup_structure.py`.
"""

import os
from pathlib import Path

# Liste des dossiers à créer
folders = [
    "data/raw",
    "data/processed",
    "src/agents",
    "src/rag",
    "src/utils",
    "src/app",
    "notebooks"
]

# Création des dossiers
for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Fichiers à créer avec docstrings de base
files_with_docstrings = {
    "src/__init__.py": '"""Initialisation du package source."""\n',
    "src/config.py": '"""Configuration globale du projet (paths, paramètres)."""\n',
    "src/main.py": '"""Point d’entrée : exécution du pipeline multi-agent."""\n',
    "src/agents/__init__.py": '"""Package des agents intelligents."""\n',
    "src/agents/agent_rh.py": '"""AgentRH : analyse de l’offre et création du profil cible."""\n\nclass AgentRH:\n    pass\n',
    "src/agents/agent_profil.py": '"""AgentProfil : évalue l’adéquation du profil du candidat."""\n\nclass AgentProfil:\n    pass\n',
    "src/agents/agent_technique.py": '"""AgentTechnique : analyse des compétences techniques."""\n\nclass AgentTechnique:\n    pass\n',
    "src/agents/agent_softskills.py": '"""AgentSoftSkills : évaluation des soft skills via LLM."""\n\nclass AgentSoftSkills:\n    pass\n',
    "src/agents/agent_decideur.py": '"""AgentDécideur : décision finale avec pondération multi-critères."""\n\nclass AgentDecideur:\n    pass\n',
    "src/rag/__init__.py": '"""Package pour l’implémentation RAG (index + retrieval)."""\n',
    "src/rag/build_index.py": '"""Création de l’index vectoriel pour les documents candidats."""\n',
    "src/rag/query_index.py": '"""Requêtes sur l’index pour trouver les candidats proches d’une offre."""\n',
    "src/utils/__init__.py": '"""Fonctions utilitaires pour le projet."""\n',
    "src/utils/parsing.py": '"""Parsing des CV et lettres de motivation."""\n',
    "src/utils/preprocessing.py": '"""Prétraitement du texte (nettoyage, normalisation)."""\n',
    "src/utils/scoring.py": '"""Calcul des scores multi-critères (profil, technique, soft skills)."""\n',
    "src/app/__init__.py": '"""Package de l’application Streamlit."""\n',
    "src/app/streamlit_app.py": '"""Interface utilisateur Streamlit pour la sélection de candidats."""\n',
    "notebooks/.gitkeep": ""
}

# Création des fichiers
for filepath, content in files_with_docstrings.items():
    file_path = Path(filepath)
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

print("🎯 Structure du projet générée avec succès !")

if __name__ == "__main__":
    print("🚀 Génération de la structure du projet démarrée...")
    # Exécuter les créations de folders et fichiers
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)

    for filepath, content in files_with_docstrings.items():
        file_path = Path(filepath)
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    print("🎯 Structure du projet générée avec succès !")

