import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  define: {'process.env.NODE_ENV': JSON.stringify('production')},
  assetsInclude: ['**/*.glb'],
  base: './',
  build: {
    outDir: '../../assets/dashboard-lanyard',
    emptyOutDir: true,
    lib: {entry: 'src/main.jsx', formats: ['es'], fileName: () => 'dashboard-lanyard.js'},
    rollupOptions: {output: {assetFileNames: '[name][extname]'}},
    assetsInlineLimit: 0
  }
});
