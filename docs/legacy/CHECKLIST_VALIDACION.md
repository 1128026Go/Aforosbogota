# ✅ CHECKLIST DE VALIDACIÓN - AFOROS RILSA v3.0.2

## PRE-INSTALACIÓN

- [ ] Python 3.8+ instalado (`python --version`)
- [ ] Node.js 18+ instalado (`node --version`)
- [ ] npm 9+ instalado (`npm --version`)
- [ ] Docker instalado (`docker --version`)
- [ ] Docker Compose instalado (`docker-compose --version`)
- [ ] Git instalado (`git --version`)

## VERIFICACIÓN DE ESTRUCTURA

### Backend (api/)
- [ ] Carpeta `api/` existe
- [ ] `api/models/config.py` existe
- [ ] `api/services/cardinals.py` existe
- [ ] `api/services/persistence.py` existe
- [ ] `api/routers/config.py` existe
- [ ] `api/main.py` existe
- [ ] `api/requirements.txt` existe

### Frontend (apps/web/)
- [ ] Carpeta `apps/web/src/` existe
- [ ] `apps/web/src/pages/DatasetConfigPage.tsx` existe
- [ ] `apps/web/src/components/TrajectoryCanvas.tsx` existe
- [ ] `apps/web/src/components/AccessEditorPanel.tsx` existe
- [ ] `apps/web/src/types/index.ts` existe
- [ ] `apps/web/src/lib/api.ts` existe
- [ ] `apps/web/package.json` existe
- [ ] `apps/web/tsconfig.json` existe
- [ ] `apps/web/vite.config.ts` existe

### Documentación
- [ ] `INICIO_RAPIDO.md` existe
- [ ] `CONFIGURACION_SISTEMA_COMPLETO.md` existe
- [ ] `ARQUITECTURA_TECNICA.md` existe
- [ ] `RESUMEN_EJECUTIVO.md` existe
- [ ] `apps/web/README.md` existe

### Infraestructura
- [ ] `docker-compose.yml` existe
- [ ] `Dockerfile.api` existe
- [ ] `apps/web/Dockerfile` existe
- [ ] `start.sh` existe (Linux/Mac)
- [ ] `start.bat` existe (Windows)
- [ ] `verify_install.py` existe

### Datos
- [ ] Carpeta `data/configs/` puede ser creada

## INSTALACIÓN

### Backend
```bash
cd aforos/api
pip install -r requirements.txt
```

- [ ] Todas las dependencias instaladas sin errores
- [ ] `from fastapi import FastAPI` funciona
- [ ] `from pydantic import BaseModel` funciona
- [ ] `import numpy` funciona

### Frontend
```bash
cd aforos/apps/web
npm install
```

- [ ] npm install completado sin errores
- [ ] `node_modules/` creada
- [ ] `package-lock.json` existe

## EJECUCIÓN

### Backend
```bash
cd aforos/api
python main.py
# o: uvicorn main:app --reload --port 3004
```

- [ ] Servidor FastAPI inicia sin errores
- [ ] Mensaje: "Uvicorn running on http://0.0.0.0:3004"
- [ ] Presionable: http://localhost:3004/health
- [ ] Swagger UI disponible en: http://localhost:3004/docs

### Frontend
```bash
cd aforos/apps/web
npm run dev
```

- [ ] Vite dev server inicia sin errores
- [ ] Mensaje: "VITE v5.X.X ready in XXX ms"
- [ ] Presionable: http://localhost:3000

## FUNCIONALIDAD CORE

### API Endpoints
- [ ] `GET /health` retorna 200 OK
- [ ] `GET /api/v1/config/view/test-dataset` retorna 200
- [ ] `POST /api/v1/config/generate_accesses/test-dataset` retorna 200
- [ ] `PUT /api/v1/config/save_accesses/test-dataset` retorna 200
- [ ] `POST /api/v1/config/generate_rilsa/test-dataset` retorna 200
- [ ] Swagger UI carga todas las rutas correctamente

### Frontend
- [ ] Página carga sin errores (F12 → Console limpia)
- [ ] URL: `http://localhost:3000?dataset=gx010323` funciona
- [ ] Canvas se renderiza
- [ ] Botones están visibles
- [ ] Controles responsive en móvil (F12 → Device Mode)

### Flujo Usuario
- [ ] Click "Generar Accesos" → No error
- [ ] Canvas actualiza con polígonos
- [ ] Seleccionar cardinal (N/S/E/O) → Polígono se resalta
- [ ] Arrastrar vértice → Se mueve suave
- [ ] Click "Guardar Accesos" → Confirmación visual
- [ ] Click "Generar RILSA" → Tabla con 16 códigos aparece

### Persistencia
- [ ] Archivos guardados en `data/configs/gx010323/config.json`
- [ ] Archivo contiene todas las secciones requeridas:
  - [ ] `dataset_id`
  - [ ] `accesses` con 4 cardinals
  - [ ] `rilsa_rules` con 16 movimientos
  - [ ] `created_at`
  - [ ] `updated_at`
- [ ] Recargando página: configuración se carga correctamente

### Nomenclatura RILSA
- [ ] Código "1" → N→S (directo) ✓
- [ ] Código "2" → S→N (directo) ✓
- [ ] Código "3" → O→E (directo) ✓
- [ ] Código "4" → E→O (directo) ✓
- [ ] Código "5" → N→E (izquierda) ✓
- [ ] Código "6" → S→O (izquierda) ✓
- [ ] Código "7" → O→N (izquierda) ✓
- [ ] Código "8" → E→S (izquierda) ✓
- [ ] Código "91" → N→O (derecha) ✓
- [ ] Código "92" → S→E (derecha) ✓
- [ ] Código "93" → O→S (derecha) ✓
- [ ] Código "94" → E→N (derecha) ✓
- [ ] Código "101" → N→N (retorno) ✓
- [ ] Código "102" → S→S (retorno) ✓
- [ ] Código "103" → O→O (retorno) ✓
- [ ] Código "104" → E→E (retorno) ✓

## VALIDACIÓN DE REQUISITOS

- [ ] Paso configuración es accesible desde la UI
- [ ] Se pueden definir/editar accesos (N, S, E, O)
- [ ] Se visualizan trayectorias en canvas
- [ ] Se visualizan polígonos en canvas
- [ ] Se permite edición manual de polígonos
- [ ] Configuración se guarda persistentemente
- [ ] Movimientos RILSA se generan con nomenclatura correcta
- [ ] API está en puerto 3004
- [ ] Frontend está en puerto 3000
- [ ] Rutas usan /api/v1/
- [ ] CORS está configurado para localhost

## SEGURIDAD Y CALIDAD

- [ ] Código TypeScript compila sin errores (`npm run type-check`)
- [ ] No hay warnings en console del navegador (F12)
- [ ] No hay errores no capturados en API (ver logs)
- [ ] Validaciones Pydantic funcionan (enviar datos inválidos)
- [ ] Manejo de errores es robusto

## DOCUMENTACIÓN

- [ ] Cada archivo tiene comentarios sobre su propósito
- [ ] Funciones principales están documentadas
- [ ] README.md es claro y completo
- [ ] Ejemplos de uso están disponibles
- [ ] Swagger /docs muestra todos los endpoints

## DEPLOYMENT READY

- [ ] docker-compose.yml correcto
- [ ] `docker-compose up -d` levanta ambos servicios
- [ ] Los servicios se comunican correctamente
- [ ] Los logs se ven correctamente
- [ ] `docker-compose down` detiene servicios cleanly

## PROBLEMAS CONOCIDOS A REVISAR

- [ ] "Connection refused 3004" → API no está corriendo
- [ ] "CORS error" → Verificar REACT_APP_API_URL
- [ ] Canvas en blanco → Verificar console (F12)
- [ ] Polígonos no se guardan → Verificar permisos data/
- [ ] Node modules issue → Eliminar node_modules y reinstalar

## SIGN-OFF

- [ ] Backend funcional completo
- [ ] Frontend funcional completo
- [ ] Integración entre ellos exitosa
- [ ] Nomenclatura RILSA correcta
- [ ] Documentación completa
- [ ] Listo para usar en producción

---

**Preparado por:** [Tu nombre]  
**Fecha de validación:** [YYYY-MM-DD]  
**Versión:** AFOROS RILSA v3.0.2  
**Estado:** ✅ APROBADO / ❌ PENDIENTE

---

## NOTAS ADICIONALES

[Espacio para observaciones, cambios realizados, o problemas encontrados]

```
_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________
```
