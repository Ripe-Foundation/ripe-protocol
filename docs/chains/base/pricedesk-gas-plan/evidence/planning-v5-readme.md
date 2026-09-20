# PriceDesk gas-budget packet — revision 5

The [retained Pool-1 claim supplement](../legacy-pool-claim-qualification.md) adds a shared release requirement: qualify all 11 existing LP dust claims by full address and actual balance, preserve the five floor-dependent values, and include complete cold legacy flows. Its pinned readback is planning evidence, not gas qualification. This supplement does not change this packet's design or owner decisions.

Read the [updated prompt](planning-v5-prompt.md) for the three-stage implementation plan and [execution reference](planning-v5-reference.md) for exact setup, tests, snapshot/estimator requirements, recovery and activation details. The [resolution record](planning-v5-resolutions.md) addresses all 13 numbered findings and every low-priority item, including both Safe subpoints. The full [latest review](reviewer-v5.txt) is preserved.

The owner has approved configurable feed-check budgets, one combined branch stacked on PR #231, D01 coverage of both PriceDesk and Teller snapshots, and the retained margins with measured batch limits. The earlier one-faulty-source-identity model remains.

**Two design choices remain pending:** conditional quote funding checks (with eager feed/snapshot/admission), and immutable defaults plus unpacked, constructor-floored per-source overrides. The prompt presents the recommended versions explicitly; do not hand it to an implementation agent as finalized until those answers are incorporated. No further answer is needed for the already-approved scope, branch, D01 or margin decisions.

The former eager-every-quote design is withdrawn because a nested revisit of the same source cannot eagerly supply its containing allowance again. The new proposal accepts certain clean results without full-allowance proof; actual source/dependency auditing and tests are therefore prerequisites, not completed evidence. This is not a claim of universal protection against arbitrary wrong prices.

New verification evidence:

- [Pinned topology read](topology-v5.block-51532116.json) confirms priorities `[1,8,2,9,4,5]`; subsequent enumeration was rate-limited and is explicitly incomplete.
- [Pinned source-registry delay](source-registry-delay-v5.block-51532116.json) reads zero. HQ replacement delay is a separate setting.
- [Struct member-access probe](vyper-struct-member-probe-v5.json) confirms one/two/three SLOADs for one/two/all fields, correcting the case for mandatory packing.
- [Anvil estimator smoke](anvil-estimator-smoke-v5.json) verifies synthetic local state equivalence at estimated versus generous gas. It is not a Base fork/D01 qualification.
- [Evidence notes](README.md) describe exact provenance, prior archived versions and limits.

Copy using the [packet hash inventory](../packet-hashes.json) as an allowlist, plus the inventory itself; exclude `.claude/` and unlisted session files. Preserve relative paths and hand over the whole listed packet. It is uncommitted and absent from pinned implementation SHA `bdf7f3da7113aabde60ab8eceab6a960a841bb88`. Implementation outputs belong in `docs/chains/base/pricedesk-gas/`.

Archived v2/v3/v4 documents are historical, not execution instructions. This revision made no production contract edits, Git branch/commit/publication, live transaction, Safe mutation or external-repository change. The live nonce-477 guidance remains a separate owner action; its latest service check in this packet is the dated revision-4 readback, not a continuing monitor.
