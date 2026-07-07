FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV BUB_AG_UI_HOST=0.0.0.0

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["bub", "gateway", "--enable-channel", "ag-ui"]
