"""
Application principale - Version simplifiée
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

# Imports directs des pages (sans emojis dans les noms)
try:
    from pages import (
        1_tableau_de_bord as tableau_de_bord,
        2_portefeuille as portefeuille,
        3_alertes as alertes,
        4_indices as indices,
        5_predictions as predictions,
        6_configuration as configuration
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
        
        # Menu sans emojis dans les valeurs (mais affichés)
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
    
    # Vérification des imports
    if not PAGES_OK:
        st.error("Impossible de charger les pages. Vérifiez la structure du dossier pages/")
        return
    
    # Routage
    try:
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
    except Exception as e:
        st.error(f"Erreur d'affichage: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
