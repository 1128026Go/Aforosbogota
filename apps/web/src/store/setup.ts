/**
 * Store para estado de configuración (Cardinals + RILSA)
 */

import { create } from 'zustand';
import { API_BASE_URL } from '../config/api';

export type Cardinal = 'N' | 'S' | 'E' | 'O';

export interface AccessPoint {
  id: string;
  display_name: string;
  cardinal: Cardinal;
  cardinal_official: Cardinal; // Cardinal oficial (N/S/E/O)
  x: number; // coords en canvas (centro del gate o punto legacy)
  y: number;
  gate?: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  polygon?: Array<{ x: number; y: number }>; // Zona poligonal (más precisa que gate)
}

export interface CardinalsConfig {
  datasetId: string;
  accesses: AccessPoint[];
  updatedAt: string;
}

export interface RilsaRule {
  origin: string; // access id
  dest: string;
  rilsa_code: number; // 1-10
}

export interface RilsaMapConfig {
  datasetId: string;
  rules: Record<string, number>; // "origin_id->dest_id": rilsa_code
  updatedAt: string;
}

interface SetupState {
  // Cardinales
  cardinals?: CardinalsConfig;
  hasCardinals: boolean;

  // RILSA
  rilsaMap?: RilsaMapConfig;
  hasRilsaMap: boolean;

  // Actions
  setCardinals: (config: CardinalsConfig) => void;
  setRilsaMap: (config: RilsaMapConfig) => void;
  loadStatus: (datasetId: string) => Promise<void>;
  loadCardinals: (datasetId: string) => Promise<void>;
  loadRilsaMap: (datasetId: string) => Promise<void>;
  saveCardinals: (datasetId: string, config: CardinalsConfig) => Promise<void>;
  saveRilsaMap: (datasetId: string, config: RilsaMapConfig) => Promise<void>;
}

export const useSetup = create<SetupState>((set, get) => ({
  cardinals: undefined,
  hasCardinals: false,
  rilsaMap: undefined,
  hasRilsaMap: false,

  setCardinals: (config) => {
    set({ cardinals: config, hasCardinals: true });
  },

  setRilsaMap: (config) => {
    set({ rilsaMap: config, hasRilsaMap: true });
  },

  loadStatus: async (datasetId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/status`);
      if (!res.ok) {
        throw new Error(`Failed to load status: ${res.status} ${res.statusText}`);
      }
      const status = await res.json();
      set({
        hasCardinals: status.has_cardinals,
        hasRilsaMap: status.has_rilsa_map,
      });
    } catch (error) {
      console.error('Error loading status:', error);
    }
  },

  loadCardinals: async (datasetId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`);
      if (res.ok) {
        const data = await res.json();
        set({ cardinals: data, hasCardinals: true });
      } else if (res.status === 404) {
        // No hay cardinales configurados - esto es normal para datasets nuevos
        set({ cardinals: undefined, hasCardinals: false });
      } else {
        throw new Error(`Failed to load cardinals: ${res.status} ${res.statusText}`);
      }
    } catch (error) {
      console.error('Error loading cardinals:', error);
      set({ cardinals: undefined, hasCardinals: false });
    }
  },

  loadRilsaMap: async (datasetId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/rilsa-map`);
      if (res.ok) {
        const data = await res.json();
        set({ rilsaMap: data, hasRilsaMap: true });
      } else if (res.status === 404) {
        // No hay mapa RILSA configurado - esto es normal para datasets nuevos
        set({ rilsaMap: undefined, hasRilsaMap: false });
      } else {
        throw new Error(`Failed to load RILSA map: ${res.status} ${res.statusText}`);
      }
    } catch (error) {
      console.error('Error loading rilsa map:', error);
      set({ rilsaMap: undefined, hasRilsaMap: false });
    }
  },

  saveCardinals: async (datasetId: string, config: CardinalsConfig) => {
    try {
      // Validar que no haya NaN en las coordenadas
      const hasNaN = config.accesses.some((acc) => {
        if (isNaN(acc.x) || isNaN(acc.y)) return true;
        if (acc.gate) {
          if (isNaN(acc.gate.x1) || isNaN(acc.gate.y1) || isNaN(acc.gate.x2) || isNaN(acc.gate.y2)) {
            return true;
          }
        }
        return false;
      });

      if (hasNaN) {
        throw new Error('No se puede guardar: las coordenadas contienen valores inválidos (NaN)');
      }

      // DEBUG: Ver qué se está enviando al backend
      console.log('🚀 Enviando al backend:', JSON.stringify(config, null, 2));
      config.accesses.forEach(acc => {
        if ((acc as any).polygon && (acc as any).polygon.length > 0) {
          console.log(`  ✓ ${acc.cardinal_official} - polígono incluido en request: ${(acc as any).polygon.length} puntos`);
        } else {
          console.log(`  ✗ ${acc.cardinal_official} - SIN polígono en request`);
        }
      });

      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!res.ok) throw new Error('Error saving cardinals');

      set({ cardinals: config, hasCardinals: true });
      await get().loadStatus(datasetId);
    } catch (error) {
      console.error('Error saving cardinals:', error);
      throw error;
    }
  },

  saveRilsaMap: async (datasetId: string, config: RilsaMapConfig) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/rilsa-map`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!res.ok) throw new Error('Error saving RILSA map');

      set({ rilsaMap: config, hasRilsaMap: true });
      await get().loadStatus(datasetId);
    } catch (error) {
      console.error('Error saving RILSA map:', error);
      throw error;
    }
  },
}));
