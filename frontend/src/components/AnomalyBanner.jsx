import React from 'react';

export default function AnomalyBanner({ anomalies, onSelectAnomaly }) {
  if (!anomalies || anomalies.length === 0) {
    return null;
  }

  // Find top anomaly by Z-score magnitude
  const topAnomaly = anomalies[0];

  return (
    <div className="mx-6 mt-4 p-3.5 rounded-xl border border-red-500/30 bg-gradient-to-r from-red-950/40 via-slate-900/60 to-slate-900/40 backdrop-blur-md shadow-lg flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 flex-shrink-0 animate-pulse">
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-red-400 uppercase tracking-wider font-mono">
              Critical Anomaly Alert ({anomalies.length} Detected)
            </span>
            <span className="text-xs text-slate-500">&bull;</span>
            <span className="text-xs text-slate-300 font-medium">
              Primary: <strong className="text-white">{topAnomaly.kpi_name}</strong> @ {topAnomaly.location_name}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Statistical deviation: <span className="text-red-300 font-mono font-semibold">Z = {topAnomaly.z_score.toFixed(2)}</span> ({topAnomaly.actual_value} {topAnomaly.unit} vs target {topAnomaly.target_value ?? 'N/A'}).
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onSelectAnomaly(topAnomaly)}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/40 transition-colors flex items-center gap-1.5 shadow-[0_0_12px_rgba(239,68,68,0.25)]"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Diagnose Primary ({topAnomaly.kpi_name.slice(0, 18)}...)
        </button>
      </div>
    </div>
  );
}
