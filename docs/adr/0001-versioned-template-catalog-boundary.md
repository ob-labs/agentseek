---
title: "ADR 0001: Versioned Standalone Template Catalog"
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-07-21
sources:
  - src/agentseek/cli/commands/create.py
  - templates/index.json
  - pyproject.toml
  - skills/README.md
  - src/skills/README.md
  - specs/lifecycle-v2-service-discovery.md
---

# ADR 0001: Use a Versioned Standalone Template Catalog

> **In short:** AgentSeek 0.1.0 will load lifecycle-v2 templates from a
> version-pinned standalone repository. The core repository will retain its
> existing lifecycle-v1 templates so released 0.0.x clients remain functional.
> Public skills will move separately; packaged built-in skills remain in core.

## Status

Accepted on 2026-07-21 for the AgentSeek 0.1.0 delivery sequence.

| Attribute | Record |
| --- | --- |
| Scope | Bundled template ownership, resolution, compatibility, and release sequencing. |
| Supersedes | None. This is the first recorded decision for template extraction. |
| Review triggers | A mutable catalog, a non-GitHub source, removal of the legacy v1 paths, or extraction of packaged built-in skills. |

This record governs template distribution and repository ownership. The
separate lifecycle-v2 service-discovery specification governs lifecycle TOML,
normalization, and public JSON semantics.

## Baseline recorded at decision time

This decision is based on published AgentSeek v0.0.1 through v0.0.5 behavior;
v0.0.5 was current when the decision was accepted. The tag links are immutable
evidence rather than descriptions of the future implementation.

- The released package version is
  [`0.0.5`](https://github.com/ob-labs/agentseek/blob/v0.0.5/pyproject.toml#L1-L4).
- Bundled template resolution hard-codes the core repository URL and
  `templates/` directory in
  [`create.py`](https://github.com/ob-labs/agentseek/blob/v0.0.5/src/agentseek/cli/commands/create.py#L76-L81).
- Installed clients reuse a complete cache. A cold or incomplete cache clones
  that repository with an optional checkout; when the caller supplies none, the
  default branch is used, as recorded in the
  [0.0.5 resolver](https://github.com/ob-labs/agentseek/blob/v0.0.5/src/agentseek/cli/commands/create.py#L223-L248).
- The core registry contains eleven public template keys in
  [`templates/index.json`](https://github.com/ob-labs/agentseek/blob/v0.0.5/templates/index.json).
- The additional `bub/contextseek` directory is deliberately quarantined and
  absent from that registry, as recorded by the
  [0.0.5 quarantine set](https://github.com/ob-labs/agentseek/blob/v0.0.5/src/agentseek/cli/commands/create.py#L81-L82).
- The wheel includes `src/skills/`, while top-level `skills/` is the public
  install surface. These are already distinct distribution boundaries in
  [`pyproject.toml`](https://github.com/ob-labs/agentseek/blob/v0.0.5/pyproject.toml#L60-L71)
  and the [public skills guide](https://github.com/ob-labs/agentseek/blob/v0.0.5/skills/README.md).

Unless an explicitly reviewed v1 compatibility fix lands before the copy, the
initial catalog source baseline is core commit
`e1953217fbe629a2ca67c3632575c22a7ba493d9` (`v0.0.5`). The actual
`catalog-origin.json` in the standalone release is authoritative.

The published backward-compatibility set is exactly v0.0.1 through v0.0.5. It
contains three resolver generations:

| Released clients | Resolver behavior | Required compatibility fixture |
| --- | --- | --- |
| v0.0.1, v0.0.2 | Cookiecutter receives the core repository plus a remote template `directory`; installed remote listing was not available. | With an isolated home, no source checkout, and an empty Cookiecutter cache, create a representative bundled template for every framework, then verify the rendered lifecycle with the frozen v1 contract. Preserve the historical installed-listing behavior. |
| v0.0.3, v0.0.4 | AgentSeek prepares a cached core repository root before listing or creation. | From an empty cache, list and create a representative template for every framework, then repeat from the warm cache; every generated lifecycle remains v1. |
| v0.0.5 | AgentSeek reuses only a complete cache and repairs an incomplete one. | Run the cold- and warm-cache cases, then corrupt the cache and prove listing and creation recover to valid lifecycle-v1 templates. |

These fixtures execute the released artifacts, not current source with a
simulated version. They preserve behavior those releases actually provided;
they do not invent remote listing for v0.0.1 or v0.0.2.

The immutable resolver evidence is the tagged
[v0.0.1](https://github.com/ob-labs/agentseek/blob/v0.0.1/contrib/agentseek-cli/src/agentseek_cli/commands/create.py#L136-L155),
[v0.0.2](https://github.com/ob-labs/agentseek/blob/v0.0.2/contrib/agentseek-cli/src/agentseek_cli/commands/create.py#L136-L155),
[v0.0.3](https://github.com/ob-labs/agentseek/blob/v0.0.3/src/agentseek/cli/commands/create.py#L181-L205),
[v0.0.4](https://github.com/ob-labs/agentseek/blob/v0.0.4/src/agentseek/cli/commands/create.py#L181-L205),
and [v0.0.5](https://github.com/ob-labs/agentseek/blob/v0.0.5/src/agentseek/cli/commands/create.py#L223-L248)
implementations.

## Context

AgentSeek templates currently live in the core repository under `templates/`.
An installed CLI that cannot find local templates prepares a cached checkout of
`https://github.com/ob-labs/agentseek` and reads `templates/index.json` from that
checkout. A complete existing cache is reused; on a cold or incomplete cache,
and without an explicit `--checkout`, released AgentSeek 0.0.x clients clone the
repository's mutable default branch.

Lifecycle v2 adds authored fields and validation rules that AgentSeek 0.0.x
does not understand. Replacing the existing lifecycle files on the default
branch would therefore break fresh or cache-recovering 0.0.x installations:
they could download a v2 template, generate a project, and then reject that
project as an unsupported lifecycle version.

AgentSeek also plans to separate templates and public skills from core. That
future direction creates an opportunity to solve the compatibility problem
with a durable repository boundary instead of conditional template files or a
second temporary template tree inside core.

## Decision drivers

- Published AgentSeek v0.0.1 through v0.0.5 installations must retain their
  released listing behavior and cold-cache bundled creation must continue
  producing valid lifecycle-v1 projects.
- AgentSeek 0.1.0 must accept existing v1 projects and provide complete
  lifecycle-v2 discovery for newly generated projects.
- A released CLI must resolve a reproducible template catalog, not mutable
  `main` content.
- Template download or cache failure must not silently change lifecycle
  semantics.
- Template development should be independently releasable without coupling all
  template files to the core package.
- The 0.1.0 release must not also absorb the unrelated public-skills migration
  or the core organization transfer.
- Public repository content and packaged runtime content need distinct owners
  and compatibility policies.

## Decision

### Repository responsibilities

The repositories have these responsibilities:

| Repository | Responsibility in 0.1.0 |
| --- | --- |
| `ob-labs/agentseek` | CLI and lifecycle runtime, specifications, JSON contracts, catalog client, and the frozen legacy v1 template mirror. A later transfer may make `agentseek-ai/agentseek` canonical. |
| `agentseek-ai/agentseek-templates` | Authoritative lifecycle-v2 template catalog, registry, template CI, and immutable catalog releases. |
| Future `agentseek-ai/agentseek-skills` | Public, independently installable skills currently represented by top-level `skills/`. It is outside the 0.1.0 scope. |

The packaged `src/skills/` directory remains in core. Those skills ship with
the AgentSeek distribution and support core lifecycle behavior. They are not
the same surface as independently installed public skills.

### Legacy v1 catalog

The current core `templates/` tree and `templates/index.json` remain on the
core default branch as the lifecycle-v1 compatibility catalog.

- Existing paths and registry keys remain valid for AgentSeek 0.0.x.
- Normal feature development stops in this mirror after 0.1.0 preparation.
- Only security fixes and critical compatibility fixes are backported.
- A backport must preserve lifecycle version 1 and remain renderable by the
  released 0.0.x CLI.
- There is no scheduled deletion date. Removing or changing these paths
  requires a superseding ADR that explicitly accepts or avoids the resulting
  break for already released clients.

This retained mirror is intentional compatibility infrastructure, not the
authoritative source for new template development.

### Standalone v2 catalog

The standalone repository owns the lifecycle-v2 source for every registered
template. It preserves the familiar layout:

```text
templates/
  index.json
  bub/<name>/cookiecutter.json
  deepagents/<name>/cookiecutter.json
  langchain/<name>/cookiecutter.json
```

Its CI renders every registered template, validates the rendered lifecycle
file, and rejects registry entries whose template content is missing or
incomplete. Before 0.1.0 is public, that validation installs the reviewed core
`core_commit` paired with the candidate catalog. After publication, the catalog
also tests the lowest supported released AgentSeek version for its release line;
for the initial lifecycle-v2 catalog, that version is AgentSeek 0.1.0.

The initial standalone catalog is copied from the core templates and migrated
to lifecycle v2. It is a copy-then-freeze transition: the v1 core mirror is not
deleted when the v2 repository becomes authoritative.

The initial migration set is exactly the registered keys in the source
`templates/index.json`, not every directory that happens to exist under
`templates/`. The quarantined, unregistered `bub/contextseek` source remains in
the core v1 mirror and is excluded from the first standalone registry until it
passes an independent remediation and registration review.

The first standalone release includes `catalog-origin.json` with schema version
1, the source core repository, full source commit SHA, SHA-256 digest of the
exact source-registry bytes as lowercase hexadecimal, sorted included keys, and
excluded template paths with reasons. This provenance record changes only when
a later catalog release imports material from another source; it is not used as
a runtime resolver.

Each registered template subtree is self-contained. Rendering may not require a
file outside that template's directory, and the catalog rejects escaping
relative paths or symlinks. Cross-template assets must be copied into each
subtree unless a later catalog contract defines a separately extracted shared
asset area.

### Catalog lock in core

The AgentSeek wheel embeds a catalog lock. The lock contains, at minimum:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `1` for the initial lock format. |
| `catalog_repository` | Exact HTTPS repository URL for the standalone catalog. |
| `catalog_commit` | Full 40-character lowercase Git commit SHA. |
| `catalog_release` | Protected release tag that permanently retains `catalog_commit`; informational at runtime. |
| `templates_root` | Repository-relative `templates` directory. |
| `index_path` | Repository-relative `templates/index.json` path. |
| `lifecycle_version` | Integer `2`. |
| `core_repository` | Exact HTTPS Git URL containing generated-project `contrib/` dependencies. |
| `core_commit` | Full 40-character lowercase Git commit SHA compatible with the catalog release. |
| `core_release` | Protected dependency-snapshot tag that permanently retains `core_commit`; informational at runtime. |
| `templates` | Registry snapshot used for offline listing and selection. |

`catalog_commit` is authoritative for template content. `core_commit` is
authoritative for generated-project dependencies. The catalog and core release
tags provide human-readable names and retain reachability, but the CLI never
resolves content by tag.

Release validation compares the embedded registry snapshot with
`templates/index.json` at `catalog_commit`. A mismatch blocks the core release.
The lock must not contain credentials or a mutable branch name.

### Catalog source and generated dependency source

The catalog repository and generated-project dependency repository are separate
coordinates. The standalone repository supplies Cookiecutter source files. It
does not supply core `contrib/` packages referenced by generated projects.

For bundled templates, AgentSeek injects the locked `core_repository` and
`core_commit` as internal Cookiecutter context. The v2 catalog carries distinct
`_agentseek_source_url` and `_agentseek_source_ref` variables, and generated Git
dependencies use both the core URL and exact revision. Catalog coordinates are
never substituted into these fields.

`core_commit` may identify a reviewed pre-release commit that contains the
compatible `contrib/` packages; it need not be the later merge commit that only
updates the final catalog lock. Before the catalog release, `core_release` must
be created as a protected permanent tag at that commit. Cross-repository tests
must render and install representative generated projects from the recorded
pair.

A local core dependency path is an explicit development override. AgentSeek
0.1.0 does not infer that dependency source from the location of a downloaded
template or silently replace the locked core coordinate.

### Template resolution

AgentSeek 0.1.0 resolves bundled templates as follows:

1. Read the embedded catalog lock.
2. Resolve the requested registry key from the embedded snapshot.
3. Reuse a complete cache entry only when its catalog repository, catalog
   commit, template key, and catalog-lock digest all match.
4. Otherwise download the standalone repository archive at the locked commit.
5. Extract only the requested template subtree into a new cache entry.
6. Validate the cached template before invoking Cookiecutter.

The catalog-lock digest is the lowercase hexadecimal SHA-256 of the exact
packaged lock-file bytes.

GitHub archive endpoints transfer a repository archive, not a server-side
subtree. AgentSeek may filter extraction to the selected template, but it must
not describe the network transfer as downloading only that directory.

Bundled-name resolution uses the locked standalone catalog even when AgentSeek
runs from a core source checkout. The local core `templates/` tree no longer
takes automatic precedence because it is the frozen v1 compatibility mirror.
Developers select a local template through the existing explicit absolute-path
Cookiecutter passthrough.

The existing external URL and absolute-path Cookiecutter passthrough remains
separate from bundled-catalog resolution. For an external URL, `--checkout`
continues to be passed to Cookiecutter. For a bundled template, `--checkout
<ref>` remains an explicit development override but now selects a ref from the
standalone catalog repository. AgentSeek resolves that ref to a commit, reads
the registry and template from the same resolved commit, and uses a separate
cache entry. It never combines the embedded registry snapshot with overridden
template files, and the override never selects the legacy core mirror.

### Cache and archive security

Catalog extraction and reuse follow these rules:

- Cache identity includes the catalog repository and exact catalog commit; a
  cache created from mutable `main` cannot satisfy the locked catalog.
- A complete entry includes `cookiecutter.json`, a generated-project source
  tree, and catalog metadata matching the lock.
- Downloads use HTTPS, bounded time, a maximum 64 MiB compressed response, no
  more than 10,000 archive members, no member larger than 32 MiB, and no more
  than 256 MiB total uncompressed content.
- Archive entries with absolute paths, traversal segments, device types,
  hardlinks, or escaping symbolic links are rejected.
- Extraction occurs in a temporary directory and becomes visible in the cache
  only after validation succeeds.
- An interrupted or incomplete cache entry is never treated as reusable.
- Failure to obtain the locked v2 catalog is an explicit error. AgentSeek does
  not silently fall back to core v1 templates or mutable `main`.

These rules extend the existing incomplete-cache recovery guarantee rather
than replacing it.

### Repository retention and availability

The standalone catalog and core dependency source are anonymously readable.
Every catalog or core dependency commit embedded in a released AgentSeek lock
remains reachable through its protected release tag, which is never moved or
deleted. Release verification fetches the catalog archive and core dependencies
by their exact locked URLs and SHAs in a clean environment without repository
credentials.

If either repository is renamed, transferred, or archived, the URL in every
supported released lock must continue resolving or redirect to equivalent
immutable content. SHA immutability alone is insufficient if a repository or
commit becomes unavailable.

### Compatibility contract

| Consumer | Template source | Generated lifecycle | Required behavior |
| --- | --- | --- | --- |
| AgentSeek v0.0.1-v0.0.5 | Core default-branch `templates/` or an existing compatible cache | v1 | Preserve each release's actual listing/cache behavior; bundled creation continues rendering v1, and lifecycle commands retain their released behavior. |
| AgentSeek 0.1.0 | Standalone repository at `catalog_commit` | v2 | Complete normalized discovery and JSON actions are available. |
| AgentSeek 0.1.0 opening an existing project | Project-local lifecycle file | v1 or v2 | V1 remains operational with conservative incomplete JSON metadata; v2 is complete. |
| Direct use of a legacy core template | Core `templates/` path | v1 | Remains valid but receives no normal feature development. |
| Explicit external Cookiecutter source | User-selected source | Source-defined | Existing passthrough behavior remains; the source is outside the bundled catalog guarantee. |

The core repository may later transfer from `ob-labs` to `agentseek-ai`, but
the old GitHub URL and default-branch template paths must continue resolving
for 0.0.x clients. The organization transfer is not required for 0.1.0.

The compatibility invariants are therefore:

1. The core default-branch catalog remains lifecycle v1 for published v0.0.1
   through v0.0.5 clients.
2. The 0.1.0 bundled catalog resolves by an exact standalone-repository commit.
3. A 0.1.0 catalog failure never falls back to the legacy mirror or mutable
   branch content.
4. AgentSeek 0.1.0 continues loading existing project-local lifecycle v1 files.
5. Repository transfer or archival must preserve the old core URL and template
   paths for already released clients, plus every standalone catalog URL and
   commit embedded in a supported release.
6. Every core dependency URL and commit embedded in a supported lock remains
   anonymously fetchable for generated-project installation.

### Skills boundary

The template extraction does not imply a simultaneous skills extraction.

- Top-level `skills/` contains public, independently installable material and
  may move to `agentseek-ai/agentseek-skills` under a later ADR.
- `src/skills/` is included in the core package and remains versioned with the
  CLI until a separate package and compatibility contract exists.
- Template references to public skills use stable installation coordinates;
  they do not import files from the core checkout by relative path.

This distinction prevents the 0.1.0 release from treating all directories named
`skills` as one deployment unit.

## Release sequence

The 0.1.0 work proceeds in this order:

1. Merge the lifecycle-v2 contract and this ADR.
2. Add v1/v2 authored loading, strict v2 validation, and safe normalization to
   core while retaining existing human v1 behavior.
3. Add typed diagnostics and versioned `info --json` and
   `doctor [--live] --json` output.
4. Create `agentseek-ai/agentseek-templates`, copy the registered source
   inventory, record its provenance, migrate the copy to lifecycle v2, and
   establish template-owned CI.
5. Add the locked standalone-catalog client to core, select the paired core
   dependency commit, create its protected dependency-snapshot tag, and verify
   both candidate coordinates.
6. Release the template catalog first and record its immutable commit.
7. Update the core catalog lock to that commit, run cross-repository release
   verification, and merge the core `release/0.1.0` PR.
8. Tag the verified core merge commit as `v0.1.0`, publish the package, deploy
   documentation, and run a fresh installation smoke test.

`catalog_release` and `core_release` may carry readable independent names, but
the lock always uses the exact catalog and core SHAs. The later core package tag
`v0.1.0` is a separate release surface.

## Required review boundaries

The delivery may use more than one PR per row, but these concerns must remain
independently reviewable and preserve this dependency order:

| Boundary | Repository | Must establish |
| --- | --- | --- |
| Contract | Core | Lifecycle-v2 specification, public documentation entry point, and this ADR. |
| Runtime compatibility | Core | Distinct v1/v2 authored models, safe normalization, and unchanged human v1 behavior. |
| Machine contract | Core | Typed diagnostics plus versioned `info --json` and `doctor --json` output. |
| Catalog bootstrap | Templates | Copied and migrated v2 catalog, registry, rendering tests, and release metadata. |
| Catalog client | Core | Embedded lock, safe archive/cache handling, and immutable resolution. |
| Catalog release | Templates | A tested release whose full commit SHA is recorded for core. |
| Core release | Core | `release/0.1.0` pinning that commit, synchronized version surfaces, and release smoke tests. |

An implementation may reuse archive-download work proposed in
[PR #136](https://github.com/ob-labs/agentseek/pull/136), but only after adapting
it to the standalone repository, immutable lock, extraction confinement, and
no-fallback rules in this record.

## Cross-repository release gates

The 0.1.0 release is blocked unless all of these are true:

- every standalone registry entry exists and renders;
- every rendered standalone template loads as lifecycle v2;
- every registry-listed core compatibility template still renders and loads as
  lifecycle v1, and quarantined sources retain their existing quarantine;
- the standalone provenance record matches the reviewed source registry and
  records every included or excluded source;
- the v0.0.1-v0.0.5 resolver-generation fixture matrix passes from isolated
  cold, warm, and intentionally incomplete caches as applicable;
- AgentSeek 0.1.0 resolves the locked standalone commit without mutable
  fallback;
- a clean, unauthenticated environment can fetch the archive from the exact
  locked catalog URL and SHA, and the protected release tag points to that SHA;
- the same clean environment can fetch and install representative generated
  `contrib/` dependencies from the exact core URL and SHA, and `core_release`
  points to `core_commit`;
- the embedded registry snapshot matches the locked catalog commit;
- a stale, partial, or wrong-commit cache is rejected and recovered;
- archive extraction confinement tests pass;
- archive response-size, member-count, per-member, and total-uncompressed limits
  reject oversized inputs without publishing a cache entry;
- bundled-name resolution ignores the local core v1 mirror unless the user
  supplies its absolute path explicitly;
- default generated Git dependencies use the locked core repository and commit,
  never the catalog repository;
- existing v1 projects retain human command behavior;
- v1 JSON is conservative and v2 JSON is complete;
- core `pyproject.toml`, `uv.lock`, package metadata, `v0.1.0` tag, GitHub
  Release, PyPI release, and documentation all identify AgentSeek 0.1.0;
- lock `schema_version` remains `1` and `lifecycle_version` remains `2`; these
  protocol versions are not required to equal the core SemVer;
- `catalog_release` points to `catalog_commit`, `core_release` points to
  `core_commit`, and documentation records both dependency snapshots
  independently of the core package version.

## Failure and rollback

The immutable catalog prevents an in-place template change from altering an
already released AgentSeek version.

If the catalog content is defective before core release, publish a corrected
template commit and update the candidate core lock. Do not move or rewrite the
recorded commit.

If a defect is discovered after AgentSeek 0.1.0 is published:

- preserve the original catalog commit for reproducibility;
- preserve the original core dependency commit and release tag;
- for a catalog-only defect, publish a new protected catalog release and reuse
  the original core dependency snapshot;
- for a core-only `contrib/` defect, publish a new protected core dependency
  snapshot and reuse the original catalog release;
- for a paired defect, publish the corrected protected core dependency snapshot
  first and the corrected protected catalog release second;
- release an AgentSeek patch whose lock pins the resulting catalog and core
  pair;
- keep existing cached catalog entries addressable by their original commit;
- document whether affected generated projects require regeneration or a
  project-local fix.

The legacy v1 mirror remains available throughout this process. It is not an
automatic fallback for 0.1.0 because doing so would silently change lifecycle
semantics.

## Alternatives considered

### Replace core templates with v2 on `main`

Rejected because released 0.0.x clients use the unversioned core default branch
and cannot parse lifecycle v2.

### Conditional v1/v2 lifecycle files

Rejected because each template would carry two lifecycle contracts inside
Cookiecutter conditionals. The files would be harder to review, validation
would need two render modes indefinitely, and the later repository split would
still be required.

### Add `templates-v2/` inside core

Rejected because it duplicates the catalog inside the repository and creates a
temporary source layout that the planned standalone repository would soon
replace.

### Perform the full templates and skills split in 0.1.0

Rejected because public skills, packaged built-in skills, template distribution,
lifecycle v2, JSON contracts, and repository transfer have different consumers
and compatibility requirements. Combining them would make rollback and release
verification unnecessarily broad.

### Defer all repository separation until after 0.1.0

Rejected because an in-core v2 migration needs conditional or duplicate
templates to protect 0.0.x. Establishing the standalone template boundary now
solves the immediate compatibility problem and is retained after the release.

## Consequences

### Positive

- AgentSeek 0.0.x remains functional without a retroactive client update.
- AgentSeek 0.1.0 receives complete lifecycle-v2 templates.
- Core releases resolve reproducible template content.
- Template CI and releases gain a clear owner and independent cadence.
- The compatibility mechanism is the intended long-term repository boundary,
  not throwaway conditional logic.
- The public-skills split can be designed independently.

### Negative

- The organization maintains a frozen v1 mirror in core.
- The 0.1.0 release requires coordinated verification across two repositories.
- Template fixes may require separate v1 and v2 judgments.
- Core must package a synchronized registry snapshot and catalog lock.
- A template-only correction needs a core patch before default AgentSeek users
  receive the new locked commit.

### Neutral

- The core repository transfer can happen before or after 0.1.0 if GitHub URL
  compatibility is preserved, but it is not part of this decision.
- Future dynamic catalog updates, signatures, mirrors, and non-GitHub sources
  require separate decisions.

## Follow-up decisions

Separate ADRs are required before:

- moving public top-level skills to a standalone repository;
- separating packaged `src/skills/` from the core distribution;
- allowing a released CLI to follow a mutable or remotely updated catalog;
- removing the legacy v1 template paths from the core default branch;
- changing the catalog trust model beyond an HTTPS repository and immutable
  commit lock.

## Related

- [Desktop Service Discovery and Lifecycle v2](https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md)
- [Lifecycle Spec](../reference/lifecycle-spec.md)
- [Template Authoring Contract](../reference/template-authoring-contract.md)
- [Templates](../reference/templates.md)
- [GitHub Discussion #133](https://github.com/ob-labs/agentseek/discussions/133)
- [Template download PR #136](https://github.com/ob-labs/agentseek/pull/136)
