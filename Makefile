.PHONY: check-lock lint typecheck typecheck-langchain typecheck-oceanbase test-langchain test-oceanbase check-langchain check-oceanbase check-optional check-all

BASELINE_TY_PATHS = src tests contrib/agentseek-schedule-sqlalchemy/src contrib/agentseek-schedule-sqlalchemy/src/tests
LANGCHAIN_TY_PATHS = contrib/agentseek-langchain/src contrib/agentseek-langchain/tests contrib/agentseek-langchain/examples
OCEANBASE_TY_PATHS = contrib/agentseek-tapestore-oceanbase/src contrib/agentseek-tapestore-oceanbase/tests

BASELINE_PYTEST_PATHS = tests contrib/agentseek-schedule-sqlalchemy/src/tests
LANGCHAIN_PYTEST_PATHS = contrib/agentseek-langchain/tests
OCEANBASE_PYTEST_PATHS = contrib/agentseek-tapestore-oceanbase/tests

.PHONY: lock
lock: ## Update uv.lock against PyPI (ignore UV_INDEX_URL so lock stays canonical)
	@echo "🚀 Updating lock file against PyPI"
	@uv lock --default-index https://pypi.org/simple

.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync --all-packages
	@uv run pre-commit install

.PHONY: check
check: check-lock lint typecheck ## Run baseline code quality tools.

.PHONY: check-lock
check-lock:
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked

.PHONY: lint
lint:
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a

.PHONY: typecheck
typecheck: ## Run baseline static type checks.
	@echo "🚀 Static type checking: Running ty"
	@uv run ty check $(BASELINE_TY_PATHS)

.PHONY: test
test: ## Test the baseline code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules $(BASELINE_PYTEST_PATHS)

.PHONY: typecheck-langchain
typecheck-langchain: ## Run static type checks for the optional langchain plugin.
	@echo "🚀 Syncing optional langchain extra"
	@uv sync --extra langchain
	@echo "🚀 Static type checking: Running ty for langchain"
	@uv run ty check $(LANGCHAIN_TY_PATHS)

.PHONY: test-langchain
test-langchain: ## Run tests for the optional langchain plugin.
	@echo "🚀 Syncing optional langchain extra"
	@uv sync --extra langchain
	@echo "🚀 Testing code: Running pytest for langchain"
	@uv run python -m pytest $(LANGCHAIN_PYTEST_PATHS)

.PHONY: check-langchain
check-langchain: typecheck-langchain test-langchain ## Run checks for the optional langchain plugin.

.PHONY: typecheck-oceanbase
typecheck-oceanbase: ## Run static type checks for the optional oceanbase plugin.
	@echo "🚀 Syncing optional oceanbase extra"
	@uv sync --extra oceanbase
	@echo "🚀 Static type checking: Running ty for oceanbase"
	@uv run ty check $(OCEANBASE_TY_PATHS)

.PHONY: test-oceanbase
test-oceanbase: ## Run tests for the optional oceanbase plugin.
	@echo "🚀 Syncing optional oceanbase extra"
	@uv sync --extra oceanbase
	@echo "🚀 Testing code: Running pytest for oceanbase"
	@uv run python -m pytest $(OCEANBASE_PYTEST_PATHS)

.PHONY: check-oceanbase
check-oceanbase: typecheck-oceanbase test-oceanbase ## Run checks for the optional oceanbase plugin.

.PHONY: check-optional
check-optional: check-langchain check-oceanbase ## Run checks for optional plugins.

.PHONY: check-all
check-all: check check-optional ## Run baseline and optional plugin checks.

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: compose-up
compose-up: ## Build and start the SQLite-based app container with docker compose
	@docker compose up --build

.PHONY: compose-down
compose-down: ## Stop docker compose
	@docker compose down

.PHONY: compose-logs
compose-logs: ## Tail docker compose logs
	@docker compose logs -f

.PHONY: docker-build
docker-build: ## Build the container image
	@docker build -t agentseek:latest .

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
