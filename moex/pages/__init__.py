"""
Package des pages Streamlit
Ce fichier permet d'exporter toutes les pages avec leurs noms exacts
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Liste de tous les fichiers de pages
__all__ = [
    '1_📈_tableau_de_bord',
    '2_💰_portefeuille', 
    '3_🔔_alertes',
    '4_📊_indices',
    '5_🤖_predictions',
    '6_⚙️_configuration'
]

# Import de tous les modules
for module_name in __all__:
    try:
        __import__(f'pages.{module_name}')
    except ImportError as e:
        print(f"Erreur d'import pour {module_name}: {e}")
