import { useEffect, useRef, useState } from 'react';
import './landing.css';
import { CinematicText } from './components/CinematicText';
import HeroColorBends from './components/HeroColorBends';
import BorderGlow from './components/BorderGlow';
import CardNav from './components/CardNav';
import { LiquidButton } from '@/components/ui/liquid-glass-button';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import WorkflowSteps from './components/WorkflowSteps';
import TraceabilitySection from './components/TraceabilitySection';
import ProblemSection from './components/ProblemSection';

const navigationItems = [
  { label: 'UiPath workflow', description: 'Follow a division report from intake through analyst approval.', links: [{ label: 'How it works', href: '#how' }] },
  { label: 'Reporting controls', description: 'See where analysts review data and its sources.', links: [{ label: 'AI and review', href: '#ai' }, { label: 'Traceability', href: '#traceability' }] },
  { label: 'Technology', description: 'Explore the web workspace and UiPath reporting workflow.', links: [{ label: 'Tech stack', href: '#tech-stack' }] },
];
const techStack = [
  ['Workspace', 'React · Recharts', 'Compare actuals with targets by division and location, and inspect KPI history.'],
  ['Reporting API', 'Python · FastAPI', 'Process Excel and CSV files, validate mappings, and block duplicate readings.'],
  ['Data', 'SQLite · SQLAlchemy', 'Store confirmed readings alongside their source rows and division feedback.'],
  ['AI', 'OpenRouter', 'Suggest column mappings and draft explanations that cite feedback for the selected KPI reading.'],
  ['Workflow automation', 'UiPath', 'Run report intake, pass approved mappings to the backend for import, retrieve the draft and its evidence, and generate the approved report.'],
];
const glowColors = ['#0864c9', '#75b6ff', '#3888d8'];
const DEMO_PREPARATION_TIMEOUT = 180_000;

export default function Landing() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [hasScreenshot, setHasScreenshot] = useState(true);
  const demoRequest = useRef(null);
  useEffect(() => () => { demoRequest.current?.abort(); demoRequest.current = null; }, []);
  const startDemo = async () => {
    if (demoRequest.current) return;
    const controller = new AbortController();
    demoRequest.current = controller;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, DEMO_PREPARATION_TIMEOUT);
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/demo/seed', {method:'POST', signal: controller.signal});
      if (demoRequest.current !== controller) return;
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || 'AI could not prepare the reports. Please retry.');
      }
      window.location.assign('/app?demo=1');
    } catch (err) {
      if (demoRequest.current !== controller) return;
      setError(timedOut
        ? 'Demo preparation is taking longer than expected. It may still finish. Open the workspace to check, or retry.'
        : err.message || 'The demo could not be prepared. Check your connection and try again.');
      setBusy(false);
    } finally {
      clearTimeout(timeout);
      if (demoRequest.current === controller) demoRequest.current = null;
    }
  };
  const cta = <Button className="landing-primary demo-expand" variant="expandIcon" size="lg" Icon={ArrowRight} iconPlacement="right" disabled={busy} aria-busy={busy} onClick={startDemo}>{busy ? 'Preparing demo…' : 'Try demo'}</Button>;
  return <div className="landing">
    <a className="landing-skip" href="#landing-main">Skip to content</a>
    <header className="landing-card-nav">
      <CardNav className="vantagenet-card-nav" logo={<span className="landing-wordmark">Vantage<strong>Net</strong></span>}
        logoHref="/" logoAlt="VantageNet home" items={navigationItems}
        cta={{ label: busy ? 'Preparing demo…' : 'Try demo', onClick: startDemo, disabled: busy }}
        ariaLabel="Product" theme="dark" surface="solid" accentColor="#0864c9" maxWidth={1040}
        intro={false} cardEffect="fade" stagger={0.04} bounce={0} cardHeight={160} />
    </header>
    <span className="sr-only" role="status">{busy ? 'Preparing the synthetic demo.' : ''}</span>
    {error && <div role="alert" className="landing-error"><p>{error}</p><div className="landing-error-actions"><a href="/app?demo=1">Open workspace</a><button onClick={startDemo} disabled={busy}>Retry demo</button></div></div>}
    <main id="landing-main">
      <section className="landing-hero">
        <HeroColorBends />
        <svg className="hero-curves" viewBox="0 0 1440 900" fill="none" aria-hidden="true"><path d="M-180 750C200 130 710 1100 1600 80M-180 800C200 180 710 1150 1600 130M-180 850C200 230 710 1200 1600 180" stroke="currentColor" /></svg>
        <div className="landing-container hero-content">
          <p className="landing-eyebrow">Telecom performance reporting</p>
          <CinematicText as="h1">{'Turn divisional reports into\none view of network performance'}</CinematicText>
          <CinematicText as="p" className="hero-description" delay={0.4} stagger={0.025} blur={8}>VantageNet helps telecom teams consolidate divisional reports and trace missed KPI targets to their source. UiPath runs the reporting stages, from file intake to the final report. Analysts approve both the mapping and the narrative.</CinematicText>
          <div className="landing-actions">
            <LiquidButton className="landing-primary hero-liquid-primary" size="xxl" disabled={busy} aria-busy={busy} onClick={startDemo}>{busy ? 'Preparing demo…' : 'Try demo'}</LiquidButton>
            <LiquidButton className="landing-secondary hero-liquid-secondary" size="xxl" asChild><a href="#how">See the UiPath workflow</a></LiquidButton>
          </div>
          <p className="demo-note">The web demo includes seven synthetic division reports. No upload needed.</p>
          <div className="product-frame">
            <div className="frame-bar"><span>VantageNet / Performance workspace</span><span>Synthetic demo data</span></div>
            {hasScreenshot ? <img src="/landing/workspace.png" width="1440" height="960" fetchPriority="high" alt="VantageNet workspace showing KPI target status and filters for synthetic division reports" onError={() => setHasScreenshot(false)} /> : <div className="screenshot-placeholder"><p>The workspace preview is unavailable. Open the demo to explore the KPI view and source reports.</p></div>}
          </div>
        </div>
      </section>
      <ProblemSection />
      <section id="how" className="landing-section landing-white" aria-labelledby="how-heading">
        <div className="landing-container reveal">
          <h2 id="how-heading">How UiPath runs the reporting workflow</h2>
          <p>In the prototype, the operator runs these as separate attended steps.</p>
          <WorkflowSteps />
        </div>
      </section>
      <section id="ai" className="landing-section landing-container reveal" aria-labelledby="ai-heading">
        <h2 id="ai-heading">AI suggests. Analysts review.</h2>
        <div className="ai-columns">
          <BorderGlow className="ai-glow" colors={glowColors} glowColor="212 80 70" backgroundColor="var(--surface)" borderRadius={16} glowRadius={12} glowIntensity={0.65} fillOpacity={0.08} animated={false}>
            <article><h3>Map report columns</h3><p>AI uses headers and up to three sample values per column to suggest which fields contain the KPI, actual, target, location, unit and feedback. Analysts can correct the mapping before import.</p></article>
          </BorderGlow>
          <BorderGlow className="ai-glow" colors={glowColors} glowColor="212 80 70" backgroundColor="var(--surface)" borderRadius={16} glowRadius={12} glowIntensity={0.65} fillOpacity={0.08} animated={false}>
            <article><h3>Draft an explanation</h3><p>AI uses division feedback for a specific KPI, location and date to draft a root-cause analysis with citations. If feedback is missing, the reading waits for evidence.</p></article>
          </BorderGlow>
        </div>
        <p className="automation-note">The backend applies fixed rules for validation, duplicate detection, target status and historical Z-scores.</p>
      </section>
      <TraceabilitySection />
      <section className="landing-section landing-container human-block reveal" aria-labelledby="human-heading">
        <h2 id="human-heading">Analysts can stop an import or a report</h2>
        <p>Rejecting the mapping stops the import. Rejecting the narrative stops report generation for that revision. The analyst can correct the mapping or edit the draft before approving it.</p>
      </section>
      <section id="tech-stack" className="landing-section landing-white" aria-labelledby="tech-stack-heading">
        <div className="landing-container stack-layout">
          <div>
            <h2 id="tech-stack-heading">VantageNet’s tech stack</h2>
            <p>UiPath runs the reporting stages, the backend validates and stores the readings, and the web workspace lets analysts compare results and trace their sources.</p>
            <a className="stack-source" href="https://github.com/Llovind/OmniKP/tree/6b3769e/deliverables/Gate-3D.1-VantageNet">View the UiPath workflow and sample report</a>
            <p>The sample shows one synthetic ED reading, from confirmed data through narrative approval to PowerPoint.</p>
          </div>
          <dl className="stack-list">
            {techStack.map(([layer, tools, role]) => <div key={layer} className="stack-row">
              <dt>{layer}</dt><dd><strong>{tools}</strong><p>{role}</p></dd>
            </div>)}
          </dl>
        </div>
      </section>
      <section className="landing-final" aria-labelledby="demo-heading"><div className="landing-container"><h2 id="demo-heading">Explore the reporting workspace</h2><p>Compare KPI targets across divisions, then follow a missed target back to its source.</p>{cta}<p className="final-reassurance">Synthetic data. No upload needed.</p></div></section>
    </main>
    <footer className="landing-footer landing-container">
      <p><strong className="footer-wordmark">Vantage<span>Net</span></strong><br /><span>Telecom performance reporting by Team Mejeuh Euy</span></p>
      <a href="https://github.com/Llovind/OmniKP">View on GitHub</a><a href="/evaluation">Mapping evaluation</a><a href="/app">Open workspace</a>
    </footer>
  </div>;
}
