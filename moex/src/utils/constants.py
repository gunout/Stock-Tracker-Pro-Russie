"""
Constantes globales de l'application
"""
from datetime import time

# Configuration de la page Streamlit
PAGE_CONFIG = {
    "page_title": "MOEX Dashboard - Bourse de Moscou",
    "page_icon": "🇷🇺",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Fuseaux horaires
MOSCOW_TZ = "Europe/Moscow"
UTC4_OFFSET = 240  # minutes

# Horaires de trading MOEX (heure de Moscou)
MOEX_OPEN_TIME = time(10, 0)  # 10:00 MSK
MOEX_CLOSE_TIME = time(18, 45)  # 18:45 MSK

# Jours fériés russes 2024
RUSSIAN_HOLIDAYS_2024 = [
    '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
    '2024-01-06', '2024-01-07', '2024-01-08', '2024-02-23', '2024-03-08',
    '2024-05-01', '2024-05-09', '2024-06-12', '2024-11-04', '2024-12-30',
    '2024-12-31',
]

# Mapping des secteurs
SECTOR_MAPPING = {
    'energy': 'Énergie',
    'finance': 'Finance',
    'metals': 'Métaux & Mines',
    'tech': 'Technologie',
    'telecom': 'Télécoms',
    'retail': 'Distribution',
    'transport': 'Transport',
    'chemical': 'Chimie'
}

# Configuration du cache
CACHE_TTL = {
    'securities': 3600,  # 1 heure
    'market_data': 10,    # 10 secondes
    'historical': 300,    # 5 minutes
    'indices': 60         # 1 minute
}

# Configuration email
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True
}