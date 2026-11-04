// Adapted from Arc's free Theme Switch: https://uiarc.dev/r/theme-switch.json
// Uses OmniKP's existing button styling instead of installing a second button system.
import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { Moon, Sun } from 'lucide-react';
import './ThemeSwitch.css';

function useSettled() {
  const [settled, setSettled] = useState(false);
  useEffect(() => {
    let second = 0;
    const first = requestAnimationFrame(() => { second = requestAnimationFrame(() => setSettled(true)); });
    return () => { cancelAnimationFrame(first); cancelAnimationFrame(second); };
  }, []);
  return settled;
}

export function ThemeSwitch({ theme, variant = 'reveal', onThemeChange, label, iconOnly = false }) {
  const reduced = useReducedMotion();
  const settled = useSettled();
  const next = theme === 'light' ? 'dark' : 'light';
  const Icon = theme === 'light' ? Sun : Moon;
  const angle = theme === 'light' ? 30 : -30;
  return <button type="button" className={`btn-ghost theme-switch ${iconOnly ? 'theme-switch--icon' : ''}`}
    data-theme={theme} data-variant={variant} aria-label={label ?? `Switch to ${next} mode`}
    aria-pressed={theme === 'dark'} onClick={event => onThemeChange(next, variant, event.currentTarget)}>
    <span className="theme-switch__icons" aria-hidden="true">
      <AnimatePresence initial={false} mode="popLayout">
        <motion.span key={theme} className="theme-switch__icon"
          initial={!settled ? false : reduced ? { opacity: 0 } : { opacity: 0, scale: .7, rotate: angle, filter: 'blur(2px)' }}
          animate={{ opacity: 1, scale: 1, rotate: 0, filter: 'blur(0px)' }}
          exit={!settled || reduced ? { opacity: 0, transition: { duration: 0 } } : { opacity: 0, scale: .7, rotate: angle, filter: 'blur(2px)', transition: { duration: .16 } }}
          transition={reduced ? { duration: 0 } : { type: 'spring', visualDuration: .26, bounce: 0, opacity: { duration: .16 }, filter: { duration: .16 } }}>
          <Icon size={18} strokeWidth={1.75} />
        </motion.span>
      </AnimatePresence>
    </span>
    {!iconOnly && <span>Switch theme</span>}
  </button>;
}
