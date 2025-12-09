# 🚀 Guide de Démarrage Rapide

Ce guide vous aidera à démarrer rapidement avec le système multi-agents de sélection de candidats.

## Étapes Rapides

### 1. Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

### 2. Préparer les Données

Placez vos fichiers dans les dossiers appropriés:

```
DATA/
├── raw/
│   ├── cv_candidat1.pdf
│   ├── cv_candidat2.txt
│   └── ...
└── jobs/
    ├── offre_data_scientist.pdf
    └── ...
```

### 3. Prétraiter les Données

```bash
# Option 1: Via Python
python -m src.app.preprocess_data

# Option 2: Via le code Python
python
>>> from src.utils.data_utils import preprocess_all_raw
>>> from src.utils.job_description_parser import preprocess_all_jobs
>>> preprocess_all_raw()
>>> preprocess_all_jobs()
```

### 4. Construire l'Index RAG

```bash
# Construire l'index
python -m src.rag.build_index

# Ou reconstruire depuis zéro
python -m src.rag.build_index --rebuild
```

### 5. Lancer l'Interface Streamlit

```bash
streamlit run src/app/streamlit_app.py
```

Ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`).

## Exemple d'Utilisation

### Via Streamlit (Recommandé)

1. Ouvrez l'interface Streamlit
2. Cliquez sur "Initialiser le Pipeline" dans la sidebar
3. Saisissez ou uploadez une description de poste
4. Cliquez sur "Lancer l'Évaluation"
5. Consultez les résultats et le classement

### Via Python

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

# Afficher les résultats
for i, candidate in enumerate(results["candidates_evaluated"][:5], 1):
    print(f"{i}. {candidate['candidate_id']}: {candidate['score_global']:.1f}/100")
    print(f"   {candidate['recommandation']}")
    print()
```

## Structure des Données

### Format CV

Les CV peuvent être en format:
- PDF (`.pdf`)
- Texte brut (`.txt`)

Ils seront automatiquement parsés et structurés.

### Format Offre d'Emploi

Les offres peuvent être en format:
- PDF (`.pdf`)
- Texte brut (`.txt`)

Ou saisies directement dans l'interface Streamlit.

## Dépannage

### Erreur: "Index RAG non trouvé"

Solution: Construisez l'index RAG d'abord:
```bash
python -m src.rag.build_index
```

### Erreur: "Aucun candidat trouvé"

Solution: Vérifiez que:
1. Les CV sont dans `DATA/raw/`
2. Vous avez exécuté le prétraitement
3. Les fichiers JSON sont dans `DATA/processed/parsed/`

### Erreur: "Module non trouvé"

Solution: Assurez-vous d'être dans le bon répertoire et que les dépendances sont installées:
```bash
pip install -r requirements.txt
```

## Prochaines Étapes

- Consultez le [README.md](README.md) pour plus de détails
- Explorez les agents dans `src/agents/`
- Personnalisez les poids de scoring dans `src/config.py`
- Ajoutez votre propre LLM en configurant `.env`

## Support

Pour toute question ou problème, consultez:
- Le README principal
- La documentation des agents
- Les exemples dans le code

