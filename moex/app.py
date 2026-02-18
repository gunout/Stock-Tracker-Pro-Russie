"""
Application principale - Version corrigée
"""
import streamlit as st
import sys
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="MOEX Dashboard",
    page_icon="🇷🇺",
    layout="wide"
)

# Ajouter le chemin au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Imports des pages (sans chiffres)
try:
    from pages import (
        page_tableau_de_bord,
        page_portefeuille,
        page_alertes,
        page_indices,
        page_predictions,
        page_configuration
    )
    PAGES_OK = True
except ImportError as e:
    st.error(f"Erreur d'import des pages: {e}")
    PAGES_OK = False

def main():
    """Fonction principale"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🇷🇺 Navigation")
        
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
        
        if st.button("🔄 Rafraîchir"):
            st.cache_data.clear()
            st.rerun()
    
    # Vérification
    if not PAGES_OK:
        st.error("Impossible de charger les pages")
        return
    
    # Routage
    try:
        if page == "📈 Tableau de bord":
            page_tableau_de_bord.show()
        elif page == "💰 Portefeuille":
            page_portefeuille.show()
        elif page == "🔔 Alertes":
            page_alertes.show()
        elif page == "📊 Indices":
            page_indices.show()
        elif page == "🤖 Prédictions":
            page_predictions.show()
        elif page == "⚙️ Configuration":
            page_configuration.show()
    except Exception as e:
        st.error(f"Erreur: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
