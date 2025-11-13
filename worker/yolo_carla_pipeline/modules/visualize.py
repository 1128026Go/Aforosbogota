"""
Módulo de visualización de trayectorias y métricas de tráfico.

Genera:
- Gráficos de trayectorias coloreadas por clase/sentido/patrón
- Heatmaps de densidad de tráfico
- Histogramas de velocidades
- Diagramas de flujo direccional
- Gráficos temporales
- Reportes visuales completos
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import seaborn as sns

logger = logging.getLogger(__name__)

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 100


CLASS_COLORS = {
    'car': '#3498db',  # azul
    'truck': '#e74c3c',  # rojo
    'bus': '#9b59b6',  # púrpura
    'motorcycle': '#f39c12',  # naranja
    'bicycle': '#2ecc71',  # verde
    'person': '#1abc9c',  # turquesa
    'traffic light': '#e67e22'  # naranja oscuro
}

DIRECTION_COLORS = {
    'north': '#3498db',
    'south': '#e74c3c',
    'east': '#2ecc71',
    'west': '#f39c12',
    'northeast': '#9b59b6',
    'northwest': '#1abc9c',
    'southeast': '#e67e22',
    'southwest': '#95a5a6',
    'stationary': '#7f8c8d'
}


class TrafficVisualizer:
    """Visualizador de trayectorias y métricas de tráfico."""

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        output_dir: str = "output/visualizations"
    ):
        """
        Inicializa el visualizador.

        Args:
            frame_width: Ancho del frame en píxeles
            frame_height: Alto del frame en píxeles
            output_dir: Directorio de salida para gráficos
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_trajectories_by_class(
        self,
        tracks: List['Track'],
        title: str = "Trayectorias por Clase",
        save_path: Optional[str] = None,
        show_arrows: bool = True
    ):
        """
        Dibuja trayectorias coloreadas por clase de vehículo.

        Args:
            tracks: Lista de trayectorias
            title: Título del gráfico
            save_path: Ruta para guardar (None = mostrar)
            show_arrows: Mostrar flechas de dirección
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        # Configurar límites
        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)  # Invertir Y
        ax.set_aspect('equal')

        # Dibujar trayectorias por clase
        for track in tracks:
            if len(track.positions) < 2:
                continue

            color = CLASS_COLORS.get(track.clase, '#95a5a6')
            positions = np.array(track.positions)

            # Línea de trayectoria
            ax.plot(
                positions[:, 0],
                positions[:, 1],
                color=color,
                alpha=0.6,
                linewidth=1.5,
                label=track.clase if track.clase not in ax.get_legend_handles_labels()[1] else ""
            )

            # Flecha de dirección
            if show_arrows and len(positions) >= 2:
                mid_idx = len(positions) // 2
                start = positions[mid_idx]
                end = positions[mid_idx + 1] if mid_idx + 1 < len(positions) else positions[-1]
                dx = end[0] - start[0]
                dy = end[1] - start[1]

                ax.arrow(
                    start[0], start[1], dx, dy,
                    head_width=15, head_length=20,
                    fc=color, ec=color, alpha=0.7
                )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('X (píxeles)', fontsize=12)
        ax.set_ylabel('Y (píxeles)', fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_trajectories_by_direction(
        self,
        tracks: List['Track'],
        analyzer: 'TrajectoryAnalyzer',
        title: str = "Trayectorias por Dirección",
        save_path: Optional[str] = None
    ):
        """
        Dibuja trayectorias coloreadas por dirección de movimiento.

        Args:
            tracks: Lista de trayectorias
            analyzer: Analizador de trayectorias
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        ax.set_aspect('equal')

        # Calcular direcciones
        for track in tracks:
            if len(track.positions) < 2:
                continue

            direction = analyzer.calculate_direction(track)
            color = DIRECTION_COLORS.get(direction.value, '#95a5a6')
            positions = np.array(track.positions)

            ax.plot(
                positions[:, 0],
                positions[:, 1],
                color=color,
                alpha=0.6,
                linewidth=1.5,
                label=direction.value if direction.value not in ax.get_legend_handles_labels()[1] else ""
            )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('X (píxeles)', fontsize=12)
        ax.set_ylabel('Y (píxeles)', fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_heatmap(
        self,
        heatmap: np.ndarray,
        title: str = "Heatmap de Densidad de Tráfico",
        save_path: Optional[str] = None,
        cmap: str = 'hot'
    ):
        """
        Dibuja un heatmap de densidad de tráfico.

        Args:
            heatmap: Matriz 2D con densidad
            title: Título del gráfico
            save_path: Ruta para guardar
            cmap: Colormap de matplotlib
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        im = ax.imshow(heatmap, cmap=cmap, aspect='auto', origin='upper')
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Grid X', fontsize=12)
        ax.set_ylabel('Grid Y', fontsize=12)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Densidad de tráfico', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Heatmap guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_velocity_distribution(
        self,
        tracks: List['Track'],
        analyzer: 'TrajectoryAnalyzer',
        title: str = "Distribución de Velocidades",
        save_path: Optional[str] = None
    ):
        """
        Dibuja histograma de distribución de velocidades.

        Args:
            tracks: Lista de trayectorias
            analyzer: Analizador de trayectorias
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Recopilar velocidades
        velocities_by_class = {}
        all_velocities = []

        for track in tracks:
            vel = analyzer.calculate_velocity_magnitude(track)
            if vel is not None:
                all_velocities.append(vel)
                if track.clase not in velocities_by_class:
                    velocities_by_class[track.clase] = []
                velocities_by_class[track.clase].append(vel)

        # Histograma general
        if all_velocities:
            ax1.hist(all_velocities, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
            ax1.axvline(np.mean(all_velocities), color='red', linestyle='--', linewidth=2, label=f'Media: {np.mean(all_velocities):.2f} px/frame')
            ax1.set_xlabel('Velocidad (píxeles/frame)', fontsize=12)
            ax1.set_ylabel('Frecuencia', fontsize=12)
            ax1.set_title('Distribución General de Velocidades', fontsize=14)
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # Box plot por clase
        if velocities_by_class:
            data_to_plot = []
            labels = []
            for clase, vels in sorted(velocities_by_class.items()):
                if vels:
                    data_to_plot.append(vels)
                    labels.append(f"{clase}\n(n={len(vels)})")

            bp = ax2.boxplot(data_to_plot, labels=labels, patch_artist=True)

            # Colorear boxes
            for patch, clase in zip(bp['boxes'], velocities_by_class.keys()):
                patch.set_facecolor(CLASS_COLORS.get(clase, '#95a5a6'))
                patch.set_alpha(0.7)

            ax2.set_ylabel('Velocidad (píxeles/frame)', fontsize=12)
            ax2.set_title('Velocidades por Clase', fontsize=14)
            ax2.grid(True, alpha=0.3, axis='y')

        plt.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_metrics_summary(
        self,
        metrics: 'TrafficMetrics',
        title: str = "Resumen de Métricas de Tráfico",
        save_path: Optional[str] = None
    ):
        """
        Dibuja un resumen visual de métricas calculadas.

        Args:
            metrics: Objeto TrafficMetrics
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # 1. Conteo por clase (Pie chart)
        ax1 = fig.add_subplot(gs[0, 0])
        if metrics.vehicles_by_class:
            classes = list(metrics.vehicles_by_class.keys())
            counts = list(metrics.vehicles_by_class.values())
            colors = [CLASS_COLORS.get(c, '#95a5a6') for c in classes]

            ax1.pie(counts, labels=classes, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribución por Clase', fontweight='bold')

        # 2. Direcciones (Bar chart)
        ax2 = fig.add_subplot(gs[0, 1])
        if metrics.direction_distribution:
            directions = list(metrics.direction_distribution.keys())
            dir_counts = list(metrics.direction_distribution.values())
            colors = [DIRECTION_COLORS.get(d, '#95a5a6') for d in directions]

            ax2.bar(range(len(directions)), dir_counts, color=colors, alpha=0.7)
            ax2.set_xticks(range(len(directions)))
            ax2.set_xticklabels(directions, rotation=45, ha='right')
            ax2.set_ylabel('Cantidad')
            ax2.set_title('Distribución Direccional', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

        # 3. Patrones de giro
        ax3 = fig.add_subplot(gs[0, 2])
        if metrics.turn_patterns:
            patterns = list(metrics.turn_patterns.keys())
            pattern_counts = list(metrics.turn_patterns.values())

            ax3.bar(patterns, pattern_counts, color='#3498db', alpha=0.7)
            ax3.set_ylabel('Cantidad')
            ax3.set_title('Patrones de Giro', fontweight='bold')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3, axis='y')

        # 4. Velocidades por clase (Bar chart horizontal)
        ax4 = fig.add_subplot(gs[1, :2])
        if metrics.velocity_distribution:
            classes = list(metrics.velocity_distribution.keys())
            velocities = list(metrics.velocity_distribution.values())
            colors = [CLASS_COLORS.get(c, '#95a5a6') for c in classes]

            y_pos = np.arange(len(classes))
            ax4.barh(y_pos, velocities, color=colors, alpha=0.7)
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(classes)
            ax4.set_xlabel('Velocidad promedio (píxeles/frame)')
            ax4.set_title('Velocidades Promedio por Clase', fontweight='bold')
            ax4.grid(True, alpha=0.3, axis='x')

        # 5. Métricas clave (Text)
        ax5 = fig.add_subplot(gs[1, 2])
        ax5.axis('off')

        metrics_text = f"""
MÉTRICAS CLAVE

Total Vehículos: {metrics.total_vehicles}

Velocidad Promedio:
  {metrics.avg_velocity_px:.2f} px/frame

Velocidad Máxima:
  {metrics.max_velocity_px:.2f} px/frame

Score Congestión:
  {metrics.congestion_score:.3f}
  {'🔴 Alta' if metrics.congestion_score > 0.7 else '🟡 Media' if metrics.congestion_score > 0.3 else '🟢 Baja'}

Densidad Promedio:
  {metrics.avg_track_density:.6f} tracks/px²
        """

        ax5.text(0.1, 0.9, metrics_text, fontsize=11, verticalalignment='top',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        # 6. Distribución temporal (si hay datos)
        if metrics.temporal_distribution:
            ax6 = fig.add_subplot(gs[2, :])
            frames = sorted(metrics.temporal_distribution.keys())
            counts = [metrics.temporal_distribution[f] for f in frames]

            ax6.plot(frames, counts, color='#3498db', linewidth=2)
            ax6.fill_between(frames, counts, alpha=0.3, color='#3498db')
            ax6.set_xlabel('Frame')
            ax6.set_ylabel('Número de detecciones')
            ax6.set_title('Distribución Temporal de Tráfico', fontweight='bold')
            ax6.grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=18, fontweight='bold', y=0.995)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Resumen guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_roi_analysis(
        self,
        tracks: List['Track'],
        rois: List['ROI'],
        title: str = "Análisis de ROIs",
        save_path: Optional[str] = None
    ):
        """
        Visualiza ROIs y trayectorias que pasan por ellas.

        Args:
            tracks: Lista de trayectorias
            rois: Lista de ROIs
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        ax.set_aspect('equal')

        # Dibujar ROIs
        for i, roi in enumerate(rois):
            polygon = patches.Polygon(
                roi.polygon,
                closed=True,
                fill=True,
                alpha=0.2,
                facecolor=f'C{i}',
                edgecolor=f'C{i}',
                linewidth=2,
                label=roi.name
            )
            ax.add_patch(polygon)

        # Dibujar trayectorias
        for track in tracks:
            if len(track.positions) < 2:
                continue

            positions = np.array(track.positions)
            ax.plot(
                positions[:, 0],
                positions[:, 1],
                color='gray',
                alpha=0.3,
                linewidth=1
            )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('X (píxeles)', fontsize=12)
        ax.set_ylabel('Y (píxeles)', fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Gráfico de ROI guardado en: {save_path}")
        else:
            plt.show()

        plt.close()

    def create_full_report(
        self,
        tracks: List['Track'],
        metrics: 'TrafficMetrics',
        analyzer: 'TrajectoryAnalyzer',
        heatmap: Optional[np.ndarray] = None,
        pkl_name: str = "report"
    ):
        """
        Genera un reporte visual completo con todos los análisis.

        Args:
            tracks: Lista de trayectorias
            metrics: Métricas calculadas
            analyzer: Analizador de trayectorias
            heatmap: Heatmap de densidad (opcional)
            pkl_name: Nombre base para archivos de salida
        """
        logger.info(f"Generando reporte completo para {pkl_name}...")

        # Crear carpeta de salida
        report_dir = self.output_dir / pkl_name
        report_dir.mkdir(parents=True, exist_ok=True)

        # 1. Trayectorias por clase
        self.plot_trajectories_by_class(
            tracks,
            title=f"Trayectorias por Clase - {pkl_name}",
            save_path=str(report_dir / "01_trajectories_by_class.png")
        )

        # 2. Trayectorias por dirección
        self.plot_trajectories_by_direction(
            tracks,
            analyzer,
            title=f"Trayectorias por Dirección - {pkl_name}",
            save_path=str(report_dir / "02_trajectories_by_direction.png")
        )

        # 3. Heatmap
        if heatmap is not None:
            self.plot_heatmap(
                heatmap,
                title=f"Heatmap de Densidad - {pkl_name}",
                save_path=str(report_dir / "03_heatmap.png")
            )

        # 4. Velocidades
        self.plot_velocity_distribution(
            tracks,
            analyzer,
            title=f"Distribución de Velocidades - {pkl_name}",
            save_path=str(report_dir / "04_velocity_distribution.png")
        )

        # 5. Resumen de métricas
        self.plot_metrics_summary(
            metrics,
            title=f"Resumen de Métricas - {pkl_name}",
            save_path=str(report_dir / "05_metrics_summary.png")
        )

        # 6. ROIs si existen
        if analyzer.rois:
            self.plot_roi_analysis(
                tracks,
                analyzer.rois,
                title=f"Análisis de ROIs - {pkl_name}",
                save_path=str(report_dir / "06_roi_analysis.png")
            )

        logger.info(f"✓ Reporte completo generado en: {report_dir}")


if __name__ == "__main__":
    print("Módulo de visualización de tráfico")
    print("Usa este módulo importándolo en tu código principal")
