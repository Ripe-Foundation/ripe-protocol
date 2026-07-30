# GuardedErc20 consumer inventory

> **30 July 2026 currentness:** The PR #61 candidate described below entered
> `rh` at historical import ancestor `ad831669…` and is retained by frozen
> protocol/pause baseline `ae0cb49…`.
> AuctionHouse safe-conversion preflight and downstream Deleverage consistency
> are part of the current reviewed source. This inventory is validation
> evidence only; no Robinhood deployment, configuration, activation, or release
> has occurred.

This is the G4 inventory rooted at baseline
`a86650b187c523f27c92f05bfe959d06840025a6` and reconciled for the
PR #61 Gate 1 candidate. It covers every `Vault`
read in CreditEngine, AuctionHouse, CreditRedeem, the reviewed-baseline
Deleverage source, Lootbox, and Teller whose result is an amount, a position
discovery input, or a vault-capability input. The machine test verifies the
source hashes, call sites, function names, getter names, classifications, and
policy below
([inventory test](../../../../tests/vaults/test_guarded_consumer_inventory.py)).

## Policy

Collateral valuation, borrowing-power calculation, withdrawal projection, and
post-withdraw amount enforcement must consume either
`getUserAssetAndAmountAtIndex` or `getTotalAmountForUser`. GuardedErc20 makes
both getters backing-aware by returning zero usable amount when exact observed
custody is unknown or below nominal liability
([Guarded source](../../../../contracts/vaults/GuardedErc20.vy#L206),
[backing-aware mutation test](../../../../tests/vaults/test_guarded_erc20.py)).

Position discovery may remain nominal: a consumer may locate an asset or learn
that a nominal balance exists, but it must obtain a backing-aware amount before
using the position for value or borrowing. Capability lookup and Lootbox reward
bookkeeping are not collateral-value or borrowing consumers and are retained
as explicit included exceptions. In particular, Lootbox's vault-total and
loot-share reads affect reward accounting, not CreditEngine collateral value
([Lootbox source](../../../../contracts/core/Lootbox.vy#L812),
[CreditEngine source](../../../../contracts/core/CreditEngine.vy#L723)).

## Frozen machine inventory

Do not hand-edit line numbers or classifications without the corresponding
source review and test update.

<!-- GUARDED_CONSUMER_INVENTORY_BEGIN -->
```json
{
  "schema": 1,
  "baseline": "a86650b187c523f27c92f05bfe959d06840025a6",
  "sources": {
    "contracts/core/AuctionHouse.vy": "e5a1603d27e22abc3fa0bf98971dbc16732afe8647b1fe323916216036998921",
    "contracts/core/CreditEngine.vy": "7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d",
    "contracts/core/CreditRedeem.vy": "0567b9118868f7fc37a0e583580ab6c5cd1e85274747860a6394f1f1c4364c0e",
    "contracts/core/Deleverage.vy": "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138",
    "contracts/core/Lootbox.vy": "669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65",
    "contracts/core/Teller.vy": "4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909"
  },
  "getter_scope": [
    "doesUserHaveBalance",
    "getTotalAmountForUser",
    "getUserAssetAndAmountAtIndex",
    "getUserAssetAtIndexAndHasBalance",
    "getUserLootBoxShare",
    "getTotalAmountForVault",
    "isSupportedVaultAsset",
    "numUserAssets",
    "userAssets"
  ],
  "rows": [
    {
      "id": "AH-420",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 420,
      "function": "_performLiquidationPhases",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Skips a stale liquidation position; no amount or USD value is derived from the Boolean.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-502",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 502,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds position enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-516",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 516,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers a nominal liquidation candidate; downstream collateral terms supply value.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-651",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 651,
      "function": "_swapWithSpecificStabPool",
      "getter": "isSupportedVaultAsset",
      "classification": "capability_discovery_nominal_allowed",
      "reason": "Prevents a stability-pool asset routing collision; it does not value user collateral.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-892",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 892,
      "function": "_canStartAuction",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Checks nominal position existence before consulting liquidation state.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-1204",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1204,
      "function": "withdrawTokensFromVault",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Clamps the Deleverage-requested withdrawal to the backing-aware user amount before safe conversion and mutation.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "CE-723",
      "path": "contracts/core/CreditEngine.vy",
      "line": 723,
      "function": "_getUserBorrowTerms",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds collateral position enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "CE-729",
      "path": "contracts/core/CreditEngine.vy",
      "line": 729,
      "function": "_getUserBorrowTerms",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "The returned amount feeds PriceDesk, collateral value, and maximum debt.",
      "evidence_test": "test_unsafe_backing_failures_keep_terms_with_zero_capacity"
    },
    {
      "id": "CE-1252",
      "path": "contracts/core/CreditEngine.vy",
      "line": 1252,
      "function": "getMaxWithdrawableForAsset",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds USD value and maximum-withdrawal borrowing constraints.",
      "evidence_test": "test_unsafe_backing_failures_keep_terms_with_zero_capacity"
    },
    {
      "id": "CR-190",
      "path": "contracts/core/CreditRedeem.vy",
      "line": 190,
      "function": "_redeemCollateral",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Short-circuits an absent nominal position; it does not compute collateral value.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-579",
      "path": "contracts/core/Deleverage.vy",
      "line": 579,
      "function": "deleverageForWithdrawal",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds withdrawal USD value and projected post-withdraw collateral.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-823",
      "path": "contracts/core/Deleverage.vy",
      "line": 823,
      "function": "_performDeleveragePhases",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Skips a stale requested position without deriving value.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-898",
      "path": "contracts/core/Deleverage.vy",
      "line": 898,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage position enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-911",
      "path": "contracts/core/Deleverage.vy",
      "line": 911,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers candidate assets; the selected path obtains value elsewhere.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1073",
      "path": "contracts/core/Deleverage.vy",
      "line": 1073,
      "function": "_getDeleverageInfo",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage information enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1081",
      "path": "contracts/core/Deleverage.vy",
      "line": 1081,
      "function": "_getDeleverageInfo",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers a nominal position before the backing-aware amount read.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1086",
      "path": "contracts/core/Deleverage.vy",
      "line": 1086,
      "function": "_getDeleverageInfo",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds PriceDesk and maximum deleveragable USD.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-298",
      "path": "contracts/core/Lootbox.vy",
      "line": 298,
      "function": "_claimLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds cleanup enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-302",
      "path": "contracts/core/Lootbox.vy",
      "line": 302,
      "function": "_claimLoot",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers nominal positions for reward cleanup, not collateral value.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-349",
      "path": "contracts/core/Lootbox.vy",
      "line": 349,
      "function": "getClaimableLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds claimable-reward enumeration only.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-351",
      "path": "contracts/core/Lootbox.vy",
      "line": 351,
      "function": "getClaimableLoot",
      "getter": "userAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Retrieves an asset identity for reward accounting, not an amount.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-812",
      "path": "contracts/core/Lootbox.vy",
      "line": 812,
      "function": "_getLatestDepositPoints",
      "getter": "getUserLootBoxShare",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Computes configured deposit-reward share; it does not set collateral value or borrowing power.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-830",
      "path": "contracts/core/Lootbox.vy",
      "line": 830,
      "function": "_refreshAssetUsdValue",
      "getter": "getTotalAmountForVault",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Refreshes global deposit reward points; it is outside CreditEngine collateral valuation.",
      "evidence_test": "test_guarded_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "TL-381",
      "path": "contracts/core/Teller.vy",
      "line": 381,
      "function": "_withdraw",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Enforces the remaining minimum deposit balance after withdrawal.",
      "evidence_test": "test_g1_backing_aware_view_mutant_restores_phantom_value"
    }
  ]
}
```
<!-- GUARDED_CONSUMER_INVENTORY_END -->

## Test-to-consumer result

The machine inventory test is exhaustive over the getter scope above. It also
requires every `value_backing_required` row to use one of the two
backing-aware getters and every nominally allowed row to carry nonempty
included/excluded reasoning. The Guarded mutation suite independently proves
that replacing the shared backing predicate with `true` restores phantom
amounts after a one-unit custody deficit
([mutation test](../../../../tests/vaults/test_guarded_erc20.py)).

This inventory is source evidence only. Corrected PR #61 entered `rh` at
historical import ancestor `ad831669943ccfe7b9ed57454995dfce51630a66`; that
later integration does not
change this inventory's reviewed getter scope and does not authorize a
deployment, registry assignment, asset configuration, or release.
