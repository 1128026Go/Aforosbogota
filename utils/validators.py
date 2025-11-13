from __future__ import annotations

from typing import Any, Dict, List, Tuple


class DataValidator:
    """Validaciones básicas para los tests unitarios."""

    REQUIRED_LOCATION_KEYS = {"x", "y", "z"}
    REQUIRED_VEHICLE_KEYS = {"id", "location"}

    @staticmethod
    def validate_vehicle_data(vehicle: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Valida la estructura mínima de un vehículo."""
        errors: List[str] = []

        missing_keys = DataValidator.REQUIRED_VEHICLE_KEYS - vehicle.keys()
        if missing_keys:
            errors.append(f"Missing keys: {', '.join(sorted(missing_keys))}")

        location = vehicle.get("location", {})
        if not isinstance(location, dict):
            errors.append("location must be a dict")
        else:
            missing_location = DataValidator.REQUIRED_LOCATION_KEYS - location.keys()
            if missing_location:
                errors.append(f"Missing location keys: {', '.join(sorted(missing_location))}")

        return len(errors) == 0, errors

    @staticmethod
    def detect_anomalies(vehicle: Dict[str, Any]) -> List[str]:
        """Detecta anomalías sencillas (ej. velocidad excesiva)."""
        anomalies: List[str] = []

        velocity = vehicle.get("velocity")
        if isinstance(velocity, dict):
            speed = sum(component**2 for component in velocity.values()) ** 0.5
        else:
            try:
                speed = float(velocity)
            except (TypeError, ValueError):
                speed = 0.0

        if speed > 55.0:  # ~200 km/h
            anomalies.append(f"Velocity too high: {speed:.2f} m/s")

        return anomalies

