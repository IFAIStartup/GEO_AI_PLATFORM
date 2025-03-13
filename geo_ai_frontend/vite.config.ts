import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import svgr from "vite-plugin-svgr";
import basicSsl from "@vitejs/plugin-basic-ssl";
import * as path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), svgr(), basicSsl()],
  resolve: {
    alias: [
      {
        find: "@assets",
        replacement: path.resolve(__dirname, "src/assets"),
      },
      {
        find: "@components",
        replacement: path.resolve(__dirname, "src/components"),
      },
      { find: "@models", replacement: path.resolve(__dirname, "src/models") },
      { find: "@pages", replacement: path.resolve(__dirname, "src/pages") },
      {
        find: "@services",
        replacement: path.resolve(__dirname, "src/services"),
      },
      { find: "@store", replacement: path.resolve(__dirname, "src/store") },
    ],
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "https://172.20.0.6:8090",
        changeOrigin: true,
        secure: false,
      },
}
  },
});
