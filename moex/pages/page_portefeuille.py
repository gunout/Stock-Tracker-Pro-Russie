"""
Page de gestion du portefeuille virtuel
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.models.portfolio import Portfolio, Position
from src.api.moex_client import MOEXClient
from src.utils.formatters import format_currency, format_percentage
from src.visualization.charts import create_allocation_chart

def show():
    """Affiche la page du portefeuille"""
    
    st.markdown("# 💰 Portefeuille virtuel")
    
    # Initialisation du portefeuille
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = Portfolio()
    
    portfolio = st.session_state.portfolio
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📊 Aperçu", "➕ Ajouter", "📈 Performance"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### 📋 Actions rapides")
            if st.button("🔄 Mettre à jour les prix", use_container_width=True):
                st.rerun()
            
            if st.button("📊 Exporter le rapport", use_container_width=True):
                # Logique d'export
                st.info("Fonctionnalité à venir")
        
        with col1:
            if portfolio.positions:
                # Récupérer les prix actuels
                client = MOEXClient()
                prices = {}
                
                with st.spinner("Mise à jour des prix..."):
                    for symbol in portfolio.positions.keys():
                        try:
                            market_data = client.get_market_data(symbol)
                            if not market_data.empty and 'LAST' in market_data.columns:
                                prices[symbol] = market_data['LAST'].iloc[0]
                            else:
                                prices[symbol] = 0
                        except:
                            prices[symbol] = 0
                
                # Calcul des totaux
                total_value = portfolio.get_current_value(prices)
                total_cost = portfolio.get_total_cost()
                total_profit = portfolio.get_profit_loss(prices)
                total_profit_pct = portfolio.get_profit_loss_percent(prices)
                
                # Métriques du portefeuille
                col_m1, col_m2, col_m3 = st.columns(3)
                
                with col_m1:
                    st.metric(
                        "Valeur totale",
                        format_currency(total_value),
                        delta=f"{format_currency(total_profit)}"
                    )
                
                with col_m2:
                    st.metric(
                        "Coût total",
                        format_currency(total_cost)
                    )
                
                with col_m3:
                    st.metric(
                        "Performance",
                        format_percentage(total_profit_pct)
                    )
                
                st.markdown("---")
                
                # Tableau des positions
                st.markdown("### 📋 Positions détaillées")
                df_positions = portfolio.to_dataframe(prices)
                st.dataframe(df_positions, use_container_width=True)
                
                # Graphique d'allocation
                st.markdown("### 🥧 Allocation du portefeuille")
                allocation = portfolio.get_allocation()
                if allocation:
                    fig = create_allocation_chart(allocation)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Bouton pour vider
                if st.button("🗑️ Vider le portefeuille", use_container_width=True):
                    st.session_state.portfolio = Portfolio()
                    st.rerun()
            
            else:
                st.info("Aucune position dans le portefeuille. Utilisez l'onglet 'Ajouter' pour commencer.")
    
    with tab2:
        st.markdown("### ➕ Ajouter une nouvelle position")
        
        with st.form("add_position_form"):
            # Récupérer la liste des actions
            client = MOEXClient()
            try:
                securities_df = client.get_securities()
                if not securities_df.empty:
                    ticker_options = securities_df['SECID'].tolist()
                    selected_ticker = st.selectbox(
                        "Symbole",
                        options=ticker_options,
                        index=0 if ticker_options else 0
                    )
                else:
                    selected_ticker = st.selectbox(
                        "Symbole",
                        options=st.session_state.watchlist,
                        index=0
                    )
            except:
                selected_ticker = st.selectbox(
                    "Symbole",
                    options=st.session_state.watchlist,
                    index=0
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                shares = st.number_input(
                    "Nombre d'actions",
                    min_value=1,
                    value=100,
                    step=10
                )
                
                buy_price = st.number_input(
                    "Prix d'achat (₽)",
                    min_value=0.01,
                    value=100.0,
                    step=10.0
                )
            
            with col2:
                buy_date = st.date_input(
                    "Date d'achat",
                    value=datetime.now()
                )
                
                notes = st.text_area(
                    "Notes (optionnel)",
                    max_chars=200
                )
            
            submitted = st.form_submit_button("✅ Ajouter au portefeuille")
            
            if submitted:
                position = Position(
                    symbol=selected_ticker,
                    shares=shares,
                    buy_price=buy_price,
                    buy_date=datetime.combine(buy_date, datetime.min.time()),
                    notes=notes if notes else None
                )
                
                portfolio.add_position(position)
                st.success(f"✅ {shares} actions {selected_ticker} ajoutées au portefeuille")
                st.rerun()
    
    with tab3:
        st.markdown("### 📈 Analyse de performance")
        st.info("Fonctionnalité en cours de développement")
        
        if portfolio.positions:
            st.markdown("**Statistiques à venir :**")
            st.markdown("- Courbe de performance")
            st.markdown("- Comparaison avec indices")
            st.markdown("- Ratios de risque (Sharpe, Sortino)")
            st.markdown("- Drawdown maximum")
