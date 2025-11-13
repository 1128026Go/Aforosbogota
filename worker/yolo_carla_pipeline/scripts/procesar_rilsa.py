"""
Script de Procesamiento RILSA
==============================

Procesa archivos de aforos y los normaliza según nomenclatura RILSA.
Detecta y corrige automáticamente errores comunes.

Uso:
    python procesar_rilsa.py <archivo_entrada> [opciones]

Ejemplos:
    python procesar_rilsa.py volumenes_15min_por_movimiento.csv
    python procesar_rilsa.py volumenes_por_movimiento.csv --no-corregir
    python procesar_rilsa.py datos.csv --uturn como_izquierda --salida resultados/
"""

import sys
import os
import argparse
from pathlib import Path

# Agregar path de módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'modules'))

from rilsa_validator import procesar_aforo_completo, ValidadorRILSA
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description='Procesa y valida aforos vehiculares según nomenclatura RILSA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s datos/volumenes_15min_por_movimiento.csv
  %(prog)s datos/aforo.csv --salida resultados_rilsa/
  %(prog)s datos/aforo.csv --no-corregir --uturn como_izquierda
        """
    )

    parser.add_argument(
        'archivo_entrada',
        help='Archivo CSV de entrada con datos de aforo'
    )

    parser.add_argument(
        '--salida', '-o',
        default='salida_rilsa',
        help='Directorio de salida para resultados (default: salida_rilsa)'
    )

    parser.add_argument(
        '--uturn',
        choices=['separado', 'como_izquierda'],
        default='separado',
        help='Criterio para giros en U: separado (10(x)) o como_izquierda (default: separado)'
    )

    parser.add_argument(
        '--no-corregir',
        action='store_true',
        help='No aplicar correcciones automáticas, solo reportar errores'
    )

    parser.add_argument(
        '--ver-errores',
        action='store_true',
        help='Mostrar errores detallados en consola'
    )

    parser.add_argument(
        '--preview',
        action='store_true',
        help='Mostrar vista previa de datos sin guardar'
    )

    args = parser.parse_args()

    # Validar archivo de entrada
    if not os.path.exists(args.archivo_entrada):
        print(f"[X] Error: Archivo no encontrado: {args.archivo_entrada}")
        return 1

    print("=" * 80)
    print("PROCESAMIENTO RILSA - NORMALIZACION Y VALIDACION DE AFOROS")
    print("=" * 80)
    print(f"\n[>] Archivo entrada: {args.archivo_entrada}")
    print(f"[>] Directorio salida: {args.salida}")
    print(f"[>] Criterio U-turn: {args.uturn}")
    print(f"[>] Auto-corregir: {'No' if args.no_corregir else 'Si'}")
    print(f"[>] Modo preview: {'Si' if args.preview else 'No'}")
    print()

    if args.preview:
        # Modo preview: solo validar y mostrar
        print("[*] Cargando datos...")
        df = pd.read_csv(args.archivo_entrada)
        print(f"   Total registros: {len(df)}")
        print(f"   Columnas: {', '.join(df.columns)}")
        print()

        print("[*] Validando segun RILSA...")
        validador = ValidadorRILSA(criterio_uturn=args.uturn)
        df_validado = validador.validar_dataframe(df)

        # Estadísticas
        total_errores = (~df_validado['es_valido']).sum()
        total_peatones = (df_validado['tipo_flujo'] == 'peaton').sum()
        total_vehiculos = (df_validado['tipo_flujo'] == 'vehicular').sum()

        print(f"\n[=] Resumen de validacion:")
        print(f"   [OK] Registros validos: {(df_validado['es_valido']).sum()}")
        print(f"   [!!] Registros con errores: {total_errores}")
        print(f"   [V] Registros vehiculares: {total_vehiculos}")
        print(f"   [P] Registros peatonales: {total_peatones}")
        print()

        if total_errores > 0:
            print("[!] Errores detectados:")
            errores_unicos = df_validado[~df_validado['es_valido']]['error_validacion'].value_counts()
            for error, count in errores_unicos.items():
                print(f"   - {error}: {count} casos")
            print()

            if args.ver_errores:
                print("\n[i] Detalle de errores:")
                for i, error in enumerate(validador.errores[:10], 1):
                    print(f"\n{i}. Fila {error['fila']}")
                    print(f"   Codigo: {error['codigo_original']} ({error['origen']} -> {error.get('destino', '?')})")
                    print(f"   Error: {error['error']}")
                    if error['correccion']:
                        print(f"   [+] Correccion: {error['correccion']}")

                if len(validador.errores) > 10:
                    print(f"\n   ... y {len(validador.errores) - 10} errores mas")

        print("\n[i] Para procesar y guardar resultados, ejecuta sin --preview")

    else:
        # Modo completo: procesar y guardar
        try:
            resultado = procesar_aforo_completo(
                archivo_entrada=args.archivo_entrada,
                directorio_salida=args.salida,
                criterio_uturn=args.uturn,
                auto_corregir=not args.no_corregir
            )

            print("[OK] Procesamiento completado exitosamente\n")

            # Mostrar resumen
            resumen = resultado['resumen']
            print(f"[=] Resumen de procesamiento:")
            print(f"   Total registros procesados: {resumen['total_registros']}")
            print(f"   Registros vehiculares: {resumen['registros_vehiculares']}")
            print(f"   Registros peatonales: {resumen['registros_peatonales']}")
            print(f"   Errores criticos: {resumen['errores_criticos']}")
            print(f"   Advertencias: {resumen['advertencias']}")
            print()

            # Archivos generados
            print(f"[+] Archivos generados en '{args.salida}':")
            for nombre, ruta in resultado['archivos_generados'].items():
                if ruta:
                    print(f"   [v] {nombre}: {os.path.basename(ruta)}")
            print()

            # Hora pico
            if resultado['hora_pico']:
                hp = resultado['hora_pico']
                print(f"[*] Hora pico detectada:")
                print(f"   Timestamp: {hp['timestamp_pico']}")
                print(f"   Volumen 15 min: {hp['volumen_15min']} veh")
                print(f"   Volumen equivalente/hora: {hp['volumen_hora_equivalente']:.0f} veh/h")
                print()

            # Validacion de consistencia
            if not resultado['validacion_acceso'].empty:
                inconsistentes = resultado['validacion_acceso'][~resultado['validacion_acceso']['es_consistente']]
                if not inconsistentes.empty:
                    print("[!] Advertencia: Inconsistencias detectadas en totales por acceso")
                    for _, row in inconsistentes.iterrows():
                        print(f"   Acceso {row['origen']}: diferencia de {row['diferencia']} vehiculos")
                    print()

            # Reporte de validacion
            if args.ver_errores and resumen['errores_criticos'] > 0:
                print("\n" + "=" * 80)
                try:
                    print(resultado['validador'].generar_reporte_validacion())
                except UnicodeEncodeError:
                    reporte = resultado['validador'].generar_reporte_validacion()
                    print(reporte.encode('utf-8', errors='replace').decode('utf-8'))

            print(f"\n[OK] Resultados guardados en: {os.path.abspath(args.salida)}")

        except Exception as e:
            print(f"\n[X] Error durante el procesamiento: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
