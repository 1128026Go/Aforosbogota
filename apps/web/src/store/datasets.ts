/**
 * Store para gestión de datasets
 * Catálogo de PKLs subidos y su configuración
 */

import { create } from 'zustand';
import { API_BASE_URL } from '../config/api';

export interface DatasetInfo {
  id: string;
  name: string;
  created_at: string;
  frames: number;
  tracks: number;
}

export interface DatasetStatus {
  has_cardinals: boolean;
  has_rilsa_map: boolean;
  intervals_ready: boolean;
}

interface DatasetsState {
  datasets: DatasetInfo[];
  selectedDatasetId: string | null;
  status: DatasetStatus | null;

  // Actions
  loadDatasets: () => Promise<void>;
  selectDataset: (id: string) => void;
  loadStatus: (id: string) => Promise<void>;
  uploadDataset: (file: File) => Promise<string>;
}

export const useDatasets = create<DatasetsState>((set, get) => ({
  datasets: [],
  selectedDatasetId: null,
  status: null,

  loadDatasets: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/datasets`);
      if (!res.ok) {
        throw new Error(`Failed to load datasets: ${res.status} ${res.statusText}`);
      }
      const datasets = await res.json();
      set({ datasets });
    } catch (error) {
      console.error('Error loading datasets:', error);
    }
  },

  selectDataset: (id: string) => {
    set({ selectedDatasetId: id });
    get().loadStatus(id);
  },

  loadStatus: async (id: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/datasets/${id}/status`);
      if (!res.ok) {
        throw new Error(`Failed to load dataset status: ${res.status} ${res.statusText}`);
      }
      const status = await res.json();
      set({ status });
    } catch (error) {
      console.error('Error loading status:', error);
    }
  },

  uploadDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error('Error uploading file');
    }

    const dataset = await res.json();
    await get().loadDatasets();
    return dataset.id;
  },
}));
