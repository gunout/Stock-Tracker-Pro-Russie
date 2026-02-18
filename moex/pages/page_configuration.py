"""
Page Configuration
"""
import streamlit as st
import json
from datetime import datetime

def show():
    st.markdown("# ⚙️ Configuration")
    
    tab1, tab2, tab3 = st.tabs(["🎨 Apparence", "📧 Notifications", "📊 Données"])
    
    with tab1:
        st.selectbox("Thème", ["Clair", "Sombre"])
        st.selectbox("Langue", ["Français", "English", "Русский"])
        st.slider("Taux de rafraîchissement (s)", 30, 300, 60)
    
    with tab2:
        st.checkbox("Activer les notifications email")
        st.text_input("Serveur SMTP", "smtp.gmail.com")
        st.text_input("Email")
        st.text_input("Mot de passe", type="password")
    
    with tab3:
        st.write(f"Cache: {len(st.session_state)} entrées")
        if st.button("Vider le cache"):
            st.cache_data.clear()
            st.success("Cache vidé !")
