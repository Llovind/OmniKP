import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from './api/client';

const pct = (value) => value == null ? '—' : `${(value * 100).toFixed(1)}%`;

const modeText = {
  live: 'Live provider call configured',
  unavailable: 'Live AI unavailable; configure the provider to process reports',
};

export default function Evaluation() {
  const [status, setStatus] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api.getAIStatus(), api.getMappingEvaluation()])
      .then(([aiStatus, mapping]) => { setStatus(aiStatus); setEvaluation(mapping); })
      .catch(err => setError(err.message));
  }, []);

  return <div className="app-shell">
    <header className="border-b border-white/10 px-5 py-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="text-xs text-indigo-300 uppercase tracking-wider">Evidence</p>
        <h1 className="display-font text-2xl font-semibold">Mapping evaluation</h1>
      </div>
      <div className="flex gap-2">
        <Link className="btn-ghost text-xs" to="/">Landing</Link>
        <Link className="btn-primary text-xs" to="/app">Open workspace</Link>
      </div>
    </header>
    <main className="workspace-main space-y-5">
      {error && <div role="alert" className="notice-error">{error}</div>}
      {status && <section className="glass p-5 space-y-2">
        <h2 className="display-font font-semibold">Configured behaviour</h2>
        <p className="text-sm text-slate-300">
          <strong>{modeText[status.mode] || status.mode}</strong>
          {status.model ? ` · ${status.model}` : ''}
        </p>
        <p className="text-xs text-slate-400">
          Input is limited to column headers plus up to {status.samples_per_column} sample values per column.
          {status.recorded_suggestions ? ` ${status.recorded_suggestions} historical header signature(s) are archived as evaluation evidence.` : ''}
        </p>
        {status.recorded_provenance && <p className="text-xs text-slate-500">
          Recorded with {status.recorded_provenance.model} on {status.recorded_provenance.recorded_at}.
          These archived suggestions are not used to replace live interpretation.
        </p>}
      </section>}

      {evaluation && <section className="glass p-5">
        <h2 className="display-font font-semibold">Synthetic mapping benchmark</h2>
        <p className="text-xs text-slate-400 mt-1 mb-4">{evaluation.dataset}</p>
        <div className="overflow-auto">
          <table className="report-table">
            <thead><tr>
              <th>Layout</th><th>Local rules</th><th>AI proposal accuracy</th><th>AI columns</th>
              <th>Rules preview</th><th>AI preview</th>
            </tr></thead>
            <tbody>{evaluation.cases.map(item => <tr key={item.case}>
              <td>{item.case.replaceAll('_', ' ')}</td>
              <td>{pct(item.rules?.accuracy)}</td>
              <td>{pct(item.ai?.accuracy)}</td>
              <td>{item.ai ? Math.round(item.ai.llm_columns) : '—'}</td>
              <td>{item.rules ? item.rules.preview_seconds + ' s' : '—'}</td>
              <td>{item.ai ? item.ai.preview_seconds + ' s' : '—'}</td>
            </tr>)}</tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Model: {evaluation.ai_model || 'not recorded'} · {evaluation.ai_repeats || 1} repeat(s) per layout · rules are the baseline.
        </p>
        <div className="glass-sm p-3 mt-4">
          <h3 className="text-xs uppercase text-indigo-300 mb-2">What this does not show</h3>
          <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4">
            {evaluation.limitations.map(limit => <li key={limit}>{limit}</li>)}
          </ul>
        </div>
      </section>}

      {!status && !error && <p role="status" className="notice-info">Loading evaluation evidence…</p>}
    </main>
  </div>;
}
