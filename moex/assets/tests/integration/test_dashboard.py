"""
Tests d'intégration pour le dashboard
"""
import pytest
from src.api.moex_client import MOEXClient
from src.data.processors import DataProcessor
import streamlit as st

class TestDashboardIntegration:
    """Tests d'intégration"""
    
    @pytest.fixture
    def client(self):
        """Fixture pour le client API"""
        return MOEXClient()
    
    def test_full_data_flow(self, client):
        """Test le flux complet des données"""
        # 1. Récupérer la liste des actions
        securities = client.get_securities()
        assert not securities.empty
        
        # 2. Prendre la première action
        first_ticker = securities['SECID'].iloc[0]
        
        # 3. Récupérer ses données de marché
        market_data = client.get_market_data(first_ticker)
        assert market_data is not None
        
        # 4. Récupérer les données historiques
        hist_data = client.get_candles(first_ticker, interval=24*60, limit=30)
        assert not hist_data.empty
        
        # 5. Traiter les données
        processed = DataProcessor.process_candles(hist_data)
        assert 'Close' in processed.columns
        
        # 6. Ajouter des indicateurs
        with_indicators = DataProcessor.add_technical_indicators(processed)
        assert 'MA20' in with_indicators.columns
    
    def test_error_handling(self, client):
        """Test la gestion d'erreur"""
        # Ticker invalide
        with pytest.raises(Exception):
            client.get_market_data('INVALID_TICKER')
    
    def test_rate_limiting_integration(self, client):
        """Test le rate limiting en conditions réelles"""
        import time
        
        start = time.time()
        # Faire plusieurs appels rapides
        for _ in range(3):
            client.get_securities()
        end = time.time()
        
        # Vérifier que le rate limiting a fonctionné
        assert end - start >= client.min_request_interval * 2