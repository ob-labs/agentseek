# Structured Output Issues

A focused reference for `with_structured_output`, `response_format`, and provider-side schema enforcement.

## Choose the API path first

LangChain exposes two related but different structured-output APIs. Diagnose and configure the one the application actually uses:

- **Model wrapper — `model.with_structured_output(...)`**: the model integration selects a steering method such as `json_schema`, `function_calling`, or `json_mode`, then parses the model response into the requested schema. Defaults vary by integration and version, so set `method` explicitly when behavior matters.
- **Agent — `create_agent(response_format=...)`**: passing a schema directly lets the agent select `ProviderStrategy` when the model profile advertises native structured output, or `ToolStrategy` otherwise. These agent strategies include agent-loop behavior such as validation and retry; they are not aliases for the model wrapper's `method` argument.

Use the automatic agent strategy when the model profile is accurate:

```python
agent = create_agent(
    model=model,
    tools=tools,
    response_format=MySchema,
)
```

Force a strategy only when provider capability is known and the automatic choice is unsuitable:

```python
from langchain.agents.structured_output import ProviderStrategy, ToolStrategy

native_agent = create_agent(
    model=model,
    tools=tools,
    response_format=ProviderStrategy(MySchema),
)

tool_agent = create_agent(
    model=model,
    tools=tools,
    response_format=ToolStrategy(MySchema),
)
```

## Issue 1: Unstable structured output, often returns None

- **Symptom**: `model.with_structured_output(schema)` returns `None`, an empty object, missing fields, or a parsing error. The same prompt can work on one run and fail on the next. Small, open-source, or quantized models tend to be less reliable with complex schemas.
- **Cause**: The cause depends on the configured method and provider capability:
  - With provider-native structured output, the provider may reject an unsupported schema or model before generation.
  - OpenAI-family `with_structured_output(..., method="function_calling")` binds the schema as a tool and **forces the schema tool** by passing its name as `tool_choice`. When the provider supports and honors forced selection, the model is not free to answer in prose instead.
  - If an adapter strips or ignores `tool_choice` — for example through `disabled_params={"tool_choice": None}` — the model is again **free to skip the schema tool**. A natural-language answer then gives the tool parser nothing to deserialize, so the parsed result can be `None`.
  - A returned tool call can still fail schema validation because its arguments are malformed, incomplete, or have the wrong types.
- **Solution**:

  1. **Inspect the raw response before changing methods.** `include_raw=True` separates "no schema tool call" from "tool call failed validation":

  ```python
  structured_model = model.with_structured_output(
      MySchema,
      method="function_calling",
      include_raw=True,
  )
  result = structured_model.invoke(prompt)

  print(result["raw"].tool_calls)
  print(result["parsed"])
  print(result["parsing_error"])
  ```

  2. **Choose a model-level method by documented provider capability.** There is no universal fallback order that works for every integration:

  - Prefer provider-native `json_schema` when the selected model and provider document schema-constrained output:

  ```python
  structured_model = model.with_structured_output(MySchema, method="json_schema")
  ```

  - Use `function_calling` when the provider supports tool calling and forced `tool_choice`. Keep `with_structured_output` so LangChain both binds the schema tool and attaches the output parser:

  ```python
  structured_model = model.with_structured_output(
      MySchema,
      method="function_calling",
  )
  ```

  Calling `bind_tools` directly returns an `AIMessage` with tool calls; it does not provide the schema parsing performed by `with_structured_output`.

  - Use `json_mode` when the provider guarantees JSON syntax but not schema conformance. Spell out field names, types, and constraints in the prompt, then validate and retry in application code:

  ```python
  structured_model = model.with_structured_output(MySchema, method="json_mode")
  ```

  3. **Configure agents through agent strategies.** For `create_agent`, use a direct schema for automatic selection, `ProviderStrategy` for known native support, or `ToolStrategy` for tool-based structured output and its validation-retry loop. Do not diagnose `create_agent(response_format=...)` solely through the model wrapper's three `method` values.

- **Lessons learned**:
  - Check `raw.tool_calls` and `parsing_error` before deciding whether the failure is tool selection or schema validation.
  - Provider-native schema enforcement is usually the strongest option when the exact model supports it, but capability must be verified rather than inferred from OpenAI-compatible transport alone.
  - Weak model + complex schema is the most failure-prone combination. Split large schemas into smaller calls when possible.

## Issue 2: `with_structured_output(..., method="function_calling")` fails because the model does not support `tool_choice`

- **Symptom**: Calling `model.with_structured_output(schema)` or `model.with_structured_output(schema, method="function_calling")` raises a provider-side 400 error like "`<model>` does not support this `tool_choice`". This often happens with `ChatOpenAI`-style integrations or derived classes such as `ChatDeepSeek` against OpenAI-compatible providers. A typical example is `deepseek-v4-flash` in thinking mode: it supports tool calling but rejects forced `tool_choice`.
- **Cause**: For `function_calling`, LangChain's OpenAI-family chat models try to make structured output more reliable by forcing the schema tool to be called. Internally, `with_structured_output` binds the schema as a tool and usually passes `tool_choice=<schema_tool_name>`. That works for providers that support forced tool selection, but some OpenAI-compatible backends only allow free-form tool calling and reject explicit `tool_choice`. When you access those models through `ChatOpenAI`, `ChatDeepSeek`, or another subclass inheriting the same behavior, the adapter forwards `tool_choice` and the provider errors before generation starts.
- **Solution**: Disable forwarding of `tool_choice` for that model instance, so LangChain still binds the schema tool but does not send the unsupported parameter:

  ```python
  from langchain_deepseek import ChatDeepSeek
  from pydantic import BaseModel

  class User(BaseModel):
      name: str
      age: int

  model = ChatDeepSeek(
      model="deepseek-v4-flash",
      disabled_params={"tool_choice": None},
      extra_body={"thinking": {"type": "enabled"}},
  )

  structured_model = model.with_structured_output(
      User,
      method="function_calling",
  )

  print(structured_model.invoke("My name is John and I am 25 years old."))
  ```

  Why this works: OpenAI-family integrations call `_filter_disabled_params(...)` before building the final payload. Setting `disabled_params={"tool_choice": None}` tells the adapter to strip that field entirely whenever it would have been sent.

  Removing forced selection restores compatibility but also makes the model free to skip the schema tool. Use `include_raw=True` to detect that case and choose another method by capability:
  - If the provider documents native schema-constrained decoding for this model, use `method="json_schema"`.
  - If it supports only JSON syntax enforcement, use `method="json_mode"`, describe the schema in the prompt, and validate plus retry in application code.
  - If neither is available, keep unforced `function_calling` only with an explicit retry or repair path for missing tool calls.
- **Lessons learned**:
  - This failure mode is not "the schema is wrong" and not "tool calling is unsupported" in general. The narrower issue is that the backend rejects forced tool selection via `tool_choice`.
  - `ChatOpenAI` compatibility is only a transport-level starting point. Once you connect it to non-OpenAI providers, verify which OpenAI request parameters they actually support, especially for reasoning models.
  - When a provider says "`... does not support this tool_choice`", the fastest fix is usually model-level configuration (`disabled_params`) rather than patching LangChain source code.
  - Removing `tool_choice` trades reliability for compatibility. If outputs start coming back as `None`, see Issue 1 and switch to `json_schema`, `json_mode`, or an explicit retry path based on provider capability.
