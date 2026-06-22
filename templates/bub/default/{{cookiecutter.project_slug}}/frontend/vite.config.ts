import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const frontendPort = Number(env.FRONTEND_PORT || "{{ cookiecutter.frontend_port }}");
  const bubTarget = env.VITE_BUB_AG_UI_URL || "http://127.0.0.1:{{ cookiecutter.gateway_port }}";
  const copilotRuntimeTarget =
    env.VITE_COPILOTKIT_RUNTIME_PROXY || "http://127.0.0.1:{{ cookiecutter.copilotkit_port }}";

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      proxy: {
        "/api/copilotkit": {
          target: copilotRuntimeTarget,
          changeOrigin: true,
        },
        "/agent": {
          target: bubTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
