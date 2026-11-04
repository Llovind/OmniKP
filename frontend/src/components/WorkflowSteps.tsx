import { useRef, useSyncExternalStore } from 'react';
import { motion, useInView } from 'motion/react';
import { FileUp, ListChecks, Layers3, Search, type LucideIcon } from 'lucide-react';
import './WorkflowSteps.css';

const steps = [
  { title: 'Submit', body: 'Choose the submitting unit, reporting date and Excel or CSV file.', Icon: FileUp },
  { title: 'Review mapping', body: 'AI proposes column meanings. The analyst reviews and corrects them.', Icon: ListChecks },
  { title: 'Consolidate', body: 'Validated readings enter a shared database, linked to the source file, row and submitting unit.', Icon: Layers3 },
  { title: 'Investigate', body: 'Attach division feedback to a KPI, location and date, then request a root-cause analysis draft.', Icon: Search },
];
const preference = '(prefers-reduced-motion: reduce)';
function subscribe(callback: () => void) {
  const media = window.matchMedia(preference);
  media.addEventListener('change', callback);
  return () => media.removeEventListener('change', callback);
}

function WorkflowStep({ title, body, Icon, index, reduced }: { title: string; body: string; Icon: LucideIcon; index: number; reduced: boolean }) {
  const ref = useRef<HTMLLIElement>(null);
  const inView = useInView(ref, { once: true, amount: .35 });
  const revealed = inView || reduced;
  const delay = reduced ? 0 : index * .07;
  return <motion.li ref={ref} className="workflow-step" data-revealed={revealed}
    initial={false} animate={{ y: revealed ? 0 : 6 }}
    transition={{ duration: reduced ? 0 : .32, delay, ease: [.16, 1, .3, 1] }}>
    <motion.span aria-hidden="true" className="workflow-step__rule" initial={false}
      animate={{ scaleX: revealed ? 1 : 0, scaleY: revealed ? 1 : 0 }}
      transition={{ duration: reduced ? 0 : .5, delay: reduced ? 0 : delay + .08, ease: [.16, 1, .3, 1] }} />
    <span className="step-number" aria-hidden="true">0{index + 1}</span>
    <h3><span className="workflow-step__icon" aria-hidden="true"><Icon size={18} strokeWidth={1.75} /></span>{title}</h3>
    <p>{body}</p>
  </motion.li>;
}

export default function WorkflowSteps() {
  const reduced = useSyncExternalStore(subscribe, () => window.matchMedia(preference).matches, () => true);
  return <ol className="landing-steps workflow-timeline" role="list">{steps.map((step, index) => <WorkflowStep key={step.title} {...step} index={index} reduced={reduced} />)}</ol>;
}
