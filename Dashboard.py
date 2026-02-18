import streamlit as st
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
import requests
import pytz
import warnings
import random
from functools import lru_cache
import hashlib
import pickle
import os

warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Tracker Bourse Russie - MOEX",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du fuseau horaire
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
        background: linear-gradient(135deg, #D52B1E 0%, #FFFFFF 50%, #0039A6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
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
        'SBER.ME', 'GAZP.ME', 'LKOH.ME', 'ROSN.ME', 'GMKN.ME',
        'YNDX.ME', 'MTSS.ME', 'NVTK.ME', 'MGNT.ME', 'TATN.ME'
    ]

if 'data_source' not in st.session_state:
    st.session_state.data_source = 'alpha_vantage'  # Option par défaut

if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'alpha_vantage': '',
        'twelve_data': '',
        'market_stack': ''
    }

# Mapping des symboles russes
RUSSIAN_STOCKS = {
    'SBER.ME': {'name': 'Sberbank', 'isin': 'RU0009029540', 'mic': 'MISX'},
    'GAZP.ME': {'name': 'Gazprom', 'isin': 'RU0007661625', 'mic': 'MISX'},
    'LKOH.ME': {'name': 'Lukoil', 'isin': 'RU0009024277', 'mic': 'MISX'},
    'ROSN.ME': {'name': 'Rosneft', 'isin': 'RU000A0J2Q06', 'mic': 'MISX'},
    'GMKN.ME': {'name': 'Norilsk Nickel', 'isin': 'RU0007288411', 'mic': 'MISX'},
    'YNDX.ME': {'name': 'Yandex', 'isin': 'NL0009805522', 'mic': 'MISX'},
    'MTSS.ME': {'name': 'MTS', 'isin': 'RU0007775219', 'mic': 'MISX'},
    'NVTK.ME': {'name': 'Novatek', 'isin': 'RU000A0DKVS5', 'mic': 'MISX'},
    'MGNT.ME': {'name': 'Magnit', 'isin': 'RU000A0JKQU8', 'mic': 'MISX'},
    'TATN.ME': {'name': 'Tatneft', 'isin': 'RU0009033591', 'mic': 'MISX'}
}

# ============================================================================
# FONCTIONS DE RÉCUPÉRATION DE DONNÉES ALTERNATIVES
# ============================================================================

def get_alpha_vantage_data(symbol, api_key):
    """Récupère les données via Alpha Vantage API"""
    try:
        # Nettoyer le symbole pour Alpha Vantage
        clean_symbol = symbol.replace('.ME', '.MCX')  # Format MOEX pour Alpha Vantage
        
        # Requête pour les données quotidiennes
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': clean_symbol,
            'apikey': api_key,
            'outputsize': 'compact'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.sort_index()
            
            # Convertir en UTC+4
            df.index = df.index.tz_localize('UTC').tz_convert(UTC4_TIMEZONE)
            
            return df, {'longName': RUSSIAN_STOCKS.get(symbol, {}).get('name', symbol)}
        
        return None, None
        
    except Exception as e:
        st.error(f"Erreur Alpha Vantage: {e}")
        return None, None

def get_twelve_data(symbol, api_key):
    """Récupère les données via Twelve Data API"""
    try:
        clean_symbol = symbol.replace('.ME', '.MCX')
        
        # Requête pour les données historiques
        url = f"https://api.twelvedata.com/time_series"
        params = {
            'symbol': clean_symbol,
            'interval': '1day',
            'apikey': api_key,
            'outputsize': 100,
            'format': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df = df.astype(float)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.sort_index()
            
            # Convertir en UTC+4
            df.index = df.index.tz_localize('UTC').tz_convert(UTC4_TIMEZONE)
            
            return df, {'longName': RUSSIAN_STOCKS.get(symbol, {}).get('name', symbol)}
        
        return None, None
        
    except Exception as e:
        st.error(f"Erreur Twelve Data: {e}")
        return None, None

def get_market_stack_data(symbol, api_key):
    """Récupère les données via Market Stack API"""
    try:
        clean_symbol = symbol.replace('.ME', '.MCX')
        
        # Requête pour les données historiques
        url = f"http://api.marketstack.com/v1/eod"
        params = {
            'access_key': api_key,
            'symbols': clean_symbol,
            'limit': 100
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            df = df.sort_index()
            
            # Convertir en UTC+4
            df.index = df.index.tz_localize('UTC').tz_convert(UTC4_TIMEZONE)
            
            return df, {'longName': RUSSIAN_STOCKS.get(symbol, {}).get('name', symbol)}
        
        return None, None
        
    except Exception as e:
        st.error(f"Erreur Market Stack: {e}")
        return None, None

def get_moex_official_data(symbol):
    """Tente de récupérer les données directement du site MOEX"""
    try:
        # Extraire le code ISIN ou ticker MOEX
        ticker = symbol.replace('.ME', '')
        
        # URL de l'API MOEX (officielle)
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'marketdata' in data and 'data' in data['marketdata']:
            # Traiter les données MOEX
            market_data = data['marketdata']['data']
            columns = data['marketdata']['columns']
            
            if market_data:
                # Créer un DataFrame avec les données
                df_dict = {}
                for row in market_data:
                    for i, col in enumerate(columns):
                        if col not in df_dict:
                            df_dict[col] = []
                        df_dict[col].append(row[i])
                
                df = pd.DataFrame(df_dict)
                
                # Convertir en format standard
                hist_data = {
                    'Open': float(df['OPEN'].iloc[-1]) if 'OPEN' in df else 0,
                    'High': float(df['HIGH'].iloc[-1]) if 'HIGH' in df else 0,
                    'Low': float(df['LOW'].iloc[-1]) if 'LOW' in df else 0,
                    'Close': float(df['LAST'].iloc[-1]) if 'LAST' in df else 0,
                    'Volume': float(df['VOLUME'].iloc[-1]) if 'VOLUME' in df else 0
                }
                
                # Créer un DataFrame avec un seul point de donnée
                hist = pd.DataFrame([hist_data], index=[datetime.now(UTC4_TIMEZONE)])
                
                info = {
                    'longName': RUSSIAN_STOCKS.get(symbol, {}).get('name', ticker),
                    'sector': 'N/A',
                    'marketCap': 0
                }
                
                return hist, info
        
        return None, None
        
    except Exception as e:
        return None, None

def generate_fallback_data(symbol, days=100):
    """Génère des données de repli basées sur des tendances réalistes"""
    np.random.seed(hash(symbol) % 42)
    
    # Prix de base selon le symbole
    base_prices = {
        'SBER.ME': 280.50,
        'GAZP.ME': 165.80,
        'LKOH.ME': 7200.50,
        'ROSN.ME': 550.30,
        'GMKN.ME': 16500.00,
        'YNDX.ME': 2850.00,
        'MTSS.ME': 320.00,
        'NVTK.ME': 1500.00,
        'MGNT.ME': 5500.00,
        'TATN.ME': 650.00
    }
    
    base_price = base_prices.get(symbol, 1000.00)
    
    # Générer des dates
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Générer une série de prix avec tendance et volatilité réalistes
    volatility = 0.02
    trend = 0.0001  # Légère tendance haussière
    
    returns = np.random.normal(trend, volatility, days)
    price_series = base_price * np.exp(np.cumsum(returns))
    
    # Ajouter quelques chocs aléatoires
    for i in range(len(price_series)):
        if random.random() < 0.05:  # 5% de chance de choc
            shock = random.uniform(-0.03, 0.03)
            price_series[i:] *= (1 + shock)
    
    # Créer le DataFrame
    df = pd.DataFrame({
        'Open': price_series * (1 - np.random.uniform(0, 0.01, days)),
        'High': price_series * (1 + np.random.uniform(0, 0.02, days)),
        'Low': price_series * (1 - np.random.uniform(0, 0.02, days)),
        'Close': price_series,
        'Volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)
    
    df.index = df.index.tz_localize(UTC4_TIMEZONE)
    
    info = {
        'longName': f"{RUSSIAN_STOCKS.get(symbol, {}).get('name', symbol)} (Données estimées)",
        'sector': 'N/A',
        'industry': 'N/A',
        'marketCap': base_price * 1000000000,  # Estimation
        'currency': 'RUB'
    }
    
    return df, info

@st.cache_data(ttl=3600)  # Cache d'une heure
def load_stock_data(symbol, period="1mo"):
    """Charge les données avec plusieurs sources de repli"""
    
    # 1. Essayer MOEX officiel d'abord
    with st.spinner("🔄 Tentative MOEX officiel..."):
        hist, info = get_moex_official_data(symbol)
        if hist is not None:
            st.success("✅ Données MOEX officielles chargées")
            return hist, info
    
    # 2. Essayer avec les clés API si disponibles
    if st.session_state.api_keys['alpha_vantage']:
        with st.spinner("🔄 Tentative Alpha Vantage..."):
            hist, info = get_alpha_vantage_data(symbol, st.session_state.api_keys['alpha_vantage'])
            if hist is not None:
                st.success("✅ Données Alpha Vantage chargées")
                return hist, info
    
    if st.session_state.api_keys['twelve_data']:
        with st.spinner("🔄 Tentative Twelve Data..."):
            hist, info = get_twelve_data(symbol, st.session_state.api_keys['twelve_data'])
            if hist is not None:
                st.success("✅ Données Twelve Data chargées")
                return hist, info
    
    # 3. Avertir l'utilisateur et proposer des options
    st.markdown("""
    <div class='warning-box'>
        <b>⚠️ Données en temps réel non disponibles</b><br>
        Les API externes sont actuellement limitées pour les actions russes.
        Vous pouvez :
        <ul>
            <li>Utiliser des données estimées pour la visualisation</li>
            <li>Configurer une clé API dans les paramètres</li>
            <li>Réessayer plus tard</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Proposer d'utiliser des données estimées
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Utiliser données estimées", use_container_width=True):
            st.session_state.data_source = 'estimated'
            st.rerun()
    with col2:
        if st.button("⚙️ Configurer API", use_container_width=True):
            st.session_state.data_source = 'config'
            st.rerun()
    
    # 4. Si l'utilisateur a choisi les données estimées
    if st.session_state.data_source == 'estimated':
        with st.spinner("🔄 Génération de données estimées..."):
            hist, info = generate_fallback_data(symbol)
            st.info("📊 Données estimées - À utiliser avec précaution")
            return hist, info
    
    return None, None

def get_exchange_rate():
    """Récupère le taux de change USD/RUB"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'].get('RUB', 90.0)
    except:
        return 90.0  # Valeur par défaut

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown("<h1 class='main-header'>🇷🇺 Tracker Bourse Russie - MOEX</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/russian-federation.png", width=80)
    st.title("Navigation")
    
    # Configuration API
    with st.expander("🔑 Configuration API", expanded=False):
        st.markdown("""
        **Obtenez des clés API gratuites :**
        - [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
        - [Twelve Data](https://twelvedata.com/apikey)
        - [Market Stack](https://marketstack.com/signup/free)
        """)
        
        st.session_state.api_keys['alpha_vantage'] = st.text_input("Alpha Vantage API Key", type="password", value=st.session_state.api_keys['alpha_vantage'])
        st.session_state.api_keys['twelve_data'] = st.text_input("Twelve Data API Key", type="password", value=st.session_state.api_keys['twelve_data'])
        st.session_state.api_keys['market_stack'] = st.text_input("Market Stack API Key", type="password", value=st.session_state.api_keys['market_stack'])
    
    st.markdown("---")
    
    menu = st.radio(
        "Choisir une section",
        ["📈 Tableau de bord", 
         "💰 Portefeuille", 
         "ℹ️ Informations"]
    )
    
    # Sélection du symbole
    symbol = st.selectbox(
        "Symbole",
        options=st.session_state.watchlist,
        index=0
    )

# ============================================================================
# SECTION: TABLEAU DE BORD
# ============================================================================
if menu == "📈 Tableau de bord":
    # Charger les données
    hist, info = load_stock_data(symbol)
    
    if hist is not None and not hist.empty:
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - previous_close
        change_pct = (change / previous_close * 100) if previous_close != 0 else 0
        
        # Métriques principales
        st.markdown(f"## {info.get('longName', symbol)}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Prix", f"₽{current_price:,.2f}", f"{change:.2f} ({change_pct:.1f}%)")
        with col2:
            st.metric("Plus haut", f"₽{hist['High'].iloc[-1]:,.2f}")
        with col3:
            st.metric("Plus bas", f"₽{hist['Low'].iloc[-1]:,.2f}")
        with col4:
            volume = hist['Volume'].iloc[-1]
            st.metric("Volume", f"{volume/1e6:.1f}M")
        
        # Graphique
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            mode='lines',
            name='Prix',
            line=dict(color='#D52B1E', width=2)
        ))
        
        fig.update_layout(
            title=f"Évolution du prix - {symbol}",
            xaxis_title="Date",
            yaxis_title="Prix (₽)",
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques
        with st.expander("📊 Statistiques détaillées"):
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Moyenne 20j", f"₽{hist['Close'].tail(20).mean():,.2f}")
                st.metric("Min 20j", f"₽{hist['Close'].tail(20).min():,.2f}")
            with col_s2:
                st.metric("Moyenne 50j", f"₽{hist['Close'].tail(50).mean():,.2f}")
                st.metric("Max 20j", f"₽{hist['Close'].tail(20).max():,.2f}")
            with col_s3:
                st.metric("Volatilité", f"{hist['Close'].pct_change().std()*100:.2f}%")
                st.metric("Variation YTD", f"{(hist['Close'].iloc[-1]/hist['Close'].iloc[0]-1)*100:.1f}%")
    
    else:
        st.markdown("""
        <div class='info-box'>
            <b>📡 Données non disponibles</b><br>
            Impossible de charger les données pour le moment.
            Veuillez vérifier votre connexion ou réessayer plus tard.
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# SECTION: PORTEFEUILLE
# ============================================================================
elif menu == "💰 Portefeuille":
    st.subheader("💰 Portefeuille virtuel")
    
    # Taux de change
    usd_rub = get_exchange_rate()
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.selectbox("Symbole", options=st.session_state.watchlist)
            shares = st.number_input("Nombre d'actions", min_value=1, value=100, step=10)
            buy_price = st.number_input("Prix d'achat (₽)", min_value=1.0, value=280.0, step=10.0)
            
            if st.form_submit_button("Ajouter"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares,
                    'buy_price': buy_price,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                st.success(f"✅ {shares} actions {symbol_pf} ajoutées")
                st.rerun()
    
    with col1:
        if st.session_state.portfolio:
            total_value = 0
            total_cost = 0
            
            for sym, positions in st.session_state.portfolio.items():
                hist, _ = load_stock_data(sym)
                current_price = hist['Close'].iloc[-1] if hist is not None else 0
                
                for pos in positions:
                    value = pos['shares'] * current_price
                    cost = pos['shares'] * pos['buy_price']
                    total_value += value
                    total_cost += cost
            
            total_profit = total_value - total_cost
            total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
            
            # Métriques du portefeuille
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Valeur totale", f"₽{total_value:,.0f}", f"${total_value/usd_rub:,.0f}")
            col_m2.metric("Coût total", f"₽{total_cost:,.0f}")
            col_m3.metric("Profit", f"₽{total_profit:,.0f}", f"{total_profit_pct:.1f}%")
            
            # Détails des positions
            st.markdown("### 📋 Positions")
            positions_data = []
            for sym, positions in st.session_state.portfolio.items():
                hist, _ = load_stock_data(sym)
                current_price = hist['Close'].iloc[-1] if hist is not None else 0
                
                for pos in positions:
                    value = pos['shares'] * current_price
                    cost = pos['shares'] * pos['buy_price']
                    profit = value - cost
                    profit_pct = (profit / cost * 100) if cost > 0 else 0
                    
                    positions_data.append({
                        'Symbole': sym,
                        'Actions': pos['shares'],
                        'Prix achat': f"₽{pos['buy_price']:,.2f}",
                        'Prix actuel': f"₽{current_price:,.2f}",
                        'Valeur': f"₽{value:,.0f}",
                        'Profit': f"₽{profit:,.0f}",
                        'Profit %': f"{profit_pct:.1f}%"
                    })
            
            st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
            
            if st.button("🗑️ Vider le portefeuille"):
                st.session_state.portfolio = {}
                st.rerun()
        else:
            st.info("Aucune position dans le portefeuille")

# ============================================================================
# SECTION: INFORMATIONS
# ============================================================================
elif menu == "ℹ️ Informations":
    st.subheader("ℹ️ À propos des actions russes")
    
    st.markdown("""
    ### 🇷🇺 Bourse de Moscou (MOEX)
    
    La Bourse de Moscou (MOEX) est la principale bourse russe, regroupant les plus grandes entreprises du pays.
    
    **Horaires de trading (UTC+4) :**
    - Ouverture : 11:00
    - Fermeture : 19:45
    - Jours ouverts : Lundi au Vendredi
    
    **Principaux indices :**
    - **IMOEX** : MOEX Russia Index (en roubles)
    - **RTSI** : RTS Index (en dollars)
    
    **Secteurs principaux :**
    - Énergie (pétrole et gaz) : Gazprom, Lukoil, Rosneft, Novatek
    - Métaux et mines : Norilsk Nickel, Alrosa, Severstal
    - Finance : Sberbank, VTB, TCS Group
    - Technologies : Yandex, VK (Mail.ru), Ozon
    - Télécoms : MTS, Rostelecom
    - Distribution : Magnit, X5 Retail Group
    
    ### 📊 Données du marché
    
    Les données présentées dans cette application proviennent de :
    - API officielle MOEX (quand disponible)
    - APIs tierces (Alpha Vantage, Twelve Data)
    - Estimations basées sur les tendances du marché
    
    **Note :** En raison des restrictions actuelles, les données en temps réel peuvent être limitées.
    """)
    
    # Tableau des actions
    st.markdown("### 📋 Liste des actions disponibles")
    stock_data = []
    for sym, info in RUSSIAN_STOCKS.items():
        stock_data.append({
            'Symbole': sym,
            'Société': info['name'],
            'ISIN': info['isin'],
            'MIC': info['mic']
        })
    
    st.dataframe(pd.DataFrame(stock_data), use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🇷🇺 Tracker Bourse Russie - MOEX | Données avec délai possible | 🕐 UTC+4"
    "</p>",
    unsafe_allow_html=True
)
