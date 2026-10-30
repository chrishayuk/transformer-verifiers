#!/bin/sh
# Start the reference-checker agent's Claude Code session for LARQL-VERIFY-001.
# Isolation comes from the --settings file (higher precedence than anything in the
# workspace), no MCP servers, and no GitHub or Hugging Face tokens in the environment.
set -eu
ROOT=/Users/christopherhay/chris-source/transformer-verifiers
cd "$ROOT/checker"
mkdir -p "$ROOT/checker/.tmp"
exec env -u GH_TOKEN -u GITHUB_TOKEN -u HF_TOKEN TMPDIR="$ROOT/checker/.tmp" \
  claude --settings "$ROOT/isolation/checker-settings.json" --strict-mcp-config "$@"
