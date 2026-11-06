import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';

// Optional decoration: a failed chunk must not prevent the landing page rendering.
const ColorBends = lazy(() => import('./ColorBends').catch(() => ({ default: () => null })));
const colors = ['#0864c9', '#3888d8', '#75b6ff'];

export default function HeroColorBends() {
  const ref = useRef(null);
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [visible, setVisible] = useState(false);
  const [tabVisible, setTabVisible] = useState(() => !document.hidden);
  const [failed, setFailed] = useState(false);
  const unavailable = useCallback(() => setFailed(true), []);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(preference.matches);
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));
    observer.observe(ref.current);
    const onVisibility = () => setTabVisible(!document.hidden);
    document.addEventListener('visibilitychange', onVisibility);
    return () => { observer.disconnect(); document.removeEventListener('visibilitychange', onVisibility); };
  }, []);
  const active = visible && tabVisible && !reduced && !failed;
  return <>
    <div ref={ref} className="hero-color-background" aria-hidden="true" data-active={active} data-unavailable={failed}>
      {active && <Suspense fallback={null}><ColorBends colors={colors} rotation={90} speed={0.08}
        scale={1} frequency={1} warpStrength={1} mouseInfluence={1} noise={0.025}
        parallax={0.5} iterations={1} intensity={0.65} bandWidth={6} transparent onUnavailable={unavailable} /></Suspense>}
    </div>

  </>;
}
