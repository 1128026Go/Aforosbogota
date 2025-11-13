"""
Fixtures y configuración para tests con pytest
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Asegurar que los paquetes principales sean importables
PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "api"

LEGACY_ARCHIVE = PROJECT_ROOT / "legacy" / "archive"

for path in (PROJECT_ROOT, API_ROOT, LEGACY_ARCHIVE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Configuración de base de datos persistente (archivo config/database.json)
DATABASE_CONFIG_PATH = PROJECT_ROOT / "config" / "database.json"
if DATABASE_CONFIG_PATH.exists():
    try:
        database_config = json.loads(DATABASE_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        database_config = {}
else:
    database_config = {}

os.environ.setdefault("POSTGRES_HOST", str(database_config.get("host", "localhost")))
os.environ.setdefault("POSTGRES_PORT", str(database_config.get("port", "5432")))
os.environ.setdefault("POSTGRES_DB", str(database_config.get("database", "bogota_traffic")))
os.environ.setdefault("POSTGRES_USER", str(database_config.get("user", "postgres")))
os.environ.setdefault("POSTGRES_PASSWORD", str(database_config.get("password", "postgres")))

# Base de datos aislada para pruebas utilizando SQLite
TEST_DB_PATH = PROJECT_ROOT / "tests" / "temp_test.db"
TEST_DB_PATH.parent.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}"


@pytest.fixture
def sample_vehicle_data():
    """Fixture con datos de vehículo de ejemplo"""
    return {
        'id': 'vehicle.tesla.model3_001',
        'actor_id': 123,
        'type': 'vehicle.tesla.model3',
        'location': {'x': 100.5, 'y': 200.3, 'z': 0.5},
        'rotation': {'pitch': 0.0, 'yaw': 90.0, 'roll': 0.0},
        'velocity': {'x': 10.0, 'y': 0.0, 'z': 0.0},
        'acceleration': {'x': 0.5, 'y': 0.0, 'z': 0.0},
        'is_at_traffic_light': False
    }


@pytest.fixture
def sample_pkl_data(sample_vehicle_data):
    """Fixture con datos PKL de ejemplo"""
    return {
        'frame': 12345,
        'timestamp': 1234567890.123,
        'vehicles': [sample_vehicle_data],
        'pedestrians': [],
        'traffic_lights': [],
        'metadata': {
            'map_name': 'Town03',
            'weather': {}
        }
    }


# --- Fin de tests/conftest.py ---
