#!/bin/sh
# Pre-publication audit of the reference checker (run by the publisher, never by the checker).
# Usage: tools/audit_checker.sh <base-commit>   e.g. the last published commit
set -eu
BASE=$1
C=/Users/christopherhay/chris-source/transformer-verifiers/checker
cd "$C"
echo "== commits since $BASE"; git log --format='%h %s' "$BASE"..HEAD
echo "== attribution trailers in new commits"; git log --format='%b' "$BASE"..HEAD | grep -ci 'co-authored' || true
echo "== lockfile changes since $BASE"; git diff --stat "$BASE" HEAD -- requirements.in requirements.lock
echo "== uncommitted"; git status --porcelain
echo "== installed environment"
.venv/bin/python -I - <<'EOF'
import importlib.metadata as m, re, hashlib, base64, os, sys, glob
lock = {}
for line in open('requirements.lock'):
    mm = re.match(r'^([A-Za-z0-9_.\-]+)==([^\s\\]+)', line)
    if mm: lock[mm.group(1).lower().replace('_', '-')] = mm.group(2)
inst = {d.metadata['Name'].lower().replace('_', '-'): d.version for d in m.distributions()}
print("extra:", sorted(set(inst) - set(lock)), "missing:", sorted(set(lock) - set(inst)),
      "mismatch:", [(k, inst[k], lock[k]) for k in lock if k in inst and inst[k] != lock[k]])
checked = bad = 0
for d in m.distributions():
    if d.read_text('direct_url.json'): print("DIRECT_URL install:", d.metadata['Name'])
    for f in d.files or []:
        if f.hash is None: continue
        try: data = open(f.locate(), 'rb').read()
        except FileNotFoundError: bad += 1; continue
        checked += 1
        if base64.urlsafe_b64encode(hashlib.new(f.hash.mode, data).digest()).rstrip(b'=').decode() != f.hash.value:
            bad += 1; print("HASH MISMATCH", f.locate())
print(f"RECORD files checked {checked}, bad {bad}")
for s in [p for p in sys.path if p.endswith('site-packages')]:
    print(".pth:", sorted(os.path.basename(x) for x in glob.glob(s + '/*.pth')),
          "customize:", [x for x in os.listdir(s) if x.startswith(('sitecustomize', 'usercustomize'))])
EOF
echo "== top-level imports"
git ls-files '*.py' | xargs grep -hE '^\s*(import|from)\s+[A-Za-z_]' | sed -E 's/^\s*(from|import)\s+([A-Za-z_][A-Za-z0-9_]*).*/\2/' | sort | uniq -c | sort -rn
echo "== non-regular-mode or non-text tracked files"
git ls-files -s | awk '$1!="100644"'; git ls-files | xargs file | grep -vE 'text|JSON|empty' || true
echo "== LARQL strings (excluding BRIEF.md)"; git grep -niE 'larql|quantise_q8|chris-source/larql|2536bb79' -- ':!BRIEF.md' | cut -c1-160 || true
echo "== tests"; .venv/bin/python -I -m unittest discover -s tests 2>&1 | tail -3
