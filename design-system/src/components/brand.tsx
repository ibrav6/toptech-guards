import type { SVGProps } from 'react';
export function BrandMark(props: SVGProps<SVGSVGElement>) {
  return <svg width="36" height="36" viewBox="0 0 40 40" fill="none" aria-hidden="true" {...props}><rect width="40" height="40" rx="11" fill="currentColor"/><path d="M9 27V20L16 13L23 20V27M17 27V17L24 10L31 17V27" stroke="var(--tt-mark-cutout, hsl(var(--background)))" strokeWidth="3" strokeLinejoin="round"/></svg>;
}
export function Brand({ compact = false }: { compact?: boolean }) {
  return <span className="tt-brand" aria-label="قمم التقنية"><BrandMark />{!compact && <span><strong>قمم التقنية</strong><small lang="en" dir="ltr">TOPTECH</small></span>}</span>;
}
