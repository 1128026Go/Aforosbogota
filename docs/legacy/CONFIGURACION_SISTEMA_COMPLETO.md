# AFOROS RILSA v3.0.2 - Sistema de Configuración de Datasets

## REGLAS SAGRADAS

✅ **Nunca cambies el flujo general ni endpoints existentes sin necesidad**
✅ **Puertos: Frontend 3000, API 3004**
✅ **Rutas: /api/v1 (todos los endpoints)**
✅ **Este paso de configuración es el corazón del sistema y no se rompe**

---

## ESTRUCTURA DEL PROYECTO

```
aforos/
├── api/                          # Backend FastAPI
│   ├── models/
│   │   ├── __init__.py
│   │   └── config.py             # DatasetConfig, AccessConfig, RilsaRule
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cardinals.py          # Lógica de detección y RILSA
│   │   └── persistence.py        # Guardar/cargar configuración
│   ├── routers/
│   │   ├── __init__.py
│   │   └── config.py             # Endpoints /api/v1/config/*
│   ├── main.py                   # App FastAPI
│   └── requirements.txt
│
└── apps/
    └── web/                      # Frontend React + TypeScript
        ├── src/
        │   ├── pages/
        │   │   └── DatasetConfigPage.tsx
        │   ├── components/
        │   │   ├── TrajectoryCanvas.tsx
        │   │   └── AccessEditorPanel.tsx
        │   ├── types/
        │   │   └── index.ts
        │   ├── lib/
        │   │   └── api.ts
        │   ├── App.tsx
        │   └── main.tsx
        ├── package.json
        ├── tsconfig.json
        ├── vite.config.ts
        └── tailwind.config.ts
```

---

## ENDPOINTS API (FastAPI - Puerto 3004)

### GET /api/v1/config/view/{dataset_id}
**Propósito:** Cargar configuración actual del dataset

**Respuesta:**
```json
{
  "dataset_id": "gx010323",
  "accesses": [...],
  "rilsa_rules": [...],
  "created_at": "2025-01-13T12:00:00",
  "updated_at": "2025-01-13T12:00:00"
}
```

### POST /api/v1/config/generate_accesses/{dataset_id}
**Propósito:** Generar propuesta automática de accesos

**Parámetros:**
- `image_width`: int (default: 1280)
- `image_height`: int (default: 720)
- `trajectories`: List[TrajectoryPoint] (body)

**Respuesta:**
```json
[
  {
    "id": "N",
    "cardinal": "N",
    "polygon": [[0, 0], [1280, 0], [1280, 108], [0, 108]],
    "centroid": [640, 54]
  },
  ...
]
```

### PUT /api/v1/config/save_accesses/{dataset_id}
**Propósito:** Guardar polígonos de accesos editados

**Body:**
```json
{
  "accesses": [
    {
      "id": "N",
      "cardinal": "N",
      "polygon": [...],
      "centroid": [640, 54]
    }
  ]
}
```

### POST /api/v1/config/generate_rilsa/{dataset_id}
**Propósito:** Generar reglas RILSA desde accesos definidos

**Respuesta:** DatasetConfig con rilsa_rules poblado

### GET /api/v1/config/rilsa_codes/{dataset_id}
**Propósito:** Obtener lista de códigos RILSA

**Respuesta:**
```json
[
  {
    "code": "1",
    "origin_access": "N",
    "dest_access": "S",
    "movement_type": "directo",
    "description": "1 – N → S (movimiento directo)"
  },
  ...
]
```

### DELETE /api/v1/config/reset/{dataset_id}
**Propósito:** Reiniciar configuración

---

## NOMENCLATURA SAGRADA RILSA

### Desde Norte (N)
| Código | Origen | Destino | Tipo | Descripción |
|--------|--------|---------|------|-------------|
| 1 | N | S | directo | Movimiento directo |
| 5 | N | E | izquierda | Giro a izquierda |
| 91 | N | O | derecha | Giro a derecha |
| 101 | N | N | retorno | Giro en U |

### Desde Sur (S)
| Código | Origen | Destino | Tipo | Descripción |
|--------|--------|---------|------|-------------|
| 2 | S | N | directo | Movimiento directo |
| 6 | S | O | izquierda | Giro a izquierda |
| 92 | S | E | derecha | Giro a derecha |
| 102 | S | S | retorno | Giro en U |

### Desde Oeste (O)
| Código | Origen | Destino | Tipo | Descripción |
|--------|--------|---------|------|-------------|
| 3 | O | E | directo | Movimiento directo |
| 7 | O | N | izquierda | Giro a izquierda |
| 93 | O | S | derecha | Giro a derecha |
| 103 | O | O | retorno | Giro en U |

### Desde Este (E)
| Código | Origen | Destino | Tipo | Descripción |
|--------|--------|---------|------|-------------|
| 4 | E | O | directo | Movimiento directo |
| 8 | E | S | izquierda | Giro a izquierda |
| 94 | E | N | derecha | Giro a derecha |
| 104 | E | E | retorno | Giro en U |

---

## FLUJO DE USO COMPLETO

### 1. INICIO
```
Usuario accede: http://localhost:3000?dataset=gx010323
```

### 2. CARGA
```
Frontend hace GET /api/v1/config/view/gx010323
└─ Si existe → carga configuración
└─ Si no existe → crea configuración vacía
```

### 3. VISUALIZACIÓN
```
Canvas muestra:
├─ Puntos de trayectorias (azul, semi-transparente)
└─ Polígonos de accesos (rojo N, azul S, verde E, ámbar O)
```

### 4. GENERACIÓN AUTOMÁTICA (Opcional)
```
Usuario: Click "Generar Accesos"
  ↓
Backend: POST /generate_accesses/gx010323
  ↓
Sistema analiza distribución de trayectorias
  ↓
Propone polígonos para N, S, E, O
  ↓
Frontend: Muestra propuesta en canvas
```

### 5. EDICIÓN MANUAL
```
Usuario: Selecciona acceso (N, S, E, O)
  ↓
Canvas: Muestra vértices en amarillo
  ↓
Usuario: Arrastra vértices para ajustar
  ↓
Sistema: Actualiza polígono en tiempo real
```

### 6. PERSISTENCIA
```
Usuario: Click "Guardar Accesos"
  ↓
Frontend: PUT /api/v1/config/save_accesses/gx010323
  ↓
Backend: Guarda en data/configs/gx010323/config.json
  ↓
Sistema: Persiste definiciones
```

### 7. GENERACIÓN RILSA
```
Usuario: Click "Generar Movimientos RILSA"
  ↓
Frontend: POST /api/v1/config/generate_rilsa/gx010323
  ↓
Backend: Genera todas las combinaciones (4x4=16 reglas)
  ↓
Sistema: Aplica Nomenclatura Sagrada automáticamente
  ↓
Frontend: Muestra tabla de códigos y descripciones
  ↓
Backend: Guarda en config.json
```

### 8. REVISIÓN FINAL
```
Sistema muestra:
├─ Resumen: 4 accesos definidos, 16 reglas RILSA
├─ Canvas: Polígonos y trayectorias
├─ Tabla: Todos los códigos RILSA generados
└─ Estado: Última actualización
```

---

## INSTALACIÓN Y EJECUCIÓN

### Backend (API - Puerto 3004)

```bash
# 1. Ir a carpeta api
cd aforos/api

# 2. Crear entorno virtual (opcional)
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
# o
uvicorn main:app --reload --port 3004 --host 0.0.0.0
```

Verificar: http://localhost:3004/docs (Swagger UI)

### Frontend (React - Puerto 3000)

```bash
# 1. Ir a carpeta web
cd aforos/apps/web

# 2. Instalar dependencias
npm install

# 3. Configurar variable de entorno (opcional)
echo "REACT_APP_API_URL=http://localhost:3004" > .env.local

# 4. Ejecutar desarrollo
npm run dev
```

Acceder: http://localhost:3000?dataset=gx010323

---

## DATOS PERSISTENTES

### Ubicación
```
data/configs/{dataset_id}/config.json
```

### Estructura
```json
{
  "dataset_id": "gx010323",
  "accesses": [
    {
      "id": "N",
      "cardinal": "N",
      "polygon": [[0, 0], [1280, 0], [1280, 108], [0, 108]],
      "centroid": [640, 54]
    },
    ...
  ],
  "rilsa_rules": [
    {
      "code": "1",
      "origin_access": "N",
      "dest_access": "S",
      "movement_type": "directo",
      "description": "1 – N → S (movimiento directo)"
    },
    ...
  ],
  "created_at": "2025-01-13T12:00:00",
  "updated_at": "2025-01-13T12:00:00"
}
```

---

## COMPONENTES CLAVE

### Backend

**`api/models/config.py`**
- `AccessConfig`: Definición de un acceso
- `RilsaRule`: Definición de una regla RILSA
- `DatasetConfig`: Configuración completa

**`api/services/cardinals.py`**
- `CardinalsService.generate_default_accesses()`: Crea propuesta automática
- `CardinalsService.generate_rilsa_rules()`: Genera códigos RILSA
- `CardinalsService.point_in_polygon()`: Test de puntos en polígono

**`api/services/persistence.py`**
- `ConfigPersistenceService.load_config()`: Lee de disco
- `ConfigPersistenceService.save_config()`: Escribe en disco

### Frontend

**`pages/DatasetConfigPage.tsx`**
- Página principal del sistema
- Maneja estado global de config
- Orquesta llamadas a API

**`components/TrajectoryCanvas.tsx`**
- Canvas HTML5 para visualización
- Renderiza trayectorias y polígonos
- Permite edición interactiva de vértices

**`components/AccessEditorPanel.tsx`**
- Panel lateral de selección de accesos
- Muestra vértices actuales
- Botón para reiniciar polígono

**`lib/api.ts`**
- Cliente HTTP (fetch)
- Métodos para todos los endpoints
- Manejo de errores

---

## VALIDACIONES Y SEGURIDAD

✅ **Backend valida:**
- Accesos con cardinal válido (N, S, E, O)
- Polígonos con al menos 3 vértices
- Coordenadas dentro del rango (0, imageWidth/Height)

✅ **Frontend valida:**
- Campo dataset_id no vacío
- Accesos seleccionados antes de guardar
- Error handling y feedback al usuario

---

## TESTING RÁPIDO

### Curl - Generar Accesos
```bash
curl -X POST http://localhost:3004/api/v1/config/generate_accesses/gx010323 \
  -H "Content-Type: application/json" \
  -d '{"trajectories": []}'
```

### Curl - Guardar Accesos
```bash
curl -X PUT http://localhost:3004/api/v1/config/save_accesses/gx010323 \
  -H "Content-Type: application/json" \
  -d '{
    "accesses": [
      {
        "id": "N",
        "cardinal": "N",
        "polygon": [[0, 0], [1280, 0], [1280, 108], [0, 108]],
        "centroid": [640, 54]
      }
    ]
  }'
```

### Curl - Generar RILSA
```bash
curl -X POST http://localhost:3004/api/v1/config/generate_rilsa/gx010323 \
  -H "Content-Type: application/json"
```

---

## TROUBLESHOOTING

### "Connection refused" en puerto 3004
```
✓ Verificar que la API está ejecutándose
✓ Verificar puerto no bloqueado
✓ Revisar firewall
```

### "CORS error" en frontend
```
✓ Verificar que CORS está habilitado en FastAPI
✓ Comprobar que REACT_APP_API_URL es correcto
✓ Revisar que la API está en http://localhost:3004
```

### Polígonos no se guardan
```
✓ Verificar que data/configs/{dataset_id}/ existe
✓ Comprobar permisos de escritura en data/
✓ Revisar logs del backend
```

### Canvas no muestra trayectorias
```
✓ Verificar que hay puntos en el array trajectories
✓ Comprobar coordenadas dentro de imageWidth/Height
✓ Revisar console del navegador (F12)
```

---

## PRÓXIMOS PASOS

1. ✅ **Sistema de configuración completado**
2. 📊 **Integrar con pipeline de procesamiento de video**
3. 📈 **Dashboard de aforos en tiempo real**
4. 🔄 **Sincronización con base de datos**
5. 📱 **Versión mobile**

---

**AFOROS RILSA v3.0.2**
*El corazón del sistema de aforos vehiculares*
*Configuración centralizada, nomenclatura consistente, movimientos exactos*
