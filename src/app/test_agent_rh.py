"""
Petit script de test pour l'Agent RH avec un LLM local (exemple Ollama).
Exécute depuis la racine : `python -m src.app.test_agent_rh`
Il parse une offre dans DATA/jobs, appelle l'AgentRH en mode LLM si possible,
et écrit le résultat dans DATA/processed/jobs_parsed/<job_id>_agent_llm.json.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.agents.agent_rh import AgentRH
from src.utils.job_description_parser import parse_job_description_file


# Adaptable : nom du fichier d'offre et modèle Ollama
JOB_FILE = Path("DATA/jobs/Stagiaire Logistique Performance & Projet - Lucas FRANCOIS.pdf")
OLLAMA_MODEL = "llama3"  # à ajuster si besoin (ex. mistral)


def ollama_llm(prompt: str) -> str:
    """
    Appelle un modèle local via Ollama et renvoie la réponse brute.
    Assure-toi qu'Ollama et le modèle sont installés.
    """
    return subprocess.check_output(["ollama", "run", OLLAMA_MODEL, prompt], text=True)


def main() -> None:
    job_path = JOB_FILE.resolve()
    jd = parse_job_description_file(job_path)

    agent = AgentRH(llm=ollama_llm)
    res = agent.analyser_offre_struct(jd["raw_text"], prefer_llm=True)

    out_path = Path("DATA/processed/jobs_parsed") / f"{jd['job_id']}_agent_llm.json"
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Résultat LLM écrit dans: {out_path}")


if __name__ == "__main__":
    main()
