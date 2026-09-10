import * as React from 'react';
import { Label } from './ui/label';
import { Input } from './ui/input';
/** الربط بين الخطأ والحقل جزء من المكوّن؛ لا نتركه لتخمين كل صفحة. */
export const TextField = React.forwardRef<HTMLInputElement, React.ComponentProps<typeof Input> & { label: string; hint?: string; error?: string }>(function TextField({ label, hint, error, id, ...props }, ref) {
  const generated = React.useId(); const fieldId = id ?? generated;
  const description = [hint && `${fieldId}-hint`, error && `${fieldId}-error`, props['aria-describedby']].filter(Boolean).join(' ') || undefined;
  return <div className="tt-field"><Label htmlFor={fieldId}>{label}{props.required && <span aria-hidden="true"> *</span>}</Label><Input {...props} ref={ref} id={fieldId} aria-invalid={!!error || undefined} aria-describedby={description} />{hint && <p id={`${fieldId}-hint`} className="tt-field-hint">{hint}</p>}{error && <p id={`${fieldId}-error`} className="tt-field-error" role="alert">{error}</p>}</div>;
});
