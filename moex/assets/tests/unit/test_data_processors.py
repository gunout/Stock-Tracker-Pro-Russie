"""
Tests unitaires pour les processeurs de données
"""
import pytest
import pandas as pd
import numpy as np
from src.data.processors import DataProcessor

class TestDataProcessor:
    """Tests pour DataProcessor"""
    
    @pytest.fixture
def sample_data(self):
        """Crée un échantillon de données"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'Open': np.random.uniform(100, 110, 100),
            'High': np.random.uniform(105, 115, 100),
            'Low': np.random.uniform(95, 105, 100),
            'Close': np.random.uniform(100, 110, 100),
            'Volume': np.random.randint(1000000, 2000000, 100)
        }, index=dates)
    
    def test_process_securities(self):
        """Test le traitement des actions"""
        df = pd.DataFrame({
            'SECID': ['SBER', 'GAZP'],
            'SHORTNAME': ['Sberbank', 'Gazprom'],
            'LONGNAME': ['Sberbank of Russia', 'Gazprom PJSC'],
            'REGNUMBER': ['123', '456'],
            'EXTRA_COL': ['x', 'y']
        })
        
        processed = DataProcessor.process_securities(df)
        
        assert 'EXTRA_COL' not in processed.columns
        assert len(processed.columns) == 5
    
    def test_process_market_data(self):
        """Test le traitement des données de marché"""
        df = pd.DataFrame({
            'SECID': ['SBER'],
            'LAST': ['280.5'],
            'CHANGE': ['+5.2'],
            'VOLT': ['1000000']
        })
        
        processed = DataProcessor.process_market_data(df)
        
        assert processed['LAST'].dtype == float
        assert processed['VOLT'].dtype == float
    
    def test_process_candles(self, sample_data):
        """Test le traitement des bougies"""
        # Renommer pour simuler les données brutes
        df = sample_data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close'
        })
        
        processed = DataProcessor.process_candles(df)
        
        assert 'Open' in processed.columns
        assert 'Close' in processed.columns
    
    def test_add_technical_indicators(self, sample_data):
        """Test l'ajout des indicateurs techniques"""
        result = DataProcessor.add_technical_indicators(sample_data)
        
        assert 'MA20' in result.columns
        assert 'RSI' in result.columns
        assert 'BB_Upper' in result.columns
        assert 'Volume_MA20' in result.columns
    
    def test_calculate_returns(self, sample_data):
        """Test le calcul des rendements"""
        result = DataProcessor.calculate_returns(sample_data)
        
        assert 'Daily_Return' in result.columns
        assert 'Log_Return' in result.columns
        assert 'Cumulative_Return' in result.columns
    
    def test_filter_by_date(self, sample_data):
        """Test le filtrage par date"""
        start = '2024-01-10'
        end = '2024-01-20'
        
        filtered = DataProcessor.filter_by_date(sample_data, start, end)
        
        assert filtered.index[0] >= pd.Timestamp(start)
        assert filtered.index[-1] <= pd.Timestamp(end)
    
    def test_resample_data(self, sample_data):
        """Test le rééchantillonnage"""
        # Rééchantillonnage hebdomadaire
        weekly = DataProcessor.resample_data(sample_data, 'W')
        
        assert len(weekly) < len(sample_data)
        assert weekly.index.freqstr == 'W'