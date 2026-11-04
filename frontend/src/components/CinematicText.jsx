// Planes Cinematic Text, free component: https://useplanes.com/r/cinematic-text.json
// Adapted to JavaScript and existing CSS; explicit line breaks preserve OmniKP's headline.
import { Fragment, useRef } from 'react';
import { motion, useInView, useReducedMotion } from 'motion/react';

export function CinematicText({ children, as: Tag = 'h1', delay = .2, stagger = .11, blur = 28, once = true, className = '' }) {
  const reduced = useReducedMotion();
  const ref = useRef(null);
  const inView = useInView(ref, { once, margin: '0px 0px -10% 0px' });
  let index = 0;
  return <Tag ref={ref} className={`cinematic-text ${className}`}>
    <span className="sr-only">{children.replaceAll('\n', ' ')}</span>
    {reduced ? <span aria-hidden="true">{children}</span> : <span aria-hidden="true">
      {children.split('\n').map((line, lineIndex) => <Fragment key={lineIndex}>
        {lineIndex > 0 && <br />}
        {line.split(/\s+/).filter(Boolean).map((word, wordIndex, words) => {
          const wordDelay = delay + index++ * stagger;
          return <motion.span key={wordIndex} className="cinematic-text__word"
            initial={{ opacity: 0, y: 22, scale: 1.04, filter: `blur(${blur}px)` }}
            animate={inView ? { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' } : { opacity: 0, y: 22, scale: 1.04, filter: `blur(${blur}px)` }}
            transition={{ duration: 1.4, delay: wordDelay, ease: [.16, 1, .3, 1] }}>
            {word}{wordIndex < words.length - 1 ? '\u00a0' : ''}
          </motion.span>;
        })}
      </Fragment>)}
    </span>}
  </Tag>;
}
