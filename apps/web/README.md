# AFOROS RILSA v3.0.2 - Frontend

Frontend web para la configuración de datasets y generación de movimientos RILSA.

## Características

- **Visualización interactiva** de trayectorias y polígonos de acceso
- **Edición de accesos cardinales** (N, S, E, O) mediante polígonos
- **Generación automática** de accesos desde trayectorias
- **Generación de reglas RILSA** siguiendo la Nomenclatura Sagrada
- **Interfaz moderna** con React + TypeScript + Tailwind CSS
- **API integrada** con validación y persistencia

## Requisitos

- Node.js 18+ 
- npm o yarn

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

Asegúrate de que la API está corriendo en `http://localhost:3004`

## Build

```bash
npm run build
```

Los archivos compilados estarán en `dist/`

## Estructura

```
src/
├── pages/
│   └── DatasetConfigPage.tsx    # Página principal
├── components/
│   ├── TrajectoryCanvas.tsx     # Canvas para visualización
│   └── AccessEditorPanel.tsx    # Panel de edición
├── types/
│   └── index.ts                 # Tipos TypeScript
├── lib/
│   └── api.ts                   # Cliente API
└── main.tsx                     # Entry point
```

## Flujo de Uso

1. Carga la página con un dataset ID: `?dataset=gx010323`
2. Sistema carga la configuración actual
3. Si no hay accesos:
   - Click "Generar Accesos" para crear propuesta automática
   - O dibuja manualmente en el canvas
4. Edita los polígonos arrastrando los vértices
5. Click "Guardar Accesos" para persistir
6. Click "Generar Movimientos RILSA" para crear las reglas

## Variables de Entorno

Copia `.env.example` a `.env` y configura:

```env
REACT_APP_API_URL=http://localhost:3004
```

## Tecnologías

- React 18
- TypeScript 5
- Tailwind CSS 3
- Vite 5
