import { useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { ThemeSwitch } from './ThemeSwitch';

export default function Header({ date, dataset }) {
  const demo = new URLSearchParams(window.location.search).get('demo') === '1';
  const [resetting, setResetting] = useState(false);
  const [resetError, setResetError] = useState('');
  const resetDemo = async () => {
    setResetting(true); setResetError('');
    try {
      const response = await fetch('/api/demo/seed?reset=true', {method:'POST'});
      if (!response.ok) throw new Error('Reset failed. Please retry.');
      window.location.assign('/app?demo=1');
    } catch (err) { setResetError(err.message); setResetting(false); }
  };
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('omnikpi-theme') || 'light'; } catch { return 'light'; } });
  const themeTransition = useRef(null);
  useEffect(() => () => themeTransition.current?.skipTransition(), []);
  const changeTheme = next => {
    const root = document.documentElement;
    // Persist intent immediately: a link can navigate before the snapshot callback runs.
    try { localStorage.setItem('omnikpi-theme', next); } catch { /* Storage is optional. */ }
    const apply = () => { flushSync(() => setTheme(next)); root.dataset.theme = next; };
    themeTransition.current?.skipTransition();
    if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      apply(); return;
    }
    root.dataset.themeTransition = 'right';
    const transition = document.startViewTransition(apply);
    themeTransition.current = transition;
    transition.ready.then(() => {
      root.animate([{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }],
        { duration: 280, easing: 'cubic-bezier(.16,1,.3,1)', pseudoElement: '::view-transition-new(root)', fill: 'both' });
    }).catch(() => { /* Unsupported or interrupted snapshots still apply the preference. */ });
    transition.finished.finally(() => {
      if (themeTransition.current === transition) { themeTransition.current = null; delete root.dataset.themeTransition; }
    }).catch(() => {});
  };
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('omnikpi-theme', theme); } catch { /* Private browsing can disable storage. */ }
  }, [theme]);
  return <header className="workspace-header">
    <a className="wordmark" href="#main">omni<strong>KPI</strong></a>
    <span className="workspace-label">Performance workspace</span>
    <div className="header-actions" style={demo ? {flexWrap:'wrap', maxWidth:'100%'} : undefined}>
      <a href="/" style={{color:'inherit'}}>Home</a>
      {demo && <><span>Synthetic demo data</span><button className="btn-ghost" onClick={resetDemo} disabled={resetting}>{resetting ? 'Resetting…' : 'Reset demo'}</button></>}
      {resetError && <span role="alert">{resetError}</span>}
      {dataset === 'demo' && <span>Synthetic sample data</span>}
      {date && <time>{date}</time>}
      <ThemeSwitch theme={theme} iconOnly onThemeChange={changeTheme} />
    </div>
  </header>;
}
