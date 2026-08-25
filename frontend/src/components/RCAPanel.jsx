import React from 'react';

export default function RCAPanel({
  selectedCell,
  rcaData,
  loading,
  error,
  onTriggerRCA,
  onClose,
  onViewHistory,
}) {
  if (!selectedCell) return null;

  const isAnomaly = selectedCell.status === 'RED' || selectedCell.is_anomaly;

  return (
    <aside className="glass border border-white/10 flex flex-col h-full overflow-hidden shadow-2xl rca-enter">
      {/* Panel Header */}
      <div className="p-4 border-b border-white/10 bg-slate-950/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 className="display-font text-sm font-bold text-white flex items-center gap-2">
              RCA Diagnostic Agent
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-500/15 border border-orange-500/30 text-orange-300 font-mono">
                SDG 9 Resilience
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">Statistical Anomaly &amp; Operational Log Synthesis</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
          title="Close Diagnostic Panel"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Main Panel Content (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Selected KPI Context Card */}
        <div className="glass-sm p-3.5 space-y-2.5 border border-white/10">
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="text-[10px] font-mono uppercase text-indigo-400 tracking-wider">
                {selectedCell.kpi_archetype || 'Archetype'}
              </span>
              <h4 className="text-sm font-bold text-slate-100 mt-0.5">{selectedCell.kpi_name}</h4>
              <p className="text-xs text-slate-400 font-medium">@ {selectedCell.location_name}</p>
            </div>

            <span
              className={`px-2.5 py-1 rounded-md text-[11px] font-bold font-mono ${
                selectedCell.status === 'RED'
                  ? 'bg-red-500/20 text-red-300 border border-red-500/40 shadow-[0_0_12px_rgba(239,68,68,0.3)]'
                  : selectedCell.status === 'YELLOW'
                  ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}
            >
              {selectedCell.status}
            </span>
          </div>

          {/* Metric Comparison Badges */}
          <div className="grid grid-cols-3 gap-2 pt-1 border-t border-white/5">
            <div className="bg-white/[0.03] p-2 rounded border border-white/5">
              <span className="text-[10px] text-slate-500 block">Actual</span>
              <span className="font-mono font-bold text-slate-100 text-xs">
                {selectedCell.actual_value} {selectedCell.unit}
              </span>
            </div>
            <div className="bg-white/[0.03] p-2 rounded border border-white/5">
              <span className="text-[10px] text-slate-500 block">Target</span>
              <span className="font-mono font-medium text-slate-300 text-xs">
                {selectedCell.target_value ?? 'N/A'} {selectedCell.unit}
              </span>
            </div>
            <div className="bg-white/[0.03] p-2 rounded border border-white/5">
              <span className="text-[10px] text-slate-500 block">Z-Score</span>
              <span
                className={`font-mono font-bold text-xs ${
                  Math.abs(selectedCell.z_score || 0) > 2 ? 'text-red-400' : 'text-slate-300'
                }`}
              >
                {selectedCell.z_score !== null && selectedCell.z_score !== undefined
                  ? `${selectedCell.z_score > 0 ? '+' : ''}${selectedCell.z_score.toFixed(2)}`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={() => onViewHistory(selectedCell)}
              className="btn-ghost flex-1 py-1.5 text-[11px] flex items-center justify-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              View 30-Day Trend
            </button>

            {!rcaData && !loading && (
              <button
                onClick={() => onTriggerRCA(selectedCell)}
                className="btn-primary flex-1 py-1.5 text-[11px] flex items-center justify-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Diagnose Root Cause
              </button>
            )}
          </div>
        </div>

        {/* Loading State Skeleton */}
        {loading && (
          <div className="space-y-3 p-4 glass-sm border border-indigo-500/20">
            <div className="flex items-center gap-2 text-indigo-300 font-medium animate-pulse">
              <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
              <span>Harvester FTS5 querying shift logs &amp; evaluating telemetry...</span>
            </div>
            <div className="h-4 skeleton w-3/4"></div>
            <div className="h-16 skeleton w-full"></div>
            <div className="h-12 skeleton w-5/6"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 space-y-1">
            <div className="font-semibold flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              RCA Retrieval Notice
            </div>
            <p className="text-[11px] text-red-400/90">{error}</p>
          </div>
        )}

        {/* Diagnostic Results */}
        {rcaData && (
          <div className="space-y-3.5">
            {/* Deterministic Confidence Score Card */}
            <div className="glass-sm p-3.5 border border-indigo-500/20 bg-indigo-950/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
                  Statistical Confidence Score
                </span>
                <span className="display-font text-base font-bold text-white font-mono">
                  {rcaData.confidence_score}%
                </span>
              </div>

              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="confidence-fill"
                  style={{ width: `${rcaData.confidence_score}%` }}
                ></div>
              </div>

              <p className="text-[10px] text-slate-400 font-mono leading-relaxed">
                <span className="text-indigo-400 font-semibold">&bull; Basis: </span>
                {rcaData.confidence_basis}
              </p>
            </div>

            {/* Root Cause Card */}
            <div className="glass-sm p-3.5 border border-white/10 space-y-1.5">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold text-[11px] uppercase tracking-wider">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Root Cause Synthesis
              </div>
              <p className="text-slate-200 leading-relaxed font-normal">
                {rcaData.root_cause}
              </p>
            </div>

            {/* Prescriptive Action Plan */}
            <div className="glass-sm p-3.5 border border-emerald-500/20 bg-emerald-950/10 space-y-1.5">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-[11px] uppercase tracking-wider">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Prescriptive Action Plan (Human-in-the-Loop)
              </div>
              <p className="text-slate-200 leading-relaxed font-normal">
                {rcaData.prescriptive_action}
              </p>
            </div>

            {/* Blast Radius / Impact */}
            <div className="glass-sm p-3.5 border border-white/10 space-y-1.5">
              <div className="flex items-center gap-1.5 text-slate-300 font-bold text-[11px] uppercase tracking-wider">
                <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Blast Radius &amp; Operational Impact
              </div>
              <p className="text-slate-300 leading-relaxed font-normal">
                {rcaData.estimated_impact}
              </p>
            </div>

            {/* Metadata Footer */}
            <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
              <span>Shift Logs Matched: {rcaData.shift_logs_retrieved}</span>
              <span className="truncate max-w-[180px]" title={rcaData.llm_model}>
                Model: {rcaData.llm_model}
              </span>
            </div>
          </div>
        )}

        {/* ISA-95 / Purdue Model Advisory Disclaimer */}
        <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-[10px] text-slate-400 space-y-1">
          <div className="font-semibold text-indigo-300 flex items-center gap-1">
            <span>🛡️ Enterprise Safety Boundary (ISA-95 Level 3)</span>
          </div>
          <p className="leading-normal">
            AI recommendations are strictly advisory. In compliance with industrial safety controls,
            no automatic actuators or direct operational commands are executed without certified operator authorization.
          </p>
        </div>
      </div>
    </aside>
  );
}
