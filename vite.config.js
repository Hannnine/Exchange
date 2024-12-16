import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"), // 配置 @ 代表 src 路径
    },
  },
  define: {
    __VUE_PROD_DEVTOOLS__: false, // 关闭生产环境下的 Vue 调试工具
    __VUE_OPTIONS_API__: true, // 启用 Options API
    __VUE_PROD_HYDRATION__: true, // 启用服务端渲染的 hydration 支持
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false, // 关闭 hydration mismatch 的详细日志
  },
  server: {
    host: "0.0.0.0", // 开发服务器监听所有网络接口
  },
});
