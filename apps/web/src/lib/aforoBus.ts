/**
 * Event Bus para trayectorias completadas
 * Patrón pub/sub simple para desacoplar emisión de eventos y consumo
 */

import type { TrajectoryCompletedEvent } from '../types/aforo';

type Handler = (event: TrajectoryCompletedEvent) => void;

const subscribers = new Set<Handler>();

export const aforoBus = {
  /**
   * Suscribirse a eventos de trayectorias completadas
   * @param handler Función que recibe el evento
   * @returns Función para desuscribirse
   */
  subscribe(handler: Handler): () => void {
    subscribers.add(handler);
    return () => subscribers.delete(handler);
  },

  /**
   * Publicar un evento de trayectoria completada
   * @param event Evento a publicar
   */
  publish(event: TrajectoryCompletedEvent): void {
    subscribers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in aforo event handler:', error);
      }
    });
  },

  /**
   * Limpiar todos los suscriptores (útil para testing)
   */
  clear(): void {
    subscribers.clear();
  },

  /**
   * Obtener número de suscriptores activos
   */
  get subscriberCount(): number {
    return subscribers.size;
  },
};
