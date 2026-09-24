import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 开发模式将 API 与静态资源代理到 FastAPI 后端
const backendTarget = process.env.BACKEND_URL || "http://127.0.0.1:4389";

export default defineConfig({
  plugins: [vue()],
  base: "/",
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": { target: backendTarget, changeOrigin: true },
      "/assets": { target: backendTarget, changeOrigin: true },
      "/background": { target: backendTarget, changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "static",
  },
});
