import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const port = Number(env.FRONTEND_PORT ?? "{{ cookiecutter.frontend_port }}");
  return {
    plugins: [react()],
    server: { host: "127.0.0.1", port, strictPort: true },
  };
});
