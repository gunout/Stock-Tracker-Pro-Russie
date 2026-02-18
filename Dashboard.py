import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import requests
import json
import time
import pytz
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MOEX - Analyse Technique Temps Réel",
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
    .buy-signal {
        background-color: #00cc96;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .sell-signal {
        background-color: #ef553b;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .neutral-signal {
        background-color: #ffa15a;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SOURCE DE DONNÉES RÉELLES POUR MOEX
# ============================================================================

class MOEXRealDataProvider:
    """Fournisseur de données réelles pour MOEX"""
    
    # Mapping des symboles MOEX vers Yahoo Finance
    YAHOO_SYMBOLS = {
        'SBER': 'SBER.ME',
        'GAZP': 'GAZP.ME',
        'LKOH': 'LKOH.ME',
        'ROSN': 'ROSN.ME',
        'NVTK': 'NVTK.ME',
        'GMKN': 'GMKN.ME',
        'SNGS': 'SNGS.ME',
        'TATN': 'TATN.ME',
        'VTBR': 'VTBR.ME',
        'PLZL': 'PLZL.ME',
        'ALRS': 'ALRS.ME',
        'MOEX': 'MOEX.ME',
        'MAGN': 'MAGN.ME',
        'NLMK': 'NLMK.ME',
        'CHMF': 'CHMF.ME',
        'AFKS': 'AFKS.ME',
        'MTSS': 'MTSS.ME',
        'PHOR': 'PHOR.ME',
        'URKA': 'URKA.ME',
        'YNDX': 'YNDX.ME',
        'TCSG': 'TCSG.ME',
        'QIWI': 'QIWI.ME',
        'FIVE': 'FIVE.ME',
        'MGNT': 'MGNT.ME',
        'RUAL': 'RUAL.ME',
        'POLY': 'POLY.ME',
        'RTKM': 'RTKM.ME',
        'IRAO': 'IRAO.ME',
        'HYDR': 'HYDR.ME'
    }
    
    # Noms des sociétés
    COMPANY_NAMES = {
        'SBER': 'Sberbank',
        'GAZP': 'Gazprom',
        'LKOH': 'Lukoil',
        'ROSN': 'Rosneft',
        'NVTK': 'Novatek',
        'GMKN': 'Norilsk Nickel',
        'SNGS': 'Surgutneftegas',
        'TATN': 'Tatneft',
        'VTBR': 'VTB Bank',
        'PLZL': 'Polyus Gold',
        'ALRS': 'Alrosa',
        'MOEX': 'Moscow Exchange',
        'MAGN': 'MMK',
        'NLMK': 'NLMK',
        'CHMF': 'Severstal',
        'AFKS': 'Sistema',
        'MTSS': 'MTS',
        'PHOR': 'PhosAgro',
        'URKA': 'Uralkali',
        'YNDX': 'Yandex',
        'TCSG': 'Tinkoff',
        'QIWI': 'Qiwi',
        'FIVE': 'X5 Retail',
        'MGNT': 'Magnit',
        'RUAL': 'Rusal',
        'POLY': 'Polymetal',
        'RTKM': 'Rostelecom',
        'IRAO': 'Inter RAO',
        'HYDR': 'RusHydro'
    }
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_historical_data(symbol, period="3mo", interval="1d"):
        """Récupère les données historiques réelles"""
        try:
            yahoo_symbol = MOEXRealDataProvider.YAHOO_SYMBOLS.get(symbol, f"{symbol}.ME")
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            # Convertir en heure de Moscou
            moscow_tz = pytz.timezone('Europe/Moscow')
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(moscow_tz)
            else:
                hist.index = hist.index.tz_convert(moscow_tz)
            
            return hist
        except Exception as e:
            st.error(f"Erreur chargement {symbol}: {e}")
            return None
    
    @staticmethod
    @st.cache_data(ttl=60)
    def get_realtime_quotes():
        """Récupère les cotations en temps réel"""
        quotes = {}
        
        for symbol, yahoo_symbol in MOEXRealDataProvider.YAHOO_SYMBOLS.items():
            try:
                ticker = yf.Ticker(yahoo_symbol)
                info = ticker.info
                
                # Récupérer le prix actuel
                if 'regularMarketPrice' in info:
                    price = info['regularMarketPrice']
                elif 'currentPrice' in info:
                    price = info['currentPrice']
                else:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                    else:
                        continue
                
                # Récupérer la variation
                if 'regularMarketChangePercent' in info:
                    change_pct = info['regularMarketChangePercent']
                else:
                    change_pct = 0
                
                # Volume
                if 'volume' in info:
                    volume = info['volume']
                else:
                    volume = 0
                
                quotes[symbol] = {
                    'name': MOEXRealDataProvider.COMPANY_NAMES.get(symbol, symbol),
                    'price': price,
                    'change': change_pct,
                    'volume': volume,
                    'high': info.get('dayHigh', price),
                    'low': info.get('dayLow', price),
                    'open': info.get('open', price)
                }
            except Exception as e:
                continue
        
        return quotes
    
    @staticmethod
    def get_indices():
        """Récupère les indices russes"""
        indices = {}
        
        try:
            # IMOEX
            imoex = yf.Ticker("IMOEX.ME")
            imoex_hist = imoex.history(period="1d")
            if not imoex_hist.empty:
                indices['IMOEX'] = {
                    'value': imoex_hist['Close'].iloc[-1],
                    'change': 0  # Calculer la variation
                }
            
            # RTS
            rts = yf.Ticker("RTS.ME")
            rts_hist = rts.history(period="1d")
            if not rts_hist.empty:
                indices['RTS'] = {
                    'value': rts_hist['Close'].iloc[-1],
                    'change': 0
                }
        except:
            pass
        
        return indices

# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

class TechnicalIndicators:
    """Calcul des indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(data, period=14):
        """RSI - Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9):
        """MACD - Moving Average Convergence Divergence"""
        exp1 = data.ewm(span=fast, adjust=False).mean()
        exp2 = data.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data, period=20, std_dev=2):
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_volume_profile(data, volume, bins=20):
        """Volume Profile"""
        price_range = np.linspace(data.min(), data.max(), bins)
        volume_profile = []
        
        for i in range(len(price_range) - 1):
            mask = (data >= price_range[i]) & (data < price_range[i + 1])
            vol = volume[mask].sum()
            volume_profile.append({
                'price_level': (price_range[i] + price_range[i + 1]) / 2,
                'volume': vol
            })
        
        return pd.DataFrame(volume_profile)
    
    @staticmethod
    def calculate_vwap(high, low, close, volume):
        """VWAP - Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    @staticmethod
    def get_signals(hist):
        """Génère des signaux d'achat/vente"""
        if len(hist) < 50:
            return "neutral", 0
        
        close = hist['Close']
        
        # RSI
        rsi = TechnicalIndicators.calculate_rsi(close).iloc[-1]
        
        # MACD
        macd, signal, _ = TechnicalIndicators.calculate_macd(close)
        macd_signal = macd.iloc[-1] - signal.iloc[-1]
        
        # Bollinger
        upper, _, lower = TechnicalIndicators.calculate_bollinger_bands(close)
        last_close = close.iloc[-1]
        
        # Score (0-100)
        score = 50
        
        # RSI signals
        if rsi < 30:
            score += 20  # Survente - potentiel achat
        elif rsi > 70:
            score -= 20  # Surachat - potentiel vente
        
        # MACD signals
        if macd_signal > 0:
            score += 10
        else:
            score -= 10
        
        # Bollinger signals
        if last_close <= lower.iloc[-1]:
            score += 15  # Support
        elif last_close >= upper.iloc[-1]:
            score -= 15  # Résistance
        
        # Volume
        avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        if current_volume > avg_volume * 1.5:
            if score > 50:
                score += 10
            else:
                score -= 10
        
        if score >= 70:
            return "buy", score
        elif score <= 30:
            return "sell", score
        else:
            return "neutral", score

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

def main():
    st.markdown("<div class='main-header'>🇷🇺 MOEX - ANALYSE TECHNIQUE AVANCÉE</div>", 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/moscow.png", width=80)
        st.title("🇷🇺 MOEX")
        
        # Sélection du symbole
        symbol = st.selectbox(
            "Symbole",
            options=list(MOEXRealDataProvider.COMPANY_NAMES.keys()),
            format_func=lambda x: f"{x} - {MOEXRealDataProvider.COMPANY_NAMES[x]}",
            index=0
        )
        
        # Période d'analyse
        period = st.selectbox(
            "Période",
            options=["1mo", "3mo", "6mo", "1y", "2y"],
            index=1
        )
        
        # Intervalle
        interval = st.selectbox(
            "Intervalle",
            options=["1d", "1wk", "1mo"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("📊 Indicateurs")
        
        show_rsi = st.checkbox("RSI", value=True)
        show_macd = st.checkbox("MACD", value=True)
        show_bollinger = st.checkbox("Bollinger Bands", value=True)
        show_vwap = st.checkbox("VWAP", value=False)
        show_volume_profile = st.checkbox("Volume Profile", value=False)
    
    # Chargement des données
    with st.spinner("Chargement des données en temps réel..."):
        hist = MOEXRealDataProvider.get_historical_data(symbol, period, interval)
        quotes = MOEXRealDataProvider.get_realtime_quotes()
    
    if hist is None or hist.empty:
        st.error("Impossible de charger les données. Veuillez réessayer.")
        return
    
    # =========================================================
    # SECTION 1: INFORMATIONS EN TEMPS RÉEL
    # =========================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
    change = current_price - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0
    
    with col1:
        st.metric(
            f"{symbol} - {MOEXRealDataProvider.COMPANY_NAMES[symbol]}",
            f"₽{current_price:,.2f}",
            f"{change:+,.2f} ({change_pct:+.2f}%)"
        )
    
    with col2:
        day_high = hist['High'].iloc[-1]
        day_low = hist['Low'].iloc[-1]
        st.metric("Jour - Haut/Bas", f"₽{day_high:,.2f} / ₽{day_low:,.2f}")
    
    with col3:
        volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].tail(20).mean()
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        
        st.metric(
            "Volume",
            f"{volume:,.0f}",
            f"{volume_ratio:.2f}x moyenne"
        )
    
    with col4:
        # Signal
        signal, score = TechnicalIndicators.get_signals(hist)
        
        if signal == "buy":
            st.markdown(f"<div class='buy-signal'>🟢 SIGNAL ACHAT ({score})</div>", 
                       unsafe_allow_html=True)
        elif signal == "sell":
            st.markdown(f"<div class='sell-signal'>🔴 SIGNAL VENTE ({score})</div>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='neutral-signal'>🟡 NEUTRE ({score})</div>", 
                       unsafe_allow_html=True)
    
    # =========================================================
    # SECTION 2: GRAPHIQUE PRINCIPAL AVEC VOLUMES
    # =========================================================
    
    st.subheader("📈 Analyse Prix & Volume")
    
    # Créer le graphique avec sous-graphiques
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.3],
        subplot_titles=(f"{symbol} - Prix et Bandes", "Volume", "RSI")
    )
    
    # Chandeliers japonais
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='Prix',
        showlegend=False,
        increasing_line_color='#00cc96',
        decreasing_line_color='#ef553b'
    ), row=1, col=1)
    
    # Bollinger Bands
    if show_bollinger:
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(hist['Close'])
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=upper,
            name='Bande supérieure',
            line=dict(color='gray', width=1, dash='dash'),
            opacity=0.5
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=middle,
            name='MM20',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=lower,
            name='Bande inférieure',
            line=dict(color='gray', width=1, dash='dash'),
            opacity=0.5,
            fill='tonexty',
            fillcolor='rgba(128, 128, 128, 0.1)'
        ), row=1, col=1)
    
    # VWAP
    if show_vwap:
        vwap = TechnicalIndicators.calculate_vwap(
            hist['High'], hist['Low'], hist['Close'], hist['Volume']
        )
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=vwap,
            name='VWAP',
            line=dict(color='purple', width=1)
        ), row=1, col=1)
    
    # Volume avec couleur conditionnelle
    colors = ['#00cc96' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] 
              else '#ef553b' for i in range(len(hist))]
    
    fig.add_trace(go.Bar(
        x=hist.index,
        y=hist['Volume'],
        name='Volume',
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)
    
    # Moyenne mobile du volume
    volume_ma = hist['Volume'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=volume_ma,
        name='Volume MA20',
        line=dict(color='blue', width=1)
    ), row=2, col=1)
    
    # RSI
    if show_rsi:
        rsi = TechnicalIndicators.calculate_rsi(hist['Close'])
        
        fig.add_trace(go.Scatter(
            x=hist.index,
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
        title=f"{symbol} - Analyse technique avec volumes",
        xaxis_title="Date",
        yaxis_title="Prix (RUB)",
        height=800,
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="Prix (RUB)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================
    # SECTION 3: ANALYSE DES VOLUMES
    # =========================================================
    
    st.subheader("📊 Analyse détaillée des volumes")
    
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        # Volume Profile
        vp = TechnicalIndicators.calculate_volume_profile(
            hist['Close'], hist['Volume'], bins=20
        )
        
        fig_vp = go.Figure()
        
        fig_vp.add_trace(go.Bar(
            x=vp['volume'],
            y=vp['price_level'],
            orientation='h',
            name='Volume Profile',
            marker_color='#0033A0',
            opacity=0.7
        ))
        
        # Prix actuel
        fig_vp.add_hline(
            y=current_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Prix actuel: ₽{current_price:,.2f}"
        )
        
        fig_vp.update_layout(
            title="Volume Profile (Distribution des volumes par prix)",
            xaxis_title="Volume",
            yaxis_title="Prix (RUB)",
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_vp, use_container_width=True)
    
    with col_v2:
        # Volume par jour
        hist['Weekday'] = hist.index.day_name()
        hist['Month'] = hist.index.month_name()
        
        daily_vol = hist.groupby('Weekday')['Volume'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'
        ])
        
        fig_daily = go.Figure()
        
        fig_daily.add_trace(go.Bar(
            x=daily_vol.index,
            y=daily_vol.values,
            marker_color='#D52B1E',
            text=[f"{v:,.0f}" for v in daily_vol.values],
            textposition='outside'
        ))
        
        fig_daily.update_layout(
            title="Volume moyen par jour de la semaine",
            xaxis_title="Jour",
            yaxis_title="Volume moyen",
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_daily, use_container_width=True)
    
    # =========================================================
    # SECTION 4: ANALYSE TECHNIQUE AVANCÉE
    # =========================================================
    
    st.subheader("📈 Indicateurs techniques")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        # MACD
        macd, signal, histogram = TechnicalIndicators.calculate_macd(hist['Close'])
        
        fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        
        fig_macd.add_trace(go.Scatter(
            x=hist.index,
            y=macd,
            name='MACD',
            line=dict(color='blue')
        ), row=1, col=1)
        
        fig_macd.add_trace(go.Scatter(
            x=hist.index,
            y=signal,
            name='Signal',
            line=dict(color='red')
        ), row=1, col=1)
        
        # Histogramme
        colors = ['green' if val >= 0 else 'red' for val in histogram]
        fig_macd.add_trace(go.Bar(
            x=hist.index,
            y=histogram,
            name='Histogramme',
            marker_color=colors
        ), row=2, col=1)
        
        fig_macd.update_layout(
            title="MACD",
            height=400,
            template='plotly_white',
            showlegend=True
        )
        
        st.plotly_chart(fig_macd, use_container_width=True)
    
    with col_t2:
        # RSI avec zones
        rsi = TechnicalIndicators.calculate_rsi(hist['Close'])
        
        fig_rsi = go.Figure()
        
        fig_rsi.add_trace(go.Scatter(
            x=hist.index,
            y=rsi,
            name='RSI',
            line=dict(color='purple', width=2),
            fill='tozeroy'
        ))
        
        # Zones de surachat/survente
        fig_rsi.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.1)
        fig_rsi.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.1)
        
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray")
        
        fig_rsi.update_layout(
            title="RSI (Relative Strength Index)",
            yaxis_range=[0, 100],
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col_t3:
        # Analyse des gaps et supports/résistances
        last_20 = hist.tail(20)
        
        support = last_20['Low'].min()
        resistance = last_20['High'].max()
        
        fig_sr = go.Figure()
        
        fig_sr.add_trace(go.Scatter(
            x=last_20.index,
            y=last_20['Close'],
            mode='lines+markers',
            name='Prix',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))
        
        # Lignes de support et résistance
        fig_sr.add_hline(
            y=support,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Support: ₽{support:,.2f}"
        )
        
        fig_sr.add_hline(
            y=resistance,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Résistance: ₽{resistance:,.2f}"
        )
        
        fig_sr.update_layout(
            title="Supports et Résistances (20 derniers jours)",
            yaxis_title="Prix (RUB)",
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_sr, use_container_width=True)
    
    # =========================================================
    # SECTION 5: STATISTIQUES DESCRIPTIVES
    # =========================================================
    
    with st.expander("📊 Statistiques détaillées"):
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        returns = hist['Close'].pct_change().dropna()
        
        with col_s1:
            st.metric("Volatilité (20j)", f"{returns.tail(20).std() * 100:.2f}%")
            st.metric("Max 52 semaines", f"₽{hist['High'].max():,.2f}")
        
        with col_s2:
            st.metric("Ratio de Sharpe", f"{returns.mean() / returns.std() * np.sqrt(252):.2f}")
            st.metric("Min 52 semaines", f"₽{hist['Low'].min():,.2f}")
        
        with col_s3:
            st.metric("Skewness", f"{returns.skew():.3f}")
            st.metric("Kurtosis", f"{returns.kurtosis():.3f}")
        
        with col_s4:
            st.metric("Var 95% (1j)", f"{returns.quantile(0.05) * 100:.2f}%")
            st.metric("CVaR 95%", f"{returns[returns <= returns.quantile(0.05)].mean() * 100:.2f}%")
    
    # =========================================================
    # SECTION 6: SIGNAL D'ALERTE
    # =========================================================
    
    st.subheader("🔔 Alertes techniques")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        # Détection de croisement de moyennes mobiles
        ma20 = hist['Close'].rolling(window=20).mean()
        ma50 = hist['Close'].rolling(window=50).mean()
        
        if len(hist) > 50:
            last_ma20 = ma20.iloc[-1]
            last_ma50 = ma50.iloc[-1]
            prev_ma20 = ma20.iloc[-2]
            prev_ma50 = ma50.iloc[-2]
            
            if last_ma20 > last_ma50 and prev_ma20 <= prev_ma50:
                st.success("🟢 CROISEMENT DORÉ : MA20 croise au-dessus MA50 (signal haussier)")
            elif last_ma20 < last_ma50 and prev_ma20 >= prev_ma50:
                st.error("🔴 CROISEMENT MORTEL : MA20 croise en-dessous MA50 (signal baissier)")
            else:
                st.info("🟡 Pas de croisement de moyennes mobiles")
    
    with col_a2:
        # Détection de divergence RSI
        if len(hist) > 20:
            last_price = hist['Close'].iloc[-1]
            price_5d_ago = hist['Close'].iloc[-6]
            
            last_rsi = rsi.iloc[-1]
            rsi_5d_ago = rsi.iloc[-6]
            
            if last_price > price_5d_ago and last_rsi < rsi_5d_ago:
                st.warning("⚠️ DIVERGENCE BAISSIÈRE : Prix monte mais RSI baisse")
            elif last_price < price_5d_ago and last_rsi > rsi_5d_ago:
                st.info("💡 DIVERGENCE HAUSSIÈRE : Prix baisse mais RSI monte")
    
    # =========================================================
    # AUTO-REFRESH
    # =========================================================
    
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    
    # Footer avec timestamp
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: gray; font-size: 0.8rem;">
        🇷🇺 MOEX - Données en temps réel via Yahoo Finance<br>
        Dernière mise à jour: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (heure Moscou)<br>
        Les données peuvent être différées de 15-20 minutes
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
