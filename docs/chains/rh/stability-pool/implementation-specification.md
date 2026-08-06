# Robinhood Stability Pool hardening implementation specification

> [!IMPORTANT]
> **Implementation handoff, not implementation authority.** This document is
> precise enough for a fresh agent to build and validate an isolated candidate.
> It does not authorize integration, deployment, configuration, activation,
> signer use, or release. Stop at every gate stated below.

> [!NOTE]
> **As-built record added 2026-08-05.** The original specification below is
> preserved as the design record. The owner-approved implementation and later
> adversarial validation produced several deliberate differences. Where the
> original prescriptive text conflicts with the as-built outcome immediately
> below, the as-built outcome describes the finished candidate. It still does
> not authorize integration, deployment, activation, signer use, or release.

## As-built outcome (2026-08-05)

The Tier A+B candidate was implemented and validation metadata was closed at:

| Field | Final value |
| --- | --- |
| Candidate commit | `e603dcee4a22c1c5100191c72ea1a23de1b40c22` |
| Candidate tree | `815b369e98308d5a79b6a41f283c107b76bd1d10` |
| Source implementation commits | `38dd2e1874705e7fb2a60a5ddc477e56edca94d4`, `99fee938257a154503b04b6a364f2507c20d2887`, `a265b3e9d7cb47d5c2d4ffccc7c8a05418e3a765` |
| `StabilityPool.vy` SHA-256 | `421e2bfbffefd1f44012af0a08416a135e07436132c999d6ff1d518ef04d3681` |
| `StabVault.vy` SHA-256 | `d8b40ec77714ff21b822963a069d4db2e411e733509a83efbd418b86aacd8c77` |
| Compiler | Vyper `0.4.3` with `# pragma optimize codesize` |

The final owner decisions and security corrections are:

1. `getTotalValue` and `getTotalUserValue` remain in the StabilityPool ABI for
   off-chain consumers. `valueToShares` and `sharesToValue` are not exported by
   the wrapper.
2. `canActivateClaimAsset` remains implemented in the StabVault module but is
   not exported by StabilityPool. Exporting it on the final candidate measured
   `25,067` deployed runtime bytes, `491` bytes above EIP-170.
3. `pruneClaimableAssets` remains permissionless in either pause state.
   `activateClaimAssets` remains permissionless but now requires the pool to be
   paused. This closes the reproduced unpaused dormant-NAV capture sequence.
4. The deposit path rejects the current GREEN address supplied through
   `Addys`, closing the reproduced RipeHq re-point admission bypass. GREEN and
   sGREEN remain constructor-bound immutables for valuation under the owner's
   chain invariant that those addresses never change.
5. StabilityPool-specific recovery wrappers remain and reject recovery of any
   token with a nonzero aggregate active or dormant claim liability.
6. Tier C automatic quarantine/retirement remains deferred.

Final bytecode and ABI evidence is:

| Measurement | Result |
| --- | ---: |
| Creation bytecode | `24,857` bytes |
| Runtime template | `24,472` bytes |
| Constructor-bound immutable data | `96` bytes |
| Deployed runtime | `24,568` bytes |
| EIP-170 headroom | `8` bytes |
| StabilityPool ABI | `65` entries; semantically identical to the committed ABI |

Focused validation completed on an isolated source-correct test fixture:

- Stability Vault module suites: `142 passed`, comprising `139` deterministic
  tests plus three Hypothesis properties that execute `70` generated examples
  inside Boa state anchors. The deterministic and generated mutation models
  reassert pair balances, aggregate liabilities, indexes, slots, counts,
  states, and custody after each transition;
- AuctionHouse Stability integration: `23 passed`;
- final exploit-regression selection: `2 passed`; and
- matched first-liquidation-receipt gas: `141,587` baseline versus `221,872`
  candidate, an increase of `80,285` gas (`56.7%`).

The repository branch is not globally green for reasons outside this candidate.
The restored `tests/conf_core.py` fixture correctly supplies the eleventh
Morpho V2 constructor argument, while the branch's `BlueChipYieldPrices.vy`
source currently accepts ten. That unrelated mismatch prevents the exact-tree
Stability tests from reaching their fixtures. The block-clock inventory module
also reports the pre-existing BlueChip, PR #61 artifact, and S5 legacy drift
(`103 passed`, `77 failed`). These signals were preserved rather than hidden by
weakening fixtures or validators.

No deployment, integration, activation, signer, or release action was
performed. The original gates below remain controlling for those later phases.

## 1. Objective

Build the smallest new-deployment Stability Pool hardening candidate that:

1. permanently bounds NAV iteration;
2. prevents first-receipt dust from entering the active NAV list;
3. preserves all received liquidation collateral when pricing or capacity
   prevents activation;
4. lets anyone prune active dust and activate accumulated dormant balances in
   bounded calls;
5. prevents claim accounting from exceeding unaccounted token custody;
6. prevents generic recovery from sweeping tokens backing claim liabilities;
7. prohibits GREEN from becoming a Stability asset and creating a self-claim;
8. proves the post-liquidation exit behavior under the exact launch flags; and
9. constrains oracle and asset admission without adding an unsafe automatic
   quarantine system.

The existing architecture remains intact: pair balances and aggregate
liabilities are the source of truth; only active claim assets are iterable for
NAV. Dormant balances remain claimable and redeemable through the existing
mapping-based paths.

## 2. Bound baseline and start procedure

This specification was authored against:

| Field | Bound value |
| --- | --- |
| Source branch | `rh` |
| Commit | `0e093e2c23eaf6cc931fe7ff15c903a99ea36738` |
| Tree | `8b6028eed43695e13c5192d079f04dd941f0d74f` |
| Compiler | Vyper `0.4.3` |
| Contract wrapper | `contracts/vaults/StabilityPool.vy` |
| Accounting module | `contracts/vaults/modules/StabVault.vy` |

The implementation agent must begin with:

```bash
git status --short --branch
git rev-parse HEAD^{commit} HEAD^{tree}
git diff --check
vyper --version
```

If the implementation baseline differs, stop and rebind this specification to
the new authoritative commit. Do not transplant the patch blindly. Inventory
all changes since the bound tree that touch StabilityPool, StabVault,
VaultData, AuctionHouse, Teller, MissionControl, PriceDesk, Switchboards,
Defaults, ABI export, artifact expectations, or Stability tests.

The implementation candidate must use a clean isolated worktree. Existing
Robinhood evidence/candidate branches are inputs, not mutable implementation
workspaces.

## 3. Controlling design decisions

These choices define the candidate. Changing one requires a design-review
record before code changes continue.

| ID | Decision |
| --- | --- |
| D-01 | Implement Tier A + Tier B from `long-term-hardening-plan.md`; do not implement Tier C quarantine/retirement. |
| D-02 | Modify the shared `StabVault.vy` source because the behavior is safe for every newly compiled Stability Pool. Do not fork unless Gate 1 rejects shared behavior. |
| D-03 | Preserve the existing mapping liabilities and sentinel-index layout. Do not introduce an enum or a second iterable dormant list. |
| D-04 | Hard cap total active claim assets per Stability asset at `12`, including GREEN. Robinhood configuration reserves one slot for GREEN and permits at most `11` non-GREEN routed claim assets. |
| D-05 | Hardcode a `$0.25` activation threshold and preserve the `$0.10` retention/deactivation threshold, both in 18-decimal USD. Activation occurs at `>= $0.25`; deactivation occurs only at nonzero `< $0.10`. |
| D-06 | A zero result from ordinary PriceDesk unavailability leaves the liability dormant and does not trigger PriceDesk's configured-feed raise. It is not proof of a specific oracle failure. Malformed or reverting dependencies remain unsupported and fail closed. |
| D-07 | A full active set leaves new/inactive receipts dormant and emits capacity telemetry. It never rejects a liquidation solely because no active slot is available. |
| D-08 | Use strict shadow-liability receipt accounting: custody must cover existing liability and the reported receipt must not exceed unaccounted custody. Short receipt reverts atomically. Supported collateral must use standard transfer semantics. |
| D-09 | Protect recovery in the StabilityPool wrapper through selective VaultData exports. Do not alter shared VaultData behavior for other vaults. |
| D-10 | Prohibit GREEN as a Stability asset in code and generated Robinhood configuration. GREEN may remain a claim asset for a non-GREEN Stability asset and counts toward the cap. |
| D-11 | Permissionless maintenance is bounded, idempotent, unrewarded, and callable while paused because it moves no custody or shares. |
| D-12 | Do not make NAV fail open on an active configured-but-unpriced asset. Existing fail-closed NAV remains; oracle liveness is controlled through admission, monitoring, pause, and recovery runbooks. |
| D-13 | The full Tier A+B wrapper exceeds EIP-170 unless wrapper ABI surface is reduced. Subject to explicit owner Gate S0 approval, selectively export StabVault and remove only `valueToShares`, `sharesToValue`, `getTotalValue`, and `getTotalUserValue`, which have no production-contract consumers in the bound repository. |

**Gate S0 status: APPROVED by the owner on 2026-08-05.** Approval is limited to
the four D-13 view removals. It does not authorize other ABI changes or any
later lifecycle action.

### 3.1 Required owner/security confirmations

Before production source implementation, record approval or correction of:

1. active cap `12` and the one-slot GREEN reserve;
2. activation/retention thresholds `$0.25/$0.10`;
3. shared-module change rather than a Robinhood-only fork;
4. strict short-receipt rejection rather than partial credit;
5. code-level GREEN Stability-asset prohibition; and
6. the launch claim/redemption flags used for post-crash exits; and
7. removal of the four unused external views required by D-13.

Item 6 has an operational composition to resolve. The bound
`DefaultsRobinhood.vy` source and canonical Robinhood parameters enable general
claims and redemptions at launch. Separately,
`config/robinhood-reward-launch-plan.json` contains an emergency reward-runway
step that disables Stability claims. Do not silently change either decision.
Prove the ordinary launch exit with both flags enabled, then determine how a
zero-raw-balance shareholder exits while that emergency claim-disable step is
active, including exact re-enable authority and criteria. This decision blocks
the incident-mode exit acceptance gate, not the registry/accounting
implementation.

## 4. Risk-to-control map

| Current risk | Candidate control | Residual risk |
| --- | --- | --- |
| One stale configured feed reverts basket NAV and dependent operations | Keep fail-closed NAV; restrict admitted sources; add revert-matrix tests, monitoring, and pause runbook | Pool and affected AuctionHouse traversal remain unavailable until feed recovery/reconfiguration |
| Active claim list can grow forever | Hard active cap of 12 | Dormant mapping pairs can accumulate but are not iterated |
| One-base-unit first receipt becomes active | Add-time cumulative USD activation gate | Unpriced or sub-floor value remains outside NAV |
| Existing dust cleanup only deactivates | Add bounded permissionless activation and pruning | Keeper responsiveness is operational, not automatic |
| Capacity rejection could revert liquidation after collateral transfer | Credit first, then leave dormant when full | A material dormant balance can temporarily be excluded from NAV; capacity alarms require immediate response |
| Entire token custody can mask a short receipt | Credit only against custody minus prior aggregate liability; strict reported-receipt check | A pre-existing unaccounted donation can still mask a same-token transfer shortfall because no pre-transfer snapshot exists |
| Custody falls below aggregate claim liability | Strict receipt check fails closed | Later receipts of that token, and liquidations routed into the pool for it, revert until the deficit is resolved |
| Generic recovery can sweep claim backing | Wrapper recovery requires aggregate claim liability zero | Surplus of a token with live liability remains intentionally unrecoverable |
| GREEN-as-Stability can self-credit and double-count | Contract and configuration prohibition | A future redesign must explicitly revisit the prohibition |
| Raw Stability balance can reach zero while shares remain | Deterministic exit tests and launch flag assertion | Exit still depends on healthy claim pricing unless a larger in-kind exit design is approved |
| Weak oracle can misprice claims | Manipulation-resistant primary-source admission; forbid spot-AMM-only pricing | Governance/source compromise remains outside this slice |
| Full Tier A+B wrapper exceeds EIP-170 | Selective StabVault exports remove four production-unused views | Off-chain consumers of those views must migrate; final source must be recompiled and measured |

## 5. Allowed implementation surface

The default source/test ceiling is:

| Path | Allowed work |
| --- | --- |
| `contracts/vaults/modules/StabVault.vy` | Constants, events, receipt accounting, activation/deactivation helpers, maintenance methods, views, GREEN guard |
| `contracts/vaults/StabilityPool.vy` | Selective StabVault/VaultData exports, four-view ABI reduction after Gate S0, and guarded recovery wrappers |
| `tests/vaults/modules/test_stab_vault_hardening.py` | New focused deterministic and invariant-style tests |
| `tests/vaults/modules/test_stab_vault.py` | Update assumptions broken by add-time threshold/cap only |
| `tests/vaults/modules/test_stab_vault_claims.py` | Preserve/extend dormant claim behavior |
| `tests/vaults/modules/test_stab_vault_redemptions.py` | Preserve/extend dormant redemption and GREEN behavior |
| `tests/core/auctionHouse/` | Composed capacity and stale-feed liquidation cases |
| `tests/vaults/test_stability_pool_recovery.py` | New wrapper recovery tests if a focused file is clearer |
| `scripts/params/generate_robinhood_defaults.py` and its tests | Generated launch-capacity/GREEN assertions only |
| `scripts/abis/StabilityPool.json` | Mechanically regenerated ABI |
| `config/contract-artifact-expectations.json` and inventory files/tests | Mechanically updated identities and source pins required by the reviewed source delta |
| `docs/chains/rh/stability-pool/` | Implementation evidence, gas table, and runbook additions |

Do not modify AuctionHouse production source, PriceDesk production source,
MissionControl storage/config structs, VaultData, Teller production source, or
Switchboard production source without a new Gate 1 scope approval. In
particular, AuctionHouse has minimal EIP-170 headroom and must not be used to
simulate a pre-transfer receipt snapshot in this slice.

Before editing, record the exact changed-path ceiling selected from the table.
After editing, fail the handoff if any unexplained path appears.

## 6. State and count semantics

Do not add stored state for dormant status. Derive it:

| State | `claimableBalances[stab][claim]` | `indexOfClaimableAsset[stab][claim]` |
| --- | ---: | ---: |
| Absent | `0` | `0` |
| Dormant | `> 0` | `0` |
| Active | `> 0` | `> 0` |

Preserve the existing sentinel layout:

- array index `0` is unused;
- `numClaimableAssets == 0` means never initialized/empty;
- otherwise `numClaimableAssets` is the next free index;
- active count is `0` when the stored value is `0`, otherwise
  `numClaimableAssets - 1`; and
- after removing the final active entry, stored `numClaimableAssets` may be `1`.

Add one internal helper and one external view using exactly those semantics:

```text
_getNumActiveClaimAssets(stabAsset) -> uint256
getNumActiveClaimAssets(stabAsset) -> uint256
```

Do not reinterpret the existing public `numClaimableAssets` getter. Existing
integrations may rely on its next-index convention.

Add:

```text
getClaimAssetState(stabAsset, claimAsset) -> uint256
```

Return `0 = absent`, `1 = dormant`, `2 = active`. The return values are ABI
contracts and must be constants in source/tests, not undocumented magic values.

## 7. Constants and events

In `StabVault.vy`, define:

```text
MAX_ACTIVE_CLAIM_ASSETS: constant(uint256) = 12
MAX_CLAIM_ASSET_MAINTENANCE: constant(uint256) = 15
ACTIVATION_USD_THRESHOLD: constant(uint256) = 25 * 10**16
RETENTION_USD_THRESHOLD: constant(uint256) = 10**17
CLAIM_ASSET_ABSENT: constant(uint256) = 0
CLAIM_ASSET_DORMANT: constant(uint256) = 1
CLAIM_ASSET_ACTIVE: constant(uint256) = 2
DEACTIVATION_ZERO: constant(uint256) = 1
DEACTIVATION_DUST: constant(uint256) = 2
DORMANT_BELOW_FLOOR: constant(uint256) = 1
DORMANT_NO_PRICE: constant(uint256) = 2
DORMANT_CAPACITY: constant(uint256) = 3
```

Replace internal references to `DUST_USD_THRESHOLD` with
`RETENTION_USD_THRESHOLD`. Do not change the value or boundary behavior.

Add events:

```text
ClaimAssetActivated(stabAsset indexed, claimAsset indexed, balance,
                    activeCount)
ClaimAssetDeactivated(stabAsset indexed, claimAsset indexed, balance,
                      activeCount, reason)
ClaimAssetLeftDormant(stabAsset indexed, claimAsset indexed, balance,
                      activeCount, reason)
```

Emit `ClaimAssetLeftDormant` only when a receipt changes the pair balance while
the pair remains inactive. Do not emit it from repeated permissionless
activation attempts; that would permit event spam. Existing AuctionHouse events
remain the receipt-level economic record.

## 8. Exact StabVault implementation

### 8.1 Non-raising activation valuation

Add a dedicated internal helper. Do not weaken `_getUsdValue`, which must keep
using `_shouldRaise=True` for active NAV:

```text
_getActivationUsdValue(asset, amount, green, savingsGreen, priceDesk)
```

Behavior:

- amount zero returns zero;
- GREEN returns amount;
- sGREEN calls `convertToAssets(amount)`;
- every other asset calls `PriceDesk.getUsdValue(asset, amount, False)`; and
- a returned zero is only “no usable activation value,” not a dust
  classification or proof of feed state.

The helper must not catch or reinterpret malformed-token or reverting ERC4626
behavior. Those assets are unsupported and must fail admission.

### 8.2 Strict shadow-liability receipt accounting

Change `_addClaimableBalance` to receive the three pricing dependencies needed
for the activation decision. Do not change either AuctionHouse-facing external
selector.

Both `swapForLiquidatedCollateral` and `swapWithClaimableGreen` must resolve or
reuse GREEN, sGREEN, and PriceDesk addresses and pass them internally. The
redemption path that adds claimable GREEN must pass the same dependencies.

The helper order is literal:

```text
assert stabAsset != empty(address)
assert claimAsset != empty(address)
assert reportedAmount != 0

custody = IERC20(claimAsset).balanceOf(self)
priorLiability = totalClaimableBalances[claimAsset]
assert custody >= priorLiability              # claim custody deficit
availableUnaccounted = custody - priorLiability
assert reportedAmount <= availableUnaccounted # short claim receipt

newPairBalance = claimableBalances[stabAsset][claimAsset] + reportedAmount
claimableBalances[stabAsset][claimAsset] = newPairBalance
totalClaimableBalances[claimAsset] = priorLiability + reportedAmount
```

Do not use `min(reportedAmount, custody)`. Do not use pair liability in place of
global liability: custody backs the aggregate across every Stability asset.

All arithmetic and storage changes must occur in the same transaction as the
existing swap/redemption operation. Any later failure must roll the credit back.

### 8.3 Add-time activation decision

After crediting:

1. If the pair is already active, return without repricing or emitting a
   dormant event.
2. Compute cumulative pair value with the non-raising activation helper.
3. If value is zero, leave dormant and emit reason `DORMANT_NO_PRICE`.
4. If value is less than `$0.25`, leave dormant and emit
   `DORMANT_BELOW_FLOOR`.
5. If active count is 12, leave dormant and emit `DORMANT_CAPACITY`.
6. Otherwise register the pair and emit `ClaimAssetActivated`.

Credit must always precede steps 2–6. Pricing failure or capacity must never
discard received collateral. A reverting unsupported token may still revert;
that is covered by asset admission and negative tests.

### 8.4 Registration helper

Centralize registration in `_registerClaimableAsset` and require:

```text
claimableBalances[stabAsset][claimAsset] > 0
indexOfClaimableAsset[stabAsset][claimAsset] == 0
_getNumActiveClaimAssets(stabAsset) < MAX_ACTIVE_CLAIM_ASSETS
```

Preserve the current sentinel/next-index write pattern. Set the forward array,
reverse index, and next index before emitting activation. No caller may bypass
this helper.

### 8.5 Deactivation and slot clearing

Retain `_reduceClaimableBalances` as the only liability-reduction helper.

- zero residual: remove the active index with reason `DEACTIVATION_ZERO`;
- nonzero residual with a nonzero USD value below `$0.10`: remove only the
  active index with reason `DEACTIVATION_DUST`;
- unavailable/zero residual price: do not classify as dust; and
- balances and aggregate liabilities change only by the amount actually paid,
  redeemed, or burned.

Change `_removeClaimableAsset` to accept a reason and clear the vacated last
slot on every successful removal:

```text
lastIndex = numClaimableAssets[stabAsset] - 1
if targetIndex != lastIndex:
    move last asset to target index
    update moved reverse index
claimableAssets[stabAsset][lastIndex] = empty(address)
indexOfClaimableAsset[stabAsset][removed] = 0
numClaimableAssets[stabAsset] = lastIndex
```

Do not alter pair balance or total liability in this helper. Emit one
deactivation event after state is consistent.

### 8.6 Permissionless pruning

Add:

```text
pruneClaimableAssets(
    stabAsset: address,
    claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]
)
```

Requirements:

- external and permissionless;
- no pause restriction;
- candidate array only—never scan the full registry;
- empty array is a no-op;
- absent/dormant candidates are no-ops;
- active zero balance deactivates with `DEACTIVATION_ZERO`;
- active nonzero balance is priced with the non-raising helper;
- price zero/unavailable is a no-op, never dust;
- nonzero value below `$0.10` deactivates with `DEACTIVATION_DUST`;
- value at or above `$0.10` is unchanged; and
- duplicates remain safe and idempotent.

The function must not change custody, pair balances, aggregate liabilities, or
user shares.

### 8.7 Permissionless activation

Add:

```text
activateClaimAssets(
    stabAsset: address,
    claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]
)
```

Requirements:

- external and permissionless;
- no pause restriction;
- candidate array only;
- empty array is a no-op;
- absent/already-active candidates are no-ops;
- confirm custody is not below the global liability before activation;
- price cumulative pair balance with the non-raising helper;
- zero or below-floor value is a no-op;
- at/above `$0.25` and below capacity activates atomically;
- when capacity is full, leave dormant without emitting another dormant event;
- duplicates remain safe; and
- activation never changes custody, liabilities, or shares.

Expose a view:

```text
canActivateClaimAsset(stabAsset, claimAsset)
    -> (canActivate: bool, usdValue: uint256, capacityRemaining: uint256)
```

It must use the same helper and threshold/cap semantics. An unavailable price
returns `(False, 0, remaining)` rather than reverting for ordinary PriceDesk
unavailability.

### 8.8 GREEN prohibition

In `_depositTokensInVault`, reject `_asset == _a.greenToken` before calculating
shares or changing balances. Use a stable developer message such as
`green cannot be stab asset`.

Also assert `_stabAsset != _greenToken` in both liquidation swap entry points.
This is defense in depth against accidental configuration/registration. Do not
prohibit GREEN as `_claimAsset`; GREEN claims for non-GREEN Stability assets are
valid and count toward the ordinary active cap.

## 9. StabilityPool wrapper size and recovery

### 9.1 Required StabVault export trim

An independent representative compile probe against the bound source measured:

| Probe | Runtime bytes | EIP-170 headroom |
| --- | ---: | ---: |
| Existing StabilityPool | 23,960 | +616 |
| Full Tier A+B surface | 26,817 | -2,241 |
| Full surface with `-O codesize` | 26,081 | -1,505 |
| Full surface plus selective StabVault exports | 23,861 | +715 |

These numbers establish a blocking design constraint but are not final artifact
evidence. Recompile and remeasure the owner-reviewed final source.

After explicit owner Gate S0 approval, replace
`exports: stabVault.__interface__` with selective exports for the five existing
claim registry getters, the six existing swap/claim/redemption entry points,
and the five new hardening functions/views. Omit exactly:

```text
valueToShares
sharesToValue
getTotalValue
getTotalUserValue
```

Repository-wide source inspection found no production-contract consumer for
those four views. Their internal helpers remain because core accounting uses
them. Treat removal as an intentional ABI change: identify any off-chain/test
consumers, update them in the later validation slice, and record the owner
approval. Do not remove any other existing selector.

### 9.2 StabilityPool recovery wrapper

Vyper 0.4.3 supports exporting individual module functions/public getters. In
`StabilityPool.vy`, replace:

```text
exports: vaultData.__interface__
```

with a tuple exporting every current VaultData public getter and external
function except `recoverFunds` and `recoverFundsMany`:

```text
vaultData.isPaused
vaultData.userBalances
vaultData.totalBalances
vaultData.userAssets
vaultData.indexOfUserAsset
vaultData.numUserAssets
vaultData.vaultAssets
vaultData.indexOfAsset
vaultData.numAssets
vaultData.isUserInVaultAsset
vaultData.doesUserHaveBalance
vaultData.deregisterUserAsset
vaultData.isSupportedVaultAsset
vaultData.deregisterVaultAsset
vaultData.doesVaultHaveAnyFunds
vaultData.getNumUserAssets
vaultData.getNumVaultAssets
vaultData.pause
```

Compile immediately after this change and compare the before/after
StabilityPool ABI. Before adding the wrappers, exactly the two recovery
selectors may be absent; no other selector may disappear or change.

Define wrapper functions with the same names, argument types, mutability, and
selectors as the removed exports. Each must:

1. require `addys._isSwitchboardAddr(msg.sender)`;
2. require `stabVault.totalClaimableBalances[asset] == 0`; and
3. call `vaultData._recoverFunds(recipient, asset)`.

For `recoverFundsMany`, check and recover each item within the same loop. Any
nonzero liability must revert the entire batch and roll back prior loop
transfers. Preserve the existing maximum array length of 20 and the existing
`VaultFundsRecovered` event emitted by VaultData.

Acceptance requires byte-for-byte equality of the old and new ABI entries for
both recovery functions. Every unrelated existing selector remains unchanged
except the four owner-approved removals in Section 9.1.

Do not weaken the guard to pair liability. Aggregate liability covers active
and dormant balances across all Stability assets.

## 10. Oracle-liveness controls

Do not change active NAV calls from `_shouldRaise=True` to `False`. Silently
skipping an unpriced active asset would allow deposits and share conversions
against knowingly incomplete NAV.

Add deterministic tests for this exact matrix:

| Active claim price state | Deposit | Withdrawal | Internal transfer | Single claim | Claim-many | Value view | AuctionHouse borrower traversal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Valid configured feed | succeeds | succeeds | succeeds | succeeds | succeeds | succeeds | succeeds |
| Configured but stale/dead | reverts | reverts | reverts | reverts | reverts | reverts | reverts |
| No feed configured | succeeds while skipping claim value | succeeds with incomplete NAV | succeeds with incomplete NAV | path-specific failure if selected | batch/path-specific | returns incomplete NAV | traverses with incomplete NAV |

Record exact observed behavior; do not make a green test by substituting a
proxy call. The stale/dead row is a known residual, not an expected fix.

Robinhood admission assertions must require:

- WETH uses the approved manipulation-resistant Chainlink path;
- no Stability-routable asset is spot-AMM-only;
- every routed asset has a configured, enabled, non-stale primary source before
  routing is enabled; and
- source-order changes are reviewed because PriceDesk accepts the first
  nonzero source.

Add a runbook under `docs/chains/rh/stability-pool/` stating detection, pause
authority, operations stopped by pause, feed restoration/reconfiguration,
verification calls, unpause criteria, and the fact that pause contains value
movement but does not restore liquidation liveness.

## 11. Robinhood capacity and launch assertions

Extend the generated Robinhood validation surface, not handwritten generated
outputs, to assert:

1. GREEN is never a priority Stability asset;
2. sGREEN remains the sole launch priority Stability asset unless separately
   approved;
3. WETH is the sole launch asset with `shouldSwapInStabPools=True` unless
   separately approved;
4. Stock Token Stability routing remains false;
5. enabled non-GREEN routed claim assets are at most 11; and
6. each enabled routed asset passes the oracle-admission rule.

The launch assertion is not a lifetime governance guarantee. Document an
operating invariant that the cumulative lifetime set of distinct tokens routed
to a given pool must remain reviewed and bounded. The on-chain active cap is the
hard protection against NAV iteration growth; overflow remains dormant.

Do not hand-edit `DefaultsRobinhood.vy` or generated JSON. Change the canonical
input/generator only when an approved configuration decision requires it, then
regenerate mechanically and inspect the complete generated diff.

## 12. Post-crash exit requirement

Create a deterministic scenario:

1. users deposit the launch Stability asset and receive shares;
2. liquidation consumes the entire raw Stability-asset balance;
3. `totalBalances[stabAsset]` remains nonzero;
4. claim collateral and custody remain positive;
5. ordinary withdrawal and internal transfer exhibit their current zero-raw-
   balance behavior;
6. execute the approved user exit path; and
7. prove liabilities, shares, and custody settle without phantom NAV.

The test must run with the exact proposed Robinhood general and per-asset claim
and redemption flags. A generic test fixture with all flags true is not launch
evidence.

Run the same scenario after applying the reward-runway emergency claim-disable
step. If the approved launch or emergency flags do not permit a complete user
exit, stop. Do not claim this risk is fully mitigated. Produce an owner decision
between:

- enabling claims with zero claim reward;
- enabling the necessary redemption path;
- adding a separately designed non-rewarded in-kind exit; or
- explicitly accepting temporary exit unavailability.

An in-kind exit is outside this implementation slice and requires a new
economic/accounting specification.

## 13. Required deterministic tests

Add focused tests with exact balance, index, count, event, and revert
assertions—not only success/failure.

### 13.1 Receipt and activation

- first receipt worth `$0.249999...` is dormant;
- first receipt exactly `$0.25` activates;
- first receipt above `$0.25` activates;
- repeated dormant receipts accumulate and activate exactly once at the floor;
- no-feed and configured-unusable non-raising activation return leave receipt
  accounted dormant;
- an already-active receipt does not reprice or consume a second slot;
- 6-, 8-, and 18-decimal tokens obey the same USD boundary;
- GREEN claim valuation is 1:1 and sGREEN uses `convertToAssets`;
- receipt at active count 12 is fully accounted dormant and swap completes;
- permissionless activation succeeds after a slot is freed; and
- no new receipt is required for activation.

### 13.2 Index integrity

- first, middle, and last removal;
- vacated last slot is zero in every case;
- moved asset reverse index is correct;
- final removal preserves documented sentinel semantics;
- repeated prune/activate and duplicate candidates are idempotent;
- count never exceeds 12; and
- no asset can occupy two indexes.

### 13.3 Custody/liability

- exact standard-token receipt succeeds;
- custody below prior aggregate liability reverts before state changes;
- reported receipt greater than unaccounted custody reverts atomically;
- reported receipt equal to unaccounted custody succeeds;
- pre-existing donation plus exact receipt credits only the report and leaves
  surplus unaccounted;
- demonstrate/document that a donation can mask a later short transfer;
- fee-on-transfer and down-rebase mocks fail closed;
- malformed/reverting `balanceOf` fails closed;
- pair and total liability updates roll back if the later Stability-asset
  transfer/burn fails; and
- one claim token shared across multiple Stability assets uses global liability.

### 13.4 Dormant claims/redemptions and MEV

- dormant balances remain directly claimable when pricing/config allows;
- dormant balances remain redeemable;
- claim/redemption reductions preserve dormant status until activation rules
  are met;
- redemption self-cleans dormant custody and liability;
- deposit → dormant activation/redemption → withdrawal in one transaction or
  block cannot extract more than the approved rounding plus dormant-value
  bound; and
- maintenance never changes shares or custody.

### 13.5 Recovery

- recover a token with zero claim liability succeeds under existing rules;
- active liability blocks single recovery;
- dormant liability blocks single recovery;
- liability under a different Stability asset blocks recovery;
- batch containing one liable token reverts all transfers;
- unauthorized caller still fails before recovery; and
- ABI selectors and events remain unchanged.

### 13.6 GREEN and exit

- GREEN deposit as a Stability asset reverts;
- both swap entry points reject GREEN as Stability asset;
- GREEN remains valid as claim asset for a non-GREEN Stability asset;
- GREEN claim occupies and counts one ordinary active slot;
- no `claimableBalances[GREEN][GREEN]` state can be created; and
- the Section 12 zero-raw-balance scenario completes or is reported blocked by
  the exact unresolved flag.

### 13.7 Oracle and composition

- complete Section 10 revert matrix;
- AuctionHouse capacity-overflow liquidation completes and records dormant
  collateral;
- AuctionHouse phase-2 borrower traversal reproduces configured-stale-feed
  failure;
- `claimMany` at 15 entries exercises the full active ceiling;
- Teller deposit paths exercise every observed count of repeated NAV
  traversals; and
- redemption gas is measured against Stability-asset count, not active-claim
  count.

## 14. Stateful and invariant validation

Add a state-machine test or equivalent randomized sequence with actions:

```text
deposit, withdraw, internal transfer, liquidation receipt, claim, claimMany,
redeem, swapWithClaimableGreen, prune, activate, donate, price change,
feed disable/restore, capacity fill, and re-add
```

After every successful action assert:

1. total claim liability equals the sum of modeled pair liabilities;
2. custody is at least aggregate liability for every supported token;
3. every active forward index has one matching reverse index;
4. every dormant pair has balance > 0 and reverse index 0;
5. absent pairs have zero balance and reverse index 0;
6. active count is at most 12;
7. every out-of-range/vacated checked slot is empty;
8. maintenance changes no custody, liability, or user shares;
9. failed operations roll back every modeled value;
10. activation/deactivation changes only NAV membership;
11. no user extracts more than share value plus the approved rounding bound;
12. dormant reactivation value capture is bounded by modeled dormant value; and
13. no capacity event corresponds to a rejected/unaccounted receipt.

Use a model with at least two Stability assets and one claim token shared across
both so aggregate-liability mistakes are detectable.

## 15. Gas, bytecode, ABI, and generated evidence

### 15.1 Gas matrix

Measure actual transactions with:

| Dimension | Cases |
| --- | --- |
| Active claims | `0, 1, 2, 4, 8, 12` |
| Price sources | `0, 1`, admitted maximum |
| Source state | cold valid, warm valid, no feed, configured stale/dead |
| Claim batch | `1`, `15` crossed with active count 12 |
| Teller deposit | each one/two/three-NAV-traversal composition observed |
| Redemption | launch and maximum Stability-asset count |
| AuctionHouse | ordinary receipt, capacity-full receipt, borrower traversal |

Report gas used, success/revert, and incremental slope. Do not approve cap 12
from view-only measurements.

### 15.2 Bytecode

Before and after implementation, record for StabilityPool and every production
contract whose compiled bytes change:

```bash
vyper -p . -f bytecode,bytecode_runtime contracts/vaults/StabilityPool.vy
```

Record creation length/hash, runtime-template length/hash, EIP-170 headroom,
compiler version, and integrity bytes. Run the repository artifact checker and
update expectations mechanically. Do not update expected hashes until the
source delta is independently reviewed.

### 15.3 ABI

Run the deterministic ABI exporter/checker. The StabilityPool ABI may add only:

- `getNumActiveClaimAssets`, `getClaimAssetState`,
  `canActivateClaimAsset`, `pruneClaimableAssets`, and `activateClaimAssets`;
- the three events specified above; and
- any public constant getters deliberately selected by implementation review.

It may remove only `valueToShares`, `sharesToValue`, `getTotalValue`, and
`getTotalUserValue`, after recorded Gate S0 approval.

Existing selectors, argument types, return types, mutability, and events must
otherwise remain unchanged. Recovery selectors must be identical despite moving
from module export to wrapper definitions.

### 15.4 Inventory

`StabVault.vy` is content-pinned by block-clock/inventory validation. Update the
canonical generator/input and derived inventory through the repository's
mechanical workflow. Never hand-edit a hash merely to make a test green.
Explain why each line-reference or hash change follows from this candidate.

## 16. Validation commands

Use isolated mode-0700 caches and suppress repository bytecode/cache residue.
Adapt the interpreter path to the validated environment, but preserve these
properties:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=<private-mode-0700-temp>/pycache
export XDG_CACHE_HOME=<private-mode-0700-temp>/xdg
export HYPOTHESIS_STORAGE_DIRECTORY=<private-mode-0700-temp>/hypothesis
export ETHERSCAN_API_KEY=local-placeholder
```

Required sequence:

1. compile StabilityPool and capture size/ABI;
2. run focused hardening tests;
3. run all three existing StabVault suites;
4. run focused AuctionHouse/Teller/MissionControl/Switchboard/config tests
   touched by the call graph;
5. run stateful/invariant tests repeatedly with recorded seeds;
6. run ABI and artifact/inventory validators;
7. run the complete repository suite;
8. rerun gas/size evidence on the final source tree; and
9. verify clean Git-visible status except the exact candidate paths.

At minimum, include:

```bash
pytest -q -p no:cacheprovider tests/vaults/modules/test_stab_vault_hardening.py
pytest -q -p no:cacheprovider tests/vaults/modules/test_stab_vault.py
pytest -q -p no:cacheprovider tests/vaults/modules/test_stab_vault_claims.py
pytest -q -p no:cacheprovider tests/vaults/modules/test_stab_vault_redemptions.py
pytest -q -p no:cacheprovider tests/inventory/test_contract_artifacts.py
pytest -q -p no:cacheprovider tests/inventory/test_block_clock_inventory.py
python scripts/export_abis.py --check
python scripts/check_contract_artifacts.py
git diff --check
git status --short
```

Use the actual script help if an option differs; do not invent a passing command
or omit a failed validator. Record full commands, environment, exit codes, and
test counts in the evidence document.

## 17. Implementation order and gates

### Gate 0 — decision acceptance

Required before production edits:

- D-01 through D-13 accepted;
- Section 3.1 decisions recorded;
- Gate S0 four-view ABI removal explicitly approved;
- exact baseline rebound;
- exact path ceiling accepted; and
- baseline ABI/gas/bytecode evidence captured.

### Unit A — registry bound and lifecycle

Implement Sections 6–8.1 and 8.3–8.7. Run focused registry, dust, claim, and
redemption tests. Stop if capacity can reject an otherwise valid liquidation or
if dormant balances cease to be mapping-claimable/redeemable.

### Unit B — custody accounting

Implement Section 8.2 and adversarial token tests. Stop if any credit can exceed
unaccounted custody, if global liability is replaced by pair liability, or if a
failed downstream swap leaves credit behind.

### Unit C — recovery and GREEN

Implement Sections 8.8 and 9. Prove the exact intentional ABI delta immediately.
Stop if any selector other than the four approved views disappears, if either
recovery selector changes, or if any other vault's compiled behavior changes
because VaultData was edited.

### Unit D — configuration, oracle, and exit evidence

Implement Sections 10–12 without changing prohibited production paths. Stop at
the claim-flag conflict if owner resolution is absent; report registry and
accounting evidence separately rather than pretending the exit gate passed.

### Gate 1 — independent design/delta review

Reviewer must confirm:

- actual source matches this transition model;
- no fail-open active NAV change;
- capacity fails dormant, not liquidation;
- custody checks use aggregate prior liability;
- recovery ABI and authorization are preserved;
- GREEN prohibition is complete;
- shared-source blast radius is understood; and
- every deviation is explicitly approved.

### Gate 2 — complete validation

All deterministic, stateful, gas, ABI, bytecode, inventory, configuration, and
full-suite evidence must pass on one exact commit/tree. A green focused suite is
not enough.

### Gate 3 — candidate handoff

Produce source commit/tree, changed-path list, numstat, compiled identities,
test/gas evidence, decision register, unresolved risks, and independent review.
This authorizes neither integration nor deployment.

## 18. Rejected shortcuts

The implementation agent must not:

- change active NAV pricing to `_shouldRaise=False` and silently skip stale
  configured assets;
- reject a receipt because the active list is full;
- zero or sweep dormant balances;
- add an iterable dormant list or any unbounded maintenance scan;
- use total token custody as the new receipt amount;
- compare custody only with the pair liability;
- modify AuctionHouse merely to obtain a pre-transfer snapshot;
- edit shared VaultData recovery behavior for every vault;
- exclude dormant balances from claims or redemptions;
- classify price zero as dust;
- exempt GREEN from total NAV iteration without still bounding it;
- hand-edit generated ABI/hash/inventory outputs;
- enable a spot-AMM-only claim price;
- treat pause as restored liveness; or
- claim the post-crash exit risk is fixed without exact launch-flag evidence.

## 19. Definition of done

The implementation candidate is complete only when:

- active NAV iteration is hard-capped at 12;
- final StabilityPool runtime is within EIP-170 with recorded headroom and only
  the four owner-approved view removals;
- sub-$0.25, unavailable-price, and capacity-full receipts are fully accounted
  dormant without registration;
- at/above-floor dormant balances can be permissionlessly activated;
- active zero/sub-$0.10 entries can be permissionlessly pruned;
- all maintenance is bounded and idempotent;
- strict custody-minus-aggregate-liability receipt checks pass adversarial
  tests;
- generic recovery cannot transfer any token with active or dormant aggregate
  claim liability;
- GREEN cannot become a Stability asset or self-claim;
- dormant balances remain claimable and redeemable;
- the stale-feed behavior and operational residual are explicitly evidenced;
- the capacity-full AuctionHouse transaction completes;
- the exact launch configuration respects routing, reserve, and oracle rules;
- post-crash exit passes with exact approved launch flags or remains an explicit
  blocking owner decision;
- ABI, runtime, inventory, gas, focused tests, and full suite bind to one exact
  commit/tree; and
- an independent reviewer accepts the source delta and residual-risk statement.

Completion of this specification means implementation-candidate readiness
only. Integration, deployment, configuration, activation, and release remain
separate owner-controlled lifecycle actions.
