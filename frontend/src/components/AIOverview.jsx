import { useEffect, useState } from 'react';

export default function AIOverview() {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/v1/ai/status', {signal: controller.signal}).then(response => {
      if (!response.ok) throw new Error('AI status unavailable');
      return response.json();
    }).then(setStatus).catch(() => { if (!controller.signal.aborted) setStatus({unknown:true}); });
    return () => controller.abort();
  }, []);
  return <section className="glass p-5 space-y-4" aria-labelledby="ai-workflow-title">
    <div><h2 id="ai-workflow-title" className="font-semibold">AI performance reporting</h2>
      <p className="text-sm mt-2">Upload a report for AI column interpretation, confirm the reviewed readings, then investigate shortfalls with AI drafts grounded in division feedback.</p>
      <p role="status" className="text-xs text-slate-400 mt-2">{!status ? 'Checking AI configuration…' : status.configured ? `AI provider · ${status.model}` : status.unknown ? 'AI configuration could not be checked.' : 'AI unavailable. Configure the provider to process reports.'}</p>
    </div>
  </section>;
}
