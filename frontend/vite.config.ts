import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      'localhost',
      '.ngrok-free.app',
      'daa65fe0204a.ngrok-free.app'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8051',
        changeOrigin: true,
      },
      '/mcp': {
        target: 'http://localhost:8051',
        changeOrigin: true,
      },
    },
  },
})
