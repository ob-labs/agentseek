# Frontend — {{ cookiecutter.project_name }}

CopilotKit + Vite frontend. Talks to the agentseek gateway over AG-UI
through a small Copilot Runtime (Express).

## Run

```bash
npm install
npm run dev
```

| Service | Port |
| --- | --- |
| Vite dev server | {{ cookiecutter.frontend_port }} |
| Copilot Runtime | 4000 |
| Agentseek gateway | {{ cookiecutter.gateway_port }} |
