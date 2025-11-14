"""
Modelos de respuesta para análisis avanzados de aforos.

Estos esquemas definen contratos inmutables para los endpoints de /analysis y
las exportaciones asociadas. No modificar sin coordinar previamente.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from api.models.config import AccessConfig


class DatasetMetadata(BaseModel):
    """Metadata básica de un dataset almacenado."""

    id: str
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str = "uploaded"
    tracks: Optional[int] = None
    frames: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class Cardinal(BaseModel):
    """Acceso cardinal definido sobre la intersección."""

    id: str
    x: float
    y: float
    cardinal: str
    count: int
    polygon: Optional[List[List[float]]] = None
    rilsa_index: Optional[int] = None


class ConfigResponse(BaseModel):
    """Respuesta de configuración para un dataset determinado."""

    dataset_id: str
    cardinals: List[Cardinal]
    rilsa_map: Dict[str, Any]


class VolumeRow(BaseModel):
    """Fila de conteo por intervalo y clase vehicular."""

    interval_start: int
    interval_end: int
    autos: int = 0
    buses: int = 0
    camiones: int = 0
    motos: int = 0
    bicis: int = 0
    peatones: int = 0
    total: int = 0


class MovementVolumeTable(BaseModel):
    """Tabla de un movimiento RILSA específico."""

    rilsa_code: str
    description: str
    rows: List[VolumeRow]


class VolumesResponse(BaseModel):
    """Respuesta del endpoint /analysis/{dataset_id}/volumes."""

    dataset_id: str
    interval_minutes: int
    totals_by_interval: List[VolumeRow]
    movements: List[MovementVolumeTable]


class SpeedStats(BaseModel):
    """Estadísticos descriptivos de velocidades (km/h)."""

    count: int
    mean_kmh: float
    median_kmh: float
    p85_kmh: float
    min_kmh: float
    max_kmh: float


class MovementSpeedStats(BaseModel):
    """Resumen de velocidades por movimiento RILSA y clase de vehículo."""

    rilsa_code: str
    description: str
    vehicle_class: str
    stats: SpeedStats


class SpeedsResponse(BaseModel):
    """Respuesta del endpoint /analysis/{dataset_id}/speeds."""

    dataset_id: str
    per_movement: List[MovementSpeedStats]


class ConflictEvent(BaseModel):
    """Conflicto detectado según métricas de seguridad vial."""

    ttc_min: float
    pet: Optional[float] = None
    time_sec: float
    x: float
    y: float
    track_id_1: str
    track_id_2: str
    severity: float
    pair_type: str


class ConflictsResponse(BaseModel):
    """Respuesta del endpoint /analysis/{dataset_id}/conflicts."""

    dataset_id: str
    total_conflicts: int
    events: List[ConflictEvent]


class ViolationSummary(BaseModel):
    """Resumen de violaciones por movimiento RILSA prohibido."""

    rilsa_code: str
    description: str
    count: int


class ViolationsResponse(BaseModel):
    """Respuesta del endpoint /analysis/{dataset_id}/violations."""

    dataset_id: str
    total_violations: int
    by_movement: List[ViolationSummary]


class AccessGenerationResponse(BaseModel):
    """Respuesta del endpoint /config/{dataset_id}/generate_accesses."""

    dataset_id: str
    accesses: List[AccessConfig]
