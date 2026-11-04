import { useRef, useSyncExternalStore } from 'react';
import { motion, useInView } from 'motion/react';
import { Download, FileSpreadsheet, ArrowDownRight } from 'lucide-react';
import './TraceabilitySection.css';

const preference = '(prefers-reduced-motion: reduce)';
function subscribe(callback: () => void) {
  const media = window.matchMedia(preference);
  media.addEventListener('change', callback);
  return () => media.removeEventListener('change', callback);
}
const sources = [
  ['Source file', 'ed.xlsx'],
  ['Source row', '5'],
  ['Submitting unit', 'ED'],
  ['Location / date', 'Demo North / 30 June 2026'],
];

export default function TraceabilitySection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, amount: .15 });
  const reduced = useSyncExternalStore(subscribe, () => window.matchMedia(preference).matches, () => true);
  const revealed = inView || reduced;
  const entrance = (delay: number, distance = 6) => ({
    initial: false as const,
    animate: { y: revealed ? 0 : distance, opacity: revealed ? 1 : .8 },
    transition: { duration: reduced ? 0 : .32, delay: reduced ? 0 : delay, ease: [.16, 1, .3, 1] as const },
    'data-trace-motion': '',
  });

  return <section ref={ref} id="traceability" className="landing-section landing-white" aria-labelledby="trace-heading" data-revealed={revealed}>
    <div className="landing-container trace-layout">
      <div className="trace-copy">
        <motion.h2 id="trace-heading" {...entrance(0)}>Every number knows <span>where it came from.</span></motion.h2>
        <motion.p {...entrance(.06)}>Follow each reading to its report and responsible unit. Keep division feedback linked to the KPI, location and reporting date.</motion.p>
        <motion.a {...entrance(.12)} className="validation-download" href="/demo/divisions/validation-pack.zip" download>
          <Download size={20} strokeWidth={1.75} aria-hidden="true" />
          <span className="trace-download-copy"><span>Download the validation pack</span><small>ZIP · 64 KiB</small></span>
        </motion.a>
      </div>
      <motion.figure className="trace-card" {...entrance(.1, 8)}>
        <figcaption><FileSpreadsheet size={18} strokeWidth={1.75} aria-hidden="true" />Synthetic demo reading</figcaption>
        <h3>Compliance Deployment Supervision</h3>
        <div className="trace-metric">
          <div className="trace-value">97.8<span className="trace-unit">%</span><span className="trace-target">actual · 98.5% target</span></div>
          <p className="trace-delta"><ArrowDownRight size={16} strokeWidth={2} aria-hidden="true" />0.7 percentage points below target</p>
        </div>
        <dl>{sources.map(([label, value], index) => <motion.div key={label} {...entrance(.18 + index * .04, 4)}><dt>{label}</dt><dd>{value}</dd></motion.div>)}</dl>
      </motion.figure>
    </div>
  </section>;
}
