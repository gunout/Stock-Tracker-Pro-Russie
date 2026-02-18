"""
Point d'entrée principal de l'application Dashboard MOEX
"""
import streamlit as st
import os
import sys
import logging
from pathlib import Path

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.constants import PAGE_CONFIG
from src.utils.time_utils import setup_timezone
from src.utils.session import init_session_state
from src.api.moex_client import MOEXClient

# Créer les dossiers nécessaires
os.makedirs('logs', exist_ok=True)
os.makedirs('cache', exist_ok=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration de la page Streamlit
st.set_page_config(**PAGE_CONFIG)

# Import dynamique des pages pour éviter les erreurs d'import
def load_page(page_name):
    """Charge dynamiquement un module de page"""
    try:
        if page_name == "📈 Tableau de bord":
            from pages import tableau_de_bord
            return tableau_de_bord
        elif page_name == "💰 Portefeuille":
            from pages import portefeuille
            return portefeuille
        elif page_name == "🔔 Alertes":
            from pages import alertes
            return alertes
        elif page_name == "📊 Indices":
            from pages import indices
            return indices
        elif page_name == "🤖 Prédictions":
            from pages import predictions
            return predictions
        elif page_name == "⚙️ Configuration":
            from pages import configuration
            return configuration
    except ImportError as e:
        logger.error(f"Erreur d'import pour {page_name}: {e}")
        return None

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    setup_timezone()
    init_session_state()
    
    # Initialisation du client API
    if 'moex_client' not in st.session_state:
        try:
            st.session_state.moex_client = MOEXClient()
        except Exception as e:
            st.error(f"Erreur d'initialisation du client API: {e}")
            st.session_state.moex_client = None
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center;'>
            <h1 style='color: #D52B1E;'>🇷🇺 MOEX</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("## Navigation")
        
        # Menu principal
        page = st.radio(
            "Aller à",
            ["📈 Tableau de bord", 
             "💰 Portefeuille", 
             "🔔 Alertes",
             "📊 Indices",
             "🤖 Prédictions",
             "⚙️ Configuration"],
            label_visibility="collapsed",
            key="navigation"
        )
        
        st.markdown("---")
        
        # Informations système
        st.caption(f"Python: {sys.version[:6]}")
        st.caption(f"Streamlit: {st.__version__}")
        
        # Bouton de rafraîchissement
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Chargement et affichage de la page sélectionnée
    page_module = load_page(page)
    if page_module and hasattr(page_module, 'show'):
        try:
            page_module.show()
        except Exception as e:
            st.error(f"Erreur lors de l'affichage de la page: {e}")
            st.exception(e)
    else:
        st.error(f"Impossible de charger la page: {page}")
        st.info("Vérifiez que tous les fichiers de pages existent dans le dossier `pages/`")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: gray; font-size: 0.8rem;'>
            🇷🇺 Dashboard MOEX - Version 1.0.0<br>
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    from datetime import datetime
    main()
