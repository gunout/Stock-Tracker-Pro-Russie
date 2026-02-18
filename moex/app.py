"""
Point d'entrée principal - Version corrigée avec noms de fichiers exacts
"""
import streamlit as st
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
st.set_page_config(
    page_title="MOEX Dashboard",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Créer les dossiers nécessaires
os.makedirs('logs', exist_ok=True)
os.makedirs('cache', exist_ok=True)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Mapping entre les noms d'affichage et les noms de fichiers
PAGE_MAPPING = {
    "📈 Tableau de bord": "1_📈_tableau_de_bord",
    "💰 Portefeuille": "2_💰_portefeuille",
    "🔔 Alertes": "3_🔔_alertes",
    "📊 Indices": "4_📊_indices",
    "🤖 Prédictions": "5_🤖_predictions",
    "⚙️ Configuration": "6_⚙️_configuration"
}

def load_page_module(page_name):
    """Charge dynamiquement un module de page basé sur le nom d'affichage"""
    try:
        # Obtenir le nom du fichier correspondant
        module_name = PAGE_MAPPING.get(page_name)
        if not module_name:
            st.error(f"Nom de page inconnu: {page_name}")
            return None
        
        # Importer le module
        import importlib
        module = importlib.import_module(f"pages.{module_name}")
        
        # Vérifier que le module a une fonction show()
        if hasattr(module, 'show'):
            return module
        else:
            st.error(f"Le module {module_name} n'a pas de fonction show()")
            return None
            
    except ImportError as e:
        st.error(f"Erreur d'import pour {page_name} (fichier: {module_name}): {e}")
        
        # Afficher les fichiers disponibles pour aider au debugging
        pages_dir = Path(__file__).parent / "pages"
        if pages_dir.exists():
            files = list(pages_dir.glob("*.py"))
            st.info("Fichiers disponibles dans pages/:")
            for f in files:
                st.write(f"- {f.name}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue: {e}")
        return None

def main():
    """Fonction principale"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center;'>
            <h1 style='color: #D52B1E;'>🇷🇺 MOEX</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("## Navigation")
        
        # Menu avec les options d'affichage
        page = st.radio(
            "Aller à",
            list(PAGE_MAPPING.keys()),  # Utiliser les clés du mapping
            key="nav"
        )
        
        st.markdown("---")
        st.caption(f"Heure: {datetime.now().strftime('%H:%M:%S')}")
        
        if st.button("🔄 Rafraîchir"):
            st.cache_data.clear()
            st.rerun()
    
    # Charger et afficher la page
    module = load_page_module(page)
    
    if module:
        try:
            module.show()
        except Exception as e:
            st.error(f"Erreur lors de l'exécution de la page: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error(f"Impossible de charger la page: {page}")

if __name__ == "__main__":
    main()
