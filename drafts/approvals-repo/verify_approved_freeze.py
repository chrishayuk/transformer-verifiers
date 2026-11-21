#!/usr/bin/env python3
"""Accept a protocol freeze only if an independent approver signed its exact commit.

Lives in the approvals repository, which only the approver controls, and is run from
there. It never executes code from the repository it checks: the freeze checks are
re-implemented here, so a new tag carrying a weakened verifier changes nothing.

Usage: verify_approved_freeze.py <PROTOCOL-ID> <path to a clone of the protocol repo>

Accepts only if all of these hold:
  1. approvals/<PROTOCOL>.json is validly signed (ssh-keygen -Y verify) by a key in
     allowed_signers, under the namespace below;
  2. the approval names the protocol, the repository and a 40-hex commit SHA;
  3. the tag refs/tags/freeze/<PROTOCOL> exists and points at exactly that commit;
  4. at that commit, every file in FREEZE.sha256 matches, is a regular file (not a
     symlink), and no unlisted file exists under a frozen root.
Any other freeze/* tag, or a tag on an unapproved commit, is rejected.
Exit status: 0 approved and intact, 1 rejected, 2 usage or environment error.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

NAMESPACE = "transformer-verifiers-freeze-approval"
HERE = Path(__file__).resolve().parent


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def verify_signature(approval: Path, signature: Path, approver: str) -> bool:
    with approval.open("rb") as message:
        result = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(HERE / "allowed_signers"),
             "-I", approver, "-n", NAMESPACE, "-s", str(signature)],
            stdin=message, capture_output=True,
        )
    return result.returncode == 0


def tree_entries(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    """Map path -> (mode, blob sha) for every entry in the commit's tree."""
    out = git(repo, "ls-tree", "-r", "-z", commit).decode()
    entries = {}
    for record in filter(None, out.split("\0")):
        meta, path = record.split("\t", 1)
        mode, _kind, sha = meta.split()
        entries[path] = (mode, sha)
    return entries


def check_frozen_tree(repo: Path, commit: str, protocol: str) -> list[str]:
    manifest_path = f"protocols/{protocol}/FREEZE.sha256"
    entries = tree_entries(repo, commit)
    if manifest_path not in entries:
        return [f"{manifest_path}: missing at {commit}"]
    roots, listed = [], {}
    for line in git(repo, "show", f"{commit}:{manifest_path}").decode().splitlines():
        if line.startswith("# root:"):
            roots.append(line.split(":", 1)[1].strip().rstrip("/"))
        elif line.strip() and not line.startswith("#"):
            digest, path = line.split(None, 1)
            listed[path.strip().removeprefix("./")] = digest
    if not roots:
        return [f"{manifest_path}: declares no '# root:' lines"]

    failures = []
    for path, digest in sorted(listed.items()):
        if path not in entries:
            failures.append(f"{path}: missing")
        elif entries[path][0] == "120000":
            failures.append(f"{path}: is a symlink")
        elif hashlib.sha256(git(repo, "show", f"{commit}:{path}")).hexdigest() != digest:
            failures.append(f"{path}: content does not match the manifest")
    allowed = set(listed) | {manifest_path}
    for path in sorted(entries):
        if any(path.startswith(root + "/") for root in roots) and path not in allowed:
            failures.append(f"{path}: not in the frozen manifest")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.split("\n\n")[2], file=sys.stderr)
        return 2
    protocol, repo = sys.argv[1], Path(sys.argv[2]).resolve()
    approval = HERE / "approvals" / f"{protocol}.json"
    signature = approval.with_suffix(".json.sig")
    if not approval.is_file() or not signature.is_file():
        print(f"REJECTED: no signed approval for {protocol}")
        return 1

    record = json.loads(approval.read_text())
    commit = record.get("commit", "")
    if record.get("protocol") != protocol or not re.fullmatch(r"[0-9a-f]{40}", commit):
        print(f"REJECTED: approval for {protocol} is malformed")
        return 1
    if not verify_signature(approval, signature, record.get("approver", "")):
        print(f"REJECTED: approval signature does not verify for approver {record.get('approver')!r}")
        return 1

    tag = f"refs/tags/freeze/{protocol}"
    tagged = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"],
                            capture_output=True, text=True)
    if tagged.returncode != 0:
        print(f"REJECTED: {tag} does not exist")
        return 1
    if tagged.stdout.strip() != commit:
        print(f"REJECTED: {tag} points at {tagged.stdout.strip()}, but the approved commit is {commit}")
        return 1

    failures = check_frozen_tree(repo, commit, protocol)
    if failures:
        print(f"REJECTED: approved commit {commit} fails its own manifest")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"APPROVED: {protocol} at {commit}, signed by {record['approver']}, "
          f"review verdict {record.get('review_verdict')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
