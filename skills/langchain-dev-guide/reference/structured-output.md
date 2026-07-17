# Structured Output Issues

A focused reference for `with_structured_output`, `response_format`, and provider-side schema enforcement.

## Issue 1: Unstable structured output, often returns None

- **Symptom**: Using `model.with_structured_output(schema)` or `create_agent(response_format=schema)` to get structured results occasionally returns `None`, an empty object, or missing fields. The same prompt can work on one run and fail on the next. The weaker the model (small-parameter, open source, quantized), the worse it gets.
- **Cause**: `with_structured_output` has three underlying implementations (`method`). By default most models go through `function_calling`, which means LangChain binds a schema-shaped tool and asks the model to emit structured data through a tool call. After binding, the model still has freedom to skip the tool, and weak models often answer in natural language instead. No tool call means the parser has nothing to deserialize, so the result becomes `None`.
- **Solution**: Raise reliability in this order. Fall back only when the previous tier is unsupported.

  - **First choice: provider-native `json_schema`**. The provider enforces schema conformance at the decoding layer. This is the most reliable approach:
  ```python
  structured_model = model.with_structured_output(MySchema, method="json_schema")
  ```

  - **Second choice: `function_calling` with forced tool selection**. If the provider does not support native schema decoding, keep `function_calling` but force the schema tool to be called:
  ```python
  model_with_tools = model.bind_tools([schema_tool], tool_choice="any")
  model_with_tools = model.bind_tools([schema_tool], tool_choice="schema_tool_name")
  ```

  - **Last resort: `json_mode` plus prompt-level constraints**. When the provider supports neither `json_schema` nor reliable forced tool calling, fall back to plain JSON generation. Spell out field names, types, and constraints in the prompt, and validate on the Python side:
  ```python
  structured_model = model.with_structured_output(MySchema, method="json_mode")
  ```

- **Lessons learned**:
  - When structured output is missing, suspect the model did not call the tool first, not a schema error. `include_raw=True` gives you both the raw `AIMessage` and the parsed object.
  - Reliability ranking from high to low: `json_schema` > `function_calling + tool_choice` > `json_mode + prompt`.
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

  If the model still behaves unreliably after removing `tool_choice`, fall back by capability:
  - If the provider supports native schema-constrained decoding, prefer `method="json_schema"`.
  - If it supports only plain JSON generation, fall back to `method="json_mode"` and enforce field constraints in the prompt plus Python-side validation.
- **Lessons learned**:
  - This failure mode is not "the schema is wrong" and not "tool calling is unsupported" in general. The narrower issue is that the backend rejects forced tool selection via `tool_choice`.
  - `ChatOpenAI` compatibility is only a transport-level starting point. Once you connect it to non-OpenAI providers, verify which OpenAI request parameters they actually support, especially for reasoning models.
  - When a provider says "`... does not support this tool_choice`", the fastest fix is usually model-level configuration (`disabled_params`) rather than patching LangChain source code.
  - Removing `tool_choice` trades reliability for compatibility. If outputs start coming back as `None`, see Issue 1 and downgrade to `json_schema` or `json_mode` based on provider capability.
