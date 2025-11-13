"""
Script para verificar si hay peatones en movimientos vehiculares
=================================================================

Este script analiza los CSVs de aforo RILSA y verifica:
1. Si hay peatones (person/pedestrian) en movimientos vehiculares (1-10)
2. Si hay vehículos en movimientos peatonales (P(1-4))
3. Estadísticas por movimiento y clase

Uso:
    python verificar_peatones_mov1.py archivo_aforo.csv
"""

import pandas as pd
import sys
from pathlib import Path
from collections import defaultdict


def verificar_clasificacion(csv_path: str):
    """Verifica clasificación correcta de peatones vs vehículos"""

    print("\n" + "="*80)
    print("VERIFICACIÓN DE CLASIFICACIÓN PEATONES VS VEHÍCULOS")
    print("="*80)
    print(f"\n📁 Archivo: {csv_path}\n")

    # Cargar CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return

    print(f"✓ CSV cargado: {len(df)} registros\n")

    # Columnas esperadas
    cols_esperadas = ['movimiento_rilsa', 'clase', 'conteo']
    cols_alternativas = {
        'movimiento_rilsa': ['movimiento', 'mov_rilsa', 'mov'],
        'clase': ['class', 'cls', 'tipo'],
        'conteo': ['n', 'count', 'cantidad']
    }

    # Mapear columnas
    col_map = {}
    for col_esperada in cols_esperadas:
        if col_esperada in df.columns:
            col_map[col_esperada] = col_esperada
        else:
            # Buscar alternativa
            for alt in cols_alternativas.get(col_esperada, []):
                if alt in df.columns:
                    col_map[col_esperada] = alt
                    break

    if len(col_map) != 3:
        print(f"❌ No se encontraron todas las columnas necesarias")
        print(f"   Columnas disponibles: {list(df.columns)}")
        return

    # Renombrar
    df_renamed = df[[col_map['movimiento_rilsa'], col_map['clase'], col_map['conteo']]].copy()
    df_renamed.columns = ['movimiento_rilsa', 'clase', 'conteo']

    # Clases peatonales y vehiculares
    clases_peatonales = {'person', 'peaton', 'pedestrian', 'peatones'}
    clases_vehiculares = {'car', 'auto', 'carro', 'truck', 'camion',
                          'bus', 'autobus', 'motorcycle', 'moto',
                          'bicycle', 'bike', 'bicicleta', 'taxi', 'van', 'camioneta'}

    # Movimientos vehiculares (1-10) vs peatonales (P(1-4))
    movs_vehiculares = set([str(i) for i in range(1, 11)])
    movs_peatonales = {'P(1)', 'P(2)', 'P(3)', 'P(4)'}

    # ANÁLISIS 1: Peatones en movimientos vehiculares
    print("-"*80)
    print("🔍 ANÁLISIS 1: ¿HAY PEATONES EN MOVIMIENTOS VEHICULARES (1-10)?")
    print("-"*80)

    problemas_peaton_en_vehicular = []

    for idx, row in df_renamed.iterrows():
        mov = str(row['movimiento_rilsa']).strip()
        clase = str(row['clase']).lower().strip()
        conteo = row['conteo']

        es_mov_vehicular = mov in movs_vehiculares
        es_clase_peatonal = clase in clases_peatonales

        if es_mov_vehicular and es_clase_peatonal and conteo > 0:
            problemas_peaton_en_vehicular.append({
                'movimiento': mov,
                'clase': clase,
                'conteo': conteo
            })

    if problemas_peaton_en_vehicular:
        print(f"\n❌ PROBLEMA ENCONTRADO: {len(problemas_peaton_en_vehicular)} registros con peatones en movimientos vehiculares\n")

        # Agrupar por movimiento
        por_movimiento = defaultdict(int)
        for p in problemas_peaton_en_vehicular:
            por_movimiento[p['movimiento']] += p['conteo']

        print(f"{'Movimiento':<15} {'Total Peatones':<20} {'Descripción'}")
        print("-"*80)

        movimientos_desc = {
            '1': 'N→S (Norte a Sur)',
            '2': 'S→N (Sur a Norte)',
            '3': 'O→E (Oeste a Este)',
            '4': 'E→O (Este a Oeste)',
            '5': 'N→E (Norte a Este, Izq)',
            '6': 'S→O (Sur a Oeste, Izq)',
            '7': 'O→S (Oeste a Sur, Izq)',
            '8': 'E→N (Este a Norte, Izq)',
            '9': 'Derechas',
            '10': 'U-turns'
        }

        for mov in sorted(por_movimiento.keys()):
            desc = movimientos_desc.get(mov, 'Desconocido')
            print(f"{mov:<15} {por_movimiento[mov]:<20} {desc}")

        print(f"\n⚠️  ESTO ESTÁ MAL: Los peatones NO deben estar en movimientos 1-10")
        print(f"    Los peatones deben estar SOLO en P(1), P(2), P(3), P(4)")

    else:
        print("\n✅ CORRECTO: No hay peatones en movimientos vehiculares (1-10)")

    # ANÁLISIS 2: Vehículos en movimientos peatonales
    print("\n" + "-"*80)
    print("🔍 ANÁLISIS 2: ¿HAY VEHÍCULOS EN MOVIMIENTOS PEATONALES P(1-4)?")
    print("-"*80)

    problemas_vehiculo_en_peaton = []

    for idx, row in df_renamed.iterrows():
        mov = str(row['movimiento_rilsa']).strip()
        clase = str(row['clase']).lower().strip()
        conteo = row['conteo']

        es_mov_peatonal = mov in movs_peatonales
        es_clase_vehicular = clase in clases_vehiculares

        if es_mov_peatonal and es_clase_vehicular and conteo > 0:
            problemas_vehiculo_en_peaton.append({
                'movimiento': mov,
                'clase': clase,
                'conteo': conteo
            })

    if problemas_vehiculo_en_peaton:
        print(f"\n❌ PROBLEMA ENCONTRADO: {len(problemas_vehiculo_en_peaton)} registros con vehículos en movimientos peatonales\n")

        for p in problemas_vehiculo_en_peaton:
            print(f"  Movimiento {p['movimiento']}: {p['conteo']} {p['clase']}")

        print(f"\n⚠️  ESTO ESTÁ MAL: Los vehículos NO deben estar en P(1-4)")

    else:
        print("\n✅ CORRECTO: No hay vehículos en movimientos peatonales P(1-4)")

    # ANÁLISIS 3: Distribución correcta
    print("\n" + "-"*80)
    print("📊 ANÁLISIS 3: DISTRIBUCIÓN GENERAL")
    print("-"*80)

    # Peatones totales
    peatones_total = df_renamed[
        df_renamed['clase'].str.lower().isin(clases_peatonales)
    ]['conteo'].sum()

    # Vehículos totales
    vehiculos_total = df_renamed[
        df_renamed['clase'].str.lower().isin(clases_vehiculares)
    ]['conteo'].sum()

    # Peatones en P(x)
    peatones_en_p = df_renamed[
        (df_renamed['movimiento_rilsa'].isin(movs_peatonales)) &
        (df_renamed['clase'].str.lower().isin(clases_peatonales))
    ]['conteo'].sum()

    # Vehículos en 1-10
    vehiculos_en_1_10 = df_renamed[
        (df_renamed['movimiento_rilsa'].astype(str).isin(movs_vehiculares)) &
        (df_renamed['clase'].str.lower().isin(clases_vehiculares))
    ]['conteo'].sum()

    print(f"\nPeatones totales: {peatones_total}")
    print(f"  └─ En P(1-4): {peatones_en_p} ({'%.1f' % (peatones_en_p/peatones_total*100 if peatones_total > 0 else 0)}%)")

    print(f"\nVehículos totales: {vehiculos_total}")
    print(f"  └─ En 1-10: {vehiculos_en_1_10} ({'%.1f' % (vehiculos_en_1_10/vehiculos_total*100 if vehiculos_total > 0 else 0)}%)")

    # RESUMEN FINAL
    print("\n" + "="*80)
    print("📋 RESUMEN")
    print("="*80)

    errores_totales = len(problemas_peaton_en_vehicular) + len(problemas_vehiculo_en_peaton)

    if errores_totales == 0:
        print("\n✅ TODO CORRECTO: No hay peatones en movimientos vehiculares ni viceversa")
    else:
        print(f"\n❌ SE ENCONTRARON {errores_totales} PROBLEMAS DE CLASIFICACIÓN")

        if problemas_peaton_en_vehicular:
            peatones_mal = sum(p['conteo'] for p in problemas_peaton_en_vehicular)
            print(f"\n   - {peatones_mal} peatones clasificados en movimientos vehiculares")
            print(f"     👉 Estos deben estar en P(1-4), NO en 1-10")

        if problemas_vehiculo_en_peaton:
            vehiculos_mal = sum(p['conteo'] for p in problemas_vehiculo_en_peaton)
            print(f"\n   - {vehiculos_mal} vehículos clasificados en movimientos peatonales")
            print(f"     👉 Estos deben estar en 1-10, NO en P(1-4)")

    print("\n" + "="*80 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Uso: python verificar_peatones_mov1.py <archivo_csv>")
        print("\nEjemplo:")
        print("  python verificar_peatones_mov1.py volumenes_15min.csv")
        return 1

    csv_path = sys.argv[1]

    if not Path(csv_path).exists():
        print(f"❌ Archivo no encontrado: {csv_path}")
        return 1

    verificar_clasificacion(csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
