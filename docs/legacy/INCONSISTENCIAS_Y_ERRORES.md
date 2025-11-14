# 🔴 INFORME DE INCONSISTENCIAS Y ERRORES - PROYECTO AFOROS

**Fecha de revisión:** 2025-01-15  
**Objetivo:** Identificar discrepancias entre los requisitos especificados (dominio de Aforos) y la implementación actual (dominio RILSA/Trayectorias)

---

## 📋 RESUMEN EJECUTIVO

El proyecto tiene **DOS DOMINIOS COMPLETAMENTE DIFERENTES MEZCLADOS**:

1. **DOMINIO ESPERADO (según requisitos): "Aforos"** - Capacidad/Ocupación
   - CSV/Excel con datos de aforos (fecha, zonaId, horaInicio, horaFin, capacidadMaxima, aforoPlanificado/aforoReal)
   - Validación matemática de capacidad vs ocupación
   - Gráficos de serie temporal
   - Reportes de ocupación por zona y día

2. **DOMINIO IMPLEMENTADO: "RILSA/Trayectorias"** - Análisis de movimiento
   - Archivos PKL (Python Pickle) con trayectorias
   - Configuración de accesos cardinales (N, S, E, O)
   - Generación de reglas RILSA de movimiento
   - Visualización de trayectorias en canvas

**CONCLUSIÓN:** El código actual NO implementa los requisitos solicitados. Implementa un sistema diferente de análisis de trayectorias de video.

---

## 🚨 ERRORES CRÍTICOS

### 1. **DISCONEXIÓN TOTAL DE DOMINIOS**

#### Backend - Routers
- ❌ `api/routers/datasets.py`: Espera archivos `.pkl` (Python Pickle), NO CSV de aforos
- ❌ `api/routers/config.py`: Maneja `AccessConfig` y `RilsaRule` (dominio RILSA), NO `AforoConfig` (umbrales, intervalos)
- ❌ `api/routers/validation.py`: Valida movimientos RILSA estadísticamente, NO valida aforos matemáticamente
- ❌ `api/routers/editor.py`: Editor de correcciones de trayectorias, NO editor de registros de aforos
- ❌ `api/routers/live.py`: Eventos de frames/tracks para visualización de video, NO serie temporal de aforos
- ❌ `api/routers/reports.py`: Reportes de movimientos RILSA, NO reportes de ocupación por zona/día
- ❌ `api/routers/history.py`: Historial de configuraciones de dataset, NO historial de uploads/cargas de aforos

#### Frontend - Páginas
- ❌ `UploadPage.tsx`: Sube archivos `.pkl`, NO CSV/Excel de aforos
- ❌ `DatasetConfigPageNew.tsx`: Configura accesos cardinales (N, S, E, O) y reglas RILSA, NO configura umbrales y capacidades
- ❌ `DatasetValidationPage.tsx`: Validación estadística de movimientos, NO validación matemática de aforos
- ❌ `DatasetEditorPage.tsx`: Editor de correcciones de trayectorias, NO editor de registros de aforos
- ❌ `AforoDetailPage.tsx`: Debería mostrar gráfico de aforos, pero probablemente muestra visualización de video
- ❌ `ResultsPage.tsx`: Resultados de movimientos RILSA, NO reportes de ocupación
- ❌ `HistoryPage.tsx`: Historial de configuraciones, NO historial de cargas

#### Tipos y Modelos
- ✅ `apps/web/src/lib/types/aforoTypes.ts`: **CORRECTO** - Define tipos para dominio de Aforos
- ❌ `apps/web/src/types/index.ts`: Define tipos para dominio RILSA (AccessConfig, RilsaRule, TrajectoryPoint)
- ✅ `api/models/aforoModels.py`: **CORRECTO** - Define modelos para dominio de Aforos
- ❌ `api/models/config.py`: Define modelos para dominio RILSA (AccessConfig, RilsaRule, DatasetConfig)

### 2. **SERVICIOS Y DOMINIO NO IMPLEMENTADOS**

#### Funciones de Dominio Existentes (pero NO USADAS):
- ✅ `api/domain/csvParsing.py`: Implementa `parsear_csv_aforos()` - **NO SE USA EN NINGÚN ROUTER**
- ✅ `api/domain/aforoValidation.py`: Implementa `validar_aforos()` - **NO SE USA EN NINGÚN ROUTER**

#### Servicios Implementados (dominio incorrecto):
- ❌ `api/services/cardinals.py`: Genera accesos cardinales (RILSA) - **DOMINIO INCORRECTO**
- ❌ `api/services/persistence.py`: Persiste configuraciones de accesos (RILSA) - **DOMINIO INCORRECTO**

---

## 🔍 INCONSISTENCIAS DETALLADAS POR PASO

### **STEP 1 - Upload**

#### ❌ Requisitos:
- Subir CSV/Excel con datos de aforos
- Lista de archivos subidos recientemente (nombre, fecha, estado)
- Barra de progreso y mensajes de error

#### ❌ Implementación Actual:
- Sube archivos `.pkl` (Python Pickle)
- Crea "datasets" con metadata (frames, tracks, dimensions)
- No parsea CSV de aforos

#### 📝 Archivos Afectados:
- `api/routers/datasets.py`: Completamente diferente
- `apps/web/src/pages/UploadPage.tsx`: Completamente diferente

---

### **STEP 2 - Config**

#### ❌ Requisitos:
- Configurar umbrales de alerta (umbralAdvertencia, umbralCritico)
- Configurar capacidades por zona
- Configurar intervalo de agregación (5, 15, 30, 60 minutos)
- Guardar configuración ligada a `uploadId`

#### ❌ Implementación Actual:
- Configura accesos cardinales (N, S, E, O) como polígonos en imagen
- Genera reglas RILSA de movimiento
- Guarda configuración ligada a `dataset_id`

#### 📝 Archivos Afectados:
- `api/routers/config.py`: Completamente diferente (AccessConfig vs AforoConfig)
- `api/models/config.py`: Modelos incorrectos
- `apps/web/src/pages/DatasetConfigPageNew.tsx`: Completamente diferente

---

### **STEP 3 - Validation**

#### ❌ Requisitos:
- Validar campos obligatorios
- Validar horaFin > horaInicio
- Validar aforoUsado <= capacidadMaxima
- Construir serie temporal discretizada
- Calcular estados (OK, ADVERTENCIA, CRÍTICO)
- Detectar solapamientos incoherentes

#### ❌ Implementación Actual:
- Valida movimientos estadísticamente (ejecuta N runs)
- Calcula estadísticas por código de movimiento
- NO valida aforos matemáticamente

#### 📝 Archivos Afectados:
- `api/routers/validation.py`: Completamente diferente
- `api/domain/aforoValidation.py`: Existe pero NO SE USA

---

### **STEP 4 - Editor**

#### ❌ Requisitos:
- Tabla editable de registros de aforos
- Edición de fecha, horaInicio, horaFin, zonaId, capacidadMaxima, aforoPlanificado/aforoReal
- Validación en tiempo real
- Revalidación al guardar cambios

#### ❌ Implementación Actual:
- Editor de correcciones de trayectorias (track_id, movement_code, object_type)
- NO edita registros de aforos

#### 📝 Archivos Afectados:
- `api/routers/editor.py`: Completamente diferente
- `apps/web/src/pages/DatasetEditorPage.tsx`: Completamente diferente

---

### **STEP 5 - Live (Gráfico Interactivo)**

#### ❌ Requisitos:
- Gráfico de serie temporal (eje X: tiempo, eje Y: número de personas)
- Series: línea de aforo, línea de capacidad
- Filtros por fecha, zonaId, rango horario
- Hover/tooltip con información del slot
- Estados visuales (OK, ADVERTENCIA, CRÍTICO)

#### ❌ Implementación Actual:
- Visualización de eventos frame-by-frame para video
- Eventos con positions, object_type, movement_code
- NO muestra gráfico de serie temporal de aforos

#### 📝 Archivos Afectados:
- `api/routers/live.py`: Completamente diferente
- `apps/web/src/pages/AforoDetailPage.tsx`: Probablemente diferente

---

### **STEP 6 - Reports**

#### ❌ Requisitos:
- Resumen por día y zona (aforoMáximoHoraPunta, aforoMedio, porcentajeTiempoEnAdvertencia/Crítico)
- Exportar a CSV

#### ❌ Implementación Actual:
- Resumen de movimientos RILSA (volumen por código, porcentajes)
- Exporta movimientos, NO reportes de ocupación

#### 📝 Archivos Afectados:
- `api/routers/reports.py`: Completamente diferente

---

### **STEP 7 - History**

#### ❌ Requisitos:
- Lista de cargas (uploads) con uploadId, nombreArchivo, fechaCarga, estadoValidación
- Historial de versiones de un upload
- Comparación entre versiones

#### ❌ Implementación Actual:
- Historial de acciones de configuración (Dataset uploaded, Accesses configured, RILSA rules generated)
- NO maneja uploads de aforos ni versiones

#### 📝 Archivos Afectados:
- `api/routers/history.py`: Completamente diferente

---

## 🔧 PROBLEMAS TÉCNICOS ADICIONALES

### 1. **API Client Frontend**
- `apps/web/src/lib/api.ts`: Define funciones para dominio RILSA (uploadDataset, generateAccesses, etc.)
- NO tiene funciones para dominio de Aforos (uploadCSV, getAforoConfig, validateAforos, etc.)

### 2. **Persistencia**
- No hay servicio de persistencia para uploads de aforos
- No hay servicio de persistencia para registros de aforos
- No hay servicio de persistencia para resultados de validación

### 3. **Nomenclatura Confusa**
- Se usa `datasetId` para lo que debería ser `uploadId`
- Se usa `dataset` para lo que debería ser `upload` (carga de archivo)

### 4. **Tests**
- `tests/test_aforoValidation.py`: Existe pero valida dominio de aforos
- `tests/test_csvParsing.py`: Existe pero parsea CSV de aforos
- Los routers actuales NO tienen tests

---

## ✅ LO QUE SÍ ESTÁ BIEN IMPLEMENTADO

1. **Tipos TypeScript para Aforos** (`apps/web/src/lib/types/aforoTypes.ts`):
   - ✅ AforoRecord
   - ✅ AforoConfig
   - ✅ ValidationError
   - ✅ TimeSlotPoint
   - ✅ ValidationResult
   - ✅ AforoUpload
   - ✅ DayZoneSummary
   - ✅ ReportSummary

2. **Modelos Pydantic para Aforos** (`api/models/aforoModels.py`):
   - ✅ AforoRecord, AforoRecordBase, AforoRecordCreate, AforoRecordUpdate
   - ✅ AforoConfig, AforoConfigBase, AforoConfigCreate, AforoConfigUpdate
   - ✅ ValidationError
   - ✅ TimeSlotPoint
   - ✅ ValidationResult
   - ✅ AforoUpload
   - ✅ DayZoneSummary, ReportSummary

3. **Funciones de Dominio Puro**:
   - ✅ `api/domain/csvParsing.py`: `parsear_csv_aforos()` - **FUNCIONAL**
   - ✅ `api/domain/aforoValidation.py`: `validar_aforos()` - **FUNCIONAL**

---

## 🎯 RECOMENDACIONES

### Opción 1: **REESCRIBIR TODO** para implementar dominio de Aforos
- Eliminar código RILSA
- Implementar routers para Aforos
- Implementar páginas para Aforos
- Crear servicios de persistencia para Aforos

### Opción 2: **SEPARAR PROYECTOS**
- Mantener proyecto actual como "RILSA/Trayectorias"
- Crear proyecto nuevo "Aforos" con la implementación correcta

### Opción 3: **REFACTORIZAR GRADUALMENTE**
- Mantener ambos dominios en el mismo proyecto
- Renombrar rutas: `/datasets/*` para RILSA, `/uploads/*` para Aforos
- Implementar nuevos routers para Aforos sin tocar los existentes

---

## 📊 ESTIMACIÓN DE IMPACTO

| Componente | Estado Actual | Estado Requerido | Esfuerzo |
|------------|---------------|------------------|----------|
| **STEP 1 - Upload** | ❌ PKL upload | ✅ CSV/Excel upload | 🔴 Alto |
| **STEP 2 - Config** | ❌ AccessConfig | ✅ AforoConfig | 🔴 Alto |
| **STEP 3 - Validation** | ❌ Stats validation | ✅ Math validation | 🔴 Alto |
| **STEP 4 - Editor** | ❌ Trajectory editor | ✅ Record editor | 🔴 Alto |
| **STEP 5 - Live** | ❌ Frame events | ✅ Time series chart | 🔴 Alto |
| **STEP 6 - Reports** | ❌ Movement reports | ✅ Occupancy reports | 🔴 Alto |
| **STEP 7 - History** | ❌ Config history | ✅ Upload history | 🔴 Alto |

**TOTAL:** 🔴 **REESCRIBIR COMPLETAMENTE** o crear proyecto nuevo

---

## 🔍 ARCHIVOS A REVISAR/REESCRIBIR

### Backend (Python/FastAPI)
```
api/routers/
  ├── datasets.py          ❌ REESCRIBIR → upload.py
  ├── config.py            ❌ REESCRIBIR → config.py (AforoConfig)
  ├── validation.py        ❌ REESCRIBIR → validation.py (aforos)
  ├── editor.py            ❌ REESCRIBIR → editor.py (records)
  ├── live.py              ❌ REESCRIBIR → live.py (time series)
  ├── reports.py           ❌ REESCRIBIR → reports.py (occupancy)
  └── history.py           ❌ REESCRIBIR → history.py (uploads)

api/services/
  ├── cardinals.py         ❌ ELIMINAR (dominio RILSA)
  └── persistence.py       ❌ REESCRIBIR → upload persistence

api/models/
  ├── aforoModels.py       ✅ CORRECTO (mantener)
  └── config.py            ❌ ELIMINAR o renombrar → rilsaModels.py
```

### Frontend (React/TypeScript)
```
apps/web/src/
  ├── pages/
  │   ├── UploadPage.tsx           ❌ REESCRIBIR
  │   ├── DatasetConfigPageNew.tsx ❌ REESCRIBIR → ConfigPage.tsx
  │   ├── DatasetValidationPage.tsx ❌ REESCRIBIR → ValidationPage.tsx
  │   ├── DatasetEditorPage.tsx    ❌ REESCRIBIR → EditorPage.tsx
  │   ├── AforoDetailPage.tsx      ❌ REVISAR/REESCRIBIR → LivePage.tsx
  │   ├── ResultsPage.tsx          ❌ REESCRIBIR → ReportsPage.tsx
  │   └── HistoryPage.tsx          ❌ REESCRIBIR
  │
  ├── lib/
  │   ├── api.ts                   ❌ REESCRIBIR (funciones de Aforos)
  │   └── types/
  │       └── aforoTypes.ts        ✅ CORRECTO (mantener)
  │
  └── types/
      └── index.ts                 ❌ ELIMINAR o mover → rilsaTypes.ts
```

---

## ✅ PASOS SIGUIENTES SUGERIDOS

1. **Decidir estrategia**: ¿Refactorizar o crear proyecto nuevo?
2. **Crear nuevos routers** para dominio de Aforos
3. **Integrar funciones de dominio existentes** (`csvParsing.py`, `aforoValidation.py`)
4. **Crear servicios de persistencia** para uploads y registros
5. **Reescribir páginas frontend** para dominio de Aforos
6. **Implementar gráficos** con librería adecuada (Chart.js, Recharts, etc.)
7. **Escribir tests** para nuevos componentes

---

**NOTA:** Este informe identifica las inconsistencias. Para implementar correctamente los requisitos, se necesita una reescritura completa o la creación de un proyecto nuevo enfocado exclusivamente en el dominio de Aforos.
