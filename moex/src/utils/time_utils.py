"""
Utilitaires de gestion du temps
"""
from datetime import datetime, time
import pytz
from typing import Tuple
from .constants import MOSCOW_TZ, UTC4_OFFSET, MOEX_OPEN_TIME, MOEX_CLOSE_TIME, RUSSIAN_HOLIDAYS_2024

# Fuseaux horaires
MOSCOW_TZ = pytz.timezone(MOSCOW_TZ)
UTC4_TZ = pytz.FixedOffset(UTC4_OFFSET)

def get_moscow_time() -> datetime:
    """Retourne l'heure actuelle à Moscou"""
    return datetime.now(MOSCOW_TZ)

def get_utc4_time() -> datetime:
    """Retourne l'heure actuelle en UTC+4"""
    return datetime.now(UTC4_TZ)

def convert_to_utc4(dt: datetime) -> datetime:
    """Convertit une date en UTC+4"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(UTC4_TZ)

def get_market_status() -> Tuple[str, str]:
    """
    Détermine le statut du marché MOEX
    
    Returns:
        Tuple[str, str]: (statut, emoji)
    """
    moscow_now = get_moscow_time()
    moscow_date = moscow_now.strftime('%Y-%m-%d')
    moscow_weekday = moscow_now.weekday()
    current_time = moscow_now.time()
    
    # Weekend
    if moscow_weekday >= 5:  # 5 = samedi, 6 = dimanche
        return "Fermé (weekend)", "🔴"
    
    # Jours fériés
    if moscow_date in RUSSIAN_HOLIDAYS_2024:
        return "Fermé (jour férié)", "🔴"
    
    # Vérifier les horaires d'ouverture
    if (current_time >= MOEX_OPEN_TIME and current_time <= MOEX_CLOSE_TIME):
        return "Ouvert", "🟢"
    else:
        return "Fermé", "🔴"

def is_market_open() -> bool:
    """Vérifie si le marché est ouvert"""
    status, _ = get_market_status()
    return status == "Ouvert"

def get_time_until_open() -> str:
    """Calcule le temps restant avant l'ouverture"""
    if is_market_open():
        return "Marché ouvert"
    
    now = get_moscow_time()
    next_open = now.replace(
        hour=MOEX_OPEN_TIME.hour,
        minute=MOEX_OPEN_TIME.minute,
        second=0,
        microsecond=0
    )
    
    if now.time() > MOEX_CLOSE_TIME:
        next_open += timedelta(days=1)
    
    # Skip les weekends
    while next_open.weekday() >= 5:
        next_open += timedelta(days=1)
    
    time_until = next_open - now
    hours = time_until.seconds // 3600
    minutes = (time_until.seconds % 3600) // 60
    
    return f"Ouverture dans {hours}h {minutes}min"

def setup_timezone():
    """Configure le fuseau horaire par défaut"""
    # Cette fonction peut être utilisée pour initialiser les settings de timezone
    pass