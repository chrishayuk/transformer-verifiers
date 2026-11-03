#!/bin/bash
set -u
N=$TMPDIR/gemvneg; T=$N/tree; PY=$HOME/chris-source/transformer-verifiers/checker/.venv/bin/python
git -C $HOME/chris-source/larql-gemv-witness worktree add -q --detach "$T" 7ac8c9e3 || exit 9
F=crates/larql-compute/src/cpu/kquant_gemv.rs
C8=$HOME/chris-models/q8enc-ad82acba/qwen3-0.6b-q8_0.vindex3; TOK=9707,1879,13,576,374,264,1273,315,279,5333,323,1181,2550,9963,11,8365
cd "$T"
for fault in reverse_blocks hoist_scale binary64_acc unsigned_codes wrong_last_element flush_subnormal_scale; do
  git checkout -q -- $F
  "$PY" -I "$N/patch.py" "$fault" $F || exit 8
  git diff --stat -- $F | tail -1
  CARGO_TARGET_DIR=$N/target LARQL_BUILD_COMMIT="7ac8c9e3+fault:$fault" cargo build -q --release --locked -p larql-cli 2>&1 | tail -2
  env PATH=/usr/bin:/bin HOME=$HOME $N/target/release/larql vindex3 exec "$C8" --backend production-q8 --representation-source stored --tokens $TOK --logit-dump $N/$fault.bin --gemv-witness $N/w-$fault --gemv-witness-max-operands 400 2>&1 | grep -E 'gemv witness|rror' | cut -c1-90
  cmp -s $N/$fault.bin $HOME/chris-models/gemv-7ac8c9e3/off.bin && echo "logits: identical to clean" || echo "logits: differ from clean"
  (cd $TMPDIR/gemv-audit && "$PY" -I "$N/judge.py" "$N/w-$fault" "$fault")
done
git checkout -q -- $F; cd $N; git -C $HOME/chris-source/larql-gemv-witness worktree remove --force "$T"; git -C $HOME/chris-source/larql-gemv-witness worktree prune; echo FINISHED
