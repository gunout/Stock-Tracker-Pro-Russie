"""
Page Portefeuille - Version corrigée
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.api.moex_client import MOEXClient
    client = MOEXClient()
    API_OK = True
except Exception as e:
    st.error(f"Erreur d'initialisation API: {e}")
    API_OK = False

# ==================== INITIALISATION DE SESSION ====================
def init_session_state():
    """Initialise toutes les variables de session nécessaires"""
    
    # Portefeuille - Vérifier si existe, sinon créer
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    
    # Watchlist - Liste par défaut si non existante
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'ROSN', 'GMKN']
    
    # Positions - Structure pour stocker les achats
    if 'positions' not in st.session_state:
        st.session_state.positions = []

# Appeler l'initialisation
init_session_state()

# ==================== FONCTIONS DU PORTEFEUILLE ====================

def add_position(symbol, shares, buy_price, buy_date):
    """Ajoute une position au portefeuille"""
    position = {
        'symbol': symbol,
        'shares': shares,
        'buy_price': buy_price,
        'buy_date': buy_date.strftime('%Y-%m-%d'),
        'total_cost': shares * buy_price
    }
    st.session_state.positions.append(position)
    
    # Mettre à jour le portfolio pour la compatibilité
    if symbol not in st.session_state.portfolio:
        st.session_state.portfolio[symbol] = []
    st.session_state.portfolio[symbol].append(position)

def remove_position(index):
    """Supprime une position"""
    if 0 <= index < len(st.session_state.positions):
        removed = st.session_state.positions.pop(index)
        # Nettoyer portfolio si nécessaire
        symbol = removed['symbol']
        if symbol in st.session_state.portfolio and st.session_state.portfolio[symbol]:
            st.session_state.portfolio[symbol].pop()
            if not st.session_state.portfolio[symbol]:
                del st.session_state.portfolio[symbol]

def calculate_portfolio_value():
    """Calcule la valeur totale du portefeuille"""
    total_value = 0
    total_cost = 0
    
    for position in st.session_state.positions:
        # Prix actuel (simulé pour l'instant)
        current_price = get_mock_price(position['symbol'])
        value = position['shares'] * current_price
        total_value += value
        total_cost += position['total_cost']
    
    return total_value, total_cost

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

def get_real_price(symbol):
    """Tente d'obtenir le prix réel via API"""
    try:
        if API_OK and hasattr(client, 'get_market_data'):
            data = client.get_market_data(symbol)
            if data is not None and not data.empty and 'LAST' in data.columns:
                return float(data['LAST'].iloc[0])
    except:
        pass
    return get_mock_price(symbol)

# ==================== INTERFACE PRINCIPALE ====================

def show():
    st.markdown("# 💰 Portefeuille virtuel")
    
    # Onglets
    tab1, tab2 = st.tabs(["📊 Aperçu", "➕ Ajouter une position"])
    
    with tab1:
        # Métriques du portefeuille
        if st.session_state.positions:
            total_value, total_cost = calculate_portfolio_value()
            total_profit = total_value - total_cost
            total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
            
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
            st.subheader("📋 Positions actuelles")
            
            positions_data = []
            for i, pos in enumerate(st.session_state.positions):
                current_price = get_real_price(pos['symbol'])
                current_value = pos['shares'] * current_price
                profit = current_value - pos['total_cost']
                profit_pct = (profit / pos['total_cost'] * 100) if pos['total_cost'] > 0 else 0
                
                positions_data.append({
                    'Symbole': pos['symbol'],
                    'Actions': pos['shares'],
                    "Prix d'achat": f"{pos['buy_price']:,.2f} ₽",
                    'Date achat': pos['buy_date'],
                    'Prix actuel': f"{current_price:,.2f} ₽",
                    'Valeur': f"{current_value:,.2f} ₽",
                    'Profit': f"{profit:+,.2f} ₽",
                    'Profit %': f"{profit_pct:+.1f}%",
                    'Index': i
                })
            
            if positions_data:
                df = pd.DataFrame(positions_data)
                st.dataframe(df.drop('Index', axis=1), use_container_width=True)
                
                # Boutons de suppression
                st.subheader("🗑️ Supprimer une position")
                col1, col2 = st.columns([3, 1])
                with col1:
                    position_to_delete = st.selectbox(
                        "Choisir une position à supprimer",
                        options=range(len(positions_data)),
                        format_func=lambda x: f"{positions_data[x]['Symbole']} - {positions_data[x]['Date achat']}"
                    )
                with col2:
                    if st.button("Supprimer", use_container_width=True):
                        remove_position(position_to_delete)
                        st.rerun()
            else:
                st.info("Aucune position dans le portefeuille")
        else:
            st.info("Aucune position dans le portefeuille. Utilisez l'onglet 'Ajouter' pour commencer.")
    
    with tab2:
        st.subheader("➕ Ajouter une nouvelle position")
        
        with st.form("add_position_form"):
            # Utiliser la watchlist initialisée
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
                notes = st.text_area("Notes (optionnel)", max_chars=200)
            
            submitted = st.form_submit_button("✅ Ajouter au portefeuille")
            
            if submitted and symbol:
                add_position(symbol, shares, buy_price, buy_date)
                st.success(f"✅ {shares} actions {symbol} ajoutées au portefeuille")
                st.rerun()
    
    # Actions rapides dans la sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📋 Actions rapides")
        
        if st.button("📊 Vider le portefeuille", use_container_width=True):
            st.session_state.positions = []
            st.session_state.portfolio = {}
            st.rerun()
        
        if st.button("🔄 Réinitialiser la watchlist", use_container_width=True):
            st.session_state.watchlist = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'ROSN', 'GMKN']
            st.rerun()
        
        st.markdown("### 📈 Statistiques")
        st.caption(f"Positions: {len(st.session_state.positions)}")
        st.caption(f"Watchlist: {len(st.session_state.watchlist)} symboles")
