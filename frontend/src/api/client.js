/**
 * api/client.js — API wrapper for OmniKPI backend.
 * Uses Vite proxy (/api → http://127.0.0.1:8000) to avoid CORS issues in dev.
 */

const BASE = new URLSearchParams(window.location.search).get('demo') === '1' ? '/api/demo/workspace/api/v1' : '/api/v1';

function query(options = {}) {
  const values = Object.entries(options).filter(([, value]) => value !== '' && value !== null && value !== undefined);
  return values.length ? `?${new URLSearchParams(values)}` : '';
}

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
  getHeatmap:   (domainId, options)         => request(`/domains/${domainId}/heatmap${query(options)}`),
  getAnomalies: (domainId, options)         => request(`/domains/${domainId}/anomalies${query(options)}`),
  getPeriods:   (domainId, options)         => request(`/domains/${domainId}/periods${query(options)}`),
  getSubmissions: (domainId)                => request(`/domains/${domainId}/submissions`),
  getHistory:   (domainId, kpiId, locId, asOf) => request(`/domains/${domainId}/kpis/${kpiId}/history${query({location_id: locId, as_of: asOf})}`),
  triggerRCA:   (domainId, kpiId, locId, factId) => request(`/domains/${domainId}/rca`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ kpi_id: kpiId, location_id: locId, fact_id: factId }),
  }),
  previewReport: (domainId, form) => request(`/domains/${domainId}/submissions/preview`, {method: 'POST', body: form}),
  reviewReport: (domainId, id, payload) => request(`/domains/${domainId}/submissions/${id}/review`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
  }),
  confirmReport: (domainId, id, payload) => request(`/domains/${domainId}/submissions/${id}/confirm`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
  }),
  addFeedback: (domainId, payload) => request(`/domains/${domainId}/feedback`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
  }),
};
