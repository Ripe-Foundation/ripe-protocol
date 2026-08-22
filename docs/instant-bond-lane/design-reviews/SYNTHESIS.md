# Instant Bond Lane design-review synthesis

- Date: 2026-08-22
- Branch: instant-bond-lane
- Sources: agent-Codex.md, agent-DeepSeek.md, agent-GLM.md, agent-Ox.md, agent-claude.md, agent-grok.md
- Pins seen: d136a262

Agent map (letter → saved memo):

| Letter | Agent | File |
|--------|--------|------|
| A | Claude | agent-claude.md |
| B | Codex | agent-Codex.md |
| C | Grok | agent-grok.md |
| D | GLM | agent-GLM.md |
| E | DeepSeek | agent-DeepSeek.md |
| F | Ox | agent-Ox.md |

All six reviews support the product concept, reject extra vesting at launch, reject the “Instant Bond” name, and keep epoch-fixed pricing with lazy rollover. The real owner calls are the controller’s timing signal, settlement consent, override semantics, and whether issuance authority is genuinely finite.

One source limitation matters: Agent A supplied only a recap, not its full private artifact. Missing A details are marked “no position” rather than reconstructed. The supplied scoreboard also omitted F; I added it.

## 1. Scoreboard

| Verdict | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Pin | `d136a262` / `2cdcdd6e` | Same | Same | Same | Same | Same |
| Web access | Yes, demonstrated; not stated verbatim | Yes | Yes, demonstrated | Yes, demonstrated | Yes, demonstrated | Yes |
| Assumed top objective | Not stated in pasted recap | Maximize reserve dollars per bounded dilution; low touch second | Raise Endaoment dollars with hard caps and little babysitting | Protected-price RIPE distribution; hard cap; then low touch | Raise Endaoment dollars with bounded dilution and near-zero touch; healthy holder base | Modest distribution to real demand at non-distressed prices; reserves second |
| Support concept | Yes; not as a bond | Yes, conditionally; current consent/control model is not sound | Yes | Yes | Yes | Yes |
| Picked shape | Simpler lane | Finite simpler “RIPE Reserve Sale” | Simpler standing tap | Current lane plus override expiry; test timing simplification | Current lane plus bounded changes and experiments | Simplified current lane |
| Vesting | Don’t add | Don’t add | Don’t add | Don’t add | Don’t add now; add calibration gate | Don’t add |
| Override | Keep exact/blunt; immediate cancel; bounded nudge only an experiment | Bounded, delayed, named-epoch nudge with expiry | Prefer bounded nudge; immediate cancel; dies on pause/expiry | Keep exact one-shot; add optional expiry | Keep exact one-shot; add mandatory freshness bound | Bounded relative nudge with expiry |
| Keep name | No | No | No | No | No | No |
| Epoch-fixed + lazy rollover | Keep | Keep | Keep | Keep | Keep | Keep |

### Top three and biggest disagreement

| Agent | Top three | Biggest recorded-decision disagreement |
|---|---|---|
| A | Collapse controller rails; bind “unlocked means unlocked”; harden immediate controls and mint accounting | Revision 24 removed the previously selected buyer lock binding |
| B | Bind settlement consent; make cap/run genuinely finite; remove timing-weighted demand and unavailable-time decay | `minRipeOut` protects quantity, not custody |
| C | Bind settlement mode; delete timing from high-utilization step; expire/disarm override | Decision 18’s timing signal is buyer-selected at a flat price |
| D | Add override expiry; rename; experimentally simplify timing | §6.7 overstates the complexity of expiry |
| E | Add override freshness; harden mint counter; gate locked settlement until truthful | Decisions 21/22 and §6.7 permit arbitrarily stale exact overrides |
| F | Delete timing weighting; use relative bounded override; rename | Activation must be safe as though timing contributes zero, so timing should not exist |

Agreement:

- All six support a small, capped, keeperless primary sale.
- All six reject separate vesting at launch.
- All six keep epoch-fixed pricing and lazy rollover.
- All six rename the public product.
- B–F require override expiry; A clearly requires harder cancellation but its recap does not disclose the second proposed edge.
- No memo favors partial fills or quote reservations.

Material splits:

- A/B/C/F pick a simpler lane; D/E retain the current controller more substantially.
- D/E retain an exact override; B/C/F replace it with a bounded nudge. A retains exact behavior and treats the nudge as experimental.
- A/B/C favor immediate cancellation; B/C also clear the override on pause. D/E/F retain timelocked cancellation and allow pause persistence, relying on expiry.
- A/B/C want buyer-bound settlement now; E wants unlocked-only activation and bindings later; F allows either bindings or explicit UI consent; D takes no explicit position.
- B alone wants a mandatory run end. C/D/E/F retain no sunset.

Objective explains part of the split:

- B/C/E start from fundraising and reserve accumulation.
- D/F start from distribution quality and protected pricing.
- B would switch to a batch auction if discovery became primary; C/F would reconsider epoch-fixed pricing if arrival time or much larger size became important.
- A’s objective was not stated and should not be inferred.

## 2. Research they used

Bucket 1 means the issuer sells its governance/equity-like token; bucket 2 means a fixed-redemption claim; bucket 3 means a buyback.

| Mechanism | Agents | Bucket | Their evidence label | Changed a rec? | Notes |
|---|---|---:|---|---|---|
| Olympus v1 reserve/LP bonds | B–F | 1 | Mechanics generally “fact”; adoption “observed”; effectiveness ranged from inference to unknown | Yes | Supported caps and halts. C/E tied vesting to visible discount; D/F treated vesting as ineffective complexity |
| Olympus v2 BondDepository | A–F | 1 | Shipped mechanics treated as fact; long-run economics mostly unknown | Yes | Supported isolated terms and simpler delivery; did not establish that RipeGov blending is equivalent |
| Olympus Pro → Bond Protocol SDA | A–F | 1 | Mechanics fact; organizational/mechanism lineage partly inference; outcomes mixed or unknown | Yes | Established the credible discovery alternative and informed timing/override arguments |
| Frax FXS Olympus Pro program | A,B,C,E,F | 1 | Proposal terms fact; deployment/value observations used with different time windows | Yes—strongly | A moved off “as-is”; C/E made vesting conditional on measurable discount; F emphasized periodic quotas |
| Frax FXB | B–F | 2 | Mechanics and live series fact; pricing efficiency usually unknown | Mostly contrast | A true redemption claim supports renaming and shows why this lane is not a bond |
| Olympus inverse bonds | B–F | 3 | Deployment fact; effectiveness described variously as observed, inferred, or unknown | Contrast | Opposite economic direction; several agents used it to argue for small issuance caps |
| VRGDA/GDA | C–F | 1 | Mechanism/shipping fact; parameter and outcome quality uncertain | Yes | C/F: if arrival time matters, move price continuously instead of measuring timing at a flat price. D rejected current use due complexity |
| Gnosis/EasyAuction batch | B,E | 1 | Mechanics fact; adoption observed; optimality evidence limited | Conditional | Best different model if discovery/fair allocation outranks instant settlement |
| Treasury uniform-price auctions | B,E | 2 | Long-running use observed/fact | Conditional | Supports batch clearing but depends on waiting, settlement, and standardized claims |
| Balancer LBP | B,C,E | 1 | Mechanics fact; outcomes mixed/inferred | Yes—rejected | Adds waiting incentives, MEV, AMM, and manipulation surfaces |
| ATM equity issuance | A,B,C,E,F | 1 | Standard structure fact; issuer use observed | Yes—materially | A: disciplined stranding; B: finite authorization and monotonic sold-to-date; E: conservative volume calibration; F: immediate controls/no sunset |
| Rights issues / pre-emption practice | B,D,E; F uncited | 1 | Standard practice observed | Limited | Relevant only if incumbent-holder protection becomes a primary objective |
| ESPP | B,C,D,E; F uncited | 1 | Mechanics fact; participation/holding effects varied in strength | Mixed | C used known discounts to reject decorative holding; D saw periodic fixed-price precedent; E drew a per-buyer-cap experiment |
| IPO lockups | B,F | — | B called it a weak analogy; F used empirical observed effects | Yes for F | Reinforced avoiding a manufactured unlock overhang |
| I/EE savings bonds | A,C,D | 2 | Product rules fact; durability observed | Naming/cadence | Supports posted-rate cadence but also demonstrates that a bond promises repayment |
| Corporate bonds / CDs | B; F uncited | 2 | Authoritative product definitions | Yes | Decisive naming contrast: principal/maturity/redemption are absent here |
| Fed TAF | A | — | A’s detailed table was not pasted | Yes for A | Reframed unsold capacity as disciplined stranding |
| Fed ON RRP | C | — | Mechanics and durable use fact/observed | Yes | A posted rate is fine; a stale lever surviving a halt is not |
| ECB fixed-rate full allotment | F | — | Adoption and persistence fact | Yes | Settled F’s support for fixed-price cadence |
| Maker debt auction | C | 1 | Crisis use observed | Yes | Supported closing locked settlement during an exit freeze |
| UK DMO gilt tap | C | 2 | Mechanics fact; exceptional use observed | Yes | Supported short-lived, current interventions rather than stale standing intent |
| Olympus Emissions Manager | C; E via §5.1 | 1 | Mechanics fact; realized outcomes unknown | Mostly rejected | Requires fair-value/backing inputs this lane deliberately avoids |
| DRIP | D | 1 | Standard use observed | Context only | Simpler but lacks issuance discipline |
| Aave stkAAVE/GHO discount | D | — | Active utility observed | Context only | Supported keeping lock-bonus arithmetic dormant rather than activating it |
| A’s remaining comparisons | A | Mixed | A says fact/observed/inference/unknown, adversarially rechecked | Unknown individually | The underlying 22-row table was not included; nothing further should be reconstructed |

Research conflicts to preserve:

- Do not standardize the claim that Olympus v1 “was an SDA.” B/C treat that as possibly retrospective terminology; D/F use a direct v1→v2→SDA lineage. The [contemporaneous Olympus post](https://olympusdao.medium.com/a-primer-on-oly-bonds-9763f125c124) was unavailable in this pass, so the terminology remains attributed.
- C inferred that v1/Frax vesting was load-bearing because the discount was visible; D/F inferred that vesting added little durable benefit. They reach the same no-vesting recommendation for different reasons.
- Frax dollar totals and discount observations came from different programs, periods, and denominators. They should not be averaged.
- C labels FXB curve usefulness and inverse-bond floor effectiveness unknown; D uses stronger “observed success/effectiveness” language. Keep those evidence labels separate.

## 3. Product shapes

| Cluster | One-sentence shape | Picked by |
|---|---|---|
| Current lane, bounded changes | Preserve the full controller and buyer flow, add override freshness and harden selected controls without changing the mechanism family | D, E |
| Simpler lane | Preserve the two-contract architecture, epoch clock, caps, and lazy rollover while removing or neutralizing timing and reducing override/control discretion | A, B, C, F |
| Different model | Batch auction, SDA/VRGDA, or oracle-linked drip only if discovery, arrival time, or much larger issuance becomes the first objective | Nobody picked it under the stated objectives |

The “simpler” picks are not identical: A simplifies largely through configuration and off-chain ceiling discipline; B adds finite versioned runs; C prioritizes lock consent and pause-cleared overrides; F uses a relative override.

## 4. Option register

Qualified support is shown explicitly. Priority signal counts only agents who placed that distinct option in their top three.

| Topic / option | For | Against | No position | Why and tradeoff | Buyer / operator effect | Surface and timing | Priority signal |
|---|---|---|---|---|---|---|---:|
| No separate vesting at launch | A–F | — | — | No demonstrated need for another claim, escrow, or clock; agents differ on whether discounted-sale precedents make this conditional | Immediate wallet RIPE or existing RipeGov path; no claim/redemption UX | Product/activation policy now | 0 |
| Revisit vesting only after measurable sustained discount or primary-distribution evidence | C, E | — | A,B,D,F | Preserves a future dump brake without taxing fair-price buyers now | Could later add isolated custody and unlock overhang | Calibration/owner gate; no current code | 0 |
| Keep optional RipeGov settlement with zero bonus | A,B,C,D,F | E at activation | — | Existing vault avoids new custody, but blended unlock is not an isolated vest | Buyer can choose wallet or live vault position; lock may blend | Current path; bonus remains zero | 0 |
| Launch unlocked-only until isolated lock lots exist | E | A,B,C,D,F | — | Strongest way to avoid selling a lock the protocol cannot guarantee | Simpler truthful launch; removes locked choice temporarily | Activation gate before use | 1 |
| Keep epoch-fixed price and lazy rollover | A–F | — | — | Predictable, auditable, no keeper; accepts a bounded boundary-price leak | First successful post-boundary buyer gets and commits new rate | Core architecture | 0 |
| Retain amount-weighted timing | E; D pending experiment | A,B,C,F | — | For: early sellout may contain extra demand information. Against: at a flat price buyers choose the signal | More calibration and monitoring; possible timing game | Controller/calibration | 0 |
| Remove or neutralize timing; use utilization-only movement | A,B,C,F; D contingent on simulation | E | — | Removes a strategically selectable input; loses distinction between early and late sellout | Same buyer quote; fewer controller parameters | Before calibration; A allows equal endpoints rather than immediate code deletion | **5** |
| Do not decay during unavailable periods | B | C,D,E,F | A | Unavailable time is not weak demand; opposing view treats deterministic empty time as part of the current controller | Less automatic cheapening after incidents; more possible stranding | Controller/lifecycle | 1 |
| Exact one-shot override with expiry/max lead | D,E | B,C,F | A | Preserves surgical governance price-setting while removing indefinite staleness | Operator keeps exact intervention; buyer may still see a governed price unrelated to controller | Lane state/rollover; before activation | **2** |
| Bounded relative/named-epoch nudge with expiry | B,C,F; A experiment only | D,E | — | Cannot park an ancient absolute price; loses exact emergency targeting | Smaller, auditable departure from controller | Lane + Foxtrot before activation | **2** |
| Immediate cancellation of installed override | A,B,C | D,E,F | — | Incident response should not require a second timelock; opposing side preserves governance-delay symmetry | Faster disarm versus sharper immediate authority | Foxtrot lifecycle | 2 |
| Pause invalidates installed/queued override | B,C | D,E,F | A | Prevents pre-pause intent from firing after reopen; opposing side treats pause as state-preserving and relies on expiry | Less stale-intent risk; operator must reinstall | Pause/reopen lifecycle | 1 |
| Bind settlement mode, vault, and effective lock on-chain | A,B,C; E when locked path activates; F as one alternative | — | D | Output slippage does not protect custody; extra calldata and quote invalidation are the cost | Buyer cannot move between wallet and vault without fresh consent | ABI, SDK, UI before any locked activation | **3** |
| UI blend calculator and explicit consent without full ABI binding | F as alternative | A,B,C | D,E | Lower code churn, weaker enforcement | Better disclosure but transaction can still execute against changed terms | UI before activation | 0 |
| Keep `available` as market-readiness only | C,D,E,F | B | A | Clean quote/reservation boundary; does not explain all deterministic downstream failures | Buyer still handles downstream reverts | Current view/API | 0 |
| Split `marketOpen` from settlement readiness / add reason codes | B; E supports a smaller reason enum | — | A,C,D,F | Better diagnosis and fewer futile transactions; larger view/SDK surface | Clearer retry path | Quote/API before production use | 0 |
| Make `cumulativeMinted` monotonic or non-decreasing while running | A,B,C,E | D | F | Turns nominal budget into meaningful lifetime accounting; reduces correction flexibility | Stronger dilution assurance; stop/recovery needed for downward reconciliation | Lane/Foxtrot | **3** |
| Timelock counter reconciliation | B,C,E,F | D | A | Supply-shaped accounting should not be instant; D values quick migration correction | Slower recovery, smaller blast radius | Foxtrot | 2 |
| Add finite run/hard end and run identity | B | C,D,E,F | A | Bounds stale qualification and authorization; opposing side treats budget plus disable as sufficient | Planned extensions rather than evergreen operation | Lane/events/config | 1 |
| Keep no sunset | C,D,E,F | B | A | Fits a standing issuance facility; relies on honest counter and operational disablement | Less campaign setup; authorization can remain stale | Current lifecycle | 0 |
| Delay reopen/start/token/economic changes; preserve immediate close | A,B | C,D,E,F | — | Reopening dilution should not be same-block; opposing side values immediate recovery and existing stop/start ceremony | Stronger lifecycle consent, slower operations | Foxtrot/start/token paths | 2 |
| Close only locked buys during an exit freeze | B,C,F; E when locked settlement exists | — | A,D | Avoids selling new frozen positions while preserving unlocked fundraising | Locked route unavailable during bad debt | Preview/`buyNow` | 0 |
| Keep full-fill-only; no reservation or implicit partial fill | B,C,D,E,F | — | A | Honest amount consent and simpler state; costs revert/retry friction | Buyer re-previews, shrinks, or waits | Current buyer flow | 0 |
| Publicly rename away from “Instant Bond” | A–F | — | — | No principal, maturity, interest, or redemption; one-time migration cost | Correct buyer expectations | Before activation | **2** |
| Rename contracts/events/ABI, not just marketing | D,E,F; B if continuity is unimportant | — | A,C | Cheapest before deployment; public-only rename avoids technical churn | Cleaner long-term surface versus migration work | Predeployment | 2 |
| Per-address epoch cap experiment | E | — | A,B,C,D,F | May reduce concentration; adds state and remains Sybil-sensitive | Limits one address’s epoch share | Later experiment | 0 |
| Early-rollover escape hatch | E experiment | — | A,B,C,D,F | Lets governance end a mispriced epoch; adds the state machine already deferred | Faster price correction, greater operator discretion | Later experiment | 0 |

### Override lifecycle choices

The common current lifecycle is: timelocked queue → execute/install → preview discloses without consumption → first successful later rollover applies and consumes → `setConfig`/`start`/`stop` invalidate. Pause and `canBuyNow` currently do not clear it.

The proposed variants are:

- B/C: bounded nudge, mandatory expiry, immediate cancel, pause disarms.
- F: bounded relative nudge, expiry, timelocked cancel, pause preserves it until expiry.
- D/E: exact target, expiry/max lead, timelocked cancel, pause preserves it.
- A: exact target retained, immediate cancel explicit; the recap does not reveal the second edge.

## 5. Recorded-decision disagreements

All six memos used `d136a262`; none relied on the older owner-decision wording. The rewrite therefore settles current documentation of decisions 8, 9, 11, and 14. It does not settle the following proposed behavior changes.

| Record or claim | Agents | Their disagreement | Classification | Verified current state |
|---|---|---|---|---|
| Revision 23 selection versus Revision 24 removal of lock/vault bindings | A,B,C,E,F | Restore bindings now, gate locked path, or require stronger consent | **Change behavior**, not stale docs | Revision 24 and code both omit settlement-mode, vault, and minimum-lock bindings |
| Decision 18: amount-weighted timing | A,B,C,D,F | Neutralize, remove, or experimentally simplify it | **Change behavior / experiment** | Timing affects the high-utilization step |
| Decisions 21/22/28 and §6.7: no override expiry | B,C,D,E,F | Add expiry; split on exact versus relative and pause/cancel behavior | **Change behavior** | Override has no target, maximum lead, or expiry |
| Decision 3: empty-time decay during pause/disable/budget exhaustion | B | Do not count unavailable time as weak demand | **Change behavior** | Current deterministic clock includes unavailable empty time |
| Decision 10: no hard sunset | B versus C,D,E,F | B wants finite runs; others retain standing-facility semantics | **Product-policy split** | No hard end exists |
| Decision 6: buys remain available during bad debt | B,C,F; E conditional | Close only locked settlement during an exit freeze | **Behavior qualification/change** | Current code permits the buy if other gates pass |
| Decision 24: `available` is market-only | B; E minor | B wants separate readiness; E wants a reason enum | **API/product change** | Current preview omits wallet and downstream settlement readiness |
| “`mintBudget` is the ultimate lane issuance cap” | B,E explicitly; A,C,F harden it; D defends current tool | The statement overstates lifetime discipline because the counter can be rewound | **Current-doc overstatement plus behavior proposal** | `setCumulativeMinted` can immediately set any value at or below `mintBudget`, reopening headroom without increasing the nominal budget |
| Pricing-design §5.1 precedent set | A,C,E | A: missing measured Frax lineage underweights ceiling risk. C: FXB is the wrong bucket. E: conclusion sound but same-product FIP-22/Olympus evidence is missing | **Research/design disagreement** | §5.1 did not change between pins |
| Activation manifest and qualifier constructor/immutable model | B | Evidence still models genesis/epoch/payment/Foxtrot as immutable and omits real economic routes | **Stale evidence/docs** | Independently confirmed at `d136a262` |
| RipeGov source-line citation | C | Cited lines are governance-point math; blend exists elsewhere | **Stale anchor only** | Described weighted-lock behavior exists |
| PR-body local byte ceilings | E,F | PR prose retains superseded limits | **Stale PR description** | Current docs correctly use EIP-170 only |

The most important factual tie-break is the counter: D is correct that `setCumulativeMinted` cannot itself raise `mintBudget`; B/E are correct that lowering the counter restores issuance headroom. It is therefore a point-in-time budget fence, not an immutable lifetime-issued total.

## 6. Quote promises

| Promise area | Agreement | Split |
|---|---|---|
| Preview reports | B–F agree it reports projected epoch/rate, capacity/minimum, budget, payout, actual lock, and—when locked—vault/exit/freeze terms | B wants separate market and settlement readiness; E wants a smaller reason enum |
| What may change | Capacity, epoch/override, pause/disable/budget/mint authority, lock floor, vault, exit/freeze terms, wallet balance/allowance, and downstream liveness | B additionally wants run/config/token/recipient identity bound |
| What `buyNow` currently binds | Exact payment, `expectedEpoch`, `minRipeOut`, and `deadlineBlock`; full fill or revert | A/B/C say this is insufficient because it does not bind custody. E gates lock then binds later. F allows code binding or explicit UI consent. D records no change |
| Reservation promise | None; preview cannot guarantee inclusion, remaining capacity, or external execution | No memo proposes reservations |
| Settlement promise | Current preview discloses actual lock/vault but does not bind them | A/B/C: wallet versus locked must never change silently. E: locked path unavailable until truthful. F: bind or obtain explicit blended-lock consent |
| Retry UX | Re-preview, rebind, and resubmit after epoch/capacity/control changes; no silent partial fill | B/C prohibit automatic retry across custody/vault changes. D uses current dev-string flow. E adds clearer reason reporting. F says current loop is adequate if published |
| Downstream preflight | Wallet/allowance/recipient/Teller/vault/RIPE liveness is not promised | B recommends an immediate call simulation; E/F place more responsibility in the client |

Agent A’s pasted recap supplies only one quote promise: a previewed unlocked purchase must settle unlocked, with intentional locks routed through Teller and the blended unlock shown.

## 7. Question register

| Question | Who asked | Topic | Status | Blocks |
|---|---|---|---|---|
| Who is the intended first buyer: retail/donors or market makers/arbitrageurs/whales? | A,E,F | other | needs an owner call | preview / controls |
| Is this a marginal fundraising rail or the primary RIPE distribution channel? | E | other | needs an owner call | vesting |
| Does RIPE have meaningful secondary liquidity, and will unlocked RIPE be sold below that market in size? | C,E | pricing / research | unanswered | pricing / vesting |
| Does price discovery, pro-rata allocation, or “when dollars arrived” outrank instant settlement and low touch? | B,C,F | pricing | competing recommendations | pricing |
| What epoch length, epoch cap, total program size, and demand scale are contemplated relative to RIPE float? | D,E,F | pricing | unanswered | pricing |
| Is the lane continuous or a set of discrete campaigns? | D | controls | needs an owner call | controls |
| Are isolated RipeGov lock lots actually on the roadmap? | E,F | vesting | needs an owner call | preview / vesting |
| Is executable governance participation a core purpose of the locked path? | B | vesting | needs an owner call | vesting |
| During bad debt, do Endaoment proceeds directly repair the condition freezing RipeGov exits? | B | controls | unanswered | controls |
| Can depeg monitoring and pause reliably fire within one epoch? | D | controls | unanswered | none |
| Will BondRoom continue alongside this lane, and what distinct role does each product serve? | A | other | unanswered | pricing |
| Was Revision 24’s binding removal ratified? | A | preview | already answered in the code or docs | none |

For the last question, Revision 24 is the current recorded/code behavior. That answers what was selected; it does not answer whether the owner should now reverse it.

## 8. Next conversation

### 1. Confirm the product objective and first buyer

Options:

- Marginal fundraising rail: B/C/E’s framing.
- Modest distribution rail: D/F’s framing.
- Competitive discovery/allocation product: B/C/F say this requires a different model.
- A did not state an objective.

Strongest points:

- Fundraising: caps, ceiling, and low-touch controller matter more than perfect discovery.
- Distribution: misleading naming, lock consent, and revert-heavy UX tax the exact buyer the product needs.
- Discovery: a flat epoch price cannot reveal the demand curve; use an auction or continuously moving price.

### 2. Decide the locked-settlement promise

Options and support:

- Bind settlement mode, vault, and effective lock now: A/B/C.
- Launch unlocked-only; enable and bind later: E.
- Bind on-chain or require explicit blended-lock UI consent: F.
- Keep disclosure-only: D records no explicit change.

Strongest points:

- Binding side: output quantity is not custody consent; wallet RIPE and a frozen blended vault position are materially different products.
- Gating side: do not expose a feature until isolated lock terms can be honestly promised.
- Current/simple side: additional bindings enlarge ABI/SDK surface and create more stale-quote failures.

### 3. Decide the controller’s timing signal

Options and support:

- Keep timing: E; D pending experiment.
- Neutralize it through equal steps first: A and D’s experimental path.
- Remove it and use utilization only: B/C/F.

Strongest points:

- Keep: early versus late sellout may contain useful demand information, while `minUpBps` remains the actual safety floor.
- Remove: at a fixed current price, buyers choose when the signal is recorded; activation already requires safety as though it contributes zero.

A separate sub-call is whether unavailable time should decay. B says no; C/D/E/F retain current deterministic empty-time behavior.

### 4. Choose override semantics and incident behavior

Common ground: an indefinitely stale override should not remain the accepted design.

Options:

- Exact target plus expiry: D/E.
- Bounded relative or named-epoch nudge plus expiry: B/C/F.
- Exact target with harder edges; nudge only experimental: A.
- Immediate cancellation/pause invalidation: A/B/C.
- Timelocked cancellation/pause persistence: D/E/F.

Strongest points:

- Exact side: early calibration may require a deliberate price pin rather than a small adjustment.
- Relative side: governance has no fair-value oracle; a bounded deviation cannot silently install an ancient absolute price.
- Pause-clear side: reopening should not fire pre-incident intent.
- Pause-preserve side: pause is an incident switch, while expiry supplies the stale-intent guard.

### 5. Decide what “lifetime budget” and reopening mean

Options:

- Monotonic counter, timelocked reconciliation: A/B/C/E; F supports timelock but does not take a monotonicity position.
- Current resettable correction tool: D.
- Mandatory finite, versioned run with delayed reopen: B.
- No sunset with operational disablement: C/D/E/F.
- Delay start/token/economic reopen while retaining immediate close: A/B.

Strongest points:

- Hardening side: a counter that can be reset immediately does not provide lifetime dilution assurance.
- Flexibility side: migration and accounting correction need a recovery path, and nominal budget/config governance remain bounded.
- Finite-run side: token qualification, price assumptions, and authorization can become stale even if quantity accounting is correct.
- Standing-facility side: no sunset is ordinary for issuance programs when disablement and governance remain available.

Blocking questions from §7:

- Intended buyer and product role.
- Secondary liquidity and likely discount.
- Approved scale relative to float.
- Whether arrival-time discovery is actually desired.
- Isolated-lock roadmap.
- Bad-debt proceeds versus exit-freeze mechanics.

What can wait:

- Separate vesting: unanimous “not now”; revisit only if discount/primary-distribution evidence changes.
- Lock bonus: keep zero until isolated lots.
- Batch auction, SDA/VRGDA, or oracle-linked drip: wait unless objective or scale changes.
- Per-address caps and early rollover: experiments, not launch requirements.
- Production parameters, calibration, deployment, and activation: none of these reviews constitutes a go-live decision.

Near-consensus action: choose a non-bond public name. The remaining naming call is whether to rename only the product surface or also the contracts/events/ABI before deployment.
