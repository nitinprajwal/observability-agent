import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],

  server: {
    port: 5173,
    proxy: {
      // ALL /api/* routes go through the obs-agent nginx (localhost:8085).
      // The obs-agent is the single ingress point: it proxies to Prometheus,
      // Loki, Tempo on the Docker internal network AND validates NitroNode
      // Better Auth sessions before forwarding to Grafana.
      //
      // DO NOT proxy individual backend ports — they are not exposed to the host.
      // Correct flow: browser → localhost:8085/api/prometheus → nginx → prometheus:9090
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
    },
  },
})