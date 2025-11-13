"""
Módulo de integración con CARLA Simulator.

Funcionalidades:
- Transformación de coordenadas píxel → metros → CARLA
- Spawn de actores (vehículos, peatones) en CARLA
- Replay de trayectorias en el simulador
- Persistencia incremental de actores
- Gestión de blueprint y configuración de actores

IMPORTANTE: Este módulo requiere CARLA instalado.
pip install carla (o desde el repositorio oficial)

SUPOSICIONES DE MAPEO:
- El video captura una región rectangular del mundo real
- Se asume una escala píxel→metros configurable
- Se asume un punto de origen (lat, lon, alt) para el mapa CARLA
- La rotación y perspectiva se pueden ajustar con matriz de homografía
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Set, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

# Intentar importar CARLA (opcional)
try:
    import carla
    CARLA_AVAILABLE = True
except ImportError:
    CARLA_AVAILABLE = False
    logger.warning("CARLA no disponible. Ejecuta: pip install carla")
    # Crear placeholders para type hints
    if not TYPE_CHECKING:
        carla = None


@dataclass
class CoordinateTransform:
    """
    Configuración para transformar coordenadas píxel → CARLA.

    Parámetros de calibración:
    - pixel_to_meter_scale: Escala píxeles → metros (ej: 0.1 = 10 píxeles = 1 metro)
    - origin_carla_x: Coordenada X de CARLA correspondiente al origen del video (píxel 0,0)
    - origin_carla_y: Coordenada Y de CARLA correspondiente al origen del video
    - origin_carla_z: Altura base en CARLA
    - rotation_degrees: Rotación del frame respecto al norte de CARLA
    - flip_y: Invertir eje Y (el video tiene Y creciendo hacia abajo, CARLA hacia arriba)

    NOTA: Estos parámetros deben ser calibrados manualmente para cada video
    basándose en puntos de referencia conocidos.
    """
    pixel_to_meter_scale: float = 0.05  # 20 píxeles = 1 metro por defecto
    origin_carla_x: float = 0.0
    origin_carla_y: float = 0.0
    origin_carla_z: float = 0.5  # Altura típica de spawn
    rotation_degrees: float = 0.0
    flip_y: bool = True

    def pixel_to_carla(self, px: float, py: float) -> Tuple[float, float, float]:
        """
        Convierte coordenadas de píxel a coordenadas CARLA.

        Args:
            px: Coordenada X en píxeles
            py: Coordenada Y en píxeles

        Returns:
            Tupla (carla_x, carla_y, carla_z)
        """
        # Escalar a metros
        mx = px * self.pixel_to_meter_scale
        my = py * self.pixel_to_meter_scale

        # Invertir Y si es necesario
        if self.flip_y:
            my = -my

        # Aplicar rotación si existe
        if self.rotation_degrees != 0:
            angle_rad = np.radians(self.rotation_degrees)
            mx_rot = mx * np.cos(angle_rad) - my * np.sin(angle_rad)
            my_rot = mx * np.sin(angle_rad) + my * np.cos(angle_rad)
            mx, my = mx_rot, my_rot

        # Trasladar al origen de CARLA
        carla_x = self.origin_carla_x + mx
        carla_y = self.origin_carla_y + my
        carla_z = self.origin_carla_z

        return carla_x, carla_y, carla_z

    def save_config(self, path: str):
        """Guarda la configuración a un archivo JSON."""
        config = {
            'pixel_to_meter_scale': self.pixel_to_meter_scale,
            'origin_carla_x': self.origin_carla_x,
            'origin_carla_y': self.origin_carla_y,
            'origin_carla_z': self.origin_carla_z,
            'rotation_degrees': self.rotation_degrees,
            'flip_y': self.flip_y
        }

        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Configuración guardada en: {path}")

    @classmethod
    def load_config(cls, path: str) -> 'CoordinateTransform':
        """Carga configuración desde un archivo JSON."""
        with open(path, 'r') as f:
            config = json.load(f)

        return cls(**config)


# Mapeo de clases YOLO → Blueprints CARLA
CLASS_TO_BLUEPRINT = {
    'car': 'vehicle.tesla.model3',
    'truck': 'vehicle.carlamotors.carlacola',
    'bus': 'vehicle.volkswagen.t2',
    'motorcycle': 'vehicle.kawasaki.ninja',
    'bicycle': 'vehicle.diamondback.century',
    'person': 'walker.pedestrian.0001'
}


@dataclass
class ActorInfo:
    """Información de un actor spawneado en CARLA."""
    actor_id: int
    track_id: int
    blueprint_id: str
    clase: str
    spawn_location: Tuple[float, float, float]
    waypoints: List[Tuple[float, float, float]] = field(default_factory=list)
    is_active: bool = True


class CARLAIntegration:
    """Integración con CARLA Simulator."""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 2000,
        timeout: float = 10.0,
        coordinate_transform: Optional[CoordinateTransform] = None,
        map_name: str = 'Town03'
    ):
        """
        Inicializa la integración con CARLA.

        Args:
            host: Host del servidor CARLA
            port: Puerto del servidor CARLA
            timeout: Timeout de conexión
            coordinate_transform: Transformación de coordenadas
            map_name: Nombre del mapa CARLA a usar
        """
        if not CARLA_AVAILABLE:
            raise ImportError("CARLA no está instalado. Ejecuta: pip install carla")

        self.host = host
        self.port = port
        self.timeout = timeout
        self.coordinate_transform = coordinate_transform or CoordinateTransform()
        self.map_name = map_name

        self.client: Optional[Any] = None  # carla.Client
        self.world: Optional[Any] = None  # carla.World
        self.blueprint_library: Optional[Any] = None  # carla.BlueprintLibrary

        self.spawned_actors: Dict[int, ActorInfo] = {}  # track_id -> ActorInfo
        self.actor_objects: Dict[int, Any] = {}  # track_id -> carla.Actor

    def connect(self):
        """Conecta con el servidor CARLA."""
        try:
            logger.info(f"Conectando a CARLA en {self.host}:{self.port}...")
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(self.timeout)

            # Obtener versión
            version = self.client.get_client_version()
            logger.info(f"Conectado a CARLA versión: {version}")

            # Cargar mundo
            self.world = self.client.get_world()
            logger.info(f"Mundo actual: {self.world.get_map().name}")

            # Cambiar mapa si es necesario
            current_map = self.world.get_map().name
            if self.map_name not in current_map:
                logger.info(f"Cambiando a mapa: {self.map_name}")
                self.world = self.client.load_world(self.map_name)

            # Obtener blueprint library
            self.blueprint_library = self.world.get_blueprint_library()

            logger.info("✓ Conexión con CARLA establecida")

        except Exception as e:
            logger.error(f"Error conectando a CARLA: {e}")
            raise

    def disconnect(self):
        """Desconecta y limpia recursos."""
        logger.info("Desconectando de CARLA...")
        # Los actores persisten en CARLA incluso después de desconectar
        self.client = None
        self.world = None

    def get_spawn_location(self, px: float, py: float) -> 'carla.Location':
        """
        Obtiene una ubicación de spawn en CARLA desde coordenadas píxel.

        Args:
            px: Coordenada X en píxeles
            py: Coordenada Y en píxeles

        Returns:
            carla.Location
        """
        carla_x, carla_y, carla_z = self.coordinate_transform.pixel_to_carla(px, py)
        return carla.Location(x=carla_x, y=carla_y, z=carla_z)

    def spawn_actor(
        self,
        track: 'Track',
        spawn_immediately: bool = True
    ) -> Optional[ActorInfo]:
        """
        Spawnea un actor en CARLA basado en una trayectoria.

        Args:
            track: Trayectoria del objeto
            spawn_immediately: Si spawnear inmediatamente o solo preparar

        Returns:
            ActorInfo o None si falla
        """
        if not self.world or not self.blueprint_library:
            logger.error("No hay conexión con CARLA")
            return None

        if track.track_id in self.spawned_actors:
            logger.warning(f"Actor con track_id {track.track_id} ya existe")
            return self.spawned_actors[track.track_id]

        # Obtener blueprint
        blueprint_id = CLASS_TO_BLUEPRINT.get(track.clase, 'vehicle.tesla.model3')

        try:
            bp = self.blueprint_library.find(blueprint_id)

            # Configurar blueprint
            if bp.has_attribute('color'):
                color = np.random.choice(bp.get_attribute('color').recommended_values)
                bp.set_attribute('color', color)

            # Punto de spawn (primera posición de la trayectoria)
            if not track.positions:
                logger.error(f"Track {track.track_id} no tiene posiciones")
                return None

            spawn_px, spawn_py = track.positions[0]
            spawn_location = self.get_spawn_location(spawn_px, spawn_py)

            # Calcular rotación inicial (dirección del movimiento)
            if len(track.positions) >= 2:
                p1 = track.positions[0]
                p2 = track.positions[1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                yaw = np.degrees(np.arctan2(dy, dx))
            else:
                yaw = 0.0

            spawn_transform = carla.Transform(
                spawn_location,
                carla.Rotation(yaw=yaw)
            )

            # Convertir todas las posiciones de la trayectoria
            waypoints = []
            for px, py in track.positions:
                cx, cy, cz = self.coordinate_transform.pixel_to_carla(px, py)
                waypoints.append((cx, cy, cz))

            # Spawnear actor si se requiere
            actor = None
            actor_id = -1

            if spawn_immediately:
                actor = self.world.try_spawn_actor(bp, spawn_transform)

                if actor is None:
                    logger.warning(f"No se pudo spawnear actor en {spawn_location}")
                    # Intentar ajustar altura
                    spawn_transform.location.z += 1.0
                    actor = self.world.try_spawn_actor(bp, spawn_transform)

                if actor is not None:
                    actor_id = actor.id
                    self.actor_objects[track.track_id] = actor
                    logger.info(f"✓ Actor spawneado: ID={actor_id}, Track={track.track_id}, Clase={track.clase}")
                else:
                    logger.error(f"✗ Fallo al spawnear actor para track {track.track_id}")
                    return None

            # Crear ActorInfo
            actor_info = ActorInfo(
                actor_id=actor_id,
                track_id=track.track_id,
                blueprint_id=blueprint_id,
                clase=track.clase,
                spawn_location=(spawn_location.x, spawn_location.y, spawn_location.z),
                waypoints=waypoints,
                is_active=True
            )

            self.spawned_actors[track.track_id] = actor_info
            return actor_info

        except Exception as e:
            logger.error(f"Error spawneando actor: {e}")
            return None

    def spawn_all_tracks(
        self,
        tracks: List['Track'],
        spawn_rate: float = 0.1
    ) -> Dict[str, int]:
        """
        Spawnea actores para todas las trayectorias.

        Args:
            tracks: Lista de trayectorias
            spawn_rate: Segundos entre spawns (para evitar sobrecarga)

        Returns:
            Estadísticas {clase: cantidad_spawneada}
        """
        stats = {}

        for i, track in enumerate(tracks):
            logger.info(f"Spawneando {i+1}/{len(tracks)}...")

            actor_info = self.spawn_actor(track, spawn_immediately=True)

            if actor_info:
                stats[track.clase] = stats.get(track.clase, 0) + 1

            # Esperar para evitar sobrecarga
            time.sleep(spawn_rate)

        logger.info(f"✓ Spawn completo: {sum(stats.values())} actores spawneados")
        for clase, count in stats.items():
            logger.info(f"  - {clase}: {count}")

        return stats

    def replay_trajectory(
        self,
        track_id: int,
        speed_multiplier: float = 1.0,
        autopilot: bool = False
    ):
        """
        Reproduce la trayectoria de un actor en tiempo real.

        Args:
            track_id: ID de la track a reproducir
            speed_multiplier: Multiplicador de velocidad (1.0 = velocidad real)
            autopilot: Usar autopilot de CARLA en lugar de waypoints fijos
        """
        if track_id not in self.actor_objects:
            logger.error(f"Actor con track_id {track_id} no existe")
            return

        actor = self.actor_objects[track_id]
        actor_info = self.spawned_actors[track_id]

        if autopilot and hasattr(actor, 'set_autopilot'):
            actor.set_autopilot(True)
            logger.info(f"Autopilot activado para track {track_id}")
            return

        # Replay manual usando waypoints
        logger.info(f"Reproduciendo trayectoria para track {track_id}...")

        for i, (cx, cy, cz) in enumerate(actor_info.waypoints):
            # Calcular rotación hacia el siguiente waypoint
            if i < len(actor_info.waypoints) - 1:
                next_wp = actor_info.waypoints[i + 1]
                dx = next_wp[0] - cx
                dy = next_wp[1] - cy
                yaw = np.degrees(np.arctan2(dy, dx))
            else:
                yaw = actor.get_transform().rotation.yaw

            # Teleportar actor (para demo)
            transform = carla.Transform(
                carla.Location(x=cx, y=cy, z=cz),
                carla.Rotation(yaw=yaw)
            )
            actor.set_transform(transform)

            # Esperar según velocidad
            time.sleep(0.033 / speed_multiplier)  # ~30 FPS

        logger.info(f"✓ Replay completado para track {track_id}")

    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas de actores spawneados."""
        return {
            'total_actors': len(self.spawned_actors),
            'active_actors': sum(1 for a in self.spawned_actors.values() if a.is_active),
            'actors_by_class': self._count_by_class()
        }

    def _count_by_class(self) -> Dict[str, int]:
        """Cuenta actores por clase."""
        counts = {}
        for actor_info in self.spawned_actors.values():
            counts[actor_info.clase] = counts.get(actor_info.clase, 0) + 1
        return counts

    def save_actor_registry(self, path: str):
        """
        Guarda el registro de actores spawneados para persistencia.

        Args:
            path: Ruta del archivo JSON de salida
        """
        registry = {
            'spawned_actors': {
                str(track_id): {
                    'actor_id': info.actor_id,
                    'track_id': info.track_id,
                    'blueprint_id': info.blueprint_id,
                    'clase': info.clase,
                    'spawn_location': info.spawn_location,
                    'num_waypoints': len(info.waypoints),
                    'is_active': info.is_active
                }
                for track_id, info in self.spawned_actors.items()
            },
            'stats': self.get_stats()
        }

        with open(path, 'w') as f:
            json.dump(registry, f, indent=2)

        logger.info(f"Registro de actores guardado en: {path}")


def calibrate_transform_interactive():
    """
    Función helper para calibrar la transformación de coordenadas interactivamente.

    El usuario debe proporcionar pares de puntos (píxel, CARLA) conocidos.
    """
    print("="*60)
    print("CALIBRACIÓN DE TRANSFORMACIÓN PÍXEL → CARLA")
    print("="*60)
    print("\nNecesitas identificar puntos de referencia conocidos en el video")
    print("y sus coordenadas correspondientes en CARLA.\n")

    # Escala píxel→metro
    print("1. ¿Cuántos píxeles equivalen a 1 metro en el video?")
    print("   (Mide un objeto conocido en píxeles)")
    pixels_per_meter = float(input("   Píxeles por metro: "))
    pixel_to_meter_scale = 1.0 / pixels_per_meter

    # Origen
    print("\n2. ¿Cuál es la coordenada CARLA del punto (0, 0) del video?")
    origin_x = float(input("   CARLA X: "))
    origin_y = float(input("   CARLA Y: "))
    origin_z = float(input("   CARLA Z (altura): "))

    # Rotación
    print("\n3. ¿Cuál es la rotación del video respecto al norte de CARLA? (grados)")
    rotation = float(input("   Rotación: "))

    # Flip Y
    flip_y = input("\n4. ¿Invertir eje Y? (s/n): ").lower() == 's'

    transform = CoordinateTransform(
        pixel_to_meter_scale=pixel_to_meter_scale,
        origin_carla_x=origin_x,
        origin_carla_y=origin_y,
        origin_carla_z=origin_z,
        rotation_degrees=rotation,
        flip_y=flip_y
    )

    # Guardar
    save_path = input("\n5. Ruta para guardar configuración (config/transform.json): ")
    if not save_path:
        save_path = "config/transform.json"

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    transform.save_config(save_path)

    print(f"\n✓ Configuración guardada en: {save_path}")
    return transform


if __name__ == "__main__":
    print("Módulo de integración con CARLA")
    print("\nPara calibrar la transformación píxel→CARLA:")
    print("  from carla_integration import calibrate_transform_interactive")
    print("  calibrate_transform_interactive()")
