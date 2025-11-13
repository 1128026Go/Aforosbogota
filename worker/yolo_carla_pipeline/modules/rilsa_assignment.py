"""
Módulo de Asignación de Códigos RILSA a Trayectorias
=====================================================

Asigna automáticamente códigos RILSA (1-8, 9(1-4), 10(1-4)) a trayectorias
vehiculares basándose en análisis geométrico de entrada y salida.

ORIENTACIÓN DE LA INTERSECCIÓN
--------------------------------
Por defecto, el sistema asume que el Norte está "arriba" en la imagen (90° en
coordenadas de píxel). Si tu intersección tiene una orientación diferente,
usa el parámetro 'rotacion_grados' para corregir.

Ejemplo visual:

    Sin rotación (rotacion_grados=0):          Con rotación (rotacion_grados=45):

          N (arriba)                                  NE (arriba)
          |                                            |
    O --- + --- E                                NO --- + --- NE
          |                                            |
          S (abajo)                                   SO (abajo)

Uso:
    # Intersección con Norte hacia arriba en la imagen
    config = crear_configuracion_simple(500, 500, rotacion_grados=0)

    # Intersección con Norte hacia noreste (45°) en la imagen
    config = crear_configuracion_simple(500, 500, rotacion_grados=45)

    # Intersección con Norte hacia la derecha en la imagen
    config = crear_configuracion_simple(500, 500, rotacion_grados=90)

Cómo determinar rotacion_grados:
    1. Identifica el Norte geográfico real en Google Maps
    2. Mide el ángulo en la imagen del video
    3. Si Norte está hacia arriba → 0°
       Si Norte está hacia derecha → 90°
       Si Norte está hacia abajo → 180°
       Si Norte está hacia izquierda → 270° o -90°

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AccesoRILSA(Enum):
    """Accesos cardinales de la intersección"""
    NORTE = "N"
    SUR = "S"
    OESTE = "O"
    ESTE = "E"
    DESCONOCIDO = "?"


@dataclass
class ZonaAcceso:
    """Define una zona de acceso de la intersección"""
    nombre: str
    acceso: AccesoRILSA
    poligono: List[Tuple[float, float]]  # Coordenadas del polígono
    angulo_entrada: float  # Ángulo típico de entrada en grados (0-360)
    angulo_salida: float   # Ángulo típico de salida en grados


@dataclass
class ConfiguracionInterseccion:
    """Configuración de la intersección para asignación RILSA"""
    centro: Tuple[float, float]  # Centro de la intersección (x, y)
    zonas_acceso: List[ZonaAcceso]
    radio_interior: float = 100.0  # Radio para detectar U-turns
    umbral_cambio_direccion: float = 30.0  # Grados para detectar giros
    rotacion_grados: float = 0.0  # Rotación de la intersección en grados (0 = Norte arriba)
    mapeo_manual: Optional[Dict[str, AccesoRILSA]] = None  # Mapeo manual de zonas a accesos


class AsignadorRILSA:
    """
    Asigna códigos RILSA a trayectorias basándose en geometría.

    Análisis:
    1. Determina acceso de entrada (N, S, O, E)
    2. Determina acceso de salida (N, S, O, E)
    3. Calcula ángulo de giro
    4. Asigna código RILSA correspondiente
    """

    def __init__(self, config: ConfiguracionInterseccion):
        """
        Args:
            config: Configuración de la intersección
        """
        self.config = config
        self.mapeo_rilsa = self._construir_mapeo_rilsa()

    def _construir_mapeo_rilsa(self) -> Dict[Tuple[str, str], str]:
        """
        Construye el mapeo completo origen-destino -> código RILSA.

        Returns:
            Dict con (origen, destino) -> código_rilsa
        """
        mapeo = {}

        # Directos (1-4)
        mapeo[('N', 'S')] = '1'   # Norte → Sur
        mapeo[('S', 'N')] = '2'   # Sur → Norte
        mapeo[('O', 'E')] = '3'   # Oeste → Este
        mapeo[('E', 'O')] = '4'   # Este → Oeste

        # Izquierdas (5-8)
        mapeo[('N', 'E')] = '5'   # Norte → Este
        mapeo[('S', 'O')] = '6'   # Sur → Oeste
        mapeo[('O', 'N')] = '7'   # Oeste → Norte
        mapeo[('E', 'S')] = '8'   # Este → Sur

        # Derechas (9 con índice) - representadas como 91-94
        mapeo[('N', 'O')] = '91'  # Norte → Oeste = 9(1)
        mapeo[('S', 'E')] = '92'  # Sur → Este = 9(2)
        mapeo[('O', 'S')] = '93'  # Oeste → Sur = 9(3)
        mapeo[('E', 'N')] = '94'  # Este → Norte = 9(4)

        # U-turns (10 con índice) - representadas como 101-104
        mapeo[('N', 'N')] = '101' # Giro en U en Norte = 10(1)
        mapeo[('S', 'S')] = '102' # Giro en U en Sur = 10(2)
        mapeo[('O', 'O')] = '103' # Giro en U en Oeste = 10(3)
        mapeo[('E', 'E')] = '104' # Giro en U en Este = 10(4)

        return mapeo

    def determinar_acceso(self, punto: Tuple[float, float],
                         es_entrada: bool = True) -> AccesoRILSA:
        """
        Determina a qué acceso pertenece un punto.

        MÉTODO PRINCIPAL: Busca primero en zonas definidas manualmente.
        MÉTODO SECUNDARIO: Si no hay zonas, usa ángulos geométricos.

        Args:
            punto: Coordenadas (x, y)
            es_entrada: True si es punto de entrada, False si es salida

        Returns:
            Acceso cardinal (N, S, O, E)
        """
        x, y = punto

        # MÉTODO 1 (RECOMENDADO): Verificar si el punto está dentro de alguna zona definida
        for zona in self.config.zonas_acceso:
            if self._punto_en_poligono(punto, zona.poligono):
                return zona.acceso

        # MÉTODO 2 (FALLBACK): Usar ángulos geométricos si no hay zonas definidas
        # NOTA: Este método puede desubicarse si la intersección no está perfectamente alineada
        cx, cy = self.config.centro

        # Calcular ángulo desde el centro
        # IMPORTANTE: En coordenadas de imagen, Y+ es ABAJO, invertimos dy para que Norte sea arriba
        dx = x - cx
        dy = -(y - cy)  # Invertir Y para que positivo sea ARRIBA
        angulo = np.degrees(np.arctan2(dy, dx))

        # Normalizar a 0-360
        if angulo < 0:
            angulo += 360

        # Aplicar rotación de la intersección (si se especificó)
        angulo_corregido = (angulo - self.config.rotacion_grados) % 360

        # Determinar acceso basándose en ángulo corregido
        # Con dy invertido: 0°=Este, 90°=Norte, 180°=Oeste, 270°=Sur
        if 45 <= angulo_corregido < 135:
            return AccesoRILSA.NORTE  # 90° centrado
        elif 135 <= angulo_corregido < 225:
            return AccesoRILSA.OESTE  # 180° centrado (CORREGIDO)
        elif 225 <= angulo_corregido < 315:
            return AccesoRILSA.SUR    # 270° centrado (CORREGIDO)
        else:  # 315-45
            return AccesoRILSA.ESTE   # 0°/360° centrado

    def _punto_en_poligono(self, punto: Tuple[float, float],
                           poligono: List[Tuple[float, float]]) -> bool:
        """
        Verifica si un punto está dentro de un polígono (Ray casting algorithm).

        Args:
            punto: (x, y)
            poligono: Lista de vértices [(x1,y1), (x2,y2), ...]

        Returns:
            True si el punto está dentro del polígono
        """
        if not poligono or len(poligono) < 3:
            return False

        x, y = punto
        n = len(poligono)
        inside = False

        p1x, p1y = poligono[0]
        for i in range(1, n + 1):
            p2x, p2y = poligono[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def calcular_angulo_giro(self, puntos: List[Tuple[float, float]]) -> float:
        """
        Calcula el ángulo total de giro de una trayectoria.

        Args:
            puntos: Lista de puntos (x, y) de la trayectoria

        Returns:
            Ángulo de giro en grados (-180 a 180)
        """
        if len(puntos) < 3:
            return 0.0

        # Vectores de entrada y salida
        # Usar primeros y últimos N puntos para mejor estimación
        n_puntos = min(5, len(puntos) // 4)

        # Vector de entrada (promedio de primeros puntos)
        puntos_entrada = puntos[:n_puntos]
        dir_entrada = np.array(puntos_entrada[-1]) - np.array(puntos_entrada[0])
        angulo_entrada = np.degrees(np.arctan2(dir_entrada[1], dir_entrada[0]))

        # Vector de salida (promedio de últimos puntos)
        puntos_salida = puntos[-n_puntos:]
        dir_salida = np.array(puntos_salida[-1]) - np.array(puntos_salida[0])
        angulo_salida = np.degrees(np.arctan2(dir_salida[1], dir_salida[0]))

        # Calcular diferencia de ángulo
        diff = angulo_salida - angulo_entrada

        # Normalizar a -180 a 180
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        return diff

    def es_uturn(self, puntos: List[Tuple[float, float]],
                 origen: AccesoRILSA) -> bool:
        """
        Detecta si una trayectoria es un U-turn.

        Args:
            puntos: Trayectoria
            origen: Acceso de origen

        Returns:
            True si es U-turn
        """
        if len(puntos) < 5:
            return False

        # Un U-turn típicamente:
        # 1. No se aleja mucho del centro
        # 2. Gira aproximadamente 180°
        # 3. Termina en el mismo acceso

        angulo = abs(self.calcular_angulo_giro(puntos))

        # Verificar ángulo cercano a 180°
        es_giro_180 = 150 < angulo < 210

        # Verificar que no cruza la intersección (distancia máxima al centro)
        cx, cy = self.config.centro
        distancias = [np.sqrt((x - cx)**2 + (y - cy)**2) for x, y in puntos]
        dist_maxima = max(distancias)

        # Si se mantiene cerca del radio interior, probablemente es U-turn
        es_cerca_centro = dist_maxima < self.config.radio_interior * 2

        return es_giro_180 and es_cerca_centro

    def es_peaton(self, clase: str) -> bool:
        """Determina si una clase es peatonal"""
        clases_peatonales = {'person', 'peaton', 'pedestrian', 'peatones'}
        return clase.lower().strip() in clases_peatonales

    def asignar_codigo_rilsa(self, track: Dict) -> Tuple[str, str, str]:
        """
        Asigna código RILSA a una trayectoria (vehicular o peatonal).

        Args:
            track: Dict con información de track (debe tener 'trajectory')

        Returns:
            (codigo_rilsa, origen, destino)
        """
        # Extraer trayectoria
        if 'trajectory' not in track:
            logger.warning(f"Track {track.get('track_id', '?')} sin trayectoria")
            return ('?', '?', '?')

        trayectoria = track['trajectory']

        if len(trayectoria) < 2:
            logger.warning(f"Track {track.get('track_id', '?')} con trayectoria muy corta")
            return ('?', '?', '?')

        # Verificar si es peatón
        clase = track.get('class', track.get('cls', 'unknown'))
        es_peaton = self.es_peaton(clase)

        # Convertir a lista de tuplas si es necesario
        if isinstance(trayectoria[0], dict):
            puntos = [(p['x'], p['y']) for p in trayectoria]
        elif isinstance(trayectoria[0], (list, tuple)):
            puntos = [tuple(p[:2]) for p in trayectoria]
        else:
            puntos = trayectoria

        # Determinar acceso de entrada (primer 20% de puntos)
        n_inicio = max(1, len(puntos) // 5)
        punto_entrada = puntos[n_inicio // 2]
        origen = self.determinar_acceso(punto_entrada, es_entrada=True)

        # PEATONES: Asignar código especial basado en origen
        # Formato: P(1) para Norte, P(2) para Sur, P(3) para Oeste, P(4) para Este
        if es_peaton:
            # Mapeo de acceso a índice peatonal
            mapeo_peaton = {
                'N': 'P(1)',
                'S': 'P(2)',
                'O': 'P(3)',
                'E': 'P(4)'
            }

            codigo_peaton = mapeo_peaton.get(origen.value, 'P(?)')

            # Para peatones, también determinar destino para estadísticas
            n_final = max(1, len(puntos) // 5)
            punto_salida = puntos[-(n_final // 2)]
            destino = self.determinar_acceso(punto_salida, es_entrada=False)

            return (codigo_peaton, origen.value, destino.value)

        # VEHÍCULOS: Lógica RILSA estándar

        # Verificar si es U-turn primero
        if self.es_uturn(puntos, origen):
            destino = origen
            codigo = self.mapeo_rilsa.get((origen.value, destino.value), '?')
            return (codigo, origen.value, destino.value)

        # Determinar acceso de salida (último 20% de puntos)
        n_final = max(1, len(puntos) // 5)
        punto_salida = puntos[-(n_final // 2)]
        destino = self.determinar_acceso(punto_salida, es_entrada=False)

        # Buscar código RILSA en mapeo
        codigo = self.mapeo_rilsa.get((origen.value, destino.value), '?')

        if codigo == '?':
            logger.warning(f"No se encontró código RILSA para {origen.value}→{destino.value}")

        return (codigo, origen.value, destino.value)

    def procesar_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """
        Procesa una lista de tracks y asigna códigos RILSA a cada uno.

        Args:
            tracks: Lista de diccionarios de tracks

        Returns:
            Lista de tracks con campos agregados: movimiento_rilsa, origen, destino
        """
        tracks_procesados = []

        for track in tracks:
            track_copia = track.copy()

            codigo, origen, destino = self.asignar_codigo_rilsa(track)

            track_copia['movimiento_rilsa'] = codigo
            track_copia['origen'] = origen
            track_copia['destino'] = destino

            tracks_procesados.append(track_copia)

        return tracks_procesados


def crear_configuracion_desde_bbox(bbox_dict: Dict[str, List]) -> ConfiguracionInterseccion:
    """
    Crea configuración de intersección desde diccionario de zonas de entrada/salida.

    MÉTODO RECOMENDADO: Define manualmente las zonas donde aparecen los vehículos
    de cada acceso (N, S, O, E) para asignación precisa de códigos RILSA.

    Args:
        bbox_dict: Dict con zonas definidas, ej:
            {
                'norte': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # Polígono del acceso Norte
                'sur': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],    # Polígono del acceso Sur
                'oeste': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # Polígono del acceso Oeste
                'este': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]    # Polígono del acceso Este
            }

    Returns:
        ConfiguracionInterseccion con zonas definidas manualmente
    """
    # Calcular centro aproximado de todas las zonas
    todos_puntos = []
    for zona_puntos in bbox_dict.values():
        todos_puntos.extend(zona_puntos)

    if not todos_puntos:
        # Default al origen si no hay zonas
        centro = (0, 0)
    else:
        xs = [p[0] for p in todos_puntos]
        ys = [p[1] for p in todos_puntos]
        centro = (np.mean(xs), np.mean(ys))

    # Crear zonas de acceso
    zonas = []

    # Mapeo de nombres de zonas a accesos
    mapeo_zonas = {
        'norte': AccesoRILSA.NORTE,
        'n': AccesoRILSA.NORTE,
        'sur': AccesoRILSA.SUR,
        's': AccesoRILSA.SUR,
        'oeste': AccesoRILSA.OESTE,
        'o': AccesoRILSA.OESTE,
        'este': AccesoRILSA.ESTE,
        'e': AccesoRILSA.ESTE
    }

    for nombre_zona, puntos in bbox_dict.items():
        # Detectar acceso del nombre
        acceso = AccesoRILSA.DESCONOCIDO
        nombre_lower = nombre_zona.lower().strip()

        # Buscar coincidencia exacta primero
        if nombre_lower in mapeo_zonas:
            acceso = mapeo_zonas[nombre_lower]
        else:
            # Buscar coincidencia parcial
            for key, valor in mapeo_zonas.items():
                if key in nombre_lower:
                    acceso = valor
                    break

        if acceso != AccesoRILSA.DESCONOCIDO and puntos:
            zona = ZonaAcceso(
                nombre=nombre_zona,
                acceso=acceso,
                poligono=[(p[0], p[1]) for p in puntos],
                angulo_entrada=0.0,  # Se puede calcular si es necesario
                angulo_salida=0.0
            )
            zonas.append(zona)

    return ConfiguracionInterseccion(
        centro=centro,
        zonas_acceso=zonas,
        radio_interior=100.0
    )


def crear_configuracion_simple(centro_x: float, centro_y: float,
                               tamano: float = 200,
                               rotacion_grados: float = 0.0) -> ConfiguracionInterseccion:
    """
    Crea una configuración simple de intersección cuadrada.

    Args:
        centro_x: Coordenada X del centro
        centro_y: Coordenada Y del centro
        tamano: Tamaño de la intersección
        rotacion_grados: Rotación de la intersección en grados (0 = Norte arriba en imagen)
                        Ejemplo: Si el Norte geográfico está a 45° en el video, usar 45

    Returns:
        ConfiguracionInterseccion básica
    """
    half = tamano / 2

    # Crear zonas básicas en cruz
    zonas = [
        ZonaAcceso(
            nombre="Norte",
            acceso=AccesoRILSA.NORTE,
            poligono=[
                (centro_x - half, centro_y - tamano),
                (centro_x + half, centro_y - tamano),
                (centro_x + half, centro_y - half),
                (centro_x - half, centro_y - half)
            ],
            angulo_entrada=270,
            angulo_salida=90
        ),
        ZonaAcceso(
            nombre="Sur",
            acceso=AccesoRILSA.SUR,
            poligono=[
                (centro_x - half, centro_y + half),
                (centro_x + half, centro_y + half),
                (centro_x + half, centro_y + tamano),
                (centro_x - half, centro_y + tamano)
            ],
            angulo_entrada=90,
            angulo_salida=270
        ),
        ZonaAcceso(
            nombre="Oeste",
            acceso=AccesoRILSA.OESTE,
            poligono=[
                (centro_x - tamano, centro_y - half),
                (centro_x - half, centro_y - half),
                (centro_x - half, centro_y + half),
                (centro_x - tamano, centro_y + half)
            ],
            angulo_entrada=180,
            angulo_salida=0
        ),
        ZonaAcceso(
            nombre="Este",
            acceso=AccesoRILSA.ESTE,
            poligono=[
                (centro_x + half, centro_y - half),
                (centro_x + tamano, centro_y - half),
                (centro_x + tamano, centro_y + half),
                (centro_x + half, centro_y + half)
            ],
            angulo_entrada=0,
            angulo_salida=180
        )
    ]

    return ConfiguracionInterseccion(
        centro=(centro_x, centro_y),
        zonas_acceso=zonas,
        radio_interior=tamano * 0.6,
        rotacion_grados=rotacion_grados
    )


if __name__ == "__main__":
    # Ejemplo de uso
    print("Módulo de Asignación RILSA")
    print("=" * 80)
    print("\nUso:")
    print("  from rilsa_assignment import AsignadorRILSA, crear_configuracion_simple")
    print("  ")
    print("  # Crear configuración")
    print("  config = crear_configuracion_simple(centro_x=500, centro_y=500)")
    print("  ")
    print("  # Crear asignador")
    print("  asignador = AsignadorRILSA(config)")
    print("  ")
    print("  # Procesar tracks")
    print("  tracks_con_rilsa = asignador.procesar_tracks(tracks)")
