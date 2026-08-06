# Fresh-agent handoff: Stability Pool contract source only

> [!CAUTION]
> **Historical and superseded as active instructions.** This source-only prompt
> was executed from its bound baseline and is retained only as implementation
> provenance. Do not reuse the instruction to "use this prompt verbatim."
> Subsequent owner decisions retained `getTotalValue` and `getTotalUserValue`,
> omitted the StabilityPool export of `canActivateClaimAsset` to satisfy
> EIP-170, and restricted permissionless manual activation to the paused state.
> Compilation, testing, validation metadata, and adversarial follow-up are now
> complete for the isolated candidate. See the
> [as-built outcome](implementation-specification.md#as-built-outcome-2026-08-05)
> for the finished behavior and remaining repository-level blockers. This
> archive grants no integration, deployment, activation, signer, or release
> authority.

Use this prompt verbatim for the first implementation step.

---

You are implementing the first, source-only slice of the Robinhood Stability
Pool hardening work.

## Objective

Make the approved smart-contract source changes and then stop so the owner can
review the complete contract diff before any compilation, tests, validation,
generated-file updates, or configuration work begins.

This is deliberately a source-review checkpoint. A complete implementation in
this step means “the two contract source files contain the intended candidate
logic,” not “the candidate has passed tests or is ready to deploy.”

### Instruction precedence

Where this prompt and `implementation-specification.md` conflict about process,
allowed files, commands, compilation, tests, validation, or the source-export
surface, this prompt governs for this source-only slice. The implementation
specification remains authoritative for accounting and state-transition
semantics unless this prompt expressly overrides it.

### Owner gate S0: APPROVED ABI-size decision

**Owner approval recorded: 2026-08-05.** The owner explicitly approved removing
the four external views listed below to make room for the Tier A+B candidate.
This approval is limited to those four selectors and does not authorize any
other ABI removal, implementation phase, test, integration, deployment, or
activation action.

The full Tier A+B surface was independently compilation-probed against the
bound source and exceeded EIP-170:

| Probe | Runtime bytes | EIP-170 headroom |
| --- | ---: | ---: |
| Existing StabilityPool | 23,960 | +616 |
| Full specified surface | 26,817 | -2,241 |
| Full surface with `-O codesize` | 26,081 | -1,505 |
| Full surface plus the Section 11 StabVault export trim | 23,861 | +715 |

The four views removed by the approved trim have no production-contract
consumers in the bound repository. Remove exactly:

```text
valueToShares
sharesToValue
getTotalValue
getTotalUserValue
```

Gate S0 is satisfied. Do not implement an oversized candidate and do not choose
a different size reduction yourself.

## Workspace and baseline

Work only in:

```text
/Users/wigglez/dev/ripe-protocol-rh-stability-pool-hardening-spec
```

Expected branch:

```text
codex/rh-stability-pool-hardening-spec
```

Expected starting source baseline:

```text
commit: 0e093e2c23eaf6cc931fe7ff15c903a99ea36738
tree:   8b6028eed43695e13c5192d079f04dd941f0d74f
```

Before editing, read completely:

```text
docs/chains/rh/stability-pool/implementation-specification.md
docs/chains/rh/stability-pool/long-term-hardening-plan.md
contracts/vaults/modules/StabVault.vy
contracts/vaults/StabilityPool.vy
contracts/vaults/modules/VaultData.vy
contracts/registries/PriceDesk.vy
contracts/core/AuctionHouse.vy
```

These three Markdown files are approved pre-existing untracked worktree
residue:

```text
docs/chains/rh/stability-pool/implementation-specification.md
docs/chains/rh/stability-pool/long-term-hardening-plan.md
docs/chains/rh/stability-pool/source-only-agent-handoff.md
```

Do not modify, stage, move, or delete them.

Run only read-only Git checks before editing:

```bash
git branch --show-current
git rev-parse 'HEAD^{commit}' 'HEAD^{tree}'
git status --short -uall
```

The expected initial status entries are exactly:

```text
?? docs/chains/rh/stability-pool/implementation-specification.md
?? docs/chains/rh/stability-pool/long-term-hardening-plan.md
?? docs/chains/rh/stability-pool/source-only-agent-handoff.md
```

If the branch, commit, tree, or pre-existing changed-path set differs from the
values above, stop and report the drift. Do not rebase, merge, pull, reset,
restore, stash, or otherwise reconcile it.

## Exact writable file ceiling

You may modify exactly these two files:

```text
contracts/vaults/modules/StabVault.vy
contracts/vaults/StabilityPool.vy
```

Do not create or modify any other file.

In particular, do not touch:

- tests or test fixtures;
- AuctionHouse, PriceDesk, Teller, MissionControl, VaultData, Switchboards, or
  any other production contract;
- interfaces;
- Defaults or Robinhood configuration;
- scripts;
- ABI JSON;
- artifact expectations;
- block-clock or other inventories;
- documentation;
- dependency or environment files; or
- generated files of any kind.

If the intended source behavior cannot be implemented entirely within the two
allowed contract files, stop and explain the exact dependency. Do not expand
scope yourself.

## Prohibited actions in this step

Do not:

- write, edit, or generate tests;
- run pytest or any test command;
- compile Vyper contracts;
- run ABI exporters;
- run artifact, bytecode, size, inventory, gas, lint, formatting, or
  configuration validators;
- regenerate checked outputs;
- install or update dependencies;
- use RPCs, forks, signers, wallets, or external services;
- stage files;
- create a commit;
- push;
- merge or rebase; or
- deploy, configure, activate, or execute any on-chain action.

You may use read-only source searches and `git diff` while implementing. At the
end, only inspect the source diff and worktree status. Do not attempt to prove
the code compiles or passes tests in this step.

## Controlling source design

Implement the Tier A + Tier B source candidate described by the implementation
specification. The decisions below are locked for this slice.

### 1. Preserve the existing accounting architecture

Do not add a stored enum or iterable dormant list.

Derive claim-asset state from existing storage:

```text
absent:  claimable balance == 0 and active index == 0
dormant: claimable balance > 0 and active index == 0
active:  claimable balance > 0 and active index > 0
```

Claims and redemptions must continue to operate directly from the balance
mappings. Dormant balances must remain claimable and redeemable.

Preserve the existing sentinel layout for `numClaimableAssets`. Index zero
remains unused. Do not reinterpret the existing public getter.

### 2. Add the locked constants

In `StabVault.vy`, add constants equivalent to:

```vyper
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

Replace internal use of `DUST_USD_THRESHOLD` with
`RETENTION_USD_THRESHOLD` without changing its value or boundary semantics.

### 3. Add source-level observability

Add events equivalent to:

```text
ClaimAssetActivated(stabAsset indexed, claimAsset indexed, balance,
                    activeCount)
ClaimAssetDeactivated(stabAsset indexed, claimAsset indexed, balance,
                      activeCount, reason)
ClaimAssetLeftDormant(stabAsset indexed, claimAsset indexed, balance,
                      activeCount, reason)
```

Emit the dormant event only when a receipt increases an inactive pair balance
and the pair remains dormant. Do not emit it for repeated permissionless
activation attempts.

### 4. Add count and state views

Add:

```text
getNumActiveClaimAssets(stabAsset) -> uint256
getClaimAssetState(stabAsset, claimAsset) -> uint256
canActivateClaimAsset(stabAsset, claimAsset)
    -> (canActivate, usdValue, capacityRemaining)
```

Active count is zero when `numClaimableAssets` is zero; otherwise it is
`numClaimableAssets - 1`.

State values are the locked absent/dormant/active constants above.

`canActivateClaimAsset` must use exactly the same price, threshold, custody,
and capacity semantics as actual activation. Ordinary unavailable pricing
returns a non-activatable result rather than invoking PriceDesk's configured-
feed raise.

### 5. Keep active NAV fail-closed

Do not change `_getUsdValue` or active NAV valuation to fail open.

Add a separate internal activation-value helper:

```text
_getActivationUsdValue(asset, amount, green, savingsGreen, priceDesk)
```

Behavior:

- zero amount returns zero;
- GREEN value equals amount;
- sGREEN uses `convertToAssets`;
- other assets call `PriceDesk.getUsdValue(asset, amount, False)`; and
- zero means no usable activation value, not proven dust.

Do not add quarantine state or silently skip stale configured assets in active
NAV.

### 6. Strengthen receipt accounting

Modify `_addClaimableBalance` and its internal callers without changing either
AuctionHouse-facing external selector.

The helper must use aggregate shadow liability in this literal order:

```text
assert stabAsset != empty(address)
assert claimAsset != empty(address)
assert reportedAmount != 0

custody = IERC20(claimAsset).balanceOf(self)
priorLiability = totalClaimableBalances[claimAsset]
assert custody >= priorLiability
availableUnaccounted = custody - priorLiability
assert reportedAmount <= availableUnaccounted

newPairBalance = oldPairBalance + reportedAmount
newTotalLiability = priorLiability + reportedAmount
```

Use strict receipt behavior. Do not partially credit a short receipt. Do not
use total custody as the receipt amount, and do not compare custody only with
the pair liability.

Ensure the liability credit remains in the same atomic transaction as the
existing swap/redemption behavior so a later revert rolls it back.

Strict receipt accounting has a deliberate liveness residual: if custody ever
falls below aggregate liability, every later receipt of that token fails closed
and a liquidation routed into the pool for that token can revert until the
deficit is resolved. Standard-token admission reduces the risk but does not
erase it. Preserve this behavior for the source candidate and call it out
explicitly in the final handoff for owner/security review.

### 7. Gate add-time activation

After the full receipt is credited:

1. If already active, keep it active without repricing.
2. If cumulative activation value is zero, leave dormant with
   `DORMANT_NO_PRICE`.
3. If cumulative value is below `$0.25`, leave dormant with
   `DORMANT_BELOW_FLOOR`.
4. If active count is already 12, leave dormant with `DORMANT_CAPACITY`.
5. Otherwise register and emit activation.

Pricing or capacity must never discard an already received and validly credited
liability. A full active list must not revert solely because registration is
unavailable.

Centralize registration and require a nonzero pair balance, zero current index,
and active count below 12.

### 8. Harden deactivation

Preserve the existing reduction behavior:

- zero residual removes the active index;
- nonzero residual with nonzero value below `$0.10` removes only the active
  index;
- zero/unavailable value is not classified as dust; and
- liability and custody are not deleted by registry removal.

Update swap-and-pop removal so it always clears the vacated final array slot,
including removal of the last item. Preserve reverse-index correctness and the
existing sentinel count convention. Emit the appropriate deactivation event
after state is consistent.

### 9. Add bounded permissionless maintenance

Add:

```text
pruneClaimableAssets(
    stabAsset,
    claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]
)

activateClaimAssets(
    stabAsset,
    claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]
)
```

Both functions must be external, permissionless, bounded by the supplied
candidate array, idempotent, and callable while paused. Neither may scan a full
registry or change custody, liabilities, or shares.

Pruning:

- ignores absent and dormant candidates;
- removes active zero balances;
- uses non-raising valuation for active nonzero balances;
- does nothing on price zero/unavailable;
- deactivates only when nonzero value is below `$0.10`; and
- safely handles empty arrays and duplicates.

Activation:

- ignores absent and already-active candidates;
- verifies custody is not below aggregate liability;
- uses cumulative non-raising value;
- activates at or above `$0.25` only when capacity exists;
- leaves balances dormant when price or capacity is insufficient; and
- safely handles empty arrays and duplicates.

### 10. Prohibit GREEN as a Stability asset

In `_depositTokensInVault`, reject `_asset == _a.greenToken` before share or
balance changes.

Also reject `_stabAsset == _greenToken` in both liquidation swap entry points.

Do not prohibit GREEN as a claim asset for a non-GREEN Stability asset. GREEN
claims remain valid and count as one ordinary active slot.

### 11. Trim unused StabVault exports to satisfy EIP-170

Under the recorded Gate S0 approval, replace:

```text
exports: stabVault.__interface__
```

with selective exports containing exactly:

```text
stabVault.claimableBalances
stabVault.totalClaimableBalances
stabVault.claimableAssets
stabVault.indexOfClaimableAsset
stabVault.numClaimableAssets
stabVault.swapForLiquidatedCollateral
stabVault.swapWithClaimableGreen
stabVault.claimFromStabilityPool
stabVault.claimManyFromStabilityPool
stabVault.redeemFromStabilityPool
stabVault.redeemManyFromStabilityPool
stabVault.getNumActiveClaimAssets
stabVault.getClaimAssetState
stabVault.canActivateClaimAsset
stabVault.pruneClaimableAssets
stabVault.activateClaimAssets
```

Do not export `valueToShares`, `sharesToValue`, `getTotalValue`, or
`getTotalUserValue`. Keep their internal helpers where production logic still
uses them. Do not remove any other existing selector.

The size figures above are probe evidence, not final validation. The later
validation slice must recompile the owner-reviewed source and may reopen the
provisional cap of 12 if gas or final bytecode evidence requires it. Do not
change the cap during this source-only slice.

### 12. Guard StabilityPool recovery without editing VaultData

Do not modify `VaultData.vy`.

In `StabilityPool.vy`, replace wholesale `vaultData.__interface__` export with
selective exports for every current public getter/external function except
`recoverFunds` and `recoverFundsMany`:

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

Then define wrapper-owned `recoverFunds` and `recoverFundsMany` functions with
the same signatures and maximum batch size as the existing exported functions.

Each recovery must:

1. preserve the existing Switchboard authorization;
2. require `stabVault.totalClaimableBalances[asset] == 0`; and
3. call `vaultData._recoverFunds(recipient, asset)`.

For the many variant, any liable token must revert the complete transaction.
Preserve the existing VaultData recovery event and other recovery guards.

Vyper 0.4.3 selective exports and this wrapper pattern were compilation-probed
successfully while preparing the handoff. Do not run that probe or any compiler
in this source-only step.

## Explicitly deferred behavior

Do not implement any of the following now:

- automatic oracle quarantine;
- a stored five-state registry;
- governance retirement or sweeping;
- native-token floor configuration;
- MissionControl or Switchboard changes;
- AuctionHouse receipt-order changes;
- partial short-receipt credit;
- an iterable dormant set;
- keeper rewards;
- a new in-kind exit; or
- launch configuration changes.

The existing active-NAV stale-feed denial-of-service risk remains explicit and
will be addressed by later admission, monitoring, pause/runbook, and validation
work. Do not disguise it with fail-open NAV pricing.

The strict-receipt custody-deficit liquidation denial described in Section 6 is
also an explicit residual requiring owner/security acceptance.

## Source-quality requirements

- Follow existing Vyper 0.4.3 style and naming.
- Keep helpers single-purpose and centralize transitions.
- Preserve all existing external selectors except for the intentional new
  functions; recovery wrappers must retain their existing selectors.
- Avoid duplicated registration/removal logic.
- Use stable developer assertion messages consistent with nearby code.
- Do not leave TODOs, commented-out alternatives, debug code, or speculative
  abstractions.
- Do not reformat unrelated source.
- Preserve checks-effects-interactions ordering and atomic rollback behavior.

## Stop and handoff

After editing the two allowed files, stop. Do not compile or test.

Perform only these read-only review checks:

```bash
git status --short -uall
git diff -- contracts/vaults/modules/StabVault.vy contracts/vaults/StabilityPool.vy
git diff --stat -- contracts/vaults/modules/StabVault.vy contracts/vaults/StabilityPool.vy
```

Confirm that the only newly modified paths are the two allowed contract files,
in addition to the three pre-existing untracked Markdown files named above. If
any other path changed, stop and report it without cleaning or hiding it.

Do not stage or commit.

Your final response must include:

1. exact branch, starting commit, and starting tree;
2. exact modified paths;
3. a concise source-change summary organized by risk addressed;
4. any implementation uncertainty or deviation from this prompt;
5. confirmation that no tests, compiler, validators, generators, RPCs, staging,
   commits, pushes, or deployments were run;
6. final `git status --short -uall`;
7. a clear statement that the contract diff is ready for owner review but is
   uncompiled and unvalidated; and
8. the complete `git diff` output inline so the owner can review one
   self-contained artifact.

Do not describe the work as complete, safe, audited, tested, deployment-ready,
or integration-ready.

---
