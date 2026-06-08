# Chat Model Integration Tests

After writing `chat_model.py`, you must write integration tests to verify the model class works correctly.

## Test Framework

Use `ChatModelIntegrationTests` from `langchain_tests` as the base class, and run tests with pytest.

Install dependencies:

```bash
pip install langchain-tests pytest python-dotenv
```

## Test File Structure

Place test files following standard unit test directory conventions:

```
src/<models_dir>/<model_name>/
├── __init__.py
├── chat_model.py
└── ...

tests/
└── test_chat_<model_name>.py
```

## Standard Test Class

For a new provider (e.g., Qwen, GLM), create a test class that inherits from `ChatModelIntegrationTests` and provides the following properties:

```python
from __future__ import annotations

import pytest
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_tests.integration_tests import ChatModelIntegrationTests

from models.qwen.chat_model import ChatQwen  # replace with the actual import path

load_dotenv()


class TestChatQwen(ChatModelIntegrationTests):
    @property
    def chat_model_class(self) -> type[BaseChatModel]:
        return ChatQwen

    @property
    def chat_model_params(self) -> dict:
        return {
            "model": "qwen-plus",
            "temperature": 0,
        }
```

### Required Properties

| Property | Description |
|----------|-------------|
| `chat_model_class` | Returns the chat model class under test. |
| `chat_model_params` | Parameters for creating an instance. Must include `model`; `temperature: 0` is recommended for deterministic results. |

## Running Tests

```bash
# Run tests for a single model
pytest tests/test_chat_<model_name>.py -v

# Skip tests marked as xfail (run only expected passes)
pytest tests/test_chat_<model_name>.py -v -m "not xfail"

# Run all model tests
pytest tests/ -v
```

## Common Issues

After setting up the test, you will likely encounter the following issues. Address them before concluding tests pass.

### Model package not importable

By default, the `<models_dir>/` directory is not installed as a Python package, so `from <models_dir>.xxx import ...` in tests will fail. Two changes are needed in `pyproject.toml`:

**1) Add build-system config:**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["<models_dir>"]
```

**2) Install in editable mode:**

```bash
uv pip install -e .
```

Without this, pytest fails with `ModuleNotFoundError: No module named '<models_dir>'`.

### Async tests not running (pytest-asyncio strict mode)

pytest-asyncio defaults to `Mode.STRICT`, which requires every async test to have an `@pytest.mark.asyncio` decorator. `langchain_tests` async methods lack this decorator.

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Without this, all async tests (`test_ainvoke`, `test_astream`, `test_abatch`, etc.) fail with "async def functions are not natively supported."
