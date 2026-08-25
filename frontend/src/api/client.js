/**
 * api/client.js — API wrapper for OmniKPI backend.
 * Uses Vite proxy (/api → http://127.0.0.1:8000) to avoid CORS issues in dev.
 */

const BASE = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getDomains:   ()                          => request('/domains'),
  getKPIs:      (domainId)                  => request(`/domains/${domainId}/kpis`),
  getLocations: (domainId)                  => request(`/domains/${domainId}/locations`),
  getHeatmap:   (domainId)                  => request(`/domains/${domainId}/heatmap`),
  getAnomalies: (domainId)                  => request(`/domains/${domainId}/anomalies`),
  getHistory:   (domainId, kpiId, locId)    => request(`/domains/${domainId}/kpis/${kpiId}/history?location_id=${locId}`),
  triggerRCA:   (domainId, kpiId, locId)    => request(`/domains/${domainId}/rca`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ kpi_id: kpiId, location_id: locId }),
  }),
};
