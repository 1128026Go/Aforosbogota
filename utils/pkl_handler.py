from __future__ import annotations

from typing import Any, Dict


class PKLHandler:
    """Manejo simplificado de estructuras PKL para los tests legacy."""

    REQUIRED_KEYS = {"frame", "timestamp"}

    def validate_structure(self, data: Dict[str, Any]) -> bool:
        """Valida que el PKL contenga llaves mínimas."""
        if not isinstance(data, dict):
            return False

        if not self.REQUIRED_KEYS <= data.keys():
            return False

        if not isinstance(data.get("frame"), (int, float)):
            return False

        return True

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae estadísticas básicas de la estructura PKL."""
        vehicles = data.get("vehicles") or []
        pedestrians = data.get("pedestrians") or []

        return {
            "frame": data.get("frame"),
            "timestamp": data.get("timestamp"),
            "num_vehicles": len(vehicles),
            "num_pedestrians": len(pedestrians),
        }

