---
title: "ADR 0001: Versioned Template Catalog Boundary"
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-07-28
sources:
  - src/agentseek/cli/commands/create.py
  - templates/index.json
  - pyproject.toml
---

# ADR 0001: Versioned Template Catalog Boundary

## Status

Accepted on 2026-07-28.

## Context

AgentSeek has two distinct template inputs:

- A catalog is an AgentSeek repository containing `templates/index.json` and
  its registered template directories.
- A direct Cookiecutter source is a positional HTTPS URL or absolute local path
  supplied by the user.

The catalog supplies AgentSeek template names, listing, filtering, descriptions,
and generation. A direct source retains Cookiecutter's existing passthrough
behavior. Treating the two forms as interchangeable would make selection and
cache reuse ambiguous.

## Decision

### Explicit catalog override

`--template-repo <https-url>` selects an explicit AgentSeek catalog repository.
It applies only to a repository with `templates/index.json`; it is not a general
Cookiecutter source option. The option requires
`--checkout <40-character-lowercase-commit-sha>`. The commit value must match
`[0-9a-f]{40}`; branches, tags, abbreviated SHAs, and uppercase SHAs are
rejected for this form.

The explicit repository and exact commit are the catalog coordinate. All
catalog operations use that same coordinate:

| Operation | Source when `--template-repo` is present |
| --- | --- |
| List | Registry at the explicit repository and commit. |
| Filter | Registry at the explicit repository and commit. |
| Describe | Registry and template metadata at the explicit repository and commit. |
| Create | Selected template at the explicit repository and commit. |

The override takes precedence over the bundled catalog for catalog operations.
An explicit repository, checkout, registry, or template failure is an error. It
never falls back to bundled templates, a local core checkout, or another
revision.

### Direct Cookiecutter sources

The positional `agentseek create <url-or-absolute-path>` form remains a direct
Cookiecutter passthrough. For that form, `--checkout` retains its existing
Cookiecutter meaning and may name a branch, tag, or commit.

`--template-repo` cannot be combined with a positional direct Cookiecutter URL
or absolute path. AgentSeek rejects the combination instead of choosing one
source implicitly. Named catalog templates, including interactive selection,
remain catalog operations.

### Cache and trust boundary

An explicit catalog cache entry is identified by the normalized repository URL
and exact commit. AgentSeek validates matching metadata before reusing it;
partial, stale, or mismatched entries are not valid cache hits.

The catalog is executable template content. Generation trusts that content and
may execute Cookiecutter hooks. Listing and describing are inspection-only
operations and do not execute Cookiecutter hooks.

### Generated-project source

The template catalog supplies template files only. Generated projects keep
`_agentseek_source_url` bound to the AgentSeek core repository, never the
selected template catalog repository.

## Consequences

- A caller can reproduce catalog selection with an HTTPS URL and immutable
  commit.
- Catalog discovery and generation cannot observe different repository
  revisions in the same invocation.
- An explicit catalog error remains visible instead of silently changing the
  generated project.
- Direct Cookiecutter URLs and absolute paths remain available outside the
  AgentSeek catalog contract.
- Catalog authors are trusted at generation time; users inspect untrusted
  catalogs through list or describe without executing their hooks.

## Out of scope

This decision does not move templates or skills, change the bundled catalog
coordinate, or introduce a mutable catalog update channel.

## Related

- [CLI Reference](../reference/cli.md)
- [Templates](../reference/templates.md)
