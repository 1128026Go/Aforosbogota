#!/usr/bin/env python3
"""
Reorganiza entregables_bogota_2aforos al formato ANSV correcto
"""

import shutil
from pathlib import Path
import sys

# Agregar path del generador
sys.path.insert(0, str(Path(__file__).parent))
from generar_paquete_ansv import GeneradorPaqueteANSV

BASE_DIR = Path(__file__).parent
ENTRADA_DIR = BASE_DIR / "entregables_bogota_2aforos" / "01_tablas"
SALIDA_DIR = BASE_DIR / "entregables_bogota_2aforos"

def reorganizar_estructura():
    """Reorganiza la estructura de entregables_bogota_2aforos"""

    print("=" * 80)
    print("REORGANIZANDO ENTREGABLES A FORMATO ANSV")
    print("=" * 80)

    # 1. Crear carpeta _qa para archivos internos
    qa_dir = SALIDA_DIR / "_qa"
    qa_dir.mkdir(exist_ok=True)

    print("\n[*] Moviendo archivos QA a _qa/...")
    archivos_qa = [
        "qa_asignaciones_cardinales.csv",
        "muestra_test.csv",
        "trayectorias_completo.csv"
    ]

    for archivo in archivos_qa:
        src = ENTRADA_DIR / archivo
        if src.exists():
            dst = qa_dir / archivo
            shutil.copy2(src, dst)
            print(f"   [OK] {archivo} -> _qa/")

    # 2. Generar estructura ANSV
    print("\n[*] Generando estructura ANSV...")
    generador = GeneradorPaqueteANSV(entrada_dir=ENTRADA_DIR)

    # Modificar salida para que vaya a entregables_bogota_2aforos directamente
    generador.cargar_datos()

    # Sobrescribir salida_dir para usar entregables_bogota_2aforos
    generador.salida_dir = SALIDA_DIR

    # Generar tablas
    print("\n" + "=" * 80)
    print("GENERANDO TABLAS ANSV")
    print("=" * 80)

    df_15min = generador.generar_tabla_A_volumenes_15min()
    df_veh_eq = generador.generar_tabla_B_veh_equivalentes(df_15min)
    df_modos = generador.generar_tabla_C_modos_sustentables(df_15min)
    df_velocidades = generador.generar_tabla_D_velocidades_resumen()
    df_conflictos = generador.generar_tabla_E_conflictos()
    df_maniobras = generador.generar_tabla_F_maniobras_indebidas()

    # Generar gráficas
    print("\n" + "=" * 80)
    print("GENERANDO GRAFICAS")
    print("=" * 80)
    generador.generar_graficas(df_15min, df_velocidades)

    # Generar Excel
    print("\n" + "=" * 80)
    print("GENERANDO FORMATO EXCEL")
    print("=" * 80)
    generador.generar_excel_ansv(df_15min, df_conflictos)

    # Generar informe
    print("\n" + "=" * 80)
    print("GENERANDO INFORME")
    print("=" * 80)
    generador.generar_informe_docx(df_veh_eq, df_velocidades)

    # Generar summary
    print("\n" + "=" * 80)
    print("GENERANDO SUMMARY")
    print("=" * 80)
    summary = generador.generar_summary_json(df_veh_eq, df_velocidades, df_conflictos, df_maniobras)

    # 3. Agregar README
    print("\n[*] Generando README.md...")
    readme_content = f"""# Entregables ANSV - Punto {generador.punto_id}

**Fecha:** {generador.fecha}
**Municipio:** {generador.df_resumen.iloc[0].get('municipio', 'N/A')}
**Departamento:** {generador.df_resumen.iloc[0].get('departamento', 'N/A')}

## Estructura del paquete

```
entregables_bogota_2aforos/
├── 01_tablas/              # Tablas en formato ANSV
│   ├── volumenes_15min_por_movimiento.csv
│   ├── resumen_veh_mixtos_equivalentes.csv
│   ├── modos_sustentables_15min.csv
│   ├── velocidades_resumen.csv
│   ├── conflictos_resumen.csv
│   └── maniobras_indebidas_resumen.csv
├── 02_graficas/            # Gráficos PNG @ 300 dpi
├── 03_formatos/            # Excel en formato ANSV
├── 04_informe/             # Informe DOCX
├── summary.json            # Resumen para UI
└── _qa/                    # Archivos internos (no entregar)
    ├── trayectorias_completo.csv
    ├── muestra_test.csv
    └── qa_asignaciones_cardinales.csv
```

## Estadísticas

- **Vehículos mixtos:** {summary['veh_mixtos']:,}
- **Vehículos equivalentes:** {summary['veh_equivalentes']:,}
- **P85 mañana:** {summary['v85_kmh']['manana']} km/h
- **P85 tarde:** {summary['v85_kmh']['tarde']} km/h

## Notas de calidad

"""

    for nota in summary['nota_fuentes']:
        readme_content += f"- {nota}\n"

    readme_path = SALIDA_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"   [OK] README.md generado")

    # Resumen final
    print("\n" + "=" * 80)
    print("REORGANIZACION COMPLETADA")
    print("=" * 80)
    print(f"\nEstructura ANSV lista en: {SALIDA_DIR}")
    print(f"\nArchivos QA movidos a: {qa_dir}")
    print(f"\nPara entregar al cliente: excluir carpeta _qa/")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    reorganizar_estructura()
