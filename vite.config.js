import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

const repoRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  root: "src",
  base: "./",
  plugins: [viteSingleFile()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    assetsInlineLimit: 100000000,
    cssCodeSplit: false,
    target: "es2020"
  },
  server: {
    fs: {
      allow: [repoRoot]
    }
  }
});
