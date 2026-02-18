"""
Page Portefeuille - Avec prix réels MOEX
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Initialisation session state
if 'positions' not in st.session_state:
    st.session_state.positions = []

def get_current_price(symbol):
    """Récupère le prix actuel depuis l'API MOEX"""
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{symbol}.json"
        params = {'iss.meta': 'off', 'iss.only': 'marketdata'}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if 'marketdata' in data and 'data' in data['marketdata']:
            marketdata = data['marketdata']
            columns = marketdata['columns']
            values = marketdata['data'][0] if marketdata['data'] else []
            
            for i, col in enumerate(columns):
                if col == 'LAST' and i < len(values):
                    return float(values[i])
        return None
    except:
        return None

def show():
    st.markdown("# 💰 Portefeuille virtuel")
    
    tab1, tab2 = st.tabs(["📊 Aperçu", "➕ Ajouter"])
    
    with tab1:
        if st.session_state.positions:
            total_value = 0
            total_cost = 0
            
            # Mettre à jour les prix
            for pos in st.session_state.positions:
                current_price = get_current_price(pos['symbol'])
                if current_price:
                    pos['current_price'] = current_price
                    total_value += pos['shares'] * current_price
                total_cost += pos['shares'] * pos['buy_price']
            
            total_profit = total_value - total_cost
            total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
            
            # Métriques
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
            
            # Tableau
            df = pd.DataFrame(st.session_state.positions)
            if not df.empty and 'current_price' in df.columns:
                df['Valeur actuelle'] = df['shares'] * df['current_price']
                df['Profit'] = df['Valeur actuelle'] - (df['shares'] * df['buy_price'])
                df['Profit %'] = (df['Profit'] / (df['shares'] * df['buy_price']) * 100).round(1)
                
                st.dataframe(df[['symbol', 'shares', 'buy_price', 'current_price', 'Valeur actuelle', 'Profit', 'Profit %']])
            
            if st.button("🗑️ Vider le portefeuille"):
                st.session_state.positions = []
                st.rerun()
        
        else:
            st.info("Aucune position")
    
    with tab2:
        with st.form("add_position"):
            symbol = st.text_input("Symbole", value="SBER").upper()
            shares = st.number_input("Nombre d'actions", min_value=1, value=10)
            buy_price = st.number_input("Prix d'achat (₽)", min_value=0.01, value=100.0)
            buy_date = st.date_input("Date d'achat", value=datetime.now())
            
            if st.form_submit_button("Ajouter"):
                st.session_state.positions.append({
                    'symbol': symbol,
                    'shares': shares,
                    'buy_price': buy_price,
                    'buy_date': buy_date.strftime('%Y-%m-%d')
                })
                st.rerun()
