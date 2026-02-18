"""
Point d'entrée principal - Version corrigée
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

def load_page_module(page_name):
    """Charge dynamiquement un module de page"""
    try:
        if page_name == "📈 Tableau de bord":
            import pages.tableau_de_bord as module
        elif page_name == "💰 Portefeuille":
            import pages.portefeuille as module
        elif page_name == "🔔 Alertes":
            import pages.alertes as module
        elif page_name == "📊 Indices":
            import pages.indices as module
        elif page_name == "🤖 Prédictions":
            import pages.predictions as module
        elif page_name == "⚙️ Configuration":
            import pages.configuration as module
        else:
            return None
        
        # Vérifier que le module a une fonction show()
        if hasattr(module, 'show'):
            return module
        else:
            st.error(f"Le module {page_name} n'a pas de fonction show()")
            return None
            
    except ImportError as e:
        st.error(f"Erreur d'import pour {page_name}: {e}")
        st.info(f"Vérifiez que le fichier pages/{page_name.split()[-1].lower()}.py existe")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue: {e}")
        return None

def main():
    """Fonction principale"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🇷🇺 Navigation")
        
        # Menu
        page = st.radio(
            "Aller à",
            ["📈 Tableau de bord", 
             "💰 Portefeuille", 
             "🔔 Alertes",
             "📊 Indices",
             "🤖 Prédictions",
             "⚙️ Configuration"],
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
        st.info("""
        **Vérifications :**
        1. Le dossier `pages/` existe-t-il ?
        2. Les fichiers `.py` sont-ils présents ?
        3. Chaque fichier a-t-il une fonction `show()` ?
        """)
        
        # Afficher la structure pour debug
        pages_dir = Path(__file__).parent / "pages"
        if pages_dir.exists():
            files = list(pages_dir.glob("*.py"))
            st.write("Fichiers trouvés dans pages/:")
            for f in files:
                st.write(f"- {f.name}")
        else:
            st.error("Le dossier pages/ n'existe pas!")

if __name__ == "__main__":
    main()
