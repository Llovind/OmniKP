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
  { label: 'How it works', description: 'From report to reviewed evidence.', links: [{ label: 'How it works', href: '#how' }] },
  { label: 'AI', description: 'Assistance where interpretation matters.', links: [{ label: 'AI', href: '#ai' }] },
  { label: 'Traceability', description: 'Every number knows where it came from.', links: [{ label: 'Traceability', href: '#traceability' }] },
];
const glowColors = ['#0864c9', '#75b6ff', '#3888d8'];
const DEMO_PREPARATION_TIMEOUT = 30_000;

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
      if (!response.ok) throw new Error('The demo could not be prepared. Please try again.');
      window.location.assign('/app?demo=1');
    } catch {
      if (demoRequest.current !== controller) return;
      setError(timedOut
        ? 'Demo preparation is taking longer than expected. It may still finish. Open the workspace to check, or retry.'
        : 'The demo could not be prepared. Check your connection and try again.');
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
      <CardNav className="omnikp-card-nav" logo={<span className="landing-wordmark">omni<strong>KPI</strong></span>}
        logoHref="/" logoAlt="omniKPI home" items={navigationItems}
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
        <div className="landing-container hero-content"><p className="landing-eyebrow">AI-assisted performance reporting</p><CinematicText as="h1">{'Every division’s report.\nOne traceable KPI view.'}</CinematicText><CinematicText as="p" className="hero-description" delay={0.4} stagger={0.025} blur={8}>omniKPI consolidates scattered Excel reports, flags what’s missing target, and helps analysts draft evidence-linked explanations.</CinematicText><div className="landing-actions"><LiquidButton className="landing-primary hero-liquid-primary" size="xxl" disabled={busy} aria-busy={busy} onClick={startDemo}>{busy ? 'Preparing demo…' : 'Try demo'}</LiquidButton><LiquidButton className="landing-secondary hero-liquid-secondary" size="xxl" asChild><a href="#how">See how it works</a></LiquidButton></div><p className="demo-note">Explore the prototype with synthetic data. No upload needed.</p>
        <div className="product-frame"><div className="frame-bar"><span>omniKPI / Performance workspace</span><span>Synthetic demo data</span></div>{hasScreenshot ? <img src="/landing/workspace.png" width="1440" height="960" fetchPriority="high" alt="Populated omniKPI workspace showing synthetic divisional KPI readings" onError={() => setHasScreenshot(false)} /> : <div className="screenshot-placeholder"><strong>Workspace screenshot placeholder</strong><p>The interactive demo contains 90 KPIs, 180 readings and seven submitting units.</p><span>Open the demo to explore the working product.</span></div>}</div></div>
      </section>
      <ProblemSection />
      <section id="how" className="landing-section landing-white" aria-labelledby="how-heading"><div className="landing-container reveal"><h2 id="how-heading">From report to reviewed evidence.</h2><WorkflowSteps /></div></section>
      <section id="ai" className="landing-section landing-container reveal" aria-labelledby="ai-heading">
        <h2 id="ai-heading">Assistance where interpretation matters.</h2>
        <div className="ai-columns">
          <BorderGlow className="ai-glow" colors={glowColors} glowColor="212 80 70" backgroundColor="var(--surface)" borderRadius={16} glowRadius={12} glowIntensity={0.65} fillOpacity={0.08} animated={false}>
            <article><h3>Schema interpretation</h3><span className="component-index">Understand the report</span><p>Reads headers plus up to 3 sample values per column and proposes what each column means: KPI, actual, target, location, unit, direction and feedback.</p></article>
          </BorderGlow>
          <BorderGlow className="ai-glow" colors={glowColors} glowColor="212 80 70" backgroundColor="var(--surface)" borderRadius={16} glowRadius={12} glowIntensity={0.65} fillOpacity={0.08} animated={false}>
            <article><h3>Evidence-linked RCA</h3><span className="component-index">Explain the shortfall</span><p>Turns feedback attached to a specific KPI, location and date into an attributed explanation with references. Returns “Insufficient evidence” when no feedback exists.</p></article>
          </BorderGlow>
        </div>
        <p className="automation-note">Everything else (threshold checks, validation, duplicate rejection, Z-score anomaly baseline) is deterministic automation, not AI.</p>
      </section>
      <TraceabilitySection />
      <section className="landing-section landing-container human-block reveal" aria-labelledby="human-heading"><h2 id="human-heading">Nothing enters the central dataset without analyst confirmation.</h2><p>Review mappings and validation results before importing your reports. Root-cause analysis drafts remain attributed explanations for analyst review. Explore the workflow with pre-reviewed synthetic reports.</p></section>
      <section className="landing-final" aria-labelledby="demo-heading"><div className="landing-container"><h2 id="demo-heading">See it with real structure,<br />synthetic data.</h2><p>Seven reconstructed division reports. One shared performance view.</p>{cta}<p className="final-reassurance">No upload needed.</p></div></section>
    </main>
    <footer className="landing-footer landing-container"><img src="/brand/omnikpi.png" width="515" height="460" alt="omniKPI" /><p>Built for ITASE 7.0 by Team Mejeuh Euy<br /><span>AI-assisted performance reporting prototype</span></p><a href="https://github.com/Llovind/OmniKP">View on GitHub</a><a href="/app">Open workspace</a></footer>
  </div>;
}
