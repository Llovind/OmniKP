// src/components/Header.jsx
export default function Header({ domain, onDomainChange, date, stats }) {
  const isDigitalInfra = domain === 1;
  const isSustainableInd = domain === 2;

  return (
    <header
      className="flex-shrink-0 px-6 py-3 flex items-center justify-between gap-6 border-b border-white/5"
      style={{ background: 'rgba(6,11,24,0.9)', backdropFilter: 'blur(16px)' }}
    >
      {/* Brand & SDG 9 Tagline */}
      <div className="flex items-center gap-3 min-w-max">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg"
          style={{
            background: 'linear-gradient(135deg,#f97316,#6366f1)',
            boxShadow: '0 0 20px rgba(99,102,241,0.4)',
          }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="display-font text-base font-bold text-white leading-none tracking-tight">
              OmniKPI
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-orange-500/20 border border-orange-500/40 text-orange-300 font-bold uppercase tracking-wider">
              UN SDG 9
            </span>
          </div>
          <div className="text-[11px] text-slate-400 leading-none mt-1">
            Industry, Innovation &amp; Infrastructure Intelligence
          </div>
        </div>
      </div>

      {/* SDG 9 Domain Switcher */}
      <div className="flex items-center gap-2 glass-sm p-1.5 border border-white/10 rounded-xl">
        <button
          id="btn-domain-telco"
          onClick={() => onDomainChange(1)}
          className={`domain-btn domain-btn-telco flex items-center gap-2 text-xs py-1.5 px-3.5 ${
            isDigitalInfra ? 'active font-bold' : 'domain-btn-inactive'
          }`}
          title="SDG 9.c & 9.1: Universal Digital Connectivity & Resilient Communications Backbone"
        >
          <span className="text-sm">🌐</span>
          <span>Digital Infrastructure</span>
          <span className="text-[10px] opacity-75 font-mono">(SDG 9.c)</span>
        </button>

        <button
          id="btn-domain-petro"
          onClick={() => onDomainChange(2)}
          className={`domain-btn domain-btn-petro flex items-center gap-2 text-xs py-1.5 px-3.5 ${
            isSustainableInd ? 'active font-bold' : 'domain-btn-inactive'
          }`}
          title="SDG 9.4: Sustainable Industrial Processes, Asset Reliability & Resource Efficiency"
        >
          <span className="text-sm">⚙️</span>
          <span>Sustainable Industry</span>
          <span className="text-[10px] opacity-75 font-mono">(SDG 9.4)</span>
        </button>
      </div>

      {/* Stats Pills & Live Indicator */}
      <div className="flex items-center gap-4">
        {stats && (
          <div className="hidden md:flex items-center gap-2">
            <Pill color="slate" label="KPIs" value={stats.total} />
            {stats.red > 0 && <Pill color="red" label="ANOMALY" value={stats.red} glow />}
            {stats.yellow > 0 && <Pill color="yellow" label="WARNING" value={stats.yellow} />}
            <Pill color="green" label="NORMAL" value={stats.green} />
          </div>
        )}

        <div className="flex items-center gap-3 text-xs">
          {date && (
            <span className="glass-sm px-2.5 py-1 text-slate-300 font-mono text-[11px] border border-white/10">
              <span className="text-slate-500 mr-1">Period:</span>
              <span className="text-indigo-300 font-medium">{date}</span>
            </span>
          )}
          <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
            <span className="dot dot-green" />
            <span className="text-[11px]">Live</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function Pill({ color, label, value, glow }) {
  const colors = {
    red: 'bg-red-500/15 border-red-500/30 text-red-300',
    yellow: 'bg-yellow-500/15 border-yellow-500/25 text-yellow-300',
    green: 'bg-emerald-500/12 border-emerald-500/25 text-emerald-300',
    slate: 'bg-white/5 border-white/10 text-slate-400',
  };
  return (
    <span
      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${colors[color]}`}
      style={glow ? { boxShadow: '0 0 10px rgba(239,68,68,0.25)' } : {}}
    >
      {value} <span className="opacity-60 font-normal text-[10px]">{label}</span>
    </span>
  );
}
