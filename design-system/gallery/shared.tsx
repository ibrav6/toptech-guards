import * as React from 'react';
export function SectionHeading({ number, title, description }: { number: string; title: string; description: string }) {
  return <div className="g-section-heading"><span className="g-eyebrow">{number} / قمم للتصميم</span><h1>{title}</h1><p>{description}</p></div>;
}
export function Block({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return <section className="g-block"><div className="g-block-head"><h2>{title}</h2>{note && <span>{note}</span>}</div><div className="g-block-body">{children}</div></section>;
}
