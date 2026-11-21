#!/bin/bash
# What a process running candidate code can reach, under candidate.sb. Each line should say BLOCKED or ALLOWED as labelled.
H=$HOME/chris-models/ncp001; N=$HOME/chris-source/transformer-verifiers
B=(sandbox-exec -D "HOME=$HOME" -f "$N/dev/NCP-001/tools/candidate.sb")
probe() { want=$1; shift; if "${B[@]}" "$@" >/dev/null 2>&1; then got=ALLOWED; else got=BLOCKED; fi; [ "$got" = "$want" ] && s=ok || s=WRONG; echo "$s $got: ${*: -1}"; }
probe BLOCKED cat $H/hidden/conform/cases.tsv
probe BLOCKED cat $H/hidden/workload/tokens.json
probe BLOCKED cat $N/dev/NCP-001/tools/evaluate.py
probe BLOCKED cat $N/dev/NCP-001/PROTOCOL.md
probe BLOCKED cat $H/build/verifier/refcheck/gemv.py
probe BLOCKED cat $HOME/.gitconfig
probe BLOCKED cat $HOME/.claude/settings.json
probe BLOCKED touch $H/bin/harness-baseline
probe BLOCKED touch $H/baseline-logits.bin
probe BLOCKED touch $H/conform-dev/x
probe BLOCKED touch $H/build/x
probe BLOCKED touch $N/x
probe BLOCKED /usr/bin/curl -s -m 5 https://example.com
probe BLOCKED stat $H/hidden/workload/tokens.json
probe BLOCKED ls $H
probe BLOCKED ls $H/hidden
probe BLOCKED ls $H/validate
probe BLOCKED cat /private/tmp/claude-501/x
probe BLOCKED ls /private/tmp/claude-501
probe ALLOWED cat $H/conform-dev/cases.tsv
probe ALLOWED cat $H/build/Cargo.toml
mkdir -p $H/scratch
probe ALLOWED touch $H/scratch/probe
rm -f $H/scratch/probe
