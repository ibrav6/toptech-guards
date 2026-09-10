'use client';
import * as React from 'react';
import { Menu } from 'lucide-react';
import { Brand } from './brand';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from './ui/sheet';
export type NavItem = { href: string; label: string; icon: React.ReactNode };
export function AppShell({ items, activeHref, onNavigate, children, header, brand = <Brand />, defaultCollapsed = false }: { items: NavItem[]; activeHref: string; onNavigate?: (href: string) => void; children: React.ReactNode; header?: React.ReactNode; brand?: React.ReactNode; defaultCollapsed?: boolean }) {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);
  const [open, setOpen] = React.useState(false);
  const mainId = React.useId(); const navId = React.useId();
  const previousRoute = React.useRef(activeHref);
  // تغيّر المعامل وحده تنقّل أيضاً؛ الإغلاق لا يعتمد على إعادة تركيب الهيكل.
  React.useEffect(() => { if (previousRoute.current !== activeHref) { setOpen(false); previousRoute.current = activeHref; } }, [activeHref]);
  React.useEffect(() => {
    const query = window.matchMedia('(min-width: 64rem)');
    const closeDesktop = () => { if (query.matches) setOpen(false); };
    query.addEventListener('change', closeDesktop); return () => query.removeEventListener('change', closeDesktop);
  }, []);
  function navigation() {
    return <ul className="tt-nav-list">{items.map(item => <li key={item.href}><a className="tt-nav-link" href={item.href} aria-label={item.label} title={item.label} aria-current={activeHref === item.href ? 'page' : undefined} onClick={event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      setOpen(false); if (onNavigate) { event.preventDefault(); onNavigate(item.href); }
    }}>{item.icon}<span className="tt-nav-text">{item.label}</span></a></li>)}</ul>;
  }
  return <div className="tt-shell" data-collapsed={collapsed}>
    <a href={`#${mainId}`} className="tt-skip">انتقل إلى المحتوى</a>
    <header className="tt-shell-header"><div className="tt-shell-header-start">
      <Button variant="ghost" size="icon" className="tt-desktop-trigger" aria-label="طيّ التنقل" aria-expanded={!collapsed} aria-controls={navId} onClick={() => setCollapsed(v => !v)}><Menu /></Button>
      <Sheet open={open} onOpenChange={setOpen}><SheetTrigger asChild><Button variant="ghost" size="icon" className="tt-mobile-trigger" aria-label="فتح التنقل"><Menu /></Button></SheetTrigger><SheetContent side="start"><SheetHeader><SheetTitle>التنقل</SheetTitle><SheetDescription>اختر وجهتك في مساحة العمل.</SheetDescription></SheetHeader><nav aria-label="التنقل في الدرج" className="mt-6">{navigation()}</nav></SheetContent></Sheet>
      {brand}</div>{header}</header>
    <nav id={navId} className="tt-shell-nav" aria-label="التنقل الرئيسي">{navigation()}</nav>
    <main id={mainId} tabIndex={-1} className="tt-shell-main">{children}</main>
  </div>;
}
