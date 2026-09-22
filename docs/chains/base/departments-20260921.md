# Base departments — deployment only, current vaults retained

These migrations do not activate departments, propose HQ changes, deploy vaults,
or transfer any funds. Existing Ledger, tokens, CCIP pools, MC, Foxtrot, and the
separately staged price-source wave are not redeployed here.

| Migration | Deployments and setup |
|---|---|
| `2026092102` | VaultBook, populated with live vaults 1–5 and their descriptions; current SP bound for legacy compatibility |
| `2026092103` | AuctionHouse, AuctionHouseNFT, Boardroom, BondBooster, BondRoom, CreditEngine, Endaoment, HumanResources, Lootbox, Teller, Deleverage, CreditRedeem, TellerUtils, EndaomentFunds |
| `2026092104` | Switchboard and Alpha/Bravo/Charlie/Delta/Echo/Golf; retain the already initialized Foxtrot at ID 6, add Golf at ID 7 |
| `2026092105` | PSM with live USDC constructor policy; paused VaultMigrator, reserve engine and reserve vesting |

New registry and action timelocks stay **zero**. Neither setup timelock setter is
called. Constructor minimum/maximum bounds are retained for future configuration;
existing live delays, including the HQ activation delay, are unchanged. Temporary
deployer governance exists only to populate the new registries and is relinquished.

Vault IDs remain 1=StabilityPool, 2=RipeGov, 3=SimpleERC20, 4=RebaseERC20,
5=Underscore. No balances, locks, vault shares or debt are migrated. The paused
VaultMigrator is merely prepared for a later wave and is bound to the current
governance vault. It does not run any migration.

## Run order

Finish the existing `2026092101` price-source migration first. Its live in-progress
journal must not be deleted or overwritten. Start with VaultBook only:

```sh
python -m scripts.migrate --profile base-mainnet \
  --start-timestamp 2026092102 --single --fork
```

After reviewing the fork, omit `--fork` to deploy live. Continue with `2026092103`,
then `2026092104`, then `2026092105`, using `--single` for each. New labels use
`BaseDepartments20260921`; the standard journal handles an unchanged script's
interrupted deployment. Deployment completion is not activation approval.

## Required before activation

- CreditEngine's constructor starts buybacks at **0%**. Set the intended **80%**
  through governance during cutover and reconcile its other mutable settings.
  These setters target the active department, so deployment alone cannot do this.
- PSM starts with minting and redemption disabled. Before allowlisted redemption
  testing, set `canRedeem=True` and `shouldEnforceRedeemAllowlist=True`, populate
  the allowlist, and reconcile the other live policy. The constructor only copies
  fees, limits, interval, USDC and yield destination—not full mutable state.
- The USDC reserve engine has explicitly dormant constructor placeholders:
  1 USDC epoch/minimum payment, payout rates of 1, and no vesting bonus. It is
  paused/unfunded, not a proposed sale. Configure actual launch economics before
  enabling it. Reserve vesting and VaultMigrator also remain paused.
- Future HQ additions must be **VaultMigrator=25, reserve engine=26, vesting=27**.
  PSM replaces slot 22. CCIP slots 23–24 are untouched.
- New Deleverage fields absent from the legacy contract use a 0.001 GREEN payoff
  buffer and 1% overage; dust forgiveness is disabled. Existing four constructor
  policy values are read live. Review these additions before activation.
- Teller is staged paused. VaultBook/Switchboard compatibility and any departments
  depending on them must be activated in a reviewed sequence.
- Inventory and migrate all PSM/EndaomentFunds assets before retiring old custody.
  Review department-local state (auctions/NFTs, bonds/boosters, HR, reward accounting,
  pending switchboard actions and settings); these deployment files do not copy it.
- Keep the legacy wrapped-OETH source in PriceDesk ID 7: current SP baskets still
  need mcbETH/VVV dust prices. Price freshness and SP/liquidation/deleverage checks
  are required at activation, not inferred from a successful deployment.

This is a staging plan. No mainnet activation or fund migration is performed.

## Fork result

All four staging migrations passed on a Base fork at block **51,629,762**:
26 deployments, 52 deployment/setup transactions, 85,119,853 aggregate execution
gas. The standard runner used temporary copies of only these four migration
files and the deployment history; the live in-progress price-source journal was
not replayed or modified. VaultBook retains all five vault identities and passes
its legacy SP interface probe. New registry/controller/HR delays remain zero,
Foxtrot is reused, and active HQ/registry addresses remain unchanged.

This verifies deployment and setup, not HQ activation, treasury migration or
end-to-end liquidation/deleverage after cutover.
