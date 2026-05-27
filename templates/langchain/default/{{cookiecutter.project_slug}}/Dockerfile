FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir .

ENV AGENTSEEK_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.demo_binding:build_spec
ENV AGENTSEEK_STREAM_OUTPUT=true

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["agentseek", "gateway", "--enable-channel", "ag-ui"]
