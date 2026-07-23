# Robinhood Stock Token Vault Decision Record

**Decision status:** Conditional; owner decision required

**Recommended outcome:** `conditional — shared vault change specification required`

**Owner approval status:** Not approved

**Evidence commit:** `ee270abd317daae25d434a4a256346b5a0cb95d3`

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

The owner approved continuation of repository analysis after the
zero-backed-liquidation stop condition was found. That approval did **not**:

- accept the custody, liquidation, first-mover, post-zero, or monitoring risk;
- select a production vault;
- authorize a production contract change;
- authorize defaults, migration, manifest, or asset-configuration changes; or
- authorize deployment or a live transaction.

All of those gates remain closed.

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
| Partial-loss external liquidation | Delivers while live balance remains | Delivers pro-rata live claim | Candidate-acceptable |
| Total-loss external liquidation | Atomic revert | Atomic revert | Safe funds; blocked progress |
| Total-loss internal liquidation | Charges for zero-backed nominal claim | Atomic revert | Simple rejected; Rebase still blocked |
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

Thus a successful internal balance move cannot be treated as proof that an
issuer-controlled token is deliverable. A follow-on specification must make
live backing an explicit precondition of the amount returned to settlement.

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
- observed pause/blocklist/forced-action/upgrade behavior;
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
required. That specification is a new owner-approved track; it is not written or
implemented here.

Also not eligible for closure are the Phase 0 deployable-vault choice at
`rh-summary.md:85-88`, the complete chosen-vault exit condition at
`rh-summary.md:200`, and launch readiness at `rh-summary.md:292`. Each still
depends on owner approval and the blockers above.
