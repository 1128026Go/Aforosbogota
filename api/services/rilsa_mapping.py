"""
Lógica de mapeo RILSA con convención estricta.

Convenciones:
  - Índices 1..4 asignados siguiendo el sentido antihorario N (0°), O (90°), S (180°), E (270°).
  - Movimientos rectos -> "1".."4".
  - Izquierda -> "5".."8".
  - Derecha -> "9_1".."9_4".
  - Retorno -> "10_1".."10_4".
  - Peatones -> "P1".."P4".
"""
from __future__ import annotations

from math import atan2, degrees
from typing import Dict, List, Tuple


CARDINAL_ORDER = ["N", "O", "S", "E"]


def _angle_for_cardinal(cardinal: str) -> float:
    """Devuelve el ángulo estándar (grados) para un cardinal."""
    normalized = cardinal.upper()
    mapping = {"N": 0.0, "O": 90.0, "W": 90.0, "S": 180.0, "E": 270.0}
    return mapping.get(normalized, 0.0)


def order_accesses_for_rilsa(accesses: List[Dict]) -> List[Dict]:
    """
    Ordena y enriquece los accesos con un índice RILSA basado en el cardinal.
    Accesos sin cardinal conocido se ubican al final conservando orden original.
    """
    def sort_key(access: Dict) -> Tuple[int, float]:
        cardinal = str(access.get("cardinal", "")).upper()
        if cardinal in CARDINAL_ORDER:
            return CARDINAL_ORDER.index(cardinal), 0.0
        # fallback: usar ángulo aproximado desde origen si se dispone de coordenadas
        x = float(access.get("x", 0.0))
        y = float(access.get("y", 0.0))
        angle = (degrees(atan2(y, x)) + 360.0) % 360.0
        return len(CARDINAL_ORDER), angle

    ordered = sorted(accesses, key=sort_key)
    for idx, access in enumerate(ordered, start=1):
        access["rilsa_index"] = idx
    return ordered


def _movement_class(origin_card: str, dest_card: str) -> str:
    """Determina la clase de movimiento basada en el orden cardinal."""
    origin = origin_card.upper()
    dest = dest_card.upper()
    order = CARDINAL_ORDER
    if origin not in order or dest not in order:
        return "unknown"
    o_idx = order.index(origin)
    d_idx = order.index(dest)
    diff = (d_idx - o_idx) % len(order)
    if diff == 0:
        return "return"
    if diff == 2:
        return "straight"
    if diff == 1:
        return "right_turn"
    if diff == 3:
        return "left_turn"
    return "unknown"


def movement_code_for_vehicle(origin_access: Dict, dest_access: Dict) -> str:
    """Convierte origen/destino en código RILSA vehicular según convención."""
    idx = int(origin_access.get("rilsa_index", 1))
    cls = _movement_class(str(origin_access.get("cardinal", "")), str(dest_access.get("cardinal", "")))
    if cls == "straight":
        return str(1 + (idx - 1))
    if cls == "left_turn":
        return str(5 + (idx - 1))
    if cls == "right_turn":
        return f"9_{idx}"
    if cls == "return":
        return f"10_{idx}"
    return f"99_{origin_access.get('id')}_{dest_access.get('id')}"


def movement_code_for_pedestrian(origin_access: Dict) -> str:
    """Asigna códigos peatonales tipo P1..P4 usando el índice RILSA de origen."""
    idx = int(origin_access.get("rilsa_index", 1))
    return f"P{idx}"


def build_rilsa_rule_map(accesses: List[Dict]) -> Dict:
    """
    Genera un mapa RILSA completo con reglas por par (origen, destino).

    Retorna:
      {
        "rules": [...],
        "metadata": {...}
      }
    """
    ordered = order_accesses_for_rilsa(accesses)
    id_lookup = {acc["id"]: acc for acc in ordered}
    rules = []
    for ori in ordered:
        for dst in ordered:
            if ori["id"] == dst["id"]:
                # Retornos explícitos
                vehicle_code = movement_code_for_vehicle(ori, dst)
            else:
                vehicle_code = movement_code_for_vehicle(ori, dst)
            pedestrian_code = movement_code_for_pedestrian(ori)
            rules.append(
                {
                    "origin_id": ori["id"],
                    "dest_id": dst["id"],
                    "movement_class": _movement_class(ori["cardinal"], dst["cardinal"]),
                    "vehicle_code": vehicle_code,
                    "pedestrian_code": pedestrian_code,
                }
            )
    return {
        "rules": rules,
        "metadata": {
            "num_accesses": len(accesses),
            "num_rules": len(rules),
        },
        "accesses": ordered,
    }


def build_lookup_tables(rilsa_map: Dict) -> Tuple[Dict[Tuple[str, str], str], Dict[Tuple[str, str], str]]:
    """
    Construye tablas de consulta para movimientos vehiculares y peatonales.
    """
    veh: Dict[Tuple[str, str], str] = {}
    ped: Dict[Tuple[str, str], str] = {}
    for rule in rilsa_map.get("rules", []):
        key = (rule["origin_id"], rule["dest_id"])
        veh[key] = rule.get("vehicle_code", "")
        ped[key] = rule.get("pedestrian_code", "")
    return veh, ped

