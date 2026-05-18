This directory is provided for local testing and debugging only.

It mirrors the minimal `.agents` setup so container and runtime integration can be exercised consistently during development.

Contents here are sample assets, not production-ready defaults:

- `mcp.json` is a placeholder MCP configuration and must be updated with real endpoints before use.
- `skills/` contains local skills for validating skill loading and workspace mounts, plus optional authoring helpers such as `documentation-writer` (from [awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills/documentation-writer)).
