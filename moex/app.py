"""
Point d'entrée principal de l'application Dashboard MOEX
"""
import streamlit as st
from src.utils.constants import PAGE_CONFIG
from src.utils.time_utils import setup_timezone
from src.utils.session import init_session_state
from src.api.moex_client import MOEXClient
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration de la page Streamlit
st.set_page_config(**PAGE_CONFIG)

# Import des pages après configuration
from pages import (
    tableau_de_bord,
    portefeuille,
    alertes,
    indices,
    predictions,
    configuration
)

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    setup_timezone()
    init_session_state()
    
    # Initialisation du client API
    if 'moex_client' not in st.session_state:
        st.session_state.moex_client = MOEXClient()
    
    # Sidebar
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/images/logo.png", width=100)
        
        st.markdown("---")
        st.markdown("## 🇷🇺 Navigation")
        
        # Menu principal
        page = st.radio(
            "Aller à",
            ["📈 Tableau de bord", 
             "💰 Portefeuille", 
             "🔔 Alertes",
             "📊 Indices",
             "🤖 Prédictions",
             "⚙️ Configuration"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Informations temps réel
        if st.session_state.get('last_update'):
            st.caption(f"Dernière MAJ: {st.session_state.last_update}")
        
        # Statut du marché
        from src.utils.time_utils import get_market_status
        status, icon = get_market_status()
        st.caption(f"{icon} Marché: {status}")
        
        # Bouton de rafraîchissement
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Routing vers les pages
    if page == "📈 Tableau de bord":
        tableau_de_bord.show()
    elif page == "💰 Portefeuille":
        portefeuille.show()
    elif page == "🔔 Alertes":
        alertes.show()
    elif page == "📊 Indices":
        indices.show()
    elif page == "🤖 Prédictions":
        predictions.show()
    elif page == "⚙️ Configuration":
        configuration.show()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8rem;'>
            🇷🇺 Dashboard MOEX - Données en temps réel via API officielle<br>
            🕐 Tous les horaires en UTC+4 | 
            <a href='https://iss.moex.com/iss/reference/' target='_blank'>Documentation API</a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()