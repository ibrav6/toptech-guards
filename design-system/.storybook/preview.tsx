import type { Preview } from '@storybook/react-vite';
import { ThemeProvider } from '@toptech/ui';
import '@fontsource/ibm-plex-sans-arabic/400.css';
import '@fontsource/ibm-plex-sans-arabic/500.css';
import '@fontsource/ibm-plex-sans-arabic/600.css';
import '@toptech/ui/styles.css';
const preview: Preview = {
  globalTypes: {
    theme: { description: 'المظهر', toolbar: { icon: 'circlehollow', items: ['light', 'dark'] } },
    direction: { description: 'الاتجاه', toolbar: { icon: 'globe', items: ['rtl', 'ltr'] } }
  }, initialGlobals: { theme: 'light', direction: 'rtl' },
  decorators: [(Story, context) => <ThemeProvider theme={context.globals.theme} dir={context.globals.direction}><div className="tt-story"><Story /></div></ThemeProvider>],
  parameters: { layout: 'fullscreen', a11y: { test: 'error' }, options: { storySort: { order: ['الهوية', 'الأساس', 'التفاعل', 'القوالب'] } } }
};
export default preview;
