# Instant Bond Lane design-review synthesis

- Date: 2026-08-22
- Branch: instant-bond-lane
- Sources: agent-Codex.md, agent-DeepSeek.md, agent-GLM.md, agent-Ox.md, agent-claude.md, agent-grok.md
- Pins seen: d136a262

Agent map (letter → saved memo):

| Letter | Agent | File |
|---|---|---|
| A | Claude | agent-claude.md |
| B | Codex | agent-Codex.md |
| C | Grok | agent-grok.md |
| D | GLM | agent-GLM.md |
| E | DeepSeek | agent-DeepSeek.md |
| F | Ox | agent-Ox.md |

All six complete reviews used commit `d136a262f560fe628d7c3f7b667b0220871cb951` and tree `2cdcdd6e8f760995f57b05b529100cbcec6d4e5a`. All had web access. Counts below are descriptive, not votes. Silence is “no position,” not opposition; qualified or experimental support is marked rather than promoted to a launch recommendation.

The durable consensus is that a small, capped, keeper-free primary RIPE sale is a sound concept; it should not add a separate vesting rail at launch, should not be called a bond, and should retain epoch-fixed pricing with lazy rollover. The real owner calls are the acceptable-price/ceiling policy, buyer settlement consent, the controller’s timing signal, override semantics, and whether the issuance authorization is truly finite or merely governed.

## 1. Scoreboard

| Verdict | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Pin | `d136a262` / `2cdcdd6e` | Same | Same | Same | Same | Same |
| Web access | Yes | Yes | Yes | Yes | Yes | Yes |
| Assumed top objective | Issuance discipline first: prevent below-market leakage; reserves and low touch follow | Maximize reserve dollars per bounded dilution; low touch second | Raise Endaoment dollars with hard caps and almost no babysitting | Protected-price distribution, then hard cap, then low touch | Raise Endaoment dollars with bounded dilution and near-zero touch while preserving holder quality | Modest distribution to real demand at non-distressed prices; reserves second and low touch third |
| Support concept | Yes after product/control fixes; not as a bond | Yes conditionally; current consent/control model is unsound | Yes | Yes | Yes | Yes |
| Picked shape | Simpler lane: one-step ratchet and ceiling-as-control | Finite epoch-posted “RIPE Reserve Sale” | Simpler standing tap | Current lane plus optional override expiry; timing experiment | Current lane plus bounded changes and experiments | Simplified current lane |
| Vesting | Do not add | Do not add | Do not add now; reconsider only if visible discount makes a real hold necessary | Do not add | Do not add now; add a calibration gate | Do not add |
| Override | Retain exact one-shot; no installed expiry; immediate installed cancel; install before first epoch; bounded nudge is an experiment | Delayed bounded named-epoch nudge; expiry; immediate cancel; pause invalidates | Short-lived lever, preferably bounded; immediate cancel; pause/stop/unused time invalidate | Exact one-shot with optional expiry; timelocked cancel; pause preserves | Exact one-shot with governed maximum lead; timelocked cancel; pause preserves | Relative bounded nudge with expiry; timelocked cancel; pause preserves |
| Keep name | No; rename full technical/public surface | No; public rename, internal continuity optional | No | No; rename full surface | No; rename full surface | No; rename full surface |
| Epoch-fixed + lazy rollover | Keep | Keep | Keep | Keep | Keep | Keep |

### Top three and biggest recorded-decision disagreement

| Agent | Top three | Biggest recorded-decision disagreement |
|---|---|---|
| A | One-step ratchet plus ceiling as the real control; “unlocked means unlocked” plus Teller/UI; harden immediate controls | Revision 24 silently removed the selected minimum-actual-lock binding |
| B | Bind settlement consent; make issuance/run genuinely finite; remove timing and unavailable-time decay | Revision 24 treats output slippage as custody consent |
| C | Bind lock mode; remove timing; make override die on pause/unused time | Decision 18 keeps buyer-selected timing at a flat price |
| D | Add override expiry; rename; test timing simplification | §6.7 materially overstates expiry complexity |
| E | Add override freshness; harden and timelock the mint counter; launch unlocked-only | Decisions 21/22 permit an exact override to fire arbitrarily late |
| F | Remove timing; use a relative bounded override; rename | Decision 18 retains a signal activation must treat as contributing zero |

Agreement:

- All six support the concept, retain the epoch-cap, nominal-budget and ceiling layers, and reject a new vesting contract at launch.
- All six keep `maxLockBonus = 0` until isolated lock lots exist.
- All six keep epoch-fixed pricing, first-buy lazy rollover, full-fill-or-revert, and no quote reservation.
- All six reject an on-chain market-price or depeg oracle at launch.
- All six rename the public product away from “Instant Bond.”

Material splits:

- A/B/C/F simplify or neutralize the timing signal; D keeps it provisionally but makes simplification a top experiment; E keeps the current controller.
- B/C want full on-chain custody bindings now. A picks a narrower zero-requested-lock guarantee plus Teller/UI. E gates the locked path and binds it later. F accepts binding or explicit UI consent. D records no change.
- B/C/E/F require installed-override freshness; D adds optional expiry; A expressly keeps installed targets without expiry.
- A/B/C want immediate installed-override cancellation. Only B/C clear it on pause; A/D/E/F preserve it through pause.
- A/B require monotonic mint accounting; E requires non-decrease while running with stopped, timelocked downward correction. B/C/E/F delay or constrain reconciliation. D retains the current resettable tool.
- B alone requires finite, versioned runs. A/C/D/E/F keep no calendar sunset.
- A alone makes periodic off-chain re-ratcheting of `maxEffectiveRate` a launch policy and treats the ceiling—not the controller—as the binding price protection.

Objective explains part of the split:

- B/C/E begin with fundraising and reserve accumulation.
- D/F begin with distribution quality and non-distressed pricing.
- A begins with a minimum acceptable sale price and the leakage created while a volume-only controller catches up.
- B would choose a batch auction if discovery became primary; C/F would choose a moving-price model if arrival time or much larger size became primary; A would schedule a reference-priced model only after a trustworthy reference exists.

## 2. Research they used

Bucket 1 means the issuer sells its governance/equity-like token; bucket 2 means a fixed-redemption claim; bucket 3 means a buyback. “C” means a contrast whose bucket does not map cleanly to the lane.

| Mechanism | Agents | Bucket | Their evidence label | Changed a rec? | Notes |
|---|---|---:|---|---|---|
| Olympus v1 reserve/LP bonds | A–F | 1 | Shipped mechanics treated as fact; treasury growth observed/project-reported; vesting benefit disputed | Yes | A found a merge/reset footgun and supply-denominated capacity loop requiring emergency reset; C/E condition future vesting on visible discount; D/F reject decorative vesting; A derives a bounded-nudge experiment |
| Olympus v2 BondDepository | A–F | 1 | Shipped mechanics fact; long-run effectiveness thin or unknown | Yes | Isolated fixed-term/expiry claims inform the lock debate; no memo establishes RipeGov blending as equivalent |
| Olympus Pro → Bond Protocol SDA/FPA/OFDA | A–F | 1 | Mechanics shipped; lineage language and current commercial durability disputed | Yes | Credible discovery alternative, frozen-market terms, floors/caps, and a warning against importing the larger parameter/claim surface |
| Frax FIP-22 FXS via Olympus Pro | A,B,C,E,F | 1 | Proposal terms fact; outcome figures differ by contract, period, and denominator | Yes—strongly | A’s on-chain scan found ~17.8% weighted discount and 40–55% blowouts; it drove the ceiling policy and rejection of per-tx caps |
| Olympus inverse bonds | A–F | 3 | Deployment fact; effectiveness/current-use claims conflict | Contrast | Opposite direction; reinforces small caps and separate issuance/buyback mandates |
| Olympus Range-Bound Stability | A | 1/3 | Mechanics fact; retunes/shutdown observed; absence of sales partly inference | Yes for A | Disciplined sellers often idle; stranding can be normal rather than a liveness failure |
| Olympus Emissions Manager / Convertible Deposits | A,C; E reviewed §5.1 | 1 | Mechanics fact; realized reserve outcome unknown | Mostly rejected now | A uses it as the later reference-priced shape; C rejects the oracle dependency; E supports the caps-over-sophistication conclusion |
| Frax FXB | A–F | 2 | Redemption mechanics fact; efficiency/success disputed | Mostly contrast | True debt-like claim settles naming; A’s zero-fill rounds show an off-market bound can strand a facility |
| GDA/VRGDA | A,C,D,E,F | 1/C | Formula fact; schedule/economic success uncertain and disputed | Yes | C/F: real arrival-time information requires a moving price; A rejects unbounded/no-floor behavior; D/E treat catch-up as a calibration comparison |
| Balancer LBP | A,B,C,E | 1 | Mechanics shipped; buyer outcomes mixed or inferred | Yes—rejected | Adds AMM/MEV/timing exposure; A also uses it as no-vesting and boundary-capture evidence |
| Gnosis/EasyAuction batch | A,B,E | 1 | Mechanics fact; B reports historical project adoption, E calls it a standard IDO rail, and A infers the governance-token venue is now effectively dormant | Conditional | B’s preferred discovery alternative; E rejects the loss of instant settlement; A reserves it for occasional large tranches |
| Maker flop/debt auction | A,C | 1 | Crisis mechanics/use observed; failures and policy lessons attributed | Yes | Supports hard bounds; C uses it against selling new locked positions during a freeze |
| Maker/Sky Smart Burn Engine → BEAM | A | 3 | Buyback mechanics fact; repeated retuning and bounded-module adoption observed | Yes for A | Operators will touch the lane more than the docs imply; a bounded lever is a later experiment |
| Sky/Aave/Hyperliquid buybacks | A | 3 | Buyback direction and periodic caps documented; continuing re-parameterization observed | Context for A | One-sided governance-token selling is exceptional; hard bounds carry the safety case |
| Fei Genesis/bonding curve | A | 2 (+1 component) | Contract mechanics fact; launch outcome/failure observed | Yes for A | Supports small epoch caps, full-fill, and no exit friction |
| Basis Cash bonds / ESD coupons | A | 2 | Claim mechanics fact; failure and buyer withdrawal observed | Naming | “Bond” can imply repayment that does not exist |
| ATM equity issuance | A,B,C,E,F | 1 | Standard structure fact; issuer use and idle capacity observed | Yes—materially | A: ceiling and accepted idleness; B: finite authorization; C: market pricing/halt; E: size versus liquidity; F: immediate controls/no sunset |
| ESPP | A,B,C,D,E; F uncited context | 1 | Statutory terms fact; holding/alignment conclusions differ | Mixed | A says permissionless caps are Sybil-defeated; C/E condition holds on observable discount; D uses cadence; B treats it as a weak public-sale analogy |
| Discount DRIP | A,D; F uncited context | 1 | A has observed multi-account arbitrage; D uses standard-practice context | Limited | A: once RIPE is liquid, a below-DEX lane is a discount DRIP and address caps can be arbitraged; D: a DRIP lacks total issuance control |
| Rights issues / offerings / pre-emption practice | A,B,D,E; F uncited rights context | 1 | A/B/D cover rights; E covers UK non-pre-emptive placings; F’s analogy is uncited | Limited | Relevant to float-relative size, holder protection, claim surfaces and aggregate disclosure |
| PIPEs / Nasdaq below-market rules | A | 1 | Legal discount rules fact; unlock effects observed | Yes for A | Discount and lock are jointly priced; supports a market-linked ceiling and no expectation that an unbonused lock shapes holders |
| IPO lockups | A,B,F | — | A/F use empirical unlock effects; B calls the analogy weak | Yes for A/F | Reinforces avoiding a manufactured unlock overhang |
| Treasury uniform-price auctions | A,B,E | 2/C | Mechanics fact; A/B date single-price adoption to Nov. 1998, while E makes a broader “standard for a century” claim | Conditional | Credible batch plumbing; waiting and standardized claims limit relevance |
| UK DMO gilt taps | A,C | 2/C | Operational notices fact; exceptional use observed | Yes | Supports prospective, short-lived interventions rather than stale standing intent |
| Medium-term note programs | A | 2/C | Posted-rate, daily-order and prospective-term practice treated as fact | Yes for A | Supports prospective governance terms rather than changes that affect a running epoch |
| US I/EE savings bonds | A,C,D | 2 | Product rules fact; durability and boundary demand observed | Cadence/naming | Posted-period rates support epoch cadence; repayment claims show why this lane is not a bond |
| NS&I | A | 2 | Posted savings-product rules used as ordinary-finance comparison | Cadence | Reinforces prospective, published terms |
| Central-bank standing facilities, capped ECB tenders, TAF | A | C | Rules fact; overbidding/abandonment and floor behavior observed | Yes for A | Below-market posted price plus a cap creates an opening rush; the floor/ceiling becomes the price |
| ECB fixed-rate full allotment | F | C | Adoption/retention fact | Yes for F | Unlimited quantity is the crucial difference from A’s failed capped-tender precedent |
| Fed ON RRP | C | C | Mechanics and daily use fact/observed | Yes for C | A posted rate is fine; stale intent surviving a halt is not |
| Corporate bonds / CDs | B; F uncited CD context only | 2 | B uses authoritative definitions; F mentions CDs only as uncited context | Naming | Principal, maturity, interest and redemption—not a token lock—make a bond |
| Claim-delivery rails: streams, PTs, ve/veNFTs, Stargate | A | 1/C | Mechanics fact; Stargate dispute/reversal observed | Yes for A | Extra claims re-price the discount; account-level blended locks are inferior to isolated lots |
| Aave stkAAVE/GHO discount | D | C | Active utility observed | Context | Supports keeping lock-bonus arithmetic dormant; distinct from A’s Aave buyback row |

Research conflicts to preserve:

- Do not standardize the claim that Olympus v1 “was an SDA.” A/B/C distinguish the historical mechanism from later terminology; D/F use a more direct lineage; E’s organizational-lineage evidence is partly indirect.
- “Shipped” is not “economically successful” or “currently durable.” This matters for Bond Protocol, FXB, inverse bonds, VRGDA, and Gnosis.
- All six reject vesting at launch, but for different reasons: footguns and tradable-claim repricing (A), weak necessity evidence (B), discount-dependent dump protection (C/E), simplification (D), and mercenary/unlock-overhang concerns (F).
- Frax totals must not be averaged: A’s ~$5.95m scanned contract, B’s ~$5m project report, C’s ~$1.6m forum figure, and F’s >$45m Olympus-Pro aggregate use different scopes.
- A’s Frax evidence says vesting did not prevent price leakage; C/E treat the vest as intentional dump protection; B says the program does not prove improved alignment.
- ATM precedent does not settle lifecycle policy: B derives finite runs, F derives no sunset, A derives disciplined idleness, E derives liquidity-relative sizing, and C derives market pricing plus rapid halt.
- Inverse-bond status is materially disputed: A/B say the program ended after seven months when RBS launched; C calls floor effectiveness unknown; D calls it still used/effective; E labels effectiveness inference; F calls use episodic.
- Treasury-auction duration is also scoped differently: A/B anchor single-price adoption to November 1998, while E uses a broader century-long characterization.
- A’s capped ECB tender and F’s full-allotment facility are opposite quantity regimes and cannot be merged into a generic endorsement.
- A’s Aave buyback example and D’s stkAAVE/GHO utility example are different mechanisms and remain separate.

## 3. Product shapes

| Cluster | One-sentence shape | Picked by |
|---|---|---|
| Current lane, bounded changes | Preserve the controller and buyer flow; add override freshness and selected counter/lock hardening without changing the mechanism family | D, E |
| Simpler posted-rate lane | Preserve the two-contract architecture, existing bounds, epoch clock and lazy rollover while neutralizing timing and reducing settlement/control discretion | A, B, C, F |
| Different model | Batch auction, SDA/VRGDA, or reference-priced drip only if discovery, arrival time, trusted market reference, or much larger issuance becomes primary | Nobody under the assumed objectives |

The simpler picks are not interchangeable. A uses equal endpoints, an actively maintained ceiling and narrow lock invariant. B adds finite versioned runs and broad identity/custody bindings. C clears timing and stale override state. F uses a relative override and accepts either ABI binding or explicit UI consent.

## 4. Option register

Qualified support is written in the relevant cell. Priority signal counts only agents who put that distinct option in their explicit top three.

| Topic / option | For | Against | No position | Why and tradeoff | Buyer / operator effect | Surface and timing | Priority signal |
|---|---|---|---|---|---|---|---:|
| No separate vesting at launch | A–F; C/E condition future reconsideration on evidence | — | — | A second claim/clock has no demonstrated launch benefit; causal reasons differ | Immediate wallet RIPE or existing vault path | Product policy now | 0 |
| Formal future vesting calibration gate | E; C qualified | — | A,B,D,F | Preserves a future dump brake if sustained market discount or primary distribution becomes real | Could later add isolated custody/unlock overhang | Calibration/owner gate; no launch code | 0 |
| Keep `maxLockBonus = 0` until isolated lots | A–F | — | — | Current account-level blending cannot price an honest lot-specific lock | No paid incentive for a duration the vault cannot promise | Activation policy | 0 |
| Preserve optional RipeGov exposure in some form | B,C,D,F; A via post-purchase Teller; E only after isolated lots/bindings | — | — | Avoids a new custody rail, but account-level blending is not isolated vesting | Buyer may choose wallet or a disclosed vault position | Product/lock policy | 0 |
| Keep current one-transaction lane-to-RipeGov settlement at launch | B,C,D,F; A qualified because its picked UX routes locking through Teller | E | — | Preserves convenience but retains live cross-contract lock semantics | One transaction versus clearer post-purchase consent | Lane/UI at activation | 0 |
| Launch unlocked-only until isolated lots | E; A offers UI-default-unlocked plus Teller as an alternative | B,C,D,F | — | Strongest contract-level truthful launch; removes an existing option | Simpler purchase; locked route unavailable | Activation gate before use | **1** |
| Zero requested lock must settle unlocked | A,B,C; E later; F as an acceptable binding | — | D | Minimum one-way custody guarantee; smaller than full quote binding | Buyer cannot be silently forced into RipeGov | Lane assertion/ABI before activation | **3** |
| Bind settlement mode, expected vault and acceptable effective lock on-chain | B,C; A if Revision-24 removal was unratified; E when locked route activates; F as one alternative | — | D | Strong consent at cost of calldata and quote invalidations; A’s picked launch delta remains narrower | Wallet/locked/vault changes require fresh consent | Lane ABI, SDK and UI | **2** |
| Teller/blend calculator plus explicit UI consent as sufficient instead of full ABI binding | A; F qualified | B,C,E | D | Less ABI churn, but weaker enforcement; A still adds the narrow zero-lock assertion | Buyer sees account-level blended unlock before choosing lock | UI/Teller before activation | **1** |
| Close locked settlement on-chain during exit freeze; keep unlocked open | B,C; E when lock activates; F experiment | A favors UI-only hiding | D | Avoids creating new frozen positions while preserving fundraising | Locked route unavailable in bad debt | Preview/`buyNow`; owner decision 6 | 0 |
| Keep epoch-fixed price and lazy rollover | A–F | — | — | Predictable, auditable and keeper-free; accepts bounded boundary/cap race | First successful post-boundary buyer gets and commits new rate | Core architecture | 0 |
| Remove or neutralize amount-weighted timing | A,B,C,F; D experiment | E | — | At a flat price buyers can choose the timing signal; loses claimed early/late demand information | Fewer parameters and no last-block softening of next step | Controller/config before calibration | **5** |
| Flat/equal-endpoint up/down step simplification | A; D experiment | E | B,C,F | Stronger simplification than timing removal; gives up severity ranges | Fewer live controller knobs | Config and simulator | **2** |
| Add A’s stranding invariant between up-step and maximum decay | A | — | B–F | Prevents one strong epoch from pricing the lane beyond what capped decay can unwind | Intentionally stalls only within an explicit bound | Qualifier and simulator | **1** |
| Do not decay while the lane is unavailable | B | A,C,D,E,F | — | Unavailable time is not weak demand; opposing side values the existing deterministic clock | Less cheapening after incidents, more possible stranding | Controller/lifecycle | **1** |
| Treat `maxEffectiveRate` as binding minimum acceptable price and re-ratchet against off-chain reference | A | — | B–F | Directly limits discount leakage; creates recurring governance/monitoring work and can intentionally stall sales; B supports adjacent minimum-economics monitoring, not this recurring policy | Published “never cheaper than” policy; idle epochs accepted | Manifest, config cadence and runbook | **1** |
| Add an on-chain market-price/depeg oracle at launch | — | A–F | — | Adds a manipulable dependency and new authority/failure path | More live pricing, less deterministic isolation | Deferred different model | 0 |
| Retain exact one-shot target without mandatory installed expiry | A; D permits this through optional expiry=0 | B,C,E,F | — | Preserves exact intervention; accepts indefinite stale intent | Operator must revalidate/cancel before reopen | Lane/Foxtrot lifecycle | 0 |
| Exact one-shot target with expiry/max lead | D,E | A,B,C,F | — | Keeps exactness while bounding age; buyer can still receive a governance-set absolute price | Self-clearing stale intent, timelocked cancel | Lane/Foxtrot before activation | **2** |
| Replace exact target with a bounded, expiring lever | B,C,F | D,E | A | Shared objective is bounded freshness; implementations differ: B names run/config/epoch, C prefers a bounded short-lived lever that dies on pause, F uses relative bps and pause persistence | Smaller, auditable departure from controller | Lane/Foxtrot before activation | **2** |
| Bounded multi-epoch nudge as later experiment while retaining exact launch override | A | D,E | B,C,F choose bounded launch behavior instead | Tests a glide path without making it a launch dependency | Potentially less pause/reprice work | Simulator first | 0 |
| Immediate cancellation of installed override | A,B,C | D,E,F | — | De-escalation should not wait for a second timelock; opposing side preserves delay symmetry | Faster disarm, sharper immediate authority | Foxtrot lifecycle | **2** |
| Pause invalidates queued/installed override | B,C | A,D,E,F | — | Prevents pre-incident intent after reopen; opposing side treats pause as state-preserving | Must reinstall after pause | Pause/reopen lifecycle | **1** |
| Allow override before first epoch for restart continuity | A | — | B–F | Avoids resetting discovered price to seed after restart | Price-continuous restart | Lane validation/seed branch | 0 |
| Keep full-fill-only; no reservation or implicit partial fill | A–F | — | — | Honest amount consent and simpler state; costs revert/retry friction | Re-preview, shrink or wait | Existing buyer flow | 0 |
| Keep `available` as market-readiness only | A,C,D,E,F | B | — | Clean quote/reservation boundary; does not diagnose every downstream failure | Client still handles wallet/Teller/token failures | Current view/API | 0 |
| Split `marketOpen` from deterministic `settlementReady` | B | A,C,D,E,F | — | Better preflight but larger, caller-sensitive surface | Fewer futile transactions | Quote/API before production | 0 |
| Add reason enum/check view or documented `eth_call` preflight | B,E; A accepts reason codes or simulation | — | C,D,F | Better diagnosis without promising inclusion; D documents current dev strings but does not reject diagnostics | Distinguishes race, pause, allowance and vault failures | SDK/UI; optional view | 0 |
| Bind run/config identity, payment token and recipient on-chain | B | — | A,C,D,E,F | Strong lifecycle consent; more ABI/versioning surface; A instead pins the token client-side | Material sale-identity change requires confirmation | Lane/events/SDK | **1** |
| Make `cumulativeMinted` monotonic/non-decreasing | A,B; E while running, with stopped/timelocked downward correction | D | C,F | Makes nominal budget meaningful lifetime accounting; reduces correction flexibility | Stronger dilution assurance | Lane/Foxtrot | **3** |
| Timelock or tightly constrain counter reconciliation | B,C,E,F | D | A | Existence for migration does not justify immediacy | Slower correction, smaller blast radius | Foxtrot/recovery path | **2** |
| Add mandatory finite run/hard end | B | A,C,D,E,F | — | Bounds stale token qualification and authorization; adds extension ceremony | Planned run extensions | Lane/events/config | **1** |
| Keep no calendar sunset | A,C,D,E,F | B | — | Fits standing issuance; relies on honest accounting and operational disablement | Less campaign setup; authorization can age | Current lifecycle | 0 |
| Delay start/reopen, cadence and payment-token changes; keep close immediate | A,B | C,D,E,F | — | Issuance-increasing changes get prospectivity; recovery slows | Stronger reopening discipline | Foxtrot/start/token routes | **2** |
| Preserve live `canBuyNow` across stale queued config execution | A | — | B–F | Prevents an old config from silently undoing an emergency disable | Kill switch stays killed | Lane config execution | **1** |
| Keep pause/disable/stop immediate | A–F | — | — | Emergency close should remain the fastest authority path | Immediate halt | Current controls | 0 |
| Rename public product away from “Instant Bond” | A–F | — | — | No principal, maturity, interest or redemption | Correct buyer expectations | Docs/UI before activation | **2** |
| Rename contracts/events/HQ ID/ABI too | A,D,E,F; B if continuity is unimportant | — | C | Cheapest predeployment; more one-time migration churn | Cleaner long-term technical surface | Before ABI/deployment freeze | **2** |
| Per-address epoch-cap experiment | E | A | B,C,D,F | May reduce concentration but is Sybil/splitting-sensitive | Limits one address, not one buyer | Later experiment | 0 |
| Remove/reject a per-transaction cap as anti-concentration control | A | — | B–F | Frax buyers split orders; an extra transaction cap adds friction without limiting one buyer | Epoch cap remains the effective single-buyer bound | Product/docs; no new state | 0 |
| Early-rollover escape-hatch experiment | E | — | A–D,F | Faster exit from a mispriced epoch at cost of a new state transition | More operator discretion | Later experiment | 0 |
| Observe utilization-only live trajectories, then replace rather than restore timing if they fail | C | — | A,B,D,E,F | Tests the simplified controller without treating timing as the fallback | Evidence can trigger a different model | Post-activation experiment | 0 |
| Dead-band/stranding and minimum-probe monitoring | A | — | B–F | Exposes flat-rate clustering and probes that defeat empty-epoch limits | Adds alerts/runbook, no buyer change | Monitoring before activation | 0 |
| Off-chain fill-vs-DEX monitoring before any reference-priced model | A | — | B–F | Tests whether market discount exceeds what ceiling cadence can absorb | Evidence for later model change | Post-launch experiment; no oracle now | 0 |

## 5. Recorded-decision disagreements

Because all six used `d136a262`, the rewrite of owner decisions 8, 9, 11 and 14 settles what the current docs say about cadence and payment-token mutability. It does not settle proposals to change that behavior.

| Record or claim | Agents | Their disagreement | Classification | Verified current state |
|---|---|---|---|---|
| Revision 23 bindings removed by Revision 24 | A,B,C,E,F | B/C want full custody fields now; E gates then restores; F accepts bindings or UI consent; A picks a narrower invariant and asks whether full removal was ratified | **Behavior and decision-trail dispute** | No settlement-mode, vault or minimum-lock binding; zero request can become a nonzero actual lock |
| Decision 18 timing signal | A,B,C,D,F | Remove, neutralize or experimentally disable buyer-selected timing | **Behavior/experiment** | Amount-weighted timing changes the high-utilization step |
| Decision 19 severity-scaled step ranges | A; D experiment | A sets equal up/down endpoints and adds a stranding invariant; D tests simplification | **Behavior/experiment** | Separate governed min/max step ranges exist |
| Decisions 21/22/28 and §6.7 override freshness | B,C,D,E,F versus A | B–F add expiry/max lead, with exact/relative and pause/cancel splits; A deliberately keeps no installed expiry but changes cancellation/restart edges | **Behavior split** | Installed exact target has no target epoch, maximum lead or expiry |
| Decision 3 unavailable-time decay | B | Do not count unavailable time as weak demand | **Behavior change** | Deterministic empty time includes unavailable periods until next successful rollover |
| Decision 10 no hard sunset | B versus A,C,D,E,F | B wants finite runs; others retain standing-facility semantics | **Product-policy split** | No hard end exists |
| Decision 6 purchases during bad debt | B,C,E,F; A UI-only | Close/gate locked settlement or require explicit consent; A hides the route in UI while leaving contract behavior | **Behavior/UI qualification** | Current code permits locked or unlocked buy if other gates pass |
| Decision 24 `available` is market-only | B; A/E diagnostics | B wants separate readiness; A/E want reasons/simulation without necessarily changing semantics | **API/product change** | Preview omits wallet and downstream settlement readiness |
| “`mintBudget` is the ultimate lane issuance cap” | A,B,C,E,F versus D | A/B require monotonic accounting; E requires non-decrease while running with stopped/timelocked downward correction; B/C/E/F delay/constrain reconciliation; D keeps current tool | **Current-doc overstatement plus behavior proposals** | `setCumulativeMinted` may lower the counter to any value ≤ budget, restoring headroom |
| Pricing-design §5.1 precedent set | A,C,E | A: omitted measured Frax lineage hides ceiling risk; C: FXB is wrong bucket; E: conclusion sound but same-product evidence missing | **Research/design disagreement** | §5.1 did not change between pins |
| Activation manifest/qualifier source model | A,B | Obsolete constructor/immutable assumptions and incomplete mutator/economic-route inventory; B also finds unbound production config/delays and mismatched simulator override lifecycle | **Stale evidence/docs** | Independently confirmed against `d136a262` |
| Revision-24 decision trail and blacklist-precheck removal | A | Record who ratified each removal and why | **Missing provenance** | Code shows the removal, not its approval |
| RipeGov weighted-lock citation | C | Cited lines are governance-point math; blend exists elsewhere | **Stale anchor only** | Described blending behavior exists |
| Executable governance benefit | B | Do not market usable voting from the pinned temporary Boardroom | **Unsupported product claim** | RipeGov position exists; usable voting was not established |
| PR-body local byte ceilings | E,F | PR prose retains dropped 11,000/6,500-byte limits | **Stale PR description** | Current docs use EIP-170 only |

The counter is the clearest factual tie-break. Lowering `cumulativeMinted` does not raise `mintBudget`, but it restores issuance headroom. The budget is therefore a governed point-in-time fence, not immutable lifetime-issued accounting.

The Revision-24 ratification question is also unresolved. Code and current docs establish what landed; they do not establish who approved reversing the earlier selected bindings or why.

## 6. Quote promises

### Common current promises

| Promise area | Agreement | Important qualification |
|---|---|---|
| Quote status | A–F: preview is a conditional quote, not a reservation | It cannot promise inclusion, remaining capacity, wallet state or external liveness |
| Preview reports | Projected epoch/rate, remaining/minimum payment, remaining budget, payout, actual deposit lock, and—when locked—vault/exit/freeze disclosure | Account-level blended unlock and payment-token address are not in the quote |
| What may change | Capacity, projected rollover/override, live controls, budget/mint authority, lock floor, vault, exit/freeze terms, wallet balance/allowance and downstream liveness | A committed epoch’s rate stays fixed; an uncommitted projected epoch can still move |
| What `buyNow` binds now | Exact payment, `expectedEpoch`, `minRipeOut`, and inclusive `deadlineBlock`; full fill or revert | It does not bind settlement mode, vault, effective account unlock, payment token, recipient, run or config identity |
| Reservation/fill | A–F: no reservation and no silent partial fill | Capacity races require a new amount or a later epoch |
| Downstream preflight | Preview does not guarantee balance, allowance, recipient/Teller/vault admission, RIPE pause/blacklist or inclusion | A/B recommend simulation; E requires client preflight; C/D/F keep more responsibility in the existing retry loop |

### Proposed settlement and retry promises

| Agent | Proposed promise | Retry UX |
|---|---|---|
| A | Zero requested lock can never become locked; intentional lock routes through Teller after blended unlock is shown; client pins payment token | Never auto-resubmit across an epoch; offer one-tap capacity resize; reconfirm newly required lock; use reason codes or `eth_call` |
| B | Bind run/config, token, recipient, settlement mode, vault, duration, maximum exit fee and freeze consent; split market and settlement readiness | Never auto-retry across identity or custody change; require renewed consent and immediate simulation |
| C | Bind unlocked/locked mode, minimum actual lock and expected vault; reject locked buys during freeze | Shrink or wait after capacity race; stop and display changed lock terms |
| D | Keep existing three guards and market-readiness semantics | Re-preview all guards; current dev strings identify the cause |
| E | Activate unlocked-only; when lock returns, bind minimum actual lock and vault; add small reason enum/UI preflight | Loop on capacity; client checks allowance/downstream state |
| F | Add bindings or require explicit blend consent; otherwise current loop is adequate if published | Re-preview, rebind and resend; publish the guidance |

### Override lifecycle options

Current verified lifecycle: timelocked queue → execute/install exact target → preview discloses without consumption → first successful later rollover applies and consumes → `setConfig`/`start`/`stop` invalidate. Pause and `canBuyNow` do not clear it. A queued Foxtrot action can be canceled immediately; canceling an already installed lane override is timelocked.

- **A:** keep exact target; queue can expire but installed target does not; allow install before first epoch; make installed cancel immediate; preserve through pause; require reopen revalidation.
- **B:** bounded named-epoch nudge tied to run/config; automatic expiry; immediate cancel; pause/run/config disarm.
- **C:** short-lived lever, with a bounded nudge preferred if a manual price tool remains; immediate cancel; pause/stop/unused time disarm.
- **D:** exact target with optional expiry (zero can retain current behavior); timelocked cancel; pause preserves.
- **E:** exact target with mandatory maximum lead; timelocked cancel; pause preserves until expiry.
- **F:** relative bounded nudge with expiry; timelocked cancel; pause preserves until expiry.

There is no six-agent common ground on installed expiry: A is the explicit dissent, and D’s expiry is optional.

## 7. Question register

| Question | Who asked | Topic | Status | Blocks |
|---|---|---|---|---|
| Who is the intended first buyer: retail/donors or market makers/arbitrageurs/whales? | A,E,F | other | needs an owner call | preview / pricing |
| Is this a marginal reserve rail or the primary RIPE distribution channel? | E | other | needs an owner call | vesting |
| Does RIPE have meaningful secondary liquidity, and will unlocked RIPE be sold below that market in size? | C,E | pricing / research | unanswered | pricing / vesting |
| Does discovery, pro-rata allocation or arrival-time information outrank instant settlement? | B,C,F | pricing | competing recommendations | pricing |
| What epoch length, epoch cap, total program size and demand scale are contemplated relative to float and locked supply? | D,E,F | pricing | unanswered | pricing |
| Is the lane continuous or a set of discrete campaigns? | D | controls | needs an owner call | controls |
| Are isolated RipeGov lock lots actually planned? | E,F | vesting | needs an owner call | vesting / preview |
| Is executable governance participation a real purpose of the locked path? | B | vesting | needs an owner call | vesting |
| During bad debt, do Endaoment proceeds directly repair the condition freezing exits? | B | controls | unanswered | controls |
| Can depeg monitoring and pause reliably fire within one epoch? | D | controls | unanswered | none |
| Will BondRoom run simultaneously, and what distinct role does each venue serve? | A | other | needs an owner call | pricing |
| Was Revision-24 removal of the lock/vault bindings owner-ratified, and where is the rationale? | A | preview | needs an owner call | preview |

## 8. Next conversation

### 1. Confirm the product objective, first buyer and protected-price policy

Options and support:

- Issuance discipline first, with `maxEffectiveRate` maintained against an off-chain reference: A.
- Reserve fundraising under bounded dilution: B/C/E.
- Modest protected-price distribution: D/F.
- Competitive discovery/allocation: B/C/F say this requires a different mechanism.

Strongest points:

- Issuance-discipline side: a volume-only controller can sell below market for multiple epochs; the ceiling is the only hard price protection.
- Fundraising side: caps, budget and low-touch pacing matter more than perfect discovery.
- Distribution side: naming, custody consent and retry friction determine whether the intended buyer can use the product.
- Discovery side: a flat posted price cannot reveal the demand curve; use an auction or moving price.

Owner sub-call: decide whether the ceiling is a static absolute bound or an actively maintained minimum acceptable price. Only A proposes the recurring re-ratchet, but it is A’s highest-priority finding and is grounded in the most detailed same-product Frax evidence.

### 2. Choose the locked-settlement promise and close the Revision-24 provenance gap

Options and support:

- Narrow “zero requested lock stays unlocked” assertion plus Teller/UI: A; B/C also support the invariant.
- Full mode/vault/effective-lock binding now: B/C.
- Launch unlocked-only, bind when isolated lots exist: E.
- Binding or explicit blend consent: F.
- Keep disclosure-only: D records no change.

Strongest points:

- Binding side: output quantity is not custody consent; wallet RIPE and a frozen blended vault position are different products.
- Narrow/Teller side: one assert blocks the worst surprise without a broad ABI expansion, and the buyer sees the real account unlock before locking.
- Gating side: do not expose a feature until the protocol can promise isolated terms.
- Current/simple side: more bindings enlarge calldata, SDK and stale-quote failure surface.

Before treating the current decision trail as authoritative, record whether Revision 24’s removals were owner-ratified and why.

Frozen-exit sub-call if any locked route survives:

- A hides the lock route in the client but leaves contract purchases available.
- B requires explicit frozen-exit consent.
- C closes locked settlement on-chain.
- E makes the issue moot while the lane is unlocked-only, then gates it when locking returns.
- F treats on-chain closure as an experiment.
- D records no change.

### 3. Choose the controller’s timing and empty-time policy

Options and support:

- Keep current timing: E; D keeps it provisionally.
- Neutralize via equal endpoints and a one-step ratchet: A; D’s experiment tests the same direction.
- Remove timing and use utilization only: B/C/F.
- Stop decay while unavailable: B.
- Keep deterministic empty/unavailable-time decay: A/C/D/E/F.

Strongest points:

- Keep: early versus late sellout can contain information; `minUpBps` remains the safety floor.
- Remove/neutralize: at a fixed current price, buyers choose when the signal is recorded; activation already requires safety as if it contributes zero.
- Stop unavailable decay: pause or lost authority is not weak demand.
- Keep unavailable decay: one deterministic clock is simpler and existing pause/reopen behavior is bounded, but needs monitoring.

### 4. Choose override semantics and incident behavior

Options and support:

- Exact, no mandatory installed expiry, immediate cancel, pre-first-epoch install, pause persistence: A.
- Exact with expiry/max lead and timelocked cancellation: D/E; D makes expiry optional, E mandatory.
- Bounded named-epoch with expiry and immediate cancellation: B.
- Short-lived lever with immediate cancellation and pause invalidation; bounded nudge preferred: C.
- Relative bounded nudge with expiry and timelocked cancellation: F.
- Pause invalidates: B/C. Pause preserves: A/D/E/F.

Strongest points:

- Exact side: early calibration may require a deliberate price pin, not a small adjustment.
- Relative side: without a fair-value oracle, a bounded deviation cannot silently install an ancient absolute price.
- Expiry side: runbooks are weaker than a mechanism guard against stale intent.
- No-expiry side: exactness and prospectivity are preserved; immediate cancel plus reopen validation keeps the lifecycle smaller.
- Pause-clear side: reopening should not fire pre-incident intent.
- Pause-preserve side: pause is an incident switch and should not rewrite economic state.

### 5. Choose issuance accounting and run/reopen authority

Options and support:

- Monotonic counter: A/B; E requires non-decrease while running and permits stopped, timelocked downward correction.
- Delayed or constrained reconciliation: B/C/E/F.
- Current resettable correction tool: D.
- Mandatory finite, versioned run: B.
- No calendar sunset: A/C/D/E/F.
- Delay start/token/economic reopen while retaining immediate close: A/B.
- Preserve `canBuyNow` across queued config: A.

Strongest points:

- Accounting-hardening side: a counter that can be lowered does not provide lifetime dilution assurance.
- Flexibility side: migration and accounting correction need a recovery path, while nominal budget/config remain governed.
- Finite-run side: token qualification, price assumptions and authorization can age even if quantity accounting is correct.
- Standing-facility side: no sunset is ordinary when disablement and governance remain available.
- Delayed-reopen side: raising issuance should be slower than stopping it.

Blocking questions from §7:

- Intended buyer, product role and protected-price policy.
- Secondary liquidity and likely discount.
- Approved epoch/program scale relative to float and locked supply.
- Whether arrival-time discovery is actually desired.
- Continuous standing facility versus discrete campaigns.
- Isolated-lock roadmap and executable governance purpose.
- Bad-debt proceeds versus exit-freeze mechanics.
- BondRoom coexistence and cross-venue arbitrage.
- Revision-24 ratification/provenance.

What can wait:

- Separate vesting: unanimous “not now”; C/E identify sustained discount or primary-distribution evidence that would reopen it.
- Lock bonus: keep zero until isolated lots exist.
- Batch auction, SDA/VRGDA or reference-priced drip: wait unless objective, scale or reference quality changes.
- Per-address caps, early rollover, bounded multi-epoch nudge, C’s utilization-only trajectory test and reference-price guard: experiments, not launch consensus.
- Production parameters, calibration, deployment and activation: none of these reviews is a go-live decision.

Near-consensus action: choose a non-bond public name. The remaining naming call is whether to rename only the public surface or also contracts, events, registry identifier and ABI before deployment.
