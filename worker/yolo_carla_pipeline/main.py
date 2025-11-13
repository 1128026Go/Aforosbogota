"""
Pipeline completo de análisis YOLOv8 PKL → Visualización → Integración CARLA

Este script orquesta todo el pipeline:
1. Lee archivos PKL con detecciones YOLOv8
2. Ejecuta tracking multi-objeto para reconstruir trayectorias
3. Calcula métricas de tráfico
4. Genera visualizaciones completas
5. (Opcional) Integra trayectorias en CARLA Simulator

Uso:
    # Solo análisis y visualización
    python main.py --pkl data/pkls/Gx010322.pkl --output output/

    # Con integración CARLA
    python main.py --pkl data/pkls/Gx010322.pkl --carla --host localhost --port 2000

    # Batch processing de múltiples PKLs
    python main.py --pkl-dir data/pkls/ --output output/
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict
import json
import time

# Configurar logging PRIMERO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Agregar modules al path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from read_pkl import load_and_validate_pkl, PKLReader
from tracking import MultiObjectTracker, Track
from analysis import TrajectoryAnalyzer, TrafficMetrics, create_default_rois
from visualize import TrafficVisualizer

# Importar CARLA solo si está disponible
try:
    from carla_integration import CARLAIntegration, CoordinateTransform
    CARLA_AVAILABLE = True
except Exception as e:
    CARLA_AVAILABLE = False
    CARLAIntegration = None
    CoordinateTransform = None
    logger.warning(f"CARLA integration not available: {e}")


class Pipeline:
    """Pipeline completo de análisis de tráfico."""

    def __init__(
        self,
        output_dir: str = "output",
        confidence_threshold: float = 0.5,
        enable_carla: bool = False,
        carla_host: str = "localhost",
        carla_port: int = 2000,
        carla_config: Optional[str] = None
    ):
        """
        Inicializa el pipeline.

        Args:
            output_dir: Directorio de salida
            confidence_threshold: Umbral de confianza para detecciones
            enable_carla: Habilitar integración con CARLA
            carla_host: Host del servidor CARLA
            carla_port: Puerto del servidor CARLA
            carla_config: Ruta al archivo de configuración de transformación
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.confidence_threshold = confidence_threshold
        self.enable_carla = enable_carla

        # Crear subdirectorios
        self.traj_dir = self.output_dir / "trajectories"
        self.metrics_dir = self.output_dir / "metrics"
        self.viz_dir = self.output_dir / "visualizations"

        for d in [self.traj_dir, self.metrics_dir, self.viz_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Integración CARLA
        self.carla_integration: Optional[CARLAIntegration] = None
        if enable_carla:
            try:
                # Cargar configuración de transformación
                if carla_config and Path(carla_config).exists():
                    transform = CoordinateTransform.load_config(carla_config)
                else:
                    logger.warning("No se especificó configuración CARLA, usando valores por defecto")
                    transform = CoordinateTransform()

                self.carla_integration = CARLAIntegration(
                    host=carla_host,
                    port=carla_port,
                    coordinate_transform=transform
                )
                self.carla_integration.connect()

            except Exception as e:
                logger.error(f"Error inicializando CARLA: {e}")
                logger.warning("El pipeline continuará sin integración CARLA")
                self.enable_carla = False

    def process_pkl(self, pkl_path: str, filter_classes: Optional[List[str]] = None) -> Dict:
        """
        Procesa un archivo PKL completo.

        Args:
            pkl_path: Ruta al archivo PKL
            filter_classes: Clases a filtrar (None = todas)

        Returns:
            Diccionario con resultados del procesamiento
        """
        pkl_name = Path(pkl_path).stem
        logger.info("="*70)
        logger.info(f"PROCESANDO: {pkl_name}")
        logger.info("="*70)

        start_time = time.time()

        # FASE 1: Leer PKL
        logger.info("FASE 1: Leyendo y validando PKL...")
        metadata, detections, stats = load_and_validate_pkl(
            pkl_path,
            confidence_threshold=self.confidence_threshold,
            filter_classes=filter_classes
        )

        if metadata is None:
            logger.error(f"Error procesando {pkl_path}")
            return {'success': False, 'error': 'Failed to load PKL'}

        logger.info(f"✓ PKL cargado: {len(detections)} detecciones válidas")

        # FASE 2: Tracking
        logger.info("\nFASE 2: Ejecutando tracking multi-objeto...")
        tracker = MultiObjectTracker(max_age=30, min_hits=3, iou_threshold=0.3)

        # Agrupar detecciones por frame
        detections_by_frame = {}
        for det in detections:
            frame = det.fotograma
            if frame not in detections_by_frame:
                detections_by_frame[frame] = []
            detections_by_frame[frame].append({
                'bbox': det.bbox,
                'clase': det.clase,
                'confianza': det.confianza
            })

        # Ejecutar tracking frame por frame
        frames = sorted(detections_by_frame.keys())
        for frame in frames:
            tracker.update(detections_by_frame[frame], frame)

        tracks = tracker.get_valid_tracks()
        logger.info(f"✓ Tracking completo: {len(tracks)} trayectorias válidas")

        # Guardar trayectorias
        tracks_file = self.traj_dir / f"{pkl_name}_tracks.json"
        self._save_tracks(tracks, tracks_file)

        # FASE 3: Análisis de tráfico
        logger.info("\nFASE 3: Analizando métricas de tráfico...")

        # Crear ROIs por defecto
        rois = create_default_rois(metadata.width, metadata.height)

        analyzer = TrajectoryAnalyzer(
            frame_width=metadata.width,
            frame_height=metadata.height,
            fps=metadata.fps,
            rois=rois
        )

        metrics = analyzer.analyze_tracks(tracks)

        logger.info(f"✓ Análisis completo:")
        logger.info(f"  - Total vehículos: {metrics.total_vehicles}")
        logger.info(f"  - Velocidad promedio: {metrics.avg_velocity_px:.2f} px/frame")
        logger.info(f"  - Score de congestión: {metrics.congestion_score:.3f}")

        # Guardar métricas
        metrics_file = self.metrics_dir / f"{pkl_name}_metrics.json"
        self._save_metrics(metrics, metadata, metrics_file)

        # Generar heatmap
        heatmap = analyzer.identify_hotspots(tracks, grid_size=50)

        # FASE 4: Visualización
        logger.info("\nFASE 4: Generando visualizaciones...")

        visualizer = TrafficVisualizer(
            frame_width=metadata.width,
            frame_height=metadata.height,
            output_dir=str(self.viz_dir)
        )

        visualizer.create_full_report(
            tracks=tracks,
            metrics=metrics,
            analyzer=analyzer,
            heatmap=heatmap,
            pkl_name=pkl_name
        )

        logger.info(f"✓ Visualizaciones generadas en: {self.viz_dir / pkl_name}")

        # FASE 5: Integración CARLA (opcional)
        carla_stats = None
        if self.enable_carla and self.carla_integration:
            logger.info("\nFASE 5: Integrando con CARLA Simulator...")

            try:
                carla_stats = self.carla_integration.spawn_all_tracks(tracks, spawn_rate=0.05)

                # Guardar registro de actores
                registry_file = self.output_dir / f"{pkl_name}_carla_registry.json"
                self.carla_integration.save_actor_registry(str(registry_file))

                logger.info(f"✓ Integración CARLA completa: {sum(carla_stats.values())} actores spawneados")

            except Exception as e:
                logger.error(f"Error en integración CARLA: {e}")

        # Resumen
        elapsed_time = time.time() - start_time

        logger.info("\n" + "="*70)
        logger.info("PROCESAMIENTO COMPLETO")
        logger.info("="*70)
        logger.info(f"Tiempo total: {elapsed_time:.2f} segundos")
        logger.info(f"Detecciones procesadas: {len(detections)}")
        logger.info(f"Trayectorias válidas: {len(tracks)}")
        logger.info(f"Outputs guardados en: {self.output_dir}")
        logger.info("="*70)

        return {
            'success': True,
            'pkl_name': pkl_name,
            'detections': len(detections),
            'tracks': len(tracks),
            'metrics': metrics.to_dict(),
            'carla_stats': carla_stats,
            'elapsed_time': elapsed_time
        }

    def process_directory(self, pkl_dir: str, filter_classes: Optional[List[str]] = None) -> List[Dict]:
        """
        Procesa todos los PKL de un directorio.

        Args:
            pkl_dir: Directorio con archivos PKL
            filter_classes: Clases a filtrar

        Returns:
            Lista de resultados
        """
        pkl_files = list(Path(pkl_dir).glob("*.pkl"))

        if not pkl_files:
            logger.error(f"No se encontraron archivos PKL en: {pkl_dir}")
            return []

        logger.info(f"Encontrados {len(pkl_files)} archivos PKL")

        results = []
        for i, pkl_file in enumerate(pkl_files, 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"ARCHIVO {i}/{len(pkl_files)}")
            logger.info(f"{'='*70}")

            result = self.process_pkl(str(pkl_file), filter_classes=filter_classes)
            results.append(result)

        # Resumen global
        logger.info("\n" + "="*70)
        logger.info("RESUMEN GLOBAL")
        logger.info("="*70)

        successful = sum(1 for r in results if r.get('success', False))
        total_tracks = sum(r.get('tracks', 0) for r in results)

        logger.info(f"Archivos procesados: {successful}/{len(pkl_files)}")
        logger.info(f"Trayectorias totales: {total_tracks}")
        logger.info("="*70)

        return results

    def _save_tracks(self, tracks: List[Track], output_path: Path):
        """Guarda trayectorias a JSON."""
        tracks_data = []

        for track in tracks:
            tracks_data.append({
                'track_id': track.track_id,
                'clase': track.clase,
                'length': track.length,
                'duration_frames': track.duration_frames,
                'avg_confidence': track.avg_confidence,
                'positions': track.positions,
                'frames': track.frames,
                'bboxes': track.bboxes
            })

        with open(output_path, 'w') as f:
            json.dump(tracks_data, f, indent=2)

        logger.info(f"Trayectorias guardadas en: {output_path}")

    def _save_metrics(self, metrics: TrafficMetrics, metadata: 'PKLMetadata', output_path: Path):
        """Guarda métricas a JSON."""
        data = {
            'metadata': metadata.to_dict(),
            'metrics': metrics.to_dict()
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Métricas guardadas en: {output_path}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Pipeline de análisis YOLOv8 PKL → Visualización → CARLA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Analizar un PKL
  python main.py --pkl data/pkls/Gx010322.pkl

  # Analizar con CARLA
  python main.py --pkl data/pkls/Gx010322.pkl --carla --carla-config config/transform.json

  # Procesar directorio completo
  python main.py --pkl-dir data/pkls/ --output output/

  # Filtrar solo autos y camiones
  python main.py --pkl data/pkls/Gx010322.pkl --classes car truck
        """
    )

    # Argumentos principales
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pkl', type=str, help='Ruta al archivo PKL')
    group.add_argument('--pkl-dir', type=str, help='Directorio con archivos PKL')

    parser.add_argument('--output', type=str, default='output', help='Directorio de salida')
    parser.add_argument('--confidence', type=float, default=0.5, help='Umbral de confianza')
    parser.add_argument('--classes', nargs='+', help='Clases a filtrar (ej: car truck bus)')

    # Argumentos CARLA
    parser.add_argument('--carla', action='store_true', help='Habilitar integración CARLA')
    parser.add_argument('--carla-host', type=str, default='localhost', help='Host CARLA')
    parser.add_argument('--carla-port', type=int, default=2000, help='Puerto CARLA')
    parser.add_argument('--carla-config', type=str, help='Archivo de configuración de transformación')

    args = parser.parse_args()

    # Inicializar pipeline
    pipeline = Pipeline(
        output_dir=args.output,
        confidence_threshold=args.confidence,
        enable_carla=args.carla,
        carla_host=args.carla_host,
        carla_port=args.carla_port,
        carla_config=args.carla_config
    )

    # Procesar
    try:
        if args.pkl:
            pipeline.process_pkl(args.pkl, filter_classes=args.classes)
        else:
            pipeline.process_directory(args.pkl_dir, filter_classes=args.classes)

        logger.info("\n✓ Pipeline completado exitosamente")

    except KeyboardInterrupt:
        logger.warning("\n⚠ Pipeline interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Error en pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
