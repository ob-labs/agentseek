# Install uv (official binary path in ghcr.io/astral-sh/uv image)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# tini: signal handling; git: uv resolves git-sourced deps; optional build steps may clone skills
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Full tree is required: workspace members (e.g. contrib/agentseek-schedule-sqlalchemy) must exist
# before `uv sync`, otherwise the first-layer-only lock+pyproject pattern fails.
COPY . /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN uv sync --frozen --no-dev

RUN chmod +x /app/entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/entrypoint.sh"]
