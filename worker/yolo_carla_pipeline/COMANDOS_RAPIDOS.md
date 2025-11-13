# ⚡ Comandos Rápidos - Referencia

## 🎯 Pipeline Principal

### Procesar PKL
```bash
cd yolo_carla_pipeline
python main.py --pkl ../data/pkls/Gx010322.pkl --output output/
```

### Procesar con filtros
```bash
python main.py --pkl ../data/pkls/Gx010322.pkl \
  --confidence 0.6 \
  --classes car truck bus \
  --output output_filtered/
```

---

## 🗺️ Sistema de Visualización (Modules)

### Generar Mapa Interactivo (OpenStreetMap)
```bash
cd modules
python map_overlay.py ../output/trajectories/tracks.json --heatmap
# Abre: output/map.html
```

### Visualización Canvas Relativo
```bash
python canvas_visualizer.py ../output/trajectories/tracks.json
```

### Crear Calibración GPS
```bash
python helpers.py
# Edita: config/calibration.json con GPS real
```

---

## 🎬 Sistema de Animación (Animation)

### Animación Interactiva Básica
```bash
cd animation
python main.py --tracks ../output_gx010322/trajectories/Gx010322_tracks.json
```

### Con Estadísticas Previas
```bash
python main.py --tracks tracks.json --stats
```

### Solo Autos, Coloreado por Velocidad
```bash
python main.py --tracks tracks.json \
  --classes car \
  --color-mode speed \
  --trails 20
```

### Vista 3D
```bash
python main.py --tracks tracks.json \
  --mode 3d \
  --classes car truck \
  --min-length 30
```

### Exportar a Video MP4
```bash
python main.py --tracks tracks.json \
  --classes car truck \
  --color-mode direction \
  --export output/animation.mp4 \
  --fps 30 \
  --dpi 150 \
  --trails 15
```

### Exportar Frames PNG
```bash
python main.py --tracks tracks.json \
  --export-frames output/frames/ \
  --fps 30
```

---

## 🎨 Modos de Coloración

```bash
--color-mode class        # Por tipo (car, truck, bus...)
--color-mode direction    # Por dirección (N, S, E, W...)
--color-mode speed        # Por velocidad (lento → rápido)
--color-mode pattern      # Por patrón (recto, giro, u-turn...)
```

---

## 🔍 Filtros Comunes

```bash
# Solo vehículos grandes
--classes truck bus

# Solo vulnerables
--classes motorcycle bicycle person

# Trayectorias largas
--min-length 50

# Rango específico
--min-length 30 --max-length 100
```

---

## ⚙️ Controles de Animación

```bash
--speed 0.5              # Cámara lenta
--speed 2.0              # 2x velocidad
--trails 30              # Estelas largas
--trails 0               # Sin estelas
--fps 60                 # Alta frecuencia
--show-ids               # Mostrar IDs de tracks
--show-full-trajectories # Mostrar trayectorias completas
```

---

## 🔄 Workflow Completo

```bash
# 1. Procesar PKL
cd yolo_carla_pipeline
python main.py --pkl ../data/pkls/VIDEO.pkl --output output/

# 2. Ver en mapa
cd modules
python map_overlay.py ../output/trajectories/VIDEO_tracks.json --heatmap
# Abre map.html en navegador

# 3. Animar
cd ../animation
python main.py --tracks ../output/trajectories/VIDEO_tracks.json \
  --color-mode speed \
  --stats \
  --export ../output/animation.mp4
```

---

## 🛠️ Instalación de Dependencias

### Python
```bash
pip install folium matplotlib pillow numpy
```

### ffmpeg (para exportar video)
```bash
# Windows (con chocolatey)
choco install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

---

## 📊 Tests Rápidos

### Test de Parser
```bash
cd animation
python parser.py ../output/trajectories/tracks.json
```

### Test de Métricas
```bash
python trajectories.py ../output/trajectories/tracks.json --color-mode direction
```

### Test de Animador (10 segundos)
```bash
timeout 10 python main.py --tracks ../output/trajectories/tracks.json --classes car
```

---

## 🐛 Solución Rápida de Problemas

### "No module named 'parser'"
```bash
# Ejecuta desde el directorio correcto
cd animation
python main.py ...
```

### "ffmpeg not found"
```bash
# Instala ffmpeg (ver arriba)
# O exporta frames en lugar de video:
python main.py --tracks tracks.json --export-frames frames/
```

### Animación lenta
```bash
# Reduce carga
python main.py --tracks tracks.json \
  --classes car \
  --min-length 50 \
  --trails 5
```

---

## 📂 Archivos Importantes

```
yolo_carla_pipeline/
├── main.py                          # Pipeline principal
├── SISTEMA_COMPLETO.md              # Documentación completa
├── COMANDOS_RAPIDOS.md              # Este archivo
│
├── modules/                         # Sistema de visualización
│   ├── map_overlay.py               # → map.html
│   ├── canvas_visualizer.py         # → PNG
│   └── helpers.py                   # Transformaciones
│
├── animation/                       # Sistema de animación
│   ├── main.py                      # CLI principal
│   ├── README.md                    # Docs completas
│   └── QUICKSTART.md                # Guía rápida
│
├── config/
│   └── calibration.json             # Calibración GPS/CARLA
│
└── output*/
    └── trajectories/
        └── *_tracks.json            # Trayectorias procesadas
```

---

## 📖 Documentación

- **Visión general**: `SISTEMA_COMPLETO.md`
- **Animación completa**: `animation/README.md`
- **Guía rápida animación**: `animation/QUICKSTART.md`
- **Este archivo**: Comandos de referencia

---

## ✅ Checklist de Uso

- [ ] Procesar PKL con pipeline principal
- [ ] Revisar `output/trajectories/tracks.json` generado
- [ ] Generar mapa interactivo (opcional)
- [ ] Editar `config/calibration.json` con GPS real (para mapa)
- [ ] Animar con `animation/main.py`
- [ ] Exportar video si es necesario
- [ ] Analizar estadísticas con `--stats`

---

**Copiar y adaptar estos comandos según tu caso de uso.**
