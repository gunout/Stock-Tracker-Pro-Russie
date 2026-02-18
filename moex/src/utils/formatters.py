"""
Fonctions de formatage
"""

def format_currency(value: float, currency: str = "RUB") -> str:
    """
    Formate une valeur monétaire
    
    Args:
        value: Valeur à formater
        currency: Code de la devise
        
    Returns:
        str: Valeur formatée
    """
    if value is None:
        return "N/A"
    
    if currency == "RUB":
        if value >= 1e12:
            return f"₽{value/1e12:.2f} трлн"
        elif value >= 1e9:
            return f"₽{value/1e9:.2f} млрд"
        elif value >= 1e6:
            return f"₽{value/1e6:.2f} млн"
        else:
            return f"₽{value:,.2f}"
    else:
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.2f}"

def format_large_number(value: float) -> str:
    """
    Formate un grand nombre selon le système russe
    
    Args:
        value: Nombre à formater
        
    Returns:
        str: Nombre formaté
    """
    if value > 1e12:
        return f"{value/1e12:.2f} трлн"
    elif value > 1e9:
        return f"{value/1e9:.2f} млрд"
    elif value > 1e6:
        return f"{value/1e6:.2f} млн"
    elif value > 1e3:
        return f"{value/1e3:.2f} тыс"
    else:
        return f"{value:,.0f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formate un pourcentage
    
    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        
    Returns:
        str: Pourcentage formaté
    """
    if value is None:
        return "N/A"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"

def format_date(dt, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formate une date
    
    Args:
        dt: Date à formater
        format: Format de date
        
    Returns:
        str: Date formatée
    """
    if dt is None:
        return "N/A"
    return dt.strftime(format)