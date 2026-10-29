import { useEffect, useState } from 'react';
import './landing.css';

export default function Landing() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [hasScreenshot, setHasScreenshot] = useState(true);
  useEffect(() => {
    const observer = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('revealed'); observer.unobserve(e.target); }
    }), {threshold:0.08});
    document.querySelectorAll('.landing .reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);
  const startDemo = async () => {
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/demo/seed', {method:'POST'});
      if (!response.ok) throw new Error('The demo could not be prepared. Please try again.');
      window.location.assign('/app?demo=1');
    } catch (err) { setError(err.message); setBusy(false); }
  };
  const cta = <button className="landing-primary" disabled={busy} onClick={startDemo}>{busy ? 'Preparing demo…' : 'Try demo'}</button>;
  return <div className="landing">
    <a className="landing-skip" href="#landing-main">Skip to content</a>
    <header className="landing-nav"><a className="landing-wordmark" href="/" aria-label="omniKPI home">omni<strong>KPI</strong></a><nav aria-label="Product"><a href="#how">How it works</a><a href="#ai">AI</a><a href="#traceability">Traceability</a></nav>{cta}</header>
    {error && <div role="alert" className="landing-error">{error} <button onClick={startDemo} disabled={busy}>Retry demo</button></div>}
    <main id="landing-main">
      <section className="landing-hero">
        <svg className="hero-curves" viewBox="0 0 1440 900" fill="none" aria-hidden="true"><path d="M-180 750C200 130 710 1100 1600 80M-180 800C200 180 710 1150 1600 130M-180 850C200 230 710 1200 1600 180" stroke="currentColor" /></svg>
        <div className="landing-container hero-content"><p className="landing-eyebrow">AI-assisted performance reporting</p><h1>Every division’s report.<br />One traceable KPI view.</h1><p className="hero-description">omniKPI consolidates scattered Excel reports, flags what’s missing target, and helps analysts draft evidence-linked explanations.</p><div className="landing-actions">{cta}<a className="landing-secondary" href="#how">See how it works</a></div><p className="demo-note">Explore the prototype with synthetic data. No upload needed.</p>
        <div className="product-frame"><div className="frame-bar"><span>omniKPI / Performance workspace</span><span>Synthetic demo data</span></div>{hasScreenshot ? <img src="/landing/workspace.png" width="1440" height="960" fetchPriority="high" alt="Populated omniKPI workspace showing synthetic divisional KPI readings" onError={() => setHasScreenshot(false)} /> : <div className="screenshot-placeholder"><strong>Workspace screenshot placeholder</strong><p>The interactive demo contains 90 KPIs, 180 readings and seven submitting units.</p><span>Open the demo to explore the working product.</span></div>}</div></div>
      </section>
      <section className="landing-section landing-container reveal" aria-labelledby="problem-heading"><p className="section-label">The reporting gap</p><h2 id="problem-heading">The data exists.<br />The shared view takes work.</h2><div className="problem-columns">{[['Reports live in different files','Each division reports separately, leaving analysts to connect the pieces.'],['Consolidating takes manual effort','Column meanings, units and targets need to line up before results can be compared.'],['Explanations get lost','The reason behind a missed target can become detached from the reading.']].map(([title,body]) => <article key={title}><h3>{title}</h3><p>{body}</p></article>)}</div></section>
      <section id="how" className="landing-section landing-white"><div className="landing-container reveal"><p className="section-label">How it works</p><h2>From report to reviewed evidence.</h2><ol className="landing-steps">{[['Submit','Choose the submitting unit, reporting date and Excel or CSV file.'],['Review mapping','AI proposes column meanings. The analyst reviews and corrects them.'],['Consolidate','Validated readings enter a shared database with source file, row and unit.'],['Investigate','Attach division feedback to a KPI, location and date, then request an RCA draft.']].map(([title,body],i) => <li key={title}><span className="step-number">0{i+1}</span><h3>{title}</h3><p>{body}</p></li>)}</ol></div></section>
      <section id="ai" className="landing-section landing-container reveal"><p className="section-label">Two AI components</p><h2>Assistance where interpretation matters.</h2><div className="ai-columns"><article><span className="component-index">01 / Understand the report</span><h3>Schema interpretation</h3><p>Reads headers plus up to 3 sample values per column and proposes what each column means: KPI, actual, target, location, unit, direction and feedback.</p></article><article><span className="component-index">02 / Explain the shortfall</span><h3>Evidence-linked RCA</h3><p>Turns feedback attached to a specific KPI, location and date into an attributed explanation with references. Returns “Insufficient evidence” when no feedback exists.</p></article></div><p className="automation-note">Everything else (threshold checks, validation, duplicate rejection, Z-score anomaly baseline) is deterministic automation, not AI.</p></section>
      <section id="traceability" className="landing-section landing-white"><div className="landing-container trace-layout reveal"><div><p className="section-label">Traceability</p><h2>Every number knows where it came from.</h2><p>Follow a reading back to its report and responsible unit. Keep division feedback attached to the exact KPI, location and reporting period.</p><a href="/demo/divisions/validation-pack.zip" download>Download the validation pack</a></div><figure className="trace-card"><figcaption>Synthetic demo reading</figcaption><h3>Compliance Deployment Supervision</h3><div className="trace-value">97.8<span>% actual · 98.5% target</span></div><dl><div><dt>Source file</dt><dd>ed.xlsx</dd></div><div><dt>Source row</dt><dd>5</dd></div><div><dt>Submitting unit</dt><dd>ED</dd></div><div><dt>Location / date</dt><dd>Demo North / 30 June 2026</dd></div></dl></figure></div></section>
      <section className="landing-section landing-container human-block reveal"><p className="section-label">Human in the loop</p><h2>Nothing enters the central dataset without analyst confirmation.</h2><p>Review mappings and validation results before importing your reports. RCA drafts remain attributed explanations for analyst review. The pre-reviewed synthetic fixtures let you explore this flow immediately.</p></section>
      <section className="landing-final"><div className="landing-container"><h2>See it with real structure,<br />synthetic data.</h2><p>Seven reconstructed division reports. One shared performance view.</p>{cta}</div></section>
    </main>
    <footer className="landing-footer landing-container"><img src="/brand/omnikpi.png" width="515" height="460" alt="omniKPI" /><p>Built for ITASE 7.0 by Team Mejeuh Euy<br /><span>AI-assisted performance reporting prototype</span></p><a href="https://github.com/Llovind/OmniKP">View on GitHub</a><a href="/app">Open workspace</a></footer>
  </div>;
}
