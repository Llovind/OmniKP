import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';

export default function KPIDetailModal({
  domainId,
  selectedCell,
  onClose,
  onTriggerRCA,
}) {
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedCell) return;
    let isMounted = true;

    api
      .getHistory(domainId, selectedCell.kpi_id, selectedCell.location_id, selectedCell.date)
      .then((data) => {
        if (isMounted) {
          setHistoryData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to fetch KPI history');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [domainId, selectedCell]);

  if (!selectedCell) return null;

  // Format chart data
  const chartPoints =
    historyData?.history.map((h) => ({
      date: h.date,
      actual: h.actual_value,
      zScore: h.z_score,
      isAnomaly: h.is_anomaly,
      status: h.status,
      target: h.target_value,
    })) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="glass w-full max-w-3xl border border-white/15 shadow-2xl rounded-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-white/10 bg-slate-950/70 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase text-indigo-400 font-semibold tracking-wider">
                {selectedCell.kpi_archetype}
              </span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-xs text-slate-400">{selectedCell.location_name}</span>
            </div>
            <h2 className="display-font text-lg font-bold text-white mt-0.5">
              {selectedCell.kpi_name}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Quick Metrics Header */}
          <div className="grid grid-cols-4 gap-3">
            <div className="glass-sm p-3 border border-white/5">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Selected Reading</span>
              <span className="display-font text-lg font-bold text-slate-100">
                {selectedCell.actual_value} <span className="text-xs font-normal text-slate-400">{selectedCell.unit}</span>
              </span>
            </div>
            <div className="glass-sm p-3 border border-white/5">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Target Threshold</span>
              <span className="display-font text-lg font-medium text-indigo-300">
                {historyData?.target_threshold ?? selectedCell.target_value ?? 'N/A'}{' '}
                <span className="text-xs font-normal text-slate-400">{selectedCell.unit}</span>
              </span>
            </div>
            <div className="glass-sm p-3 border border-white/5">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Standard Rule</span>
              <span className="text-xs font-medium text-slate-200 block mt-1">
                {(historyData?.higher_is_better ?? selectedCell.higher_is_better) ? 'Higher is Better' : 'Lower is Better'}
              </span>
            </div>
            <div className="glass-sm p-3 border border-white/5">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Latest Z-Score</span>
              <span
                className={`display-font text-lg font-bold ${
                  Math.abs(selectedCell.z_score || 0) > 2 ? 'text-red-400' : 'text-emerald-400'
                }`}
              >
                {selectedCell.z_score !== null && selectedCell.z_score !== undefined
                  ? `${selectedCell.z_score > 0 ? '+' : ''}${selectedCell.z_score.toFixed(2)}`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Historical Trend Chart */}
          <div className="glass-sm p-4 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Recent Readings &amp; Applicable Targets (up to 30)
              </h4>
              <span className="text-[11px] text-slate-400">
                Unit: <strong className="text-slate-200">{selectedCell.unit}</strong>
              </span>
            </div>

            {loading ? (
              <div className="h-64 flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                <span className="text-xs text-slate-400">Rendering telemetry series...</span>
              </div>
            ) : error ? (
              <div className="h-64 flex items-center justify-center text-xs text-red-400">
                {error}
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartPoints}
                    margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (active && payload && payload.length) {
                          const pt = payload[0].payload;
                          return (
                            <div className="glass p-3 border border-white/15 text-xs space-y-1 shadow-xl">
                              <p className="font-bold text-slate-200">{label}</p>
                              <p className="text-indigo-300 font-mono">
                                Actual: <strong>{pt.actual} {selectedCell.unit}</strong>
                              </p>
                              {pt.zScore !== null && pt.zScore !== undefined && (
                                <p className={`font-mono ${Math.abs(pt.zScore) > 2 ? 'text-red-400 font-bold' : 'text-slate-400'}`}>
                                  Z-Score: {pt.zScore.toFixed(2)}
                                </p>
                              )}
                              <p className="text-[10px] font-mono uppercase">
                                Status: <span className={pt.status === 'RED' ? 'text-red-400 font-bold' : pt.status === 'YELLOW' ? 'text-yellow-300' : 'text-emerald-400'}>{pt.status}</span>
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line type="stepAfter" dataKey="target" name="Applicable target" stroke="#f97316" strokeDasharray="4 4" dot={false} connectNulls={false} />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      dot={(props) => {
                        const { cx, cy, payload } = props;
                        if (payload.status === 'RED') {
                          return (
                            <circle
                              key={`dot-${payload.date}`}
                              cx={cx}
                              cy={cy}
                              r={5}
                              fill="#ef4444"
                              stroke="#ffffff"
                              strokeWidth={1.5}
                            />
                          );
                        }
                        return (
                          <circle
                            key={`dot-${payload.date}`}
                            cx={cx}
                            cy={cy}
                            r={2.5}
                            fill="#6366f1"
                          />
                        );
                      }}
                      activeDot={{ r: 6, fill: '#38bdf8' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 bg-slate-950/70 flex items-center justify-between">
          <button onClick={onClose} className="btn-ghost text-xs">
            Close Detail View
          </button>

          <button
            onClick={() => {
              onClose();
              onTriggerRCA(selectedCell);
            }}
            className="btn-primary text-xs flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Review / draft RCA
          </button>
        </div>
      </div>
    </div>
  );
}
