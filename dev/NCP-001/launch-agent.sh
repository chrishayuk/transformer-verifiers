#!/bin/sh
# Start the NCP-001 agent: no MCP servers, no network, no tokens, and reads limited to its workspace and the toolchain.
set -eu
N=/Users/christopherhay/chris-source/transformer-verifiers/dev/NCP-001
W=/Users/christopherhay/chris-source/ncp001-candidate
cd "$W"
exec env -u GH_TOKEN -u GITHUB_TOKEN -u HF_TOKEN DISABLE_AUTOUPDATER=1 CARGO_NET_OFFLINE=true CARGO_HOME="$W/.cargo-home" PATH="$W/.ncp/bin:/Users/christopherhay/.local/bin:/Users/christopherhay/.rustup/toolchains/1.98.0-aarch64-apple-darwin/bin:/usr/bin:/bin:/usr/sbin:/sbin" CARGO_TARGET_DIR="$W/target" TMPDIR="$W/.tmp" \
  claude --settings "$N/agent-settings.json" --strict-mcp-config --model claude-opus-5-5 "$@"
