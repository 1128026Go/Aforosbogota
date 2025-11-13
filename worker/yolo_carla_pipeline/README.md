# 🚗 Pipeline YOLO → Aforos RILSA → Visualización

Pipeline profesional en Python para generación automática de aforos vehiculares y peatonales según nomenclatura RILSA estándar.

## 📋 Tabla de Contenidos

- [Sistema RILSA](#sistema-rilsa)
- [Características](#características)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Módulos](#módulos)
- [Outputs](#outputs)
- [Documentación](#documentación)

---

## 🎯 Sistema RILSA

Este proyecto implementa el **sistema RILSA completo con 20 movimientos**:

### Movimientos Vehiculares (16)
- **Directos (4):** 1, 2, 3, 4
- **Izquierdas (4):** 5, 6, 7, 8
- **Derechas (4):** 9(1), 9(2), 9(3), 9(4)
- **U-turns (4):** 10(1), 10(2), 10(3), 10(4)

### Movimientos Peatonales (4)
- **P(1)** - Peatones desde Norte
- **P(2)** - Peatones desde Sur
- **P(3)** - Peatones desde Oeste
- **P(4)** - Peatones desde Este

**Accesos:** N (Norte), S (Sur), O (Oeste), E (Este)
**Índices:** N=1, S=2, O=3, E=4

---

## ✨ Características

### 🚦 Aforos Vehiculares RILSA
- ✅ **Detección automática** de movimientos RILSA desde trayectorias
- ✅ **Separación automática** de flujos vehiculares y peatonales
- ✅ **Validación y corrección** automática de códigos
- ✅ **Tablas por intervalo** (15 min configurables)
- ✅ **Diagramas visuales** de intersección
- ✅ **Exportación CSV** compatible con formatos ANSV

### 🚶 Aforos Peatonales
- ✅ **Códigos P(1-4)** por acceso de origen
- ✅ **Separación automática** de vehículos
- ✅ **Tablas dedicadas** para flujo peatonal
- ✅ **Integración con dashboard** interactivo

### 📊 Visualización y Análisis
- ✅ **Dashboard interactivo** con filtros por movimiento
- ✅ **Animación de trayectorias** en tiempo real
- ✅ **Aforo en vivo** con intervalos de 15 min
- ✅ **Heatmaps** de entrada/salida
- ✅ **Detección de hora pico** automática

### 🔍 Validación y Diagnóstico
- ✅ **Validador RILSA** con 50+ reglas
- ✅ **Corrección automática** de errores comunes
- ✅ **Reportes de inconsistencias**
- ✅ **Scripts de diagnóstico** de peatones y tracks

---

## 🏗️ Arquitectura del Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      ENTRADA: PKL YOLO                       │
│   (Detecciones frame por frame: bbox, clase, confianza)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  read_pkl.py    │  ← Ingesta y filtrado
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │  tracking.py    │  ← ByteTrack (IoU + Kalman)
                └────────┬────────┘
                         │
                ┌────────▼─────────────┐
                │ rilsa_assignment.py  │  ← Asignación códigos RILSA
                │  • Detecta origen/   │     (1-8, 9(x), 10(x), P(x))
                │    destino (N/S/O/E) │
                │  • Separa peatones   │
                └────────┬─────────────┘
                         │
                ┌────────▼────────┐
                │ rilsa_tablas.py │  ← Genera tablas 15 min
                └────────┬────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼─────────┐         ┌──────────▼──────────┐
│ rilsa_validator  │         │  diagrama_rilsa.py  │
│ • Valida códigos │         │  • Gráfico visual   │
│ • Corrige errores│         │  • Matriz O-D       │
└────────┬─────────┘         └──────────┬──────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
        ┌────────────────▼───────────────┐
        │ create_multi_aforo_dashboard   │  ← Dashboard interactivo
        │  • Animación trayectorias      │
        │  • Filtros P(1-4)              │
        │  • Aforo en vivo               │
        └────────────────┬───────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     OUTPUTS RILSA                            │
│  • volumenes_15min_por_movimiento.csv (con P(1-4))          │
│  • vehicular_normalizado.csv (solo 1-10)                    │
│  • peatonal.csv (solo P(1-4))                               │
│  • diagrama_rilsa.png                                       │
│  • dashboard_interactivo.html                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Instalación

### Requisitos
- Python 3.8+
- pip

### Instalación de dependencias

```bash
cd yolo_carla_pipeline
pip install -r requirements.txt
```

**Dependencias principales:**
- pandas, numpy
- opencv-python
- matplotlib, seaborn
- filterpy (Kalman)
- scipy (Hungarian algorithm)

---

## 🚀 Uso Rápido

### 1. Generar aforos desde tracks

```bash
python scripts/generar_aforo_rilsa.py \
    --tracks output/Gx010322_tracks.json \
    --zonas config/zonas_ejemplo.json \
    --salida aforos_rilsa/ \
    --intervalo 15
```

**Esto genera:**
- ✅ Tablas de 15 min con códigos RILSA (incluye P(1-4))
- ✅ Archivos vehicular y peatonal separados
- ✅ Diagrama visual de la intersección
- ✅ **Informe PDF con screenshots por movimiento** ⭐ NUEVO
- ✅ Reporte de validación completo

### 2. Validar y normalizar aforos existentes

```bash
python scripts/procesar_rilsa.py volumenes_15min.csv \
    --salida validados/ \
    --ver-errores
```

**Corrige automáticamente:**
- ❌ Códigos 9 y 10 sin índice → `9(x)`, `10(x)`
- ❌ Peatones mezclados con vehículos → Separa a P(1-4)
- ❌ Movimientos incorrectos → Corrige según origen-destino

### 3. Visualizar en dashboard interactivo

```bash
# Dentro de animation/
python create_multi_aforo_dashboard.py \
    --json ../output/combined_tracks.json \
    --output dashboard.html
```

**Abre en navegador:**
- 🎬 Animación de trayectorias
- 🚶 Filtros por movimiento (incluye P(1-4))
- 📊 Aforo en vivo con tablas vehicular y peatonal
- ⏱️ Control de velocidad y tiempo

---

## 📁 Flujo de Trabajo Completo

### Paso 1: Procesar video con YOLO
```bash
# Genera detecciones PKL
yolo detect model=yolov8n.pt source=video.mp4
```

### Paso 2: Tracking + RILSA
```bash
# Pipeline completo: PKL → Tracks → RILSA → Tablas
python main.py --pkl detections.pkl --output aforos/
```

### Paso 3: Validación RILSA
```bash
# Valida y corrige códigos RILSA
python scripts/procesar_rilsa.py aforos/volumenes_15min.csv
```

### Paso 4: Visualización
```bash
# Dashboard interactivo
cd animation/
python create_multi_aforo_dashboard.py --json ../aforos/tracks.json
```

---

## 🧩 Módulos Principales

### Core RILSA

#### `modules/rilsa_assignment.py`
Asigna códigos RILSA (1-8, 9(x), 10(x), P(x)) a cada trayectoria:
- Detecta acceso de origen y destino
- Separa peatones → P(1-4)
- Detecta U-turns → 10(x)
- Calcula ángulos de giro

#### `modules/rilsa_tablas.py`
Genera tablas de conteo por intervalo:
- Agrupa por timestamp de 15 min
- Filtra clases vehiculares vs peatonales
- Calcula totales por acceso y movimiento
- Detecta hora pico

#### `modules/rilsa_validator.py`
Valida y corrige códigos RILSA:
- 50+ reglas de validación
- Corrección automática de índices
- Separación de peatones
- Reporte de inconsistencias

#### `modules/diagrama_rilsa.py`
Genera diagramas visuales:
- Matriz origen-destino
- Diagrama de intersección
- Volúmenes por movimiento
- Compatible con 20 movimientos

### Tracking y Detección

#### `modules/tracking.py`
Implementa ByteTrack para multi-object tracking:
- Kalman Filter para predicción
- Hungarian Algorithm para asociación
- Filtro de tracks válidas (hits >= 3)

#### `modules/read_pkl.py`
Lectura y validación de PKL YOLO:
- Extrae metadata del video
- Filtra por confianza
- Parsea detecciones

### Utilidades

#### `modules/helpers.py`
Funciones auxiliares compartidas

#### `modules/map_overlay.py`
Integración con mapas (opcional)

---

## 📂 Outputs Generados

### Tablas CSV

```
aforos_rilsa/
├── volumenes_15min_por_movimiento.csv      # Principal (con P(1-4))
├── volumenes_por_movimiento.csv             # Totales
├── resumen_por_acceso.csv                   # Por acceso (N/S/O/E)
├── resumen_por_tipo_movimiento.csv          # Por tipo
├── vehicular_normalizado_YYYYMMDD.csv       # Solo vehículos (1-10)
├── peatonal_YYYYMMDD.csv                    # Solo peatones (P(1-4))
└── validacion_consistencia_YYYYMMDD.csv     # Validación
```

### Visuales

```
aforos_rilsa/
├── diagrama_rilsa.png                       # Diagrama intersección
├── informe_aforo_rilsa.pdf                  # PDF con 20 páginas (1 por movimiento)  ⭐
├── dashboard.html                            # Dashboard interactivo
└── reporte_validacion_YYYYMMDD.txt          # Reporte texto
```

**Nuevo: Informe PDF**
- ✅ Portada con resumen general
- ✅ 20 páginas (una por cada movimiento RILSA)
- ✅ Cada página incluye:
  - Estadísticas del movimiento
  - Screenshot de trayectorias filtradas
  - Desglose por clase vehicular/peatonal

### Formato de Tabla Principal

```csv
timestamp_inicio,periodo,ramal,movimiento_rilsa,clase,conteo
2025-08-13 06:00:00,mañana,N,1,car,45
2025-08-13 06:00:00,mañana,N,5,motorcycle,28
2025-08-13 06:00:00,mañana,N,9(1),truck,12
2025-08-13 06:00:00,mañana,N,P(1),person,18
```

---

## 📖 Documentación Completa

### Manuales RILSA
- **[MANUAL_RILSA.md](../docs/MANUAL_RILSA.md)** - Manual técnico completo
- **[README_RILSA.md](../docs/README_RILSA.md)** - Guía rápida
- **[RILSA_CHEATSHEET.md](../docs/RILSA_CHEATSHEET.md)** - Referencia rápida

### Guías de Usuario
- **[GUIA_GENERAR_AFOROS.md](../docs/GUIA_GENERAR_AFOROS.md)** - Tutorial paso a paso
- **[COMANDOS_RAPIDOS.md](COMANDOS_RAPIDOS.md)** - Comandos frecuentes
- **[SISTEMA_COMPLETO.md](SISTEMA_COMPLETO.md)** - Arquitectura completa

---

## 🔍 Scripts de Diagnóstico

### Verificar peatones mal clasificados
```bash
python scripts/verificar_peatones_mov1.py volumenes_15min.csv
```

### Analizar PKL original
```bash
python scripts/analizar_pkl_peatones.py detections.pkl
```

### Diagnosticar tracks
```bash
python scripts/diagnostico_tracks.py tracks.json
```

---

## 📌 Notas Importantes

### ✅ Reglas RILSA
- Códigos **1-8**: SIN índice
- Códigos **9, 10, P**: CON índice obligatorio `(1-4)`
- Peatones: SOLO en P(1-4), NUNCA en 1-10
- Vehículos: SOLO en 1-10, NUNCA en P(1-4)

### ⚠️ Configuración de Zonas
**ESENCIAL:** Definir zonas manualmente para asignación precisa:
```bash
python scripts/definir_zonas_interactivo.py video.mp4 --output zonas.json
```

Sin zonas definidas, el sistema usa detección geométrica que puede fallar.

### 🐛 Threshold de Tracking
Las trayectorias con menos de **3 detecciones** son filtradas.
Para incluir más tracks: modificar `tracking.py:55` (`hits >= 2`)

---

## 🆕 Actualizaciones Recientes

- ✅ **Informe PDF automático** con screenshots por movimiento ⭐ NUEVO
- ✅ **Sistema P(1-4)** para movimientos peatonales
- ✅ **Separación automática** vehicular/peatonal
- ✅ **Dashboard con filtros** por movimiento RILSA
- ✅ **Aforo en vivo** con tabla peatonal dedicada
- ✅ **Validación mejorada** con corrección automática
- ✅ **Tiempo real** en barra de progreso (HH:MM:SS)

---

## 📞 Soporte

Para problemas o dudas:
1. Consulta la [documentación RILSA](../docs/)
2. Revisa el [informe de limpieza](../INFORME_LIMPIEZA.md)
3. Ejecuta scripts de diagnóstico

---

## 📄 Licencia

Proyecto interno - Sistema de Aforos Vehiculares RILSA

---

**Versión:** 2.0 (Sistema RILSA Completo)
**Última actualización:** 2025-11-09
