"""
Script de Diagnóstico - Mapeo RILSA
====================================

Verifica que el mapeo RILSA esté correcto en memoria.
"""

import sys
from pathlib import Path

# Agregar path de módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'modules'))

from rilsa_assignment import AsignadorRILSA, crear_configuracion_simple

def main():
    print("=" * 80)
    print("DIAGNÓSTICO DE MAPEO RILSA")
    print("=" * 80)

    # Crear configuración simple
    config = crear_configuracion_simple(500, 500)

    # Crear asignador
    asignador = AsignadorRILSA(config)

    print("\n✓ Asignador RILSA creado")
    print(f"✓ Total movimientos en mapeo: {len(asignador.mapeo_rilsa)}")

    # Verificar movimientos desde Oeste
    print("\n" + "=" * 80)
    print("VERIFICACIÓN: Movimientos desde OESTE")
    print("=" * 80)

    movimientos_oeste = {
        ('O', 'E'): 'esperado: 3 (directo)',
        ('O', 'S'): 'esperado: 7 (izquierda)',
        ('O', 'N'): 'esperado: 9(3) (derecha)',
        ('O', 'O'): 'esperado: 10(3) (u-turn)'
    }

    todo_correcto = True

    for (origen, destino), descripcion in movimientos_oeste.items():
        codigo_actual = asignador.mapeo_rilsa.get((origen, destino), 'NO ENCONTRADO')
        print(f"\n{origen} → {destino}:")
        print(f"  {descripcion}")
        print(f"  Código actual en mapeo: {codigo_actual}")

        # Verificar si es correcto
        if (origen, destino) == ('O', 'S') and codigo_actual != '7':
            print(f"  ❌ ERROR: Debería ser '7', pero es '{codigo_actual}'")
            todo_correcto = False
        elif (origen, destino) == ('O', 'N') and codigo_actual != '9(3)':
            print(f"  ❌ ERROR: Debería ser '9(3)', pero es '{codigo_actual}'")
            todo_correcto = False
        elif (origen, destino) == ('O', 'E') and codigo_actual != '3':
            print(f"  ❌ ERROR: Debería ser '3', pero es '{codigo_actual}'")
            todo_correcto = False
        elif (origen, destino) == ('O', 'O') and codigo_actual != '10(3)':
            print(f"  ❌ ERROR: Debería ser '10(3)', pero es '{codigo_actual}'")
            todo_correcto = False
        else:
            print(f"  ✓ Correcto")

    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)

    if todo_correcto:
        print("\n✅ TODO CORRECTO: El mapeo RILSA está bien configurado en memoria")
        print("\nSi sigues viendo códigos incorrectos en los CSVs, el problema puede ser:")
        print("  1. Estás viendo un CSV antiguo (no el recién generado)")
        print("  2. Las zonas de acceso están mal definidas y detecta mal O→N vs O→S")
        print("  3. Los tracks JSON ya tienen 'movimiento_rilsa' y se está usando ese campo")
    else:
        print("\n❌ ERROR: El mapeo RILSA tiene errores")
        print("\nPosibles causas:")
        print("  1. El módulo no se recargó correctamente")
        print("  2. Hay archivos .pyc en cache con código antiguo")
        print("  3. Estás importando desde una ubicación diferente")

    # Mostrar tabla completa
    print("\n" + "=" * 80)
    print("MAPEO COMPLETO DESDE OESTE")
    print("=" * 80)
    print("\n| Origen | Destino | Código | Tipo |")
    print("|--------|---------|--------|------|")

    for destino in ['N', 'S', 'E', 'O']:
        codigo = asignador.mapeo_rilsa.get(('O', destino), '?')
        tipo = ""
        if destino == 'E':
            tipo = "Directo"
        elif destino == 'S':
            tipo = "Izquierda"
        elif destino == 'N':
            tipo = "Derecha"
        elif destino == 'O':
            tipo = "U-turn"

        print(f"| O      | {destino}       | {codigo:6} | {tipo} |")

    print("\n" + "=" * 80)

    return 0 if todo_correcto else 1


if __name__ == "__main__":
    sys.exit(main())
