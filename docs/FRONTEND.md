# Frontend (React + Vite)

## Dependencias

```bash
cd apps/web
npm install
```

## Scripts principales

- `npm run dev`: servidor de desarrollo en `http://localhost:5173`.
- `npm run build`: compilación de producción en `dist/`.
- `npm run preview`: vista previa sobre el build generado.

## Estructura

- `src/main.tsx`: punto de entrada, monta `<App />`.
- `src/App.tsx`: layout principal con navegación por pasos.
- `src/pages/UploadPage.tsx`: subida del PKL y metadatos base.
- `src/pages/DatasetConfigPageNew.tsx`: editor de accesos/cardinals.
- `src/pages/ResultsPage.tsx`: vista de resultados (volúmenes, velocidades, conflictos).
- `src/components/StepNavigation.tsx`: navegación por los pasos activos.
- `src/components/LoadDatasetStep.tsx`: tarjeta principal del paso de subida.
- `src/components/AccessEditorPanel.tsx`: formulario para ajustes de accesos.
- `src/components/results/*`: componentes segmentados para tablas y visualizaciones (si se habilitan).
- `src/lib/api.ts`: cliente HTTP centralizado (datasets, config, analysis, reports).
- `src/types/index.ts`: definiciones TypeScript alineadas con la API.

## Variables de entorno

Crea `.env` (no se versiona) si necesitas apuntar a otra URL del backend:

```
VITE_API_BASE_URL=http://localhost:8000
```

Por defecto, `lib/api.ts` usa la URL local (`http://localhost:8000`).

## Buenas prácticas

- Mantener los componentes de resultados segmentados por dominio (volúmenes, velocidades, conflictos) para facilitar pruebas.
- Reutilizar `lib/api.ts` en lugar de crear clientes duplicados.
- Actualizar `types/index.ts` cuando la API cambie.
- Añadir pruebas de componentes con Vitest/Testing Library en futuras iteraciones.
