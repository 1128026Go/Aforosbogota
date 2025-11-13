"""
Fixtures simplificados para tests que no requieren base de datos
"""

import pytest
import sys
from pathlib import Path

# Agregar api al path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))




