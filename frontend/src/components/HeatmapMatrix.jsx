export default function HeatmapMatrix({heatmapData, selectedCell, onSelectCell, loading}) {
  if (loading) return <div role="status" className="glass p-8">Loading KPI performance…</div>;
  if (!heatmapData?.locations?.length) return <div className="glass p-8">No KPI heatmap data available for this domain.</div>;
  const locations = heatmapData.locations;
  const kpis = [...new Map(locations.flatMap(loc => loc.kpis).map(k => [k.kpi_id,k])).values()].sort((a,b) => a.kpi_archetype.localeCompare(b.kpi_archetype) || a.kpi_name.localeCompare(b.kpi_name));
  const groups = [...new Set(kpis.map(k => k.kpi_archetype))];
  const maps = locations.map(loc => new Map(loc.kpis.map(k => [k.kpi_id,k])));
  const status = value => value === 'RED' ? 'Missing target' : value === 'GREEN' ? 'Meeting target' : 'Target unavailable';
  return <section className="glass overflow-hidden">
    <div className="matrix-toolbar"><div className="matrix-title"><h2 className="display-font">KPI performance</h2><span className="matrix-meta">{kpis.length} KPIs · {locations.length} locations</span></div><div className="matrix-legend" aria-label="Target attainment legend">{[['green','Meeting target'],['yellow','Target unavailable'],['red','Missing target']].map(([color,label]) => <div key={color}><span className={'dot dot-'+color}/>{label}</div>)}</div></div>
    <p id="matrix-help" className="matrix-help">Scroll down to review KPIs. Select a reading to investigate.</p>
    <div className="table-region kpi-rows-scroll" role="region" aria-label="KPI readings by location" aria-describedby="matrix-help" tabIndex={0}>
      <table className="matrix-table kpi-rows-table"><thead><tr><th scope="col" className="kpi-name-column">KPI / metric</th>{locations.map(loc => <th scope="col" key={loc.location_id}><span className="matrix-node-name">{loc.location_name}</span><span className="matrix-node-type">{loc.location_type}</span><span className="kpi-location-summary">{loc.summary.green} meeting · {loc.summary.red} missing{loc.summary.yellow ? ` · ${loc.summary.yellow} unavailable` : ''}</span></th>)}</tr></thead>
      {groups.map(group => <tbody key={group}><tr className="kpi-category-row"><th scope="rowgroup" colSpan={locations.length+1}>{group}</th></tr>{kpis.filter(k => k.kpi_archetype === group).map(kpi => <tr key={kpi.kpi_id}>
        <th scope="row" className="kpi-name-column"><span className="kpi-row-name">{kpi.kpi_name}</span><span className="matrix-unit">{kpi.unit || 'idx'}</span></th>
        {locations.map((loc,index) => {
          const cell = maps[index].get(kpi.kpi_id);
          if (!cell) return <td key={loc.location_id} className="kpi-reading-slot"><span className="kpi-no-reading">Not reported</span></td>;
          const selected = selectedCell?.kpi_id === cell.kpi_id && selectedCell?.location_id === loc.location_id;
          const baseline = cell.z_score == null ? 'No baseline' : `Z: ${cell.z_score.toFixed(1)}`;
          return <td key={loc.location_id} className="kpi-reading-slot"><button type="button" id={`cell-${loc.location_id}-${cell.kpi_id}`} aria-pressed={selected} className={`cell ${cell.status === 'RED' ? 'cell-red' : cell.status === 'GREEN' ? 'cell-green' : 'cell-yellow'} ${selected ? 'cell-selected' : ''}`}
            aria-label={`${cell.kpi_name}, ${loc.location_name}: ${cell.actual_value} ${cell.unit || ''}; ${status(cell.status)}. Target ${cell.target_value ?? 'not supplied'}. ${baseline}. Select to investigate.`}
            title={`Actual: ${cell.actual_value} ${cell.unit || ''}\nTarget: ${cell.target_value ?? 'not supplied'}\n${status(cell.status)}\n${baseline}`}
            onClick={() => onSelectCell({...cell,location_id:loc.location_id,location_name:loc.location_name})}>
            <span className="cell-value">{typeof cell.actual_value === 'number' ? Number.isInteger(cell.actual_value) ? cell.actual_value : cell.actual_value.toFixed(1) : cell.actual_value}</span><span className="cell-context">{baseline}</span>
          </button></td>;
        })}
      </tr>)}</tbody>)}</table>
    </div>
  </section>;
}
