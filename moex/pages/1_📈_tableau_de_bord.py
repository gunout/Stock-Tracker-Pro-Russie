"""
Page du tableau de bord principal - Version robuste
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import traceback

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports avec gestion d'erreur
try:
    from src.api.moex_client import MOEXClient
    from src.data.processors import DataProcessor
    from src.data.validators import DataValidator
    from src.visualization.charts import create_price_chart, create_candle_chart
    from src.utils.formatters import format_currency, format_percentage
    IMPORTS_OK = True
except ImportError as e:
    st.error(f"Erreur d'import des modules: {e}")
    IMPORTS_OK = False

def get_mock_data():
    """Génère des données de démonstration si l'API n'est pas disponible"""
    import numpy as np
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    prices = 100 + np.cumsum(np.random.randn(30) * 2)
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 30)
    }, index=dates)
    return df

def show():
    """Affiche la page du tableau de bord"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Vérifier que les imports sont OK
    if not IMPORTS_OK:
        st.warning("Mode démo activé - Utilisation de données simulées")
        show_demo_mode()
        return
    
    # Sidebar pour les contrôles (dans la page)
    with st.sidebar:
        st.markdown("## 🔍 Options")
        
        # Sélection de l'action
        ticker = st.text_input("Symbole", value="SBER", key="dashboard_ticker").upper()
        
        # Période
        period = st.selectbox(
            "Période",
            options=["1j", "5j", "1m", "3m", "6m", "1a"],
            index=2,
            key="dashboard_period"
        )
        
        # Type de graphique
        chart_type = st.radio(
            "Type",
            ["Ligne", "Bougies"],
            horizontal=True,
            key="dashboard_chart"
        )
    
    # Chargement des données
    try:
        # Vérifier si le client API existe
        if 'moex_client' not in st.session_state:
            st.session_state.moex_client = MOEXClient()
        
        client = st.session_state.moex_client
        
        # Mapping période -> jours
        period_days = {"1j": 1, "5j": 5, "1m": 30, "3m": 90, "6m": 180, "1a": 365}
        days = period_days.get(period, 30)
        
        with st.spinner(f"Chargement des données pour {ticker}..."):
            # Date de fin = aujourd'hui
            end_date = datetime.now().strftime('%Y-%m-%d')
            # Date de début
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Récupérer les données
            hist_data = client.get_candles(
                ticker,
                interval=24*60,
                from_date=start_date,
                to_date=end_date
            )
            
            market_data = client.get_market_data(ticker)
        
        if hist_data is None or hist_data.empty:
            st.warning(f"Pas de données pour {ticker}. Utilisation de données simulées.")
            hist_data = get_mock_data()
            market_data = pd.DataFrame()
        
        # Traitement des données
        processor = DataProcessor()
        hist_data = processor.process_candles(hist_data)
        
        # Prix actuel
        current_price = hist_data['Close'].iloc[-1]
        prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current_price
        
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Prix",
                format_currency(current_price),
                delta=f"{change:+.2f} ({change_pct:+.1f}%)"
            )
        
        with col2:
            high = hist_data['High'].max()
            st.metric("Plus haut", format_currency(high))
        
        with col3:
            low = hist_data['Low'].min()
            st.metric("Plus bas", format_currency(low))
        
        with col4:
            volume = hist_data['Volume'].mean()
            st.metric("Volume moy", f"{volume/1e6:.1f}M")
        
        # Graphique
        if chart_type == "Ligne":
            fig = create_price_chart(hist_data, title=f"{ticker} - {period}")
        else:
            fig = create_candle_chart(hist_data, title=f"{ticker} - {period}")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Données brutes
        with st.expander("📊 Données détaillées"):
            st.dataframe(hist_data.tail(10), use_container_width=True)
    
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        st.code(traceback.format_exc())
        show_demo_mode()

def show_demo_mode():
    """Affiche une version démo avec des données simulées"""
    st.info("Mode démonstration - Données simulées")
    
    # Générer des données de démo
    hist_data = get_mock_data()
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SBER", "280.50 ₽", "+5.20 (1.9%)")
    with col2:
        st.metric("GAZP", "165.80 ₽", "-2.30 (-1.4%)")
    with col3:
        st.metric("LKOH", "7200.50 ₽", "+120.50 (1.7%)")
    with col4:
        st.metric("YNDX", "2850.00 ₽", "+50.00 (1.8%)")
    
    # Graphique de démo
    fig = create_price_chart(hist_data, title="Données simulées")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### 🔧 Pour utiliser les données réelles :
    1. Vérifiez que le client API est correctement configuré
    2. Assurez-vous que le symbole existe (SBER, GAZP, LKOH, etc.)
    3. Réessayez plus tard
    """)
