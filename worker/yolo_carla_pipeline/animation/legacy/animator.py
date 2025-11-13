"""
Animador de trayectorias con controles de reproducción.

Este módulo proporciona animación frame-por-frame de trayectorias en canvas infinito:
- Reproducción con controles (play, pause, rewind, speed)
- Canvas dinámico ajustado a bounding box de datos
- Visualización 2D y 3D
- Trails opcionales (estelas de trayectorias)
- Exportación a video

Uso:
    animator = TrajectoryAnimator(manager, mode='2d')
    animator.animate(fps=30, speed=1.0, show_trails=True)
    # O exportar:
    animator.export_video('output.mp4', fps=30, dpi=150)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.widgets import Button, Slider
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict
from pathlib import Path

from trajectories import TrajectoryManager

logger = logging.getLogger(__name__)


class TrajectoryAnimator:
    """Animador de trayectorias con canvas infinito."""

    def __init__(
        self,
        trajectory_manager: TrajectoryManager,
        mode: str = '2d',
        trail_length: int = 10,
        marker_size: int = 100,
        show_ids: bool = False
    ):
        """
        Inicializa el animador.

        Args:
            trajectory_manager: TrajectoryManager con trayectorias y métricas
            mode: Modo de visualización ('2d' o '3d')
            trail_length: Longitud de estelas (frames previos a mostrar, 0 = sin estelas)
            marker_size: Tamaño de marcadores de posición
            show_ids: Mostrar IDs de tracks
        """
        self.manager = trajectory_manager
        self.mode = mode
        self.trail_length = trail_length
        self.marker_size = marker_size
        self.show_ids = show_ids

        # Calcular bounding box de todas las trayectorias
        self.bbox = self._calculate_bounding_box()

        # Estado de animación
        self.current_frame = self.manager.frame_range[0]
        self.is_playing = False
        self.playback_speed = 1.0

        # Elementos visuales
        self.fig = None
        self.ax = None
        self.animation = None

        # Para almacenar trails
        self.trail_history: Dict[int, List[Tuple[float, float]]] = {}

        logger.info(f"TrajectoryAnimator inicializado (modo: {mode})")
        logger.info(f"  Canvas bounds: X=[{self.bbox['min_x']:.1f}, {self.bbox['max_x']:.1f}], "
                   f"Y=[{self.bbox['min_y']:.1f}, {self.bbox['max_y']:.1f}]")
        logger.info(f"  Dimensiones: {self.bbox['width']:.1f} x {self.bbox['height']:.1f} px")

    def _calculate_bounding_box(self) -> Dict:
        """Calcula bounding box de todas las trayectorias."""
        all_x = []
        all_y = []

        for traj in self.manager.trajectories:
            for pos in traj['positions']:
                all_x.append(pos[0])
                all_y.append(pos[1])

        # Agregar margen del 10%
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        margin_x = (max_x - min_x) * 0.1
        margin_y = (max_y - min_y) * 0.1

        return {
            'min_x': min_x - margin_x,
            'max_x': max_x + margin_x,
            'min_y': min_y - margin_y,
            'max_y': max_y + margin_y,
            'width': (max_x - min_x) + 2 * margin_x,
            'height': (max_y - min_y) + 2 * margin_y
        }

    def animate(
        self,
        fps: int = 30,
        speed: float = 1.0,
        show_trails: bool = True,
        show_full_trajectories: bool = False,
        save_path: Optional[str] = None
    ):
        """
        Inicia animación interactiva.

        Args:
            fps: Frames por segundo de la animación
            speed: Velocidad de reproducción (1.0 = normal, 2.0 = 2x, etc.)
            show_trails: Mostrar estelas de posiciones previas
            show_full_trajectories: Mostrar trayectorias completas en el fondo
            save_path: Si se especifica, guarda a video en lugar de mostrar
        """
        self.playback_speed = speed

        # Crear figura
        if self.mode == '2d':
            self.fig, self.ax = plt.subplots(figsize=(16, 12))
        elif self.mode == '3d':
            from mpl_toolkits.mplot3d import Axes3D
            self.fig = plt.figure(figsize=(16, 12))
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            raise ValueError(f"Modo desconocido: {self.mode}")

        # Configurar canvas
        self._setup_canvas(show_full_trajectories)

        # Crear controles de reproducción
        if save_path is None:
            self._create_controls()

        # Total de frames
        total_frames = self.manager.frame_range[1] - self.manager.frame_range[0] + 1

        # Crear animación
        interval = int(1000 / (fps * self.playback_speed))

        self.animation = FuncAnimation(
            self.fig,
            self._update_frame,
            frames=range(self.manager.frame_range[0], self.manager.frame_range[1] + 1),
            interval=interval,
            repeat=True,
            fargs=(show_trails,)
        )

        logger.info(f"Animacion configurada: {total_frames} frames @ {fps} FPS (velocidad {speed}x)")

        if save_path:
            self._save_animation(save_path, fps)
        else:
            plt.show()

    def _setup_canvas(self, show_full_trajectories: bool):
        """Configura el canvas inicial."""
        if self.mode == '2d':
            self.ax.set_xlim(self.bbox['min_x'], self.bbox['max_x'])
            self.ax.set_ylim(self.bbox['max_y'], self.bbox['min_y'])  # Invertir Y
            self.ax.set_aspect('equal')
            self.ax.grid(True, alpha=0.3, linestyle='--')
            self.ax.set_xlabel('X (pixels)', fontsize=12)
            self.ax.set_ylabel('Y (pixels)', fontsize=12)

            # Dibujar trayectorias completas en el fondo (opcional)
            if show_full_trajectories:
                for traj in self.manager.trajectories:
                    positions = np.array(traj['positions'])
                    color = self.manager.colors.get(traj['track_id'], '#95a5a6')
                    self.ax.plot(
                        positions[:, 0], positions[:, 1],
                        color=color, alpha=0.2, linewidth=0.5, zorder=1
                    )

        elif self.mode == '3d':
            self.ax.set_xlim(self.bbox['min_x'], self.bbox['max_x'])
            self.ax.set_ylim(self.bbox['min_y'], self.bbox['max_y'])
            self.ax.set_zlim(0, 100)  # Altura arbitraria para visualización
            self.ax.set_xlabel('X (pixels)')
            self.ax.set_ylabel('Y (pixels)')
            self.ax.set_zlabel('Time (frames)')

            # En modo 3D, mostrar trayectorias completas con eje temporal
            if show_full_trajectories:
                for traj in self.manager.trajectories:
                    positions = np.array(traj['positions'])
                    frames_normalized = np.array(traj['frames']) - self.manager.frame_range[0]
                    color = self.manager.colors.get(traj['track_id'], '#95a5a6')

                    self.ax.plot(
                        positions[:, 0], positions[:, 1], frames_normalized,
                        color=color, alpha=0.3, linewidth=1, zorder=1
                    )

    def _create_controls(self):
        """Crea controles de reproducción."""
        # Ajustar layout para hacer espacio a controles
        plt.subplots_adjust(bottom=0.2)

        # Botón Play/Pause
        ax_play = plt.axes([0.2, 0.05, 0.1, 0.05])
        self.btn_play = Button(ax_play, 'Play/Pause')
        self.btn_play.on_clicked(self._toggle_play)

        # Botón Reset
        ax_reset = plt.axes([0.35, 0.05, 0.1, 0.05])
        self.btn_reset = Button(ax_reset, 'Reset')
        self.btn_reset.on_clicked(self._reset)

        # Slider de velocidad
        ax_speed = plt.axes([0.5, 0.05, 0.3, 0.03])
        self.slider_speed = Slider(
            ax_speed, 'Speed', 0.1, 5.0,
            valinit=self.playback_speed,
            valstep=0.1
        )
        self.slider_speed.on_changed(self._update_speed)

        # Texto de frame actual
        self.frame_text = self.ax.text(
            0.02, 0.98, '',
            transform=self.ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=10,
            zorder=100
        )

    def _update_frame(self, frame: int, show_trails: bool):
        """
        Actualiza visualización para un frame específico.

        Args:
            frame: Número de frame a visualizar
            show_trails: Mostrar estelas
        """
        # Limpiar marcadores y trails previos
        # (mantener trayectorias de fondo si se configuraron)
        if hasattr(self, '_active_artists'):
            for artist in self._active_artists:
                artist.remove()

        self._active_artists = []

        # Obtener trayectorias activas en este frame
        active_tracks = self.manager.get_active_at_frame(frame)

        # Dibujar cada trayectoria activa
        for track_info in active_tracks:
            track_id = track_info['track_id']
            position = track_info['position']
            color = track_info['color']

            # Actualizar trail history
            if track_id not in self.trail_history:
                self.trail_history[track_id] = []

            self.trail_history[track_id].append(tuple(position))

            # Limitar longitud de trail
            if len(self.trail_history[track_id]) > self.trail_length:
                self.trail_history[track_id].pop(0)

            # Dibujar trail (estela)
            if show_trails and len(self.trail_history[track_id]) > 1:
                trail = np.array(self.trail_history[track_id])

                if self.mode == '2d':
                    line, = self.ax.plot(
                        trail[:, 0], trail[:, 1],
                        color=color, alpha=0.5, linewidth=2, zorder=2
                    )
                    self._active_artists.append(line)
                elif self.mode == '3d':
                    # Trail en 3D
                    z_values = np.linspace(0, 10, len(trail))
                    line, = self.ax.plot(
                        trail[:, 0], trail[:, 1], z_values,
                        color=color, alpha=0.5, linewidth=2, zorder=2
                    )
                    self._active_artists.append(line)

            # Dibujar marcador de posición actual
            if self.mode == '2d':
                marker = self.ax.scatter(
                    position[0], position[1],
                    c=[color], s=self.marker_size, alpha=0.9,
                    edgecolors='white', linewidths=1.5, zorder=3
                )
                self._active_artists.append(marker)

                # ID del track (opcional)
                if self.show_ids:
                    text = self.ax.text(
                        position[0], position[1] - 15,
                        f"{track_id}",
                        fontsize=8, ha='center',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7),
                        zorder=4
                    )
                    self._active_artists.append(text)

            elif self.mode == '3d':
                marker = self.ax.scatter(
                    position[0], position[1], 10,
                    c=[color], s=self.marker_size, alpha=0.9,
                    edgecolors='white', linewidths=1.5, zorder=3
                )
                self._active_artists.append(marker)

        # Actualizar texto de frame
        stats = self.manager.get_summary_stats()
        frame_progress = frame - self.manager.frame_range[0]
        total_frames = stats['total_frames']

        info_text = f"Frame: {frame}/{self.manager.frame_range[1]}\n"
        info_text += f"Progreso: {frame_progress}/{total_frames} ({100*frame_progress/total_frames:.1f}%)\n"
        info_text += f"Activos: {len(active_tracks)}\n"
        info_text += f"Velocidad: {self.playback_speed:.1f}x"

        if hasattr(self, 'frame_text'):
            self.frame_text.set_text(info_text)

        self.current_frame = frame

        return self._active_artists

    def _toggle_play(self, event):
        """Toggle reproducción."""
        if self.is_playing:
            self.animation.pause()
            self.is_playing = False
            logger.info("Animacion pausada")
        else:
            self.animation.resume()
            self.is_playing = True
            logger.info("Animacion reanudada")

    def _reset(self, event):
        """Reinicia animación al principio."""
        self.current_frame = self.manager.frame_range[0]
        self.trail_history.clear()
        self.animation.frame_seq = self.animation.new_frame_seq()
        logger.info("Animacion reiniciada")

    def _update_speed(self, val):
        """Actualiza velocidad de reproducción."""
        self.playback_speed = val
        # Re-calcular intervalo
        if hasattr(self, 'animation') and self.animation:
            new_interval = int(1000 / (30 * self.playback_speed))
            self.animation.event_source.interval = new_interval
            logger.info(f"Velocidad actualizada: {val:.1f}x")

    def _save_animation(self, save_path: str, fps: int):
        """Guarda animación a video."""
        logger.info(f"Guardando animacion a: {save_path}")

        try:
            writer = FFMpegWriter(fps=fps, metadata={'artist': 'TrajectoryAnimator'})
            self.animation.save(save_path, writer=writer, dpi=150)
            logger.info(f"Video guardado exitosamente: {save_path}")
        except Exception as e:
            logger.error(f"Error guardando video: {e}")
            logger.warning("Asegurate de tener ffmpeg instalado y en el PATH")

    def export_video(
        self,
        output_path: str,
        fps: int = 30,
        dpi: int = 150,
        show_trails: bool = True,
        show_full_trajectories: bool = False
    ):
        """
        Exporta animación a video MP4.

        Args:
            output_path: Ruta del archivo de salida
            fps: Frames por segundo
            dpi: Resolución
            show_trails: Mostrar estelas
            show_full_trajectories: Mostrar trayectorias completas
        """
        logger.info(f"Exportando animacion a video: {output_path}")

        # Crear animación sin controles
        self.animate(
            fps=fps,
            speed=1.0,
            show_trails=show_trails,
            show_full_trajectories=show_full_trajectories,
            save_path=output_path
        )

    def export_frames(
        self,
        output_dir: str,
        fps: int = 30,
        show_trails: bool = True
    ):
        """
        Exporta frames individuales a imágenes PNG.

        Args:
            output_dir: Directorio de salida
            fps: Frames a exportar por segundo
            show_trails: Mostrar estelas
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando frames a: {output_dir}")

        # Crear figura
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        self._setup_canvas(show_full_trajectories=False)

        frame_count = 0
        for frame in range(self.manager.frame_range[0], self.manager.frame_range[1] + 1):
            self._update_frame(frame, show_trails)

            # Guardar frame
            frame_path = output_path / f"frame_{frame_count:06d}.png"
            plt.savefig(frame_path, dpi=150, bbox_inches='tight')

            frame_count += 1

            if frame_count % 100 == 0:
                logger.info(f"  Exportados {frame_count} frames...")

        plt.close(self.fig)
        logger.info(f"Exportacion completa: {frame_count} frames en {output_dir}")


if __name__ == "__main__":
    import sys
    import json
    from parser import TrajectoryParser
    from trajectories import TrajectoryManager

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Uso: python animator.py <tracks.json> [--mode 2d|3d] [--speed 1.0] [--export output.mp4]")
        print("\nOpciones:")
        print("  --mode 2d|3d          Modo de visualizacion (default: 2d)")
        print("  --speed N             Velocidad de reproduccion (default: 1.0)")
        print("  --trails N            Longitud de estelas en frames (default: 10)")
        print("  --color-mode MODE     Modo de coloracion (class|direction|speed|pattern)")
        print("  --export PATH         Exportar a video en lugar de mostrar")
        print("  --export-frames DIR   Exportar frames individuales")
        sys.exit(1)

    # Argumentos
    tracks_path = sys.argv[1]

    mode = '2d'
    if '--mode' in sys.argv:
        mode = sys.argv[sys.argv.index('--mode') + 1]

    speed = 1.0
    if '--speed' in sys.argv:
        speed = float(sys.argv[sys.argv.index('--speed') + 1])

    trail_length = 10
    if '--trails' in sys.argv:
        trail_length = int(sys.argv[sys.argv.index('--trails') + 1])

    color_mode = 'class'
    if '--color-mode' in sys.argv:
        color_mode = sys.argv[sys.argv.index('--color-mode') + 1]

    export_path = None
    if '--export' in sys.argv:
        export_path = sys.argv[sys.argv.index('--export') + 1]

    export_frames_dir = None
    if '--export-frames' in sys.argv:
        export_frames_dir = sys.argv[sys.argv.index('--export-frames') + 1]

    # Cargar trayectorias
    with open(tracks_path, 'r') as f:
        trajectories = json.load(f)

    # Crear manager
    manager = TrajectoryManager(trajectories, color_mode=color_mode)

    # Crear animator
    animator = TrajectoryAnimator(
        manager,
        mode=mode,
        trail_length=trail_length,
        show_ids=False
    )

    # Ejecutar
    if export_frames_dir:
        animator.export_frames(export_frames_dir, fps=30, show_trails=True)
    elif export_path:
        animator.export_video(export_path, fps=30, show_trails=True, show_full_trajectories=False)
    else:
        animator.animate(fps=30, speed=speed, show_trails=True, show_full_trajectories=False)
