"""
Overlay de trayectorias sobre OpenStreetMap usando Folium.

Este módulo permite visualizar trayectorias sobre un mapa real de OpenStreetMap.
Las coordenadas píxel se transforman a lat/lon usando la configuración de calibración.

Características:
- Overlay de trayectorias sobre OSM
- Coloreado por clase, dirección, velocidad
- Heatmap de densidad
- Markers para puntos de interés
- Clusters para gran cantidad de datos
- Exportación a HTML interactivo

IMPORTANTE - CALIBRACIÓN REQUERIDA:
El archivo de calibración (config/calibration.json) debe tener las coordenadas
GPS reales de las esquinas del frame del video.

Para calibrar:
1. Abre Google Maps o similar
2. Identifica la esquina superior izquierda del área del video
3. Copia las coordenadas (lat, lon) → origin_lat, origin_lon
4. Identifica la esquina inferior derecha
5. Copia las coordenadas (lat, lon) → corner_lat, corner_lon
6. Guarda en config/calibration.json

Si no tienes coordenadas reales, el mapa usará valores por defecto
de Bogotá, pero las trayectorias NO estarán correctamente posicionadas.

Uso:
    overlay = MapOverlay(calibration_config="config/calibration.json")
    overlay.load_trajectories("output/tracks.json")
    overlay.create_map(save_path="output/map.html")
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    logging.warning("folium no disponible. Instala con: pip install folium")

import numpy as np

from helpers import CalibrationConfig, CoordinateTransformer, COLOR_SCHEMES, get_color_for_track

logger = logging.getLogger(__name__)


class MapOverlay:
    """Overlay de trayectorias sobre OpenStreetMap."""

    def __init__(
        self,
        calibration_config: Optional[str] = None,
        default_zoom: int = 15
    ):
        """
        Inicializa el overlay de mapa.

        Args:
            calibration_config: Ruta al archivo de calibración JSON
            default_zoom: Nivel de zoom por defecto
        """
        if not FOLIUM_AVAILABLE:
            raise ImportError("folium no está instalado. Ejecuta: pip install folium")

        # Cargar configuración de calibración
        if calibration_config and Path(calibration_config).exists():
            self.config = CalibrationConfig.load(calibration_config)
            logger.info(f"Configuración cargada desde: {calibration_config}")
        else:
            logger.warning("⚠️  Usando configuración por defecto (NO calibrada)")
            logger.warning("   Las trayectorias NO estarán correctamente posicionadas en el mapa")
            logger.warning("   Edita config/calibration.json con coordenadas GPS reales")
            self.config = CalibrationConfig()

        self.transformer = CoordinateTransformer(self.config)
        self.default_zoom = default_zoom

        self.trajectories: List[Dict] = []
        self.map = None

        # Centro del mapa (promedio de esquinas)
        self.map_center = [
            (self.config.origin_lat + self.config.corner_lat) / 2,
            (self.config.origin_lon + self.config.corner_lon) / 2
        ]

    def load_trajectories(self, json_path: str):
        """
        Carga trayectorias desde JSON.

        Args:
            json_path: Ruta al archivo JSON con trayectorias
        """
        with open(json_path, 'r') as f:
            self.trajectories = json.load(f)

        logger.info(f"Cargadas {len(self.trajectories)} trayectorias para mapa")

    def create_map(
        self,
        color_by: str = 'class',
        show_heatmap: bool = False,
        show_markers: bool = False,
        max_trajectories: Optional[int] = None,
        save_path: str = "output/map.html"
    ):
        """
        Crea mapa interactivo con trayectorias.

        Args:
            color_by: Modo de coloración ('class', 'direction', 'speed')
            show_heatmap: Mostrar heatmap de densidad
            show_markers: Mostrar markers en inicio/fin de trayectorias
            max_trajectories: Límite de trayectorias a mostrar (None = todas)
            save_path: Ruta para guardar HTML
        """
        # Crear mapa base
        self.map = folium.Map(
            location=self.map_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )

        # Agregar tiles alternativos
        folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(self.map)
        folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(self.map)

        # Filtrar trayectorias si es necesario
        tracks_to_plot = self.trajectories[:max_trajectories] if max_trajectories else self.trajectories

        logger.info(f"Dibujando {len(tracks_to_plot)} trayectorias en mapa...")

        # Dibujar trayectorias
        for i, track in enumerate(tracks_to_plot):
            if len(track['positions']) < 2:
                continue

            # Transformar a lat/lon
            latlon_positions = [
                self.transformer.pixel_to_latlon(px, py)
                for px, py in track['positions']
            ]

            # Color
            color = get_color_for_track(track, color_by=color_by)

            # Crear polyline
            folium.PolyLine(
                locations=latlon_positions,
                color=color,
                weight=2,
                opacity=0.7,
                popup=f"{track['clase']} (Track {track['track_id']})<br>"
                      f"Longitud: {track['length']} puntos<br>"
                      f"Duración: {track['duration_frames']} frames",
                tooltip=f"{track['clase']}"
            ).add_to(self.map)

            # Markers de inicio/fin
            if show_markers:
                # Inicio (verde)
                folium.CircleMarker(
                    location=latlon_positions[0],
                    radius=4,
                    color='green',
                    fill=True,
                    fillColor='green',
                    fillOpacity=0.6,
                    popup=f"Inicio: {track['clase']}"
                ).add_to(self.map)

                # Fin (rojo)
                folium.CircleMarker(
                    location=latlon_positions[-1],
                    radius=4,
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.6,
                    popup=f"Fin: {track['clase']}"
                ).add_to(self.map)

            # Progreso
            if (i + 1) % 100 == 0:
                logger.info(f"  Procesadas {i + 1}/{len(tracks_to_plot)} trayectorias...")

        # Heatmap de densidad
        if show_heatmap:
            self._add_heatmap(tracks_to_plot)

        # Agregar rectángulo del área del video
        self._add_frame_boundary()

        # Leyenda
        self._add_legend(color_by)

        # Control de capas
        folium.LayerControl().add_to(self.map)

        # Guardar
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        self.map.save(save_path)

        logger.info(f"✓ Mapa guardado en: {save_path}")
        logger.info(f"  Abre en navegador para visualizar")

        # Verificar calibración
        self._print_calibration_warning()

    def _add_heatmap(self, tracks: List[Dict]):
        """Agrega heatmap de densidad al mapa."""
        # Recopilar todas las posiciones
        all_positions = []
        for track in tracks:
            for px, py in track['positions']:
                lat, lon = self.transformer.pixel_to_latlon(px, py)
                all_positions.append([lat, lon])

        if all_positions:
            # Crear heatmap
            heat_map = plugins.HeatMap(
                all_positions,
                name='Heatmap Densidad',
                min_opacity=0.2,
                max_opacity=0.8,
                radius=15,
                blur=20,
                gradient={
                    0.0: 'blue',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            )
            heat_map.add_to(self.map)

            logger.info(f"  Heatmap agregado con {len(all_positions)} puntos")

    def _add_frame_boundary(self):
        """Agrega rectángulo mostrando el área del video."""
        # Esquinas del frame
        top_left = [self.config.origin_lat, self.config.origin_lon]
        bottom_right = [self.config.corner_lat, self.config.corner_lon]
        top_right = [self.config.origin_lat, self.config.corner_lon]
        bottom_left = [self.config.corner_lat, self.config.origin_lon]

        # Rectángulo
        folium.Polygon(
            locations=[top_left, top_right, bottom_right, bottom_left],
            color='blue',
            weight=3,
            fill=False,
            opacity=0.7,
            popup="Área del video",
            dash_array='10'
        ).add_to(self.map)

        # Markers en esquinas
        folium.Marker(
            location=top_left,
            popup="Esquina superior izquierda (píxel 0,0)",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(self.map)

        folium.Marker(
            location=bottom_right,
            popup=f"Esquina inferior derecha (píxel {self.config.frame_width},{self.config.frame_height})",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(self.map)

    def _add_legend(self, color_by: str):
        """Agrega leyenda al mapa."""
        # HTML de leyenda
        legend_html = f'''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 180px; height: auto;
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius:5px; padding: 10px">
        <p style="margin:0; font-weight:bold;">Trayectorias</p>
        <p style="margin:5px 0; font-size:12px;">Coloreado por: {color_by}</p>
        '''

        # Agregar colores según el modo
        if color_by == 'class':
            for clase, color in COLOR_SCHEMES['class'].items():
                legend_html += f'<p style="margin:3px 0;"><span style="color:{color};">■</span> {clase}</p>'

        legend_html += '</div>'

        # Agregar al mapa
        self.map.get_root().html.add_child(folium.Element(legend_html))

    def _print_calibration_warning(self):
        """Imprime advertencia sobre calibración."""
        print("\n" + "="*70)
        print("⚠️  IMPORTANTE - VERIFICAR CALIBRACIÓN")
        print("="*70)
        print("\nSi las trayectorias NO están correctamente posicionadas en el mapa:")
        print("\n1. Abre el mapa generado en un navegador")
        print("2. Verifica si el rectángulo azul coincide con el área real del video")
        print("3. Si NO coincide, edita config/calibration.json con coordenadas GPS correctas:")
        print(f"\n   Actual configuración:")
        print(f"   - Esquina superior izquierda: ({self.config.origin_lat:.6f}, {self.config.origin_lon:.6f})")
        print(f"   - Esquina inferior derecha: ({self.config.corner_lat:.6f}, {self.config.corner_lon:.6f})")
        print("\n4. Para calibrar correctamente:")
        print("   a. Identifica puntos de referencia en el video (edificios, cruces, etc.)")
        print("   b. Encuentra esos puntos en Google Maps")
        print("   c. Copia las coordenadas GPS")
        print("   d. Actualiza config/calibration.json")
        print("\n5. Vuelve a generar el mapa con las coordenadas correctas")
        print("="*70 + "\n")

    def create_clustered_map(
        self,
        save_path: str = "output/map_clustered.html"
    ):
        """
        Crea mapa con markers clusterizados (mejor para muchas trayectorias).

        Args:
            save_path: Ruta para guardar HTML
        """
        self.map = folium.Map(
            location=self.map_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )

        # Crear cluster
        marker_cluster = plugins.MarkerCluster().add_to(self.map)

        # Agregar markers por trayectoria
        for track in self.trajectories:
            if not track['positions']:
                continue

            # Posición inicial
            px, py = track['positions'][0]
            lat, lon = self.transformer.pixel_to_latlon(px, py)

            # Color según clase
            color_map = {
                'car': 'blue',
                'truck': 'red',
                'bus': 'purple',
                'motorcycle': 'orange',
                'person': 'green'
            }
            color = color_map.get(track['clase'], 'gray')

            # Marker
            folium.Marker(
                location=[lat, lon],
                popup=f"{track['clase']} (Track {track['track_id']})<br>"
                      f"Longitud: {track['length']} puntos<br>"
                      f"Duración: {track['duration_frames']} frames",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(marker_cluster)

        # Guardar
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        self.map.save(save_path)

        logger.info(f"✓ Mapa clusterizado guardado en: {save_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python map_overlay.py <tracks.json> [--heatmap] [--markers] [--clustered]")
        print("\nOpciones:")
        print("  --heatmap    Agregar heatmap de densidad")
        print("  --markers    Mostrar markers inicio/fin")
        print("  --clustered  Crear mapa con markers clusterizados")
        print("\nEjemplo:")
        print("  python map_overlay.py output/trajectories/tracks.json --heatmap")
        sys.exit(1)

    # Argumentos
    tracks_path = sys.argv[1]
    show_heatmap = '--heatmap' in sys.argv
    show_markers = '--markers' in sys.argv
    clustered = '--clustered' in sys.argv

    # Crear overlay
    overlay = MapOverlay(calibration_config="config/calibration.json")
    overlay.load_trajectories(tracks_path)

    if clustered:
        overlay.create_clustered_map(save_path="output/map_clustered.html")
    else:
        overlay.create_map(
            color_by='class',
            show_heatmap=show_heatmap,
            show_markers=show_markers,
            max_trajectories=500,  # Limitar para no sobrecargar el navegador
            save_path="output/map.html"
        )

    print("\n✓ Mapa generado exitosamente")
    print("  Abre el archivo HTML en un navegador para visualizar")
