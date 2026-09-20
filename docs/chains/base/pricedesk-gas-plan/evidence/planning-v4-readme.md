# PriceDesk configurable-gas implementation packet — revision 4

Start with [updated-prompt.md](updated-prompt.md), a concise three-stage handoff: contract/tests, Base values/monitoring, and fork rehearsal/activation instructions. Use [implementation-reference.md](implementation-reference.md) for source pins, existing tooling, measurement details, test commands and registry/Safe/bootstrap mechanics. Hand over the **whole directory**; no chat context is required.

**Two owner answers are pending:** configurable feed-check budgets and one combined replacement branch. The proposed prompt clearly labels these recommendations and is not yet a finalized implementation instruction. The owner approved normal gas ×1.5 plus one faulty source identity across every invocation per transaction, and previously approved stacking on PR #231. Neither earlier approval settles the two pending choices.

[Review resolutions](review-resolutions.md) addresses every one of the latest review's six main findings and six smaller items, explains qualifications/disagreements and preserves earlier corrections. [The latest supplied review](evidence/reviewer-v4.txt) is included verbatim for traceability.

Planning checks are distinct from implementation acceptance:

- [Current dated PR readback](evidence/pr-231-v4-readback.json): PR #231 remains at the pinned SHA.
- [Current dated live refresh](evidence/planning-v4-live-refresh.json): old desk active and slot 7 empty at finalized block 51,531,230; Safe service separately reports nonce 477 unexecuted. The slot-7 proposal is an immediate separate owner action, not deferred until implementation completes. No live mutation occurred.
- [Vyper layout probe](evidence/vyper-budget-layout-probe.json): verifies explicit packing is necessary; it does not implement the budgets or prove runtime gas.
- [Evidence notes](evidence/README.md): historical code/readbacks, prior validation, current limitations and archived revisions.
- [Packet hash inventory](packet-hashes.json): SHA-256/size inventory of all files except itself.

Archived v2/v3 prompts/resolutions in `evidence/` are historical and superseded. Do not execute their narrow-first, classifier, four-hour, exhaustive-fault or conflicting branch/pytest instructions.

This directory is durable but uncommitted and absent from implementation pin `bdf7f3da7113aabde60ab8eceab6a960a841bb88`; copy it into an isolated implementation checkout. Results belong in the separate `docs/chains/base/pricedesk-gas/` directory. This revision changed planning documents only; no contract edits, Git commits/publication, Safe operations or deployment were performed.
