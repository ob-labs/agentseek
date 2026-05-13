import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime } from "@copilotkit/runtime/v2";
import { createCopilotExpressHandler } from "@copilotkit/runtime/v2/express";
import express from "express";

const port = Number(process.env.COPILOTKIT_PORT || 4000);
const basePath = "/api/copilotkit";
const agentseekAgentUrl = process.env.AGENTSEEK_AG_UI_AGENT_URL || "http://127.0.0.1:8088/agent";

const runtime = new CopilotRuntime({
  agents: {
    default: new HttpAgent({
      url: agentseekAgentUrl
    })
  }
});

const app = express();

app.use(
  createCopilotExpressHandler({
    runtime,
    basePath,
    cors: true
  })
);

app.get("/health", (_request, response) => {
  response.json({
    status: "ok",
    runtime: "copilotkit",
    agent: agentseekAgentUrl,
    basePath
  });
});

app.listen(port, () => {
  console.log(`CopilotKit runtime listening at http://127.0.0.1:${port}${basePath}`);
  console.log(`Forwarding default agent runs to ${agentseekAgentUrl}`);
});
