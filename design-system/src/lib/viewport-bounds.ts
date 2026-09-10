import * as React from 'react';
/**
 * على 320px، قلبُ Radix للقائمة الفرعية وحده يترك حافتها عند 402px.
 * عند غياب المساحة الجانبية نسمح بالتراكب. يُراقب إطارُ القائمة المفتوحة
 * فقط لأن موضع Popper يتغيّر بالـtransform دون أن يراه ResizeObserver.
 */
export function useViewportBounds<T extends HTMLElement>(forwardedRef: React.ForwardedRef<T>) {
  const [node, setNode] = React.useState<T | null>(null);
  React.useLayoutEffect(() => {
    if (!node) return;
    let frame = 0;
    function measure() {
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const applied = Number.parseFloat(getComputedStyle(node).translate) || 0;
      const originalLeft = rect.left - applied;
      const available = document.documentElement.clientWidth;
      const shift = Math.max(16 - originalLeft, Math.min(0, available - 16 - (originalLeft + rect.width)));
      const value = `${shift}px`;
      if (node.style.getPropertyValue('--tt-popup-shift') !== value) node.style.setProperty('--tt-popup-shift', value);
      frame = requestAnimationFrame(measure);
    }
    frame = requestAnimationFrame(measure);
    return () => cancelAnimationFrame(frame);
  }, [node]);
  return React.useCallback((node: T | null) => {
    setNode(node);
    if (typeof forwardedRef === 'function') forwardedRef(node);
    else if (forwardedRef) forwardedRef.current = node;
  }, [forwardedRef]);
}
