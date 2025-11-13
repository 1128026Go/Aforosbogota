/**
 * Estado global de UI
 * Gestiona el aforo seleccionado actualmente
 */

import { create } from 'zustand';

type UIState = {
  selectedAforoId: string | 'ALL';
  setSelectedAforoId: (id: string | 'ALL') => void;
};

export const useUI = create<UIState>((set) => ({
  selectedAforoId: 'ALL',
  setSelectedAforoId: (id) => set({ selectedAforoId: id }),
}));
