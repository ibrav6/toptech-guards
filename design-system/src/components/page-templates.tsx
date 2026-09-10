import type { ReactNode } from 'react';
import { cn } from '../lib/utils';
export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
 return <header className="tt-page-header"><div>{eyebrow && <p className="tt-page-eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="tt-page-description">{description}</p>}</div>{actions && <div className="tt-page-actions">{actions}</div>}</header>;
}
export function PageSection({ title, description, children, className, id }: { title: string; description?: string; children: ReactNode; className?: string; id?: string }) {
 return <section className={cn('tt-page-section',className)} id={id}><div className="tt-page-section-heading"><h2>{title}</h2>{description && <p>{description}</p>}</div>{children}</section>;
}
export function ListPage({ header, filters, summary, children }: { header: ReactNode; filters?: ReactNode; summary?: ReactNode; children: ReactNode }) {
 return <div className="tt-page">{header}{summary && <div className="tt-page-summary">{summary}</div>}{filters && <div className="tt-page-filters" role="search" aria-label="تصفية القائمة">{filters}</div>}{children}</div>;
}
export function DetailPage({ header, summary, navigation, aside, children }: { header: ReactNode; summary?: ReactNode; navigation?: ReactNode; aside?: ReactNode; children: ReactNode }) {
 return <div className="tt-page">{header}{summary && <div className="tt-page-summary">{summary}</div>}{navigation}<div className="tt-detail-layout" data-aside={!!aside}><div className="tt-detail-content">{children}</div>{aside && <aside className="tt-detail-aside">{aside}</aside>}</div></div>;
}
export function SettingsPage({ header, children, footer }: { header: ReactNode; children: ReactNode; footer?: ReactNode }) {
 return <div className="tt-page tt-settings-page">{header}<div className="tt-settings-sections">{children}</div>{footer && <div className="tt-settings-footer">{footer}</div>}</div>;
}
