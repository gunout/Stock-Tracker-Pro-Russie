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
USER_TIMEZONE = pytz.timezone('Europe/Paris')  # UTC+1/UTC+2
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')  # UTC+3 (MSK - Moscow Time)
US_TIMEZONE = pytz.timezone('America/New_York')

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
    .demo-mode-badge {
        background-color: #ff9800;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 0.5rem;
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
        'SNGS.ME',      # Surgutneftegas (pref)
        'SNGSP.ME',     # Surgutneftegas (common)
        'MOEX.ME',      # Moscow Exchange
        'AFKS.ME',      # Sistema
        'PHOR.ME',      # PhosAgro
        'PLZL.ME',      # Polymetal
        'ALRS.ME',      # Alrosa
        'RUAL.ME',      # Rusal
        'MAGN.ME',      # Magnitogorsk Iron & Steel
        'CHMF.ME',      # Severstal
        'NLMK.ME',      # NLMK
        'HYDR.ME',      # RusHydro
        'AFLT.ME',      # Aeroflot
        'FIVE.ME',      # X5 Retail Group
        'MAIL.ME',      # Mail.ru Group
        'QIWI.ME',      # Qiwi
        'TCSG.ME',      # TCS Group (Tinkoff)
        'FESH.ME',      # FESCO
        'LSRG.ME',      # LSR Group
        'PIKK.ME',      # PIK Group
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

if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

if 'last_successful_data' not in st.session_state:
    st.session_state.last_successful_data = {}

# Mapping des suffixes russes
RUSSIAN_EXCHANGES = {
    '.ME': 'MOEX (Moscow Exchange)',
    '.MM': 'MOEX (alternative)',
    '': 'US Listed (ADR/GDR)'
}

# Jours fériés russes 2024
RUSSIAN_HOLIDAYS_2024 = [
    '2024-01-01',  # New Year Holidays
    '2024-01-02',  # New Year Holidays
    '2024-01-03',  # New Year Holidays
    '2024-01-04',  # New Year Holidays
    '2024-01-05',  # New Year Holidays
    '2024-01-06',  # New Year Holidays
    '2024-01-07',  # Orthodox Christmas
    '2024-01-08',  # New Year Holidays
    '2024-02-23',  # Defender of the Fatherland Day
    '2024-03-08',  # International Women's Day
    '2024-05-01',  # Spring and Labor Day
    '2024-05-09',  # Victory Day
    '2024-06-12',  # Russia Day
    '2024-11-04',  # Unity Day
    '2024-12-30',  # New Year Holidays (early)
    '2024-12-31',  # New Year Holidays
]

# Données de démonstration pour les principales actions russes
DEMO_DATA = {
    'SBER.ME': {
        'name': 'Sberbank of Russia',
        'current_price': 280.50,
        'previous_close': 275.30,
        'day_high': 285.20,
        'day_low': 276.10,
        'volume': 85000000,
        'market_cap': 6200000000000,  # 6.2 трлн RUB
        'pe_ratio': 5.2,
        'dividend_yield': 8.5,
        'beta': 0.95,
        'sector': 'Financials',
        'industry': 'Banking',
        'website': 'www.sberbank.ru'
    },
    'GAZP.ME': {
        'name': 'Gazprom',
        'current_price': 165.80,
        'previous_close': 162.40,
        'day_high': 168.50,
        'day_low': 163.20,
        'volume': 120000000,
        'market_cap': 3900000000000,  # 3.9 трлн RUB
        'pe_ratio': 3.8,
        'dividend_yield': 12.0,
        'beta': 1.2,
        'sector': 'Energy',
        'industry': 'Oil & Gas',
        'website': 'www.gazprom.ru'
    },
    'LKOH.ME': {
        'name': 'Lukoil',
        'current_price': 7200.50,
        'previous_close': 7150.00,
        'day_high': 7300.00,
        'day_low': 7100.50,
        'volume': 2500000,
        'market_cap': 5200000000000,  # 5.2 трлн RUB
        'pe_ratio': 4.5,
        'dividend_yield': 9.2,
        'beta': 1.1,
        'sector': 'Energy',
        'industry': 'Oil & Gas',
        'website': 'www.lukoil.ru'
    },
    'YNDX.ME': {
        'name': 'Yandex',
        'current_price': 2850.00,
        'previous_close': 2800.50,
        'day_high': 2900.00,
        'day_low': 2780.00,
        'volume': 1500000,
        'market_cap': 950000000000,  # 950 млрд RUB
        'pe_ratio': 25.0,
        'dividend_yield': 0,
        'beta': 1.5,
        'sector': 'Technology',
        'industry': 'Internet',
        'website': 'www.yandex.ru'
    }
}

# Fonction pour générer des données historiques de démonstration
def generate_demo_history(symbol, period="1mo", interval="1d"):
    """Génère des données historiques simulées pour la démonstration"""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Prix de base selon le symbole
    if symbol in DEMO_DATA:
        base_price = DEMO_DATA[symbol]['current_price']
        if symbol == 'GAZP.ME':
            volatility = 0.025
        elif symbol == 'SBER.ME':
            volatility = 0.02
        elif symbol == 'YNDX.ME':
            volatility = 0.035
        else:
            volatility = 0.02
    else:
        base_price = 1000
        volatility = 0.03
    
    # Générer une série de prix avec une légère tendance
    np.random.seed(hash(symbol) % 42)
    returns = np.random.normal(0.0003, volatility, len(dates))
    price_series = base_price * np.exp(np.cumsum(returns))
    
    # Créer le DataFrame
    df = pd.DataFrame({
        'Open': price_series * (1 - np.random.uniform(0, 0.01, len(dates))),
        'High': price_series * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': price_series * (1 - np.random.uniform(0, 0.02, len(dates))),
        'Close': price_series,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    # Convertir l'index en timezone-aware
    df.index = df.index.tz_localize(USER_TIMEZONE)
    
    return df

# Fonction pour charger les données avec gestion des erreurs améliorée
@st.cache_data(ttl=600)
def load_stock_data(symbol, period, interval, retry_count=3):
    """Charge les données boursières avec gestion des erreurs et retry"""
    
    # Vérifier si on a des données en cache dans la session
    if st.session_state.demo_mode and symbol in DEMO_DATA:
        return generate_demo_history(symbol, period, interval), DEMO_DATA[symbol]
    
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                time.sleep(2 ** attempt)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval, timeout=10)
            info = ticker.info
            
            if hist is not None and not hist.empty:
                if hist.index.tz is None:
                    hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
                else:
                    hist.index = hist.index.tz_convert(USER_TIMEZONE)
                
                st.session_state.last_successful_data[symbol] = {
                    'hist': hist,
                    'info': info,
                    'timestamp': datetime.now()
                }
                
                return hist, info
            
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                st.warning(f"⚠️ Limite de requêtes atteinte. Tentative {attempt + 1}/{retry_count}...")
            else:
                st.warning(f"⚠️ Erreur: {e}. Tentative {attempt + 1}/{retry_count}...")
    
    # Si toutes les tentatives échouent, utiliser les données en cache
    if symbol in st.session_state.last_successful_data:
        cached = st.session_state.last_successful_data[symbol]
        time_diff = datetime.now() - cached['timestamp']
        if time_diff.total_seconds() < 3600:
            st.info(f"📋 Utilisation des données en cache du {cached['timestamp'].strftime('%H:%M:%S')}")
            return cached['hist'], cached['info']
    
    # Activer le mode démo automatiquement
    if not st.session_state.demo_mode:
        st.session_state.demo_mode = True
        st.info("🔄 Mode démonstration activé - Données simulées")
    
    # Données de démonstration par défaut
    demo_info = DEMO_DATA.get(symbol, {
        'name': f'{symbol} (Données démo)',
        'current_price': 1000,
        'sector': 'N/A',
        'industry': 'N/A',
        'marketCap': 100000000000,
        'trailingPE': 10.0,
        'dividendYield': 0.05,
        'beta': 1.0
    })
    
    return generate_demo_history(symbol, period, interval), demo_info

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
        # Format russe: avec ₽ et séparateur
        if value >= 1e12:  # Трлн (trillion)
            return f"₽{value/1e12:.2f} трлн"
        elif value >= 1e9:  # Млрд (billion)
            return f"₽{value/1e9:.2f} млрд"
        elif value >= 1e6:  # Млн (million)
            return f"₽{value/1e6:.2f} млн"
        else:
            return f"₽{value:,.2f}"
    else:
        return f"${value:.2f}"

def format_large_number_russian(num):
    """Formate les grands nombres selon le système russe (тыс, млн, млрд, трлн)"""
    if num > 1e12:
        return f"{num/1e12:.2f} трлн"
    elif num > 1e9:
        return f"{num/1e9:.2f} млрд"
    elif num > 1e6:
        return f"{num/1e6:.2f} млн"
    elif num > 1e3:
        return f"{num/1e3:.2f} тыс"
    else:
        return f"{num:,.0f}"

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
    """Détermine le statut du marché russe (MOEX)"""
    moscow_now = datetime.now(MOSCOW_TIMEZONE)
    moscow_hour = moscow_now.hour
    moscow_minute = moscow_now.minute
    moscow_weekday = moscow_now.weekday()
    moscow_date = moscow_now.strftime('%Y-%m-%d')
    
    # Weekend (samedi = 5, dimanche = 6)
    if moscow_weekday >= 5:
        return "Fermé (weekend)", "🔴"
    
    # Jours fériés
    if moscow_date in RUSSIAN_HOLIDAYS_2024:
        return "Fermé (jour férié)", "🔴"
    
    # Horaires MOEX: 10:00 - 18:45 MSK
    if (moscow_hour > 10 or (moscow_hour == 10 and moscow_minute >= 0)) and moscow_hour < 18:
        return "Ouvert", "🟢"
    elif moscow_hour == 18 and moscow_minute <= 45:
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
current_time_paris = datetime.now(USER_TIMEZONE)
current_time_moscow = datetime.now(MOSCOW_TIMEZONE)
current_time_ny = datetime.now(US_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Heure Paris : {current_time_paris.strftime('%H:%M:%S')} (UTC+1/UTC+2)<br>
    🇷🇺 Heure Moscou : {current_time_moscow.strftime('%H:%M:%S')} (MSK - UTC+3)<br>
    🇺🇸 Heure NY : {current_time_ny.strftime('%H:%M:%S')} (UTC-4/UTC-5)<br>
    📍 Décalage Moscou/France : +1h/2h (selon heure d'été)
</div>
""", unsafe_allow_html=True)

# Mode démo badge
if st.session_state.demo_mode:
    st.markdown("""
    <div style='text-align: center; margin: 10px 0;'>
        <span class='demo-mode-badge'>🎮 MODE DÉMONSTRATION</span>
        <span style='color: #666;'>Données simulées - API temporairement indisponible</span>
    </div>
    """, unsafe_allow_html=True)

# Note sur le marché russe
st.markdown("""
<div class='russia-market-note'>
    <span class='moex-badge'>MOEX</span> 
    <span class='rts-badge'>RTS</span><br>
    🇷🇺 Bourse de Moscou (MOEX) - Principale bourse russe<br>
    - Actions MOEX: suffixe .ME (ex: SBER.ME - Sberbank)<br>
    - ADRs: symboles US (ex: Yandex → YNDX, Mobile TeleSystems → MBT)<br>
    - RTS Index: indices en dollars, MOEX Index: indices en roubles<br>
    Horaires trading: Lundi-Vendredi 10:00 - 18:45 (MSK)
</div>
""", unsafe_allow_html=True)

# Sidebar pour la navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/russian-federation.png", width=80)
    st.title("Navigation")
    
    # Boutons pour le mode démo
    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        if st.button("🎮 Mode Démo"):
            st.session_state.demo_mode = True
            st.rerun()
    with col_demo2:
        if st.button("🔄 Mode Réel"):
            st.session_state.demo_mode = False
            st.cache_data.clear()
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
    
    # Configuration commune
    st.subheader("⚙️ Configuration")
    st.caption(f"🕐 Fuseau : Heure Paris (UTC+1/UTC+2)")
    
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
    
    st.caption("""
    📍 Suffixes Russie:
    - .ME: MOEX (Moscow Exchange)
    - .MM: MOEX (format alternatif)
    - Sans suffixe: ADR US
    """)
    
    # Période et intervalle
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox(
            "Période",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
            index=2
        )
    
    with col2:
        interval_map = {
            "1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes",
            "30m": "30 minutes", "1h": "1 heure", "1d": "1 jour",
            "1wk": "1 semaine", "1mo": "1 mois"
        }
        interval = st.selectbox(
            "Intervalle",
            options=list(interval_map.keys()),
            format_func=lambda x: interval_map[x],
            index=4 if period == "1d" else 6
        )
    
    # Auto-refresh
    auto_refresh = st.checkbox("Actualisation automatique", value=False)
    if auto_refresh:
        st.warning("⚠️ L'actualisation automatique peut entraîner des limitations API")
        refresh_rate = st.slider(
            "Fréquence (secondes)",
            min_value=30,
            max_value=300,
            value=60,
            step=10
        )

# Chargement des données
try:
    hist, info = load_stock_data(symbol, period, interval)
except Exception as e:
    st.error(f"Erreur lors du chargement: {e}")
    st.session_state.demo_mode = True
    hist, info = generate_demo_history(symbol, period, interval), DEMO_DATA.get(symbol, {
        'longName': f'{symbol} (Mode démo)',
        'sector': 'N/A',
        'industry': 'N/A'
    })

if hist is None or hist.empty:
    st.warning(f"⚠️ Impossible de charger les données pour {symbol}. Utilisation du mode démo.")
    st.session_state.demo_mode = True
    hist = generate_demo_history(symbol, period, interval)
    info = DEMO_DATA.get(symbol, {
        'longName': f'{symbol} (Mode démo)',
        'sector': 'N/A',
        'industry': 'N/A',
        'marketCap': 100000000000
    })

current_price = safe_get_metric(hist, 'Close')

# Vérification des alertes
triggered_alerts = check_price_alerts(current_price, symbol)
for alert in triggered_alerts:
    st.balloons()
    st.success(f"🎯 Alerte déclenchée pour {symbol} à {format_currency(current_price, symbol)}")
    
    if st.session_state.email_config['enabled']:
        subject = f"🚨 Alerte prix - {symbol}"
        body = f"""
        <h2>Alerte de prix déclenchée</h2>
        <p><b>Symbole:</b> {symbol}</p>
        <p><b>Prix actuel:</b> {format_currency(current_price, symbol)}</p>
        <p><b>Condition:</b> {alert['condition']} {format_currency(alert['price'], symbol)}</p>
        <p><b>Date:</b> {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)</p>
        """
        send_email_alert(subject, body, st.session_state.email_config['email'])
    
    if alert.get('one_time', False):
        st.session_state.price_alerts.remove(alert)

# ============================================================================
# SECTION 1: TABLEAU DE BORD
# ============================================================================
if menu == "📈 Tableau de bord":
    # Statut du marché
    market_status, market_icon = get_market_status()
    st.info(f"{market_icon} Marché Russe (MOEX): {market_status}")
    
    if hist is not None and not hist.empty:
        exchange = get_exchange(symbol)
        currency = get_currency(symbol)
        
        company_name = info.get('longName', symbol) if info else symbol
        if st.session_state.demo_mode:
            company_name += " (Mode démo)"
        
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
        
        try:
            moscow_time = hist.index[-1].tz_convert(MOSCOW_TIMEZONE)
            st.caption(f"Dernière mise à jour: {hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (heure Paris) / {moscow_time.strftime('%H:%M:%S')} MSK")
        except:
            st.caption(f"Dernière mise à jour: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)")
        
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
            title=f"{symbol} - {period} (heure Paris)",
            yaxis_title=f"Prix ({'₽' if currency=='RUB' else '$'})",
            yaxis2=dict(
                title="Volume",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            xaxis_title="Date (heure Paris)",
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
                    
                    st.write(f"**P/E :** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Dividende :** {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "**Dividende :** N/A")
                    st.write(f"**Beta :** {info.get('beta', 'N/A')}")
            else:
                st.write("Informations non disponibles")
    else:
        st.warning(f"Aucune donnée disponible pour {symbol}")

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
            
            st.caption("""
            Suffixes Russie:
            - .ME: MOEX (Moscow Exchange)
            - Sans suffixe: ADR US
            """)
            
            shares = st.number_input("Nombre d'actions", min_value=1, step=1, value=100)
            buy_price = st.number_input("Prix d'achat (₽)", min_value=0.01, step=10.0, value=280.0)
            
            if st.form_submit_button("Ajouter au portefeuille"):
                if symbol_pf and shares > 0:
                    if symbol_pf not in st.session_state.portfolio:
                        st.session_state.portfolio[symbol_pf] = []
                    
                    st.session_state.portfolio[symbol_pf].append({
                        'shares': shares,
                        'buy_price': buy_price,
                        'date': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    st.success(f"✅ {shares} actions {symbol_pf} ajoutées")
    
    with col1:
        st.markdown("### 📊 Performance du portefeuille")
        
        if st.session_state.portfolio:
            portfolio_data = []
            total_value_rub = 0
            total_cost_rub = 0
            total_value_usd = 0
            total_cost_usd = 0
            
            # Taux de change approximatif
            usd_rub_rate = 90.0  # 1 USD = 90 RUB
            
            for symbol_pf, positions in st.session_state.portfolio.items():
                try:
                    if st.session_state.demo_mode and symbol_pf in DEMO_DATA:
                        current = DEMO_DATA[symbol_pf]['current_price']
                    else:
                        ticker = yf.Ticker(symbol_pf)
                        hist = ticker.history(period='1d')
                        current = hist['Close'].iloc[-1] if not hist.empty else 0
                    
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
                            total_cost_usd += cost / usd_rub_rate
                            total_value_usd += value / usd_rub_rate
                        else:
                            total_cost_usd += cost
                            total_value_usd += value
                            total_cost_rub += cost * usd_rub_rate
                            total_value_rub += value * usd_rub_rate
                        
                        if currency == 'RUB':
                            buy_price_str = f"₽{buy_price:,.2f}"
                            current_str = f"₽{current:,.2f}"
                            value_str = f"₽{value:,.2f}"
                            profit_str = f"₽{profit:,.2f}"
                        else:
                            buy_price_str = f"${buy_price:.2f}"
                            current_str = f"${current:.2f}"
                            value_str = f"${value:,.2f}"
                            profit_str = f"${profit:,.2f}"
                        
                        portfolio_data.append({
                            'Symbole': symbol_pf,
                            'Marché': exchange,
                            'Devise': currency,
                            'Actions': shares,
                            "Prix d'achat": buy_price_str,
                            'Prix actuel': current_str,
                            'Valeur': value_str,
                            'Profit': profit_str,
                            'Profit %': f"{profit_pct:.1f}%"
                        })
                except Exception as e:
                    st.warning(f"Impossible de charger {symbol_pf}")
            
            if portfolio_data:
                total_profit_rub = total_value_rub - total_cost_rub
                total_profit_pct_rub = (total_profit_rub / total_cost_rub * 100) if total_cost_rub > 0 else 0
                
                st.markdown("#### Total en Roubles (RUB)")
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur totale", f"₽{total_value_rub:,.2f}")
                col_i2.metric("Coût total", f"₽{total_cost_rub:,.2f}")
                col_i3.metric(
                    "Profit total",
                    f"₽{total_profit_rub:,.2f}",
                    delta=f"{total_profit_pct_rub:.1f}%"
                )
                
                total_profit_usd = total_value_usd - total_cost_usd
                total_profit_pct_usd = (total_profit_usd / total_cost_usd * 100) if total_cost_usd > 0 else 0
                
                st.markdown("#### Total en Dollars (USD)")
                col_u1, col_u2, col_u3 = st.columns(3)
                col_u1.metric("Valeur totale", f"${total_value_usd:,.2f}")
                col_u2.metric("Coût total", f"${total_cost_usd:,.2f}")
                col_u3.metric("Profit total", f"${total_profit_usd:,.2f}", delta=f"{total_profit_pct_usd:.1f}%")
                
                st.caption(f"Taux de change utilisé: 1 USD = {usd_rub_rate} RUB")
                
                st.markdown("### 📋 Positions détaillées")
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                try:
                    fig_pie = px.pie(
                        names=[p['Symbole'] for p in portfolio_data],
                        values=[float(p['Valeur'].replace('₽', '').replace('$', '').replace(',', '')) for p in portfolio_data],
                        title="Répartition du portefeuille"
                    )
                    st.plotly_chart(fig_pie)
                except:
                    st.warning("Impossible de générer le graphique")
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
            else:
                st.info("Aucune donnée de performance disponible")
        else:
            st.info("Aucune position dans le portefeuille. Ajoutez des actions russes pour commencer !")

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
            exchange = get_exchange(alert_symbol)
            st.caption(f"Marché: {exchange}")
            
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
                    'created': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ Alerte créée pour {alert_symbol} à {format_currency(alert_price, alert_symbol)}")
    
    with col2:
        st.markdown("### 📋 Alertes actives")
        if st.session_state.price_alerts:
            for i, alert in enumerate(st.session_state.price_alerts):
                with st.container():
                    st.markdown(f"""
                    <div class='alert-box alert-warning'>
                        <b>{alert['symbol']}</b> - {alert['condition']} {format_currency(alert['price'], alert['symbol'])}<br>
                        <small>Créée: {alert['created']} (heure Paris) | {('Usage unique' if alert['one_time'] else 'Permanent')}</small>
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
                        f"<h2>Test réussi !</h2><p>Votre configuration email fonctionne correctement !</p><p>Heure d'envoi: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)</p>",
                        test_email
                    ):
                        st.success("Email de test envoyé !")
                    else:
                        st.error("Échec de l'envoi")
    
    with st.expander("📋 Aperçu de la configuration"):
        st.json(st.session_state.email_config)

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
            display_hist.index = display_hist.index.strftime('%Y-%m-%d %H:%M:%S (heure Paris)')
            st.dataframe(display_hist.tail(20))
            
            csv = hist.to_csv()
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("### 📈 Rapport PDF")
            st.info("Génération de rapport PDF (simulée)")
            
            st.markdown("**Statistiques:**")
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
                'last_update': datetime.now(USER_TIMEZONE).isoformat(),
                'timezone': 'Europe/Paris',
                'current_price': float(current_price) if current_price else 0,
                'statistics': {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in stats.items()},
                'data': hist.reset_index().to_dict(orient='records')
            }
            
            st.download_button(
                label="📥 Télécharger en JSON",
                data=json.dumps(json_data, indent=2, default=str),
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.warning(f"Aucune donnée à exporter pour {symbol}")

# ============================================================================
# SECTION 6: PRÉDICTIONS ML
# ============================================================================
elif menu == "🤖 Prédictions ML":
    st.subheader("🤖 Prédictions avec Machine Learning - Actions Russes")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        st.markdown("### Modèle de prédiction (Régression polynomiale)")
        
        st.info("""
        ⚠️ Facteurs influençant la bourse russe:
        - Prix du pétrole et du gaz (Brent, Urals)
        - Taux de change USD/RUB
        - Politique monétaire de la Banque Centrale de Russie (CBR)
        - Tensions géopolitiques et sanctions internationales
        - Politique budgétaire et réserves souveraines
        - Dividendes des géants énergétiques (Gazprom, Rosneft, Lukoil)
        - Inflation et taux directeur
        - Développement du secteur technologique (Yandex, TCS, Ozon)
        - Métaux précieux (Norilsk Nickel, Polymetal, Alrosa)
        """)
        
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
            title=f"Prédictions pour {symbol} - {days_to_predict} jours (heure Paris)",
            xaxis_title="Date (heure Paris)",
            yaxis_title=f"Prix ({'₽' if get_currency(symbol)=='RUB' else '$'})",
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        st.markdown("### 📋 Prédictions détaillées")
        pred_df = pd.DataFrame({
            'Date (heure Paris)': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [format_currency(p, symbol) for p in predictions],
            'Variation %': [f"{(p/current_price - 1)*100:.2f}%" for p in predictions]
        })
        st.dataframe(pred_df, use_container_width=True)
        
        st.markdown("### 📊 Performance du modèle")
        residuals = y - model.predict(X)
        mse = np.mean(residuals**2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(residuals))
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("RMSE", f"{format_currency(rmse, symbol)}")
        col_m2.metric("MAE", f"{format_currency(mae, symbol)}")
        col_m3.metric("R²", f"{model.score(X, y):.3f}")
        
        st.markdown("### 📈 Analyse des tendances")
        last_price = current_price
        last_pred = predictions[-1]
        trend = "HAUSSIÈRE 📈" if last_pred > last_price else "BAISSIÈRE 📉" if last_pred < last_price else "NEUTRE ➡️"
        
        if last_pred > last_price * 1.05:
            strength = "Forte tendance haussière 🚀"
        elif last_pred > last_price:
            strength = "Légère tendance haussière 📈"
        elif last_pred < last_price * 0.95:
            strength = "Forte tendance baissière 🔻"
        elif last_pred < last_price:
            strength = "Légère tendance baissière 📉"
        else:
            strength = "Tendance latérale ⏸️"
        
        st.info(f"**Tendance prévue:** {trend} - {strength}")
        
        with st.expander("🇷🇺 Facteurs influençant le marché russe"):
            st.markdown("""
            **Indicateurs économiques clés:**
            - **Prix du pétrole Urals/Brent**: Corrélation directe avec le marché
            - **Taux de change USD/RUB**: Volatilité importante
            - **Taux directeur CBR**: Actuellement élevé pour lutter contre l'inflation
            - **Inflation**: Objectif de 4% de la banque centrale
            - **PIB**: Impact des sanctions et de la réorientation vers l'Est
            - **Balance commerciale**: Excédent grâce aux exportations d'énergie
            
            **Secteurs importants:**
            - **Pétrole & Gaz**: Gazprom, Lukoil, Rosneft, Novatek, Tatneft, Surgutneftegas
            - **Métaux & Mines**: Norilsk Nickel, Alrosa, Rusal, Severstal, NLMK, MMK
            - **Finance**: Sberbank, VTB, TCS Group (Tinkoff), Moscow Exchange
            - **Technologie/Internet**: Yandex, Ozon, VK (Mail.ru), Qiwi
            - **Télécoms**: MTS, Rostelecom, MegaFon
            - **Retail**: Magnit, X5 Retail Group, Detsky Mir
            - **Transport**: Aeroflot, FESCO, Globaltrans
            - **Chimie**: PhosAgro, Acron, Uralkali
            
            **Politique monétaire CBR:**
            - Taux directeur actuel élevé (15%+)
            - Interventions sur le Forex
            - Contrôle des capitaux
            - Politique de change flottant avec interventions
            
            **Sanctions internationales:**
            - Impact sur l'accès aux marchés de capitaux
            - Restrictions sur les technologies
            - Gestion des avoirs gelés
            - Réorientation vers les marchés asiatiques (Chine, Inde)
            
            **Calendrier économique:**
            - Réunion CBR sur les taux : 8 fois par an
            - Résultats entreprises : Avril-Mai, Août-Septembre, Novembre-Décembre
            - Budget fédéral : Décembre
            - Données d'inflation : Mensuel
            """)
        
    else:
        st.warning(f"Pas assez de données historiques pour {symbol} (minimum 30 points)")

# ============================================================================
# SECTION 7: INDICES MOEX & RTS
# ============================================================================
elif menu == "🇷🇺 Indices MOEX & RTS":
    st.subheader("🇷🇺 Indices boursiers russes")
    
    russian_indices = {
        'IMOEX.ME': 'MOEX Russia Index (Roubles)',
        'RTSI.ME': 'RTS Index (Dollars)',
        'RGBI.ME': 'Russian Government Bond Index',
        'MICEX10.ME': 'MICEX 10 Index',
        'MICEXFNL.ME': 'MICEX Financials Index',
        'MICEXO&G.ME': 'MICEX Oil & Gas Index',
        'MICEXMM.ME': 'MICEX Metals & Mining Index',
        'MICEXTLC.ME': 'MICEX Telecoms Index',
        'MICEXPWR.ME': 'MICEX Power Index',
        'MICEXCGS.ME': 'MICEX Consumer Goods Index',
        'SBER.ME': 'Sberbank (composant principal)',
        'GAZP.ME': 'Gazprom (composant principal)',
        'LKOH.ME': 'Lukoil (composant principal)',
        'YNDX.ME': 'Yandex (composant principal)'
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### 🇷🇺 Sélection d'indice")
        selected_index = st.selectbox(
            "Choisir un indice",
            options=list(russian_indices.keys()),
            format_func=lambda x: f"{russian_indices[x]} ({x})",
            index=0
        )
        
        st.markdown("### 📊 Performance des indices")
        perf_period = st.selectbox(
            "Période de comparaison",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"],
            index=0
        )
    
    with col1:
        try:
            if st.session_state.demo_mode:
                # Données simulées pour la démo
                st.markdown(f"### {russian_indices[selected_index]} (Mode démo)")
                
                current_index = random.uniform(2000, 3500) if 'RTS' in selected_index else random.uniform(3000, 4500)
                prev_index = current_index * random.uniform(0.97, 1.03)
                index_change = current_index - prev_index
                index_change_pct = (index_change / prev_index * 100)
                
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur", f"{current_index:,.2f}")
                col_i2.metric("Variation", f"{index_change:,.2f}")
                col_i3.metric("Variation %", f"{index_change_pct:.2f}%", delta=f"{index_change_pct:.2f}%")
                
                # Générer un graphique simulé
                dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
                values = current_index * (1 + np.random.normal(0, 0.01, 100).cumsum() / 100)
                
                fig_index = go.Figure()
                fig_index.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines',
                    name=russian_indices[selected_index],
                    line=dict(color='#D52B1E', width=2)
                ))
                
                fig_index.update_layout(
                    title=f"Évolution simulée - {perf_period} (heure Paris)",
                    xaxis_title="Date (heure Paris)",
                    yaxis_title="Points",
                    height=500,
                    hovermode='x unified',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig_index, use_container_width=True)
                
            else:
                index_ticker = yf.Ticker(selected_index)
                index_hist = index_ticker.history(period=perf_period)
                
                if not index_hist.empty:
                    if index_hist.index.tz is None:
                        index_hist.index = index_hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
                    else:
                        index_hist.index = index_hist.index.tz_convert(USER_TIMEZONE)
                    
                    current_index = index_hist['Close'].iloc[-1]
                    prev_index = index_hist['Close'].iloc[-2] if len(index_hist) > 1 else current_index
                    index_change = current_index - prev_index
                    index_change_pct = (index_change / prev_index * 100) if prev_index != 0 else 0
                    
                    st.markdown(f"### {russian_indices[selected_index]}")
                    
                    col_i1, col_i2, col_i3 = st.columns(3)
                    col_i1.metric("Valeur", f"{current_index:,.2f}")
                    col_i2.metric("Variation", f"{index_change:,.2f}")
                    col_i3.metric("Variation %", f"{index_change_pct:.2f}%", delta=f"{index_change_pct:.2f}%")
                    
                    moscow_time = index_hist.index[-1].tz_convert(MOSCOW_TIMEZONE)
                    st.caption(f"Dernière mise à jour: {index_hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (heure Paris) / {moscow_time.strftime('%H:%M:%S')} MSK")
                    
                    fig_index = go.Figure()
                    fig_index.add_trace(go.Scatter(
                        x=index_hist.index,
                        y=index_hist['Close'],
                        mode='lines',
                        name=russian_indices[selected_index],
                        line=dict(color='#D52B1E', width=2)
                    ))
                    
                    if len(index_hist) > 20:
                        ma_20 = index_hist['Close'].rolling(window=20).mean()
                        ma_50 = index_hist['Close'].rolling(window=50).mean()
                        
                        fig_index.add_trace(go.Scatter(
                            x=index_hist.index,
                            y=ma_20,
                            mode='lines',
                            name='MA 20',
                            line=dict(color='orange', width=1, dash='dash')
                        ))
                        
                        fig_index.add_trace(go.Scatter(
                            x=index_hist.index,
                            y=ma_50,
                            mode='lines',
                            name='MA 50',
                            line=dict(color='purple', width=1, dash='dash')
                        ))
                    
                    fig_index.update_layout(
                        title=f"Évolution - {perf_period} (heure Paris)",
                        xaxis_title="Date (heure Paris)",
                        yaxis_title="Points",
                        height=500,
                        hovermode='x unified',
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig_index, use_container_width=True)
                    
                    st.markdown("### 📈 Statistiques")
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    col_s1.metric("Plus haut", f"{index_hist['High'].max():,.2f}")
                    col_s2.metric("Plus bas", f"{index_hist['Low'].min():,.2f}")
                    col_s3.metric("Moyenne", f"{index_hist['Close'].mean():,.2f}")
                    col_s4.metric("Volatilité", f"{index_hist['Close'].pct_change().std()*100:.2f}%")
                else:
                    st.warning("Données non disponibles")
        except Exception as e:
            st.error(f"Erreur lors du chargement: {e}")
    
    # Tableau de comparaison des indices
    st.markdown("### 📊 Comparaison des indices")
    
    comparison_data = []
    for idx, name in list(russian_indices.items())[:10]:
        try:
            if st.session_state.demo_mode:
                current = random.uniform(1000, 5000)
                prev = current * random.uniform(0.95, 1.05)
                change_pct = ((current - prev) / prev * 100)
                
                comparison_data.append({
                    'Indice': name,
                    'Symbole': idx,
                    'Valeur': f"{current:,.2f}",
                    'Variation 5j': f"{change_pct:.2f}%",
                    'Direction': '📈' if change_pct > 0 else '📉' if change_pct < 0 else '➡️'
                })
            else:
                ticker = yf.Ticker(idx)
                hist = ticker.history(period="5d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[0]
                    change_pct = ((current - prev) / prev * 100) if prev != 0 else 0
                    
                    comparison_data.append({
                        'Indice': name,
                        'Symbole': idx,
                        'Valeur': f"{current:,.2f}",
                        'Variation 5j': f"{change_pct:.2f}%",
                        'Direction': '📈' if change_pct > 0 else '📉' if change_pct < 0 else '➡️'
                    })
        except:
            pass
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)
    
    with st.expander("ℹ️ À propos des indices russes"):
        st.markdown("""
        **MOEX Russia Index (IMOEX):**
        - Principal indice de la Bourse de Moscou
        - Libellé en roubles russes (RUB)
        - Toutes les actions les plus liquides de la cote
        - Pondéré par capitalisation flottante
        - Révisé trimestriellement
        
        **RTS Index (RTSI):**
        - Même composition que le MOEX mais libellé en dollars USD
        - Baromètre pour les investisseurs étrangers
        - Sensible aux variations du taux de change USD/RUB
        - Historique depuis 1995
        
        **Indices sectoriels MOEX:**
        - **MICEXO&G**: Pétrole et Gaz (Gazprom, Lukoil, Rosneft, Novatek)
        - **MICEXMM**: Métaux et Mines (Norilsk Nickel, Alrosa, Severstal)
        - **MICEXFNL**: Finance (Sberbank, TCS, VTB)
        - **MICEXTLC**: Télécoms (MTS, Rostelecom)
        - **MICEXPWR**: Énergie électrique (RusHydro, Inter RAO)
        - **MICEXCGS**: Biens de consommation (Magnit, X5, Detsky Mir)
        
        **Principaux secteurs représentés:**
        - **Pétrole & Gaz**: 45-50% de l'indice
        - **Métaux & Mines**: 15-20%
        - **Finance**: 10-15%
        - **Technologie**: 5-8%
        - **Télécoms**: 3-5%
        - **Retail**: 3-5%
        
        **Horaires de trading (MSK):**
        - Session principale: 10:00 - 18:45
        - Pré-ouverture: 09:45 - 10:00
        - Post-clôture (dérivés): 19:05 - 23:50
        - Week-end: Fermé
        """)

# ============================================================================
# WATCHLIST ET DERNIÈRE MISE À JOUR
# ============================================================================
st.markdown("---")
col_w1, col_w2 = st.columns([3, 1])

with col_w1:
    st.subheader("📋 Watchlist Russie")
    
    moex_stocks = [s for s in st.session_state.watchlist if s.endswith('.ME')]
    us_stocks = [s for s in st.session_state.watchlist if not s.endswith('.ME')]
    
    tabs = st.tabs(["MOEX", "ADR US"])
    
    with tabs[0]:
        if moex_stocks:
            cols_per_row = 4
            for i in range(0, len(moex_stocks), cols_per_row):
                cols = st.columns(min(cols_per_row, len(moex_stocks) - i))
                for j, sym in enumerate(moex_stocks[i:i+cols_per_row]):
                    with cols[j]:
                        try:
                            if st.session_state.demo_mode and sym in DEMO_DATA:
                                price = DEMO_DATA[sym]['current_price']
                                prev_close = DEMO_DATA[sym]['previous_close']
                                change = ((price - prev_close) / prev_close * 100)
                                st.metric(sym, f"₽{price:,.2f}", delta=f"{change:.1f}%")
                            else:
                                ticker = yf.Ticker(sym)
                                hist = ticker.history(period='1d')
                                if not hist.empty:
                                    price = hist['Close'].iloc[-1]
                                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else price
                                    change = ((price - prev_close) / prev_close * 100)
                                    st.metric(sym, f"₽{price:,.2f}", delta=f"{change:.1f}%")
                                else:
                                    st.metric(sym, "N/A")
                        except:
                            price = random.uniform(100, 10000)
                            st.metric(sym, f"₽{price:,.2f}*", delta="0%")
        else:
            st.info("Aucune action MOEX")
    
    with tabs[1]:
        if us_stocks:
            cols_per_row = 4
            for i in range(0, len(us_stocks), cols_per_row):
                cols = st.columns(min(cols_per_row, len(us_stocks) - i))
                for j, sym in enumerate(us_stocks[i:i+cols_per_row]):
                    with cols[j]:
                        try:
                            if st.session_state.demo_mode:
                                price = random.uniform(10, 100)
                                st.metric(sym, f"${price:.2f}", delta=f"{random.uniform(-3, 3):.1f}%")
                            else:
                                ticker = yf.Ticker(sym)
                                hist = ticker.history(period='1d')
                                if not hist.empty:
                                    price = hist['Close'].iloc[-1]
                                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else price
                                    change = ((price - prev_close) / prev_close * 100)
                                    st.metric(sym, f"${price:.2f}", delta=f"{change:.1f}%")
                                else:
                                    st.metric(sym, "N/A")
                        except:
                            price = random.uniform(10, 100)
                            st.metric(sym, f"${price:.2f}*", delta="0%")
        else:
            st.info("Aucune action US")

with col_w2:
    paris_time = datetime.now(USER_TIMEZONE)
    moscow_time = datetime.now(MOSCOW_TIMEZONE)
    ny_time = datetime.now(US_TIMEZONE)
    
    st.caption(f"🇫🇷 Paris: {paris_time.strftime('%H:%M:%S')}")
    st.caption(f"🇷🇺 MSK: {moscow_time.strftime('%H:%M:%S')}")
    st.caption(f"🇺🇸 NY: {ny_time.strftime('%H:%M:%S')}")
    
    market_status, market_icon = get_market_status()
    st.caption(f"{market_icon} Marché Russe: {market_status}")
    
    if st.session_state.demo_mode:
        st.caption("🎮 Mode démonstration")
    else:
        st.caption(f"Dernière MAJ: {paris_time.strftime('%H:%M:%S')}")
    
    if auto_refresh and hist is not None and not hist.empty:
        time.sleep(refresh_rate)
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🇷🇺 Tracker Bourse Russie - MOEX & RTS | Données fournies par yfinance | "
    "⚠️ Données avec délai possible - Sujettes à restrictions | 🕐 Heure Paris (UTC+1/UTC+2) | 🇷🇺 MSK (UTC+3)"
    "</p>",
    unsafe_allow_html=True
)
