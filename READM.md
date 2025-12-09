readme


## 1. Vision globale du projet

Objectif :

> Construire un **système multi-agents** qui aide un recruteur à **sélectionner des candidats** à partir de CV, lettres de motivation et (optionnel) profils LinkedIn, en combinant :

* Prétraitement + analyse exploratoire
* NLP classique (NER, extraction de compétences)
* **RAG** (base de connaissances + embeddings)
* Un **LLM** (GPT, Mistral…) pour le raisonnement
* Plusieurs **agents spécialisés** + un **agent décideur**
* Une **interface Streamlit** pour la démo

---

## 2. Architecture des agents (fonctionnelle)

Tu peux garder exactement ces 5 agents (théorie + implémentation)  :

1. **Agent RH**

   * Input : description de poste (JD) + critères du recruteur (salaire, séniorité, localisation…)
   * Output :

     * un **profil cible structuré** (dictionnaire / JSON)
       → ex : `{"poste": "Data Scientist", "exp_min": 2, "skills_obligatoires": ["Python", "Power BI"], "langues": ["Français", "Anglais"], ...}`
   * Rôle : normaliser ce que veut le recruteur.

2. **Agent Profil**

   * Input : CV + lettre de motivation (texte brut ou PDF parsé)
   * Tâches :

     * extraction d’infos (NER : nom, école, diplômes, expériences, dates)
     * extraction/normalisation des **compétences** (skills)
     * calcul d’un **score global de matching** profil ↔ offre
   * Output :

     * `profil_structuré` + `score_profil` (0–100)

3. **Agent Technique**

   * Input : profil structuré + exigences techniques (du profil cible)
   * Tâches :

     * check des compétences techniques requises (Python, ML, Cloud…)
     * scoring technique (0–100) + justification textuelle
   * Output :

     * `score_technique`, `commentaire_technique`

4. **Agent Soft Skills**

   * Input : lettre de motivation + éventuellement expérience + mots-clés du recruteur (teamwork, communication, autonomie)
   * Tâches :

     * analyse de ton (motivation, clarté, cohérence)
     * extraction d’indices sur soft skills
     * scoring soft skills (0–100) + justification
   * Output :

     * `score_softskills`, `commentaire_softskills`

5. **Agent Décideur**

   * Input : tous les scores + commentaires des autres agents
   * Tâches :

     * agrégation (pondération des scores : ex. 40% technique, 30% profil, 30% soft skills)
     * classification : “fortement recommandé / recommandé / à rejeter”
     * **classement final des candidats** + **rapport explicable**
   * Output :

     * tableau final : `[(id_candidat, score_global, résumé_justification), ...]`

---

## 3. Pipeline technique détaillé

### Étape 0 – Données & setup

* Choisir un **jeu de CV + lettres** (vrais ou simulés).
* Stockage des documents (dossier `data/raw`).
* Enregistrer les descriptions de postes (plusieurs cas d’usage).

### Étape 1 – Prétraitement & analyse exploratoire (obligatoire) 

Dans le rapport vous montrez :

1. **Parsing des documents**

   * PDF → texte : `pdfplumber`, `PyPDF2`, `textract`, etc.
   * Normalisation : lowercasing, suppression des caractères spéciaux…

2. **Analyse exploratoire (EDA)**

   * stats : nb de candidats, diplômes les plus fréquents, répartition des années d’XP…
   * nuages de mots sur les compétences
   * histogramme des skills techniques (Python, SQL, Power BI…)

3. **Construction d’un dataset structuré**

   * un CSV / JSON du type :

```json
{
  "id": "CAND_01",
  "nom": "Dupont",
  "annees_experience": 3,
  "skills": ["Python", "Power BI", "SQL"],
  "langues": ["FR", "EN"],
  "texte_cv": "...",
  "texte_lettre": "..."
}
```

### Étape 2 – RAG & embeddings

Idée :

* Construire une **base de connaissances** des candidats (CV, expériences, projets).
* Utiliser des **embeddings** pour faire des similarités entre offre et candidats.

Pipeline :

1. Choix d’un modèle d’embeddings (OpenAI embeddings ou modèle local type `sentence-transformers`).
2. Construction d’un **index vectoriel** (ChromaDB, FAISS, LlamaIndex).
3. Pour chaque candidat :

   * indexer son CV + lettre comme documents.
4. Lorsqu’une offre arrive :

   * créer une requête textuelle (par Agent RH) :
     “Data Scientist, 2 ans d’XP, Python + Power BI, secteur X”
   * récupérer les candidats les plus proches via RAG (top-k).

### Étape 3 – Implémentation des agents

Tu peux choisir :

* **CrewAI**, **LangGraph** ou **LangChain** pour orchestrer les agents (comme le sujet le suggère). 
* Chaque agent est une **classe Python** ou un “Tool/Agent” dans le framework.

Exemple de style (pseudo-code simple) :

```python
class AgentRH:
    def __init__(self, llm):
        self.llm = llm

    def analyser_offre(self, description_poste: str) -> dict:
        prompt = f"""
        Tu es un expert RH. À partir de la description suivante, extrais un profil structuré...
        {description_poste}
        """
        reponse = self.llm(prompt)
        return json.loads(reponse)  # ou parsing manuel
```

Même logique pour AgentProfil, AgentTechnique, etc.

### Étape 4 – Agrégation & scoring (Agent Décideur)

Un exemple simple :

```python
score_global = (
    0.3 * score_profil +
    0.4 * score_technique +
    0.3 * score_softskills
)
```

L’agent décideur génère ensuite une **justification détaillée** en langage naturel en se basant sur :

* les scores
* les commentaires des autres agents
* la description de poste

---

## 4. Organisation du code dans ton repo GitHub

Dans ton repo `MULTI-AGENT-CANDIDATE-SELECTION`, je te suggère ceci :

```text
MULTI-AGENT-CANDIDATE-SELECTION/
│
├── README.md
├── requirements.txt
├── src/
│   ├── data/
│   │   ├── raw/          # CV, lettres, profils bruts
│   │   └── processed/    # JSON/CSV nettoyés
│   ├── agents/
│   │   ├── agent_rh.py
│   │   ├── agent_profil.py
│   │   ├── agent_technique.py
│   │   ├── agent_softskills.py
│   │   └── agent_decideur.py
│   ├── rag/
│   │   ├── build_index.py
│   │   └── query_index.py
│   ├── utils/
│   │   ├── parsing_cv.py
│   │   ├── preprocessing.py
│   │   └── scoring.py
│   ├── app/
│   │   └── streamlit_app.py
│   └── main.py           # script principal: enchaîne les agents
│
└── report/
    ├── rapport.pdf
    └── slides.pptx
```

👉 Chaque membre du groupe peut prendre une “brique” :

* Personne A : prétraitement + EDA + parsing
* Personne B : RAG + embeddings
* Personne C : Agents (profil, technique, soft skills)
* Personne D : Agent décideur + Streamlit + rapport

---

## 5. Rapport technique (structure pour viser 20/20)

Tu peux organiser ainsi :

1. **Introduction**

   * Contexte RH, problématique de sélection
   * Objectif du projet

2. **Cadre théorique**

   * Multi-Agents (définition, architectures, coordination)
   * RAG (principe index + retrieval + generation)
   * LLM & NLP (embeddings, NER, scoring textuel)
   * Explicabilité (XAI, SHAP ou justification textuelle) 

3. **Données & Prétraitement**

   * Source des CV / lettres
   * Méthodes de parsing & nettoyage
   * Analyse exploratoire (graphes, tableaux)

4. **Architecture du Système**

   * Description détaillée des 5 agents
   * Diagrammes (diagramme de séquence, vue globale)
   * Flux : recruteur → Agent RH → RAG → Agents → Décideur

5. **Implémentation**

   * Choix technos (LangChain/CrewAI, spaCy, ChromaDB, Streamlit…)
   * Structures de données (JSON, index vectoriel, classes agents)
   * Exemples de prompts clés

6. **Expérimentations & Résultats**

   * Cas d’usage : ex. “Data Scientist 2 ans Python + Power BI” 
   * Classement de plusieurs candidats (tableau)
   * Discussion : cohérence des classements, transferts possibles vers d’autres postes

7. **Interface & Déploiement**

   * Captures de la web app Streamlit
   * Explication du fonctionnement (input JD, affichage top candidats)

8. **Limites & Pistes d’amélioration**

   * Biais du LLM, qualité des CV, données limitées…
   * Idées futures (connexion à LinkedIn API, feedback des recruteurs…)

---

## 6. Démo Streamlit (pour la vidéo 15–20 min)

Interface simple mais efficace :

* Zone de texte : **description de poste**
* Bouton : **“Analyser les candidats”**
* Zone d’affichage :

  * Tableau : `Candidat | Score Profil | Score Tech | Score Soft Skills | Score Global | Recommandation`
  * Quand on clique sur un candidat → afficher la justification détaillée générée par l’agent Décideur.

---

Si tu veux, **dans le prochain message**, je peux :

* soit te proposer un **squelette de code Python** (`main.py` + 1 agent complet en exemple),
* soit un **plan détaillé de répartition des tâches du groupe + planning** jusqu’à la date de rendu.

Dis-moi ce que tu préfères, et on construit ton 20/20 ensemble 😉
