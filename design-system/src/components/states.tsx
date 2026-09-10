import type { ReactNode } from 'react';
import { AlertCircle, Check, Circle, Inbox } from 'lucide-react';
import { Skeleton } from './ui/skeleton';
export function StatusBadge({ tone = 'neutral', children }: { tone?: 'neutral' | 'success' | 'warning' | 'danger'; children: ReactNode }) {
  const Icon = tone === 'success' ? Check : tone === 'neutral' ? Circle : AlertCircle;
  return <span className="tt-status" data-tone={tone}><Icon size={14} aria-hidden="true" />{children}</span>;
}
export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="tt-state"><Inbox size={28} aria-hidden="true" /><h3>{title}</h3><p>{description}</p>{action}</div>;
}
export function ErrorState({ title = 'تعذّر تحميل المحتوى', description, action }: { title?: string; description: string; action?: ReactNode }) {
  return <div className="tt-state" role="alert"><AlertCircle size={28} aria-hidden="true" /><h3>{title}</h3><p>{description}</p>{action}</div>;
}
export function LoadingState({ label = 'جارٍ تحميل المحتوى' }: { label?: string }) {
  return <div className="space-y-3 p-6" role="status" aria-label={label}><span className="sr-only">{label}</span><Skeleton className="h-5 w-2/3"/><Skeleton className="h-4 w-full"/><Skeleton className="h-4 w-4/5"/></div>;
}
