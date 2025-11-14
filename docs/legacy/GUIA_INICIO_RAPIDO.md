# 🚀 GUÍA DE INICIO RÁPIDO - AFOROS RILSA v3.0.2

## En 5 Minutos: Desde Cero a Sistema Funcionando

### Requisitos Previos
- Node.js 18+ con npm
- Python 3.9+
- Git

---

## 1️⃣ Instalar Dependencias (2 min)

### Backend
```bash
cd c:\Users\David\aforos\api
pip install -r requirements.txt
```

### Frontend
```bash
cd c:\Users\David\aforos\apps\web
npm install
```

---

## 2️⃣ Iniciar Servicios (1 min)

### Backend (Terminal 1)
```bash
cd c:\Users\David\aforos\api
python main.py
```

**Esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:3004
```

### Frontend (Terminal 2)
```bash
cd c:\Users\David\aforos\apps\web
npm run dev
```

**Esperado:**
```
  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

---

## 3️⃣ Acceder al Sistema (30 seg)

Abre tu navegador:
```
http://localhost:3000
```

Deberías ver:
- Barra de navegación con 7 pasos
- Página UploadPage (Paso 1)
- Botón para subir archivo PKL

---

## 4️⃣ Probar el Flujo Completo

### Demo: Subir Dataset Simulado

1. **En UploadPage:**
   - Haz clic en "Arrastra un archivo o haz clic"
   - Selecciona cualquier archivo `.pkl`
   - Haz clic en "Subir y Procesar PKL"

2. **Auto-navegación:**
   - El sistema crea un `dataset_id`
   - Auto-navega a `/datasets/{datasetId}/config`

3. **Navega por los pasos:**
   - Usa la barra superior para ir entre pasos
   - Los pasos se habilitan progresivamente
   - Puedes retroceder cuando quieras

4. **Explora cada sección:**
   - **Config:** Visualiza accesos (N, S, E, O)
   - **Validation:** Ejecuta validaciones con 5 corridas
   - **Editor:** Ve tabla de trayectorias
   - **Live:** Playback y conteos
   - **Results:** Descarga CSV/PDF
   - **History:** Auditoría de cambios

---

## 🔍 Verificar que Todo Está Funcionando

### Backend API
```bash
curl http://localhost:3004/health
```

**Respuesta esperada:**
```json
{"status": "ok", "version": "3.0.2"}
```

### API Documentation
```
http://localhost:3004/docs
```

Verás Swagger UI con todos los 21 endpoints.

### Frontend
```
http://localhost:3000
```

Deberías ver la interfaz con la barra de 7 pasos.

---

## 📊 Estructura de Directorios Clave

```
aforos/
├── api/                          # Backend FastAPI
│   ├── main.py                   # Aplicación principal
│   ├── routers/
│   │   ├── datasets.py           # Paso 1: Upload
│   │   ├── config.py             # Paso 2: Config
│   │   ├── validation.py         # Paso 3: Validation
│   │   ├── editor.py             # Paso 4: Editor
│   │   ├── live.py               # Paso 5: Live
│   │   ├── reports.py            # Paso 6: Reports
│   │   └── history.py            # Paso 7: History
│   └── requirements.txt
│
└── apps/web/                     # Frontend React+Vite
    ├── src/
    │   ├── pages/
    │   │   ├── UploadPage.tsx
    │   │   ├── DatasetConfigPageNew.tsx
    │   │   ├── DatasetValidationPage.tsx
    │   │   ├── DatasetEditorPage.tsx
    │   │   ├── AforoDetailPage.tsx
    │   │   ├── ResultsPage.tsx
    │   │   └── HistoryPage.tsx
    │   ├── components/
    │   │   ├── StepNavigation.tsx
    │   │   ├── TrajectoryCanvas.tsx
    │   │   └── AccessEditorPanel.tsx
    │   ├── App.tsx               # Router principal
    │   └── types/index.ts
    ├── .env.local                # VITE_API_URL=http://localhost:3004
    └── package.json
```

---

## 🛠️ Troubleshooting Rápido

### "Cannot find module 'react-router-dom'"
```bash
cd apps/web
npm install react-router-dom
```

### "Uvicorn not found"
```bash
cd api
pip install uvicorn
```

### Puerto 3000 ya en uso
```bash
# Usa otro puerto
cd apps/web
npm run dev -- --port 3001
```

### Puerto 3004 ya en uso
```bash
# Usa otro puerto en main.py
# O mata el proceso que lo usa
taskkill /PID <pid> /F
```

### API retorna 404
```bash
# Verifica que backend está corriendo
curl http://localhost:3004/health
# Debe responder con JSON
```

### No veo cambios en frontend
```bash
# Ctrl+Shift+R en navegador (hard refresh)
# O limpia caché: Ctrl+Shift+Del
```

---

## 📱 URLs Útiles

| Sección | URL |
|---------|-----|
| **Frontend (Paso 1)** | http://localhost:3000 |
| **Upload** | http://localhost:3000/datasets/upload |
| **Config (sample)** | http://localhost:3000/datasets/gx010323/config |
| **API Docs** | http://localhost:3004/docs |
| **API Health** | http://localhost:3004/health |
| **API Root** | http://localhost:3004/ |

---

## 📝 Ejemplos de Uso por Paso

### Paso 1: Upload
```bash
# Simular upload (usando curl)
curl -X POST http://localhost:3004/api/v1/datasets/upload \
  -F "file=@archivo.pkl"
```

### Paso 2: Config
```bash
# Ver configuración actual
curl http://localhost:3004/api/v1/config/view/gx010323

# Generar RILSA
curl -X POST http://localhost:3004/api/v1/config/generate_rilsa/gx010323
```

### Paso 3: Validation
```bash
# Ejecutar validaciones (5 corridas)
curl -X POST http://localhost:3004/api/v1/validate/gx010323 \
  -H "Content-Type: application/json" \
  -d '{"runs": 5}'
```

### Paso 6: Reports
```bash
# Obtener resumen
curl http://localhost:3004/api/v1/reports/gx010323/summary

# Descargar CSV
curl http://localhost:3004/api/v1/reports/gx010323/csv > aforo.csv
```

---

## 🎯 Próximos Pasos Recomendados

1. **Explorar la interfaz**
   - Navega por los 7 pasos
   - Nota cómo se habilitan/deshabilitan
   - Observa los mensajes de error y success

2. **Revisar el código**
   - `apps/web/src/components/StepNavigation.tsx` - Barra de pasos
   - `apps/web/src/App.tsx` - Router principal
   - `api/main.py` - Configuración backend

3. **Implementar funcionalidades reales**
   - Ver `CHECKLIST_IMPLEMENTACION_7PASOS.md` para TODOs
   - Comenzar con normalización PKL
   - Luego estadísticas
   - Finalmente PDF generation

4. **Agregar tests**
   - Pytest para backend
   - Jest/Vitest para frontend

---

## 📚 Documentación Disponible

- **ARQUITECTURA_7PASOS.md** - Arquitectura completa
- **CHECKLIST_IMPLEMENTACION_7PASOS.md** - Estado del código
- **RESUMEN_EJECUTIVO_7PASOS.md** - Resumen de alto nivel
- **Esta guía** - Inicio rápido

---

## ✅ Checklist Final

- [ ] Backend corriendo en puerto 3004
- [ ] Frontend corriendo en puerto 3000
- [ ] Puedo acceder a http://localhost:3000
- [ ] Veo barra de 7 pasos
- [ ] API docs accesibles en http://localhost:3004/docs
- [ ] Puedo navegar entre pasos
- [ ] Mensajes de error/success aparecen correctamente

---

## 🎓 Conceptos Clave

### The 7-Step Workflow
```
Upload PKL 
  ↓
Configure Cardinals (N,S,E,O)
  ↓
Validate with Statistics
  ↓
Edit Trajectories
  ↓
View Live Playback + Aforo
  ↓
Download Results (CSV/PDF)
  ↓
Audit History
```

### Nomenclatura RILSA
```
16 Movement Codes:
- North: 1, 5, 91, 101
- South: 2, 6, 92, 102
- West: 3, 7, 93, 103
- East: 4, 8, 94, 104
```

### Dataset Lifecycle
```
dataset_id → raw.pkl → normalized.parquet → metadata.json
     ↓
config.json (accesses + RILSA rules)
     ↓
events.json (para live playback)
     ↓
reports (CSV, PDF)
     ↓
history.json (audit log)
```

---

## 🤝 Soporte

Si algo no funciona:

1. **Chequea los logs:**
   - Terminal del backend: Revisa errores de Python
   - Console del navegador: F12 → Console tab
   - Network tab: F12 → Network (ve requests/responses)

2. **Verifica salud del sistema:**
   ```bash
   curl http://localhost:3004/health
   ```

3. **Revisa configuración:**
   - `.env.local` debe tener `VITE_API_URL=http://localhost:3004`
   - Puertos 3000 y 3004 deben estar libres

4. **Lee documentación:**
   - Ver archivos `.md` en raíz del proyecto
   - Ver comentarios en código fuente

---

**¡Estás listo para comenzar! 🚀**

**Versión:** 3.0.2
**Última actualización:** 13 de Enero de 2025
