# Instant Bond Lane design review — Codex

- Date: 2026-08-22
- Branch: instant-bond-lane
- Agent: Codex
- Pin confirmed: d136a262
- Web access: yes

## 1. Exact target

Verified once:

- Commit: \`d136a262f560fe628d7c3f7b667b0220871cb951\`
- Tree: \`2cdcdd6e8f760995f57b05b529100cbcec6d4e5a\`

I reviewed the pinned files through \`git show\`. Web research was available. I made no working-tree, branch, commit, or remote changes.

## 2. Summary and verdicts

Assumed top objective: maximize stable reserve dollars raised per bounded RIPE dilution, with low routine operator touch second. If competitive price discovery becomes the top objective, my recommendation flips to a batch auction.

The direct-sale concept is sound; the current implementation is not yet a sound version of that product.

Ordinary buyer flow today:

1. Approve the payment token.
2. Preview an amount and requested lock.
3. Submit \`buyNow\` with an expected epoch, minimum RIPE output, and deadline.
4. Payment goes directly to Endaoment Funds.
5. RIPE either reaches the wallet or is deposited through Teller into the execution-time core RipeGov vault.

Ordinary operator flow today:

1. Deploy paused and stopped with a payment token and complete controller configuration.
2. Start the lane; the first successful purchase commits the seed rate.
3. Use Foxtrot for configuration and overrides.
4. Immediately enable/disable, stop/start, replace the payment token while stopped, and rewrite \`cumulativeMinted\`.

That last set of controls is much sharper than the product narrative suggests.

Important source/evidence conflicts:

- \`mintBudget\` is not an ultimate lifetime cap. \`setCumulativeMinted\` can lower the counter, including to zero, and restore issuance headroom. A test explicitly exercises that path. Source behavior controls over the implementation-spec claim.
- The activation manifest and qualifier use a stale constructor/“immutable” model. At this commit, genesis and epoch length are installed by \`start\`, the payment token is replaceable while stopped, and Foxtrot dynamically resolves the lane. The qualifier also omits four real economic routes: start, stop, payment-token replacement, and cumulative-counter replacement.
- The activation evidence does not bind the deployed 17-field \`bondConfig\` or Foxtrot’s production delays. It is not reliable readiness evidence for this source.
- The simulator models a versioned, no-overwrite override. The contract implements an unversioned, last-write-wins scalar override. Its controller arithmetic remains useful; its override lifecycle does not describe this commit.
- RipeGov accrues a governance position, but the pinned \`Boardroom.vy\` is explicitly temporary and contains no usable voting flow. I therefore do not credit the locked path with proven executable voting.

One-line verdicts:

- Support the product concept? **Yes, conditionally; not the current control and consent model.**
- Picked shape: **A finite, epoch-posted “RIPE Reserve Sale” with a simpler utilization controller.**
- Top three changes: **Bind buyer settlement consent; make the lifetime issuance cap real and the run finite; remove timing-weighted demand and unavailable-time decay.**
- Vesting: **Do not add it.**
- Override: **Replace the blunt exact override with a delayed, bounded, named-epoch nudge that expires.**
- Keep “Instant Bond”? **No.**
- Epoch-fixed price plus lazy rollover? **Keep.**
- Biggest disagreement: **Revision 24 allows a wallet quote to become a locked vault purchase—or a requested lock to become wallet delivery—without buyer-bound settlement consent. Output slippage protection is not custody consent.**

## 3. Research

For issuance rows, pricing is normalized to payout/native token per unit of payment value. Up means the native token is cheaper; down means it is more expensive.

Buckets:

1. Issuer sells its governance/equity-like token for reserves or LP.
2. Issuer sells a discounted fixed-redemption claim.
3. Issuer spends reserves repurchasing its own token.

| Mechanism | Bucket | Pricing | Delivery / vest / lock | Caps | Operator lever | Durable? evidence | Implication |
|---|---:|---|---|---|---|---|---|
| [Olympus V1 reserve and LP bonds](https://docs.olympusdao.finance/main/contracts-old/equations) | 1 | **Fact:** Payment value per OHM was \`1 + BCV × debt ratio\`; normalized OHM/payment was its inverse. Purchases increased debt and made later OHM more expensive; inactivity decayed debt. | **Fact:** Buyer transferred reserves or LP and received an account-bound OHM receivable with roughly five-day linear vesting and partial redemption. | Max payout, max debt and capacity-like controls. | Policy could change BCV, minimum price, vesting, fees and debt adjustments. | **Observed, project-reported:** Olympus reported over $6.5m of assets and substantial POL acquisition shortly after launch. That proves treasury acquisition, not fair discounts or durable buyer returns. [Launch report](https://olympusdao.medium.com/dai-bonds-a-more-effective-sales-mechanism-c9a57586f1f7) | Strong precedent for capacity, price bounds and emergency close. Weak evidence that vesting is necessary. |
| [Olympus V2 BondDepository](https://olympusdao.medium.com/introducing-v2-bonds-a17c7da298a2) | 1 | **Fact:** Debt decay lowered quote price over time; purchases raised it. Auto-tuning attempted to pace capacity toward conclusion. | **Fact:** Payout was minted and staked at purchase, accrued rebases, and became redeemable at a cliff. Markets supported buyer-relative fixed terms or a common fixed expiry. | Quote- or OHM-denominated capacity, max payout, max debt, conclusion and minimum price. | Policy created/closed markets and set vesting, tuning and capacity. | **Fact:** Public V2 bonds shipped in January 2022. **Unknown:** reviewed official sources do not isolate their long-run economic performance. | Best vesting comparison: locked exposure remained productive. RipeGov achieves that more simply, provided settlement is explicit. |
| [Bond Protocol Sequential Dutch Auction](https://docs.bondprotocol.finance/products/permissionless-bonds/issuers/auction-type) | 1 | **Fact:** Price decays until demand; a purchase moves the next price upward, reducing payout/payment, then decay resumes. | **Fact:** Buyer receives a transferable bond claim: fixed-term ERC-1155 or common-expiry ERC-20, redeemable later. [Tokenization](https://docs.bondprotocol.finance/products/permissionless-bonds/issuers/bond-tokenization) | Capacity, debt buffer, minimum price, conclusion and purchase interval. | Issuer selects quote/payout denomination, vesting type, curve and close controls. | **Observed, project-reported:** the Olympus Pro business preceding the spinout reported more than 50 protocols and nearly $150m bonded. That figure is not specific proof of later SDA efficiency. [OIP-104](https://forum.olympusdao.finance/d/1243-oip-104-deploy-permissionless-op-as-bond-protocol) | Credible when continuous discovery and transferable claims matter. Adds a second asset, maturity UX and timing games that Ripe does not need. |
| [Olympus inverse bonds](https://docs.olympusdao.finance/main/legacy/bonding) | 3 | Opposite direction: an OHM holder sold OHM to the treasury for reserves. | Immediate reserve delivery; no vesting claim. | Weekly/daily capacity and reserve-spend limits. | Policy changed reference prices, capacity and market availability. | **Observed, project-reported:** the seven-month program spent about $82m acquiring 32,500 gOHM before being replaced by RBS. [Q4 report](https://storage.googleapis.com/olympusdao-landing-page-reports/quarterly-reports/Olympus_Q4_Quarterly_Review_2022.pdf) | Contrast only. Issuance and buyback need separate mandates and accounting. |
| [Frax 2021 FXS Olympus Pro program](https://gov.frax.finance/t/fip-22-olympus-bond-program-with-fxs/130) | 1 | V1-style debt pricing: demand reduced normalized FXS/LP value; inactivity increased it. | **Fact:** Buyers deposited targeted LP and received discounted FXS over a 14-day linear vest. | Proposed allocation was 90,000 FXS monthly with a preferred average discount below 10%. | Olympus managed market parameters for a fee; Frax selected budget and target LP. | **Observed, project-reported:** a later Frax proposal attributed about $5m total bonded value to Olympus Pro. [FIP-51](https://gov.frax.finance/t/fip-51-olympusdao-ohm-frax-uni-v3-gauge/854) | Shows discounted governance-token issuance can acquire POL. It does not prove the 14-day claim improved alignment or economics. |
| [Later Frax FXB](https://docs.frax.finance/frax-v3-100-cr-and-more/fxbs) | 2 | Auction price moves toward a floor; lower FRAX/FXB means more FXB claim per FRAX. Purchases create price/size pressure. | Buyer receives transferable FXB immediately and can redeem it 1:1 for FRAX at maturity. It carries no FXS governance vote. | Series-specific issuance caps and maturities. | Operator controls series, quantity, price curve, floor and expiry. | **Fact:** Multiple series and secondary integrations shipped. **Unknown:** sources reviewed do not establish auction efficiency or utilization-adjusted returns. | FXB is economically bond-like because it promises fixed redemption. Instant Bond Lane does not. |
| [Gnosis EasyAuction](https://github.com/Gnosis-Auction/auction-contracts) | 1 | Buyers submit quantity and maximum-price bids; accepted orders clear at one uniform price. | Buyer waits for settlement, then claims tokens or refund. No automatic vesting. | Fixed sale inventory, minimum price, closing time and concentration rules chosen by issuer. | Issuer creates discrete auctions and may set cancellation/settlement boundaries. | **Observed, project-reported:** the repository reports more than $20m distributed through IDOs. Independent evidence of optimal clearing is limited. | Best different model if transparent price discovery and allocation outweigh instant delivery. |
| [Balancer LBP](https://medium.com/balancer-protocol/building-liquidity-into-token-distribution-a49d4286e0d4) | 1 | Changing pool weights mechanically lower price over time; purchases push it upward. | Immediate transferable token plus ongoing AMM liquidity. | Finite inventory and sale window. | Operator sets weights, duration, starting liquidity, fee and pause. | **Observed, project-reported:** Balancer reported Radicle raised 24.73m USDC in a two-day LBP. | Rejected for this lane: it makes buyer timing central and imports AMM, MEV, inventory and manipulation risk. |
| [ATM equity program](https://www.sec.gov/Archives/edgar/data/1861622/000149315225024695/form424b5.htm) | 1 | Shares sell at prevailing market prices; normalized shares/cash varies with the external market. | Buyer receives ordinary common stock, without a special public-sale vest. | Aggregate authorization, daily limits, minimum sale price and program expiry. | Issuer controls sale notices, timing, quantity, floor and termination. | **Observed:** Realty Income reported $1.743bn of ATM net proceeds in 2024 and expected to replenish the program. [10-K](https://www.sec.gov/Archives/edgar/data/726728/000072672825000055/o-20241231.htm) | Closest ordinary-finance analogue. Borrow its finite authorization and monotonic sold-to-date accounting, not its live pricing without a trustworthy RIPE market. |
| [Treasury single-price auction and reopening](https://www.treasurydirect.gov/help-center/faqs/additional-auction-related-faqs/) | 2 | Competitive bidders submit yields; all accepted bidders receive the stop-out-equivalent uniform price. | Buyer receives a standardized transferable debt claim with fixed maturity. | Noncompetitive limits, 35% competitive award cap, stated offering size and close. | Treasury chooses security, amount, timing and reopening schedule. | **Observed:** the U.S. Treasury has used single-price auctions across marketable securities since November 1998. [Reopenings](https://treasurydirect.gov/auctions/when-auctions-happen/schedule-auction-reopenings/) | Strong batch plumbing, but durability depends on a standardized fixed claim and deep secondary market—not applicable RIPE valuation evidence. |
| [Rights offering](https://www.sec.gov/Archives/edgar/data/875355/000110465926016867/tulp-20260218x424b3.htm) | 1 | Existing holders receive a pro-rata right to buy at a fixed price or formula. Excess demand may be prorated. | Purchased shares become ordinary equity; rights may be transferable or non-transferable. | Record date, holder entitlement, offer size and closing date. | Issuer may extend, terminate and define over-subscription rules. | **Observed:** Empire Petroleum reported two 2024 offerings raising about $20.7m and $10m gross. [Annual report](https://www.sec.gov/Archives/edgar/data/887396/000107261325000316/empannual2024.pdf) | Correct model only if incumbent-holder protection outranks permissionless distribution. Do not bolt pro-rata rights onto this lane. |
| [ESPP and IPO lockup](https://www.irs.gov/faqs/capital-gains-losses-and-sale-of-home/stocks-options-splits-traders/stocks-options-splits-traders-4) | 1, weak analogy | ESPPs commonly use a market discount and contribution limits. | ESPP tax holding periods are not necessarily enforced transfer locks. IPO lockups ordinarily restrict insiders, not new public buyers. [Lockup explanation](https://www.investor.gov/introduction-investing/investing-basics/glossary/initial-public-offerings-lockup-agreements) | Payroll/share caps or contractual insider restrictions. | Employer/underwriter defines eligibility and period. | **Unknown:** these sources do not establish that an extra public-buyer hold improves alignment. | Rejected precedent for mandatory buyer vesting. The participants, purpose and legal mechanics differ. |
| [Corporate bond and CD](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/what-are) | 2 | Price/yield reflects a promised principal and interest claim. | A bond promises principal at maturity, usually with interest; a CD posts a rate/term and generally charges an early-withdrawal penalty. [CFPB](https://www.consumerfinance.gov/ask-cfpb/what-is-a-certificate-of-deposit-cd-en-917/) | Principal, maturity, rate and often issuance/deposit limits. | Issuer sets contractual claim terms. | These are durable product classes precisely because the buyer’s redemption claim is explicit. | Decisive naming contrast: locking an equity-like token does not turn it into a bond. |

Synthesis:

- **Olympus-to-Bond lineage:** Olympus V2 already used debt decay, purchase-driven price increases, pacing and auto-tuning. OIP-104 spun the Olympus Pro team and a new permissionless system into Bond Protocol, which subsequently formalized the generalized mechanism as an SDA. That is a supported product lineage. It would be an overclaim to call Olympus V1 “SDA” or attribute first inventorship conclusively.
- **ATM issuance** changed the recommendation most: keep a finite authorization, hard end, monotonic sold-to-date accounting, minimum acceptable economics, and immediate close.
- **Olympus, Bond Protocol and Frax** validate capacity-based issuance, not the economic optimality of discounts or vesting.
- **Gnosis and Treasury auctions** establish the credible alternative if price discovery or fair allocation becomes primary.
- **FXB, corporate bonds and CDs** settle the naming question: a maturity and redemption claim make a bond; a RIPE lock does not.
- **Balancer LBP** is rejected because it amplifies precisely the timing and market-manipulation exposure this design should avoid.
- **Rights offerings** become relevant only if protecting existing holders becomes the first objective.
- **Inverse bonds** belong to a separate reserve-spend policy, not this issuance lane.

## 4. Three product shapes

### Current lane as-is

The buyer gets instant settlement and a simple-looking fixed quote, but “available” does not mean executable, settlement mode can change, and the quote does not identify the sale lifecycle. The operator appears low-touch, yet immediate restart, token replacement, cumulative-counter reset and persistent override create substantial hidden discretion. Issuance discipline is not real because the purported lifetime counter can be lowered.

### Simpler lane — picked

The buyer sees one posted price for the epoch, exact payment asset and recipient, remaining capacity, and an explicit wallet-or-RipeGov settlement commitment. Price moves only from completed utilization, not purchase timing, and unavailable periods do not count as weak demand. The sale has a genuine lifetime cap and finite end. Emergency closing remains immediate; opening and economic changes are delayed and versioned. This keeps no-keeper lazy rollover with much clearer economics.

### Uniform-price batch auction

The buyer submits a maximum payment-per-RIPE bid, waits for close, then receives a pro-rata fill or refund at one clearing price. Each auction has an explicit inventory and deadline. It provides better price discovery and allocation visibility, but introduces bidding, cancellation, clearing and claim UX, plus recurring auction setup. Pick this if large one-off size or competitive price discovery outranks instant delivery and low operator touch.

## 5. Decision register for the simpler lane

| Keep / change / remove / experiment | Decision | Why | Buyer / operator effect | Surface and timing | Priority |
|---|---|---|---|---|---|
| Keep | No separate vesting. Keep wallet delivery and explicit optional RipeGov settlement; keep lock bonus at zero. | The reserve-sale objective does not justify a second claim asset. RipeGov is an account-level blended lock, not isolated vesting. | Immediate RIPE or knowingly selected vault position; no claim/redemption workflow. | Product policy and UI now. Do not activate bonus without isolated, measurable lock economics. | P1 |
| Change | Replace exact persistent override with one bounded, delayed, named-epoch nudge. | Today’s override can carry stale intent indefinitely and silently replaces controller output. | Preview shows controller rate, final rate and source; operator gets a controlled exception without an open-ended rewrite. | Lane and Foxtrot before production use. | P1 |
| Change | Keep epoch-fixed/lazy rollover; replace amount-weighted timing with utilization-only movement and no decay during unavailable periods. | Timing at an unchanged price is not willingness-to-pay. Unavailable time is not weak demand. | Easier quote; less strategic waiting. Operator sacrifices some automatic cap-clearing aggressiveness. | Controller, simulator and calibration before production use. | P1 |
| Change | Bind sale lifecycle, payment asset, recipient and settlement outcome. Split \`marketOpen\` from deterministic \`settlementReady\`. | Output slippage does not protect custody, lock duration or vault choice. Current \`available=true\` can describe a currently impossible purchase. | Material changes require re-consent; deterministic failures are surfaced earlier. | ABI, Lane events, SDK and UI before production use. | P0 |
| Change | Make cumulative issuance monotonic, add a hard run end, delay reopen/token changes, version configuration, and gate locked buys during exit freezes. Keep immediate close and full-fill. | Current recovery controls can reopen dilution and restart seed pricing. Numeric epoch IDs also collide across runs. | Stronger issuance assurance; slightly slower operator recovery. Capacity races still re-preview rather than fill silently. | Lane, Foxtrot and qualification evidence before production use. | P0 |
| Change | Public name: **RIPE Reserve Sale**. The internal contract name may remain if ABI continuity matters. | There is no debt, principal, interest, maturity or fixed redemption. | Buyers receive an accurate expectation: primary token sale, optionally locked. | Documentation and UI immediately. | P2 |

### Vesting comparison

| Option | Custody | Transferability | Voting | Early exit | What the buyer sees |
|---|---|---|---|---|---|
| Delayed mint | No RIPE exists yet; protocol records a future obligation. | Usually none. | No RIPE vote before mint. | Normally none. | Claimable amount and countdown, plus future-mint risk. |
| Mint into escrow | Escrow holds minted RIPE. | None unless another claim token is added. | Only if the escrow explicitly supports delegation. | Policy-defined. | Escrowed, vested and claimable balances. |
| Transferable claim | Claim token in buyer wallet; backing sits in escrow or future mint authority. | Claim is tradable. | Usually no RIPE vote before redemption. | Sell the claim on a secondary market. | A separate asset, maturity and market discount. |
| Non-transferable claim | Contract records an isolated entitlement. | None. | Normally none. | None unless cancellation is designed. | Purchase-specific release schedule. |
| Immediate RipeGov deposit | Live core vault holds RIPE; buyer receives an account-level position. | Underlying RIPE is unavailable until withdrawal. | RipeGov points accrue, but executable Boardroom voting is not established at this commit. | Fee-, holder- and bad-debt-freeze-dependent. | Vault shares, blended account lock, exit fee and freeze state. |
| No extra vesting | Buyer wallet holds RIPE. | Immediate. | Ordinary RIPE rights only; no added lock-based vote. | Immediate liquidity. | Standard RIPE balance. |

Recommendation: use the last two choices only, selected explicitly by the buyer. Do not represent the RipeGov path as vesting: its duration blends with existing shares, early exit may be charged or frozen, and \`actualLock\` is not the buyer’s final account-level unlock.

### Highest-priority change 1: buyer-bound quote and settlement

What changes:

- Add a monotonic \`runId\` and \`configVersion\`.
- Bind payment-token address and payment recipient.
- Require settlement mode: \`UNLOCKED_ONLY\`, \`LOCKED_ONLY\`, or deliberately flexible.
- For locked settlement, bind expected vault and acceptable deposit-duration range—preferably exact duration.
- Preview the projected blended account unlock, not merely the new deposit duration.
- Bind maximum exit fee and whether a currently frozen exit is acceptable.
- Surface controller rate, final rate and whether governance changed it.

This rejects Revision 24’s decision to omit buyer-bound vault/lock terms and rely on \`minRipeOut\`, live minimum-lock policy and the all-in payout ceiling. Those controls constrain quantity; they do not constrain what claim the buyer receives.

Tradeoff: more calldata, more quote invalidations and a larger SDK surface. That is justified because wallet RIPE and a frozen vault position are materially different products.

ATM placement instructions support binding asset, timing, floor and capacity, but the analogy ends at consent: an on-chain vault introduces custody and execution-state risks absent from ordinary share settlement.

### Highest-priority change 2: real issuance authorization and lifecycle discipline

What changes:

- Remove runtime \`setCumulativeMinted\`; if migration reconciliation is unavoidable, allow only a one-time, stopped, timelocked, monotonic increase.
- Add a mandatory end block to each run.
- Immediate actions: pause, disable, stop and cancel an unused override.
- Delayed actions: start/reopen, payment-token replacement, config activation, budget increase and counter reconciliation.
- Every start creates a new \`runId\`; epoch numbers are scoped to it.
- Require nonzero production delay and config-version compare-and-swap.
- Keep epoch length fixed within a run; change it only through a new delayed run.
- Reject new locked purchases during a RipeGov exit freeze unless the buyer expressly permits it. Unlocked purchases may remain available if reserve policy allows.
- Treat the payment token by address and qualification status—not generically as “a dollar.” A depeg should trigger pause/re-authorization, not an automatic DEX-priced controller.

This rejects the recorded “no hard sunset” choice and the claim that \`mintBudget\` is the ultimate cap. Even a correctly monotonic quantity cap would not bound stale token qualification, price assumptions or governance authorization over time.

Tradeoff: operators lose same-block recovery and must plan extensions. That is appropriate for reopening dilution. ATM programs and Treasury offerings support finite authorization, while on-chain mutability requires even stronger accounting because there is no transfer agent independently maintaining sold-to-date records.

### Highest-priority change 3: simpler controller

What changes:

- Keep one fixed price per epoch.
- Keep rollover in the first subsequent purchase; no keeper is needed.
- Use total accepted payment/utilization only. Splitting transactions then has no pricing effect.
- High utilization lowers \`rate\`, making RIPE more expensive; low utilization raises it; a neutral band holds.
- Apply empty-epoch decay only to epochs during which the sale was continuously eligible.
- Pause, disable, exhausted budget or lost mint permission must hold/reset the demand clock rather than masquerade as weak demand.
- Keep hard minimum/maximum rate and all-in payout bounds.
- Do not automatically import a DEX price. Use independent monitoring and pause/re-authorization.

This overrides the recorded timing-weighted high-utilization decision. Its stated advantage is split resistance and treating earlier demand as stronger evidence. Gross utilization is already split-resistant, and at a fixed price an early buyer has not expressed greater willingness to pay than a late buyer. A dominant buyer can wait until the last block and deliberately minimize the next increase.

Tradeoff: the lane becomes less aggressive about clearing its cap by deadline. Olympus/Bond Protocol show that time decay can improve pacing, but also demonstrate timing-sensitive buyer behavior. If deterministic cap clearing becomes primary, the correct response is an auction or SDA—not a strategically selectable pseudo-signal inside a fixed-price epoch.

## 6. Quote matrix and override lifecycle

A quote should be a conditional, buyer-bound offer—not a reservation. It can promise bound terms if the transaction succeeds; it cannot promise block inclusion or external token/vault liveness.

| Surface | What preview reports now | What can change | What buy binds now | Retry UX in the picked shape |
|---|---|---|---|---|
| Sale identity | Numeric epoch, computed market state and deadline context. | Stop/restart can recreate the same epoch number with a new seed, token or config. | \`expectedEpoch\` and \`deadlineBlock\`; no run/config identity. | Refresh automatically, but require confirmation when \`runId\`, token, recipient or config changes. |
| Price and capacity | Rate, RIPE output and market-level cap/budget availability. | A rollover or competing purchase can alter epoch/capacity. | Payment amount and \`minRipeOut\`; full-fill only. | If capacity shrank, show the new maximum and ask for a newly signed amount. Do not silently partial-fill. |
| Settlement | Requested/actual lock and currently resolved vault. | Minimum lock, core vault, exit fee, freeze state and blended account unlock can change. | Only \`requestedLock\`; no settlement mode, vault or effective-lock bound. | Never auto-retry across wallet/locked mode or vault changes. Show the changed custody terms and require fresh consent. |
| Protocol readiness | A single \`available\` result covering only market-level checks. | RIPE pause/blacklist, vault admission, Teller state, HQ minting and bad debt may make execution impossible. | No readiness snapshot. | Rename to \`marketOpen\`; add \`settlementReady\` and reason bits. Re-preview after protocol-state errors. |
| Wallet/external execution | Does not establish balance, allowance or every recipient/token transfer behavior. | Balance, approval, transfer hooks and recipient behavior. | ERC-20 execution succeeds or the transaction reverts atomically. | Run an immediate \`eth_call\` preflight; distinguish approval/balance failures from repricing. Do not describe this as guaranteed availability. |

Override lifecycle:

1. **Queue:** timelock \`{runId, configVersion, targetEpoch, signed bounded nudge}\`.
2. **Activate:** only after the nonzero delay and only if lifecycle/config still match.
3. **Apply:** exactly once to the named rollover; preview exposes controller rate, final rate and source.
4. **Expire:** automatically if the target epoch passes, the run/config changes, or the sale closes.
5. **Cancel:** immediate before application, with a clear event.
6. **Pause:** immediate and invalidates the queued/active override so stale intent cannot survive reopening.

This rejects §6.7’s rationale that target and expiry create an unnecessary state machine. The existing indefinite one-shot override is already stateful; it simply has weaker stale-intent controls.

## 7. Open questions

1. Is competitive price discovery or pro-rata allocation actually more important than instant delivery and low operator touch? If yes, choose the uniform-price auction shape.
2. During RipeGov bad debt, do Endaoment sale proceeds directly repair the condition freezing exits? If not, locked purchases should close automatically; if they do, explicit frozen-exit consent may be defensible.
3. Is executable governance participation a core purpose of the locked path? If yes, usable voting integration and precise account-level lock disclosure must exist before the product markets a governance benefit or activates a lock bonus.

No files or repository state were changed. Prior memory was used only to target likely review areas; potentially stale historical conclusions were not treated as current evidence and were rechecked against the pinned source.
