# Instant Bond Lane — On-Chain Pricing via a Demand Controller

**Status:** Design proposal / rationale. Planning and discussion only.

> **Note (read first):** This is the pricing *rationale and intuition* only. The
> **decided v1 shape lives in [`implementation-spec.md`](implementation-spec.md)**,
> which supersedes this document wherever they differ. Superseded here: v1 uses
> **flexible configurable locks with a linear bonus** (not a single fixed lock); the
> **DECAY** empty-epoch policy (not HOLD); **governed-like-the-bonds** configuration
> with a **governed, raisable mint budget** (not an immutable pilot / immutable
> budget); a **dedicated Switchboard** for config (there *are* governance changes, not
> "no Switchboard changes"); a **deployment-selected dollar-denominated payment
> token with a derived decimal scale** (not USDC-only or a fixed six-decimal scale);
> and **no hard sunset** (governance disables instead). Read the sections below for
> the *why*; take the *what* from the spec.

**Prepared:** 5 August 2026 · **Revised:** 6 August 2026 after implementation reconciliation

**Purpose:** This document explains how the Instant Bond Lane sets its Buy Now
price and why. The broader feature scope (shared Bonding UI, inventory, settlement
into the RIPE governance vault) is covered by the original design doc kept outside
this repo, in `hightop-notes/ripe/`; this file focuses only on price.

**What this mechanism is, stated plainly:** a **cap-clearing controller**, not a
fair-value oracle. It finds the price at which a small, fixed sale budget clears
near a target level of demand, and it manages that budget conservatively. It does
not attempt to discover what RIPE is worth on external venues. Arbitrage keeps its
price tethered to the external market — the tether tighter the smaller the cap —
but the controller's job is to sell a bounded budget at a self-adjusting price, not
to be an oracle.

**Implementation authority:** None. Nothing here authorizes contract changes,
deployment, configuration, RIPE minting, or activation.

---

## 1. The core idea

Let the sale set its own price. Each lane epoch has one fixed Buy Now price,
computed once at rollover from a single fact the contract already knows: **how
much of the previous epoch's capacity actually sold.** If an epoch clears its cap,
the next epoch's price steps up. If it clears weakly, the next epoch's price steps
down, above a hard floor. Nothing else feeds the price — no reference feed, no
observation buffer, no DEX read, no per-epoch admin transaction.

The safety of the design lives in three immutable limits, not in the controller:
a small per-epoch capacity cap, a hard price floor, and a small lifetime mint
ceiling. The controller is convenience automation that moves the price between
epochs; the limits are what protect the treasury and RIPE supply.

---

## 2. How the controller works

A three-state rule keyed on the previous epoch's utilization. Reasoning in price
space (USD per RIPE):

```text
u = acceptedPayment[prev] / paymentCap[prev]  # same payment-token units; see §2.1

if   u >= uHigh:   price steps up    (price *= 1 + upBps/10_000)
elif u <= uLow:    price steps down  (price *= 1 - downBps/10_000)
else:              price unchanged

price = max(price, floor)                     # hard floor; lock-adjusted if locks are used
```

The two thresholds `uHigh`/`uLow` are the dead band. There is deliberately no
separate target, gain, or clamp — a bounded step in one of three directions is the
whole controller, which keeps it trivial to audit and reason about.

### 2.1 One consistent domain: payment-token utilization

Utilization is measured as **accepted payment over the snapshotted payment cap** —
a single domain end to end. This matches the Bond Room's payment-domain capacity
and directly measures how much fundraising capacity cleared. (Because the price is
fixed within an epoch, payment and RIPE are proportional inside that epoch, so the
signal is the same either way; what matters is that the cap and the "sold" figure
are the same unit.)

A payment-token cap does not by itself bound RIPE dilution — at a low price a fixed
payment cap mints more RIPE. That second boundary is provided explicitly by the
**hard floor** (which caps RIPE-per-payment-token, so worst-case per-epoch issuance
is `paymentCap × floorRate / PAYMENT_SCALE`) and the **mint budget**. The configured
dollar-denominated payment token supplies the capacity domain; the floor and mint
budget carry dilution control.

### 2.2 Exact inverse-price arithmetic

The lane stores a rate `R` = RIPE-wei per whole payment token, which is the inverse
of price, so a price *increase* is a rate *decrease* — and not by the same
percentage. Bind it exactly, rounding to the treasury-protective side (fewer RIPE
out):

```text
price up   -> R = R * 10_000 / (10_000 + upBps)     # round down
price down -> R = R * 10_000 / (10_000 - downBps)    # round down
R = min(R, floorRate)                                # max RIPE-wei per whole payment token

ripeOut = paymentAmount * R / PAYMENT_SCALE          # derive scale from token decimals
```

Naively multiplying the rate by `(1 - upBps)` for a price rise introduces roughly a
0.16% per-step error that compounds; the exact form above avoids it.

### 2.3 Downward movement and empty epochs

The price rises only when buyers actually pay for it. It falls on weak demand — and
"weak demand" needs an honest definition, because an epoch with **zero** buyers is
ambiguous: it can mean genuine absence of demand, or it can mean an operational
outage (frontend down, lane paused, mint budget exhausted, payment token paused,
chain congestion). Two options, presented as a dial the owner sets once:

- **Treasury-protective (recommended default):** only epochs with real but
  insufficient demand (`u <= uLow` with nonzero sales) step the price down. A fully
  empty epoch **holds** the price. This closes the "wait it down for free" option,
  at the cost that after a sharp downward regime change the price can sit stale-high
  and the lane goes dormant until the pilot sunsets (acceptable for a small,
  time-boxed pilot — see §7).
- **Availability:** a fully empty epoch applies a small bounded decay. This gives
  automatic downward discovery but is honestly a *free waiting option* for a patient
  buyer (cost = time and front-run risk, not capital). The floor, small cap, and
  sunset bound what that option is worth.

Either way, the honest statement is: **moving the price up costs real money;
moving it down costs only patience.** The floor and the small cap — not any claim
that waiting is expensive — are what bound the downside.

---

## 3. What the controller does and does not give you

**It gives you a price with no routine configuration and no oracle.** The step
sizes and thresholds are set once. They are invariant to the price *level* — the
controller adjusts multiplicatively from wherever the price already is, so the same
`upBps`/`downBps` keep working whether RIPE is at 3 cents or 30 cents.

**It does not give you fast tracking of external value, and its equilibrium is not
purely a function of the price level.** The controller finds a *cap-clearing*
price, and where that clears depends on capacity, epoch length, buyer
concentration, lock terms, and demand elasticity — not just the level. Arbitrage
pulls the cap-clearing price toward external value (below market → sells out →
steps up; above market → sits → steps down), and the smaller the cap relative to
real market volume, the tighter that tether. So "tracks the market" is true only in
the limited, arbitrage-mediated, lagged sense, and only while the cap stays small.

**Its response is bounded and, for large moves, slow.** With an illustrative 4%
up-step and 8-hour epochs:

| Move | Sold-out epochs to track it | Wall-clock |
| --- | --- | --- |
| +30% | ~7 | ~2.3 days |
| 2× | ~18 | ~5.9 days |
| 10× | ~59 | ~19.6 days |

A downward 1.5% step halves the price in ~46 epochs (~15 days). A sellout is also
*censored* information: it tells you demand was at least the cap, not whether it was
1.1× or 100× the cap, so the controller cannot leap — it can only ratchet. This is
fine when the cap is small (the per-epoch cost of lagging is bounded, §4); it is the
core reason this is a pilot mechanism for a bounded budget, not a large-issuance
oracle.

---

## 4. The lag cost, quantified

Because the controller is reactive, a fast upward move opens a temporary gap during
which the lane sells its capacity below external value to whoever moves first. The
cost is bounded and self-correcting, and it has a clean rule of thumb:

```text
leak  ≈  capacity  ×  gap²  /  (2 × upStep)
```

For a $50k/epoch cap, a sudden +30% move, and 4% steps, that is ≈ $56k of value left
on the table over the whole ~7-epoch catch-up — a one-time transient, not a standing
leak. The formula shows the three levers: the cost is **quadratic** in the size of
the move (gentle drift costs almost nothing), **inversely proportional** to the step
size (faster catch-up, less leak), and **linear** in capacity — which is why a small
cap is the primary control. The leak is a transfer to fast arbitrageurs, and the
same sellouts that hand it to them are what feed the controller the signal to close
the gap.

Two later refinements (§6.6) attack this directly if the pilot shows it matters:
*sellout-time acceleration* (step up harder when an epoch sells out very early,
using early sellout as a proxy for the censored excess demand) shortens the catch-up,
and a *within-epoch tranche schedule* (sell the cap along a rising ramp) captures
part of the gap for the treasury and de-censors the demand signal. Both are
deliberately out of the minimal pilot.

---

## 5. Precedent

This design draws on a family of on-chain issuance mechanisms, though it is its own
mechanism — a once-per-epoch, prior-utilization feedback rule rather than any of
these exactly. What they collectively validate are the **primitives**: bounded
capacity, a hard price floor, demand-responsive pricing, asymmetric adjustment
(raise faster than you lower), and conservative issuance.

- **Bond Protocol's Sequential Dutch Auctioneer** — oracle-free pricing driven by
  the market's own realized sales versus a target, with increases applied faster
  than decreases and a debt-buffer circuit breaker (worth borrowing as a velocity
  breaker). It tunes continuously through purchases rather than once per epoch.
- **Paradigm's GDA / VRGDA** — price responds to sales being ahead of or behind an
  explicit issuance schedule; validates schedule-vs-price feedback, a different
  signal than prior-epoch cap utilization.
- **Frax FXB** — a live gradual Dutch auction with a governed price floor;
  validates the `max(demand-driven price, floor)` safety shape.
- **Olympus's Emissions Manager** — a surviving admin-light issuance rule anchored
  to a stored solvency figure via an explicit governance path; a conceptual
  reference for a backing-linked floor, not a template for reading a wallet balance
  as a solvency oracle.

The consistent lesson across all of them is that the **floor and the capacity cap,
not pricing sophistication, are what protect the treasury.**

---

## 6. Supporting design choices

### 6.1 Mint at purchase against an immutable lifetime ceiling

The lane mints exactly the RIPE it sells, at purchase time, decrementing an
allowance **before** any external call. For the pilot the lifetime ceiling is
**immutable and small** — no replenishment path exists. This eliminates the
pre-minted bucket, inventory retirement, excess-balance reconciliation, and
circulating-supply ambiguity, and it keeps the global kill-switch honest (RipeHq's
`mintEnabled` halts minting instantly). Scaling the budget later is a fresh
deployment and a fresh decision, not an automatic top-up.

### 6.2 An independent lane epoch — a deliberate reversal

Because the controller needs nothing from the Bond Room at runtime, the lane runs
its own deterministic clock:

```text
laneEpoch = (block.number - genesis) // EPOCH_LENGTH
```

No stored clock, no cross-contract refresh, no epoch-key handshake, no coupling to
Bond Room pause or sellout. This must be recorded as a **deliberate reversal** of
the broader design's agreed direction (which specified strict Bond Room / Ledger
following and one canonical epoch): call it the *lane epoch*, not the canonical Bond
epoch; do not promise a single shared countdown unless the two schedules genuinely
stay aligned; accept that a Bond Room sellout or restart no longer closes the Buy
Now epoch; and reconcile the broader document if this is approved. The upside is a
markedly smaller, self-contained contract, which is why the reversal is worth
proposing.

(Implementer's note, if strict following is ever revived instead: the Bond Room
schedules a post-sellout epoch at a *future* start, and the one-line "fix"
`newStartBlock = max(block.number, epochEnd + restartDelayBlocks)` is a no-op because
`block.number < epochEnd` always holds at sellout. The independent clock avoids the
whole issue.)

### 6.3 A fixed, conservative floor for v1

The pilot uses **one immutable, conservative effective-price floor**, enforced in
the stored rate domain as a maximum RIPE-per-payment-token. No PriceDesk call, no
backing calculation. A solvency-linked, self-updating floor is attractive in
principle but is a real subsystem — it needs definitions and failure semantics for which
Endaoment assets count, their pricing, liabilities and encumbrances, "circulating
RIPE" exclusions, depeg behavior, and last-good handling, and a naive
`max(governedFloor, k × backing)` can fall automatically when backing falls, which
would contradict a "lower only deliberately" rule. It is deferred to §6.6, not part
of v1.

### 6.4 Buyer is the recipient

The `buyNow` entry requires `recipient == msg.sender` for the pilot. The Bond Room
explicitly gates bonding-for-another (`BondRoom.vy:144-145`), and because RipeGov
merges deposits into one weighted, blended-unlock position per user
(`RipeGov.vy:679,719`), a third party locking on someone's behalf can move that
person's unlock schedule — a griefing surface. Gifting and delegated-wallet support
can be added later with an explicit authorization and lock-interaction spec.

### 6.5 Isolation limits code risk, not economic risk

A separate contract protects the Bond Room and Ledger from regressions. It does
**not** bound RIPE supply risk: once the lane is a registered minter, RipeHq's check
is binary (`RipeHq.vy:389`), and the global `mintEnabled` switch stops every minter
at once, not just this one. The lane therefore needs, as first-class requirements:
its own pause; an immutable, small lifetime mint ceiling; the decrement-before-
external-call budget invariant; a deliberately small per-epoch cap; and an explicit
sunset. The pause can reuse the existing generic Switchboard pause
(`SwitchboardCharlie.vy:491` pauses an arbitrary contract), so no Switchboard change
is required for a fully-immutable pilot.

### 6.6 Deferred refinements (post-pilot, each with a trigger)

Kept out of v1 on purpose; revisit only if pilot data calls for it:

- **Continuous controller** (target + gain + clamped step) if the three-state rule
  proves too coarse.
- **Sellout-time acceleration** and a **within-epoch tranche schedule** if the lag
  cost (§4) or the censored-demand signal proves material.
- **Self-updating solvency floor** (§6.3) if a fixed floor drifts too far from
  reality over time — with the full backing definitions specified.
- **Flexible lock bonuses** (see §6.7) if a single fixed lock is too limiting.
- **Replenishable mint budget and governed setters** if the pilot graduates to a
  standing mechanism — which requires a Switchboard change or an internal timelock
  (there is no generic timelocked-call executor today).
- **Third-party recipients / gifting** with proper authorization (§6.4).

### 6.7 Lock terms: one fixed lock for the pilot

The broader design wants flexible lock selection (an agreed direction there), and
that remains the destination. For the minimal pilot, though, a **single fixed lock
duration with one all-in payout rate** (or no lock at all) is cleaner: it removes a
second continuous pricing dimension, and it avoids a governance-concentration edge —
a maximum-lock purchase can receive up to 3× the RIPE *and* accrue up to a further
3× RipeGov points on that larger position (up to ~9× point accrual per dollar versus
an unlocked base unit; `RipeGov.vy:618,679`), which the small per-epoch cap and short
pilot are what keep in check. If flexible locks are retained instead, measuring
utilization in the payment/base domain (§2.1) keeps the control signal clean, since a
buyer's lock choice does not change how much of the cap their payment consumes. A
transaction-size-based minimum-lock rule is **not** recommended — it is evadable by
splitting across recipients or transactions, and is dropped in favor of a uniform
lock decision.

### 6.8 Configured payment-token settlement math

The single configured payment token needs no unit-flooring (the Bond Room floors to
whole units, `BondRoom.vy:164`, because it is multi-asset). Use every smallest unit —
`ripeOut = paymentAmount * R / PAYMENT_SCALE` — and forward the exact accepted
payment straight to Endaoment Funds. `PAYMENT_SCALE` is derived from the token's
declared decimals at deployment. No dust, no temporary balance, no refund branch.

### 6.9 Booster excluded; bad debt scoped

The Bond Booster stays out of Buy Now (the single largest per-dollar dilution
improvement). On bad debt: there is no special *pricing* branch (a buyer's
payment-to-payout ratio is unaffected), but integration decisions remain and should
be settled before launch — whether Buy Now is available during bad debt, whether its
proceeds count toward recorded debt reduction, whether its mint budget sits outside
the global Bond allowance, and how combined Bond + Buy Now dilution is reported.

---

## 7. The minimal pilot to build

One immutable, non-upgradeable contract. Achievable as a *single* new contract
precisely because everything is fixed at deployment — no setters, no replenishment,
generic pause reused. Roughly 150–250 lines of Vyper; zero changes to `BondRoom`,
`Ledger`, `RipeToken`, or `RipeGov`. The only external step is registering it as a
RIPE minter in RipeHq (a governance action, not a contract change), and it should
carry an explicit sunset and eventual deregistration.

**Immutable at deploy:**

```text
EPOCH_LENGTH            # lane epoch, in blocks
uHigh / uLow            # utilization thresholds (the dead band)
upBps / downBps         # asymmetric step sizes (up larger than down)
floorRate               # max RIPE-wei per whole payment token
paymentCapPerEpoch      # small per-epoch capacity, payment-token domain
lifetimeMintCeiling     # small hard cap on total RIPE the lane can ever mint
seedRate                # the one-time human price judgment
sunsetEpoch             # lane stops selling after this
emptyEpochPolicy        # hold (default) or bounded-decay (§2.3)
```

**Stored state (bounded — current and previous only; history via events):**

```text
currentEpoch, currentRate
prevEpochAcceptedPayment, prevEpochPaymentCap
cumulativeMinted
```

**Functions:**

```text
buyNow(paymentAmount, expectedEpoch, minRipeOut, deadline)   # recipient == msg.sender
previewBuyNow(paymentAmount)                                  # mirrors lazy rollover read-only
# rollover is lazy inside buyNow; no external initializeEpoch
# pause via the existing generic Switchboard pause; global mint switch also applies
```

**Purchase path:** lazily roll the epoch if `laneEpoch` advanced (compute the new
rate from `prevEpochAcceptedPayment / prevEpochPaymentCap` via §2.2, apply the empty-epoch
policy for any fully-skipped epochs, clamp to `floorRate`) → validate
`expectedEpoch`, sunset, pause, `deadline`, remaining epoch cap, and lifetime
ceiling → `ripeOut = paymentAmount * R / PAYMENT_SCALE`, check `>= minRipeOut` →
decrement the mint ceiling and epoch cap **before** external calls → mint `ripeOut`
→ forward exact payment to Endaoment Funds → settle RIPE (transfer, or
trusted-deposit if a fixed lock is used). Revert on cap exceed (no partial fills).

If a fixed lock is included, settlement adds the Teller/RipeGov trusted-deposit path;
the controller and all math above are unchanged.

---

## 8. Where this design lands on the open questions

| ID | Question | Pilot position |
| --- | --- | --- |
| IBL-003 | Effective-price floor | Fixed, conservative, immutable; solvency-linked floor deferred (§6.3) |
| IBL-004 | Price behavior within an epoch | One immutable price per epoch; tranche schedule deferred |
| IBL-005 | Capacity cap domain | Configured payment token per epoch; dilution bounded by the floor + mint budget (§2.1) |
| IBL-007 | Payment asset | Deployment-selected dollar-denominated ERC-20, with derived decimal scale (§6.8) |
| IBL-009 | Bond Booster | Excluded |
| IBL-010 | Minimum lock | One fixed lock (or none); no size-threshold rule (§6.7) |
| IBL-013 | Purchase entry / recipient | Direct call, `recipient == msg.sender` (§6.4) |
| IBL-014/15/18/22 | Inventory and supply | Mint-at-purchase against an immutable lifetime ceiling; no replenishment in the pilot (§6.1) |
| IBL-016/17 | Epoch clock and pause | Independent lane epoch — a deliberate reversal (§6.2); generic pause |
| IBL-024 | Cold-start price | One immutable `seedRate`; the acknowledged human judgment |
| IBL-025 | Bad debt | No special pricing branch; integration decisions remain open (§6.9) |

---

## 9. Next steps

1. **Approve the framing:** a small, immutable, capped pilot that clears a bounded
   sale budget at a self-adjusting price — explicitly *not* a fair-value oracle and
   not (yet) a large-issuance mechanism.
2. **Approve the two reversals/scope calls explicitly:** the independent lane epoch
   (§6.2) and a single fixed lock for the pilot (§6.7).
3. **Calibrate the pilot constants.** Historical Bond activity gives rough context
   but not clean Buy Now elasticity (different auction shape, capacity, and
   incentives), so size `paymentCapPerEpoch`, `upBps`/`downBps`, `uHigh`/`uLow`, and
   `floorRate` conservatively and small, and let the pilot itself produce the
   elasticity data.
4. **Simulate** the three-state controller across a fast rally, a decline, a quiet
   stretch, a cold start, and whale-dominated flow — checking tracking, oscillation,
   and the fraction of epochs live versus dormant.
5. **Spec and audit** the immutable pilot as a new, isolated registered minter, with
   the mint-ceiling and settlement invariants as the focus.
6. **Gate scaling on a fresh decision.** Any capacity or budget increase is a new
   economic and security review and a fresh deployment — never an automatic
   post-sellout increase.

---

## 10. Summary

The way to a fully on-chain Buy Now price that needs no routine configuration is to
let the sale move the price: raise it when the lane clears its cap, lower it
(boundedly, above a hard floor) when it does not. Kept honest, the mechanism is a
**cap-clearing controller for a small, bounded budget** — its price rises only when
buyers pay for it, falls only on weak demand, tracks external value only loosely and
through arbitrage, and responds to large moves over days, not minutes. Its safety
comes from three immutable limits — a small per-epoch cap, a hard floor, and a small
lifetime mint ceiling — plus its own pause and an explicit sunset. Build that pilot,
learn the real demand curve from it, and let a fresh decision — not the mechanism
itself — decide whether to scale.
