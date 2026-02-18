"""
Exceptions personnalisées
"""

class MOEXAPIError(Exception):
    """Exception de base pour l'API MOEX"""
    pass

class MOEXRateLimitError(MOEXAPIError):
    """Exception pour dépassement de rate limit"""
    pass
