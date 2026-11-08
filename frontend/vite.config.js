import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev the API is proxied at /api, so the browser needs no CORS setup.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": { target: "http://localhost:8000", rewrite: (p) => p.replace(/^\/api/, "") } } },
});
