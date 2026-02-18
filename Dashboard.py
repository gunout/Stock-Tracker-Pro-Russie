import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import time
import pytz
import hashlib
import json
import os
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MOEX - Analyse Technique Multi-Sources",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0033A0, #D52B1E);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .source-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .source-moex { background-color: #0033A0; color: white; }
    .source-tradingview { background-color: #2196F3; color: white; }
    .source-investing { background-color: #FF9800; color: white; }
    .source-cache { background-color: #4CAF50; color: white; }
    .source-simulated { background-color: #9E9E9E; color: white; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GESTIONNAIRE DE CACHE INTELLIGENT
# ============================================================================

class SmartCache:
    """Cache intelligent avec expiration et persistance"""
    
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, symbol, period, interval):
        """Génère une clé de cache unique"""
        key_str = f"{symbol}_{period}_{interval}_{datetime.now().strftime('%Y%m%d_%H')}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, symbol, period, interval, max_age=3600):
        """Récupère les données du cache si elles sont encore valides"""
        cache_key = self._get_cache_key(symbol, period, interval)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < max_age:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except:
                    pass
        return None
    
    def set(self, symbol, period, interval, data):
        """Sauvegarde les données dans le cache"""
        cache_key = self._get_cache_key(symbol, period, interval)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

# ============================================================================
# SOURCES DE DONNÉES MULTIPLES POUR MOEX
# ============================================================================

class MOEXMultiSourceProvider:
    """Fournisseur avec plusieurs sources de données"""
    
    # Mapping des symboles
    SYMBOLS = {
        'SBER': {'name': 'Sberbank', 'isin': 'RU0009029540'},
        'GAZP': {'name': 'Gazprom', 'isin': 'RU0007661625'},
        'LKOH': {'name': 'Lukoil', 'isin': 'RU0009024277'},
        'ROSN': {'name': 'Rosneft', 'isin': 'RU000A0J2Q06'},
        'NVTK': {'name': 'Novatek', 'isin': 'RU000A0DKV59'},
        'GMKN': {'name': 'Norilsk Nickel', 'isin': 'RU0007288411'},
        'YNDX': {'name': 'Yandex', 'isin': 'NL0009805522'},
    }
    
    def __init__(self):
        self.cache = SmartCache()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_data_moex_iss(self, symbol):
        """Source 1: API officielle MOEX ISS"""
        try:
            # Récupérer l'ISIN
            isin = self.SYMBOLS.get(symbol, {}).get('isin', '')
            if not isin:
                return None
            
            # Requête à l'API MOEX
            url = f"https://iss.moex.com/iss/securities/{isin}.json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {'source': 'moex', 'data': data}
        except:
            pass
        return None
    
    def get_data_tradingview(self, symbol):
        """Source 2: TradingView via API"""
        try:
            url = "https://scanner.tradingview.com/russia/scan"
            
            payload = {
                "symbols": {
                    "tickers": [f"MOEX:{symbol}"],
                    "query": {"types": []}
                },
                "columns": [
                    "close", "volume", "high", "low", "open",
                    "change", "relative_volume", "RSI", "MACD.macd"
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {'source': 'tradingview', 'data': data}
        except:
            pass
        return None
    
    def get_data_investing(self, symbol):
        """Source 3: Investing.com"""
        try:
            # Mapping des paires Investing
            investing_ids = {
                'SBER': '8830',
                'GAZP': '8833',
                'LKOH': '8835',
            }
            
            pair_id = investing_ids.get(symbol, '')
            if not pair_id:
                return None
            
            url = f"https://api.investing.com/api/financialdata/{pair_id}/historical"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {'source': 'investing', 'data': data}
        except:
            pass
        return None
    
    def get_data_yahoo_alternative(self, symbol):
        """Source 4: Yahoo Finance via API alternative"""
        try:
            # Utiliser yfinance avec rate limiting
            import yfinance as yf
            
            # Attendre entre les requêtes
            time.sleep(2)
            
            ticker = yf.Ticker(f"{symbol}.ME")
            hist = ticker.history(period="1mo", interval="1d")
            
            if not hist.empty:
                # Convertir en format standard
                data = []
                for date, row in hist.iterrows():
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume'])
                    })
                
                return {
                    'source': 'yahoo',
                    'data': data,
                    'current': {
                        'price': float(hist['Close'].iloc[-1]),
                        'change': float(((hist['Close'].iloc[-1] / hist['Close'].iloc[-2]) - 1) * 100)
                    }
                }
        except:
            pass
        return None
    
    def generate_simulated_data(self, symbol, days=30):
        """Source 5: Données simulées réalistes (fallback)"""
        base_prices = {
            'SBER': 280.50,
            'GAZP': 165.30,
            'LKOH': 7100.00,
            'ROSN': 550.00,
            'NVTK': 1300.00,
            'GMKN': 17000.00,
            'YNDX': 2600.00,
        }
        
        base_price = base_prices.get(symbol, 1000.00)
        
        # Générer des données réalistes
        dates = []
        data = []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        price = base_price
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Jours de semaine
                # Variation réaliste
                change = np.random.normal(0.0005, 0.02)
                price = price * (1 + change)
                
                high = price * (1 + abs(np.random.normal(0, 0.01)))
                low = price * (1 - abs(np.random.normal(0, 0.01)))
                
                dates.append(current_date.strftime('%Y-%m-%d'))
                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'open': float(price * 0.999),
                    'high': float(high),
                    'low': float(low),
                    'close': float(price),
                    'volume': int(np.random.randint(100000, 10000000))
                })
            
            current_date += timedelta(days=1)
        
        return {
            'source': 'simulated',
            'data': data,
            'current': {
                'price': float(price),
                'change': float(np.random.uniform(-3, 3))
            }
        }
    
    def get_best_available_data(self, symbol, period="1mo", interval="1d"):
        """Tente toutes les sources dans l'ordre et retourne la meilleure disponible"""
        
        # Vérifier le cache d'abord
        cached = self.cache.get(symbol, period, interval)
        if cached:
            cached['source'] = 'cache'
            return cached
        
        # Liste des sources dans l'ordre de préférence
        sources = [
            ('MOEX ISS', self.get_data_moex_iss),
            ('TradingView', self.get_data_tradingview),
            ('Investing.com', self.get_data_investing),
            ('Yahoo (ralenti)', self.get_data_yahoo_alternative),
        ]
        
        for source_name, source_func in sources:
            try:
                st.info(f"🔄 Tentative: {source_name}...")
                result = source_func(symbol)
                
                if result and result.get('data'):
                    # Sauvegarder dans le cache
                    self.cache.set(symbol, period, interval, result)
                    
                    # Ajouter la source pour affichage
                    result['source_display'] = source_name
                    return result
                
            except Exception as e:
                continue
        
        # Fallback: données simulées
        st.warning("⚠️ Utilisation de données simulées (aucune source en temps réel disponible)")
        simulated = self.generate_simulated_data(symbol)
        simulated['source_display'] = 'Simulé'
        return simulated

# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

class TechnicalIndicators:
    """Calcul des indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger(prices, period=20, std_dev=2):
        """Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

def main():
    st.markdown("<div class='main-header'>🇷🇺 MOEX - DONNÉES MULTI-SOURCES INTELLIGENTES</div>", 
                unsafe_allow_html=True)
    
    # Initialisation
    provider = MOEXMultiSourceProvider()
    
    # Sidebar
    with st.sidebar:
        st.title("Configuration")
        
        # Sélection du symbole
        symbol = st.selectbox(
            "Symbole",
            options=list(MOEXMultiSourceProvider.SYMBOLS.keys()),
            format_func=lambda x: f"{x} - {MOEXMultiSourceProvider.SYMBOLS[x]['name']}"
        )
        
        # Option pour vider le cache
        if st.button("🗑️ Vider le cache"):
            cache_dir = ".cache"
            if os.path.exists(cache_dir):
                for f in os.listdir(cache_dir):
                    os.remove(os.path.join(cache_dir, f))
            st.success("Cache vidé !")
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Sources disponibles:**")
        st.markdown("• 🏦 MOEX ISS (officiel)")
        st.markdown("• 📊 TradingView")
        st.markdown("• 💹 Investing.com")
        st.markdown("• ⏳ Yahoo Finance (limité)")
        st.markdown("• 🎲 Simulé (fallback)")
    
    # Chargement des données
    with st.spinner("Recherche de la meilleure source de données..."):
        data = provider.get_best_available_data(symbol)
    
    if not data:
        st.error("Impossible de charger les données. Veuillez réessayer plus tard.")
        return
    
    # Afficher la source utilisée
    source_display = data.get('source_display', data.get('source', 'Inconnue'))
    source_class = {
        'MOEX ISS': 'source-moex',
        'TradingView': 'source-tradingview',
        'Investing.com': 'source-investing',
        'cache': 'source-cache',
        'Simulé': 'source-simulated'
    }.get(source_display, 'source-simulated')
    
    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <span class="source-badge {source_class}">📡 Source: {source_display}</span>
        <span style="color: gray; font-size: 0.9rem;">Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Traitement des données selon le format
    if 'data' in data and isinstance(data['data'], list):
        # Format standard
        df = pd.DataFrame(data['data'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        current_price = data.get('current', {}).get('price', df['close'].iloc[-1])
        current_change = data.get('current', {}).get('change', 0)
    else:
        st.warning("Format de données non supporté")
        return
    
    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"{symbol} - {MOEXMultiSourceProvider.SYMBOLS[symbol]['name']}",
            f"₽{current_price:,.2f}",
            f"{current_change:+.2f}%"
        )
    
    with col2:
        st.metric("Plus haut", f"₽{df['high'].max():,.2f}")
    
    with col3:
        st.metric("Plus bas", f"₽{df['low'].min():,.2f}")
    
    with col4:
        st.metric("Volume total", f"{df['volume'].sum():,.0f}")
    
    # Graphique principal
    st.subheader("📈 Analyse Prix & Volume")
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.3],
        subplot_titles=(f"{symbol} - Chandeliers", "Volume", "RSI")
    )
    
    # Chandeliers
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Prix',
        increasing_line_color='#00cc96',
        decreasing_line_color='#ef553b'
    ), row=1, col=1)
    
    # Bollinger Bands
    upper, middle, lower = TechnicalIndicators.calculate_bollinger(df['close'])
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=upper,
        name='BB Upper',
        line=dict(color='gray', dash='dash'),
        opacity=0.5
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=middle,
        name='MA20',
        line=dict(color='orange')
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=lower,
        name='BB Lower',
        line=dict(color='gray', dash='dash'),
        opacity=0.5,
        fill='tonexty'
    ), row=1, col=1)
    
    # Volume
    colors = ['#00cc96' if df['close'].iloc[i] >= df['open'].iloc[i] 
              else '#ef553b' for i in range(len(df))]
    
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['volume'],
        name='Volume',
        marker_color=colors
    ), row=2, col=1)
    
    # RSI
    rsi = TechnicalIndicators.calculate_rsi(df['close'])
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=rsi,
        name='RSI',
        line=dict(color='purple')
    ), row=3, col=1)
    
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
    
    fig.update_layout(
        height=800,
        template='plotly_white',
        showlegend=True,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Informations sur le taux de limitation
    if source_display == 'Simulé':
        st.warning("""
        ⚠️ **Données simulées utilisées**
        
        Causes possibles:
        - Limitation de taux (rate limiting) des API
        - Indisponibilité temporaire des sources
        - Sanctions affectant l'accès aux données
        
        **Solutions:**
        1. Attendez quelques minutes et réessayez
        2. Utilisez le bouton "Vider le cache"
        3. Réessayez plus tard
        """)
    
    # Bouton d'actualisation
    if st.button("🔄 Actualiser maintenant"):
        st.cache_data.clear()
        provider.cache = SmartCache()  # Nouveau cache
        st.rerun()
    
    # Timer pour éviter le rate limiting
    time.sleep(2)

if __name__ == "__main__":
    main()
