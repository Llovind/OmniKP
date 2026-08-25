import React from 'react';

const ARCHETYPE_STYLES = {
  Availability: {
    bg: 'rgba(59, 130, 246, 0.12)',
    border: 'rgba(59, 130, 246, 0.4)',
    text: '#93c5fd',
    label: 'Availability',
  },
  Performance: {
    bg: 'rgba(168, 85, 247, 0.12)',
    border: 'rgba(168, 85, 247, 0.4)',
    text: '#c4b5fd',
    label: 'Performance',
  },
  Quality: {
    bg: 'rgba(34, 197, 94, 0.12)',
    border: 'rgba(34, 197, 94, 0.4)',
    text: '#86efac',
    label: 'Quality',
  },
  Reliability: {
    bg: 'rgba(234, 179, 8, 0.12)',
    border: 'rgba(234, 179, 8, 0.4)',
    text: '#fde047',
    label: 'Reliability',
  },
  Composite: {
    bg: 'rgba(99, 102, 241, 0.15)',
    border: 'rgba(99, 102, 241, 0.45)',
    text: '#a5b4fc',
    label: 'Composite',
  },
};

export default function HeatmapMatrix({
  heatmapData,
  selectedCell,
  onSelectCell,
  loading,
}) {
  if (loading) {
    return (
      <div className="glass p-8 flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="w-10 h-10 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading enterprise KPI heatmap matrix...</p>
      </div>
    );
  }

  if (!heatmapData || !heatmapData.locations || heatmapData.locations.length === 0) {
    return (
      <div className="glass p-8 text-center text-slate-400">
        No KPI heatmap data available for this domain.
      </div>
    );
  }

  // Get canonical list of KPIs from the first location (all locations share the same KPIs)
  const sampleKpis = heatmapData.locations[0]?.kpis || [];
  
  // Group KPIs by archetype to create 2-tier header
  const archetypeGroups = [];
  sampleKpis.forEach((kpi) => {
    let group = archetypeGroups.find((g) => g.archetype === kpi.kpi_archetype);
    if (!group) {
      group = {
        archetype: kpi.kpi_archetype,
        kpis: [],
      };
      archetypeGroups.push(group);
    }
    group.kpis.push(kpi);
  });

  return (
    <div className="glass overflow-hidden flex flex-col border border-white/10 shadow-2xl">
      {/* Matrix Controls / Subheader */}
      <div className="px-5 py-3.5 border-b border-white/5 bg-slate-950/40 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
          <h2 className="display-font text-sm font-semibold text-white tracking-wide">
            SDG 9 Infrastructure Health Matrix &bull; {heatmapData.domain_name}
          </h2>
          <span className="text-xs text-slate-400 ml-2">
            ({heatmapData.locations.length} nodes &bull; {sampleKpis.length} KPIs monitored)
          </span>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="dot dot-green"></span>
            <span className="text-slate-300">Normal (&plusmn;1.5&sigma;)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="dot dot-yellow"></span>
            <span className="text-slate-300">Warning (1.5&sigma;&ndash;2.0&sigma;)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="dot dot-red"></span>
            <span className="text-slate-300 font-semibold text-red-400">
              Critical Anomaly (&gt;2.0&sigma;)
            </span>
          </div>
        </div>
      </div>

      {/* Matrix Table Container */}
      <div className="overflow-x-auto overflow-y-auto max-h-[calc(100vh-280px)]">
        <table className="w-full border-collapse text-left text-xs min-w-max">
          <thead>
            {/* Top Tier: Archetype Header Groups */}
            <tr className="bg-slate-950/80 sticky top-0 z-20 backdrop-blur-md">
              <th
                rowSpan={2}
                className="p-3.5 border-b border-r border-white/10 text-slate-300 font-semibold min-w-[200px] sticky left-0 z-30 bg-slate-950/95"
              >
                Monitored Node / Location
              </th>
              <th
                rowSpan={2}
                className="p-3.5 border-b border-r border-white/10 text-center text-slate-300 font-semibold min-w-[110px] sticky left-[200px] z-30 bg-slate-950/95 shadow-[4px_0_12px_rgba(0,0,0,0.5)]"
              >
                Status Split
              </th>
              {archetypeGroups.map((group) => {
                const style = ARCHETYPE_STYLES[group.archetype] || ARCHETYPE_STYLES.Composite;
                return (
                  <th
                    key={group.archetype}
                    colSpan={group.kpis.length}
                    className="py-2 px-3 text-center border-b border-r border-white/10 font-bold uppercase tracking-wider text-[11px]"
                    style={{
                      backgroundColor: style.bg,
                      color: style.text,
                      borderBottomColor: style.border,
                    }}
                  >
                    {group.archetype} ({group.kpis.length})
                  </th>
                );
              })}
            </tr>

            {/* Bottom Tier: Individual KPI Names */}
            <tr className="bg-slate-900/90 sticky top-[33px] z-20 backdrop-blur-md border-b border-white/10">
              {archetypeGroups.flatMap((group) =>
                group.kpis.map((kpi) => (
                  <th
                    key={kpi.kpi_id}
                    className="p-2.5 text-center border-r border-white/5 font-medium text-slate-300 min-w-[95px] max-w-[120px]"
                    title={`${kpi.kpi_name} (${kpi.unit || ''}) - Target: ${kpi.target_value ?? 'N/A'}`}
                  >
                    <div className="truncate text-[11px] font-medium" title={kpi.kpi_name}>
                      {kpi.kpi_name}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                      {kpi.unit || 'idx'}
                    </div>
                  </th>
                ))
              )}
            </tr>
          </thead>

          <tbody className="divide-y divide-white/5">
            {heatmapData.locations.map((loc) => {
              const kpiMap = new Map(loc.kpis.map((k) => [k.kpi_id, k]));
              const hasRed = loc.summary.red > 0;

              return (
                <tr
                  key={loc.location_id}
                  className={`transition-colors hover:bg-white/[0.02] ${
                    hasRed ? 'bg-red-950/10' : ''
                  }`}
                >
                  {/* Location Column (Sticky Left) */}
                  <td className="p-3.5 border-r border-white/10 sticky left-0 z-10 bg-slate-950/95 font-medium text-slate-200">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          hasRed ? 'bg-red-500 shadow-[0_0_8px_#ef4444]' : 'bg-emerald-500'
                        }`}
                      />
                      <div>
                        <div className="font-semibold text-slate-100">{loc.location_name}</div>
                        <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                          {loc.location_type}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Summary Column (Sticky Left 2nd) */}
                  <td className="p-2.5 border-r border-white/10 text-center sticky left-[200px] z-10 bg-slate-950/95 shadow-[4px_0_12px_rgba(0,0,0,0.5)]">
                    <div className="flex items-center justify-center gap-1 font-mono text-[10px]">
                      {loc.summary.red > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 font-bold border border-red-500/40">
                          {loc.summary.red}R
                        </span>
                      )}
                      {loc.summary.yellow > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 font-medium border border-yellow-500/30">
                          {loc.summary.yellow}Y
                        </span>
                      )}
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                        {loc.summary.green}G
                      </span>
                    </div>
                  </td>

                  {/* KPI Cells */}
                  {archetypeGroups.flatMap((group) =>
                    group.kpis.map((kpiHeader) => {
                      const cell = kpiMap.get(kpiHeader.kpi_id);
                      if (!cell) {
                        return (
                          <td
                            key={kpiHeader.kpi_id}
                            className="p-1 border-r border-white/5 text-center text-slate-600"
                          >
                            -
                          </td>
                        );
                      }

                      const isSelected =
                        selectedCell?.kpi_id === cell.kpi_id &&
                        selectedCell?.location_id === loc.location_id;

                      const statusClass =
                        cell.status === 'RED'
                          ? 'cell-red'
                          : cell.status === 'YELLOW'
                          ? 'cell-yellow'
                          : 'cell-green';

                      return (
                        <td
                          key={cell.kpi_id}
                          className="p-1 border-r border-white/5 text-center"
                        >
                          <div
                            id={`cell-${loc.location_id}-${cell.kpi_id}`}
                            onClick={() =>
                              onSelectCell({
                                ...cell,
                                location_id: loc.location_id,
                                location_name: loc.location_name,
                              })
                            }
                            className={`cell ${statusClass} ${
                              isSelected ? 'cell-selected' : ''
                            }`}
                            title={`${cell.kpi_name} @ ${loc.location_name}\nActual: ${cell.actual_value} ${cell.unit}\nTarget: ${cell.target_value ?? 'N/A'}\nZ-Score: ${cell.z_score?.toFixed(2) ?? 'N/A'}\nStatus: ${cell.status}`}
                          >
                            <div className="font-bold text-xs font-mono">
                              {typeof cell.actual_value === 'number'
                                ? cell.actual_value % 1 === 0
                                  ? cell.actual_value
                                  : cell.actual_value.toFixed(1)
                                : cell.actual_value}
                            </div>
                            <div className="text-[10px] opacity-75 font-mono">
                              {cell.z_score !== null && cell.z_score !== undefined
                                ? `Z:${cell.z_score > 0 ? '+' : ''}${cell.z_score.toFixed(1)}`
                                : cell.unit}
                            </div>
                          </div>
                        </td>
                      );
                    })
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
