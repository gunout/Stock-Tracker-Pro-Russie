"""
Page Tableau de bord - Version ultra-simplifiée
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objs as go
import requests

# ==================== FONCTIONS DE GRAPHIQUES ====================

def create_simple_chart(data, title="Évolution du prix"):
    """Crée un graphique simple avec Plotly"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='Prix',
        line=dict(color='#D52B1E', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Prix (₽)",
        height=500,
        template='plotly_white'
    )
    
    return fig

# ==================== GÉNÉRATION DE DONNÉES ====================

def generate_demo_prices():
    """Génère des prix de démonstration"""
    np.random.seed(42)
    
    # Dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Prix avec tendance
    returns = np.random.randn(len(dates)) * 0.02
    prices = 100 * (1 + np.cumsum(returns))
    
    return pd.DataFrame({
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)

def get_moex_candles(ticker, days=30):
    """Récupère les données MOEX"""
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
            
            # Récupérer les colonnes
            if 'columns' in candles:
                columns = candles['columns']
                # Si columns est une liste de dicts
                if columns and isinstance(columns[0], dict):
                    columns = [col['name'] for col in columns]
                
                df = pd.DataFrame(candles['data'], columns=columns)
                
                if 'begin' in df.columns:
                    df['begin'] = pd.to_datetime(df['begin'])
                    df.set_index('begin', inplace=True)
                
                # Standardiser les noms
                rename_map = {
                    'open': 'Open', 'high': 'High', 'low': 'Low',
                    'close': 'Close', 'volume': 'Volume'
                }
                df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
                
                return df
    
    except Exception as e:
        st.warning(f"Erreur API: {e}")
    
    return None

# ==================== MODE DÉMO ====================

def show_demo_mode():
    """Affiche le mode démonstration"""
    st.info("🎮 Mode démonstration - Données simulées")
    
    # Métriques en haut
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SBER", "280.50 ₽", "+1.2%", delta_color="normal")
    with col2:
        st.metric("GAZP", "165.80 ₽", "-0.5%", delta_color="inverse")
    with col3:
        st.metric("LKOH", "7200.50 ₽", "+2.1%", delta_color="normal")
    with col4:
        st.metric("YNDX", "2850.00 ₽", "+1.8%", delta_color="normal")
    
    # Générer des données de démo
    demo_data = generate_demo_prices()
    
    # Créer le graphique
    fig = create_simple_chart(demo_data, "Données simulées - Évolution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Dernières données
    with st.expander("📊 Voir les données simulées"):
        st.dataframe(demo_data.tail(10))
    
    # Instructions
    with st.expander("ℹ️ Comment obtenir des données réelles"):
        st.markdown("""
        **Pour utiliser des données réelles :**
        1. Entrez un symbole valide (SBER, GAZP, LKOH, YNDX, etc.)
        2. Désactivez le mode démo
        3. Les données seront chargées depuis l'API MOEX
        
        **Symboles populaires :**
        - SBER : Sberbank
        - GAZP : Gazprom
        - LKOH : Lukoil
        - YNDX : Yandex
        - ROSN : Rosneft
        - GMKN : Norilsk Nickel
        """)

# ==================== MODE RÉEL ====================

def show_real_mode(ticker, days):
    """Affiche les données réelles"""
    with st.spinner(f"Chargement de {ticker}..."):
        df = get_moex_candles(ticker, days)
    
    if df is None or df.empty:
        st.warning(f"⚠️ Pas de données pour {ticker}")
        return False
    
    # Métriques
    current = df['Close'].iloc[-1]
    prev = df['Close'].iloc[-2] if len(df) > 1 else current
    change = current - prev
    change_pct = (change / prev * 100) if prev != 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta_color = "normal" if change >= 0 else "inverse"
        st.metric(
            "Prix",
            f"{current:,.2f} ₽",
            delta=f"{change:+.2f} ({change_pct:+.1f}%)",
            delta_color=delta_color
        )
    
    with col2:
        st.metric("Plus haut", f"{df['High'].max():,.2f} ₽")
    
    with col3:
        st.metric("Plus bas", f"{df['Low'].min():,.2f} ₽")
    
    with col4:
        st.metric("Volume moy", f"{df['Volume'].mean()/1e6:.1f}M")
    
    # Graphique
    fig = create_simple_chart(df, f"{ticker} - Évolution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Dernières données
    with st.expander("📋 Dernières transactions"):
        st.dataframe(df.tail(10))
    
    return True

# ==================== PAGE PRINCIPALE ====================

def show():
    """Fonction principale"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔍 Paramètres")
        
        ticker = st.text_input("Symbole", value="SBER", key="main_ticker").upper()
        
        period_days = st.select_slider(
            "Période (jours)",
            options=[7, 14, 30, 60, 90, 180, 365],
            value=30
        )
        
        force_demo = st.checkbox("Forcer mode démo", value=False, key="force_demo")
        
        st.markdown("---")
        st.caption(f"Symbole: {ticker}")
        st.caption(f"Période: {period_days} jours")
    
    # Mode démo forcé ou automatique
    if force_demo:
        show_demo_mode()
    else:
        # Essayer le mode réel
        success = show_real_mode(ticker, period_days)
        
        if not success:
            st.warning(" Passage en mode démonstration")
            show_demo_mode()
