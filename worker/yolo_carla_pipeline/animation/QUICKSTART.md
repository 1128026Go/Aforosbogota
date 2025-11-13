# 🚀 Guía Rápida - Sistema de Animación

## ✅ Sistema Completado

Se ha desarrollado un **sistema completo de animación** con canvas infinito (sin mapa de fondo) que incluye:

### 📦 Módulos Implementados

1. **`parser.py`** - Parser de trayectorias JSON
   - Carga archivos individuales o múltiples
   - Validación de estructura
   - Cálculo dinámico de bounding box
   - Acceso frame-por-frame

2. **`trajectories.py`** - Gestor de trayectorias y métricas
   - Cálculo automático de velocidad, aceleración, dirección
   - Detección de patrones de movimiento (recto, izquierda, derecha, u-turn, complejo)
   - Asignación de colores por clase/dirección/velocidad/patrón
   - Estadísticas completas

3. **`animator.py`** - Motor de animación
   - Animación frame-por-frame con FuncAnimation de matplotlib
   - Controles interactivos (Play/Pause, Reset, Speed slider)
   - Modos 2D y 3D
   - Estelas configurables
   - Exportación a video MP4 o frames PNG

4. **`main.py`** - CLI orquestador
   - Interfaz de línea de comandos completa
   - Filtros por clase, longitud, etc.
   - Múltiples modos de visualización
   - Exportación flexible

## 🎯 Prueba Realizada con Datos Reales

✅ **Probado exitosamente** con `Gx010322_tracks.json`:
- **3381 trayectorias** totales
- **145,919 frames** (≈81 minutos de video a 30 FPS)
- **5 clases**: car, truck, bus, motorcycle, person
- **Canvas dinámico**: 1257 x 609.5 píxeles (ajustado a datos)

### Resultados de Prueba

```
Total trayectorias: 3381
Clases: car, person, bus, truck, motorcycle
Frames: 2 - 145920 (145919 total)

Canvas Bounds:
  X: [9.5, 1266.5] (1257.0 px width)
  Y: [88.0, 697.5] (609.5 px height)

Métricas:
  Velocidad promedio: 7.47 px/frame
  Velocidad máxima: 75.48 px/frame
  Distancia total: 1,294,149.6 px
  Sinuosidad promedio: 5.42

Distribución de direcciones:
  east: 1314    west: 1316
  north: 169    south: 86
  (bidireccional como esperado)

Patrones detectados:
  straight: 1235
  u_turn: 1156
  right: 471
  left: 413
  complex: 106
```

## 🚀 Comandos de Uso Inmediato

### 1. Animación Interactiva Básica (Solo Autos)

```bash
cd animation
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json --classes car --min-length 30 --stats
```

**Resultado**: Abre ventana con animación de autos, estadísticas previas, controles de reproducción.

### 2. Visualización por Velocidad (Colormap)

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json --color-mode speed --classes car truck --trails 20
```

**Resultado**:
- 🔵 Azul: muy lento
- 🟢 Verde: lento
- 🟠 Naranja: medio
- 🔴 Rojo: rápido

### 3. Visualización por Dirección

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json --color-mode direction --mode 2d
```

**Resultado**: Cada dirección cardinal tiene un color diferente.

### 4. Vista 3D Espacio-Temporal

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json --mode 3d --classes car --min-length 50
```

**Resultado**: Canvas 3D donde Z = tiempo. Visualiza evolución temporal.

### 5. Exportar a Video MP4

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json \
  --classes car truck \
  --color-mode speed \
  --export output/traffic_animation.mp4 \
  --fps 30 \
  --dpi 150 \
  --trails 15
```

**Requisito**: Tener `ffmpeg` instalado.

**Windows**:
```bash
choco install ffmpeg
```

**Linux**:
```bash
sudo apt-get install ffmpeg
```

### 6. Exportar Frames PNG

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json \
  --classes car \
  --min-length 30 \
  --export-frames output/frames/ \
  --fps 30
```

**Resultado**: Crea `frame_000000.png`, `frame_000001.png`, etc.

### 7. Análisis Completo con Estadísticas

```bash
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json \
  --stats \
  --color-mode pattern \
  --mode 2d \
  --trails 10 \
  --show-full-trajectories
```

**Resultado**: Muestra estadísticas detalladas antes de animar, luego visualiza con trayectorias completas de fondo.

## 📊 Filtros Útiles

### Filtrar por Clase
```bash
--classes car                          # Solo autos
--classes car truck bus                # Vehículos grandes
--classes motorcycle bicycle person    # Vulnerables
```

### Filtrar por Longitud
```bash
--min-length 50                        # Mínimo 50 puntos
--max-length 200                       # Máximo 200 puntos
--min-length 30 --max-length 100       # Entre 30 y 100
```

### Ajustar Calidad Visual
```bash
--trails 0                             # Sin estelas
--trails 30                            # Estelas largas
--marker-size 150                      # Marcadores grandes
--show-ids                             # Mostrar IDs de tracks
--show-full-trajectories               # Mostrar trayectorias completas
```

### Controlar Velocidad
```bash
--speed 0.5                            # Cámara lenta
--speed 2.0                            # 2x velocidad
--speed 5.0                            # 5x velocidad
--fps 60                               # 60 FPS (más suave)
```

## 🎨 Modos de Coloración Explicados

### `--color-mode class` (Default)
Colores por tipo de objeto:
- 🔵 car → Azul
- 🔴 truck → Rojo
- 🟣 bus → Morado
- 🟠 motorcycle → Naranja
- 🟢 bicycle → Verde
- 🔷 person → Cyan

### `--color-mode direction`
Colores por dirección de movimiento:
- 🔵 Norte → Azul
- 🔴 Sur → Rojo
- 🟢 Este → Verde
- 🟠 Oeste → Naranja
- (+ direcciones intermedias)

### `--color-mode speed`
Colores por velocidad:
- 🔵 0-2 px/frame → Azul (muy lento)
- 🟢 2-5 px/frame → Verde (lento)
- 🟠 5-10 px/frame → Naranja (medio)
- 🔴 10+ px/frame → Rojo (rápido)

### `--color-mode pattern`
Colores por patrón de trayectoria:
- 🔵 Recto → Azul
- 🟢 Giro izquierda → Verde
- 🟠 Giro derecha → Naranja
- 🔴 U-turn → Rojo
- 🟣 Complejo → Morado

## 🔧 Controles Interactivos

Cuando ejecutas animación interactiva (sin `--export`):

- **Botón "Play/Pause"**: Pausar/reanudar animación
- **Botón "Reset"**: Volver al frame inicial
- **Slider "Speed"**: Ajustar velocidad en tiempo real (0.1x - 5.0x)
- **Información en pantalla**: Frame actual, progreso %, trayectorias activas

## 📈 Comparación de Rendimiento

### Dataset Grande (3381 trayectorias, 145K frames)
- **Carga inicial**: ~2 segundos
- **Cálculo de métricas**: ~5-10 segundos
- **Animación interactiva**: Fluida con filtros aplicados

### Recomendaciones para Grandes Datasets
```bash
# Opción 1: Filtrar antes de animar
--classes car --min-length 30        # Reduce a ~1300 trayectorias

# Opción 2: Reducir trails
--trails 5                           # Menos procesamiento

# Opción 3: Exportar directamente (más eficiente que interactivo)
--export video.mp4                   # No renderiza en pantalla
```

## 🐛 Solución de Problemas

### "No module named 'parser'"
```bash
# Asegúrate de estar en el directorio correcto
cd animation
python main.py --tracks tracks.json
```

### "ffmpeg not found" al exportar
```bash
# Instalar ffmpeg
choco install ffmpeg          # Windows
sudo apt install ffmpeg       # Linux
brew install ffmpeg           # macOS
```

### Animación muy lenta
```bash
# Reducir carga
python main.py --tracks tracks.json --classes car --min-length 50 --trails 5
```

### Canvas muy grande/pequeño
El canvas se ajusta automáticamente a los datos. Si parece extraño:
- Revisa los datos con `--stats`
- Verifica que las coordenadas sean píxeles (no lat/lon)

## 🔗 Integración con Pipeline Principal

El pipeline principal genera los archivos `*_tracks.json` compatibles:

```bash
# PASO 1: Generar trayectorias con pipeline principal
cd yolo_carla_pipeline
python main.py --pkl ../data/pkls/Gx010322.pkl --output output_gx010322/

# PASO 2: Animar trayectorias generadas
cd animation
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json --stats
```

## 📝 Próximos Pasos Sugeridos

1. **Experimentar con modos**:
   ```bash
   # Probar diferentes combinaciones
   python main.py --tracks TRACKS.json --color-mode direction --mode 3d
   python main.py --tracks TRACKS.json --color-mode speed --trails 30
   ```

2. **Crear videos temáticos**:
   ```bash
   # Video solo de camiones rápidos
   python main.py --tracks TRACKS.json --classes truck --color-mode speed --export trucks_fast.mp4
   ```

3. **Análisis de patrones**:
   ```bash
   # Ver solo U-turns (requiere filtro manual por ahora)
   python main.py --tracks TRACKS.json --color-mode pattern --stats
   ```

4. **Exportar múltiples vistas**:
   ```bash
   # Vista 2D
   python main.py --tracks TRACKS.json --mode 2d --export view_2d.mp4

   # Vista 3D
   python main.py --tracks TRACKS.json --mode 3d --export view_3d.mp4
   ```

## 🎓 Uso Programático (Python)

```python
from parser import TrajectoryParser
from trajectories import TrajectoryManager
from animator import TrajectoryAnimator

# Cargar y filtrar
parser = TrajectoryParser()
parser.load_from_json("tracks.json")
parser.filter_by_class(['car'])

# Crear gestor
manager = TrajectoryManager(
    trajectories=parser.trajectories,
    color_mode='speed',
    calculate_metrics=True
)

# Ver estadísticas
stats = manager.get_summary_stats()
print(f"Velocidad promedio: {stats['speed_stats']['avg']:.2f}")

# Animar
animator = TrajectoryAnimator(manager, mode='2d', trail_length=15)
animator.animate(fps=30, speed=1.5, show_trails=True)

# O exportar
animator.export_video("output.mp4", fps=30, dpi=150)
```

## ✅ Checklist de Funcionalidades

- ✅ Canvas infinito (bounds dinámicos)
- ✅ Animación frame-por-frame
- ✅ Controles interactivos (Play/Pause/Reset/Speed)
- ✅ Múltiples modos de color (class/direction/speed/pattern)
- ✅ Vista 2D y 3D
- ✅ Estelas configurables
- ✅ Filtros por clase y longitud
- ✅ Exportación a video MP4
- ✅ Exportación a frames PNG
- ✅ Cálculo automático de métricas
- ✅ Detección de patrones de movimiento
- ✅ Estadísticas completas
- ✅ Soporte para múltiples archivos
- ✅ CLI completo y documentado

## 📄 Documentación Completa

Ver `README.md` para documentación exhaustiva de todas las funcionalidades.

---

**Sistema desarrollado y probado exitosamente con 3381 trayectorias reales.**
