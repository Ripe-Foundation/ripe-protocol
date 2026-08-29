# PR #223 cutover

211 already ran. This flip is only the promo / Golf generation.
Do not rewrite or re-run `pr-211-cutover-sequence.md`.

## What changes

Replace the 211-generation boards that 223 actually changed, and register Golf.

| Contract | Registry | Slot | Notes |
|---|---|---|---|
| SwitchboardGolf | Switchboard | next id (tests use 7) | **New.** Register before or in the same Safe tx as the Bravo replace. |
| SwitchboardFoxtrot | Switchboard | 6 | Clock arm / GREEN snapshot |
| SwitchboardCharlie | Switchboard | 3 | Armed empty-checkpoint guard; `updateMany` rejects `address(0)` |
| MissionControl | RipeHq | 5 | Clock storage. Snapshot Defaults off the **current** MC (clocks are 0 if no campaign is armed). |
| Lootbox | RipeHq | 16 | Accrual floor. **After** MC. |
| SwitchboardBravo | Switchboard | 2 | Thin Bravo. No `addAsset`. After or with Golf. |

**Do not replace Ledger.** Do not replace Alpha, AuctionHouse, Deleverage, or CreditRedeem unless a later review says they changed.

## Hard restrictions

- Do not replace MissionControl while any `accrualStartBlock` is nonzero unless a purpose-built migration copies the clocks. Defaults and `prepare_defaults` do not carry clocks. A silent MC replace zeros armed/live clocks and undoes “activate never ends.”
- Promo assets must `golf.addAsset` with **one** vault so MC auto-selects `rewardVaultId`. Charlie `setRewardVaultId` checkpoints the new row and makes it non-virgin; Foxtrot then cannot arm.
- Opening deposits is the commit. `lastUpdate == 0` is required to arm or abort.
- MC before Lootbox. Golf before or with Bravo.

## Operator facts

- Live RH rows cannot arm.
- Foxtrot emits `AccrualClockArmedSet`. Bravo activation is `AssetDepositParamsSet` plus the on-chain clock.
- After this flip, NVDA-style `addAsset` goes through Golf. See `migrations/robinhood-mainnet/2026082800_RipeNvdaPool.py`.

Re-read HQ / Switchboard addresses at execution. Do not copy 211 slot addresses from the old cutover.
