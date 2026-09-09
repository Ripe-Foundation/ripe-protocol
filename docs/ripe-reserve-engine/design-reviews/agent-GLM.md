# Instant Bond Lane design review — GLM

- Date: 2026-08-22
- Branch: instant-bond-lane
- Agent: GLM
- Pin confirmed: d136a262f560fe628d7c3f7b667b0220871cb951
- Web access: yes

## 1. Commit and tree confirmation

**Confirmed.** Commit `d136a262f560fe628d7c3f7b667b0220871cb951`, tree `2cdcdd6e8f760995f57b05b529100cbcec6d4e5a`. All reads were via `git show d136a262:<path>`. No working-tree writes were made.

---

## 2. Summary and one-line verdicts

**What this is, in product language.** A buyer pays dollars (a configured ERC-20 treated as dollar-denominated), payment goes to Endaoment Funds, and the lane mints RIPE to the buyer — either unlocked to their wallet or deposited into the live core RipeGov vault with a lock the buyer chose. One price holds for the entire epoch. After the epoch ends, the *next* buy silently computes a new price from how full the last epoch was and when the payments arrived, then buys at that new price in the same transaction. No keeper, no auction within an epoch, no partial fills, no vesting schedule.

**My assumed top objective, stated once:** controlled distribution of RIPE at a governed, demand-responsive pace — with a hard cap on total issuance, a floor under the rate when demand is weak, and a ceiling when it's strong. I rank: **distribution at a protected price > hard issuance cap > low operator touch > governance lock > price discovery > reserves.** The design optimizes for exactly this ranking. I'd only flip "low operator touch" above "hard issuance cap" if the lane were meant to run unattended for months — and the override's persistence-through-pause behavior shows that it's not.

**One-line verdicts:**

- **Support this product concept?** **Yes.** A bounded, oracle-free, demand-responsive primary sale with hard caps is the right shape for distributing a governance token without a liquid market.
- **Picked shape:** Current lane as-is, with override expiry added and timing-weighted adjustment flagged as first simplification candidate.
- **Top 3 changes:** (1) Add override expiry, (2) Rename away from "bond," (3) Simplify or remove the timing-weighted high-utilization signal.
- **Vesting:** Don't add. The Olympus V1→V2 migration shows vesting adds complexity without distribution benefit; selling-pressure management belongs in RipeGov, not the lane.
- **Override:** Replace the blunt one-shot with a one-shot that carries an optional expiry epoch. The recorded reason for skipping expiry ("adds a new state machine") is wrong — it's one variable and one check.
- **Keep the name "Instant Bond"?** **No.** It implies debt, maturity, and redemption that don't exist. Rename to something like "Primary Sale Lane" or "RIPE Direct Mint."
- **Epoch-fixed + lazy rollover:** **Keep.** The no-keeper design is elegant and the "first buyer gets the adjusted rate" leak is bounded by the per-epoch cap.
- **Biggest disagreement with a recorded decision:** The override has no expiry, target epoch, or maximum lead, and the recorded reason is that adding one would "add a new signal, authority path, or state machine." An expiry counter is a single `uint256` and a single `if` at rollover. The real risk — a forgotten override applying weeks later after an unplanned pause — is operational, not architectural, and the mechanism should fail safe against it.

---

## 3. Research

### Lineage attribution: Olympus → Bond Protocol

**Olympus V1 (2021)** introduced reserve bonds: the protocol sold OHM at a discount for reserve assets (DAI, FRAX, LP tokens). The discount was driven by a **debt ratio** (outstanding bond debt / OHM supply) scaled by a **Bond Control Variable (BCV)** — a governance-tunable "speed" parameter. As more bonds were purchased, the debt ratio rose, the premium increased, and the discount shrank. Vests were linear (initially 5 days). There was no per-epoch cap — the price was continuous within a market.

**Olympus V2 (late 2021)** replaced linear vesting with **fixed-term** and **fixed-expiry** markets and auto-staking: bond payouts were staked on behalf of the buyer, and the buyer waited until the term ended to redeem. Multiple vesting terms were offered simultaneously. The key lesson from V1→V2: linear vesting added gas cost and complexity without meaningful selling-pressure dampening, because buyers could claim incrementally anyway.

**Bond Protocol (2022)** generalized Olympus V2's mechanism into a permissionless platform for any project to sell vested governance tokens. Its core innovation was the **Sequential Dutch Auction (SDA)**: split a bond program's capacity into a sequence of Dutch auctions, each starting at a price and decaying (via the BCV) until clearing. Bids were "live" — a buyer instantly acquired vested tokens at the current discount. This is the direct descendant of Olympus V1's debt-ratio-driven premium, formalized as a sequence of discrete Dutch auctions with a tunable decay rate.

**Attribution (labeled):** The sequential-Dutch-auction lineage is Olympus V1 (debt-ratio-driven continuous discount, 2021) → Olympus V2 (fixed-term/fixed-expiry markets with auto-staking, late 2021) → Bond Protocol SDA (capacity split into a sequence of Dutch auctions with BCV-controlled decay, 2022). Paradigm's GDA/VRGDA (2022) is a *parallel* continuous formulation of the same insight — price should respond to sales velocity vs a target — but expressed as a continuous decay function rather than discrete auctions.

The Instant Bond Lane is **not** in this lineage. It has no within-epoch price decay. Its price is fixed for the entire epoch and adjusts only at epoch boundaries. It is a different family: a step-function feedback controller (utilization → next-epoch rate adjustment), not a Dutch auction (price decays until clearing).

### Research table

| Mechanism | Bucket | Pricing | Delivery / vest / lock | Caps | Operator lever | Durable? evidence | Implication |
|-----------|--------|---------|------------------------|------|----------------|-------------------|-------------|
| Olympus V1 reserve bonds (2021) | Issuer sells governance token for reserves | Debt-ratio × BCV; discount shrinks as debt rises; continuous within market | Linear vest, 5 days | Per-market capacity | BCV adjustment | **No** — deprecated, replaced by V2. Observed: the debt-ratio premium was gameable and the 5-day vest was too short to matter. | Linear vesting adds complexity without distribution benefit. The Lane correctly avoids it. |
| Olympus V2 BondDepository (late 2021) | Same | Same debt-ratio model, but fixed-term and fixed-expiry markets | Auto-stake; no linear vesting; wait until term end | Per-market | BCV, market open/close | **Partially** — V2 exists but bonding is less central to Olympus. Observed: auto-staking + fixed term was a deliberate simplification. | Fixed-term vesting is simpler than linear but still doesn't prevent sell pressure if the token is liquid. |
| Bond Protocol SDA (2022) | Same (generalized for any token) | Sequential Dutch Auction: price starts high, decays via BCV until clearing | Vested token (fixed term or fixed expiry); bids are live | Per-auction capacity | BCV, auction duration | **Yes** — still operational. Observed: the SDA is effective for price discovery but requires active market management. | Direct Olympus→Bond Protocol lineage. The Lane is a different family — step-function at epoch boundaries, not within-epoch decay. |
| Paradigm GDA/VRGDA (2022) | Same (sell tokens without liquid market) | Continuous: price = f(target_rate, actual_sales, time); price rises when below target, falls when above | Immediate | Target sale rate | Target rate, decay function | **Yes** — used in NFT and token launches. Observed: effective for sales but sensitive to parameterization. | The continuous analog of the Lane's discrete controller. The Lane trades precision for testability and epoch-boundary clarity. |
| Frax FXB (2023+) | Issuer sells discounted claim on own stablecoin | Auction at discount to face value; 1 FXB → 1 FRAX at maturity | Zero-coupon; redeem at maturity for FRAX | Per-auction | Auction parameters, maturity | **Yes** — still operational. Observed: successful for FRAX yield management. | **Contrast, not template.** FXB is a stablecoin-denominated debt instrument, not a governance token sale. The Lane sells RIPE (governance) for reserves, not a stablecoin claim. |
| Olympus inverse bonds (2022) | Issuer spends reserves to buy back own token | Protocol sells reserve assets (USDC) for OHM | Instant | Per-market | Market open/close, price | **Yes** — still used. Observed: effective for absorbing sell pressure. | **Contrast — opposite direction.** The Lane sells RIPE for reserves; inverse bonds sell reserves for RIPE. Not a template. |
| ESPP (ordinary finance) | Issuer sells equity to employees at discount | Fixed discount (5–15%) to market; lookback uses lower of enrollment-date or purchase-date price | Immediate (or short hold); some plans require 3–12 month hold | $25K/year IRS limit; per-plan | Discount rate, offering period, lookback | **Yes** — 50% of S&P 500. Observed: high participation with 15% + lookback. | **Closest ordinary-finance analog.** The Lane is an ESPP for the open market: periodic, fixed-price, capped. The epoch-snapshotted rate is the lookback equivalent. |
| DRIP (ordinary finance) | Issuer sells equity to existing shareholders at discount | Small discount (0–5%) to market | Immediate | None typically | Discount rate | **Yes** — widely used. Observed: simple but doesn't control total issuance. | DRIP is simpler (no period, no cap) but less controlled. The Lane adds cap and epoch structure that DRIP lacks — and that's the right call. |
| I Bonds (ordinary finance) | Issuer sells savings product with posted rate and hold | Fixed rate + inflation rate; adjusted semiannually; composite rate = fixed + (2 × semiannual inflation) + (fixed × inflation) | 12-month lock; 3-month penalty before 5 years; 30-year maturity | $10K/year per SSN | Fixed rate (set semiannually by Treasury) | **Yes** — Treasury program since 1998. Observed: demand tracks inflation; caps prevent large-scale arbitrage. | **Closest ordinary-finance analog to the epoch-fixed price + hold pattern.** The semiannual rate adjustment is the I-Bond analog of the Lane's per-epoch adjustment. The $10K cap is the I-Bond analog of the Lane's per-epoch payment cap. |
| Rights issue (ordinary finance) | Issuer sells equity to existing shareholders, pro-rata | Discount (15–30%) to market | Rights are tradable; exercise within 16–30 days | Pro-rata to holdings | Discount, subscription period | **Yes** — widely used in capital raises. Observed: effective for raising capital without diluting existing holders who exercise. | Rights issues are pro-rata; the Lane is permissionless. The tradable right is a feature the Lane lacks — a transferable claim would be the analog, but it adds a new token and transfer surface. |
| Aave GHO stkAAVE discount (2023) | Governance-token utility (not a sale) | Discount on GHO borrow rate, per-stkAAVE up to a cap | n/a (borrow rate, not a sale) | Per-stkAAVE GHO cap | Discount rate, per-token cap | **Yes** — active. Observed: gives stkAAVE a real economic reason to hold. | The Lane's dormant lock bonus is a similar utility mechanism — lock RIPE, get bonus RIPE. Both are ways to give governance token holders an economic benefit. The dormancy is correct given RipeGov blending. |

### Synthesis: which precedents changed a recommendation

**Olympus V1→V2 vesting migration → don't add vesting.** Olympus moved from linear vesting to fixed-term because linear vesting added gas cost and complexity without meaningful selling-pressure dampening — buyers could claim incrementally and the 5-day window was too short to matter. The lesson: vesting is the wrong tool for a distribution mechanism. Selling pressure belongs in the lock product (RipeGov), not the sale product. This directly shaped my "don't add vesting" recommendation.

**GDA/VRGDA continuous pricing → keep epoch-fixed.** The GDA is the continuous analog of the Lane's discrete controller, and it's effective — but it's harder to reason about, harder to test, and more sensitive to parameterization. The Lane's epoch-fixed design trades one-epoch price staleness for testability and clear boundary semantics. The GDA precedent confirmed that the continuous alternative is viable but not obviously better for a distribution-focused lane.

**Bond Protocol SDA lineage → the Lane is not a Dutch auction, and shouldn't be compared to one.** The Olympus→Bond Protocol lineage is about within-auction price decay (a Dutch auction where price falls until someone buys). The Lane has no within-epoch price movement — it's a step-function feedback controller. This matters because it means the Lane's "lag" (selling at a stale price for an entire epoch) is inherent to its design class, not a bug that a Dutch auction would fix. The Dutch auction alternative would add within-epoch price decay but would also add front-running susceptibility (as Bond Protocol explicitly acknowledged) and active market management.

**ESPP lookback → epoch-snapshotted rate is well-precedented.** The ESPP's lookback feature (use the lower of enrollment-date or purchase-date price) is the ordinary-finance analog of the Lane's epoch-snapshotted rate: a price is fixed at the start of a period and held until the next adjustment. This confirmed that periodic fixed-price sales with later adjustment are a well-established pattern in ordinary finance, not a DeFi novelty.

**I Bonds → periodic rate adjustment with a hold is ordinary finance.** I Bonds adjust their composite rate semiannually and have a 12-month lock — the closest ordinary-finance analog to the Lane's per-epoch rate adjustment with optional RipeGov lock. This confirmed that "posted rate that adjusts periodically + hold" is a standard savings-product pattern, which is the Lane's closest ordinary-finance cousin.

**Rejected obvious analogy: "this is like Olympus bonding."** It's not. Olympus bonding was a continuous-price, debt-ratio-driven mechanism with within-market discount decay. The Lane is a fixed-price-per-epoch, utilization-driven controller with no within-epoch movement. The only shared feature is "sell governance token for reserves at a discount." The mechanism families are different, and the Lane's design is simpler and more testable as a result. Calling it a "bond" inherits the Olympus naming confusion without inheriting the mechanism.

---

## 4. Three shapes, then pick one

### Shape 1: Current lane as-is

**Buyer experience:** Preview a quote at a fixed rate for the current epoch. Buy at that rate — full fill or revert. Get RIPE unlocked to your wallet, or deposited into RipeGov with your chosen lock duration. Next epoch's rate adjusts based on how full this epoch was and when you bought. If another buyer consumes capacity first, your transaction reverts and you re-preview and retry.

**Issuance discipline:** Hard per-epoch payment cap, hard cumulative mint budget, all-in rate ceiling, `MIN_BASE_RATE` floor, utilization-driven step adjustment, bounded decay, one-shot override. Four-branch controller (high/low/dead-band/empty) with amount-weighted timing on the high branch.

**Operator load:** Timelocked full-config replacement through Foxtrot. Timelocked override installation and cancellation. Immediate `canBuyNow`, start/stop, payment-token swap (while stopped), `setCumulativeMinted`. External depeg monitoring. No keeper.

**Complexity:** High. 17-field config struct, 4-branch controller with timing-weighted earliness, one-shot override with persistence-through-pause, 13 Lane events, 10 Foxtrot events. The timing-weighted adjustment is the most complex single feature and provides a strategically selectable signal.

### Shape 2: A simpler lane

**Buyer experience:** Identical — preview, buy at fixed rate, get RIPE. The only visible difference is that the rate adjustment between epochs is simpler (flat step, no timing weighting).

**Issuance discipline:** Same hard caps (payment cap, mint budget, rate ceiling, floor). Simpler controller: high utilization → flat `upBps` step, low → flat `downBps` step, empty → `decayBps` step. No timing-weighted earliness. Override with optional expiry epoch — installed via timelock, consumed at next rollover, silently clears if not consumed by the expiry epoch.

**Operator load:** Lower. No timing parameters to calibrate (`minUpBps`/`maxUpBps` collapse to one `upBps`; same for down). Override has a natural retirement path, reducing the "forgotten override" operational risk. Fewer config fields (13 vs 17 if timing ranges are collapsed to single values).

**Complexity:** Moderate. 3-branch controller (high/low/empty), no timing math, override with one additional state variable (expiry epoch). Roughly 20–30% less controller code. The anti-ratchet bounds simplify to two inequalities instead of four.

### Shape 3: VRGDA/GDA-style continuous price

**Buyer experience:** Price changes continuously — every block, the rate decays slightly if no one buys, and jumps when someone does. Preview shows the current instantaneous rate. Buy at that rate. No epoch boundaries, no rollover events, no "first buyer gets the new rate" cliff.

**Issuance discipline:** Continuous price function: `price(t) = base * decay(t) * boost(recent_sales)`. Hard mint budget and rate ceiling still apply. No per-epoch cap — the rate itself limits demand. No timing signal — all sales are at the current continuous price.

**Operator load:** Lower in one dimension (no epoch management, no rollover, no `expectedEpoch` binding). Higher in another (parameterization is more sensitive — a wrong decay constant can make the lane sell too fast or stall indefinitely).

**Complexity:** Moderate in code (one formula, no epoch state) but higher in reasoning. The continuous price surface is harder to test exhaustively — stateful fuzzing would need to handle continuous time rather than discrete epochs. The integer-arithmetic edge cases (division, rounding, overflow) are different and less naturally bounded.

### Pick: Shape 1 (current lane), with override expiry added

The epoch-fixed design is the right shape for a distribution-focused lane. It's simpler to reason about than a continuous price, the lazy rollover eliminates the keeper problem, and the per-epoch cap bounds the "stale price" leak to one epoch's worth of capacity. The timing-weighted adjustment adds complexity for marginal value but doesn't create a safety problem (the `minUpBps` floor is the safety boundary). The override is the one piece I'd change — adding an expiry makes it fail safe against the most likely operational failure mode.

---

## 5. Decision register for the picked shape (current lane + override expiry)

| Keep / change / remove / experiment | Decision | Why | Buyer / operator effect | Surface and timing | Priority |
|--------------------------------------|----------|-----|-------------------------|--------------------|----------|
| **Change** | Add an optional expiry epoch to the override | The recorded reason for skipping expiry is that it "adds a new signal, authority path, or state machine" (§6.7, deferred mechanisms). This is wrong: an expiry is one `uint256` and one `if` at rollover. The real risk is operational — a forgotten override applying weeks later after an unplanned Department pause — and the mechanism should fail safe. | Operator: if an override is installed and not consumed by its expiry epoch, it silently clears and the ordinary controller resumes. Buyer: no visible change; the rate they see at rollover is either the override (if not expired) or the controller's. | `InstantBondLane.vy`: add `overrideExpiryEpoch: public(uint256)`, check at `_getEpochSnapshot` rollover. `SwitchboardFoxtrot.vy`: add expiry to the `setInstantBondRateOverride` action. Default: `0` = no expiry (backward compatible). | **1** — highest |
| **Change** | Rename from "Instant Bond Lane" to a non-bond name (e.g., "Primary Sale Lane" or "RIPE Direct Mint") | The name "bond" implies debt, maturity, face value, and redemption — none of which exist. The Olympus naming precedent is widely criticized for the same confusion. The FAQ says "it is a direct primary-market RIPE purchase," which is exactly what the name should say. | Buyer: clearer expectations — no vesting, no maturity, no claim on future redemption. Operator: less confusion in support and monitoring. | All doc references, contract names, event names, RipeHq registry id. Contract rename is a deploy-time decision. | **2** |
| **Change** | Simplify the timing-weighted high-utilization signal (experiment first) | The timing signal is strategically selectable (buyers can wait for the last block), which means it measures buyer sophistication more than demand urgency. The recorded reason for keeping it is that it provides information and `minUpBps` is the safety floor. This is correct but the information value is marginal and the complexity is real. | Buyer: no visible change (rate still adjusts at rollover). Operator: fewer parameters to calibrate (collapse `minUpBps`/`maxUpBps` to one `upBps`; same for down). | `InstantBondLane.vy`: `_nextRate` high branch. Config: drop `minUpBps`/`maxUpBps` to a single `upBps`, or keep both but set them equal in production calibration. | **3** |
| **Keep** | No vesting / no extra lock separate from RipeGov | The Olympus V1→V2 migration shows that vesting adds complexity without distribution benefit. Selling-pressure management belongs in RipeGov (the lock product), not the sale product. The dormant `maxLockBonus=0` policy is correct given RipeGov's share-weighted blending. | Buyer: gets RIPE unlocked (or RipeGov-locked if they choose). No new claim token, no escrow, no transfer surface. Operator: no new contract, no new state, no new token. | No change. | — |
| **Keep** | Override as one-shot, last-write-wins, consumed at next successful rollover | The one-shot design is the right granularity for a governance intervention — it sets one rate for one epoch and then resumes the ordinary controller. Adding a multi-epoch hold or target-epoch scheduling would create a state machine that's harder to reason about. The only change is adding expiry (row 1). | No change from current design except expiry. | No change. | — |
| **Keep** | Epoch-fixed price + lazy rollover (no keeper) | The no-keeper design eliminates a failure mode (keeper goes down, rate doesn't update). The "first buyer gets the new rate" leak is bounded by the per-epoch cap and is the same value-transfer that Olympus's first-bonder-after-adjustment experienced. A continuous-price alternative (Shape 3) would eliminate this but adds more complexity than it saves. | Buyer: the first buy after an epoch boundary gets the newly-adjusted rate. This is a small, bounded advantage. Operator: no keeper to run, monitor, or secure. | No change. | — |
| **Keep** | Full-fill-only (no partial fills, no reservations) | Partial fills would require a reservation system (new state, new race condition) or an implicit fill (surprising to buyers who expected the full amount). Full-fill-or-revert is the simplest honest behavior. | Buyer: if capacity is consumed first, the transaction reverts and they re-preview and retry. This is explicit and documented. | No change. | — |
| **Keep** | `canBuyNow` as an immediate emergency switch (not timelocked) | Pricing fields are prospective (snapshotted at rollover). `canBuyNow` is the only immediate "stop selling now" control besides Department pause. Timelocking it would delay emergency response. | Operator: can disable purchases immediately without waiting for a timelock. | No change. | — |
| **Keep** | `setCumulativeMinted` as a budget-management tool | This lets governance correct accounting (e.g., after a replacement lane) or reduce remaining budget. It can't increase the mint budget (that requires a full config write). Bounded by `mintBudget`. | Operator: can adjust remaining budget without a full config replacement. | No change. | — |
| **Keep** | No payment-token depeg oracle in the contract | The contract can't read external prices without an oracle it explicitly doesn't want. Depeg detection is an operational requirement (activation manifest: price source, deviation threshold, monitoring owner, pause authority, reopening requirements). The exact-receipt check protects against fee-on-transfer and short transfers, not against a depegged token that transfers correctly but is worth $0.50. The per-epoch cap and mint budget bound the maximum damage. | Operator: must monitor payment-token price externally and pause on depeg. The lane will happily accept a depegged token at the configured rate until paused. | No change — but the activation manifest already requires the full depeg monitoring stack. | — |
| **Keep** | No hard sunset; `mintBudget` is the effective sunset | Once `cumulativeMinted` reaches `mintBudget`, no more RIPE can be minted. The lane stays in a "budget exhausted" state until governance raises the budget or decommissions it. This is the right behavior for a distribution mechanism — it runs until its job is done. | Operator: decommission with `canBuyNow=false`, pause, or deregistration. | No change. | — |
| **Keep** | Immutable `epochLength` once installed (only `start` can change it) | Allowing `setConfig` to change the epoch length would break the deterministic clock and require a rebaseline branch. The current design (stop → start with new length) is simpler and safer. | Operator: changing the cadence requires stop/start, which clears the epoch state and override. This is a feature, not a bug. | No change. | — |
| **Keep** | Preview `available` as market-readiness only (not wallet preflight) | `available` is not a guarantee that `buyNow` will succeed — it doesn't check wallet balance, allowance, Endaoment liveness, vault/Teller admission, or RIPE pause. This is the right split: preview is a quote, not a reservation. | Buyer: must handle `buyNow` reverts from downstream failures by retrying. The `expectedEpoch`/`minRipeOut`/`deadlineBlock` bindings protect price and timing. | No change. | — |

### Expansion of the three highest-priority changes

**1. Add override expiry (change)**

*What changes:* The override gains an optional `overrideExpiryEpoch`. If set, the override silently clears when the projected epoch exceeds it, reverting to the ordinary controller rate. If `0` (default), no expiry — backward compatible with the current behavior.

*Tradeoff:* An override that expires silently could surprise an operator who expected it to persist. But the alternative — an override that persists indefinitely through pause and applies at an unexpected time — is worse. The fail-safe direction is: if in doubt, revert to the ordinary controller, which is the default safe state. The operator can re-install the override if still needed.

*Precedent:* No DeFi precedent has a persistent-no-expiry override that I found. Olympus's BCV was continuously adjustable (no expiry needed). Bond Protocol's auction parameters are set per-auction (naturally expire at auction close). The closest analog is the ESPP offering period — it has a defined end date, after which the discount is no longer available.

*Where it breaks:* If the operator installs an override and the lane runs normally, the override is consumed at the next rollover (as today) and the expiry never triggers. The expiry only matters when the lane is paused or has no buyers for longer than the expiry window — exactly the scenario where a stale override is most likely to be wrong.

*Recorded decision overridden:* §6.7 "Deferred mechanisms" lists "automatic target-epoch override scheduling or expiry" as deliberately excluded because "each would add a new signal, authority path, or state machine." An expiry epoch is not a target-epoch scheduler (it doesn't choose *when* to apply; it chooses *when to stop applying*). It's not a new authority path (the same Foxtrot action that installs the override can set its expiry). It's not a state machine (it's one comparison). The recorded reason is wrong.

**2. Rename from "Instant Bond" (change)**

*What changes:* The contract, docs, events, and RipeHq registry entry are renamed to reflect what the mechanism is: a primary-market RIPE sale with demand-responsive pricing.

*Tradeoff:* "Bond" has DeFi familiarity (Olympus, Bond Protocol) but creates false expectations. A buyer who sees "bond" expects vesting, maturity, or a claim on future redemption. The FAQ explicitly says "no — it is a direct primary-market RIPE purchase with optional RipeGov locking." The name should say what the FAQ says.

*Precedent:* Olympus's naming was widely criticized for the same reason — "bonds" that were actually discounted token sales with vesting, not debt instruments. Bond Protocol inherited the term. Neither is a reason to repeat the confusion.

*Where it breaks:* If the name stays "bond," every buyer education effort must start by saying "it's not actually a bond." If the name changes, there's a one-time migration cost (renamed events, renamed contracts, updated indexers) but ongoing clarity.

**3. Simplify timing-weighted adjustment (change, experiment first)**

*What changes:* The high-utilization branch's amount-weighted earliness signal is either removed (collapse `minUpBps`/`maxUpBps` to a single `upBps`) or made optional. The controller still raises the rate on high utilization — it just doesn't distinguish early from late sellouts.

*Tradeoff:* The timing signal provides one piece of information: "did the epoch sell out early (demand likely far above cap) or late (demand likely close to cap)?" This is a real signal. But it's strategically selectable — a sophisticated buyer can wait for the last block, getting the `minUpBps` response regardless. The net effect is that the signal measures buyer sophistication, not demand urgency. The design's response is correct: "`minUpBps` and the entire range must remain safe under repeated final-block full-cap purchases." So the timing signal is a bonus on top of the safety floor, not a safety mechanism itself.

*Precedent:* The GDA/VRGDA doesn't use a timing signal — it uses sales velocity. The Olympus BCV didn't use timing — it used debt ratio. No precedent I found uses amount-weighted within-period timing as a price signal. The innovation is real but the value is marginal.

*Where it breaks:* If the timing signal is removed, the controller can't distinguish a 100%-utilization epoch that sold out in block 1 from one that sold out in the last block. Both get the same `upBps` step. This loses information but not safety — the step is still bounded by the anti-ratchet constraints and the rate ceiling.

*Experiment:* Run the deterministic simulator with `minUpBps == maxUpBps` (timing-weighted adjustment effectively disabled) and compare the rate trajectories against the current `minUpBps < maxUpBps` configuration. If the trajectories are within the calibration tolerance (which the owner hasn't set yet — this is pre-calibration), the timing signal isn't worth its complexity. Evidence that would settle it: a simulation showing that the timing-weighted rate trajectory is materially better at matching a target utilization than the flat-step trajectory, over a range of demand scenarios. If it's not materially better, remove it.

*Recorded decision overridden:* The implementation-spec (owner decision #18) records that "high-utilization price increases use governed minimum and maximum steps" determined by "both utilization above the high threshold and the payment-amount-weighted purchase timing within the epoch." This is the recorded decision. My disagreement: the timing signal is strategically selectable, which limits its value to marginal. The `minUpBps` floor is the real safety boundary. The `maxUpBps` ceiling adds calibration surface (two parameters instead of one) and controller complexity (the earliness computation and amount-weighted accumulation) for a signal that sophisticated buyers will game toward `minUpBps` anyway.

---

## 6. Quote matrix

### What preview reports, what can change, what buy binds, retry UX

| What `previewBuyNow` reports | What can change before `buyNow` | What `buyNow` binds | Retry UX |
|------------------------------|----------------------------------|---------------------|----------|
| `available` — market-readiness: unpaused, running, `canBuyNow`, payment in cap/min window, mint budget covers payout, RipeHq authorizes mint. **Not** wallet balance, allowance, Endaoment liveness, vault/Teller admission, RIPE pause/blacklist. | Another buyer consumes capacity (reduces `remainingPayment`). A live control changes (`canBuyNow`, pause, mint budget, RipeHq mint auth). The epoch rolls over (rate changes, cap resets). Lock terms change (vault min/max, exit fee, freeze). An override is installed or cancelled. | `expectedEpoch` — must match the projected epoch at execution. `minRipeOut` — slippage floor; buy reverts if `totalRipe < minRipeOut`. `deadlineBlock` — buy reverts if `block.number > deadlineBlock`. | If `buyNow` reverts: re-preview (fresh `expectedEpoch`, fresh `minRipeOut`, fresh `deadlineBlock`), retry. Full-fill only — no partial fill to fall back on. The revert reason (`dev:` string) tells the client what changed. |

### What preview reports in detail

The `InstantBondQuote` struct:
- `available`, `epoch`, `rate` — the projected epoch's fixed base rate
- `remainingPayment` — remaining epoch capacity
- `minPaymentAmount` — epoch minimum
- `budgetRemaining` — `mintBudget - cumulativeMinted`
- `baseRipe`, `bonusRatio`, `bonusRipe`, `actualLock`, `totalRipe` — payout math
- `ripeGovVaultId` — current core RipeGov vault (locked only)
- `canExitEarly`, `exitFee`, `isExitFrozen` — lock disclosure (locked only)

### Override lifecycle (with the proposed expiry change)

1. **Queue:** Operator calls `setInstantBondRateOverride(targetRate)` via Foxtrot. Foxtrot pre-validates with `isValidRateOverride`. Timelock starts. `PendingRateOverrideSet` event.
2. **Activate:** After timelock, operator calls `executePendingAction(aid)`. Foxtrot re-validates and calls `lane.setRateOverride(targetRate)`. `RateOverrideInstalled` event. The override is now live: valid only while the lane is running and `epochState.rate != 0`.
3. **Expire (new):** If `overrideExpiryEpoch != 0` and the projected epoch exceeds it, the override silently clears at the next rollover projection. `RateOverrideInvalidated` event (or a new `RateOverrideExpired` event). The ordinary controller rate is used.
4. **Consume:** The first successful rollover after installation stores the override rate exactly, consumes it (`rateOverride = 0`), and emits `RateOverrideApplied` with the counterfactual `controllerRate`. The following epoch resumes ordinary control from the overridden rate.
5. **Cancel:** Operator calls `cancelInstantBondRateOverride()` via Foxtrot (timelocked). Foxtrot pre-validates with `canCancelRateOverride`. After timelock, `executePendingAction(aid)` calls `lane.cancelRateOverride()`. `RateOverrideCancelled` event.
6. **Invalidate:** Any successful `setConfig`, `start`, or `stop` clears the override. `RateOverrideInvalidated` event. `setCanBuyNow` does **not** clear it.
7. **Pause:** Department pause does **not** clear the override. The override persists through pause. This is by design (pause is a short incident switch that preserves state). The operator must revalidate or cancel before unpause — this is an operational requirement, not a mechanism guard. The proposed expiry is the mechanism guard.

---

## 7. Open questions

1. **What is the intended epoch length and payment cap for production?** This determines whether the "first buyer gets the new rate" leak is material (1 epoch = 1 hour = small leak) or significant (1 epoch = 1 day = large leak). It also determines whether the timing-weighted signal is worth its complexity (short epochs → less time to strategize → more honest signal; long epochs → more time → more gaming). This would settle the priority-3 experiment.

2. **Is the lane intended to run continuously or in discrete campaigns?** If continuous, the no-sunset design is correct and the override expiry is important (forgotten overrides accumulate over time). If in discrete campaigns (e.g., "distribute 500K RIPE over 3 months"), a sunset or campaign-end mechanism would be more natural than the current perpetual-until-disabled design.

3. **Does the operator have an off-chain depeg monitoring and pause procedure that can fire within one epoch?** If yes, the no-depeg-oracle design is fine — the per-epoch cap bounds the damage. If no (monitoring is slow or manual), the maximum depeg damage is `paymentCapPerEpoch × maxEffectiveRate / paymentScale` RIPE minted for a depegged token, which could be significant. This doesn't change the picked shape (the contract can't do oracle-based depeg detection without adding one), but it changes the urgency of the operational depeg monitoring requirement.
