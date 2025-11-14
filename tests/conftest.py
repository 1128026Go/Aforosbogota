"""
CONFTEST para pytest - Configuración global de tests
"""

import sys
from pathlib import Path

# Agregar root de proyecto al path para que los imports funcionen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
