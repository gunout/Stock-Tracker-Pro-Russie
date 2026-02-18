"""
Page Portefeuille - Version avec initialisation corrigée
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Ajouter le chemin racine (important pour les imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== INITIALISATION DE L'ÉTAT DE SESSION ====================
# Cette section doit être EXÉCUTÉE AVANT toute lecture de st.session_state

# 1. Portefeuille (liste des positions)
if 'positions' not in st.session_state:
    st.session_state.positions = []

# 2. Watchlist (liste des symboles favoris)
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'ROSN', 'GMKN']

# 3. Portfolio (structure alternative pour compatibilité)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# ==================== IMPORTS API (après initialisation) ====================
# Tentative d'import du client API (optionnel)
try:
    from src.api.moex_client import MOEXClient
    client = MOEXClient()
    API_OK = True
except Exception as e:
    # Silently fail, on utilisera des prix simulés
    API_OK = False
    client = None

# ==================== FONCTIONS DU PORTEFEUILLE ====================

def get_mock_price(symbol):
    """Prix simulé pour les tests"""
    mock_prices = {
        'SBER': 280.50,
        'GAZP': 165.80,
        'LKOH': 7200.50,
        'YNDX': 2850.00,
        'ROSN': 550.30,
        'GMKN': 16500.00
    }
    return mock_prices.get(symbol, 100.00)

def calculate_portfolio_summary():
    """Calcule les métriques du portefeuille"""
    total_value = 0.0
    total_cost = 0.0
    
    for pos in st.session_state.positions:
        current_price = get_mock_price(pos['symbol'])
        value = pos['shares'] * current_price
        total_value += value
        total_cost += pos['total_cost']
    
    return total_value, total_cost

# ==================== INTERFACE PRINCIPALE ====================

def show():
    st.markdown("# 💰 Portefeuille virtuel")
    
    # Onglets
    tab1, tab2 = st.tabs(["📊 Aperçu", "➕ Ajouter une position"])
    
    with tab1:
        if st.session_state.positions:
            # Calcul des métriques
            total_value, total_cost = calculate_portfolio_summary()
            total_profit = total_value - total_cost
            total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0.0
            
            # Affichage des métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valeur totale", f"{total_value:,.2f} ₽")
            with col2:
                st.metric("Coût total", f"{total_cost:,.2f} ₽")
            with col3:
                delta_color = "normal" if total_profit >= 0 else "inverse"
                st.metric(
                    "Profit/Perte",
                    f"{total_profit:+,.2f} ₽",
                    delta=f"{total_profit_pct:+.1f}%",
                    delta_color=delta_color
                )
            
            # Tableau des positions
            st.subheader("📋 Positions")
            
            positions_data = []
            for i, pos in enumerate(st.session_state.positions):
                current_price = get_mock_price(pos['symbol'])
                current_value = pos['shares'] * current_price
                profit = current_value - pos['total_cost']
                profit_pct = (profit / pos['total_cost'] * 100) if pos['total_cost'] > 0 else 0.0
                
                positions_data.append({
                    'Symbole': pos['symbol'],
                    'Actions': pos['shares'],
                    "Prix d'achat": f"{pos['buy_price']:,.2f} ₽",
                    'Date': pos['buy_date'],
                    'Prix actuel': f"{current_price:,.2f} ₽",
                    'Valeur': f"{current_value:,.2f} ₽",
                    'Profit': f"{profit:+,.2f} ₽",
                    'Profit %': f"{profit_pct:+.1f}%"
                })
            
            st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
            
            # Suppression de position
            with st.expander("🗑️ Supprimer une position"):
                pos_options = [f"{p['symbol']} - {p['buy_date']}" for p in st.session_state.positions]
                if pos_options:
                    idx_to_delete = st.selectbox(
                        "Choisir une position",
                        range(len(pos_options)),
                        format_func=lambda x: pos_options[x]
                    )
                    if st.button("Supprimer cette position"):
                        st.session_state.positions.pop(idx_to_delete)
                        st.rerun()
        else:
            st.info("Aucune position dans le portefeuille. Utilisez l'onglet 'Ajouter' pour commencer.")
    
    with tab2:
        st.subheader("➕ Ajouter une position")
        
        with st.form("add_position_form"):
            # Sélection du symbole (utilise watchlist initialisée)
            symbol_options = st.session_state.watchlist + ["Autre..."]
            symbol_choice = st.selectbox("Symbole", options=symbol_options)
            
            if symbol_choice == "Autre...":
                symbol = st.text_input("Entrez le symbole", value="").upper()
            else:
                symbol = symbol_choice
            
            col1, col2 = st.columns(2)
            with col1:
                shares = st.number_input("Nombre d'actions", min_value=1, value=10, step=1)
                buy_price = st.number_input("Prix d'achat (₽)", min_value=0.01, value=100.0, step=10.0)
            with col2:
                buy_date = st.date_input("Date d'achat", value=datetime.now())
            
            submitted = st.form_submit_button("✅ Ajouter au portefeuille")
            
            if submitted and symbol:
                # Ajouter la position
                new_position = {
                    'symbol': symbol,
                    'shares': shares,
                    'buy_price': buy_price,
                    'buy_date': buy_date.strftime('%Y-%m-%d'),
                    'total_cost': shares * buy_price
                }
                st.session_state.positions.append(new_position)
                
                # Mettre à jour portfolio pour compatibilité
                if symbol not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol] = []
                st.session_state.portfolio[symbol].append(new_position)
                
                st.success(f"✅ {shares} actions {symbol} ajoutées")
                st.rerun()
    
    # Actions rapides dans la sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📋 Actions rapides")
        
        if st.button("🗑️ Vider le portefeuille", use_container_width=True):
            st.session_state.positions = []
            st.session_state.portfolio = {}
            st.rerun()
        
        if st.button("🔄 Réinitialiser la watchlist", use_container_width=True):
            st.session_state.watchlist = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'ROSN', 'GMKN']
            st.rerun()
        
        st.markdown("### 📈 Statistiques")
        st.caption(f"Positions: {len(st.session_state.positions)}")
        st.caption(f"Watchlist: {len(st.session_state.watchlist)} symboles")
