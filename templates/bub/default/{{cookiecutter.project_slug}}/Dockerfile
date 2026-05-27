FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["agentseek", "gateway", "--enable-channel", "ag-ui"]
