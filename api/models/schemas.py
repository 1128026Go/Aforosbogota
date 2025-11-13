"""
Schemas Pydantic para API
"""

from pydantic import BaseModel, field_validator
from typing import Dict, List, Optional, Literal
from datetime import datetime


class DatasetInfo(BaseModel):
    """Información de dataset"""

    id: str
    name: str
    created_at: str
    frames: int
    tracks: int


class DatasetStatus(BaseModel):
    """Estado de configuración del dataset"""

    has_cardinals: bool
    has_rilsa_map: bool
    intervals_ready: bool


class Gate(BaseModel):
    """Gate/línea de cruce para detectar entrada/salida de vehículos"""
    x1: float
    y1: float
    x2: float
    y2: float


class PolygonPoint(BaseModel):
    """Punto de un polígono"""
    x: float
    y: float


class AccessPoint(BaseModel):
    """Punto de acceso con cardinal oficial y gate de cruce"""

    id: str
    display_name: str  # nombre libre del usuario
    cardinal_official: Literal['N', 'S', 'E', 'O']  # cardinal OBLIGATORIO
    gate: Optional[Gate] = None  # línea de cruce (opcional si hay polígono)
    polygon: Optional[List[PolygonPoint]] = None  # polígono de zona (opcional, más preciso que gate)
    x: Optional[float] = None  # coordenada X del punto central
    y: Optional[float] = None  # coordenada Y del punto central

    @field_validator('cardinal_official')
    @classmethod
    def validate_cardinal(cls, v):
        if v not in ['N', 'S', 'E', 'O']:
            raise ValueError('cardinal_official debe ser N, S, E u O')
        return v


class CardinalConfig(BaseModel):
    """Configuración de puntos cardinales"""

    datasetId: str
    accesses: List[AccessPoint]
    updatedAt: str
    orientation_deg: Optional[float] = None  # solo para UI, no afecta clasificación
    center: Optional[Dict[str, float]] = None  # solo para UI

    @field_validator('accesses')
    @classmethod
    def validate_all_cardinals(cls, v):
        if not v:
            raise ValueError('Debe haber al menos un acceso')

        # Verificar que todos tengan cardinal_official
        for acc in v:
            if not acc.cardinal_official:
                raise ValueError(f'El acceso {acc.id} no tiene cardinal_official definido')

        return v


class RilsaRule(BaseModel):
    """Regla RILSA: origen->destino = código"""

    origin: str
    dest: str
    rilsa_code: int  # 1-10, 91-94, 101-104
    description: Optional[str] = None


class RilsaMapConfig(BaseModel):
    """
    Mapa de movimientos RILSA - 100% manual basado en cardinales oficiales

    Las reglas se definen por par de cardinales (N/S/E/O), no por coordenadas
    Ejemplo: "N->S": 1 (recto), "E->S": 91 (derecha según configuración del usuario)
    """

    version: int = 1
    rectos: Optional[Dict[str, int]] = {}  # "N->S": 1, "S->N": 2, etc.
    grupos: Optional[Dict[str, int]] = {}  # "derecha": 91, "izquierda": 92, etc.
    reglas: Dict[str, int]  # "N->E": 91, "E->N": 92, etc. - reglas específicas
    metadata: Optional[Dict] = {}


class TrackCompleted(BaseModel):
    """Trayectoria completada (egreso)"""

    track_id: str
    clase: str  # car, motorcycle, bus, truck_c1, truck_c2, truck_c3, bicycle, person
    t_exit_iso: str
    origin_access: str
    dest_access: str
