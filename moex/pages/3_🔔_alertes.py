"""
Page de gestion des alertes de prix
"""
import streamlit as st
from datetime import datetime
from src.models.alerts import PriceAlert, AlertType, AlertStatus
from src.api.moex_client import MOEXClient
from src.utils.formatters import format_currency

def show():
    """Affiche la page des alertes"""
    
    st.markdown("# 🔔 Alertes de prix")
    
    # Onglets
    tab1, tab2 = st.tabs(["📋 Alertes actives", "➕ Nouvelle alerte"])
    
    with tab1:
        st.markdown("### 📋 Alertes actives")
        
        if st.session_state.price_alerts:
            for i, alert_dict in enumerate(st.session_state.price_alerts):
                # Convertir en objet Alert si c'est un dictionnaire
                if isinstance(alert_dict, dict):
                    alert = PriceAlert.from_dict(alert_dict)
                else:
                    alert = alert_dict
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{alert.symbol}**")
                    
                    with col2:
                        condition = "≥" if alert.alert_type == AlertType.ABOVE else "≤"
                        st.markdown(f"{condition} {format_currency(alert.target_price)}")
                    
                    with col3:
                        status_color = {
                            AlertStatus.ACTIVE: "🟢",
                            AlertStatus.TRIGGERED: "🔴",
                            AlertStatus.EXPIRED: "⚫",
                            AlertStatus.DISABLED: "⚪"
                        }.get(alert.status, "⚪")
                        
                        st.markdown(f"{status_color} {alert.status.value}")
                    
                    with col4:
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state.price_alerts.pop(i)
                            st.rerun()
                    
                    st.caption(f"Créée le {alert.created_at.strftime('%d/%m/%Y %H:%M')}")
                    if alert.one_time:
                        st.caption("🔄 Usage unique")
                    
                    st.markdown("---")
        else:
            st.info("Aucune alerte active. Créez votre première alerte dans l'onglet 'Nouvelle alerte'.")
    
    with tab2:
        st.markdown("### ➕ Créer une nouvelle alerte")
        
        with st.form("new_alert_form"):
            # Récupérer la liste des actions
            client = MOEXClient()
            try:
                securities_df = client.get_securities()
                if not securities_df.empty:
                    ticker_options = securities_df['SECID'].tolist()
                    symbol = st.selectbox(
                        "Symbole",
                        options=ticker_options,
                        index=0 if ticker_options else 0
                    )
                else:
                    symbol = st.selectbox(
                        "Symbole",
                        options=st.session_state.watchlist,
                        index=0
                    )
            except:
                symbol = st.selectbox(
                    "Symbole",
                    options=st.session_state.watchlist,
                    index=0
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                alert_type = st.selectbox(
                    "Type d'alerte",
                    options=[AlertType.ABOVE, AlertType.BELOW],
                    format_func=lambda x: "Au-dessus de" if x == AlertType.ABOVE else "En-dessous de"
                )
                
                target_price = st.number_input(
                    "Prix cible (₽)",
                    min_value=0.01,
                    value=100.0,
                    step=10.0
                )
            
            with col2:
                one_time = st.checkbox("Alerte unique", value=True, help="L'alerte se désactive après déclenchement")
                
                notification = st.checkbox("Notification email", value=False)
            
            submitted = st.form_submit_button("✅ Créer l'alerte")
            
            if submitted:
                alert = PriceAlert(
                    symbol=symbol,
                    alert_type=alert_type,
                    target_price=target_price,
                    one_time=one_time,
                    created_at=datetime.now()
                )
                
                st.session_state.price_alerts.append(alert.to_dict())
                st.success(f"✅ Alerte créée pour {symbol} à {format_currency(target_price)}")
                st.rerun()
    
    # Vérification périodique des alertes
    st.markdown("---")
    if st.button("🔄 Vérifier les alertes maintenant"):
        check_alerts()

def check_alerts():
    """Vérifie toutes les alertes actives"""
    client = MOEXClient()
    triggered = []
    
    for i, alert_dict in enumerate(st.session_state.price_alerts):
        if isinstance(alert_dict, dict):
            alert = PriceAlert.from_dict(alert_dict)
        else:
            alert = alert_dict
        
        if alert.status == AlertStatus.ACTIVE:
            try:
                market_data = client.get_market_data(alert.symbol)
                if not market_data.empty and 'LAST' in market_data.columns:
                    current_price = market_data['LAST'].iloc[0]
                    
                    if alert.check(current_price):
                        triggered.append(alert)
                        
                        # Mettre à jour dans la session
                        st.session_state.price_alerts[i] = alert.to_dict()
                        
                        st.balloons()
                        st.success(f"🎯 Alerte déclenchée pour {alert.symbol} à {format_currency(current_price)}")
            except:
                pass
    
    if not triggered:
        st.info("Aucune alerte déclenchée")