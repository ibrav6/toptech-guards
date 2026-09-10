import type { Config } from 'tailwindcss';
import animate from 'tailwindcss-animate';
const color = (name: string) => `hsl(var(--${name}) / <alpha-value>)`;
export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./src/**/*.{ts,tsx}', './gallery/**/*.{ts,tsx}'],
  important: '.tt-theme',
  corePlugins: { preflight: false },
  theme: { extend: {
    colors: Object.fromEntries(['background','foreground','card','card-foreground','popover','popover-foreground','primary','primary-foreground','secondary','secondary-foreground','muted','muted-foreground','accent','accent-foreground','destructive','destructive-foreground','border','input','ring'].map(name => [name, color(name)])),
    borderRadius: { lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)' },
    fontFamily: { sans: ['var(--tt-font)', 'sans-serif'] },
    keyframes: { 'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } }, 'accordion-up': { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } } },
    animation: { 'accordion-down': 'accordion-down .18s ease-out', 'accordion-up': 'accordion-up .18s ease-out' }
  } }, plugins: [animate]
} satisfies Config;
