"""
Sistema de Persistencia a Base de Datos.

Guarda información de aforos y trayectorias en PostgreSQL para análisis futuro.
"""

import json
import sys
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class DatabasePersistence:
    """Maneja la persistencia de datos de aforos en PostgreSQL."""

    def __init__(self, config: dict):
        """Inicializa conexión a la base de datos."""
        self.config = config
        self.conn = None

    def connect(self):
        """Conecta a la base de datos."""
        try:
            db_config = self.config['configuracion_global']['base_de_datos']

            self.conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['puerto'],
                database=db_config['nombre_db'],
                user=db_config['usuario'],
                password=db_config['password']
            )

            logger.info(f"✓ Conectado a base de datos: {db_config['nombre_db']}")
            return True

        except Exception as e:
            logger.error(f"Error conectando a base de datos: {e}")
            return False

    def create_tables(self):
        """Crea las tablas necesarias si no existen."""
        logger.info("Creando/verificando tablas...")

        sql_create_tables = """
        -- Tabla de aforos
        CREATE TABLE IF NOT EXISTS aforos (
            id VARCHAR(50) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            video_source VARCHAR(255),
            offset_x FLOAT DEFAULT 0,
            offset_y FLOAT DEFAULT 0,
            color_tema VARCHAR(20),
            descripcion TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT true
        );

        -- Tabla de sesiones de análisis
        CREATE TABLE IF NOT EXISTS sesiones_analisis (
            id SERIAL PRIMARY KEY,
            aforo_id VARCHAR(50) REFERENCES aforos(id),
            fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            video_path TEXT,
            num_trayectorias INTEGER,
            frame_inicio INTEGER,
            frame_fin INTEGER,
            duracion_segundos FLOAT,
            metadata JSONB
        );

        -- Tabla de trayectorias
        CREATE TABLE IF NOT EXISTS trayectorias (
            id SERIAL PRIMARY KEY,
            sesion_id INTEGER REFERENCES sesiones_analisis(id),
            aforo_id VARCHAR(50) REFERENCES aforos(id),
            track_id INTEGER NOT NULL,
            clase VARCHAR(50) NOT NULL,
            num_frames INTEGER,
            duracion_frames INTEGER,
            confianza_promedio FLOAT,
            distancia_total FLOAT,
            velocidad_promedio FLOAT,
            frames INTEGER[],
            positions JSONB,
            metadata JSONB
        );

        -- Tabla de estadísticas agregadas por aforo
        CREATE TABLE IF NOT EXISTS estadisticas_aforo (
            id SERIAL PRIMARY KEY,
            aforo_id VARCHAR(50) REFERENCES aforos(id),
            fecha DATE DEFAULT CURRENT_DATE,
            total_vehiculos INTEGER,
            por_clase JSONB,
            velocidad_promedio FLOAT,
            hora_pico_inicio TIME,
            hora_pico_fin TIME,
            metadata JSONB
        );

        -- Índices para mejorar rendimiento
        CREATE INDEX IF NOT EXISTS idx_trayectorias_aforo ON trayectorias(aforo_id);
        CREATE INDEX IF NOT EXISTS idx_trayectorias_clase ON trayectorias(clase);
        CREATE INDEX IF NOT EXISTS idx_sesiones_aforo ON sesiones_analisis(aforo_id);
        CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON sesiones_analisis(fecha_analisis);
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_tables)
            self.conn.commit()
            cursor.close()
            logger.info("✓ Tablas creadas/verificadas correctamente")
            return True

        except Exception as e:
            logger.error(f"Error creando tablas: {e}")
            self.conn.rollback()
            return False

    def upsert_aforo(self, aforo_config: dict):
        """Inserta o actualiza información de un aforo."""
        sql = """
        INSERT INTO aforos (id, nombre, video_source, offset_x, offset_y, color_tema, descripcion, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            nombre = EXCLUDED.nombre,
            video_source = EXCLUDED.video_source,
            offset_x = EXCLUDED.offset_x,
            offset_y = EXCLUDED.offset_y,
            color_tema = EXCLUDED.color_tema,
            descripcion = EXCLUDED.descripcion,
            activo = EXCLUDED.activo
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                aforo_config['id'],
                aforo_config['nombre'],
                aforo_config['video_source'],
                aforo_config['offset_x'],
                aforo_config['offset_y'],
                aforo_config['color_tema'],
                aforo_config['descripcion'],
                aforo_config['activo']
            ))
            self.conn.commit()
            cursor.close()
            logger.info(f"  ✓ Aforo guardado: {aforo_config['nombre']}")
            return True

        except Exception as e:
            logger.error(f"Error guardando aforo: {e}")
            self.conn.rollback()
            return False

    def create_sesion(self, aforo_id: str, trajectories: list, video_path: str = None) -> int:
        """Crea una sesión de análisis y retorna su ID."""
        # Calcular estadísticas
        if not trajectories:
            return None

        frames_all = []
        for traj in trajectories:
            frames_all.extend(traj.get('frames', []))

        frame_inicio = min(frames_all) if frames_all else 0
        frame_fin = max(frames_all) if frames_all else 0

        sql = """
        INSERT INTO sesiones_analisis
        (aforo_id, video_path, num_trayectorias, frame_inicio, frame_fin, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                aforo_id,
                video_path,
                len(trajectories),
                frame_inicio,
                frame_fin,
                json.dumps({'fecha_procesamiento': datetime.now().isoformat()})
            ))
            sesion_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            logger.info(f"  ✓ Sesión creada: ID={sesion_id}")
            return sesion_id

        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            self.conn.rollback()
            return None

    def save_trajectories(self, sesion_id: int, aforo_id: str, trajectories: list):
        """Guarda trayectorias en batch."""
        if not trajectories:
            return True

        sql = """
        INSERT INTO trayectorias
        (sesion_id, aforo_id, track_id, clase, num_frames, duracion_frames,
         confianza_promedio, frames, positions, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            cursor = self.conn.cursor()
            batch_data = []

            for traj in trajectories:
                track_id = traj.get('track_id_original', traj.get('track_id'))
                frames = traj.get('frames', [])

                batch_data.append((
                    sesion_id,
                    aforo_id,
                    track_id,
                    traj.get('clase', 'unknown'),
                    len(traj.get('positions', [])),
                    traj.get('duration_frames', 0),
                    traj.get('avg_confidence', 0.0),
                    frames,
                    json.dumps(traj.get('positions', [])),
                    json.dumps({
                        'aforo_offset': traj.get('aforo_offset', [0, 0])
                    })
                ))

            execute_batch(cursor, sql, batch_data, page_size=1000)
            self.conn.commit()
            cursor.close()
            logger.info(f"  ✓ {len(batch_data)} trayectorias guardadas")
            return True

        except Exception as e:
            logger.error(f"Error guardando trayectorias: {e}")
            self.conn.rollback()
            return False

    def save_combined_data(self, combined_data: dict):
        """Guarda todos los datos combinados en la base de datos."""
        logger.info("\n" + "="*70)
        logger.info("GUARDANDO EN BASE DE DATOS")
        logger.info("="*70)

        trajectories_by_aforo = {}
        for traj in combined_data['trajectories']:
            aforo_id = traj.get('aforo_id')
            if aforo_id not in trajectories_by_aforo:
                trajectories_by_aforo[aforo_id] = []
            trajectories_by_aforo[aforo_id].append(traj)

        # Guardar cada aforo
        for aforo_info in combined_data['aforos']:
            aforo_id = aforo_info['id']
            logger.info(f"\nProcesando: {aforo_info['nombre']}")

            # Buscar configuración completa del aforo
            aforo_config = next(
                (a for a in self.config['aforos'] if a['id'] == aforo_id),
                None
            )

            if not aforo_config:
                logger.warning(f"  Configuración no encontrada para {aforo_id}")
                continue

            # Guardar aforo
            if not self.upsert_aforo(aforo_config):
                continue

            # Crear sesión
            trajectories = trajectories_by_aforo.get(aforo_id, [])
            sesion_id = self.create_sesion(
                aforo_id,
                trajectories,
                aforo_config.get('video_source')
            )

            if sesion_id:
                # Guardar trayectorias
                self.save_trajectories(sesion_id, aforo_id, trajectories)

        logger.info("\n" + "="*70)
        logger.info("✓ DATOS GUARDADOS EXITOSAMENTE")
        logger.info("="*70)

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            logger.info("Conexión cerrada")


def main():
    if len(sys.argv) < 2:
        print("Uso: python persist_to_database.py <combined_aforos.json>")
        sys.exit(1)

    combined_path = sys.argv[1]

    print("="*70)
    print("SISTEMA DE PERSISTENCIA A BASE DE DATOS")
    print("="*70)

    # Cargar configuración
    config_path = Path(__file__).parent.parent / "config" / "aforos_config.json"

    if not config_path.exists():
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Cargar datos combinados
    logger.info(f"\nCargando datos desde: {combined_path}")
    with open(combined_path, 'r', encoding='utf-8') as f:
        combined_data = json.load(f)

    logger.info(f"  - Trayectorias: {len(combined_data['trajectories'])}")
    logger.info(f"  - Aforos: {len(combined_data['aforos'])}")

    # Conectar y guardar
    db = DatabasePersistence(config)

    if not db.connect():
        logger.error("No se pudo conectar a la base de datos")
        sys.exit(1)

    if not db.create_tables():
        logger.error("Error creando tablas")
        db.close()
        sys.exit(1)

    db.save_combined_data(combined_data)
    db.close()

    print("\n✓ Proceso completado exitosamente")


if __name__ == "__main__":
    main()
