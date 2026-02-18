"""
Gestion de l'état de session Streamlit
"""
import streamlit as st
from datetime import datetime
from src.utils.time_utils import get_utc4_time

def init_session_state():
    """Initialise toutes les variables de session"""
    
    # Portefeuille
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    
    # Alertes
    if 'price_alerts' not in st.session_state:
        st.session_state.price_alerts = []
    
    # Watchlist par défaut
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = [
            'SBER', 'GAZP', 'LKOH', 'ROSN', 'GMKN',
            'YNDX', 'MTSS', 'NVTK', 'MGNT', 'TATN'
        ]
    
    # Cache des données
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = {}
    
    # Dernière mise à jour
    if 'last_update' not in st.session_state:
        st.session_state.last_update = get_utc4_time().strftime('%H:%M:%S')
    
    # Configuration email
    if 'email_config' not in st.session_state:
        st.session_state.email_config = {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',
            'password': ''
        }
    
    # Préférences utilisateur
    if 'preferences' not in st.session_state:
        st.session_state.preferences = {
            'theme': 'light',
            'default_period': '1mo',
            'refresh_rate': 60,
            'currency': 'RUB'
        }
    
    # Statistiques API
    if 'api_stats' not in st.session_state:
        st.session_state.api_stats = {
            'total_requests': 0,
            'rate_limit_hits': 0,
            'last_request_time': None
        }

def update_last_update():
    """Met à jour le timestamp de dernière mise à jour"""
    st.session_state.last_update = get_utc4_time().strftime('%H:%M:%S')

def add_to_cache(key: str, value, ttl: int = 300):
    """
    Ajoute une valeur au cache session
    
    Args:
        key: Clé du cache
        value: Valeur à stocker
        ttl: Durée de vie en secondes
    """
    st.session_state.data_cache[key] = {
        'value': value,
        'timestamp': datetime.now(),
        'ttl': ttl
    }

def get_from_cache(key: str):
    """
    Récupère une valeur du cache si non expirée
    
    Args:
        key: Clé du cache
        
    Returns:
        Valeur ou None si expirée/non trouvée
    """
    if key in st.session_state.data_cache:
        cached = st.session_state.data_cache[key]
        age = (datetime.now() - cached['timestamp']).total_seconds()
        if age < cached['ttl']:
            return cached['value']
        else:
            del st.session_state.data_cache[key]
    return None