import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

import { reviewerApiPlugin } from "./reviewerApiPlugin";

export default defineConfig({
  plugins: [vue(), reviewerApiPlugin()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5174,
    strictPort: true,
  },
  build: {
    outDir: "dist-reviewer",
    emptyOutDir: true,
    rollupOptions: {
      input: "reviewer.html",
    },
  },
});
