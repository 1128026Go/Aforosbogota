"""
Validación de Velocidad para Trayectorias
Detecta anomalías basadas en velocidad esperada por tipo de vehículo
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


# Rangos de velocidad esperados por clase (m/s)
# CONFIGURACIÓN URBANA ESTRICTA (intersecciones)
SPEED_RANGES = {
    'car': {'min': 0.5, 'max': 22.0},       # ~2-80 km/h (urbano típico: 10-50 km/h)
    'bus': {'min': 0.5, 'max': 18.0},       # ~2-65 km/h (más lento en ciudad)
    'truck': {'min': 0.5, 'max': 18.0},     # Similar a bus
    'motorcycle': {'min': 0.5, 'max': 25.0},  # ~2-90 km/h (más ágiles pero urbano)
    'bicycle': {'min': 0.3, 'max': 10.0},   # ~1-36 km/h (urbano: 10-20 km/h)
    'person': {'min': 0.2, 'max': 5.0}      # ~1-18 km/h (caminando: 4-6 km/h)
}

# Aceleración máxima permitida por clase (m/s²)
MAX_ACCELERATION = {
    'car': 4.5,        # Aceleración/frenado normal urbano
    'bus': 2.5,        # Más pesados
    'truck': 2.0,      # Más inercia
    'motorcycle': 6.0,  # Muy ágiles
    'bicycle': 3.0,    # Moderado
    'person': 2.5      # Cambios de ritmo al caminar/correr
}

# Velocidad instantánea máxima absoluta (detectar teleportaciones)
# Esto es más estricto que max speed para detectar errores de tracking
MAX_INSTANT_SPEED = {
    'car': 70.0,       # 252 km/h - solo para detectar errores graves
    'bus': 55.0,       # 198 km/h
    'truck': 55.0,
    'motorcycle': 80.0,  # 288 km/h
    'bicycle': 25.0,   # 90 km/h
    'person': 10.0     # 36 km/h
}


class VelocityValidator:
    """
    Valida trayectorias basándose en velocidad y aceleración
    """

    def __init__(
        self,
        fps: float = 30.0,
        pixels_per_meter: float = 20.0,
        enable_avg_validation: bool = True,
        enable_instant_validation: bool = True
    ):
        """
        Args:
            fps: Frames por segundo del video
            pixels_per_meter: Factor de conversión píxeles a metros
            enable_avg_validation: Activar validación de velocidad promedio (Opción 1)
            enable_instant_validation: Activar validación frame-a-frame (Opción 2)
        """
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        self.enable_avg_validation = enable_avg_validation
        self.enable_instant_validation = enable_instant_validation

    def validate_track(
        self,
        track: Dict,
        verbose: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Valida una trayectoria completa

        Args:
            track: Diccionario con trayectoria
            verbose: Si imprimir detalles

        Returns:
            (is_valid, issues) - True si pasa validación, lista de problemas
        """
        issues = []
        positions = track.get('positions', [])
        frames = track.get('frames', [])
        clase = track.get('class', 'car')
        track_id = track.get('track_id', 'unknown')

        if len(positions) < 2 or len(frames) < 2:
            return True, []  # Muy corta para validar velocidad

        # Normalizar clase (consolidar variantes de truck)
        if clase.startswith('truck_'):
            clase = 'truck'

        # Usar rangos por defecto si clase no está definida
        if clase not in SPEED_RANGES:
            clase = 'car'

        # OPCIÓN 1: Validación de velocidad promedio
        if self.enable_avg_validation:
            avg_valid, avg_issues = self._validate_average_speed(
                positions, frames, clase, track_id
            )
            if not avg_valid:
                issues.extend(avg_issues)

        # OPCIÓN 2: Validación frame-a-frame
        if self.enable_instant_validation:
            instant_valid, instant_issues = self._validate_instant_speed(
                positions, frames, clase, track_id, verbose
            )
            if not instant_valid:
                issues.extend(instant_issues)

        is_valid = len(issues) == 0

        return is_valid, issues

    def _validate_average_speed(
        self,
        positions: List[Tuple[float, float]],
        frames: List[int],
        clase: str,
        track_id: str
    ) -> Tuple[bool, List[str]]:
        """
        OPCIÓN 1: Valida velocidad promedio de la trayectoria completa

        Returns:
            (is_valid, issues)
        """
        issues = []

        # Calcular distancia total recorrida
        total_distance_px = 0.0
        for i in range(1, len(positions)):
            pos_prev = positions[i-1]
            pos_curr = positions[i]

            if isinstance(pos_prev, (list, tuple)) and isinstance(pos_curr, (list, tuple)):
                x1, y1 = float(pos_prev[0]), float(pos_prev[1])
                x2, y2 = float(pos_curr[0]), float(pos_curr[1])
                dist_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                total_distance_px += dist_px

        # Convertir a metros
        total_distance_m = total_distance_px / self.pixels_per_meter

        # Calcular duración total
        frame_start = min(frames)
        frame_end = max(frames)
        duration_frames = frame_end - frame_start + 1
        duration_seconds = duration_frames / self.fps

        if duration_seconds == 0:
            return True, []

        # Velocidad promedio (m/s)
        avg_speed = total_distance_m / duration_seconds

        # Verificar rangos
        speed_range = SPEED_RANGES.get(clase, SPEED_RANGES['car'])
        min_speed = speed_range['min']
        max_speed = speed_range['max']

        if avg_speed < min_speed:
            issues.append(
                f"[AVG] Velocidad promedio muy baja: {avg_speed:.2f} m/s < {min_speed} m/s ({avg_speed*3.6:.1f} km/h)"
            )

        if avg_speed > max_speed:
            issues.append(
                f"[AVG] Velocidad promedio muy alta: {avg_speed:.2f} m/s > {max_speed} m/s ({avg_speed*3.6:.1f} km/h)"
            )

        is_valid = len(issues) == 0
        return is_valid, issues

    def _validate_instant_speed(
        self,
        positions: List[Tuple[float, float]],
        frames: List[int],
        clase: str,
        track_id: str,
        verbose: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        OPCIÓN 2: Valida velocidad frame-a-frame

        Detecta:
        - Teleportaciones (velocidad instantánea > umbral físico)
        - Aceleraciones imposibles
        - Cambios bruscos de velocidad

        Returns:
            (is_valid, issues)
        """
        issues = []
        teleportations = []
        impossible_accelerations = []

        max_instant = MAX_INSTANT_SPEED.get(clase, MAX_INSTANT_SPEED['car'])
        max_accel = MAX_ACCELERATION.get(clase, MAX_ACCELERATION['car'])

        prev_speed = None

        for i in range(1, len(positions)):
            pos_prev = positions[i-1]
            pos_curr = positions[i]
            frame_prev = frames[i-1]
            frame_curr = frames[i]

            if not (isinstance(pos_prev, (list, tuple)) and isinstance(pos_curr, (list, tuple))):
                continue

            x1, y1 = float(pos_prev[0]), float(pos_prev[1])
            x2, y2 = float(pos_curr[0]), float(pos_curr[1])

            # Distancia entre frames consecutivos
            dist_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            dist_m = dist_px / self.pixels_per_meter

            # Tiempo entre frames
            frame_gap = frame_curr - frame_prev
            if frame_gap == 0:
                continue

            time_gap = frame_gap / self.fps

            # Velocidad instantánea (m/s)
            instant_speed = dist_m / time_gap

            # DETECCIÓN DE TELEPORTACIÓN
            if instant_speed > max_instant:
                teleportations.append({
                    'frame': frame_curr,
                    'speed': instant_speed,
                    'speed_kmh': instant_speed * 3.6,
                    'distance': dist_m
                })

            # DETECCIÓN DE ACELERACIÓN IMPOSIBLE
            if prev_speed is not None:
                delta_speed = abs(instant_speed - prev_speed)
                acceleration = delta_speed / time_gap

                if acceleration > max_accel:
                    impossible_accelerations.append({
                        'frame': frame_curr,
                        'acceleration': acceleration,
                        'prev_speed': prev_speed,
                        'curr_speed': instant_speed
                    })

            prev_speed = instant_speed

        # Reportar problemas encontrados
        if teleportations:
            # Solo reportar si hay muchas teleportaciones (>10% de frames)
            teleport_ratio = len(teleportations) / len(positions)

            if teleport_ratio > 0.1:
                worst_teleport = max(teleportations, key=lambda x: x['speed'])
                issues.append(
                    f"[INSTANT] Teleportaciones detectadas: {len(teleportations)} "
                    f"({teleport_ratio*100:.1f}% de frames). "
                    f"Peor caso: {worst_teleport['speed']:.1f} m/s ({worst_teleport['speed_kmh']:.1f} km/h) "
                    f"en frame {worst_teleport['frame']}"
                )

        if impossible_accelerations:
            # Similar: solo reportar si es frecuente
            accel_ratio = len(impossible_accelerations) / len(positions)

            if accel_ratio > 0.1:
                worst_accel = max(impossible_accelerations, key=lambda x: x['acceleration'])
                issues.append(
                    f"[INSTANT] Aceleraciones imposibles: {len(impossible_accelerations)} "
                    f"({accel_ratio*100:.1f}% de frames). "
                    f"Peor caso: {worst_accel['acceleration']:.1f} m/s² en frame {worst_accel['frame']}"
                )

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_speed_stats(self, track: Dict) -> Dict:
        """
        Calcula estadísticas de velocidad para una trayectoria

        Returns:
            {
                'avg_speed_ms': float,
                'avg_speed_kmh': float,
                'max_instant_speed_ms': float,
                'max_instant_speed_kmh': float,
                'min_instant_speed_ms': float,
                'speeds_histogram': list
            }
        """
        positions = track.get('positions', [])
        frames = track.get('frames', [])

        if len(positions) < 2:
            return None

        # Velocidad promedio
        total_distance_px = sum(
            np.sqrt((float(positions[i][0]) - float(positions[i-1][0]))**2 +
                   (float(positions[i][1]) - float(positions[i-1][1]))**2)
            for i in range(1, len(positions))
            if isinstance(positions[i], (list, tuple)) and isinstance(positions[i-1], (list, tuple))
        )

        total_distance_m = total_distance_px / self.pixels_per_meter
        duration_s = (max(frames) - min(frames) + 1) / self.fps
        avg_speed_ms = total_distance_m / duration_s if duration_s > 0 else 0

        # Velocidades instantáneas
        instant_speeds = []
        for i in range(1, len(positions)):
            if isinstance(positions[i], (list, tuple)) and isinstance(positions[i-1], (list, tuple)):
                x1, y1 = float(positions[i-1][0]), float(positions[i-1][1])
                x2, y2 = float(positions[i][0]), float(positions[i][1])
                dist_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                dist_m = dist_px / self.pixels_per_meter

                frame_gap = frames[i] - frames[i-1]
                time_gap = frame_gap / self.fps if frame_gap > 0 else 1/self.fps

                instant_speed = dist_m / time_gap
                instant_speeds.append(instant_speed)

        max_instant = max(instant_speeds) if instant_speeds else 0
        min_instant = min(instant_speeds) if instant_speeds else 0

        return {
            'avg_speed_ms': round(avg_speed_ms, 2),
            'avg_speed_kmh': round(avg_speed_ms * 3.6, 2),
            'max_instant_speed_ms': round(max_instant, 2),
            'max_instant_speed_kmh': round(max_instant * 3.6, 2),
            'min_instant_speed_ms': round(min_instant, 2),
            'min_instant_speed_kmh': round(min_instant * 3.6, 2),
            'instant_speeds': instant_speeds
        }
