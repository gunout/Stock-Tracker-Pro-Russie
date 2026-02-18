import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import time
import pytz
import json
import os
import hashlib
from typing import Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MOEX - Analyse Technique",
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
    .source-official { background-color: #0033A0; color: white; }
    .source-cache { background-color: #4CAF50; color: white; }
    .source-simulated { background-color: #FF9800; color: white; }
    .data-quality {
        font-size: 0.9rem;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .quality-high { background-color: #d4edda; color: #155724; }
    .quality-medium { background-color: #fff3cd; color: #856404; }
    .quality-low { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MODÈLE DE DONNÉES UNIFIÉ
# ============================================================================

class MOEXData:
    """Structure de données unifiée pour MOEX"""
    
    def __init__(self):
        self.symbol = ""
        self.company_name = ""
        self.source = ""
        self.last_update = None
        self.dates = []
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.volume = []
        self.current_price = 0.0
        self.change_percent = 0.0
        self.quality_score = 0  # 0-100
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convertit en DataFrame pandas"""
        if not self.dates:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }, index=pd.to_datetime(self.dates))
        
        return df
    
    def is_valid(self) -> bool:
        """Vérifie si les données sont valides"""
        return (len(self.dates) > 0 and 
                len(self.open) > 0 and 
                len(self.close) > 0)
    
    def get_quality_score(self) -> int:
        """Calcule un score de qualité des données"""
        score = 100
        
        # Pénalités basées sur la source
        source_penalties = {
            'MOEX Officiel': 0,
            'Cache': 10,
            'Simulé': 50
        }
        score -= source_penalties.get(self.source, 30)
        
        # Vérifier la complétude
        if len(self.dates) < 20:
            score -= 30
        
        # Vérifier la fraîcheur
        if self.last_update:
            age_hours = (datetime.now() - self.last_update).total_seconds() / 3600
            if age_hours > 24:
                score -= 20
            elif age_hours > 6:
                score -= 10
        
        return max(0, min(100, score))

# ============================================================================
# COLLECTEUR DE DONNÉES MOEX
# ============================================================================

class MOEXDataCollector:
    """Collecte les données de multiples sources et les unifie"""
    
    # Mapping des symboles
    SYMBOLS = {
        'SBER': {
            'name': 'Sberbank',
            'isin': 'RU0009029540',
            'moex_id': 'SBER',
            'figi': 'BBG004730N88'
        },
        'GAZP': {
            'name': 'Gazprom',
            'isin': 'RU0007661625',
            'moex_id': 'GAZP',
            'figi': 'BBG004730RP0'
        },
        'LKOH': {
            'name': 'Lukoil',
            'isin': 'RU0009024277',
            'moex_id': 'LKOH',
            'figi': 'BBG004731032'
        },
        'ROSN': {
            'name': 'Rosneft',
            'isin': 'RU000A0J2Q06',
            'moex_id': 'ROSN',
            'figi': 'BBG0047315D0'
        },
        'NVTK': {
            'name': 'Novatek',
            'isin': 'RU000A0DKV59',
            'moex_id': 'NVTK',
            'figi': 'BBG004Q0X2S7'
        },
        'GMKN': {
            'name': 'Norilsk Nickel',
            'isin': 'RU0007288411',
            'moex_id': 'GMKN',
            'figi': 'BBG0047315T0'
        },
        'YNDX': {
            'name': 'Yandex',
            'isin': 'NL0009805522',
            'moex_id': 'YNDX',
            'figi': 'BBG006L6B6V6'
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        self.cache_dir = ".moex_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, symbol: str) -> str:
        """Génère une clé de cache"""
        date_str = datetime.now().strftime('%Y%m%d_%H')
        key = f"{symbol}_{date_str}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _save_to_cache(self, symbol: str, data: MOEXData):
        """Sauvegarde les données dans le cache"""
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(symbol)}.json")
        
        cache_data = {
            'symbol': data.symbol,
            'company_name': data.company_name,
            'source': data.source,
            'last_update': data.last_update.isoformat() if data.last_update else None,
            'dates': [d.isoformat() if hasattr(d, 'isoformat') else d for d in data.dates],
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume,
            'current_price': data.current_price,
            'change_percent': data.change_percent
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Erreur cache: {e}")
    
    def _load_from_cache(self, symbol: str) -> Optional[MOEXData]:
        """Charge les données du cache si disponibles"""
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(symbol)}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Vérifier l'âge du cache
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > 3600:  # Plus d'une heure
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            data = MOEXData()
            data.symbol = cache_data.get('symbol', symbol)
            data.company_name = cache_data.get('company_name', '')
            data.source = cache_data.get('source', 'Cache')
            data.last_update = datetime.fromisoformat(cache_data['last_update']) if cache_data.get('last_update') else None
            data.dates = [datetime.fromisoformat(d) for d in cache_data.get('dates', [])]
            data.open = cache_data.get('open', [])
            data.high = cache_data.get('high', [])
            data.low = cache_data.get('low', [])
            data.close = cache_data.get('close', [])
            data.volume = cache_data.get('volume', [])
            data.current_price = cache_data.get('current_price', 0)
            data.change_percent = cache_data.get('change_percent', 0)
            
            return data
        except Exception:
            return None
    
    def collect_from_moex(self, symbol: str) -> Optional[MOEXData]:
        """Collecte les données depuis l'API MOEX"""
        try:
            # Utiliser l'API ISS MOEX
            moex_id = self.SYMBOLS.get(symbol, {}).get('moex_id', symbol)
            
            # Récupérer les données historiques
            url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/tqbr/securities/{moex_id}.json"
            params = {
                'from': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'till': datetime.now().strftime('%Y-%m-%d'),
                'start': 0,
                'limit': 100
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Vérifier la structure des données
            if 'history' not in data or 'data' not in data['history']:
                return None
            
            # Créer l'objet de données
            moex_data = MOEXData()
            moex_data.symbol = symbol
            moex_data.company_name = self.SYMBOLS.get(symbol, {}).get('name', symbol)
            moex_data.source = 'MOEX Officiel'
            moex_data.last_update = datetime.now()
            
            # Parcourir les données
            columns = data['history']['columns']
            date_idx = columns.index('TRADEDATE')
            open_idx = columns.index('OPEN') if 'OPEN' in columns else None
            high_idx = columns.index('HIGH') if 'HIGH' in columns else None
            low_idx = columns.index('LOW') if 'LOW' in columns else None
            close_idx = columns.index('CLOSE') if 'CLOSE' in columns else None
            volume_idx = columns.index('VOLUME') if 'VOLUME' in columns else None
            
            for row in data['history']['data']:
                try:
                    date = datetime.strptime(row[date_idx], '%Y-%m-%d')
                    
                    moex_data.dates.append(date)
                    moex_data.open.append(float(row[open_idx]) if open_idx is not None and row[open_idx] else 0)
                    moex_data.high.append(float(row[high_idx]) if high_idx is not None and row[high_idx] else 0)
                    moex_data.low.append(float(row[low_idx]) if low_idx is not None and row[low_idx] else 0)
                    moex_data.close.append(float(row[close_idx]) if close_idx is not None and row[close_idx] else 0)
                    moex_data.volume.append(float(row[volume_idx]) if volume_idx is not None and row[volume_idx] else 0)
                except (ValueError, IndexError):
                    continue
            
            if moex_data.close:
                moex_data.current_price = moex_data.close[-1]
                if len(moex_data.close) > 1:
                    moex_data.change_percent = ((moex_data.close[-1] / moex_data.close[-2]) - 1) * 100
            
            return moex_data
            
        except Exception as e:
            print(f"Erreur MOEX: {e}")
            return None
    
    def collect_from_yahoo(self, symbol: str) -> Optional[MOEXData]:
        """Collecte depuis Yahoo Finance"""
        try:
            import yfinance as yf
            
            # Attendre pour éviter rate limiting
            time.sleep(2)
            
            ticker = yf.Ticker(f"{symbol}.ME")
            hist = ticker.history(period="3mo", interval="1d")
            
            if hist.empty:
                return None
            
            moex_data = MOEXData()
            moex_data.symbol = symbol
            moex_data.company_name = self.SYMBOLS.get(symbol, {}).get('name', symbol)
            moex_data.source = 'Yahoo Finance'
            moex_data.last_update = datetime.now()
            
            # Convertir les données
            for date, row in hist.iterrows():
                moex_data.dates.append(date)
                moex_data.open.append(float(row['Open']))
                moex_data.high.append(float(row['High']))
                moex_data.low.append(float(row['Low']))
                moex_data.close.append(float(row['Close']))
                moex_data.volume.append(int(row['Volume']))
            
            moex_data.current_price = moex_data.close[-1] if moex_data.close else 0
            if len(moex_data.close) > 1:
                moex_data.change_percent = ((moex_data.close[-1] / moex_data.close[-2]) - 1) * 100
            
            return moex_data
            
        except Exception as e:
            print(f"Erreur Yahoo: {e}")
            return None
    
    def generate_simulated_data(self, symbol: str) -> MOEXData:
        """Génère des données simulées réalistes"""
        
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
        
        moex_data = MOEXData()
        moex_data.symbol = symbol
        moex_data.company_name = self.SYMBOLS.get(symbol, {}).get('name', symbol)
        moex_data.source = 'Simulé'
        moex_data.last_update = datetime.now()
        
        # Générer 90 jours de données
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        current_date = start_date
        price = base_price
        volatility = 0.02
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Jours de semaine
                # Mouvement de prix réaliste
                drift = 0.0002  # Légère tendance haussière
                shock = np.random.normal(0, volatility)
                price = price * np.exp(drift + shock)
                
                # Générer OHLC
                high_mult = 1 + abs(np.random.normal(0, 0.005))
                low_mult = 1 - abs(np.random.normal(0, 0.005))
                
                moex_data.dates.append(current_date)
                moex_data.open.append(float(price * 0.998))
                moex_data.high.append(float(price * high_mult))
                moex_data.low.append(float(price * low_mult))
                moex_data.close.append(float(price))
                moex_data.volume.append(int(np.random.uniform(100000, 5000000)))
            
            current_date += timedelta(days=1)
        
        moex_data.current_price = moex_data.close[-1] if moex_data.close else base_price
        moex_data.change_percent = np.random.uniform(-2, 2)
        
        return moex_data
    
    def get_best_data(self, symbol: str, use_cache: bool = True) -> MOEXData:
        """Récupère les meilleures données disponibles"""
        
        # Essayer le cache d'abord
        if use_cache:
            cached = self._load_from_cache(symbol)
            if cached and cached.is_valid():
                cached.source = "Cache"
                return cached
        
        # Essayer MOEX officiel
        st.info("🔄 Tentative: MOEX Officiel...")
        data = self.collect_from_moex(symbol)
        if data and data.is_valid():
            self._save_to_cache(symbol, data)
            return data
        
        # Essayer Yahoo
        st.info("🔄 Tentative: Yahoo Finance...")
        data = self.collect_from_yahoo(symbol)
        if data and data.is_valid():
            self._save_to_cache(symbol, data)
            return data
        
        # Fallback aux données simulées
        st.warning("⚠️ Utilisation de données simulées (aucune source disponible)")
        data = self.generate_simulated_data(symbol)
        return data

# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

class TechnicalAnalyzer:
    """Analyse technique"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcule le RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calcule le MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Calcule les bandes de Bollinger"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calcule le VWAP"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

def main():
    st.markdown("<div class='main-header'>🇷🇺 MOEX - DONNÉES BOURSIÈRES RUSSES</div>", 
                unsafe_allow_html=True)
    
    # Initialisation
    collector = MOEXDataCollector()
    analyzer = TechnicalAnalyzer()
    
    # Sidebar
    with st.sidebar:
        st.title("Configuration")
        
        # Sélection du symbole
        symbol = st.selectbox(
            "Symbole",
            options=list(MOEXDataCollector.SYMBOLS.keys()),
            format_func=lambda x: f"{x} - {MOEXDataCollector.SYMBOLS[x]['name']}"
        )
        
        # Option de cache
        use_cache = st.checkbox("Utiliser le cache", value=True)
        
        # Bouton de rafraîchissement
        if st.button("🔄 Forcer le rafraîchissement"):
            use_cache = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Sources de données:**")
        st.markdown("1. 🇷🇺 MOEX Officiel (prioritaire)")
        st.markdown("2. 📈 Yahoo Finance")
        st.markdown("3. 💾 Cache local")
        st.markdown("4. 🎲 Simulation (fallback)")
    
    # Récupération des données
    with st.spinner("Récupération des données..."):
        data = collector.get_best_data(symbol, use_cache=use_cache)
    
    if not data or not data.is_valid():
        st.error("Impossible de récupérer les données")
        return
    
    # Score de qualité
    quality_score = data.get_quality_score()
    quality_class = "quality-high" if quality_score >= 70 else "quality-medium" if quality_score >= 40 else "quality-low"
    
    # Affichage de la source et qualité
    col_source1, col_source2 = st.columns([2, 1])
    
    with col_source1:
        source_class = f"source-{data.source.lower().split()[0]}" if data.source.lower() in ['moex', 'cache', 'simulé'] else "source-simulated"
        st.markdown(f"""
        <div>
            <span class="source-badge {source_class}">📡 Source: {data.source}</span>
            <span style="color: gray;">Dernière mise à jour: {data.last_update.strftime('%H:%M:%S') if data.last_update else 'N/A'}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_source2:
        st.markdown(f"<div class='data-quality {quality_class}'>Qualité: {quality_score}/100</div>", 
                   unsafe_allow_html=True)
    
    # Convertir en DataFrame pour l'analyse
    df = data.to_dataframe()
    
    if df.empty:
        st.error("Données insuffisantes pour l'analyse")
        return
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"{symbol} - {data.company_name}",
            f"₽{data.current_price:,.2f}",
            f"{data.change_percent:+.2f}%"
        )
    
    with col2:
        st.metric("Plus haut (période)", f"₽{df['high'].max():,.2f}")
    
    with col3:
        st.metric("Plus bas (période)", f"₽{df['low'].min():,.2f}")
    
    with col4:
        st.metric("Volume total", f"{df['volume'].sum():,.0f}")
    
    # Graphique principal
    st.subheader("📈 Analyse Prix & Volume")
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.3]
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
    upper, middle, lower = analyzer.calculate_bollinger(df['close'])
    
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
        line=dict(color='orange', width=1)
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
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)
    
    # RSI
    rsi = analyzer.calculate_rsi(df['close'])
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=rsi,
        name='RSI',
        line=dict(color='purple', width=1)
    ), row=3, col=1)
    
    # Lignes de référence RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=3, col=1)
    
    # Mise en page
    fig.update_layout(
        title=f"{symbol} - Analyse technique",
        xaxis_title="Date",
        yaxis_title="Prix (RUB)",
        height=800,
        template='plotly_white',
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistiques
    with st.expander("📊 Statistiques détaillées"):
        col_s1, col_s2, col_s3 = st.columns(3)
        
        returns = df['close'].pct_change().dropna()
        
        with col_s1:
            st.metric("Moyenne (période)", f"₽{df['close'].mean():,.2f}")
            st.metric("Volatilité", f"{returns.std() * 100:.2f}%")
        
        with col_s2:
            st.metric("Médiane", f"₽{df['close'].median():,.2f}")
            st.metric("Skewness", f"{returns.skew():.3f}")
        
        with col_s3:
            st.metric("Ecart-type", f"₽{df['close'].std():,.2f}")
            st.metric("Kurtosis", f"{returns.kurtosis():.3f}")
        
        # Afficher les dernières données
        st.subheader("Dernières transactions")
        st.dataframe(df.tail(10))
    
    # Note sur la qualité des données
    if data.source == "Simulé":
        st.warning("""
        ⚠️ **Données simulées**
        
        Les données en temps réel ne sont pas disponibles actuellement. 
        Causes possibles:
        - API MOEX temporairement indisponible
        - Limitations de taux
        - Restrictions d'accès
        
        Réessayez dans quelques minutes.
        """)

if __name__ == "__main__":
    main()
