"""
Tests de integración para endpoints de validación
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
import shutil

# Importar app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from main import app

client = TestClient(app)

# Datos de prueba
TEST_DATASET_ID = "test_dataset_validation"
TEST_DATA_DIR = Path("data")


@pytest.fixture
def setup_test_dataset():
    """Crea un dataset de prueba con configuración"""
    dataset_dir = TEST_DATA_DIR / TEST_DATASET_ID
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Crear metadata
    metadata = {
        "id": TEST_DATASET_ID,
        "name": "Test Dataset",
        "created_at": "2024-11-10T10:00:00"
    }
    (dataset_dir / "metadata.json").write_text(json.dumps(metadata))

    # Crear configuración
    config = {
        "dataset_id": TEST_DATASET_ID,
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
    (dataset_dir / "dataset_config.json").write_text(json.dumps(config))

    # Crear trayectorias de prueba
    trajectories = [
        {
            "track_id": 1,
            "class": "car",
            "duration": 10.0,
            "distance": 50.0,
            "avg_speed": 30.0,
            "points": [
                {"x": 100, "y": 100},
                {"x": 150, "y": 150},
                {"x": 200, "y": 200}
            ],
            "cardinal_origin": "N",
            "cardinal_destination": "S",
            "movimiento_rilsa": 1
        },
        {
            "track_id": 2,
            "class": "car",
            "duration": 0.5,  # Inválida: muy corta
            "distance": 50.0,
            "points": [{"x": 100, "y": 100}],  # Pocos puntos
            "cardinal_origin": "N"
        }
    ]
    (dataset_dir / "playback_events.json").write_text(json.dumps(trajectories))

    yield

    # Limpiar
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)


def test_run_validation_success(setup_test_dataset):
    """Test ejecución exitosa de validación"""
    response = client.post(f"/api/validation/run/{TEST_DATASET_ID}")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "statistics" in data
    assert data["statistics"]["total"] > 0
    assert "valid_count" in data
    assert "invalid_count" in data


def test_run_validation_dataset_not_found():
    """Test validación con dataset inexistente"""
    response = client.post("/api/validation/run/dataset_nonexistent")

    assert response.status_code == 404


def test_get_validation_results_success(setup_test_dataset):
    """Test obtención exitosa de resultados de validación"""
    # Primero ejecutar validación
    client.post(f"/api/validation/run/{TEST_DATASET_ID}")

    # Luego obtener resultados
    response = client.get(f"/api/validation/results/{TEST_DATASET_ID}")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "results" in data
    assert "statistics" in data["results"]


def test_get_validation_results_not_found():
    """Test obtención de resultados inexistentes"""
    response = client.get("/api/validation/results/dataset_nonexistent")

    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




