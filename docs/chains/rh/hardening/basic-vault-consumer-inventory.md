# BasicVault consumer inventory

> **15 August 2026 PR #143 scope note:** PR #143 refreshes only AuctionHouse's
> source identity and call-site rows. After rebasing onto remediation commit
> `348f8c1ed5b95be7d44b8458ab499c61c5b65660`, the inherited Deleverage,
> Lootbox, and Teller identities are also current and the complete enforcement
> test passes. PR #143 does not claim to have re-reviewed those upstream deltas.
> The underlying B-AUD-008 candidate was originally reviewed at
> `f9152f27ab8b14ede0ce562974430d57168960b0` and rebased for PR publication onto
> remediation commit `c3bc780d5b3b59193389c917fd6543312f5ee6c3`, with the
> AuctionHouse consumer rows refreshed for the SC-01/SC-02/SC-08 conservation
> candidate on draft PR #143. The package does not modify an immutable deployed
> vault, configure an asset, or activate a launch route.
>
> **15 August 2026 base reconciliation:** source pins and line locators were
> refreshed at `1148f89f5cd28f91ae4ee06b463b64625094b7ee` after independently reviewed
> Deleverage, Lootbox, and Teller changes. The discovered getter set, containing
> functions, and safety classifications are unchanged.
>
> **15 August 2026 PR #145 reconciliation:** PR #145 refreshes Deleverage's
> source identity and call-site rows on top of the merged AuctionHouse record.
> It preserves the inherited AuctionHouse, Lootbox, and Teller classifications
> without claiming to re-review those upstream deltas. The complete enforcement
> test passes. This package does not modify an immutable deployed vault,
> configure an asset, or activate a launch route.

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
using the position for value or borrowing. CreditEngine uses that distinction
explicitly: a backing-aware zero vault total plus a nominal user-balance bit
identifies custody quarantine without treating nominal balance as collateral.

Capability lookup remains a nominal included exception. Lootbox reward reads
are included but no longer classified as nominal: BasicVault suppresses
`getUserLootBoxShare` during a custody shortfall, while the already
backing-aware `getTotalAmountForVault` refreshes the vault's reward USD value to
zero. Neither getter supplies CreditEngine collateral value
([Lootbox source](../../../../contracts/core/Lootbox.vy#L893),
[CreditEngine source](../../../../contracts/core/CreditEngine.vy#L753)).

## Frozen machine inventory

Do not hand-edit line numbers or classifications without the corresponding
source review and test update.

<!-- BASIC_VAULT_CONSUMER_INVENTORY_BEGIN -->
```json
{
  "schema": 1,
  "baseline": "1e36c0c3dd168dbf292456eb5760b02d1f1e4a80",
  "sources": {
    "contracts/core/AuctionHouse.vy": "e7eb7b1b80ae0dce6a9df21ad7ec35cc3fd2248aac0bc3f02797d99b10e8409e",
    "contracts/core/CreditEngine.vy": "98001bce0f07992bdc51e4dede81fce5fbccbdaf9862c3ecef7694f6a2bd4f3f",
    "contracts/core/CreditRedeem.vy": "c8c7f5f8c3323fbe56d6307840a44ca1aa7ddb775438a9a1b31794af2a9b3017",
    "contracts/core/Deleverage.vy": "b035d9bb2ee20a4cab0575c468fe6a06e7e8e5a097f2ec9b00cc841e8bed44b1",
    "contracts/core/HumanResources.vy": "3a08959aea7ca59dda77b6aebcf1a1653239b4114a6b1390dc087e56ecf5c70d",
    "contracts/core/Lootbox.vy": "30a08f661271fe29a29ce52480d94dc8e5891ee1f038e09fe1dced72665d0e6f",
    "contracts/core/Teller.vy": "1ac2fd7b2c36fe454fd4fcdc0b422237f6a4936c5128bccada16524301a6b049",
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
      "id": "AH-439",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 439,
      "function": "_performLiquidationPhases",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Skips a deficient priority asset before any stability-pool swap or auction attempt.",
      "evidence_test": "test_quarantine_suppresses_new_liquidation_redemption_and_forced_deleverage"
    },
    {
      "id": "AH-521",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 521,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-535",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 535,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "Enumerates only candidates with a nonzero backing-aware amount before liquidation handling.",
      "evidence_test": "test_quarantine_suppresses_new_liquidation_redemption_and_forced_deleverage"
    },
    {
      "id": "AH-913",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 913,
      "function": "_canStartAuction",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Prevents creation of an auction whose collateral became deficient.",
      "evidence_test": "test_quarantine_suppresses_new_liquidation_redemption_and_forced_deleverage"
    },
    {
      "id": "AH-1265",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1265,
      "function": "withdrawTokensFromVault",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Clamps the Deleverage-requested withdrawal to the backing-aware user amount before safe conversion and mutation.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "AH-1293",
      "path": "contracts/core/AuctionHouse.vy",
      "line": 1293,
      "function": "_transferCollateral",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Soft-skips deficient collateral before internal transfer or external withdrawal settlement.",
      "evidence_test": "test_safe_nominal_volatile_deleverage_suppresses_quarantined_account"
    },
    {
      "id": "CE-730",
      "path": "contracts/core/CreditEngine.vy",
      "line": 730,
      "function": "_getUserBorrowTerms",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds collateral position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "CE-736",
      "path": "contracts/core/CreditEngine.vy",
      "line": 736,
      "function": "_getUserBorrowTerms",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "The returned amount feeds PriceDesk, collateral value, and maximum debt.",
      "evidence_test": "test_unsafe_backing_failures_keep_terms_with_zero_capacity"
    },
    {
      "id": "CE-753",
      "path": "contracts/core/CreditEngine.vy",
      "line": 753,
      "function": "_getUserBorrowTerms",
      "getter": "getTotalAmountForVault",
      "classification": "quarantine_status_backing_required",
      "reason": "Requires the whole vault to report zero usable custody before a nominal zero-amount position is classified as quarantined.",
      "evidence_test": "test_quarantine_detection_borrow_block_and_automatic_recovery"
    },
    {
      "id": "CE-754",
      "path": "contracts/core/CreditEngine.vy",
      "line": 754,
      "function": "_getUserBorrowTerms",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Confirms a nominal position remains after the backing-aware amount reaches zero; it is a quarantine discriminator and never supplies collateral value.",
      "evidence_test": "test_quarantine_detection_borrow_block_and_automatic_recovery"
    },
    {
      "id": "CE-1256",
      "path": "contracts/core/CreditEngine.vy",
      "line": 1256,
      "function": "getMaxWithdrawableForAsset",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds USD value and maximum-withdrawal borrowing constraints.",
      "evidence_test": "test_unsafe_backing_failures_keep_terms_with_zero_capacity"
    },
    {
      "id": "CR-191",
      "path": "contracts/core/CreditRedeem.vy",
      "line": 191,
      "function": "_redeemCollateral",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Soft-skips a deficient redemption entry before pricing or collateral movement.",
      "evidence_test": "test_credit_redeem_many_suppresses_all_entries_for_quarantined_user"
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
      "id": "DL-857",
      "path": "contracts/core/Deleverage.vy",
      "line": 857,
      "function": "_performDeleveragePhases",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Skips a stale requested position without deriving value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-939",
      "path": "contracts/core/Deleverage.vy",
      "line": 939,
      "function": "_iterateThruAssetsWithinVault",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage position enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-966",
      "path": "contracts/core/Deleverage.vy",
      "line": 966,
      "function": "_getBroadTraversalAsset",
      "getter": "getUserAssetAndAmountAtIndex",
      "classification": "value_backing_required",
      "reason": "Shared fail-soft availability and backing-aware amount probe for optional Stability Pool traversal and public deleverage sizing.",
      "evidence_test": "test_sc09_withdrawal_preflight_skips_unavailable_stab_cohort"
    },
    {
      "id": "DL-970",
      "path": "contracts/core/Deleverage.vy",
      "line": 970,
      "function": "_getBroadTraversalAsset",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers candidate assets; the selected path obtains value elsewhere.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1126",
      "path": "contracts/core/Deleverage.vy",
      "line": 1126,
      "function": "_getDeleverageInfo",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds deleverage information enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "DL-1141",
      "path": "contracts/core/Deleverage.vy",
      "line": 1141,
      "function": "_getDeleverageInfo",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "The amount feeds PriceDesk and maximum deleveragable USD.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "HR-391",
      "path": "contracts/core/HumanResources.vy",
      "line": 391,
      "function": "hasRipeBalance",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Checks whether a contributor has a RIPE governance-vault position; it neither values BasicVault collateral nor grants borrowing power.",
      "evidence_test": "test_hr_has_ripe_balance_no_balance"
    },
    {
      "id": "LB-301",
      "path": "contracts/core/Lootbox.vy",
      "line": 301,
      "function": "_claimLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds cleanup enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-305",
      "path": "contracts/core/Lootbox.vy",
      "line": 305,
      "function": "_claimLoot",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers nominal positions for reward cleanup, not collateral value.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-358",
      "path": "contracts/core/Lootbox.vy",
      "line": 358,
      "function": "getClaimableLoot",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds claimable-reward enumeration only.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-360",
      "path": "contracts/core/Lootbox.vy",
      "line": 360,
      "function": "getClaimableLoot",
      "getter": "userAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Retrieves an asset identity for reward accounting, not an amount.",
      "evidence_test": "test_basic_vault_consumer_inventory_enforces_amount_policy"
    },
    {
      "id": "LB-439",
      "path": "contracts/core/Lootbox.vy",
      "line": 439,
      "function": "_getDepositLootData",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Distinguishes a live reward position from an exited one when deciding whether a zero-paying category may resolve terminally; it does not value collateral.",
      "evidence_test": "test_exited_funded_dust_gets_one_wei_and_inactive_category_exhausts"
    },
    {
      "id": "LB-893",
      "path": "contracts/core/Lootbox.vy",
      "line": 893,
      "function": "_getLatestDepositPoints",
      "getter": "getUserLootBoxShare",
      "classification": "reward_accounting_backing_aware",
      "reason": "Reads the current reward-eligible share; BasicVault returns zero during custody shortfall and restores it with custody without mutating nominal balances.",
      "evidence_test": "test_zero_ltv_shortfall_suppresses_user_rewards_without_debt_quarantine"
    },
    {
      "id": "LB-913",
      "path": "contracts/core/Lootbox.vy",
      "line": 913,
      "function": "_refreshAssetUsdValue",
      "getter": "getTotalAmountForVault",
      "classification": "reward_accounting_backing_aware",
      "reason": "Refreshes vault-wide reward USD value from a backing-aware total, which becomes zero during custody shortfall.",
      "evidence_test": "test_shortfall_checkpoints_each_normalized_user_share_and_leaves_healthy_asset_untouched"
    },
    {
      "id": "TL-410",
      "path": "contracts/core/Teller.vy",
      "line": 410,
      "function": "_withdraw",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Enforces the remaining minimum deposit balance after withdrawal.",
      "evidence_test": "test_deficit_zeroes_usable_views_but_surplus_preserves_only_nominal"
    },
    {
      "id": "VM-154",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 154,
      "function": "migrateVaultPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds ordinary-vault source position enumeration only.",
      "evidence_test": "test_normal_migration_rejects_more_than_twenty_source_asset_slots"
    },
    {
      "id": "VM-162",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 162,
      "function": "migrateVaultPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live source assets; exact transferred value is proven by Teller and token-balance deltas.",
      "evidence_test": "test_all_user_assets_migrate_with_one_housekeeping_call"
    },
    {
      "id": "VM-186",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 186,
      "function": "migrateVaultPositions",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Verifies that the exact ordinary-vault withdrawal removed the source position; it does not derive value.",
      "evidence_test": "test_all_user_assets_migrate_with_one_housekeeping_call"
    },
    {
      "id": "VM-253",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 253,
      "function": "migrateRipeGovPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds governance-vault source position enumeration only.",
      "evidence_test": "test_governance_migration_rejects_more_than_five_source_asset_slots"
    },
    {
      "id": "VM-261",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 261,
      "function": "migrateRipeGovPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live governance assets before the backing-aware migration snapshot and exact receipt checks.",
      "evidence_test": "test_one_user_migrates_all_governance_assets_with_one_housekeeping_call"
    },
    {
      "id": "VM-348",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 348,
      "function": "migrateLegacyRipeGovPositions",
      "getter": "numUserAssets",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Bounds legacy governance source position enumeration only.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-356",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 356,
      "function": "migrateLegacyRipeGovPositions",
      "getter": "getUserAssetAtIndexAndHasBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Discovers live legacy assets before their backing-aware snapshots are captured.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-472",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 472,
      "function": "_getPreMigrationData",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Captures the source amount used to construct and verify the governance migration payload.",
      "evidence_test": "test_base_legacy_route_preserves_position_then_normal_claim_cleans_source"
    },
    {
      "id": "VM-523",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 523,
      "function": "_verifyRipeGovExport",
      "getter": "getTotalAmountForUser",
      "classification": "value_backing_required",
      "reason": "Requires the backing-aware source amount to be zero after the exact governance-vault export.",
      "evidence_test": "test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points"
    },
    {
      "id": "VM-524",
      "path": "contracts/core/VaultMigrator.vy",
      "line": 524,
      "function": "_verifyRipeGovExport",
      "getter": "doesUserHaveBalance",
      "classification": "position_discovery_nominal_allowed",
      "reason": "Verifies removal of the exported source position after the amount and token deltas have been checked.",
      "evidence_test": "test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points"
    },
    {
      "id": "VM-549",
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
