"""
Package des pages Streamlit
Ce fichier permet d'exporter toutes les pages
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from . import tableau_de_bord
    from . import portefeuille
    from . import alertes
    from . import indices
    from . import predictions
    from . import configuration
except ImportError as e:
    print(f"Erreur d'import des pages: {e}")

__all__ = [
    'tableau_de_bord',
    'portefeuille', 
    'alertes',
    'indices',
    'predictions',
    'configuration'
]
