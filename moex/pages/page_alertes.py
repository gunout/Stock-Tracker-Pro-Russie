"""
Page Alertes - Avec surveillance des prix réels
"""
import streamlit as st
import requests
import time
from datetime import datetime

if 'alerts' not in st.session_state:
    st.session_state.alerts = []

def check_price(symbol, target, condition):
    """Vérifie si le prix atteint la condition"""
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{symbol}.json"
        response = requests.get(url, params={'iss.meta': 'off'}, timeout=5)
        data = response.json()
        
        if 'marketdata' in data and 'data' in data['marketdata']:
            marketdata = data['marketdata']
            columns = marketdata['columns']
            values = marketdata['data'][0]
            
            for i, col in enumerate(columns):
                if col == 'LAST':
                    price = float(values[i])
                    
                    if condition == "above" and price >= target:
                        return True, price
                    elif condition == "below" and price <= target:
                        return True, price
        return False, None
    except:
        return False, None

def show():
    st.markdown("# 🔔 Alertes de prix")
    
    tab1, tab2 = st.tabs(["📋 Alertes", "➕ Nouvelle alerte"])
    
    with tab1:
        if st.session_state.alerts:
            for i, alert in enumerate(st.session_state.alerts):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{alert['symbol']}**")
                with col2:
                    condition = "≥" if alert['condition'] == "above" else "≤"
                    st.write(f"{condition} {alert['price']} ₽")
                with col3:
                    status = "✅ Active" if not alert.get('triggered') else "🔴 Déclenchée"
                    st.write(status)
                with col4:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.alerts.pop(i)
                        st.rerun()
                
                # Vérification automatique
                if not alert.get('triggered'):
                    triggered, price = check_price(
                        alert['symbol'],
                        alert['price'],
                        alert['condition']
                    )
                    if triggered:
                        alert['triggered'] = True
                        alert['triggered_price'] = price
                        alert['triggered_time'] = datetime.now()
                        st.balloons()
                        st.success(f"🎯 Alerte {alert['symbol']} à {price} ₽")
        else:
            st.info("Aucune alerte")
    
    with tab2:
        with st.form("new_alert"):
            symbol = st.text_input("Symbole", value="SBER").upper()
            price = st.number_input("Prix cible (₽)", min_value=1.0, value=300.0)
            condition = st.selectbox("Condition", ["above (≥)", "below (≤)"])
            condition = "above" if "above" in condition else "below"
            
            if st.form_submit_button("Créer l'alerte"):
                st.session_state.alerts.append({
                    'symbol': symbol,
                    'price': price,
                    'condition': condition,
                    'created': datetime.now(),
                    'triggered': False
                })
                st.rerun()
