# B1: freeze-lock setup and status

**Status: partly built, not closed.** This file is a record, not a claim that B1 is met. Only the blind review
decides that.

## Built so far (drafted by the coordinating session for the freeze owner to review)

| Part | Where | State |
|---|---|---|
| Private remote | `github.com/chrishayuk/transformer-verifiers`, branch `main` | Created 2026-10-30 |
| Verifier | `tools/freeze_verify.py` | Takes the manifest and its own code from the protected tag `freeze/<PROTOCOL>`. Checks the manifest is unregenerated, listed files' hashes match, listed files are not symlinks, no unlisted files exist under the frozen roots, and the enforcement files (verifier, workflow, CODEOWNERS) match the tag |
| CI | `.github/workflows/freeze.yml` | Runs on every push and PR. When the tag exists, it runs the verifier *from the tag*, not from the commit under test. It reports NOT FROZEN until the tag exists |
| Code owners | `.github/CODEOWNERS` | `* @chrishayuk` |
| Local self-test | throwaway clone with a test tag, not B1 evidence | Clean tree VERIFIED. Rejected: protocol edit, regenerated manifest, added override file, deleted file, symlink swap, rename, edited verifier, edited workflow |

## For the freeze owner to do

1. **Review** `tools/freeze_verify.py` and `.github/workflows/freeze.yml`. You own them, not the agent that drafted
   them.
2. **Protect `main`.** Use a ruleset, or branch protection on a plan that supports it for private repositories:
   - require a pull request with **code-owner review**
   - require the status check **`freeze / verify (LARQL-VERIFY-001)`**
   - block force pushes and deletion
   - **do not allow bypass**, administrators included
3. **Protect the tags `freeze/*`.** Use a tag ruleset: only the owner may create them, nobody may update or delete
   them.
4. **Name the human reviewer** of the lock in this file.
5. **Keep credentials away from research agents.** Every agent running on this host as your user can use your `gh`
   login, and an admin token can change branch protection itself. The boundary therefore depends on research agents
   never holding that token. The reference-checker session has no token and no network (`evidence/ISOLATION.md`).
   Any other agent that the freeze governs must run the same way.

## Tamper tests (still to be run, as the agent role, against the real remote after protection is on)

Each test is attempted by a push or PR from a token without admin rights. The evidence for each must record the
commit hashes involved and the CI run or ruleset rejection that decided it. A legitimate verification must also be
shown passing.

1. Edit a byte of each frozen class: protocol, tolerances, corpus, held-out part, mutation suite, checker.
2. Regenerate the manifest after an edit.
3. Add an unlisted file, such as a tolerance override.
4. Delete a listed file.
5. Swap a file for a symlink, and retarget an existing symlink.
6. Edit the check script or the CI workflow, **including leaving the frozen files unchanged while altering the
   verifier or workflow so that a corrupted manifest passes**.
7. Rename a file.
8. Change the checker's dependency lockfile.
9. Change a semantics-altering `LARQL_*` variable in the pinned environment record.

**Known limit:** for a `pull_request` event, GitHub runs the workflow file from the PR, so a PR can rewrite the
workflow to skip verification. Code-owner review on `.github/**` and no bypass are what stop that, not the
verifier. Test 6 must show that such a PR cannot merge.
