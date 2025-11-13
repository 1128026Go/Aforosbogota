/**
 * Ejemplo de cómo emitir eventos de trayectorias completadas
 * Integrar este código en el motor de trayectorias existente
 */

import { aforoBus } from './aforoBus';
import { mapRilsa } from './rilsa';
import type { TrajectoryCompletedEvent, ClaseMovil, Cardinal } from '../types/aforo';

/**
 * Ejemplo 1: Emitir evento cuando una trayectoria sale del área
 */
export function onTrackExit(trackData: {
  track_id: string;
  clase: string; // 'car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'
  last_timestamp: number; // timestamp Unix en segundos
  origin_cardinal: Cardinal; // 'N', 'S', 'E', 'O'
  dest_cardinal: Cardinal;
  median_speed_kmh?: number;
}) {
  // Convertir timestamp Unix a ISO
  const exitDate = new Date(trackData.last_timestamp * 1000);
  const t_exit_iso = exitDate.toISOString();

  // Calcular movimiento RILSA
  const mov_rilsa = mapRilsa(trackData.origin_cardinal, trackData.dest_cardinal);

  // Construir payload del evento
  const event: TrajectoryCompletedEvent = {
    track_id: trackData.track_id,
    clase: trackData.clase as ClaseMovil,
    t_exit_iso,
    origin_cardinal: trackData.origin_cardinal,
    dest_cardinal: trackData.dest_cardinal,
    mov_rilsa,
    ramal: trackData.origin_cardinal, // Ramal = origen
    v_kmh_mediana: trackData.median_speed_kmh,
  };

  // Publicar evento
  aforoBus.publish(event);

  console.log(`🚗 Trayectoria completada: ${trackData.track_id}`);
}

/**
 * Ejemplo 2: Integración con WebWorker
 * Si el procesamiento está en un worker, enviar mensaje al thread principal
 */
export function onTrackExitInWorker(trackData: any) {
  // En el worker
  self.postMessage({
    type: 'TRACK_COMPLETED',
    data: trackData,
  });
}

// En el thread principal (main.tsx o donde recibas mensajes del worker):
/*
worker.onmessage = (event) => {
  if (event.data.type === 'TRACK_COMPLETED') {
    const trackData = event.data.data;
    onTrackExit(trackData);
  }
};
*/

/**
 * Ejemplo 3: Integración con sistema existente de detección de salida
 */
export class TrajectoryTracker {
  private tracks = new Map<string, {
    id: string;
    clase: string;
    origin: Cardinal;
    speeds: number[];
    startTime: number;
  }>();

  onTrackEnter(trackId: string, clase: string, origin: Cardinal) {
    this.tracks.set(trackId, {
      id: trackId,
      clase,
      origin,
      speeds: [],
      startTime: Date.now(),
    });
  }

  onTrackUpdate(trackId: string, speed: number) {
    const track = this.tracks.get(trackId);
    if (track) {
      track.speeds.push(speed);
    }
  }

  onTrackLeave(trackId: string, dest: Cardinal) {
    const track = this.tracks.get(trackId);
    if (!track) {
      console.warn(`Track ${trackId} no encontrado`);
      return;
    }

    // Calcular velocidad mediana
    const sortedSpeeds = [...track.speeds].sort((a, b) => a - b);
    const median = sortedSpeeds[Math.floor(sortedSpeeds.length / 2)] ?? 0;

    // Emitir evento
    onTrackExit({
      track_id: trackId,
      clase: track.clase,
      last_timestamp: Date.now() / 1000,
      origin_cardinal: track.origin,
      dest_cardinal: dest,
      median_speed_kmh: median,
    });

    // Limpiar
    this.tracks.delete(trackId);
  }
}

/**
 * Ejemplo de uso simple:
 */
/*
// 1. Cuando el emoji completa su recorrido:
onTrackExit({
  track_id: '12345',
  clase: 'car',
  last_timestamp: Date.now() / 1000,
  origin_cardinal: 'N',
  dest_cardinal: 'S',
  median_speed_kmh: 45.5
});

// 2. El evento se propaga automáticamente al store
// 3. El panel de aforo se actualiza en tiempo real
// 4. El usuario ve el conteo incrementado en la tabla
*/
