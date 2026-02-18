"""
Page Tableau de bord - Version complète
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le chemin racine
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports nécessaires
try:
    from src.api.moex_client import MOEXClient
    from src.visualization.charts import create_price_chart, create_candle_chart
    from src.utils.formatters import format_currency
    IMPORTS_OK = True
except ImportError as e:
    st.error(f"Erreur d'import: {e}")
    IMPORTS_OK = False

def generate_demo_data():
    """Génère des données de démonstration"""
    np.random.seed(42)  # Pour des résultats reproductibles
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Générer des prix avec une tendance
    base = 100
    returns = np.random.randn(100) * 0.02
    prices = base * (1 + np.cumsum(returns))
    
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
    
    # Vérifier que create_price_chart est disponible
    if 'create_price_chart' in globals():
        fig = create_price_chart(hist_data, title="Données simulées - Évolution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback: graphique simple avec Streamlit
        st.subheader("Évolution simulée")
        st.line_chart(hist_data['Close'])
    
    with st.expander("ℹ️ Informations"):
        st.markdown("""
        **Mode démonstration activé**
        - Les données sont simulées
        - Utilisez des symboles réels (SBER, GAZP, LKOH) pour les données réelles
        - Vérifiez votre connexion internet
        """)

def show():
    """Fonction principale de la page"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Vérification des imports
    if not IMPORTS_OK:
        st.error("Erreur de configuration - Mode démo uniquement")
        show_demo_mode()
        return
    
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
        
        use_demo = st.checkbox("Forcer mode démo", value=False)
    
    # Mode démo forcé
    if use_demo:
        show_demo_mode()
        return
    
    # Mode réel
    try:
        client = MOEXClient()
        
        # Conversion de la période
        period_days = {"7j": 7, "30j": 30, "90j": 90, "180j": 180, "365j": 365}
        days = period_days.get(period, 30)
        
        with st.spinner(f"Chargement des données pour {ticker}..."):
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            hist_data = client.get_candles(
                ticker,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            market_data = client.get_market_data(ticker)
        
        if hist_data.empty:
            st.warning(f"Pas de données pour {ticker}")
            show_demo_mode()
            return
        
        # Métriques
        current = hist_data['Close'].iloc[-1]
        prev = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev != 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Prix",
                f"{current:,.2f} ₽",
                delta=f"{change:+.2f} ({change_pct:+.1f}%)"
            )
        
        with col2:
            high = hist_data['High'].max()
            st.metric("Plus haut", f"{high:,.2f} ₽")
        
        with col3:
            low = hist_data['Low'].min()
            st.metric("Plus bas", f"{low:,.2f} ₽")
        
        with col4:
            volume = hist_data['Volume'].mean()
            st.metric("Volume moy", f"{volume/1e6:.1f}M")
        
        # Graphique
        if chart_type == "Ligne":
            fig = create_price_chart(
                hist_data,
                title=f"{ticker} - Évolution du prix",
                show_volume=True
            )
        else:
            fig = create_candle_chart(
                hist_data,
                title=f"{ticker} - Graphique en bougies",
                show_volume=True
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Dernières données
        with st.expander("📋 Dernières transactions"):
            st.dataframe(hist_data.tail(10))
    
    except Exception as e:
        st.error(f"Erreur: {e}")
        show_demo_mode()
