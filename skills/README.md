# Skills

This directory is reserved for skill-source examples and downstream packaging experiments.

For this repository itself, builtin skills are shipped directly from `bub_skills/` and do not require a separate sync step.

If you are building a downstream distribution and want to vendor remote skills at build time, use `pdm-build-bub` from your own `pyproject.toml`.
