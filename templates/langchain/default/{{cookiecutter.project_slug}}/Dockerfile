FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /usr/local/bin/

WORKDIR /app

ARG INSTALL_FEISHU=false
ARG UV_DEFAULT_INDEX
ARG UV_INDEX_URL
ARG UV_INSECURE_HOST
{% if cookiecutter._agentseek_source_path %}
RUN if [ "$INSTALL_FEISHU" = "true" ]; then \
        apt-get update \
        && apt-get install -y --no-install-recommends git \
        && rm -rf /var/lib/apt/lists/*; \
    fi

COPY --from=agentseek_source contrib/agentseek-ag-ui {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-ag-ui
COPY --from=agentseek_source contrib/agentseek-langchain {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-langchain

{% else %}
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

{% endif %}
COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
{% if cookiecutter._agentseek_source_path %}
RUN set -e; \
    if [ -n "${UV_DEFAULT_INDEX:-}" ]; then export UV_DEFAULT_INDEX; fi; \
    if [ -n "${UV_INDEX_URL:-}" ]; then export UV_INDEX_URL; fi; \
    if [ -n "${UV_INSECURE_HOST:-}" ]; then export UV_INSECURE_HOST; fi; \
    UV_LINK_MODE=copy uv pip install --system \
        {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-ag-ui \
        {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-langchain \
        "bub==0.3.9" \
        -r requirements.txt \
    && if [ "$INSTALL_FEISHU" = "true" ]; then \
        uv pip install --system "bub-feishu @ git+https://github.com/bubbuild/bub-contrib.git@5374c8ffc8a38091a4e26dcc455c54f3c9e71aff#subdirectory=packages/bub-feishu"; \
    fi \
    && uv pip install --system --no-deps .
{% else %}
RUN set -e; \
    if [ -n "${UV_DEFAULT_INDEX:-}" ]; then export UV_DEFAULT_INDEX; fi; \
    if [ -n "${UV_INDEX_URL:-}" ]; then export UV_INDEX_URL; fi; \
    if [ -n "${UV_INSECURE_HOST:-}" ]; then export UV_INSECURE_HOST; fi; \
    UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/usr/local uv sync --no-dev --no-cache
{% endif %}

ENV BUB_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.demo_binding:build_spec
ENV BUB_STREAM_OUTPUT=true
ENV BUB_AG_UI_HOST=0.0.0.0

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["bub", "gateway", "--enable-channel", "ag-ui"]
