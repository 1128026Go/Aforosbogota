/**
 * Store para agregación en vivo de conteos por intervalos de 15 min
 * Se conecta con el backend para guardar trayectorias completadas
 */

import { create } from 'zustand';
import { API_BASE_URL } from '../config/api';

export interface IntervalData {
  interval_start: string;
  counts: Record<string, number>; // {mov_rilsa}_{clase}: count
  tracks: Array<{
    track_id: string;
    clase: string;
    mov_rilsa: number;
    origin: string;
    dest: string;
    t_exit: string;
  }>;
}

interface AforoLiveState {
  intervals: string[];
  selectedInterval: string | null;
  currentData: IntervalData | null;

  // Actions
  loadIntervals: (datasetId: string) => Promise<void>;
  selectInterval: (interval: string) => void;
  loadIntervalData: (datasetId: string, interval: string) => Promise<void>;
  sendTrackCompleted: (
    datasetId: string,
    track: {
      track_id: string;
      clase: string;
      t_exit_iso: string;
      origin_access: string;
      dest_access: string;
    }
  ) => Promise<void>;
}

export const useAforoLive = create<AforoLiveState>((set, get) => ({
  intervals: [],
  selectedInterval: null,
  currentData: null,

  loadIntervals: async (datasetId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/intervals`);
      const data = await res.json();
      const intervals = data.intervals || [];
      set({ intervals });

      // Auto-seleccionar el más reciente
      if (intervals.length > 0 && !get().selectedInterval) {
        get().selectInterval(intervals[0]);
      }
    } catch (error) {
      console.error('Error loading intervals:', error);
    }
  },

  selectInterval: (interval: string) => {
    set({ selectedInterval: interval });
  },

  loadIntervalData: async (datasetId: string, interval: string) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/datasets/${datasetId}/intervals/${encodeURIComponent(interval)}`
      );
      const data = await res.json();
      set({ currentData: data });
    } catch (error) {
      console.error('Error loading interval data:', error);
    }
  },

  sendTrackCompleted: async (datasetId, track) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/aforos/${datasetId}/track-completed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(track),
      });

      if (!res.ok) {
        const error = await res.json();
        console.error('Error registering track:', error);
        return;
      }

      // Recargar intervalos y datos
      await get().loadIntervals(datasetId);

      if (get().selectedInterval) {
        await get().loadIntervalData(datasetId, get().selectedInterval!);
      }
    } catch (error) {
      console.error('Error sending track:', error);
    }
  },
}));
