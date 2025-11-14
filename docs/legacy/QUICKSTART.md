# Guía de Inicio Rápido - Traffic Analyzer

## Opción 1: Usar Ejecutable (.exe)

### Instalación
1. Ejecutar `build.bat`
2. Esperar a que compile
3. El ejecutable estará en `dist\TrafficAnalyzer.exe`

### Uso
1. Doble clic en `TrafficAnalyzer.exe`
2. Cargar archivo PKL
3. ¡Listo!

---

## Opción 2: Ejecutar desde Python

### Instalación
```bash
# Ejecutar el instalador
install.bat

# O manualmente:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Uso
```bash
# Ejecutar directamente
run.bat

# O manualmente:
venv\Scripts\activate
python traffic_analyzer.py
```

---

## Tutorial Rápido (5 minutos)

### 1️⃣ Cargar Datos (1 min)
- Clic en **"📁 Cargar PKL"**
- Seleccionar tu archivo `.pkl`
- Opcional: Cargar video asociado

### 2️⃣ Detectar Zonas Automáticamente (2 min)
- Seleccionar método: **KMeans** (para empezar)
- Número de zonas: **5**
- Clic en **"🔍 Detectar Zonas Automáticamente"**
- Ver zonas en la visualización

### 3️⃣ Ajustar Zonas (1 min)
- Seleccionar zona en la lista
- Ver estadísticas en panel derecho
- Editar o eliminar según necesites

### 4️⃣ Exportar Configuración (1 min)
- Clic en **"💾 Exportar JSON"**
- Guardar archivo
- Usar en tu pipeline de aforo

---

## Casos de Uso Típicos

### Caso 1: Contar Vehículos por Zona
```
PKL → Cargar → KMeans (4 zonas) → Renombrar → Exportar JSON
```

### Caso 2: Detectar Puntos Calientes
```
PKL → Cargar → Heatmap → Ver zonas calientes → Exportar
```

### Caso 3: Definir Zonas Personalizadas
```
PKL → Cargar → Agregar manual → Dibujar → Exportar
```

---

## Solución Rápida de Problemas

| Problema | Solución |
|----------|----------|
| No inicia | Ejecutar `install.bat` |
| Error al cargar PKL | Verificar formato del PKL |
| No se ven zonas | Ajustar parámetros de clustering |
| Exportación falla | Verificar permisos de carpeta |

---

## Formatos de Archivos

### Entrada
- **PKL**: Detecciones de YOLO
- **Video**: MP4, AVI, MOV (opcional)

### Salida
- **JSON**: Configuración de zonas
- **CSV**: Datos tabulares
- **PKL**: Datos binarios
- **PNG/JPG**: Visualizaciones

---

## Siguiente Paso

Ver **README.md** para documentación completa.

---

## Soporte

¿Problemas? Revisar:
1. Logs en la aplicación (panel derecho)
2. README.md (documentación completa)
3. zones_example.json (ejemplo de configuración)
