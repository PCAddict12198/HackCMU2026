import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

const here = fileURLToPath(new URL(".", import.meta.url));
const repoRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig(({ mode }) => {
  // .env / .env.local live at the repo root (API_PORT comes from the per-worktree .env.local)
  const env = loadEnv(mode, repoRoot, "");
  const apiPort = process.env.API_PORT || env.API_PORT || "8000";
  return {
    plugins: [react()],
    envDir: repoRoot,
    resolve: { alias: { "@contracts": fileURLToPath(new URL("../contracts", import.meta.url)) } },
    server: {
      fs: { allow: [here, repoRoot] },
      proxy: { "/api": `http://127.0.0.1:${apiPort}` },
    },
    test: { environment: "node" },
  };
});
