"""
Client principal pour l'API MOEX ISS
Documentation: https://iss.moex.com/iss/reference/
"""
import requests
import pandas as pd
import time
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from .exceptions import MOEXAPIError, MOEXRateLimitError
from .endpoints import Endpoints, MOEX_BASE_URL
from ..utils.cache_manager import cache

logger = logging.getLogger(__name__)

class MOEXClient:
    """
    Client pour interagir avec l'API MOEX ISS
    """
    
    def __init__(self, base_url: str = MOEX_BASE_URL, timeout: int = 30):
        """
        Initialise le client MOEX
        
        Args:
            base_url: URL de base de l'API
            timeout: Timeout des requêtes en secondes
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MOEX-Dashboard/1.0)',
            'Accept': 'application/json'
        })
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms minimum entre requêtes
        
    def _rate_limit(self):
        """Applique le rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Effectue une requête à l'API avec gestion d'erreur
        
        Args:
            endpoint: Endpoint API
            params: Paramètres de la requête
            
        Returns:
            Dict: Réponse JSON de l'API
        """
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        default_params = {
            'iss.meta': 'off',
            'iss.only': 'data',
            'lang': 'ru'
        }
        
        if params:
            default_params.update(params)
        
        try:
            logger.debug(f"Requête API: {url}")
            response = self.session.get(
                url, 
                params=default_params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Vérifier les limites de taux
            if response.status_code == 429:
                raise MOEXRateLimitError("Rate limit atteint")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise MOEXAPIError("Timeout de la requête")
        except requests.exceptions.ConnectionError:
            raise MOEXAPIError("Erreur de connexion")
        except requests.exceptions.HTTPError as e:
            raise MOEXAPIError(f"Erreur HTTP: {e}")
        except ValueError as e:
            raise MOEXAPIError(f"Erreur de parsing JSON: {e}")
    
    def _parse_response(self, data: Dict, block_name: str) -> pd.DataFrame:
        """
        Parse la réponse MOEX en DataFrame
        
        Args:
            data: Réponse JSON
            block_name: Nom du bloc de données
            
        Returns:
            pd.DataFrame: Données formatées
        """
        if block_name not in data:
            return pd.DataFrame()
        
        block = data[block_name]
        
        if 'columns' not in block or 'data' not in block:
            return pd.DataFrame()
        
        columns = [col['name'] for col in block['columns']]
        rows = block['data']
        
        return pd.DataFrame(rows, columns=columns)
    
    @cache(ttl=60)
    def get_securities(self, board: str = "TQBR") -> pd.DataFrame:
        """
        Récupère la liste des actions d'un board
        
        Args:
            board: Code du board (TQBR pour actions principales)
            
        Returns:
            pd.DataFrame: Liste des actions
        """
        endpoint = Endpoints.SECURITIES.format(board=board)
        data = self._make_request(endpoint)
        return self._parse_response(data, 'securities')
    
    @cache(ttl=300)
    def get_security_info(self, ticker: str) -> Dict[str, Any]:
        """
        Récupère les informations détaillées sur une action
        
        Args:
            ticker: Code de l'action (ex: SBER)
            
        Returns:
            Dict: Informations sur l'action
        """
        endpoint = Endpoints.SECURITY_INFO.format(ticker=ticker)
        data = self._make_request(endpoint)
        
        # Combiner les différentes sections
        result = {}
        for section in ['description', 'boards', 'dataversion']:
            if section in data:
                df = self._parse_response(data, section)
                if not df.empty:
                    result[section] = df.to_dict('records')
        
        return result
    
    @cache(ttl=10)
    def get_market_data(self, ticker: str) -> pd.DataFrame:
        """
        Récupère les données de marché en temps réel
        
        Args:
            ticker: Code de l'action
            
        Returns:
            pd.DataFrame: Données de marché
        """
        endpoint = Endpoints.MARKET_DATA.format(ticker=ticker)
        data = self._make_request(endpoint)
        return self._parse_response(data, 'marketdata')
    
    @cache(ttl=3600)
    def get_candles(
        self, 
        ticker: str, 
        interval: int = 24,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Récupère les données historiques (bougies)
        
        Args:
            ticker: Code de l'action
            interval: Intervalle en minutes (1, 10, 60, 24*60)
            from_date: Date de début (YYYY-MM-DD)
            to_date: Date de fin (YYYY-MM-DD)
            limit: Nombre maximum de bougies
            
        Returns:
            pd.DataFrame: Données historiques
        """
        params = {
            'interval': interval,
            'limit': limit
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['till'] = to_date
        
        endpoint = Endpoints.CANDLES.format(ticker=ticker)
        data = self._make_request(endpoint, params)
        
        df = self._parse_response(data, 'candles')
        if not df.empty and 'begin' in df.columns:
            df['begin'] = pd.to_datetime(df['begin'])
            df.set_index('begin', inplace=True)
        
        return df
    
    @cache(ttl=60)
    def get_board_securities(self, board: str = "TQBR") -> pd.DataFrame:
        """
        Récupère toutes les actions d'un board avec leurs prix
        
        Args:
            board: Code du board
            
        Returns:
            pd.DataFrame: Actions avec prix
        """
        endpoint = Endpoints.BOARD_SECURITIES.format(board=board)
        data = self._make_request(endpoint)
        return self._parse_response(data, 'marketdata')
    
    def search_securities(self, query: str) -> pd.DataFrame:
        """
        Recherche des actions par nom ou code
        
        Args:
            query: Terme de recherche
            
        Returns:
            pd.DataFrame: Résultats de recherche
        """
        all_securities = self.get_securities()
        if all_securities.empty:
            return pd.DataFrame()
        
        # Recherche insensible à la casse
        mask = (
            all_securities['SECID'].str.contains(query, case=False, na=False) |
            all_securities['SHORTNAME'].str.contains(query, case=False, na=False)
        )
        return all_securities[mask]
    
    def get_top_gainers(self, limit: int = 10) -> pd.DataFrame:
        """
        Récupère les plus fortes hausses
        
        Args:
            limit: Nombre de résultats
            
        Returns:
            pd.DataFrame: Top hausses
        """
        market_data = self.get_board_securities()
        if market_data.empty:
            return pd.DataFrame()
        
        if 'CHANGE' in market_data.columns:
            return market_data.nlargest(limit, 'CHANGE')
        return pd.DataFrame()
    
    def get_top_losers(self, limit: int = 10) -> pd.DataFrame:
        """
        Récupère les plus fortes baisses
        
        Args:
            limit: Nombre de résultats
            
        Returns:
            pd.DataFrame: Top baisses
        """
        market_data = self.get_board_securities()
        if market_data.empty:
            return pd.DataFrame()
        
        if 'CHANGE' in market_data.columns:
            return market_data.nsmallest(limit, 'CHANGE')
        return pd.DataFrame()