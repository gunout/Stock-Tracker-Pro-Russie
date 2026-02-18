"""
Calcul des indicateurs techniques
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple

def add_moving_averages(df: pd.DataFrame, windows: list = [20, 50, 200]) -> pd.DataFrame:
    """
    Ajoute des moyennes mobiles
    
    Args:
        df: DataFrame avec colonne 'Close'
        windows: Liste des périodes
        
    Returns:
        pd.DataFrame: DataFrame avec MA
    """
    result = df.copy()
    
    for window in windows:
        if len(df) >= window:
            result[f'MA{window}'] = df['Close'].rolling(window=window).mean()
    
    return result

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Ajoute le RSI (Relative Strength Index)
    
    Args:
        df: DataFrame avec colonne 'Close'
        period: Période du RSI
        
    Returns:
        pd.DataFrame: DataFrame avec RSI
    """
    result = df.copy()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    result['RSI'] = 100 - (100 / (1 + rs))
    
    return result

def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std: int = 2) -> pd.DataFrame:
    """
    Ajoute les bandes de Bollinger
    
    Args:
        df: DataFrame avec colonne 'Close'
        period: Période de la moyenne mobile
        std: Nombre d'écarts-types
        
    Returns:
        pd.DataFrame: DataFrame avec bandes
    """
    result = df.copy()
    
    result['BB_Middle'] = df['Close'].rolling(window=period).mean()
    bb_std = df['Close'].rolling(window=period).std()
    result['BB_Upper'] = result['BB_Middle'] + (bb_std * std)
    result['BB_Lower'] = result['BB_Middle'] - (bb_std * std)
    
    return result

def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Ajoute le MACD (Moving Average Convergence Divergence)
    
    Args:
        df: DataFrame avec colonne 'Close'
        fast: Période rapide
        slow: Période lente
        signal: Période du signal
        
    Returns:
        pd.DataFrame: DataFrame avec MACD
    """
    result = df.copy()
    
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    result['MACD'] = exp1 - exp2
    result['MACD_Signal'] = result['MACD'].ewm(span=signal, adjust=False).mean()
    result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']
    
    return result

def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute des indicateurs basés sur le volume
    
    Args:
        df: DataFrame avec colonne 'Volume'
        
    Returns:
        pd.DataFrame: DataFrame avec indicateurs de volume
    """
    result = df.copy()
    
    if 'Volume' in df.columns:
        # Moyenne mobile du volume
        result['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        
        # Volume relatif
        result['Volume_Ratio'] = df['Volume'] / result['Volume_MA20']
        
        # Accumulation/Distribution
        if all(col in df.columns for col in ['Close', 'Low', 'High']):
            clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
            result['AD'] = clv * df['Volume']
            result['AD_MA'] = result['AD'].rolling(window=20).mean()
    
    return result

def add_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calcule la volatilité historique
    
    Args:
        df: DataFrame avec colonne 'Close'
        window: Fenêtre de calcul
        
    Returns:
        pd.DataFrame: DataFrame avec volatilité
    """
    result = df.copy()
    
    # Rendements journaliers
    returns = df['Close'].pct_change()
    
    # Volatilité historique (annualisée)
    result['Volatility'] = returns.rolling(window=window).std() * np.sqrt(252)
    
    return result

def add_support_resistance(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Identifie les niveaux de support et résistance
    
    Args:
        df: DataFrame avec colonnes 'High' et 'Low'
        window: Fenêtre de recherche
        
    Returns:
        pd.DataFrame: DataFrame avec niveaux
    """
    result = df.copy()
    
    # Plus hauts et plus bas sur la période
    result['Resistance'] = df['High'].rolling(window=window, center=True).max()
    result['Support'] = df['Low'].rolling(window=window, center=True).min()
    
    return result

def get_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule tous les indicateurs techniques
    
    Args:
        df: DataFrame avec OHLCV
        
    Returns:
        pd.DataFrame: DataFrame avec tous les indicateurs
    """
    result = df.copy()
    
    result = add_moving_averages(result)
    result = add_rsi(result)
    result = add_bollinger_bands(result)
    result = add_macd(result)
    result = add_volume_indicators(result)
    result = add_volatility(result)
    result = add_support_resistance(result)
    
    return result