import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pytz
import warnings
import random
from requests.exceptions import HTTPError, ConnectionError
import urllib3
from functools import lru_cache
import hashlib
import pickle

warnings.filterwarnings('ignore')

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration de la page
st.set_page_config(
    page_title="Tracker Bourse Russie - MOEX",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du fuseau horaire
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')  # UTC+3
UTC4_TIMEZONE = pytz.FixedOffset(240)  # UTC+4

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #D52B1E;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Montserrat', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #D52B1E 0%, #FFFFFF 50%, #0039A6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stock-price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #D52B1E;
        text-align: center;
    }
    .stock-change-positive {
        color: #0039A6;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .stock-change-negative {
        color: #ef553b;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .portfolio-table {
        font-size: 0.9rem;
    }
    .stButton>button {
        width: 100%;
    }
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .russia-market-note {
        background: linear-gradient(135deg, #D52B1E 0%, #FFFFFF 50%, #0039A6 100%);
        color: #000000;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-weight: bold;
        text-align: center;
    }
    .moex-badge {
        background-color: #D52B1E;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .rts-badge {
        background-color: #0039A6;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .cache-badge {
        background-color: #6c757d;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = [
        'SBER.ME',      # Sberbank
        'GAZP.ME',      # Gazprom
        'LKOH.ME',      # Lukoil
        'ROSN.ME',      # Rosneft
        'GMKN.ME',      # Norilsk Nickel
        'YNDX.ME',      # Yandex
        'MTSS.ME',      # MTS
        'NVTK.ME',      # Novatek
        'MGNT.ME',      # Magnit
        'TATN.ME',      # Tatneft
    ]

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'email_config' not in st.session_state:
    st.session_state.email_config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': '',
        'password': ''
    }

if 'data_cache' not in st.session_state:
    st.session_state.data_cache = {}

if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = 0

if 'rate_limit_hits' not in st.session_state:
    st.session_state.rate_limit_hits = 0

# Mapping des suffixes russes
RUSSIAN_EXCHANGES = {
    '.ME': 'MOEX (Moscow Exchange)',
    '.MM': 'MOEX (alternative)',
    '': 'US Listed (ADR/GDR)'
}

# Jours fériés russes 2024
RUSSIAN_HOLIDAYS_2024 = [
    '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
    '2024-01-06', '2024-01-07', '2024-01-08', '2024-02-23', '2024-03-08',
    '2024-05-01', '2024-05-09', '2024-06-12', '2024-11-04', '2024-12-30',
    '2024-12-31',
]

# Cache fichier pour persister les données entre les redémarrages
CACHE_DIR = "stock_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_key(symbol, period, interval):
    """Génère une clé de cache unique"""
    return hashlib.md5(f"{symbol}_{period}_{interval}".encode()).hexdigest()

def save_to_file_cache(key, data):
    """Sauvegarde les données dans un fichier cache"""
    try:
        cache_file = os.path.join(CACHE_DIR, f"{key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'timestamp': datetime.now(),
                'data': data
            }, f)
    except Exception as e:
        st.warning(f"Erreur lors de la sauvegarde du cache: {e}")

def load_from_file_cache(key, max_age_minutes=30):
    """Charge les données du cache fichier"""
    try:
        cache_file = os.path.join(CACHE_DIR, f"{key}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
                age = datetime.now() - cached['timestamp']
                if age.total_seconds() < max_age_minutes * 60:
                    return cached['data']
    except Exception as e:
        st.warning(f"Erreur lors du chargement du cache: {e}")
    return None

def rate_limiter(min_interval=2):
    """Limite le taux d'appels API"""
    current_time = time.time()
    time_since_last_call = current_time - st.session_state.last_api_call
    
    if time_since_last_call < min_interval:
        sleep_time = min_interval - time_since_last_call
        time.sleep(sleep_time)
    
    st.session_state.last_api_call = time.time()

def fetch_with_retry(symbol, period, interval, max_retries=5):
    """Récupère les données avec retry et backoff exponentiel"""
    
    for attempt in range(max_retries):
        try:
            # Appliquer le rate limiting
            rate_limiter(min_interval=2)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval, timeout=15)
            info = ticker.info
            
            if hist is not None and not hist.empty:
                return hist, info
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "429" in error_str or "too many requests" in error_str:
                st.session_state.rate_limit_hits += 1
                
                if attempt < max_retries - 1:
                    # Backoff exponentiel avec jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    
                    progress_text = f"⚠️ Limite API atteinte. Attente {wait_time:.1f}s..."
                    if attempt == 0:
                        st.toast(progress_text, icon="⏳")
                    elif attempt == 1:
                        st.warning(progress_text)
                    else:
                        with st.spinner(progress_text):
                            time.sleep(wait_time)
                    continue
            else:
                if attempt < max_retries - 1:
                    wait_time = 1 + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                else:
                    st.error(f"Erreur après {max_retries} tentatives: {e}")
    
    return None, None

@st.cache_data(ttl=300, show_spinner="Chargement des données...")
def load_stock_data_cached(symbol, period, interval):
    """Version mise en cache du chargement des données"""
    return fetch_with_retry(symbol, period, interval)

def load_stock_data(symbol, period, interval, force_refresh=False):
    """Charge les données avec stratégie de cache multiple"""
    
    cache_key = get_cache_key(symbol, period, interval)
    
    # Vérifier le cache session
    if not force_refresh and cache_key in st.session_state.data_cache:
        cached = st.session_state.data_cache[cache_key]
        age = datetime.now() - cached['timestamp']
        if age.total_seconds() < 300:  # 5 minutes
            return cached['hist'], cached['info']
    
    # Vérifier le cache fichier
    if not force_refresh:
        file_cached = load_from_file_cache(cache_key, max_age_minutes=30)
        if file_cached:
            hist, info = file_cached
            st.session_state.data_cache[cache_key] = {
                'hist': hist,
                'info': info,
                'timestamp': datetime.now()
            }
            return hist, info
    
    # Faire un appel API
    with st.spinner(f"🔄 Chargement des données pour {symbol}..."):
        hist, info = load_stock_data_cached(symbol, period, interval)
    
    if hist is not None and not hist.empty:
        # Convertir en UTC+4
        if hist.index.tz is None:
            hist.index = hist.index.tz_localize('UTC').tz_convert(UTC4_TIMEZONE)
        else:
            hist.index = hist.index.tz_convert(UTC4_TIMEZONE)
        
        # Sauvegarder dans les caches
        st.session_state.data_cache[cache_key] = {
            'hist': hist,
            'info': info,
            'timestamp': datetime.now()
        }
        
        save_to_file_cache(cache_key, (hist, info))
        
        return hist, info
    
    return None, None

def load_multiple_stocks(symbols, period="1d"):
    """Charge plusieurs actions en une seule fois pour optimiser les appels"""
    results = {}
    
    with st.spinner(f"Chargement de {len(symbols)} symboles..."):
        for symbol in symbols:
            hist, info = load_stock_data(symbol, period, "1d", force_refresh=False)
            if hist is not None and not hist.empty:
                results[symbol] = {
                    'price': hist['Close'].iloc[-1],
                    'change': ((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100) if len(hist) > 1 else 0
                }
            time.sleep(0.5)  # Petit délai entre les requêtes
    
    return results

def get_exchange(symbol):
    """Détermine l'échange pour un symbole"""
    if symbol.endswith('.ME') or symbol.endswith('.MM'):
        return 'MOEX (Moscow Exchange)'
    else:
        return 'US Listed (ADR/GDR)'

def get_currency(symbol):
    """Détermine la devise pour un symbole"""
    if symbol.endswith('.ME') or symbol.endswith('.MM'):
        return 'RUB'
    else:
        return 'USD'

def format_currency(value, symbol):
    """Formate la monnaie selon le symbole"""
    if value is None or value == 0:
        return "N/A"
    
    currency = get_currency(symbol)
    if currency == 'RUB':
        if value >= 1e12:
            return f"₽{value/1e12:.2f} трлн"
        elif value >= 1e9:
            return f"₽{value/1e9:.2f} млрд"
        elif value >= 1e6:
            return f"₽{value/1e6:.2f} млн"
        else:
            return f"₽{value:,.2f}"
    else:
        return f"${value:.2f}"

def send_email_alert(subject, body, to_email):
    """Envoie une notification par email"""
    if not st.session_state.email_config['enabled']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(
            st.session_state.email_config['smtp_server'], 
            st.session_state.email_config['smtp_port']
        )
        server.starttls()
        server.login(
            st.session_state.email_config['email'],
            st.session_state.email_config['password']
        )
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi: {e}")
        return False

def check_price_alerts(current_price, symbol):
    """Vérifie les alertes de prix"""
    triggered = []
    for alert in st.session_state.price_alerts:
        if alert['symbol'] == symbol:
            if alert['condition'] == 'above' and current_price >= alert['price']:
                triggered.append(alert)
            elif alert['condition'] == 'below' and current_price <= alert['price']:
                triggered.append(alert)
    
    return triggered

def get_market_status():
    """Détermine le statut du marché russe (MOEX) en UTC+4"""
    now_utc4 = datetime.now(UTC4_TIMEZONE)
    hour = now_utc4.hour
    minute = now_utc4.minute
    weekday = now_utc4.weekday()
    date_str = now_utc4.strftime('%Y-%m-%d')
    
    # Weekend
    if weekday >= 5:
        return "Fermé (weekend)", "🔴"
    
    # Jours fériés
    if date_str in RUSSIAN_HOLIDAYS_2024:
        return "Fermé (jour férié)", "🔴"
    
    # Horaires MOEX en UTC+4: 11:00 - 19:45
    if (hour > 11 or (hour == 11 and minute >= 0)) and hour < 19:
        return "Ouvert", "🟢"
    elif hour == 19 and minute <= 45:
        return "Ouvert", "🟢"
    else:
        return "Fermé", "🔴"

def safe_get_metric(hist, metric, index=-1):
    """Récupère une métrique en toute sécurité"""
    try:
        if hist is not None and not hist.empty and len(hist) > abs(index):
            return hist[metric].iloc[index]
        return 0
    except:
        return 0

# Titre principal
st.markdown("<h1 class='main-header'>🇷🇺 Tracker Bourse Russie - MOEX en Temps Réel</h1>", unsafe_allow_html=True)

# Bannière de fuseau horaire
current_time_utc4 = datetime.now(UTC4_TIMEZONE)
current_time_moscow = datetime.now(MOSCOW_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇷🇺 Heure locale (UTC+4) : {current_time_utc4.strftime('%H:%M:%S')}<br>
    🇷🇺 Heure Moscou (MSK - UTC+3) : {current_time_moscow.strftime('%H:%M:%S')}<br>
    📍 Toutes les heures affichées sont en UTC+4
</div>
""", unsafe_allow_html=True)

# Avertissement API si trop de hits
if st.session_state.rate_limit_hits > 5:
    st.markdown("""
    <div class='warning-box'>
        <b>⚠️ Limitations API détectées</b><br>
        Yahoo Finance applique des limites de requêtes. Les données peuvent être en cache ou retardées.
        Les actualisations automatiques sont temporairement ralenties.
    </div>
    """, unsafe_allow_html=True)

# Note sur le marché russe
st.markdown("""
<div class='russia-market-note'>
    <span class='moex-badge'>MOEX</span> 
    <span class='rts-badge'>RTS</span><br>
    🇷🇺 Bourse de Moscou (MOEX) - Principale bourse russe<br>
    - Actions MOEX: suffixe .ME (ex: SBER.ME - Sberbank)<br>
    - ADRs: symboles US (ex: Yandex → YNDX)<br>
    Horaires trading: 11:00 - 19:45 (UTC+4)
</div>
""", unsafe_allow_html=True)

# Sidebar pour la navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/russian-federation.png", width=80)
    st.title("Navigation")
    
    # Bouton de rafraîchissement forcé
    if st.button("🔄 Forcer le rafraîchissement", use_container_width=True):
        st.cache_data.clear()
        st.session_state.data_cache = {}
        st.rerun()
    
    st.markdown("---")
    
    menu = st.radio(
        "Choisir une section",
        ["📈 Tableau de bord", 
         "💰 Portefeuille virtuel", 
         "🔔 Alertes de prix",
         "📧 Notifications email",
         "📤 Export des données",
         "🤖 Prédictions ML",
         "🇷🇺 Indices MOEX & RTS"]
    )
    
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    # Sélection du symbole principal
    symbol = st.selectbox(
        "Symbole principal",
        options=st.session_state.watchlist + ["Autre..."],
        index=0
    )
    
    if symbol == "Autre...":
        symbol = st.text_input("Entrer un symbole", value="SBER.ME").upper()
        if symbol and symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(symbol)
    
    # Période et intervalle
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox(
            "Période",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            index=2
        )
    
    with col2:
        interval_map = {
            "1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes",
            "30m": "30 minutes", "1h": "1 heure", "1d": "1 jour",
            "1wk": "1 semaine"
        }
        interval = st.selectbox(
            "Intervalle",
            options=list(interval_map.keys()),
            format_func=lambda x: interval_map[x],
            index=6
        )
    
    # Auto-refresh avec intervalle plus long si limitations
    auto_refresh = st.checkbox("Actualisation auto", value=False)
    if auto_refresh:
        min_refresh = 120 if st.session_state.rate_limit_hits > 3 else 60
        refresh_rate = st.slider(
            "Fréquence (s)",
            min_value=min_refresh,
            max_value=300,
            value=min_refresh,
            step=30
        )
    
    # Stats API
    st.markdown("---")
    st.caption(f"📊 Appels API: {st.session_state.rate_limit_hits} limitations")
    st.caption(f"💾 Cache: {len(st.session_state.data_cache)} entrées")

# Chargement des données
hist, info = load_stock_data(symbol, period, interval)

if hist is None or hist.empty:
    st.error(f"❌ Impossible de charger les données pour {symbol}")
    st.info("💡 Suggestions:\n- Réessayez dans quelques minutes\n- Vérifiez que le symbole est correct\n- Utilisez le bouton 'Forcer le rafraîchissement'")
    st.stop()

current_price = safe_get_metric(hist, 'Close')

# Vérification des alertes
triggered_alerts = check_price_alerts(current_price, symbol)
for alert in triggered_alerts:
    st.balloons()
    st.success(f"🎯 Alerte déclenchée pour {symbol} à {format_currency(current_price, symbol)}")
    
    if alert.get('one_time', False):
        st.session_state.price_alerts.remove(alert)

# ============================================================================
# SECTION 1: TABLEAU DE BORD
# ============================================================================
if menu == "📈 Tableau de bord":
    # Statut du marché
    market_status, market_icon = get_market_status()
    
    col_status, col_cache = st.columns([3, 1])
    with col_status:
        st.info(f"{market_icon} Marché Russe (MOEX): {market_status}")
    with col_cache:
        cache_age = datetime.now(UTC4_TIMEZONE) - hist.index[-1]
        st.caption(f"🕒 Données: il y a {cache_age.total_seconds()//60:.0f} min")
    
    if hist is not None and not hist.empty:
        exchange = get_exchange(symbol)
        currency = get_currency(symbol)
        
        company_name = info.get('longName', symbol) if info else symbol
        
        st.subheader(f"📊 Aperçu en temps réel - {company_name}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        previous_close = safe_get_metric(hist, 'Close', -2) if len(hist) > 1 else current_price
        change = current_price - previous_close
        change_pct = (change / previous_close * 100) if previous_close != 0 else 0
        
        with col1:
            st.metric(
                label="Prix actuel",
                value=format_currency(current_price, symbol),
                delta=f"{change:.2f} ({change_pct:.2f}%)"
            )
        
        with col2:
            day_high = safe_get_metric(hist, 'High')
            st.metric("Plus haut", format_currency(day_high, symbol))
        
        with col3:
            day_low = safe_get_metric(hist, 'Low')
            st.metric("Plus bas", format_currency(day_low, symbol))
        
        with col4:
            volume = safe_get_metric(hist, 'Volume')
            if currency == 'RUB':
                volume_formatted = f"{volume/1e9:.2f} млрд" if volume > 1e9 else f"{volume/1e6:.2f} млн" if volume > 1e6 else f"{volume:,.0f}"
            else:
                volume_formatted = f"{volume/1e6:.1f}M" if volume > 1e6 else f"{volume/1e3:.1f}K"
            st.metric("Volume", volume_formatted)
        
        st.caption(f"Dernière mise à jour: {hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (UTC+4)")
        
        # Graphique principal
        st.subheader("📉 Évolution du prix")
        
        fig = go.Figure()
        
        if interval in ["1m", "5m", "15m", "30m", "1h"]:
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='Prix',
                increasing_line_color='#0039A6',
                decreasing_line_color='#ef553b'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='Prix',
                line=dict(color='#D52B1E', width=2)
            ))
        
        if len(hist) >= 20:
            ma_20 = hist['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=ma_20,
                mode='lines',
                name='MA 20',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        if len(hist) >= 50:
            ma_50 = hist['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=ma_50,
                mode='lines',
                name='MA 50',
                line=dict(color='purple', width=1, dash='dash')
            ))
        
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='lightgray', opacity=0.3)
        ))
        
        fig.update_layout(
            title=f"{symbol} - {period} (UTC+4)",
            yaxis_title=f"Prix ({'₽' if currency=='RUB' else '$'})",
            yaxis2=dict(
                title="Volume",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            xaxis_title="Date (UTC+4)",
            height=600,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Informations sur l'entreprise
        with st.expander("ℹ️ Informations sur l'entreprise"):
            if info:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Nom :** {info.get('longName', 'N/A')}")
                    st.write(f"**Secteur :** {info.get('sector', 'N/A')}")
                    st.write(f"**Industrie :** {info.get('industry', 'N/A')}")
                    st.write(f"**Site web :** {info.get('website', 'N/A')}")
                    st.write(f"**Bourse :** {exchange}")
                    st.write(f"**Devise :** {currency}")
                
                with col2:
                    market_cap = info.get('marketCap', 0)
                    if market_cap > 0:
                        if currency == 'RUB':
                            st.write(f"**Capitalisation :** ₽{market_cap:,.0f} ({format_large_number_russian(market_cap)})")
                        else:
                            st.write(f"**Capitalisation :** ${market_cap:,.0f}")
                    else:
                        st.write("**Capitalisation :** N/A")
                    
                    pe = info.get('trailingPE', 'N/A')
                    st.write(f"**P/E :** {pe if pe != 'N/A' else 'N/A'}")
                    
                    div_yield = info.get('dividendYield', 0)
                    st.write(f"**Dividende :** {div_yield*100:.2f}%" if div_yield else "**Dividende :** N/A")
                    
                    beta = info.get('beta', 'N/A')
                    st.write(f"**Beta :** {beta if beta != 'N/A' else 'N/A'}")
            else:
                st.write("Informations non disponibles")

# ============================================================================
# SECTION 2: PORTEFEUILLE VIRTUEL
# ============================================================================
elif menu == "💰 Portefeuille virtuel":
    st.subheader("💰 Gestion de portefeuille virtuel - Actions Russes")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.text_input("Symbole", value="SBER.ME").upper()
            shares = st.number_input("Nombre d'actions", min_value=1, step=1, value=100)
            buy_price = st.number_input("Prix d'achat (₽)", min_value=0.01, step=10.0, value=280.0)
            
            if st.form_submit_button("Ajouter au portefeuille"):
                if symbol_pf and shares > 0:
                    if symbol_pf not in st.session_state.portfolio:
                        st.session_state.portfolio[symbol_pf] = []
                    
                    st.session_state.portfolio[symbol_pf].append({
                        'shares': shares,
                        'buy_price': buy_price,
                        'date': datetime.now(UTC4_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    st.success(f"✅ {shares} actions {symbol_pf} ajoutées")
    
    with col1:
        st.markdown("### 📊 Performance du portefeuille")
        
        if st.session_state.portfolio:
            portfolio_data = []
            total_value_rub = 0
            total_cost_rub = 0
            
            for symbol_pf, positions in st.session_state.portfolio.items():
                try:
                    hist, _ = load_stock_data(symbol_pf, "1d", "1d", force_refresh=False)
                    current = hist['Close'].iloc[-1] if hist is not None and not hist.empty else 0
                    
                    exchange = get_exchange(symbol_pf)
                    currency = get_currency(symbol_pf)
                    
                    for pos in positions:
                        shares = pos['shares']
                        buy_price = pos['buy_price']
                        cost = shares * buy_price
                        value = shares * current
                        profit = value - cost
                        profit_pct = (profit / cost * 100) if cost > 0 else 0
                        
                        if currency == 'RUB':
                            total_cost_rub += cost
                            total_value_rub += value
                        
                        portfolio_data.append({
                            'Symbole': symbol_pf,
                            'Marché': exchange,
                            'Actions': shares,
                            "Prix d'achat": f"₽{buy_price:,.2f}",
                            'Prix actuel': f"₽{current:,.2f}" if current else "N/A",
                            'Valeur': f"₽{value:,.2f}",
                            'Profit': f"₽{profit:,.2f}",
                            'Profit %': f"{profit_pct:.1f}%"
                        })
                except Exception as e:
                    st.warning(f"Impossible de charger {symbol_pf}")
            
            if portfolio_data:
                total_profit_rub = total_value_rub - total_cost_rub
                total_profit_pct_rub = (total_profit_rub / total_cost_rub * 100) if total_cost_rub > 0 else 0
                
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur totale", f"₽{total_value_rub:,.2f}")
                col_i2.metric("Coût total", f"₽{total_cost_rub:,.2f}")
                col_i3.metric("Profit total", f"₽{total_profit_rub:,.2f}", delta=f"{total_profit_pct_rub:.1f}%")
                
                st.markdown("### 📋 Positions détaillées")
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
            else:
                st.info("Aucune donnée de performance disponible")
        else:
            st.info("Aucune position dans le portefeuille")

# ============================================================================
# SECTION 3: ALERTES DE PRIX
# ============================================================================
elif menu == "🔔 Alertes de prix":
    st.subheader("🔔 Gestion des alertes de prix")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ➕ Créer une nouvelle alerte")
        with st.form("new_alert"):
            alert_symbol = st.text_input("Symbole", value=symbol if symbol else "SBER.ME").upper()
            
            default_price = float(current_price * 1.05) if current_price > 0 else 280.0
            alert_price = st.number_input(
                f"Prix cible ({format_currency(0, alert_symbol).split('0')[0]})", 
                min_value=0.01, 
                step=10.0, 
                value=default_price
            )
            
            col_cond, col_type = st.columns(2)
            with col_cond:
                condition = st.selectbox("Condition", ["above (au-dessus)", "below (en-dessous)"])
                condition = condition.split()[0]
            with col_type:
                alert_type = st.selectbox("Type", ["Permanent", "Une fois"])
            
            one_time = alert_type == "Une fois"
            
            if st.form_submit_button("Créer l'alerte"):
                st.session_state.price_alerts.append({
                    'symbol': alert_symbol,
                    'price': alert_price,
                    'condition': condition,
                    'one_time': one_time,
                    'created': datetime.now(UTC4_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ Alerte créée pour {alert_symbol}")
    
    with col2:
        st.markdown("### 📋 Alertes actives")
        if st.session_state.price_alerts:
            for i, alert in enumerate(st.session_state.price_alerts):
                with st.container():
                    st.markdown(f"""
                    <div class='alert-box alert-warning'>
                        <b>{alert['symbol']}</b> - {alert['condition']} {format_currency(alert['price'], alert['symbol'])}<br>
                        <small>Créée: {alert['created']} | {('Unique' if alert['one_time'] else 'Permanent')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Supprimer", key=f"del_alert_{i}"):
                        st.session_state.price_alerts.pop(i)
                        st.rerun()
        else:
            st.info("Aucune alerte active")

# ============================================================================
# SECTION 4: NOTIFICATIONS EMAIL
# ============================================================================
elif menu == "📧 Notifications email":
    st.subheader("📧 Configuration des notifications email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer les notifications email", value=st.session_state.email_config['enabled'])
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("Serveur SMTP", value=st.session_state.email_config['smtp_server'])
            smtp_port = st.number_input("Port SMTP", value=st.session_state.email_config['smtp_port'])
        
        with col2:
            email = st.text_input("Adresse email", value=st.session_state.email_config['email'])
            password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        
        test_email = st.text_input("Email de test (optionnel)")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Sauvegarder"):
                st.session_state.email_config = {
                    'enabled': enabled,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email': email,
                    'password': password
                }
                st.success("Configuration sauvegardée !")
        
        with col_btn2:
            if st.form_submit_button("📨 Tester"):
                if test_email:
                    if send_email_alert(
                        "Test de notification",
                        f"<h2>Test réussi !</h2><p>{datetime.now(UTC4_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (UTC+4)</p>",
                        test_email
                    ):
                        st.success("Email de test envoyé !")
                    else:
                        st.error("Échec de l'envoi")

# ============================================================================
# SECTION 5: EXPORT DES DONNÉES
# ============================================================================
elif menu == "📤 Export des données":
    st.subheader("📤 Export des données")
    
    if hist is not None and not hist.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Données historiques")
            display_hist = hist.copy()
            display_hist.index = display_hist.index.strftime('%Y-%m-%d %H:%M:%S (UTC+4)')
            st.dataframe(display_hist.tail(20))
            
            csv = hist.to_csv()
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"{symbol}_data_{datetime.now(UTC4_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("### 📈 Statistiques")
            stats = {
                'Moyenne': hist['Close'].mean(),
                'Écart-type': hist['Close'].std(),
                'Min': hist['Close'].min(),
                'Max': hist['Close'].max(),
                'Variation totale': f"{(hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100:.2f}%" if len(hist) > 1 else "N/A"
            }
            
            for key, value in stats.items():
                if isinstance(value, float):
                    st.write(f"{key}: {format_currency(value, symbol)}")
                else:
                    st.write(f"{key}: {value}")
            
            json_data = {
                'symbol': symbol,
                'exchange': get_exchange(symbol),
                'currency': get_currency(symbol),
                'last_update': datetime.now(UTC4_TIMEZONE).isoformat(),
                'timezone': 'UTC+4',
                'current_price': float(current_price) if current_price else 0,
                'statistics': {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in stats.items()},
            }
            
            st.download_button(
                label="📥 Télécharger en JSON",
                data=json.dumps(json_data, indent=2, default=str),
                file_name=f"{symbol}_data_{datetime.now(UTC4_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# ============================================================================
# SECTION 6: PRÉDICTIONS ML
# ============================================================================
elif menu == "🤖 Prédictions ML":
    st.subheader("🤖 Prédictions avec Machine Learning")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        df_pred = hist[['Close']].reset_index()
        df_pred['Days'] = (df_pred['Date'] - df_pred['Date'].min()).dt.days
        
        X = df_pred['Days'].values.reshape(-1, 1)
        y = df_pred['Close'].values
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_to_predict = st.slider("Jours à prédire", min_value=1, max_value=30, value=7)
            degree = st.slider("Degré du polynôme", min_value=1, max_value=5, value=2)
        
        with col2:
            show_confidence = st.checkbox("Afficher l'intervalle de confiance", value=True)
        
        model = make_pipeline(
            PolynomialFeatures(degree=degree),
            LinearRegression()
        )
        model.fit(X, y)
        
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_to_predict + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        last_date = df_pred['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        fig_pred = go.Figure()
        
        fig_pred.add_trace(go.Scatter(
            x=df_pred['Date'],
            y=y,
            mode='lines',
            name='Historique',
            line=dict(color='blue')
        ))
        
        fig_pred.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Prédictions',
            line=dict(color='red', dash='dash'),
            marker=dict(size=8)
        ))
        
        if show_confidence:
            residuals = y - model.predict(X)
            std_residuals = np.std(residuals)
            
            upper_bound = predictions + 2 * std_residuals
            lower_bound = predictions - 2 * std_residuals
            
            fig_pred.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='rgba(255,0,0,0)'),
                name='Intervalle confiance 95%'
            ))
        
        fig_pred.update_layout(
            title=f"Prédictions pour {symbol} - {days_to_predict} jours",
            xaxis_title="Date (UTC+4)",
            yaxis_title=f"Prix ({'₽' if get_currency(symbol)=='RUB' else '$'})",
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        st.markdown("### 📋 Prédictions détaillées")
        pred_df = pd.DataFrame({
            'Date (UTC+4)': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [format_currency(p, symbol) for p in predictions],
            'Variation %': [f"{(p/current_price - 1)*100:.2f}%" for p in predictions]
        })
        st.dataframe(pred_df, use_container_width=True)

# ============================================================================
# SECTION 7: INDICES MOEX & RTS
# ============================================================================
elif menu == "🇷🇺 Indices MOEX & RTS":
    st.subheader("🇷🇺 Indices boursiers russes")
    
    russian_indices = {
        'IMOEX.ME': 'MOEX Russia Index (Roubles)',
        'RTSI.ME': 'RTS Index (Dollars)',
        'RGBI.ME': 'Russian Government Bond Index',
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### 🇷🇺 Sélection")
        selected_index = st.selectbox(
            "Choisir un indice",
            options=list(russian_indices.keys()),
            format_func=lambda x: f"{russian_indices[x]} ({x})",
            index=0
        )
    
    with col1:
        try:
            index_hist, _ = load_stock_data(selected_index, "1mo", "1d")
            
            if index_hist is not None and not index_hist.empty:
                current_index = index_hist['Close'].iloc[-1]
                prev_index = index_hist['Close'].iloc[-2] if len(index_hist) > 1 else current_index
                index_change = current_index - prev_index
                index_change_pct = (index_change / prev_index * 100) if prev_index != 0 else 0
                
                st.markdown(f"### {russian_indices[selected_index]}")
                
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur", f"{current_index:,.2f}")
                col_i2.metric("Variation", f"{index_change:,.2f}")
                col_i3.metric("Variation %", f"{index_change_pct:.2f}%", delta=f"{index_change_pct:.2f}%")
                
                st.caption(f"Dernière mise à jour: {index_hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (UTC+4)")
                
                fig_index = go.Figure()
                fig_index.add_trace(go.Scatter(
                    x=index_hist.index,
                    y=index_hist['Close'],
                    mode='lines',
                    name=russian_indices[selected_index],
                    line=dict(color='#D52B1E', width=2)
                ))
                
                fig_index.update_layout(
                    title=f"Évolution - 1 mois",
                    xaxis_title="Date (UTC+4)",
                    yaxis_title="Points",
                    height=400,
                    template='plotly_white'
                )
                
                st.plotly_chart(fig_index, use_container_width=True)
            else:
                st.warning("Données non disponibles")
        except Exception as e:
            st.error(f"Erreur: {e}")

# ============================================================================
# WATCHLIST
# ============================================================================
st.markdown("---")
col_w1, col_w2 = st.columns([3, 1])

with col_w1:
    st.subheader("📋 Watchlist")
    
    if st.button("🔄 Rafraîchir la watchlist", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Charger les données de la watchlist de manière optimisée
    watchlist_data = load_multiple_stocks(st.session_state.watchlist[:8])  # Limiter à 8 pour éviter trop d'appels
    
    cols_per_row = 4
    symbols_list = list(watchlist_data.keys())
    
    for i in range(0, len(symbols_list), cols_per_row):
        cols = st.columns(min(cols_per_row, len(symbols_list) - i))
        for j, sym in enumerate(symbols_list[i:i+cols_per_row]):
            with cols[j]:
                data = watchlist_data[sym]
                st.metric(
                    sym, 
                    format_currency(data['price'], sym),
                    delta=f"{data['change']:.1f}%"
                )

with col_w2:
    current_time = datetime.now(UTC4_TIMEZONE)
    st.caption(f"🇷🇺 Heure: {current_time.strftime('%H:%M:%S')} (UTC+4)")
    
    market_status, market_icon = get_market_status()
    st.caption(f"{market_icon} Marché: {market_status}")
    
    if auto_refresh and hist is not None and not hist.empty:
        time.sleep(refresh_rate)
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🇷🇺 Tracker Bourse Russie - MOEX | Données yfinance | 🕐 UTC+4"
    "</p>",
    unsafe_allow_html=True
)
