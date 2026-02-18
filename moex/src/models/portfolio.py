"""
Modèle pour le portefeuille virtuel
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np

@dataclass
class Position:
    """Position dans le portefeuille"""
    symbol: str
    shares: float
    buy_price: float
    buy_date: datetime
    notes: Optional[str] = None
    
    @property
    def cost(self) -> float:
        """Coût total de la position"""
        return self.shares * self.buy_price
    
    @property
    def current_value(self, current_price: float) -> float:
        """Valeur actuelle"""
        return self.shares * current_price
    
    @property
    def profit_loss(self, current_price: float) -> float:
        """Profit/perte"""
        return self.current_value(current_price) - self.cost
    
    @property
    def profit_loss_percent(self, current_price: float) -> float:
        """Profit/perte en pourcentage"""
        if self.cost == 0:
            return 0
        return (self.profit_loss(current_price) / self.cost) * 100

@dataclass
class Portfolio:
    """Portefeuille virtuel"""
    name: str = "Mon Portefeuille"
    positions: Dict[str, List[Position]] = field(default_factory=dict)
    cash: float = 0.0
    currency: str = "RUB"
    
    def add_position(self, position: Position):
        """Ajoute une position"""
        if position.symbol not in self.positions:
            self.positions[position.symbol] = []
        self.positions[position.symbol].append(position)
    
    def remove_position(self, symbol: str, index: int = -1):
        """Supprime une position"""
        if symbol in self.positions and self.positions[symbol]:
            if index == -1:
                self.positions[symbol].pop()
            else:
                self.positions[symbol].pop(index)
            
            if not self.positions[symbol]:
                del self.positions[symbol]
    
    def get_total_cost(self) -> float:
        """Coût total du portefeuille"""
        total = self.cash
        for symbol_positions in self.positions.values():
            for pos in symbol_positions:
                total += pos.cost
        return total
    
    def get_current_value(self, prices: Dict[str, float]) -> float:
        """Valeur actuelle du portefeuille"""
        total = self.cash
        for symbol, positions in self.positions.items():
            current_price = prices.get(symbol, 0)
            for pos in positions:
                total += pos.current_value(current_price)
        return total
    
    def get_profit_loss(self, prices: Dict[str, float]) -> float:
        """Profit/perte total"""
        return self.get_current_value(prices) - self.get_total_cost()
    
    def get_profit_loss_percent(self, prices: Dict[str, float]) -> float:
        """Profit/perte en pourcentage"""
        total_cost = self.get_total_cost()
        if total_cost == 0:
            return 0
        return (self.get_profit_loss(prices) / total_cost) * 100
    
    def to_dataframe(self, prices: Dict[str, float] = None) -> pd.DataFrame:
        """Convertit en DataFrame pour affichage"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for symbol, positions in self.positions.items():
            for i, pos in enumerate(positions):
                current_price = prices.get(symbol, 0) if prices else 0
                current_value = pos.current_value(current_price)
                profit = pos.profit_loss(current_price)
                profit_pct = pos.profit_loss_percent(current_price)
                
                data.append({
                    'Symbole': symbol,
                    'Position': i + 1,
                    'Actions': pos.shares,
                    "Prix d'achat": f"{pos.buy_price:,.2f} ₽",
                    'Date achat': pos.buy_date.strftime('%Y-%m-%d'),
                    'Prix actuel': f"{current_price:,.2f} ₽",
                    'Valeur': f"{current_value:,.2f} ₽",
                    'Profit': f"{profit:,.2f} ₽",
                    'Profit %': f"{profit_pct:.1f}%"
                })
        
        return pd.DataFrame(data)
    
    def get_allocation(self) -> Dict[str, float]:
        """Calcule l'allocation par symbole"""
        allocation = {}
        total_value = sum(pos.cost for positions in self.positions.values() for pos in positions)
        
        if total_value == 0:
            return {}
        
        for symbol, positions in self.positions.items():
            symbol_value = sum(pos.cost for pos in positions)
            allocation[symbol] = (symbol_value / total_value) * 100
        
        return allocation