import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  plugins: [react()],
  resolve: {alias: {'@': fileURLToPath(new URL('./src', import.meta.url))}},
  define: {'process.env.NODE_ENV': JSON.stringify('production')},
  base: './',
  build: {
    outDir: '../../assets/goals-star-border',
    emptyOutDir: true,
    lib: {entry: 'src/goals-star-border.jsx', formats: ['es'], fileName: () => 'goals-star-border.js', cssFileName: 'goals-star-border'},
    rollupOptions: {output: {assetFileNames: '[name][extname]'}}
  }
});
