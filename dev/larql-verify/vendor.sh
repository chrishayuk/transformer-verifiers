#!/bin/sh
# Export refcheck from the checker repository at a pinned commit, read-only. Nothing in checker/ is modified (D15).
set -eu
COMMIT=${1:-e505afc}
HERE=$(cd "$(dirname "$0")" && pwd)
CHECKER="$HERE/../../checker"
DEST="$HERE/vendor/refcheck-$COMMIT"
FULL=$(git -C "$CHECKER" rev-parse "$COMMIT^{commit}")
TREE=$(git -C "$CHECKER" rev-parse "$COMMIT:refcheck")
rm -rf "$DEST"; mkdir -p "$DEST"
git -C "$CHECKER" archive "$FULL" refcheck | tar -x -C "$DEST"
printf '{"checker_commit": "%s", "refcheck_tree": "%s"}\n' "$FULL" "$TREE" > "$DEST/PIN.json"
cat "$DEST/PIN.json"
