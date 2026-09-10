import React from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/ibm-plex-sans-arabic/400.css';
import '@fontsource/ibm-plex-sans-arabic/500.css';
import '@fontsource/ibm-plex-sans-arabic/600.css';
import '@toptech/ui/styles.css';
import './gallery.css';
import { Gallery } from './gallery';
createRoot(document.getElementById('root')!).render(<React.StrictMode><Gallery /></React.StrictMode>);
