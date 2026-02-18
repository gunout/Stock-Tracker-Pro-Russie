"""
Page Tableau de bord - Connectée à l'API MOEX
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objs as go
import requests

def get_moex_candles(ticker, days=30):
    """
    Récupère les données historiques de l'API MOEX
    """
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json"
        
        end = datetime.now()
        start = end - timedelta(days=days)
        
        params = {
            'from': start.strftime('%Y-%m-%d'),
            'till': end.strftime('%Y-%m-%d'),
            'interval': 24,  # Quotidien
            'limit': 100,
            'iss.meta': 'off'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'candles' not in data:
            return None
        
        candles = data['candles']
        
        # Extraire les colonnes
        if 'columns' in candles and 'data' in candles:
            columns = candles['columns']
            # Si columns est une liste de dictionnaires
            if columns and isinstance(columns[0], dict):
                columns = [col['name'] for col in columns]
            
            df = pd.DataFrame(candles['data'], columns=columns)
            
            if 'begin' in df.columns:
                df['begin'] = pd.to_datetime(df['begin'])
                df.set_index('begin', inplace=True)
            
            # Renommer pour standardiser
            rename_map = {
                'open': 'Open', 'high': 'High', 'low': 'Low',
                'close': 'Close', 'volume': 'Volume'
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
            
            return df
        
        return None
        
    except Exception as e:
        st.error(f"Erreur API: {e}")
        return None

def get_current_price(ticker):
    """
    Récupère le prix actuel depuis l'API MOEX
    """
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        
        params = {
            'iss.meta': 'off',
            'iss.only': 'marketdata'
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if 'marketdata' in data and 'data' in data['marketdata']:
            marketdata = data['marketdata']
            columns = marketdata['columns']
            values = marketdata['data'][0] if marketdata['data'] else []
            
            result = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    result[col] = values[i]
            
            return result
        
        return None
        
    except:
        return None

def show():
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔍 Recherche")
        
        ticker = st.text_input("Symbole", value="SBER", key="dashboard_ticker").upper()
        
        days = st.slider("Période (jours)", 7, 365, 30)
        
        if st.button("🔄 Rafraîchir"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 Symboles populaires")
        st.markdown("""
        - **SBER** - Sberbank
        - **GAZP** - Gazprom
        - **LKOH** - Lukoil
        - **YNDX** - Yandex
        - **ROSN** - Rosneft
        - **GMKN** - Norilsk Nickel
        - **MTSS** - MTS
        """)
    
    # Chargement des données
    with st.spinner(f"Chargement des données pour {ticker}..."):
        # Prix actuel
        current_data = get_current_price(ticker)
        
        # Données historiques
        hist_data = get_moex_candles(ticker, days)
    
    if current_data:
        # Extraire les données importantes
        last = current_data.get('LAST', 0)
        open_price = current_data.get('OPEN', 0)
        high = current_data.get('HIGH', 0)
        low = current_data.get('LOW', 0)
        volume = current_data.get('VOLT', 0)
        
        # Calculer la variation
        if last and open_price:
            change = last - open_price
            change_pct = (change / open_price * 100) if open_price else 0
        else:
            change = 0
            change_pct = 0
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_color = "normal" if change >= 0 else "inverse"
            st.metric(
                f"{ticker}",
                f"{last:,.2f} ₽" if last else "N/A",
                delta=f"{change:+.2f} ({change_pct:+.1f}%)" if last else None,
                delta_color=delta_color
            )
        
        with col2:
            st.metric("Plus haut", f"{high:,.2f} ₽" if high else "N/A")
        
        with col3:
            st.metric("Plus bas", f"{low:,.2f} ₽" if low else "N/A")
        
        with col4:
            st.metric("Volume", f"{volume:,.0f}" if volume else "N/A")
        
        st.success(f"✅ Données en temps réel pour {ticker}")
    
    else:
        st.error(f"❌ Impossible de charger {ticker}")
        st.info("Vérifiez que le symbole existe (SBER, GAZP, LKOH...)")
    
    # Graphique historique
    if hist_data is not None and not hist_data.empty:
        st.subheader(f"Historique {days} jours")
        
        fig = go.Figure()
        
        # Prix de clôture
        if 'Close' in hist_data.columns:
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                name='Clôture',
                line=dict(color='#D52B1E', width=2)
            ))
        
        # Ajouter les bougies si demandé
        if st.checkbox("Afficher en bougies"):
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name='Bougies',
                increasing_line_color='#0039A6',
                decreasing_line_color='#D52B1E'
            ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Prix (₽)",
            height=500,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Dernières données
        with st.expander("📊 Données détaillées"):
            st.dataframe(hist_data.tail(10))
    else:
        st.warning("Données historiques non disponibles")
