# PriceDesk gas-budget packet — final handoff (revision 7)

Start with [updated-prompt.md](updated-prompt.md) and the short [test/setup reference](implementation-reference.md). They are the only required execution documents. **Implement all steps continuously, fix resulting issues and run only affected tests; no interim owner-review checkpoints or full-suite run.**

The prepared workspace is `/Users/wigglez/dev/ripe-protocol-pricedesk-gas`, branch `codex/pricedesk-configurable-gas`, based on PR #231 head `bdf7f3da7113aabde60ab8eceab6a960a841bb88`. Use this worktree and its packet. The original checkout’s older packet is superseded; do not edit or copy it back over this one. This worktree's packet is now the canonical Git-tracked copy, including its evidence and hash inventory. The main checkout's untracked copy remains untouched and is not authoritative.

All design choices are settled: conditional ordinary quote checks; eager feed/snapshot/admission checks; immutable defaults with per-source overrides; and a Teller-to-PriceDesk Curve snapshot relay. Measure runtime early, resolve routine implementation details independently and collect any genuine remaining questions in the final report. This is scoped contract/test work, not release qualification.

[Review dispositions](review-resolutions.md) explain the changes. [Deferred qualification](follow-up-qualification.md) and the unchanged [Pool-1 supplement](legacy-pool-claim-qualification.md) preserve later release requirements; do not execute them now. Archived evidence is optional background, not additional instructions.

For transfer, copy the files in [packet-hashes.json](packet-hashes.json), plus that inventory, preserving relative paths and excluding `.claude/` and unlisted session files. Revision 7 records the original approved implementation scope. The implementation and subsequent reviewer fixes are recorded in [the current handoff](../pricedesk-gas-implementation.md); consult it for current paths, commands, configuration decisions, and remaining release work. Historical prompts and evidence are preserved for provenance, not as instructions to rerun old operations.
