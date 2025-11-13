"""
Servicio de clasificación RILSA basado exclusivamente en cardinales oficiales
NO usa coordenadas, vectores, ni ángulos para decidir códigos
"""

from typing import Optional, Dict


def assign_rilsa(origin_cardinal: str, dest_cardinal: str, rilsa_map: dict) -> Optional[int]:
    """
    Asigna código RILSA basado SOLO en cardinales oficiales

    Args:
        origin_cardinal: Cardinal oficial del acceso de origen (N/S/E/O)
        dest_cardinal: Cardinal oficial del acceso de destino (N/S/E/O)
        rilsa_map: Configuración de reglas RILSA del dataset

    Returns:
        Código RILSA (int) o None si no está definido

    IMPORTANTE:
    - Solo usa los cardinales oficiales asignados manualmente
    - No infiere nada de coordenadas geométricas
    - Si el par cardinal no está en las reglas, retorna None
    """
    pair = f"{origin_cardinal}->{dest_cardinal}"

    # 1. Buscar en movimientos rectos (prioridad)
    rectos = rilsa_map.get("rectos", {})
    if pair in rectos:
        return rectos[pair]

    # 2. Buscar en reglas específicas
    reglas = rilsa_map.get("reglas", {})
    if pair in reglas:
        return reglas[pair]

    # 3. No definido - retornar None
    # El usuario debe definir explícitamente todos los pares que desee clasificar
    return None


def get_movement_description(origin_cardinal: str, dest_cardinal: str, rilsa_code: Optional[int]) -> str:
    """
    Genera descripción legible del movimiento

    Args:
        origin_cardinal: Cardinal de origen
        dest_cardinal: Cardinal de destino
        rilsa_code: Código RILSA asignado

    Returns:
        Descripción del movimiento
    """
    if rilsa_code is None:
        return f"Sin clasificar ({origin_cardinal} → {dest_cardinal})"

    # Movimientos rectos (1-4)
    if rilsa_code in [1, 2, 3, 4]:
        return f"Recto RILSA {rilsa_code} ({origin_cardinal} → {dest_cardinal})"

    # Giros izquierda (5-8)
    if rilsa_code in [5, 6, 7, 8]:
        return f"Izquierda RILSA {rilsa_code} ({origin_cardinal} → {dest_cardinal})"

    # Giros derecha (91-94)
    if 91 <= rilsa_code <= 94:
        suffix = rilsa_code - 90
        return f"Derecha RILSA 9({suffix}) ({origin_cardinal} → {dest_cardinal})"

    # Retornos/U-turns (101-104)
    if 101 <= rilsa_code <= 104:
        suffix = rilsa_code - 100
        return f"Retorno RILSA 10({suffix}) ({origin_cardinal})"

    return f"RILSA {rilsa_code} ({origin_cardinal} → {dest_cardinal})"


def validate_rilsa_map(rilsa_map: dict, cardinals: list) -> list:
    """
    Valida que el mapa RILSA esté completo para los cardinales disponibles

    Args:
        rilsa_map: Configuración de reglas RILSA
        cardinals: Lista de cardinales disponibles ['N', 'S', 'E', 'O']

    Returns:
        Lista de pares no definidos (warnings)
    """
    missing_pairs = []

    for origin in cardinals:
        for dest in cardinals:
            pair = f"{origin}->{dest}"

            # Verificar si está en rectos o reglas
            in_rectos = pair in rilsa_map.get("rectos", {})
            in_reglas = pair in rilsa_map.get("reglas", {})

            if not in_rectos and not in_reglas:
                missing_pairs.append(pair)

    return missing_pairs
