import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { viteSingleFile } from 'vite-plugin-singlefile';
export default defineConfig({
  plugins: [svelte(), viteSingleFile()],
  build: { outDir: 'dist-' + (process.env.VITE_LANGUE || 'fr'), target: 'es2019', cssCodeSplit: false, assetsInlineLimit: 100000000 }
});
