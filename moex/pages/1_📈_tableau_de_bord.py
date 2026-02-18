"""
Page du tableau de bord principal
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.api.moex_client import MOEXClient
from src.data.processors import DataProcessor
from src.data.validators import DataValidator
from src.visualization.charts import create_price_chart, create_candle_chart
from src.utils.formatters import format_currency, format_percentage
from src.utils.time_utils import get_market_status

def show():
    """Affiche la page du tableau de bord"""
    
    st.markdown("# 📈 Tableau de bord MOEX")
    
    # Initialisation du client API
    client = MOEXClient()
    
    # Sidebar pour les contrôles
    with st.sidebar:
        st.markdown("## 🔍 Filtres")
        
        # Sélection de l'action
        try:
            securities_df = client.get_securities()
            if not securities_df.empty:
                ticker_options = securities_df['SECID'].tolist()
                ticker_labels = [
                    f"{row['SECID']} - {row['SHORTNAME']}" 
                    for _, row in securities_df.iterrows()
                ]
                
                selected_idx = st.selectbox(
                    "Choisir une action",
                    range(len(ticker_options)),
                    format_func=lambda x: ticker_labels[x]
                )
                selected_ticker = ticker_options[selected_idx]
            else:
                selected_ticker = st.selectbox(
                    "Choisir une action",
                    st.session_state.watchlist
                )
        except Exception as e:
            st.error(f"Erreur chargement liste: {e}")
            selected_ticker = st.selectbox(
                "Choisir une action",
                st.session_state.watchlist
            )
        
        # Période
        period_options = {
            '1j': 1,
            '5j': 5,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1a': 365
        }
        period = st.selectbox(
            "Période",
            options=list(period_options.keys()),
            index=2
        )
        
        # Type de graphique
        chart_type = st.radio(
            "Type de graphique",
            ["Ligne", "Bougies"]
        )
        
        # Afficher les indicateurs
        show_indicators = st.checkbox("Afficher les indicateurs techniques", value=True)
    
    # Chargement des données
    try:
        with st.spinner("Chargement des données..."):
            # Date de fin = aujourd'hui
            end_date = datetime.now().strftime('%Y-%m-%d')
            # Date de début = aujourd'hui - période
            days = period_options[period]
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Récupérer les données historiques
            hist_data = client.get_candles(
                selected_ticker,
                interval=24*60,  # Quotidien
                from_date=start_date,
                to_date=end_date
            )
            
            # Récupérer les données de marché en temps réel
            market_data = client.get_market_data(selected_ticker)
        
        if hist_data.empty:
            st.warning(f"Aucune donnée disponible pour {selected_ticker}")
            return
        
        # Traitement des données
        processor = DataProcessor()
        hist_data = processor.process_candles(hist_data)
        
        if show_indicators:
            hist_data = processor.add_technical_indicators(hist_data)
        
        # Validation
        validator = DataValidator()
        is_valid, errors = validator.validate_price_data(hist_data)
        if not is_valid:
            st.warning(f"Problèmes de données détectés: {', '.join(errors)}")
        
        # Prix actuel
        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else 0
        prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current_price
        
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Prix actuel",
                format_currency(current_price),
                delta=f"{change:+.2f} ({change_pct:+.1f}%)"
            )
        
        with col2:
            if not market_data.empty and 'HIGH' in market_data.columns:
                day_high = market_data['HIGH'].iloc[0]
                st.metric("Plus haut", format_currency(day_high))
            else:
                day_high = hist_data['High'].max()
                st.metric("Plus haut (période)", format_currency(day_high))
        
        with col3:
            if not market_data.empty and 'LOW' in market_data.columns:
                day_low = market_data['LOW'].iloc[0]
                st.metric("Plus bas", format_currency(day_low))
            else:
                day_low = hist_data['Low'].min()
                st.metric("Plus bas (période)", format_currency(day_low))
        
        with col4:
            if not market_data.empty and 'VOLT' in market_data.columns:
                volume = market_data['VOLT'].iloc[0]
                st.metric("Volume", f"{volume/1e6:.1f}M")
            else:
                volume = hist_data['Volume'].iloc[-1]
                st.metric("Volume", f"{volume/1e6:.1f}M")
        
        # Graphique
        st.markdown("---")
        
        if chart_type == "Ligne":
            fig = create_price_chart(
                hist_data,
                title=f"{selected_ticker} - Évolution du prix",
                show_volume=True,
                show_ma=show_indicators
            )
        else:
            fig = create_candle_chart(
                hist_data,
                title=f"{selected_ticker} - Graphique en bougies",
                show_volume=True
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques supplémentaires
        with st.expander("📊 Statistiques détaillées"):
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.markdown("**Statistiques de prix**")
                st.write(f"Moyenne période: {format_currency(hist_data['Close'].mean())}")
                st.write(f"Médiane: {format_currency(hist_data['Close'].median())}")
                st.write(f"Écart-type: {format_currency(hist_data['Close'].std())}")
            
            with col_s2:
                st.markdown("**Rendements**")
                returns = hist_data['Close'].pct_change()
                st.write(f"Moyenne: {format_percentage(returns.mean() * 100)}")
                st.write(f"Volatilité: {format_percentage(returns.std() * 100)}")
                st.write(f"Max: {format_percentage(returns.max() * 100)}")
                st.write(f"Min: {format_percentage(returns.min() * 100)}")
            
            with col_s3:
                st.markdown("**Volume**")
                st.write(f"Moyen: {hist_data['Volume'].mean()/1e6:.1f}M")
                st.write(f"Total: {hist_data['Volume'].sum()/1e6:.1f}M")
        
        # Dernières transactions
        with st.expander("📋 Dernières données"):
            st.dataframe(
                hist_data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10),
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        st.info("Veuillez réessayer plus tard ou vérifier votre connexion.")