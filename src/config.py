"""Configuration globale du projet (paths, paramètres)."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "DATA"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = PROCESSED_DIR / "parsed"
JOBS_DIR = DATA_DIR / "jobs"
JOBS_PARSED_DIR = PROCESSED_DIR / "jobs_parsed"

# RAG Configuration
RAG_INDEX_DIR = PROCESSED_DIR / "rag_index"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")  # chroma or faiss

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

# Agent Scoring Weights (for Agent Décideur)
WEIGHT_PROFIL = 0.3
WEIGHT_TECHNIQUE = 0.4
WEIGHT_SOFTSKILLS = 0.3

# RAG Parameters
TOP_K_CANDIDATES = 10
SIMILARITY_THRESHOLD = 0.5

# Streamlit Configuration
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"
