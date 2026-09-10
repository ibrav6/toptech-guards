import { defineConfig } from 'tsup';
export default defineConfig({ entry: ['src/index.ts'], format: ['esm'], dts: true, clean: true, splitting: true, treeshake: false, external: ['react', 'react-dom'], banner: { js: '"use client";' } });
