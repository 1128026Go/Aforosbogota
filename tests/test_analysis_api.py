"""
Pruebas de integración ligera para los endpoints de análisis y configuración.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.config import AccessConfig, DatasetConfig, ForbiddenMovement
from api.routers import datasets as datasets_router
from api.services import analysis_settings as analysis_settings_service
from api.services.persistence import ConfigPersistenceService
from api.services.rilsa_mapping import build_rilsa_rule_map

DATASET_ID = "demo_dataset"


@pytest.fixture
def api_client(tmp_path, monkeypatch) -> Tuple[TestClient, str]:
    """Configura un dataset mínimo en un directorio temporal y devuelve el cliente de pruebas."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    config_dir = tmp_path / "configs"

    # Redirigir rutas de almacenamiento
    monkeypatch.setattr(datasets_router, "DATA_DIR", data_dir)
    monkeypatch.setattr(analysis_settings_service, "DATA_DIR", data_dir)
    monkeypatch.setattr(ConfigPersistenceService, "DEFAULT_CONFIG_DIR", str(config_dir))

    dataset_dir = data_dir / DATASET_ID
    dataset_dir.mkdir(parents=True)

    # Datos normalizados de ejemplo (dos trayectorias)
    df = pd.DataFrame(
        {
            "frame_id": [0, 1, 2, 0, 1, 2],
            "track_id": [1, 1, 1, 2, 2, 2],
            "x": [0.0, 0.0, 0.0, 5.0, 4.0, 3.0],
            "y": [0.0, 45.0, 90.0, 100.0, 60.0, 10.0],
            "object_class": ["car", "car", "car", "truck", "truck", "truck"],
        }
    )
    df.to_parquet(dataset_dir / "normalized.parquet")

    accesses = [
        {"id": "A_N", "cardinal": "N", "x": 0.0, "y": 0.0, "count": 0},
        {"id": "A_S", "cardinal": "S", "x": 0.0, "y": 120.0, "count": 0},
        {"id": "A_E", "cardinal": "E", "x": 120.0, "y": 0.0, "count": 0},
        {"id": "A_O", "cardinal": "O", "x": -120.0, "y": 0.0, "count": 0},
    ]
    (dataset_dir / "cardinals.json").write_text(json.dumps(accesses), encoding="utf-8")
    rilsa_map = build_rilsa_rule_map(accesses)
    (dataset_dir / "rilsa_map.json").write_text(json.dumps(rilsa_map), encoding="utf-8")

    # Configuración persistida con un movimiento prohibido
    config = DatasetConfig(
        dataset_id=DATASET_ID,
        accesses=[
            AccessConfig(id="A_N", cardinal="N", polygon=[], centroid=None),
            AccessConfig(id="A_S", cardinal="S", polygon=[], centroid=None),
            AccessConfig(id="A_E", cardinal="E", polygon=[], centroid=None),
            AccessConfig(id="A_O", cardinal="O", polygon=[], centroid=None),
        ],
        rilsa_rules=[],
        forbidden_movements=[ForbiddenMovement(rilsa_code="1", description="Giro directo N→S prohibido")],
    )
    ConfigPersistenceService.save_config(config)

    client = TestClient(app)
    return client, DATASET_ID


def test_analysis_settings_roundtrip(api_client):
    client, dataset_id = api_client

    response = client.get(f"/api/v1/config/{dataset_id}/analysis_settings")
    assert response.status_code == 200
    defaults = response.json()
    assert defaults["interval_minutes"] == 15

    payload = {
        "interval_minutes": 10,
        "min_length_m": 3.0,
        "max_direction_changes": 12,
        "min_net_over_path_ratio": 0.15,
        "ttc_threshold_s": 1.2,
    }
    save_resp = client.put(
        f"/api/v1/config/{dataset_id}/analysis_settings",
        json=payload,
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["interval_minutes"] == 10

    confirm_resp = client.get(f"/api/v1/config/{dataset_id}/analysis_settings")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["ttc_threshold_s"] == pytest.approx(1.2)


def test_forbidden_movements_roundtrip(api_client):
    client, dataset_id = api_client

    initial = client.get(f"/api/v1/config/{dataset_id}/forbidden_movements")
    assert initial.status_code == 200
    assert initial.json()[0]["rilsa_code"] == "1"

    updated = [
        {"rilsa_code": "5", "description": "Giro izquierda restringido"},
        {"rilsa_code": "9_", "description": "Movimiento peatonal prohibido"},
    ]
    save = client.put(
        f"/api/v1/config/{dataset_id}/forbidden_movements",
        json=updated,
    )
    assert save.status_code == 200
    assert len(save.json()) == 2

    confirm = client.get(f"/api/v1/config/{dataset_id}/forbidden_movements")
    assert confirm.status_code == 200
    assert {item["rilsa_code"] for item in confirm.json()} == {"5", "9_"}


def test_analysis_endpoints(api_client):
    client, dataset_id = api_client

    client.put(
        f"/api/v1/config/{dataset_id}/analysis_settings",
        json={
            "interval_minutes": 12,
            "min_length_m": 2.0,
            "max_direction_changes": 15,
            "min_net_over_path_ratio": 0.1,
            "ttc_threshold_s": 1.4,
        },
    )

    volumes = client.get(f"/api/v1/analysis/{dataset_id}/volumes")
    assert volumes.status_code == 200
    body = volumes.json()
    assert body["interval_minutes"] == 12
    assert body["totals_by_interval"]

    speeds = client.get(f"/api/v1/analysis/{dataset_id}/speeds")
    assert speeds.status_code == 200
    assert isinstance(speeds.json()["per_movement"], list)

    conflicts = client.get(f"/api/v1/analysis/{dataset_id}/conflicts")
    assert conflicts.status_code == 200
    assert conflicts.json()["total_conflicts"] >= 0

    violations = client.get(f"/api/v1/analysis/{dataset_id}/violations")
    assert violations.status_code == 200
    data = violations.json()
    assert data["total_violations"] >= 1


def test_reports_generation(api_client):
    client, dataset_id = api_client

    excel_resp = client.get(f"/api/v1/reports/{dataset_id}/excel")
    assert excel_resp.status_code == 200
    file_name = excel_resp.json()["file_name"]
    path = Path(datasets_router.DATA_DIR) / dataset_id / "reports" / file_name
    assert path.exists()

    try:
        import weasyprint  # noqa: F401
    except Exception:
        pytest.skip("WeasyPrint no disponible en el entorno de pruebas")

    pdf_resp = client.get(f"/api/v1/reports/{dataset_id}/pdf")
    assert pdf_resp.status_code == 200
    pdf_name = pdf_resp.json()["file_name"]
    pdf_path = Path(datasets_router.DATA_DIR) / dataset_id / "reports" / pdf_name
    assert pdf_path.exists()


def test_generate_accesses_from_normalized(api_client):
    client, dataset_id = api_client

    response = client.post(f"/api/v1/config/{dataset_id}/generate_accesses")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == dataset_id
    assert isinstance(payload["accesses"], list)
    assert {access["cardinal"] for access in payload["accesses"]}

