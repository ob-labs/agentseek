---
title: Lifecycle v2 Service Discovery
type: reference
audience: [A2, A3, A5]
runs: no
verified_on: 2026-07-21
sources:
  - specs/lifecycle-v2-service-discovery.md
  - docs/adr/0001-versioned-template-catalog-boundary.md
---

# Lifecycle v2 Service Discovery

> **In short:** Lifecycle v2 is the accepted authored contract for describing
> services, their relationships, and safe user actions. AgentSeek projects it
> into deterministic JSON for Desktop and other machine consumers.

The canonical normative specification is
[Desktop Service Discovery and Lifecycle v2](https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md).
It is accepted for AgentSeek 0.1.0 and does not describe behavior available in
AgentSeek 0.0.5.

## Contract surfaces

| Surface | What the specification standardizes |
| --- | --- |
| Authored lifecycle v2 | Compact service identity, kind, display hint, primary service, references, and explicit relationship exceptions. |
| Normalized project model | One safe internal model projected from distinct lifecycle-v1 and lifecycle-v2 inputs. |
| `agentseek info --json` | Deterministic project, service, check, task, reference, and action metadata. |
| `agentseek doctor [--live] --json` | Typed static and live diagnostic results with stable identifiers and exit behavior. |
| Safety boundary | No commands, secrets, environment values, unsafe paths, or unsafe endpoints in public JSON. |
| Compatibility | Existing v1 projects remain loadable; v1 JSON is conservative and explicitly incomplete. |

Template ownership and release compatibility are recorded separately in
[ADR 0001](../adr/0001-versioned-template-catalog-boundary.md).

## Design discussion

Questions and design history belong in
[GitHub Discussion #133](https://github.com/ob-labs/agentseek/discussions/133).
Normative changes must be reflected in the canonical specification rather than
living only in discussion comments.
