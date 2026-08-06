# Track 6 S5 Checkpoint 0 Owner-Decision Packet

**Status:** Owner direction, the isolated-probe authorization, the named owner,
and direct rows 7/9 risk decisions are recorded. Independent-security,
operations, deployment, live-proof, and final Checkpoint 0 closure remain
pending. Stage B is not authorized.

**Prepared:** 24 July 2026

**Owner-decision state:** On 24 July 2026, after a walkthrough of the
recommended design, unchanged behavior, alternatives, and residual risks, the
owner gave the general approval response quoted in section 9. The owner then
directly confirmed that the human approver is **Mick Hagen**, accepted row 7's
preserved external-housekeeping risk instead of expanding S5 into Teller, and
accepted row 9's strict fail-closed ArbSys availability risk with no
ancestor-number fallback, subject to proof, monitoring, and an incident
runbook. Section 9 preserves the exact questions and verbatim numbered
answers. Rows 2 and 13 remain blocked on live/final evidence, row 11 remains
blocked on S5 recreation and revalidation after H-01, and every named
security/operations gate remains open.

**Purpose:** Decide whether the S5 Ledger action-block work may proceed from
evidence-only Stage A to a narrowly bounded production implementation.

**Controlling posture:** Make the fewest production smart-contract changes
necessary for the Robinhood launch. Prefer unchanged behavior, configuration,
omission, or explicit residual-risk acceptance over a broader portability or
future-proofing design.

## 1. Authority and current state

This packet summarizes, but does not replace, the complete S5 Stage A record.
Reviewers must read the complete record before approving a row.

| Authority | Identity |
| --- | --- |
| S5 task contract | `docs/chains/rh/track-6-s5-ledger-guard.md` |
| S5 evidence branch | `rh-track-6-s5-ledger-guard` |
| Frozen S5 evidence package | `6652a10e4de2a74ca27be0da94be4331aeef18f6` |
| Frozen S5 evidence tree | `c21fdef7f6156abac1da606492c7e0329315b693` |
| Complete decision record | `docs/chains/rh/ledger-guard-security-decision.md` at the frozen evidence package |
| Decision-record SHA-256 | `c425bd57201d268e39b2f3fac7e0c0999f1fa2b7bfab74605f4ed96329505095` |
| Production Ledger in Stage A | Unchanged; Git blob `ef02462508e01f59e8f8112ffce0ca8d17d4d0b8` |
| Isolated probe result | Local tests pass; no live Robinhood RPC proof has run |
| H-01 dependency gate | Integrated on `rh` at merge `575d47b82055b42da2bddf1535d8076cd7cf4c63`; post-integration evidence committed at `26eb3a78668d623be40ed2b6e16f52c919906a12`; S5 recreation and revalidation remain pending |
| S4 overlap | Closed as no-code for the initial launch; S4 Stage B/C prohibited |

The original integration baseline used while preparing this packet was
`03c07f01dda03a5529c602aafbfe5545ae86df69`, with tree
`e825aae0408748319f1f88f4fe00a3cf44b9048a`. Local `rh` and `origin/rh`
resolved to that correctly labeled Track 8 M0 integration commit. At owner
response, local and remote `rh` instead resolved to exact post-H-01 evidence
commit `26eb3a78668d623be40ed2b6e16f52c919906a12`. The S5 evidence branch has
not yet been reconciled to that newer baseline, so no current-baseline
validation or implementation authority is inferred from the owner response.

### 1.1 Verbatim authority for the four-file probe exception

The written Stage A contract originally authorized only the decision record.
On 24 July 2026, the owner later expanded that boundary with this direct
instruction:

> This authorizes the narrow Stage A correction and a Robinhood testnet-only
> proof. It does not authorize production Ledger implementation, mainnet
> activity, merge, or deployment.

The same instruction specified the isolation boundary verbatim:

> - test-only Vyper contract under `contracts/testing/`;
> - runner under `scripts/probes/`;
> - focused local tests under `tests/probes/`; and
> - a sanitized evidence record under `docs/chains/rh/evidence/`.

The same message preserved the stop boundary:

> After completing the work, leave the repository changes uncommitted for
> security review. Report every changed file, all commands and test results,
> all sanitized testnet evidence, any inconclusive topology, and the exact
> remaining Checkpoint 0 blockers. Do not begin S5 Stage B, merge, push, or
> modify the production Ledger.

That authorization maps exactly to:

- `contracts/testing/ActionBlockIdentityProbe.vy`;
- `scripts/probes/action_block_identity_probe.py`;
- `tests/probes/test_action_block_identity_probe.py`; and
- `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md`.

The owner also required the result to remain uncommitted for security review
at that checkpoint and prohibited Stage B, merge, push, and production-Ledger
modification. Later on 24 July 2026, Mick Hagen authorized the local evidence
commit:

> Then commit exactly the five reviewed S5 files locally and return the commit
> hash and final file hashes for verification. Do not push or merge. Keep all
> 14 Checkpoint 0 rows pending. The next substantive gates remain H-01
> integration and the separately approved Robinhood testnet proof; Stage B and
> Stage C remain prohibited.

After the initial local commit, Mick Hagen reported the independent
verification result and authorized a message-only amend:

> The five-file Stage A commit is independently verified byte-for-byte. Please
> amend only the commit message from docs(rh): record S5 ledger guard Stage A
> probe to test(rh): add S5 action-block probe and evidence, then report the new
> commit hash. Do not modify file contents, push, merge, contact an RPC, or
> begin Stage B/C. The branch remains frozen pending H-01 integration, the
> approved Robinhood testnet proof, all Checkpoint 0 decisions, and later
> inventory reconciliation.

The authorized message-only amend produced frozen evidence commit
`6652a10e4de2a74ca27be0da94be4331aeef18f6` with the same verified tree.

The preserved report does not name the independent verifier, so this packet
attributes the statement to Mick Hagen's report rather than inventing a
reviewer identity. Neither instruction expanded the probe or production scope.
No live RPC proof, signing, broadcast, production implementation, inventory
edit, merge, push, or deployment authority is inferred from either
instruction.

The frozen decision record at evidence commit `6652a10` retains the earlier
unquoted authorization assertion in its §2.1. This packet §1.1 supersedes that
paragraph **only as the authoritative provenance record for the four-file
probe exception and local evidence commit**. The frozen record and tree remain
unchanged.

## 2. What S5 is—and is not—trying to preserve

The selected property is:

> For a user subject to the guard, a second checked action in the same actual
> execution block must fail.

This is deliberately not:

- a twelve-second cooldown;
- a one-transaction-per-ancestor-block rule;
- a rate limit;
- oracle-freshness protection;
- a general flash-loan theorem;
- a general reentrancy guard; or
- a prohibition on every lower-risk action in the block.

The current ordering remains asymmetric:

- every successful housekeeping call writes the user's last-touch identity;
- only the current six higher-risk actions check whether that identity was
  already used;
- a lower-risk touch can therefore arm and block a later checked action in the
  same action block;
- a checked action followed by a lower-risk touch remains allowed; and
- an Underscore-classified wallet or vault skips the equality assertion but
  still writes the identity.

Underscore is omitted from the initial Robinhood launch. The shared-source
exemption is retained only for Base and possible future compatibility; no
Underscore registry should be configured on Robinhood at launch.

The current Ledger does not reject a zero-address user. When Teller supplies
`address(0)`, Ledger succeeds and writes the selected action-block identity to
`lastTouch[address(0)]`. Every zero-address use therefore shares one guard key,
which can create surprising cross-path coupling. S5 recommends preserving that
observed behavior, with an exact regression test and explicit risk acceptance,
rather than adding a separate identity-policy change.

Current source and test evidence does not establish a successful production
Teller path that persists that key. Borrow is a proven attempted-but-rolled-back
route: Teller reaches Ledger and attempts the zero-key write first, then
CreditEngine rejects the zero user, and the downstream revert rolls back the
entire transaction. The current vault modules contain zero-user and
zero-recipient rejections, while a zero-user liquidation that returns without
liquidation touches the keeper, not the supplied liquidation user. Other
parameterized paths can syntactically receive zero, but a transfer, permission,
or economic check can revert anywhere in the same transaction—before or after
housekeeping—and roll back any Ledger write. Therefore the shared-key coupling
is a proven direct-Ledger behavior, and its attempted reachability through
borrow is proven, but no successful persistent Teller route is established
until the complete entry-point regression matrix pins reachability and order.

The sole current external-housekeeping caller is already proven closed for this
specific key: `Deleverage.swapCollateral` rejects an empty `_user` before any
value movement or housekeeping. The remaining reachability question is limited
to Teller's other internally routed user, recipient, keeper, liquidator, and
delegate identities.

## 3. Minimum-change stress test

| Option | Production change | Result | Disposition |
| --- | --- | --- | --- |
| Keep native `block.number` on Robinhood | None | Uses ancestor height, so distinct child blocks can share an identity and ordinary users can be falsely throttled beyond one real execution block | Reject; it does not honor the owner-selected property |
| Disable `shouldCheckLastTouch` on Robinhood | Configuration only | Avoids false throttling but removes the selected same-block protection | Reject; it changes the approved security posture |
| Convert the guard to elapsed time | Shared Ledger/Teller policy change | Implements a cooldown rather than same-block identity | Reject |
| Deploy a generic clock-provider contract | Ledger plus a new production contract/interface/deployment | Can be portable, but adds a deployed artifact, call frame, manifest, and failure boundary | Reject as larger than necessary |
| Put one immutable source discriminator in canonical `Ledger.vy` | One production contract plus tests and its ABI | Zero selects native `block.number`; exact `0x64` selects only `arbBlockNumber()`; every other value rejects | **Recommend as the smallest sufficient change** |
| Add a Robinhood-specific Ledger or `chain.id` branch | Chain-specific production logic | Creates permanent source divergence | Reject |
| Replace the deployed Base Ledger | Stateful Base migration | Risks losing or corrupting non-enumerable debt, locks, rewards, auction, and accounting state | Reject |

The recommended production blast radius is one shared contract:
`contracts/data/Ledger.vy`. Robinhood deploys it fresh. The deployed Base
Ledger remains untouched indefinitely.

## 4. Recommended minimal design

Subject to the live proof and remaining approvals:

1. Add one immutable address-valued source discriminator to canonical
   `Ledger.vy`.
2. Interpret the zero address as native EVM `block.number`.
3. Interpret exactly
   `0x0000000000000000000000000000000000000064` as the ArbSys precompile and
   call only `arbBlockNumber()`.
4. Reject every other constructor value.
5. On the `0x64` path, require a successful constructor-time call and valid
   ABI decode.
6. Expose only a read-only getter for the immutable source.
7. Do not add a mode immutable, generic provider, arbitrary selector,
   `chain.id` branch, fallback, per-touch event, mutable source, or
   per-user nondecrease assertion.
8. Preserve the current equality check, write ordering, locks, pause behavior,
   high-risk set, identities, Boolean governance control, and Underscore
   exemption.

The published Robinhood profile and pinned Nitro sources imply that profile
`61` should produce a raw `ArbSys.arbOSVersion()` return of `116`. That pair is
a preflight identity check, not a substitute for proving that
`arbBlockNumber()` agrees with actual Robinhood receipt child-block identity.

## 5. Risks the owner and security reviewer must accept—or use to reject the
design

### 5.1 Preserving the existing external-housekeeping surface

Any address accepted by `addys._isValidRipeAddr` can call Teller's external
housekeeping surface and supply the target user, risk flag, debt-update flag,
and an optional Addys bundle. A valid protocol caller can therefore:

- write a victim's last-touch identity;
- make a later checked action for that victim fail in the same child block;
- force debt and snapshot work; and
- supply the housekeeping address bundle.

No direct asset-theft or privilege-escalation result is established by Stage A,
and the intended denial window becomes one Robinhood child block when the
selected source works. The residual griefing and caller-supplied-bundle surface
is nevertheless real.

The sole current in-repository caller of this external Teller surface is
`Deleverage.swapCollateral`. It is not the Underscore
`deleverageForWithdrawal` path, and a zero deleverage cooldown does not disable
it. Row 7 therefore cannot be accepted on the theory that S4 and Underscore are
dormant.

The caller is limited to governance or valid Ripe addresses. A successful
swap withdraws the user's existing collateral to that authorized caller,
requires the caller to transfer real replacement collateral, prices the two
legs to the same USD value through PriceDesk, requires the replacement asset's
configured LTV to be at least the withdrawn asset's LTV, and deposits the
replacement into the user's position before housekeeping. The caller therefore
cannot arm the guard through this path as a free no-value ping, and the
configured value/LTV checks are intended not to reduce the user's borrowing
power. Those facts strengthen the one-child-block griefing acceptance case,
subject to the existing token, oracle, and configuration trust assumptions.

The counterweight is equally important: `swapCollateral` lets an authorized
caller forcibly exchange a user's collateral. That pre-existing trusted-caller
and value-moving authority is broader than housekeeping griefing and is outside
S5's clock-source scope. Row 7 acknowledges it as the context of the only live
caller; it does not silently expand S5 to redesign or newly ratify the full
economic policy of forced collateral swaps.

**Minimum-change recommendation:** accept this existing behavior for the
initial launch. Narrowing it would add Teller and its authorization/ABI surface
to S5, materially increasing the production and audit scope. If this risk is
not accepted, reject the proposed Stage B file set and write a separately
reviewed Teller-hardening slice; do not expand S5 silently.

### 5.2 Fail-closed ArbSys availability

The recommended design has no ancestor-number fallback. If the configured
ArbSys call later reverts, returns malformed data, or becomes unavailable,
Ledger housekeeping fails closed.

That failure blocks all Teller paths that perform housekeeping, including:

- repayment;
- `liquidateUser`; and
- `liquidateManyUsers`.

The liquidation transactions revert atomically even though housekeeping occurs
after AuctionHouse work. This is a solvency-defense availability risk, not a
minor diagnostics issue.

The existing `shouldCheckLastTouch` Boolean is **not an emergency source
bypass**. Teller passes only the derived per-call check Boolean to Ledger, and
Ledger still writes `lastTouch` when it is false. Preserving that write means
the action-block source is still read even when the global check is disabled.
Creating an emergency bypass would require a larger semantic or Teller ABI
change, a fallback, or a mutable source—each of which changes the approved
property or expands the blast radius.

The availability risk should be calibrated against the chain boundary. ArbSys
at `0x64` is a chain-core Arbitrum precompile, not an optional application
service. After constructor validation, live receipt-agreement proof, and soak,
its runtime failure would ordinarily indicate a Robinhood chain malfunction;
blocked repayment during that incident is therefore unlikely to be an
independent application failure on an otherwise healthy chain. This makes the
marginal risk over baseline chain availability small, but not zero:
misconfiguration, an incorrect ABI/artifact, or a future incompatible chain
upgrade remain S5-specific failure modes and are why activation evidence,
monitoring, and an incident runbook are still mandatory.

**Minimum-change recommendation:** retain strict fail-closed behavior with no
fallback, and require activation proof, soak evidence, monitoring, and an
incident runbook. Accept explicitly that a precompile failure can suspend
repayment and liquidation. If that availability risk is unacceptable, stop
S5 and design a separately reviewed emergency mechanism before implementation.

### 5.3 Permanent Base/Robinhood live-version divergence

Base keeps the existing Ledger bytecode and state. Robinhood is the first
production deployment of the revised shared source. This creates intentional,
permanent live-bytecode divergence for a custody/accounting-bearing component.

**Minimum-change recommendation:** accept the divergence. Record the exact
address, runtime hash, source/artifact identity, constructor source, and
chain-specific operational implications. Do not create a Base convergence
deadline.

## 6. Checkpoint 0 decision recommendations

“Owner approved” does not mean closed. Each row also needs every security,
operations, deployment, live-evidence, or external-review gate named in the
Stage A record.

| Row | Decision | Recommendation now | Closure state |
| --- | --- | --- | --- |
| 0 | Owner direction | Confirm same-real-block property, native ordinary-EVM source, Robinhood child-block source, and listed non-goals | **Owner approved; security decision pending** |
| 1 | Abstraction shape | Approve the single immutable internal discriminator; reject provider/mode/chain-specific alternatives | **Owner approved; security decision pending** |
| 2 | Clock-source contract | Approve the proposed zero/`0x64`/reject-all-other policy in principle; require live `arbBlockNumber()` and receipt agreement before closing | **Owner approved in principle; blocked on approved live proof and security closure** |
| 3 | Arming semantics | Preserve any-touch write and later checked-higher-risk rejection, including same-block griefing possibility | **Owner approved; security decision pending** |
| 4 | High-risk set | Preserve exactly `withdraw`, `withdrawMany`, `rebalance`, `borrow`, `claimFromStabilityPool`, and `claimManyFromStabilityPool` | **Owner approved; security decision pending** |
| 5 | Underscore policy | Preserve shared-source exemption; omit Underscore registry from initial Robinhood graph | **Owner approved; security decision pending** |
| 6 | Identity policy | Preserve every current user/recipient/keeper/liquidator/delegate choice; preserve direct Ledger zero-address behavior; no successful Teller-to-zero-key path is presently established, so Gate 1 must pin every entry point's reachability and stop on any unexpected successful path | **Owner approved; security decision and mandatory Stage B reachability evidence pending** |
| 7 | External housekeeping | Accept existing valid-Ripe-caller grief/Addys/debt surface for the initial launch; do not add Teller to S5 | **Owner directly accepted risk; security approval pending** |
| 8 | Configuration/compatibility | Keep the existing Boolean and governance/default surfaces; add only the immutable source getter; no event | **Owner approved; security and operations decisions pending** |
| 9 | Lock/pause/failure | Preserve locks and pause; accept that source failure blocks repayment and both liquidation entry points; no fallback | **Owner directly accepted availability risk; security approval pending** |
| 10 | Base live version | Permanently retain deployed Base Ledger; no migration or convergence | **Owner approved; security and operations decisions pending** |
| 11 | H-01/S4 sequence | S4 no-code disposition is compatible; H-01 is integrated; recreate S5 on exact `rh` by default; reconciliation in place is exceptional and needs express owner/security approval | **Integration satisfied; recreation and revalidation pending** |
| 12 | Stage B ownership | Approve only the file ceiling in section 7 below; any expansion returns to Checkpoint 0 | **Owner approved; security decision pending** |
| 13 | Evidence bar | Approve the evidence standard and require a targeted external review of the exact Ledger/precompile change; live proof and final evidence remain outstanding | **Owner approved in principle; live proof, final evidence, and external-review decision remain open** |

## 7. Proposed Stage B file ceiling

Approval means these files may be changed only where necessary. It does not
require changing every listed test.

### Production

- `contracts/data/Ledger.vy`

### Tests and fixtures

- `tests/conf_core.py`
- `tests/data/test_ledger.py`
- `tests/data/test_ledger_action_block.py`
- `tests/core/teller/test_teller_deposit.py`
- `tests/core/teller/test_teller_withdraw.py`
- `tests/core/teller/test_teller_rebalance.py`
- `tests/core/creditEngine/test_credit_borrow.py`
- `tests/core/creditEngine/test_credit_repay.py`
- `tests/vaults/modules/test_stab_vault_claims.py`

The Stage B regression must cover every housekeeping entry point in the frozen
call graph with its zero-address-capable user, recipient, keeper, liquidator,
and delegate inputs. It must record whether the call reaches Ledger and can
succeed end to end, prove that a revert anywhere in the same transaction—before
or after housekeeping—leaves `lastTouch[address(0)]` unchanged, and identify
whether any successful route is lower or higher risk. An unexpected successful
Teller-to-zero-key route stops Gate 1 and returns row 6 to the owner and
security reviewer; it is not silently accepted by this packet.

### Generated artifact and implementation record

- `scripts/abis/Ledger.json`
- `docs/chains/rh/ledger-guard-implementation-record.md`

No production provider or interface file is approved. If Vyper compilation
proves an external interface file is necessary, stop and return with its exact
path and reason.

The following remain prohibited in Stage B:

- Teller, TellerUtils, MissionControl, Switchboard, or Defaults changes;
- any Robinhood-specific production contract or `chain.id` branch;
- dependency or lock-file changes;
- historical migrations or manifests;
- Track 7 migration `0030_Track6S5LedgerGuard.py`;
- S2 inventory changes before Stage C;
- Base deployment or migration;
- Robinhood deployment, configuration, activation, signing, or transaction;
- Underscore source; and
- `rh-summary.md` or shared planning-register edits.

## 8. Items that must remain open

### 8.1 H-01 baseline

H-01 is approved and integrated. S5 must be recreated from that exact `rh`
baseline by default and repeat compiler/runtime capture, artifact hashes,
targeted tests, S1, S2, and the full suite. Reconciliation in place is an
exception only if the owner and independent security reviewer expressly
approve it against the exact stale-branch/current-`rh` diff.

### 8.2 Live Robinhood proof

Before any live preflight or transaction, a separate secret-free approval
packet must name:

- RPC endpoint label, environment-variable name, and endpoint fingerprint;
- expected published profile `61` and raw ArbSys version return `116`;
- signer address and private-key environment-variable name, but no secret;
- signer-funding approval;
- nonce and predicted deployment address;
- exact probe creation/runtime hashes and selector;
- transaction-count bound;
- gas limits, EIP-1559 limits, and maximum total fee;
- observation count and topology cases;
- timeout;
- dated owner, security, and deployment approval.

The proof must establish:

- live `0x64` code/precompile behavior;
- raw version return `116`;
- `arbBlockNumber()` agreement with Robinhood receipt child-block identity;
- two observations in one child block if feasible;
- observations in successive child blocks;
- repeated ancestor `block.number` across distinct child blocks if observable;
- deterministic signed-transaction journaling and hash matching; and
- no fallback behavior.

Inconclusive topology evidence does not become a protocol fact.

### 8.3 Targeted external review

Because the production diff affects a protocol-wide Ledger gate and makes
ArbSys availability a repayment/liquidation dependency, this packet recommends
a targeted independent external security review before activation. The review
may be narrowly scoped to:

- the exact `Ledger.vy` diff;
- constructor/staticcall ABI and decode behavior;
- storage and immutable layout;
- all Teller housekeeping paths and preserved identities;
- failure, pause, lock, and rollback behavior;
- external-housekeeping griefing acceptance; and
- live proof, activation, monitoring, and incident response.

If the owner chooses not to require that review, the decision must explicitly
accept the residual risk; silence does not waive it.

## 9. Owner approval record

On 24 July 2026, after the owner was walked through the underlying guard, the
minimal Ledger-only design, every preserved behavior, the larger alternatives,
the row 7 external-housekeeping risk, the row 9 fail-closed availability risk,
the remaining gates, and the actions not being authorized, the owner replied:

> okay. this makes sense. I approve them. let's keep moving forward.

That utterance is preserved as evidence of general assent, but it does not by
itself meet this task contract's approval standard. The exact follow-up
questions were:

1. What human name should be recorded as the owner approver? Git identifies
   `Mick Hagen`, but I will not treat Git configuration as owner evidence
   without your confirmation.
2. Row 7: Do you explicitly accept the preserved external-housekeeping
   griefing and caller-supplied bundle risk for launch, instead of expanding S5
   into Teller hardening?
3. Row 9: Do you explicitly accept that ArbSys failure may block repayment and
   both liquidation entry points—with no ancestor fallback—subject to proof,
   monitoring, and an incident runbook, instead of requiring an
   emergency-bypass design?

The owner replied verbatim:

> 1. yes
> 2. yes
> 3. yes

**Transcript-channel note:** the implementation-task transcript used as the
direct authority for this packet records the numbered reply above. A separate
reviewer reports witnessing the semantically identical single-line reply
`yes, yes, yes` in its own channel. This channel-level presentation difference
does not change the one-to-one decision mapping or any approval condition.

The numbered answer maps one-to-one to the enumerated questions above. The
formal owner record is therefore:

| Required field | Recorded value |
| --- | --- |
| Decision date | 24 July 2026 |
| Human approver | **Mick Hagen**, directly confirmed by answer 1; not inferred from Git identity |
| Evidence package reviewed | `6652a10e4de2a74ca27be0da94be4331aeef18f6`, tree `c21fdef7f6156abac1da606492c7e0329315b693` |
| General utterance | Preserved verbatim above |
| Row 7 direct answer | **Yes**, answer 2: accept the preserved external-housekeeping griefing and caller-supplied bundle risk for launch instead of expanding S5 into Teller hardening |
| Row 9 direct answer | **Yes**, answer 3: accept strict fail-closed ArbSys availability—including blocked repayment and both liquidation entry points—with no ancestor fallback, subject to proof, monitoring, and an incident runbook |
| Conditions | Every live-proof, H-01 recreation/revalidation, security, operations, deployment, external-review, implementation, inventory, merge, activation, governance, and Base-migration gate stated in this packet |

The contract-complete owner scope is:

- rows 0, 1, 3, 4, 5, 6, 8, 10, and 12: owner approval subject to their named
  independent-security and operational approvals;
- row 7: explicit acceptance of the existing external-housekeeping griefing
  and caller-supplied bundle risk for initial launch;
- row 9: explicit acceptance of strict fail-closed ArbSys availability,
  including blocked repayment and both liquidation entry points, with no
  ancestor-number fallback, subject to proof, monitoring, and an incident
  runbook;
- rows 2 and 13: approve in principle only, while keeping live proof, final
  validation, and the external-review decision open; and
- row 11: keep open for recreation and revalidation on the integrated H-01
  baseline.

This owner approval authorizes no RPC access, signer or secret use,
transaction, Stage B implementation, inventory change, merge, push,
deployment, configuration, activation, governance action, or Base migration
unless a later authorization says so expressly.

The row 6 approval preserves the direct-Ledger behavior only. It remains
conditioned on the Stage B entry-point matrix above; an unexpected successful
Teller-to-zero-key route returns for a new owner/security decision before Gate
1 can close.

## 10. Workflow after decisions

1. Obtain complete-file independent-security review of this packet and the
   frozen Stage A record.
2. Preserve this named owner record and its direct rows 7/9 answers without
   marking blocked rows closed.
3. Treat H-01 integration as complete at `575d47b82055b42da2bddf1535d8076cd7cf4c63`
   with post-integration evidence at
   `26eb3a78668d623be40ed2b6e16f52c919906a12`.
4. Recreate S5 on that exact post-H-01 `rh` baseline by default and rerun every
   required baseline and focused validation. Reconcile the stale branch in
   place only as an expressly owner/security-approved exception.
5. Obtain separate authorization and run the bounded live Robinhood proof.
6. Close the remaining Checkpoint 0 rows with owner, security, operations, and
   deployment provenance.
7. Authorize Stage B against the exact file ceiling.
8. Implement the one-contract change and run Gate 1 review.
9. Reconcile S2 inventory in separately authorized Stage C.
10. Run Gate 2 review before any merge.

Until those steps finish: no production Ledger change, Stage B, Stage C,
merge, deployment, activation, signing, or governance action is authorized.
