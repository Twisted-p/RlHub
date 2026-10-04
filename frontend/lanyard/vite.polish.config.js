import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  plugins:[react()],resolve:{alias:{'@':fileURLToPath(new URL('./src',import.meta.url))}},
  define:{'process.env.NODE_ENV':JSON.stringify('production')},base:'./',
  build:{outDir:'../../assets/app-polish',emptyOutDir:true,
    lib:{entry:'src/app-polish.jsx',formats:['es'],fileName:()=> 'app-polish.js',cssFileName:'app-polish'},
    rollupOptions:{output:{assetFileNames:'[name][extname]'}}}
});
