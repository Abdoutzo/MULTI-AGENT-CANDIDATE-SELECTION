"""Création de l'index vectoriel pour les documents candidats."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from src.config import RAG_INDEX_DIR, EMBEDDING_MODEL, VECTOR_STORE_TYPE
from src.utils.data_utils import PARSED_DIR, list_raw_files, parse_raw_file


class RAGIndexBuilder:
    """Builder pour créer et gérer l'index vectoriel RAG."""
    
    def __init__(self, embedding_model: str = None, vector_store_type: str = None):
        """
        Args:
            embedding_model: Nom du modèle d'embeddings
            vector_store_type: Type de vector store ('chroma' ou 'faiss')
        """
        self.embedding_model_name = embedding_model or EMBEDDING_MODEL
        self.vector_store_type = vector_store_type or VECTOR_STORE_TYPE
        self.embedding_model = None
        self.client = None
        self.collection = None
    
    def initialize(self):
        """Initialise le modèle d'embeddings et le vector store."""
        print(f"[INFO] Chargement du modèle d'embeddings: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        if self.vector_store_type == "chroma":
            RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(RAG_INDEX_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="candidates",
                metadata={"hnsw:space": "cosine"}
            )
            print("[INFO] Index ChromaDB initialisé")
        else:
            raise ValueError(f"Vector store type non supporté: {self.vector_store_type}")
    
    def build_index_from_candidates(self, candidates: List[Dict] = None) -> int:
        """
        Construit l'index à partir d'une liste de candidats.
        
        Args:
            candidates: Liste de dicts candidats. Si None, charge depuis PARSED_DIR
        
        Returns:
            Nombre de documents indexés
        """
        if not self.embedding_model:
            self.initialize()
        
        if candidates is None:
            candidates = self._load_candidates_from_files()
        
        if not candidates:
            print("[WARNING] Aucun candidat à indexer")
            return 0
        
        print(f"[INFO] Indexation de {len(candidates)} candidat(s)...")
        
        documents = []
        metadatas = []
        ids = []
        
        for candidate in candidates:
            # Création du document texte pour embedding
            doc_text = self._create_document_text(candidate)
            
            # Embedding
            embedding = self.embedding_model.encode(doc_text).tolist()
            
            documents.append(doc_text)
            metadatas.append({
                "candidate_id": candidate.get("id", ""),
                "email": candidate.get("email", ""),
                "skills": ", ".join(candidate.get("skills_list", [])[:10]),
                "years_experience": str(candidate.get("years_experience", 0)),
            })
            ids.append(candidate.get("id", f"cand_{len(ids)}"))
        
        # Ajout à ChromaDB
        if self.vector_store_type == "chroma":
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[OK] {len(documents)} document(s) indexé(s)")
        
        return len(documents)
    
    def _create_document_text(self, candidate: Dict) -> str:
        """Crée un texte de document à partir d'un candidat."""
        parts = []
        
        # Compétences
        skills = candidate.get("skills_list", [])
        if skills:
            parts.append(f"Compétences: {', '.join(skills)}")
        
        # Expérience
        exp_text = candidate.get("experience_text", "")
        if exp_text:
            parts.append(f"Expérience: {exp_text[:500]}")
        
        # Éducation
        edu_text = candidate.get("education_text", "")
        if edu_text:
            parts.append(f"Formation: {edu_text[:300]}")
        
        # Texte brut
        raw_text = candidate.get("raw_text", "")
        if raw_text:
            parts.append(raw_text[:1000])
        
        return "\n\n".join(parts)
    
    def _load_candidates_from_files(self) -> List[Dict]:
        """Charge les candidats depuis les fichiers JSON parsés."""
        candidates = []
        
        if not PARSED_DIR.exists():
            print(f"[WARNING] Dossier {PARSED_DIR} n'existe pas")
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
    
    def rebuild_index(self):
        """Reconstruit l'index (supprime l'ancien et en crée un nouveau)."""
        if self.vector_store_type == "chroma" and self.client:
            try:
                self.client.delete_collection("candidates")
                print("[INFO] Ancien index supprimé")
            except Exception:
                pass
        
        self.initialize()
        return self.build_index_from_candidates()


def build_index(candidates: List[Dict] = None, rebuild: bool = False) -> RAGIndexBuilder:
    """
    Fonction utilitaire pour construire l'index.
    
    Args:
        candidates: Liste de candidats (optionnel)
        rebuild: Si True, reconstruit l'index
    
    Returns:
        Instance de RAGIndexBuilder
    """
    builder = RAGIndexBuilder()
    
    if rebuild:
        builder.rebuild_index()
    else:
        builder.initialize()
        builder.build_index_from_candidates(candidates)
    
    return builder


if __name__ == "__main__":
    # Script pour construire l'index depuis la ligne de commande
    import argparse
    
    parser = argparse.ArgumentParser(description="Construire l'index RAG")
    parser.add_argument("--rebuild", action="store_true", help="Reconstruire l'index")
    args = parser.parse_args()
    
    builder = build_index(rebuild=args.rebuild)
    print("[OK] Index construit avec succès")
