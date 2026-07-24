# Robinhood Stock Token Vault Decision Record

**Decision status:** Conditional; owner decision required

**Recommended outcome:** `conditional — shared vault change specification required`

**Owner production-behavior approval status:** Not approved

**Evidence commit:** `05940a5273cb7ff625ad0dc9bfb5ddc52c22844d`

## Decision

Do not select either existing deployable vault unchanged for Robinhood Stock
Token collateral yet.

`SimpleErc20` is rejected unchanged because its nominal accounting permits
phantom collateral, first-withdrawer capture, capture of fresh post-zero
deposits, and a confirmed internal-auction settlement in which a liquidator pays
GREEN for a claim backed by zero live tokens.

`RebaseErc20`/`SharesVault` is the preferred accounting direction because live
claims reflect custody and partial losses are socialized pro rata. It is not
accepted unchanged because:

1. total loss makes the common collateral amount and weighted debt terms zero,
   preventing a new liquidation and blocking settlement/deleveraging;
2. a fresh deposit after total loss dilutes old shares to a zero-rounded claim;
3. its donation allocation and raw-share reward/monitoring semantics require
   explicit owner acceptance; and
4. the shared deposit path can mismeasure a later short-received transfer.

The next production step is a separately scoped, owner-approved,
chain-portable vault-change specification. Track 5 does not implement that
change.

## Approval boundary

After the agent paused on the zero-backed-liquidation stop condition and
reported the issue, the owner explicitly replied, “yes you can continue” and
asked that the issue be clearly documented before continuing. This
conversation—not a repository artifact—is the evidence for approval to
continue repository analysis. That approval did **not**:

- accept the custody, liquidation, first-mover, post-zero, or monitoring risk;
- select a production vault;
- authorize a production contract change;
- authorize defaults, migration, manifest, or asset-configuration changes; or
- authorize deployment or a live transaction.

The owner later reconfirmed this boundary: “That's correct. I approved the
analysis to keep going forward but I'm not approving the underlying behavior.”
This later confirmation is also conversation evidence rather than a repository
artifact.

All of those gates remain closed.

## Owner-authorized scope amendment and complete deliverable ledger

The original Track 5 contract permitted a test-only mock, a comparison test
suite, and two decision/comparison documents. It also directed the agent to
identify a required follow-on specification without designing that change in
Track 5.

After those four deliverables were complete, the owner separately asked, “Okay
can you document somewhere what your recommended fixes are for this?” and
specifically requested “the simplest way to mitigate this risk.” That request
authorized a documentation-only scope amendment:

`docs/chains/rh/stock-token-vault-fix-recommendations.md`

It did **not** authorize production implementation, configuration, deployment,
or acceptance of the behavior. The recommendations document remains an
unapproved input to any future, separately opened implementation track.

The complete branch deliverable set is five files:

1. `contracts/mock/MockStockTokenControls.vy`;
2. `tests/vaults/test_stock_token_vault_comparison.py`;
3. `docs/chains/rh/stock-token-vault-comparison.md`;
4. `docs/chains/rh/stock-token-vault-decision.md`; and
5. `docs/chains/rh/stock-token-vault-fix-recommendations.md`.

The complete material commit ledger through the pre-ledger-review head is:

| Commit | Change |
|---|---|
| `d8f11e9` | Added the issuer-control mock and initial comparison harness |
| `ee270ab` | Closed initial comparison-matrix gaps |
| `4283008` | Added the comparison and decision records |
| `c5d09f0` | Added tests for first re-review coverage gaps |
| `a2c5fe1` | Updated both records for the first re-review |
| `05940a5` | Tightened final test assertions |
| `2b34989` | Refreshed final test evidence in both records |
| `4f86616` | Added the owner-requested fix recommendations and linked them from this record |
| `d941f31` | Recorded owner confirmation and normalized final-evidence citations |

Any completion report for this branch must report all five files and must
distinguish the original four deliverables from the later owner-authorized fifth
deliverable. Reporting only the latest commit is not a complete branch
completion report.

## Relationship to the earlier phantom-collateral posture

The controlling executive summary had already accepted interim vault-balance
overstatement, missing-asset borrowing power, and first-withdrawer advantage
after an administrative burn
(`hood-chain-executive-summary.md:190-201`, especially line 196). Track 5
reopens that interim posture because the new evidence is more severe than
passive overstatement: AuctionHouse can actively accept the stale amount as
delivered collateral, charge a third-party buyer GREEN, reduce borrower debt,
and leave the buyer with an undeliverable claim. The two-buyer test also proves
that separately purchased internal claims can exceed live custody and become
withdrawal-order dependent.

Accordingly, this record supersedes the earlier accepted-consequence framing
for vault selection. It does not reject the architectural decision to tolerate
issuer authority, and it does not silently revoke an owner decision. It
identifies an active settlement invariant that was not captured by the earlier
summary and returns the vault choice to an explicit owner/specification gate.

## Selected and rejected paths

### Selected deployable contract and module path

**None approved.**

The conditional follow-on candidate is:

```text
contracts/vaults/RebaseErc20.vy
  -> contracts/vaults/modules/SharesVault.vy
  -> contracts/vaults/modules/VaultData.vy
```

That path is a candidate for a shared-change specification, not the selected
production vault.

### Rejected unchanged: `SimpleErc20`

Path:

```text
contracts/vaults/SimpleErc20.vy
  -> contracts/vaults/modules/BasicVault.vy
  -> contracts/vaults/modules/VaultData.vy
```

Reasons:

- issuer reductions do not reduce user or vault common views;
- collateral value and borrowing power remain against missing tokens;
- partial loss creates a deterministic first-withdrawer advantage;
- an old claimant can take a new depositor's tokens after total loss;
- internal liquidation can return a nominal amount that is not economically
  deliverable; and
- the confirmed zero-backed internal auction charges GREEN and reduces debt.

### Not accepted unchanged: `RebaseErc20`/`SharesVault`

Reasons:

- total live-balance loss produces zero claims but leaves raw shares and debt;
- zero collateral also removes the weighted liquidation/redemption thresholds,
  preventing a new liquidation;
- active internal and external auctions revert at zero, preserving funds but
  leaving no progress path;
- tested Deleverage external withdrawal also stops at zero;
- fresh deposits after zero almost entirely dilute old shares;
- user reward weight remains raw-share-based while global value becomes live;
  and
- the common deposit logic does not measure a per-call balance delta.

## Behavior acceptance ledger

No row in this table constitutes owner approval. “Candidate-acceptable” means
the behavior can be carried into a follow-on specification for owner review.

| Behavior | `SimpleErc20` | `RebaseErc20`/`SharesVault` | Track 5 status |
|---|---|---|---|
| Ordinary deposit/withdraw | Exact nominal accounting | Live share accounting with bounded dust | Candidate-acceptable |
| Donation before first deposit | Donation remains unallocated | Virtual shares/assets dilute small deposits | Requires explicit policy |
| Donation between deposits | Existing users do not receive it | Existing shareholders receive it | Requires explicit policy |
| Per-call deposit measurement | Can overcredit a later short receipt | Can mint from incorrect amount/previous balance | Rejected for both |
| Partial administrative burn | Phantom nominal claims | Pro-rata live claims | Rebase direction preferred |
| Forced transfer/redemption | Same as burn | Same as burn | Rebase direction preferred |
| Total custody loss | Phantom claims remain | Claims become zero | Neither supplies complete resolution |
| Fresh deposit after zero | Old claimant can capture it | Old shares can round to zero | Rejected pending specification |
| Pause/blocklist on token transfer | Atomic revert/retry | Atomic revert/retry | Candidate-acceptable with monitoring |
| Internal move while paused | Succeeds nominally | Succeeds in shares | Not evidence of deliverability |
| Internal auction purchase while paused | Charges GREEN; buyer gets nominal claim but cannot withdraw | Charges GREEN; buyer gets live-share claim but cannot withdraw | Not accepted as delivery proof; operations policy required |
| External auction purchase while blocklisted | Atomic revert for sender, recipient, and operator roles; retry succeeds | Same | Candidate-acceptable with monitoring |
| Partial-loss external liquidation | Delivers while live balance remains | Delivers pro-rata live claim | Candidate-acceptable |
| Auction initiated after partial loss | Internal/external modes settle, with Simple ordering risk | Internal/external modes settle pro rata | Rebase direction preferred |
| Total-loss external liquidation | Atomic revert | Atomic revert | Safe funds; blocked progress |
| Total-loss liquidation initiated after loss | Starts and charges for zero-backed nominal claim | Does not enter liquidation or start an auction | Simple rejected; Rebase still blocked |
| Total-loss internal liquidation opened before loss | Charges for zero-backed nominal claim | Atomic revert | Simple rejected; Rebase still blocked |
| Deleverage at partial loss | External delivery reconciles | External delivery reconciles | Candidate-acceptable |
| Deleverage at total loss | Reverts | Reverts | Requires defined bad-debt path |
| Behavior-switch upgrade test | Transfer failure is atomic | Transfer failure is atomic | Proxy behavior still unproven |

## Phantom collateral, first-mover, and debt-health conclusions

- **Simple phantom collateral:** proved. User and vault common views do not
  change after issuer burn/forced reduction. CreditEngine continues pricing the
  nominal amount.
- **Simple first-mover advantage:** proved with two users and both withdrawal
  orderings. The first user receives all remaining live custody; the second
  retains a nominal balance but cannot withdraw.
- **Rebase pro-rata loss:** proved. Both withdrawal orderings receive the same
  live share within base-unit rounding.
- **Borrowing power:** Simple stays stale; Rebase falls immediately with custody.
- **Total-loss debt health:** Rebase's zero amount is solvent-accounting-correct
  but operationally incomplete. With no collateral weight, the effective
  liquidation/redemption thresholds can be zero, so `canLiquidateUser` is false
  even while debt remains.

## Internal versus external liquidation

`AuctionHouse._transferCollateral` has two settlement modes:

- internal mode calls `transferBalanceWithinVault`; and
- external mode calls `withdrawTokensFromVault`.

At total live loss:

- Simple internal mode returns nominal collateral, after which AuctionHouse
  charges GREEN and CreditEngine reduces debt. No token is delivered, and the
  resulting claim cannot be withdrawn.
- Simple external mode reverts before GREEN/debt state is committed.
- Rebase internal and external modes both reject the zero-live conversion and
  revert the whole purchase. GREEN, debt, buyer balances, and auction state are
  unchanged.

The suite starts auctions on both sides of the issuer action. After partial
loss, both vaults can enter liquidation and settle through either mode. After
total loss, Simple still enters liquidation and repeats the unsafe internal
settlement; Rebase's zero weighted threshold prevents liquidation mode and no
auction starts.

Thus a successful internal balance move cannot be treated as proof that an
issuer-controlled token is deliverable. A follow-on specification must make
live backing an explicit precondition of the amount returned to settlement.

The integration suite also proves the paused-but-live case: a real internal
auction purchase succeeds, charges 20 GREEN, reduces debt by 20 GREEN, and
assigns about 40 tokens of vault claim while the buyer's withdrawal is blocked
until unpause. This is distinct from the zero-backed failure—the claim is live
backed but not presently deliverable—and still requires explicit settlement
and operations policy.

For external settlement, sender-blocked vault, recipient-blocked buyer, and
operator-blocked vault cases all revert atomically. GREEN, debt, custody, and
auction state remain unchanged; clearing the exact role permits retry.

Deleverage has no internal-transfer settlement branch. Its applicable volatile
asset and collateral-swap paths call the AuctionHouse external-withdrawal
wrapper (`Deleverage.vy:433,1065`). The tested partial/total-loss external
withdrawal therefore covers its complete current Stock Token custody surface.

## Reward, view, ABI, event, and monitoring implications

The deployable vaults share `Vault.vyi`, so choosing Rebase does not require a
new external vault interface. The meanings of existing fields differ:

| Surface | Simple meaning | Rebase meaning |
|---|---|---|
| `userBalances` | Nominal token amount | Raw shares |
| `totalBalances` | Nominal token amount | Raw shares |
| `getTotalAmountForUser` | Nominal claim | Converted live claim |
| `getTotalAmountForVault` | Nominal total | Live ERC-20 balance |
| `getUserLootBoxShare` | Nominal token amount | Raw shares divided by `10**8` |
| Teller deposit/withdraw events | Returned nominal amount | Returned token amount converted from shares |

Consequences if the Rebase direction later wins approval:

1. dashboards, indexers, alerts, and parameter-export scripts must distinguish
   raw shares, converted claim, and actual ERC-20 balance;
2. the share price or conversion inputs must be monitored, not only
   `totalBalances`;
3. a loss can reduce global USD value without reducing a user's Lootbox raw
   share weight;
4. event reconciliation must compare returned token amounts with share deltas
   and actual token deltas; and
5. the per-call deposit-delta fix may require an internal or external API/event
   decision in the follow-on specification.

The event requirement is behaviorally covered, not inferred. For both vaults,
the suite reconciles Teller deposit/withdraw events and vault
deposit/withdraw/internal-transfer events to return values, token deltas, stored
balance deltas, and—on Rebase—the emitted `shares`/`transferShares` fields.

The reward implication is also covered through the real
`Lootbox.updateDepositPoints` and Ledger state path. After donation and total
loss, both vaults continue accruing user balance points from the unchanged
nominal/raw-share weight. Simple's asset/global USD input remains nominal at
$100; Rebase refreshes from $100 to $200 after donation and to $0 after total
loss. This divergence is an explicit policy and monitoring decision, not merely
a view-level observation.

No ABI or event change is authorized here.

## VaultBook and `DefaultsRobinhood` implications

### VaultBook

The test fixture registers `SimpleErc20` as ID 3 and `RebaseErc20` as ID 4
(`tests/conf_core.py:658-674`). Those are local test IDs only.

Production implications:

1. Track 3 must supply the stable component ID and live-version status.
2. A migration must register or confirm the approved deployable vault in the
   Robinhood `VaultBook`.
3. The configured `AssetConfig.vaultIds` must use the returned/manifested
   registry ID, never assume test ID 3 or 4.
4. A vault address update or disable is blocked while
   `doesVaultHaveAnyFunds()` is true (`VaultBook.vy:94-147`). Raw shares or
   nominal state can therefore block registry operations even when live token
   custody is zero.
5. A post-deployment smoke check must reconcile
   `VaultBook.getRegId(vault)`, `getAddr(id)`, and
   `MissionControl.getFirstVaultIdForAsset(token)`.

The suite now tests cleanup after both partial and total issuer loss. User and
asset deregistration remain blocked by nonzero raw nominal/share accounting.
Governance recovery rejects a partially live registered balance and has
nothing to recover at total live loss. A zero live balance alone is not a
cleanup or migration path.

### `DefaultsRobinhood`

`DefaultsRobinhood` does not exist at the starting commit. It is owned by later
configuration/deployment work and must not be created in Track 5.

Once the owner approves a vault and any required shared change, that artifact
must:

- assign the exact approved `vaultIds` entry for each Stock Token;
- set `canRedeemCollateral = false`;
- set `shouldSwapInStabPools = false` unless a separate owner decision accepts
  Stability Pool custody;
- disable Endaoment, treasury, yield, Underscore, and unsupported collateral
  routing;
- use later-approved token addresses, feed mappings, limits, and debt terms;
- contain values and inventory only, not divergent protocol logic; and
- remain consistent with migration and manifest registry IDs.

`DefaultsBase` is unchanged and must not be edited in place for Robinhood.

## Required asset configuration

Track 5 tests only the vault-dependent flags. Production values remain pending:

```text
AssetConfig.vaultIds              = [approved VaultBook ID]
AssetConfig.canRedeemCollateral   = false
AssetConfig.shouldSwapInStabPools = false
```

The harness verifies `canRedeemCollateralAsset == false` through
`MissionControl.getRedeemCollateralConfig()` and verifies
`shouldSwapInStabPools == false` through `getAssetLiqConfig()`.

Stock Token `CreditRedeem` remains disabled regardless of later vault choice.
No Stock Token should be routed through Stability Pool, Endaoment, Base treasury,
partner liquidity, yield, or Underscore without a separate owner-approved
decision and test record.

## Shared-source and live-version implications

Any follow-on production change must:

- be a shared improvement to an existing canonical vault path;
- remain deployable on Base, Robinhood, and future EVM chains;
- avoid `chain.id` branches and a Robinhood-only vault;
- document whether the Base live deployment uses an older source/version;
- include Base and Robinhood regression/migration implications; and
- update Track 3's source-status and live-version fields separately.

Track 5 does not recommend a dedicated issuer-aware vault. If the minimum
invariants cannot be met by an approved shared change, the valid outcome is
`do not list Stock Tokens under the current vault designs`.

## Required follow-on shared vault-change specification

The owner-requested concrete mitigation and implementation recommendation is
recorded in
[`stock-token-vault-fix-recommendations.md`](stock-token-vault-fix-recommendations.md).
It distinguishes:

- immediate controls available on the current Base deployment;
- the smallest fail-closed change that prevents new phantom-backed borrowing;
- required deposit and auction companion fixes;
- the preferred permanent share-based behavior;
- total-loss and bad-debt requirements; and
- implementation order, tests, migration implications, and owner gates.

The recommendation does not authorize a production contract or configuration
change.

The specification must define, without implementing yet:

1. **Deposit delta:** actual per-call token balance delta, returned/event amount,
   user credit, limit accounting, and zero/short receipt behavior.
2. **Internal settlement backing:** the maximum live-backed amount transferable
   internally after partial and total loss.
3. **Borrowing value:** no positive borrowing power for a zero-backed claim.
4. **Atomic payment:** no GREEN spend or debt reduction beyond live-backed
   collateral transferred.
5. **Total-loss progress:** liquidation eligibility, active-auction behavior,
   Deleverage/bad-debt resolution, and governance controls at zero.
6. **Post-zero allocation:** treatment of old claims, donations, recovery, and
   new deposits.
7. **Rounding:** share offset, conversion direction, minimum deposit, maximum
   dust, and recovery.
8. **Rewards/monitoring:** units, conversions, events, alerts, and operator
   reconciliation.
9. **Registry/migration:** live funds checks, raw-state cleanup, vault/version
   registration, and rollback constraints.
10. **Test matrix:** both chains, exact candidate token on a pinned fork, issuer
    actions, two-user/two-liquidator ordering, and all downstream consumers.

## Unresolved dependencies and launch blockers

### Pending Track 2

- exact candidate Stock Token proxy, implementation, decimals, and code hash;
- observed pause/blocklist/forced-action/upgrade behavior, including whether
  approvals are gated and whether transfers can invoke callbacks;
- pinned-fork transfer behavior; and
- owner-approved live third-party-contract transferability evidence.

### Pending Track 3

Stable component IDs and source/live-version entries for:

- `SimpleErc20`;
- `RebaseErc20` and `SharesVault`;
- `VaultBook`;
- `AuctionHouse`;
- `CreditEngine`; and
- `CreditRedeem`.

### Explicit launch blockers

1. No production vault is approved.
2. The zero-backed Simple internal-auction invariant failure is unresolved.
3. Rebase total-loss liquidation/deleveraging and post-zero policy are
   unresolved.
4. Per-call short-received deposit measurement is unresolved for both paths.
5. Track 2 exact-token evidence is not integrated.
6. Track 3 stable IDs and live-version matrix are not integrated.
7. The shared vault-change specification has not been approved, implemented,
   audited, migrated, or smoke-tested.
8. Production addresses, feeds, limits, parameters, defaults, and manifests are
   intentionally absent.

## Exact `rh-summary.md` owner-review eligibility

Track 5 does not edit `docs/chains/rh-summary.md`.

Eligible for owner review, but **not closure as an approved vault choice**:

> `docs/chains/rh-summary.md:186`
>
> `- [ ] Finish the SimpleErc20 versus RebaseErc20/SharesVault comparison:`

The comparison itself is complete. The owner can review this checkbox's
evidence, but closing it must not be read as selecting a vault or accepting the
documented risks.

Not eligible for closure:

> `docs/chains/rh-summary.md:189`
>
> `- [ ] Test the chosen vault's accepted behavior for donations, measured deposits, total-balance loss, zero-balance recovery, blocked transfers, withdrawals, and internal-share liquidation.`

No vault has been chosen and the behavior is not accepted.

Eligible to activate as the required next step:

> `docs/chains/rh-summary.md:190`
>
> `- [ ] If the chosen behavior is unacceptable, stop and write a separate vault-change specification before modifying custody code.`

Track 5 establishes that a separate shared vault-change specification is
required. At the owner's later request, the unapproved technical recommendation
is now recorded in `stock-token-vault-fix-recommendations.md`. A dedicated
implementation track, approved specification baseline, production code change,
and deployment authorization remain unopened.

Also not eligible for closure are the Phase 0 deployable-vault choice at
`rh-summary.md:85-88`, the complete chosen-vault exit condition at
`rh-summary.md:200`, and launch readiness at `rh-summary.md:292`. Each still
depends on owner approval and the blockers above.
