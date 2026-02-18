"""
Endpoints API MOEX
"""

MOEX_BASE_URL = "https://iss.moex.com/iss"

class Endpoints:
    """Endpoints principaux"""
    SECURITIES = "engines/stock/markets/shares/boards/{board}/securities.json"
    MARKET_DATA = "engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
    CANDLES = "engines/stock/markets/shares/securities/{ticker}/candles.json"
