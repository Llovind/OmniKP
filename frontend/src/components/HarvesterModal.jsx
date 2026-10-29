import { useEffect, useState } from 'react';
import { api } from '../api/client';

const fields = [
  ['ignore', 'Ignore'], ['kpi_name', 'KPI name'], ['actual_value', 'Actual value'],
  ['target_value', 'Target / limit'], ['location_name', 'Location'], ['date', 'Reporting date'],
  ['unit', 'Unit'], ['higher_is_better', 'Higher / lower is better'],
  ['kpi_archetype', 'KPI category'], ['notes', 'Division feedback'], ['wide_location', 'Actual for one location…'],
];

function PreviewTable({rows}) {
  if (!rows?.length) return null;
  const keys = Object.keys(rows[0]).filter(k => k !== 'notes');
  return <div className="overflow-auto max-h-60"><table className="report-table">
    <thead><tr>{keys.map(k => <th key={k}>{k.replaceAll('_', ' ')}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={i}>{keys.map(k => <td key={k}>{String(row[k] ?? '—')}</td>)}</tr>)}</tbody>
  </table></div>;
}

export default function HarvesterModal({domainId, onClose, onImported}) {
  const [file, setFile] = useState(null);
  const [division, setDivision] = useState('');
  const [demoReports, setDemoReports] = useState([]);
  const [reportDate, setReportDate] = useState(new Date().toLocaleDateString('en-CA'));
  const [sheet, setSheet] = useState('');
  const [headerRow, setHeaderRow] = useState(0);
  const [headerDepth, setHeaderDepth] = useState(1);
  const [useAI, setUseAI] = useState(false);
  const [result, setResult] = useState(null);
  const [mapping, setMapping] = useState({});
  const [defaultDirection, setDefaultDirection] = useState('');
  const [validation, setValidation] = useState(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    fetch('/demo/divisions/manifest.json').then(r => {
      if (!r.ok) throw new Error('Division demo catalogue is unavailable.');
      return r.json();
    }).then(setDemoReports).catch(err => setError(err.message));
  }, []);
  const chooseDemo = async (report) => {
    setBusy('Loading demo file…'); setError('');
    try {
      const response = await fetch('/demo/divisions/'+report.filename);
      if (!response.ok) throw new Error('Unable to load demo workbook.');
      setFile(new File([await response.blob()], report.filename, {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
      setDivision(report.division); setReportDate(report.report_date); setSheet(report.sheet);
      setHeaderRow(report.header_row); setHeaderDepth(report.header_depth);
    } catch (err) { setError(err.message); }
    finally { setBusy(''); }
  };

  const interpret = async (e) => {
    e.preventDefault(); setBusy('Interpreting report…'); setError(''); setResult(null); setValidation(null);
    const form = new FormData();
    form.append('file', file); form.append('division', division); form.append('report_date', reportDate);
    form.append('sheet_name', sheet); form.append('header_row', headerRow);
    form.append('header_depth', headerDepth); form.append('use_ai', useAI);
    try {
      const data = await api.previewReport(domainId, form);
      setResult(data); setSheet(data.sheet_name);
      setMapping(Object.fromEntries(Object.entries(data.column_mapping).map(([col, meta]) => [col, meta.target])));
      // Confirmation is enabled only after the user explicitly validates their mapping.
    } catch (err) { setError(err.message); }
    finally { setBusy(''); }
  };
  const update = (col, target) => {
    setMapping(prev => ({...prev, [col]: target})); setValidation(null); setError('');
  };
  const validate = async () => {
    setBusy('Validating every reading…'); setError('');
    try { setValidation(await api.reviewReport(domainId, result.submission_id, {mapping, default_direction: defaultDirection || null})); }
    catch (err) { setError(err.message); setValidation(null); }
    finally { setBusy(''); }
  };
  const confirm = async () => {
    setBusy('Consolidating readings…'); setError('');
    try { onImported(await api.confirmReport(domainId, result.submission_id, {mapping, default_direction: defaultDirection || null})); }
    catch (err) { setError(err.message); setValidation(null); }
    finally { setBusy(''); }
  };
  return <div className="modal-backdrop">
    <section role="dialog" aria-modal="true" aria-labelledby="intake-title" className="glass modal-content max-w-5xl">
      <header className="p-5 border-b border-white/10 flex justify-between items-start gap-4">
        <div><p className="text-xs text-indigo-300 uppercase tracking-wider">Harvester Agent</p>
          <h2 id="intake-title" className="display-font text-xl font-semibold mt-1">Submit a division report</h2>
          <p className="text-sm text-slate-400 mt-2">Interpret the file, review its meaning, then confirm what enters the shared dataset.</p></div>
        <button className="btn-ghost" disabled={!!busy} onClick={onClose} aria-label="Close upload">✕</button>
      </header>
      <div className="p-5 overflow-auto space-y-5">
        {!result ? <form onSubmit={interpret} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <label className="field-label">Submitting division
              <input className="field-input" list="division-options" value={division} onChange={e => setDivision(e.target.value)} required maxLength={100} />
              <datalist id="division-options">{demoReports.map(r => <option key={r.division} value={r.division} />)}</datalist>
              <span className="text-xs text-slate-500">Source grouping: SUB-UNIT REG BARU. Select a workbook unit or enter another submitting unit.</span>
            </label>
            <label className="field-label">Default reporting date
              <input className="field-input" type="date" value={reportDate} onChange={e => setReportDate(e.target.value)} required />
              <span className="text-xs text-slate-500">Used when the report has no Date column. Choose the period the readings represent.</span>
            </label>
          </div>
          <label className="field-label">Report file (.xlsx or UTF-8 .csv)
            <input className="field-input" type="file" accept=".xlsx,.csv" required={!file} onChange={e => {setFile(e.target.files[0]); setSheet(''); setHeaderRow(0); setHeaderDepth(1);}} />
            {file && <span>Selected: {file.name}</span>}
          </label>
          <details className="glass-sm p-3">
            <summary className="text-sm cursor-pointer">Worksheet and header settings</summary>
            <div className="grid sm:grid-cols-3 gap-3 mt-3">
              <label className="field-label">Worksheet name <input className="field-input" value={sheet} placeholder="First worksheet" onChange={e => setSheet(e.target.value)} /></label>
              <label className="field-label">First header row <input className="field-input" type="number" min="0" max="50" value={headerRow} onChange={e => setHeaderRow(e.target.value)} /><span className="text-xs text-slate-500">0 detects the row automatically</span></label>
              <label className="field-label">Header levels <select className="field-input" value={headerDepth} onChange={e => setHeaderDepth(e.target.value)}><option value="1">1 row</option><option value="2">2 rows</option><option value="3">3 rows</option></select></label>
            </div>
          </details>
          <label className="flex items-start gap-3 text-sm text-slate-300">
            <input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)} className="mt-1" />
            <span>Use the configured AI to interpret headers and sample values.
              <span className="block text-xs text-slate-500 mt-1">Sends column headers and up to three sample values per column to your configured provider. Leave off for local rules and manual mapping.</span></span>
          </label>
          <p className="text-xs text-slate-500">Demo limits: 10 MB, 5,000 rows, 300 columns. Formula cells need values saved by Excel. This reads one worksheet at a time.</p>
          <button className="btn-primary" disabled={!!busy || !file}>{busy || 'Interpret report'}</button>
          <section className="space-y-3">
            <h3 className="font-semibold">Division demo workbooks</h3>
            <div className="flex flex-wrap gap-3"><a className="btn-ghost" href="/demo/divisions/validation-pack.zip" download>Download validation pack</a><a className="btn-ghost" href="/demo/divisions/expected-consolidated.xlsx" download>Expected consolidated results</a><a className="btn-ghost" href="/demo/divisions/VALIDATE.md" download>Validation checklist</a></div>
            <p className="text-sm text-slate-400">Seven reconstructed reports cover all 90 KPIs in the June WISA workbook. Ownership, names, units and directions follow the source. Measurements, targets, locations and feedback are synthetic. Load each report, review it, and confirm to build a 180-reading consolidated view for 30 June 2026.</p>
            <div className="overflow-auto"><table className="report-table"><thead><tr><th>Submitting unit</th><th>KPIs / readings</th><th>Layout</th><th>Workbook</th></tr></thead><tbody>
              {demoReports.map(r => <tr key={r.division}><td>{r.division}</td><td>{r.kpis} / {r.readings}</td><td>{r.layout}</td><td className="flex gap-2"><button type="button" className="btn-ghost" disabled={!!busy} onClick={() => chooseDemo(r)}>Load {r.division}</button><a className="btn-ghost" href={'/demo/divisions/'+r.filename} download>Download</a></td></tr>)}
            </tbody></table></div>
          </section>
        </form> : <>
          <div className="flex flex-wrap justify-between gap-3 items-center">
            <div><p className="font-medium">{result.division} · {result.filename}</p>
              <p className="text-xs text-slate-400 mt-1">{result.rows_parsed} source rows · {result.sheet_name} · header starts at row {result.header_row}</p></div>
            <button className="btn-ghost" disabled={!!busy} onClick={() => {setResult(null); setValidation(null);}}>Change file / settings</button>
          </div>
          <p className="notice-info">{result.message}</p>
          <div>
            <h3 className="font-semibold mb-2">Review column meanings</h3>
            <p className="text-xs text-slate-400 mb-3">For a wide report, choose “Actual for one location” for each measurement column and enter its location. Ignore ACH / achievement columns.</p>
            <div className="overflow-auto max-h-80"><table className="report-table"><thead><tr><th>Source column</th><th>Meaning</th><th>Suggestion source</th></tr></thead>
              <tbody>{result.columns.map(col => <tr key={col}><td className="max-w-xs break-words">{col}</td><td>
                <select className="field-input" value={mapping[col]?.startsWith('location:') ? 'wide_location' : mapping[col]} onChange={e => update(col, e.target.value === 'wide_location' ? 'location:'+col.split('|')[0].trim() : e.target.value)}>
                  {fields.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                {mapping[col]?.startsWith('location:') && <input aria-label={'Location for '+col} className="field-input mt-2" value={mapping[col].slice(9)} onChange={e => update(col, 'location:'+e.target.value)} />}
              </td><td className="text-xs text-slate-400">{result.column_mapping[col]?.method === 'llm' ? 'AI suggestion' : result.column_mapping[col]?.method === 'approved_memory' ? 'Approved mapping' : 'Local rules'}</td></tr>)}</tbody>
            </table></div>
          </div>
          <details className="glass-sm p-3"><summary className="text-sm cursor-pointer">Original values (first five rows)</summary><PreviewTable rows={result.raw_preview} /></details>
          <label className="field-label max-w-md">Direction for new KPIs without a Direction column
            <select className="field-input" value={defaultDirection} onChange={e => {setDefaultDirection(e.target.value); setValidation(null);}}>
              <option value="">Require an explicit direction</option><option value="higher">Higher is better</option><option value="lower">Lower is better</option>
            </select>
          </label>
          <p className="text-xs text-slate-400">New KPI names are registered with the reviewed unit and direction. Include a Category column to choose their group; otherwise they are grouped under Performance. Targets are saved per reading, including location-specific targets in row-format reports.</p>
          <button className="btn-primary" disabled={!!busy} onClick={validate}>{busy || 'Validate reviewed mapping'}</button>
          {validation && <div className="space-y-3">
            <div role="status" className={validation.can_confirm ? 'notice-success' : 'notice-error'}>
              {validation.valid_readings} valid readings · {validation.invalid_readings} invalid · {validation.conflict_count} existing-reading conflicts.
              {!validation.can_confirm && ' Nothing will be imported until all issues are resolved.'}
            </div>
            {[...(validation.issues || []), ...(validation.conflicts || [])].length > 0 && <ul className="text-xs text-red-200 space-y-2 max-h-40 overflow-auto">
              {[...(validation.issues || []), ...(validation.conflicts || [])].map((issue, i) => <li key={i}>Row {issue.row || '—'}{issue.column ? ' / '+issue.column : ''}: {issue.message}</li>)}
            </ul>}
            <h3 className="font-semibold">Normalized readings (first ten)</h3><PreviewTable rows={validation.preview} />
            <button className="btn-primary" disabled={!validation.can_confirm || !!busy} onClick={confirm}>{busy || 'Confirm and consolidate '+validation.valid_readings+' readings'}</button>
            <p className="text-xs text-slate-500">Confirmation also saves this division’s column mapping for matching future layouts. Existing readings are never silently replaced.</p>
          </div>}
        </>}
        {error && <div role="alert" className="notice-error">{error}</div>}
      </div>
    </section>
  </div>;
}
