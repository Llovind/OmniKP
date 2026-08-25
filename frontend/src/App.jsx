import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import HeatmapMatrix from './components/HeatmapMatrix';
import RCAPanel from './components/RCAPanel';
import KPIDetailModal from './components/KPIDetailModal';
import AnomalyBanner from './components/AnomalyBanner';
import HarvesterModal from './components/HarvesterModal';
import { api } from './api/client';

export default function App() {
  // Domain: 1 = Telco, 2 = Petrochemical
  const [domainId, setDomainId] = useState(1);
  const [heatmapData, setHeatmapData] = useState(null);
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected cell for detail view / RCA
  const [selectedCell, setSelectedCell] = useState(null);
  const [rcaData, setRcaData] = useState(null);
  const [rcaLoading, setRcaLoading] = useState(false);
  const [rcaError, setRcaError] = useState(null);

  // Modals
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showHarvesterModal, setShowHarvesterModal] = useState(false);

  // Load heatmap and anomaly data
  const fetchData = useCallback(async (dId) => {
    setLoading(true);
    setError(null);
    try {
      const [hm, anom] = await Promise.all([
        api.getHeatmap(dId),
        api.getAnomalies(dId),
      ]);
      setHeatmapData(hm);
      setAnomaliesData(anom);
    } catch (err) {
      setError(err.message || 'Failed to connect to OmniKPI telemetry engine');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(domainId);
    setSelectedCell(null);
    setRcaData(null);
  }, [domainId, fetchData]);

  // Aggregate stats across all leaf locations
  const stats = React.useMemo(() => {
    if (!heatmapData || !heatmapData.locations) {
      return { total: 0, red: 0, yellow: 0, green: 0 };
    }
    let total = 0, red = 0, yellow = 0, green = 0;
    heatmapData.locations.forEach((loc) => {
      total += loc.summary.total;
      red += loc.summary.red;
      yellow += loc.summary.yellow;
      green += loc.summary.green;
    });
    return { total, red, yellow, green };
  }, [heatmapData]);

  // Trigger RCA for a given cell
  const handleTriggerRCA = async (cell) => {
    setSelectedCell(cell);
    setRcaLoading(true);
    setRcaError(null);
    setRcaData(null);

    try {
      const result = await api.triggerRCA(domainId, cell.kpi_id, cell.location_id);
      setRcaData(result);
    } catch (err) {
      setRcaError(err.message || 'RCA Agent failed to retrieve diagnostic narration');
    } finally {
      setRcaLoading(false);
    }
  };

  // Handle cell click from matrix
  const handleSelectCell = (cell) => {
    setSelectedCell(cell);
    setRcaData(null);
    setRcaError(null);
    // If it's a critical anomaly, auto-trigger RCA diagnostic
    if (cell.status === 'RED' || cell.is_anomaly) {
      handleTriggerRCA(cell);
    }
  };

  // Handle top banner anomaly selection
  const handleSelectAnomaly = (anomaly) => {
    const cell = {
      ...anomaly,
      location_id: anomaly.location_id,
      location_name: anomaly.location_name,
    };
    handleSelectCell(cell);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#060b18] text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Application Header */}
      <Header
        domain={domainId}
        onDomainChange={(id) => setDomainId(id)}
        date={heatmapData?.date}
        stats={stats}
      />

      {/* Critical Anomaly Alert Banner */}
      <AnomalyBanner
        anomalies={anomaliesData?.anomalies}
        onSelectAnomaly={handleSelectAnomaly}
      />

      {/* Main Workspace Layout */}
      <main className="flex-1 px-6 py-4 flex flex-col lg:flex-row gap-5 overflow-hidden">
        {/* Left: Heatmap Matrix & Controls */}
        <div className={`flex-1 flex flex-col gap-4 min-w-0 transition-all ${selectedCell ? 'lg:w-2/3' : 'w-full'}`}>
          {/* Action Toolbar */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchData(domainId)}
                className="btn-ghost text-xs flex items-center gap-1.5"
                title="Refresh Live Telemetry"
              >
                <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync Telemetry
              </button>

              <button
                onClick={() => setShowHarvesterModal(true)}
                className="btn-ghost text-xs flex items-center gap-1.5 border-emerald-500/20 text-emerald-300 hover:bg-emerald-500/10"
              >
                <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Ingest Excel (Harvester Agent)
              </button>
            </div>

            <div className="text-[11px] text-slate-500 font-mono hidden sm:block">
              Architecture: Star Schema &bull; FTS5 Shift Logs &bull; RapidFuzz ETL
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center justify-between">
              <span>{error}</span>
              <button onClick={() => fetchData(domainId)} className="underline hover:text-white">
                Retry
              </button>
            </div>
          )}

          {/* Matrix Table */}
          <HeatmapMatrix
            heatmapData={heatmapData}
            selectedCell={selectedCell}
            onSelectCell={handleSelectCell}
            loading={loading}
          />
        </div>

        {/* Right: Slide-in / Split Diagnostic RCA Panel */}
        {selectedCell && (
          <div className="lg:w-1/3 min-w-[360px] max-w-[480px] flex flex-col">
            <RCAPanel
              selectedCell={selectedCell}
              rcaData={rcaData}
              loading={rcaLoading}
              error={rcaError}
              onTriggerRCA={handleTriggerRCA}
              onClose={() => setSelectedCell(null)}
              onViewHistory={() => setShowHistoryModal(true)}
            />
          </div>
        )}
      </main>

      {/* KPI 30-Day Historical Trend Modal */}
      {showHistoryModal && selectedCell && (
        <KPIDetailModal
          domainId={domainId}
          selectedCell={selectedCell}
          onClose={() => setShowHistoryModal(false)}
          onTriggerRCA={(cell) => {
            setShowHistoryModal(false);
            handleTriggerRCA(cell);
          }}
        />
      )}

      {/* Harvester Ingestion Modal */}
      {showHarvesterModal && (
        <HarvesterModal
          domainId={domainId}
          onClose={() => setShowHarvesterModal(false)}
        />
      )}
    </div>
  );
}
