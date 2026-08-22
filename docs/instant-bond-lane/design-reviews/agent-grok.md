# Instant Bond Lane design review — grok

- Date: 2026-08-22
- Agent: grok
- Pin confirmed: d136a262
- Web access: yes

## 1. Confirm

Read at `d136a262f560fe628d7c3f7b667b0220871cb951`. Tree is `2cdcdd6e8f760995f57b05b529100cbcec6d4e5a`. Matches the pin. Files were read with `git show d136a262:<path>`. HEAD on this machine was a different commit; the working tree was not used as the source.

Two docs/code mismatches at this commit:

- The spec cites `RipeGov.vy:936-961` for share-weighted unlock. Those lines are governance-point math. The blend that exists is `_getWeightedLockOnTokenDeposit` at `1012–1040`. The described behavior matches that function.
- Revision 23 says the owner chose buyer-bound vault ID and minimum lock. Revision 24 and the contract drop both. Tests at this commit show an unlocked preview can settle locked if `minLockDuration` is raised between quote and buy.

## 2. Summary and verdicts

**Assumed top objective:** raise dollars for Endaoment Funds (the protocol vault) by selling newly minted RIPE, with a hard epoch cap and mint budget, and almost no operator babysitting.

I would not rank price discovery or governance-lock above that. This lane has no market price, and the RipeGov lock does not keep a separate lot. If the real goal were discovery, I would replace the controller. If the real goal were lock, I would not sell through RipeGov until isolated lots exist.

The product concept is sound. A buyer pays a qualified dollar token, the vault gets the cash, the buyer gets RIPE now or RIPE deposited into RipeGov. The clock ticks by itself. The first successful buy after a period boundary writes the new rate and fills at that rate. That is a standing primary sale, not a bond and not a fair-value oracle.

What is wrong is the extra machinery that fights that sale. Because the period price does not move, a buyer who thinks the cap will fill can wait until the last block, pay the same rate, and force only the weakest next-period increase. The activation manifest names that as strategically selectable. That is not a calibration leftover. It is the mechanism telling a large buyer when to hit it. The one-shot rate override can also sit through a pause and then fire, skipping the cheapening that empty time would have produced. And a buyer who asked for unlocked RIPE can be forced into a lock if operators raise the live floor before the transaction lands.

**Verdicts**

- Support this product concept? **yes**
- Picked shape: **simpler standing tap** (epoch-fixed utilization controller, no timing game, no extra vest, bind lock path, expire overrides)
- Top 3 changes: **bind unlocked vs locked; drop timing from the high-util step; make the override die on pause or unused time**
- Vesting: **don’t add**
- Override: **replace** with a short-lived lever that dies on pause (bounded nudge if they keep a manual price tool)
- Keep the name “Instant Bond”? **no**
- Epoch-fixed + lazy rollover: **keep**
- Biggest disagreement with a recorded decision: **keeping amount-weighted timing while the period price is fixed**, after calling that timing strategically selectable. The recorded reason treats last-block `minUpBps` as a calibration problem. It is a design problem. Buyers choose the signal because the price does not move.

---

## 3. Research

Quote direction, normalized: Ripe `rate` is RIPE per 1.0 payment-token unit. Higher rate = cheaper RIPE. Bond Protocol and Olympus markets quote payment per payout token (higher = more expensive OHM/payout). Olympus “discount” is versus an external market price. This lane has no market price, so it has no on-chain discount.

| Mechanism | Bucket | Pricing | Delivery / vest / lock | Caps | Operator lever | Durable? evidence | Implication |
|-----------|--------|---------|------------------------|------|----------------|-------------------|-------------|
| **Olympus v1 (2021) reserve and LP bonds** | Issuer sells gov token for reserves or LP | BCV / debt-ratio premium versus market OHM. Higher BCV → smaller discount. *Fact* from contemporaneous policy writeups and the v2 announcement’s description of v1. Current Olympus “legacy” pages now call this an SDA and point at Bond Protocol; that is a later rewrite, not 2021 language. | ~5-day **linear vest**; payout locked and staked; buyer could claim as it unlocked. *Fact* ([v2 announcement](https://olympusdao.medium.com/introducing-v2-bonds-a17c7da298a2), [user guide](https://docs.olympusdao.finance/main/user-guides/using-website/bonds/)). | Outstanding-debt / capacity via BCV. | BCV, vesting term, which assets. | **Shipped.** *Observed:* large treasury and near-total POL in 2021. *Observed:* discounted unlocked-over-days OHM was sold into a liquid market; later inverse bonds were built to absorb the other side. *Inference:* vest was load-bearing because there was a real market discount. *Unknown:* whether any given BCV path was “correct.” | Do not copy the name or the discount story. Do copy the reason they vested: they were selling cheap vs a visible market. This lane cannot see a market. |
| **Olympus v2 BondDepository (announced 8 Jan 2022)** | Same | Control variable, capacity, debt decay, tune interval. Markets retire at capacity. *Fact* ([v2 post](https://olympusdao.medium.com/introducing-v2-bonds-a17c7da298a2), [oighty’s v2 notes](https://blog.oighty.com/olympus-v2-bonds)). | Auto-stake; **no linear vest**. Fixed-term or fixed-expiry. Isolated markets, so one 3-day and one 60-day DAI bond can coexist. | Capacity in quote or payout; max payout / deposit interval; market `conclusion`. | Create/close markets; terms frozen after init. | **Shipped.** *Observed:* this is the contract shape Bond Protocol later productized. *Unknown:* whether auto-stake reduced dumps. | Isolated lots matter. RipeGov’s one blended unlock is the opposite of v2’s isolated markets. Keep `maxLockBonus = 0`. |
| **Olympus inverse bonds (2022)** | Issuer spends reserves to buy back its token | Offered when OHM was near or under liquid backing; premium capped by backing. *Fact* ([legacy bonding](https://docs.olympusdao.finance/main/legacy/bonding), [OIP-76 coverage](https://thedefiant.io/news/defi/olymusdao-inverse-bonds)). | Instant vest. OHM in, stables out. | Daily capacity; DAO on/off. | When to open, size, stop. | **Shipped as a policy lever.** *Observed:* built because reserve bonds had created sell pressure. *Unknown:* whether they “worked” as a floor. | Contrast only. Do not keep selling RIPE as a standing product and call it crisis hygiene. |
| **Olympus Pro → Bond Protocol SDA (2021–22)** | Issuer sells gov / protocol token for reserves or LP | Sequential Dutch: start high, decay, a fill jumps price up, then decay again. `price = decayed debt × control variable`. Tuning moves the control variable so the market can still finish its capacity. *Fact* ([Pro launch](https://olympusdao.medium.com/introducing-olympus-pro-d8db3052fca5), [Bond Protocol launch](https://medium.com/@Bond_Protocol/introducing-bond-protocol-8476881f84e4), [SDA pricing](https://dev.bondprotocol.finance/smart-contracts/bond-system/auctioneer/sequential-dutch-auctioneer-sda/auction-pricing)). **Lineage, labeled:** *Fact:* Pro (Sep 2021) sold Olympus-style bonds as a service. *Fact:* Bond Protocol (Jul 2022) is that service spun out. *Inference:* SDA is the named formalization of the v2 control-variable + debt-decay + tune market, not a 2021 v1 invention. | Vesting configurable; Bond Protocol markets have a conclusion time. 3-day minimum vest in the SDA writeup so price cannot gap to zero. | Capacity, max payout, debt buffer, conclusion. | Create, tune interval, min price, close. | **Shipped and reused.** *Observed:* many protocols ran these markets. *Unknown:* typical realized discount vs intent. *Inference:* “it shipped” is not “it was a good treasury trade.” | Closest DeFi cousin in the right bucket. Waiting is expensive. Ripe’s period price makes waiting cheap. That is the inverted incentive. |
| **Frax 2021 Olympus Pro (FIP-22)** | Issuer sells FXS for LP (first FXS-ETH, then FRAX-ETH) | Discount to market FXS, target preferably &lt;10%. *Fact* ([FIP-22](https://gov.frax.finance/t/fip-22-olympus-bond-program-with-fxs/130)). | **14-day linear vest, on purpose**, “so discount buyers can’t immediately flip.” Partial claims allowed. | 90k FXS / month proposed. Olympus took 3.3% of payouts. | Size, pair, discount, stop. | **Shipped as a pilot.** *Observed:* later forum comments cite ~$1.6M amassed. *Unknown:* net of discount and fee, whether the LP was worth it. | The vest was not flavor. It was the dump brake. If Ripe sells unlocked RIPE, it is not this program. |
| **Frax FXB (later)** | Issuer sells a discounted claim on its stablecoin | Gradual Dutch auction with a governed floor; redeem 1:1 for Legacy Frax Dollar at maturity. *Fact* ([Frax FXB docs](https://docs.frax.com/protocol/assets/frxusd/fxb)). | Fungible ERC-20; cash locked until maturity; then redeem FRAX, not FXS. | Series supply; auction qty and floor. | Comptroller / AMO starts auctions, sets floor. | **Shipped.** *Observed:* series exist and have been sold. *Unknown:* whether the curve is a useful policy rate. | Contrast. This is not a sale of the governance token. §5.1 should not treat it as a template. |
| **VRGDA (Paradigm, 2022)** | Issuer sells its own token to a schedule | Price rises when sales are ahead of schedule, falls when behind. Continuous. *Fact* ([Paradigm](https://www.paradigm.xyz/2022/08/vrgda)). | Immediate delivery in the published NFT uses. | Implied by the schedule and a price that can go arbitrarily high. | Target price, decay, schedule. | **Shipped** in Art Gobblers / 0xMonaco. *Unknown:* how often the schedule was actually hit. | If you care about “when” volume arrives, move price inside the period. Ripe’s timing branch observes when buyers chose to arrive at a flat price. That is not the same signal. |
| **Balancer LBP** | Issuer sells its own token for reserves | Weights shift so the project token cheapens unless buys push back. Waiting is the intended strategy. *Fact* ([Balancer LBP](https://docs.balancer.fi/concepts/explore-available-balancer-pools/liquidity-bootstrapping-pool/liquidity-bootstrapping-pool.html)). | Immediate tokens; sale window has a start and end; owner can pause. | Pool inventory and window. | Weights, window, pause, buy-only. | **Shipped widely.** *Observed:* used for launches and treasury sales. *Unknown / mixed:* post-sale dumps and bot flow still happen. | Rejected as a rebuild. Useful as a warning: a flat period price with a last-block bonus is an LBP with the slope removed and the late-arrival reward kept. |
| **Maker flop (debt auction)** | Issuer sells newly minted MKR for DAI | Reverse auction: fixed DAI, bidders take less and less MKR. *Fact* ([Maker flop docs](https://docs.makerdao.com/smart-contract-modules/system-stabilizer-module/flop-detailed-documentation)). | Immediate MKR. | Lot / bid size; only when bad debt clears a threshold. | `beg`, `ttl`, `tau`, on/off. | **Shipped.** *Observed:* used as crisis recap, not a standing window. Auction failures in stress are a known history. | Rejected as a template. The lesson is the opposite of owner decision 6: minting the governance token against cash during bad debt is a recap tool with a competitive price, not a standing tap that also freezes lock exits. |
| **Olympus Emissions Manager** | Issuer sells OHM for reserves | Only when market premium over backing exceeds a floor; size scales with premium. Needs a price module. Heartbeat. *Fact* ([EM docs](https://docs.olympusdao.finance/main/overview/emissions-manager)). | Auction / Bond Protocol fallback. | Rate × supply, tracking period. | Premium floor, rate, disable. | **Shipped** as later Olympus policy. *Unknown:* realized vs target. | Rejected analog. “Admin-light” here still needs a fair-value/backing oracle. Copying it would break this lane’s no-oracle choice. |
| **US ATM equity program** | Issuer sells its own equity for cash | **Market**, not a posted administered price. Agent dribbles shares into the tape. *Fact* ([Morrison Foerster ATM FAQ](https://assets.contentstack.io/v3/assets/blt5775cc69c999c255/bltf69f2ea7c45f697c/faqatthemarketofferings.pdf), [Cleary 2022](https://www.clearygottlieb.com/-/media/files/alert-memos-2022/20220606-alternative-capital-raising-for-public-companies-2022-ed.pdf), [DLA Piper](https://marketedge.dlapiper.com/2025/11/equity-lines-of-credit-and-at-the-market-offerings-alternative-public-financing-options/)). | Immediate listed shares. No vest. | Program size; practice is a small slice of daily volume (often cited ~5–15% ADTV). Issuer can set a floor. | Pause any time. Change floor, agent, remaining size. | **Durable in ordinary finance.** *Fact:* standard shelf tool. *Observed:* widely used by REITs and other issuers. | Closest ordinary-finance cousin if RIPE is unlocked. Price tracks the market. A stale posted rate is exactly what an ATM avoids. No vest. Rename. |
| **UK DMO gilt tap** | Issuer sells more of an existing gilt | Modern taps are **exceptional mini-auctions**, not a 24/7 window. Min price often near the then market. Uniform or multiple price. ≥1 hour notice. *Fact* ([DMO 2007](https://www.dmo.gov.uk/media/0ewlkrij/opnot180507.pdf), [DMO 2015](https://www.dmo.gov.uk/media/tcyim11a/opnot20150401.pdf)). | Ordinary gilt; no retail vest. | Announced size. | Announce, min price, close, never use as routine funding. | **Durable as a crisis/market-management tool; no longer routine.** | Rejected as “standing posted tap.” Useful anyway: the issuer does not leave a stale bid on the screen, and can halt. |
| **Fed ON RRP** | Standing facility (not equity issuance) | Posted offering rate, set by the FOMC, changed on a known schedule. *Fact* ([NY Fed FAQ](https://www.newyorkfed.org/markets/rrp_faq)). | Overnight; you get Treasuries and your cash back tomorrow. | Per-counterparty cap ($160bn on the current FAQ page); aggregate limited by available SOMA bills. | Rate, cap, eligibility, hours. | **Durable.** *Observed:* used daily as a rate floor. | Not a token sale. Use it for the control surface: posted rate, hard cap, operator can change the rate, nothing “fires later” after a halt. |
| **US Series EE / I savings bonds** | Issuer sells a claim on itself (dollars back + interest) | Posted rate for a window (I-bond composite resets every 6 months). *Fact* ([TreasuryDirect buy](https://treasurydirect.gov/savings-bonds/buy-a-bond/), [compare](https://treasurydirect.gov/savings-bonds/comparing-ee-and-i-bonds/)). | 12-month minimum hold; 3-month interest penalty if redeemed before 5 years; not a liquid market. $10k / person / year per series. | Annual purchase cap. | Treasury sets the rate; product rules are public. | **Durable.** | Rejected name analog. In ordinary speech a bond pays you back. This lane never returns the payment token. |
| **§423 ESPP** | Issuer sells its own equity to employees at a known discount | Up to 15% off market, often with a lookback. *Fact* ([IRS Topic 427](https://www.irs.gov/taxtopics/tc427), [myStockOptions](https://www.mystockoptions.com/articles/fundamentals-of-employee-stock-purchase-plans-part-3-tax-treatment-of-your-purchases-and-sales)). | Tax hold is 1 year from purchase and 2 years from offering for qualifying treatment. People can sell earlier and pay ordinary tax. | $25k FMV / year. | Plan design; not permissionless. | **Durable.** | Hold exists because the discount vs market is known. This lane has no such discount. Do not add a hold to cosplay an ESPP. |

**Lineage, short.** Olympus v1 (2021) was BCV + linear vest. Olympus v2 (early 2022) was capacity, control variable, auto-stake, fixed-term / fixed-expiry. Olympus Pro (Sep 2021) sold that family as a service. Bond Protocol (Jul 2022) is that service under a new name, with Sequential Dutch Auction as the written mechanism. I would not call 2021 v1 an SDA except in later Olympus docs that already point at Bond Protocol.

**Which comparisons changed a recommendation**

- **ATM** → treat this as a standing primary sale, not a bond; do not add vest; do not leave a stale administered price without a halt.
- **Olympus v1 / FIP-22 vest** → vest only if you are selling cheap versus a visible market. This lane cannot see a market, so do not add a second time-release.
- **Olympus v2 isolated markets** → keep lock bonus off until RipeGov can hold a separate lot.
- **Bond Protocol SDA / VRGDA** → keep epoch-fixed price if you want no keeper, but delete the timing branch. A flat price plus a last-block weaker up-step is the SDA waiting penalty run in reverse.
- **ON RRP / DMO halt** → a posted-rate window is fine; a lever that survives a pause and then fires is not.
- **Maker flop** → do not sell locked RIPE while early exit is frozen. Crisis issuance, if any, needs a competitive price and an open exit.
- **FXB, inverse bonds, savings bonds, Emissions Manager** → rejected templates. Wrong bucket, wrong direction, or they need an oracle this product refused.

---

## 4. Three shapes

**Current lane as-is.** Buyer sees a posted period rate, a remaining dollar cap, and a choice of unlocked RIPE or a RipeGov deposit. The first buy after the boundary can change that rate in the same transaction. A large buyer can wait until the last block, take the cap, and weaken the next increase. Operators have pause, `canBuyNow`, a timelocked full-config rewrite, and a one-shot exact rate that lives until a later successful rollover. Issuance discipline is real (epoch cap, mint budget, exact dollars to Endaoment). Operator load is low until something goes wrong, then the override and live lock floor are easy to misuse. Complexity is high for a posted-price tap: timing math, dormant bonus, override that ignores decay.

**A simpler lane (pick).** Same buyer path: approve the dollar token, preview, buy the whole size or revert, dollars to Endaoment, RIPE in wallet or RipeGov. Same epoch-fixed rate and lazy rollover, so still no keeper. Next rate moves on how much of the cap filled, not on when the buyer chose to arrive. Unlocked vs locked is bound on the buy. Manual price changes expire or die on pause. Issuance discipline is the same or tighter. Operator load is lower because there is less silent state. Complexity drops in the one place buyers can game and the one place operators can forget a loaded override.

**Bond Protocol-style sequential Dutch (from the table).** Buyer sees a price that cheapens until someone hits it, then jumps up. Waiting costs money. Vesting, if any, is a separate claim, not a RipeGov blend. Each market has a capacity and an end time. Issuance discipline is strong if min price and capacity are conservative. Operator load is higher: someone opens, tunes, and closes markets (or you take on Bond Protocol as a dependency). Complexity is higher than a tap and is a different product. I would only pick this if the top objective flipped to intra-period discovery.

---

## 5. Decision register (simpler lane)

| Keep / change / remove / experiment | Decision | Why | Buyer / operator effect | Surface and timing | Priority |
|--------------------------------------|----------|-----|-------------------------|--------------------|----------|
| **Change** | Bind unlocked vs locked on `buyNow` (and fail if the path flips). Restore what rev 24 removed. | Live `minLockDuration` can turn an unlocked quote into a locked settlement. Tests already show it. | Buyer cannot be shoved into RipeGov. Operators must change the floor between periods or accept failed buys. | `buyNow` + quote. Before any activation. | **P0** |
| **Change** | Drop amount-weighted timing from the high-util step. Utilization only. | Timing is chosen, not discovered, because the period price is flat. Overrides recorded “strategically selectable” / last-block `minUpBps` as a calibration task. | Last-block fill still pays this period’s rate (unavoidable if the price is fixed). It no longer also softens the next increase. | Controller only. Before calibration. | **P0** |
| **Change** | Replace the immortal one-shot override. Timelocked install, **immediate cancel**, **dies on pause / stop / unused expiry**. Prefer a bounded nudge over an exact rate. | Recorded skip: expiry/scheduling is “a new state machine” (§6.7 / complexity controls). Wrong. Pause and `canBuyNow` do not clear the override; the next buy can apply it and skip decay. | Operators cannot leave a forgotten rate under a pause. Buyers do not hit a pre-pause price after empty time. | Foxtrot + lane. Before any reopen runbook is treated as a control. | **P0** |
| **Keep** | Epoch-fixed price + lazy rollover on the first successful buy. | Matches low operator touch. Continuous/VRGDA/SDA is a different product. | Same quote-then-buy loop. First post-boundary buy still writes the new rate. | Already built. | — |
| **Don’t add** | No second RIPE vest. Optional RipeGov only. | See vesting table. Bonus stays at 0 until isolated lots. | Unlocked buyer gets RIPE now. Locked buyer gets a deposit, not a promised calendar unlock. | Product, not a new contract. | — |
| **Change** | Locked buys unavailable when preview would show `isExitFrozen`. Unlocked buys may continue. | Owner decision 6 keeps sales open in bad debt. Fine for unlocked. Wrong for a lock the buyer cannot leave. | Locked path closes in a freeze. Unlocked path still raises cash. | `buyNow` / preview `available`. With the lock bind. | **P1** |
| **Change** | Timelock `setCumulativeMinted`. Do not let it silently rewind issuance. | Immediate rewrite of “how much have we minted” is too sharp for a budget that is the only lifetime supply bound. | Operators reconcile on a delay. Buyers are not suddenly given a larger remaining budget. | Foxtrot. Before activation. | **P1** |
| **Keep** | Full-fill, `expectedEpoch`, `minRipeOut`, `deadlineBlock`, pause, `canBuyNow`, stop-then-start to change token or cadence, no sunset, no keeper. | Standing facility with a hard remaining cap. Partial fills hide the race. | Retry is preview-again. Halt is pause or disable. | Already built. | — |
| **Keep** | Payment-token swap only while stopped. Exact receipt. No payment-token oracle in the contract. | Token identity is an activation/ops problem. The contract should not pretend the token is a dollar. | Stop is the asset-change ceremony. Depeg is pause. | Already built. | — |
| **Remove** | The name “Instant Bond.” | Buyer does not get the dollars back. There is no coupon and, on the unlocked path, no hold. Olympus already stretched “bond.” Unlocked RIPE is a tap. | Marketing and UI say “buy RIPE from the protocol” or “Ripe tap.” | Docs/UI. Anytime. | **P1** |
| **Experiment** | After timing is gone, whether utilization-only steps plus the dead band actually track a comfortable implied price. | Evidence that would settle it: a few dozen live epochs where cap fill and next rate do not systematically cheapen RIPE after last-block or empty-wait behavior. If they do, replace the controller (SDA/VRGDA), do not re-add timing. | — | Post-activation, still not a go-live parameter set. | — |

### Vesting vs lock

Read the recorded policy first: production `maxLockBonus = 0` because RipeGov blends locks share-weighted. That policy is right. A new 1,000-block deposit into a large expired position can collapse to a one-block account unlock. The lane must not pay a bonus for a lock the vault will not keep.

Do not assume the lane holds RIPE. Compare the actual custody choices:

| | Custody | Transferability | Voting | Early exit | What the buyer sees |
|---|---|---|---|---|---|
| Delayed mint | Nothing yet | None | No | n/a | “RIPE later.” Lane must remember a debt. |
| Mint-into-escrow | Escrow / lane | Only if you add it | Only if escrow votes | Only if you add it | “RIPE exists but I can’t use it.” Second vault. |
| Transferable claim | Claim token | Yes | Usually no | Sell the claim | A ticket. Price discovery moves to the ticket. |
| Non-transferable claim | Claim | No | No | Wait or forfeit | A ticket they cannot sell. Closest to v1 vest. |
| Immediate RipeGov deposit | RipeGov, blended | Vault rules | Yes, via points | Live fee / freeze | “Locked,” but the calendar unlock may not match the request. |
| No extra vest (current unlocked path) | Buyer wallet | Full | Only if they later lock | Sell now | RIPE now. This is the ATM path. |

**Don’t add vest.** A hold is justified when the buyer is getting a known discount to a market (Olympus v1, FIP-22, ESPP). This lane has no market price. RipeGov is not a vest: it is an optional deposit into a blender. If dump risk is unacceptable, stop offering unlocked, or wait for isolated lots. Do not build a third clock.

### Expand P0

**1. Bind the lock path.** Add a buyer flag or `minActualLock` / expected-unlocked bit so a previewed unlocked buy reverts if the live floor would lock, and a locked buy reverts if vault ID or actual lock moved against the buyer. Tradeoff: one extra argument and some failed txs when operators change terms mid-period. Precedent: Olympus v2 isolated the lot; ATM binds price, not a surprise lockup. Where it breaks: Ripe lock terms are live on another switchboard, so binding is the only honest handshake. This overrides **rev 24** (“no vault-ID or minimum-lock bindings”) and the recorded reason that preview disclosure is enough. Disclosure is not a bind. The tests are the evidence.

**2. Drop timing.** High-util step uses only how full the cap was. Tradeoff: you lose a claimed “earliness” signal. That signal is fake while the price is flat. Precedent: SDA and VRGDA move price inside the window so time has a cost; ATM does not pretend last prints are a demand clock. Where it breaks: you still leak the period gap until rollover (the docs’ own lag heuristic). That is the price of epoch-fixed, not a reason to reward last-block fills. This overrides **owner decision 18**, **rev 23 “strategically-selectable timing”**, **manifest `timing_is_strategically_selectable`**, and the §6.7 refusal of intra-epoch ramps *as an excuse to keep a gamed timing branch*. I agree with not building ramps. I do not agree with keeping a selectable timing bonus.

**3. Override dies.** Install stays timelocked. Cancel becomes immediate (pause is not enough if someone already queued a bad exact rate). An installed target expires after one unused rollover window or any pause/stop. Better than exact: a bounded nudge around the controller rate so a stale number cannot skip decay. Tradeoff: operators cannot pre-stage a rate weeks ahead. That is the point. Precedent: ON RRP rate is posted and current; DMO does not leave a tap working after the notice window; Bond Protocol markets end. Where it breaks: you still need pause for true emergencies. This overrides **owner decisions 21 and 28** and **§6.7 “no automatic override expiry.”** The recorded reason is complexity. The cheaper thing they chose is a runbook. Runbooks lose to the first successful `buyNow` after an unpause.

---

## 6. Quote matrix

| | Preview reports | Can change after preview | Buy binds | Retry UX |
|---|---|---|---|---|
| Period / rate | Projected epoch and rate, including a projected override | First later buy can commit rollover; override can still be installed or cancelled | `expectedEpoch` | If epoch moved, preview again. Do not resubmit blind. |
| Size | Remaining cap, min payment, remaining mint budget | Another fill, live budget, uncommitted cap change before first fill | Exact `paymentAmount`. Full fill or revert | If “exceeds available,” preview remaining; either shrink or wait for next epoch. |
| Payout | Base / bonus / total RIPE, actual lock | Live min lock, vault terms, bonus ceiling (snapshotted only after first fill) | `minRipeOut`. **Add:** unlocked vs locked, and for locked, min actual lock | If lock path or payout flipped, stop and show the new quote. |
| Destination | Core RipeGov vault ID (disclosure) | Vault pointer can rotate | **Add for locked:** expected vault ID | If vault moved, preview again. |
| Exit / freeze | `canExitEarly`, fee, `isExitFrozen` | Bad debt and RipeGov terms are live | **Add:** reject locked buy when frozen | Show “lock path closed” and offer unlocked if that is still on. |
| Readiness | `available` = unpaused, running, `canBuyNow`, size fits, budget covers, HQ still allows mint | Pause, disable, mint auth, HQ | Implicit: those same gates revert | If `available` was true and buy reverts, read the revert. Wallet, allowance, Endaoment, Teller/vault admission, RIPE pause/blacklist were **never** promised. |
| Time | Not a reservation | Deadline block | `deadlineBlock` | Expired → new quote. |

Preview may fill rate math when `available` is false. That is a quote, not a reservation. Preview and buy may disagree on wallet, allowance, Endaoment liveness, vault admission, RIPE pause/blacklist, and any race on remaining cap. They should **not** be allowed to disagree on unlocked vs locked or on “I bought in this epoch.”

**Override lifecycle if changed**

1. **Queue** — governance starts a timelocked install (exact rate or, better, a bounded nudge).
2. **Activate** — after the lock, execute. Target sits on the lane. Preview shows it for the next epoch. Same-epoch buys do not consume it.
3. **Expire** — if no successful rollover by the expiry, or if the lane is paused/stopped, the target clears. Empty-time decay is not skipped.
4. **Cancel** — immediate, because the emergency is “do not sell at that number,” not “wait out another Foxtrot lock.”
5. **Pause** — still the incident switch. Pause now also disarms the override, so unpause does not fire a pre-pause price.

---

## 7. Open questions

Only these would flip the picked shape or a P0:

1. **Is unlocked RIPE meant to be sold into a live market in size?** If there is no thick market, this is distribution, not an ATM, and the dump argument weakens. If there is a thick market and the posted rate will sit below it, the simpler lane is the wrong shape: either add a real hold (isolated lot, not RipeGov blend) or stop offering unlocked.
2. **Is “when the dollars arrived” actually a goal?** If yes, do not keep epoch-fixed. Build SDA or VRGDA. Do not keep a flat price and a timing statistic.

This is not a go-live call. Calibration, payment-token qualification, and the aggregate mint ledger are still empty in the activation manifest, and they should stay empty until these product choices are settled.
