#!/bin/bash

set -eo pipefail

if [ -f "/workspace/startup.sh" ]; then
    exec bash /workspace/startup.sh
else
    exec /app/.venv/bin/agentseek gateway
fi
