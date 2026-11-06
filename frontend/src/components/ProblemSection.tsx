import { useRef, useSyncExternalStore } from 'react';
import { motion, useInView } from 'motion/react';
import { Files, Combine, MessageSquareOff, type LucideIcon } from 'lucide-react';
import './ProblemSection.css';

const reducedQuery = '(prefers-reduced-motion: reduce)';
const hoverQuery = '(hover: hover) and (pointer: fine)';
function observe(query: string, callback: () => void) {
  const media = window.matchMedia(query);
  media.addEventListener('change', callback);
  return () => media.removeEventListener('change', callback);
}
const subscribeReduced = (callback: () => void) => observe(reducedQuery, callback);
const subscribeHover = (callback: () => void) => observe(hoverQuery, callback);
const problems = [
  { title: 'Reports live in different files', body: 'Each division reports separately, leaving analysts to connect the pieces.', Icon: Files },
  { title: 'Consolidating takes manual effort', body: 'Column meanings, units and targets need to line up before results can be compared.', Icon: Combine },
  { title: 'Explanations get lost', body: 'The reason behind a missed target can become detached from the reading.', Icon: MessageSquareOff },
];

function ProblemPanel({ title, body, Icon, index, reduced, canHover }: {
  title: string; body: string; Icon: LucideIcon; index: number; reduced: boolean; canHover: boolean;
}) {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, amount: .3 });
  const revealed = inView || reduced;
  return <motion.article ref={ref} className="problem-panel" data-revealed={revealed} data-problem-motion=""
    initial={false} animate={{ y: revealed ? 0 : 8 }}
    transition={{ duration: reduced ? 0 : .3, delay: reduced ? 0 : index * .06, ease: [.16, 1, .3, 1] }}
    whileHover={canHover && !reduced ? { y: -3, transition: { duration: .18, delay: 0, ease: [.16, 1, .3, 1] } } : undefined}>
    <span className="problem-panel__icon"><Icon size={26} strokeWidth={1.5} aria-hidden="true" /></span>
    <h3>{title}</h3><p>{body}</p>
  </motion.article>;
}

export default function ProblemSection() {
  const heading = useRef<HTMLHeadingElement>(null);
  const inView = useInView(heading, { once: true, amount: .5 });
  const reduced = useSyncExternalStore(subscribeReduced, () => window.matchMedia(reducedQuery).matches, () => true);
  const canHover = useSyncExternalStore(subscribeHover, () => window.matchMedia(hoverQuery).matches, () => false);
  return <section className="landing-section landing-container problem-section" aria-labelledby="problem-heading">
    <motion.h2 ref={heading} id="problem-heading" data-problem-motion="" initial={false}
      animate={{ y: inView || reduced ? 0 : 6 }} transition={{ duration: reduced ? 0 : .3, ease: [.16, 1, .3, 1] }}>
      <span>The data exists.</span><br />The shared view takes work.
    </motion.h2>
    <div className="problem-columns">{problems.map((problem, index) => <ProblemPanel key={problem.title} {...problem} index={index} reduced={reduced} canHover={canHover} />)}</div>
  </section>;
}
