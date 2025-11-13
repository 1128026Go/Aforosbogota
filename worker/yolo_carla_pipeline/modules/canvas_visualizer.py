"""
Visualizador interactivo de trayectorias en canvas (lienzo relativo).

Este módulo permite visualizar trayectorias sobre un canvas de píxeles con:
- Múltiples modos de coloración (clase, dirección, velocidad, patrón)
- Overlays configurables (heatmap, ROIs, métricas)
- Soporte para imagen de fondo opcional
- Filtros interactivos por clase, dirección, etc.
- Exportación de visualizaciones

Uso:
    visualizer = CanvasVisualizer(frame_width=1280, frame_height=720)
    visualizer.load_trajectories("output/tracks.json")
    visualizer.visualize(color_by='class', show_arrows=True)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button, CheckButtons
import numpy as np
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image

from helpers import get_color_for_track, calculate_bounds, COLOR_SCHEMES

logger = logging.getLogger(__name__)


class CanvasVisualizer:
    """Visualizador interactivo de trayectorias en canvas."""

    def __init__(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
        background_image: Optional[str] = None
    ):
        """
        Inicializa el visualizador.

        Args:
            frame_width: Ancho del canvas en píxeles
            frame_height: Alto del canvas en píxeles
            background_image: Ruta opcional a imagen de fondo
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.background_image = background_image

        self.trajectories: List[Dict] = []
        self.filtered_trajectories: List[Dict] = []

        self.current_color_mode = 'class'
        self.show_arrows = True
        self.show_heatmap = False
        self.show_rois = False

        # Filtros activos
        self.active_classes = set()
        self.active_directions = set()

    def load_trajectories(self, json_path: str):
        """
        Carga trayectorias desde JSON.

        Args:
            json_path: Ruta al archivo JSON con trayectorias
        """
        with open(json_path, 'r') as f:
            self.trajectories = json.load(f)

        # Extraer clases únicas
        self.active_classes = set(t['clase'] for t in self.trajectories)

        logger.info(f"Cargadas {len(self.trajectories)} trayectorias")
        logger.info(f"Clases encontradas: {self.active_classes}")

        self.filtered_trajectories = self.trajectories.copy()

    def filter_trajectories(
        self,
        classes: Optional[List[str]] = None,
        min_length: int = 0,
        max_length: Optional[int] = None,
        min_duration: int = 0
    ):
        """
        Filtra trayectorias según criterios.

        Args:
            classes: Lista de clases a incluir (None = todas)
            min_length: Longitud mínima de trayectoria
            max_length: Longitud máxima de trayectoria
            min_duration: Duración mínima en frames
        """
        filtered = self.trajectories.copy()

        if classes:
            filtered = [t for t in filtered if t['clase'] in classes]

        if min_length > 0:
            filtered = [t for t in filtered if t['length'] >= min_length]

        if max_length:
            filtered = [t for t in filtered if t['length'] <= max_length]

        if min_duration > 0:
            filtered = [t for t in filtered if t['duration_frames'] >= min_duration]

        self.filtered_trajectories = filtered
        logger.info(f"Filtradas: {len(filtered)}/{len(self.trajectories)} trayectorias")

    def visualize(
        self,
        color_by: str = 'class',
        show_arrows: bool = True,
        show_heatmap: bool = False,
        show_rois: bool = False,
        alpha: float = 0.6,
        linewidth: float = 1.5,
        save_path: Optional[str] = None,
        title: Optional[str] = None
    ):
        """
        Visualiza las trayectorias en el canvas.

        Args:
            color_by: Modo de coloración ('class', 'direction', 'speed', 'pattern')
            show_arrows: Mostrar flechas de dirección
            show_heatmap: Overlay de heatmap
            show_rois: Mostrar regiones de interés
            alpha: Transparencia de las líneas
            linewidth: Grosor de las líneas
            save_path: Ruta para guardar imagen (None = mostrar)
            title: Título del gráfico
        """
        fig, ax = plt.subplots(figsize=(16, 12))

        # Cargar imagen de fondo si existe
        if self.background_image and Path(self.background_image).exists():
            try:
                bg_img = Image.open(self.background_image)
                ax.imshow(bg_img, extent=[0, self.frame_width, self.frame_height, 0], alpha=0.3)
                logger.info(f"Imagen de fondo cargada: {self.background_image}")
            except Exception as e:
                logger.warning(f"Error cargando imagen de fondo: {e}")

        # Configurar límites
        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        ax.set_aspect('equal')

        # Dibujar trayectorias
        legend_handles = {}

        for track in self.filtered_trajectories:
            if len(track['positions']) < 2:
                continue

            color = get_color_for_track(track, color_by=color_by)
            positions = np.array(track['positions'])

            # Línea de trayectoria
            line = ax.plot(
                positions[:, 0],
                positions[:, 1],
                color=color,
                alpha=alpha,
                linewidth=linewidth,
                zorder=2
            )[0]

            # Agregar a leyenda si no existe
            label = track.get('clase', 'unknown')
            if label not in legend_handles:
                legend_handles[label] = line

            # Flechas de dirección
            if show_arrows and len(positions) >= 10:
                # Dibujar flecha en el punto medio
                mid_idx = len(positions) // 2
                start = positions[mid_idx]
                end = positions[min(mid_idx + 5, len(positions) - 1)]

                dx = end[0] - start[0]
                dy = end[1] - start[1]

                if np.sqrt(dx**2 + dy**2) > 5:  # Solo si hay movimiento significativo
                    ax.arrow(
                        start[0], start[1], dx, dy,
                        head_width=15, head_length=20,
                        fc=color, ec=color, alpha=alpha * 0.8,
                        zorder=3
                    )

        # Overlay de heatmap
        if show_heatmap:
            self._add_heatmap_overlay(ax)

        # ROIs
        if show_rois:
            self._add_roi_overlay(ax)

        # Configurar título y etiquetas
        if title:
            ax.set_title(title, fontsize=16, fontweight='bold')
        else:
            ax.set_title(f'Trayectorias coloreadas por {color_by}', fontsize=16, fontweight='bold')

        ax.set_xlabel('X (píxeles)', fontsize=12)
        ax.set_ylabel('Y (píxeles)', fontsize=12)

        # Leyenda
        if legend_handles:
            ax.legend(
                legend_handles.values(),
                legend_handles.keys(),
                loc='upper right',
                fontsize=10,
                framealpha=0.9
            )

        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Info en esquina
        info_text = f"Total trayectorias: {len(self.filtered_trajectories)}\n"
        info_text += f"Color por: {color_by}"
        ax.text(
            0.02, 0.98, info_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=10
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Visualización guardada en: {save_path}")
            plt.close()
        else:
            plt.show()

    def _add_heatmap_overlay(self, ax, grid_size: int = 50):
        """Agrega overlay de heatmap de densidad."""
        grid_h = (self.frame_height // grid_size) + 1
        grid_w = (self.frame_width // grid_size) + 1
        heatmap = np.zeros((grid_h, grid_w))

        # Contar posiciones en cada celda
        for track in self.filtered_trajectories:
            for pos in track['positions']:
                x, y = pos
                grid_x = int(x // grid_size)
                grid_y = int(y // grid_size)

                if 0 <= grid_x < grid_w and 0 <= grid_y < grid_h:
                    heatmap[grid_y, grid_x] += 1

        # Overlay
        extent = [0, self.frame_width, self.frame_height, 0]
        im = ax.imshow(
            heatmap,
            extent=extent,
            cmap='hot',
            alpha=0.4,
            interpolation='bilinear',
            zorder=1
        )

        # Colorbar pequeño
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins = inset_axes(ax, width="3%", height="30%", loc='lower left')
        plt.colorbar(im, cax=axins, orientation='vertical')

    def _add_roi_overlay(self, ax):
        """Agrega overlay de ROIs por defecto."""
        # ROI central (intersección)
        center_x, center_y = self.frame_width / 2, self.frame_height / 2
        margin = 100

        roi_rect = patches.Rectangle(
            (center_x - margin, center_y - margin),
            margin * 2, margin * 2,
            linewidth=2, edgecolor='red', facecolor='red',
            alpha=0.2, linestyle='--', zorder=4
        )
        ax.add_patch(roi_rect)
        ax.text(
            center_x, center_y - margin - 10,
            'Centro/Intersección',
            ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )

    def create_interactive_viewer(self):
        """
        Crea un visualizador interactivo con controles.

        Permite cambiar color_by, toggle overlays, filtrar clases en tiempo real.
        """
        fig, ax = plt.subplots(figsize=(18, 12))
        plt.subplots_adjust(left=0.3)

        # Panel de controles
        ax_color = plt.axes([0.05, 0.8, 0.15, 0.15])
        ax_class = plt.axes([0.05, 0.4, 0.15, 0.35])
        ax_overlay = plt.axes([0.05, 0.2, 0.15, 0.15])

        # Botones de modo de color
        color_modes = ['class', 'direction', 'speed', 'pattern']
        color_buttons = CheckButtons(ax_color, color_modes, [True, False, False, False])

        # Checkboxes de clases
        class_list = sorted(list(self.active_classes))
        class_checks = CheckButtons(ax_class, class_list, [True] * len(class_list))

        # Checkboxes de overlays
        overlay_options = ['Heatmap', 'ROIs', 'Arrows']
        overlay_checks = CheckButtons(ax_overlay, overlay_options, [False, False, True])

        def update_visualization(label):
            """Actualiza visualización cuando cambia algún control."""
            ax.clear()

            # Determinar modo de color activo
            active_colors = [c for c, s in zip(color_modes, color_buttons.get_status()) if s]
            color_by = active_colors[0] if active_colors else 'class'

            # Filtrar por clases activas
            active_class_list = [c for c, s in zip(class_list, class_checks.get_status()) if s]
            self.filter_trajectories(classes=active_class_list if active_class_list else None)

            # Determinar overlays activos
            overlay_status = overlay_checks.get_status()
            show_heatmap = overlay_status[0]
            show_rois = overlay_status[1]
            show_arrows = overlay_status[2]

            # Re-visualizar (interno, no usar self.visualize para evitar nueva ventana)
            self._draw_on_ax(
                ax,
                color_by=color_by,
                show_arrows=show_arrows,
                show_heatmap=show_heatmap,
                show_rois=show_rois
            )

            fig.canvas.draw_idle()

        color_buttons.on_clicked(update_visualization)
        class_checks.on_clicked(update_visualization)
        overlay_checks.on_clicked(update_visualization)

        # Visualización inicial
        self._draw_on_ax(ax, color_by='class', show_arrows=True)

        plt.show()

    def _draw_on_ax(
        self,
        ax,
        color_by: str = 'class',
        show_arrows: bool = True,
        show_heatmap: bool = False,
        show_rois: bool = False
    ):
        """Dibuja en un eje específico (para visualizador interactivo)."""
        # Configurar límites
        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        ax.set_aspect('equal')

        # Dibujar trayectorias
        legend_handles = {}

        for track in self.filtered_trajectories:
            if len(track['positions']) < 2:
                continue

            color = get_color_for_track(track, color_by=color_by)
            positions = np.array(track['positions'])

            line = ax.plot(
                positions[:, 0], positions[:, 1],
                color=color, alpha=0.6, linewidth=1.5, zorder=2
            )[0]

            label = track.get('clase', 'unknown')
            if label not in legend_handles:
                legend_handles[label] = line

            if show_arrows and len(positions) >= 10:
                mid_idx = len(positions) // 2
                start = positions[mid_idx]
                end = positions[min(mid_idx + 5, len(positions) - 1)]
                dx, dy = end[0] - start[0], end[1] - start[1]

                if np.sqrt(dx**2 + dy**2) > 5:
                    ax.arrow(
                        start[0], start[1], dx, dy,
                        head_width=15, head_length=20,
                        fc=color, ec=color, alpha=0.5, zorder=3
                    )

        if show_heatmap:
            self._add_heatmap_overlay(ax)

        if show_rois:
            self._add_roi_overlay(ax)

        ax.set_title(f'Trayectorias ({color_by})', fontsize=14, fontweight='bold')
        ax.set_xlabel('X (píxeles)', fontsize=11)
        ax.set_ylabel('Y (píxeles)', fontsize=11)
        ax.grid(True, alpha=0.3)

        if legend_handles:
            ax.legend(legend_handles.values(), legend_handles.keys(), loc='upper right', fontsize=9)

    def export_animation(
        self,
        output_path: str,
        fps: int = 30,
        duration_seconds: Optional[int] = None
    ):
        """
        Exporta animación de trayectorias evolucionando en el tiempo.

        Args:
            output_path: Ruta del video de salida (MP4)
            fps: Frames por segundo
            duration_seconds: Duración del video (None = basado en datos)
        """
        try:
            from matplotlib.animation import FuncAnimation, FFMpegWriter
        except ImportError:
            logger.error("matplotlib.animation no disponible. Instala ffmpeg")
            return

        # TODO: Implementar animación frame-por-frame
        logger.warning("export_animation no implementado aún")


if __name__ == "__main__":
    import sys

    # Ejemplo de uso
    if len(sys.argv) < 2:
        print("Uso: python canvas_visualizer.py <tracks.json> [--interactive]")
        sys.exit(1)

    visualizer = CanvasVisualizer(frame_width=1280, frame_height=720)
    visualizer.load_trajectories(sys.argv[1])

    if '--interactive' in sys.argv:
        visualizer.create_interactive_viewer()
    else:
        # Generar visualizaciones estáticas
        output_dir = Path("output/canvas_viz")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Por clase
        visualizer.filter_trajectories(min_length=10)
        visualizer.visualize(
            color_by='class',
            show_arrows=True,
            save_path=str(output_dir / "trajectories_class.png"),
            title="Trayectorias por Clase"
        )

        # Por dirección (requiere análisis previo)
        # visualizer.visualize(
        #     color_by='direction',
        #     save_path=str(output_dir / "trajectories_direction.png")
        # )

        # Con heatmap
        visualizer.visualize(
            color_by='class',
            show_heatmap=True,
            save_path=str(output_dir / "trajectories_heatmap.png"),
            title="Trayectorias + Heatmap de Densidad"
        )

        print(f"Visualizaciones guardadas en: {output_dir}")
