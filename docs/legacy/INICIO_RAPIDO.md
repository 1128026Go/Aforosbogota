# GUÍA RÁPIDA - AFOROS RILSA v3.0.2

## ⚡ INICIO RÁPIDO (5 minutos)

### Windows
```batch
# 1. Ejecutar script
start.bat

# 2. Abrir en navegador
http://localhost:3000?dataset=gx010323
```

### Linux/Mac
```bash
# 1. Dar permisos
chmod +x start.sh

# 2. Ejecutar
./start.sh

# 3. Abrir en navegador
http://localhost:3000?dataset=gx010323
```

---

## 📋 FLUJO DE USO

### Paso 1: Cargar Dataset
```
URL: http://localhost:3000?dataset=gx010323
└─ Automáticamente carga/crea configuración
```

### Paso 2: Generar o Editar Accesos
```
Opción A - Automático:
  ├─ Click "Generar Accesos"
  ├─ Sistema propone N, S, E, O
  └─ Edita si es necesario

Opción B - Manual:
  ├─ Selecciona un cardinal (N/S/E/O)
  ├─ Dibuja en el canvas
  └─ El sistema lo guarda
```

### Paso 3: Guardar Accesos
```
Click "Guardar Accesos"
└─ Persiste en data/configs/{dataset_id}/config.json
```

### Paso 4: Generar Movimientos RILSA
```
Click "Generar Movimientos RILSA"
├─ Sistema genera 16 reglas (4x4 combinaciones)
├─ Aplica Nomenclatura Sagrada automáticamente
├─ Muestra tabla de códigos
└─ Guarda en config.json
```

---

## 🔑 CÓDIGOS RILSA (Nomenclatura Sagrada)

### Desde NORTE (N)
```
1   → S (directo)
5   → E (izquierda)
91  → O (derecha)
101 → N (retorno)
```

### Desde SUR (S)
```
2   → N (directo)
6   → O (izquierda)
92  → E (derecha)
102 → S (retorno)
```

### Desde OESTE (O)
```
3   → E (directo)
7   → N (izquierda)
93  → S (derecha)
103 → O (retorno)
```

### Desde ESTE (E)
```
4   → O (directo)
8   → S (izquierda)
94  → N (derecha)
104 → E (retorno)
```

---

## 🎮 CONTROLES DEL CANVAS

```
Seleccionar acceso     → Click en botón N/S/E/O
Editar vértice         → Arrastrar punto amarillo
Agregar vértice        → [Próxima versión]
Eliminar polígono      → "Reiniciar polígono"
Zoom/Pan               → [Próxima versión]
```

---

## 📁 ARCHIVOS IMPORTANTES

### Backend
```
api/
├── models/config.py         ← Modelos de datos
├── services/cardinals.py    ← Lógica RILSA
├── services/persistence.py  ← Guardar/cargar
├── routers/config.py        ← Endpoints
└── main.py                  ← App FastAPI
```

### Frontend
```
apps/web/src/
├── pages/DatasetConfigPage.tsx   ← Página principal
├── components/TrajectoryCanvas.tsx
├── components/AccessEditorPanel.tsx
├── types/index.ts                ← Tipos TypeScript
└── lib/api.ts                    ← Cliente HTTP
```

### Datos
```
data/configs/{dataset_id}/
└── config.json  ← Configuración persistente
```

---

## 🌐 ENDPOINTS PRINCIPALES

| Método | Endpoint | Propósito |
|--------|----------|-----------|
| GET | `/api/v1/config/view/{id}` | Cargar config |
| POST | `/api/v1/config/generate_accesses/{id}` | Generar automático |
| PUT | `/api/v1/config/save_accesses/{id}` | Guardar accesos |
| POST | `/api/v1/config/generate_rilsa/{id}` | Generar RILSA |
| GET | `/api/v1/config/rilsa_codes/{id}` | Obtener códigos |
| DELETE | `/api/v1/config/reset/{id}` | Reiniciar |

---

## 🔍 DEBUGGING

### Ver logs de la API
```bash
docker-compose logs -f api
```

### Ver logs del Frontend
```bash
docker-compose logs -f web
```

### Verificar que API está activo
```bash
curl http://localhost:3004/health
```

### Ver Swagger UI (documentación interactiva)
```
http://localhost:3004/docs
```

---

## ❌ ERRORES COMUNES

### "Connection refused" en 3004
```
✓ Verificar: docker ps
✓ Iniciar: docker-compose up -d
✓ Logs: docker-compose logs api
```

### "CORS error" en consola
```
✓ Verificar REACT_APP_API_URL en .env
✓ Debe ser: http://localhost:3004
✓ Recargar: Ctrl+Shift+R
```

### Polígonos no aparecen
```
✓ Verificar que accesos tienen polygon definido
✓ Ver console del navegador (F12)
✓ Verificar que hay trayectorias cargadas
```

---

## 📊 FORMATO DE DATOS

### Config guardado (config.json)
```json
{
  "dataset_id": "gx010323",
  "accesses": [
    {
      "id": "N",
      "cardinal": "N",
      "polygon": [[0,0], [1280,0], [1280,108], [0,108]],
      "centroid": [640, 54]
    }
  ],
  "rilsa_rules": [
    {
      "code": "1",
      "origin_access": "N",
      "dest_access": "S",
      "movement_type": "directo",
      "description": "1 – N → S (movimiento directo)"
    }
  ],
  "created_at": "2025-01-13T12:00:00",
  "updated_at": "2025-01-13T12:00:00"
}
```

---

## 🚀 DESARROLLO

### Modificar backend
```bash
# Los cambios se recargan automáticamente
# Ver: docker-compose logs -f api
```

### Modificar frontend
```bash
# Los cambios se recargan automáticamente (HMR)
# Ver: http://localhost:3000
```

### Instalar dependencia backend
```bash
pip install <package>
# Actualizar: api/requirements.txt
```

### Instalar dependencia frontend
```bash
cd apps/web
npm install <package>
```

---

## ✅ VALIDACIONES

El sistema valida automáticamente:
- ✓ Cardinales válidos (N, S, E, O)
- ✓ Polígonos con mínimo 3 vértices
- ✓ Coordenadas dentro del rango
- ✓ Dataset ID no vacío
- ✓ Accesos definidos antes de generar RILSA

---

## 📞 SOPORTE

**Documentación completa:**
```
CONFIGURACION_SISTEMA_COMPLETO.md
```

**API Documentation:**
```
http://localhost:3004/docs
```

**Frontend README:**
```
apps/web/README.md
```

---

**AFOROS RILSA v3.0.2**
*Configuración centralizada, nomenclatura consistente, movimientos exactos*
