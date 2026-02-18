"""
Client pour l'API MOEX ISS - Version robuste avec gestion de tous les formats
"""
import requests
import pandas as pd
import time
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MOEXClient:
    """
    Client robuste pour l'API MOEX ISS
    """
    
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.last_request_time = 0
        self.min_interval = 1.0  # 1 seconde entre requêtes
    
    def _rate_limit(self):
        """Rate limiting simple"""
        current = time.time()
        elapsed = current - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Effectue une requête HTTP"""
        self._rate_limit()
        
        default_params = {'iss.meta': 'off'}
        if params:
            default_params.update(params)
        
        try:
            response = self.session.get(url, params=default_params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erreur requête: {e}")
            return None
    
    def _extract_dataframe(self, data: Dict, block_name: str) -> pd.DataFrame:
        """
        Extrait un DataFrame de la réponse MOEX - Gère tous les formats possibles
        """
        if not data or block_name not in data:
            return pd.DataFrame()
        
        block = data[block_name]
        
        # Si le bloc n'est pas un dictionnaire
        if not isinstance(block, dict):
            return pd.DataFrame()
        
        # Vérifier la présence des données
        if 'columns' not in block or 'data' not in block:
            return pd.DataFrame()
        
        # Extraire les colonnes - Gestion des différents formats
        columns_raw = block['columns']
        data_raw = block['data']
        
        # Cas 1: columns est une liste de dictionnaires avec 'name'
        if columns_raw and isinstance(columns_raw[0], dict):
            columns = [col['name'] for col in columns_raw]
        # Cas 2: columns est une liste de chaînes
        elif columns_raw and isinstance(columns_raw[0], str):
            columns = columns_raw
        else:
            logger.warning(f"Format de colonnes non reconnu: {type(columns_raw)}")
            return pd.DataFrame()
        
        # Créer le DataFrame
        try:
            df = pd.DataFrame(data_raw, columns=columns)
            
            # Conversion automatique des types numériques
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
            
            return df
        except Exception as e:
            logger.error(f"Erreur création DataFrame: {e}")
            return pd.DataFrame()
    
    def get_candles(self, ticker: str, interval: int = 24, 
                   from_date: Optional[str] = None,
                   to_date: Optional[str] = None,
                   limit: int = 100) -> pd.DataFrame:
        """
        Récupère les données historiques (bougies)
        
        Args:
            ticker: Code de l'action (ex: SBER)
            interval: Intervalle en minutes (1, 10, 60, 24*60)
            from_date: Date début (YYYY-MM-DD)
            to_date: Date fin (YYYY-MM-DD)
            limit: Nombre max de bougies
            
        Returns:
            pd.DataFrame: Données historiques
        """
        url = f"{self.base_url}/engines/stock/markets/shares/securities/{ticker}/candles.json"
        
        params = {
            'interval': interval,
            'limit': limit
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['till'] = to_date
        
        data = self._make_request(url, params)
        df = self._extract_dataframe(data, 'candles')
        
        if not df.empty and 'begin' in df.columns:
            df['begin'] = pd.to_datetime(df['begin'])
            df.set_index('begin', inplace=True)
            
            # Renommer les colonnes pour standardiser
            rename_map = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        return df
    
    def get_market_data(self, ticker: str) -> pd.DataFrame:
        """
        Récupère les données de marché en temps réel
        
        Args:
            ticker: Code de l'action
            
        Returns:
            pd.DataFrame: Données de marché
        """
        url = f"{self.base_url}/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        
        data = self._make_request(url)
        return self._extract_dataframe(data, 'marketdata')
    
    def get_securities(self, board: str = "TQBR") -> pd.DataFrame:
        """
        Récupère la liste des actions
        
        Args:
            board: Code du board (TQBR pour actions principales)
            
        Returns:
            pd.DataFrame: Liste des actions
        """
        url = f"{self.base_url}/engines/stock/markets/shares/boards/{board}/securities.json"
        
        data = self._make_request(url)
        return self._extract_dataframe(data, 'securities')
    
    def search_securities(self, query: str) -> pd.DataFrame:
        """
        Recherche des actions par nom ou code
        
        Args:
            query: Terme de recherche
            
        Returns:
            pd.DataFrame: Résultats de recherche
        """
        df = self.get_securities()
        if df.empty:
            return df
        
        # Recherche textuelle
        mask = pd.Series([False] * len(df))
        
        if 'SECID' in df.columns:
            mask |= df['SECID'].str.contains(query, case=False, na=False)
        if 'SHORTNAME' in df.columns:
            mask |= df['SHORTNAME'].str.contains(query, case=False, na=False)
        if 'LONGNAME' in df.columns:
            mask |= df['LONGNAME'].str.contains(query, case=False, na=False)
        
        return df[mask]
