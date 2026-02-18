"""
Point d'entrée principal - Version avec nettoyage
"""
import streamlit as st
import os
import sys
from pathlib import Path

# NETTOYAGE COMPLET DU CACHE
st.cache_data.clear()
if 'moex_client' in st.session_state:
    del st.session_state.moex_client

# Ajouter le chemin
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
st.set_page_config(
    page_title="MOEX Dashboard",
    page_icon="🇷🇺",
    layout="wide"
)

# Import des pages
from pages import (
    tableau_de_bord,
    portefeuille,
    alertes,
    indices,
    predictions,
    configuration
)

def main():
    with st.sidebar:
        st.markdown("## 🇷🇺 Navigation")
        page = st.radio(
            "Aller à",
            ["📈 Tableau de bord", "💰 Portefeuille", "🔔 Alertes",
             "📊 Indices", "🤖 Prédictions", "⚙️ Configuration"]
        )
    
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

if __name__ == "__main__":
    main()
