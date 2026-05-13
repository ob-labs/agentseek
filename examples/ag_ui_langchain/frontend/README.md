# LangChain example frontend (CopilotKit + Hashbrown)

Standalone Vite app for [`../README.md`](../README.md). **Does not** modify `examples/ag-ui/frontend`.

- **Vite**: `http://127.0.0.1:5174` (proxies `/api/copilotkit` → Copilot Runtime below).
- **Copilot Runtime** (`server.ts`): `http://127.0.0.1:4001` by default (`COPILOTKIT_PORT`), forwards to gateway `http://127.0.0.1:8088/agent`.

Aligns with [LangChain CopilotKit + Hashbrown](https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit): `useUiKit`, `useAgentContext` (`output_schema`), assistant markdown slot + `useJsonParser` / `kit.render`, with markdown fallback when content is not valid UI JSON.

## Run

From this directory (after the gateway is up with `--enable-channel ag-ui`):

```bash
npm install
npm run dev
```

Optional env (see [`.env.example`](.env.example)): `COPILOTKIT_PORT`, `AGENTSEEK_AG_UI_AGENT_URL`, `VITE_COPILOTKIT_RUNTIME_PROXY`, `VITE_AGENTSEEK_AG_UI_URL`.
