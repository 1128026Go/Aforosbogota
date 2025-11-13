"""
Script Principal - Generación de Aforo RILSA Completo
======================================================

Procesamiento end-to-end desde tracks hasta entregables RILSA validados.

Pipeline:
1. Leer tracks desde JSON/PKL
2. Asignar códigos RILSA automáticamente
3. Generar tablas de conteo
4. Validar y corregir según normativa RILSA
5. Generar diagramas visuales
6. Exportar entregables finales

Uso:
    python generar_aforo_rilsa.py <tracks_file> [opciones]

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Agregar path de módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'modules'))

from rilsa_assignment import AsignadorRILSA, crear_configuracion_simple, crear_configuracion_desde_bbox
from rilsa_tablas import GeneradorTablasRILSA
from rilsa_validator import procesar_aforo_completo
from diagrama_rilsa import generar_diagrama_completo

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cargar_tracks_json(archivo: str) -> list:
    """Carga tracks desde archivo JSON"""
    logger.info(f"Cargando tracks desde {archivo}...")
    with open(archivo, 'r') as f:
        data = json.load(f)

    # El archivo puede ser una lista directa o tener un campo 'tracks'
    if isinstance(data, list):
        tracks = data
    elif isinstance(data, dict) and 'tracks' in data:
        tracks = data['tracks']
    else:
        raise ValueError(f"Formato de archivo no reconocido: {archivo}")

    logger.info(f"✓ {len(tracks)} tracks cargados")
    return tracks


def cargar_tracks_pkl(archivo: str) -> list:
    """Carga tracks desde archivo PKL"""
    import pickle
    logger.info(f"Cargando tracks desde {archivo}...")

    with open(archivo, 'rb') as f:
        data = pickle.load(f)

    if isinstance(data, list):
        tracks = data
    elif isinstance(data, dict) and 'tracks' in data:
        tracks = data['tracks']
    else:
        raise ValueError(f"Formato de archivo PKL no reconocido")

    logger.info(f"✓ {len(tracks)} tracks cargados")
    return tracks


def main():
    parser = argparse.ArgumentParser(
        description='Genera aforo RILSA completo desde tracks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s tracks.json
  %(prog)s tracks.json --centro 500 500 --fps 30 --rotacion 0
  %(prog)s tracks.json --salida entregables_rilsa/ --fecha "2025-08-13 06:00"
  %(prog)s tracks.json --rotacion 45  # Norte geográfico a 45° en la imagen
  %(prog)s tracks.json --no-validar --no-diagrama
        """
    )

    parser.add_argument(
        'tracks_file',
        help='Archivo de tracks (JSON o PKL)'
    )

    parser.add_argument(
        '--salida', '-o',
        default='entregables_rilsa',
        help='Directorio de salida (default: entregables_rilsa)'
    )

    parser.add_argument(
        '--centro',
        nargs=2,
        type=float,
        metavar=('X', 'Y'),
        help='Coordenadas del centro de la intersección (ej: 500 500)'
    )

    parser.add_argument(
        '--fps',
        type=float,
        default=30.0,
        help='Frames por segundo del video (default: 30)'
    )

    parser.add_argument(
        '--fecha',
        help='Fecha/hora inicial del aforo (formato: "YYYY-MM-DD HH:MM")'
    )

    parser.add_argument(
        '--tamano-interseccion',
        type=float,
        default=200.0,
        help='Tamaño de la intersección para asignación RILSA (default: 200)'
    )

    parser.add_argument(
        '--no-validar',
        action='store_true',
        help='No ejecutar validación RILSA (más rápido pero sin correcciones)'
    )

    parser.add_argument(
        '--no-diagrama',
        action='store_true',
        help='No generar diagrama visual'
    )

    parser.add_argument(
        '--uturn',
        choices=['separado', 'como_izquierda'],
        default='separado',
        help='Criterio para giros en U (default: separado)'
    )

    parser.add_argument(
        '--zonas',
        help='Archivo JSON con zonas de acceso definidas manualmente (RECOMENDADO). '\
             'Formato: {"norte": [[x1,y1],[x2,y2],...], "sur": [...], ...}'
    )

    parser.add_argument(
        '--rotacion',
        type=float,
        default=0.0,
        help='[EXPERIMENTAL] Rotación de la intersección en grados (0 = Norte arriba). '\
             'Solo si no usas --zonas. Puede desubicarse.'
    )

    args = parser.parse_args()

    # Validar archivo de entrada
    if not os.path.exists(args.tracks_file):
        logger.error(f"❌ Archivo no encontrado: {args.tracks_file}")
        return 1

    print("=" * 80)
    print("GENERACIÓN DE AFORO RILSA - PIPELINE COMPLETO")
    print("=" * 80)
    print(f"\nTracks: {args.tracks_file}")
    print(f"Salida: {args.salida}")
    print(f"FPS: {args.fps}")
    print(f"Rotación: {args.rotacion}° (0 = Norte arriba en imagen)")
    print(f"Criterio U-turn: {args.uturn}")
    print(f"Validación RILSA: {'No' if args.no_validar else 'Sí'}")
    print(f"Diagrama: {'No' if args.no_diagrama else 'Sí'}")
    print()

    try:
        # ===================================================================
        # PASO 1: Cargar tracks
        # ===================================================================
        print("\n[1/7] Cargando tracks...")

        extension = Path(args.tracks_file).suffix.lower()
        if extension == '.json':
            tracks = cargar_tracks_json(args.tracks_file)
        elif extension in ['.pkl', '.pickle']:
            tracks = cargar_tracks_pkl(args.tracks_file)
        else:
            logger.error(f"❌ Formato no soportado: {extension}")
            return 1

        if not tracks:
            logger.error("❌ No se cargaron tracks")
            return 1

        # ===================================================================
        # PASO 2: Configurar intersección y asignar códigos RILSA
        # ===================================================================
        print("\n[2/7] Asignando códigos RILSA a trayectorias...")

        # MÉTODO 1 (RECOMENDADO): Usar zonas definidas manualmente
        if args.zonas:
            logger.info(f"[MÉTODO MANUAL] Cargando zonas desde {args.zonas}...")

            if not os.path.exists(args.zonas):
                logger.error(f"❌ Archivo de zonas no encontrado: {args.zonas}")
                return 1

            with open(args.zonas, 'r') as f:
                zonas_dict = json.load(f)

            config = crear_configuracion_desde_bbox(zonas_dict)
            logger.info(f"✓ {len(config.zonas_acceso)} zonas de acceso cargadas")
            for zona in config.zonas_acceso:
                logger.info(f"  - {zona.nombre}: {zona.acceso.value}")

        # MÉTODO 2 (FALLBACK GEOMÉTRICO): Usar ángulos - puede desubicarse
        else:
            logger.warning("[MÉTODO GEOMÉTRICO - EXPERIMENTAL] No se especificaron zonas")
            logger.warning("Se usará detección por ángulos (puede desubicarse)")
            logger.warning("RECOMENDACIÓN: Usa --zonas para definir accesos manualmente")

            # Determinar centro de la intersección
            if args.centro:
                centro_x, centro_y = args.centro
            else:
                # Calcular centro automáticamente desde tracks
                logger.info("Calculando centro automáticamente...")
                todos_puntos = []
                for track in tracks:
                    if 'trajectory' in track:
                        traj = track['trajectory']
                        if isinstance(traj[0], dict):
                            todos_puntos.extend([(p['x'], p['y']) for p in traj])
                        else:
                            todos_puntos.extend([tuple(p[:2]) for p in traj])

                if todos_puntos:
                    xs = [p[0] for p in todos_puntos]
                    ys = [p[1] for p in todos_puntos]
                    centro_x = sum(xs) / len(xs)
                    centro_y = sum(ys) / len(ys)
                    logger.info(f"Centro calculado: ({centro_x:.1f}, {centro_y:.1f})")
                else:
                    logger.warning("No se pudo calcular centro, usando (0, 0)")
                    centro_x, centro_y = 0, 0

            # Crear configuración simple (sin zonas definidas, usará ángulos)
            config = crear_configuracion_simple(
                centro_x=centro_x,
                centro_y=centro_y,
                tamano=args.tamano_interseccion,
                rotacion_grados=args.rotacion
            )

        # Crear asignador y procesar tracks
        asignador = AsignadorRILSA(config)
        tracks_con_rilsa = asignador.procesar_tracks(tracks)

        # Estadísticas de asignación
        codigos_unicos = set(t['movimiento_rilsa'] for t in tracks_con_rilsa)
        logger.info(f"✓ Códigos RILSA asignados: {len(codigos_unicos)}")
        logger.info(f"  Movimientos detectados: {sorted(codigos_unicos)}")

        # ===================================================================
        # PASO 3: Generar tablas de conteo
        # ===================================================================
        print("\n[3/7] Generando tablas de conteo...")

        # Parsear fecha si se proporcionó
        if args.fecha:
            try:
                fecha_base = datetime.strptime(args.fecha, "%Y-%m-%d %H:%M")
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {args.fecha}, usando fecha actual")
                fecha_base = None
        else:
            fecha_base = None

        # Crear directorio temporal para tablas sin validar
        dir_temporal = os.path.join(args.salida, 'tmp')
        os.makedirs(dir_temporal, exist_ok=True)

        generador = GeneradorTablasRILSA(fps=args.fps, fecha_base=fecha_base)
        generador.exportar_tablas(tracks_con_rilsa, dir_temporal)

        # ===================================================================
        # PASO 4: Validación RILSA (opcional)
        # ===================================================================
        if not args.no_validar:
            print("\n[4/7] Validando y normalizando según RILSA...")

            archivo_15min = os.path.join(dir_temporal, 'volumenes_15min_por_movimiento.csv')

            if os.path.exists(archivo_15min):
                resultado_validacion = procesar_aforo_completo(
                    archivo_entrada=archivo_15min,
                    directorio_salida=args.salida,
                    criterio_uturn=args.uturn,
                    auto_corregir=True
                )

                # Mostrar resumen de validación
                resumen = resultado_validacion['resumen']
                print(f"\n  📊 Resumen de validación:")
                print(f"     Total registros: {resumen['total_registros']}")
                print(f"     Vehiculares: {resumen['registros_vehiculares']}")
                print(f"     Peatonales: {resumen['registros_peatonales']}")
                print(f"     Errores corregidos: {resumen['errores_criticos']}")
                print(f"     Advertencias: {resumen['advertencias']}")

                # Usar archivo validado para diagrama
                archivo_para_diagrama = resultado_validacion['archivos_generados']['vehicular']
            else:
                logger.warning("No se encontró archivo de 15 min, saltando validación")
                archivo_para_diagrama = None
        else:
            print("\n[4/7] Validación RILSA omitida")
            archivo_para_diagrama = os.path.join(dir_temporal, 'volumenes_15min_por_movimiento.csv')

        # ===================================================================
        # PASO 5: Generar diagrama visual (opcional)
        # ===================================================================
        if not args.no_diagrama and archivo_para_diagrama and os.path.exists(archivo_para_diagrama):
            print("\n[5/7] Generando diagrama RILSA...")

            archivo_diagrama = os.path.join(args.salida, 'diagrama_rilsa.png')
            generar_diagrama_completo(
                archivo_csv=archivo_para_diagrama,
                archivo_salida=archivo_diagrama,
                titulo='Diagrama RILSA - Aforo Vehicular',
                mostrar=False
            )
        else:
            print("\n[5/7] Generación de diagrama omitida")

        # ===================================================================
        # PASO 5.5: Generar informe PDF con screenshots por movimiento
        # ===================================================================
        print("\n[6/7] Generando informe PDF con screenshots por movimiento...")

        try:
            # Importar generador de PDF
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from scripts.generar_informe_pdf_rilsa import GeneradorInformePDFRILSA

            # Archivo de salida PDF
            archivo_pdf = os.path.join(args.salida, 'informe_aforo_rilsa.pdf')

            # Generar PDF
            generador_pdf = GeneradorInformePDFRILSA()
            generador_pdf.cargar_tracks(args.tracks)

            # Usar archivo validado si existe, sino el temporal
            archivo_csv_para_pdf = archivo_para_diagrama
            if not archivo_csv_para_pdf or not os.path.exists(archivo_csv_para_pdf):
                archivo_csv_para_pdf = os.path.join(dir_temporal, 'volumenes_15min_por_movimiento.csv')

            if os.path.exists(archivo_csv_para_pdf):
                generador_pdf.cargar_volumenes(archivo_csv_para_pdf)
                generador_pdf.generar_pdf(archivo_pdf)
                logger.info(f"  ✓ PDF generado: {archivo_pdf}")
            else:
                logger.warning("  ⚠ No se pudo generar PDF: archivo CSV no encontrado")

        except Exception as e:
            logger.warning(f"  ⚠ No se pudo generar PDF: {e}")
            logger.debug(f"Traceback: ", exc_info=True)

        # ===================================================================
        # PASO 7: Limpiar archivos temporales
        # ===================================================================
        print("\n[7/7] Finalizando...")

        # Copiar archivos importantes si no hubo validación
        if args.no_validar and os.path.exists(dir_temporal):
            import shutil
            for archivo in os.listdir(dir_temporal):
                src = os.path.join(dir_temporal, archivo)
                dst = os.path.join(args.salida, archivo)
                shutil.copy2(src, dst)

        # Eliminar directorio temporal
        if os.path.exists(dir_temporal):
            import shutil
            shutil.rmtree(dir_temporal)

        # ===================================================================
        # RESUMEN FINAL
        # ===================================================================
        print("\n" + "=" * 80)
        print("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📁 Archivos generados en: {os.path.abspath(args.salida)}/")
        print("\nArchivos principales:")

        # Listar archivos generados
        if os.path.exists(args.salida):
            archivos = sorted(os.listdir(args.salida))
            for archivo in archivos:
                if archivo.endswith(('.csv', '.json', '.txt', '.png', '.pdf')):
                    emoji = '📄' if archivo.endswith('.pdf') else '📊' if archivo.endswith('.png') else '✓'
                    print(f"  {emoji} {archivo}")

        print("\n💡 Para validar manualmente, ejecuta:")
        print(f"   cd {Path(__file__).parent}")
        print(f"   python procesar_rilsa.py ../{args.salida}/volumenes_15min_*.csv --ver-errores")

        print("\n" + "=" * 80)

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
