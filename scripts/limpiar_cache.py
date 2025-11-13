"""
Script de Limpieza de Cache del Proyecto
=========================================

Elimina todos los archivos temporales y cache de Python, testing, etc.

Uso:
    python limpiar_cache.py
    python limpiar_cache.py --dry-run  (solo mostrar, no eliminar)
"""

import os
import shutil
import argparse
from pathlib import Path


def limpiar_cache(dry_run=False):
    """Limpia cache y archivos temporales"""

    print("="*70)
    print("LIMPIEZA DE CACHE Y ARCHIVOS TEMPORALES")
    print("="*70)

    if dry_run:
        print("\n[MODO DRY-RUN: Solo mostrando, no eliminando]\n")

    # Configuración
    cache_dirs = []
    cache_files = []

    # Patrones de directorios a eliminar
    dir_patterns = [
        '__pycache__',
        '.pytest_cache',
        '.mypy_cache',
        '.ipynb_checkpoints',
        'htmlcov',
        '.coverage',
        '*.egg-info'
    ]

    # Patrones de archivos a eliminar
    file_patterns = [
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '*~',
        '*.swp',
        '*.swo',
        '.DS_Store',
        'Thumbs.db',
        '*.log.tmp'
    ]

    # Buscar archivos y directorios
    print("\nBuscando archivos de cache...")

    for root, dirs, files in os.walk('.'):
        # Ignorar node_modules y .git
        if 'node_modules' in root or '.git' in root:
            continue

        # Buscar directorios
        for d in dirs:
            if any(d == pattern or d.endswith(pattern.replace('*', ''))
                   for pattern in dir_patterns):
                cache_dirs.append(os.path.join(root, d))

        # Buscar archivos
        for f in files:
            if any(f.endswith(pattern.replace('*', '')) or f == pattern
                   for pattern in file_patterns):
                cache_files.append(os.path.join(root, f))

    # Mostrar resumen
    print(f"\nEncontrados:")
    print(f"  - {len(cache_dirs)} directorios de cache")
    print(f"  - {len(cache_files)} archivos temporales")

    if not cache_dirs and not cache_files:
        print("\nNo se encontro cache para limpiar.")
        return

    # Eliminar directorios
    if cache_dirs:
        print(f"\nEliminando {len(cache_dirs)} directorios de cache...")
        for d in cache_dirs:
            try:
                if dry_run:
                    print(f"  [DRY-RUN] Eliminaria: {d}")
                else:
                    shutil.rmtree(d, ignore_errors=True)
                    print(f"  Eliminado: {d}")
            except Exception as e:
                print(f"  Error eliminando {d}: {e}")

    # Eliminar archivos
    if cache_files:
        print(f"\nEliminando {len(cache_files)} archivos temporales...")
        for f in cache_files:
            try:
                if dry_run:
                    print(f"  [DRY-RUN] Eliminaria: {f}")
                else:
                    os.remove(f)
                    print(f"  Eliminado: {f}")
            except Exception as e:
                print(f"  Error eliminando {f}: {e}")

    # Resumen final
    print("\n" + "="*70)
    if dry_run:
        print("LIMPIEZA SIMULADA COMPLETADA")
        print(f"Se eliminarian {len(cache_dirs)} directorios y {len(cache_files)} archivos")
    else:
        print("LIMPIEZA COMPLETADA")
        print(f"Eliminados {len(cache_dirs)} directorios y {len(cache_files)} archivos")
    print("="*70 + "\n")


def limpiar_logs_antiguos(dias=7, dry_run=False):
    """Limpia logs antiguos (mas de N dias)"""

    import time
    import datetime

    print("\nLimpiando logs antiguos...")

    log_dirs = [
        'app/logs',
        'yolo_carla_pipeline/logs',
        'logs'
    ]

    ahora = time.time()
    limite = ahora - (dias * 86400)  # dias en segundos

    logs_eliminados = 0

    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue

        for archivo in os.listdir(log_dir):
            if not archivo.endswith('.log'):
                continue

            ruta = os.path.join(log_dir, archivo)

            # Verificar edad
            mtime = os.path.getmtime(ruta)

            if mtime < limite:
                edad_dias = (ahora - mtime) / 86400

                if dry_run:
                    print(f"  [DRY-RUN] Eliminaria log de {edad_dias:.1f} dias: {ruta}")
                else:
                    try:
                        os.remove(ruta)
                        print(f"  Eliminado log de {edad_dias:.1f} dias: {ruta}")
                        logs_eliminados += 1
                    except Exception as e:
                        print(f"  Error eliminando {ruta}: {e}")

    if logs_eliminados > 0 or dry_run:
        print(f"\nLogs antiguos eliminados: {logs_eliminados}")


def main():
    parser = argparse.ArgumentParser(
        description='Limpia cache y archivos temporales del proyecto',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo mostrar que se eliminaria, sin eliminar'
    )

    parser.add_argument(
        '--logs',
        type=int,
        metavar='DIAS',
        help='Tambien eliminar logs mas antiguos que N dias'
    )

    args = parser.parse_args()

    # Limpieza de cache
    limpiar_cache(dry_run=args.dry_run)

    # Limpieza de logs si se especifico
    if args.logs:
        limpiar_logs_antiguos(dias=args.logs, dry_run=args.dry_run)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
