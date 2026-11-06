import { useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, useReducedMotion } from 'motion/react';

// Native modal dialogs provide background inertness and keyboard focus containment.
export default function Dialog({ children, onClose, labelledBy, className = '', busy = false }) {
  const ref = useRef(null);
  const [closing, setClosing] = useState(false);
  const reduced = useReducedMotion();
  useLayoutEffect(() => {
    const dialog = ref.current;
    const trigger = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.showModal();
    return () => {
      dialog.close();
      document.body.style.overflow = overflow;
      if (trigger?.isConnected) trigger.focus({ preventScroll: true });
    };
  }, []);
  const dismiss = () => { if (!busy) setClosing(true); };
  const containTab = event => {
    if (event.key !== 'Tab') return;
    const controls = [...ref.current.querySelectorAll('button,input,select,textarea,a[href],summary,[tabindex]')]
      .filter(node => !node.disabled && node.tabIndex >= 0 && node.getClientRects().length);
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault(); last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first?.focus();
    }
  };
  return createPortal(
    <dialog ref={ref} className="ui-dialog" aria-labelledby={labelledBy}
      onKeyDown={containTab}
      onCancel={event => { event.preventDefault(); dismiss(); }}
      onClick={event => { if (event.target.closest('[data-dialog-close]')) dismiss(); }}>
      <motion.div className={`dialog-panel ${className}`}
        initial={reduced ? false : { opacity: 0, y: 8 }}
        animate={closing ? { opacity: 0, y: reduced ? 0 : 6 } : { opacity: 1, y: 0 }}
        transition={{ duration: reduced ? 0 : closing ? 0.18 : 0.22, ease: [0.2, 0.8, 0.2, 1] }}
        onAnimationComplete={() => { if (closing) onClose(); }}>
        {children}
      </motion.div>
    </dialog>, document.body,
  );
}
