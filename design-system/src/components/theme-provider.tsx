'use client';
import * as React from 'react';
import { DirectionProvider } from '@radix-ui/react-direction';
import { cn } from '../lib/utils';
export type DesignTheme = 'light' | 'dark' | 'auto';
export type DesignDirection = 'rtl' | 'ltr';
const DesignContext = React.createContext<{ theme: DesignTheme; dir: DesignDirection }>({ theme: 'light', dir: 'rtl' });
export function useDesignSystem() { return React.useContext(DesignContext); }
export function ThemeProvider({ children, theme = 'light', dir = 'rtl', className }: { children: React.ReactNode; theme?: DesignTheme; dir?: DesignDirection; className?: string }) {
  return <DesignContext.Provider value={{ theme, dir }}><DirectionProvider dir={dir}><div className={cn('tt-theme', className)} data-theme={theme} dir={dir}>{children}</div></DirectionProvider></DesignContext.Provider>;
}
/** البوابة تخرج من شجرة DOM؛ إعادة الاتجاه والرموز تمنع فقدان العربية والمظهر. */
export function PortalTheme({ children }: { children: React.ReactNode }) {
  const { theme, dir } = useDesignSystem();
  return <div className="tt-theme tt-portal" data-theme={theme} dir={dir}>{children}</div>;
}
