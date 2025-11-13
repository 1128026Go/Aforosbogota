"""
Generador de Informe PDF RILSA con Screenshots por Movimiento
=============================================================

Genera un PDF profesional con:
- Una página por cada movimiento RILSA (20 total)
- Estadísticas del movimiento
- Screenshot de trayectorias del movimiento
- Datos tabulares

Uso:
    python generar_informe_pdf_rilsa.py \
        --tracks tracks_rilsa.json \
        --csv volumenes_15min.csv \
        --output informe_rilsa.pdf

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeneradorInformePDFRILSA:
    """Generador de informes PDF con visualizaciones por movimiento RILSA"""

    # Definición de 20 movimientos RILSA
    MOVIMIENTOS_RILSA = {
        # Directos (4)
        '1': {'origen': 'N', 'destino': 'S', 'tipo': 'Directo', 'desc': 'Norte → Sur'},
        '2': {'origen': 'S', 'destino': 'N', 'tipo': 'Directo', 'desc': 'Sur → Norte'},
        '3': {'origen': 'O', 'destino': 'E', 'tipo': 'Directo', 'desc': 'Oeste → Este'},
        '4': {'origen': 'E', 'destino': 'O', 'tipo': 'Directo', 'desc': 'Este → Oeste'},

        # Izquierdas (4)
        '5': {'origen': 'N', 'destino': 'E', 'tipo': 'Izquierda', 'desc': 'Norte → Este'},
        '6': {'origen': 'S', 'destino': 'O', 'tipo': 'Izquierda', 'desc': 'Sur → Oeste'},
        '7': {'origen': 'O', 'destino': 'N', 'tipo': 'Izquierda', 'desc': 'Oeste → Norte'},
        '8': {'origen': 'E', 'destino': 'S', 'tipo': 'Izquierda', 'desc': 'Este → Sur'},

        # Derechas (4) - códigos 91-94
        '91': {'origen': 'N', 'destino': 'O', 'tipo': 'Derecha', 'desc': 'Norte → Oeste (9(1))'},
        '92': {'origen': 'S', 'destino': 'E', 'tipo': 'Derecha', 'desc': 'Sur → Este (9(2))'},
        '93': {'origen': 'O', 'destino': 'S', 'tipo': 'Derecha', 'desc': 'Oeste → Sur (9(3))'},
        '94': {'origen': 'E', 'destino': 'N', 'tipo': 'Derecha', 'desc': 'Este → Norte (9(4))'},

        # U-turns (4) - códigos 101-104
        '101': {'origen': 'N', 'destino': 'N', 'tipo': 'U-turn', 'desc': 'Retorno Norte (10(1))'},
        '102': {'origen': 'S', 'destino': 'S', 'tipo': 'U-turn', 'desc': 'Retorno Sur (10(2))'},
        '103': {'origen': 'O', 'destino': 'O', 'tipo': 'U-turn', 'desc': 'Retorno Oeste (10(3))'},
        '104': {'origen': 'E', 'destino': 'E', 'tipo': 'U-turn', 'desc': 'Retorno Este (10(4))'},

        # Peatonales (4)
        'P(1)': {'origen': 'N', 'destino': '-', 'tipo': 'Peatonal', 'desc': 'Peatones desde Norte'},
        'P(2)': {'origen': 'S', 'destino': '-', 'tipo': 'Peatonal', 'desc': 'Peatones desde Sur'},
        'P(3)': {'origen': 'O', 'destino': '-', 'tipo': 'Peatonal', 'desc': 'Peatones desde Oeste'},
        'P(4)': {'origen': 'E', 'destino': '-', 'tipo': 'Peatonal', 'desc': 'Peatones desde Este'},
    }

    def __init__(self):
        self.tracks = []
        self.df_volumenes = None
        self.fig_size = (11, 8.5)  # Tamaño carta

    def cargar_tracks(self, archivo_tracks: str):
        """Carga tracks desde JSON"""
        logger.info(f"Cargando tracks desde {archivo_tracks}...")

        with open(archivo_tracks, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            self.tracks = data
        elif isinstance(data, dict) and 'tracks' in data:
            self.tracks = data['tracks']
        else:
            raise ValueError("Formato de tracks JSON no reconocido")

        logger.info(f"✓ {len(self.tracks)} tracks cargados")

    def cargar_volumenes(self, archivo_csv: str):
        """Carga datos de volumenes desde CSV"""
        logger.info(f"Cargando volumenes desde {archivo_csv}...")

        self.df_volumenes = pd.read_csv(archivo_csv)

        logger.info(f"✓ {len(self.df_volumenes)} registros cargados")

    def filtrar_tracks_por_movimiento(self, codigo_rilsa: str) -> List[Dict]:
        """Filtra tracks que pertenecen a un movimiento RILSA específico"""

        tracks_filtrados = []

        for track in self.tracks:
            # Verificar si el track tiene código RILSA asignado
            if 'movimiento_rilsa' in track:
                if str(track['movimiento_rilsa']) == str(codigo_rilsa):
                    tracks_filtrados.append(track)
            # Si no tiene RILSA, intentar inferir por origen/destino
            elif 'origen' in track and 'destino' in track:
                mov_info = self.MOVIMIENTOS_RILSA.get(codigo_rilsa)
                if mov_info:
                    if (track.get('origen') == mov_info['origen'] and
                        track.get('destino') == mov_info['destino']):
                        tracks_filtrados.append(track)

        return tracks_filtrados

    def obtener_estadisticas_movimiento(self, codigo_rilsa: str) -> Dict:
        """Obtiene estadísticas de un movimiento desde el CSV"""

        if self.df_volumenes is None:
            return {}

        # Filtrar por movimiento
        df_mov = self.df_volumenes[
            self.df_volumenes['movimiento_rilsa'].astype(str) == str(codigo_rilsa)
        ]

        if len(df_mov) == 0:
            return {
                'total_conteo': 0,
                'clases': {},
                'intervalos': 0
            }

        stats = {
            'total_conteo': int(df_mov['conteo'].sum()),
            'clases': df_mov.groupby('clase')['conteo'].sum().to_dict(),
            'intervalos': len(df_mov['timestamp_inicio'].unique()) if 'timestamp_inicio' in df_mov.columns else 0
        }

        return stats

    def visualizar_trayectorias_movimiento(self, codigo_rilsa: str, ax: plt.Axes):
        """Dibuja trayectorias de un movimiento específico en un axes"""

        # Filtrar tracks
        tracks_mov = self.filtrar_tracks_por_movimiento(codigo_rilsa)

        if len(tracks_mov) == 0:
            # No hay tracks, dibujar mensaje
            ax.text(0.5, 0.5, 'No hay trayectorias\ndisponibles',
                   ha='center', va='center', fontsize=16, color='gray',
                   transform=ax.transAxes)
            ax.axis('off')
            return

        # Encontrar bounds
        all_x, all_y = [], []
        for track in tracks_mov:
            positions = track.get('positions', [])
            if len(positions) > 0:
                xs = [p[0] if isinstance(p, (list, tuple)) else p.get('x', 0) for p in positions]
                ys = [p[1] if isinstance(p, (list, tuple)) else p.get('y', 0) for p in positions]
                all_x.extend(xs)
                all_y.extend(ys)

        if not all_x:
            ax.text(0.5, 0.5, 'Datos de posición\nno disponibles',
                   ha='center', va='center', fontsize=16, color='gray',
                   transform=ax.transAxes)
            ax.axis('off')
            return

        # Configurar límites con margen
        margin = 50
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

        # Dibujar grid suave
        ax.grid(True, alpha=0.2, linestyle='--')

        # Dibujar trayectorias
        colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(tracks_mov))))

        for idx, track in enumerate(tracks_mov[:100]):  # Limitar a 100 para no saturar
            positions = track.get('positions', [])

            if len(positions) < 2:
                continue

            # Extraer coordenadas
            xs = [p[0] if isinstance(p, (list, tuple)) else p.get('x', 0) for p in positions]
            ys = [p[1] if isinstance(p, (list, tuple)) else p.get('y', 0) for p in positions]

            # Color según clase
            clase = track.get('clase', 'unknown')
            color_map = {
                'car': '#3498db',
                'truck': '#e74c3c',
                'bus': '#f39c12',
                'motorcycle': '#9b59b6',
                'bicycle': '#27ae60',
                'person': '#1abc9c'
            }
            color = color_map.get(clase, colors[idx % len(colors)])

            # Dibujar trayectoria
            ax.plot(xs, ys, color=color, alpha=0.6, linewidth=2)

            # Marcar inicio (círculo verde) y fin (círculo rojo)
            ax.plot(xs[0], ys[0], 'go', markersize=6, alpha=0.8)
            ax.plot(xs[-1], ys[-1], 'ro', markersize=6, alpha=0.8)

            # Flecha en dirección
            if len(xs) >= 10:
                mid_idx = len(xs) // 2
                dx = xs[mid_idx + 5] - xs[mid_idx]
                dy = ys[mid_idx + 5] - ys[mid_idx]
                ax.arrow(xs[mid_idx], ys[mid_idx], dx, dy,
                        head_width=20, head_length=15, fc=color, ec=color, alpha=0.7)

        # Etiquetas
        ax.set_xlabel('Coordenada X (píxeles)', fontsize=10)
        ax.set_ylabel('Coordenada Y (píxeles)', fontsize=10)

        # Leyenda con número de tracks
        legend_text = f'{len(tracks_mov)} trayectorias'
        if len(tracks_mov) > 100:
            legend_text += f' (mostrando 100)'
        ax.text(0.02, 0.98, legend_text,
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    def generar_pagina_movimiento(self, codigo_rilsa: str, ax_main: plt.Axes, ax_stats: plt.Axes):
        """Genera una página completa para un movimiento"""

        mov_info = self.MOVIMIENTOS_RILSA[codigo_rilsa]
        stats = self.obtener_estadisticas_movimiento(codigo_rilsa)

        # === Panel superior: Información del movimiento ===
        ax_stats.axis('off')

        # Título
        titulo = f"Movimiento {codigo_rilsa}: {mov_info['desc']}"
        ax_stats.text(0.5, 0.95, titulo,
                     ha='center', va='top', fontsize=18, fontweight='bold',
                     transform=ax_stats.transAxes)

        # Subtítulo con tipo
        tipo_color = {
            'Directo': '#3498db',
            'Izquierda': '#f39c12',
            'Derecha': '#9b59b6',
            'U-turn': '#e74c3c',
            'Peatonal': '#1abc9c'
        }
        color = tipo_color.get(mov_info['tipo'], 'black')

        ax_stats.text(0.5, 0.88, f"Tipo: {mov_info['tipo']}",
                     ha='center', va='top', fontsize=14,
                     color=color, fontweight='bold',
                     transform=ax_stats.transAxes)

        # Estadísticas
        y_pos = 0.75

        # Total
        ax_stats.text(0.1, y_pos, f"Total conteo:",
                     ha='left', va='top', fontsize=12, fontweight='bold',
                     transform=ax_stats.transAxes)
        ax_stats.text(0.9, y_pos, f"{stats.get('total_conteo', 0):,}",
                     ha='right', va='top', fontsize=12,
                     transform=ax_stats.transAxes)

        y_pos -= 0.15

        # Desglose por clase
        if stats.get('clases'):
            ax_stats.text(0.1, y_pos, "Desglose por clase:",
                         ha='left', va='top', fontsize=11, fontweight='bold',
                         transform=ax_stats.transAxes)
            y_pos -= 0.08

            for clase, conteo in sorted(stats['clases'].items(), key=lambda x: -x[1]):
                emoji_map = {
                    'car': '🚗', 'truck': '🚚', 'bus': '🚌',
                    'motorcycle': '🏍️', 'bicycle': '🚴', 'person': '🚶'
                }
                emoji = emoji_map.get(clase, '•')

                ax_stats.text(0.15, y_pos, f"{emoji} {clase.capitalize()}:",
                             ha='left', va='top', fontsize=10,
                             transform=ax_stats.transAxes)
                ax_stats.text(0.9, y_pos, f"{conteo:,}",
                             ha='right', va='top', fontsize=10,
                             transform=ax_stats.transAxes)
                y_pos -= 0.06

        # === Panel principal: Visualización de trayectorias ===
        self.visualizar_trayectorias_movimiento(codigo_rilsa, ax_main)

    def generar_pdf(self, archivo_salida: str):
        """Genera el PDF completo con todas las páginas"""

        logger.info(f"\nGenerando informe PDF: {archivo_salida}")

        with PdfPages(archivo_salida) as pdf:

            # === Página de portada ===
            fig = plt.figure(figsize=self.fig_size)
            ax = fig.add_subplot(111)
            ax.axis('off')

            # Título
            ax.text(0.5, 0.7, 'INFORME DE AFORO RILSA',
                   ha='center', va='center', fontsize=28, fontweight='bold')

            # Subtítulo
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M')
            ax.text(0.5, 0.6, f'Fecha de generación: {fecha}',
                   ha='center', va='center', fontsize=14)

            # Resumen
            if self.df_volumenes is not None:
                total_vehiculos = self.df_volumenes[
                    ~self.df_volumenes['movimiento_rilsa'].astype(str).str.startswith('P')
                ]['conteo'].sum()

                total_peatones = self.df_volumenes[
                    self.df_volumenes['movimiento_rilsa'].astype(str).str.startswith('P')
                ]['conteo'].sum() if 'P' in str(self.df_volumenes['movimiento_rilsa'].unique()) else 0

                ax.text(0.5, 0.4, f'Total vehículos: {total_vehiculos:,}',
                       ha='center', va='center', fontsize=16)
                ax.text(0.5, 0.35, f'Total peatones: {total_peatones:,}',
                       ha='center', va='center', fontsize=16)
                ax.text(0.5, 0.3, f'Trayectorias analizadas: {len(self.tracks):,}',
                       ha='center', va='center', fontsize=16)

            # Logo o marca
            ax.text(0.5, 0.1, '🚗 Sistema RILSA - 20 Movimientos 🚶',
                   ha='center', va='center', fontsize=14, style='italic')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # === Páginas individuales por movimiento ===
            logger.info("\nGenerando páginas por movimiento...")

            for idx, codigo_rilsa in enumerate(self.MOVIMIENTOS_RILSA.keys(), 1):
                logger.info(f"  [{idx}/20] Movimiento {codigo_rilsa}...")

                fig = plt.figure(figsize=self.fig_size)

                # Layout: Panel superior para stats, panel inferior para trayectorias
                gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.3)
                ax_stats = fig.add_subplot(gs[0])
                ax_main = fig.add_subplot(gs[1])

                # Generar contenido
                self.generar_pagina_movimiento(codigo_rilsa, ax_main, ax_stats)

                # Número de página
                fig.text(0.95, 0.02, f'Página {idx + 1}/21',
                        ha='right', va='bottom', fontsize=8, color='gray')

                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        logger.info(f"\n✓ PDF generado exitosamente: {archivo_salida}")


def main():
    parser = argparse.ArgumentParser(
        description='Genera informe PDF RILSA con screenshots por movimiento',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplo de uso:
    python generar_informe_pdf_rilsa.py \\
        --tracks ../output/Gx010322_tracks.json \\
        --csv volumenes_15min.csv \\
        --output informe_rilsa.pdf
        """
    )

    parser.add_argument('--tracks', required=True, help='Archivo JSON con tracks (con movimiento_rilsa asignado)')
    parser.add_argument('--csv', required=True, help='Archivo CSV con volumenes por movimiento')
    parser.add_argument('--output', default='informe_rilsa.pdf', help='Archivo PDF de salida')

    args = parser.parse_args()

    # Validar archivos
    if not Path(args.tracks).exists():
        logger.error(f"❌ Archivo de tracks no encontrado: {args.tracks}")
        return 1

    if not Path(args.csv).exists():
        logger.error(f"❌ Archivo CSV no encontrado: {args.csv}")
        return 1

    # Generar informe
    try:
        generador = GeneradorInformePDFRILSA()
        generador.cargar_tracks(args.tracks)
        generador.cargar_volumenes(args.csv)
        generador.generar_pdf(args.output)

        logger.info(f"\n{'='*70}")
        logger.info(f"✓ INFORME PDF GENERADO EXITOSAMENTE")
        logger.info(f"{'='*70}")
        logger.info(f"\n📄 Archivo: {args.output}")
        logger.info(f"📊 Páginas: 21 (portada + 20 movimientos RILSA)")
        logger.info(f"\nCada página incluye:")
        logger.info(f"  • Estadísticas del movimiento")
        logger.info(f"  • Screenshot de trayectorias")
        logger.info(f"  • Desglose por clase vehicular\n")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
