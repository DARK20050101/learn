import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
    strictPort: true,
  },
  build: {
    outDir: "dist-reviewer",
    emptyOutDir: true,
    rollupOptions: {
      input: fileURLToPath(new URL("./reviewer.html", import.meta.url)),
    },
  },
});
