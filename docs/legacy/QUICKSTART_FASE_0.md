# ⚡ GUÍA RÁPIDA - FASE 0 COMPLETADA

**Última actualización:** 14 de Enero de 2025

---

## 🎯 De un vistazo

✅ **Documentación:** Plan de 4 semanas + Resumen ejecutivo  
✅ **Tipos:** 18+ interfaces TypeScript + 20+ modelos Pydantic  
✅ **Funciones:** 2 funciones puras (CSV parser + validador)  
✅ **Tests:** 69 tests unitarios (todos pasan)

---

## 📂 Estructura de Carpetas

```
c:\Users\David\aforos\
├── PLAN_EJECUCION_COMPLETO.md      ← Roadmap de 4 semanas
├── FASE_0_COMPLETADA.md             ← Resumen de lo hecho
├── MANIFEST_FASE_0.md               ← Índice de archivos
│
├── api/
│   ├── domain/
│   │   ├── csvParsing.py            ← Función: parsear CSV ✅
│   │   └── aforoValidation.py       ← Función: validar aforos ✅
│   └── models/
│       └── aforoModels.py           ← Pydantic models ✅
│
├── apps/web/src/lib/types/
│   └── aforoTypes.ts                ← TypeScript types ✅
│
├── tests/
│   ├── test_csvParsing.py           ← 43 tests ✅
│   ├── test_aforoValidation.py      ← 26 tests ✅
│   ├── conftest.py                  ← Config pytest ✅
│   └── README.md                    ← Guía de testing
│
└── run_tests.py                     ← Script para ejecutar tests
```

---

## 🔍 Qué Hay en Cada Archivo

### 1️⃣ `csvParsing.py` - Parse CSV

```python
# Función principal
parsear_csv_aforos(contenido: str, encoding: str) → ParseResult

# Valida:
✅ Headers presentes (fecha, zonaId, horaInicio, horaFin, capacidadMaxima)
✅ Formato fecha (YYYY-MM-DD)
✅ Formato hora (HH:mm)
✅ Lógica: horaFin > horaInicio
✅ Capacidad > 0
✅ Aforos >= 0
```

**Retorna:**
```python
ParseResult(
    registros=[{...}, ...],     # Registros válidos
    errores=[{...}, ...],       # Errores encontrados
    totalFilas=3,               # Total de filas
    filasExitosas=2             # Filas sin errores
)
```

---

### 2️⃣ `aforoValidation.py` - Validación Matemática

```python
# Función principal
validar_aforos(uploadId, registros, config) → ValidationResult

# Hace:
✅ Valida registros individuales
✅ Genera slots horarios (5/15/30/60 min)
✅ Calcula aforo agregado (con solapamientos)
✅ Aplica máquina de estados:
   - OK: ratio < 0.8
   - ADVERTENCIA: 0.8 ≤ ratio < 1.0
   - CRÍTICO: ratio ≥ 1.0
```

**Retorna:**
```python
ValidationResult(
    uploadId="upload1",
    serieTemporal=[TimeSlotPoint(...), ...],
    erroresPorRegistro={"reg1": [ValidationError(...), ...]},
    valido=True,
    totalErrores=0
)
```

---

### 3️⃣ `aforoTypes.ts` - Tipos TypeScript

```typescript
// Interfaces principales
interface AforoRecord { ... }
interface AforoConfig { ... }
interface TimeSlotPoint { ... }
interface ValidationResult { ... }
interface AforoUpload { ... }

// Enums
enum TimeSlotState { OK, ADVERTENCIA, CRÍTICO }
enum UploadStatus { PENDING, VALIDATED, APPROVED }
enum ValidationErrorType { PARSING, REQUERIDO, TIPO, LOGICA }
```

**Uso en React:**
```typescript
import { AforoRecord, TimeSlotPoint } from '@/lib/types/aforoTypes';

const [record, setRecord] = useState<AforoRecord>(...);
const [serie, setSerie] = useState<TimeSlotPoint[]>([]);
```

---

### 4️⃣ `aforoModels.py` - Pydantic Models

```python
# Para requests
class AforoRecordCreate(BaseModel):
    fecha: str
    zonaId: str
    horaInicio: str
    horaFin: str
    capacidadMaxima: int
    aforoPlanificado: Optional[int] = None

# Para responses
class AforoRecord(AforoRecordCreate):
    id: str
    uploadId: str
    createdAt: datetime
```

**Uso en FastAPI:**
```python
@router.post("/records")
async def create_record(record: AforoRecordCreate):
    # FastAPI valida automáticamente
    ...
```

---

## ✅ Tests

### Ejecutar todos

```bash
python run_tests.py
```

### Ver resultados

```bash
python -m pytest tests/ -v
```

### Con coverage

```bash
python -m pytest tests/ --cov=api.domain --cov-report=html
```

### Tests disponibles

**CSV Parser (43 tests):**
- Headers válidos/inválidos
- Formatos de fecha, hora, números
- Validación de campos
- Manejo de errores
- Datos especiales (UTF-8, comillas, etc.)

**Validación (26 tests):**
- Funciones de utilidad
- Validación de campos
- Serie temporal
- Máquina de estados (OK/ADVERTENCIA/CRÍTICO)
- Solapamientos de registros
- Múltiples zonas

---

## 🚀 Próximos Pasos (Fase 1)

### Backend Routers a Crear

```python
# api/routers/datasets.py
@router.post("/api/v1/uploads")
async def upload_csv(file: UploadFile):
    resultado = parsear_csv_aforos(await file.read())
    # Guardar en DB
    return resultado

# api/routers/validation.py
@router.post("/api/v1/validate/{uploadId}")
async def validate(uploadId: str, config: AforoConfig):
    registros = await db.get_registros(uploadId)
    resultado = validar_aforos(uploadId, registros, config.dict())
    # Guardar resultado en DB
    return resultado
```

### Frontend Pages a Crear

```typescript
// apps/web/src/pages/UploadPage.tsx
import { AforoRecord } from '@/lib/types/aforoTypes';

export default function UploadPage() {
    const [file, setFile] = useState<File | null>(null);
    const handleUpload = async () => {
        const result = await api.uploadCsv(file);
        // result es ParseResult
    };
}

// apps/web/src/pages/ValidationPage.tsx
export default function ValidationPage() {
    const [config, setConfig] = useState<AforoConfig>(...);
    const result = await api.validate(uploadId, config);
    // result es ValidationResult
    // result.serieTemporal → para gráficos
}
```

---

## 📋 Checklist para Fase 1

- [ ] Crear `api/routers/datasets.py` (POST /uploads)
- [ ] Crear `api/routers/config.py` (GET/POST /config)
- [ ] Crear `api/routers/validation.py` (POST /validate)
- [ ] Crear `api/routers/editor.py` (GET/PUT /records)
- [ ] Crear `UploadPage.tsx`
- [ ] Crear `ConfigPage.tsx`
- [ ] Crear `ValidationPage.tsx`
- [ ] Crear `FileUpload.tsx` component
- [ ] Actualizar `api.ts` con nuevas rutas
- [ ] Crear `useUpload` hook
- [ ] Crear `useValidation` hook

---

## 🔗 Referencia Rápida

### Tipos más importantes

```typescript
// Frontend
AforoRecord       // Un registro de aforo
AforoConfig       // Configuración de validación
TimeSlotPoint     // Punto en serie temporal
ValidationResult  // Resultado de validación
```

### Funciones más importantes

```python
# Backend
parsear_csv_aforos(str) → ParseResult
validar_aforos(str, List, Dict) → ValidationResult
```

### Validaciones soportadas

| Campo | Tipo | Validación |
|-------|------|-----------|
| fecha | str | YYYY-MM-DD |
| horaInicio | str | HH:mm (00:00-23:59) |
| horaFin | str | HH:mm, fin > inicio |
| zonaId | str | No vacío |
| capacidadMaxima | int | > 0 |
| aforoPlanificado | int | >= 0 (opcional) |
| aforoReal | int | >= 0 (opcional) |

---

## 🎓 Conceptos Clave

### Estado de un Slot
- **OK:** ocupación < 80% → Capacidad normal
- **ADVERTENCIA:** 80% ≤ ocupación < 100% → Acercándose al límite
- **CRÍTICO:** ocupación ≥ 100% → Sobre-capacidad

### Serie Temporal
Agregación de registros por hora/zona en slots discretos.
Incluye:
- Fecha, zonaId, horas
- Aforo agregado
- Capacidad
- Ratio de uso
- Estado
- IDs de registros que contribuyeron

### Solapamientos
Cuando dos registros cubren el mismo período, sus aforos se suman.
Ejemplo:
```
Registro 1: 09:00-10:00 → aforo 30
Registro 2: 09:30-10:30 → aforo 40
Slot 09:00-10:00 → aforo = 30 + 30 = 60 (solo 30 min de registro 2)
Slot 10:00-10:30 → aforo = 40
```

---

## 💡 Tips

1. **Ejecutar tests antes de cambiar código**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Revisar tests para entender comportamiento**
   - Ver `tests/test_csvParsing.py` para ejemplos de uso
   - Ver `tests/test_aforoValidation.py` para casos de error

3. **Usar conftest.py para fixtures compartidas**
   - Agregar setup común ahí
   - Los tests pueden acceder como parámetros

4. **Tests son documentación viva**
   - Muestran cómo se usan las funciones
   - Documentan casos exitosos y de error

---

## ❓ Preguntas Frecuentes

**P: ¿Dónde agrego nuevas validaciones CSV?**  
R: En `csvParsing.py`, en la función `parsear_csv_aforos()`. Agregar test en `test_csvParsing.py`.

**P: ¿Cómo cambio los umbrales de ADVERTENCIA/CRÍTICO?**  
R: En `aforoValidation.py`, la config tiene `umbralAdvertencia` (0.8) y `umbralCritico` (1.0).

**P: ¿Puedo cambiar el intervalo de discretización?**  
R: Sí, en config: `intervaloMinutos` (default 15). Soporta 5, 15, 30, 60.

**P: ¿Cómo accedo a los tipos desde React?**  
R: `import { AforoRecord } from '@/lib/types/aforoTypes'`

**P: ¿Qué hago si un test falla?**  
R: Leer el mensaje de error, revisar el test para entender qué falta, arreglarlo y re-ejecutar.

---

## 📞 Contacto/Soporte

- Revisar documentación en archivos `.md`
- Ver tests para ejemplos
- Verificar PLAN_EJECUCION_COMPLETO.md para roadmap

---

**Status:** ✅ LISTO  
**Tests:** ✅ 69 tests pasan  
**Documentación:** ✅ Completa  
**Siguiente:** 🚀 Fase 1 - Backend Routers
