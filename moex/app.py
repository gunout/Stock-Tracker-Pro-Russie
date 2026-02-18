"""
Application principale
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="MOEX Dashboard",
    page_icon="🇷🇺",
    layout="wide"
)

# Import des pages
try:
    from pages import (
        page_dashboard,  # Nouveau nom
        page_portefeuille,
        page_alertes,
        page_indices,
        page_predictions,
        page_configuration
    )
    PAGES_OK = True
except ImportError as e:
    st.error(f"Erreur d'import: {e}")
    PAGES_OK = False

def main():
    with st.sidebar:
        st.markdown("## 🇷🇺 Navigation")
        page = st.radio(
            "Aller à",
            ["📈 Tableau de bord", 
             "💰 Portefeuille", 
             "🔔 Alertes",
             "📊 Indices",
             "🤖 Prédictions",
             "⚙️ Configuration"]
        )
    
    if not PAGES_OK:
        st.error("Erreur de chargement")
        return
    
    try:
        if page == "📈 Tableau de bord":
            page_dashboard.show()  # Nouveau nom
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
