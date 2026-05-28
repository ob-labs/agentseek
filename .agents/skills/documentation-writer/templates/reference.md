---
title: <Subject> reference
type: reference
audience: [A2, A3, A4]
runs: no                    # "yes" only if the page itself executes anything
verified_on: YYYY-MM-DD
sources:
  - <authoritative code file(s)>
---

# <Subject> reference

This page is a lookup, not a tutorial. Each entry mirrors a fact in the source files listed
above. If you see drift, treat the source as authoritative and file a doc bug.

## <Group 1>

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `<name>` | `<type>` | `<default>` | <one-line description> |

## <Group 2>

`<command>`
:   <one-line description>
    - **Flags:** `--foo`, `--bar`
    - **Defined in:** `path/to/file.py:LINE`
    - **Notes:** <edge cases, side effects, exit codes>

## Precedence

1. <Highest-precedence source>
2. <Next>
3. <Lowest>

## See also

- How-to: `../how-to/<page>.md`
- Explanation: `../explanation/<page>.md`
