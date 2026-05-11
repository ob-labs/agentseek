#!/usr/bin/env bash

set -euo pipefail

workspace_path="${BUB_WORKSPACE_PATH:-${AGENTSEEK_WORKSPACE_PATH:-/workspace}}"
agentseek_home="${BUB_HOME:-${AGENTSEEK_HOME:-${workspace_path}/.agentseek}}"
skills_target="${workspace_path}/.agents/skills"
skills_home="${BUB_SKILLS_HOME:-${AGENTSEEK_SKILLS_HOME:-${skills_target}}}"
project_home="${BUB_PROJECT:-${AGENTSEEK_PROJECT:-${agentseek_home}/agentseek-project}}"
mcp_config_target="${agentseek_home}/mcp.json"
mcp_config_source="${BUB_MCP_CONFIG_PATH:-${AGENTSEEK_MCP_CONFIG_PATH:-}}"

if [ -z "${mcp_config_source}" ] && [ -f "${workspace_path}/.agents/mcp.json" ]; then
    mcp_config_source="${workspace_path}/.agents/mcp.json"
fi

export BUB_WORKSPACE_PATH="${workspace_path}"
export AGENTSEEK_WORKSPACE_PATH="${AGENTSEEK_WORKSPACE_PATH:-${workspace_path}}"
export BUB_HOME="${agentseek_home}"
export AGENTSEEK_HOME="${AGENTSEEK_HOME:-${agentseek_home}}"
export BUB_SKILLS_HOME="${skills_home}"
export AGENTSEEK_SKILLS_HOME="${AGENTSEEK_SKILLS_HOME:-${skills_home}}"
export BUB_PROJECT="${project_home}"
export AGENTSEEK_PROJECT="${AGENTSEEK_PROJECT:-${project_home}}"
export BUB_MCP_CONFIG_PATH="${mcp_config_target}"
export AGENTSEEK_MCP_CONFIG_PATH="${AGENTSEEK_MCP_CONFIG_PATH:-${mcp_config_target}}"

mkdir -p "${BUB_HOME}" "${BUB_PROJECT}" "${workspace_path}/.agents"

if [ "${skills_home}" = "${skills_target}" ]; then
    mkdir -p "${skills_target}"
else
    mkdir -p "${skills_home}"
    ln -sfn "${skills_home}" "${skills_target}"
fi

if [ -n "${mcp_config_source}" ] && [ "${mcp_config_source}" != "${mcp_config_target}" ] && [ -f "${mcp_config_source}" ]; then
    ln -sfn "${mcp_config_source}" "${mcp_config_target}"
fi

if [ -f "${workspace_path}/startup.sh" ]; then
    exec bash "${workspace_path}/startup.sh"
fi

exec /app/.venv/bin/agentseek gateway
