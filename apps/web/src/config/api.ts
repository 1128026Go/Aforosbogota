/**
 * API Configuration
 */

// En desarrollo local (npm run dev fuera de docker) pegamos directo al 3004.
// En producción / docker usamos ruta relativa (proxy /api a 3004).
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV
    ? "http://localhost:3004/api/v1"
    : "/api/v1");

export { API_BASE_URL };
