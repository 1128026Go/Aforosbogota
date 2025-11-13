"""
Módulo de análisis de trayectorias y métricas de tráfico.

Calcula:
- Aforo (conteo de vehículos)
- Sentido de movimiento dominante
- Velocidades promedio y distribución
- Patrones de giro (izquierda, derecha, recto)
- Métricas de congestión
- Análisis de cruces peatonales
- Zonas de interés (ROI)
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Direcciones de movimiento."""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"
    STATIONARY = "stationary"


class TurnPattern(Enum):
    """Patrones de giro."""
    STRAIGHT = "straight"
    LEFT = "left"
    RIGHT = "right"
    U_TURN = "u_turn"
    COMPLEX = "complex"


@dataclass
class ROI:
    """Region of Interest (Región de Interés)."""
    name: str
    polygon: List[Tuple[float, float]]  # [(x, y), ...]
    roi_type: str = "generic"  # generic, intersection, crosswalk, etc.

    def contains_point(self, x: float, y: float) -> bool:
        """Verifica si un punto está dentro del ROI usando ray casting."""
        n = len(self.polygon)
        inside = False

        p1x, p1y = self.polygon[0]
        for i in range(n + 1):
            p2x, p2y = self.polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside


@dataclass
class TrafficMetrics:
    """Métricas de tráfico calculadas."""

    # Conteo
    total_vehicles: int = 0
    vehicles_by_class: Dict[str, int] = field(default_factory=dict)

    # Velocidades (píxeles/frame)
    avg_velocity_px: float = 0.0
    max_velocity_px: float = 0.0
    velocity_distribution: Dict[str, float] = field(default_factory=dict)  # class -> avg_velocity

    # Direcciones
    direction_distribution: Dict[str, int] = field(default_factory=dict)  # direction -> count

    # Patrones de giro
    turn_patterns: Dict[str, int] = field(default_factory=dict)  # pattern -> count

    # Congestión
    congestion_score: float = 0.0  # 0-1
    avg_track_density: float = 0.0  # tracks por unidad de área

    # ROI
    roi_counts: Dict[str, int] = field(default_factory=dict)  # roi_name -> count

    # Temporales
    temporal_distribution: Dict[int, int] = field(default_factory=dict)  # frame -> count

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            'total_vehicles': self.total_vehicles,
            'vehicles_by_class': self.vehicles_by_class,
            'avg_velocity_px': self.avg_velocity_px,
            'max_velocity_px': self.max_velocity_px,
            'velocity_distribution': self.velocity_distribution,
            'direction_distribution': self.direction_distribution,
            'turn_patterns': self.turn_patterns,
            'congestion_score': self.congestion_score,
            'avg_track_density': self.avg_track_density,
            'roi_counts': self.roi_counts
        }


class TrajectoryAnalyzer:
    """Analizador de trayectorias y métricas de tráfico."""

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        fps: float = 30.0,
        rois: Optional[List[ROI]] = None
    ):
        """
        Inicializa el analizador.

        Args:
            frame_width: Ancho del frame en píxeles
            frame_height: Alto del frame en píxeles
            fps: Frames por segundo del video
            rois: Lista de regiones de interés
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.rois = rois or []

    def calculate_direction(self, track: 'Track') -> Direction:
        """
        Calcula la dirección dominante de una trayectoria.

        Args:
            track: Trayectoria a analizar

        Returns:
            Dirección dominante
        """
        if len(track.positions) < 2:
            return Direction.STATIONARY

        # Calcular desplazamiento total
        start = track.positions[0]
        end = track.positions[-1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Si el desplazamiento es muy pequeño, es estacionario
        total_displacement = np.sqrt(dx**2 + dy**2)
        if total_displacement < 10:  # threshold en píxeles
            return Direction.STATIONARY

        # Calcular ángulo
        angle = np.arctan2(-dy, dx)  # -dy porque y crece hacia abajo
        angle_deg = np.degrees(angle)

        # Normalizar a [0, 360)
        if angle_deg < 0:
            angle_deg += 360

        # Clasificar dirección
        if 337.5 <= angle_deg or angle_deg < 22.5:
            return Direction.EAST
        elif 22.5 <= angle_deg < 67.5:
            return Direction.NORTHEAST
        elif 67.5 <= angle_deg < 112.5:
            return Direction.NORTH
        elif 112.5 <= angle_deg < 157.5:
            return Direction.NORTHWEST
        elif 157.5 <= angle_deg < 202.5:
            return Direction.WEST
        elif 202.5 <= angle_deg < 247.5:
            return Direction.SOUTHWEST
        elif 247.5 <= angle_deg < 292.5:
            return Direction.SOUTH
        else:  # 292.5 <= angle_deg < 337.5
            return Direction.SOUTHEAST

    def calculate_turn_pattern(self, track: 'Track') -> TurnPattern:
        """
        Detecta el patrón de giro de una trayectoria.

        Args:
            track: Trayectoria a analizar

        Returns:
            Patrón de giro
        """
        if len(track.positions) < 5:
            return TurnPattern.STRAIGHT

        # Calcular ángulos de giro entre segmentos consecutivos
        angles = []
        for i in range(1, len(track.positions) - 1):
            p1 = track.positions[i - 1]
            p2 = track.positions[i]
            p3 = track.positions[i + 1]

            v1 = (p2[0] - p1[0], p2[1] - p1[1])
            v2 = (p3[0] - p2[0], p3[1] - p2[1])

            # Calcular ángulo entre vectores
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            det = v1[0] * v2[1] - v1[1] * v2[0]
            angle = np.arctan2(det, dot)
            angles.append(np.degrees(angle))

        if not angles:
            return TurnPattern.STRAIGHT

        # Analizar distribución de ángulos
        total_turn = sum(angles)
        avg_turn = total_turn / len(angles)

        # Clasificar patrón
        if abs(avg_turn) < 10:
            return TurnPattern.STRAIGHT
        elif avg_turn > 90:
            return TurnPattern.LEFT
        elif avg_turn < -90:
            return TurnPattern.RIGHT
        elif abs(total_turn) > 150:
            return TurnPattern.U_TURN
        else:
            return TurnPattern.COMPLEX

    def calculate_velocity_magnitude(self, track: 'Track') -> Optional[float]:
        """
        Calcula la magnitud de velocidad promedio en píxeles/frame.

        Args:
            track: Trayectoria a analizar

        Returns:
            Velocidad promedio o None
        """
        velocity = track.get_velocity_px_per_frame()
        if velocity is None:
            return None

        vx, vy = velocity
        return np.sqrt(vx**2 + vy**2)

    def calculate_congestion_score(
        self,
        tracks: List['Track'],
        current_frame: int,
        window_frames: int = 30
    ) -> float:
        """
        Calcula un score de congestión basado en densidad de tracks.

        Args:
            tracks: Lista de trayectorias
            current_frame: Frame actual
            window_frames: Ventana temporal para análisis

        Returns:
            Score de congestión 0-1 (0=libre, 1=congestionado)
        """
        # Contar tracks activas en la ventana temporal
        active_tracks = [
            t for t in tracks
            if any(current_frame - window_frames <= f <= current_frame for f in t.frames)
        ]

        if not active_tracks:
            return 0.0

        # Calcular densidad espacial
        all_positions = []
        for track in active_tracks:
            # Solo posiciones en la ventana temporal
            for i, frame in enumerate(track.frames):
                if current_frame - window_frames <= frame <= current_frame:
                    all_positions.append(track.positions[i])

        if not all_positions:
            return 0.0

        # Área cubierta (simplificado)
        positions = np.array(all_positions)
        x_range = positions[:, 0].max() - positions[:, 0].min()
        y_range = positions[:, 1].max() - positions[:, 1].min()
        area = max(x_range * y_range, 1.0)

        # Densidad = número de posiciones / área
        density = len(all_positions) / area

        # Normalizar a [0, 1] (ajustar threshold según necesidad)
        # Asumiendo que 0.01 posiciones/píxel² es alta congestión
        congestion = min(density / 0.01, 1.0)

        return congestion

    def count_vehicles_in_roi(
        self,
        tracks: List['Track'],
        roi: ROI
    ) -> int:
        """
        Cuenta vehículos que pasaron por un ROI.

        Args:
            tracks: Lista de trayectorias
            roi: Región de interés

        Returns:
            Número de vehículos
        """
        count = 0
        for track in tracks:
            # Verificar si alguna posición está dentro del ROI
            for pos in track.positions:
                if roi.contains_point(pos[0], pos[1]):
                    count += 1
                    break  # Contar cada track solo una vez

        return count

    def analyze_tracks(
        self,
        tracks: List['Track'],
        current_frame: Optional[int] = None
    ) -> TrafficMetrics:
        """
        Analiza una lista de trayectorias y calcula métricas.

        Args:
            tracks: Lista de trayectorias
            current_frame: Frame actual (para análisis temporal)

        Returns:
            Objeto TrafficMetrics con todas las métricas
        """
        metrics = TrafficMetrics()

        if not tracks:
            logger.warning("No hay tracks para analizar")
            return metrics

        # Usar el último frame si no se especifica
        if current_frame is None:
            current_frame = max(max(t.frames) for t in tracks if t.frames)

        # Conteo total
        metrics.total_vehicles = len(tracks)

        # Conteo por clase
        for track in tracks:
            metrics.vehicles_by_class[track.clase] = metrics.vehicles_by_class.get(track.clase, 0) + 1

        # Velocidades
        velocities = []
        velocity_by_class = defaultdict(list)

        for track in tracks:
            vel = self.calculate_velocity_magnitude(track)
            if vel is not None:
                velocities.append(vel)
                velocity_by_class[track.clase].append(vel)

        if velocities:
            metrics.avg_velocity_px = float(np.mean(velocities))
            metrics.max_velocity_px = float(np.max(velocities))

            # Velocidad promedio por clase
            for clase, vels in velocity_by_class.items():
                metrics.velocity_distribution[clase] = float(np.mean(vels))

        # Direcciones
        for track in tracks:
            direction = self.calculate_direction(track)
            metrics.direction_distribution[direction.value] = \
                metrics.direction_distribution.get(direction.value, 0) + 1

        # Patrones de giro
        for track in tracks:
            pattern = self.calculate_turn_pattern(track)
            metrics.turn_patterns[pattern.value] = \
                metrics.turn_patterns.get(pattern.value, 0) + 1

        # Congestión
        metrics.congestion_score = self.calculate_congestion_score(tracks, current_frame)

        # Densidad de tracks
        frame_area = self.frame_width * self.frame_height
        metrics.avg_track_density = len(tracks) / frame_area

        # ROI counts
        for roi in self.rois:
            count = self.count_vehicles_in_roi(tracks, roi)
            metrics.roi_counts[roi.name] = count

        # Distribución temporal (histograma por frames)
        for track in tracks:
            for frame in track.frames:
                metrics.temporal_distribution[frame] = \
                    metrics.temporal_distribution.get(frame, 0) + 1

        logger.info(f"Análisis completado: {metrics.total_vehicles} vehículos analizados")
        return metrics

    def get_flow_rate(
        self,
        tracks: List['Track'],
        time_window_seconds: float = 60.0
    ) -> Dict[str, float]:
        """
        Calcula el flujo de vehículos (vehículos/minuto) por clase.

        Args:
            tracks: Lista de trayectorias
            time_window_seconds: Ventana temporal en segundos

        Returns:
            Diccionario {clase: vehículos_por_minuto}
        """
        if not tracks:
            return {}

        # Obtener rango temporal
        all_frames = []
        for track in tracks:
            all_frames.extend(track.frames)

        if not all_frames:
            return {}

        frame_range = max(all_frames) - min(all_frames)
        duration_seconds = frame_range / self.fps

        if duration_seconds == 0:
            return {}

        # Contar por clase
        flow_rates = {}
        for clase, count in self.analyze_tracks(tracks).vehicles_by_class.items():
            # Normalizar a vehículos por minuto
            flow_rates[clase] = (count / duration_seconds) * 60.0

        return flow_rates

    def identify_hotspots(
        self,
        tracks: List['Track'],
        grid_size: int = 50
    ) -> np.ndarray:
        """
        Identifica zonas calientes (hotspots) de tráfico en una grilla.

        Args:
            tracks: Lista de trayectorias
            grid_size: Tamaño de la celda de la grilla en píxeles

        Returns:
            Matriz 2D con densidad de tráfico por celda
        """
        # Crear grilla
        grid_h = (self.frame_height // grid_size) + 1
        grid_w = (self.frame_width // grid_size) + 1
        heatmap = np.zeros((grid_h, grid_w))

        # Contar posiciones en cada celda
        for track in tracks:
            for pos in track.positions:
                x, y = pos
                grid_x = int(x // grid_size)
                grid_y = int(y // grid_size)

                if 0 <= grid_x < grid_w and 0 <= grid_y < grid_h:
                    heatmap[grid_y, grid_x] += 1

        return heatmap

    def analyze_pedestrian_crossings(
        self,
        tracks: List['Track'],
        crosswalk_rois: List[ROI]
    ) -> Dict[str, int]:
        """
        Analiza cruces de peatones en zonas específicas.

        Args:
            tracks: Lista de trayectorias
            crosswalk_rois: Lista de ROIs que representan cruces peatonales

        Returns:
            Diccionario {crosswalk_name: número_de_cruces}
        """
        crossings = {}

        # Filtrar solo peatones
        pedestrian_tracks = [t for t in tracks if t.clase == 'person']

        for roi in crosswalk_rois:
            count = self.count_vehicles_in_roi(pedestrian_tracks, roi)
            crossings[roi.name] = count

        return crossings


def create_default_rois(frame_width: int, frame_height: int) -> List[ROI]:
    """
    Crea ROIs por defecto para análisis general.

    Args:
        frame_width: Ancho del frame
        frame_height: Alto del frame

    Returns:
        Lista de ROIs
    """
    rois = []

    # Zona central (intersección)
    center_x, center_y = frame_width / 2, frame_height / 2
    margin = 100

    rois.append(ROI(
        name="center_intersection",
        polygon=[
            (center_x - margin, center_y - margin),
            (center_x + margin, center_y - margin),
            (center_x + margin, center_y + margin),
            (center_x - margin, center_y + margin)
        ],
        roi_type="intersection"
    ))

    # Zonas de entrada/salida
    edge_margin = 50

    rois.append(ROI(
        name="north_entry",
        polygon=[
            (0, 0),
            (frame_width, 0),
            (frame_width, edge_margin),
            (0, edge_margin)
        ],
        roi_type="entry"
    ))

    rois.append(ROI(
        name="south_exit",
        polygon=[
            (0, frame_height - edge_margin),
            (frame_width, frame_height - edge_margin),
            (frame_width, frame_height),
            (0, frame_height)
        ],
        roi_type="exit"
    ))

    return rois


if __name__ == "__main__":
    print("Módulo de análisis de tráfico")
    print("Usa este módulo importándolo en tu código principal")
