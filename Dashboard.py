import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from pytz import timezone
import plotly.graph_objs as go
from zoneinfo import ZoneInfo  # Python 3.9+

# ============================================================================
# CONFIGURATION COMPLÈTE DES FUSEAUX HORAIRES
# ============================================================================

class TimezoneManager:
    """Gestionnaire complet des fuseaux horaires"""
    
    # Tous les fuseaux UTC de -12 à +14
    UTC_OFFSETS = {
        'UTC-12': -12, 'UTC-11': -11, 'UTC-10': -10, 'UTC-9': -9, 'UTC-8': -8,
        'UTC-7': -7, 'UTC-6': -6, 'UTC-5': -5, 'UTC-4': -4, 'UTC-3': -3,
        'UTC-2': -2, 'UTC-1': -1, 'UTC±0': 0, 'UTC+1': 1, 'UTC+2': 2,
        'UTC+3': 3, 'UTC+4': 4, 'UTC+5': 5, 'UTC+5:30': 5.5, 'UTC+5:45': 5.75,
        'UTC+6': 6, 'UTC+6:30': 6.5, 'UTC+7': 7, 'UTC+8': 8, 'UTC+8:45': 8.75,
        'UTC+9': 9, 'UTC+9:30': 9.5, 'UTC+10': 10, 'UTC+10:30': 10.5,
        'UTC+11': 11, 'UTC+12': 12, 'UTC+13': 13, 'UTC+14': 14
    }
    
    # Mapping des fuseaux IANA principaux
    IANA_TIMEZONES = {
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
        'UTC±0': 'Europe/London',
        'UTC+1': 'Europe/Paris',
        'UTC+2': 'Europe/Helsinki',
        'UTC+3': 'Europe/Moscow',
        'UTC+3:30': 'Asia/Tehran',
        'UTC+4': 'Asia/Dubai',
        'UTC+4:30': 'Asia/Kabul',
        'UTC+5': 'Asia/Karachi',
        'UTC+5:30': 'Asia/Kolkata',
        'UTC+5:45': 'Asia/Kathmandu',
        'UTC+6': 'Asia/Dhaka',
        'UTC+6:30': 'Asia/Rangoon',
        'UTC+7': 'Asia/Bangkok',
        'UTC+8': 'Asia/Shanghai',
        'UTC+8:45': 'Australia/Eucla',
        'UTC+9': 'Asia/Tokyo',
        'UTC+9:30': 'Australia/Darwin',
        'UTC+10': 'Australia/Sydney',
        'UTC+10:30': 'Australia/Lord_Howe',
        'UTC+11': 'Pacific/Noumea',
        'UTC+12': 'Pacific/Auckland',
        'UTC+13': 'Pacific/Apia',
        'UTC+14': 'Pacific/Kiritimati'
    }
    
    # Grandes villes par fuseau
    MAJOR_CITIES = {
        'UTC-10': 'Honolulu',
        'UTC-8': 'Los Angeles, San Francisco',
        'UTC-7': 'Denver, Phoenix',
        'UTC-6': 'Chicago, Mexico',
        'UTC-5': 'New York, Toronto, Bogota',
        'UTC-4': 'Santiago, Caracas',
        'UTC-3': 'Buenos Aires, São Paulo',
        'UTC±0': 'Londres, Dublin, Lisbonne',
        'UTC+1': 'Paris, Berlin, Rome, Madrid',
        'UTC+2': 'Helsinki, Le Caire, Johannesburg',
        'UTC+3': 'Moscou, Istanbul, Riyad',
        'UTC+3:30': 'Téhéran',
        'UTC+4': 'Dubaï, Bakou',
        'UTC+5': 'Karachi, Tachkent',
        'UTC+5:30': 'Mumbai, New Delhi',
        'UTC+6': 'Dhaka',
        'UTC+7': 'Bangkok, Jakarta',
        'UTC+8': 'Shanghai, Singapour, Perth',
        'UTC+9': 'Tokyo, Séoul',
        'UTC+9:30': 'Adélaïde',
        'UTC+10': 'Sydney, Melbourne',
        'UTC+11': 'Nouméa',
        'UTC+12': 'Auckland, Fidji'
    }
    
    # Bourses mondiales avec leurs fuseaux
    STOCK_EXCHANGES = {
        'MOEX (Moscou)': {'tz': 'Europe/Moscow', 'utc': 3, 'hours': '10:00-18:45'},
        'LSE (Londres)': {'tz': 'Europe/London', 'utc': 0, 'hours': '08:00-16:30'},
        'NYSE (New York)': {'tz': 'America/New_York', 'utc': -5, 'hours': '09:30-16:00'},
        'NASDAQ': {'tz': 'America/New_York', 'utc': -5, 'hours': '09:30-16:00'},
        'TSX (Toronto)': {'tz': 'America/Toronto', 'utc': -5, 'hours': '09:30-16:00'},
        'Euronext (Paris)': {'tz': 'Europe/Paris', 'utc': 1, 'hours': '09:00-17:30'},
        'Deutsche Börse': {'tz': 'Europe/Berlin', 'utc': 1, 'hours': '09:00-17:30'},
        'SIX (Zurich)': {'tz': 'Europe/Zurich', 'utc': 1, 'hours': '09:00-17:30'},
        'Bovespa (São Paulo)': {'tz': 'America/Sao_Paulo', 'utc': -3, 'hours': '10:00-17:30'},
        'HKEX (Hong Kong)': {'tz': 'Asia/Hong_Kong', 'utc': 8, 'hours': '09:30-16:00'},
        'SSE (Shanghai)': {'tz': 'Asia/Shanghai', 'utc': 8, 'hours': '09:30-15:00'},
        'TSE (Tokyo)': {'tz': 'Asia/Tokyo', 'utc': 9, 'hours': '09:00-15:00'},
        'ASX (Sydney)': {'tz': 'Australia/Sydney', 'utc': 10, 'hours': '10:00-16:00'},
        'JSE (Johannesburg)': {'tz': 'Africa/Johannesburg', 'utc': 2, 'hours': '09:00-17:00'}
    }
    
    @staticmethod
    def get_all_timezones():
        """Retourne tous les fuseaux disponibles"""
        return sorted(TimezoneManager.UTC_OFFSETS.keys())
    
    @staticmethod
    def convert_time(dt, from_tz, to_tz):
        """Convertit une heure entre fuseaux"""
        if isinstance(from_tz, str):
            from_tz = pytz.timezone(from_tz)
        if isinstance(to_tz, str):
            to_tz = pytz.timezone(to_tz)
        
        if dt.tzinfo is None:
            dt = from_tz.localize(dt)
        
        return dt.astimezone(to_tz)
    
    @staticmethod
    def get_current_time_in_utc(utc_offset):
        """Heure actuelle dans un fuseau UTC spécifique"""
        utc_now = datetime.now(pytz.UTC)
        return utc_now + timedelta(hours=utc_offset)
    
    @staticmethod
    def format_time_for_display(dt, format="%H:%M:%S"):
        """Formate l'heure pour affichage"""
        return dt.strftime(format)
    
    @staticmethod
    def get_market_hours_in_timezone(exchange, target_tz):
        """Convertit les heures de marché dans un fuseau cible"""
        exchange_info = TimezoneManager.STOCK_EXCHANGES.get(exchange)
        if not exchange_info:
            return None
        
        exchange_tz = timezone(exchange_info['tz'])
        today = datetime.now(exchange_tz).date()
        
        # Heures d'ouverture/fermeture
        open_time = datetime.strptime(exchange_info['hours'].split('-')[0], '%H:%M').time()
        close_time = datetime.strptime(exchange_info['hours'].split('-')[1], '%H:%M').time()
        
        open_dt = exchange_tz.localize(datetime.combine(today, open_time))
        close_dt = exchange_tz.localize(datetime.combine(today, close_time))
        
        # Conversion
        target_tz = timezone(target_tz) if isinstance(target_tz, str) else target_tz
        open_local = open_dt.astimezone(target_tz)
        close_local = close_dt.astimezone(target_tz)
        
        return {
            'open': open_local.strftime('%H:%M'),
            'close': close_local.strftime('%H:%M'),
            'date': open_local.strftime('%Y-%m-%d')
        }

# ============================================================================
# COMPOSANT STREAMLIT POUR LA SÉLECTION DE FUSEAU
# ============================================================================

def timezone_selector(key="tz_selector"):
    """Sélecteur de fuseau horaire complet"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sélection par décalage UTC
        tz_options = TimezoneManager.get_all_timezones()
        selected_utc = st.selectbox(
            "🌐 Sélectionner un fuseau horaire",
            options=tz_options,
            index=tz_options.index('UTC+3'),  # Moscou par défaut
            key=f"{key}_utc"
        )
        
        # Afficher les grandes villes
        if selected_utc in TimezoneManager.MAJOR_CITIES:
            st.caption(f"🏙️ Villes: {TimezoneManager.MAJOR_CITIES[selected_utc]}")
    
    with col2:
        # Heure actuelle dans le fuseau sélectionné
        offset = TimezoneManager.UTC_OFFSETS[selected_utc]
        current_time = TimezoneManager.get_current_time_in_utc(offset)
        
        st.metric(
            "Heure locale",
            current_time.strftime("%H:%M:%S"),
            delta=f"UTC{offset:+g}" if offset != 0 else "UTC"
        )
        
        # Date
        st.caption(current_time.strftime("%d %B %Y"))
    
    return selected_utc, offset

def exchange_time_comparison():
    """Compare les heures des bourses mondiales"""
    
    st.subheader("🏦 Heures des bourses mondiales")
    
    # Sélectionner le fuseau de référence
    ref_tz = st.selectbox(
        "Fuseau de référence",
        options=list(TimezoneManager.STOCK_EXCHANGES.keys()),
        format_func=lambda x: f"{x} ({TimezoneManager.STOCK_EXCHANGES[x]['tz']})"
    )
    
    # Afficher le tableau comparatif
    data = []
    ref_info = TimezoneManager.STOCK_EXCHANGES[ref_tz]
    ref_tz_obj = timezone(ref_info['tz'])
    
    for exchange, info in TimezoneManager.STOCK_EXCHANGES.items():
        market_hours = TimezoneManager.get_market_hours_in_timezone(exchange, ref_tz_obj)
        if market_hours:
            # Statut du marché
            now_ref = datetime.now(ref_tz_obj)
            current_time_str = now_ref.strftime("%H:%M")
            
            is_open = market_hours['open'] <= current_time_str <= market_hours['close']
            status = "🟢 Ouvert" if is_open else "🔴 Fermé"
            
            data.append({
                'Bourse': exchange,
                'Fuseau': f"UTC{info['utc']:+g}",
                'Heure locale': market_hours['open'] + '-' + market_hours['close'],
                f'Heure ({ref_tz})': f"{market_hours['open']} - {market_hours['close']}",
                'Statut': status
            })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def world_clock_dashboard():
    """Dashboard des heures mondiales"""
    
    st.subheader("🕐 Horloges mondiales")
    
    # Sélectionner plusieurs villes
    cols = st.columns(4)
    major_cities = [
        ('New York', 'America/New_York', -5),
        ('Londres', 'Europe/London', 0),
        ('Paris', 'Europe/Paris', 1),
        ('Moscou', 'Europe/Moscow', 3),
        ('Dubai', 'Asia/Dubai', 4),
        ('Mumbai', 'Asia/Kolkata', 5.5),
        ('Shanghai', 'Asia/Shanghai', 8),
        ('Tokyo', 'Asia/Tokyo', 9),
        ('Sydney', 'Australia/Sydney', 10)
    ]
    
    for i, (city, tz_name, offset) in enumerate(major_cities):
        with cols[i % 4]:
            tz = timezone(tz_name)
            now = datetime.now(tz)
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                <b>{city}</b><br>
                <span style="font-size: 1.5rem;">{now.strftime('%H:%M')}</span><br>
                <span style="font-size: 0.8rem;">{now.strftime('%d/%m/%Y')}</span><br>
                <span style="font-size: 0.7rem;">UTC{offset:+g}</span>
            </div>
            """, unsafe_allow_html=True)

def market_countdown_timer():
    """Timer pour l'ouverture/fermeture du marché russe"""
    
    st.subheader("⏳ Compte à rebours MOEX")
    
    moscow_tz = timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    
    # Horaires MOEX
    open_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=18, minute=45, second=0, microsecond=0)
    
    # Ajuster pour le jour suivant si nécessaire
    if now > close_time:
        open_time = open_time + timedelta(days=1)
        close_time = close_time + timedelta(days=1)
    elif now < open_time:
        close_time = close_time  # même jour
    
    # Calculer les différences
    time_to_open = open_time - now if now < open_time else None
    time_to_close = close_time - now if open_time <= now <= close_time else None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if time_to_open and time_to_open.total_seconds() > 0:
            hours = int(time_to_open.total_seconds() // 3600)
            minutes = int((time_to_open.total_seconds() % 3600) // 60)
            seconds = int(time_to_open.total_seconds() % 60)
            st.metric("⏰ Prochaine ouverture", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            st.metric("⏰ Prochaine ouverture", "Marché ouvert")
    
    with col2:
        if time_to_close and time_to_close.total_seconds() > 0:
            hours = int(time_to_close.total_seconds() // 3600)
            minutes = int((time_to_close.total_seconds() % 3600) // 60)
            seconds = int(time_to_close.total_seconds() % 60)
            st.metric("🔔 Fermeture dans", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            st.metric("🔔 Fermeture dans", "Fermé")
    
    with col3:
        # Session en cours
        if open_time <= now <= close_time:
            session_progress = (now - open_time).total_seconds() / (close_time - open_time).total_seconds() * 100
            st.progress(session_progress / 100, text=f"Session: {session_progress:.1f}%")
        else:
            st.progress(0, text="Hors session")

def timezone_converter_tool():
    """Outil de conversion entre fuseaux"""
    
    st.subheader("🔄 Convertisseur de fuseaux horaires")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        from_tz = st.selectbox(
            "Fuseau source",
            options=TimezoneManager.get_all_timezones(),
            key="from_tz"
        )
        
        # Heure à convertir
        input_time = st.time_input("Heure", value=datetime.now().time())
        input_date = st.date_input("Date", value=datetime.now().date())
    
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>→</h1>", unsafe_allow_html=True)
    
    with col3:
        to_tz = st.selectbox(
            "Fuseau cible",
            options=TimezoneManager.get_all_timezones(),
            index=TimezoneManager.get_all_timezones().index('UTC+3'),
            key="to_tz"
        )
        
        # Effectuer la conversion
        dt = datetime.combine(input_date, input_time)
        from_offset = TimezoneManager.UTC_OFFSETS[from_tz]
        to_offset = TimezoneManager.UTC_OFFSETS[to_tz]
        
        # Conversion simple (sans DST)
        converted_dt = dt + timedelta(hours=to_offset - from_offset)
        
        st.metric(
            "Heure convertie",
            converted_dt.strftime("%H:%M:%S"),
            delta=f"{to_tz}"
        )
        st.caption(converted_dt.strftime("%d %B %Y"))

# ============================================================================
# INTÉGRATION DANS L'APPLICATION PRINCIPALE
# ============================================================================

def main():
    st.set_page_config(
        page_title="Gestionnaire de Fuseaux Horaires",
        page_icon="🕐",
        layout="wide"
    )
    
    st.title("🕐 Gestionnaire complet des fuseaux horaires")
    st.markdown("UTC-12 à UTC+14 · Tous les décalages")
    
    # Menu principal
    menu = st.sidebar.radio(
        "Navigation",
        ["🌍 Horloges mondiales",
         "🏦 Bourses internationales",
         "🔄 Convertisseur",
         "📊 Dashboard MOEX",
         "ℹ️ Informations"]
    )
    
    if menu == "🌍 Horloges mondiales":
        # Sélecteur principal
        selected_tz, offset = timezone_selector()
        
        # Dashboard des villes
        world_clock_dashboard()
        
        # Afficher tous les fuseaux
        with st.expander("📋 Tous les fuseaux UTC"):
            cols = st.columns(4)
            for i, (tz_name, offset_val) in enumerate(TimezoneManager.UTC_OFFSETS.items()):
                with cols[i % 4]:
                    current = TimezoneManager.get_current_time_in_utc(offset_val)
                    st.write(f"**{tz_name}**: {current.strftime('%H:%M:%S')}")
    
    elif menu == "🏦 Bourses internationales":
        exchange_time_comparison()
        
        # Carte thermique des heures d'ouverture
        st.subheader("🌡️ Carte thermique des ouvertures")
        
        # Créer des données pour les 24h
        hours = list(range(24))
        exchanges = list(TimezoneManager.STOCK_EXCHANGES.keys())
        
        open_matrix = []
        for exchange in exchanges:
            row = []
            info = TimezoneManager.STOCK_EXCHANGES[exchange]
            tz = timezone(info['tz'])
            
            for hour in hours:
                # Vérifier si la bourse est ouverte à cette heure UTC
                utc_time = datetime.now(pytz.UTC).replace(hour=hour, minute=0)
                local_time = utc_time.astimezone(tz)
                
                open_hour = int(info['hours'].split('-')[0].split(':')[0])
                close_hour = int(info['hours'].split('-')[1].split(':')[0])
                
                is_open = open_hour <= local_time.hour < close_hour
                row.append(1 if is_open else 0)
            
            open_matrix.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=open_matrix,
            x=[f"{h:02d}:00" for h in hours],
            y=exchanges,
            colorscale=[[0, 'red'], [1, 'green']],
            showscale=False
        ))
        
        fig.update_layout(
            title="Périodes d'ouverture (UTC)",
            xaxis_title="Heure UTC",
            yaxis_title="Bourse",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif menu == "🔄 Convertisseur":
        timezone_converter_tool()
        
        # Table de conversion rapide
        with st.expander("📊 Table de conversion rapide"):
            base_tz = st.selectbox(
                "Fuseau de base",
                options=TimezoneManager.get_all_timezones(),
                index=TimezoneManager.get_all_timezones().index('UTC±0')
            )
            
            base_offset = TimezoneManager.UTC_OFFSETS[base_tz]
            base_time = datetime.now().replace(hour=12, minute=0)
            
            data = []
            for tz_name, offset in TimezoneManager.UTC_OFFSETS.items():
                converted = base_time + timedelta(hours=offset - base_offset)
                data.append({
                    'Fuseau': tz_name,
                    'Décalage': f"{offset:+g}" if offset != 0 else "0",
                    'Heure (midi base)': converted.strftime('%H:%M'),
                    'Villes': TimezoneManager.MAJOR_CITIES.get(tz_name, '')
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
    
    elif menu == "📊 Dashboard MOEX":
        st.header("🇷🇺 Moscow Exchange (MOEX)")
        
        # Compte à rebours
        market_countdown_timer()
        
        # Informations MOEX
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Heures MOEX")
            moscow_tz = timezone('Europe/Moscow')
            now_moscow = datetime.now(moscow_tz)
            
            st.write(f"**Heure actuelle (Moscou)**: {now_moscow.strftime('%H:%M:%S')}")
            st.write("**Session principale**: 10:00 - 18:45 (UTC+3)")
            st.write("**Session du soir**: 19:05 - 23:50 (certains instruments)")
            st.write("**Week-end**: Fermé")
        
        with col2:
            st.subheader("Conversion dans votre fuseau")
            user_tz, _ = timezone_selector(key="moex_tz")
            user_offset = TimezoneManager.UTC_OFFSETS[user_tz]
            
            # Convertir les heures MOEX
            moex_open_local = (datetime.now().replace(hour=10, minute=0) + 
                              timedelta(hours=user_offset - 3)).strftime('%H:%M')
            moex_close_local = (datetime.now().replace(hour=18, minute=45) + 
                               timedelta(hours=user_offset - 3)).strftime('%H:%M')
            
            st.write(f"**Ouverture locale**: {moex_open_local}")
            st.write(f"**Fermeture locale**: {moex_close_local}")
    
    elif menu == "ℹ️ Informations":
        st.header("ℹ️ À propos des fuseaux horaires")
        
        st.markdown("""
        ### 📚 Guide des fuseaux horaires
        
        #### UTC (Temps Universel Coordonné)
        - Référence internationale
        - Ne change pas avec les saisons
        - Base pour tous les autres fuseaux
        
        #### Décalages courants
        - **UTC-5**: Heure de l'Est (New York)
        - **UTC±0**: UTC (Londres)
        - **UTC+1**: Heure d'Europe centrale (Paris)
        - **UTC+2**: Heure d'Europe de l'Est (Helsinki)
        - **UTC+3**: Heure de Moscou
        - **UTC+5:30**: Heure de l'Inde
        - **UTC+8**: Heure de Chine
        - **UTC+9**: Heure du Japon
        
        #### Heure d'été
        Certains pays ajustent leur heure en été:
        - Europe: Dernier dimanche de mars au dernier dimanche d'octobre
        - USA: Deuxième dimanche de mars au premier dimanche de novembre
        - Russie: N'observe plus l'heure d'été depuis 2014
        
        #### Bourse de Moscou (MOEX)
        - Fuseau: UTC+3 (constant, pas d'heure d'été)
        - Horaires: 10:00 - 18:45
        - Jours ouverts: Lundi-Vendredi
        """)

if __name__ == "__main__":
    main()
