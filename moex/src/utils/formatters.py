"""
Fonctions de formatage
"""

def format_currency(value: float, currency: str = "RUB") -> str:
    """Formate une valeur monétaire"""
    if value is None:
        return "N/A"
    
    if currency == "RUB":
        if value >= 1e9:
            return f"₽{value/1e9:.2f} млрд"
        elif value >= 1e6:
            return f"₽{value/1e6:.2f} млн"
        else:
            return f"₽{value:,.2f}"
    else:
        return f"${value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Formate un pourcentage"""
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"
