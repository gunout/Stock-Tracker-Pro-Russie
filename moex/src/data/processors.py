"""
Traitement et transformation des données MOEX
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Classe pour le traitement des données brutes MOEX"""
    
    @staticmethod
    def process_securities(df: pd.DataFrame) -> pd.DataFrame:
        """
        Traite la liste des actions
        
        Args:
            df: DataFrame brut des actions
            
        Returns:
            pd.DataFrame: Actions traitées
        """
        if df.empty:
            return df
        
        # Garder les colonnes pertinentes
        relevant_cols = ['SECID', 'SHORTNAME', 'LONGNAME', 'REGNUMBER', 
                        'ISIN', 'LOTSIZE', 'FACEVALUE']
        available_cols = [col for col in relevant_cols if col in df.columns]
        
        processed = df[available_cols].copy()
        
        # Nettoyer les noms
        if 'SHORTNAME' in processed.columns:
            processed['SHORTNAME'] = processed['SHORTNAME'].str.strip()
        
        return processed
    
    @staticmethod
    def process_market_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Traite les données de marché
        
        Args:
            df: DataFrame brut des données de marché
            
        Returns:
            pd.DataFrame: Données de marché traitées
        """
        if df.empty:
            return df
        
        # Colonnes d'intérêt
        keep_cols = ['SECID', 'LAST', 'CHANGE', 'CHANGEPCT', 'VOLT', 
                    'VALT', 'OPEN', 'LOW', 'HIGH', 'NUMTRADES']
        available_cols = [col for col in keep_cols if col in df.columns]
        
        processed = df[available_cols].copy()
        
        # Convertir en numériques
        numeric_cols = ['LAST', 'CHANGE', 'CHANGEPCT', 'VOLT', 
                       'VALT', 'OPEN', 'LOW', 'HIGH', 'NUMTRADES']
        for col in numeric_cols:
            if col in processed.columns:
                processed[col] = pd.to_numeric(processed[col], errors='coerce')
        
        return processed
    
    @staticmethod
    def process_candles(df: pd.DataFrame) -> pd.DataFrame:
        """
        Traite les données de bougies
        
        Args:
            df: DataFrame brut des bougies
            
        Returns:
            pd.DataFrame: Bougies traitées
        """
        if df.empty:
            return df
        
        # Renommer les colonnes
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'value': 'Value'
        }
        
        processed = df.rename(columns=column_mapping)
        
        # S'assurer que l'index est datetime
        if processed.index.name == 'begin':
            processed.index = pd.to_datetime(processed.index)
        
        return processed
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des indicateurs techniques
        
        Args:
            df: DataFrame avec colonnes Open, High, Low, Close, Volume
            
        Returns:
            pd.DataFrame: DataFrame avec indicateurs
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        # Moyennes mobiles
        if 'Close' in result.columns:
            result['MA20'] = result['Close'].rolling(window=20).mean()
            result['MA50'] = result['Close'].rolling(window=50).mean()
            result['MA200'] = result['Close'].rolling(window=200).mean()
        
        # RSI
        if 'Close' in result.columns:
            delta = result['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            result['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        if 'Close' in result.columns:
            result['BB_Middle'] = result['Close'].rolling(window=20).mean()
            bb_std = result['Close'].rolling(window=20).std()
            result['BB_Upper'] = result['BB_Middle'] + (bb_std * 2)
            result['BB_Lower'] = result['BB_Middle'] - (bb_std * 2)
        
        # Volume moyen
        if 'Volume' in result.columns:
            result['Volume_MA20'] = result['Volume'].rolling(window=20).mean()
        
        # Volatilité
        if 'Close' in result.columns:
            result['Volatility'] = result['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
        
        return result
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule différents types de rendements
        
        Args:
            df: DataFrame avec prix
            
        Returns:
            pd.DataFrame: DataFrame avec rendements
        """
        if df.empty or 'Close' not in df.columns:
            return df
        
        result = df.copy()
        
        # Rendements
        result['Daily_Return'] = result['Close'].pct_change()
        result['Log_Return'] = np.log(result['Close'] / result['Close'].shift(1))
        
        # Cumulés
        result['Cumulative_Return'] = (1 + result['Daily_Return']).cumprod() - 1
        
        return result
    
    @staticmethod
    def filter_by_date(
        df: pd.DataFrame, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filtre un DataFrame par date
        
        Args:
            df: DataFrame avec index datetime
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: DataFrame filtré
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        if start_date:
            result = result[result.index >= pd.Timestamp(start_date)]
        
        if end_date:
            result = result[result.index <= pd.Timestamp(end_date)]
        
        return result
    
    @staticmethod
    def resample_data(
        df: pd.DataFrame,
        rule: str,
        agg_dict: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Rééchantillonne les données à différentes fréquences
        
        Args:
            df: DataFrame avec index datetime
            rule: Règle de rééchantillonnage (ex: 'W' pour semaine)
            agg_dict: Dictionnaire d'agrégation personnalisé
            
        Returns:
            pd.DataFrame: Données rééchantillonnées
        """
        if df.empty:
            return df
        
        if agg_dict is None:
            agg_dict = {
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }
        
        # Garder seulement les colonnes existantes
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        return df.resample(rule).agg(agg_dict)