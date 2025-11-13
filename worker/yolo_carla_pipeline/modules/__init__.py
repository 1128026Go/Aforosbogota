"""
Módulos del pipeline de análisis YOLOv8 → CARLA

Componentes:
- read_pkl: Ingesta y validación de PKL
- tracking: Multi-object tracking (SORT)
- analysis: Métricas de tráfico
- visualize: Visualizaciones
- carla_integration: Integración con CARLA Simulator
"""

__version__ = "1.0.0"
__author__ = "Traffic Analysis Pipeline"

from .read_pkl import load_and_validate_pkl, PKLReader, Detection, PKLMetadata
from .tracking import MultiObjectTracker, Track
from .analysis import TrajectoryAnalyzer, TrafficMetrics, Direction, TurnPattern, ROI
from .visualize import TrafficVisualizer

__all__ = [
    'load_and_validate_pkl',
    'PKLReader',
    'Detection',
    'PKLMetadata',
    'MultiObjectTracker',
    'Track',
    'TrajectoryAnalyzer',
    'TrafficMetrics',
    'Direction',
    'TurnPattern',
    'ROI',
    'TrafficVisualizer'
]
