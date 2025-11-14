# ARQUITECTURA TÉCNICA - AFOROS RILSA v3.0.2

## OVERVIEW GENERAL

El sistema está dividido en dos capas bien definidas:

```
┌─────────────────────────────────────────┐
│     FRONTEND (React + TypeScript)       │ Puerto 3000
│  - UI interactiva                       │
│  - Visualización Canvas                 │
│  - Gestión de estado local              │
└────────────────┬────────────────────────┘
                 │ HTTP/REST
                 ↓
        ┌────────────────────┐
        │  NGINX/Proxy       │ (opcional)
        └────────────────────┘
                 │ HTTP/REST
                 ↓
┌─────────────────────────────────────────┐
│     BACKEND (FastAPI + Python)          │ Puerto 3004
│  - API REST                             │
│  - Lógica de negocio                    │
│  - Persistencia en disco                │
└─────────────────────────────────────────┘
                 ↓
        ┌────────────────────┐
        │ Filesystem (JSON)  │
        │ data/configs/      │
        └────────────────────┘
```

---

## BACKEND (FastAPI)

### Estructura de Carpetas

```
api/
├── models/
│   ├── __init__.py
│   └── config.py              # Pydantic models
├── services/
│   ├── __init__.py
│   ├── cardinals.py           # Lógica de detección y generación RILSA
│   └── persistence.py         # I/O a disco
├── routers/
│   ├── __init__.py
│   └── config.py              # Endpoints HTTP
├── main.py                    # FastAPI app
└── requirements.txt
```

### Modelos Pydantic (config.py)

```python
class AccessConfig:
    id: str                              # "N", "S", "E", "O"
    cardinal: Literal["N", "S", "E", "O"]
    polygon: List[Tuple[float, float]]   # [(x1,y1), (x2,y2), ...]
    centroid: Optional[Tuple[float, float]]

class RilsaRule:
    code: str                           # "1", "91", "101", etc.
    origin_access: Literal["N", "S", "E", "O"]
    dest_access: Literal["N", "S", "E", "O"]
    movement_type: Literal["directo", "izquierda", "derecha", "retorno"]
    description: str                    # "1 – N → S (movimiento directo)"

class DatasetConfig:
    dataset_id: str
    accesses: List[AccessConfig]
    rilsa_rules: List[RilsaRule]
    created_at: datetime
    updated_at: datetime
```

### CardinalsService

**Responsabilidades:**
- Generar propuestas automáticas de accesos
- Generar reglas RILSA según nomenclatura
- Algoritmos de geometría (point-in-polygon)

**Métodos clave:**

```python
@staticmethod
def generate_default_accesses(
    trajectories: List[Dict],
    image_width: int = 1280,
    image_height: int = 720
) -> List[AccessConfig]:
    """
    Analiza distribución de trayectorias y propone
    polígonos para N, S, E, O.
    
    Algoritmo:
    1. Divide imagen en 4 zonas (bordes 15%)
    2. Crea polígonos rectangulares iniciales
    3. Calcula centroides
    
    Resultado: 4 AccessConfig con polígonos propuestos
    """

@staticmethod
def generate_rilsa_rules(accesses: List[AccessConfig]) -> List[RilsaRule]:
    """
    Genera todas las combinaciones cartesianas de accesos
    y aplica la Nomenclatura Sagrada.
    
    Algoritmo:
    1. Para cada cardinal origen (N, S, E, O)
    2. Para cada cardinal destino (N, S, E, O)
    3. Buscar en RILSA_MAPPING
    4. Crear RilsaRule con código y descripción
    
    Resultado: 16 reglas (4x4)
    """

@staticmethod
def point_in_polygon(point, polygon) -> bool:
    """Ray casting algorithm para test de punto en polígono"""

@staticmethod
def calculate_centroid(polygon) -> Tuple[float, float]:
    """Media aritmética de vértices"""
```

### ConfigPersistenceService

**Responsabilidades:**
- Leer/escribir JSON desde disco
- Gestionar directorios
- Serialización/deserialización

**Métodos:**

```python
@classmethod
def load_config(dataset_id: str) -> Optional[DatasetConfig]:
    """Lee config.json del dataset"""
    # Ruta: data/configs/{dataset_id}/config.json

@classmethod
def save_config(config: DatasetConfig) -> bool:
    """Escribe config.json, crea directorios si no existen"""

@classmethod
def create_default_config(dataset_id: str) -> DatasetConfig:
    """Crea config vacía para dataset nuevo"""
```

### Routers (config.py)

**Endpoints disponibles:**

| Ruta | Método | Función |
|------|--------|---------|
| `/api/v1/config/view/{dataset_id}` | GET | ViewConfigResponse |
| `/api/v1/config/generate_accesses/{dataset_id}` | POST | GenerateAccessesResponse |
| `/api/v1/config/save_accesses/{dataset_id}` | PUT | SaveAccessesResponse |
| `/api/v1/config/generate_rilsa/{dataset_id}` | POST | GenerateRilsaResponse |
| `/api/v1/config/rilsa_codes/{dataset_id}` | GET | GetRilsaCodesResponse |
| `/api/v1/config/reset/{dataset_id}` | DELETE | ResetResponse |

**Validaciones por endpoint:**

```python
@router.put("/save_accesses/{dataset_id}")
async def save_accesses(dataset_id: str, update: AccessPolygonUpdate):
    # Validar:
    # ✓ dataset_id no vacío
    # ✓ accesses tiene cardinal válido
    # ✓ polygons tiene mínimo 3 puntos (si no está vacío)
    # ✓ Coordenadas dentro de rango
    
@router.post("/generate_rilsa/{dataset_id}")
async def generate_rilsa(dataset_id: str):
    # Validar:
    # ✓ Config existe
    # ✓ Hay al menos 1 acceso definido
    # ✓ Cada acceso tiene cardinal único
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3004",
        "127.0.0.1"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## FRONTEND (React + TypeScript)

### Estructura de Carpetas

```
apps/web/src/
├── pages/
│   └── DatasetConfigPage.tsx        # Componente raíz
├── components/
│   ├── TrajectoryCanvas.tsx         # Canvas HTML5
│   └── AccessEditorPanel.tsx        # Panel lateral
├── types/
│   └── index.ts                     # Types TypeScript
├── lib/
│   └── api.ts                       # Cliente HTTP
├── App.tsx                          # Wrapper
└── main.tsx                         # Entry point React
```

### Type System (types/index.ts)

```typescript
export type Cardinal = "N" | "S" | "E" | "O";
export type MovementType = "directo" | "izquierda" | "derecha" | "retorno";

export interface AccessConfig {
  id: string;
  cardinal: Cardinal;
  polygon: [number, number][];
  centroid?: [number, number];
}

export interface RilsaRule {
  code: string;
  origin_access: Cardinal;
  dest_access: Cardinal;
  movement_type: MovementType;
  description: string;
}

export interface DatasetConfig {
  dataset_id: string;
  accesses: AccessConfig[];
  rilsa_rules: RilsaRule[];
  created_at: string;
  updated_at: string;
}
```

### API Client (lib/api.ts)

```typescript
const api = {
  async viewConfig(datasetId: string): Promise<DatasetConfig>
  async generateAccesses(datasetId: string, options?: {...}): Promise<AccessConfig[]>
  async saveAccesses(datasetId: string, update: AccessPolygonUpdate): Promise<DatasetConfig>
  async generateRilsaRules(datasetId: string): Promise<DatasetConfig>
  async getRilsaCodes(datasetId: string): Promise<RilsaRule[]>
  async resetConfig(datasetId: string): Promise<{message: string}>
}
```

### TrajectoryCanvas Component

**Props:**
```typescript
interface TrajectoryCanvasProps {
  trajectories: TrajectoryPoint[];      // Puntos a visualizar
  accesses: AccessConfig[];              // Polígonos a mostrar
  selectedAccess: Cardinal | null;       // Cardinal seleccionado
  onAccessPolygonChange: (cardinal, polygon) => void;  // Callback
  imageWidth?: number;                   // Default 1280
  imageHeight?: number;                  // Default 720
  editable?: boolean;                    // Modo edición
}
```

**Funcionalidades:**
- Canvas HTML5 fullscreen
- Renderiza trayectorias como puntos azules
- Renderiza polígonos con colores por cardinal
- Edición: drag de vértices
- Grid de fondo
- Zoom automático para ajustar al canvas

**Eventos:**
```javascript
canvasRef.onmousedown = (e) => {
  // Detectar si hace click en vértice
  // Si sí, iniciar drag
}

canvasRef.onmousemove = (e) => {
  // Si dragging, actualizar posición vértice
  // Callback: onAccessPolygonChange
}

canvasRef.onmouseup = () => {
  // Finalizar drag
}
```

### AccessEditorPanel Component

**Props:**
```typescript
interface AccessEditorPanelProps {
  accesses: AccessConfig[];
  selectedAccess: Cardinal | null;
  onSelectAccess: (cardinal | null) => void;
  onAccessChange: (access) => void;
  onRemovePolygon: (cardinal) => void;
  editable?: boolean;
}
```

**UI:**
- 4 botones (uno por cardinal)
- Color único por cardinal
- Estado visual del botón seleccionado
- Muestra número de vértices
- Lista de vértices en modo edición
- Botón "Reiniciar polígono"
- Leyenda de colores

### DatasetConfigPage Component

**Estado:**
```typescript
const [config, setConfig] = useState<DatasetConfig | null>();
const [trajectories, setTrajectories] = useState<TrajectoryPoint[]>([]);
const [selectedAccess, setSelectedAccess] = useState<Cardinal | null>();
const [loading, setLoading] = useState(true);
const [saving, setSaving] = useState(false);
const [generating, setGenerating] = useState(false);
const [error, setError] = useState<string | null>();
const [success, setSuccess] = useState<string | null>();
```

**Flujo de interacción:**

```
1. useEffect montaje
   └─ loadConfig() via api.viewConfig()

2. User: Click "Generar Accesos"
   ├─ handleGenerateAccesses()
   ├─ api.generateAccesses()
   └─ setConfig({...accesses: result})

3. User: Edita polígono en canvas
   ├─ TrajectoryCanvas.onAccessPolygonChange()
   ├─ handleAccessPolygonChange()
   └─ setConfig({...accesses: updated})

4. User: Click "Guardar Accesos"
   ├─ handleSaveAccesses()
   ├─ api.saveAccesses({accesses: config.accesses})
   └─ setConfig(result)

5. User: Click "Generar RILSA"
   ├─ handleGenerateRilsa()
   ├─ api.generateRilsaRules()
   └─ setConfig({...rilsa_rules: result})
```

### Tailwind + CSS

**Configuración:**
- `tailwind.config.ts`: Theme personalizado
- `postcss.config.js`: Procesar Tailwind
- `App.css`: Directives @tailwind

**Clases utilizadas:**
```
Layout:
├─ max-w-7xl mx-auto px-4 (contenedor)
├─ grid grid-cols-1 lg:grid-cols-4 gap-6 (responsive)
└─ bg-gradient-to-br from-slate-50 via-blue-50 (fondo)

Tarjetas:
├─ bg-white rounded-2xl shadow-sm
├─ border border-slate-200
└─ p-6

Botones:
├─ px-4 py-2 rounded-lg font-medium
├─ bg-blue-500 text-white hover:bg-blue-600
└─ disabled:bg-gray-300

Alertas:
├─ bg-red-50 border border-red-200 rounded-lg
├─ bg-green-50 border border-green-200 rounded-lg
└─ p-4 text-sm
```

---

## FLUJO DE DATOS

### Secuencia: Cargar → Generar → Editar → Guardar → Generar RILSA

```
USER
  │
  ├─ Abre: http://localhost:3000?dataset=gx010323
  │   ├─ Frontend: Parse URL parameters
  │   └─ Extract: dataset_id = "gx010323"
  │
  ├─ useEffect (montaje)
  │   └─ loadConfig()
  │       ├─ GET /api/v1/config/view/gx010323
  │       ├─ Backend: load_config("gx010323")
  │       │   ├─ Si existe: return DatasetConfig
  │       │   └─ Si no existe: return empty config
  │       └─ Frontend: setConfig(result)
  │
  ├─ Visualización
  │   └─ TrajectoryCanvas
  │       ├─ Dibuja trayectorias (si existen)
  │       └─ Dibuja polígonos de accesos (vacíos si nuevo)
  │
  ├─ Click "Generar Accesos"
  │   └─ handleGenerateAccesses()
  │       ├─ POST /api/v1/config/generate_accesses/gx010323
  │       ├─ Backend: CardinalsService.generate_default_accesses()
  │       │   ├─ Analiza trayectorias
  │       │   ├─ Propone polígonos N, S, E, O
  │       │   └─ return List[AccessConfig]
  │       └─ Frontend: Canvas actualiza con propuesta
  │
  ├─ Edición manual
  │   ├─ User selecciona cardinal (N/S/E/O)
  │   ├─ User arrastra vértices en canvas
  │   └─ handleAccessPolygonChange()
  │       └─ setConfig({...accesses: updated})
  │
  ├─ Click "Guardar Accesos"
  │   └─ handleSaveAccesses()
  │       ├─ PUT /api/v1/config/save_accesses/gx010323
  │       ├─ Body: {accesses: [...]}
  │       ├─ Backend: ConfigPersistenceService.save_config()
  │       │   ├─ Valida accesos
  │       │   ├─ Crea data/configs/gx010323/ si no existe
  │       │   ├─ Escribe config.json
  │       │   └─ return updated DatasetConfig
  │       └─ Frontend: success message
  │
  ├─ Click "Generar Movimientos RILSA"
  │   └─ handleGenerateRilsa()
  │       ├─ POST /api/v1/config/generate_rilsa/gx010323
  │       ├─ Backend: CardinalsService.generate_rilsa_rules()
  │       │   ├─ Obtiene accesos desde config
  │       │   ├─ Para cada (origen, destino)
  │       │   │   ├─ Busca en RILSA_MAPPING
  │       │   │   └─ Crea RilsaRule
  │       │   ├─ Resultado: 16 reglas
  │       │   ├─ ConfigPersistenceService.save_config()
  │       │   └─ return updated DatasetConfig
  │       └─ Frontend: Muestra tabla de códigos RILSA
  │
  └─ Visualización final
      ├─ Canvas: Polígonos N, S, E, O
      ├─ Tabla: Todos los códigos RILSA
      └─ Estado: 4 accesos, 16 reglas
```

---

## PERSISTENCIA (Filesystem)

### Estructura de Directorios

```
data/
├── configs/
│   └── {dataset_id}/              # Uno por dataset
│       └── config.json            # Archivo persistente
└── [otros directorios]
```

### Formato de config.json

```json
{
  "dataset_id": "gx010323",
  "accesses": [
    {
      "id": "N",
      "cardinal": "N",
      "polygon": [[0, 0], [1280, 0], [1280, 108], [0, 108]],
      "centroid": [640.0, 54.0]
    },
    {
      "id": "S",
      "cardinal": "S",
      "polygon": [[0, 612], [1280, 612], [1280, 720], [0, 720]],
      "centroid": [640.0, 666.0]
    },
    {
      "id": "E",
      "cardinal": "E",
      "polygon": [[1088, 0], [1280, 0], [1280, 720], [1088, 720]],
      "centroid": [1184.0, 360.0]
    },
    {
      "id": "O",
      "cardinal": "O",
      "polygon": [[0, 0], [192, 0], [192, 720], [0, 720]],
      "centroid": [96.0, 360.0]
    }
  ],
  "rilsa_rules": [
    {
      "code": "1",
      "origin_access": "N",
      "dest_access": "S",
      "movement_type": "directo",
      "description": "1 – N → S (movimiento directo)"
    },
    {
      "code": "2",
      "origin_access": "S",
      "dest_access": "N",
      "movement_type": "directo",
      "description": "2 – S → N (movimiento directo)"
    },
    {
      "code": "3",
      "origin_access": "O",
      "dest_access": "E",
      "movement_type": "directo",
      "description": "3 – O → E (movimiento directo)"
    },
    {
      "code": "4",
      "origin_access": "E",
      "dest_access": "O",
      "movement_type": "directo",
      "description": "4 – E → O (movimiento directo)"
    },
    {
      "code": "5",
      "origin_access": "N",
      "dest_access": "E",
      "movement_type": "izquierda",
      "description": "5 – N → E (giro izquierda)"
    },
    {
      "code": "6",
      "origin_access": "S",
      "dest_access": "O",
      "movement_type": "izquierda",
      "description": "6 – S → O (giro izquierda)"
    },
    {
      "code": "7",
      "origin_access": "O",
      "dest_access": "N",
      "movement_type": "izquierda",
      "description": "7 – O → N (giro izquierda)"
    },
    {
      "code": "8",
      "origin_access": "E",
      "dest_access": "S",
      "movement_type": "izquierda",
      "description": "8 – E → S (giro izquierda)"
    },
    {
      "code": "91",
      "origin_access": "N",
      "dest_access": "O",
      "movement_type": "derecha",
      "description": "91 – N → O (giro derecha)"
    },
    {
      "code": "92",
      "origin_access": "S",
      "dest_access": "E",
      "movement_type": "derecha",
      "description": "92 – S → E (giro derecha)"
    },
    {
      "code": "93",
      "origin_access": "O",
      "dest_access": "S",
      "movement_type": "derecha",
      "description": "93 – O → S (giro derecha)"
    },
    {
      "code": "94",
      "origin_access": "E",
      "dest_access": "N",
      "movement_type": "derecha",
      "description": "94 – E → N (giro derecha)"
    },
    {
      "code": "101",
      "origin_access": "N",
      "dest_access": "N",
      "movement_type": "retorno",
      "description": "101 – N → N (giro en U)"
    },
    {
      "code": "102",
      "origin_access": "S",
      "dest_access": "S",
      "movement_type": "retorno",
      "description": "102 – S → S (giro en U)"
    },
    {
      "code": "103",
      "origin_access": "O",
      "dest_access": "O",
      "movement_type": "retorno",
      "description": "103 – O → O (giro en U)"
    },
    {
      "code": "104",
      "origin_access": "E",
      "dest_access": "E",
      "movement_type": "retorno",
      "description": "104 – E → E (giro en U)"
    }
  ],
  "created_at": "2025-01-13T12:00:00",
  "updated_at": "2025-01-13T12:34:56"
}
```

---

## SEGURIDAD Y VALIDACIÓN

### Validaciones Backend

```python
# En router/config.py
def validate_access_config(access: AccessConfig):
    ✓ cardinal en ["N", "S", "E", "O"]
    ✓ polygon vacío OR tiene >= 3 puntos
    ✓ cada punto: 0 <= x <= imageWidth, 0 <= y <= imageHeight
    ✓ id es string no vacío

def validate_dataset_id(dataset_id: str):
    ✓ No vacío
    ✓ Caracteres válidos (alphanumeric, guión)
```

### Validaciones Frontend

```typescript
// En components/TrajectoryCanvas.tsx
function validatePolygon(polygon: [number, number][]): boolean {
  ✓ polygon.length >= 3 || polygon.length === 0
  ✓ Cada punto: x, y son números válidos
}

// En pages/DatasetConfigPage.tsx
function canGenerateRilsa(config: DatasetConfig): boolean {
  ✓ config.accesses.length > 0
  ✓ Todos tienen cardinal definido
}
```

### CORS

- Solo localhost (desarrollo)
- Producción: agregar dominio específico
- Métodos: GET, POST, PUT, DELETE
- Headers: application/json

---

## ESCALABILIDAD

### Próximas versiones

1. **Base de Datos**
   - MongoDB o PostgreSQL
   - Reemplazar filesystem
   - Soporte multi-usuario

2. **Autenticación**
   - JWT tokens
   - Roles: admin, editor, viewer

3. **WebSocket**
   - Real-time updates
   - Colaboración multi-usuario

4. **Cache**
   - Redis para configs frecuentes
   - Invalidación automática

5. **Generación de reportes**
   - PDF de configuración
   - Estadísticas de movimientos

---

**AFOROS RILSA v3.0.2**
*Arquitectura modular, escalable y mantenible*
