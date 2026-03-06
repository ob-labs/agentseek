# Bundled Skills

This directory contains skills that ship with the `bubseek` distribution.

## Conventions

- Each skill lives in its own directory.
- Each skill directory must contain a `SKILL.md` file.
- Local bundled skills are locked by directory content hash and copied into `.agents/skills/` during `bubseek sync`.

## Scope

Use this directory for skills that are owned, reviewed, and released together with `bubseek`.
Remote skills should be declared in `bubseek.toml` and resolved through `bubseek.lock`.
