// API client helper for the unified Bogota Traffic app
const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3004';
const AFOROS = import.meta.env.VITE_AF_ORIGIN ?? 'http://localhost:3001';

function request(url: string, options: RequestInit = {}) {
  return fetch(url, { ...options }).then(async res => {
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || `HTTP ${res.status}`);
    }
    return res.json();
  });
}

export const datasets = {
  list: () => request(`${API}/api/v1/datasets`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API}/api/v1/datasets`, { method: 'POST', body: formData }).then(r => r.json());
  },
  setCardinals: (pklId: string, body: any) => request(`${API}/api/v1/datasets/${pklId}/cardinals`, { method: 'PUT', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } }),
  setDelimiters: (pklId: string, body: any) => request(`${API}/api/v1/datasets/${pklId}/delimiters`, { method: 'PUT', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } }),
  inferMovements: (pklId: string) => request(`${API}/api/v1/datasets/${pklId}/infer-movements`, { method: 'POST' }),
};

export const aforos = {
  init: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${AFOROS}/api/v1/aforos/process/init`, { method: 'POST', body: formData }).then(r => r.json());
  },
  run: (pklId: string) => request(`${AFOROS}/api/v1/aforos/process/run?pkl_id=${pklId}`, { method: 'POST' }),
  status: (jobId: string) => request(`${AFOROS}/api/v1/aforos/status/${jobId}`),
  validate: (pkl: string, runs: number = 5) => request(`${AFOROS}/api/v1/aforos/validate`, { method: 'POST', body: JSON.stringify({ pkl, runs }), headers: { 'Content-Type': 'application/json' } }),
  multiaforo: (intersectionId: string, pklIds: string[]) => request(`${AFOROS}/api/v1/aforos/multiaforo`, { method: 'POST', body: JSON.stringify({ intersection_id: intersectionId, pkl_ids: pklIds }), headers: { 'Content-Type': 'application/json' } }),
};

export const reports = {
  final: (pklId: string) => request(`${API}/api/v1/aforos/${pklId}/final`),
  pdf: (pklId: string) => request(`${API}/api/v1/reports/pdf`, { method: 'POST', body: JSON.stringify({ pkl_id: pklId }), headers: { 'Content-Type': 'application/json' } }),
};
