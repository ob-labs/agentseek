FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null \
    || pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["python", "-m", "{{ cookiecutter.project_slug }}"]
