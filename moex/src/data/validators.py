"""
Validation des données MOEX
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional

class DataValidator:
    """Validation et nettoyage des données"""
    
    @staticmethod
    def validate_price_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valide les données de prix
        
        Args:
            df: DataFrame à valider
            
        Returns:
            Tuple[bool, List[str]]: (est_valide, liste_erreurs)
        """
        errors = []
        
        if df.empty:
            errors.append("DataFrame vide")
            return False, errors
        
        required_cols = ['Open', 'High', 'Low', 'Close']
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Colonne manquante: {col}")
        
        if errors:
            return False, errors
        
        # Vérifier les prix négatifs
        for col in required_cols:
            if (df[col] < 0).any():
                errors.append(f"Prix négatifs dans {col}")
        
        # Vérifier High >= Low
        if 'High' in df.columns and 'Low' in df.columns:
            if (df['High'] < df['Low']).any():
                errors.append("High < Low détecté")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_market_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valide les données de marché
        
        Args:
            df: DataFrame à valider
            
        Returns:
            Tuple[bool, List[str]]: (est_valide, liste_erreurs)
        """
        errors = []
        
        if df.empty:
            errors.append("DataFrame vide")
            return False, errors
        
        # Vérifier les colonnes essentielles
        essential_cols = ['SECID', 'LAST']
        for col in essential_cols:
            if col not in df.columns:
                errors.append(f"Colonne manquante: {col}")
        
        # Vérifier les valeurs aberrantes
        if 'LAST' in df.columns:
            if (df['LAST'] < 0).any():
                errors.append("Prix négatifs détectés")
            
            # Détection des outliers (prix > 10^6)
            outliers = df[df['LAST'] > 1_000_000]
            if not outliers.empty:
                errors.append(f"Prix anormalement élevés pour: {outliers['SECID'].tolist()}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les données (NaN, duplicates, etc.)
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            pd.DataFrame: DataFrame nettoyé
        """
        if df.empty:
            return df
        
        cleaned = df.copy()
        
        # Supprimer les duplicates
        cleaned = cleaned[~cleaned.index.duplicated(keep='first')]
        
        # Gérer les NaN
        numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Remplacer les NaN par forward fill puis backward fill
            cleaned[col] = cleaned[col].fillna(method='ffill').fillna(method='bfill')
        
        # Supprimer les lignes avec trop de NaN
        cleaned = cleaned.dropna(thresh=len(cleaned.columns) * 0.5)
        
        return cleaned
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, column: str, std_threshold: float = 3) -> pd.DataFrame:
        """
        Détecte les anomalies dans une colonne
        
        Args:
            df: DataFrame
            column: Nom de la colonne
            std_threshold: Seuil d'écart-type
            
        Returns:
            pd.DataFrame: Anomalies détectées
        """
        if df.empty or column not in df.columns:
            return pd.DataFrame()
        
        mean = df[column].mean()
        std = df[column].std()
        
        anomalies = df[np.abs(df[column] - mean) > std_threshold * std]
        
        return anomalies
    
    @staticmethod
    def check_consistency(df: pd.DataFrame) -> List[str]:
        """
        Vérifie la cohérence des données
        
        Args:
            df: DataFrame
            
        Returns:
            List[str]: Liste des incohérences
        """
        inconsistencies = []
        
        if df.empty:
            return ["DataFrame vide"]
        
        # Vérifier l'ordre chronologique
        if isinstance(df.index, pd.DatetimeIndex):
            if not df.index.is_monotonic_increasing:
                inconsistencies.append("Index non chronologique")
        
        # Vérifier les OHLC
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            if (df['High'] < df['Low']).any():
                inconsistencies.append("High < Low détecté")
            if (df['High'] < df['Close']).any() or (df['High'] < df['Open']).any():
                inconsistencies.append("High inférieur à Open/Close")
            if (df['Low'] > df['Close']).any() or (df['Low'] > df['Open']).any():
                inconsistencies.append("Low supérieur à Open/Close")
        
        return inconsistencies