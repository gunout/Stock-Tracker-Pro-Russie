"""
Tests unitaires pour le client API MOEX
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.api.moex_client import MOEXClient
from src.api.exceptions import MOEXAPIError

class TestMOEXClient:
    """Tests pour MOEXClient"""
    
    @pytest.fixture
    def client(self):
        """Fixture pour créer un client"""
        return MOEXClient()
    
    def test_init(self, client):
        """Test l'initialisation du client"""
        assert client.base_url == "https://iss.moex.com/iss"
        assert client.timeout == 30
        assert client.session is not None
    
    @patch('requests.Session.get')
    def test_get_securities_success(self, mock_get, client):
        """Test la récupération des actions avec succès"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'securities': {
                'columns': [{'name': 'SECID'}, {'name': 'SHORTNAME'}],
                'data': [['SBER', 'Sberbank'], ['GAZP', 'Gazprom']]
            }
        }
        mock_get.return_value = mock_response
        
        # Appel
        df = client.get_securities()
        
        # Vérifications
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'SECID' in df.columns
        assert df['SECID'].iloc[0] == 'SBER'
    
    @patch('requests.Session.get')
    def test_get_securities_error(self, mock_get, client):
        """Test la gestion d'erreur"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(MOEXAPIError):
            client.get_securities()
    
    @patch('requests.Session.get')
    def test_get_market_data(self, mock_get, client):
        """Test la récupération des données de marché"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'marketdata': {
                'columns': [{'name': 'SECID'}, {'name': 'LAST'}, {'name': 'VOLT'}],
                'data': [['SBER', 280.5, 1000000]]
            }
        }
        mock_get.return_value = mock_response
        
        df = client.get_market_data('SBER')
        
        assert not df.empty
        assert df['LAST'].iloc[0] == 280.5
    
    @patch('requests.Session.get')
    def test_get_candles(self, mock_get, client):
        """Test la récupération des données historiques"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candles': {
                'columns': [{'name': 'open'}, {'name': 'close'}, {'name': 'begin'}],
                'data': [[100, 101, '2024-01-01'], [101, 102, '2024-01-02']]
            }
        }
        mock_get.return_value = mock_response
        
        df = client.get_candles('SBER')
        
        assert not df.empty
        assert len(df) == 2
        assert 'open' in df.columns
    
    def test_rate_limiting(self, client):
        """Test le rate limiting"""
        import time
        
        start = time.time()
        client._rate_limit()
        client._rate_limit()
        end = time.time()
        
        # Devrait avoir attendu au moins min_interval entre les appels
        assert end - start >= client.min_request_interval
    
    @patch('requests.Session.get')
    def test_retry_on_error(self, mock_get, client):
        """Test le mécanisme de retry"""
        # Premier appel échoue, second réussit
        mock_get.side_effect = [
            Exception("First error"),
            Mock(status_code=200, json=lambda: {'securities': {'columns': [], 'data': []}})
        ]
        
        # Doit réussir après retry
        result = client.get_securities()
        assert result is not None