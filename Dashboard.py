import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import requests
import json
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MOEX Exchange - Dashboard Complet",
    page_icon="🇷🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0033A0, #D52B1E);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 2rem;
        font-weight: bold;
    }
    .timezone-card {
        background-color: #1e1e2f;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .market-open {
        background-color: #00cc96;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .market-closed {
        background-color: #ef553b;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .live-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-size: 0.8rem;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .metric-rub {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0033A0;
    }
    .metric-usd {
        font-size: 1.8rem;
        font-weight: bold;
        color: #D52B1E;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GESTIONNAIRE DE FUSEAUX HORAIRES POUR MOEX
# ============================================================================

class MOEXTimeZoneManager:
    """Gestionnaire des fuseaux horaires pour MOEX"""
    
    # Tous les fuseaux UTC
    UTC_OFFSETS = {
        'UTC-12': -12, 'UTC-11': -11, 'UTC-10': -10, 'UTC-9': -9, 'UTC-8': -8,
        'UTC-7': -7, 'UTC-6': -6, 'UTC-5': -5, 'UTC-4': -4, 'UTC-3': -3,
        'UTC-2': -2, 'UTC-1': -1, 'UTC+0': 0, 'UTC+1': 1, 'UTC+2': 2,
        'UTC+3': 3, 'UTC+4': 4, 'UTC+5': 5, 'UTC+6': 6, 'UTC+7': 7,
        'UTC+8': 8, 'UTC+9': 9, 'UTC+10': 10, 'UTC+11': 11, 'UTC+12': 12,
        'UTC+13': 13, 'UTC+14': 14
    }
    
    # Mapping IANA pour MOEX
    IANA_MAPPING = {
        'UTC-12': 'Etc/GMT+12',
        'UTC-11': 'Pacific/Midway',
        'UTC-10': 'Pacific/Honolulu',
        'UTC-9': 'America/Anchorage',
        'UTC-8': 'America/Los_Angeles',
        'UTC-7': 'America/Denver',
        'UTC-6': 'America/Chicago',
        'UTC-5': 'America/New_York',
        'UTC-4': 'America/Caracas',
        'UTC-3': 'America/Sao_Paulo',
        'UTC-2': 'America/Noronha',
        'UTC-1': 'Atlantic/Cape_Verde',
        'UTC+0': 'Europe/London',
        'UTC+1': 'Europe/Paris',
        'UTC+2': 'Europe/Helsinki',
        'UTC+3': 'Europe/Moscow',
        'UTC+4': 'Asia/Dubai',
        'UTC+5': 'Asia/Karachi',
        'UTC+6': 'Asia/Dhaka',
        'UTC+7': 'Asia/Bangkok',
        'UTC+8': 'Asia/Shanghai',
        'UTC+9': 'Asia/Tokyo',
        'UTC+10': 'Australia/Sydney',
        'UTC+11': 'Pacific/Noumea',
        'UTC+12': 'Pacific/Auckland',
        'UTC+13': 'Pacific/Apia',
        'UTC+14': 'Pacific/Kiritimati'
    }
    
    # Grandes villes par fuseau
    MAJOR_CITIES = {
        'UTC-5': 'New York, Toronto',
        'UTC+0': 'Londres, Dublin',
        'UTC+1': 'Paris, Berlin, Rome',
        'UTC+2': 'Helsinki, Le Caire',
        'UTC+3': 'Moscou, Istanbul',
        'UTC+4': 'Dubaï',
        'UTC+5': 'Karachi',
        'UTC+5:30': 'Mumbai',
        'UTC+8': 'Shanghai, Singapour',
        'UTC+9': 'Tokyo, Séoul'
    }
    
    def __init__(self):
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        
    def get_moscow_time(self):
        """Heure actuelle à Moscou"""
        return datetime.now(self.moscow_tz)
    
    def convert_to_timezone(self, dt, target_tz):
        """Convertit une heure de Moscou vers un autre fuseau"""
        if isinstance(target_tz, str):
            target_tz = pytz.timezone(target_tz)
        return dt.astimezone(target_tz)
    
    def get_market_hours_local(self, target_tz):
        """Heures d'ouverture MOEX en heure locale"""
        moscow_now = self.get_moscow_time()
        today = moscow_now.date()
        
        # Heures MOEX (heure de Moscou)
        moex_open = self.moscow_tz.localize(datetime.combine(today, datetime.strptime('10:00', '%H:%M').time()))
        moex_close = self.moscow_tz.localize(datetime.combine(today, datetime.strptime('18:45', '%H:%M').time()))
        moex_evening_open = self.moscow_tz.localize(datetime.combine(today, datetime.strptime('19:05', '%H:%M').time()))
        moex_evening_close = self.moscow_tz.localize(datetime.combine(today, datetime.strptime('23:50', '%H:%M').time()))
        
        # Conversion
        target = pytz.timezone(target_tz) if isinstance(target_tz, str) else target_tz
        
        return {
            'main_open': moex_open.astimezone(target).strftime('%H:%M'),
            'main_close': moex_close.astimezone(target).strftime('%H:%M'),
            'evening_open': moex_evening_open.astimezone(target).strftime('%H:%M'),
            'evening_close': moex_evening_close.astimezone(target).strftime('%H:%M'),
            'date': moex_open.astimezone(target).strftime('%d/%m/%Y')
        }
    
    def get_market_status(self):
        """Statut actuel du marché MOEX"""
        moscow_now = self.get_moscow_time()
        
        # Vérifier weekend
        if moscow_now.weekday() >= 5:
            return "Fermé (Week-end)", "closed"
        
        # Horaires
        main_open = moscow_now.replace(hour=10, minute=0, second=0)
        main_close = moscow_now.replace(hour=18, minute=45, second=0)
        evening_open = moscow_now.replace(hour=19, minute=5, second=0)
        evening_close = moscow_now.replace(hour=23, minute=50, second=0)
        
        if main_open <= moscow_now <= main_close:
            return "Session principale", "open"
        elif evening_open <= moscow_now <= evening_close:
            return "Session du soir", "evening"
        elif moscow_now < main_open:
            return "Pré-ouverture", "pre"
        else:
            return "Fermé", "closed"
    
    def time_until_next_session(self):
        """Temps avant la prochaine session"""
        moscow_now = self.get_moscow_time()
        
        # Prochaine ouverture
        next_open = moscow_now.replace(hour=10, minute=0, second=0)
        if moscow_now > next_open:
            next_open = next_open + timedelta(days=1)
            # Skip weekend
            while next_open.weekday() >= 5:
                next_open = next_open + timedelta(days=1)
        
        delta = next_open - moscow_now
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        seconds = int(delta.total_seconds() % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ============================================================================
# DONNÉES MOEX
# ============================================================================

class MOEXDataProvider:
    """Fournisseur de données pour MOEX"""
    
    # Actions MOEX
    MOEX_STOCKS = {
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
        'PHOR': 'PhosAgro',
        'URKA': 'Uralkali',
        'YNDX': 'Yandex',
        'TCSG': 'Tinkoff',
        'QIWI': 'Qiwi',
        'FIVE': 'X5',
        'MGNT': 'Magnit',
        'RUAL': 'Rusal',
        'POLY': 'Polymetal',
        'RTKM': 'Rostelecom',
        'IRAO': 'Inter RAO',
        'HYDR': 'RusHydro'
    }
    
    # Indices
    INDICES = {
        'IMOEX': 'MOEX Russia Index',
        'RTSI': 'RTS Index',
        'MOEXBC': 'MOEX Blue Chip',
        'MOEXMM': 'MOEX Metals & Mining',
        'MOEXOG': 'MOEX Oil & Gas',
        'MOEXFN': 'MOEX Finance',
        'MOEXCN': 'MOEX Consumer'
    }
    
    @staticmethod
    def get_realtime_data():
        """Simule des données en temps réel"""
        # Dans une vraie application, utilisez l'API MOEX
        # https://iss.moex.com/iss/reference/
        
        data = {}
        for symbol, name in MOEXDataProvider.MOEX_STOCKS.items():
            # Générer des données réalistes
            base_price = {
                'SBER': 280.50, 'GAZP': 165.30, 'LKOH': 7100.00, 'ROSN': 550.00,
                'NVTK': 1300.00, 'GMKN': 17000.00, 'YNDX': 2600.00, 'TCSG': 3400.00
            }.get(symbol, np.random.uniform(100, 1000))
            
            # Variation aléatoire
            change_pct = np.random.uniform(-3, 3)
            price = base_price * (1 + change_pct/100)
            
            data[symbol] = {
                'name': name,
                'price': price,
                'change': change_pct,
                'change_abs': price - base_price,
                'volume': np.random.randint(10000, 10000000),
                'market_cap': price * np.random.randint(1000000, 1000000000)
            }
        
        return data
    
    @staticmethod
    def get_indices():
        """Données des indices"""
        return {
            'IMOEX': {'value': 3245.67, 'change': 0.45},
            'RTSI': {'value': 1089.34, 'change': -0.12},
            'MOEXBC': {'value': 1850.23, 'change': 0.32},
            'MOEXOG': {'value': 4120.56, 'change': 0.78}
        }

# ============================================================================
# INTERFACE PRINCIPALE - DASHBOARD MOEX
# ============================================================================

def main():
    # Initialisation
    tz_manager = MOEXTimeZoneManager()
    moex_data = MOEXDataProvider()
    
    # Header
    st.markdown("<div class='main-header'>🇷🇺 MOEX MOSCOW EXCHANGE - DASHBOARD COMPLET</div>", 
                unsafe_allow_html=True)
    
    # =========================================================
    # SECTION 1: FUSEAUX HORAIRES ET STATUT
    # =========================================================
    
    st.subheader("🕐 Gestionnaire de fuseaux horaires MOEX")
    
    # Sélecteur de fuseau
    col_tz1, col_tz2, col_tz3 = st.columns([2, 2, 1])
    
    with col_tz1:
        selected_utc = st.selectbox(
            "🌐 Votre fuseau horaire",
            options=list(MOEXTimeZoneManager.UTC_OFFSETS.keys()),
            index=list(MOEXTimeZoneManager.UTC_OFFSETS.keys()).index('UTC+3'),
            help="Sélectionnez votre fuseau horaire pour voir les heures MOEX converties"
        )
        
        # Afficher les grandes villes
        if selected_utc in MOEXTimeZoneManager.MAJOR_CITIES:
            st.caption(f"🏙️ {MOEXTimeZoneManager.MAJOR_CITIES[selected_utc]}")
    
    with col_tz2:
        # Heure dans le fuseau sélectionné
        offset = MOEXTimeZoneManager.UTC_OFFSETS[selected_utc]
        tz_name = MOEXTimeZoneManager.IANA_MAPPING.get(selected_utc, 'Europe/Moscow')
        local_tz = pytz.timezone(tz_name)
        local_time = datetime.now(local_tz)
        
        st.metric(
            "Heure locale",
            local_time.strftime("%H:%M:%S"),
            delta=f"{selected_utc}"
        )
        st.caption(local_time.strftime("%d %B %Y"))
    
    with col_tz3:
        # Heure de Moscou
        moscow_time = tz_manager.get_moscow_time()
        st.metric(
            "🇷🇺 Moscou",
            moscow_time.strftime("%H:%M:%S"),
            delta="UTC+3"
        )
    
    # Statut du marché
    status, status_class = tz_manager.get_market_status()
    countdown = tz_manager.time_until_next_session()
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        if status_class == "open":
            st.markdown(f"<div class='market-open'>🟢 {status}</div>", unsafe_allow_html=True)
        elif status_class == "evening":
            st.markdown(f"<div class='market-open'>🌙 {status}</div>", unsafe_allow_html=True)
        elif status_class == "pre":
            st.markdown(f"<div class='market-closed'>🟡 {status}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='market-closed'>🔴 {status}</div>", unsafe_allow_html=True)
    
    with col_stat2:
        st.metric("⏳ Prochaine ouverture", countdown)
    
    with col_stat3:
        st.metric("📅 Date", moscow_time.strftime("%d/%m/%Y"))
    
    with col_stat4:
        st.markdown("<span class='live-badge'>LIVE</span>", unsafe_allow_html=True)
    
    # Heures MOEX converties
    st.markdown("---")
    st.subheader("📅 Horaires MOEX dans votre fuseau")
    
    market_hours = tz_manager.get_market_hours_local(tz_name)
    
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    
    with col_h1:
        st.info(f"**Session principale**\n\n{market_hours['main_open']} - {market_hours['main_close']}")
    with col_h2:
        st.info(f"**Session du soir**\n\n{market_hours['evening_open']} - {market_hours['evening_close']}")
    with col_h3:
        st.info(f"**Date locale**\n\n{market_hours['date']}")
    with col_h4:
        # Jours restants dans la semaine
        days_left = 5 - moscow_time.weekday()
        if days_left > 0 and moscow_time.weekday() < 5:
            st.info(f"**Jours de trading**\n\n{days_left} jours restants")
        else:
            st.info("**Jours de trading**\n\nWeek-end")
    
    # =========================================================
    # SECTION 2: INDICES MOEX
    # =========================================================
    
    st.markdown("---")
    st.subheader("📊 Indices MOEX")
    
    indices = moex_data.get_indices()
    
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    
    with col_i1:
        st.metric(
            "IMOEX (RUB)",
            f"{indices['IMOEX']['value']:.2f}",
            f"{indices['IMOEX']['change']:.2f}%"
        )
    with col_i2:
        st.metric(
            "RTS (USD)",
            f"{indices['RTSI']['value']:.2f}",
            f"{indices['RTSI']['change']:.2f}%"
        )
    with col_i3:
        st.metric(
            "MOEX Blue Chip",
            f"{indices['MOEXBC']['value']:.2f}",
            f"{indices['MOEXBC']['change']:.2f}%"
        )
    with col_i4:
        st.metric(
            "MOEX Oil & Gas",
            f"{indices['MOEXOG']['value']:.2f}",
            f"{indices['MOEXOG']['change']:.2f}%"
        )
    
    # =========================================================
    # SECTION 3: TOP ACTIONS MOEX
    # =========================================================
    
    st.markdown("---")
    st.subheader("📈 Top Actions MOEX")
    
    # Charger les données
    with st.spinner("Chargement des données en temps réel..."):
        stocks = moex_data.get_realtime_data()
    
    # Créer DataFrame
    df_stocks = pd.DataFrame([
        {
            'Symbole': sym,
            'Société': info['name'],
            'Prix (RUB)': f"₽{info['price']:,.2f}",
            'Variation': info['change'],
            'Variation %': f"{info['change']:+.2f}%",
            'Volume': f"{info['volume']:,}",
            'Cap. Marché': f"₽{info['market_cap']/1e9:.2f}B"
        }
        for sym, info in stocks.items()
    ])
    
    # Trier par variation
    df_stocks = df_stocks.sort_values('Variation', ascending=False)
    
    # Colorer les variations
    def color_variation(val):
        if isinstance(val, str) and '%' in val:
            if '+' in val:
                return 'color: #00cc96'
            elif '-' in val:
                return 'color: #ef553b'
        return ''
    
    styled_df = df_stocks.style.applymap(color_variation, subset=['Variation %'])
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # =========================================================
    # SECTION 4: TOP GAINERS / LOSERS
    # =========================================================
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("📈 Top 5 Hausses")
        gainers = df_stocks.head(5)
        for _, row in gainers.iterrows():
            st.markdown(f"""
            <div style="background-color: #f0fff0; padding: 0.8rem; margin: 0.3rem 0; border-radius: 0.5rem; border-left: 4px solid #00cc96;">
                <b>{row['Société']}</b> ({row['Symbole']})<br>
                {row['Prix (RUB)']} | <span style="color: #00cc96;">{row['Variation %']}</span> | Vol: {row['Volume']}
            </div>
            """, unsafe_allow_html=True)
    
    with col_g2:
        st.subheader("📉 Top 5 Baisses")
        losers = df_stocks.tail(5).sort_values('Variation')
        for _, row in losers.iterrows():
            st.markdown(f"""
            <div style="background-color: #fff0f0; padding: 0.8rem; margin: 0.3rem 0; border-radius: 0.5rem; border-left: 4px solid #ef553b;">
                <b>{row['Société']}</b> ({row['Symbole']})<br>
                {row['Prix (RUB)']} | <span style="color: #ef553b;">{row['Variation %']}</span> | Vol: {row['Volume']}
            </div>
            """, unsafe_allow_html=True)
    
    # =========================================================
    # SECTION 5: GRAPHIQUE D'UN TITRE
    # =========================================================
    
    st.markdown("---")
    st.subheader("📊 Analyse détaillée")
    
    col_chart1, col_chart2 = st.columns([3, 1])
    
    with col_chart2:
        selected_symbol = st.selectbox(
            "Choisir une action",
            options=list(MOEXDataProvider.MOEX_STOCKS.keys()),
            format_func=lambda x: f"{x} - {MOEXDataProvider.MOEX_STOCKS[x]}"
        )
        
        # Période
        period = st.selectbox(
            "Période",
            options=["1j", "5j", "1m", "3m", "6m", "1a"],
            index=0
        )
        
        # Info rapide
        if selected_symbol in stocks:
            info = stocks[selected_symbol]
            st.metric("Prix actuel", f"₽{info['price']:,.2f}", f"{info['change']:+.2f}%")
            st.metric("Volume", f"{info['volume']:,}")
    
    with col_chart1:
        # Simuler des données historiques
        dates = pd.date_range(
            end=tz_manager.get_moscow_time(),
            periods=100,
            freq='D'
        )
        
        # Base price
        base_price = stocks[selected_symbol]['price'] if selected_symbol in stocks else 1000
        
        # Générer des prix réalistes
        returns = np.random.normal(0.001, 0.02, 100)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name=selected_symbol,
            line=dict(color='#0033A0', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 51, 160, 0.1)'
        ))
        
        # Ajouter moyenne mobile
        ma20 = pd.Series(prices).rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=dates,
            y=ma20,
            mode='lines',
            name='MA20',
            line=dict(color='orange', width=1, dash='dash')
        ))
        
        fig.update_layout(
            title=f"{selected_symbol} - {MOEXDataProvider.MOEX_STOCKS[selected_symbol]}",
            xaxis_title="Date",
            yaxis_title="Prix (RUB)",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================
    # SECTION 6: VOLUME PAR SECTEUR
    # =========================================================
    
    st.markdown("---")
    st.subheader("📊 Distribution par secteur")
    
    # Données simulées par secteur
    sectors = {
        'Finance': 25.5,
        'Pétrole & Gaz': 32.8,
        'Métaux & Mines': 18.3,
        'Technologie': 8.2,
        'Télécoms': 6.1,
        'Consommation': 5.1,
        'Électricité': 4.0
    }
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        # Pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(sectors.keys()),
            values=list(sectors.values()),
            hole=0.4,
            marker_colors=['#0033A0', '#D52B1E', '#FFD700', '#00cc96', '#ef553b', '#ab63fa', '#ffa15a']
        )])
        
        fig_pie.update_layout(
            title="Capitalisation par secteur (%)",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_p2:
        # Bar chart
        df_sectors = pd.DataFrame({
            'Secteur': list(sectors.keys()),
            'Capitalisation (Mds ₽)': [v * 10 for v in sectors.values()]
        })
        
        fig_bar = px.bar(
            df_sectors,
            x='Secteur',
            y='Capitalisation (Mds ₽)',
            color='Secteur',
            color_discrete_sequence=['#0033A0', '#D52B1E', '#FFD700', '#00cc96', '#ef553b', '#ab63fa', '#ffa15a']
        )
        
        fig_bar.update_layout(
            title="Capitalisation par secteur",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # =========================================================
    # SECTION 7: CONVERTISSEUR DE FUSEAU POUR MOEX
    # =========================================================
    
    st.markdown("---")
    st.subheader("🔄 Convertisseur MOEX - Tous fuseaux")
    
    col_conv1, col_conv2, col_conv3 = st.columns(3)
    
    with col_conv1:
        from_tz = st.selectbox(
            "Fuseau source",
            options=list(MOEXTimeZoneManager.UTC_OFFSETS.keys()),
            key="from_tz"
        )
        
        # Heure MOEX
        moex_hour = st.time_input("Heure MOEX", value=datetime.strptime("10:00", "%H:%M").time())
    
    with col_conv2:
        st.markdown("<br><h2 style='text-align: center;'>→</h2>", unsafe_allow_html=True)
    
    with col_conv3:
        to_tz = st.selectbox(
            "Fuseau cible",
            options=list(MOEXTimeZoneManager.UTC_OFFSETS.keys()),
            index=list(MOEXTimeZoneManager.UTC_OFFSETS.keys()).index('UTC-5'),
            key="to_tz"
        )
        
        # Calculer la conversion
        from_offset = MOEXTimeZoneManager.UTC_OFFSETS[from_tz]
        to_offset = MOEXTimeZoneManager.UTC_OFFSETS[to_tz]
        
        # Convertir
        moex_dt = datetime.combine(datetime.now().date(), moex_hour)
        converted_dt = moex_dt + timedelta(hours=to_offset - from_offset)
        
        st.metric(
            "Heure convertie",
            converted_dt.strftime("%H:%M"),
            delta=f"{to_tz}"
        )
        
        # Afficher la différence
        diff = to_offset - from_offset
        st.caption(f"Différence: {diff:+g} heures")
    
    # =========================================================
    # SECTION 8: CALENDRIER MOEX
    # =========================================================
    
    with st.expander("📅 Calendrier MOEX 2024"):
        st.markdown("""
        | Date | Jour férié |
        |------|------------|
        | 1-8 janvier | Nouvel An |
        | 7 janvier | Noël orthodoxe |
        | 23 février | Jour du défenseur de la patrie |
        | 8 mars | Journée internationale des femmes |
        | 1 mai | Fête du printemps et du travail |
        | 9 mai | Jour de la Victoire |
        | 12 juin | Jour de la Russie |
        | 4 novembre | Journée de l'unité nationale |
        
        **Horaires spéciaux:**
        - Dernier jour de l'année: Fermeture à 14:00
        - Veilles de jours fériés: Horaires normaux
        """)
    
    # =========================================================
    # FOOTER
    # =========================================================
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: gray; font-size: 0.8rem; padding: 1rem;">
        🇷🇺 MOEX Moscow Exchange - Dashboard Temps Réel<br>
        Dernière mise à jour: {tz_manager.get_moscow_time().strftime('%Y-%m-%d %H:%M:%S')} (heure Moscou)<br>
        Fuseaux disponibles: UTC-12 à UTC+14 | Heure de Moscou: UTC+3 (fixe)
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh option
    if st.checkbox("🔄 Actualisation automatique (30s)"):
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
