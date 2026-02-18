"""
Modèles pour les alertes de prix
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

class AlertType(Enum):
    """Type d'alerte"""
    ABOVE = "above"  # Prix au-dessus
    BELOW = "below"  # Prix en-dessous
    PERCENT = "percent"  # Variation en pourcentage
    VOLUME = "volume"  # Volume inhabituel

class AlertStatus(Enum):
    """Statut de l'alerte"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    DISABLED = "disabled"

@dataclass
class PriceAlert:
    """Alerte de prix"""
    symbol: str
    alert_type: AlertType
    target_price: float
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = None
    triggered_at: Optional[datetime] = None
    message: str = ""
    one_time: bool = True
    notification_sent: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def check(self, current_price: float) -> bool:
        """
        Vérifie si l'alerte est déclenchée
        
        Args:
            current_price: Prix actuel
            
        Returns:
            bool: True si déclenchée
        """
        if self.status != AlertStatus.ACTIVE:
            return False
        
        triggered = False
        
        if self.alert_type == AlertType.ABOVE:
            triggered = current_price >= self.target_price
        elif self.alert_type == AlertType.BELOW:
            triggered = current_price <= self.target_price
        elif self.alert_type == AlertType.PERCENT:
            # À implémenter
            pass
        
        if triggered:
            self.triggered_at = datetime.now()
            self.status = AlertStatus.TRIGGERED
            self.message = f"{self.symbol} a atteint {current_price:,.2f} ₽"
        
        return triggered
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            'symbol': self.symbol,
            'type': self.alert_type.value,
            'target_price': self.target_price,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'message': self.message,
            'one_time': self.one_time,
            'notification_sent': self.notification_sent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PriceAlert':
        """Crée une instance depuis un dictionnaire"""
        return cls(
            symbol=data['symbol'],
            alert_type=AlertType(data['type']),
            target_price=data['target_price'],
            status=AlertStatus(data.get('status', 'active')),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            triggered_at=datetime.fromisoformat(data['triggered_at']) if data.get('triggered_at') else None,
            message=data.get('message', ''),
            one_time=data.get('one_time', True),
            notification_sent=data.get('notification_sent', False)
        )