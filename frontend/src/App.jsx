import { useEffect, useRef, useState } from 'react';
import Header from './components/Header';
import HeatmapMatrix from './components/HeatmapMatrix';
import RCAPanel from './components/RCAPanel';
import KPIDetailModal from './components/KPIDetailModal';
import HarvesterModal from './components/HarvesterModal';
import { api } from './api/client';

export default function App() {
  const domainId = 1;
  const [dataset, setDataset] = useState('submitted');
  const [date, setDate] = useState(() => new URLSearchParams(window.location.search).get('demo') === '1' ? '2026-06-30' : '');
  const [division, setDivision] = useState('');
  const [periods, setPeriods] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [heatmap, setHeatmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(null);
  const [rca, setRca] = useState(null);
  const [rcaLoading, setRcaLoading] = useState(false);
  const [rcaError, setRcaError] = useState('');
  const [upload, setUpload] = useState(false);
  const [history, setHistory] = useState(false);
  const [notice, setNotice] = useState('');
  const rcaRequest = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const options = {dataset, division, date};
    Promise.all([
      api.getHeatmap(domainId, options),
      api.getPeriods(domainId, {dataset, division}),
      api.getSubmissions(domainId),
    ]).then(([data, days, reports]) => {
      if (!cancelled) {
        setHeatmap(data); setPeriods(days); setSubmissions(reports); setError('');
      }
    }).catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [dataset, division, date, revision]);

  const resetSelection = () => {
    rcaRequest.current += 1;
    setSelected(null); setRca(null); setRcaError(''); setRcaLoading(false); setHistory(false);
  };
  const changeView = (setter, value) => {
    resetSelection(); setLoading(true); setter(value);
  };
  const diagnose = async (cell) => {
    const requestId = ++rcaRequest.current;
    setSelected(cell); setRca(null); setRcaError(''); setRcaLoading(true);
    try {
      const result = await api.triggerRCA(domainId, cell.kpi_id, cell.location_id, cell.fact_id);
      if (requestId === rcaRequest.current) setRca(result);
    } catch (err) {
      if (requestId === rcaRequest.current) setRcaError(err.message);
    } finally {
      if (requestId === rcaRequest.current) setRcaLoading(false);
    }
  };
  const stats = (heatmap?.locations || []).reduce((sum, location) => {
    for (const key of ['total', 'red', 'yellow', 'green']) sum[key] += location.summary[key];
    return sum;
  }, {total: 0, red: 0, yellow: 0, green: 0});
  const divisions = [...new Set(submissions.map(s => s.division))].sort();
  const visibleReports = submissions.filter(s => (!division || s.division === division) && s.report_date === heatmap?.date);

  return <div className="app-shell">
    <Header date={heatmap?.date} stats={stats} dataset={dataset} />
    <main id="main" className="workspace-main space-y-5">
      <section className="page-heading flex flex-wrap justify-between items-center gap-5">
        <div>
          <div className="workspace-path"><span>Workspace</span><span aria-hidden="true">/</span><span>Overview</span></div>
          <h1 className="display-font text-2xl md:text-3xl font-semibold">Performance overview</h1>
          <p className="text-sm text-slate-400 mt-3 max-w-2xl">Your division reports, connected. Track performance and turn feedback into evidence-linked analysis.</p>
        </div>
        <button className="btn-primary" onClick={() => setUpload(true)}>Upload report</button>
      </section>
      {notice && <div role="status" className="notice-success">{notice}</div>}
      {error && <div role="alert" className="notice-error">{error} <button className="underline ml-3" onClick={() => {setLoading(true); setRevision(n => n+1);}}>Retry</button></div>}
      <section className="summary-strip" aria-label="Reporting summary">
        {[
          ['Readings in this view', stats.total, 'text-white'],
          ['Missing target', stats.red, 'text-red-300'],
          ['Meeting target', stats.green, 'text-emerald-300'],
          ['Divisions represented', new Set((heatmap?.locations || []).flatMap(l => l.kpis.map(k => k.division).filter(Boolean))).size, 'text-indigo-300'],
        ].map(([label, value, color]) => <div key={label}><p className="text-xs text-slate-400">{label}</p><p className={'text-2xl font-semibold mt-2 '+color}>{loading ? '…' : value}</p></div>)}
      </section>
      <div className="filter-bar flex flex-wrap items-end gap-3">
        <label className="field-label">Data
          <select className="field-input" value={dataset} onChange={e => {setDate(''); setDivision(''); changeView(setDataset, e.target.value);}}>
            <option value="submitted">Division submissions</option><option value="demo">Synthetic seed history</option>
          </select>
        </label>
        <label className="field-label">Reporting date
          <select className="field-input" value={date} onChange={e => changeView(setDate, e.target.value)}>
            <option value="">Latest available</option>{periods.map(day => <option key={day}>{day}</option>)}
          </select>
        </label>
        {dataset === 'submitted' && <label className="field-label">Division
          <select className="field-input" value={division} onChange={e => {setDate(''); changeView(setDivision, e.target.value);}}>
            <option value="">All divisions</option>{divisions.map(d => <option key={d}>{d}</option>)}
          </select>
        </label>}
        <button className="btn-ghost" onClick={() => {resetSelection(); setLoading(true); setRevision(n => n+1);}}>Refresh</button>
        <p className="text-xs text-slate-500 flex-1 text-right">Colors show target attainment. Z-scores provide separate historical context.</p>
      </div>
      {!loading && !error && !stats.total ? <section className="glass empty-workspace">
        <img className="brand-art" src="/brand/omnikpi.png" width="515" height="460" alt="OMNIkpi: agentic infrastructure and industrial intelligence" />
        <div className="space-y-4">
        <h2 className="display-font text-xl">Bring your reports into focus.</h2>
        <p className="text-sm text-slate-400">Upload a division report to build your shared performance view. Review the column mappings before any readings are added.</p>
        <button className="btn-primary" onClick={() => setUpload(true)}>Upload your first report</button>
        <p className="text-xs text-slate-400">Exploring omniKPI? Start with a synthetic sample.</p>
        <div className="flex flex-wrap gap-3">
          <button className="btn-ghost" onClick={() => setUpload(true)}>Browse seven division workbooks</button>
        </div>
        </div>
      </section> : <div className="flex flex-col xl:flex-row gap-5 items-start">
        <div className="flex-1 min-w-0 w-full">
          <HeatmapMatrix heatmapData={heatmap} selectedCell={selected} onSelectCell={diagnose} loading={loading} />
        </div>
        {selected && <div className="w-full xl:w-[410px] xl:shrink-0">
          <RCAPanel key={selected.fact_id} domainId={domainId} selectedCell={selected} rcaData={rca}
            loading={rcaLoading} error={rcaError} onTriggerRCA={diagnose} onClose={resetSelection}
            onViewHistory={() => setHistory(true)}
            onFeedbackSaved={() => {setRevision(n => n+1); diagnose(selected);}} />
        </div>}
      </div>}
      {dataset === 'submitted' && submissions.length > 0 && <section className="glass p-5">
        <h2 className="display-font font-semibold">Submission ledger</h2>
        <p className="text-xs text-slate-400 mt-1 mb-4">{visibleReports.length} report(s) have a default reporting date matching this view. No expected-division checklist is configured.</p>
        <div className="overflow-auto max-h-64"><table className="report-table"><thead><tr><th>Division</th><th>Source report</th><th>Default report date</th><th>Imported readings</th></tr></thead>
          <tbody>{submissions.map(s => <tr key={s.submission_id}><td>{s.division}</td><td>{s.filename}</td><td>{s.report_date}</td><td>{s.readings}</td></tr>)}</tbody></table></div>
      </section>}
    </main>
    {upload && <HarvesterModal domainId={domainId} onClose={() => setUpload(false)} onImported={result => {
      resetSelection(); setUpload(false); setDataset('submitted'); setDivision(''); setDate(result.dates.at(-1) || '');
      setNotice(result.readings_imported+' readings from '+result.division+' are now in the central dataset.');
      setLoading(true); setRevision(n => n+1);
    }} />}
    {history && selected && <KPIDetailModal domainId={domainId} selectedCell={selected} onClose={() => setHistory(false)}
      onTriggerRCA={cell => {setHistory(false); diagnose(cell);}} />}
  </div>;
}
