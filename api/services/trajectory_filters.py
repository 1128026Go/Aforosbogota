"""
Filtros de Calidad para Trayectorias
Reglas para depurar trayectorias antes del conteo
"""

import numpy as np
from typing import List, Dict, Tuple, Optional


# Clases válidas permitidas para conteo
VALID_CLASSES = {
    'car', 'bus', 'motorcycle',
    'truck', 'truck_c1', 'truck_c2', 'truck_c3',
    'bicycle', 'person'
}


def calculate_total_distance(positions: List[Tuple[float, float]], pixels_per_meter: float = 20.0) -> float:
    """
    Calcula la distancia total real recorrida por una trayectoria

    Args:
        positions: Lista de posiciones [(x, y), ...]
        pixels_per_meter: Factor de conversión píxeles a metros (default: 20 px/m)

    Returns:
        Distancia total en metros
    """
    if len(positions) < 2:
        return 0.0

    total_distance_px = 0.0
    for i in range(1, len(positions)):
        x1, y1 = positions[i-1]
        x2, y2 = positions[i]
        dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        total_distance_px += dist

    return total_distance_px / pixels_per_meter


def calculate_duration_seconds(frames: List[int], fps: float = 30.0) -> float:
    """
    Calcula la duración de una trayectoria en segundos

    Args:
        frames: Lista de frame IDs
        fps: Frames por segundo del video

    Returns:
        Duración en segundos
    """
    if len(frames) < 2:
        return 0.0

    total_frames = max(frames) - min(frames) + 1
    return total_frames / fps


def is_inside_aoi(position: Tuple[float, float], bounds: Dict[str, float]) -> bool:
    """
    Verifica si una posición está dentro del área de interés

    Args:
        position: (x, y)
        bounds: {'min_x', 'max_x', 'min_y', 'max_y'}

    Returns:
        True si está dentro
    """
    x, y = position
    return (bounds['min_x'] <= x <= bounds['max_x'] and
            bounds['min_y'] <= y <= bounds['max_y'])


def calculate_aoi_percentage(positions: List[Tuple[float, float]], bounds: Dict[str, float]) -> float:
    """
    Calcula qué porcentaje de la trayectoria ocurre dentro del AOI

    Args:
        positions: Lista de posiciones
        bounds: Límites del área de interés

    Returns:
        Porcentaje (0.0 a 1.0)
    """
    if not positions:
        return 0.0

    inside_count = sum(1 for pos in positions if is_inside_aoi(pos, bounds))
    return inside_count / len(positions)


def calculate_direction_coherence(positions: List[Tuple[float, float]]) -> float:
    """
    Calcula la coherencia de dirección de una trayectoria
    Detecta cambios bruscos de dirección (zigzag)

    Args:
        positions: Lista de posiciones

    Returns:
        Score de coherencia (0.0 a 1.0, más alto = más coherente)
    """
    if len(positions) < 3:
        return 1.0  # Muy corta, asumimos coherente

    angles = []

    for i in range(1, len(positions) - 1):
        x1, y1 = positions[i-1]
        x2, y2 = positions[i]
        x3, y3 = positions[i+1]

        # Vectores
        v1 = np.array([x2 - x1, y2 - y1])
        v2 = np.array([x3 - x2, y3 - y2])

        # Magnitudes
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            continue

        # Ángulo entre vectores
        cos_angle = np.dot(v1, v2) / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle) * 180 / np.pi

        angles.append(angle)

    if not angles:
        return 1.0

    # Contar cambios bruscos (>90 grados)
    sharp_turns = sum(1 for angle in angles if angle > 90)

    # Score: penalizar cambios bruscos frecuentes
    coherence = 1.0 - (sharp_turns / len(angles))

    return coherence


def has_duplicate_track_id(track_id: str, all_tracks: List[Dict]) -> bool:
    """
    Detecta si un track_id aparece duplicado en diferentes zonas

    Args:
        track_id: ID del track a verificar
        all_tracks: Lista de todos los tracks

    Returns:
        True si hay duplicado
    """
    tracks_with_id = [t for t in all_tracks if t.get('track_id') == track_id]

    if len(tracks_with_id) <= 1:
        return False

    # Si hay múltiples tracks con mismo ID, verificar si están en zonas distintas
    # (simplificado: si sus posiciones iniciales están muy separadas)
    for i in range(len(tracks_with_id)):
        for j in range(i + 1, len(tracks_with_id)):
            pos1 = tracks_with_id[i]['positions'][0]
            pos2 = tracks_with_id[j]['positions'][0]

            x1, y1 = pos1 if isinstance(pos1, (list, tuple)) else (pos1, pos1)
            x2, y2 = pos2 if isinstance(pos2, (list, tuple)) else (pos2, pos2)

            dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

            # Si están a más de 200 px, es sospechoso
            if dist > 200:
                return True

    return False


def filter_trajectory(
    track: Dict,
    all_tracks: List[Dict],
    bounds: Optional[Dict[str, float]] = None,
    fps: float = 30.0,
    pixels_per_meter: float = 20.0,
    min_distance_meters: float = 10.0,  # 10m mínimos para vehículos (más estricto)
    min_duration_seconds: float = 1.0,  # 1.0s mínimo para eliminar glitches de vehículos
    min_aoi_percentage: float = 0.8,
    min_coherence: float = 0.3,  # Reducido a 0.3 para permitir zigzag natural del tracking
    check_duplicates: bool = True,
    validate_velocity: bool = False  # Desactivado: aceleraciones "imposibles" son artefactos del tracking
) -> Tuple[bool, str]:
    """
    Aplica todos los filtros de calidad a una trayectoria

    Args:
        track: Diccionario con datos del track
        all_tracks: Lista completa de tracks (para detección de duplicados)
        bounds: Límites del AOI (opcional)
        fps: Frames por segundo
        pixels_per_meter: Conversión píxeles a metros
        min_distance_meters: Distancia mínima real recorrida
        min_duration_seconds: Duración mínima
        min_aoi_percentage: Porcentaje mínimo dentro del AOI
        min_coherence: Score mínimo de coherencia de dirección
        check_duplicates: Si verificar duplicados

    Returns:
        (is_valid, reason) - True si pasa todos los filtros, False con razón si no
    """
    positions = track.get('positions', [])
    frames = track.get('frames', [])
    clase = track.get('class', '')
    track_id = track.get('track_id', '')

    # Regla 3: Clasificación válida
    if clase not in VALID_CLASSES:
        return False, f"Clase inválida: {clase}"

    # FILTROS DIFERENCIADOS PARA PEATONES
    is_pedestrian = clase in ['person', 'pedestrian', 'peaton']

    # Regla 1: Distancia mínima real recorrida (RELAJADO PARA PEATONES)
    distance = calculate_total_distance(positions, pixels_per_meter)
    min_dist = 1.0 if is_pedestrian else min_distance_meters  # Peatones: 1m vs Vehículos: 10m
    if distance < min_dist:
        return False, f"Distancia muy corta: {distance:.2f}m < {min_dist}m"

    # Regla 2: Duración mínima (RELAJADO PARA PEATONES)
    duration = calculate_duration_seconds(frames, fps)
    min_dur = 0.3 if is_pedestrian else min_duration_seconds  # Peatones: 0.3s vs Vehículos: 1.0s
    if duration < min_dur:
        return False, f"Duración muy corta: {duration:.2f}s < {min_dur}s"

    # Regla 4: Filtro por área de interés (si bounds está definido)
    if bounds is not None:
        aoi_pct = calculate_aoi_percentage(positions, bounds)
        if aoi_pct < min_aoi_percentage:
            return False, f"Fuera de AOI: {aoi_pct*100:.1f}% < {min_aoi_percentage*100:.1f}%"

    # Regla 5: Dirección coherente
    coherence = calculate_direction_coherence(positions)
    if coherence < min_coherence:
        return False, f"Dirección incoherente: score={coherence:.2f} < {min_coherence}"

    # Regla 6: No duplicados
    if check_duplicates and has_duplicate_track_id(track_id, all_tracks):
        return False, f"Track ID duplicado: {track_id}"

    # Regla 7: Validación de velocidad (OPCIÓN 1 + OPCIÓN 2)
    if validate_velocity:
        from services.velocity_validator import VelocityValidator

        validator = VelocityValidator(
            fps=fps,
            pixels_per_meter=pixels_per_meter,
            enable_avg_validation=True,   # Opción 1: Velocidad promedio
            enable_instant_validation=True  # Opción 2: Frame-a-frame
        )

        velocity_valid, velocity_issues = validator.validate_track(track)

        if not velocity_valid:
            # Retornar el primer issue encontrado
            return False, velocity_issues[0] if velocity_issues else "Velocidad inválida"

    return True, "OK"


def filter_tracks(
    tracks: List[Dict],
    bounds: Optional[Dict[str, float]] = None,
    fps: float = 30.0,
    pixels_per_meter: float = 20.0,
    min_distance_meters: float = 5.0,
    min_duration_seconds: float = 0.5,
    verbose: bool = True
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Filtra una lista de tracks aplicando todas las reglas de calidad

    Args:
        tracks: Lista de tracks a filtrar
        bounds: Límites del AOI
        fps: Frames por segundo
        pixels_per_meter: Conversión píxeles a metros
        verbose: Si imprimir estadísticas

    Returns:
        (filtered_tracks, stats) - Lista filtrada y diccionario con estadísticas
    """
    filtered = []
    rejection_reasons = {}

    for track in tracks:
        is_valid, reason = filter_trajectory(
            track=track,
            all_tracks=tracks,
            bounds=bounds,
            fps=fps,
            pixels_per_meter=pixels_per_meter,
            min_distance_meters=min_distance_meters,
            min_duration_seconds=min_duration_seconds
        )

        if is_valid:
            filtered.append(track)
        else:
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    stats = {
        'total': len(tracks),
        'accepted': len(filtered),
        'rejected': len(tracks) - len(filtered),
        'acceptance_rate': len(filtered) / len(tracks) if tracks else 0.0,
        'rejection_reasons': rejection_reasons
    }

    if verbose:
        print(f"\n[ESTADISTICAS] Filtrado de Trayectorias:")
        print(f"   Total: {stats['total']}")
        print(f"   [OK] Aceptadas: {stats['accepted']} ({stats['acceptance_rate']*100:.1f}%)")
        print(f"   [X] Rechazadas: {stats['rejected']}")

        if rejection_reasons:
            print(f"\n   Razones de rechazo:")
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
                print(f"      • {reason}: {count}")

    return filtered, stats
