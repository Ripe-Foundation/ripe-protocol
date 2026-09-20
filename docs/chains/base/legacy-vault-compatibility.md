# Base legacy-vault compatibility release notes

This change lets new departments read retained Stability Pool 1 through VaultBook while preserving direct, authorized settlement calls. Retained RipeGov 2 also remains usable through the new Teller and Lootbox. Ordinary tests compile both retained vaults from their authenticated historical sources; their provenance is recorded in `tests/fixtures/legacy_pool/provenance.json`.

## Pricing dependency of withdrawal preparation

`Deleverage.getDeleverageInfo` now includes Pool-1 positions using the legacy pool's full net asset value. With positive spendable stabilization-token custody, that getter values every recorded claim in the selected cohort using strict quotes. An unavailable claim price can therefore revert the view and `deleverageForWithdrawal` preparation, even when that claim is only dust. Paused pools and cohorts with no spendable custody are skipped before valuation.

The repository's contracts do not call either external entry point; external integrations that use them for withdrawal preparation must account for this dependency. The same strict legacy valuation also remains relevant to ordinary deposits, withdrawals and claims. Liquidation readiness intentionally examines only the selected payment path and does not certify unrelated claim prices or backing. A pool can be ready for a liquidation swap while its NAV-dependent user flows cannot complete.

The saved Base readback at block **51,532,106** records eleven non-GREEN claims in the LP cohort. Both active and staged PriceDesk observations record unit prices of **1 USD wei** for VVV (`0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf`, 18 decimals) and mcbETH (`0x3bf93770f2d4a794c3d9ebefbaebae2a8f09a5e5`, 8 decimals). Each has one raw claim unit. Their unrounded dollar values are zero; PriceDesk's positive-price floor gives each a one-USD-wei quote. The evidence establishes those values, not the intent behind setting them.

The committed `DefaultsBaseLive.vy` snapshot at block **51,479,022** does not include mcbETH. Replaying only MissionControl's asset list is therefore insufficient to preserve the LP cohort's pricing dependencies. Before activation, the release owner must verify usable, nonzero quote paths for **all retained claim assets**, including VVV and mcbETH, in the selected PriceDesk. These notes do not prescribe retaining economically incorrect prices. Changing prices or resolving residual claims remains a release decision. No new live readback or oracle configuration was performed for this follow-up.

## Constructor validation boundary

VaultBook validates Base chain identity, HQ identity and the non-valuing legacy getter shapes. It does not invoke `getTotalAmountForUser` during construction. In the historical implementation, a zero user still triggers cohort valuation; a zero asset fails its ERC20 balance read, and an existing cohort can fail on an unavailable claim price. Adding that call as a structural requirement would make deployment depend on current oracle health and reject otherwise authentic pools. Tests cover empty, populated, paused and unpriceable cases. The full historical ABI/runtime must be authenticated before choosing the immutable legacy binding; constructor probes alone do not authenticate arbitrary supplied code.

## Rehearsal and activation boundary

`scripts/base_full_update_fork.py` compiles fresh candidates through its deployment adapter. The adapter now appends retained Pool 1 to both historical VaultBook constructor calls, including the populated replacement. Local tests deploy the resulting contracts and exercise all three compatibility helpers. Historical migration files and deployment records retain their original arguments.

An already-staged on-chain VaultBook does not acquire these helpers from a source update. A compatible candidate and an updated production deployment step are still required before activating departments that call them. This task changed only the fork adapter and ran local tests; it did not restage contracts, execute a network fork campaign, or authorize activation.

## Regression placement

The composed tests live in `tests/core/auctionHouse/test_base_legacy_vault_compat.py`, which belongs to the existing AuctionHouse CI shard. The registry tests remain in `tests/registries/test_vault_book_legacy_compat.py`. No workflow change is needed. The focused contract selection includes both; the shard-coverage check guards future placement.
