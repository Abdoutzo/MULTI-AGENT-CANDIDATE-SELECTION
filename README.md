# 🤖 Système Multi-Agents pour la Sélection Intelligente des Candidats

Système automatisé de sélection de candidats utilisant une architecture multi-agents combinant RAG, IA générative et raisonnement multi-agent.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du Projet](#structure-du-projet)
- [Agents](#agents)
- [Technologies](#technologies)

## 🎯 Vue d'ensemble

Ce projet simule un comité virtuel de recrutement où chaque agent évalue les candidats sous un angle différent avant qu'un agent "décideur" n'émette un classement final justifié.

### Fonctionnalités

- ✅ Analyse automatique des descriptions de poste
- ✅ Extraction et structuration des informations des CV
- ✅ Évaluation multi-critères (profil, technique, soft skills)
- ✅ Recherche RAG pour pré-filtrer les candidats pertinents
- ✅ Classement automatique avec justifications
- ✅ Interface Streamlit interactive
- ✅ Rapports détaillés et explicables

## 🏗️ Architecture

Le système comprend 5 agents spécialisés:

1. **Agent RH** 📋: Analyse les descriptions de poste et génère un profil cible structuré
2. **Agent Profil** 👤: Extrait les informations des CV (NER, compétences, expérience)
3. **Agent Technique** 💻: Évalue les compétences techniques
4. **Agent Soft Skills** 🤝: Analyse les qualités interpersonnelles et la motivation
5. **Agent Décideur** ⚖️: Agrège les scores et génère un classement final justifié

## 🚀 Installation

### Prérequis

- Python 3.9+
- pip

### Étapes d'installation

1. **Cloner le repository** (si applicable)
```bash
cd MULTI-AGENT-CANDIDATE-SELECTION
```

2. **Créer un environnement virtuel** (recommandé)
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Télécharger les modèles spaCy** (optionnel, pour NER avancé)
```bash
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

5. **Configuration** (optionnel)
```bash
cp .env.example .env
# Éditer .env avec vos clés API si vous utilisez OpenAI/GPT
```

## 📖 Utilisation

### 1. Préparation des données

Placez vos fichiers dans les dossiers appropriés:

```
DATA/
├── raw/              # CV bruts (PDF, TXT)
└── jobs/             # Descriptions de poste (PDF, TXT)
```

### 2. Prétraitement des données

Parsez les CV et offres d'emploi:

```python
from src.utils.data_utils import preprocess_all_raw
from src.utils.job_description_parser import preprocess_all_jobs

# Parser les CV
candidates = preprocess_all_raw()

# Parser les offres
jobs = preprocess_all_jobs()
```

### 3. Construction de l'index RAG

Construisez l'index vectoriel pour la recherche de candidats:

```python
from src.rag.build_index import build_index

# Construire l'index
builder = build_index()

# Ou reconstruire depuis zéro
builder = build_index(rebuild=True)
```

Ou depuis la ligne de commande:

```bash
python -m src.rag.build_index --rebuild
```

### 4. Utilisation via Streamlit (Recommandé)

Lancez l'interface web:

```bash
streamlit run src/app/streamlit_app.py
```

Puis ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`).

### 5. Utilisation via Python

```python
from src.main import MultiAgentPipeline

# Initialisation
pipeline = MultiAgentPipeline()
pipeline.initialize_rag()

# Description de l'offre
job_description = """
Data Scientist

Nous recherchons un Data Scientist avec 2 ans d'expérience minimum.
Compétences requises: Python, Machine Learning, Power BI.
Langues: Français, Anglais.
"""

# Traitement
results = pipeline.process_job_offer(job_description)

# Résultats
print(results["report"]["resume"])
for candidate in results["candidates_evaluated"][:5]:
    print(f"{candidate['candidate_id']}: {candidate['score_global']:.1f}/100")
```

## 📁 Structure du Projet

```
MULTI-AGENT-CANDIDATE-SELECTION/
│
├── DATA/
│   ├── raw/                  # CV bruts
│   ├── jobs/                 # Offres d'emploi
│   └── processed/
│       ├── parsed/           # CV parsés (JSON)
│       ├── jobs_parsed/      # Offres parsées (JSON)
│       └── rag_index/        # Index vectoriel RAG
│
├── src/
│   ├── agents/
│   │   ├── agent_rh.py       # Agent RH
│   │   ├── agent_profil.py   # Agent Profil
│   │   ├── agent_technique.py # Agent Technique
│   │   ├── agent_softskills.py # Agent Soft Skills
│   │   └── agent_decideur.py  # Agent Décideur
│   │
│   ├── rag/
│   │   ├── build_index.py    # Construction de l'index RAG
│   │   └── query_index.py    # Requêtes RAG
│   │
│   ├── utils/
│   │   ├── preprocessing.py  # Prétraitement texte
│   │   ├── parsing.py        # Parsing CV
│   │   ├── scoring.py        # Calcul des scores
│   │   ├── data_utils.py     # Utilitaires données
│   │   └── job_description_parser.py # Parsing offres
│   │
│   ├── app/
│   │   └── streamlit_app.py  # Interface Streamlit
│   │
│   ├── config.py             # Configuration
│   └── main.py               # Pipeline principal
│
├── requirements.txt
├── README.md
└── .env.example
```

## 🤖 Agents

### Agent RH

**Rôle**: Analyser les descriptions de poste et extraire un profil structuré.

**Input**: Description de poste (texte)
**Output**: Profil structuré avec:
- Poste, séniorité
- Expérience min/max
- Compétences obligatoires/optionnelles
- Langues, lieu, contrat, salaire

### Agent Profil

**Rôle**: Analyser le profil d'un candidat depuis son CV.

**Input**: CV (texte), lettre de motivation (optionnel)
**Output**: 
- Profil structuré (nom, email, expérience, compétences, diplômes)
- Score de profil (0-100)
- Commentaire justificatif

### Agent Technique

**Rôle**: Évaluer les compétences techniques.

**Input**: Liste de compétences candidat, compétences requises
**Output**:
- Score technique (0-100)
- Compétences correspondantes/manquantes
- Commentaire technique

### Agent Soft Skills

**Rôle**: Évaluer les soft skills et la motivation.

**Input**: Lettre de motivation, expérience, mots-clés
**Output**:
- Score soft skills (0-100)
- Soft skills détectés
- Commentaire sur la motivation

### Agent Décideur

**Rôle**: Agréger les scores et générer un classement final.

**Input**: Tous les scores et commentaires des autres agents
**Output**:
- Score global (pondéré)
- Recommandation (fortement recommandé / recommandé / à rejeter)
- Justification complète
- Classement final des candidats

## 🛠️ Technologies

| Domaine | Outils |
|---------|--------|
| Framework agentique | LangChain |
| NLP et extraction | spaCy, Transformers, Sentence Transformers |
| RAG | ChromaDB, Sentence Transformers |
| Modèles LLM | GPT-4/3.5, Mistral, Claude (optionnel) |
| Interface | Streamlit |
| Traitement PDF | pdfplumber, PyPDF2 |

## 📊 Exemple de Résultat

```
Top 3 candidats:
  1. candidat_01 - Score: 92.3/100 (FORTEMENT RECOMMANDÉ)
  2. candidat_02 - Score: 87.1/100 (RECOMMANDÉ)
  3. candidat_03 - Score: 84.5/100 (RECOMMANDÉ)

Justification candidat_01:
- Profil: Expérience adéquate (3 ans), compétences correspondantes: Python, Power BI
- Technique: Score technique: 95.0/100 (excellent, 8/8 compétences)
- Soft Skills: Score soft skills: 88.0/100 (excellent)
```

## 🔧 Configuration

Les paramètres peuvent être modifiés dans `src/config.py`:

- `WEIGHT_PROFIL`: Poids du score profil (défaut: 0.3)
- `WEIGHT_TECHNIQUE`: Poids du score technique (défaut: 0.4)
- `WEIGHT_SOFTSKILLS`: Poids du score soft skills (défaut: 0.3)
- `EMBEDDING_MODEL`: Modèle d'embeddings (défaut: sentence-transformers/all-MiniLM-L6-v2)
- `TOP_K_CANDIDATES`: Nombre de candidats retournés par RAG (défaut: 10)

## 📝 Notes

- Le système fonctionne sans LLM externe (utilise des règles et heuristiques)
- Pour utiliser un LLM (GPT, Claude, etc.), configurez votre clé API dans `.env`
- L'index RAG doit être construit avant la première utilisation
- Les CV doivent être en format PDF ou TXT dans `DATA/raw/`

## 🤝 Contribution

Ce projet a été développé dans le cadre d'un projet académique sur les systèmes multi-agents.

## 📄 Licence

Ce projet est fourni à des fins éducatives.

## 🙏 Remerciements

- LangChain pour le framework agentique
- ChromaDB pour le stockage vectoriel
- Streamlit pour l'interface utilisateur
- Sentence Transformers pour les embeddings

