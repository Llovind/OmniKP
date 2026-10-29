import { useEffect, useState } from 'react';

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
      <button className="btn-ghost" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
        {theme === 'light' ? 'Dark mode' : 'Light mode'}
      </button>
    </div>
  </header>;
}
