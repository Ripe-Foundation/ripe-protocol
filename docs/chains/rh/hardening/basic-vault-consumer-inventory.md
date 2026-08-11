# BasicVault consumer inventory

> **10 August 2026 repository currentness:** the shared BasicVault safety change
> is integrated in the current `rh` source tree. This source state does not
> modify an immutable deployed vault, configure an asset, or activate a launch
> route.

This is the G4 inventory rooted at feature baseline
`1e36c0c3dd168dbf292456eb5760b02d1f1e4a80`. It covers every `Vault`
read anywhere in the complete production `contracts/**/*.vy` tree whose result
is an amount, a position-discovery input, or a vault-capability input. The
machine test discovers the callers before comparing the source hashes, call
sites, function names, getter names, classifications, and policy below
([inventory test](../../../../tests/vaults/test_basic_vault_consumer_inventory.py)).

## Policy

Collateral valuation, borrowing-power calculation, withdrawal projection, and
post-withdraw amount enforcement must consume either
`getUserAssetAndAmountAtIndex` or `getTotalAmountForUser`. BasicVault makes
both getters backing-aware by returning zero usable amount when observed
custody is below nominal liability. Invalid typed balance observations revert
instead of being interpreted as usable backing
([BasicVault source](../../../../contracts/vaults/modules/BasicVault.vy#L147),
[backing-aware safety test](../../../../tests/vaults/test_basic_vault_safety.py)).

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

<!-- BASIC_VAULT_CONSUMER_INVENTORY_BEGIN -->
```json
{
  "schema": 1,
  "baseline": "1e36c0c3dd168dbf292456eb5760b02d1f1e4a80",
  "sources": {
    "contracts/core/AuctionHouse.vy": "d0414b5b3d8248c65dd16a722b4333767c386170f76dfe69913e4c1de1abed8f",
    "contracts/core/CreditEngine.vy": "d8fae4e9cffff0d95adbe48a59e57c622585f021017b94089f8a70e615c36e43",
    "contracts/core/CreditRedeem.vy": "36daec6010821ddc5a0da31e958c692869bfdd7797fc90431e5922f9bb516937",
    "contracts/core/Deleverage.vy": "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138",
    "contracts/core/HumanResources.vy": "7422f2dee9b5898b0f163371477bbea7c4a9b03a22b393e15594bbaadb00cddb",
    "contracts/core/Lootbox.vy": "9a39a2dbf44043498908da5fb2c0c99e270417243e7608543d585f841d07b0f1",
    "contracts/core/Teller.vy": "753417c6e642deb3753f9138dd9577cc4a6e6d1a10179cacdadb4ade7f65f211"
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
      "id": "AH-419",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 419,
      "function": "_performLiquidationPhases",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Skips a deficient priority asset before any stability-pool swap or auction attempt.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-501",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 501,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-515",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 515,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "Enumerates only candidates with a nonzero backing-aware amount before liquidation handling.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-891",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 891,
      "function": "_canStartAuction",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Prevents creation of an auction whose collateral became deficient.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-1199",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1199,
      "function": "withdrawTokensFromVault",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Clamps the Deleverage-requested withdrawal to the backing-aware user amount before safe conversion and mutation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-1227",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1227,
      "function": "_transferCollateral",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Soft-skips deficient collateral before internal transfer or external withdrawal settlement.",
      "evidence_test": "test_safe_nominal_volatile_deleverage_skips_deficit_and_continues"
    },
    {
      "id": "CE-727",
      "path": "contracts/core/CreditEngine.vy",
      "line": 727,
      "function": "_getUserBorrowTerms",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds collateral position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "CE-733",
      "path": "contracts/core/CreditEngine.vy",
      "line": 733,
      "function": "_getUserBorrowTerms",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "The returned amount feeds PriceDesk, collateral value, and maximum debt.",
      "evidence_test": "test_unsafe_backing_failures_keep_terms_with_zero_capacity"
    },
    {
      "id": "CE-1260",
      "path": "contracts/core/CreditEngine.vy",
      "line": 1260,
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
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Soft-skips a deficient redemption entry before pricing or collateral movement.",
      "evidence_test": "test_credit_redeem_many_skips_deficient_and_preserves_healthy_entry"
    },
    {
      "id": "DL-579",
      "path": "contracts/core/Deleverage.vy",
      "line": 579,
      "function": "deleverageForWithdrawal",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds withdrawal USD value and projected post-withdraw collateral.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-823",
      "path": "contracts/core/Deleverage.vy",
      "line": 823,
      "function": "_performDeleveragePhases",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Skips a stale requested position without deriving value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-898",
      "path": "contracts/core/Deleverage.vy",
      "line": 898,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-911",
      "path": "contracts/core/Deleverage.vy",
      "line": 911,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers candidate assets; the selected path obtains value elsewhere.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1073",
      "path": "contracts/core/Deleverage.vy",
      "line": 1073,
      "function": "_getDeleverageInfo",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage information enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1081",
      "path": "contracts/core/Deleverage.vy",
      "line": 1081,
      "function": "_getDeleverageInfo",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers a nominal position before the backing-aware amount read.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1086",
      "path": "contracts/core/Deleverage.vy",
      "line": 1086,
      "function": "_getDeleverageInfo",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds PriceDesk and maximum deleveragable USD.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "HR-390",
      "path": "contracts/core/HumanResources.vy",
      "line": 390,
      "function": "hasRipeBalance",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Checks whether a contributor has a RIPE governance-vault position; it neither values BasicVault collateral nor grants borrowing power.",
      "evidence_test": "test_hr_has_ripe_balance_no_balance"
    },
    {
      "id": "LB-299",
      "path": "contracts/core/Lootbox.vy",
      "line": 299,
      "function": "_claimLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds cleanup enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-303",
      "path": "contracts/core/Lootbox.vy",
      "line": 303,
      "function": "_claimLoot",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers nominal positions for reward cleanup, not collateral value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-351",
      "path": "contracts/core/Lootbox.vy",
      "line": 351,
      "function": "getClaimableLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds claimable-reward enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-353",
      "path": "contracts/core/Lootbox.vy",
      "line": 353,
      "function": "getClaimableLoot",
      "getter": "userAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Retrieves an asset identity for reward accounting, not an amount.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-825",
      "path": "contracts/core/Lootbox.vy",
      "line": 825,
      "function": "_getLatestDepositPoints",
      "getter": "getUserLootBoxShare",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Computes configured deposit-reward share; it does not set collateral value or borrowing power.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-843",
      "path": "contracts/core/Lootbox.vy",
      "line": 843,
      "function": "_refreshAssetUsdValue",
      "getter": "getTotalAmountForVault",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Refreshes global deposit reward points; it is outside CreditEngine collateral valuation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "TL-422",
      "path": "contracts/core/Teller.vy",
      "line": 422,
      "function": "_withdraw",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Enforces the remaining minimum deposit balance after withdrawal.",
      "evidence_test": "test_deficit_zeroes_usable_views_but_surplus_preserves_only_nominal"
    }
  ]
}
```
<!-- BASIC_VAULT_CONSUMER_INVENTORY_END -->

## Test-to-consumer result

The machine inventory test is exhaustive over the getter scope across every
production Vyper source, including HumanResources rather than only the six
initially reviewed consumers. It also
requires every `value_backing_required` row to use one of the two
backing-aware getters and every nominally allowed row to carry nonempty
included/excluded reasoning. The BasicVault safety suite independently proves
that a one-unit custody deficit zeroes the value-bearing getter results while
preserving the nominal position-discovery boundary
([safety test](../../../../tests/vaults/test_basic_vault_safety.py)).

This inventory is source evidence only. Corrected PR #61 entered `rh` at
historical import ancestor `ad831669943ccfe7b9ed57454995dfce51630a66`; that
later integration does not
change this inventory's reviewed getter scope and does not authorize a
deployment, registry assignment, asset configuration, or release.
