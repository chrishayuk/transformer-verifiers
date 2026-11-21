# transformer-verifiers-approvals (DRAFT, for the freeze owner)

This repository decides which protocol freezes are **authorised**. An immutable `freeze/*` tag in
`transformer-verifiers` proves only that a frozen version cannot be replaced. This repository proves that a specific
commit was approved.

**Status: draft, written by the coordinating Claude session and not yet adopted.** The freeze owner reviews the code,
creates the repository and holds the key. The agent that drafted this must not control it.

## How it works

- `approvals/<PROTOCOL>.json` names the protocol, repository, exact commit SHA, approver, review verdict and date.
- `approvals/<PROTOCOL>.json.sig` is an SSH signature over that file (`ssh-keygen -Y sign`, namespace
  `transformer-verifiers-freeze-approval`).
- `allowed_signers` holds the approver's public key.
- `verify_approved_freeze.py <PROTOCOL> <clone>` accepts only if four things hold:
  - the signature verifies
  - `freeze/<PROTOCOL>` points at exactly the approved commit
  - that commit's tree satisfies its own `FREEZE.sha256`
  - no frozen file is a symlink, and no unlisted file sits under a frozen root

  It never runs code from the repository it checks.

**Draft test (throwaway keys, throwaway repository), all as expected:**

| # | Case | Result |
|---|---|---|
| 1 | Valid approval of the tagged, intact commit | APPROVED |
| 2 | Approval JSON edited after signing | REJECTED (signature) |
| 3 | Signed by a key not in `allowed_signers` | REJECTED (signature) |
| 4 | Tag moved to an unapproved commit | REJECTED (commit mismatch) |
| 5 | Approval rewritten to that commit and signed with another key | REJECTED (signature) |
| 6 | Approved commit violates its own manifest | REJECTED (unlisted file) |
| 7 | No approval record | REJECTED |

## What the freeze owner must do. The independence comes from these steps, not from the code.

1. **Make the approval key yourself, with a passphrase**, and never give it to an agent:
   `ssh-keygen -t ed25519 -C freeze-approver -f ~/.ssh/tv_freeze_approver`. Use a hardware key (`-t ed25519-sk`) if
   you have one. Every agent on this machine runs as you, so an unencrypted key file would be usable by them.
2. **Record the public key's fingerprint somewhere offline** (`ssh-keygen -lf ~/.ssh/tv_freeze_approver.pub`).
   Anyone with your `gh` token could edit `allowed_signers` in a repository you own. The offline fingerprint is how
   an acceptance run confirms that `allowed_signers` was not swapped. Better still, create this repository under an
   account or organisation whose credentials no agent on this machine holds.
3. **Review `verify_approved_freeze.py`**, then create the repository and push this directory.
4. **For each freeze**, after the blind review returns READY TO FREEZE:
   - write `approvals/<PROTOCOL>.json` with the exact commit SHA
   - sign it: `ssh-keygen -Y sign -f ~/.ssh/tv_freeze_approver -n transformer-verifiers-freeze-approval approvals/<PROTOCOL>.json`
   - commit it
5. **Acceptance:** run this repository's verifier from a fresh clone of this repository against a fresh clone of
   `transformer-verifiers`, and check that the `allowed_signers` fingerprint matches your offline record.

## Known limits

- Whoever holds the approval key's passphrase can approve anything. That is the intended authority.
- If this repository sits under credentials an agent can use, step 2's offline fingerprint is the only defence
  against a swapped `allowed_signers`.
- The verifier checks the committed tree. Whether a run *used* that tree is a separate question, answered by the
  run's own provenance records.
