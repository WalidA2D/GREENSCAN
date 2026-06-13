import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le frontend appelle l'API via /api -> proxifié vers FastAPI (port 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
