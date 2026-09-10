# Uniswap V3 TWAP operator notes

The full operator handoff (status, footguns, gate checklist, per-asset procedures,
monitoring and incident playbook) is [uniswap-v3-twap-operator-handoff.md](uniswap-v3-twap-operator-handoff.md).

Owner decisions D1–D20, 2026-09-09. These notes specify proposal checks and scale
recovery semantics. PR #229 does not deploy, register or activate any feed.
FinishSetup inclusion and token-scale first-sync hardening are separate work.

Before any proposal, record the candidate token's proxy/upgrade controls and
whether decimals can change. Confirm the canonical pool and ordered pair,
resolved window/age, initialized history and cardinality >= window+1. Review
all potentially authoritative quote sources, including fallbacks: each must
never call back into PriceDesk, and V3 must be after all of them. Repeat this
review after every registry or MissionControl priority change. Re-run the cold
T11/T22 qualification against the actual selected registry and quote route before
any proposal. The fixed-WETH laboratory alone does not qualify a production registry.

Run `scripts/twap_pool_depth.py RPC POOL ASSET --source SOURCE` at a printed,
pinned block. With no source, supply window/age/ratio explicitly or accept
3600/1800/5000. The script resolves the source's RipeHq and current desk;
without a source it uses the chain's current-manifest RipeHq for chain 4663 or
8453, then reads desk ID 7 at the pin. `--price-desk` supports other explicit
laboratories/chains; an override with a source must equal its canonical desk.
Review the printed desk identity. An RPC failure, unavailable quote or changed
header produces no verified depth estimate. Historical depth or missing TWAP
history must not be substituted with constant in-range liquidity.

**Governance minimum smaller-direction 2% depth (USD): unset.** Governance must
set and record a value for the candidate in its proposal record before a feed
proposal. Do not propose when the helper's smaller-direction 2% depth is below
that value, or while the value remains unset. This PR selects no financial
threshold, LTV, cap or borrowing policy. Depth is fee-inclusive market depth
at the pinned block, not the cost to manipulate a TWAP for the window.

**Confirmation transaction:** confirm on its own, or with only a preceding
`PriceDesk.syncTokenScale(asset)` for that same asset. Do not put quote-price
reads, route preflights, other feeds, or other calls in that transaction.
Perform those checks in a separate prior transaction: they can warm quote
storage and let the admission ceiling pass a route that later fails cold.
Both standalone and batched confirmation still require cold qualification.
Estimate the complete intended transaction and use a generous gas buffer;
a tight transaction limit can starve the inner 250,000-gas call under EIP-150
and revert with `price source not executable` even for a valid route.

Do not leave a newly admitted asset's cached scale at zero in production.
Prefer `[syncTokenScale(asset), confirmNewPriceFeed(asset)]`; if confirmed
separately, sync immediately before using any USD/asset conversion. An unset
scale permits a USD18 price read, but `getUsdValue` and `getAssetAmount` return
zero, or revert with `missing token scale` when their raising flag is true.
Verify the exact cached scale after syncing.

For a priced-asset scale mismatch that arises after a valid proposal, wait for
the proposal timelock and batch `[PriceDesk.syncTokenScale(asset), confirm]`.
A transient confirmation failure reverts both calls and preserves the proposal.
An identity-drift cancellation returns false and leaves the sync in place,
which can darken an existing feed until governance re-proposes and confirms.

When the mismatch is already present before proposal, use
`propose update -> wait timelock -> batch [syncTokenScale, confirmPriceFeedUpdate]`.
Proposal intentionally skips the scale guard. The active feed keeps pricing
while its old decimal snapshot still matches the old cached scale, until the
sync. A successful confirmation installs the new snapshot; an identity cancel
after the sync can leave the old feed dark. Disable and re-add does not bypass
the confirmation scale check.

**Identity cancellation precedes the timelock check.** Calling `confirm*`
before unlock while token or pool identity has drifted cancels the proposal
and consumes it; it does not leave a retryable timelock failure. Check current
identity before submitting, including for tokens with upgradeable metadata.

After any batch, verify the exact `NewUniV3FeedAdded` or `UniV3FeedUpdated` event
for the asset, pool, quote and resolved policy, then verify pending state,
cached scale and cold price. Safe MultiSend does not treat a returned false as
failure. A successful outer transaction therefore does not guarantee that
both sync and confirmation succeeded; a cancel event identifies partial
success. Transient reverts roll back the whole atomic batch.
