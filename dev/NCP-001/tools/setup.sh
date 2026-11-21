#!/bin/bash
# NCP-001 Phase 0, part 1. Everything here is outside what the agent can read.
set -eu
COMMIT=bb15f826f18c2f9c2b16e7bee8a02dfafbfce8f0
N=$HOME/chris-source/transformer-verifiers/dev/NCP-001; H=$HOME/chris-models/ncp001; REPO=$HOME/chris-source/larql-verifier
mkdir -p "$H"
git -C "$REPO" worktree add -q --detach "$H/build" "$COMMIT"
[ -d "$H/venv" ] || python3 -m venv "$H/venv"
"$H/venv/bin/pip" install -q --require-hashes --no-deps -r "$H/build/verifier/requirements.lock" 2>&1 | grep -v notice || true
"$H/venv/bin/pip" install -q --no-deps "$H/build/verifier" 2>&1 | grep -v notice || true
cp -R "$N/harness" "$H/harness"
cp "$H/build/Cargo.lock" "$H/harness/Cargo.lock"
export RUSTUP_TOOLCHAIN=1.98.0
(cd "$H/harness" && CARGO_TARGET_DIR=$H/target-harness cargo build -q --release 2>&1 | tail -3)
mkdir -p "$H/bin"; cp "$H/target-harness/release/ncp001-harness" "$H/bin/harness-baseline"
(cd "$H/build" && CARGO_TARGET_DIR=$H/target-larql LARQL_BUILD_COMMIT=$COMMIT cargo build -q --release --locked -p larql-cli 2>&1 | tail -3)
cp "$H/target-larql/release/larql" "$H/bin/larql-baseline"
"$H/bin/harness-baseline" refuse && echo "baseline refuses bad geometry"
export PYTHONPATH=$H/build/verifier
"$H/venv/bin/python" -I -c "import sys; sys.path.insert(0, '$H/build/verifier'); sys.argv=['x','$H/conform-dev','1001']; exec(open('$N/tools/make_conformance.py').read())"
"$H/venv/bin/python" -I -c "import sys; sys.path.insert(0, '$H/build/verifier'); sys.argv=['x','$H/hidden/conform','977331']; exec(open('$N/tools/make_conformance.py').read())"
shasum -a 256 "$H"/bin/* | cut -c1-16,65-
du -sh "$H" | cut -f1
echo SETUP-DONE
