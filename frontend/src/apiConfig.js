/**
 * API Base URL configuration.
 *
 * In development   → backend runs locally on :8000, Vite proxies /api → localhost:8000
 * In production    → set VITE_API_BASE_URL in frontend/.env.production to the Render URL
 *                    e.g.  VITE_API_BASE_URL=https://mp-mitra-backend.onrender.com
 *                    If not set, falls back to '' (same-origin, which works when Firebase
 *                    Hosting proxies /api to the backend).
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default API_BASE;
