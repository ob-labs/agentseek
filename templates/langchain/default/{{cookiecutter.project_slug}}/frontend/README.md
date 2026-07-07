# Frontend — {{ cookiecutter.project_name }}

This frontend mirrors the repository's LangChain + AG-UI example: CopilotKit,
Hashbrown, a small Copilot Runtime, and a Vite app that talks to
`bub gateway --enable-channel ag-ui`.

## Run

```bash
npm install
npm run dev
```

| Service | Port |
| --- | --- |
| Vite dev server | {{ cookiecutter.frontend_port }} |
| Copilot Runtime | {{ cookiecutter.copilotkit_port }} |
| Agentseek gateway | {{ cookiecutter.gateway_port }} |
