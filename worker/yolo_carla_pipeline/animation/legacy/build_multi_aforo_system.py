"""
Script Maestro del Sistema Multi-Aforo.

Automatiza todo el flujo:
1. Combina múltiples aforos
2. Genera dashboard integrado
3. Guarda en base de datos (opcional)
4. Abre el dashboard en el navegador
"""

import subprocess
import sys
from pathlib import Path
import argparse


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        print(f"OK - {description} completado")
        return True
    else:
        print(f"ERROR - {description}")
        print(result.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Sistema Maestro Multi-Aforo',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        default=1000,
        help='Número máximo de trayectorias por aforo (default: 1000)'
    )

    parser.add_argument(
        '--save-db',
        action='store_true',
        help='Guardar en base de datos PostgreSQL'
    )

    parser.add_argument(
        '--no-open',
        action='store_true',
        help='No abrir el dashboard automáticamente'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("SISTEMA MAESTRO MULTI-AFORO")
    print("="*70)
    print(f"Configuracion:")
    print(f"  - Sample size: {args.sample_size} trayectorias/aforo")
    print(f"  - Guardar en DB: {'Si' if args.save_db else 'No'}")
    print(f"  - Abrir dashboard: {'No' if args.no_open else 'Si'}")
    print("="*70)

    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "modules" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_file = script_dir / "combined_aforos.json"
    dashboard_file = output_dir / "multi_aforo_dashboard.html"

    # Paso 1: Combinar aforos
    cmd_combine = f'python "{script_dir / "combine_aforos.py"}" --output "{combined_file}" --sample-size {args.sample_size}'
    if not run_command(cmd_combine, "PASO 1: Combinando multiples aforos"):
        print("\nERROR en la combinacion de aforos")
        return 1

    # Paso 2: Generar dashboard
    cmd_dashboard = f'python "{script_dir / "create_multi_aforo_dashboard.py"}" "{combined_file}" "{dashboard_file}"'
    if not run_command(cmd_dashboard, "PASO 2: Generando dashboard multi-aforo"):
        print("\nERROR generando dashboard")
        return 1

    # Paso 3: Guardar en base de datos (opcional)
    if args.save_db:
        cmd_db = f'python "{script_dir / "persist_to_database.py"}" "{combined_file}"'
        if not run_command(cmd_db, "PASO 3: Guardando en base de datos"):
            print("\nAdvertencia: Error guardando en base de datos (continuando...)")

    # Paso 4: Abrir dashboard
    if not args.no_open:
        print(f"\n{'='*70}")
        print("PASO FINAL: Abriendo dashboard")
        print(f"{'='*70}")

        import os
        os.startfile(str(dashboard_file))
        print(f"OK - Dashboard abierto: {dashboard_file}")

    # Resumen
    print("\n" + "="*70)
    print("SISTEMA MULTI-AFORO GENERADO EXITOSAMENTE")
    print("="*70)
    print(f"\nArchivos generados:")
    print(f"  - Datos combinados: {combined_file}")
    print(f"  - Dashboard: {dashboard_file}")
    print(f"\n{'='*70}")

    print("\nCOMO AGREGAR MAS AFOROS:")
    print("="*70)
    print("1. Procesa el nuevo video con YOLO para obtener el archivo JSON de trayectorias")
    print("2. Edita 'config/aforos_config.json' y agrega:")
    print("   - id: Identificador unico (ej: 'aforo_002')")
    print("   - nombre: Nombre descriptivo")
    print("   - tracks_file: Ruta al JSON de trayectorias")
    print("   - offset_x, offset_y: Posicion en el canvas")
    print("   - activo: true")
    print("3. Ejecuta este script de nuevo:")
    print(f"   python build_multi_aforo_system.py")
    print("\nLos nuevos aforos se integraran automaticamente en el mismo lienzo!")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
