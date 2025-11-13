/**
 * Integración del sistema de aforo en vivo
 * Conecta el event bus con el store multi-aforo
 */

import * as React from 'react';
import { aforoBus } from './aforoBus';
import { useAforos } from '../store/aforos';

/**
 * Inicializa la integración del aforo en vivo
 * Debe llamarse al inicio de la aplicación (en main.tsx o index.tsx)
 */
export function initAforoIntegration(): () => void {
  console.log('🚀 Iniciando integración multi-aforo...');

  // Suscribirse a eventos de trayectorias completadas
  const unsubscribe = aforoBus.subscribe((event) => {
    const { upsert } = useAforos.getState();
    upsert(event);
  });

  console.log('✅ Multi-aforo inicializado');
  console.log('📊 Los aforos se crearán automáticamente al completarse trayectorias');

  // Retornar función para limpiar (útil en desarrollo)
  return () => {
    unsubscribe();
    console.log('🛑 Multi-aforo detenido');
  };
}

/**
 * Hook de React para inicializar aforo automáticamente
 * Uso: useAforoIntegration() en el componente raíz
 */
export function useAforoIntegration() {
  React.useEffect(() => {
    const cleanup = initAforoIntegration();
    return cleanup;
  }, []);
}
