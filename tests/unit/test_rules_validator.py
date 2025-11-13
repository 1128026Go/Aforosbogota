"""
Tests unitarios para RulesValidator
"""

import pytest
from api.services.rules_validator import RulesValidator


class TestRulesValidator:
    """Tests para RulesValidator"""

    @pytest.fixture
    def validator(self):
        """Fixture para crear validador"""
        return RulesValidator()

    @pytest.fixture
    def sample_config(self):
        """Configuración de ejemplo"""
        return {
            "trajectory_filters": {
                "min_duration_seconds": 2.0,
                "max_duration_seconds": 300.0,
                "min_distance_meters": 5.0,
                "max_distance_meters": 500.0,
                "min_speed_kmh": 1.0,
                "max_speed_kmh": 120.0
            },
            "cardinal_config": {
                "accesses": {
                    "N": {"allows_entry": True, "allows_exit": True},
                    "S": {"allows_entry": True, "allows_exit": True}
                }
            },
            "correction_rules": []
        }

    def test_validate_trajectory_valid(self, validator, sample_config):
        """Test validación de trayectoria válida"""
        trajectory = {
            "track_id": 1,
            "class": "car",
            "duration": 10.0,
            "distance": 50.0,
            "avg_speed": 30.0,
            "points": [{"x": 100, "y": 100}, {"x": 150, "y": 150}],
            "cardinal_origin": "N",
            "cardinal_destination": "S"
        }

        is_valid, errors = validator.validate_trajectory(trajectory, sample_config)
        assert is_valid
        assert len(errors) == 0

    def test_validate_trajectory_short_duration(self, validator, sample_config):
        """Test validación de trayectoria con duración muy corta"""
        trajectory = {
            "track_id": 1,
            "class": "car",
            "duration": 0.5,  # Muy corta
            "distance": 50.0,
            "points": [{"x": 100, "y": 100}]
        }

        is_valid, errors = validator.validate_trajectory(trajectory, sample_config)
        assert not is_valid
        assert any("duración" in error.lower() for error in errors)

    def test_validate_trajectory_high_speed(self, validator, sample_config):
        """Test validación de trayectoria con velocidad muy alta"""
        trajectory = {
            "track_id": 1,
            "class": "car",
            "duration": 10.0,
            "distance": 50.0,
            "avg_speed": 200.0,  # Muy alta
            "points": [{"x": 100, "y": 100}, {"x": 150, "y": 150}]
        }

        is_valid, errors = validator.validate_trajectory(trajectory, sample_config)
        assert not is_valid
        assert any("velocidad" in error.lower() for error in errors)

    def test_validate_trajectory_few_points(self, validator, sample_config):
        """Test validación de trayectoria con pocos puntos"""
        trajectory = {
            "track_id": 1,
            "class": "car",
            "duration": 10.0,
            "distance": 50.0,
            "points": [{"x": 100, "y": 100}]  # Solo 1 punto
        }

        is_valid, errors = validator.validate_trajectory(trajectory, sample_config)
        assert not is_valid
        assert any("puntos" in error.lower() for error in errors)

    def test_validate_batch(self, validator, sample_config):
        """Test validación de lote de trayectorias"""
        trajectories = [
            {
                "track_id": 1,
                "class": "car",
                "duration": 10.0,
                "distance": 50.0,
                "points": [{"x": 100, "y": 100}, {"x": 150, "y": 150}]
            },
            {
                "track_id": 2,
                "class": "car",
                "duration": 0.5,  # Inválida
                "distance": 50.0,
                "points": [{"x": 100, "y": 100}]
            }
        ]

        result = validator.validate_batch(trajectories, sample_config)

        assert len(result["valid"]) == 1
        assert len(result["invalid"]) == 1
        assert result["statistics"]["total"] == 2
        assert result["statistics"]["valid"] == 1
        assert result["statistics"]["invalid"] == 1

    def test_detect_incomplete_trajectories(self, validator):
        """Test detección de trayectorias incompletas"""
        trajectories = [
            {
                "track_id": 1,
                "points": [{"x": 100, "y": 100}],  # Pocos puntos
                "cardinal_origin": "N"
            },
            {
                "track_id": 2,
                "points": [{"x": 100, "y": 100}, {"x": 150, "y": 150}],
                # Sin origen ni destino
            }
        ]

        incomplete = validator.detect_incomplete_trajectories(trajectories)

        assert len(incomplete) == 2
        assert all("incomplete_reasons" in traj for traj in incomplete)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




