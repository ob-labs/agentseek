# API reference

The following modules are part of the public surface of the `bubseek` package. For config and lockfile types, start with `bubseek.config`; for sync behavior, see `bubseek.sync`.

## bubseek

Package root. Re-exports commonly used helpers.

::: bubseek

## bubseek.config

Configuration and lockfile loading, validation, and generation. Defines `BubseekConfig`, `BubseekLock`, and helpers such as `load_config`, `load_lock`, `generate_config`, `generate_lock`, and path resolution.

::: bubseek.config

## bubseek.sync

Applying the lockfile: install contrib packages and sync skills into a workspace. Main entry: `sync_from_lock`. Types: `SyncResult`, `BubseekSyncSettings`.

::: bubseek.sync

## bubseek.skills

Bundled skills discovery and installation into a workspace. Functions: `bundled_skill_names`, `install_skills_to_workspace`, `install_skill_dir`.

::: bubseek.skills

## bubseek.contrib

Contrib metadata from config. Functions: `load_bubseek_config`, `default_contrib_packages`.

::: bubseek.contrib
