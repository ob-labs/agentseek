---
name: langchain-cn-models
description: "Integrate Chinese LLM providers (DeepSeek, Qwen, GLM, etc.) into LangChain. Use when a developer asks to connect a Chinese model via LangChain or wire up a Chinese provider with langchain."
---

# LangChain CN Models

Help developers write LangChain integration classes for a specified Chinese model (e.g., Qwen, GLM, DeepSeek, Moonshot) using the OpenAI-compatible interface.

> [!CAUTION]
> **Never read, write, or access user configuration files such as `.env`, `.env.local`, `credentials.json`, or any other files that may contain secrets or sensitive information.** API Keys and other credentials must always be filled in by the user themselves — do not peek into or modify these files under any circumstances.

## Step 1: Gather Information

First, confirm the following details with the user:

1. **Model Name** — lowercase, e.g., `qwen`, `glm`, `deepseek`. Used for directory names, class names, and `_llm_type`.
2. **API Base URL** — the model's OpenAI-compatible endpoint URL.
3. **API Key Environment Variable Name** — e.g., `QWEN_API_KEY`.

If the user does not explicitly provide any of these, use reasonable defaults.

Additionally, inspect the project directory structure to determine the Python package manager (`uv.lock` → uv, `poetry.lock` → poetry, `requirements.txt` → pip, etc.).

## Step 2: Create Directory and Files

1. Create a top-level directory `<models_dir>/`.
2. Create a model subdirectory `<models_dir>/<model_name>/` with `model_name` in lowercase.
3. Keep the top-level `<models_dir>/__init__.py` empty.

```
<models_dir>/
├── __init__.py                   # empty
├── <model_name>/
│   ├── __init__.py
│   └── chat_model.py
└── ...
```

## Step 3: Check if DeepSeek

**If the model is DeepSeek**, first check whether `langchain-deepseek` is installed; install it if not. Then copy `chat_model.py` and `__init__.py` from `reference/deepseek/` into the target subdirectory. Skip all subsequent steps.

DeepSeek has an official integration `langchain_deepseek.ChatDeepSeek` whose `_get_request_payload` handles content list conversion and Azure `tool_choice` compatibility, but it does **NOT write back `reasoning_content`**. The code in `reference/` subclasses the official class, only overriding `_get_request_payload` to inject reasoning write-back logic. No other methods need overriding.

**If the model is another provider**, continue with the steps below.

## Step 4: Copy the Template

1. Check whether `langchain-openai` is installed; install it if not.
2. Copy `template/chat_model.py` into the target subdirectory.
3. Create `__init__.py`: `from .chat_model import <CHAT_CLASS_NAME>`

## Step 5: Replace Placeholders

Use grep to list all placeholders, then replace each one with the actual value:

| Placeholder | Description | Example (Qwen) |
|-------------|-------------|----------------|
| `ChatModel` | Class name | `ChatQwen` |
| `PROVIDER_API_KEY` | API Key env var name | `QWEN_API_KEY` |
| `PROVIDER_API_BASE` | API Base env var name | `QWEN_API_BASE` |
| `PROVIDER_API_BASE_URL` | Default API URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `chat-provider` | Model identifier for `_llm_type` | `chat-qwen` |
| `Provider` | Provider display name for error messages | `Qwen` |

Each placeholder is a standalone, complete token — simply do a global find-and-replace. Apply replacements in both `chat_model.py` and `__init__.py`.

## Step 6: Configure Model Profile (Optional)

Use `langchain-model-profiles` to download profile information for the model provider. `<provider_name>` is the provider name; try a few likely candidates.

1. Check whether `langchain-model-profiles` is installed; install it if not.
2. Run the download command:

```bash
langchain-profiles refresh --provider <provider_name> --data-dir ./<models_dir>/<model_name>/data
```

On success, a `data/_profiles.py` file is generated under the model directory, which is used by `_get_default_model_profile` in the template. If you cannot find the corresponding provider after several attempts, skip this step.

## Step 7: Write Integration Tests

After the model class is complete, you must write integration tests. See the detailed guide at [reference/integration-tests.md](reference/integration-tests.md).

> [!IMPORTANT]
> **Before running integration tests, you must remind the user to edit the `.env` file themselves and fill in the required API Key and other environment variables.**
>
> When running tests, you will likely encounter common setup issues (package not importable, async test mode, etc.). Refer to the "Common Issues" section at the end of [reference/integration-tests.md](reference/integration-tests.md) for fixes.
