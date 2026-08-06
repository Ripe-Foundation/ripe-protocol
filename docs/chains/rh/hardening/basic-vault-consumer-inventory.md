# BasicVault consumer inventory

> **4 August 2026 candidate currentness:** the shared BasicVault safety change
> is feature-branch source only. It does not modify an immutable deployed vault,
> integrate into `rh`, configure an asset, or activate a launch route.

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
    "contracts/core/AuctionHouse.vy": "3fe2ae20b013ce3493daa272270ebf65324656561a807ea8df878e1bc87dfad3",
    "contracts/core/CreditEngine.vy": "05bb1157c6885fc734cc4831efa2fe6aa4c189d14a1bc22bb80472103de105bb",
    "contracts/core/CreditRedeem.vy": "62f6aa664becc2df31702dcb88c28f2a1bbf749a5f9d665a3ea3d7bf69283bdd",
    "contracts/core/Deleverage.vy": "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138",
    "contracts/core/HumanResources.vy": "5f5712002ae22fed15829b8488c1cdf2e17cfef4f82ce66903b04fa562c749cb",
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
      "id": "AH-421",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 421,
      "function": "_performLiquidationPhases",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Skips a deficient priority asset before any stability-pool swap or auction attempt.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-503",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 503,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-517",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 517,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "Enumerates only candidates with a nonzero backing-aware amount before liquidation handling.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-652",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 652,
      "function": "_swapWithSpecificStabPool",
      "getter": "isSupportedVaultAsset",
      "classification": "capability_discovery_nominal_allowed",
      "reason": "Prevents a stability-pool asset routing collision; it does not value user collateral.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-893",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 893,
      "function": "_canStartAuction",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Prevents creation of an auction whose collateral became deficient.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-1201",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1201,
      "function": "withdrawTokensFromVault",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Clamps the Deleverage-requested withdrawal to the backing-aware user amount before safe conversion and mutation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-1229",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1229,
      "function": "_transferCollateral",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Soft-skips deficient collateral before internal transfer or external withdrawal settlement.",
      "evidence_test": "test_safe_nominal_volatile_deleverage_skips_deficit_and_continues"
    },
    {
      "id": "CE-723",
      "path": "contracts/core/CreditEngine.vy",
      "line": 723,
      "function": "_getUserBorrowTerms",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds collateral position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
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
      "id": "LB-298",
      "path": "contracts/core/Lootbox.vy",
      "line": 298,
      "function": "_claimLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds cleanup enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-302",
      "path": "contracts/core/Lootbox.vy",
      "line": 302,
      "function": "_claimLoot",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers nominal positions for reward cleanup, not collateral value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-349",
      "path": "contracts/core/Lootbox.vy",
      "line": 349,
      "function": "getClaimableLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds claimable-reward enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-351",
      "path": "contracts/core/Lootbox.vy",
      "line": 351,
      "function": "getClaimableLoot",
      "getter": "userAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Retrieves an asset identity for reward accounting, not an amount.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-812",
      "path": "contracts/core/Lootbox.vy",
      "line": 812,
      "function": "_getLatestDepositPoints",
      "getter": "getUserLootBoxShare",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Computes configured deposit-reward share; it does not set collateral value or borrowing power.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-830",
      "path": "contracts/core/Lootbox.vy",
      "line": 830,
      "function": "_refreshAssetUsdValue",
      "getter": "getTotalAmountForVault",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Refreshes global deposit reward points; it is outside CreditEngine collateral valuation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "TL-381",
      "path": "contracts/core/Teller.vy",
      "line": 381,
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
