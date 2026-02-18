"""
Page Tableau de bord - Version 100% autonome
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

def show():
    """Fonction principale - Tout est dans cette fonction"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    st.info("🎮 Mode démonstration - Données simulées")
    
    # ========== MÉTRIQUES ==========
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("SBER", "280.50 ₽", "+1.2%")
    with col2:
        st.metric("GAZP", "165.80 ₽", "-0.5%")
    with col3:
        st.metric("LKOH", "7200.50 ₽", "+2.1%")
    with col4:
        st.metric("YNDX", "2850.00 ₽", "+1.8%")
    
    # ========== GRAPHIQUE SIMPLE ==========
    st.subheader("Évolution simulée")
    
    # Générer des données de test
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    # Graphique avec Plotly (directement ici, pas de fonction externe)
    import plotly.graph_objs as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name='Prix',
        line=dict(color='#D52B1E', width=2)
    ))
    fig.update_layout(
        title="Évolution du prix (simulé)",
        xaxis_title="Date",
        yaxis_title="Prix (₽)",
        height=500,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== TABLEAU DES DONNÉES ==========
    with st.expander("📊 Voir les données simulées"):
        df = pd.DataFrame({
            'Date': dates.strftime('%Y-%m-%d'),
            'Prix': prices.round(2)
        })
        st.dataframe(df, use_container_width=True)
    
    # ========== INFORMATIONS ==========
    with st.expander("ℹ️ À propos"):
        st.markdown("""
        **Mode démonstration**
        
        Cette page affiche des données simulées en attendant la connexion à l'API MOEX.
        
        **Fonctionnalités à venir :**
        - Données en temps réel
        - Graphiques en bougies japonaises
        - Indicateurs techniques
        - Portefeuille virtuel
        """)
