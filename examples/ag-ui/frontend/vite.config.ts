import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const agentseekTarget = env.VITE_AGENTSEEK_AG_UI_URL || "http://127.0.0.1:8088";
  const copilotRuntimeTarget = env.VITE_COPILOTKIT_RUNTIME_PROXY || "http://127.0.0.1:4000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api/copilotkit": {
          target: copilotRuntimeTarget,
          changeOrigin: true
        },
        "/agent": {
          target: agentseekTarget,
          changeOrigin: true
        }
      }
    }
  };
});
