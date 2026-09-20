# Historical planning evidence

Publication note (2026-09-19, extended 2026-09-20): archived copies have portable
path substitutions, quoted worktree commands, a parameterized smoke-output path,
repaired navigation links and clarified historical scope. They are historical
evidence, not current execution instructions or byte-for-byte original captures. See the [packet entry point](../README.md)
and [original versus published hashes](../packet-hashes.json) for exact provenance.

**Historical revision-7 scope:** that revision authorized contracts and related
tests only. Statements below about prerequisites, pending decisions or operational
work describe their historical revisions. See the [current implementation
handoff](../../pricedesk-gas-implementation.md) and [review closure](../../pricedesk-gas-review-232.md)
for subsequently authorized maintenance, publication and complete applicable
workflow validation. Deployed-source authentication, Base qualification and
operations remain in [deferred qualification](../follow-up-qualification.md);
the archive does not authorize their execution.

These files preserve planning evidence, not implementation acceptance or deployment approval. The historical verification paragraphs below describe the earlier v2/v3 reviews; revision-4 checks are listed separately at the end.

| File | Provenance and scope |
| --- | --- |
| `live-summary.block-51524517.json` | Earlier read-only planning check, copied byte-for-byte from the temporary artifact. Chain values are pinned to block 51,524,517/hash `0x37ebbf61930e433ee35894adda51ab9054cff823e5febe9c6ef32c589606f10b`. Contains all 22 locally decoded Safe calls. |
| `live-readback.block-51524517.json` | Same earlier check, copied byte-for-byte with the Safe service's decoded batch response. Safe-service queue data was fetched shortly after the block-pinned chain reads and is not itself a block-pinned chain proof. |
| `candidate-runtime.block-51524517.json` | New read-only historical `eth_getCode` retrieval for candidate `0xad70893e2f51076b0e9ba18fc593e924593a073f`, after validating chain ID and the exact historical block hash. Includes full code, 17,898-byte count, and Keccak-256. Source/build equivalence was not checked in this planning pass. |
| `planning-v2-prompt.md` | Previous 3,301-word prompt, preserved byte-for-byte before the re-review update. Superseded; not current instructions. |
| `planning-v2-resolutions.md` | Previous 28-item resolution record, preserved byte-for-byte. Superseded where the current record differs; its historical verification statements remain attributed to that earlier turn. |

The earlier snapshot found the old desk active, no on-chain pending slot-7 entry, and unexecuted Safe nonce 477 containing a proposal for the 1.5M/1.5M candidate. It also found the Base manifest's MissionControl matched the active address and had code. None of these is a claim about current live state at the future implementation start; refresh then.

The original slot-7 confirmation simulations from both caller roles reverted while no update was pending. They do not independently prove confirmation authorization. Governance-only confirmation was read from the inspected source; the implementation task still must bind deployed code when relying on that authorization operationally.

The earlier master runtime test was run with task-local caches and `-m gas`: `1 passed in 94.02s`; output `PRICEDESK_DEPLOYED_RUNTIME size=17742 headroom=6834`. This re-review checked marker selection with collection only (`1 test collected in 0.01s`), without rerunning that runtime test. No Base gas sweep or full transaction qualification has been performed by the planning task.

Offline runtime verification is `code = bytes.fromhex(record['runtime'][2:])`; assert `len(code) == record['runtime_bytes'] == 17898` and compare `Web3.keccak(code)` with `record['runtime_keccak256']`. The packet hash inventory covers every evidence file, including this explanatory record; its SHA-256 file hashes are distinct from the EVM runtime's Keccak-256.

Primary references checked for the final corrections: [EIP-150 call-gas forwarding](https://eips.ethereum.org/EIPS/eip-150) and [pytest command-line precedence](https://docs.pytest.org/en/stable/example/simple.html#how-to-change-command-line-options-defaults). Static-path constraints retain the earlier [EIP-214](https://eips.ethereum.org/EIPS/eip-214) and [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153) references. Fork mechanics were checked directly against the installed Titanoboa 0.2.7 implementation.

## Revision-4 checks

- `reviewer-v4.txt` is the complete latest user-supplied feedback.
- `planning-v3-prompt.md`, `planning-v3-resolutions.md` and `planning-v3-hashes.json` preserve the preceding packet byte-for-byte. Their instructions and owner-decision status are historical; current decisions are in the main prompt/resolution record.
- `vyper-budget-layout-probe.json` includes compiler version, exact standalone source and generated layout: three uint64 struct fields use three slots; a uint256 uses one. Mapping read counts and a packed production implementation were not tested.
- `pr-231-v4-readback.json` records the read-only GitHub result: PR open against master with unchanged head.
- `planning-v4-live-refresh.json` preserves initial sandbox name-resolution failures, the permitted PublicNode/Safe retry (RPC HTTP 403), and the successful official-RPC fallback. At finalized Base block 51,531,230/hash `0xcb7ef0979e164af8e5c6a2d6a11e79abe2d302ab9972225c15a80e01c0c42aed`, HQ still reported the old desk active, no pending slot-7 entry and the same governance. The separately timed Safe service response still reported the same nonce-477 hash unexecuted. Local ABI decoding confirmed the slot-7 proposal is batch call index 2 of 22; other calls were not re-reviewed. This refresh did not authenticate deployed bytecode again or measure gas.

Revision 4 checked [Optimism SafeCall](https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/libraries/SafeCall.sol) and [OpenZeppelin ERC2771Forwarder](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/metatx/ERC2771Forwarder.sol) directly. The former demonstrates pre-call minimum-gas checking and warns about intervening/memory costs; its forward-all-gas helper is not the proposed bounded PriceDesk implementation. The latter's post-call OOG check does not establish the stronger full-forwarding guarantee for every caught-inner-failure composition. These are design references, not production qualification of a Vyper adaptation.

No contract regression suite, gas sweep, complete transaction rehearsal, production-budget monitor or deployment was implemented/run by this planning revision. Current documentation/link/hash checks do not replace those tasks.

## Revision-5 checks

`reviewer-v5.txt` preserves the latest supplied feedback. `planning-v4-{prompt,reference,resolutions,readme,hashes}` preserves the complete preceding current packet after its hashes were verified. The current prompt supersedes its eager-every-quote design, packing requirement, mutable defaults proposal and older pending decisions.

`topology-v5.block-51532116.json` records independent historical HQ/MC/desk reads and priorities `[1,8,2,9,4,5]` at hash `0x2d63b25e62be864d40eabbe4a08d536121d44c7ff6406b50550935c9d4a0890a`. HTTP 429 interrupted later inventory; the artifact is explicitly incomplete. It does not prove all six Undy assets' dependencies/fallbacks or authenticate deployed source builds. `source-registry-delay-v5.block-51532116.json` records the separate successful PriceDesk source-delay read of zero at the same pin; HQ replacement delay is a different setting.

`vyper-struct-member-probe-v5.json` contains exact Vyper 0.4.3 source, runtime opcodes and SLOAD counts: one member/one read, two members/two reads, full struct/three reads. It corrects the inference that three storage slots force three reads for every getter. The reviewer's absolute gas figures and production layout performance were not rerun.

`anvil-estimator-smoke-v5.py` and its JSON output preserve a synthetic, non-fork local smoke using Anvil 1.3.5, loopback only, zero generated accounts, synthetic addresses and no private keys or `.env`. It estimates 43,106 gas, restores the same local snapshot for each run, and verifies the same SSTORE result with estimated versus 100,000 gas. The separate `*-sandbox.json` records the initial listener permission failure; a permitted retry succeeded and terminated the node. It is not Base qualification or a D01 contract regression. Re-running requires selecting the documented binary, setting `PRICEDESK_REVIEW_OUTPUT` (the JSON is a generated output), and verifying the chosen port is unused before launch. This historical smoke script is evidence, not the production qualification runner.

This review also inspected pinned D01 and Teller's 500k fail-open call, current feed-decimals helpers, LocalGov authorization, and local Underscore Appraiser caller sites. It did not implement production guards, alter third-party repositories, run actual Base fault injection or broadcast any live transaction. The actual historical source/dependency audit and full caller inventory are implementation prerequisites.

Copy this packet using `packet-hashes.json` as an allowlist (plus the inventory itself). Ignore `.claude/`, including the reviewer-created empty `.cc-writes` directory, and any unlisted files. Nothing in those directories is an implementation instruction or packet evidence.

## Revision-6 checks

`reviewer-v6.txt` preserves the complete latest feedback. `planning-v5-{prompt,reference,resolutions,readme,hashes}` preserves the preceding packet byte-for-byte, including its Pool-1 references. All current design decisions have since been approved. The separate Pool-1 supplement and its pinned evidence were preserved unchanged.

`teller-runtime-size-v6.json` records a synthetic local deployment of unchanged Teller using Vyper 0.4.3 / Titanoboa 0.2.7, synthetic HQ address 1, paused true and Curve ID 2. The complete code is 24,552 bytes including immutables, leaving 24 bytes below 24,576. Its source and directly inspected module/interface hashes match the pinned PR tree. Task-local caches were used. The first harness attempt used a nonexistent top-level Boa cache setter; the corrected `boa.interpret.set_cache_dir` run succeeded. This is a local runtime measurement, not a fresh on-chain read or a measured relay implementation.

The final review inspected actual Curve authorization, Teller's raw-call success/event behavior, pinned PriceDesk constructor defaults and historical staging-test argument bindings. It did not implement the new guards/relay, run contract regressions or run a full suite. Packet links, archive preservation and file hashes were checked separately. New prompt/reference scope is intentionally much smaller; previous release requirements are retained as deferred work, not silently discarded.

## Revision-7 final handoff review

The owner requested continuous execution, a dedicated branch/worktree, affected tests only and plain reliability language. A persistent worktree was created from `bdf7f3da7113aabde60ab8eceab6a960a841bb88` on `codex/pricedesk-configurable-gas`; packet files were copied only after their revision-6 hashes passed. Final planning edits are confined to that worktree. The original packet remains unchanged; this copy is authoritative. No contract implementation or contract test execution occurred in this final review. Active runtime figures still refer to the recorded revision-6 measurement, not an implemented relay.
