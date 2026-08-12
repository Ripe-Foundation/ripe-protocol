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
([Lootbox source](../../../../contracts/core/Lootbox.vy#L912),
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
    "contracts/core/AuctionHouse.vy": "af1856ce2d6e3d64b965933916994322f41d49f81e2f199f2b16ac1e92eb5951",
    "contracts/core/CreditEngine.vy": "96e7deef17d5fe094c964090850cae9eb9293350eff94567519444631701deb6",
    "contracts/core/CreditRedeem.vy": "36daec6010821ddc5a0da31e958c692869bfdd7797fc90431e5922f9bb516937",
    "contracts/core/Deleverage.vy": "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138",
    "contracts/core/HumanResources.vy": "7422f2dee9b5898b0f163371477bbea7c4a9b03a22b393e15594bbaadb00cddb",
    "contracts/core/Lootbox.vy": "279b859a6e5234676e091cecb8736aeadac68bc8f1b909267b7a06c69a901f43",
    "contracts/core/Teller.vy": "fe99197239821ef0eae63409fdca39aa4bd84b501697915150d0fec050406476",
    "contracts/core/VaultMigrator.vy": "4836fc22e4645eb6008126a3295001286d3e3f2ad216d67c9c3cf63183b6d8e7"
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
      "id": "AH-431",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 431,
      "function": "_performLiquidationPhases",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Skips a deficient priority asset before any stability-pool swap or auction attempt.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-513",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 513,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-527",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 527,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "Enumerates only candidates with a nonzero backing-aware amount before liquidation handling.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-902",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 902,
      "function": "_canStartAuction",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Prevents creation of an auction whose collateral became deficient.",
      "evidence_test": "test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation"
    },
    {
      "id": "AH-1215",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1215,
      "function": "withdrawTokensFromVault",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Clamps the Deleverage-requested withdrawal to the backing-aware user amount before safe conversion and mutation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-1243",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1243,
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
      "id": "CE-1249",
      "path": "contracts/core/CreditEngine.vy",
      "line": 1249,
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
      "id": "LB-300",
      "path": "contracts/core/Lootbox.vy",
      "line": 300,
      "function": "_claimLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds cleanup enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-304",
      "path": "contracts/core/Lootbox.vy",
      "line": 304,
      "function": "_claimLoot",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers nominal positions for reward cleanup, not collateral value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-357",
      "path": "contracts/core/Lootbox.vy",
      "line": 357,
      "function": "getClaimableLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds claimable-reward enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-359",
      "path": "contracts/core/Lootbox.vy",
      "line": 359,
      "function": "getClaimableLoot",
      "getter": "userAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Retrieves an asset identity for reward accounting, not an amount.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-438",
      "path": "contracts/core/Lootbox.vy",
      "line": 438,
      "function": "_getDepositLootData",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Distinguishes a live reward position from an exited one when deciding whether a zero-paying category may resolve terminally; it does not value collateral.",
      "evidence_test": "test_exited_funded_dust_gets_one_wei_and_inactive_category_exhausts"
    },
    {
      "id": "LB-892",
      "path": "contracts/core/Lootbox.vy",
      "line": 892,
      "function": "_getLatestDepositPoints",
      "getter": "getUserLootBoxShare",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Computes configured deposit-reward share; it does not set collateral value or borrowing power.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-912",
      "path": "contracts/core/Lootbox.vy",
      "line": 912,
      "function": "_refreshAssetUsdValue",
      "getter": "getTotalAmountForVault",
      "classification": "reward_accounting_nominal_allowed",
      "reason": "Refreshes global deposit reward points; it is outside CreditEngine collateral valuation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "TL-407",
      "path": "contracts/core/Teller.vy",
      "line": 407,
      "function": "_withdraw",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Enforces the remaining minimum deposit balance after withdrawal.",
      "evidence_test": "test_deficit_zeroes_usable_views_but_surplus_preserves_only_nominal"
    },
    {
      "id": "VM-157",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 154,
      "function": "migrateVaultPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds ordinary-vault source position enumeration only.",
      "evidence_test": "test_normal_migration_rejects_more_than_twenty_source_asset_slots"
    },
    {
      "id": "VM-165",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 162,
      "function": "migrateVaultPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live source assets; exact transferred value is proven by Teller and token-balance deltas.",
      "evidence_test": "test_all_user_assets_migrate_with_one_housekeeping_call"
    },
    {
      "id": "VM-189",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 186,
      "function": "migrateVaultPositions",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Verifies that the exact ordinary-vault withdrawal removed the source position; it does not derive value.",
      "evidence_test": "test_all_user_assets_migrate_with_one_housekeeping_call"
    },
    {
      "id": "VM-256",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 253,
      "function": "migrateRipeGovPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds governance-vault source position enumeration only.",
      "evidence_test": "test_governance_migration_rejects_more_than_five_source_asset_slots"
    },
    {
      "id": "VM-264",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 261,
      "function": "migrateRipeGovPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live governance assets before the backing-aware migration snapshot and exact receipt checks.",
      "evidence_test": "test_one_user_migrates_all_governance_assets_with_one_housekeeping_call"
    },
    {
      "id": "VM-352",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 348,
      "function": "migrateLegacyRipeGovPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds legacy governance source position enumeration only.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-360",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 356,
      "function": "migrateLegacyRipeGovPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live legacy assets before their backing-aware snapshots are captured.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-479",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 472,
      "function": "_getPreMigrationData",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Captures the source amount used to construct and verify the governance migration payload.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-600",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 523,
      "function": "_verifyRipeGovExport",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Requires the backing-aware source amount to be zero after the exact governance-vault export.",
      "evidence_test": "test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points"
    },
    {
      "id": "VM-601",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 524,
      "function": "_verifyRipeGovExport",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Verifies removal of the exported source position after the amount and token deltas have been checked.",
      "evidence_test": "test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points"
    },
    {
      "id": "VM-626",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 549,
      "function": "_verifyRipeGovImport",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Verifies that the imported governance position is discoverable after shares and exact receipt checks.",
      "evidence_test": "test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points"
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
