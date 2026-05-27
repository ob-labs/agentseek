FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

EXPOSE {{ cookiecutter.gateway_port }}

CMD ["python", "-m", "{{ cookiecutter.project_slug }}"]
