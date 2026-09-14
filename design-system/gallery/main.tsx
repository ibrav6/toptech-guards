import React from 'react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import '@fontsource/ibm-plex-sans-arabic/400.css';
import '@fontsource/ibm-plex-sans-arabic/500.css';
import '@fontsource/ibm-plex-sans-arabic/600.css';
import '@toptech/ui/styles.css';
import './gallery.css';
import { Gallery, prepareGallery } from './gallery';
void prepareGallery().then(() => {
 const root = document.getElementById('root')!;
 const app = <React.StrictMode><Gallery /></React.StrictMode>;
 if (root.hasChildNodes()) hydrateRoot(root, app);
 else createRoot(root).render(app);
});
