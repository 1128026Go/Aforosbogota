# AFOROS RILSA v3.0.2 - Arquitectura Completa de 7 Pasos

## 📋 Resumen

Arquitectura full-stack con **7 pasos secuenciales** para procesar videos de tráfico, detectar movimientos y generar reportes de aforo con nomenclatura RILSA.

**Puertos:**
- Frontend: `3000` (Vite)
- Backend: `3004` (FastAPI)

---

## 🎯 Los 7 Pasos del Flujo

### Paso 1: **Subir PKL**
**Ruta:** `/datasets/upload`

- El usuario sube un archivo `.pkl` con datos de trayectorias
- Backend normaliza a Parquet
- Sistema genera `dataset_id` único
- Auto-navega a Paso 2

**API:**
- `POST /api/v1/datasets/upload` → crea dataset, guarda metadata

---

### Paso 2: **Configurar Accesos + Gráfico Interactivo**
**Ruta:** `/datasets/:datasetId/config`

- Visualizar trayectorias en canvas
- Mostrar/editar polígonos de accesos cardinales (N, S, E, O)
- Generar movimientos RILSA (16 códigos)
- Guardar configuración

**APIs:**
- `GET /api/v1/config/view/:datasetId` → obtiene config actual
- `POST /api/v1/config/generate_accesses/:datasetId` → propone accesos
- `PUT /api/v1/config/save_accesses/:datasetId` → guarda accesos editados
- `POST /api/v1/config/generate_rilsa/:datasetId` → genera movimientos

---

### Paso 3: **Validaciones Matemáticas**
**Ruta:** `/datasets/:datasetId/validation`

- Input para número de corridas (N)
- Ejecutar procesamiento N veces
- Calcular estadísticas: media, desv. estándar, min, max, mediana

**API:**
- `POST /api/v1/validate/:datasetId` → { runs: int }

---

### Paso 4: **Editor de Trayectorias**
**Ruta:** `/datasets/:datasetId/editor`

- Tabla de trayectorias procesadas
- Permitir correcciones: descartar, ocultar en PDF, notas
- Editar asignación de movimientos RILSA

**APIs:**
- `GET /api/v1/editor/:datasetId/corrections`
- `POST /api/v1/editor/:datasetId/corrections`

---

### Paso 5: **Visualizador en Vivo (Playback + Aforo Real)**
**Ruta:** `/datasets/:datasetId/live`

- Canvas con reproducción frame-a-frame de trayectorias
- Play/Pause/Slider
- Panel lateral con conteos acumulados por movimiento y tipo de objeto

**API:**
- `GET /api/v1/live/:datasetId` → lista de eventos (frame_id, track_id, x, y, object_type, movement_code)

---

### Paso 6: **Resultados Finales + Descarga**
**Ruta:** `/datasets/:datasetId/results`

- Tabla de movimientos RILSA: código, descripción, volumen, %
- Resumen por tipo de objeto (vehículo, moto, peatón)
- Botones: **Descargar CSV** y **Descargar PDF**

**APIs:**
- `GET /api/v1/reports/:datasetId/summary` → datos
- `GET /api/v1/reports/:datasetId/pdf` → archivo PDF
- `GET /api/v1/reports/:datasetId/csv` → archivo CSV

---

### Paso 7: **Historial / Auditoría** (Opcional)
**Ruta:** `/datasets/:datasetId/history`

- Registro de todas las acciones: upload, config, validaciones, ediciones
- Versiones del dataset
- Timestamps y usuario

**API:**
- `GET /api/v1/history/:datasetId`

---

## 🏗️ Estructura de Carpetas

### Frontend (`apps/web/src/`)

```
pages/
├── UploadPage.tsx              # Paso 1: Subir PKL
├── DatasetConfigPageNew.tsx    # Paso 2: Config + Gráfico
├── DatasetValidationPage.tsx   # Paso 3: Validaciones
├── DatasetEditorPage.tsx       # Paso 4: Editor
├── AforoDetailPage.tsx         # Paso 5: Visualizador en vivo
├── ResultsPage.tsx             # Paso 6: Resultados
└── HistoryPage.tsx             # Paso 7: Historial

components/
├── StepNavigation.tsx          # Barra de pasos (7 pasos)
├── TrajectoryCanvas.tsx        # Canvas para visualización
├── AccessEditorPanel.tsx       # Panel editor de accesos
└── [otros componentes...]

lib/
├── api.ts                       # Cliente API completo

types/
└── index.ts                     # Tipos TypeScript
```

### Backend (`api/`)

```
routers/
├── __init__.py
├── config.py                   # Config (paso 2)
├── datasets.py                 # Datasets (paso 1)
├── validation.py               # Validaciones (paso 3)
├── editor.py                   # Editor (paso 4)
├── live.py                     # Live events (paso 5)
├── reports.py                  # Reports (paso 6)
└── history.py                  # History (paso 7)

services/
├── cardinals.py
├── persistence.py
└── [otros servicios]

models/
└── config.py

main.py                         # FastAPI app
```

---

## 🔌 Endpoints API Completos

### Datasets (Paso 1)
```
POST   /api/v1/datasets/upload          # Subir PKL
GET    /api/v1/datasets/list            # Listar datasets
GET    /api/v1/datasets/:datasetId      # Obtener metadata
```

### Config (Paso 2)
```
GET    /api/v1/config/view/:datasetId
POST   /api/v1/config/generate_accesses/:datasetId
PUT    /api/v1/config/save_accesses/:datasetId
POST   /api/v1/config/generate_rilsa/:datasetId
```

### Validation (Paso 3)
```
POST   /api/v1/validate/:datasetId      # { runs: int }
```

### Editor (Paso 4)
```
GET    /api/v1/editor/:datasetId/corrections
POST   /api/v1/editor/:datasetId/corrections
```

### Live (Paso 5)
```
GET    /api/v1/live/:datasetId
```

### Reports (Paso 6)
```
GET    /api/v1/reports/:datasetId/summary
GET    /api/v1/reports/:datasetId/pdf
GET    /api/v1/reports/:datasetId/csv
```

### History (Paso 7)
```
GET    /api/v1/history/:datasetId
```

---

## 🎨 Componente StepNavigation

Barra visual de 7 pasos con:
- Círculos indicadores (completado ✓, actual 🔵, pendiente ⚪)
- Líneas conectoras mostrando progreso
- Nombres y descripciones de pasos
- Click para navegar (si está permitido)
- Deshabilitados pasos que requieren datasetId

---

## 💾 Flujo de Datos

```
1. Usuario sube PKL
   ↓
2. Sistema crea dataset_id, normaliza, guarda metadata
   ↓
3. Frontend navega a /datasets/:datasetId/config
   ↓
4. Usuario define accesos, genera RILSA
   ↓
5. Usuario ejecuta validaciones (N corridas)
   ↓
6. Usuario edita trayectorias si es necesario
   ↓
7. Sistema renderiza visualizador en vivo con aforo
   ↓
8. Usuario descarga CSV/PDF con resultados
   ↓
9. Historial registra cada paso
```

---

## 🚀 Inicio Rápido

### Instalar y Ejecutar

```bash
# Backend
cd api
pip install -r requirements.txt
python main.py              # Uvicorn en puerto 3004

# Frontend
cd apps/web
npm install
npm run dev                 # Vite en puerto 3000
```

### Acceder
```
http://localhost:3000
```

---

## 🎯 Estado de Implementación

✅ **Completado:**
- Rutas y StepNavigation (7 pasos)
- Todas las páginas stub creadas
- Todos los routers backend creados
- Tipos TypeScript actualizados
- Cliente API completo

🔄 **Por Implementar (TODO):**
- Normalización real PKL→Parquet en datasets.py
- Extracción de metadata (frames, tracks, dimensiones)
- Lógica de generación automática de accesos
- Estadísticas multi-corrida
- Renderización de PDF
- Almacenamiento persistente de correcciones

---

## 📝 Nomenclatura RILSA (16 movimientos)

```
NORTE (origen N):
1   → N→S (directo)
5   → N→E (izquierda)
91  → N→O (derecha)
101 → N→N (U)

SUR (origen S):
2   → S→N (directo)
6   → S→O (izquierda)
92  → S→E (derecha)
102 → S→S (U)

OESTE (origen O):
3   → O→E (directo)
7   → O→N (izquierda)
93  → O→S (derecha)
103 → O→O (U)

ESTE (origen E):
4   → E→O (directo)
8   → E→S (izquierda)
94  → E→N (derecha)
104 → E→E (U)
```

---

## 🔐 CORS y Seguridad

Backend CORS configurado para:
- `http://localhost:3000` (frontend dev)
- `http://localhost:3004` (documentación)
- `127.0.0.1`

---

## 📞 Soporte

Para errores o preguntas, revisa:
1. Console del navegador (DevTools)
2. Logs de FastAPI (stderr)
3. Network tab para ver requests/responses
