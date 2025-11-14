# 📋 PLAN DE EJECUCIÓN - AFOROS (Semanas 1-2)

**Versión:** v1.0
**Fecha:** 13 de Enero de 2025
**Duración:** 14 días (2 semanas)
**Status:** 🚀 INICIO INMEDIATO

---

## 📊 ANÁLISIS DE CONTEXTO ACTUAL

### Stack Identificado
- **Frontend:** React 18 + TypeScript 5.3.3 (strict) + Tailwind CSS + React Router v6 ✅
- **Backend:** FastAPI 0.104.1 + Pydantic 2.5.0 + Uvicorn ✅
- **Puertos:** 3000 (front) + 3004 (back) ✅
- **API Prefix:** `/api/v1/` ✅

### Arquitectura Existente
```
Frontend:
  pages/         → Componentes de página (UploadPage, ConfigPage, etc.)
  components/    → Componentes reutilizables (StepNavigation, etc.)
  lib/
    ├─ api.ts    → Cliente HTTP tipado
    └─ types/    → Tipos/Interfaces centralizados

Backend:
  routers/       → Routers por dominio (datasets, config, validation, etc.)
  main.py        → FastAPI app con includes
```

### Convenciones Observadas
- ✅ Componentes funcionales con hooks (React)
- ✅ Tipos/Interfaces centralizados (no tipos inline)
- ✅ Routers organizados por dominio (no por verbos HTTP)
- ✅ Validación con Pydantic
- ✅ Estilos con Tailwind (utility-first)
- ✅ API client centralizado

---

## 🎯 ROADMAP DE 2 SEMANAS

### SEMANA 1: Steps 1, 2, 3 (Upload, Config, Validation)

```
DÍA 1-2:  Step 1 - Upload
├─ Backend: Parser CSV + persistencia
├─ Frontend: Componente Upload con drag-drop
└─ API: POST /api/v1/uploads

DÍA 3-4:  Step 2 - Config
├─ Backend: CRUD de configuración
├─ Frontend: Pantalla de config
└─ API: GET/POST /api/v1/config/:uploadId

DÍA 5-7:  Step 3 - Validation
├─ Backend: Motor de validación matemática
├─ Frontend: Vista de errores y serieTemporal
└─ API: POST /api/v1/validate/:uploadId
```

### SEMANA 2: Steps 4, 5, 6, 7 (Editor, Live, Reports, History)

```
DÍA 8-9:  Step 4 - Editor
├─ Frontend: Tabla editable con revalidación
├─ Backend: Actualizar registros
└─ API: PUT /api/v1/records/:recordId

DÍA 10:   Step 5 - Live (Gráfico)
├─ Frontend: Gráfico con serieTemporal
└─ Reuse de librerías de gráficos existentes

DÍA 11-12: Step 6 - Reports
├─ Backend: Agregaciones por día/zona
├─ Frontend: Tabla de resumen + export CSV
└─ API: GET /api/v1/reports/:uploadId

DÍA 13:   Step 7 - History
├─ Backend: Tracking de versiones
├─ Frontend: Lista de uploads + historial
└─ API: GET /api/v1/uploads (list)

DÍA 14:   Testing & Polish
├─ Tests unitarios de validación
├─ Tests de componentes
└─ Responsive design
```

---

## 📁 ESTRUCTURA A CREAR

```
frontend/
  src/
    ├─ pages/
    │  ├─ [Existente] UploadPage.tsx ← REUSE (solo expandir)
    │  ├─ [Existente] DatasetConfigPageNew.tsx ← REUSE (solo expandir)
    │  ├─ [Existente] DatasetValidationPage.tsx ← REUSE (solo expandir)
    │  ├─ [NEW] EditorPage.tsx
    │  ├─ [NEW] LivePage.tsx (con gráfico)
    │  ├─ [NEW] ReportsPage.tsx
    │  └─ [NEW] HistoryPage.tsx
    │
    ├─ components/
    │  ├─ [NEW] FileUpload.tsx (atom/reutilizable)
    │  ├─ [NEW] ValidationErrorsList.tsx
    │  ├─ [NEW] EditableTable.tsx (reutilizable)
    │  ├─ [NEW] AforoChart.tsx (gráfico)
    │  └─ [Existente] StepNavigation.tsx
    │
    ├─ lib/
    │  ├─ api.ts ← EXPAND (agregar endpoints nuevos)
    │  ├─ types/
    │  │  └─ index.ts ← EXPAND (types de Aforo)
    │  ├─ [NEW] validators/
    │  │  └─ aforoValidators.ts (lógica pura de validación)
    │  └─ [NEW] serialization/
    │     └─ csvParser.ts (parse CSV)
    │
    └─ hooks/
       ├─ [NEW] useUpload.ts
       ├─ [NEW] useValidation.ts
       └─ [NEW] useEditor.ts

backend/
  ├─ routers/
  │  ├─ [MODIFY] datasets.py ← Agregar upload de CSV
  │  ├─ [MODIFY] config.py ← CRUD de configuración
  │  ├─ [MODIFY] validation.py ← Motor de validación
  │  ├─ [NEW] editor.py
  │  ├─ [NEW] reports.py
  │  └─ [NEW] history.py
  │
  ├─ domain/
  │  ├─ [NEW] aforoValidation.py (lógica pura)
  │  ├─ [NEW] csvParsing.py
  │  └─ [NEW] aggregation.py
  │
  ├─ models/
  │  ├─ [NEW] aforoModels.py (Pydantic models)
  │  └─ [NEW] validationResults.py
  │
  ├─ [MODIFY] main.py ← Incluir routers nuevos
  └─ [NEW] database.py ← Persistencia (si no existe)

tests/
  ├─ [NEW] test_aforoValidation.py
  ├─ [NEW] test_csvParsing.py
  └─ [NEW] test_components.tsx
```

---

## 🛠️ TIPOS/INTERFACES CENTRALES

### Dominio de Aforos

```typescript
// types/aforoTypes.ts (NUEVA)

// ===== REGISTROS =====
export interface AforoRecord {
  id: string;                    // UUID
  uploadId: string;              // FK a Upload
  fecha: Date;
  zonaId: string;
  horaInicio: string;            // HH:mm
  horaFin: string;               // HH:mm
  capacidadMaxima: number;       // > 0
  aforoPlanificado?: number;     // >= 0
  aforoReal?: number;            // >= 0
  version: number;               // Para historial
  createdAt: Date;
  updatedAt: Date;
}

// ===== CONFIGURACIÓN =====
export interface AforoConfig {
  id: string;
  uploadId: string;              // FK a Upload
  umbralAdvertencia: number;     // 0-1 (default 0.8)
  umbralCritico: number;         // 0-1 (default 1.0)
  intervaloMinutos: number;      // 5, 15, 30, 60
  capacidadesPorZona?: Record<string, number>;
  createdAt: Date;
  updatedAt: Date;
}

// ===== VALIDACIÓN =====
export interface ValidationError {
  registroId?: string;
  campo?: string;
  mensaje: string;
  tipo: "parsing" | "requerido" | "tipo" | "logica" | "solapamiento";
  severidad: "error" | "advertencia";
}

export interface TimeSlotPoint {
  fecha: Date;
  zonaId: string;
  inicio: Date;                  // Inicio del slot
  fin: Date;                     // Fin del slot
  aforo: number;
  capacidad: number;
  ratioUso: number;              // 0-1 o > 1
  estado: "OK" | "ADVERTENCIA" | "CRITICO";
  registrosIds: string[];        // IDs que contribuyen
}

export interface ValidationResult {
  uploadId: string;
  erroresGlobales: ValidationError[];
  erroresPorRegistro: Record<string, ValidationError[]>;
  serieTemporal: TimeSlotPoint[];
  fechaValidacion: Date;
  valido: boolean;
}

// ===== UPLOAD =====
export interface AforoUpload {
  id: string;
  nombreArchivo: string;
  nombreUsuario?: string;
  fechaCarga: Date;
  estadoValidacion: "OK" | "CON_ERRORES" | "PENDIENTE";
  cantidadRegistros: number;
  cantidadErrores: number;
}

// ===== HISTORIAL =====
export interface UploadVersion {
  id: string;
  uploadId: string;
  numeroVersion: number;
  fechaVersion: Date;
  usuarioModifico?: string;
  cambios: {
    registrosModificados: number;
    registrosAgregados: number;
    registrosEliminados: number;
  };
}
```

---

## 📡 ENDPOINTS A IMPLEMENTAR

### STEP 1: Upload

```
POST /api/v1/uploads
├─ Body: FormData (archivo CSV)
├─ Response: { uploadId, totalRegistros, estado }
└─ Backend: Parsear CSV → Guardar registros → DB

GET /api/v1/uploads/list
├─ Response: AforoUpload[]
└─ Backend: Listar todas las cargas
```

### STEP 2: Config

```
GET /api/v1/config/:uploadId
├─ Response: AforoConfig
└─ Backend: Obtener config actual

POST /api/v1/config/:uploadId
├─ Body: { umbralAdvertencia, umbralCritico, intervaloMinutos, capacidadesPorZona }
├─ Response: AforoConfig (guardada)
└─ Backend: Guardar config en DB
```

### STEP 3: Validation

```
POST /api/v1/validate/:uploadId
├─ Body: {} (toma config del uploadId)
├─ Response: ValidationResult
└─ Backend: Ejecutar validateAforos(registros, config) → Guardar resultado
```

### STEP 4: Editor

```
GET /api/v1/records/:uploadId
├─ Response: AforoRecord[]
└─ Backend: Listar registros del upload

PUT /api/v1/records/:recordId
├─ Body: AforoRecord (campos a actualizar)
├─ Response: AforoRecord (actualizado)
└─ Backend: Actualizar en DB → Revalidar upload

DELETE /api/v1/records/:recordId
├─ Response: { success }
└─ Backend: Borrar → Revalidar
```

### STEP 5: Live (Data para gráfico)

```
GET /api/v1/live/:uploadId?fecha=...&zonaId=...&horaInicio=...&horaFin=...
├─ Response: TimeSlotPoint[]
└─ Backend: Reutilizar serieTemporal de ValidationResult
```

### STEP 6: Reports

```
GET /api/v1/reports/summary/:uploadId?desde=...&hasta=...&zonas=...
├─ Response: ReportSummary (resumen por día/zona)
└─ Backend: Agregaciones sobre serieTemporal

GET /api/v1/reports/export/:uploadId?formato=csv
├─ Response: CSV (descargable)
└─ Backend: Generar CSV de serieTemporal
```

### STEP 7: History

```
GET /api/v1/uploads/:uploadId/versions
├─ Response: UploadVersion[]
└─ Backend: Listar versiones del upload

GET /api/v1/uploads/:uploadId/compare?v1=...&v2=...
├─ Response: { resumen cambios }
└─ Backend: Comparar dos versiones
```

---

## 🔄 FLUJO DE DATOS

```
CSV Upload
    ↓
parseCsv() → AforoRecord[]
    ↓
POST /api/v1/uploads (guardar en DB)
    ↓
POST /api/v1/config/:uploadId (configurar)
    ↓
POST /api/v1/validate/:uploadId
    ├─ validateAforos(registros, config)
    ├─ Retorna: ValidationResult
    └─ Guardar en DB
    ↓
GET /api/v1/live/:uploadId → TimeSlotPoint[] (para gráfico)
    ↓
Editor modifica registro
    ├─ PUT /api/v1/records/:recordId
    ├─ Revalidar upload
    └─ Actualizar TimeSlotPoint[]
    ↓
GET /api/v1/reports/:uploadId → Agregaciones
```

---

## 🚀 EJECUCIÓN POR DÍA

### DÍA 1-2: STEP 1 - Upload

#### Backend
1. Crear `backend/domain/csvParsing.py`
   - Función `parseCsv(contenido: str) -> AforoRecord[]`
   - Manejo de headers, tipos, validación básica

2. Crear `backend/models/aforoModels.py`
   - Pydantic models: AforoRecord, AforoUpload, AforoConfig, etc.

3. Modificar `backend/routers/datasets.py`
   - `POST /api/v1/uploads` (recibir FormData, parsear, guardar en DB)

#### Frontend
1. Expandir `frontend/src/pages/UploadPage.tsx`
   - Agregar FileUpload component
   - Hacer upload real (llamar a `POST /api/v1/uploads`)
   - Mostrar lista de uploads recientes

2. Crear `frontend/src/components/FileUpload.tsx`
   - Drag-drop + file input
   - Progress bar
   - Error messages

3. Expandir `frontend/src/lib/api.ts`
   - `uploadAforoFile(file: File): Promise<{uploadId, totalRegistros}>`
   - `listUploads(): Promise<AforoUpload[]>`

---

### DÍA 3-4: STEP 2 - Config

#### Backend
1. Crear `backend/routers/config.py` (NUEVO) o expandir existente
   - `GET /api/v1/config/:uploadId` → AforoConfig
   - `POST /api/v1/config/:uploadId` → Guardar config

2. Crear `backend/models/aforoModels.py` (si no existe)
   - AforoConfig Pydantic model

#### Frontend
1. Expandir/Crear `frontend/src/pages/DatasetConfigPageNew.tsx`
   - Mostrar upload seleccionado
   - Formulario: umbralAdvertencia, umbralCritico, intervaloMinutos, capacidadesPorZona
   - Guardar config

2. Crear `frontend/src/hooks/useConfig.ts`
   - Hook para fetchar y guardar config

---

### DÍA 5-7: STEP 3 - Validation

#### Backend
1. Crear `backend/domain/aforoValidation.py`
   - **Función pura** `validateAforos(registros: List[AforoRecord], config: AforoConfig) -> ValidationResult`
   - Lógica:
     - Validar campos requeridos
     - Validar tipos (hora, fechas, números)
     - Validar horaFin > horaInicio
     - Validar aforoUsado <= capacidad
     - Construir serie temporal
     - Marcar estados (OK, ADVERTENCIA, CRITICO)
     - Detectar solapamientos

2. Crear `backend/routers/validation.py` (NUEVO) o expandir
   - `POST /api/v1/validate/:uploadId` → ValidationResult

3. Crear tests `tests/test_aforoValidation.py`
   - 10+ test cases cubriendo reglas

#### Frontend
1. Crear `frontend/src/pages/DatasetValidationPage.tsx`
   - Botón "Ejecutar validación"
   - Mostrar errores globales y por registro
   - Mostrar preview de serieTemporal

2. Crear `frontend/src/components/ValidationErrorsList.tsx`
   - Lista de errores con iconos/severidad

3. Crear `frontend/src/lib/validators/aforoValidators.ts`
   - Validación a nivel de UI (números positivos, horas válidas, etc.)

---

### DÍA 8-9: STEP 4 - Editor

#### Backend
1. Crear `backend/routers/editor.py` (NUEVO)
   - `GET /api/v1/records/:uploadId` → AforoRecord[]
   - `PUT /api/v1/records/:recordId` → Guardar cambios + Revalidar
   - `DELETE /api/v1/records/:recordId`

#### Frontend
1. Crear `frontend/src/pages/EditorPage.tsx`
   - Tabla editable de registros

2. Crear `frontend/src/components/EditableTable.tsx`
   - Componente reutilizable para tablas editables
   - Validación en tiempo real
   - Botones guardar/cancelar por fila

3. Crear `frontend/src/hooks/useEditor.ts`
   - Hook para fetch y actualización de registros

---

### DÍA 10: STEP 5 - Live (Gráfico)

#### Backend
1. Crear `backend/routers/live.py` (NUEVO)
   - `GET /api/v1/live/:uploadId?filters` → TimeSlotPoint[]

#### Frontend
1. Crear `frontend/src/pages/LivePage.tsx`
   - Filtros (fecha, zonaId, rango horario)

2. Crear `frontend/src/components/AforoChart.tsx`
   - Gráfico con:
     - Línea de aforo
     - Línea de capacidad
     - Colores por estado (OK/ADVERTENCIA/CRITICO)
     - Tooltip interactivo
   - Reutilizar librería de gráficos existente

---

### DÍA 11-12: STEP 6 - Reports

#### Backend
1. Crear `backend/domain/aggregation.py`
   - `aggregateByDayAndZone(serieTemporal) -> ReportSummary`

2. Crear `backend/routers/reports.py` (NUEVO)
   - `GET /api/v1/reports/summary/:uploadId`
   - `GET /api/v1/reports/export/:uploadId?formato=csv`

#### Frontend
1. Crear `frontend/src/pages/ReportsPage.tsx`
   - Tabla de resumen por día/zona
   - Filtros (rango fechas, zonas)
   - Botón exportar CSV

---

### DÍA 13: STEP 7 - History

#### Backend
1. Crear `backend/routers/history.py` (NUEVO)
   - `GET /api/v1/uploads/:uploadId/versions`
   - `GET /api/v1/uploads/:uploadId/compare?v1=...&v2=...`

#### Frontend
1. Crear `frontend/src/pages/HistoryPage.tsx`
   - Lista de uploads (reutilizar de Step 1)
   - Historial de versiones
   - Comparación básica entre versiones

---

### DÍA 14: Testing & Polish

#### Testing
1. Tests unitarios:
   - `test_aforoValidation.py` (10+ cases)
   - `test_csvParsing.py` (5+ cases)

2. Tests de componentes:
   - FileUpload.tsx
   - EditableTable.tsx
   - AforoChart.tsx

#### Polish
1. Responsive design
2. Loading states en toda la app
3. Mensajes de error claros
4. Icons/estilo consistente

---

## 📋 CHECKLIST DE CONVENCIONES

Al implementar, respetar:

- [ ] **TypeScript strict mode** en todo
- [ ] **Tipos centralizados** en `lib/types/`
- [ ] **Funciones puras** de dominio (validación, parsing, agregación)
- [ ] **Componentes funcionales** con hooks
- [ ] **Estilos Tailwind** (no CSS custom si puede evitarse)
- [ ] **API client centralizado** en `api.ts`
- [ ] **Routers por dominio** (no por verbo HTTP)
- [ ] **Pydantic models** para validación backend
- [ ] **Manejo de errores** consistente
- [ ] **Tests unitarios** para lógica pura
- [ ] **Nombres claros** en inglés (como el proyecto existente)

---

## 🎯 DEFINICIÓN DE LISTO

Semana 1 LISTO cuando:
- [ ] Upload funciona con archivos reales
- [ ] Config se guarda y recupera
- [ ] Validación matemática implementada (con tests)
- [ ] No hay errores en console

Semana 2 LISTO cuando:
- [ ] Editor permite editar y revalidar
- [ ] Gráfico muestra datos de serie temporal
- [ ] Reports genera CSV
- [ ] Historia de uploads funciona
- [ ] Tests unitarios pasan
- [ ] Responsive en móvil/tablet

---

## 🚨 RIESGOS & MITIGACIÓN

| Riesgo | Mitigación |
|--------|-----------|
| Parseo CSV complejo | Empezar con CSV simple, iterar |
| Performance de validación | Validar solo lo modificado, cachear |
| UI compleja en Step 5 (gráfico) | Usar librería existente del proyecto |
| Base de datos no existe | Mockear en memoria o usar SQLite para dev |
| Tipos TypeScript muy complejos | Crear tipos reutilizables, evitar anidación excesiva |

---

## ✅ PRÓXIMO PASO

1. **Confirmar estructura propuesta** ↑
2. **Crear types centralizados** (`aforoTypes.ts`)
3. **Empezar DÍA 1: Backend CSV parsing**
4. **DÍA 2: Frontend Upload UI**

¿Continuar? 🚀
