"""
Tests de integración para endpoints de reportes RILSA
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
TEST_DATASET_ID = "test_dataset_report"
TEST_DATA_DIR = Path("data")


@pytest.fixture
def setup_test_dataset():
    """Crea un dataset de prueba con trayectorias"""
    dataset_dir = TEST_DATA_DIR / TEST_DATASET_ID
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Crear metadata
    metadata = {
        "id": TEST_DATASET_ID,
        "name": "Test Dataset",
        "created_at": "2024-11-10T10:00:00"
    }
    (dataset_dir / "metadata.json").write_text(json.dumps(metadata))

    # Crear trayectorias de prueba
    trajectories = [
        {
            "track_id": 1,
            "class": "car",
            "t_exit": "2024-11-10T14:15:00",
            "cardinal_origin": "N",
            "cardinal_destination": "S",
            "movimiento_rilsa": 1,
            "avg_speed": 30.0
        },
        {
            "track_id": 2,
            "class": "motorcycle",
            "t_exit": "2024-11-10T14:20:00",
            "cardinal_origin": "E",
            "cardinal_destination": "O",
            "movimiento_rilsa": 3,
            "avg_speed": 25.0
        }
    ]
    (dataset_dir / "playback_events.json").write_text(json.dumps(trajectories))

    yield

    # Limpiar
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)


def test_generate_rilsa_report_success(setup_test_dataset):
    """Test generación exitosa de reporte RILSA"""
    response = client.post(f"/api/rilsa/report/{TEST_DATASET_ID}")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["dataset_id"] == TEST_DATASET_ID
    assert "report" in data
    assert "files_generated" in data
    assert "generated_at" in data


def test_generate_rilsa_report_csv_format(setup_test_dataset):
    """Test generación de reporte en formato CSV"""
    response = client.post(
        f"/api/rilsa/report/{TEST_DATASET_ID}",
        params={"format": "csv"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "csv_files" in data
    assert "download_urls" in data


def test_generate_rilsa_report_dataset_not_found():
    """Test generación de reporte con dataset inexistente"""
    response = client.post("/api/rilsa/report/dataset_nonexistent")

    assert response.status_code == 404


def test_download_report_file_success(setup_test_dataset):
    """Test descarga exitosa de archivo de reporte"""
    # Primero generar reporte
    report_response = client.post(f"/api/rilsa/report/{TEST_DATASET_ID}")
    report_data = report_response.json()

    if report_data.get("files_generated"):
        # Obtener primer archivo CSV
        csv_files = [f for f in report_data["files_generated"] if f.endswith(".csv")]
        if csv_files:
            filename = Path(csv_files[0]).name

            # Descargar archivo
            response = client.get(f"/api/files/{TEST_DATASET_ID}/reports/{filename}")

            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "") or \
                   "application/octet-stream" in response.headers.get("content-type", "")


def test_download_report_file_not_found():
    """Test descarga de archivo inexistente"""
    response = client.get(f"/api/files/{TEST_DATASET_ID}/reports/nonexistent.csv")

    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




