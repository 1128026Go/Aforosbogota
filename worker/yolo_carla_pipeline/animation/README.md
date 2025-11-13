# Sistema de Animación de Trayectorias

Sistema completo de visualización y animación de trayectorias vehiculares/peatonales con **canvas infinito** (sin mapa de fondo).

## 🎯 Características

- **Canvas Infinito**: Límites determinados completamente por los datos, no por un mapa de fondo
- **Animación Frame-por-Frame**: Reproducción precisa basada en timestamps reales
- **Controles de Reproducción**: Play, Pause, Reset, Speed Control (0.1x - 5.0x)
- **Múltiples Modos de Coloración**:
  - `class`: Color por tipo de objeto (car, truck, bus, etc.)
  - `direction`: Color por dirección cardinal (N, S, E, W, NE, NW, SE, SW)
  - `speed`: Color por velocidad (very_slow, slow, medium, fast)
  - `pattern`: Color por patrón de movimiento (straight, left, right, u_turn, complex)
- **Visualización 2D/3D**: Vista superior o espacio-temporal
- **Estelas (Trails)**: Trazas de posiciones previas configurables
- **Exportación**: Video MP4 o frames individuales PNG
- **Filtros**: Por clase, longitud de trayectoria, etc.
- **Métricas Avanzadas**: Velocidad, aceleración, dirección, sinuosidad, patrones

## 📁 Arquitectura

```
animation/
├── parser.py          # Carga y validación de trayectorias JSON
├── trajectories.py    # Gestión, métricas y asignación de colores
├── animator.py        # Motor de animación con controles
├── main.py           # CLI orquestador
└── README.md         # Este archivo
```

## 🚀 Uso Básico

### Animación Interactiva Simple

```bash
cd animation
python main.py --tracks ../output/trajectories/tracks.json
```

Esto abrirá una ventana interactiva con:
- Animación automática de trayectorias
- Botones Play/Pause y Reset
- Slider de velocidad ajustable en tiempo real
- Información de frame actual y estadísticas

### Modos de Visualización

#### 2D (Vista Superior)
```bash
python main.py --tracks ../output/trajectories/tracks.json --mode 2d
```

Canvas XY con posiciones de vehículos/peatones. Ideal para análisis de patrones espaciales.

#### 3D (Vista Espacio-Temporal)
```bash
python main.py --tracks ../output/trajectories/tracks.json --mode 3d
```

Canvas XYZ donde Z = tiempo (frames). Permite visualizar evolución temporal de trayectorias.

### Modos de Coloración

#### Por Clase de Objeto
```bash
python main.py --tracks tracks.json --color-mode class
```
- 🔵 Azul: cars
- 🔴 Rojo: trucks
- 🟣 Morado: buses
- 🟠 Naranja: motorcycles
- 🟢 Verde: bicycles
- 🔷 Cyan: persons

#### Por Dirección de Movimiento
```bash
python main.py --tracks tracks.json --color-mode direction
```
- Norte, Sur, Este, Oeste
- Direcciones intermedias (NE, NW, SE, SW)
- Gris: estacionario

#### Por Velocidad
```bash
python main.py --tracks tracks.json --color-mode speed
```
- Azul: muy lento (0-2 px/frame)
- Verde: lento (2-5 px/frame)
- Naranja: medio (5-10 px/frame)
- Rojo: rápido (10+ px/frame)

#### Por Patrón de Movimiento
```bash
python main.py --tracks tracks.json --color-mode pattern
```
- Azul: recto
- Verde: giro izquierda
- Naranja: giro derecha
- Rojo: U-turn
- Morado: complejo

### Controles de Animación

```bash
# Velocidad 2x
python main.py --tracks tracks.json --speed 2.0

# Velocidad lenta 0.5x
python main.py --tracks tracks.json --speed 0.5

# Estelas largas (30 frames)
python main.py --tracks tracks.json --trails 30

# Sin estelas
python main.py --tracks tracks.json --trails 0

# 60 FPS
python main.py --tracks tracks.json --fps 60

# Mostrar IDs de tracks
python main.py --tracks tracks.json --show-ids

# Mostrar trayectorias completas en el fondo
python main.py --tracks tracks.json --show-full-trajectories
```

### Filtros

```bash
# Solo autos y camiones
python main.py --tracks tracks.json --classes car truck

# Trayectorias con al menos 20 puntos
python main.py --tracks tracks.json --min-length 20

# Trayectorias entre 10 y 100 puntos
python main.py --tracks tracks.json --min-length 10 --max-length 100
```

### Combinar Múltiples Archivos

```bash
python main.py --tracks track1.json track2.json track3.json --mode 2d
```

Todas las trayectorias se animarán en el mismo canvas.

## 📹 Exportación

### Exportar a Video MP4

```bash
python main.py --tracks tracks.json --export output/animation.mp4 --fps 30 --dpi 150
```

**Requisito**: Tener `ffmpeg` instalado y en el PATH.

```bash
# Windows (con chocolatey)
choco install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### Exportar Frames Individuales

```bash
python main.py --tracks tracks.json --export-frames output/frames/
```

Genera frames PNG numerados: `frame_000000.png`, `frame_000001.png`, ...

Útil para post-procesamiento o crear videos con ffmpeg manualmente:

```bash
ffmpeg -framerate 30 -i output/frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p output/video.mp4
```

## 📊 Estadísticas

```bash
python main.py --tracks tracks.json --stats
```

Muestra estadísticas detalladas antes de animar:
- Total de trayectorias y frames
- Clases presentes
- Velocidades (promedio, mínima, máxima)
- Distancias recorridas
- Sinuosidad (cuán serpenteantes son las trayectorias)
- Distribución de direcciones
- Distribución de patrones de movimiento

Ejemplo de salida:

```
======================================================================
ESTADISTICAS DE TRAYECTORIAS
======================================================================
Total: 150 trayectorias
Frames: 0 - 500 (501 total)
Clases: car, truck, bus, motorcycle

Velocidad promedio: 5.23 px/frame
Velocidad maxima: 15.67 px/frame

Distancia total recorrida: 75432.5 px
Distancia promedio: 502.9 px/trayectoria

Sinuosidad promedio: 1.15

Distribucion de direcciones:
  north       :   45 (30.0%)
  south       :   42 (28.0%)
  east        :   30 (20.0%)
  west        :   25 (16.7%)
  northeast   :    8 ( 5.3%)

Distribucion de patrones:
  straight    :  120 (80.0%)
  left        :   15 (10.0%)
  right       :   10 ( 6.7%)
  u_turn      :    3 ( 2.0%)
  complex     :    2 ( 1.3%)
======================================================================
```

## 🔬 Uso Programático

### Ejemplo en Python

```python
from parser import TrajectoryParser
from trajectories import TrajectoryManager
from animator import TrajectoryAnimator

# Cargar trayectorias
parser = TrajectoryParser()
parser.load_from_json("tracks.json")

# Filtrar solo autos
parser.filter_by_class(['car'])

# Crear gestor con colores por dirección
manager = TrajectoryManager(
    trajectories=parser.trajectories,
    color_mode='direction',
    calculate_metrics=True
)

# Obtener estadísticas
stats = manager.get_summary_stats()
print(f"Total: {stats['total_trajectories']} trayectorias")

# Crear animador
animator = TrajectoryAnimator(
    trajectory_manager=manager,
    mode='2d',
    trail_length=15,
    show_ids=True
)

# Animar
animator.animate(fps=30, speed=1.5, show_trails=True)

# O exportar
animator.export_video("output.mp4", fps=30, dpi=150)
```

### Acceso a Trayectorias Activas por Frame

```python
from trajectories import TrajectoryManager

# ... setup manager ...

# Obtener trayectorias activas en frame 100
active = manager.get_active_at_frame(100)

for track in active:
    print(f"Track {track['track_id']}: clase={track['clase']}, pos={track['position']}")
    if 'metrics' in track:
        print(f"  Velocidad: {track['metrics']['speed']:.2f} px/frame")
        print(f"  Dirección: {track['metrics']['direction']}")
```

## 📐 Canvas Infinito

El canvas se ajusta **automáticamente** a los límites de los datos:

```python
# parser.py calcula bounds dinámicamente
def _calculate_bounding_box(self):
    all_x = []
    all_y = []
    for traj in self.trajectories:
        for pos in traj['positions']:
            all_x.append(pos[0])
            all_y.append(pos[1])

    self.bounding_box = BoundingBox(
        min_x=min(all_x),
        max_x=max(all_x),
        min_y=min(all_y),
        max_y=max(all_y)
    )
```

**No hay dimensiones fijas de canvas**. El sistema visualiza cualquier escala de datos.

## 🎨 Personalización de Colores

Edita los esquemas de color en `trajectories.py`:

```python
COLOR_SCHEMES = {
    'class': {
        'car': '#3498db',      # Cambiar a tu color preferido
        'truck': '#e74c3c',
        # ...
    },
    # ...
}
```

## 🐛 Solución de Problemas

### Error: "No module named 'parser'"

Asegúrate de ejecutar desde el directorio `animation/`:

```bash
cd animation
python main.py --tracks tracks.json
```

### Error: "ffmpeg not found" al exportar video

Instala ffmpeg:
- Windows: `choco install ffmpeg` o descarga desde https://ffmpeg.org/
- Linux: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

### Animación muy lenta

Reduce el número de trayectorias o la longitud de trails:

```bash
python main.py --tracks tracks.json --trails 5 --min-length 20
```

### Canvas muy pequeño o muy grande

El canvas se ajusta automáticamente. Si las trayectorias tienen coordenadas muy dispersas, considera filtrar outliers o revisar los datos.

## 🔄 Integración con Pipeline Principal

El sistema principal (`yolo_carla_pipeline/main.py`) genera archivos `tracks.json` compatibles:

```bash
# 1. Generar trayectorias con pipeline principal
cd yolo_carla_pipeline
python main.py --pkl ../data/pkls/Gx010322.pkl --output output/

# 2. Animar trayectorias generadas
cd animation
python main.py --tracks ../output/trajectories/Gx010322_tracks.json --mode 2d --stats
```

## 📚 Formato de Entrada (JSON)

El sistema espera archivos JSON con esta estructura:

```json
[
  {
    "track_id": 1,
    "clase": "car",
    "positions": [[x1, y1], [x2, y2], ...],
    "frames": [0, 1, 2, ...],
    "length": 100,
    "duration_frames": 100,
    "avg_confidence": 0.95
  },
  ...
]
```

Campos requeridos:
- `track_id`: ID único de la trayectoria
- `clase`: Clase del objeto (car, truck, bus, etc.)
- `positions`: Lista de coordenadas [x, y]
- `frames`: Lista de números de frame correspondientes

Campos opcionales:
- `length`: Longitud de la trayectoria
- `duration_frames`: Duración en frames
- `avg_confidence`: Confianza promedio de detecciones

## 🚦 Próximas Funcionalidades

- [ ] Georeferenciación opcional (integración con `modules/map_overlay.py`)
- [ ] Exportación a formatos 3D (OBJ, PLY)
- [ ] Análisis de flujo vehicular por ROIs
- [ ] Detección automática de colisiones/near-misses
- [ ] Soporte para WebGL/plotly para animaciones web interactivas
- [ ] Modo comparación (visualizar múltiples archivos lado a lado)

## 📄 Licencia

Parte del proyecto `proyecto_bogota_traffic`.

## 👤 Autor

Sistema de animación desarrollado como parte del pipeline YOLOv8 + SORT para análisis de tráfico.
