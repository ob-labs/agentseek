# Frontend — {{ cookiecutter.project_name }}

CopilotKit + Vite frontend. Talks to the Bub AG-UI gateway through a small
Copilot Runtime (Express).

## Run

```bash
npm install
npm run dev
```

| Service | Port |
| --- | --- |
| Vite dev server | {{ cookiecutter.frontend_port }} |
| Copilot Runtime | {{ cookiecutter.copilotkit_port }} |
| Bub AG-UI gateway | {{ cookiecutter.gateway_port }} |
