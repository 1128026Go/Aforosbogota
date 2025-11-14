"""
Lógica para detección de accesos cardinales y generación del mapa RILSA.
"""
from __future__ import annotations

from collections import defaultdict
from math import atan2
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from api.models.config import AccessConfig, RilsaRule
from api.services import rilsa_mapping


def _centroid(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calcula el centroide simple de una lista de puntos."""
    if not points:
        return 0.0, 0.0
    xs, ys = zip(*points)
    return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))


def detect_accesses_from_parquet(parquet_path: Path) -> List[Dict]:
    """
    Detecta accesos cardinales a partir de un parquet normalizado.

    Estrategia:
      - Calcula el centro global de los puntos iniciales.
      - Agrupa por cuadrante (N, S, E, O) según desplazamiento relativo.
      - Devuelve un listado de diccionarios con centroides y conteos.
    """
    df = pd.read_parquet(parquet_path)
    if df.empty:
        return []

    starts = df.sort_values("frame_id").groupby("track_id").first()
    x_center = float(starts["x"].mean())
    y_center = float(starts["y"].mean())

    access_points: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for _, row in starts.iterrows():
        dx = float(row["x"]) - x_center
        dy = y_center - float(row["y"])  # invertir para eje vertical convencional
        if abs(dx) > abs(dy):
            cardinal = "E" if dx >= 0 else "O"
        else:
            cardinal = "N" if dy >= 0 else "S"
        access_points[cardinal].append((float(row["x"]), float(row["y"])))

    accesses: List[Dict] = []
    for idx, (cardinal, points) in enumerate(access_points.items(), start=1):
        cx, cy = _centroid(points)
        accesses.append(
            {
                "id": f"A{idx}",
                "x": cx,
                "y": cy,
                "cardinal": cardinal,
                "count": len(points),
                "polygon": None,
            }
        )

    return rilsa_mapping.order_accesses_for_rilsa(accesses)


def generate_default_rilsa_rules(accesses: List[Dict]) -> Dict:
    """Genera mapa RILSA completo usando la convención acordada."""
    return rilsa_mapping.build_rilsa_rule_map(accesses)


class CardinalsService:
    """
    Envoltura retrocompatible utilizada por routers existentes.

    Cuando no se proporciona trayectoria ni parquet, devuelve accesos vacíos.
    """

    @staticmethod
    def generate_default_accesses(
        trajectories: List[Dict],
        image_width: int = 1280,
        image_height: int = 720,
    ) -> List[AccessConfig]:
        if not trajectories:
            midpoint_x = image_width / 2
            midpoint_y = image_height / 2
            return [
                AccessConfig(id="N", cardinal="N", polygon=[], centroid=(midpoint_x, midpoint_y * 0.2)),
                AccessConfig(id="S", cardinal="S", polygon=[], centroid=(midpoint_x, midpoint_y * 1.8)),
                AccessConfig(id="O", cardinal="O", polygon=[], centroid=(midpoint_x * 0.2, midpoint_y)),
                AccessConfig(id="E", cardinal="E", polygon=[], centroid=(midpoint_x * 1.8, midpoint_y)),
            ]
        points = [(float(t.get("x", 0.0)), float(t.get("y", 0.0))) for t in trajectories]
        x_center = sum(p[0] for p in points) / len(points)
        y_center = sum(p[1] for p in points) / len(points)
        accesses_map: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        for x, y in points:
            dx = x - x_center
            dy = y_center - y
            if abs(dx) > abs(dy):
                cardinal = "E" if dx >= 0 else "O"
            else:
                cardinal = "N" if dy >= 0 else "S"
            accesses_map[cardinal].append((x, y))
        configs: List[AccessConfig] = []
        for idx, (cardinal, pts) in enumerate(accesses_map.items(), start=1):
            cx, cy = _centroid(pts)
            configs.append(
                AccessConfig(
                    id=f"A{idx}",
                    cardinal=cardinal,  # type: ignore[arg-type]
                    polygon=pts,
                    centroid=(cx, cy),
                )
            )
        return configs

    @staticmethod
    def generate_rilsa_rules(accesses: List[AccessConfig]) -> List[RilsaRule]:
        raw_accesses = [
            {
                "id": acc.id,
                "x": acc.centroid[0] if acc.centroid else 0.0,
                "y": acc.centroid[1] if acc.centroid else 0.0,
                "cardinal": acc.cardinal,
                "count": len(acc.polygon) if acc.polygon else 0,
            }
            for acc in accesses
        ]
        id_to_cardinal = {acc.id: acc.cardinal for acc in accesses}
        movement_type_map = {
            "straight": "directo",
            "left_turn": "izquierda",
            "right_turn": "derecha",
            "return": "retorno",
        }
        rilsa_map = rilsa_mapping.build_rilsa_rule_map(raw_accesses)
        rules = []
        for rule in rilsa_map["rules"]:
            origin_cardinal = id_to_cardinal.get(rule["origin_id"], "N")
            dest_cardinal = id_to_cardinal.get(rule["dest_id"], "S")
            movement_type = movement_type_map.get(rule["movement_class"], "directo")
            rules.append(
                RilsaRule(
                    code=rule["vehicle_code"],
                    origin_access=origin_cardinal,  # type: ignore[arg-type]
                    dest_access=dest_cardinal,  # type: ignore[arg-type]
                    movement_type=movement_type,  # type: ignore[arg-type]
                    description=f"{rule['vehicle_code']} – {movement_type}",
                )
            )
        return rules
