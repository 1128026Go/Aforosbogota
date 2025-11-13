/**
 * Aforo Integrado - SPA Principal
 * Sistema de aforos con trayectorias y agregación de 15 min
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import UploadPage from './pages/upload/UploadPage';
import LibraryPage from './pages/library/LibraryPage';
import AforoDetailPage from './pages/detail/AforoDetailPage';
import AforoMovimientosTestPage from './pages/AforoMovimientosTestPage';
import { DatasetsListPage } from './pages/datasets/DatasetsListPage';
import { DatasetEditorPage } from './pages/datasets/DatasetEditorPage';
import { DatasetRulesPage } from './pages/datasets/DatasetRulesPage';
import { DatasetHistoryPage } from './pages/datasets/DatasetHistoryPage';
import { DatasetConfigPage } from './pages/datasets/DatasetConfigPage';
import { DatasetValidationPage } from './pages/datasets/DatasetValidationPage';

// Contexto de navegación simple
const NavigationContext = React.createContext<{
  navigate: (path: string) => void;
  params: Record<string, string>;
}>({
  navigate: () => {},
  params: {},
});

export function useNavigate() {
  return React.useContext(NavigationContext).navigate;
}

export function useParams<T extends Record<string, string>>(): T {
  return React.useContext(NavigationContext).params as T;
}

/**
 * Router simple basado en pathname
 */
function Router() {
  const [path, setPath] = React.useState(window.location.pathname);

  const navigate = (newPath: string) => {
    window.history.pushState({}, '', newPath);
    setPath(newPath);
  };

  React.useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Extraer params
  let component: React.ReactNode = null;
  let params: Record<string, string> = {};

  // Rutas de edición de datasets
  if (path.startsWith('/datasets/')) {
    const parts = path.split('/');
    if (parts.length === 2 || parts[2] === '') {
      // /datasets o /datasets/
      component = <DatasetsListPage />;
    } else if (parts.length === 4) {
      // /datasets/:id/editor, /datasets/:id/rules, /datasets/:id/history, /datasets/:id/config, /datasets/:id/validation
      params = { id: parts[2] };
      if (parts[3] === 'editor') {
        component = <DatasetEditorPage />;
      } else if (parts[3] === 'rules') {
        component = <DatasetRulesPage />;
      } else if (parts[3] === 'history') {
        component = <DatasetHistoryPage />;
      } else if (parts[3] === 'config') {
        component = <DatasetConfigPage />;
      } else if (parts[3] === 'validation') {
        component = <DatasetValidationPage />;
      }
    }
  }
  // Ruta: /aforo/:datasetId
  else if (path.startsWith('/aforo/')) {
    const parts = path.split('/');
    if (parts.length === 3) {
      params = { datasetId: parts[2] };
      component = <AforoDetailPage />;
    }
  }
  // Ruta: /library
  else if (path === '/library' || path === '/library/') {
    component = <LibraryPage />;
  }
  // Ruta: /upload
  else if (path === '/upload' || path === '/upload/') {
    component = <UploadPage />;
  }
  // Ruta: /test-movimientos (página de prueba de movimientos RILSA)
  else if (path === '/test-movimientos' || path === '/test-movimientos/') {
    component = <AforoMovimientosTestPage />;
  }
  // Ruta: / (redirect a datasets)
  else {
    component = <DatasetsListPage />;
  }

  return (
    <NavigationContext.Provider value={{ navigate, params }}>
      {component}
    </NavigationContext.Provider>
  );
}

function App() {
  return <Router />;
}

// Renderizar aplicación
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Estilos globales básicos
const globalStyles = document.createElement('style');
globalStyles.textContent = `
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f9fafb;
  }

  .app {
    min-height: 100vh;
  }

  .map-container {
    padding: 40px;
  }

  .map-container h1 {
    font-size: 32px;
    color: #111827;
    margin-bottom: 8px;
  }

  .map-container p {
    color: #6b7280;
    margin-bottom: 20px;
  }
`;
document.head.appendChild(globalStyles);
