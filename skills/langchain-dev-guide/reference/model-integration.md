# Model Integration Issues

## Issue 1: What problems arise from using ChatOpenAI directly?

For OpenAI-compatible models, the simplest approach is to reuse `ChatOpenAI` from `langchain-openai`. Using Qwen as an example:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="qwen-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)
```

This is the fastest way to get started, but in production it exposes the following issues:

- **`reasoning_content` (the thinking process) is silently dropped** — `_create_chat_result` and `_convert_chunk_to_generation_chunk` don't recognize this field, so neither streaming nor non-streaming responses surface the reasoning content.
- **The reasoning context is broken across multi-turn conversations** — `reasoning_content` in an AIMessage can't be sent back to the model. `_get_request_payload` doesn't handle `additional_kwargs["reasoning_content"]`, so subsequent turns lose the previous turn's reasoning chain.
- **An empty `tools: []` triggers provider errors** — some providers strictly validate empty arrays, but `ChatOpenAI` still sends the field even when no tools are bound.

So `ChatOpenAI` is suitable only for **quick verification** and **simple conversations without needing to display reasoning**. Once reasoning models or multi-turn reasoning chains are involved, a deeper adapter is needed.

## Issue 2: How to robustly integrate OpenAI-compatible reasoning models

To address the issues above, two approaches are recommended — pick one based on team preference.

### Approach 1: Use the langchain-cn-models skill to generate integration classes

Using the `langchain-cn-models` skill, generate (via AI Coding) an integration class that subclasses `BaseChatOpenAI` and fixes all critical methods in one shot:

```python
# Using Qwen as an example, the generated class fixes all the issues above:
from models.qwen import ChatQwen

llm = ChatQwen(model="qwen-max")
# reasoning_content automatically preserved, empty tools automatically removed, JSONDecodeError friendly hints
```

The generated integration class covers:

- `_get_request_payload`: reasoning_content round-tripping + removal of empty tools
- `_create_chat_result`: extracting reasoning_content from non-streaming responses
- `_convert_chunk_to_generation_chunk`: extracting reasoning_content from streaming deltas
- `_stream` / `_astream` / `_generate` / `_agenerate`: unified JSONDecodeError handling

**DeepSeek special path**: if `langchain-deepseek` is installed, the skill generates a subclass of the official class, only adding reasoning_content round-tripping while reusing the official implementation. Providers like Qwen with no official integration class inherit `BaseChatOpenAI` directly.

Suitable for: teams that want the adapter logic to live in their code repo, easy to read and customize.

### Approach 2: Use the third-party community library langchain-dev-utils

`langchain-dev-utils` is a third-party `langchain` ecosystem toolkit with built-in deep adapters for OpenAI-compatible models, removing the cost of hand-writing subclasses.

First install the standard version:

```bash
pip install -U langchain-dev-utils[standard]
```

#### 2.1 Dynamically generate integration classes via a factory function

Use the `create_openai_compatible_model` factory function to dynamically generate a chat model class at runtime:

```python
from langchain_dev_utils.chat_models.adapters import create_openai_compatible_model

ChatQwen = create_openai_compatible_model(
    model_provider="qwen",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    chat_model_cls_name="ChatQwen",
    compatibility_options={
        "supported_tool_choice": ["auto","none", "specific"],
        "supported_response_format": ["json_schema"],  # When enabled, with_structured_output defaults to json_schema
    },
)

model = ChatQwen(model="qwen3-max", reasoning_keep_policy="current")
```

Environment variables follow the `${PROVIDER_NAME}_API_BASE` / `${PROVIDER_NAME}_API_KEY` naming convention; omitting `base_url` reads them automatically.

The function is built on `BaseChatOpenAI`, with the main enhancements being:

- **Reasoning field extraction and round-tripping**: automatically parses `reasoning_content` / `reasoning`, with the `reasoning_keep_policy` (`never` / `current` / `all`) controlling how reasoning is retained in historical messages — fits Interleaved Thinking and Preserved Thinking.
- **tool_choice differential adaptation**: use `supported_tool_choice` to declare which strategies the provider supports; unsupported values are filtered out instead of being forwarded and triggering errors.
- **Dynamic structured-output selection**: based on `supported_response_format`, automatically pick the best strategy between `json_schema` and `function_calling`; declaring `json_schema` automatically sets `model.profile.structured_output` to `True`, integrated with `create_agent`.
- **video content_block support**: fills in the video-type multimodal capability missing from `ChatOpenAI`.
- **Model profiles**: pass a `profile` at creation or instantiation, so higher-level components like `create_agent` can sense model capabilities.

> **Note**: under the hood it uses pydantic `create_model`, which has dynamic-creation overhead, and the profiles dict is global. Create integration classes once at project startup to avoid repeated runtime regeneration.

#### 2.2 The registration-based style aligned with `init_chat_model`

The factory function in 2.1 requires the business side to explicitly hold a concrete class like `ChatQwen`. If you prefer LangChain's native `init_chat_model("provider:model")` "model by string" initialization style, `langchain-dev-utils` provides an equivalent experience — just use `register_model_provider` to register an OpenAI-compatible model under a unified entry point and set `chat_model` to `"openai-compatible"`. Internally it calls the `create_openai_compatible_model` above to build the integration class, and the business side no longer needs to reference the model class directly.

**Method 1: Pass arguments explicitly**

```python
from langchain_dev_utils.chat_models import register_model_provider

register_model_provider(
    provider_name="qwen",
    chat_model="openai-compatible",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
```

**Method 2: Via environment variables (recommended for config management)**

```bash
export QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
export QWEN_API_KEY=sk-xxx
```

```python
from langchain_dev_utils.chat_models import register_model_provider

register_model_provider(
    provider_name="qwen",
    chat_model="openai-compatible",
    # Auto-reads QWEN_API_BASE / QWEN_API_KEY
)
```

Parameters like `base_url`, `compatibility_options`, and `model_profiles` from `create_openai_compatible_model` are also passed through — usage is identical to calling the factory function directly:

```python
from langchain_dev_utils.chat_models import register_model_provider

register_model_provider(
    provider_name="qwen",
    chat_model="openai-compatible",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    compatibility_options={
        "supported_tool_choice": ["auto", "none","specific"],
        "supported_response_format": ["json_schema"],
    },
    model_profiles=model_profiles,
)
```

After registration, business code can initialize models through the unified entry point `load_chat_model("qwen:qwen3-max")` — this is the usage pattern aligned with `init_chat_model()`. The call sites no longer couple to specific class names, `base_url`, or `api_key`.