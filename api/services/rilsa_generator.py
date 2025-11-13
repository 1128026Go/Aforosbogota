"""
Generador automático de mapas RILSA basado en metodología estándar
Información SAGRADA de asignación de códigos RILSA

CHANGELOG:
- v2.0.0 (2024-11-10): Refactorización completa
  - Integración con AggregatorService
  - Generación de reportes completos
  - Auto-detección de accesos cardinales
  - Métodos de export a CSV/PDF
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import logging
from collections import defaultdict

# Importar numpy si está disponible (para clustering)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)


class RilsaGenerator:
    """
    Generador de mapas RILSA según metodología estándar de ingeniería de tránsito

    METODOLOGÍA RILSA ESTÁNDAR:

    1. Movimientos directos (pasan de frente):
       - 1: Norte → Sur
       - 2: Sur → Norte
       - 3: Oeste → Este
       - 4: Este → Oeste

    2. Giros a la izquierda:
       - 5: Norte → Este
       - 6: Sur → Oeste
       - 7: Oeste → Norte
       - 8: Este → Sur

    3. Giros a la derecha (código 9 con índice):
       - 9(1) o 91: Norte → Oeste
       - 9(2) o 92: Sur → Este
       - 9(3) o 93: Oeste → Sur
       - 9(4) o 94: Este → Norte

    4. Giros en U (código 10 con índice):
       - 10(1) o 101: Giro en U en acceso Norte
       - 10(2) o 102: Giro en U en acceso Sur
       - 10(3) o 103: Giro en U en acceso Oeste
       - 10(4) o 104: Giro en U en acceso Este
    """

    # Definición sagrada de códigos RILSA
    DIRECT_MOVEMENTS = {
        ("N", "S"): 1,  # Norte → Sur
        ("S", "N"): 2,  # Sur → Norte
        ("O", "E"): 3,  # Oeste → Este
        ("E", "O"): 4,  # Este → Oeste
    }

    LEFT_TURNS = {
        ("N", "E"): 5,  # Norte → Este
        ("S", "O"): 6,  # Sur → Oeste
        ("O", "N"): 7,  # Oeste → Norte (izquierda)
        ("E", "S"): 8,  # Este → Sur
    }

    RIGHT_TURNS = {
        ("N", "O"): 91,  # Norte → Oeste - 9(1)
        ("S", "E"): 92,  # Sur → Este - 9(2)
        ("O", "S"): 93,  # Oeste → Sur (derecha) - 9(3)
        ("E", "N"): 94,  # Este → Norte - 9(4)
    }

    U_TURNS = {
        ("N", "N"): 101,  # U-turn Norte - 10(1)
        ("S", "S"): 102,  # U-turn Sur - 10(2)
        ("O", "O"): 103,  # U-turn Oeste - 10(3)
        ("E", "E"): 104,  # U-turn Este - 10(4)
    }

    def __init__(self, data_dir: Path, aggregator=None):
        """
        Inicializa el generador RILSA

        Args:
            data_dir: Directorio base de datos
            aggregator: Instancia de AggregatorService (opcional)
        """
        self.data_dir = Path(data_dir)
        self.aggregator = aggregator

    # ============================================================================
    # MÉTODOS CLÁSICOS (Compatibilidad v1.x)
    # ============================================================================

    @classmethod
    def generate_rilsa_map(cls, accesses: List[Dict]) -> Dict[str, int]:
        """
        Genera automáticamente el mapa RILSA completo basado en los accesos definidos

        Args:
            accesses: Lista de accesos con 'id', 'name', 'cardinal', 'x', 'y'

        Returns:
            Diccionario con formato "access_id_origin->access_id_dest": rilsa_code
        """
        rilsa_map = {}

        # Crear mapeo de cardinal a access_id
        cardinal_to_id = {acc["cardinal"]: acc["id"] for acc in accesses}
        id_to_cardinal = {acc["id"]: acc["cardinal"] for acc in accesses}

        # Generar todas las combinaciones posibles
        for origin_access in accesses:
            origin_id = origin_access["id"]
            origin_cardinal = origin_access["cardinal"]

            for dest_access in accesses:
                dest_id = dest_access["id"]
                dest_cardinal = dest_access["cardinal"]

                # Obtener código RILSA según la combinación cardinal
                key = (origin_cardinal, dest_cardinal)
                rilsa_code = cls._get_rilsa_code(key)

                if rilsa_code is not None:
                    movement_key = f"{origin_id}->{dest_id}"
                    rilsa_map[movement_key] = rilsa_code

        return rilsa_map

    @classmethod
    def _get_rilsa_code(cls, movement: tuple) -> Optional[int]:
        """
        Obtiene el código RILSA para un movimiento (cardinal_origen, cardinal_destino)
        """
        # Buscar en movimientos directos
        if movement in cls.DIRECT_MOVEMENTS:
            return cls.DIRECT_MOVEMENTS[movement]

        # Buscar en giros izquierda
        if movement in cls.LEFT_TURNS:
            return cls.LEFT_TURNS[movement]

        # Buscar en giros derecha
        if movement in cls.RIGHT_TURNS:
            return cls.RIGHT_TURNS[movement]

        # Buscar en U-turns
        if movement in cls.U_TURNS:
            return cls.U_TURNS[movement]

        # Movimiento no estándar (no debería ocurrir con 4 accesos cardinales)
        return None

    @classmethod
    def get_movement_description(cls, origin_cardinal: str, dest_cardinal: str) -> str:
        """
        Obtiene descripción legible del movimiento
        """
        key = (origin_cardinal, dest_cardinal)

        if key in cls.DIRECT_MOVEMENTS:
            return f"Directo ({origin_cardinal} → {dest_cardinal})"

        if key in cls.LEFT_TURNS:
            return f"Giro izquierda ({origin_cardinal} → {dest_cardinal})"

        if key in cls.RIGHT_TURNS:
            code = cls.RIGHT_TURNS[key]
            suffix = code - 90  # 91->1, 92->2, etc.
            return f"Giro derecha 9({suffix}) ({origin_cardinal} → {dest_cardinal})"

        if key in cls.U_TURNS:
            code = cls.U_TURNS[key]
            suffix = code - 100  # 101->1, 102->2, etc.
            return f"Vuelta en U 10({suffix}) ({origin_cardinal})"

        return f"Movimiento no estándar ({origin_cardinal} → {dest_cardinal})"

    @classmethod
    def generate_rilsa_map_with_descriptions(cls, accesses: List[Dict]) -> List[Dict]:
        """
        Genera mapa RILSA con descripciones detalladas para visualización

        Returns:
            Lista de reglas con formato:
            [
                {
                    "origin_id": "acc_1",
                    "origin_name": "Acceso Norte",
                    "origin_cardinal": "N",
                    "dest_id": "acc_2",
                    "dest_name": "Acceso Sur",
                    "dest_cardinal": "S",
                    "rilsa_code": 1,
                    "description": "Directo (N → S)"
                },
                ...
            ]
        """
        rules = []

        for origin_access in accesses:
            origin_id = origin_access["id"]
            origin_name = origin_access["name"]
            origin_cardinal = origin_access["cardinal"]

            for dest_access in accesses:
                dest_id = dest_access["id"]
                dest_name = dest_access["name"]
                dest_cardinal = dest_access["cardinal"]

                key = (origin_cardinal, dest_cardinal)
                rilsa_code = cls._get_rilsa_code(key)

                if rilsa_code is not None:
                    rules.append({
                        "origin_id": origin_id,
                        "origin_name": origin_name,
                        "origin_cardinal": origin_cardinal,
                        "dest_id": dest_id,
                        "dest_name": dest_name,
                        "dest_cardinal": dest_cardinal,
                        "rilsa_code": rilsa_code,
                        "description": cls.get_movement_description(origin_cardinal, dest_cardinal),
                    })

        return rules

    # ============================================================================
    # NUEVOS MÉTODOS v2.0 - AUTO-GENERACIÓN
    # ============================================================================

    @classmethod
    def detect_cardinal_accesses_from_trajectories(cls, trajectories: List[Dict]) -> List[Dict]:
        """
        Detecta automáticamente los 4 accesos cardinales analizando trayectorias

        Usa clustering (K-means) en puntos de entrada/salida para identificar
        los 4 accesos principales y asignarles nombres cardinales basados en posición

        Args:
            trajectories: Lista de trayectorias con campo 'points' [{'x', 'y', ...}]

        Returns:
            Lista de accesos detectados con formato:
            [
                {
                    "id": "access_N",
                    "name": "Acceso Norte",
                    "cardinal": "N",
                    "centroid_x": 425.5,
                    "centroid_y": 100.2,
                    "num_trajectories": 150
                },
                ...
            ]
        """
        if not HAS_NUMPY:
            logger.warning("NumPy no disponible - no se puede usar clustering automático")
            return []

        from sklearn.cluster import KMeans

        # Extraer puntos de entrada (primer punto de cada trayectoria)
        entry_points = []
        for traj in trajectories:
            points = traj.get("points", [])
            if len(points) > 0:
                first_point = points[0]
                entry_points.append([first_point["x"], first_point["y"]])

        if len(entry_points) < 4:
            logger.error(f"Insuficientes puntos de entrada ({len(entry_points)}) para detectar 4 accesos")
            return []

        # K-means con 4 clusters
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        kmeans.fit(entry_points)

        # Asignar nombres cardinales basado en posición geométrica
        centroids = kmeans.cluster_centers_
        accesses = cls._assign_cardinal_names_to_centroids(centroids)

        # Contar trayectorias por acceso
        labels = kmeans.labels_
        for idx, label in enumerate(labels):
            for access in accesses:
                if access["cluster_id"] == label:
                    access["num_trajectories"] = access.get("num_trajectories", 0) + 1

        logger.info(f"Detectados {len(accesses)} accesos cardinales automáticamente")

        return accesses

    @classmethod
    def _assign_cardinal_names_to_centroids(cls, centroids: "np.ndarray") -> List[Dict]:
        """
        Asigna N, S, E, O basado en posición geométrica de centroids

        - Norte: centroid más arriba (menor Y)
        - Sur: centroid más abajo (mayor Y)
        - Este: centroid más a la derecha (mayor X)
        - Oeste: centroid más a la izquierda (menor X)

        Args:
            centroids: Array de NumPy con coordenadas [x, y] de cada centroid

        Returns:
            Lista de accesos con nombres cardinales asignados
        """
        # Ordenar por Y (para Norte/Sur)
        sorted_by_y = sorted(enumerate(centroids), key=lambda x: x[1][1])

        # Ordenar por X (para Este/Oeste)
        sorted_by_x = sorted(enumerate(centroids), key=lambda x: x[1][0])

        # Asignar cardinales
        cardinal_map = {}
        cardinal_map[sorted_by_y[0][0]] = "N"   # Menor Y = Norte (arriba)
        cardinal_map[sorted_by_y[-1][0]] = "S"  # Mayor Y = Sur (abajo)
        cardinal_map[sorted_by_x[0][0]] = "O"   # Menor X = Oeste (izquierda)
        cardinal_map[sorted_by_x[-1][0]] = "E"  # Mayor X = Este (derecha)

        # Crear lista de accesos
        accesses = []
        for idx, centroid in enumerate(centroids):
            cardinal = cardinal_map[idx]
            accesses.append({
                "id": f"access_{cardinal}",
                "name": f"Acceso {cardinal}",
                "cardinal": cardinal,
                "centroid_x": float(centroid[0]),
                "centroid_y": float(centroid[1]),
                "cluster_id": idx,
                "num_trajectories": 0  # Se llenará después
            })

        return accesses

    @classmethod
    def infer_movements_from_polygons(cls, accesses: Dict) -> Dict:
        """
        Analiza polígonos de entrada/salida para inferir movimientos válidos

        Args:
            accesses: Diccionario con configuración de accesos cardinales
                     {
                         "N": {
                             "entry_polygon": [[x1, y1], ...],
                             "exit_polygon": [[x1, y1], ...],
                             "allows_entry": True,
                             "allows_exit": True
                         },
                         ...
                     }

        Returns:
            {
                "N-S": {"code": 1, "type": "directo", "allowed": True},
                "N-E": {"code": 9.1, "type": "giro_izquierda", "allowed": True},
                ...
            }
        """
        movements = {}
        cardinal_pairs = [
            ("N", "S"), ("N", "E"), ("N", "O"),
            ("S", "N"), ("S", "E"), ("S", "O"),
            ("E", "O"), ("E", "N"), ("E", "S"),
            ("O", "E"), ("O", "N"), ("O", "S")
        ]

        for origin, destination in cardinal_pairs:
            if origin in accesses and destination in accesses:
                origin_cfg = accesses[origin]
                dest_cfg = accesses[destination]

                # Validar si movimiento está permitido
                can_exit_from_origin = origin_cfg.get("allows_exit", True)
                can_enter_to_dest = dest_cfg.get("allows_entry", True)

                if can_exit_from_origin and can_enter_to_dest:
                    movement_type = cls._classify_movement(origin, destination)
                    code = cls._get_rilsa_code((origin, destination))

                    if code is not None:
                        movements[f"{origin}-{destination}"] = {
                            "code": code,
                            "type": movement_type,
                            "allowed": True,
                            "origin": origin,
                            "destination": destination
                        }

        return movements

    @classmethod
    def _classify_movement(cls, origin: str, destination: str) -> str:
        """
        Clasifica movimiento como: directo, giro_izquierda, giro_derecha, retorno

        Basado en ángulos cardinales:
        - Directo: 180° (opuestos)
        - Giro derecha: 90° clockwise
        - Giro izquierda: 90° counterclockwise
        - Retorno: 0° (mismo cardinal - no permitido normalmente)
        """
        key = (origin, destination)

        if key in cls.DIRECT_MOVEMENTS:
            return "directo"

        if key in cls.LEFT_TURNS:
            return "giro_izquierda"

        if key in cls.RIGHT_TURNS:
            return "giro_derecha"

        if key in cls.U_TURNS:
            return "retorno"

        return "otro"

    @classmethod
    def auto_generate_rilsa_config(cls, trajectories: List[Dict]) -> Dict:
        """
        Genera configuración RILSA completa automáticamente desde trayectorias

        Args:
            trajectories: Lista de trayectorias

        Returns:
            {
                "accesses": [...],  # Accesos detectados
                "rilsa_map": {...},  # Mapa de códigos RILSA
                "rilsa_map_with_descriptions": [...]  # Con descripciones
            }
        """
        # 1. Detectar accesos cardinales
        accesses = cls.detect_cardinal_accesses_from_trajectories(trajectories)

        if not accesses:
            logger.error("No se pudieron detectar accesos automáticamente")
            return {
                "error": "No se pudieron detectar accesos automáticamente",
                "accesses": [],
                "rilsa_map": {},
                "rilsa_map_with_descriptions": []
            }

        # 2. Generar mapa RILSA
        rilsa_map = cls.generate_rilsa_map(accesses)

        # 3. Generar descripciones
        rilsa_descriptions = cls.generate_rilsa_map_with_descriptions(accesses)

        logger.info(f"Configuración RILSA auto-generada: {len(accesses)} accesos, {len(rilsa_map)} movimientos")

        return {
            "accesses": accesses,
            "rilsa_map": rilsa_map,
            "rilsa_map_with_descriptions": rilsa_descriptions,
            "auto_generated": True,
            "generated_at": datetime.now().isoformat()
        }

    # ============================================================================
    # MÉTODOS DE GENERACIÓN DE REPORTES v2.0
    # ============================================================================

    def generate_volume_report(self, dataset_id: str) -> List[Dict]:
        """
        Genera reporte de volúmenes por intervalo de 15 min usando AggregatorService

        Args:
            dataset_id: ID del dataset

        Returns:
            Lista de registros con formato:
            [
                {
                    "interval": "2024-11-10T14:00:00",
                    "movimiento_rilsa": 1,
                    "clase": "car",
                    "cantidad": 25,
                    "descripcion": "Directo (N → S)"
                },
                ...
            ]
        """
        if not self.aggregator:
            logger.error("AggregatorService no configurado")
            return []

        # Obtener intervalos disponibles
        intervals = self.aggregator.get_intervals(dataset_id)

        report = []
        for interval_iso in intervals:
            interval_data = self.aggregator.get_interval_data(dataset_id, interval_iso)

            if not interval_data:
                continue

            # Procesar conteos
            for key, count in interval_data.get("counts", {}).items():
                try:
                    mov_rilsa_str, clase = key.split("_", 1)
                    mov_rilsa = int(mov_rilsa_str)

                    # Obtener descripción (requiere conocer origen/destino)
                    # Por ahora, descripción genérica
                    descripcion = f"Movimiento {mov_rilsa}"

                    report.append({
                        "interval": interval_iso,
                        "movimiento_rilsa": mov_rilsa,
                        "clase": clase,
                        "cantidad": count,
                        "descripcion": descripcion
                    })

                except ValueError as e:
                    logger.warning(f"Error parseando key '{key}': {e}")
                    continue

        logger.info(f"Reporte de volúmenes generado: {len(report)} registros")

        return report

    def generate_velocity_stats(self, dataset_id: str) -> Dict:
        """
        Genera estadísticas de velocidades para el dataset

        Args:
            dataset_id: ID del dataset

        Returns:
            {
                "total_trajectories": 1500,
                "mean_kmh": 45.2,
                "median_kmh": 42.0,
                "p85_kmh": 58.5,
                "min_kmh": 5.0,
                "max_kmh": 95.0,
                "by_class": {
                    "car": {"mean_kmh": 48.0, ...},
                    "truck": {"mean_kmh": 35.0, ...}
                }
            }
        """
        trajectories = self._load_trajectories(dataset_id)

        if not trajectories:
            return {"error": "No trajectories found"}

        speeds = []
        speeds_by_class = defaultdict(list)

        for traj in trajectories:
            avg_speed = traj.get("avg_speed", traj.get("velocidad_promedio", 0))
            if avg_speed > 0:
                speeds.append(avg_speed)

                clase = traj.get("class", traj.get("cls", "unknown"))
                speeds_by_class[clase].append(avg_speed)

        if not speeds:
            return {"error": "No speed data available"}

        if HAS_NUMPY:
            stats = {
                "total_trajectories": len(trajectories),
                "trajectories_with_speed": len(speeds),
                "mean_kmh": float(np.mean(speeds)),
                "median_kmh": float(np.median(speeds)),
                "p85_kmh": float(np.percentile(speeds, 85)),
                "min_kmh": float(np.min(speeds)),
                "max_kmh": float(np.max(speeds)),
                "std_kmh": float(np.std(speeds))
            }

            # Estadísticas por clase
            stats["by_class"] = {}
            for clase, class_speeds in speeds_by_class.items():
                stats["by_class"][clase] = {
                    "count": len(class_speeds),
                    "mean_kmh": float(np.mean(class_speeds)),
                    "median_kmh": float(np.median(class_speeds)),
                    "p85_kmh": float(np.percentile(class_speeds, 85))
                }

        else:
            # Fallback sin NumPy
            stats = {
                "total_trajectories": len(trajectories),
                "trajectories_with_speed": len(speeds),
                "mean_kmh": sum(speeds) / len(speeds),
                "min_kmh": min(speeds),
                "max_kmh": max(speeds)
            }

        logger.info(f"Estadísticas de velocidad calculadas para {len(trajectories)} trayectorias")

        return stats

    def generate_od_matrix(self, dataset_id: str) -> List[Dict]:
        """
        Genera matriz Origen-Destino

        Args:
            dataset_id: ID del dataset

        Returns:
            [
                {
                    "origin_cardinal": "N",
                    "dest_cardinal": "S",
                    "cantidad": 150,
                    "movimiento_rilsa": 1
                },
                ...
            ]
        """
        trajectories = self._load_trajectories(dataset_id)

        # Agrupar por origen-destino
        od_counts = defaultdict(int)
        od_info = {}

        for traj in trajectories:
            origin = traj.get("cardinal_origin", "unknown")
            dest = traj.get("cardinal_destination", "unknown")
            rilsa_code = traj.get("rilsa_code", 0)

            key = (origin, dest)
            od_counts[key] += 1

            if key not in od_info:
                od_info[key] = rilsa_code

        # Convertir a lista
        od_matrix = []
        for (origin, dest), count in sorted(od_counts.items()):
            od_matrix.append({
                "origin_cardinal": origin,
                "dest_cardinal": dest,
                "cantidad": count,
                "movimiento_rilsa": od_info[(origin, dest)],
                "descripcion": self.get_movement_description(origin, dest)
            })

        logger.info(f"Matriz OD generada: {len(od_matrix)} pares origen-destino")

        return od_matrix

    def generate_executive_summary(self, dataset_id: str) -> Dict:
        """
        Genera resumen ejecutivo del dataset

        Returns:
            {
                "dataset_id": "dataset_xxx",
                "total_trajectories": 1500,
                "total_vehicles": 1350,
                "total_pedestrians": 150,
                "time_period": "2024-11-10 14:00 - 15:30",
                "avg_speed_kmh": 45.2,
                "movements_detected": 12,
                "accesses_configured": 4
            }
        """
        trajectories = self._load_trajectories(dataset_id)

        if not trajectories:
            return {"error": "No data available"}

        # Contar por tipo
        vehicles = 0
        pedestrians = 0
        for traj in trajectories:
            clase = traj.get("class", traj.get("cls", ""))
            if clase == "person":
                pedestrians += 1
            else:
                vehicles += 1

        # Tiempo de análisis
        if trajectories:
            first_traj = min(trajectories, key=lambda t: t.get("t_entry", 0))
            last_traj = max(trajectories, key=lambda t: t.get("t_exit", 0))

            time_period = f"{first_traj.get('t_entry', 'N/A')} - {last_traj.get('t_exit', 'N/A')}"
        else:
            time_period = "N/A"

        # Movimientos únicos
        movements = set(traj.get("rilsa_code", 0) for traj in trajectories if traj.get("rilsa_code"))

        summary = {
            "dataset_id": dataset_id,
            "total_trajectories": len(trajectories),
            "total_vehicles": vehicles,
            "total_pedestrians": pedestrians,
            "time_period": time_period,
            "movements_detected": len(movements),
            "generated_at": datetime.now().isoformat()
        }

        # Agregar velocidades si disponibles
        velocity_stats = self.generate_velocity_stats(dataset_id)
        if "mean_kmh" in velocity_stats:
            summary["avg_speed_kmh"] = velocity_stats["mean_kmh"]
            summary["p85_speed_kmh"] = velocity_stats["p85_kmh"]

        logger.info(f"Resumen ejecutivo generado para dataset {dataset_id}")

        return summary

    def generate_interval_volumes(self, trajectories: List[Dict], interval_minutes: int = 15) -> List[Dict]:
        """
        Calcula volúmenes por intervalo de tiempo desde trayectorias

        Args:
            trajectories: Lista de trayectorias con campos:
                         track_id, class, movimiento_rilsa, t_entry, t_exit,
                         cardinal_origin, cardinal_destination
            interval_minutes: Duración del intervalo en minutos (default: 15)

        Returns:
            Lista de registros con formato:
            [
                {
                    "interval_start": "2024-11-10T14:00:00",
                    "interval_end": "2024-11-10T14:15:00",
                    "movimiento_rilsa": 1,
                    "clase": "car",
                    "cantidad": 25,
                    "origin_cardinal": "N",
                    "dest_cardinal": "S"
                },
                ...
            ]
        """
        from datetime import timedelta

        # Agrupar por intervalo
        volumes_by_interval = defaultdict(int)

        for traj in trajectories:
            # Obtener timestamp de salida
            t_exit_str = traj.get("t_exit", traj.get("t_exit_iso", ""))
            if not t_exit_str:
                continue

            try:
                t_exit = datetime.fromisoformat(t_exit_str.replace("Z", ""))
            except (ValueError, AttributeError):
                continue

            # Calcular inicio del intervalo
            minutes = (t_exit.minute // interval_minutes) * interval_minutes
            interval_start = t_exit.replace(minute=minutes, second=0, microsecond=0)
            interval_end = interval_start + timedelta(minutes=interval_minutes)

            # Obtener datos del movimiento
            mov_rilsa = traj.get("movimiento_rilsa", traj.get("rilsa_code", 0))
            clase = traj.get("class", traj.get("cls", "unknown"))
            origin = traj.get("cardinal_origin", traj.get("origin_cardinal", ""))
            dest = traj.get("cardinal_destination", traj.get("dest_cardinal", ""))

            # Clave única por intervalo, movimiento, clase
            key = (interval_start.isoformat(), mov_rilsa, clase, origin, dest)
            volumes_by_interval[key] += 1

        # Convertir a lista
        volumes = []
        for (interval_start_iso, mov_rilsa, clase, origin, dest), cantidad in volumes_by_interval.items():
            interval_start = datetime.fromisoformat(interval_start_iso)
            interval_end = interval_start + timedelta(minutes=interval_minutes)

            volumes.append({
                "interval_start": interval_start.isoformat(),
                "interval_end": interval_end.isoformat(),
                "movimiento_rilsa": mov_rilsa,
                "clase": clase,
                "cantidad": cantidad,
                "origin_cardinal": origin,
                "dest_cardinal": dest
            })

        # Ordenar por intervalo
        volumes.sort(key=lambda x: x["interval_start"])

        logger.info(f"Volúmenes calculados: {len(volumes)} registros en {len(set(v['interval_start'] for v in volumes))} intervalos")

        return volumes

    def generate_rilsa_tables(self, volumes: List[Dict], accesses: Optional[Dict] = None) -> Dict:
        """
        Genera tablas RILSA con formato estándar

        Args:
            volumes: Lista de volúmenes por intervalo (de generate_interval_volumes)
            accesses: Configuración de accesos (opcional, para descripciones)

        Returns:
            {
                "volumenes_por_movimiento": [...],
                "volumenes_por_ramal": [...],
                "volumenes_por_intervalo": [...],
                "resumen_por_clase": [...]
            }
        """
        from collections import defaultdict

        # 1. Volúmenes por movimiento (totales)
        volumes_by_movement = defaultdict(lambda: defaultdict(int))
        for vol in volumes:
            mov = vol.get("movimiento_rilsa", 0)
            clase = vol.get("clase", "unknown")
            volumes_by_movement[mov][clase] += vol.get("cantidad", 0)

        volumenes_por_movimiento = []
        for mov, clases in sorted(volumes_by_movement.items()):
            for clase, cantidad in sorted(clases.items()):
                # Buscar origen/destino para este movimiento
                origin = ""
                dest = ""
                for vol in volumes:
                    if vol.get("movimiento_rilsa") == mov:
                        origin = vol.get("origin_cardinal", "")
                        dest = vol.get("dest_cardinal", "")
                        break

                descripcion = self.get_movement_description(origin, dest) if (origin and dest) else f"Movimiento {mov}"

                volumenes_por_movimiento.append({
                    "movimiento_rilsa": mov,
                    "clase": clase,
                    "cantidad": cantidad,
                    "descripcion": descripcion
                })

        # 2. Volúmenes por ramal (origen)
        volumes_by_ramal = defaultdict(lambda: defaultdict(int))
        for vol in volumes:
            origin = vol.get("origin_cardinal", "unknown")
            clase = vol.get("clase", "unknown")
            volumes_by_ramal[origin][clase] += vol.get("cantidad", 0)

        volumenes_por_ramal = []
        for origin, clases in sorted(volumes_by_ramal.items()):
            for clase, cantidad in sorted(clases.items()):
                volumenes_por_ramal.append({
                    "origin_cardinal": origin,
                    "clase": clase,
                    "cantidad": cantidad
                })

        # 3. Resumen por clase
        volumes_by_class = defaultdict(int)
        for vol in volumes:
            clase = vol.get("clase", "unknown")
            volumes_by_class[clase] += vol.get("cantidad", 0)

        resumen_por_clase = [
            {"clase": clase, "cantidad": cantidad}
            for clase, cantidad in sorted(volumes_by_class.items())
        ]

        tables = {
            "volumenes_por_movimiento": volumenes_por_movimiento,
            "volumenes_por_ramal": volumenes_por_ramal,
            "volumenes_por_intervalo": volumes,  # Ya está en formato correcto
            "resumen_por_clase": resumen_por_clase
        }

        logger.info(f"Tablas RILSA generadas: {len(volumenes_por_movimiento)} movimientos, {len(volumenes_por_ramal)} ramales")

        return tables

    def generate_complete_report(self, dataset_id: str, output_dir: Optional[Path] = None) -> Dict:
        """
        Genera reporte completo RILSA (método maestro)

        Args:
            dataset_id: ID del dataset
            output_dir: Directorio de salida para archivos (opcional)

        Returns:
            {
                "dataset_id": "dataset_xxx",
                "volume_report": [...],
                "velocity_stats": {...},
                "od_matrix": [...],
                "executive_summary": {...},
                "rilsa_tables": {...},  # Nuevo: tablas RILSA completas
                "files_generated": [...],  # Si output_dir especificado
                "generated_at": "2024-11-10T15:30:00"
            }
        """
        logger.info(f"Generando reporte completo para dataset {dataset_id}")

        # Cargar trayectorias
        trajectories = self._load_trajectories(dataset_id)

        # Generar volúmenes por intervalo
        interval_volumes = self.generate_interval_volumes(trajectories, interval_minutes=15)

        # Generar tablas RILSA
        rilsa_tables = self.generate_rilsa_tables(interval_volumes)

        # Generar todos los componentes
        report = {
            "dataset_id": dataset_id,
            "volume_report": self.generate_volume_report(dataset_id),
            "velocity_stats": self.generate_velocity_stats(dataset_id),
            "od_matrix": self.generate_od_matrix(dataset_id),
            "executive_summary": self.generate_executive_summary(dataset_id),
            "rilsa_tables": rilsa_tables,  # Nuevo
            "interval_volumes": interval_volumes,  # Nuevo
            "generated_at": datetime.now().isoformat()
        }

        # Exportar a archivos si se especificó output_dir
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            files_generated = self._export_report_to_files(report, output_path)
            report["files_generated"] = files_generated

        logger.info(f"Reporte completo generado exitosamente")

        return report

    def _export_report_to_files(self, report: Dict, output_dir: Path) -> List[str]:
        """
        Exporta componentes del reporte a archivos CSV/JSON

        Args:
            report: Reporte generado
            output_dir: Directorio de salida

        Returns:
            Lista de archivos generados
        """
        files = []

        # 1. Volúmenes por intervalo a CSV
        if "volume_report" in report and report["volume_report"]:
            volume_file = output_dir / "volumenes_por_intervalo.csv"
            self._export_to_csv(report["volume_report"], volume_file)
            files.append(str(volume_file))

        # 2. Tablas RILSA (nuevas)
        if "rilsa_tables" in report and report["rilsa_tables"]:
            tables = report["rilsa_tables"]

            # 2.1 Volúmenes por movimiento
            if "volumenes_por_movimiento" in tables:
                mov_file = output_dir / "volumenes_por_movimiento.csv"
                self._export_to_csv(tables["volumenes_por_movimiento"], mov_file)
                files.append(str(mov_file))

            # 2.2 Volúmenes por ramal
            if "volumenes_por_ramal" in tables:
                ramal_file = output_dir / "volumenes_por_ramal.csv"
                self._export_to_csv(tables["volumenes_por_ramal"], ramal_file)
                files.append(str(ramal_file))

            # 2.3 Volúmenes por intervalo (detallado)
            if "volumenes_por_intervalo" in tables:
                intervalo_file = output_dir / "volumenes_15min_detallado.csv"
                self._export_to_csv(tables["volumenes_por_intervalo"], intervalo_file)
                files.append(str(intervalo_file))

            # 2.4 Resumen por clase
            if "resumen_por_clase" in tables:
                clase_file = output_dir / "resumen_por_clase.csv"
                self._export_to_csv(tables["resumen_por_clase"], clase_file)
                files.append(str(clase_file))

        # 3. Matriz OD a CSV
        if "od_matrix" in report and report["od_matrix"]:
            od_file = output_dir / "matriz_od.csv"
            self._export_to_csv(report["od_matrix"], od_file)
            files.append(str(od_file))

        # 4. Resumen ejecutivo a JSON
        if "executive_summary" in report:
            summary_file = output_dir / "resumen_ejecutivo.json"
            summary_file.write_text(json.dumps(report["executive_summary"], indent=2, ensure_ascii=False))
            files.append(str(summary_file))

        # 5. Velocidades a JSON
        if "velocity_stats" in report:
            velocity_file = output_dir / "estadisticas_velocidades.json"
            velocity_file.write_text(json.dumps(report["velocity_stats"], indent=2, ensure_ascii=False))
            files.append(str(velocity_file))

        logger.info(f"Exportados {len(files)} archivos a {output_dir}")

        return files

    def _export_to_csv(self, data: List[Dict], output_file: Path):
        """Exporta lista de diccionarios a CSV"""
        if not data:
            logger.warning(f"No hay datos para exportar a {output_file}")
            return

        import csv

        keys = data[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

        logger.debug(f"CSV exportado: {output_file}")

    # ============================================================================
    # MÉTODOS AUXILIARES
    # ============================================================================

    def _load_trajectories(self, dataset_id: str) -> List[Dict]:
        """
        Carga trayectorias desde archivo playback_events.json

        Args:
            dataset_id: ID del dataset

        Returns:
            Lista de trayectorias
        """
        dataset_dir = self.data_dir / dataset_id
        playback_file = dataset_dir / "playback_events.json"

        if not playback_file.exists():
            logger.warning(f"Archivo playback no encontrado: {playback_file}")
            return []

        try:
            data = json.loads(playback_file.read_text())
            trajectories = data if isinstance(data, list) else data.get("events", [])

            logger.debug(f"Cargadas {len(trajectories)} trayectorias de {playback_file}")

            return trajectories

        except Exception as e:
            logger.error(f"Error cargando trayectorias: {e}")
            return []

    @classmethod
    def validate_rilsa_map(cls, rilsa_map: Dict) -> Tuple[bool, List[str]]:
        """
        Valida que el mapa RILSA sea consistente

        Args:
            rilsa_map: Mapa RILSA a validar

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # 1. Verificar códigos únicos
        codes = list(rilsa_map.values())
        if len(codes) != len(set(codes)):
            errors.append("Códigos RILSA duplicados encontrados")

        # 2. Verificar códigos en rango válido
        # Códigos válidos: 1-8 (directos e izquierda), 9.1-9.4 (derecha), 10.1-10.4 (U-turn)
        # También acepta formato antiguo: 91-94, 101-104
        valid_codes = (
            list(range(1, 9)) +  # 1-8
            [9.1, 9.2, 9.3, 9.4] +  # Giros derecha (formato nuevo)
            [91, 92, 93, 94] +  # Giros derecha (formato antiguo)
            [10.1, 10.2, 10.3, 10.4] +  # U-turns (formato nuevo)
            [101, 102, 103, 104]  # U-turns (formato antiguo)
        )
        for movement_key, code in rilsa_map.items():
            if code not in valid_codes:
                errors.append(f"Código RILSA inválido: {code} en movimiento {movement_key}")

        # 3. Verificar formato de keys
        for key in rilsa_map.keys():
            if "->" not in key:
                errors.append(f"Formato de key inválido: {key} (debe ser 'origin_id->dest_id')")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Mapa RILSA validado exitosamente")
        else:
            logger.error(f"Mapa RILSA inválido: {len(errors)} errores encontrados")

        return (is_valid, errors)
