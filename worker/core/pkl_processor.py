from __future__ import annotations

from typing import Dict

from utils.pkl_handler import PKLHandler
from utils.validators import DataValidator


class PKLProcessor:
    """Procesador simple de archivos PKL para compatibilidad con tests legacy."""

    def __init__(self) -> None:
        self.pkl_handler = PKLHandler()
        self.validator = DataValidator
        self._stats: Dict[str, int] = {"processed_files": 0}

    def get_stats(self) -> Dict[str, int]:
        """Devuelve estadísticas acumuladas."""
        return dict(self._stats)

