import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// المعرض صفحة عميل: إدراج CSS في HTML يزيل رحلة الشبكة الحاجبة لأول رسم.
export default defineConfig({ plugins: [react(), {
  name: 'gallery-critical-css',
  enforce: 'post',
  generateBundle(_, bundle) {
    for (const asset of Object.values(bundle)) {
      if (asset.type !== 'asset' || !asset.fileName.endsWith('.html')) continue;
      asset.source = String(asset.source).replace(/<link rel="stylesheet"[^>]*href="\.\/([^\"]+)"[^>]*>/g, (tag, file: string) => {
        const css = bundle[file];
        return css?.type === 'asset' ? `<style>${String(css.source).replaceAll('url(./', 'url(./assets/')}</style>` : tag;
      });
    }
  }
}], base: './', build: { outDir: 'gallery-dist' }, server: { host: '127.0.0.1', port: 4178, strictPort: true } });
