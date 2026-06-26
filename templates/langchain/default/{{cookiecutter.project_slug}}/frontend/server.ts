import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime } from "@copilotkit/runtime/v2";
import { createCopilotExpressHandler } from "@copilotkit/runtime/v2/express";
import express from "express";
import { loadEnv } from "vite";

const env = loadEnv(process.env.NODE_ENV || "development", process.cwd(), "");
const port = Number(
  process.env.COPILOTKIT_PORT || env.COPILOTKIT_PORT || {{ cookiecutter.copilotkit_port }},
);
const basePath = "/api/copilotkit";
const bubAgentUrl =
  process.env.BUB_AG_UI_AGENT_URL ||
  env.BUB_AG_UI_AGENT_URL ||
  "http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent";

const runtime = new CopilotRuntime({
  agents: {
    default: new HttpAgent({
      url: bubAgentUrl,
    }),
  },
});

const app = express();

app.use(
  createCopilotExpressHandler({
    runtime,
    basePath,
    cors: true,
  }),
);

app.get("/health", (_request, response) => {
  response.json({
    status: "ok",
    runtime: "copilotkit",
    agent: bubAgentUrl,
    basePath,
    port,
  });
});

const server = app.listen(port, () => {
  console.log(`CopilotKit runtime listening at http://127.0.0.1:${port}${basePath}`);
  console.log(`Forwarding default agent runs to ${bubAgentUrl}`);
});

void server;
