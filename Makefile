.PHONY: \
	lock install check check-lock lint typecheck test \
	check-contrib check-all build clean-build publish build-and-publish \
	docs-test docs compose-up compose-down compose-logs docker-build help

CORE_TY_PATHS = src tests
CONTRIB_DIRS = $(sort $(dir $(wildcard contrib/agentseek-*/pyproject.toml)))
contrib_name = $(patsubst contrib/agentseek-%,%,$(patsubst %/,%,$(1)))
CONTRIB_CHECKS = $(foreach dir,$(CONTRIB_DIRS),check-$(call contrib_name,$(dir)))

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
	@uv run ty check $(CORE_TY_PATHS)

.PHONY: test
test: ## Test the baseline code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules

define define_contrib_targets
.PHONY: typecheck-$(1) test-$(1) check-$(1)

typecheck-$(1): sync-contrib ## Run static type checks for the $(1) contrib package.
	@dir="$(2)"; \
	paths=$$$$(for path in src tests examples; do if [ -e "$$$$dir/$$$$path" ]; then printf '%s ' "$$$$dir/$$$$path"; fi; done); \
	test -n "$$$$paths" || { echo "No typecheck paths found for $$$$dir" >&2; exit 1; }; \
	echo "🚀 Static type checking: Running ty for $(1)"; \
	uv run ty check $$$$paths

test-$(1): sync-contrib ## Run tests for the $(1) contrib package.
	@dir="$(2)"; \
	paths=$$$$(for path in tests src/tests; do if [ -e "$$$$dir/$$$$path" ]; then printf '%s ' "$$$$dir/$$$$path"; fi; done); \
	test -n "$$$$paths" || { echo "No test paths found for $$$$dir" >&2; exit 1; }; \
	echo "🚀 Testing code: Running pytest for $(1)"; \
	uv run python -m pytest $$$$paths

check-$(1): typecheck-$(1) test-$(1) ## Run checks for the $(1) contrib package.
endef

$(foreach dir,$(CONTRIB_DIRS),$(eval $(call define_contrib_targets,$(call contrib_name,$(dir)),$(patsubst %/,%,$(dir)))))

.PHONY: sync-contrib
sync-contrib: ## Sync dependencies for all contrib packages.
	@echo "🚀 Syncing dependencies for contrib packages"
	@uv sync --all-packages

.PHONY: check-contrib
check-contrib: $(CONTRIB_CHECKS) ## Run checks for contrib packages.

.PHONY: check-all
check-all: check check-contrib ## Run baseline and contrib package checks.

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
	entries = []; \
	seen = set(); \
	[entries.extend(re.findall(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', open(makefile).read(), re.M)) for makefile in '$(MAKEFILE_LIST)'.strip().split()]; \
	[entries.append((f'{prefix}-{directory.removeprefix(\"contrib/agentseek-\").removesuffix(\"/\")}', template.format(name=directory.removeprefix('contrib/agentseek-').removesuffix('/')))) for directory in '$(CONTRIB_DIRS)'.split() for prefix, template in [('typecheck', 'Run static type checks for the {name} contrib package.'), ('test', 'Run tests for the {name} contrib package.'), ('check', 'Run checks for the {name} contrib package.')]]; \
	[(seen.add(target), print(f'\033[36m{target:<20}\033[0m {description}')) for target, description in entries if target not in seen]"

.DEFAULT_GOAL := help
