import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "FRONTEND_");
  const host = process.env.FRONTEND_HOST ?? env.FRONTEND_HOST ?? "127.0.0.1";
  const port = Number(
    process.env.FRONTEND_PORT ?? env.FRONTEND_PORT ?? "{{ cookiecutter.frontend_port }}",
  );
  return {
    plugins: [react()],
    server: { host, port, strictPort: true },
  };
});
