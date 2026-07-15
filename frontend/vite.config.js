import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// dev: proxy /api -> uvicorn :8000 (W-D6). prod: FastAPI serve dist/.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./tests/setup.js",
  },
});
