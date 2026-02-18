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
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION SPÉCIFIQUE RUSSIE
# ============================================================================

# Configuration de la page
st.set_page_config(
    page_title="Tracker Bourse Russie - Moscow Exchange (MOEX)",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des fuseaux horaires
MOSCOW_TZ = pytz.timezone('Europe/Moscow')  # UTC+3 (pas d'heure d'été)
NY_TZ = pytz.timezone('America/New_York')
LONDON_TZ = pytz.timezone('Europe/London')

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0033A0; /* Bleu russe */
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Montserrat', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .stock-price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0033A0;
        text-align: center;
    }
    .stock-change-positive {
        color: #00cc96;
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
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .russia-market-note {
        background: linear-gradient(135deg, #0033A0 0%, #FFFFFF 50%, #D52B1E 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .rts-badge {
        background-color: #D52B1E;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .sanctions-warning {
        background-color: #ffebee;
        border-left: 4px solid #c62828;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
        color: #b71c1c;
        font-weight: bold;
    }
    .symbol-update {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DONNÉES SPÉCIFIQUES À LA RUSSIE
# ============================================================================

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# WATCHLIST RUSSE (MOEX) - Symboles au format international
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = [
        # Principales sociétés russes (format yfinance)
        'SBER.ME',      # Sberbank (MOEX)
        'GAZP.ME',      # Gazprom
        'LKOH.ME',      # Lukoil
        'ROSN.ME',      # Rosneft
        'NVTK.ME',      # Novatek
        'GMKN.ME',      # Norilsk Nickel
        'SNGS.ME',      # Surgutneftegas
        'TATN.ME',      # Tatneft
        'VTBR.ME',      # VTB Bank
        'PLZL.ME',      # Polyus Gold
        'ALRS.ME',      # Alrosa
        'MOEX.ME',      # Moscow Exchange
        'MAGN.ME',      # Magnitogorsk Iron & Steel
        'NLMK.ME',      # Novolipetsk Steel
        'CHMF.ME',      # Severstal
        'AFKS.ME',      # Sistema
        'MTSS.ME',      # MTS (Mobile TeleSystems)
        'RSTI.ME',      # Rosseti
        'PHOR.ME',      # PhosAgro
        'URKA.ME',      # Uralkali
        'YNDX.ME',      # Yandex
        'TCSG.ME',      # TCS Group (Tinkoff)
        'QIWI.ME',      # Qiwi
        'FIVE.ME',      # X5 Retail Group
        'MGNT.ME',      # Magnit
        'DSKY.ME',      # Detsky Mir
        'RUAL.ME',      # Rusal
        'ENPG.ME',      # En+ Group
        'POLY.ME',      # Polymetal
        'RTKM.ME',      # Rostelecom
        'TRNFP.ME',     # Transneft (pref)
        'BANE.ME',      # Bashneft
        'MFON.ME',      # MegaFon
        'MSNG.ME',      # Mosenergo
        'IRAO.ME',      # Inter RAO
        'FEES.ME',      # FGC UES
        'HYDR.ME',      # RusHydro
        'OGKB.ME',      # OGK-2
        'TGKA.ME',      # TGC-1
        'LSNGP.ME',     # LSR Group
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

# Indices russes
RUSSIAN_INDICES = {
    'IMOEX.ME': 'MOEX Russia Index (RUB)',
    'RTS.ME': 'RTS Index (USD) [citation:1][citation:7]',
    'RTSI.ME': 'RTS Index (USD) - alternatif',
    'RTSI$': 'RTS Index (USD) - ancien format [citation:1]',
    'RTS.ME': 'Russian Trading System',
    'IMOEX': 'MOEX Russia Index',
    'RGBITR': 'Russia Government Bonds',
}

# Correspondance des anciens symboles (avant changement de ticker)
SYMBOL_MAPPING = {
    'SBER.ME': 'SBER.ME',      # inchangé
    'GAZP.ME': 'GAZP.ME',       # inchangé
    'TOTF.PA': 'TTE.PA',        # hors Russie, mais gardé pour info
    'RTSI$': 'RTS.ME',          # ancien format RTS
    'MICEX': 'IMOEX.ME',         # ancien nom de l'indice
}

# Jours fériés russes (approximatifs)
RUSSIAN_HOLIDAYS_2024 = [
    '2024-01-01',  # New Year
    '2024-01-02',  # New Year
    '2024-01-03',  # New Year
    '2024-01-04',  # New Year
    '2024-01-05',  # New Year
    '2024-01-06',  # New Year
    '2024-01-07',  # Orthodox Christmas
    '2024-01-08',  # New Year (day off)
    '2024-02-23',  # Defender of the Fatherland Day
    '2024-03-08',  # International Women's Day
    '2024-05-01',  # Spring and Labour Day
    '2024-05-09',  # Victory Day
    '2024-06-12',  # Russia Day
    '2024-11-04',  # Unity Day
]

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def validate_and_fix_symbol(symbol):
    """Valide et corrige automatiquement les symboles obsolètes"""
    if symbol in SYMBOL_MAPPING:
        return SYMBOL_MAPPING[symbol], f"🔄 {symbol} → {SYMBOL_MAPPING[symbol]}"
    return symbol, None

def get_exchange(symbol):
    """Détermine l'échange pour un symbole"""
    if symbol.endswith('.ME'):
        return 'Moscow Exchange (MOEX) [citation:2]'
    elif symbol.endswith('.L'):
        return 'London Stock Exchange'
    elif symbol.endswith('.DE'):
        return 'Deutsche Börse'
    elif symbol.endswith('.PA'):
        return 'Euronext Paris'
    else:
        return 'International'

def get_currency(symbol):
    """Détermine la devise pour un symbole"""
    if symbol in ['RTS.ME', 'RTSI$']:
        return 'USD'
    elif symbol.endswith('.ME'):
        return 'RUB'
    elif symbol.endswith('.L'):
        return 'GBP'
    elif symbol.endswith('.DE') or symbol.endswith('.PA'):
        return 'EUR'
    else:
        return 'USD'

def format_currency(value, symbol):
    """Formate la monnaie selon le symbole"""
    currency = get_currency(symbol)
    if currency == 'RUB':
        # Format roubles russes
        if value >= 1e9:
            return f"₽{value/1e9:.2f} млрд"
        elif value >= 1e6:
            return f"₽{value/1e6:.2f} млн"
        else:
            return f"₽{value:,.2f}"
    elif currency == 'USD':
        return f"${value:,.2f}"
    elif currency == 'EUR':
        return f"€{value:,.2f}"
    elif currency == 'GBP':
        return f"£{value:,.2f}"
    else:
        return f"{value:,.2f}"

def get_market_status():
    """Détermine le statut des marchés russes"""
    moscow_now = datetime.now(MOSCOW_TZ)
    moscow_hour = moscow_now.hour
    moscow_minute = moscow_now.minute
    moscow_weekday = moscow_now.weekday()
    moscow_date = moscow_now.strftime('%Y-%m-%d')
    
    # Weekend
    if moscow_weekday >= 5:  # samedi ou dimanche
        return "Fermé (weekend)", "🔴"
    
    # Jours fériés
    if moscow_date in RUSSIAN_HOLIDAYS_2024:
        return "Fermé (jour férié)", "🔴"
    
    # Horaires MOEX: 10:00 - 18:45 (heure de Moscou)
    if 10 <= moscow_hour < 18:
        return "Ouvert", "🟢"
    elif moscow_hour == 18 and moscow_minute <= 45:
        return "Ouvert", "🟢"
    elif 9 <= moscow_hour < 10:
        return "Pré-ouverture", "🟡"
    else:
        return "Fermé", "🔴"

@st.cache_data(ttl=300)
def load_stock_data(symbol, period, interval):
    """Charge les données boursières avec correction automatique"""
    try:
        # Vérifier et corriger le symbole si nécessaire
        original_symbol = symbol
        fixed_symbol, message = validate_and_fix_symbol(symbol)
        
        if fixed_symbol != original_symbol and message:
            st.info(message)
            symbol = fixed_symbol
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        info = ticker.info
        
        # Convertir l'index en heure de Moscou
        if not hist.empty:
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(MOSCOW_TZ)
            else:
                hist.index = hist.index.tz_convert(MOSCOW_TZ)
        
        return hist, info
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None, None

def safe_get_metric(hist, metric, index=-1):
    """Récupère une métrique en toute sécurité"""
    try:
        if hist is not None and not hist.empty and len(hist) > abs(index):
            return hist[metric].iloc[index]
        return 0
    except:
        return 0

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

# ============================================================================
# TITRE PRINCIPAL ET BANNIÈRES
# ============================================================================

st.markdown("<h1 class='main-header'>🇷🇺 Tracker Bourse Russie - Moscow Exchange (MOEX)</h1>", unsafe_allow_html=True)

# AVERTISSEMENT SUR LES SANCTIONS
st.markdown("""
<div class='sanctions-warning'>
    ⚠️ <b>ATTENTION - Sanctions internationales</b> ⚠️<br><br>
    Depuis 2022, l'accès aux données de la bourse russe est <b>fortement limité</b> pour les investisseurs internationaux [citation:3][citation:6][citation:8].<br>
    - La plupart des API financières (yfinance, Bloomberg, Reuters) ne fournissent plus de données en temps réel<br>
    - Les transactions sur titres russes sont <b>suspendues</b> pour les investisseurs occidentaux [citation:3][citation:8]<br>
    - Les données disponibles peuvent être <b>obsolètes ou incomplètes</b><br>
    - Le Fonds monétaire norvégien est toujours bloqué avec des actions russes depuis 2022 [citation:3]<br><br>
    <b>Cette application est fournie à titre informatif uniquement.</b>
</div>
""", unsafe_allow_html=True)

# Bannière de fuseau horaire
current_time_moscow = datetime.now(MOSCOW_TZ)
current_time_ny = datetime.now(NY_TZ)
current_time_london = datetime.now(LONDON_TZ)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇷🇺 Moscou : {current_time_moscow.strftime('%H:%M:%S')} (UTC+3, pas d'heure d'été)<br>
    🇬🇧 Londres : {current_time_london.strftime('%H:%M:%S')}<br>
    🇺🇸 New York : {current_time_ny.strftime('%H:%M:%S')}<br>
    📍 Toutes les heures sont affichées en heure de Moscou (UTC+3)
</div>
""", unsafe_allow_html=True)

# Note sur les marchés russes
st.markdown("""
<div class='russia-market-note'>
    <b>🇷🇺 Moscow Exchange (MOEX) :</b> 
    <span class='rts-badge'>RTS Index</span><br>
    - Actions russes: suffixe .ME (ex: SBER.ME, GAZP.ME, LKOH.ME)<br>
    - Indices principaux: MOEX Russia Index (RUB) et RTS Index (USD) [citation:1][citation:7]<br>
    - Horaires trading: Lundi-Vendredi 10:00 - 18:45 (heure de Moscou)<br>
    - Composition: Environ 50 valeurs les plus liquides [citation:1][citation:2]<br>
    - Devise: Rouble russe (RUB) pour la plupart des actions [citation:7]
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - NAVIGATION
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/moscow.png", width=80)
    st.title("Navigation")
    
    menu = st.radio(
        "Choisir une section",
        ["📈 Tableau de bord", 
         "💰 Portefeuille virtuel", 
         "🔔 Alertes de prix",
         "📧 Notifications email",
         "📤 Export des données",
         "🤖 Prédictions ML",
         "🇷🇺 Indices russes"]
    )
    
    st.markdown("---")
    
    # Configuration commune
    st.subheader("⚙️ Configuration")
    st.caption(f"🕐 Heure actuelle: {current_time_moscow.strftime('%H:%M:%S')} (Moscou)")
    
    # Créer une liste de symboles avec noms lisibles
    symbol_display = {
        'SBER.ME': 'Sberbank',
        'GAZP.ME': 'Gazprom',
        'LKOH.ME': 'Lukoil',
        'ROSN.ME': 'Rosneft',
        'NVTK.ME': 'Novatek',
        'GMKN.ME': 'Norilsk Nickel',
        'SNGS.ME': 'Surgutneftegas',
        'TATN.ME': 'Tatneft',
        'VTBR.ME': 'VTB Bank',
        'PLZL.ME': 'Polyus Gold',
        'ALRS.ME': 'Alrosa',
        'MOEX.ME': 'Moscow Exchange',
    }
    
    # Options pour le selectbox avec noms lisibles
    options_with_names = [f"{sym} - {symbol_display.get(sym, sym.replace('.ME', ''))}" for sym in st.session_state.watchlist]
    options_with_names.append("Autre...")
    
    selected_option = st.selectbox(
        "Symbole principal",
        options=options_with_names,
        index=0
    )
    
    # Extraire le symbole de l'option sélectionnée
    if selected_option == "Autre...":
        symbol_input = st.text_input("Entrer un symbole", value="SBER.ME").upper()
        
        # Vérifier et corriger automatiquement
        fixed_symbol, message = validate_and_fix_symbol(symbol_input)
        if message:
            st.info(message)
            symbol = fixed_symbol
        else:
            symbol = symbol_input
    else:
        symbol = selected_option.split(" - ")[0]
    
    # Aide sur les symboles
    with st.expander("📌 Symboles MOEX"):
        st.markdown("""
        **Format des symboles:**
        - `SBER.ME` - Sberbank
        - `GAZP.ME` - Gazprom  
        - `LKOH.ME` - Lukoil
        - `YNDX.ME` - Yandex
        - `GMKN.ME` - Norilsk Nickel
        
        **Indices:**
        - `IMOEX.ME` - MOEX Russia (RUB)
        - `RTS.ME` - RTS Index (USD)
        """)
    
    # Note sur les suffixes
    st.caption("""
    📍 Suffixes MOEX:
    - .ME: Moscow Exchange
    - .L: London (DRs)
    - .DE: Frankfurt
    """)
    
    # Période et intervalle
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox(
            "Période",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
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
        refresh_rate = st.slider(
            "Fréquence (secondes)",
            min_value=5,
            max_value=60,
            value=30,
            step=5
        )

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

hist, info = load_stock_data(symbol, period, interval)

# Vérification si les données sont disponibles
if hist is None or hist.empty:
    st.warning(f"⚠️ Impossible de charger les données pour {symbol}.")
    st.info("💡 Les données pour les actions russes peuvent ne pas être disponibles via les API internationales en raison des sanctions. Essayez plutôt les indices ou les ADRs sur d'autres places.")
    current_price = 0
else:
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
    st.info(f"{market_icon} Marché Moscow Exchange: {market_status}")
    
    if hist is not None and not hist.empty:
        # Métriques principales
        exchange = get_exchange(symbol)
        currency = get_currency(symbol)
        
        # Nom de l'entreprise si disponible
        company_name = info.get('longName', symbol) if info else symbol
        st.subheader(f"📊 {company_name} ({symbol}) - {exchange}")
        
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
            if volume > 1e9:
                volume_formatted = f"{volume/1e9:.2f}B"
            elif volume > 1e6:
                volume_formatted = f"{volume/1e6:.2f}M"
            elif volume > 1e3:
                volume_formatted = f"{volume/1e3:.2f}K"
            else:
                volume_formatted = f"{volume:.0f}"
            st.metric("Volume", volume_formatted)
        
        st.caption(f"Dernière mise à jour: {hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (heure Moscou)")
        
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
                increasing_line_color='#00cc96',
                decreasing_line_color='#ef553b'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='Prix',
                line=dict(color='#0033A0', width=2)
            ))
        
        # Moyennes mobiles
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
        
        # Volume
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='lightgray', opacity=0.3)
        ))
        
        fig.update_layout(
            title=f"{symbol} - {period} (heure Moscou)",
            yaxis_title=f"Prix ({currency})",
            yaxis2=dict(
                title="Volume",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            xaxis_title="Date (heure Moscou)",
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
                        st.write(f"**Capitalisation :** {format_currency(market_cap, symbol)}")
                    else:
                        st.write("**Capitalisation :** N/A")
                    
                    st.write(f"**P/E :** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Dividende :** {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "**Dividende :** N/A")
                    st.write(f"**Beta :** {info.get('beta', 'N/A')}")
                    
                    # Information sur les sanctions
                    st.markdown("---")
                    st.markdown("**⚠️ Statut sanctions:**")
                    st.markdown("Vérifier sur [GOV.UK Russia sanctions list](https://www.gov.uk/guidance/russia-list-of-designations-and-sanctions-notices) [citation:10]")
            else:
                st.write("Informations non disponibles")
    else:
        st.warning(f"Aucune donnée disponible pour {symbol}")

# ============================================================================
# SECTION 2: PORTEFEUILLE VIRTUEL
# ============================================================================

elif menu == "💰 Portefeuille virtuel":
    st.subheader("💰 Gestion de portefeuille virtuel - Actions Russes")
    
    # Avertissement spécifique
    st.warning("⚠️ Les investissements en actions russes sont actuellement soumis à des restrictions sévères pour les investisseurs internationaux [citation:3][citation:6]. Ce portefeuille est purement virtuel et à titre éducatif.")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.text_input("Symbole", value="SBER.ME").upper()
            
            # Vérifier et corriger automatiquement
            fixed_symbol, message = validate_and_fix_symbol(symbol_pf)
            if message:
                st.info(message)
                symbol_pf = fixed_symbol
            
            # Aide sur les suffixes
            st.caption("""
            Suffixes MOEX:
            - .ME: Moscow Exchange
            - .L: London (ADRs)
            """)
            
            shares = st.number_input("Nombre d'actions", min_value=0.01, step=0.01, value=1.0)
            buy_price = st.number_input("Prix d'achat", min_value=0.01, step=0.01, value=100.0)
            currency_pf = get_currency(symbol_pf)
            st.caption(f"Devise: {currency_pf}")
            
            if st.form_submit_button("Ajouter au portefeuille"):
                if symbol_pf and shares > 0:
                    if symbol_pf not in st.session_state.portfolio:
                        st.session_state.portfolio[symbol_pf] = []
                    
                    st.session_state.portfolio[symbol_pf].append({
                        'shares': shares,
                        'buy_price': buy_price,
                        'date': datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d %H:%M:%S')
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
                    ticker = yf.Ticker(symbol_pf)
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                    else:
                        current = 0
                    
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
                            'Devise': currency,
                            'Actions': shares,
                            "Prix d'achat": f"{buy_price:.2f}",
                            'Prix actuel': f"{current:.2f}" if current > 0 else "N/A",
                            'Valeur': f"{value:.2f}",
                            'Profit': f"{profit:.2f}",
                            'Profit %': f"{profit_pct:.1f}%"
                        })
                except Exception as e:
                    st.warning(f"Impossible de charger {symbol_pf}")
            
            if portfolio_data:
                # Métriques globales
                total_profit_rub = total_value_rub - total_cost_rub
                total_profit_pct_rub = (total_profit_rub / total_cost_rub * 100) if total_cost_rub > 0 else 0
                
                st.markdown("#### Total en Roubles")
                col_e1, col_e2, col_e3 = st.columns(3)
                col_e1.metric("Valeur totale", format_currency(total_value_rub, 'RUB.ME'))
                col_e2.metric("Coût total", format_currency(total_cost_rub, 'RUB.ME'))
                col_e3.metric(
                    "Profit total",
                    format_currency(total_profit_rub, 'RUB.ME'),
                    delta=f"{total_profit_pct_rub:.1f}%"
                )
                
                # Tableau des positions
                st.markdown("### 📋 Positions détaillées")
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                # Bouton pour vider le portefeuille
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
            else:
                st.info("Aucune donnée de performance disponible")
        else:
            st.info("Aucune position dans le portefeuille")

# ============================================================================
# SECTION 7: INDICES RUSSES
# ============================================================================

elif menu == "🇷🇺 Indices russes":
    st.subheader("🇷🇺 Indices boursiers russes")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### 🇷🇺 Sélection d'indice")
        selected_index = st.selectbox(
            "Choisir un indice",
            options=list(RUSSIAN_INDICES.keys()),
            format_func=lambda x: f"{RUSSIAN_INDICES[x]} ({x})",
            index=0
        )
        
        st.markdown("### 📊 Performance")
        
        # Période de comparaison
        perf_period = st.selectbox(
            "Période",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            index=0
        )
    
    with col1:
        try:
            index_ticker = yf.Ticker(selected_index)
            index_hist = index_ticker.history(period=perf_period)
            
            if not index_hist.empty:
                # Convertir en heure Moscou
                if index_hist.index.tz is None:
                    index_hist.index = index_hist.index.tz_localize('UTC').tz_convert(MOSCOW_TZ)
                else:
                    index_hist.index = index_hist.index.tz_convert(MOSCOW_TZ)
                
                current_index = index_hist['Close'].iloc[-1]
                prev_index = index_hist['Close'].iloc[-2] if len(index_hist) > 1 else current_index
                index_change = current_index - prev_index
                index_change_pct = (index_change / prev_index * 100) if prev_index != 0 else 0
                
                st.markdown(f"### {RUSSIAN_INDICES[selected_index]}")
                
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur", f"{current_index:.2f}")
                col_i2.metric("Variation", f"{index_change:.2f}")
                col_i3.metric("Variation %", f"{index_change_pct:.2f}%")
                
                st.caption(f"Dernière mise à jour: {index_hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')} (heure Moscou)")
                
                # Graphique
                fig_index = go.Figure()
                fig_index.add_trace(go.Scatter(
                    x=index_hist.index,
                    y=index_hist['Close'],
                    mode='lines',
                    name=RUSSIAN_INDICES[selected_index],
                    line=dict(color='#0033A0', width=2)
                ))
                
                fig_index.update_layout(
                    title=f"Évolution - {perf_period}",
                    xaxis_title="Date (heure Moscou)",
                    yaxis_title="Points",
                    height=500,
                    template='plotly_white'
                )
                
                st.plotly_chart(fig_index, use_container_width=True)
                
        except Exception as e:
            st.error(f"Erreur lors du chargement de l'indice: {str(e)}")
    
    # Notes sur les indices russes
    with st.expander("ℹ️ À propos des indices russes"):
        st.markdown("""
        **Principaux indices:**
        
        - **MOEX Russia Index** : Indice de référence en roubles, environ 50 valeurs [citation:2][citation:7]
        - **RTS Index** : Même composition que MOEX, mais calculé en dollars USD [citation:1][citation:7]
        
        **Composition (principales valeurs):** [citation:2][citation:5]
        - Sberbank (SBER)
        - Gazprom (GAZP)
        - Lukoil (LKOH)
        - Norilsk Nickel (GMKN)
        - Novatek (NVTK)
        
        **Horaires de trading (heure Moscou):**
        - Session principale: 10:00 - 18:45
        - Pas d'heure d'été (UTC+3 constant)
        
        **⚠️ Situation actuelle:** [citation:3][citation:8]
        - Accès limité pour les investisseurs étrangers
        - Sanctions sur de nombreuses sociétés
        - Volatilité extrême
        """)

# ============================================================================
# WATCHLIST
# ============================================================================

st.markdown("---")
col_w1, col_w2 = st.columns([3, 1])

with col_w1:
    st.subheader("📋 Watchlist Russie - MOEX")
    
    # Afficher en grille
    cols_per_row = 4
    for i in range(0, len(st.session_state.watchlist), cols_per_row):
        cols = st.columns(min(cols_per_row, len(st.session_state.watchlist) - i))
        for j, sym in enumerate(st.session_state.watchlist[i:i+cols_per_row]):
            with cols[j]:
                try:
                    ticker = yf.Ticker(sym)
                    hist = ticker.history(period='2d')
                    if not hist.empty and len(hist) >= 2:
                        price = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[-2]
                        change = price - prev_close
                        change_pct = (change / prev_close * 100)
                        
                        # Nom simplifié
                        display_name = sym.replace('.ME', '')
                        
                        st.metric(
                            display_name,
                            format_currency(price, sym),
                            delta=f"{change:.2f} ({change_pct:.1f}%)",
                            delta_color="normal" if change >= 0 else "inverse"
                        )
                    elif not hist.empty:
                        price = hist['Close'].iloc[-1]
                        st.metric(sym.replace('.ME', ''), format_currency(price, sym))
                    else:
                        st.metric(sym.replace('.ME', ''), "N/A")
                except:
                    st.metric(sym.replace('.ME', ''), "Err")

with col_w2:
    # Heures actuelles
    moscow_time = datetime.now(MOSCOW_TZ)
    ny_time = datetime.now(NY_TZ)
    london_time = datetime.now(LONDON_TZ)
    
    st.caption(f"🇷🇺 Moscou: {moscow_time.strftime('%H:%M:%S')}")
    st.caption(f"🇬🇧 Londres: {london_time.strftime('%H:%M:%S')}")
    st.caption(f"🇺🇸 NY: {ny_time.strftime('%H:%M:%S')}")
    
    # Statut des marchés
    market_status, market_icon = get_market_status()
    st.caption(f"{market_icon} MOEX: {market_status}")
    
    st.caption(f"Dernière MAJ: {moscow_time.strftime('%H:%M:%S')}")
    
    if auto_refresh and hist is not None and not hist.empty:
        time.sleep(refresh_rate)
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🇷🇺 Tracker Bourse Russie - Moscow Exchange (MOEX) | Données fournies par yfinance | "
    "⚠️ Données limitées par les sanctions internationales | 🕐 Heure de Moscou (UTC+3)<br>"
    "📌 Les données peuvent être obsolètes ou indisponibles. À titre informatif uniquement."
    "</p>",
    unsafe_allow_html=True
)
