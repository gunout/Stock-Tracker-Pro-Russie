"""
Page Dashboard - Nouvelle version sans aucun appel externe
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objs as go

def show():
    """Fonction principale"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    st.success("✅ Page chargée avec succès!")
    
    # Métriques simples
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Test", "100", "5%")
    with col2:
        st.metric("Test", "200", "-2%")
    with col3:
        st.metric("Test", "300", "10%")
    
    # Graphique ultra simple
    st.subheader("Graphique de test")
    
    # Données simples
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    values = np.random.randn(30).cumsum() + 100
    
    # Création directe du graphique (pas de fonction externe)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines',
        name='Test'
    ))
    fig.update_layout(
        title="Test",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau simple
    with st.expander("Données"):
        df = pd.DataFrame({
            'Date': dates,
            'Valeur': values
        })
        st.dataframe(df)
