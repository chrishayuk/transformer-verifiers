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

## Update 2026-10-30: the enforcement model chosen by the freeze owner

GitHub does not offer rulesets or branch protection for private repositories on a free personal plan. The freeze
owner chose to **make the repository public** and **not to use branch protection**.

**Now enforced server-side:**
- **Ruleset `freeze-tags`** (id 26246512, active, no bypass actors) on `refs/tags/freeze/*`. It blocks update,
  deletion and non-fast-forward. Once created, a freeze tag cannot be moved or deleted, not even by the owner's admin
  account without first changing the ruleset.
- **Test:** an identical ruleset on a throwaway `rulesettest/*` pattern. Creating a tag was allowed; a forced move
  was rejected (`GH013`); deletion was rejected (`GH013`); the tag stayed at `a2aa5af`. Afterwards, the test ruleset
  and tag were removed.

**Not enforced, by the owner's choice:**
- `main` is unprotected. Anyone with push access can push anything, including edits to `tools/freeze_verify.py` and
  `.github/workflows/freeze.yml`.
- CODEOWNERS review is not required. The file remains, but is advisory.

**What this means for the freeze:**
- **The trust anchor is the immutable tag, not the branch.** A frozen protocol is whatever `freeze/<PROTOCOL>`
  points at.
- **Run the verifier from the tag.** Anyone can check any commit by taking the verifier from the tag
  (`git show freeze/<P>:tools/freeze_verify.py`) and running it against that commit. CI does this on every push. An
  edited workflow on `main` can skip CI, but cannot change what the tagged verifier reports.
- **Who can change the tag rule.** An admin token can still edit or delete the ruleset itself. The boundary
  therefore still depends on research agents never holding the owner's token. The checker session has none
  (`../ISOLATION.md`).
- **Tamper tests to run after a freeze tag exists:** the nine tests listed above, against the tagged verifier. Test 6
  (alter the workflow so a corrupted manifest passes) is expected to succeed in skipping CI on `main`, because the
  branch is unprotected. It must still be shown that the tagged verifier, run independently, reports TAMPERED.

## Open B1 acceptance issue: protecting a frozen version is not the same as approving it

Raised by the freeze owner on 2026-10-30. The immutable `freeze/*` tags stop an existing freeze from being replaced.
They do **not** stop someone with write access from creating a *new* freeze tag that points at unreviewed criteria,
because `main` is unprotected and CODEOWNERS is advisory.

**Required before the freeze review can accept B1:**
- The verifier must accept only a freeze whose exact commit SHA appears in an **approval record controlled
  independently of anyone who can push to this repository**. Accepting any tag that matches `freeze/*` is not
  enough.
- The approval record names the protocol, the commit SHA, the approver and the date. It is kept somewhere the
  research agents and this repository's writers cannot alter.
- Tamper test 10, added to the list: create a new `freeze/<P>-x` tag, or a tag for an unapproved commit, and show
  the verifier rejects it.

**Not yet built.** Where the approval record lives depends on who the independent approver is, which is still
undecided.

**Decision (freeze owner, 2026-10-30):** use a separate approval repository. A draft is at
`~/chris-source/transformer-verifiers-approvals-draft/`. It contains an SSH-signed approval record binding the
protocol to its exact commit, plus a verifier that runs from the approval repository and never runs code from the
checked repository. It passed 7 of 7 local cases with throwaway keys. **Not adopted yet:** the owner creates the
signing key (with a passphrase, never available to agents), creates the repository, and records the key's
fingerprint offline. The drafting agent does not control any of it.
