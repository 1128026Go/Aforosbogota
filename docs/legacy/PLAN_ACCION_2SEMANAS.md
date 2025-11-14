# 📅 PLAN DE ACCIÓN - PRÓXIMAS 2 SEMANAS

**Proyecto:** AFOROS RILSA v3.0.2
**Fase Actual:** Arquitectura Completa → Implementación Funcional
**Duración:** 14 días
**Fecha de Inicio:** 13 de Enero de 2025

---

## 📊 ESTADO ACTUAL

```
Arquitectura (Scaffolding):  ███████████████████ 100% ✅
Funcionalidades Reales:      ░░░░░░░░░░░░░░░░░░░  0% ⏳
Testing:                     ░░░░░░░░░░░░░░░░░░░  0% ⏳
Deployment:                  ░░░░░░░░░░░░░░░░░░░  0% ⏳
```

---

## 📋 SEMANA 1: BASES FUNCIONALES (13-19 Enero)

### Día 1-2: Setup & Validación

#### Morning (4 horas)
- [ ] Iniciar backend en terminal 1
- [ ] Iniciar frontend en terminal 2
- [ ] Verificar que ambos arrancan sin errores
- [ ] Abrir navegador en http://localhost:3000
- [ ] Verificar que se ven los 7 pasos

#### Afternoon (4 horas)
- [ ] Test de cada ruta en el navegador
- [ ] Revisar console del navegador (F12)
- [ ] Revisar logs del backend
- [ ] Crear archivo `TEST_MANUAL.md` con resultados
- [ ] Documentar cualquier error encontrado

#### Deliverables
- ✅ Backend funcionando
- ✅ Frontend funcionando
- ✅ Navegación entre 7 pasos
- ✅ No hay errores en consola

---

### Día 3: Implementar Upload (Paso 1)

#### Tarea Principal: PKL Upload & Processing

**Backend (`api/routers/datasets.py`)**

```python
# TODO: Implementar en POST /datasets/upload

1. Recibir archivo PKL
2. Validar formato (debe ser .pkl o .parquet)
3. Generar dataset_id único (timestamp + random)
4. Crear carpeta: data/{dataset_id}/
5. Guardar archivo raw: data/{dataset_id}/raw.pkl
6. Generar metadata.json:
   {
     "dataset_id": "...",
     "filename": "...",
     "upload_date": "...",
     "file_size": "...",
     "status": "uploaded"
   }
7. Retornar: {dataset_id, status, metadata}
8. Almacenar dataset_id en sesión/cookie (frontend)
```

**Frontend (`src/pages/UploadPage.tsx`)**

```typescript
// TODO: Implementar upload real

1. Capturar archivo del usuario
2. POST /api/v1/datasets/upload (FormData)
3. Si éxito: guardar dataset_id en localStorage
4. Mostrar success message
5. Auto-navigate a /datasets/{dataset_id}/config
6. Si error: mostrar error message
```

#### Sub-tareas
- [ ] Crear carpeta `data` en backend
- [ ] Implementar validación de formato PKL
- [ ] Generar dataset_id único
- [ ] Guardar metadata.json
- [ ] Test: subir archivo PKL
- [ ] Test: verificar que se crea carpeta
- [ ] Test: verificar que metadata.json existe

#### Deliverables
- ✅ Upload funciona
- ✅ dataset_id se genera
- ✅ Archivo se guarda
- ✅ Metadata se crea
- ✅ Frontend puede subir archivos

---

### Día 4: Implementar Config (Paso 2)

#### Tarea Principal: Configuración de Accesos

**Backend (`api/routers/config.py`)**

```python
# TODO: Expandir los 4 endpoints existentes

1. GET /config/view/:datasetId
   - Leer config.json del dataset
   - Retornar accesos y reglas RILSA

2. POST /config/generate_accesses
   - Generar accesos por defecto (4 direcciones)
   - Guardar en config.json
   - Retornar lista de accesos

3. PUT /config/save_accesses
   - Recibir lista de accesos modificados
   - Validar coordenadas
   - Guardar en config.json
   - Retornar confirmación

4. POST /config/generate_rilsa
   - Generar 16 códigos RILSA
   - Guardar en config.json
   - Retornar lista de códigos
```

**Frontend (`src/pages/DatasetConfigPageNew.tsx`)**

```typescript
// TODO: Conectar con backend real

1. En mount: GET /config/view/:datasetId
2. Mostrar canvas con accesos
3. Permitir editar accesos
4. Click "Guardar": PUT /config/save_accesses
5. Click "Generar RILSA": POST /config/generate_rilsa
6. Mostrar lista de 16 códigos RILSA
```

#### Sub-tareas
- [ ] Crear config.json en data/{dataset_id}/
- [ ] Implementar lectura de config.json
- [ ] Implementar escritura de config.json
- [ ] Validar accesos (coordenadas válidas)
- [ ] Test: crear config
- [ ] Test: editar accesos
- [ ] Test: generar RILSA codes

#### Deliverables
- ✅ Config se crea
- ✅ Accesos se guardan
- ✅ RILSA codes se generan
- ✅ Canvas muestra accesos

---

### Día 5: Implementar Validation (Paso 3)

#### Tarea Principal: Validación Estadística

**Backend (`api/routers/validation.py`)**

```python
# TODO: Implementar POST /validate/:datasetId

1. Recibir {runs: int} del frontend
2. Para cada run:
   a. Leer raw.pkl
   b. Contar movimientos
   c. Calcular estadísticas
3. Calcular por movimiento:
   - mean (promedio)
   - std_dev (desviación estándar)
   - min (mínimo)
   - max (máximo)
   - median (mediana)
4. Retornar: {dataset_id, runs, stats: [{movement_code, stats}]}
```

**Frontend (`src/pages/DatasetValidationPage.tsx`)**

```typescript
// TODO: Conectar con backend real

1. Input: number de runs
2. Click "Ejecutar Validación": POST /validate/:datasetId
3. Mostrar tabla de estadísticas
4. Mostrar resumen (total movimientos)
```

#### Sub-tareas
- [ ] Implementar lectura de PKL
- [ ] Calcular estadísticas (numpy)
- [ ] Generar tabla de results
- [ ] Test: calcular stats
- [ ] Test: múltiples runs
- [ ] Test: mostrar en tabla

#### Deliverables
- ✅ Validación funciona
- ✅ Stats se calculan
- ✅ Tabla muestra resultados

---

### Día 6-7: Buffer & Testing

#### Testing Manual Completo

- [ ] Test: Upload → Config → Validation (flujo completo)
- [ ] Test: Verificar dataset_id persiste
- [ ] Test: Verificar archivos se guardan
- [ ] Test: Verificar metadata se actualiza
- [ ] Crear `TEST_REPORT_WEEK1.md`

#### Code Review

- [ ] Revisar código backend
- [ ] Revisar código frontend
- [ ] Verificar tipos TypeScript
- [ ] Verificar error handling
- [ ] Aplicar refactorings

#### Documentación

- [ ] Actualizar CHECKLIST_IMPLEMENTACION_7PASOS.md
- [ ] Documentar cambios en main.py
- [ ] Documentar cambios en routers

---

## 📋 SEMANA 2: FUNCIONALIDADES AVANZADAS (20-26 Enero)

### Día 8-9: Implementar Editor (Paso 4)

#### Tarea Principal: Corrección de Trayectorias

**Backend (`api/routers/editor.py`)**

```python
# TODO: Expandir 2 endpoints

1. GET /editor/:datasetId/corrections
   - Leer corrections.json
   - Retornar lista de correcciones
   - Si no existe, retornar []

2. POST /editor/:datasetId/corrections
   - Recibir Correction model
   - Validar {track_id, movement_code, object_type}
   - Guardar en corrections.json
   - Retornar confirmación
```

**Frontend (`src/pages/DatasetEditorPage.tsx`)**

```typescript
// TODO: Conectar con backend

1. En mount: GET /editor/:datasetId/corrections
2. Mostrar tabla de correcciones
3. Permitir editar cada fila
4. Click "Guardar": POST /editor/:datasetId/corrections
5. Actualizar tabla
```

#### Sub-tareas
- [ ] Crear corrections.json
- [ ] Implementar lectura de correcciones
- [ ] Implementar escritura de correcciones
- [ ] Validar campos
- [ ] Test: crear corrección
- [ ] Test: editar corrección
- [ ] Test: mostrar en tabla

#### Deliverables
- ✅ Correcciones se guardan
- ✅ Tabla editable
- ✅ Cambios persisten

---

### Día 9-10: Implementar Live Visualizer (Paso 5)

#### Tarea Principal: Visualización en Canvas

**Backend (`api/routers/live.py`)**

```python
# TODO: Implementar GET /live/:datasetId

1. Leer raw.pkl
2. Normalizar trayectorias
3. Generar lista de eventos:
   [{frame_id, track_id, x, y, object_type, movement_code}]
4. Retornar: {dataset_id, events, total_frames}
```

**Frontend (`src/pages/AforoDetailPage.tsx`)**

```typescript
// TODO: Conectar con backend

1. En mount: GET /live/:datasetId
2. Cargar eventos en estado
3. Inicializar canvas
4. Implementar playback controls:
   - Play/Pause button
   - Frame slider
   - Timer display
5. Dibujar eventos en canvas
6. Actualizar contadores por frame
```

#### Sub-tareas
- [ ] Implementar normalización de trayectorias
- [ ] Generar eventos desde PKL
- [ ] Implementar canvas rendering
- [ ] Implementar playback logic
- [ ] Test: cargar eventos
- [ ] Test: renderizar en canvas
- [ ] Test: controles de reproducción

#### Deliverables
- ✅ Canvas muestra trayectorias
- ✅ Playback funciona
- ✅ Contadores se actualizan

---

### Día 11: Implementar Reports (Paso 6)

#### Tarea Principal: Generación de Reportes

**Backend (`api/routers/reports.py`)**

```python
# TODO: Implementar 3 endpoints

1. GET /reports/:datasetId/summary
   - Leer events
   - Contar movimientos por tipo
   - Contar tracks totales
   - Retornar resumen

2. GET /reports/:datasetId/csv
   - Generar CSV con eventos
   - Incluir: frame_id, track_id, x, y, type, code
   - StreamingResponse
   - Header: content-disposition

3. GET /reports/:datasetId/pdf
   - Generar PDF con gráficos
   - Usar reportlab
   - Incluir: resumen, gráficos, tabla
```

**Frontend (`src/pages/ResultsPage.tsx`)**

```typescript
// TODO: Conectar con backend

1. En mount: GET /reports/:datasetId/summary
2. Mostrar cards con resumen
3. Mostrar tabla de movimientos
4. Botón "Descargar CSV": GET /reports/.../csv
5. Botón "Descargar PDF": GET /reports/.../pdf
```

#### Sub-tareas
- [ ] Implementar agregación de datos
- [ ] Generar CSV
- [ ] Implementar PDF (reportlab)
- [ ] Test: summary funciona
- [ ] Test: CSV se descarga
- [ ] Test: PDF se genera

#### Deliverables
- ✅ Resumen se muestra
- ✅ CSV se descarga
- ✅ PDF se genera

---

### Día 12: Implementar History (Paso 7)

#### Tarea Principal: Auditoría de Cambios

**Backend (`api/routers/history.py`)**

```python
# TODO: Implementar GET /history/:datasetId

1. Leer metadata.json y history.json
2. Generar timeline:
   [{id, action, version, timestamp, user, details}]
3. Retornar: {dataset_id, history, total_entries}
```

**Frontend (`src/pages/HistoryPage.tsx`)**

```typescript
// TODO: Conectar con backend

1. En mount: GET /history/:datasetId
2. Mostrar timeline de eventos
3. Mostrar versiones
4. Mostrar timestamps
```

#### Sub-tareas
- [ ] Crear history.json
- [ ] Registrar eventos en cada paso
- [ ] Generar timeline
- [ ] Test: eventos se registran
- [ ] Test: timeline se muestra

#### Deliverables
- ✅ History se registra
- ✅ Timeline se muestra

---

### Día 13: Testing & Quality

#### Comprehensive Testing

- [ ] Test completo: Upload → Historia
- [ ] Verificar que dataset_id persiste todo el flujo
- [ ] Verificar que cambios se guardan
- [ ] Verificar que PDFs se generan
- [ ] Verificar que CSVs se descargan

#### Code Quality

- [ ] Linting: `npm run lint` (frontend)
- [ ] Type checking: `npm run type-check`
- [ ] Backend: revisar imports y tipos
- [ ] Refactoring si es necesario

#### Documentation

- [ ] Actualizar documentación
- [ ] Crear `TEST_REPORT_WEEK2.md`
- [ ] Actualizar CHECKLIST_IMPLEMENTACION_7PASOS.md

---

### Día 14: Polish & Deployment Ready

#### Final Touches

- [ ] Error handling mejorado
- [ ] Loading states en UI
- [ ] Mensajes de error amigables
- [ ] Validaciones robustas

#### Performance

- [ ] Verificar tiempos de carga
- [ ] Optimizar queries
- [ ] Caché si es necesario

#### Deployment Prep

- [ ] Revisar código para producción
- [ ] Crear `.env.production`
- [ ] Verificar CORS en producción
- [ ] Crear README de deployment

---

## 📊 RESUMEN DE TAREAS

### Backend (Total: ~40 horas)

| Router | Tareas | Est. Horas | Estado |
|--------|--------|-----------|--------|
| datasets.py | Upload, List, Get | 6 | 📋 |
| config.py | View, Generate, Save, RILSA | 8 | 📋 |
| validation.py | Calcular stats | 6 | 📋 |
| editor.py | CRUD correcciones | 5 | 📋 |
| live.py | Normalizar, eventos | 8 | 📋 |
| reports.py | Summary, CSV, PDF | 8 | 📋 |
| history.py | Timeline, audit | 5 | 📋 |
| **Total** | | **46h** | |

### Frontend (Total: ~30 horas)

| Page | Tareas | Est. Horas | Estado |
|------|--------|-----------|--------|
| UploadPage | Upload real, validation | 4 | 📋 |
| ConfigPage | Canvas, editor real | 5 | 📋 |
| ValidationPage | Stats display | 3 | 📋 |
| EditorPage | Table editing | 4 | 📋 |
| AforoDetailPage | Canvas, playback | 6 | 📋 |
| ResultsPage | Download, display | 4 | 📋 |
| HistoryPage | Timeline | 3 | 📋 |
| **Total** | | **29h** | |

### Testing & QA (Total: ~15 horas)

| Item | Est. Horas |
|------|-----------|
| Manual Testing | 6 |
| Code Review | 4 |
| Bug Fixes | 3 |
| Documentation | 2 |
| **Total** | **15h** |

### **TOTAL ESTIMADO: 90 horas (~2 semanas a tiempo completo)**

---

## ⏰ CRONOGRAMA DETALLADO

```
LUNES 13:      Setup & Validación
MARTES 14:     Continuación validación + START Upload
MIÉRCOLES 15:  Upload + START Config
JUEVES 16:     Config + START Validation
VIERNES 17:    Validation + Buffer

SÁBADO 18:     Buffer & Testing
DOMINGO 19:    Buffer & Testing

LUNES 20:      START Editor
MARTES 21:     Editor + START Live
MIÉRCOLES 22:  Live + START Reports
JUEVES 23:     Reports + START History
VIERNES 24:    History + Final touches

SÁBADO 25:     Testing & Deployment Prep
DOMINGO 26:    Final Review & Documentation
```

---

## 🎯 SUCCESS CRITERIA

Al final de las 2 semanas, podrás:

- ✅ Subir un archivo PKL
- ✅ Configurar accesos y RILSA
- ✅ Validar estadísticas
- ✅ Editar trayectorias
- ✅ Visualizar datos en canvas
- ✅ Descargar reportes (CSV y PDF)
- ✅ Ver historial de cambios
- ✅ Flujo completo funcional

---

## 📞 CONTINGENCY PLAN

Si algo toma más tiempo:

| Si se atrasa | Plan B |
|-------------|--------|
| Upload (1-2 dias extra) | Usar mock upload primero, luego PKL |
| Config (1-2 dias extra) | Usar config pre-generado |
| Validation (1 dia extra) | Usar stats mock |
| Live (2-3 dias extra) | Canvas estático primero, luego animado |
| Reports (1 dia extra) | CSV primero, PDF después |

---

## 📈 PROGRESS TRACKING

### Crear archivo `PROGRESS_TRACKING.md`

```markdown
# Progress Tracking - AFOROS RILSA v3.0.2

## Semana 1
- [ ] Día 1-2: Setup OK
- [ ] Día 3: Upload DONE / IN PROGRESS / TODO
- [ ] Día 4: Config DONE / IN PROGRESS / TODO
- [ ] Día 5: Validation DONE / IN PROGRESS / TODO
- [ ] Día 6-7: Testing DONE / IN PROGRESS / TODO

## Semana 2
- [ ] Día 8-9: Editor DONE / IN PROGRESS / TODO
- [ ] Día 10: Live DONE / IN PROGRESS / TODO
- [ ] Día 11: Reports DONE / IN PROGRESS / TODO
- [ ] Día 12: History DONE / IN PROGRESS / TODO
- [ ] Día 13-14: Polish DONE / IN PROGRESS / TODO
```

---

## 🚀 NEXT STEPS

1. Guardar este documento
2. Abrir INICIO_INMEDIATO.md
3. Iniciar backend y frontend
4. Empezar con Día 1

**¡Adelante!** 💪

---

**Documento creado:** 13 de Enero de 2025
**Plan para:** 13-26 de Enero de 2025
**Versión:** AFOROS RILSA v3.0.2
