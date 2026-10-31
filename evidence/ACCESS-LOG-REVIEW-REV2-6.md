# Access-log review: hidden-corpus authors, revisions 2–6 (and the revision 1 context)

- **Requested by:** freeze review 1, minimum change 7, and the protocol owner.
- **Reviewed by:** the coordinating session, 2026-10-31.
- **Method:** a scan of every tool call recorded in the subagent transcripts under
  `~/.claude/projects/-Users-christopherhay-chris-source-transformer-verifiers/*/subagents/` (19 transcripts, all three
  sessions).
  - **Paths matched:** the live checker tree, `checker-src` clones, `CHECKER-PUBLICATION`, `AMB-022` and
    `checker-run-*` logs.
  - **Recursive searches:** listed separately (`grep -r`, `find`, `Grep`/`Glob`) when they were run inside the reviewer
    repository.
  - **Classification:** each hit was classified by hand, with its timestamp compared against the seal commits.
  - **Scripts:** `evidence/access-log/accesslog.py` and `accesslog2.py`.

**This is not proof that prohibited access did not occur.** The limits are listed at the end.

## Who authored which revision

| Revision | Author (subagent) | Seal commit (reviewer repo, time UTC) | Also scored |
|---|---|---|---|
| 1 | `a891f115` | before `792a8b3` (2026-10-30 23:24) | run 1 |
| 2 | `acc792a2` | `3333c76` (2026-10-31 16:52) | run 2 |
| 3, 4 | `a5c843e7` | `1b5d554` (17:28), `7a18a71` (18:29) | runs 3, 4, 5 |
| 5, 6 | `a9aa3d92` | `bbc84af` (19:03), seal of revision 6 before run 7 | runs 6, 7 |
| 7 | `a29de3e6` | `0caf4f1` | run 8 (reviewed in isolation part 10) |

## Findings

1. **Revisions 2–6: no direct read of checker implementation.**
   - **What none of the three authors did:** open checker source (`refcheck/`), tests, `AMBIGUITIES.md`, `BRIEF.md`,
     checker run logs, `CHECKER-PUBLICATION.md` or the AMB-022 audit.
   - **The flagged calls fall into three groups.** First, `stat` on checker-run log file names, which is metadata only.
     Second, the text of the authors' own writes. Third, the scoring steps, listed in 2.
2. **Clones and checker execution came after each seal.**
   - **Clones:** every `checker-src` clone was created after the corresponding seal, during scoring.
   - **Probes:** the field-name probes imported checker modules to list output key names and types.
   - **The venv:** the authors also used the checker's venv interpreter to run their own scripts (environment only).
   - **One coordinator-checked case:** a9aa3d92's 19:03:16 command checked the checker commit and venv, 6 seconds
     after the revision 5 seal.
3. **Recursive searches traversed clone folders without displaying their content.**
   - **acc792a2:** ran `grep -rn -i checker` over the reviewer repository. The run 1 clone was present, and its lines
     were filtered out of the output, so the clone was read by `grep` but not displayed.
   - **a5c843e7:** ran `grep -rl` (file names only), once without excluding the clones.
   - **Nothing displayed:** neither search showed checker content to the author.
4. **Earlier clones were present in the workspace while later revisions were built.**
   - **Which ones:** revision 4 was built with the run 2–4 clones present, and revisions 5 and 6 with the run 2–6
     clones present.
   - **What the logs show:** no call opened them.
5. **Indirect channel 1: scoring artefacts.** The reviewer repository holds scoring artefacts written after seeing
   checker output and its README: field maps, field-name lists, results, reports, and the rules of later runs.
   - **Who could read them:** later authors could, and did, read earlier rules and reports.
   - **Why it is by design:** corpus authors learn of earlier failures, for example the run 6 field-identity failures
     that led to schema v1.
   - **The limit it implies:** later corpora are not blind to the checker's earlier *outputs*. They are blind to its
     implementation.
6. **Indirect channel 2: revision 1.**
   - **What happened:** during scoring run 1, the revision 1 author read checker implementation (`refcheck/e1.py`,
     `refcheck/metrics.py`, parts of `refcheck/synth.py` and `AMBIGUITIES.md`, at 2026-10-30 23:23). That was before
     committing the run 1 pass/fail rules (`792a8b3`, 23:24). The revision 1 corpus was already sealed.
   - **Who that author was:** that agent authored no later revision.
   - **What it left behind:** the files it wrote (`scoring/run-1/`, including `TOLERANCES.md`) remained readable to
     later authors.
   - **Already partly addressed:** D1 and OQ5 already treat the run 1 exposure and the tolerance provenance
     (`decisions/OQ5-PROVENANCE.md`).
   - **New here:** the run 1 rules were written after implementation was read.

## Limits

- **Tool calls only.** The scan sees only recorded tool calls, matched by path. It would miss access through a script
  that computed a path, or through a library import beyond the scoring probes.
- **Briefs not examined.** It does not cover information passed in the coordinating session's briefs to reviewers. The
  coordinating session had read checker code, and examining that channel needs the briefs in the main transcript.
- **No independent access record.** There is no OS-level access record, and the reviewer had no sandbox (freeze review
  1, focus area 4).

## Consequence for Stage A (proposed, for the owner)

Stage A hidden artefacts:
- the E2/E3 held-out set;
- the frozen A4 suite;
- any freeze-time hidden rows.

They should be built under a mechanism, not a log review:
- no checker tree or clone readable by the author;
- a sandbox with read allow-lists like the checker's;
- briefs preserved verbatim.

The E2/E3 corpus author started on 2026-10-31 under written rules only. Its tool log is to be reviewed in the same way
when it completes.
