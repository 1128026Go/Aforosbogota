"""
Script simplificado para probar asignación cardinal y velocidades
"""

import pandas as pd
import yaml
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importar módulos
from aforos import velocidades
from aforos import rilsa

def main():
    logger.info("=" * 80)
    logger.info("TEST PIPELINE - Asignación Cardinal y Velocidades")
    logger.info("=" * 80)

    # 1. Cargar configuración
    logger.info("\n1. Cargando configuración...")
    with open('config/aforos.yml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    logger.info("OK - Configuración cargada")

    # 2. Cargar PKL
    logger.info("\n2. Cargando datos PKL...")
    df = pd.read_pickle('data/aforos_bogota_2aforos.pkl')
    logger.info(f"OK - Cargados {len(df):,} registros de {df['track_id'].nunique():,} trayectorias")

    # 3. Corregir velocidades
    logger.info("\n3. Corrigiendo velocidades...")
    df = velocidades.corregir_velocidades_si_px(df, cfg)
    logger.info(f"OK - Velocidad promedio: {df['v_kmh'].mean():.2f} km/h")

    # 4. Asignar cardinales
    logger.info("\n4. Asignando puntos cardinales...")
    df = rilsa.aplicar_asignaciones_cardinales(df, cfg)
    logger.info(f"OK - Cardinales asignados")

    # 5. Clasificar movimientos RILSA
    logger.info("\n5. Clasificando movimientos RILSA...")
    df = rilsa.classify_all_trajectories(df)
    logger.info(f"OK - Movimientos clasificados")

    # 6. Mostrar estadísticas
    logger.info("\n" + "=" * 80)
    logger.info("ESTADÍSTICAS FINALES")
    logger.info("=" * 80)

    logger.info(f"\nTotal registros: {len(df):,}")
    logger.info(f"Total trayectorias: {df['track_id'].nunique():,}")
    logger.info(f"\nVelocidad promedio: {df['v_kmh'].mean():.2f} km/h")
    logger.info(f"Velocidad P85: {df['v_kmh'].quantile(0.85):.2f} km/h")

    logger.info(f"\nDistribución de orígenes:")
    for cardinal, count in df.groupby('track_id')['origin_cardinal'].first().value_counts().items():
        pct = (count / df['track_id'].nunique()) * 100
        logger.info(f"  {cardinal}: {count:,} ({pct:.1f}%)")

    logger.info(f"\nDistribución de destinos:")
    for cardinal, count in df.groupby('track_id')['dest_cardinal'].first().value_counts().items():
        pct = (count / df['track_id'].nunique()) * 100
        logger.info(f"  {cardinal}: {count:,} ({pct:.1f}%)")

    logger.info(f"\nDistribución de movimientos RILSA:")
    for mov, count in df.groupby('track_id')['movimiento_rilsa'].first().value_counts().sort_index().items():
        pct = (count / df['track_id'].nunique()) * 100
        desc = rilsa.get_movement_description(mov)
        logger.info(f"  Mov {mov} ({desc}): {count:,} ({pct:.1f}%)")

    # 7. Guardar muestra
    logger.info(f"\n7. Guardando muestra de resultados...")
    sample = df.groupby('track_id').first().reset_index()
    sample_cols = ['track_id', 'origin_cardinal', 'dest_cardinal', 'movimiento_rilsa', 'v_kmh', 'cls']
    sample[sample_cols].head(20).to_csv('entregables_bogota_2aforos/01_tablas/muestra_test.csv', index=False)
    logger.info("OK - Muestra guardada en entregables_bogota_2aforos/01_tablas/muestra_test.csv")

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETADO EXITOSAMENTE")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()
