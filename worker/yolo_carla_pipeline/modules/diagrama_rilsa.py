"""
Generador de Diagramas RILSA
=============================

Genera diagramas visuales de intersecciones según nomenclatura RILSA
con volumenes de tráfico por movimiento.

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class DiagramaRILSA:
    """Generador de diagramas RILSA para intersecciones"""

    def __init__(self, titulo: str = "Diagrama RILSA - Intersección"):
        """
        Inicializa el generador de diagramas.

        Args:
            titulo: Título del diagrama
        """
        self.titulo = titulo
        self.fig = None
        self.ax = None

    def crear_canvas(self, tamano: Tuple[int, int] = (14, 14)):
        """Crea el canvas para el diagrama"""
        self.fig, self.ax = plt.subplots(figsize=tamano)
        self.ax.set_aspect('equal')
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.axis('off')
        self.ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20)

    def dibujar_calles(self):
        """Dibuja las calles de la intersección"""
        # Calles horizontales (E-O)
        self.ax.add_patch(Rectangle((-10, -2), 20, 4, facecolor='#666666', edgecolor='white', linewidth=2))

        # Calles verticales (N-S)
        self.ax.add_patch(Rectangle((-2, -10), 4, 20, facecolor='#666666', edgecolor='white', linewidth=2))

        # Líneas de división de carriles
        self.ax.plot([-10, -2], [0, 0], 'w--', linewidth=1, alpha=0.5)
        self.ax.plot([2, 10], [0, 0], 'w--', linewidth=1, alpha=0.5)
        self.ax.plot([0, 0], [-10, -2], 'w--', linewidth=1, alpha=0.5)
        self.ax.plot([0, 0], [2, 10], 'w--', linewidth=1, alpha=0.5)

        # Etiquetas de accesos
        self.ax.text(0, 9, 'NORTE', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        self.ax.text(0, -9, 'SUR', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        self.ax.text(-9, 0, 'OESTE', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        self.ax.text(9, 0, 'ESTE', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

    def obtener_coordenadas_movimiento(self, codigo: str) -> Tuple[Tuple[float, float], Tuple[float, float], str]:
        """
        Obtiene coordenadas de inicio, fin y curvatura para un movimiento.

        Returns:
            (punto_inicio, punto_fin, tipo_curva)
        """
        movimientos_coords = {
            # Directos
            '1': ((0, 6), (0, -6), 'recto'),        # N→S
            '2': ((0, -6), (0, 6), 'recto'),        # S→N
            '3': ((-6, 0), (6, 0), 'recto'),        # O→E
            '4': ((6, 0), (-6, 0), 'recto'),        # E→O

            # Izquierdas
            '5': ((0, 6), (6, 0), 'izquierda'),     # N→E
            '6': ((0, -6), (-6, 0), 'izquierda'),   # S→O
            '7': ((-6, 0), (0, -6), 'izquierda'),   # O→S
            '8': ((6, 0), (0, 6), 'izquierda'),     # E→N

            # Derechas
            '9(1)': ((0, 6), (-6, 0), 'derecha'),   # N→O
            '9(2)': ((0, -6), (6, 0), 'derecha'),   # S→E
            '9(3)': ((-6, 0), (0, 6), 'derecha'),   # O→N
            '9(4)': ((6, 0), (0, -6), 'derecha'),   # E→S

            # U-turns
            '10(1)': ((1, 6), (-1, 6), 'u_turn'),   # Norte
            '10(2)': ((-1, -6), (1, -6), 'u_turn'), # Sur
            '10(3)': ((-6, -1), (-6, 1), 'u_turn'), # Oeste
            '10(4)': ((6, 1), (6, -1), 'u_turn'),   # Este
        }

        return movimientos_coords.get(codigo, ((0, 0), (0, 0), 'recto'))

    def dibujar_flecha_movimiento(self, codigo: str, volumen: int, color: str = 'blue'):
        """
        Dibuja una flecha representando un movimiento vehicular.

        Args:
            codigo: Código RILSA del movimiento
            volumen: Volumen de vehículos
            color: Color de la flecha
        """
        inicio, fin, tipo = self.obtener_coordenadas_movimiento(codigo)

        # Ajustar grosor según volumen (escala logarítmica para mejor visualización)
        grosor = 1 + np.log10(max(volumen, 1)) * 1.5

        if tipo == 'recto':
            arrow = FancyArrowPatch(
                inicio, fin,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                color=color,
                linewidth=grosor,
                alpha=0.7,
                zorder=5
            )
        elif tipo == 'izquierda':
            arrow = FancyArrowPatch(
                inicio, fin,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                color=color,
                linewidth=grosor,
                connectionstyle='arc3,rad=0.5',
                alpha=0.7,
                zorder=5
            )
        elif tipo == 'derecha':
            arrow = FancyArrowPatch(
                inicio, fin,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                color=color,
                linewidth=grosor,
                connectionstyle='arc3,rad=-0.5',
                alpha=0.7,
                zorder=5
            )
        elif tipo == 'u_turn':
            arrow = FancyArrowPatch(
                inicio, fin,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                color=color,
                linewidth=grosor,
                connectionstyle='arc3,rad=1.5',
                alpha=0.7,
                zorder=5
            )

        self.ax.add_patch(arrow)

        # Agregar etiqueta con volumen
        mid_x = (inicio[0] + fin[0]) / 2
        mid_y = (inicio[1] + fin[1]) / 2

        # Ajustar posición de etiqueta para mejor legibilidad
        offset_x, offset_y = 0, 0
        if tipo == 'izquierda':
            offset_x, offset_y = 0.8, 0.8
        elif tipo == 'derecha':
            offset_x, offset_y = -0.8, -0.8
        elif tipo == 'u_turn':
            if codigo in ['10(1)', '10(2)']:
                offset_x, offset_y = 0, 1.5
            else:
                offset_x, offset_y = 1.5, 0

        self.ax.text(
            mid_x + offset_x, mid_y + offset_y,
            f"{codigo}\n{volumen}",
            ha='center', va='center',
            fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.9),
            zorder=10
        )

    def procesar_dataframe(self, df: pd.DataFrame, columna_movimiento: str = 'movimiento_rilsa',
                           columna_volumen: str = 'conteo'):
        """
        Procesa un DataFrame y dibuja todos los movimientos.

        Args:
            df: DataFrame con datos de aforo
            columna_movimiento: Nombre de la columna con códigos RILSA
            columna_volumen: Nombre de la columna con volumenes
        """
        # Agrupar por movimiento y sumar volumenes
        volumenes = df.groupby(columna_movimiento)[columna_volumen].sum()

        # Colores para diferentes tipos de movimiento
        colores = {
            'directo': '#2196F3',       # Azul
            'izquierda': '#4CAF50',     # Verde
            'derecha': '#FF9800',       # Naranja
            'u_turn': '#9C27B0'         # Púrpura
        }

        for codigo, volumen in volumenes.items():
            codigo_str = str(codigo).strip()

            # Determinar tipo de movimiento
            if codigo_str in ['1', '2', '3', '4']:
                color = colores['directo']
            elif codigo_str in ['5', '6', '7', '8']:
                color = colores['izquierda']
            elif codigo_str.startswith('9('):
                color = colores['derecha']
            elif codigo_str.startswith('10('):
                color = colores['u_turn']
            else:
                color = '#757575'  # Gris para códigos desconocidos

            self.dibujar_flecha_movimiento(codigo_str, volumen, color)

    def agregar_leyenda(self):
        """Agrega leyenda de colores y tipos de movimiento"""
        legend_elements = [
            patches.Patch(color='#2196F3', label='Directos (1-4)'),
            patches.Patch(color='#4CAF50', label='Izquierdas (5-8)'),
            patches.Patch(color='#FF9800', label='Derechas (9)'),
            patches.Patch(color='#9C27B0', label='U-turns (10)')
        ]
        self.ax.legend(handles=legend_elements, loc='upper left',
                      bbox_to_anchor=(0.02, 0.98), fontsize=10)

    def agregar_resumen_volumenes(self, df: pd.DataFrame, columna_movimiento: str = 'movimiento_rilsa',
                                  columna_volumen: str = 'conteo'):
        """Agrega tabla resumen de volumenes totales por acceso"""
        if 'origen' in df.columns:
            totales = df.groupby('origen')[columna_volumen].sum()

            texto_resumen = "VOLUMENES POR ACCESO\n" + "="*25 + "\n"
            for acceso in ['N', 'S', 'O', 'E']:
                if acceso in totales:
                    texto_resumen += f"{acceso}: {totales[acceso]:,} veh\n"

            total_general = totales.sum()
            texto_resumen += "="*25 + "\n"
            texto_resumen += f"TOTAL: {total_general:,} veh"

            self.ax.text(
                0.98, 0.02, texto_resumen,
                transform=self.ax.transAxes,
                fontsize=9,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                family='monospace'
            )

    def dibujar_poligonos_acceso(
        self,
        accesses_config: Dict,
        escala: float = 0.1
    ):
        """
        Dibuja polígonos de entrada/salida de accesos con coordenadas

        Args:
            accesses_config: Configuración de accesos con polígonos
            escala: Factor de escala para convertir coordenadas reales a diagrama
        """
        from matplotlib.patches import Polygon

        colores = {
            'N': 'blue',
            'S': 'red',
            'E': 'green',
            'O': 'orange'
        }

        for cardinal, access in accesses_config.items():
            color = colores.get(cardinal, 'gray')

            # Polígono de entrada
            entry_poly = access.get("entry_polygon", [])
            if entry_poly:
                # Escalar coordenadas
                poly_scaled = [[p[0] * escala, p[1] * escala] for p in entry_poly]
                polygon = Polygon(
                    poly_scaled,
                    facecolor=color,
                    alpha=0.2,
                    edgecolor=color,
                    linewidth=2,
                    label=f"{cardinal} - Entrada"
                )
                self.ax.add_patch(polygon)

                # Añadir coordenadas de vértices
                for i, (x, y) in enumerate(poly_scaled):
                    self.ax.plot(x, y, 'ko', markersize=3)
                    self.ax.annotate(
                        f"({int(entry_poly[i][0])}, {int(entry_poly[i][1])})",
                        xy=(x, y),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=6,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)
                    )

            # Polígono de salida
            exit_poly = access.get("exit_polygon", [])
            if exit_poly:
                poly_scaled = [[p[0] * escala, p[1] * escala] for p in exit_poly]
                polygon = Polygon(
                    poly_scaled,
                    facecolor=color,
                    alpha=0.1,
                    edgecolor=color,
                    linewidth=2,
                    linestyle='--',
                    label=f"{cardinal} - Salida"
                )
                self.ax.add_patch(polygon)

    def calcular_angulo_movimiento(self, codigo: str) -> float:
        """
        Calcula el ángulo de un movimiento RILSA

        Returns:
            Ángulo en grados
        """
        # Mapeo de códigos a origen/destino
        codigo_to_movement = {
            '1': ('N', 'S'), '2': ('S', 'N'),
            '3': ('O', 'E'), '4': ('E', 'O'),
            '5': ('N', 'E'), '6': ('S', 'O'),
            '7': ('O', 'S'), '8': ('E', 'N'),
            '9(1)': ('N', 'O'), '9(2)': ('S', 'E'),
            '9(3)': ('O', 'N'), '9(4)': ('E', 'S'),
            '10(1)': ('N', 'N'), '10(2)': ('S', 'S'),
            '10(3)': ('O', 'O'), '10(4)': ('E', 'E')
        }

        movement = codigo_to_movement.get(str(codigo).strip())
        if not movement:
            return 0.0

        origin, dest = movement

        # Calcular ángulo basado en cardinales
        cardinal_angles = {"N": 0, "E": 90, "S": 180, "O": 270}
        angle_origin = cardinal_angles.get(origin, 0)
        angle_dest = cardinal_angles.get(dest, 0)

        # Calcular diferencia angular
        diff = (angle_dest - angle_origin) % 360

        return float(diff)

    def agregar_angulos_giros(self, df: pd.DataFrame, columna_movimiento: str = 'movimiento_rilsa'):
        """
        Añade indicadores de ángulos en los giros

        Args:
            df: DataFrame con movimientos
            columna_movimiento: Columna con códigos RILSA
        """
        from matplotlib.patches import Arc

        movimientos = df[columna_movimiento].unique()

        for codigo in movimientos:
            codigo_str = str(codigo).strip()

            # Solo para giros (no directos)
            if codigo_str in ['1', '2', '3', '4']:
                continue

            inicio, fin, tipo = self.obtener_coordenadas_movimiento(codigo_str)

            if tipo in ['izquierda', 'derecha', 'u_turn']:
                # Calcular ángulo
                angle = self.calcular_angulo_movimiento(codigo_str)

                # Dibujar arco de ángulo
                center = ((inicio[0] + fin[0]) / 2, (inicio[1] + fin[1]) / 2)
                radius = 1.5

                # Ángulo de inicio y fin para el arco
                if tipo == 'izquierda':
                    start_angle, end_angle = 0, 90
                elif tipo == 'derecha':
                    start_angle, end_angle = 270, 360
                else:  # u_turn
                    start_angle, end_angle = 0, 180

                arc = Arc(
                    center,
                    2 * radius, 2 * radius,
                    angle=0,
                    theta1=start_angle,
                    theta2=end_angle,
                    color='red',
                    linewidth=1.5,
                    linestyle='--',
                    alpha=0.6
                )
                self.ax.add_patch(arc)

                # Añadir texto de ángulo
                mid_angle = (start_angle + end_angle) / 2
                text_x = center[0] + radius * 1.3 * np.cos(np.radians(mid_angle))
                text_y = center[1] + radius * 1.3 * np.sin(np.radians(mid_angle))

                self.ax.text(
                    text_x, text_y,
                    f"{int(angle)}°",
                    fontsize=8,
                    color='red',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.6)
                )

    def agregar_tabla_resumen_completa(
        self,
        df: pd.DataFrame,
        rilsa_map: Optional[Dict] = None,
        columna_movimiento: str = 'movimiento_rilsa',
        columna_volumen: str = 'conteo'
    ):
        """
        Agrega tabla resumen completa con códigos, ángulos y coordenadas

        Args:
            df: DataFrame con datos
            rilsa_map: Mapa RILSA (opcional)
            columna_movimiento: Columna con códigos RILSA
            columna_volumen: Columna con volúmenes
        """
        # Preparar datos para la tabla
        volumenes = df.groupby(columna_movimiento)[columna_volumen].sum()

        table_data = [["Código", "Movimiento", "Tipo", "Volumen", "Ángulo"]]

        for codigo, volumen in sorted(volumenes.items(), key=lambda x: str(x[0])):
            codigo_str = str(codigo).strip()

            # Obtener tipo de movimiento
            _, _, tipo = self.obtener_coordenadas_movimiento(codigo_str)
            tipo_display = {
                'recto': 'Directo',
                'izquierda': 'Giro Izq.',
                'derecha': 'Giro Der.',
                'u_turn': 'U-turn'
            }.get(tipo, 'Desconocido')

            # Calcular ángulo
            angle = self.calcular_angulo_movimiento(codigo_str)

            # Obtener movimiento (origen→destino)
            inicio, fin, _ = self.obtener_coordenadas_movimiento(codigo_str)
            movimiento_str = f"({int(inicio[0])},{int(inicio[1])})→({int(fin[0])},{int(fin[1])})"

            table_data.append([
                f"M{codigo_str}",
                movimiento_str,
                tipo_display,
                f"{volumen}",
                f"{int(angle)}°" if angle > 0 else "N/A"
            ])

        # Crear tabla usando matplotlib
        table = self.ax.table(
            cellText=table_data,
            cellLoc='center',
            loc='right',
            bbox=[1.05, 0.3, 0.4, 0.6],
            colWidths=[0.15, 0.25, 0.2, 0.15, 0.15]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)

        # Estilo de header
        for i in range(5):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Alternar colores de filas
        for i in range(1, len(table_data)):
            color = '#f0f0f0' if i % 2 == 0 else 'white'
            for j in range(5):
                table[(i, j)].set_facecolor(color)

    def guardar(self, archivo: str, dpi: int = 300, formato: str = 'png'):
        """
        Guarda el diagrama en un archivo (PNG o SVG)

        Args:
            archivo: Ruta del archivo
            dpi: Resolución (solo para PNG)
            formato: 'png' o 'svg'
        """
        plt.tight_layout()

        if formato.lower() == 'svg':
            plt.savefig(archivo, format='svg', bbox_inches='tight')
        else:
            plt.savefig(archivo, dpi=dpi, bbox_inches='tight', format='png')

        print(f"[OK] Diagrama guardado: {archivo} ({formato.upper()})")

    def mostrar(self):
        """Muestra el diagrama en pantalla"""
        plt.tight_layout()
        plt.show()


def generar_diagrama_completo(
    archivo_csv: str,
    archivo_salida: str,
    titulo: str = "Diagrama RILSA - Intersección",
    mostrar: bool = False
):
    """
    Genera un diagrama RILSA completo a partir de un archivo CSV.

    Args:
        archivo_csv: Ruta al CSV con datos de aforo
        archivo_salida: Ruta donde guardar el diagrama
        titulo: Título del diagrama
        mostrar: Si True, muestra el diagrama en pantalla
    """
    # Leer datos
    df = pd.read_csv(archivo_csv)

    # Crear diagrama
    diagrama = DiagramaRILSA(titulo=titulo)
    diagrama.crear_canvas()
    diagrama.dibujar_calles()
    diagrama.procesar_dataframe(df)
    diagrama.agregar_leyenda()
    diagrama.agregar_resumen_volumenes(df)

    # Guardar
    diagrama.guardar(archivo_salida)

    # Mostrar si se solicita
    if mostrar:
        diagrama.mostrar()
    else:
        plt.close()


if __name__ == "__main__":
    print("Generador de Diagramas RILSA")
    print("=" * 80)
    print("\nUso:")
    print("  from diagrama_rilsa import generar_diagrama_completo")
    print("  ")
    print("  generar_diagrama_completo(")
    print("      archivo_csv='vehicular_normalizado.csv',")
    print("      archivo_salida='diagrama_rilsa.png',")
    print("      titulo='Diagrama RILSA - Intersección Principal'")
    print("  )")
