"""
Funciones helper para transformaciones de coordenadas y mapeo de colores.

Este módulo proporciona utilidades para:
- Transformación de coordenadas píxel → lat/lon (relativo)
- Transformación píxel → CARLA coords
- Mapeo de colores para clases y direcciones
- Calibración y escalado de coordenadas
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class CalibrationConfig:
    """
    Configuración de calibración para transformaciones de coordenadas.

    IMPORTANTE: Estos valores son PLACEHOLDERS que deben ser calibrados
    manualmente según tu caso de uso específico.

    Para calibrar correctamente:
    1. Identifica puntos de referencia conocidos en el video
    2. Obtén sus coordenadas reales (GPS o CARLA)
    3. Ajusta los parámetros para que coincidan
    """

    # === CALIBRACIÓN PÍXEL → METROS ===
    # ¿Cuántos píxeles equivalen a 1 metro en el mundo real?
    # AJUSTAR: Mide un objeto conocido en píxeles y en metros
    pixels_per_meter: float = 20.0  # Ejemplo: 20 píxeles = 1 metro

    # === CALIBRACIÓN PÍXEL → LAT/LON (OpenStreetMap) ===
    # Coordenadas GPS de la esquina superior izquierda del frame (píxel 0,0)
    # AJUSTAR: Usa Google Maps para obtener las coordenadas exactas
    origin_lat: float = 4.6097  # Ejemplo: Bogotá norte
    origin_lon: float = -74.0817

    # Coordenadas GPS de la esquina inferior derecha del frame
    # AJUSTAR: Identifica el punto opuesto en el mapa
    corner_lat: float = 4.6085  # Ejemplo: ~150m al sur
    corner_lon: float = -74.0805  # Ejemplo: ~100m al este

    # Dimensiones del frame en píxeles
    frame_width: int = 1280
    frame_height: int = 720

    # === CALIBRACIÓN PÍXEL → CARLA ===
    # Origen CARLA (coordenadas x, y, z en CARLA que corresponden al píxel 0,0)
    # AJUSTAR: Encuentra el punto de origen en tu mapa CARLA
    carla_origin_x: float = 0.0
    carla_origin_y: float = 0.0
    carla_origin_z: float = 0.5  # Altura de spawn

    # Escala píxel → CARLA (metros por píxel)
    # AJUSTAR: Basado en la escala del mundo CARLA
    carla_scale: float = 0.05  # 0.05 metros por píxel

    # Rotación del frame respecto al norte de CARLA (grados)
    # AJUSTAR: Si el frame está rotado respecto al mapa
    carla_rotation: float = 0.0

    # Invertir eje Y (video: Y crece hacia abajo, CARLA: Y crece hacia arriba)
    flip_y: bool = True

    def save(self, path: str):
        """Guarda la configuración a JSON."""
        config = {
            'pixels_per_meter': self.pixels_per_meter,
            'origin_lat': self.origin_lat,
            'origin_lon': self.origin_lon,
            'corner_lat': self.corner_lat,
            'corner_lon': self.corner_lon,
            'frame_width': self.frame_width,
            'frame_height': self.frame_height,
            'carla_origin_x': self.carla_origin_x,
            'carla_origin_y': self.carla_origin_y,
            'carla_origin_z': self.carla_origin_z,
            'carla_scale': self.carla_scale,
            'carla_rotation': self.carla_rotation,
            'flip_y': self.flip_y
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'CalibrationConfig':
        """Carga configuración desde JSON."""
        with open(path, 'r') as f:
            config = json.load(f)
        return cls(**config)


class CoordinateTransformer:
    """Transforma coordenadas entre diferentes sistemas de referencia."""

    def __init__(self, config: CalibrationConfig):
        """
        Inicializa el transformador.

        Args:
            config: Configuración de calibración
        """
        self.config = config

        # Pre-calcular factores de conversión lat/lon
        self._lat_per_pixel = (config.corner_lat - config.origin_lat) / config.frame_height
        self._lon_per_pixel = (config.corner_lon - config.origin_lon) / config.frame_width

    def pixel_to_latlon(self, px: float, py: float) -> Tuple[float, float]:
        """
        Convierte coordenadas píxel a lat/lon.

        NOTA: Esta es una transformación lineal simplificada que asume
        que el frame está alineado con lat/lon (sin rotación).
        Para mayor precisión, usar homografía de 4 puntos.

        Args:
            px: Coordenada X en píxeles
            py: Coordenada Y en píxeles

        Returns:
            Tupla (latitud, longitud)
        """
        lat = self.config.origin_lat + (py * self._lat_per_pixel)
        lon = self.config.origin_lon + (px * self._lon_per_pixel)

        return lat, lon

    def pixel_to_meters(self, px: float, py: float) -> Tuple[float, float]:
        """
        Convierte coordenadas píxel a metros (relativo al origen).

        Args:
            px: Coordenada X en píxeles
            py: Coordenada Y en píxeles

        Returns:
            Tupla (metros_x, metros_y)
        """
        meters_x = px / self.config.pixels_per_meter
        meters_y = py / self.config.pixels_per_meter

        return meters_x, meters_y

    def pixel_to_carla(self, px: float, py: float) -> Tuple[float, float, float]:
        """
        Convierte coordenadas píxel a coordenadas CARLA.

        Aplica:
        1. Escalado píxel → metros
        2. Inversión de eje Y si está configurado
        3. Rotación si está configurada
        4. Traslación al origen CARLA

        Args:
            px: Coordenada X en píxeles
            py: Coordenada Y en píxeles

        Returns:
            Tupla (carla_x, carla_y, carla_z)
        """
        # Escalar a metros
        mx = px * self.config.carla_scale
        my = py * self.config.carla_scale

        # Invertir Y si es necesario
        if self.config.flip_y:
            my = -my

        # Aplicar rotación si existe
        if self.config.carla_rotation != 0:
            angle_rad = np.radians(self.config.carla_rotation)
            mx_rot = mx * np.cos(angle_rad) - my * np.sin(angle_rad)
            my_rot = mx * np.sin(angle_rad) + my * np.cos(angle_rad)
            mx, my = mx_rot, my_rot

        # Trasladar al origen CARLA
        carla_x = self.config.carla_origin_x + mx
        carla_y = self.config.carla_origin_y + my
        carla_z = self.config.carla_origin_z

        return carla_x, carla_y, carla_z

    def transform_trajectory(
        self,
        trajectory: List[Tuple[float, float]],
        target_system: str = 'latlon'
    ) -> List[Tuple[float, float]]:
        """
        Transforma una trayectoria completa a otro sistema.

        Args:
            trajectory: Lista de puntos (px, py)
            target_system: 'latlon', 'meters', o 'carla'

        Returns:
            Lista de puntos transformados
        """
        if target_system == 'latlon':
            return [self.pixel_to_latlon(px, py) for px, py in trajectory]
        elif target_system == 'meters':
            return [self.pixel_to_meters(px, py) for px, py in trajectory]
        elif target_system == 'carla':
            return [(x, y) for x, y, z in
                    [self.pixel_to_carla(px, py) for px, py in trajectory]]
        else:
            raise ValueError(f"Sistema desconocido: {target_system}")


# Paletas de colores predefinidas
COLOR_SCHEMES = {
    'class': {
        'car': '#3498db',
        'truck': '#e74c3c',
        'bus': '#9b59b6',
        'motorcycle': '#f39c12',
        'bicycle': '#2ecc71',
        'person': '#1abc9c',
        'traffic light': '#e67e22'
    },
    'direction': {
        'north': '#3498db',
        'south': '#e74c3c',
        'east': '#2ecc71',
        'west': '#f39c12',
        'northeast': '#9b59b6',
        'northwest': '#1abc9c',
        'southeast': '#e67e22',
        'southwest': '#95a5a6',
        'stationary': '#7f8c8d'
    },
    'speed': {
        'very_slow': '#3498db',    # 0-2 px/frame
        'slow': '#2ecc71',         # 2-5 px/frame
        'medium': '#f39c12',       # 5-10 px/frame
        'fast': '#e74c3c',         # 10+ px/frame
    },
    'pattern': {
        'straight': '#3498db',
        'left': '#2ecc71',
        'right': '#f39c12',
        'u_turn': '#e74c3c',
        'complex': '#9b59b6'
    }
}


def get_color_for_track(track: dict, color_by: str = 'class') -> str:
    """
    Obtiene el color apropiado para una trayectoria.

    Args:
        track: Diccionario con datos de trayectoria
        color_by: Atributo por el cual colorear ('class', 'direction', 'speed', 'pattern')

    Returns:
        Color en formato hexadecimal
    """
    if color_by == 'class':
        return COLOR_SCHEMES['class'].get(track.get('clase', 'unknown'), '#95a5a6')

    elif color_by == 'direction':
        # Necesita cálculo de dirección
        return COLOR_SCHEMES['direction'].get(track.get('direction', 'stationary'), '#7f8c8d')

    elif color_by == 'speed':
        # Calcular velocidad promedio
        avg_speed = track.get('avg_speed', 0)
        if avg_speed < 2:
            return COLOR_SCHEMES['speed']['very_slow']
        elif avg_speed < 5:
            return COLOR_SCHEMES['speed']['slow']
        elif avg_speed < 10:
            return COLOR_SCHEMES['speed']['medium']
        else:
            return COLOR_SCHEMES['speed']['fast']

    elif color_by == 'pattern':
        return COLOR_SCHEMES['pattern'].get(track.get('pattern', 'straight'), '#3498db')

    return '#95a5a6'  # Color por defecto


def create_default_calibration(
    frame_width: int,
    frame_height: int,
    output_path: Optional[str] = None
) -> CalibrationConfig:
    """
    Crea una configuración de calibración por defecto.

    IMPORTANTE: Esta es una configuración PLACEHOLDER.
    Debe ser ajustada según tu caso de uso específico.

    Args:
        frame_width: Ancho del frame en píxeles
        frame_height: Alto del frame en píxeles
        output_path: Ruta opcional para guardar la configuración

    Returns:
        CalibrationConfig con valores por defecto
    """
    config = CalibrationConfig(
        frame_width=frame_width,
        frame_height=frame_height
    )

    if output_path:
        config.save(output_path)
        print(f"Configuración por defecto guardada en: {output_path}")
        print("⚠️  IMPORTANTE: Edita este archivo con valores reales para tu caso de uso")

    return config


def calculate_bounds(trajectories: List[dict]) -> Dict[str, float]:
    """
    Calcula los límites (bounding box) de un conjunto de trayectorias.

    Args:
        trajectories: Lista de trayectorias con 'positions'

    Returns:
        Dict con min_x, max_x, min_y, max_y
    """
    all_x = []
    all_y = []

    for track in trajectories:
        for pos in track.get('positions', []):
            all_x.append(pos[0])
            all_y.append(pos[1])

    if not all_x:
        return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}

    return {
        'min_x': min(all_x),
        'max_x': max(all_x),
        'min_y': min(all_y),
        'max_y': max(all_y)
    }


if __name__ == "__main__":
    # Crear configuración de ejemplo
    config = create_default_calibration(
        frame_width=1280,
        frame_height=720,
        output_path="config/calibration.json"
    )

    # Ejemplo de uso
    transformer = CoordinateTransformer(config)

    # Punto de ejemplo (centro del frame)
    px, py = 640, 360

    lat, lon = transformer.pixel_to_latlon(px, py)
    mx, my = transformer.pixel_to_meters(px, py)
    cx, cy, cz = transformer.pixel_to_carla(px, py)

    print(f"\nPíxel ({px}, {py}) transformado a:")
    print(f"  Lat/Lon: ({lat:.6f}, {lon:.6f})")
    print(f"  Metros: ({mx:.2f}, {my:.2f})")
    print(f"  CARLA: ({cx:.2f}, {cy:.2f}, {cz:.2f})")
