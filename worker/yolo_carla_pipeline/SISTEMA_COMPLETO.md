# 🚦 Sistema Completo de Visualización y Animación de Tráfico

## 📦 Resumen General

Se han desarrollado **DOS sistemas complementarios** para visualización de trayectorias vehiculares/peatonales:

### 1️⃣ Sistema de Visualización (Módulos)
**Ubicación**: `modules/`

Visualización estática/interactiva con **referencia geográfica**:
- Canvas relativo (coordenadas píxel)
- Overlay sobre OpenStreetMap
- Preparación para CARLA Simulator

### 2️⃣ Sistema de Animación (Animation)
**Ubicación**: `animation/`

Animación dinámica con **canvas infinito** (sin mapa de fondo):
- Animación frame-por-frame
- Controles de reproducción
- Exportación a video
- Métricas avanzadas

---

## 🗂️ Estructura de Archivos

```
proyecto_bogota_traffic/
└── yolo_carla_pipeline/
    ├── modules/                              # Sistema de Visualización
    │   ├── helpers.py                        # Transformaciones de coordenadas
    │   ├── canvas_visualizer.py              # Visualizador canvas relativo
    │   ├── map_overlay.py                    # Overlay OpenStreetMap
    │   └── output/
    │       └── map.html                      # Mapa interactivo generado (3.4 MB)
    │
    ├── animation/                            # Sistema de Animación
    │   ├── parser.py                         # Parser de trayectorias JSON
    │   ├── trajectories.py                   # Gestor de métricas y colores
    │   ├── animator.py                       # Motor de animación
    │   ├── main.py                          # CLI orquestador
    │   ├── README.md                        # Documentación completa
    │   └── QUICKSTART.md                    # Guía rápida
    │
    ├── config/
    │   └── calibration.json                 # Parámetros de calibración GPS/CARLA
    │
    └── output_gx010322/
        └── trajectories/
            └── Gx010322_tracks.json         # Trayectorias procesadas (ejemplo)
```

---

## 1️⃣ SISTEMA DE VISUALIZACIÓN (Modules)

### 🎯 Propósito
Visualización estática/interactiva con **contexto geográfico** (mapas, calibración GPS).

### 📁 Componentes

#### `modules/helpers.py`
**Funcionalidad**: Transformaciones de coordenadas y calibración.

**Clases principales**:
```python
@dataclass
class CalibrationConfig:
    """Configuración de calibración píxel ↔ lat/lon ↔ CARLA"""
    pixels_per_meter: float = 20.0  # AJUSTAR
    origin_lat: float = 4.6097      # GPS esquina superior izquierda
    origin_lon: float = -74.0817
    corner_lat: float = 4.6085      # GPS esquina inferior derecha
    corner_lon: float = -74.0805
    # ... parámetros CARLA

class CoordinateTransformer:
    """Transforma coordenadas entre sistemas"""
    def pixel_to_latlon(px, py) -> (lat, lon)
    def pixel_to_meters(px, py) -> (mx, my)
    def pixel_to_carla(px, py) -> (cx, cy, cz)
```

**Paletas de colores**: Esquemas predefinidos para `class`, `direction`, `speed`, `pattern`.

**Uso**:
```python
from helpers import CalibrationConfig, CoordinateTransformer

config = CalibrationConfig.load("config/calibration.json")
transformer = CoordinateTransformer(config)

lat, lon = transformer.pixel_to_latlon(640, 360)  # Centro del frame
```

---

#### `modules/canvas_visualizer.py`
**Funcionalidad**: Visualización en canvas relativo (píxeles) con matplotlib.

**Características**:
- Canvas con dimensiones fijas (ej: 1280x720)
- Overlay de imagen de fondo opcional
- Visualización estática o interactiva
- Heatmap de densidad
- ROIs (Regiones de Interés)
- Flechas de dirección
- Filtros por clase/longitud

**Uso**:
```python
from canvas_visualizer import CanvasVisualizer

visualizer = CanvasVisualizer(
    frame_width=1280,
    frame_height=720,
    background_image="frame_sample.png"  # Opcional
)

visualizer.load_trajectories("tracks.json")

# Visualización estática
visualizer.visualize(
    color_by='class',
    show_arrows=True,
    show_heatmap=True,
    save_path="output/viz_class.png"
)

# Visualización interactiva con controles
visualizer.create_interactive_viewer()
```

**Salidas**:
- Imágenes PNG con trayectorias coloreadas
- Ventanas interactivas con checkboxes para filtrar clases/overlays en tiempo real

---

#### `modules/map_overlay.py`
**Funcionalidad**: Overlay de trayectorias sobre OpenStreetMap usando Folium.

**Características**:
- Transforma píxeles → lat/lon usando calibración
- Genera mapas HTML interactivos
- Heatmap de densidad
- Markers de inicio/fin
- Múltiples capas de tiles (OSM, CartoDB, etc.)
- Rectángulo del área del video
- Modo clusterizado para grandes datasets

**⚠️ IMPORTANTE**: Requiere **calibración GPS real** de las esquinas del video en `config/calibration.json`.

**Uso**:
```python
from map_overlay import MapOverlay

overlay = MapOverlay(calibration_config="config/calibration.json")
overlay.load_trajectories("tracks.json")

overlay.create_map(
    color_by='class',
    show_heatmap=True,
    show_markers=False,
    max_trajectories=500,  # Limitar para rendimiento
    save_path="output/map.html"
)
```

**Calibración** (editar `config/calibration.json`):
1. Abre el video y pausa en un frame representativo
2. Identifica esquinas superior izquierda e inferior derecha
3. Usa Google Maps para obtener coordenadas GPS de esos puntos
4. Actualiza `origin_lat`, `origin_lon`, `corner_lat`, `corner_lon`
5. Regenera el mapa

**Salida**: Archivo HTML interactivo con mapa de OpenStreetMap.

**Ejemplo generado**: `modules/output/map.html` (3.4 MB) con 500 trayectorias de Gx010322.

---

#### `config/calibration.json`
**Funcionalidad**: Configuración centralizada de parámetros de transformación.

```json
{
  "pixels_per_meter": 20.0,
  "origin_lat": 4.6097,      // GPS esquina superior izquierda (AJUSTAR)
  "origin_lon": -74.0817,
  "corner_lat": 4.6085,      // GPS esquina inferior derecha (AJUSTAR)
  "corner_lon": -74.0805,
  "frame_width": 1280,
  "frame_height": 720,
  "carla_origin_x": 0.0,     // Coords CARLA de píxel (0,0)
  "carla_origin_y": 0.0,
  "carla_origin_z": 0.5,
  "carla_scale": 0.05,       // Metros por píxel en CARLA
  "carla_rotation": 0.0,     // Rotación del frame vs norte CARLA
  "flip_y": true
}
```

**⚠️ TODOS LOS VALORES SON PLACEHOLDERS**: Deben ser ajustados según tu caso de uso específico.

---

### 📝 Uso del Sistema de Visualización

#### Generar Visualización en Canvas
```bash
cd modules
python canvas_visualizer.py ../output/trajectories/tracks.json
```

#### Generar Mapa Interactivo
```bash
cd modules
python map_overlay.py ../output/trajectories/tracks.json --heatmap
```

Abre `output/map.html` en un navegador.

#### Crear Calibración por Defecto
```bash
cd modules
python helpers.py
```

Genera `config/calibration.json` con valores placeholder que debes editar.

---

## 2️⃣ SISTEMA DE ANIMACIÓN (Animation)

### 🎯 Propósito
Animación frame-por-frame con **canvas infinito** (sin mapa de fondo), determinado completamente por los datos.

### 📁 Componentes

#### `animation/parser.py`
**Funcionalidad**: Carga y valida trayectorias JSON.

**Características**:
- Carga archivos individuales o múltiples
- Validación de estructura (track_id, clase, positions, frames)
- Cálculo **dinámico** de bounding box (canvas infinito)
- Acceso frame-por-frame para animación
- Filtros por clase/longitud

**Uso**:
```python
from parser import TrajectoryParser

parser = TrajectoryParser()
parser.load_from_json("tracks.json")

# O múltiples archivos
parser.load_multiple(["track1.json", "track2.json"])

# Filtrar
parser.filter_by_class(['car', 'truck'])
parser.filter_by_length(min_length=30)

# Estadísticas
stats = parser.get_stats()
print(f"Canvas: {stats['bounding_box']}")
print(f"Frames: {stats['frame_range']}")
```

**Canvas Infinito**: Los límites (min_x, max_x, min_y, max_y) se calculan del **mínimo/máximo de todas las posiciones**, no de dimensiones fijas.

---

#### `animation/trajectories.py`
**Funcionalidad**: Gestión de trayectorias con cálculo de métricas avanzadas.

**Características**:
- Cálculo automático de velocidad, aceleración, dirección cardinal
- Detección de patrones de movimiento:
  - `straight`: Trayectoria recta
  - `left`: Giro a la izquierda
  - `right`: Giro a la derecha
  - `u_turn`: Vuelta en U (cambio >150°)
  - `complex`: Múltiples cambios de dirección
- Asignación de colores según modo (class/direction/speed/pattern)
- Estadísticas completas

**Métricas calculadas**:
```python
@dataclass
class TrajectoryMetrics:
    avg_speed: float          # Píxeles por frame
    max_speed: float
    direction: Direction      # N, S, E, W, NE, NW, SE, SW
    pattern: Pattern          # straight, left, right, u_turn, complex
    total_distance: float     # Píxeles recorridos
    displacement: float       # Distancia directa inicio-fin
    sinuosity: float          # total_distance / displacement
    avg_acceleration: float
```

**Uso**:
```python
from trajectories import TrajectoryManager

manager = TrajectoryManager(
    trajectories=parser.trajectories,
    color_mode='speed',       # class | direction | speed | pattern
    calculate_metrics=True
)

# Obtener estadísticas
stats = manager.get_summary_stats()
print(f"Velocidad promedio: {stats['speed_stats']['avg']:.2f}")
print(f"Direcciones: {stats['direction_distribution']}")

# Trayectorias activas en frame específico
active = manager.get_active_at_frame(frame=100)
for track in active:
    print(f"{track['clase']} en {track['position']}, color {track['color']}")
```

---

#### `animation/animator.py`
**Funcionalidad**: Motor de animación con controles interactivos.

**Características**:
- Animación frame-por-frame usando `matplotlib.animation.FuncAnimation`
- Controles interactivos:
  - Botón **Play/Pause**
  - Botón **Reset**
  - Slider de **velocidad** (0.1x - 5.0x) ajustable en tiempo real
- Estelas (trails) configurables
- Modos 2D (XY) y 3D (XYZ donde Z = tiempo)
- Canvas ajustado dinámicamente con margen 10%
- Exportación a video MP4 (requiere ffmpeg)
- Exportación a frames PNG individuales
- Información en pantalla (frame actual, progreso, activos)

**Uso**:
```python
from animator import TrajectoryAnimator

animator = TrajectoryAnimator(
    trajectory_manager=manager,
    mode='2d',              # '2d' o '3d'
    trail_length=15,        # Frames de estela
    marker_size=100,
    show_ids=False
)

# Animación interactiva
animator.animate(
    fps=30,
    speed=1.5,
    show_trails=True,
    show_full_trajectories=False
)

# Exportar a video
animator.export_video(
    output_path="animation.mp4",
    fps=30,
    dpi=150,
    show_trails=True
)

# Exportar frames
animator.export_frames(
    output_dir="frames/",
    fps=30
)
```

---

#### `animation/main.py`
**Funcionalidad**: CLI orquestador completo.

**Argumentos principales**:
```
--tracks TRACKS [TRACKS ...]   # Archivos JSON (uno o múltiples)
--mode {2d,3d}                 # Modo de visualización
--color-mode {class,direction,speed,pattern}
--speed SPEED                  # Velocidad de reproducción
--fps FPS                      # Frames por segundo
--trails N                     # Longitud de estelas
--classes CLASS [CLASS ...]    # Filtrar por clases
--min-length N                 # Longitud mínima de trayectoria
--stats                        # Mostrar estadísticas previas
--export PATH.mp4              # Exportar a video
--export-frames DIR/           # Exportar frames PNG
```

**Ejemplos de uso**:

1. **Animación interactiva básica**:
```bash
cd animation
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json
```

2. **Solo autos, coloreados por velocidad**:
```bash
python main.py --tracks tracks.json --classes car --color-mode speed --stats
```

3. **Vista 3D con estelas largas**:
```bash
python main.py --tracks tracks.json --mode 3d --trails 30 --speed 0.5
```

4. **Exportar a video MP4**:
```bash
python main.py --tracks tracks.json --classes car truck \
  --color-mode direction \
  --export output/traffic.mp4 \
  --fps 30 --dpi 150
```

5. **Comparar múltiples archivos**:
```bash
python main.py --tracks track1.json track2.json track3.json --mode 2d
```

---

### ✅ Prueba con Datos Reales

**Archivo**: `output_gx010322/trajectories/Gx010322_tracks.json`

**Resultados**:
```
Total trayectorias: 3381
Clases: car (39%), person (35%), truck (15%), bus (8%), motorcycle (3%)
Frames: 2 - 145920 (145919 total, ~81 minutos @ 30 FPS)

Canvas dinámico:
  X: [9.5, 1266.5] (1257.0 px width)
  Y: [88.0, 697.5] (609.5 px height)

Métricas globales:
  Velocidad promedio: 7.47 px/frame
  Velocidad máxima: 75.48 px/frame
  Distancia total: 1,294,149.6 px
  Sinuosidad promedio: 5.42 (serpenteo moderado)

Distribución de direcciones:
  east: 1314 (38.9%)    west: 1316 (38.9%)  ← Bidireccional
  north: 169 (5.0%)     south: 86 (2.5%)
  northeast: 132        southeast: 150
  northwest: 122        southwest: 92

Patrones detectados:
  straight: 1235 (36.5%)
  u_turn: 1156 (34.2%)    ← Muchas vueltas en U!
  right: 471 (13.9%)
  left: 413 (12.2%)
  complex: 106 (3.1%)
```

**Conclusiones**:
- Dataset grande y rico en patrones
- Tráfico bidireccional (E-W)
- Alto porcentaje de U-turns (posible intersección o rotonda)
- Sistema probado exitosamente con carga real

---

## 🔄 Integración entre Sistemas

### Workflow Completo

```bash
# PASO 1: Procesar PKL con pipeline principal
cd yolo_carla_pipeline
python main.py --pkl ../data/pkls/Gx010322.pkl \
  --confidence 0.6 \
  --output output_gx010322/

# Genera:
# - output_gx010322/trajectories/Gx010322_tracks.json
# - output_gx010322/metrics/Gx010322_metrics.json
# - output_gx010322/visualizations/...

# PASO 2a: Visualización estática/mapa (Modules)
cd modules
python map_overlay.py ../output_gx010322/trajectories/Gx010322_tracks.json --heatmap
# Abre: output/map.html

# PASO 2b: Animación dinámica (Animation)
cd ../animation
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json \
  --color-mode speed \
  --classes car truck \
  --stats \
  --export ../output_gx010322/animation.mp4
```

---

## 📊 Comparación de Sistemas

| Aspecto | Sistema de Visualización (Modules) | Sistema de Animación (Animation) |
|---------|-----------------------------------|----------------------------------|
| **Canvas** | Fijo (ej: 1280x720) | Infinito (dinámico según datos) |
| **Referencia** | Geográfica (GPS/CARLA) | Relativa (píxeles puros) |
| **Tipo** | Estático/Interactivo | Animación temporal |
| **Salida** | PNG, HTML interactivo | Video MP4, PNG frames |
| **Calibración** | Requiere GPS real | No requiere |
| **Uso Principal** | Análisis espacial georeferenciado | Análisis temporal de flujo |
| **Métricas** | Básicas | Avanzadas (velocidad, patrón, dirección) |
| **Interactividad** | Checkboxes de filtros | Controles de reproducción |

**Cuándo usar cada uno**:
- **Modules**: Cuando necesitas visualizar en un **contexto geográfico real** (OSM, CARLA)
- **Animation**: Cuando quieres ver **evolución temporal** o crear **videos de flujo**

---

## 🎨 Modos de Coloración (Ambos Sistemas)

Ambos sistemas soportan los mismos modos de coloración:

### `class` - Por Tipo de Objeto
- 🔵 car → `#3498db`
- 🔴 truck → `#e74c3c`
- 🟣 bus → `#9b59b6`
- 🟠 motorcycle → `#f39c12`
- 🟢 bicycle → `#2ecc71`
- 🔷 person → `#1abc9c`

### `direction` - Por Dirección Cardinal
- 🔵 north → `#3498db`
- 🔴 south → `#e74c3c`
- 🟢 east → `#2ecc71`
- 🟠 west → `#f39c12`
- + Intermedias (NE, NW, SE, SW)

### `speed` - Por Velocidad
- 🔵 very_slow (0-2) → `#3498db`
- 🟢 slow (2-5) → `#2ecc71`
- 🟠 medium (5-10) → `#f39c12`
- 🔴 fast (10+) → `#e74c3c`

### `pattern` - Por Patrón
- 🔵 straight → `#3498db`
- 🟢 left → `#2ecc71`
- 🟠 right → `#f39c12`
- 🔴 u_turn → `#e74c3c`
- 🟣 complex → `#9b59b6`

---

## 📚 Documentación Completa

- **`animation/README.md`**: Documentación exhaustiva del sistema de animación
- **`animation/QUICKSTART.md`**: Guía rápida con comandos listos para usar
- **Este archivo**: Visión general de ambos sistemas

---

## 🛠️ Dependencias

### Sistema de Visualización (Modules)
```bash
pip install folium matplotlib pillow numpy
```

### Sistema de Animación (Animation)
```bash
pip install matplotlib numpy

# Para exportar video:
# Windows:
choco install ffmpeg

# Linux:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

---

## 🚀 Ejemplos de Uso Práctico

### Caso de Uso 1: Análisis de Congestión
```bash
# 1. Generar trayectorias
python main.py --pkl video.pkl --output analysis/

# 2. Visualizar en mapa con heatmap
cd modules
python map_overlay.py ../analysis/trajectories/tracks.json --heatmap

# 3. Animar solo momentos de alta densidad
cd ../animation
python main.py --tracks ../analysis/trajectories/tracks.json \
  --color-mode speed \
  --export congestion.mp4
```

### Caso de Uso 2: Estudio de Patrones de Giro
```bash
cd animation
python main.py --tracks tracks.json \
  --color-mode pattern \
  --stats \
  --show-full-trajectories
# Analizar estadísticas de patrones antes de visualizar
```

### Caso de Uso 3: Comparación Temporal
```bash
# Generar trayectorias de diferentes horas
python main.py --pkl morning.pkl --output morning/
python main.py --pkl afternoon.pkl --output afternoon/

# Animar cada uno
cd animation
python main.py --tracks ../morning/trajectories/tracks.json --export morning.mp4
python main.py --tracks ../afternoon/trajectories/tracks.json --export afternoon.mp4

# Comparar videos lado a lado
```

### Caso de Uso 4: Exportar para Análisis Externo
```bash
cd animation
# Exportar frames para procesamiento con OpenCV/ML
python main.py --tracks tracks.json \
  --export-frames frames/ \
  --classes car \
  --min-length 50
```

---

## ✅ Checklist de Funcionalidades Completadas

### Sistema de Visualización (Modules)
- ✅ Transformación píxel → lat/lon
- ✅ Transformación píxel → CARLA
- ✅ Canvas relativo con matplotlib
- ✅ Overlay sobre OpenStreetMap
- ✅ Heatmap de densidad
- ✅ ROIs (Regiones de Interés)
- ✅ Visualizador interactivo con checkboxes
- ✅ Calibración configurable (JSON)
- ✅ Mapa HTML generado y probado (3.4 MB)

### Sistema de Animación (Animation)
- ✅ Canvas infinito (bounds dinámicos)
- ✅ Animación frame-por-frame
- ✅ Controles interactivos (Play/Pause/Reset/Speed)
- ✅ Modos 2D y 3D
- ✅ Estelas configurables
- ✅ Múltiples modos de color (4 modos)
- ✅ Cálculo de métricas avanzadas
- ✅ Detección de patrones de movimiento
- ✅ Filtros por clase/longitud
- ✅ Exportación a video MP4
- ✅ Exportación a frames PNG
- ✅ CLI completo y documentado
- ✅ Soporte para múltiples archivos
- ✅ Estadísticas detalladas
- ✅ Probado con 3381 trayectorias reales

---

## 🎓 Próximos Pasos Sugeridos

1. **Calibrar GPS** (Modules):
   - Editar `config/calibration.json` con coordenadas GPS reales
   - Regenerar mapa y verificar alineación

2. **Generar Videos** (Animation):
   - Exportar animaciones temáticas (solo camiones, solo velocidad alta, etc.)
   - Crear comparaciones temporales

3. **Integración CARLA** (Futuro):
   - Usar `helpers.pixel_to_carla()` para spawn en CARLA Simulator
   - Ver `modules/carla_integration.py` del pipeline principal

4. **Análisis Personalizado**:
   - Modificar paletas de colores en `trajectories.py`
   - Agregar ROIs personalizados en `canvas_visualizer.py`

---

## 📞 Soporte

- **Documentación completa**: `animation/README.md`
- **Guía rápida**: `animation/QUICKSTART.md`
- **Calibración**: Editar `config/calibration.json`
- **Problemas comunes**: Ver secciones "Solución de Problemas" en READMEs

---

**Sistemas completados, probados y documentados.**
**Listos para producción con datos reales.**

---

_Desarrollado para análisis de tráfico vehicular en Bogotá_
_Pipeline YOLOv8 + SORT → Visualización → Animación → CARLA_
