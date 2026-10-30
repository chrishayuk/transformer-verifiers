#!/usr/bin/env python3
"""Verify a protocol freeze against its protected git tag.

Run by CI from the copy of this script stored in the protected tag, never from the
tree under test, so editing this file in a branch cannot change what is checked.

Checks, for the protocol named on the command line:
  1. the tag refs/tags/freeze/<PROTOCOL> exists and its FREEZE.sha256 is used as truth;
  2. the working tree's FREEZE.sha256 is byte-identical to the tag's (no regeneration);
  3. every listed path exists, is a regular file (not a symlink) and has the listed SHA-256;
  4. no unlisted file exists under any frozen root (no added overrides, no renames);
  5. the enforcement files (this script, the CI workflow, CODEOWNERS) equal the tag's copies.

Before a freeze tag exists it reports NOT FROZEN and exits 0, so drafts can be edited.
Exit status: 0 verified or not frozen, 1 tampered, 2 usage or environment error.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

ENFORCEMENT_FILES = [
    "tools/freeze_verify.py",
    ".github/workflows/freeze.yml",
    ".github/CODEOWNERS",
]


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def tag_exists(tag: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}"],
        capture_output=True,
    ).returncode == 0


def parse_manifest(text: str) -> tuple[list[str], dict[str, str]]:
    """Return (frozen roots, {path: sha256}). Roots are declared as '# root: <dir>' lines."""
    roots, entries = [], {}
    for line in text.splitlines():
        if line.startswith("# root:"):
            roots.append(line.split(":", 1)[1].strip().rstrip("/"))
        elif line.strip() and not line.startswith("#"):
            digest, path = line.split(None, 1)
            entries[path.strip().removeprefix("./")] = digest
    if not roots:
        raise ValueError("manifest declares no '# root:' lines")
    return roots, entries


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: freeze_verify.py <PROTOCOL-ID>", file=sys.stderr)
        return 2
    protocol = sys.argv[1]
    tag = f"freeze/{protocol}"
    manifest_path = f"protocols/{protocol}/FREEZE.sha256"

    if not tag_exists(tag):
        print(f"NOT FROZEN: no tag {tag}")
        return 0

    failures = []
    tagged = git("show", f"refs/tags/{tag}:{manifest_path}").decode()
    local = Path(manifest_path)
    if not local.is_file() or local.is_symlink():
        failures.append(f"{manifest_path}: missing or not a regular file")
    elif local.read_text() != tagged:
        failures.append(f"{manifest_path}: differs from {tag} (manifest regenerated or edited)")

    roots, entries = parse_manifest(tagged)
    for path, digest in sorted(entries.items()):
        p = Path(path)
        if p.is_symlink():
            failures.append(f"{path}: is a symlink")
        elif not p.is_file():
            failures.append(f"{path}: missing")
        elif sha256(p) != digest:
            failures.append(f"{path}: content changed")

    listed = set(entries) | {manifest_path}
    for root in roots:
        for p in sorted(Path(root).rglob("*")):
            rel = p.as_posix()
            if (p.is_file() or p.is_symlink()) and rel not in listed:
                failures.append(f"{rel}: not in the frozen manifest")

    for path in ENFORCEMENT_FILES:
        p = Path(path)
        if p.is_symlink() or not p.is_file():
            failures.append(f"{path}: enforcement file missing or a symlink")
        elif p.read_bytes() != git("show", f"refs/tags/{tag}:{path}"):
            failures.append(f"{path}: enforcement file differs from {tag}")

    commit = git("rev-parse", f"refs/tags/{tag}^{{commit}}").decode().strip()
    if failures:
        print(f"TAMPERED: {protocol} against {tag} ({commit})")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"VERIFIED: {protocol} matches {tag} ({commit}), {len(entries)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
