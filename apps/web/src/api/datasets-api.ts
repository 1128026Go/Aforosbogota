/**
 * API Client para la gestión de datasets (upload, delete, etc.)
 */

import { API_BASE_URL } from '@/config/api';

const DATASETS_BASE_URL = `${API_BASE_URL}/datasets`;

/**
 * Helper para hacer requests con manejo de errores
 */
async function fetchAPI<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export interface DatasetFile {
  id: string;
  name: string;
  size: number;
  created_at: number;
}

export interface UploadResponse {
  id: string;
  name: string;
  message: string;
  size: number;
}

/**
 * Lista todos los datasets subidos
 */
export async function listUploadedDatasets(): Promise<{ datasets: DatasetFile[] }> {
  return fetchAPI(`${DATASETS_BASE_URL}`);
}

/**
 * Sube un dataset PKL
 */
export async function uploadDataset(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return fetchAPI(`${DATASETS_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * Elimina un dataset
 */
export async function deleteDataset(datasetId: string): Promise<{ message: string }> {
  return fetchAPI(`${DATASETS_BASE_URL}/${datasetId}`, {
    method: 'DELETE',
  });
}

/**
 * Obtiene información de un dataset específico
 */
export async function getDataset(datasetId: string): Promise<DatasetFile & { path: string }> {
  return fetchAPI(`${DATASETS_BASE_URL}/${datasetId}`);
}