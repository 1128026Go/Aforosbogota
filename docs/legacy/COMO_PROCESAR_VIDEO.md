# Cómo Procesar Tu Video (SIN CUDA)

## 🎯 Problema
- Tienes un video
- Necesitas convertirlo a PKL
- Te da error de CUDA
- **TrafficAnalyzer NO procesa videos (solo los visualiza)**

## ✅ Solución: Usar Procesador Simple

---

## 🚀 Método 1: Ultra Rápido (Batch File)

### Paso 1: Instalar ultralytics (Solo Primera Vez)
```bash
pip install ultralytics
```

### Paso 2: Procesar Video
```bash
# Doble click en:
procesar_video.bat

# Arrastrar tu video cuando lo pida
# Esperar...
# Listo! Se genera video_detections.pkl
```

---

## 🖥️ Método 2: Línea de Comandos

### Procesar Video
```bash
python procesar_video_simple.py mi_video.mp4
```

### Con Nombre Personalizado
```bash
python procesar_video_simple.py mi_video.mp4 resultado.pkl
```

---

## ⚙️ Configuración Automática

El script `procesar_video_simple.py` usa **configuración fija optimizada**:

```
✓ Modelo: yolov8n (más rápido)
✓ Dispositivo: CPU (SIN CUDA)
✓ Skip frames: 2 (procesa mitad)
✓ Resolución: 640px
✓ Tracking: Activado
```

**No necesitas configurar nada. Solo ejecuta y espera.**

---

## ⏱️ ¿Cuánto Tarda?

### Video de 1 Minuto (1800 frames)
- Skip=2 → Procesa 900 frames
- ~5-8 minutos en CPU
- Genera ~500KB PKL

### Video de 10 Minutos
- ~50-80 minutos en CPU
- Genera ~5MB PKL

### Video de 1 Hora
- ~5-8 horas en CPU
- Genera ~30MB PKL

**Tip**: Para videos largos, procesa de noche.

---

## 📊 Después de Procesar

### Paso 1: Abrir Visualizador
```bash
dist\TrafficAnalyzer.exe
```

### Paso 2: Cargar PKL Generado
```
1. Click "Cargar PKL"
2. Seleccionar: mi_video_detections.pkl
3. Ver detecciones y trayectorias
```

### Paso 3: Opcionalmente Cargar Video
```
1. Click "Cargar Video (Opcional)"
2. Seleccionar: mi_video.mp4
3. Ver video con detecciones superpuestas
```

---

## 🔍 Diferencias con video_processor_gui.py

| Característica | procesar_video_simple.py | video_processor_gui.py |
|----------------|--------------------------|------------------------|
| **Interfaz** | Línea de comandos | GUI amigable |
| **Configuración** | Fija (automática) | Manual (ajustable) |
| **CUDA** | ❌ NUNCA (solo CPU) | ✓ Opcional |
| **Complejidad** | Simple | Avanzado |
| **Recomendado** | ✓ Si tienes error CUDA | Si quieres control total |

---

## ✅ Ventajas del Script Simple

1. **Nunca usa CUDA** → No hay errores de GPU
2. **Configuración automática** → No tienes que pensar
3. **Un solo comando** → Más rápido de usar
4. **Funciona en cualquier PC** → Solo necesita CPU

---

## 📝 Ejemplo Completo

### 1. Procesar Video
```bash
# En la carpeta aforos:
python procesar_video_simple.py trafico.mp4

# Salida:
# ========================================
#   PROCESADOR DE VIDEO - MODO CPU
# ========================================
#
# ✓ Modelo cargado en CPU
# ⚙️ Procesando frames...
# [10/450] 2.2% - 23 detecciones
# [20/450] 4.4% - 48 detecciones
# ...
# ✓ Procesamiento completado!
# 💾 Guardando PKL: trafico_detections.pkl
# ✓ PKL guardado!
```

### 2. Visualizar Resultado
```bash
# Abrir visualizador
dist\TrafficAnalyzer.exe

# Cargar PKL
# Ver video + detecciones
```

---

## 🐛 Solución de Problemas

### "ultralytics not found"
```bash
pip install ultralytics
```

### "No module named 'torch'"
```bash
pip install torch torchvision
```

### Video no se puede abrir
```bash
# Verificar que el video no esté corrupto
# Probar abrir con VLC u otro reproductor
```

### Procesamiento interrumpido
```bash
# Ctrl+C detiene el proceso
# Puedes reanudar procesando desde el inicio
```

### Error al guardar PKL
```bash
# Verificar espacio en disco
# Verificar permisos de escritura
```

---

## 💡 Tips

### Tip 1: Procesar Videos Largos
```bash
# Para videos de más de 1 hora:
# - Procesa de noche
# - Cierra otros programas
# - Desactiva protector de pantalla
```

### Tip 2: Probar Primero con Corto
```bash
# Corta un pedazo de 30 segundos del video
# Procesa ese pedazo primero
# Verifica que funcione bien
# Luego procesa el video completo
```

### Tip 3: Múltiples Videos
```bash
# Procesa uno a la vez
# Cada video genera su propio PKL
```

---

## 📦 Archivos Generados

### video_detections.pkl
Contiene:
- ✓ Todas las detecciones por frame
- ✓ Trayectorias de vehículos
- ✓ Info del video (dimensiones, FPS)
- ✓ Metadata del procesamiento

### Compatible con:
- ✓ TrafficAnalyzer.exe
- ✓ Tu pipeline de aforo
- ✓ Análisis en Python/pandas

---

## 🎯 Resumen Ultra Rápido

```bash
# 1. Instalar (solo primera vez)
pip install ultralytics

# 2. Procesar video
python procesar_video_simple.py video.mp4

# 3. Visualizar
dist\TrafficAnalyzer.exe
# → Cargar PKL generado

# ¡Listo!
```

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo procesar en TrafficAnalyzer.exe?**
R: No. TrafficAnalyzer solo VISUALIZA. Necesitas este script para PROCESAR.

**P: ¿Necesito GPU NVIDIA?**
R: No. Este script usa solo CPU.

**P: ¿Por qué es lento?**
R: CPU es más lento que GPU. Es normal. Ten paciencia.

**P: ¿Puedo acelerar el proceso?**
R: No con este script (configuración fija). Usa `video_processor_gui.py` si quieres ajustar.

**P: ¿El PKL es compatible?**
R: Sí, 100% compatible con TrafficAnalyzer.

---

**¡Ya puedes procesar tus videos sin problemas de CUDA!** 🎉
