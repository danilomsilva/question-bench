import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev-only: forward API calls to the FastAPI app so the SPA can use
// same-origin relative URLs. In the container the app is served behind
// its own origin and these paths hit the backend directly.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/generate": "http://localhost:8000",
      "/items": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
