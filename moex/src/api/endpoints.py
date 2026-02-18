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
    INDICES = "stat/engines/stock/markers/index/analytics/{index}.json"
    INDEX_SECURITIES = "stat/engines/stock/markets/index/securities/{index}.json"
    
    # Ordres de marché
    ORDERBOOK = "engines/stock/markets/shares/boards/TQBR/securities/{ticker}/orderbook.json"
    TRADES = "engines/stock/markets/shares/boards/TQBR/securities/{ticker}/trades.json"
    
    # Statistiques et turnover
    TURNOVERS = "engines/stock/markets/shares/securities/{ticker}/turnovers.json"
    
    # Référentiels
    BOARDS = "index/boards.json"
    ENGINE = "engines/stock.json"
    MARKETS = "engines/stock/markets.json"
    
    # Formats de réponse disponibles
    FORMATS = {
        'json': '.json',
        'xml': '.xml',
        'csv': '.csv',
        'html': '.html'
    }
    
    # Intervalles pour les bougies (en minutes)
    CANDLE_INTERVALS = {
        1: '1 minute',
        10: '10 minutes',
        60: '1 heure',
        24*60: '1 jour',
        7*24*60: '1 semaine',
        30*24*60: '1 mois'
    }
    
    # Boards principaux
    BOARDS = {
        'TQBR': 'Actions ordinaires',
        'TQPI': 'Actions privilégiées',
        'TQTF': 'ETF',
        'TQTD': 'DR'
    }

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
    
    # Formats
    FORMAT = 'format'