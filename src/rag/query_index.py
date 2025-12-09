"""Requêtes sur l'index pour trouver les candidats proches d'une offre."""
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer
import chromadb

from src.config import RAG_INDEX_DIR, EMBEDDING_MODEL, VECTOR_STORE_TYPE, TOP_K_CANDIDATES
from src.rag.build_index import RAGIndexBuilder


class RAGQueryEngine:
    """Moteur de requêtes RAG pour trouver des candidats pertinents."""
    
    def __init__(self, embedding_model: str = None, vector_store_type: str = None):
        """
        Args:
            embedding_model: Nom du modèle d'embeddings
            vector_store_type: Type de vector store
        """
        self.embedding_model_name = embedding_model or EMBEDDING_MODEL
        self.vector_store_type = vector_store_type or VECTOR_STORE_TYPE
        self.embedding_model = None
        self.client = None
        self.collection = None
    
    def initialize(self):
        """Initialise le modèle et la connexion au vector store."""
        if not self.embedding_model:
            print(f"[INFO] Chargement du modèle d'embeddings: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        if self.vector_store_type == "chroma":
            if not RAG_INDEX_DIR.exists():
                raise ValueError(f"Index RAG non trouvé dans {RAG_INDEX_DIR}. Exécutez build_index.py d'abord.")
            
            self.client = chromadb.PersistentClient(
                path=str(RAG_INDEX_DIR),
                settings=chromadb.config.Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="candidates",
                metadata={"hnsw:space": "cosine"}
            )
            print("[INFO] Connexion à l'index ChromaDB établie")
    
    def query(
        self,
        query_text: str,
        top_k: int = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche des candidats pertinents pour une requête.
        
        Args:
            query_text: Texte de la requête (description de poste, critères)
            top_k: Nombre de résultats à retourner
            filter_metadata: Filtres sur les métadonnées (ex: {"years_experience": "3"})
        
        Returns:
            Liste de dicts avec:
            - candidate_id: ID du candidat
            - score: score de similarité
            - document: texte du document
            - metadata: métadonnées du candidat
        """
        if not self.collection:
            self.initialize()
        
        top_k = top_k or TOP_K_CANDIDATES
        
        # Embedding de la requête
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        # Recherche dans ChromaDB
        if self.vector_store_type == "chroma":
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Formatage des résultats
            candidates = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    candidate_id = results["ids"][0][i]
                    distance = results["distances"][0][i]
                    score = 1 - distance  # Convertir distance en score de similarité
                    document = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    
                    candidates.append({
                        "candidate_id": candidate_id,
                        "score": score,
                        "distance": distance,
                        "document": document,
                        "metadata": metadata
                    })
            
            return candidates
        
        return []
    
    def query_by_job_profile(self, job_profile: Dict, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Recherche des candidats pertinents pour un profil de poste.
        
        Args:
            job_profile: Dict avec les clés du profil de poste
            top_k: Nombre de résultats
        
        Returns:
            Liste de candidats pertinents
        """
        # Construction de la requête textuelle depuis le profil
        query_parts = []
        
        if job_profile.get("poste"):
            query_parts.append(f"Poste: {job_profile['poste']}")
        
        if job_profile.get("skills_obligatoires"):
            query_parts.append(f"Compétences requises: {', '.join(job_profile['skills_obligatoires'])}")
        
        if job_profile.get("exp_min"):
            query_parts.append(f"Expérience minimale: {job_profile['exp_min']} ans")
        
        query_text = ". ".join(query_parts)
        
        # Filtres optionnels sur métadonnées
        filter_metadata = None
        if job_profile.get("exp_min"):
            # Note: ChromaDB filtre sur strings, donc conversion
            filter_metadata = {
                "years_experience": {"$gte": str(job_profile["exp_min"])}
            }
        
        return self.query(query_text, top_k=top_k, filter_metadata=filter_metadata)


def query_candidates(
    query_text: str,
    top_k: int = None,
    job_profile: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour rechercher des candidats.
    
    Args:
        query_text: Texte de la requête
        top_k: Nombre de résultats
        job_profile: Profil de poste (optionnel, pour requête enrichie)
    
    Returns:
        Liste de candidats pertinents
    """
    engine = RAGQueryEngine()
    
    if job_profile:
        return engine.query_by_job_profile(job_profile, top_k=top_k)
    else:
        return engine.query(query_text, top_k=top_k)


if __name__ == "__main__":
    # Test de la requête
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python query_index.py 'requête textuelle'")
        sys.exit(1)
    
    query = sys.argv[1]
    engine = RAGQueryEngine()
    results = engine.query(query, top_k=5)
    
    print(f"\nRésultats pour: '{query}'\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['candidate_id']} (score: {result['score']:.3f})")
        print(f"   {result['document'][:200]}...\n")
