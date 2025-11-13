/**
 * Store multi-aforo con buckets de 15 minutos
 * Gestiona conteos por trayectoria con idempotencia
 */

import { create } from 'zustand';
import type { TrajectoryCompletedEvent, BucketKey, CountKey } from '@/types/aforo';

type Counts = Record<string, number>; // key: JSON.stringify(CountKey)

interface AforoNode {
  seenTracks: Set<string>;
  counts: Map<string, Counts>; // key: JSON.stringify(BucketKey)
  totals: Map<string, number>; // total por bucket
  latestBucketIso?: string;
}

interface AforoState {
  byAforo: Map<string, AforoNode>;

  upsert(e: TrajectoryCompletedEvent): void;
  resetAforo(aforoId: string): void;
  listAforos(): { id: string; totalTracks: number; latest?: string }[];
  getBuckets(aforoId: string): string[]; // ordenados desc
  getCounts(aforoId: string, bucketIso: string): Counts | undefined;
  getTotal(aforoId: string, bucketIso: string): number;
}

/**
 * Redondea fecha al bloque de 15 minutos inferior
 */
function floor15(date: Date): Date {
  const d = new Date(date);
  const minutes = d.getMinutes();
  const floored = Math.floor(minutes / 15) * 15;
  d.setMinutes(floored, 0, 0);
  return d;
}

/**
 * Determina periodo (mañana/tarde)
 */
function getPeriodo(date: Date): 'mañana' | 'tarde' {
  return date.getHours() < 12 ? 'mañana' : 'tarde';
}

export const useAforos = create<AforoState>((set, get) => ({
  byAforo: new Map(),

  upsert: (e: TrajectoryCompletedEvent) => {
    const byAforo = new Map(get().byAforo);
    const node: AforoNode = byAforo.get(e.aforoId) ?? {
      seenTracks: new Set(),
      counts: new Map(),
      totals: new Map(),
    };

    // Idempotencia: no contar mismo track dos veces
    if (node.seenTracks.has(e.track_id)) {
      byAforo.set(e.aforoId, node);
      return set({ byAforo });
    }

    node.seenTracks.add(e.track_id);

    const exitDate = new Date(e.t_exit_iso);
    const bucketDate = floor15(exitDate);
    const bucketIso = bucketDate.toISOString();

    const bucketKey: BucketKey = {
      bucket_iso: bucketIso,
      periodo: getPeriodo(bucketDate),
      ramal: e.ramal,
    };
    const bucketKeyStr = JSON.stringify(bucketKey);

    const countKey: CountKey = {
      movimiento_rilsa: e.mov_rilsa,
      clase: e.clase,
    };
    const countKeyStr = JSON.stringify(countKey);

    // Inicializar bucket si no existe
    if (!node.counts.has(bucketKeyStr)) {
      node.counts.set(bucketKeyStr, {});
      node.totals.set(bucketKeyStr, 0);
    }

    const bucketCounts = node.counts.get(bucketKeyStr)!;
    const prevCount = bucketCounts[countKeyStr] || 0;
    bucketCounts[countKeyStr] = prevCount + 1;

    node.totals.set(bucketKeyStr, (node.totals.get(bucketKeyStr) || 0) + 1);
    node.latestBucketIso = bucketIso;

    byAforo.set(e.aforoId, node);
    set({ byAforo });
  },

  resetAforo: (aforoId: string) => {
    const byAforo = new Map(get().byAforo);
    byAforo.delete(aforoId);
    set({ byAforo });
  },

  listAforos: () => {
    return Array.from(get().byAforo.entries()).map(([id, node]) => ({
      id,
      totalTracks: node.seenTracks.size,
      latest: node.latestBucketIso,
    }));
  },

  getBuckets: (aforoId: string) => {
    const node = get().byAforo.get(aforoId);
    if (!node) return [];

    const bucketIsos = new Set<string>();
    for (const bucketKeyStr of node.counts.keys()) {
      const bucketKey: BucketKey = JSON.parse(bucketKeyStr);
      bucketIsos.add(bucketKey.bucket_iso);
    }

    return Array.from(bucketIsos).sort().reverse(); // más reciente primero
  },

  getCounts: (aforoId: string, bucketIso: string) => {
    const node = get().byAforo.get(aforoId);
    if (!node) return undefined;

    for (const [bucketKeyStr, counts] of node.counts.entries()) {
      const bucketKey: BucketKey = JSON.parse(bucketKeyStr);
      if (bucketKey.bucket_iso === bucketIso) {
        return counts;
      }
    }

    return undefined;
  },

  getTotal: (aforoId: string, bucketIso: string) => {
    const node = get().byAforo.get(aforoId);
    if (!node) return 0;

    for (const [bucketKeyStr, total] of node.totals.entries()) {
      const bucketKey: BucketKey = JSON.parse(bucketKeyStr);
      if (bucketKey.bucket_iso === bucketIso) {
        return total;
      }
    }

    return 0;
  },
}));
