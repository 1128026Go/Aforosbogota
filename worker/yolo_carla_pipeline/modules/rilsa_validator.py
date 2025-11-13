"""
Módulo de Validación y Normalización RILSA
==========================================

Sistema completo para validar, normalizar y generar entregables de aforos
vehiculares y peatonales según nomenclatura RILSA.

Autor: Sistema de Validación RILSA
Fecha: 2025-11-09
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime
import json


class Acceso(Enum):
    """Accesos cardinales de la intersección"""
    NORTE = "N"
    SUR = "S"
    OESTE = "O"
    ESTE = "E"


@dataclass
class MovimientoRILSA:
    """Definición de movimiento según nomenclatura RILSA"""
    codigo: str
    origen: Acceso
    destino: Acceso
    tipo: str  # 'directo', 'izquierda', 'derecha', 'u_turn'
    descripcion: str

    def __str__(self):
        return f"{self.codigo}: {self.origen.value}→{self.destino.value} ({self.tipo})"


class ValidadorRILSA:
    """
    Validador y normalizador de aforos según nomenclatura RILSA.

    Nomenclatura RILSA:
    - Directos: 1 (N→S), 2 (S→N), 3 (O→E), 4 (E→O)
    - Izquierdas: 5 (N→E), 6 (S→O), 7 (O→S), 8 (E→N)
    - Derechas: 9(1) (N→O), 9(2) (S→E), 9(3) (O→N), 9(4) (E→S)
    - U-turns: 10(1) (Norte), 10(2) (Sur), 10(3) (Oeste), 10(4) (Este)
    - Peatonales: P(1) (Norte), P(2) (Sur), P(3) (Oeste), P(4) (Este)
    """

    def __init__(self, criterio_uturn: str = "separado"):
        """
        Inicializa el validador.

        Args:
            criterio_uturn: 'separado' o 'como_izquierda' según norma local
        """
        self.criterio_uturn = criterio_uturn
        self.movimientos_validos = self._definir_movimientos_rilsa()
        self.errores: List[Dict] = []
        self.advertencias: List[Dict] = []

    def _definir_movimientos_rilsa(self) -> Dict[str, MovimientoRILSA]:
        """Define todos los movimientos válidos según RILSA"""
        movimientos = {}

        # Movimientos directos
        movimientos['1'] = MovimientoRILSA('1', Acceso.NORTE, Acceso.SUR, 'directo', 'Norte → Sur')
        movimientos['2'] = MovimientoRILSA('2', Acceso.SUR, Acceso.NORTE, 'directo', 'Sur → Norte')
        movimientos['3'] = MovimientoRILSA('3', Acceso.OESTE, Acceso.ESTE, 'directo', 'Oeste → Este')
        movimientos['4'] = MovimientoRILSA('4', Acceso.ESTE, Acceso.OESTE, 'directo', 'Este → Oeste')

        # Giros a la izquierda
        movimientos['5'] = MovimientoRILSA('5', Acceso.NORTE, Acceso.ESTE, 'izquierda', 'Norte → Este (izq)')
        movimientos['6'] = MovimientoRILSA('6', Acceso.SUR, Acceso.OESTE, 'izquierda', 'Sur → Oeste (izq)')
        movimientos['7'] = MovimientoRILSA('7', Acceso.OESTE, Acceso.SUR, 'izquierda', 'Oeste → Sur (izq)')
        movimientos['8'] = MovimientoRILSA('8', Acceso.ESTE, Acceso.NORTE, 'izquierda', 'Este → Norte (izq)')

        # Giros a la derecha (con índice de acceso)
        movimientos['9(1)'] = MovimientoRILSA('9(1)', Acceso.NORTE, Acceso.OESTE, 'derecha', 'Norte → Oeste (der)')
        movimientos['9(2)'] = MovimientoRILSA('9(2)', Acceso.SUR, Acceso.ESTE, 'derecha', 'Sur → Este (der)')
        movimientos['9(3)'] = MovimientoRILSA('9(3)', Acceso.OESTE, Acceso.NORTE, 'derecha', 'Oeste → Norte (der)')
        movimientos['9(4)'] = MovimientoRILSA('9(4)', Acceso.ESTE, Acceso.SUR, 'derecha', 'Este → Sur (der)')

        # Giros en U (con índice de acceso)
        movimientos['10(1)'] = MovimientoRILSA('10(1)', Acceso.NORTE, Acceso.NORTE, 'u_turn', 'Retorno en Norte')
        movimientos['10(2)'] = MovimientoRILSA('10(2)', Acceso.SUR, Acceso.SUR, 'u_turn', 'Retorno en Sur')
        movimientos['10(3)'] = MovimientoRILSA('10(3)', Acceso.OESTE, Acceso.OESTE, 'u_turn', 'Retorno en Oeste')
        movimientos['10(4)'] = MovimientoRILSA('10(4)', Acceso.ESTE, Acceso.ESTE, 'u_turn', 'Retorno en Este')

        # Movimientos peatonales (con índice de acceso)
        # Nota: Para peatones, el destino puede variar (se marca como origen para simplicidad)
        movimientos['P(1)'] = MovimientoRILSA('P(1)', Acceso.NORTE, Acceso.NORTE, 'peatonal', 'Peatón desde Norte')
        movimientos['P(2)'] = MovimientoRILSA('P(2)', Acceso.SUR, Acceso.SUR, 'peatonal', 'Peatón desde Sur')
        movimientos['P(3)'] = MovimientoRILSA('P(3)', Acceso.OESTE, Acceso.OESTE, 'peatonal', 'Peatón desde Oeste')
        movimientos['P(4)'] = MovimientoRILSA('P(4)', Acceso.ESTE, Acceso.ESTE, 'peatonal', 'Peatón desde Este')

        return movimientos

    def inferir_indice_acceso(self, origen: str, codigo_base: str) -> Optional[str]:
        """
        Infiere el índice correcto para códigos 9, 10 y P basándose en el origen.

        Args:
            origen: Acceso de origen ('N', 'S', 'O', 'E')
            codigo_base: '9', '10' o 'P'

        Returns:
            Código completo con índice (ej: '9(2)', '10(4)', 'P(1)') o None
        """
        if codigo_base not in ['9', '10', 'P']:
            return None

        # Mapeo de origen a índice
        indice_map = {
            'N': '1',
            'S': '2',
            'O': '3',
            'E': '4'
        }

        indice = indice_map.get(origen.upper())
        if indice:
            return f"{codigo_base}({indice})"
        return None

    def inferir_codigo_rilsa(self, origen: str, destino: str = None) -> Optional[str]:
        """
        Infiere el código RILSA correcto a partir de origen y opcionalmente destino.

        Args:
            origen: Acceso de origen ('N', 'S', 'O', 'E')
            destino: Acceso de destino opcional ('N', 'S', 'O', 'E')

        Returns:
            Código RILSA correcto o None si no se puede inferir
        """
        try:
            origen_enum = Acceso(origen.upper())
            if destino:
                destino_enum = Acceso(destino.upper())
            else:
                destino_enum = None
        except ValueError:
            return None

        # Si tenemos destino, buscar movimiento completo
        if destino_enum:
            for codigo, mov in self.movimientos_validos.items():
                if mov.origen == origen_enum and mov.destino == destino_enum:
                    return codigo

        return None

    def validar_codigo_movimiento(self, codigo: str, origen: str = None, destino: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Valida si un código de movimiento es correcto según RILSA.

        Args:
            codigo: Código del movimiento (ej: '1', '9(1)', '10')
            origen: Acceso de origen opcional para validación cruzada
            destino: Acceso de destino opcional para validación cruzada

        Returns:
            (es_valido, mensaje_error, codigo_corregido)
        """
        codigo_str = str(codigo).strip()

        # Error: Códigos 9, 10 o P sin índice
        if codigo_str in ['9', '10', 'P']:
            # Primero intentar con origen+destino si están disponibles
            if origen and destino:
                codigo_corregido = self.inferir_codigo_rilsa(origen, destino)
                if codigo_corregido:
                    return False, f"Código '{codigo_str}' sin índice. Debe ser {codigo_corregido}", codigo_corregido
            # Si solo tenemos origen, inferir el índice basándose en él
            elif origen:
                codigo_corregido = self.inferir_indice_acceso(origen, codigo_str)
                if codigo_corregido:
                    return False, f"Código '{codigo_str}' sin índice. Debe ser {codigo_corregido}", codigo_corregido
            return False, f"Código '{codigo_str}' requiere índice de acceso: {codigo_str}(1..4)", None

        # Validar si existe en movimientos RILSA
        if codigo_str not in self.movimientos_validos:
            # Intentar corregir si tenemos origen/destino
            if origen and destino:
                codigo_corregido = self.inferir_codigo_rilsa(origen, destino)
                if codigo_corregido:
                    return False, f"Código '{codigo_str}' incorrecto para {origen}→{destino}. Debe ser '{codigo_corregido}'", codigo_corregido
            return False, f"Código '{codigo_str}' no existe en nomenclatura RILSA", None

        # Validación cruzada con origen/destino si están disponibles
        if origen and destino:
            mov = self.movimientos_validos[codigo_str]
            if mov.origen.value != origen.upper() or mov.destino.value != destino.upper():
                codigo_corregido = self.inferir_codigo_rilsa(origen, destino)
                return False, f"Código '{codigo_str}' no corresponde a {origen}→{destino}. Debe ser '{codigo_corregido}'", codigo_corregido

        return True, "", None

    def es_peaton(self, clase: str) -> bool:
        """Determina si una clase de objeto corresponde a un peatón"""
        clases_peatonales = {'person', 'peaton', 'pedestrian', 'peatones'}
        return clase.lower().strip() in clases_peatonales

    def es_vehiculo_valido(self, clase: str) -> bool:
        """Determina si una clase corresponde a un vehículo válido"""
        vehiculos_validos = {
            'car', 'auto', 'automovil', 'carro',
            'motorcycle', 'moto', 'motocicleta',
            'bus', 'autobus', 'buseta',
            'truck', 'camion',
            'bicycle', 'bicicleta', 'bike',
            'taxi',
            'van', 'camioneta'
        }
        return clase.lower().strip() in vehiculos_validos

    def validar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y normaliza un DataFrame de aforos.

        Args:
            df: DataFrame con columnas [movimiento_rilsa, ramal/origin_cardinal, clase, conteo]

        Returns:
            DataFrame normalizado con columnas adicionales de validación
        """
        df_validado = df.copy()

        # Asegurar columnas necesarias
        if 'ramal' in df.columns:
            df_validado['origen'] = df_validado['ramal']
        elif 'origin_cardinal' in df.columns:
            df_validado['origen'] = df_validado['origin_cardinal']
        else:
            raise ValueError("DataFrame debe tener columna 'ramal' u 'origin_cardinal'")

        if 'dest_cardinal' not in df.columns:
            df_validado['destino'] = None
        else:
            df_validado['destino'] = df_validado['dest_cardinal']

        # Columnas de validación
        df_validado['es_valido'] = True
        df_validado['error_validacion'] = ''
        df_validado['codigo_corregido'] = None
        df_validado['tipo_flujo'] = 'desconocido'

        # Validar cada registro
        for idx, row in df_validado.iterrows():
            codigo = str(row['movimiento_rilsa'])
            origen = row['origen']
            destino = row.get('destino')
            clase = row.get('clase', row.get('cls', ''))

            # Clasificar tipo de flujo
            if self.es_peaton(clase):
                df_validado.at[idx, 'tipo_flujo'] = 'peaton'
                df_validado.at[idx, 'es_valido'] = False
                df_validado.at[idx, 'error_validacion'] = 'PEATÓN mezclado con vehículos - debe separarse'
                self.advertencias.append({
                    'fila': idx,
                    'tipo': 'peaton_mezclado',
                    'mensaje': f'Peatón en movimiento vehicular {codigo}',
                    'clase': clase
                })
            elif self.es_vehiculo_valido(clase):
                df_validado.at[idx, 'tipo_flujo'] = 'vehicular'
            else:
                df_validado.at[idx, 'tipo_flujo'] = 'no_vehicular'
                df_validado.at[idx, 'es_valido'] = False
                df_validado.at[idx, 'error_validacion'] = f'Clase no vehicular: {clase}'
                self.advertencias.append({
                    'fila': idx,
                    'tipo': 'clase_invalida',
                    'mensaje': f'Clase no vehicular detectada: {clase}',
                    'movimiento': codigo
                })

            # Validar código de movimiento
            es_valido, mensaje, corregido = self.validar_codigo_movimiento(codigo, origen, destino)

            if not es_valido:
                df_validado.at[idx, 'es_valido'] = False
                df_validado.at[idx, 'error_validacion'] = mensaje
                df_validado.at[idx, 'codigo_corregido'] = corregido
                self.errores.append({
                    'fila': idx,
                    'codigo_original': codigo,
                    'origen': origen,
                    'destino': destino,
                    'error': mensaje,
                    'correccion': corregido
                })

        return df_validado

    def corregir_automaticamente(self, df_validado: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica correcciones automáticas a códigos incorrectos.

        Args:
            df_validado: DataFrame con validaciones

        Returns:
            DataFrame corregido
        """
        df_corregido = df_validado.copy()

        # Aplicar correcciones donde sea posible
        mask_corregible = (~df_corregido['codigo_corregido'].isna())

        if mask_corregible.any():
            df_corregido.loc[mask_corregible, 'movimiento_rilsa'] = df_corregido.loc[mask_corregible, 'codigo_corregido']
            df_corregido.loc[mask_corregible, 'es_valido'] = True
            df_corregido.loc[mask_corregible, 'error_validacion'] = 'CORREGIDO'

        return df_corregido

    def separar_peatones(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Separa flujos peatonales de vehiculares.

        Args:
            df: DataFrame con datos mixtos

        Returns:
            (df_vehicular, df_peatonal)
        """
        if 'tipo_flujo' not in df.columns:
            df = self.validar_dataframe(df)

        df_vehicular = df[df['tipo_flujo'] == 'vehicular'].copy()
        df_peatonal = df[df['tipo_flujo'] == 'peaton'].copy()

        return df_vehicular, df_peatonal

    def calcular_totales_por_acceso(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula totales por acceso validando consistencia.

        Args:
            df: DataFrame de aforos vehiculares normalizado

        Returns:
            DataFrame con totales por acceso y tipo de movimiento
        """
        if 'movimiento_rilsa' not in df.columns or 'origen' not in df.columns:
            raise ValueError("DataFrame debe tener 'movimiento_rilsa' y 'origen'")

        # Agregar tipo de movimiento
        df_con_tipo = df.copy()
        df_con_tipo['tipo_movimiento'] = df_con_tipo['movimiento_rilsa'].apply(
            lambda x: self.movimientos_validos.get(str(x).strip(), MovimientoRILSA('', Acceso.NORTE, Acceso.NORTE, 'desconocido', '')).tipo
        )

        # Agrupar por acceso y tipo
        columna_conteo = 'conteo' if 'conteo' in df.columns else 'cantidad'

        totales = df_con_tipo.groupby(['origen', 'tipo_movimiento'])[columna_conteo].sum().reset_index()

        # Calcular totales por acceso
        totales_acceso = df_con_tipo.groupby('origen')[columna_conteo].sum().reset_index()
        totales_acceso.rename(columns={columna_conteo: 'total_acceso'}, inplace=True)

        # Validar que suma de movimientos = total por acceso
        validacion = totales.groupby('origen')[columna_conteo].sum().reset_index()
        validacion.rename(columns={columna_conteo: 'suma_movimientos'}, inplace=True)

        comparacion = pd.merge(totales_acceso, validacion, on='origen')
        comparacion['diferencia'] = comparacion['total_acceso'] - comparacion['suma_movimientos']
        comparacion['es_consistente'] = comparacion['diferencia'].abs() < 1

        return totales, totales_acceso, comparacion

    def identificar_hora_pico(self, df: pd.DataFrame, intervalo_min: int = 15) -> Dict:
        """
        Identifica la hora pico analizando intervalos de tiempo.

        Args:
            df: DataFrame con columna timestamp_inicio y conteo
            intervalo_min: Duración del intervalo en minutos (default: 15)

        Returns:
            Dict con información de hora pico
        """
        if 'timestamp_inicio' not in df.columns:
            raise ValueError("DataFrame debe tener columna 'timestamp_inicio'")

        df_tiempo = df.copy()
        df_tiempo['timestamp_inicio'] = pd.to_datetime(df_tiempo['timestamp_inicio'])

        # Agrupar por intervalo
        columna_conteo = 'conteo' if 'conteo' in df.columns else 'cantidad'
        volumenes_tiempo = df_tiempo.groupby('timestamp_inicio')[columna_conteo].sum().reset_index()
        volumenes_tiempo.rename(columns={columna_conteo: 'volumen_total'}, inplace=True)

        # Calcular factor hora pico (volumen máximo de 15 min * 4)
        if intervalo_min == 15:
            volumenes_tiempo['fhp_volumen'] = volumenes_tiempo['volumen_total'] * 4
        else:
            volumenes_tiempo['fhp_volumen'] = volumenes_tiempo['volumen_total'] * (60 / intervalo_min)

        # Identificar pico
        idx_pico = volumenes_tiempo['volumen_total'].idxmax()
        hora_pico = volumenes_tiempo.loc[idx_pico]

        return {
            'timestamp_pico': hora_pico['timestamp_inicio'],
            'volumen_15min': hora_pico['volumen_total'],
            'volumen_hora_equivalente': hora_pico['fhp_volumen'],
            'duracion_intervalo_min': intervalo_min,
            'histograma': volumenes_tiempo
        }

    def generar_reporte_validacion(self) -> str:
        """
        Genera un reporte detallado de validación.

        Returns:
            Texto del reporte
        """
        reporte = []
        reporte.append("=" * 80)
        reporte.append("REPORTE DE VALIDACIÓN RILSA")
        reporte.append("=" * 80)
        reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        reporte.append(f"Criterio U-turn: {self.criterio_uturn}")
        reporte.append("")

        # Resumen de errores
        reporte.append(f"ERRORES CRÍTICOS: {len(self.errores)}")
        reporte.append("-" * 80)
        if self.errores:
            for i, error in enumerate(self.errores, 1):
                reporte.append(f"{i}. Fila {error['fila']}: {error['error']}")
                reporte.append(f"   Código original: {error['codigo_original']} ({error['origen']}→{error.get('destino', '?')})")
                if error['correccion']:
                    reporte.append(f"   ✓ Corrección sugerida: {error['correccion']}")
                reporte.append("")
        else:
            reporte.append("✓ No se detectaron errores críticos")
            reporte.append("")

        # Resumen de advertencias
        reporte.append(f"ADVERTENCIAS: {len(self.advertencias)}")
        reporte.append("-" * 80)
        if self.advertencias:
            for i, adv in enumerate(self.advertencias, 1):
                reporte.append(f"{i}. {adv['tipo']}: {adv['mensaje']}")
        else:
            reporte.append("✓ No se detectaron advertencias")

        reporte.append("")
        reporte.append("=" * 80)

        return "\n".join(reporte)


def procesar_aforo_completo(
    archivo_entrada: str,
    directorio_salida: str,
    criterio_uturn: str = "separado",
    auto_corregir: bool = True
) -> Dict[str, any]:
    """
    Procesa un archivo de aforos completo con validación RILSA.

    Args:
        archivo_entrada: Ruta al CSV de entrada
        directorio_salida: Directorio para guardar resultados
        criterio_uturn: 'separado' o 'como_izquierda'
        auto_corregir: Si True, aplica correcciones automáticas

    Returns:
        Dict con resultados del procesamiento
    """
    import os

    # Crear directorio de salida
    os.makedirs(directorio_salida, exist_ok=True)

    # Leer datos
    df = pd.read_csv(archivo_entrada)

    # Inicializar validador
    validador = ValidadorRILSA(criterio_uturn=criterio_uturn)

    # Validar
    df_validado = validador.validar_dataframe(df)

    # Separar peatones
    df_vehicular, df_peatonal = validador.separar_peatones(df_validado)

    # Corregir si se solicita
    if auto_corregir:
        df_vehicular = validador.corregir_automaticamente(df_vehicular)

    # Calcular totales
    if not df_vehicular.empty:
        totales_mov, totales_acc, validacion_acc = validador.calcular_totales_por_acceso(df_vehicular)
    else:
        totales_mov = totales_acc = validacion_acc = pd.DataFrame()

    # Identificar hora pico
    if 'timestamp_inicio' in df_vehicular.columns:
        hora_pico_info = validador.identificar_hora_pico(df_vehicular)
    else:
        hora_pico_info = None

    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. Datos vehiculares normalizados
    archivo_vehicular = os.path.join(directorio_salida, f'vehicular_normalizado_{timestamp}.csv')
    df_vehicular.to_csv(archivo_vehicular, index=False, encoding='utf-8-sig')

    # 2. Datos peatonales
    if not df_peatonal.empty:
        archivo_peatonal = os.path.join(directorio_salida, f'peatonal_{timestamp}.csv')
        df_peatonal.to_csv(archivo_peatonal, index=False, encoding='utf-8-sig')

    # 3. Totales por movimiento
    if not totales_mov.empty:
        archivo_totales_mov = os.path.join(directorio_salida, f'totales_por_movimiento_{timestamp}.csv')
        totales_mov.to_csv(archivo_totales_mov, index=False, encoding='utf-8-sig')

    # 4. Totales por acceso
    if not totales_acc.empty:
        archivo_totales_acc = os.path.join(directorio_salida, f'totales_por_acceso_{timestamp}.csv')
        totales_acc.to_csv(archivo_totales_acc, index=False, encoding='utf-8-sig')

    # 5. Validación de consistencia
    if not validacion_acc.empty:
        archivo_validacion = os.path.join(directorio_salida, f'validacion_consistencia_{timestamp}.csv')
        validacion_acc.to_csv(archivo_validacion, index=False, encoding='utf-8-sig')

    # 6. Reporte de validación
    reporte = validador.generar_reporte_validacion()
    archivo_reporte = os.path.join(directorio_salida, f'reporte_validacion_{timestamp}.txt')
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write(reporte)

    # 7. Hora pico
    if hora_pico_info:
        archivo_hora_pico = os.path.join(directorio_salida, f'hora_pico_{timestamp}.json')
        hora_pico_serializable = {
            'timestamp_pico': str(hora_pico_info['timestamp_pico']),
            'volumen_15min': int(hora_pico_info['volumen_15min']),
            'volumen_hora_equivalente': float(hora_pico_info['volumen_hora_equivalente']),
            'duracion_intervalo_min': hora_pico_info['duracion_intervalo_min']
        }
        with open(archivo_hora_pico, 'w', encoding='utf-8') as f:
            json.dump(hora_pico_serializable, f, indent=2, ensure_ascii=False)

        # Guardar histograma
        archivo_histograma = os.path.join(directorio_salida, f'histograma_15min_{timestamp}.csv')
        hora_pico_info['histograma'].to_csv(archivo_histograma, index=False, encoding='utf-8-sig')

    return {
        'validador': validador,
        'df_vehicular': df_vehicular,
        'df_peatonal': df_peatonal,
        'totales_movimiento': totales_mov,
        'totales_acceso': totales_acc,
        'validacion_acceso': validacion_acc,
        'hora_pico': hora_pico_info,
        'archivos_generados': {
            'vehicular': archivo_vehicular,
            'peatonal': archivo_peatonal if not df_peatonal.empty else None,
            'totales_movimiento': archivo_totales_mov if not totales_mov.empty else None,
            'totales_acceso': archivo_totales_acc if not totales_acc.empty else None,
            'validacion': archivo_validacion if not validacion_acc.empty else None,
            'reporte': archivo_reporte,
            'hora_pico': archivo_hora_pico if hora_pico_info else None,
            'histograma': archivo_histograma if hora_pico_info else None
        },
        'resumen': {
            'total_registros': len(df),
            'registros_vehiculares': len(df_vehicular),
            'registros_peatonales': len(df_peatonal),
            'errores_criticos': len(validador.errores),
            'advertencias': len(validador.advertencias),
            'auto_corregido': auto_corregir
        }
    }


if __name__ == "__main__":
    # Ejemplo de uso
    print("Módulo de Validación RILSA")
    print("=" * 80)
    print("\nUso:")
    print("  from rilsa_validator import procesar_aforo_completo")
    print("  ")
    print("  resultado = procesar_aforo_completo(")
    print("      archivo_entrada='volumenes_15min_por_movimiento.csv',")
    print("      directorio_salida='salida_rilsa',")
    print("      criterio_uturn='separado',")
    print("      auto_corregir=True")
    print("  )")
