import { useRef, useSyncExternalStore } from 'react';
import { motion, useInView } from 'motion/react';
import { FileUp, ListChecks, FileCheck, Search, type LucideIcon } from 'lucide-react';
import './WorkflowSteps.css';

const steps = [
  { title: 'Collect a report', body: 'UiPath submits a division file with its reporting date and requests an AI mapping preview.', Icon: FileUp },
  { title: 'Review and import', body: 'The analyst reviews the mapping. UiPath confirms the import after backend validation and analyst approval.', Icon: ListChecks },
  { title: 'Investigate a shortfall', body: 'UiPath retrieves the selected reading, its source and a draft based on division feedback.', Icon: Search },
  { title: 'Approve the report', body: 'The analyst reviews the narrative. UiPath generates the PowerPoint report after approval.', Icon: FileCheck },
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
