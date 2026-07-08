import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const frontendPort = Number(process.env.FRONTEND_PORT || env.FRONTEND_PORT || "{{ cookiecutter.frontend_port }}");
  const bubTarget =
    process.env.VITE_BUB_AG_UI_URL ||
    env.VITE_BUB_AG_UI_URL ||
    "http://127.0.0.1:{{ cookiecutter.gateway_port }}";
  const copilotRuntimeTarget =
    process.env.VITE_COPILOTKIT_RUNTIME_PROXY ||
    env.VITE_COPILOTKIT_RUNTIME_PROXY ||
    "http://127.0.0.1:{{ cookiecutter.copilotkit_port }}";

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
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
