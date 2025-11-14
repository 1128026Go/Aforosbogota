# Guía de Procesamiento de Videos - Recursos Limitados

## 🎯 Problema y Solución

### ❌ Problema
- **Error: "CUDA out of memory"** (memoria GPU insuficiente)
- **Video tarda demasiado** en procesarse
- **PC se congela** durante procesamiento

### ✅ Solución
He creado un **procesador optimizado** que funciona con:
- ✓ **CPU** (sin GPU NVIDIA)
- ✓ **GPU con poca memoria** (2-4 GB)
- ✓ **RAM limitada** (8 GB o menos)

---

## 📦 Herramientas Incluidas

### 1. **video_processor.py**
Script de línea de comandos para procesamiento optimizado

### 2. **video_processor_gui.py** ⭐ RECOMENDADO
GUI amigable con todas las opciones

### 3. **TrafficAnalyzer.exe**
Visor de resultados (NO procesa, solo visualiza)

---

## 🚀 Instalación

### Paso 1: Instalar Dependencias

```bash
# Si ya tienes el entorno virtual:
venv\Scripts\activate
pip install ultralytics psutil

# O desde cero:
pip install -r requirements.txt
```

### Paso 2: Descargar Modelo YOLO (Automático)
El modelo se descarga automáticamente la primera vez.

---

## 💻 Uso - GUI (RECOMENDADO)

### Iniciar GUI
```bash
python video_processor_gui.py
```

### Configuración para PC con Recursos Bajos

#### 1. **Modelo** → `yolov8n.pt (Nano)`
- Más rápido
- Menos memoria
- Buena precisión

#### 2. **Dispositivo** → `cpu`
- Si no tienes GPU NVIDIA
- O si tu GPU da error de memoria

#### 3. **Procesar 1 de cada N frames** → `2` o `3`
- 1 = Procesar todos (lento pero preciso)
- 2 = Procesar mitad (2x más rápido)
- 3 = Procesar un tercio (3x más rápido)

#### 4. **Resolución** → `480` o `640`
- 320 = Muy rápido, baja calidad
- 480 = Rápido, calidad media ⭐
- 640 = Balance (RECOMENDADO) ⭐
- 1280 = Lento, alta calidad

### Ejemplo Configuración Óptima (PC Baja Gama)
```
Modelo: yolov8n.pt
Dispositivo: cpu
Skip frames: 2
Resolución: 480
Confianza: 0.25
Tracking: ✓ Activado
```

---

## 🖥️ Uso - Línea de Comandos

### Procesamiento Básico (CPU)
```bash
python video_processor.py mi_video.mp4
```

### Procesamiento Rápido
```bash
python video_processor.py mi_video.mp4 --skip 3 --img-size 480
```

### Con GPU (si tienes)
```bash
python video_processor.py mi_video.mp4 --device cuda
```

### Todas las Opciones
```bash
python video_processor.py mi_video.mp4 \
  --model yolov8n.pt \
  --device cpu \
  --skip 2 \
  --img-size 640 \
  --conf 0.25 \
  --output detecciones.pkl
```

---

## ⚙️ Opciones de Configuración

### Modelos YOLO (de menor a mayor)

| Modelo | Velocidad | Precisión | Memoria | Recomendado Para |
|--------|-----------|-----------|---------|------------------|
| **yolov8n** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | 6 MB | PC baja gama ✓ |
| **yolov8s** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 22 MB | Balance |
| **yolov8m** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 52 MB | PC potente |
| **yolov8l** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 87 MB | Servidor |
| **yolov8x** | ⚡ | ⭐⭐⭐⭐⭐ | 136 MB | Máxima precisión |

**Recomendación: yolov8n para recursos bajos**

### Skip Frames

| Skip | Frames Procesados | Velocidad | Uso |
|------|-------------------|-----------|-----|
| 1 | 100% (todos) | 1x | Video fluido |
| 2 | 50% (mitad) | 2x ⭐ | Balance |
| 3 | 33% | 3x | Rápido |
| 5 | 20% | 5x | Muy rápido |
| 10 | 10% | 10x | Ultra rápido |

**Recomendación: 2-3 para recursos bajos**

### Resolución de Procesamiento

| Resolución | Velocidad | Calidad | RAM |
|------------|-----------|---------|-----|
| 320 | ⚡⚡⚡⚡⚡ | ⭐⭐ | Mínima |
| 480 | ⚡⚡⚡⚡ | ⭐⭐⭐ | Baja ⭐ |
| 640 | ⚡⚡⚡ | ⭐⭐⭐⭐ | Media ⭐ |
| 1280 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Alta |

**Recomendación: 480-640 para recursos bajos**

---

## 📊 Estimaciones de Tiempo

### Video de 1 minuto (1800 frames @ 30fps)

#### PC Baja Gama (CPU, 8GB RAM)
| Configuración | Tiempo | Resultado |
|---------------|--------|-----------|
| yolov8n, skip=1, 640px | ~15 min | Excelente |
| yolov8n, skip=2, 480px | ~5 min | Bueno ⭐ |
| yolov8n, skip=3, 480px | ~3 min | Aceptable |

#### PC Media (GPU 4GB, 16GB RAM)
| Configuración | Tiempo | Resultado |
|---------------|--------|-----------|
| yolov8s, cuda, skip=1, 640px | ~3 min | Excelente ⭐ |
| yolov8n, cuda, skip=2, 640px | ~1 min | Muy bueno |

#### PC Alta (GPU 8GB+, 32GB RAM)
| Configuración | Tiempo | Resultado |
|---------------|--------|-----------|
| yolov8m, cuda, skip=1, 1280px | ~5 min | Profesional |
| yolov8s, cuda, skip=1, 640px | ~1 min | Óptimo |

---

## 🔧 Solución de Problemas

### Error: "CUDA out of memory"

**Solución 1: Usar CPU**
```
Dispositivo: cpu
```

**Solución 2: Modelo más pequeño**
```
Modelo: yolov8n.pt (en vez de yolov8s o yolov8m)
```

**Solución 3: Resolución menor**
```
Resolución: 320 o 480 (en vez de 640)
```

### Error: "ultralytics not found"

```bash
pip install ultralytics
```

### Procesamiento muy lento

**Opción 1: Aumentar skip frames**
```
Skip frames: 3 o 5 (en vez de 1)
```

**Opción 2: Reducir resolución**
```
Resolución: 480 (en vez de 640)
```

**Opción 3: Modelo más rápido**
```
Modelo: yolov8n.pt (el más rápido)
```

### PC se congela

**Causa:** Memoria RAM insuficiente

**Solución:** Cerrar otros programas
```
- Cerrar navegador
- Cerrar aplicaciones pesadas
- Reiniciar PC antes de procesar
```

---

## 📈 Flujo de Trabajo Completo

### 1. Procesar Video
```bash
python video_processor_gui.py

# Configuración:
- Modelo: yolov8n.pt
- Dispositivo: cpu
- Skip frames: 2
- Resolución: 640

# Resultado: mi_video_detections.pkl
```

### 2. Visualizar Resultados
```bash
dist\TrafficAnalyzer.exe

# En la aplicación:
1. Cargar PKL → mi_video_detections.pkl
2. Cargar Video → mi_video.mp4 (opcional)
3. Navegar y analizar
```

### 3. Clasificar Zonas
```
1. Detectar zonas automáticamente (KMeans)
2. Editar zonas manualmente
3. Exportar configuración JSON
```

### 4. Integrar con Pipeline
```python
import json

with open('zones_config.json', 'r') as f:
    zones = json.load(f)

# Usar en tu sistema de aforo
```

---

## 💡 Tips y Trucos

### Para Máxima Velocidad
```
Modelo: yolov8n
Skip: 5
Resolución: 320
Tracking: Desactivado
```

### Para Máxima Calidad
```
Modelo: yolov8m
Skip: 1
Resolución: 1280
Tracking: Activado
```

### Balance (Recomendado)
```
Modelo: yolov8n
Skip: 2
Resolución: 640
Tracking: Activado
```

---

## 🎯 Recomendaciones por Tipo de PC

### PC Básica (Celeron, 4GB RAM, Sin GPU)
```yaml
Modelo: yolov8n
Dispositivo: cpu
Skip: 3
Resolución: 480
Tiempo estimado: ~10 min por minuto de video
```

### PC Media (i5, 8GB RAM, GPU integrada)
```yaml
Modelo: yolov8n
Dispositivo: cpu
Skip: 2
Resolución: 640
Tiempo estimado: ~5 min por minuto de video
```

### PC Buena (i7, 16GB RAM, GPU dedicada 4GB)
```yaml
Modelo: yolov8s
Dispositivo: cuda
Skip: 1
Resolución: 640
Tiempo estimado: ~2 min por minuto de video
```

### PC Potente (i9/Ryzen 9, 32GB RAM, GPU 8GB+)
```yaml
Modelo: yolov8m
Dispositivo: cuda
Skip: 1
Resolución: 1280
Tiempo estimado: ~5 min por minuto de video
```

---

## 📦 Archivos Generados

### mi_video_detections.pkl
Archivo principal con todas las detecciones
- Formato compatible con TrafficAnalyzer
- Contiene: detecciones, trayectorias, metadata

### mi_video_summary.json
Resumen del procesamiento
- Estadísticas
- Configuración usada
- Info del video

---

## 🔄 Workflow Típico

```
1. Grabar video
   ↓
2. Procesar con video_processor_gui.py
   ↓
3. Generar PKL
   ↓
4. Abrir TrafficAnalyzer.exe
   ↓
5. Cargar PKL + Video
   ↓
6. Clasificar zonas
   ↓
7. Exportar configuración
   ↓
8. Integrar con pipeline de aforo
```

---

## ❓ FAQ

### ¿Necesito GPU NVIDIA?
No. Puedes usar CPU, solo será más lento.

### ¿Cuánta RAM necesito?
Mínimo 4GB, recomendado 8GB+.

### ¿Qué tan largo puede ser el video?
Cualquier duración. Solo tomará más tiempo.

### ¿Puedo procesar múltiples videos?
Sí, uno a la vez. Procesa cada video y genera su PKL.

### ¿TrafficAnalyzer necesita GPU?
No. TrafficAnalyzer solo visualiza, no procesa.

### ¿Puedo pausar el procesamiento?
No actualmente. Planifica tiempo suficiente.

### ¿Los PKL generados son compatibles?
Sí, 100% compatibles con TrafficAnalyzer.

---

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Video de Cámara de Seguridad (1 hora)
```bash
python video_processor_gui.py

# Configuración:
- Modelo: yolov8n
- CPU
- Skip: 5 (procesar 1 de cada 5 frames)
- Resolución: 480

# Resultado: ~1 hora de procesamiento
# PKL con detecciones cada 5 frames (suficiente para aforo)
```

### Ejemplo 2: Video de Drone (5 minutos, alta calidad)
```bash
python video_processor_gui.py

# Configuración:
- Modelo: yolov8s
- CUDA (si tienes)
- Skip: 1 (todos los frames)
- Resolución: 1280

# Resultado: ~10 minutos procesamiento
# PKL con máxima calidad
```

### Ejemplo 3: Prueba Rápida
```bash
python video_processor.py test.mp4 --skip 10 --img-size 320

# Resultado: ~30 segundos para 1 min de video
# Solo para verificar que funciona
```

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en la GUI
2. Prueba con configuración más baja
3. Verifica que ultralytics esté instalado
4. Revisa que el video no esté corrupto

---

## ✅ Checklist Pre-Procesamiento

- [ ] ultralytics instalado (`pip install ultralytics`)
- [ ] Video en formato compatible (MP4, AVI, MOV)
- [ ] Suficiente espacio en disco (~igual al tamaño del video)
- [ ] Otros programas cerrados (liberar RAM)
- [ ] Tiempo disponible (estimar según tabla)
- [ ] Configuración seleccionada según tu PC

---

**¡Listo para procesar videos con recursos limitados!** 🚀
