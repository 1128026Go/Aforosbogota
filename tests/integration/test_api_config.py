"""
Tests de integración para endpoints de configuración
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
TEST_DATASET_ID = "test_dataset_config"
TEST_DATA_DIR = Path("data")


@pytest.fixture
def setup_test_dataset():
    """Crea un dataset de prueba"""
    dataset_dir = TEST_DATA_DIR / TEST_DATASET_ID
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Crear metadata
    metadata = {
        "id": TEST_DATASET_ID,
        "name": "Test Dataset",
        "created_at": "2024-11-10T10:00:00",
        "frames": 1000,
        "tracks": 100
    }
    (dataset_dir / "metadata.json").write_text(json.dumps(metadata))

    # Crear trayectorias de prueba
    trajectories = [
        {
            "track_id": 1,
            "class": "car",
            "points": [
                {"x": 100, "y": 50},
                {"x": 150, "y": 100},
                {"x": 200, "y": 150}
            ],
            "cardinal_origin": "N",
            "cardinal_destination": "S"
        },
        {
            "track_id": 2,
            "class": "car",
            "points": [
                {"x": 800, "y": 450},
                {"x": 750, "y": 400},
                {"x": 700, "y": 350}
            ],
            "cardinal_origin": "E",
            "cardinal_destination": "O"
        }
    ]
    (dataset_dir / "playback_events.json").write_text(json.dumps(trajectories))

    yield

    # Limpiar
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)


def test_generate_config_success(setup_test_dataset):
    """Test generación exitosa de configuración"""
    response = client.post(f"/api/config/generate/{TEST_DATASET_ID}")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["dataset_id"] == TEST_DATASET_ID
    assert "config" in data
    assert data["cardinals_detected"] >= 0
    assert data["movements_inferred"] >= 0


def test_generate_config_dataset_not_found():
    """Test generación con dataset inexistente"""
    response = client.post("/api/config/generate/dataset_nonexistent")

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()


def test_view_config_success(setup_test_dataset):
    """Test obtención exitosa de configuración"""
    # Primero generar configuración
    client.post(f"/api/config/generate/{TEST_DATASET_ID}")

    # Luego obtenerla
    response = client.get(f"/api/config/view/{TEST_DATASET_ID}")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "config" in data
    assert "access_coordinates" in data
    assert "inferred_movements" in data


def test_view_config_not_found():
    """Test obtención de configuración inexistente"""
    response = client.get("/api/config/view/dataset_nonexistent")

    assert response.status_code == 404


def test_update_polygons_success(setup_test_dataset):
    """Test actualización exitosa de polígonos"""
    # Primero generar configuración
    client.post(f"/api/config/generate/{TEST_DATASET_ID}")

    # Actualizar polígonos
    polygons = {
        "entry_polygon": [[100, 50], [150, 50], [150, 100], [100, 100]],
        "exit_polygon": [[100, 800], [150, 800], [150, 850], [100, 850]]
    }

    response = client.put(
        f"/api/config/update-polygons/{TEST_DATASET_ID}/N",
        json=polygons
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["cardinal"] == "N"


def test_update_polygons_invalid_cardinal(setup_test_dataset):
    """Test actualización con cardinal inválido"""
    polygons = {
        "entry_polygon": [[100, 50], [150, 50], [150, 100]]
    }

    response = client.put(
        f"/api/config/update-polygons/{TEST_DATASET_ID}/X",
        json=polygons
    )

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




