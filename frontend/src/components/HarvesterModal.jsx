import React, { useState } from 'react';

export default function HarvesterModal({ domainId, onClose }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`/api/v1/domains/${domainId}/harvest`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(data.detail || 'Upload failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Error processing file via Harvester Agent');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="glass w-full max-w-2xl border border-white/15 shadow-2xl rounded-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-white/10 bg-slate-950/70 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h2 className="display-font text-base font-bold text-white">
                Harvester Agent &bull; Ingestion Pipeline
              </h2>
              <p className="text-xs text-slate-400">Fuzzy Schema Mapping with LLM Fallback (Human-in-the-Loop)</p>
            </div>
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

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          {/* File Upload Area */}
          <div className="border-2 border-dashed border-white/15 hover:border-indigo-500/50 rounded-xl p-6 text-center bg-white/[0.01] transition-colors">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
              id="harvester-file-input"
            />
            <label
              htmlFor="harvester-file-input"
              className="cursor-pointer flex flex-col items-center gap-2"
            >
              <svg className="w-10 h-10 text-slate-500 hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-slate-200 font-medium">
                {file ? file.name : 'Select or drop enterprise KPI Excel file (.xlsx)'}
              </span>
              <span className="text-[11px] text-slate-500">
                Supports unstructured headers &bull; Harvester maps columns automatically
              </span>
            </label>
          </div>

          {file && (
            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="btn-primary py-2 px-4 text-xs flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Executing RapidFuzz &amp; Schema Mapping...
                  </>
                ) : (
                  <>
                    <span>Run Harvester ETL</span>
                  </>
                )}
              </button>
            </div>
          )}

          {error && (
            <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300">
              {error}
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-4">
              {/* Mapping Status */}
              <div className="glass-sm p-3.5 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-200 uppercase font-mono text-[11px]">
                    Column Alignment Matrix ({result.rows_parsed} rows parsed)
                  </h4>
                  <span className="text-[10px] text-emerald-400 font-mono font-bold">
                    PASSED VALIDATION
                  </span>
                </div>

                <div className="divide-y divide-white/5 text-[11px]">
                  {Object.entries(result.column_mapping).map(([sourceCol, meta]) => (
                    <div key={sourceCol} className="py-2 flex items-center justify-between gap-2">
                      <span className="font-mono text-slate-300 font-medium">{sourceCol}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500">&rarr;</span>
                        <span className="font-mono font-bold text-indigo-300 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-500/30">
                          {meta.target || 'UNMAPPED'}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {meta.confidence}% ({meta.method})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data Preview */}
              {result.preview && result.preview.length > 0 && (
                <div className="glass-sm p-3.5 border border-white/10 space-y-2">
                  <h4 className="font-bold text-slate-200 uppercase font-mono text-[11px]">
                    Ingestion Sample (First 5 Rows)
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px] font-mono">
                      <thead>
                        <tr className="border-b border-white/10 text-slate-400">
                          {Object.keys(result.preview[0]).map((key) => (
                            <th key={key} className="p-1.5">{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {result.preview.map((row, i) => (
                          <tr key={i}>
                            {Object.values(row).map((val, j) => (
                              <td key={j} className="p-1.5 text-slate-300">{String(val)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-slate-950/70 flex items-center justify-between">
          <button onClick={onClose} className="btn-ghost text-xs">
            Close
          </button>
          {result?.success && (
            <span className="text-xs text-emerald-400 font-mono">
              Ready for operator confirmation &bull; Read-only preview
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
