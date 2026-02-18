"""
Exceptions personnalisées pour l'API MOEX
"""

class MOEXAPIError(Exception):
    """Exception de base pour les erreurs API"""
    pass

class MOEXRateLimitError(MOEXAPIError):
    """Exception pour dépassement de rate limit"""
    pass

class MOEXConnectionError(MOEXAPIError):
    """Exception pour erreurs de connexion"""
    pass

class MOEXDataError(MOEXAPIError):
    """Exception pour erreurs de données"""
    pass

class MOEXNotFoundError(MOEXAPIError):
    """Exception pour ressource non trouvée"""
    pass

class MOEXAuthenticationError(MOEXAPIError):
    """Exception pour erreurs d'authentification"""
    pass

class MOEXTimeoutError(MOEXAPIError):
    """Exception pour timeout"""
    pass