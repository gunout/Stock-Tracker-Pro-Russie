"""
Page Tableau de bord - Version autonome sans dépendances externes
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objs as go

# Pas d'imports externes - tout est défini dans ce fichier

def create_price_chart(df, title="Évolution du prix", show_volume=True):
    """
    Crée un graphique de prix en ligne - Défini localement
    """
    fig = go.Figure()
    
    # Prix
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Prix',
        line=dict(color='#D52B1E', width=2)
    ))
    
    # Volume
    if show_volume and 'Volume' in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='lightgray', opacity=0.3)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title="Prix (₽)",
        yaxis2=dict(
            title="Volume",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title="Date",
        height=500,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_candle_chart(df, title="Graphique en bougies", show_volume=True):
    """
    Crée un graphique en bougies - Défini localement
    """
    fig = go.Figure()
    
    # Bougies
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Bougies',
        increasing_line_color='#0039A6',
        decreasing_line_color='#D52B1E'
    ))
    
    # Volume
    if show_volume and 'Volume' in df.columns:
        colors = ['#0039A6' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
                  else '#D52B1E' for i in range(len(df))]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color=colors, opacity=0.3)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title="Prix (₽)",
        yaxis2=dict(
            title="Volume",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title="Date",
        height=500,
        hovermode='x unified',
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    
    return fig

def format_currency(value):
    """Formate une valeur monétaire"""
    if value is None:
        return "N/A"
    if value >= 1e9:
        return f"₽{value/1e9:.2f} млрд"
    elif value >= 1e6:
        return f"₽{value/1e6:.2f} млн"
    else:
        return f"₽{value:,.2f}"

def generate_demo_data():
    """Génère des données de démonstration"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Générer des prix avec une tendance
    returns = np.random.randn(100) * 0.02
    prices = 100 * (1 + np.cumsum(returns))
    
    return pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)

def show_demo_mode():
    """Affiche le mode démonstration"""
    st.info("🎮 Mode démonstration - Données simulées")
    
    # Métriques de démo
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SBER", "280.50 ₽", "+1.2%")
    with col2:
        st.metric("GAZP", "165.80 ₽", "-0.5%")
    with col3:
        st.metric("LKOH", "7200.50 ₽", "+2.1%")
    with col4:
        st.metric("YNDX", "2850.00 ₽", "+1.8%")
    
    # Graphique de démo
    hist_data = generate_demo_data()
    
    # Utiliser la fonction locale
    fig = create_price_chart(hist_data, title="Données simulées - Évolution")
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Données simulées"):
        st.dataframe(hist_data.tail(10))
    
    with st.expander("ℹ️ Informations"):
        st.markdown("""
        **Mode démonstration activé**
        - Les données sont simulées
        - Utilisez des symboles réels (SBER, GAZP, LKOH) pour les données réelles
        - Vérifiez votre connexion internet
        """)

def get_moex_data(ticker, days=30):
    """Tente de récupérer des données MOEX réelles"""
    import requests
    
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
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'candles' in data and 'data' in data['candles']:
            candles = data['candles']
            
            # Extraire les colonnes
            if 'columns' in candles:
                columns = candles['columns']
                # Si columns est une liste de dictionnaires
                if columns and isinstance(columns[0], dict):
                    columns = [col['name'] for col in columns]
                
                df = pd.DataFrame(candles['data'], columns=columns)
                
                if 'begin' in df.columns:
                    df['begin'] = pd.to_datetime(df['begin'])
                    df.set_index('begin', inplace=True)
                
                # Renommer pour standardiser
                rename = {
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }
                df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
                
                return df
    
    except Exception as e:
        st.warning(f"Erreur API: {e}")
    
    return None

def show():
    """Fonction principale de la page"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Sidebar dans la page
    with st.sidebar:
        st.markdown("## 🔍 Options")
        
        ticker = st.text_input("Symbole", value="SBER", key="ticker").upper()
        
        period = st.selectbox(
            "Période",
            options=["7j", "30j", "90j", "180j", "365j"],
            index=1,
            format_func=lambda x: x.replace('j', ' jours')
        )
        
        chart_type = st.radio(
            "Type de graphique",
            ["Ligne", "Bougies"],
            horizontal=True
        )
        
        use_demo = st.checkbox("Mode démo", value=False)
    
    # Mode démo forcé
    if use_demo:
        show_demo_mode()
        return
    
    # Essayer de charger les données réelles
    period_days = {"7j": 7, "30j": 30, "90j": 90, "180j": 180, "365j": 365}
    days = period_days.get(period, 30)
    
    with st.spinner(f"Chargement des données pour {ticker}..."):
        df = get_moex_data(ticker, days)
    
    if df is not None and not df.empty:
        # Succès - afficher les données réelles
        st.success(f"✅ Données réelles pour {ticker}")
        
        # Métriques
        current = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2] if len(df) > 1 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev != 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Prix",
                format_currency(current),
                delta=f"{change:+.2f} ({change_pct:+.1f}%)"
            )
        
        with col2:
            st.metric("Plus haut", format_currency(df['High'].max()))
        
        with col3:
            st.metric("Plus bas", format_currency(df['Low'].min()))
        
        with col4:
            st.metric("Volume moy", f"{df['Volume'].mean()/1e6:.1f}M")
        
        # Graphique
        if chart_type == "Ligne":
            fig = create_price_chart(df, title=f"{ticker} - Évolution du prix")
        else:
            fig = create_candle_chart(df, title=f"{ticker} - Graphique en bougies")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Données
        with st.expander("📋 Données détaillées"):
            st.dataframe(df.tail(10))
    
    else:
        # Échec - passer en mode démo
        st.warning(f"Impossible de charger les données pour {ticker}")
        show_demo_mode()
