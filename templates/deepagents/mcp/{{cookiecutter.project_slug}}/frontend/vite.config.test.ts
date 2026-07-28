{% raw %}
import { existsSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import type { ConfigEnv, UserConfig } from "vite";
import viteConfig from "./vite.config";

const resolveConfig = viteConfig as (environment: ConfigEnv) => UserConfig;
const frontendEnvPath = join(process.cwd(), ".env");
const originalHost = process.env.FRONTEND_HOST;
const originalFrontendEnv = existsSync(frontendEnvPath)
  ? readFileSync(frontendEnvPath, "utf-8")
  : null;

function serveEnvironment(): ConfigEnv {
  return { command: "serve", mode: "development", isSsrBuild: false, isPreview: false };
}

afterEach(() => {
  if (originalHost === undefined) delete process.env.FRONTEND_HOST;
  else process.env.FRONTEND_HOST = originalHost;

  if (originalFrontendEnv === null) {
    if (existsSync(frontendEnvPath)) unlinkSync(frontendEnvPath);
  } else {
    writeFileSync(frontendEnvPath, originalFrontendEnv, "utf-8");
  }
});

describe("vite host resolution", () => {
  it("prefers the exported host over the frontend env file", () => {
    writeFileSync(frontendEnvPath, "FRONTEND_HOST=192.0.2.10\n", "utf-8");
    process.env.FRONTEND_HOST = "0.0.0.0";

    const config = resolveConfig(serveEnvironment());

    expect(config.server?.host).toBe("0.0.0.0");
  });

  it("loads a persistent host from frontend/.env", () => {
    delete process.env.FRONTEND_HOST;
    writeFileSync(frontendEnvPath, "FRONTEND_HOST=192.0.2.20\n", "utf-8");

    const config = resolveConfig(serveEnvironment());

    expect(config.server?.host).toBe("192.0.2.20");
  });
});
{% endraw %}
