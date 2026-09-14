import * as React from 'react';
import { renderToString } from 'react-dom/server';
import { Gallery, prepareGallery } from './gallery';
export async function renderPages() {
 const pages: Record<string, string> = {};
 await prepareGallery('#components');
 for (const section of ['overview', 'foundations', 'components', 'patterns', 'guidelines']) {
  for (const theme of ['light', 'dark', 'auto']) for (const dir of ['rtl', 'ltr']) {
   pages[`${section}/${theme}/${dir}`] = renderToString(<React.StrictMode><Gallery initialHash={`#${section}`} initialSearch={`?theme=${theme}&dir=${dir}`} /></React.StrictMode>);
  }
 }
 return pages;
}
