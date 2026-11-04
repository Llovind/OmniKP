
export default function HeatmapMatrix({
  heatmapData,
  selectedCell,
  onSelectCell,
  loading,
}) {
  if (loading) {
    return (
      <div role="status" aria-busy="true" className="glass p-8 flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="w-10 h-10 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading enterprise KPI heatmap matrix…</p>
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

  // Different divisions and locations may report different KPI sets.
  const sampleKpis = [...new Map(heatmapData.locations.flatMap(loc => loc.kpis).map(kpi => [kpi.kpi_id, kpi])).values()]
    .sort((a, b) => a.kpi_archetype.localeCompare(b.kpi_archetype) || a.kpi_name.localeCompare(b.kpi_name));
  
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
      <div className="matrix-toolbar">
        <div className="matrix-title">
          <h2 className="display-font">
            KPI performance
          </h2>
          <span className="matrix-meta">
            ({heatmapData.locations.length} nodes &bull; {sampleKpis.length} KPIs monitored)
          </span>
        </div>

        {/* Legend */}
        <div className="matrix-legend" aria-label="Target attainment legend">
          <div className="flex items-center gap-1.5">
            <span className="dot dot-green"></span>
            <span className="text-slate-300">Meeting target</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="dot dot-yellow"></span>
            <span className="text-slate-300">Target unavailable</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="dot dot-red"></span>
            <span className="text-slate-300 font-semibold text-red-400">
              Missing target
            </span>
          </div>
        </div>
      </div>

      {/* Matrix Table Container */}
      <p id="matrix-help" className="matrix-help">Select a reading to investigate. Scroll the table to compare all KPIs.</p>
      <div className="matrix-scroll table-region max-h-[calc(100vh-280px)]" role="region" aria-label="KPI performance matrix" aria-describedby="matrix-help" tabIndex={0}>
        <table className="matrix-table w-full text-left text-xs min-w-max">
          <thead className="matrix-head">
            {/* Top Tier: Archetype Header Groups */}
            <tr className="bg-slate-950/80">
              <th
                rowSpan={2}
                scope="col"
                className="p-3.5 border-b border-r border-white/10 text-slate-300 font-semibold min-w-[200px] sticky left-0 z-30 bg-slate-950/95"
              >
                Monitored Node / Location
              </th>
              <th
                rowSpan={2}
                scope="col"
                className="p-3.5 border-b border-r border-white/10 text-center text-slate-300 font-semibold min-w-[110px] bg-slate-950/95"
              >
                Status Split
              </th>
              {archetypeGroups.map((group) => (
                  <th
                    key={group.archetype}
                    colSpan={group.kpis.length}
                    scope="colgroup"
                    className="matrix-group py-2 px-3 text-center border-b border-r border-white/10 font-semibold uppercase tracking-wider text-xs"
                  >
                    {group.archetype} ({group.kpis.length})
                  </th>
              ))}
            </tr>

            {/* Bottom Tier: Individual KPI Names */}
            <tr className="bg-slate-900/90 border-b border-white/10">
              {archetypeGroups.flatMap((group) =>
                group.kpis.map((kpi) => (
                  <th
                    key={kpi.kpi_id}
                    scope="col"
                    className="p-2.5 text-center border-r border-white/5 font-medium text-slate-300 min-w-[95px] max-w-[120px]"
                    title={`${kpi.kpi_name} (${kpi.unit || ''}) - Target: ${kpi.target_value ?? 'N/A'}`}
                  >
                    <div className="kpi-column-name" title={kpi.kpi_name}>
                      {kpi.kpi_name}
                    </div>
                    <div className="matrix-unit text-slate-500 mt-0.5">
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
                  <th scope="row" className="p-3.5 border-r border-white/10 sticky left-0 z-10 bg-slate-950/95 font-medium text-slate-200">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          hasRed ? 'dot-red' : 'dot-green'
                        }`}
                      />
                      <div>
                        <div className="matrix-node-name font-semibold text-slate-100">{loc.location_name}</div>
                        <div className="matrix-node-type">
                          {loc.location_type}
                        </div>
                      </div>
                    </div>
                  </th>

                  {/* Summary Column (Sticky Left 2nd) */}
                  <td className="p-2.5 border-r border-white/10 text-center bg-slate-950/95">
                    <div className="flex items-center justify-center gap-1 font-mono text-[10px]">
                      {loc.summary.red > 0 && (
                        <span className="status-count status-count-red" aria-label={`${loc.summary.red} missing target`}>
                          {loc.summary.red}R
                        </span>
                      )}
                      {loc.summary.yellow > 0 && (
                        <span className="status-count status-count-yellow" aria-label={`${loc.summary.yellow} target unavailable`}>
                          {loc.summary.yellow}Y
                        </span>
                      )}
                      <span className="status-count status-count-green" aria-label={`${loc.summary.green} meeting target`}>
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
                          <button
                            type="button"
                            aria-pressed={isSelected}
                            aria-label={`${cell.kpi_name}, ${loc.location_name}: ${cell.actual_value} ${cell.unit || ''}; ${cell.status === 'RED' ? 'Missing target' : cell.status === 'GREEN' ? 'Meeting target' : 'Target unavailable'}. Target ${cell.target_value ?? 'not supplied'}. ${cell.z_score == null ? 'No historical baseline.' : 'Z-score '+cell.z_score.toFixed(2)+'.'} Select to investigate.`}
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
                            <div className="cell-value">
                              {typeof cell.actual_value === 'number'
                                ? cell.actual_value % 1 === 0
                                  ? cell.actual_value
                                  : cell.actual_value.toFixed(1)
                                : cell.actual_value}
                            </div>
                            <div className="cell-context">
                              {cell.z_score !== null && cell.z_score !== undefined
                                ? `Z:${cell.z_score > 0 ? '+' : ''}${cell.z_score.toFixed(1)}`
                                  : 'No baseline'}
                            </div>
                          </button>
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
