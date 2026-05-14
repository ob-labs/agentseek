# LangChain example frontend (CopilotKit + Hashbrown)

This is the standalone frontend for [`../README.md`](../README.md). It keeps its own ports so it can run next to `examples/ag-ui/frontend` without collisions.

- **Vite**: `http://127.0.0.1:5174` (proxies `/api/copilotkit` → Copilot Runtime below).
- **Copilot Runtime** (`server.ts`): `http://127.0.0.1:4001` by default (`COPILOTKIT_PORT`), forwards to gateway `http://127.0.0.1:8088/agent`.

The rendering path follows the [LangChain CopilotKit + Hashbrown](https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit) pattern: `useUiKit`, `useAgentContext` (`output_schema`), and an assistant markdown slot that tries `useJsonParser` / `kit.render` first, then falls back to markdown for non-UI replies.

## Run

From this directory (after the gateway is up with `--enable-channel ag-ui`):

```bash
npm install
npm run dev
```

Optional env (see [`.env.example`](.env.example)):

- `COPILOTKIT_PORT`
- `AGENTSEEK_AG_UI_AGENT_URL`
- `VITE_COPILOTKIT_RUNTIME_PROXY`
- `VITE_AGENTSEEK_AG_UI_URL`

## Verify

```bash
npm run build
curl -s http://127.0.0.1:4001/health
```
