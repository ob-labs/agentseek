# Frontend — {{ cookiecutter.project_name }}

CopilotKit + Vite frontend. Talks to the Bub AG-UI gateway through a small
Copilot Runtime (Express).

## Run

```bash
npm install
npm run dev
```

The Vite server reads frontend env files and shell environment variables. The
project root `.env` is used by AgentSeek readiness checks and by the Bub gateway,
not as an implicit frontend runtime injection layer.

| Service | Port |
| --- | --- |
| Vite dev server | {{ cookiecutter.frontend_port }} |
| Copilot Runtime | {{ cookiecutter.copilotkit_port }} |
| Bub AG-UI gateway | {{ cookiecutter.gateway_port }} |
