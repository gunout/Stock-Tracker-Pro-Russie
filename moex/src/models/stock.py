"""
Modèle représentant une action
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class StockInfo:
    """Informations sur une action"""
    secid: str
    shortname: str
    longname: str
    isin: str
    regnumber: str
    lotsize: int
    facevalue: float
    
@dataclass
class Stock:
    """Modèle complet d'une action avec données de marché"""
    
    # Informations de base
    secid: str
    name: str
    board: str = "TQBR"
    
    # Données de marché
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    value: Optional[float] = None
    
    # Prix du jour
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    
    # Métadonnées
    last_update: Optional[datetime] = None
    currency: str = "RUB"
    
    @property
    def is_positive(self) -> bool:
        """Vérifie si la variation est positive"""
        return self.change is not None and self.change > 0
    
    @property
    def is_negative(self) -> bool:
        """Vérifie si la variation est négative"""
        return self.change is not None and self.change < 0
    
    @property
    def price_formatted(self) -> str:
        """Prix formaté"""
        if self.price is None:
            return "N/A"
        return f"{self.price:,.2f} ₽"
    
    @property
    def change_formatted(self) -> str:
        """Variation formatée"""
        if self.change is None:
            return "N/A"
        sign = "+" if self.change > 0 else ""
        return f"{sign}{self.change:,.2f} ₽"
    
    @property
    def change_percent_formatted(self) -> str:
        """Variation en pourcentage formatée"""
        if self.change_percent is None:
            return "N/A"
        sign = "+" if self.change_percent > 0 else ""
        return f"{sign}{self.change_percent:.2f}%"
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            'secid': self.secid,
            'name': self.name,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
    
    @classmethod
    def from_market_data(cls, secid: str, market_data: dict) -> 'Stock':
        """
        Crée une instance à partir des données de marché
        
        Args:
            secid: Code de l'action
            market_data: Données de marché brutes
            
        Returns:
            Stock: Instance de Stock
        """
        return cls(
            secid=secid,
            name=market_data.get('SHORTNAME', secid),
            price=market_data.get('LAST'),
            change=market_data.get('CHANGE'),
            change_percent=market_data.get('CHANGEPCT'),
            volume=market_data.get('VOLT'),
            value=market_data.get('VALT'),
            open=market_data.get('OPEN'),
            high=market_data.get('HIGH'),
            low=market_data.get('LOW'),
            close=market_data.get('LAST'),
            last_update=datetime.now()
        )