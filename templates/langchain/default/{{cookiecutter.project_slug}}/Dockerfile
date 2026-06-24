FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /usr/local/bin/

WORKDIR /app

ARG INSTALL_FEISHU=false
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

{% if cookiecutter._agentseek_source_path %}
COPY --from=agentseek_source . {{ cookiecutter._agentseek_source_path }}

{% endif %}
COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
{% if cookiecutter._agentseek_source_path %}
RUN UV_LINK_MODE=copy uv pip install --system \
        {{ cookiecutter._agentseek_source_path }} \
        {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-ag-ui \
        {{ cookiecutter._agentseek_source_path }}/contrib/agentseek-langchain \
        -r requirements.txt \
    && if [ "$INSTALL_FEISHU" = "true" ]; then \
        uv pip install --system "bub-feishu @ git+https://github.com/bubbuild/bub-contrib.git@5374c8ffc8a38091a4e26dcc455c54f3c9e71aff#subdirectory=packages/bub-feishu"; \
    fi \
    && uv pip install --system --no-deps .
{% else %}
RUN UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/usr/local uv sync --no-dev --no-cache
{% endif %}

ENV AGENTSEEK_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.demo_binding:build_spec
ENV AGENTSEEK_STREAM_OUTPUT=true

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["agentseek", "gateway", "--enable-channel", "ag-ui"]
