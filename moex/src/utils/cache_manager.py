"""
Gestionnaire de cache avec persistance fichier
"""
import pickle
import hashlib
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional
import streamlit as st

CACHE_DIR = "cache"

class CacheManager:
    """Gestionnaire de cache avec support fichier et mémoire"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.memory_cache = {}
    
    def _get_file_path(self, key: str) -> str:
        """Retourne le chemin du fichier cache"""
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Génère une clé unique pour la fonction et ses arguments"""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur du cache"""
        # Essayer le cache mémoire d'abord
        if key in self.memory_cache:
            cached = self.memory_cache[key]
            if cached['expires'] > datetime.now():
                return cached['value']
            else:
                del self.memory_cache[key]
        
        # Essayer le cache fichier
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    cached = pickle.load(f)
                    if cached['expires'] > datetime.now():
                        # Restaurer dans le cache mémoire
                        self.memory_cache[key] = cached
                        return cached['value']
                    else:
                        os.remove(file_path)
            except:
                pass
        
        return default
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Stocke une valeur dans le cache"""
        expires = datetime.now() + timedelta(seconds=ttl)
        cached_data = {
            'value': value,
            'expires': expires,
            'created': datetime.now()
        }
        
        # Cache mémoire
        self.memory_cache[key] = cached_data
        
        # Cache fichier
        try:
            file_path = self._get_file_path(key)
            with open(file_path, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            print(f"Erreur sauvegarde cache: {e}")
    
    def clear(self):
        """Vide tous les caches"""
        self.memory_cache.clear()
        for file in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, file))

# Instance globale
_cache_manager = CacheManager()

def cache(ttl: int = 300):
    """
    Décorateur pour mettre en cache les résultats des fonctions
    
    Args:
        ttl: Durée de vie en secondes
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Vérifier d'abord le cache session Streamlit
            cache_key = f"{func.__name__}_{hash(str(args))}_{hash(str(kwargs))}"
            
            if cache_key in st.session_state.get('data_cache', {}):
                cached = st.session_state.data_cache[cache_key]
                age = (datetime.now() - cached['timestamp']).total_seconds()
                if age < ttl:
                    return cached['value']
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Stocker dans le cache session
            if 'data_cache' not in st.session_state:
                st.session_state.data_cache = {}
            
            st.session_state.data_cache[cache_key] = {
                'value': result,
                'timestamp': datetime.now()
            }
            
            return result
        return wrapper
    return decorator