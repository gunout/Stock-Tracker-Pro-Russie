"""
Endpoints de l'API MOEX ISS
Documentation: https://iss.moex.com/iss/reference/
"""

# URL de base
MOEX_BASE_URL = "https://iss.moex.com/iss"

class Endpoints:
    """Constantes des endpoints API"""
    
    # Actions et indices
    SECURITIES = "engines/stock/markets/shares/boards/{board}/securities.json"
    SECURITY_INFO = "securities/{ticker}.json"
    
    # Données de marché
    MARKET_DATA = "engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
    BOARD_SECURITIES = "engines/stock/markets/shares/boards/{board}/securities.json"
    
    # Données historiques
    CANDLES = "engines/stock/markets/shares/securities/{ticker}/candles.json"
    HISTORY = "history/engines/stock/markets/shares/securities/{ticker}.json"
    
    # Indices
    INDICES = "stat/engines/stock/markets/index/analytics/{index}.json"
    INDEX_SECURITIES = "stat/engines/stock/markets/index/securities/{index}.json"

class APIParams:
    """Paramètres standards pour les requêtes API"""
    
    # Paramètres de contrôle
    ISS_ONLY = 'iss.only'
    ISS_META = 'iss.meta'
    ISS_DATA = 'iss.data'
    ISS_JSON = 'iss.json'
    
    # Paramètres de pagination
    START = 'start'
    LIMIT = 'limit'
    
    # Paramètres de date
    FROM = 'from'
    TILL = 'till'
    DATE = 'date'
    
    # Langue
    LANG = 'lang'
