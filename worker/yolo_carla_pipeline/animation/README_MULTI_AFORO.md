# Sistema Multi-Aforo - Dashboard de Tráfico Integrado

Sistema completo para integrar múltiples aforos (puntos de conteo de tráfico) en un solo dashboard animado con trayectorias diferenciadas por colores y emojis según la clase de vehículo.

## 🎯 Características Principales

- **Vista Unificada**: Múltiples aforos en el mismo lienzo/canvas
- **Animación en Tiempo Real**: Vehículos moviéndose con emojis (🚗🚚🚌🏍️🚴🚶)
- **Colores por Clase**: Cada tipo de vehículo tiene su color de trayectoria
- **Filtros Avanzados**: Por aforo y por categoría de vehículo
- **Base de Datos**: Persistencia de datos para análisis histórico
- **Escalable**: Agrega nuevos aforos fácilmente
- **Alto Rendimiento**: Optimizado para manejar miles de trayectorias

## 📁 Archivos del Sistema

```
animation/
├── build_multi_aforo_system.py          # ⭐ Script maestro (todo-en-uno)
├── combine_aforos.py                    # Combina múltiples JSONs de trayectorias
├── create_multi_aforo_dashboard.py      # Genera el dashboard HTML
├── persist_to_database.py               # Guarda en PostgreSQL
├── create_demo_aforo.py                 # Crea aforos de demo
└── README_MULTI_AFORO.md                # Esta documentación

config/
└── aforos_config.json                   # Configuración de todos los aforos

modules/output/
└── multi_aforo_dashboard.html           # Dashboard generado
```

## 🚀 Uso Rápido

### Opción 1: Script Maestro (Recomendado)

```bash
cd yolo_carla_pipeline/animation

# Generar dashboard con configuración por defecto
python build_multi_aforo_system.py

# Con opciones personalizadas
python build_multi_aforo_system.py --sample-size 800 --save-db
```

### Opción 2: Paso a Paso

```bash
# 1. Combinar aforos
python combine_aforos.py --output combined_aforos.json --sample-size 800

# 2. Generar dashboard
python create_multi_aforo_dashboard.py combined_aforos.json ../modules/output/multi_aforo_dashboard.html

# 3. (Opcional) Guardar en base de datos
python persist_to_database.py combined_aforos.json
```

## 🎨 Colores y Emojis por Clase

El sistema diferencia automáticamente cada tipo de vehículo:

| Clase | Emoji | Color Trayectoria | Código Hex |
|-------|-------|-------------------|------------|
| Car (Carro) | 🚗 | Azul | #3498db |
| Truck (Camión) | 🚚 | Rojo | #e74c3c |
| Bus | 🚌 | Morado | #9b59b6 |
| Motorcycle (Moto) | 🏍️ | Naranja | #f39c12 |
| Bicycle (Bici) | 🚴 | Verde | #2ecc71 |
| Person (Peatón) | 🚶 | Turquesa | #1abc9c |

**Nota**: Los colores se aplican a las **trayectorias** (líneas), mientras que los **emojis** representan el vehículo moviéndose.

## 📝 Cómo Agregar un Nuevo Aforo

### Paso 1: Procesar el Video

Procesa tu nuevo video con YOLO para obtener el archivo JSON de trayectorias:

```bash
cd yolo_carla_pipeline

# Procesar video nuevo
python main.py --pkl ../data/pkls/NUEVO_VIDEO.pkl --output output_nuevo
```

Esto genera: `output_nuevo/trajectories/tracks.json`

### Paso 2: Configurar el Aforo

Edita `config/aforos_config.json` y agrega tu nuevo aforo:

```json
{
  "id": "aforo_003",
  "nombre": "Intersección Sur",
  "video_source": "NUEVO_VIDEO.MP4",
  "tracks_file": "output_nuevo/trajectories/tracks.json",
  "offset_x": 0,
  "offset_y": 1000,
  "activo": true,
  "color_tema": "#2ecc71",
  "descripcion": "Tercer aforo - Intersección sur con tráfico moderado"
}
```

**Parámetros importantes:**
- `id`: Identificador único (ej: aforo_003, aforo_004, etc.)
- `nombre`: Nombre descriptivo para mostrar en el dashboard
- `tracks_file`: Ruta relativa al JSON de trayectorias (desde `yolo_carla_pipeline/`)
- `offset_x`, `offset_y`: Posición en el canvas (en píxeles)
- `activo`: `true` para incluirlo, `false` para desactivarlo
- `color_tema`: Color hexadecimal para identificar visualmente el aforo en la leyenda

**💡 Tip para Offsets:**
```
Primer aforo:        (0, 0)       ← Arriba izquierda
Segundo a la derecha: (1500, 0)    ← Misma altura, a la derecha
Tercero abajo:       (0, 1000)   ← Debajo del primero
Cuarto diagonal:     (1500, 1000) ← Abajo derecha
```

### Paso 3: Regenerar el Sistema

```bash
cd yolo_carla_pipeline/animation
python build_multi_aforo_system.py
```

¡Listo! El nuevo aforo se integra automáticamente en el dashboard.

## 🗄️ Base de Datos

### Estructura de Tablas

El sistema crea automáticamente las siguientes tablas en PostgreSQL:

1. **aforos**: Información de cada punto de aforo
   - Columnas: id, nombre, offset_x, offset_y, color_tema, activo, etc.

2. **sesiones_analisis**: Sesiones de procesamiento de video
   - Columnas: id, aforo_id, fecha_analisis, num_trayectorias, etc.

3. **trayectorias**: Todas las trayectorias detectadas
   - Columnas: id, sesion_id, aforo_id, track_id, clase, positions, velocidad_promedio, etc.

4. **estadisticas_aforo**: Estadísticas agregadas por aforo
   - Columnas: id, aforo_id, fecha, total_vehiculos, por_clase, etc.

### Guardar en Base de Datos

```bash
# Al ejecutar el script maestro
python build_multi_aforo_system.py --save-db

# O manualmente
python persist_to_database.py combined_aforos.json
```

### Configuración de Base de Datos

Edita `config/aforos_config.json` → `configuracion_global` → `base_de_datos`:

```json
{
  "host": "localhost",
  "puerto": 5432,
  "nombre_db": "bogota_traffic",
  "usuario": "postgres",
  "password": "bogota_traffic_2024_secure"
}
```

### Consultas SQL de Ejemplo

```sql
-- Contar vehículos por aforo y clase
SELECT
    aforo_id,
    clase,
    COUNT(*) as total
FROM trayectorias
GROUP BY aforo_id, clase
ORDER BY aforo_id, total DESC;

-- Velocidad promedio por aforo
SELECT
    aforo_id,
    AVG(velocidad_promedio) as vel_promedio,
    MAX(velocidad_promedio) as vel_maxima
FROM trayectorias
WHERE velocidad_promedio > 0
GROUP BY aforo_id;

-- Sesiones procesadas
SELECT
    aforo_id,
    COUNT(*) as num_sesiones,
    SUM(num_trayectorias) as total_trayectorias
FROM sesiones_analisis
GROUP BY aforo_id;

-- Distribución de clases por aforo
SELECT
    aforo_id,
    clase,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY aforo_id), 2) as porcentaje
FROM trayectorias
GROUP BY aforo_id, clase
ORDER BY aforo_id, cantidad DESC;
```

## 🎮 Uso del Dashboard

### Controles Principales

- **▶ Play / ⏸ Pause / ↺ Reset**: Controlar la animación
- **Velocidad**: Slider de 0.25x a 5x
- **Barra de progreso**: Muestra el avance de la simulación (%)

### Filtros

**Por Aforo:**
- Checkboxes para activar/desactivar cada intersección
- Ver cada aforo por separado o combinados

**Por Categoría:**
- Filtra por tipo de vehículo (car, truck, bus, etc.)
- Múltiples categorías pueden estar activas simultáneamente

### Navegación

- **Zoom**: Rueda del mouse o botones +/- en la esquina
- **Pan**: Click y arrastra para mover el canvas en cualquier dirección
- **Reset Zoom**: Botón ⟲ para volver a la vista completa

### Opciones de Visualización

- **Mostrar trayectorias**: Ver/ocultar líneas de trayectorias (con colores por clase)
- **Mostrar IDs**: Ver/ocultar identificadores de vehículos
- **Mostrar cuadrícula**: Grid de referencia para orientación
- **Mostrar nombres de aforos**: Etiquetas de cada intersección

### Leyenda

En la esquina superior derecha se muestra:
- Nombre de cada aforo activo
- Color tema del aforo
- Número de trayectorias

## 📊 Casos de Uso

### Caso 1: Análisis de una Intersección

```bash
# Activar solo un aforo en aforos_config.json
# Ejecutar dashboard
python build_multi_aforo_system.py --sample-size 1500
```

### Caso 2: Comparación de Múltiples Intersecciones

```json
// Activar múltiples aforos en aforos_config.json
{
  "aforo_001": { "activo": true },
  "aforo_002": { "activo": true },
  "aforo_003": { "activo": true }
}
```

```bash
python build_multi_aforo_system.py --sample-size 800
```

### Caso 3: Análisis Histórico con Base de Datos

```bash
# Guardar todos los datos procesados
python build_multi_aforo_system.py --save-db

# Consultar en PostgreSQL
psql -d bogota_traffic
SELECT aforo_id, clase, COUNT(*) FROM trayectorias GROUP BY aforo_id, clase;
```

## 🔧 Parámetros del Script Maestro

```bash
python build_multi_aforo_system.py [opciones]

Opciones:
  --sample-size N    Número máximo de trayectorias por aforo (default: 1000)
  --save-db          Guardar en base de datos PostgreSQL
  --no-open          No abrir el dashboard automáticamente
  -h, --help         Mostrar ayuda
```

**Ejemplos:**

```bash
# Dashboard básico
python build_multi_aforo_system.py

# Con más trayectorias
python build_multi_aforo_system.py --sample-size 1500

# Guardar en BD sin abrir navegador
python build_multi_aforo_system.py --save-db --no-open
```

## 📈 Optimización y Rendimiento

### Para Datasets Grandes

```bash
# Reducir trayectorias para mejor rendimiento
python build_multi_aforo_system.py --sample-size 500
```

### Para Mejor Calidad Visual

```bash
# Usar más trayectorias (puede ser más lento)
python build_multi_aforo_system.py --sample-size 2000
```

### Rendimiento del Dashboard

El dashboard está optimizado con:
- **Canvas en 2 capas**: Fondo estático + animación dinámica
- **requestAnimationFrame**: Para animaciones fluidas a 60 FPS
- **Renderizado condicional**: Solo redibuja cuando hay cambios
- **Interpolación**: Movimiento suave entre frames

## 🐛 Solución de Problemas

### Error: "Archivo no encontrado"

Verifica que la ruta en `tracks_file` sea correcta:
```bash
# La ruta debe ser relativa a yolo_carla_pipeline/
"tracks_file": "output_gx010322/trajectories/Gx010322_tracks.json"
```

### Error de Base de Datos

1. Verifica que PostgreSQL esté corriendo:
```bash
# Windows
net start postgresql-x64-14

# Linux/Mac
sudo service postgresql status
```

2. Verifica las credenciales en `aforos_config.json`

3. Crea la base de datos si no existe:
```bash
createdb bogota_traffic
```

### Dashboard No Se Ve Bien

- Usa Chrome o Firefox (navegadores modernos)
- Dale click a "Reset Zoom" (⟲) para recentrar
- Desactiva algunos aforos si hay demasiados
- Reduce `--sample-size` si está muy lento

### Procesamiento Muy Lento

- Los PKL con >300k detecciones pueden tardar varios minutos
- Usa `--sample-size` más bajo (500-800)
- Cierra otros programas para liberar RAM

## 🎯 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│  PKL Files (YOLO Detections)                       │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  main.py (Procesa PKL → JSON Trajectories)         │
│  - Tracking                                         │
│  - Análisis                                         │
│  - Métricas                                         │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  aforos_config.json (Configuración)                 │
│  - Define aforos                                    │
│  - Offsets espaciales                              │
│  - Estado (activo/inactivo)                        │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  combine_aforos.py                                  │
│  - Combina múltiples aforos                        │
│  - Aplica offsets                                  │
│  - Agrega colores y emojis por clase              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  create_multi_aforo_dashboard.py                    │
│  - Genera HTML interactivo                         │
│  - Canvas 2 capas                                  │
│  - Controles y filtros                             │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Dashboard Multi-Aforo (HTML + JavaScript)          │
│  - Animación en tiempo real                        │
│  - Zoom, pan, filtros                              │
│  - Trayectorias con colores por clase              │
└─────────────────────────────────────────────────────┘
                 │
                 ▼ (opcional)
┌─────────────────────────────────────────────────────┐
│  persist_to_database.py → PostgreSQL                │
│  - Persistencia de datos                           │
│  - Análisis histórico                              │
└─────────────────────────────────────────────────────┘
```

## 📚 Formato de Datos

### JSON de Trayectorias (Input)

```json
[
  {
    "track_id": 0,
    "clase": "car",
    "length": 597,
    "duration_frames": 763,
    "avg_confidence": 0.69,
    "positions": [[28.5, 271.5], [29.0, 272.0], ...],
    "frames": [1, 2, 3, ...]
  }
]
```

### JSON Combinado (Output de combine_aforos.py)

```json
{
  "trajectories": [
    {
      "track_id": "aforo_001_0",
      "track_id_original": 0,
      "clase": "car",
      "positions": [[28.5, 271.5], [29.0, 272.0], ...],
      "frames": [1, 2, 3, ...],
      "aforo_id": "aforo_001",
      "aforo_offset": [0, 0],
      "color": "#3498db",
      "emoji": "🚗"
    }
  ],
  "aforos": [
    {
      "id": "aforo_001",
      "nombre": "Intersección Principal",
      "offset_x": 0,
      "offset_y": 0,
      "color_tema": "#3498db",
      "num_trayectorias": 846
    }
  ],
  "metadata": {
    "total_aforos": 2,
    "total_trayectorias": 1688
  }
}
```

## 🎓 Próximos Pasos

1. **Procesar más videos** de diferentes intersecciones
2. **Activar nuevos aforos** en la configuración
3. **Analizar patrones** de tráfico en la base de datos
4. **Exportar visualizaciones** para reportes
5. **Integrar con mapas reales** (OpenStreetMap, Google Maps)

---

**¡El sistema está listo para crecer! Cada nuevo video que proceses se integra automáticamente al mapa de tráfico.**
