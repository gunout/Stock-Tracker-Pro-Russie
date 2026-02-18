"""
Page Indices MOEX
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objs as go

indices = {
    'IMOEX': 'MOEX Russia Index',
    'RTSI': 'RTS Index',
    'RGBI': 'Russian Government Bond Index'
}

def get_index_data(index, days=30):
    """Récupère les données d'un indice"""
    try:
        url = f"https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics/{index}.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data
    except:
        return None

def show():
    st.markdown("# 📊 Indices MOEX")
    
    selected = st.selectbox("Choisir un indice", list(indices.keys()))
    
    if selected:
        st.subheader(indices[selected])
        
        # Données simulées pour l'exemple (à remplacer par API réelle)
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        values = 3000 + np.cumsum(np.random.randn(100) * 20)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name=selected))
        fig.update_layout(height=500)
        st.plotly_chart(fig)
