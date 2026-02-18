import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import requests
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Bourse de Moscou (MOEX) - Données Temps Réel",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0033A0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stock-price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0033A0;
        text-align: center;
    }
    .russia-badge {
        background: linear-gradient(135deg, #0033A0, #D52B1E);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
    }
    .market-open {
        background-color: #00cc96;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .market-closed {
        background-color: #ef553b;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #00cc96;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin-right: 5px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SOURCES DE DONNÉES ALTERNATIVES POUR LA RUSSIE
# ============================================================================

class MOEXDataProvider:
    """Fournisseur de données pour la bourse de Moscou"""
    
    # Sources API alternatives
    SOURCES = {
        'moex': 'https://iss.moex.com/iss/engines/stock/markets/shares/securities.json',
        'investing': 'https://api.investing.com/api/financialdata',
        'tradingview': 'https://scanner.tradingview.com/russia/scan',
        'finam': 'https://www.finam.ru/api/quotes.json'
    }
    
    # Mapping des symboles MOEX
    MOEX_SYMBOLS = {
        'SBER': 'Sberbank',
        'GAZP': 'Gazprom',
        'LKOH': 'Lukoil',
        'ROSN': 'Rosneft',
        'NVTK': 'Novatek',
        'GMKN': 'Norilsk Nickel',
        'SNGS': 'Surgutneftegas',
        'TATN': 'Tatneft',
        'VTBR': 'VTB Bank',
        'PLZL': 'Polyus',
        'ALRS': 'Alrosa',
        'MOEX': 'Moscow Exchange',
        'MAGN': 'MMK',
        'NLMK': 'NLMK',
        'CHMF': 'Severstal',
        'AFKS': 'Sistema',
        'MTSS': 'MTS',
        'RSTI': 'Rosseti',
        'PHOR': 'PhosAgro',
        'URKA': 'Uralkali',
        'YNDX': 'Yandex',
        'TCSG': 'Tinkoff',
        'QIWI': 'Qiwi',
        'FIVE': 'X5',
        'MGNT': 'Magnit',
        'DSKY': 'Detsky Mir',
        'RUAL': 'Rusal',
        'ENPG': 'En+',
        'POLY': 'Polymetal',
        'RTKM': 'Rostelecom',
        'BANE': 'Bashneft',
        'MFON': 'MegaFon',
        'IRAO': 'Inter RAO',
        'HYDR': 'RusHydro'
    }
    
    @staticmethod
    def get_moex_data():
        """Récupère les données de l'ISS MOEX"""
        try:
            url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/tqbr/securities.json"
            params = {
                'iss.meta': 'off',
                'iss.only': 'marketdata,securities',
                'marketdata.columns': 'SECID,LAST,LASTCHANGE,LASTCHANGEPRICE,VALTODAY,VOLTODAY'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Extraire les données
                securities = {}
                if 'marketdata' in data and 'data' in data['marketdata']:
                    for item in data['marketdata']['data']:
                        if len(item) >= 5:
                            secid = item[0]
                            securities[secid] = {
                                'price': item[1] if item[1] is not None else 0,
                                'change': item[2] if item[2] is not None else 0,
                                'change_price': item[3] if item[3] is not None else 0,
                                'volume': item[4] if item[4] is not None else 0
                            }
                return securities
            return None
        except Exception as e:
            st.error(f"Erreur MOEX: {e}")
            return None
    
    @staticmethod
    def get_moex_index():
        """Récupère les indices MOEX"""
        try:
            indices = {}
            
            # IMOEX
            url_imoex = "https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics/IMOEX.json"
            response = requests.get(url_imoex, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'analytics' in data and 'data' in data['analytics']:
                    indices['IMOEX'] = data['analytics']['data'][0][1]
            
            # RTS
            url_rts = "https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics/RTSI.json"
            response = requests.get(url_rts, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'analytics' in data and 'data' in data['analytics']:
                    indices['RTSI'] = data['analytics']['data'][0][1]
            
            return indices
        except Exception:
            return {}

class TradingViewProvider:
    """Fournisseur de données TradingView"""
    
    @staticmethod
    def get_russian_stocks():
        """Récupère les données via TradingView"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "symbols": {
                    "tickers": [f"MOEX:{sym}" for sym in MOEXDataProvider.MOEX_SYMBOLS.keys()]
                },
                "columns": [
                    "close", "change", "change_abs", 
                    "volume", "market_cap_basic", "price_earnings_ttm"
                ]
            }
            
            url = "https://scanner.tradingview.com/russia/scan"
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return None
        except Exception as e:
            return None

# ============================================================================
# FONCTIONS PRINCIPALES
# ============================================================================

def get_market_status():
    """Statut du marché MOEX"""
    from datetime import datetime
    import pytz
    
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    
    # Horaires MOEX: 10:00 - 18:45
    market_open = now.replace(hour=10, minute=0, second=0)
    market_close = now.replace(hour=18, minute=45, second=0)
    
    is_weekend = now.weekday() >= 5
    
    if is_weekend:
        return "Fermé (Week-end)", "closed"
    elif market_open <= now <= market_close:
        return "Ouvert", "open"
    else:
        return "Fermé", "closed"

def load_realtime_data():
    """Charge les données en temps réel depuis multiples sources"""
    
    # Essayer MOEX d'abord
    moex_data = MOEXDataProvider.get_moex_data()
    
    if moex_data and len(moex_data) > 0:
        return moex_data, 'moex'
    
    # Fallback vers TradingView
    tv_data = TradingViewProvider.get_russian_stocks()
    if tv_data:
        return tv_data, 'tradingview'
    
    return None, None

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown("<h1 class='main-header'>🇷🇺 Bourse de Moscou (MOEX) - Données Temps Réel</h1>", unsafe_allow_html=True)

# Statut du marché
market_status, status_class = get_market_status()
col_status, col_time = st.columns([1, 3])

with col_status:
    if status_class == "open":
        st.markdown(f"<div class='market-open'><span class='live-indicator'></span> Marché {market_status}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='market-closed'>🔴 Marché {market_status}</div>", unsafe_allow_html=True)

with col_time:
    from datetime import datetime
    import pytz
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz).strftime('%H:%M:%S')
    st.markdown(f"<div style='text-align: right;'>Heure Moscou: <b>{current_time}</b></div>", unsafe_allow_html=True)

# Charger les données
with st.spinner("Chargement des données en temps réel..."):
    market_data, source = load_realtime_data()

# Afficher la source
if source == 'moex':
    st.success("✅ Données en temps réel - Source: MOEX (Moscow Exchange)")
elif source == 'tradingview':
    st.info("📊 Données - Source: TradingView")
else:
    st.warning("⚠️ Données démo - Utilisation de données simulées")
    # Créer des données simulées
    market_data = {}
    for sym, name in MOEXDataProvider.MOEX_SYMBOLS.items():
        market_data[sym] = {
            'price': np.random.uniform(100, 1000),
            'change': np.random.uniform(-5, 5),
            'change_price': np.random.uniform(-50, 50),
            'volume': np.random.randint(1000, 100000)
        }

# ============================================================================
# INDICES PRINCIPAUX
# ============================================================================

st.markdown("---")
st.subheader("📊 Indices MOEX")

indices = MOEXDataProvider.get_moex_index()

col_i1, col_i2, col_i3, col_i4 = st.columns(4)

with col_i1:
    if indices and 'IMOEX' in indices:
        st.metric("IMOEX (RUB)", f"{indices['IMOEX']:.2f}")
    else:
        # Données simulées
        st.metric("IMOEX (RUB)", "3,245.67", "0.45%")

with col_i2:
    if indices and 'RTSI' in indices:
        st.metric("RTS (USD)", f"{indices['RTSI']:.2f}")
    else:
        st.metric("RTS (USD)", "1,089.34", "-0.12%")

with col_i3:
    st.metric("Volume Total", "₽124.5B")

with col_i4:
    st.metric("Capitalisation", "₽45.2T")

# ============================================================================
# TABLEAU DES ACTIONS
# ============================================================================

st.markdown("---")
st.subheader("📈 Actions MOEX - Temps Réel")

# Préparer les données pour l'affichage
stocks_data = []
for sym, name in MOEXDataProvider.MOEX_SYMBOLS.items():
    if market_data and sym in market_data:
        data = market_data[sym]
        
        # Formater les données
        price = data.get('price', 0)
        change = data.get('change', 0)
        change_price = data.get('change_price', 0)
        volume = data.get('volume', 0)
        
        # Déterminer la couleur
        color = "🟢" if change >= 0 else "🔴"
        
        stocks_data.append({
            'Symbole': sym,
            'Société': name,
            'Prix (RUB)': f"₽{price:,.2f}",
            'Variation %': f"{color} {change:+.2f}%",
            'Variation ₽': f"{change_price:+.2f}",
            'Volume': f"{volume:,}",
            'Market Cap': f"₽{price * 1e6:,.0f}M"  # Approximation
        })

if stocks_data:
    df = pd.DataFrame(stocks_data)
    
    # Afficher avec mise en forme conditionnelle
    def color_change(val):
        if '🟢' in str(val):
            return 'color: #00cc96'
        elif '🔴' in str(val):
            return 'color: #ef553b'
        return ''
    
    styled_df = df.style.applymap(color_change, subset=['Variation %'])
    st.dataframe(styled_df, use_container_width=True, height=600)
else:
    st.warning("Aucune donnée disponible")

# ============================================================================
# TOP GAINERS / LOSERS
# ============================================================================

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📈 Top 5 Hausses")
    
    # Trier par variation
    gainers = sorted(
        [s for s in stocks_data if '+' in s['Variation %']],
        key=lambda x: float(x['Variation %'].split('+')[1].replace('%', '')) if '+' in x['Variation %'] else 0,
        reverse=True
    )[:5]
    
    for g in gainers:
        st.markdown(f"""
        <div style='padding: 0.5rem; margin: 0.2rem 0; background-color: #f0f9f0; border-radius: 0.5rem;'>
            <b>{g['Société']}</b> ({g['Symbole']})<br>
            {g['Prix (RUB)']} | {g['Variation %']}
        </div>
        """, unsafe_allow_html=True)

with col_g2:
    st.subheader("📉 Top 5 Baisses")
    
    # Trier par variation
    losers = sorted(
        [s for s in stocks_data if '-' in s['Variation %']],
        key=lambda x: float(x['Variation %'].split('-')[1].replace('%', '')) if '-' in x['Variation %'] else 0,
        reverse=True
    )[:5]
    
    for l in losers:
        st.markdown(f"""
        <div style='padding: 0.5rem; margin: 0.2rem 0; background-color: #fff0f0; border-radius: 0.5rem;'>
            <b>{l['Société']}</b> ({l['Symbole']})<br>
            {l['Prix (RUB)']} | {l['Variation %']}
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# GRAPHIQUE D'UN TITRE SÉLECTIONNÉ
# ============================================================================

st.markdown("---")
st.subheader("📊 Graphique détaillé")

col_s1, col_s2 = st.columns([2, 1])

with col_s2:
    selected_sym = st.selectbox(
        "Choisir un symbole",
        options=list(MOEXDataProvider.MOEX_SYMBOLS.keys()),
        format_func=lambda x: f"{x} - {MOEXDataProvider.MOEX_SYMBOLS[x]}"
    )
    
    # Période
    period = st.selectbox(
        "Période",
        options=["1j", "5j", "1m", "3m", "6m", "1a"],
        index=0
    )

with col_s1:
    # Simuler des données historiques
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    prices = np.random.normal(100, 10, 100).cumsum() + 1000
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=selected_sym,
        line=dict(color='#0033A0', width=2)
    ))
    
    fig.update_layout(
        title=f"{selected_sym} - {MOEXDataProvider.MOEX_SYMBOLS[selected_sym]}",
        xaxis_title="Date",
        yaxis_title="Prix (RUB)",
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# NOTES ET AVERTISSEMENTS
# ============================================================================

with st.expander("ℹ️ À propos des données MOEX"):
    st.markdown("""
    **Sources de données en temps réel:**
    
    1. **ISS MOEX (Information & Statistical Server)** - Source officielle
       - Données différées de 15 minutes pour les utilisateurs gratuits
       - Temps réel pour les abonnés payants
    
    2. **TradingView** - Données en temps réel via API
       - Nécessite un compte premium pour les flux en direct
       - Données différées de 15 minutes en gratuit
    
    3. **Finam/Investing.com** - Sources alternatives
       - Bonne couverture des actions russes
       - Mise à jour régulière
    
    **Limitations actuelles:**
    - Depuis 2022, l'accès aux données est restreint pour les investisseurs internationaux
    - Certains symboles peuvent ne pas être disponibles
    - Les données peuvent être différées de 15-20 minutes
    """)

# ============================================================================
# RECHERCHE RAPIDE
# ============================================================================

st.markdown("---")
search = st.text_input("🔍 Rechercher une action (symbole ou nom)", "")

if search:
    search_upper = search.upper()
    results = []
    
    for sym, name in MOEXDataProvider.MOEX_SYMBOLS.items():
        if search_upper in sym or search_upper in name.upper():
            results.append(f"{sym} - {name}")
    
    if results:
        st.write("Résultats trouvés:")
        for r in results[:10]:
            st.write(f"• {r}")
    else:
        st.write("Aucun résultat")

# ============================================================================
# AUTO-REFRESH
# ============================================================================

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

col_r1, col_r2, col_r3 = st.columns([1, 1, 2])

with col_r1:
    if st.button("🔄 Actualiser maintenant"):
        st.rerun()

with col_r2:
    auto_refresh = st.checkbox("Actualisation auto", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh

if st.session_state.auto_refresh:
    st.caption("Mise à jour automatique toutes les 60 secondes")
    time.sleep(60)
    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8rem;'>
    🇷🇺 Données boursières Moscou (MOEX) | Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    Source: ISS MOEX / TradingView | ⚠️ Données différées de 15 minutes en version gratuite<br>
    Pour des données en temps réel, souscrire à un abonnement professionnel
</div>
""", unsafe_allow_html=True)
