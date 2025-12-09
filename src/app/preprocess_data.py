"""Script pour prétraiter les données (CV et offres)."""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.data_utils import preprocess_all_raw
from src.utils.job_description_parser import preprocess_all_jobs


def main():
    """Prétraite tous les CV et offres disponibles."""
    print("="*60)
    print("PRÉTRAITEMENT DES DONNÉES")
    print("="*60)
    
    print("\n1. Prétraitement des CV...")
    candidates = preprocess_all_raw()
    print(f"   ✓ {len(candidates)} CV(s) traité(s)")
    
    print("\n2. Prétraitement des offres d'emploi...")
    jobs = preprocess_all_jobs()
    print(f"   ✓ {len(jobs)} offre(s) traitée(s)")
    
    print("\n" + "="*60)
    print("PRÉTRAITEMENT TERMINÉ")
    print("="*60)
    print("\nProchaines étapes:")
    print("1. Construire l'index RAG: python -m src.rag.build_index")
    print("2. Lancer l'interface: streamlit run src/app/streamlit_app.py")


if __name__ == "__main__":
    main()
