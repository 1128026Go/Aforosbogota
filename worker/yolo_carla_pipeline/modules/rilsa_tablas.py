"""
Generador de Tablas de Aforo RILSA
===================================

Genera tablas de conteo vehicular en formato RILSA a partir de tracks procesados.

Salidas:
- volumenes_15min_por_movimiento.csv
- volumenes_por_movimiento.csv
- resumen_por_acceso.csv
- resumen_por_tipo_movimiento.csv

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class GeneradorTablasRILSA:
    """
    Genera tablas de aforo en formato RILSA desde tracks procesados.
    """

    def __init__(self, fps: float = 30.0, fecha_base: Optional[datetime] = None):
        """
        Args:
            fps: Frames por segundo del video
            fecha_base: Fecha/hora inicial del aforo (default: ahora)
        """
        self.fps = fps
        self.fecha_base = fecha_base or datetime.now().replace(second=0, microsecond=0)

        # Definir clases vehiculares RILSA
        self.clases_vehiculares = {
            'car', 'auto', 'automovil', 'carro',
            'motorcycle', 'moto', 'motocicleta',
            'bus', 'autobus', 'buseta',
            'truck', 'camion',
            'bicycle', 'bike', 'bicicleta',
            'taxi',
            'van', 'camioneta'
        }

    def es_clase_vehicular(self, clase: str) -> bool:
        """Verifica si una clase es vehicular"""
        return clase.lower().strip() in self.clases_vehiculares

    def frame_a_timestamp(self, frame: int) -> datetime:
        """
        Convierte número de frame a timestamp.

        Args:
            frame: Número de frame

        Returns:
            Timestamp correspondiente
        """
        segundos = frame / self.fps
        return self.fecha_base + timedelta(seconds=segundos)

    def asignar_intervalo_15min(self, timestamp: datetime) -> datetime:
        """
        Asigna un timestamp al inicio de su intervalo de 15 minutos.

        Args:
            timestamp: Timestamp a asignar

        Returns:
            Timestamp del inicio del intervalo de 15 min
        """
        minuto_base = (timestamp.minute // 15) * 15
        return timestamp.replace(minute=minuto_base, second=0, microsecond=0)

    def determinar_periodo(self, timestamp: datetime) -> str:
        """
        Determina el periodo del día (mañana, tarde, noche).

        Args:
            timestamp: Timestamp

        Returns:
            'mañana', 'tarde' o 'noche'
        """
        hora = timestamp.hour

        if 6 <= hora < 12:
            return 'mañana'
        elif 12 <= hora < 19:
            return 'tarde'
        else:
            return 'noche'

    def procesar_tracks_a_dataframe(self, tracks: List[Dict]) -> pd.DataFrame:
        """
        Convierte lista de tracks con RILSA a DataFrame estructurado.

        Args:
            tracks: Lista de dicts con campos:
                    track_id, class, movimiento_rilsa, origen, destino,
                    first_frame, last_frame

        Returns:
            DataFrame con columnas RILSA estándar
        """
        registros = []

        for track in tracks:
            # Validar que tenga información RILSA
            if 'movimiento_rilsa' not in track:
                clase = track.get('class', track.get('cls', '?'))
                logger.warning(f"Track {track.get('track_id', '?')} (clase: {clase}) sin código RILSA - omitido")
                continue

            # Obtener clase
            clase = track.get('class', track.get('cls', 'unknown'))
            clase_lower = clase.lower().strip()

            # Verificar si es vehículo o peatón (ambos se procesan)
            es_vehicular = self.es_clase_vehicular(clase)
            es_peaton = clase_lower in ['person', 'peaton', 'pedestrian']

            # Descartar solo si NO es vehículo NI peatón
            if not es_vehicular and not es_peaton:
                logger.debug(f"Clase no reconocida filtrada: {clase}")
                continue

            # Obtener información del track
            track_id = track.get('track_id', 0)
            movimiento = track.get('movimiento_rilsa', '?')
            origen = track.get('origen', '?')
            destino = track.get('destino', '?')

            # Frame donde se detectó por primera vez
            frame = track.get('first_frame', track.get('frame', 0))

            # Convertir a timestamp
            timestamp = self.frame_a_timestamp(frame)
            timestamp_15min = self.asignar_intervalo_15min(timestamp)
            periodo = self.determinar_periodo(timestamp)

            registro = {
                'track_id': track_id,
                'timestamp_inicio': timestamp_15min,
                'timestamp_exacto': timestamp,
                'periodo': periodo,
                'ramal': origen,
                'movimiento_rilsa': movimiento,
                'clase': clase.lower(),
                'origen': origen,
                'destino': destino
            }

            registros.append(registro)

        # Crear DataFrame
        if not registros:
            logger.warning("No se generaron registros")
            return pd.DataFrame()

        df = pd.DataFrame(registros)

        # Estadísticas de lo procesado
        total = len(df)
        vehiculares = df[df['clase'].isin(self.clases_vehiculares)].shape[0]
        peatonales = total - vehiculares

        logger.info(f"Registros procesados: {total} total ({vehiculares} vehiculares, {peatonales} peatonales)")

        return df

    def generar_tabla_15min(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera tabla con conteos por intervalos de 15 minutos.

        Args:
            df: DataFrame con tracks procesados

        Returns:
            DataFrame agregado por intervalo de 15 min
        """
        if df.empty:
            return pd.DataFrame()

        # Agrupar por intervalo, acceso, movimiento y clase
        tabla_15min = df.groupby([
            'timestamp_inicio',
            'periodo',
            'ramal',
            'movimiento_rilsa',
            'clase'
        ]).size().reset_index(name='conteo')

        # Ordenar por timestamp
        tabla_15min = tabla_15min.sort_values('timestamp_inicio')

        return tabla_15min

    def generar_tabla_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera tabla con totales por movimiento (todo el periodo).

        Args:
            df: DataFrame con tracks procesados

        Returns:
            DataFrame con totales
        """
        if df.empty:
            return pd.DataFrame()

        # Agrupar por movimiento y clase
        tabla_total = df.groupby([
            'movimiento_rilsa',
            'origen',
            'destino',
            'clase'
        ]).size().reset_index(name='cantidad')

        # Agregar descripción
        tabla_total['descripcion'] = tabla_total.apply(
            lambda row: self._describir_movimiento(row['movimiento_rilsa']),
            axis=1
        )

        return tabla_total

    def generar_resumen_por_acceso(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera resumen de volumenes por acceso.

        Args:
            df: DataFrame con tracks procesados

        Returns:
            DataFrame con totales por acceso
        """
        if df.empty:
            return pd.DataFrame()

        # Total por acceso de origen
        resumen = df.groupby('origen').size().reset_index(name='total_vehiculos')

        # Agregar por tipo de movimiento
        for tipo in ['directo', 'izquierda', 'derecha', 'u_turn']:
            mask = df['movimiento_rilsa'].apply(lambda x: self._tipo_movimiento(x) == tipo)
            volumenes_tipo = df[mask].groupby('origen').size()
            resumen[f'total_{tipo}'] = resumen['origen'].map(volumenes_tipo).fillna(0).astype(int)

        return resumen

    def generar_resumen_por_tipo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera resumen de volumenes por tipo de movimiento.

        Args:
            df: DataFrame con tracks procesados

        Returns:
            DataFrame con totales por tipo
        """
        if df.empty:
            return pd.DataFrame()

        # Agregar columna de tipo
        df_con_tipo = df.copy()
        df_con_tipo['tipo_movimiento'] = df_con_tipo['movimiento_rilsa'].apply(self._tipo_movimiento)

        # Agrupar
        resumen = df_con_tipo.groupby('tipo_movimiento').agg({
            'track_id': 'count',
            'clase': lambda x: x.value_counts().to_dict()
        }).reset_index()

        resumen.columns = ['tipo_movimiento', 'total_vehiculos', 'distribucion_clases']

        return resumen

    def _tipo_movimiento(self, codigo: str) -> str:
        """Determina el tipo de movimiento desde el código RILSA"""
        codigo_str = str(codigo).strip()

        if codigo_str in ['1', '2', '3', '4']:
            return 'directo'
        elif codigo_str in ['5', '6', '7', '8']:
            return 'izquierda'
        elif codigo_str.startswith('9('):
            return 'derecha'
        elif codigo_str.startswith('10('):
            return 'u_turn'
        else:
            return 'desconocido'

    def _describir_movimiento(self, codigo: str) -> str:
        """Genera descripción textual del movimiento"""
        descripciones = {
            '1': 'Norte → Sur (directo)',
            '2': 'Sur → Norte (directo)',
            '3': 'Oeste → Este (directo)',
            '4': 'Este → Oeste (directo)',
            '5': 'Norte → Este (izquierda)',
            '6': 'Sur → Oeste (izquierda)',
            '7': 'Oeste → Norte (izquierda)',
            '8': 'Este → Sur (izquierda)',
            '9(1)': 'Norte → Oeste (derecha)',
            '9(2)': 'Sur → Este (derecha)',
            '9(3)': 'Oeste → Sur (derecha)',
            '9(4)': 'Este → Norte (derecha)',
            '10(1)': 'Retorno en Norte',
            '10(2)': 'Retorno en Sur',
            '10(3)': 'Retorno en Oeste',
            '10(4)': 'Retorno en Este'
        }
        return descripciones.get(str(codigo).strip(), 'Movimiento desconocido')

    def exportar_tablas(self, tracks: List[Dict], directorio_salida: str):
        """
        Genera y exporta todas las tablas RILSA.

        Args:
            tracks: Lista de tracks con códigos RILSA
            directorio_salida: Directorio donde guardar los CSV
        """
        import os

        os.makedirs(directorio_salida, exist_ok=True)

        # Convertir tracks a DataFrame
        logger.info("Procesando tracks a DataFrame...")
        df = self.procesar_tracks_a_dataframe(tracks)

        if df.empty:
            logger.warning("No hay datos para exportar")
            return

        logger.info(f"Total vehículos procesados: {len(df)}")

        # 1. Tabla de 15 minutos
        logger.info("Generando tabla de 15 minutos...")
        tabla_15min = self.generar_tabla_15min(df)
        archivo_15min = os.path.join(directorio_salida, 'volumenes_15min_por_movimiento.csv')
        tabla_15min.to_csv(archivo_15min, index=False, encoding='utf-8-sig')
        logger.info(f"✓ {archivo_15min}")

        # 2. Tabla total
        logger.info("Generando tabla de totales...")
        tabla_total = self.generar_tabla_total(df)
        archivo_total = os.path.join(directorio_salida, 'volumenes_por_movimiento.csv')
        tabla_total.to_csv(archivo_total, index=False, encoding='utf-8-sig')
        logger.info(f"✓ {archivo_total}")

        # 3. Resumen por acceso
        logger.info("Generando resumen por acceso...")
        resumen_acceso = self.generar_resumen_por_acceso(df)
        archivo_acceso = os.path.join(directorio_salida, 'resumen_por_acceso.csv')
        resumen_acceso.to_csv(archivo_acceso, index=False, encoding='utf-8-sig')
        logger.info(f"✓ {archivo_acceso}")

        # 4. Resumen por tipo
        logger.info("Generando resumen por tipo de movimiento...")
        resumen_tipo = self.generar_resumen_por_tipo(df)
        archivo_tipo = os.path.join(directorio_salida, 'resumen_por_tipo_movimiento.csv')
        resumen_tipo.to_csv(archivo_tipo, index=False, encoding='utf-8-sig')
        logger.info(f"✓ {archivo_tipo}")

        # Estadísticas generales
        logger.info("\n" + "=" * 80)
        logger.info("ESTADÍSTICAS GENERALES")
        logger.info("=" * 80)

        # Separar vehículos y peatones
        df_vehicular = df[df['clase'].isin(self.clases_vehiculares)]
        df_peatonal = df[~df['clase'].isin(self.clases_vehiculares)]

        logger.info(f"Total registros: {len(df)}")
        logger.info(f"  - Vehiculares: {len(df_vehicular)}")
        logger.info(f"  - Peatonales: {len(df_peatonal)}")
        logger.info(f"Intervalos de 15 min: {len(tabla_15min['timestamp_inicio'].unique())}")
        logger.info(f"Movimientos RILSA únicos: {len(df['movimiento_rilsa'].unique())}")
        logger.info(f"Accesos activos: {', '.join(sorted(df['origen'].unique()))}")

        if len(df_vehicular) > 0:
            logger.info("\nDistribución vehicular por tipo de movimiento:")
            for tipo, count in df_vehicular.groupby(df_vehicular['movimiento_rilsa'].apply(self._tipo_movimiento)).size().items():
                logger.info(f"  {tipo}: {count} vehículos")

        if len(df_peatonal) > 0:
            logger.info("\nDistribución peatonal por acceso:")
            for acceso, count in df_peatonal.groupby('origen').size().items():
                logger.info(f"  Acceso {acceso}: {count} peatones")

        logger.info("=" * 80)


if __name__ == "__main__":
    # Ejemplo de uso
    print("Generador de Tablas RILSA")
    print("=" * 80)
    print("\nUso:")
    print("  from rilsa_tablas import GeneradorTablasRILSA")
    print("  ")
    print("  # Crear generador")
    print("  generador = GeneradorTablasRILSA(fps=30.0, fecha_base=datetime(2025, 8, 13, 6, 0))")
    print("  ")
    print("  # Exportar tablas")
    print("  generador.exportar_tablas(tracks_con_rilsa, 'entregables/')")
