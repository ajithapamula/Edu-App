import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('./certs/key.pem'),
      cert: fs.readFileSync('./certs/cert.pem'),
    },
    host: true, // or '0.0.0.0' if you prefer
    port: 5179, // 👈 fixed port (change to what you want)
    strictPort: true, // 👈 ensures it won’t auto-fallback
    proxy: {
      '/api': {
        target: 'https://192.168.48.201:8070',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
