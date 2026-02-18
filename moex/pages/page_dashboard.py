"""
Page Tableau de bord - Connectée à l'API MOEX
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objs as go
import requests

def get_moex_data(ticker):
    """
    Récupère les données en temps réel depuis l'API MOEX
    """
    try:
        # URL pour les données de marché en temps réel
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        
        params = {
            'iss.meta': 'off',
            'iss.only': 'marketdata',
            'lang': 'ru'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'marketdata' in data and 'data' in data['marketdata']:
            marketdata = data['marketdata']
            columns = marketdata['columns']
            values = marketdata['data'][0] if marketdata['data'] else []
            
            # Créer un dictionnaire avec les données
            result = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    result[col] = values[i]
            
            return result
    except Exception as e:
        st.warning(f"Erreur API pour {ticker}: {e}")
    
    return None

def get_moex_history(ticker, days=30):
    """
    Récupère l'historique des prix depuis l'API MOEX
    """
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json"
        
        end = datetime.now()
        start = end - timedelta(days=days)
        
        params = {
            'from': start.strftime('%Y-%m-%d'),
            'till': end.strftime('%Y-%m-%d'),
            'interval': 24,
            'limit': 100,
            'iss.meta': 'off'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'candles' in data and 'data' in data['candles']:
            candles = data['candles']
            
            # Extraire les colonnes
            if 'columns' in candles:
                columns = candles['columns']
                if columns and isinstance(columns[0], dict):
                    columns = [col['name'] for col in columns]
                
                df = pd.DataFrame(candles['data'], columns=columns)
                
                if 'begin' in df.columns:
                    df['begin'] = pd.to_datetime(df['begin'])
                    df.set_index('begin', inplace=True)
                
                return df
    except Exception as e:
        st.warning(f"Erreur historique pour {ticker}: {e}")
    
    return None

def show():
    """Fonction principale"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Sidebar pour les contrôles
    with st.sidebar:
        st.markdown("## 🔍 Recherche")
        
        ticker = st.text_input("Symbole", value="SBER", key="api_ticker").upper()
        
        days = st.slider("Période (jours)", 7, 365, 30)
        
        use_api = st.checkbox("Utiliser l'API MOEX", value=True, key="use_api")
        
        if st.button("🔄 Rafraîchir"):
            st.cache_data.clear()
            st.rerun()
    
    if not use_api:
        # Mode démo
        st.info("🎮 Mode démonstration - Données simulées")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("SBER", "280.50 ₽", "+1.2%")
        with col2:
            st.metric("GAZP", "165.80 ₽", "-0.5%")
        with col3:
            st.metric("LKOH", "7200.50 ₽", "+2.1%")
        with col4:
            st.metric("YNDX", "2850.00 ₽", "+1.8%")
        
        # Graphique démo
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Prix'))
        fig.update_layout(title="Données simulées", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        return
    
    # Mode API réelle
    with st.spinner(f"Connexion à l'API MOEX pour {ticker}..."):
        # Données en temps réel
        realtime = get_moex_data(ticker)
        
        # Données historiques
        history = get_moex_history(ticker, days)
    
    if realtime:
        st.success(f"✅ Connecté à l'API MOEX - {ticker}")
        
        # Extraire les données importantes
        last_price = realtime.get('LAST', 0)
        open_price = realtime.get('OPEN', 0)
        high = realtime.get('HIGH', 0)
        low = realtime.get('LOW', 0)
        volume = realtime.get('VOLT', 0)
        
        # Calculer la variation
        if last_price and open_price:
            change = last_price - open_price
            change_pct = (change / open_price * 100) if open_price else 0
        else:
            change = 0
            change_pct = 0
        
        # Afficher les métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_color = "normal" if change >= 0 else "inverse"
            st.metric(
                f"{ticker}",
                f"{last_price:,.2f} ₽",
                delta=f"{change:+.2f} ({change_pct:+.1f}%)",
                delta_color=delta_color
            )
        
        with col2:
            st.metric("Plus haut", f"{high:,.2f} ₽" if high else "N/A")
        
        with col3:
            st.metric("Plus bas", f"{low:,.2f} ₽" if low else "N/A")
        
        with col4:
            st.metric("Volume", f"{volume:,.0f}" if volume else "N/A")
        
        # Graphique historique
        if history is not None and not history.empty:
            st.subheader(f"Évolution sur {days} jours")
            
            fig = go.Figure()
            
            # Prix de clôture
            if 'close' in history.columns:
                fig.add_trace(go.Scatter(
                    x=history.index,
                    y=history['close'],
                    mode='lines',
                    name='Clôture',
                    line=dict(color='#D52B1E', width=2)
                ))
            
            # Bandes haute/basse
            if 'high' in history.columns and 'low' in history.columns:
                fig.add_trace(go.Scatter(
                    x=history.index,
                    y=history['high'],
                    mode='lines',
                    name='Plus haut',
                    line=dict(color='green', width=1, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=history.index,
                    y=history['low'],
                    mode='lines',
                    name='Plus bas',
                    line=dict(color='red', width=1, dash='dash')
                ))
            
            fig.update_layout(
                title=f"{ticker} - Historique",
                xaxis_title="Date",
                yaxis_title="Prix (₽)",
                height=500,
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Dernières données
            with st.expander("📋 Détails historiques"):
                st.dataframe(history.tail(10))
        else:
            st.warning("Données historiques non disponibles")
        
        # Informations supplémentaires
        with st.expander("ℹ️ Données brutes API"):
            st.json(realtime)
    
    else:
        st.error(f"❌ Impossible de se connecter à l'API pour {ticker}")
        st.info("""
        **Conseils :**
        - Vérifiez que le symbole existe (SBER, GAZP, LKOH, YNDX, ROSN, GMKN)
        - Réessayez dans quelques instants
        - Utilisez le mode démo pour tester l'interface
        """)

if __name__ == "__main__":
    show()
