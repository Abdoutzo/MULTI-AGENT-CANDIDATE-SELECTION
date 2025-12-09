import re
import json
from typing import Any, Dict, List, Optional
from src.utils.job_description_parser import parse_job_description_text

# Liste élargie d'intitulés de poste pour couvrir data/produit/ingénierie/ops/IT
JOB_TITLES = [
    "data scientist",
    "data analyst",
    "ml engineer",
    "machine learning engineer",
    "ai engineer",
    "mlops engineer",
    "data engineer",
    "analytics engineer",
    "business analyst",
    "product manager",
    "product owner",
    "product designer",
    "ux designer",
    "ui designer",
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "fullstack engineer",
    "mobile developer",
    "android developer",
    "ios developer",
    "devops engineer",
    "site reliability engineer",
    "sre",
    "cloud engineer",
    "platform engineer",
    "security engineer",
    "cybersecurity analyst",
    "secops",
    "network engineer",
    "supply chain manager",
    "supply chain analyst",
    "logistics manager",
    "operations manager",
    "finance analyst",
    "financial analyst",
    "risk analyst",
    "data governance",
    "data steward",
    "project manager",
    "scrum master",
    "qa engineer",
    "test engineer",
    "automation engineer",
]

class AgentRH:
    def __init__(self, llm: Any = None):
        self.llm = llm  # futur LLM si besoin

    def analyser_offre(
        self,
        description_poste: str,
        criteres: Optional[Dict] = None,
        cv_parsed: Optional[Dict[str, Any]] = None,
        prefer_llm: bool = True,
    ) -> Dict:
        """
        Analyse une description de poste et retourne un profil cible structuré.
        Si un LLM est fourni et prefer_llm=True, tente un parsing LLM, sinon fallback règles.
        Peut accepter un CV déjà parsé (JSON/dict) pour conserver un contexte minimal.
        """
        criteres = criteres or {}
        desc = description_poste.lower()

        if self.llm and prefer_llm:
            parsed = self._extract_with_llm(description_poste, criteres, cv_parsed)
            if parsed:
                return parsed

        return self._extract_with_rules(desc, description_poste, criteres, cv_parsed)

    def analyser_offre_struct(
        self,
        description_poste: str,
        criteres: Optional[Dict] = None,
        prefer_llm: bool = True,
    ) -> Dict:
        """
        Variante qui renvoie une structure similaire au parseur d'offre (job_description_parser).
        """
        criteres = criteres or {}
        if self.llm and prefer_llm:
            parsed = self._extract_job_with_llm(description_poste, criteres)
            if parsed:
                return parsed

        parsed = parse_job_description_text(description_poste)
        parsed["job_title"] = criteres.get("poste") or parsed.get("job_title", "")
        parsed["exp_min"] = criteres.get("exp_min", parsed.get("exp_min"))
        parsed["exp_max"] = criteres.get("exp_max", parsed.get("exp_max"))
        parsed["salaire_min"] = criteres.get("salaire_min", parsed.get("salaire_min"))
        parsed["salaire_max"] = criteres.get("salaire_max", parsed.get("salaire_max"))
        parsed["contrat"] = criteres.get("contrat") or parsed.get("contrat", "")
        parsed["lieu"] = criteres.get("lieu") or parsed.get("lieu", "")
        parsed["langues"] = criteres.get("langues") or parsed.get("langues", [])
        return parsed

    # ---- Helpers ----
    def _extract_with_llm(
        self,
        description_poste: str,
        criteres: Dict,
        cv_parsed: Optional[Dict[str, Any]],
    ) -> Optional[Dict]:
        """
        Appel LLM (gratuit/local) attendu sous forme de fonction/callable qui retourne du JSON.
        Si le parsing échoue, retourne None pour laisser le fallback règles prendre le relais.
        """
        prompt = f"""
Tu es un agent RH. Analyse la description suivante et renvoie UNIQUEMENT un JSON compact
avec les clés suivantes :
{{
  "poste": "...",
  "seniorite": "...",
  "exp_min": nombre_ou_null,
  "exp_max": nombre_ou_null,
  "skills_obligatoires": ["..."],
  "skills_optionnelles": ["..."],
  "langues": ["..."],
  "lieu": "...",
  "salaire_min": nombre_ou_null,
  "salaire_max": nombre_ou_null,
  "contrat": "...",
  "mots_cles": ["..."],
  "notes_libres": ""
}}
Description de poste :
{description_poste}

Critères donnés par le recruteur (prioritaires si renseignés) :
{json.dumps(criteres, ensure_ascii=False)}
"""
        try:
            llm_response = self.llm(prompt)
            if not llm_response:
                return None
            parsed = llm_response if isinstance(llm_response, dict) else json.loads(llm_response)
            parsed["cv_context"] = self._extract_cv_context(cv_parsed) if cv_parsed else None
            return parsed
        except Exception:
            return None

    def _extract_with_rules(
        self,
        desc: str,
        description_poste: str,
        criteres: Dict,
        cv_parsed: Optional[Dict[str, Any]],
    ) -> Dict:
        """Extraction basique par règles et regex."""

        def find_number(patterns: List[str]) -> Optional[int]:
            for pat in patterns:
                m = re.search(pat, desc)
                if m:
                    try:
                        return int(m.group(1))
                    except ValueError:
                        continue
            return None

        exp_min = criteres.get("exp_min") or find_number([r"(\d+)\s*ans? d[' ]exp", r"(\d+)\+?\s*years"])
        exp_max = criteres.get("exp_max")

        skills_obl = criteres.get("skills_obligatoires") or []
        skills_opt = criteres.get("skills_optionnelles") or []

        profil = {
            "poste": criteres.get("poste") or self._detect_poste(desc),
            "seniorite": criteres.get("seniorite") or self._detect_seniorite(desc),
            "exp_min": exp_min,
            "exp_max": exp_max,
            "skills_obligatoires": skills_obl,
            "skills_optionnelles": skills_opt,
            "langues": criteres.get("langues") or self._detect_langues(desc),
            "lieu": criteres.get("lieu") or self._detect_lieu(desc),
            "salaire_min": criteres.get("salaire_min"),
            "salaire_max": criteres.get("salaire_max"),
            "contrat": criteres.get("contrat") or self._detect_contrat(desc),
            "mots_cles": criteres.get("mots_cles") or self._detect_keywords(desc),
            "notes_libres": criteres.get("notes_libres", ""),
            "raw_description": description_poste.strip(),
        }

        profil["cv_context"] = self._extract_cv_context(cv_parsed) if cv_parsed else None
        return profil

    def _detect_poste(self, desc: str) -> str:
        for title in JOB_TITLES:
            if title in desc:
                return title
        return ""

    def _detect_seniorite(self, desc: str) -> str:
        if any(k in desc for k in ["junior", "debutant", "débutant", "entry"]):
            return "junior"
        if any(k in desc for k in ["senior", "experimente", "expérimenté", "lead"]):
            return "senior"
        if "alternance" in desc or "apprentissage" in desc or "intern" in desc:
            return "intern"
        return "intermediaire"

    def _detect_langues(self, desc: str) -> List[str]:
        langs: List[str] = []
        if "anglais" in desc or "english" in desc:
            langs.append("anglais")
        if "francais" in desc or "français" in desc or "french" in desc:
            langs.append("francais")
        if "espagnol" in desc or "spanish" in desc:
            langs.append("espagnol")
        if "allemand" in desc or "german" in desc:
            langs.append("allemand")
        return langs

    def _detect_lieu(self, desc: str) -> str:
        m = re.search(r"(paris|lyon|lille|remote|télétravail|teletravail|nantes|bordeaux|levallois|perret|idf|ile-de-france)", desc)
        return m.group(1) if m else ""

    def _detect_contrat(self, desc: str) -> str:
        if "cdi" in desc:
            return "CDI"
        if "cdd" in desc:
            return "CDD"
        if "stage" in desc:
            return "Stage"
        if "alternance" in desc or "apprentissage" in desc:
            return "Alternance"
        if "freelance" in desc or "indep" in desc or "indépendant" in desc:
            return "Freelance"
        return ""

    def _detect_keywords(self, desc: str) -> List[str]:
        keywords: List[str] = []
        for kw in [
            "python",
            "r ",
            "sql",
            "power bi",
            "tableau",
            "excel",
            "pandas",
            "spark",
            "dbt",
            "airflow",
            "ml",
            "machine learning",
            "deep learning",
            "nlp",
            "rag",
            "llm",
            "pytorch",
            "tensorflow",
            "cloud",
            "azure",
            "aws",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            "javascript",
            "typescript",
            "react",
            "vue",
            "node",
            "java",
            "c#",
            "dotnet",
            "go",
            "rust",
            "logistique",
            "supply chain",
            "sap",
            "erp",
            "finance",
            "comptabilite",
            "comptabilité",
            "risk",
            "assurance",
        ]:
            if kw in desc:
                keywords.append(kw.strip())
        return keywords

    def _extract_cv_context(self, cv_parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Sélectionne quelques champs utiles du CV parsé (id, skills, langues, email)."""
        return {
            "id": cv_parsed.get("id"),
            "skills_from_cv": cv_parsed.get("skills_list") or [],
            "langues_from_cv": cv_parsed.get("languages_text") or cv_parsed.get("langues") or "",
            "email": cv_parsed.get("email"),
        }

    def _extract_job_with_llm(
        self,
        description_poste: str,
        criteres: Dict,
    ) -> Optional[Dict]:
        """
        Appel LLM pour renvoyer le même format que parse_job_description_text.
        """
        prompt = f"""
Tu es un agent RH. Analyse la description suivante et renvoie UNIQUEMENT un JSON compact
avec les clés suivantes :
{{
  "job_title": "...",
  "raw_text": "...",
  "sections": {{"responsibilities": "", "requirements": "", "skills": "", "soft_skills": "", "benefits": "", "company": ""}},
  "exp_min": nombre_ou_null,
  "exp_max": nombre_ou_null,
  "salaire_min": nombre_ou_null,
  "salaire_max": nombre_ou_null,
  "contrat": "...",
  "lieu": "...",
  "langues": ["..."]
}}
Description de poste :
{description_poste}

Critères donnés par le recruteur (prioritaires si renseignés) :
{json.dumps(criteres, ensure_ascii=False)}
"""
        try:
            llm_response = self.llm(prompt)
            if not llm_response:
                return None
            parsed = llm_response if isinstance(llm_response, dict) else json.loads(llm_response)
            return parsed
        except Exception:
            return None
