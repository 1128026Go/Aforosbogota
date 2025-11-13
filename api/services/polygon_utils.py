"""
Utilidades para detección de puntos en polígonos
"""

from typing import List, Tuple


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """
    Determina si un punto está dentro de un polígono usando el algoritmo ray-casting.

    Args:
        point: Tupla (x, y) del punto a verificar
        polygon: Lista de tuplas (x, y) que definen los vértices del polígono

    Returns:
        True si el punto está dentro del polígono, False si está fuera

    Algoritmo:
        Ray-casting: Traza un rayo desde el punto hacia el infinito y cuenta
        cuántas veces cruza los bordes del polígono. Si es impar, está dentro.
    """
    if len(polygon) < 3:
        return False

    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]

        # Verificar si el punto está en el rango vertical del segmento
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    # Calcular intersección del rayo con el segmento
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

                    # Si el segmento es vertical o el punto está a la izquierda
                    if p1x == p2x or x <= xinters:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def get_cardinal_from_position(
    position: Tuple[float, float],
    cardinal_zones: dict
) -> str:
    """
    Determina el cardinal de un punto basándose en zonas poligonales.

    Args:
        position: Tupla (x, y) de la posición a verificar
        cardinal_zones: Dict con estructura:
            {
                "N": {"polygon": [(x1,y1), (x2,y2), ...]},
                "S": {"polygon": [...]},
                ...
            }

    Returns:
        Cardinal ('N', 'S', 'E', 'O') o None si no está en ninguna zona
    """
    for cardinal, zone_data in cardinal_zones.items():
        polygon = zone_data.get('polygon', [])
        if len(polygon) >= 3:
            # Convertir a tuplas si viene como lista de listas
            polygon_tuples = [tuple(p) if isinstance(p, list) else p for p in polygon]

            if point_in_polygon(position, polygon_tuples):
                return cardinal

    return None


def trajectory_enters_zone(
    trajectory: List[Tuple[float, float]],
    zone_polygon: List[Tuple[float, float]],
    check_first_n: int = 5
) -> bool:
    """
    Verifica si una trayectoria entra en una zona poligonal.

    Args:
        trajectory: Lista de posiciones (x, y) de la trayectoria
        zone_polygon: Polígono que define la zona
        check_first_n: Número de primeros puntos a verificar

    Returns:
        True si alguno de los primeros N puntos está dentro de la zona
    """
    if len(trajectory) == 0 or len(zone_polygon) < 3:
        return False

    # Verificar los primeros N puntos
    points_to_check = trajectory[:min(check_first_n, len(trajectory))]

    for point in points_to_check:
        if point_in_polygon(point, zone_polygon):
            return True

    return False


def trajectory_exits_zone(
    trajectory: List[Tuple[float, float]],
    zone_polygon: List[Tuple[float, float]],
    check_last_n: int = 5
) -> bool:
    """
    Verifica si una trayectoria sale de una zona poligonal.

    Args:
        trajectory: Lista de posiciones (x, y) de la trayectoria
        zone_polygon: Polígono que define la zona
        check_last_n: Número de últimos puntos a verificar

    Returns:
        True si alguno de los últimos N puntos está dentro de la zona
    """
    if len(trajectory) == 0 or len(zone_polygon) < 3:
        return False

    # Verificar los últimos N puntos
    points_to_check = trajectory[-min(check_last_n, len(trajectory)):]

    for point in points_to_check:
        if point_in_polygon(point, zone_polygon):
            return True

    return False
