"""
Client API MOEX - Version ultra-simplifiée
"""
import requests
import pandas as pd
from datetime import datetime, timedelta

class MOEXClient:
    """Client simple pour l'API MOEX"""
    
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
    
    def get_candles(self, ticker, interval=24, from_date=None, to_date=None, limit=100):
        """Récupère les données historiques"""
        url = f"{self.base_url}/engines/stock/markets/shares/securities/{ticker}/candles.json"
        
        params = {
            'interval': interval,
            'limit': limit,
            'iss.meta': 'off'
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['till'] = to_date
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'candles' not in data:
                return pd.DataFrame()
            
            candles = data['candles']
            
            # Extraction simple
            if isinstance(candles, dict) and 'columns' in candles and 'data' in candles:
                columns = candles['columns']
                # Si columns est une liste de strings
                if columns and isinstance(columns[0], str):
                    df = pd.DataFrame(candles['data'], columns=columns)
                    
                    # Convertir les colonnes importantes
                    if 'begin' in df.columns:
                        df['begin'] = pd.to_datetime(df['begin'])
                        df.set_index('begin', inplace=True)
                    
                    # Renommer pour standardiser
                    rename = {
                        'open': 'Open',
                        'high': 'High', 
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }
                    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
                    
                    return df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Erreur: {e}")
            return pd.DataFrame()
    
    def get_market_data(self, ticker):
        """Récupère les données de marché"""
        url = f"{self.base_url}/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        
        try:
            response = requests.get(url, params={'iss.meta': 'off'}, timeout=10)
            data = response.json()
            
            if 'marketdata' in data:
                market = data['marketdata']
                if isinstance(market, dict) and 'columns' in market and 'data' in market:
                    columns = market['columns']
                    if columns and isinstance(columns[0], str):
                        df = pd.DataFrame(market['data'], columns=columns)
                        return df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Erreur: {e}")
            return pd.DataFrame()
