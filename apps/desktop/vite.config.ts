import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
const ENGINE_PORT = process.env.ENGINE_PORT ?? '9000'
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: { port: 5173, proxy: { '/api': { target: `http://127.0.0.1:${ENGINE_PORT}`, changeOrigin: true, ws: true } } },
  build: { outDir: 'dist', emptyOutDir: true },
  test: { globals: true, environment: 'jsdom', setupFiles: ['./tests/setup.ts'], include: ['tests/**/*.test.{ts,tsx}'], alias: { '@': path.resolve(__dirname, 'src') } },
})
