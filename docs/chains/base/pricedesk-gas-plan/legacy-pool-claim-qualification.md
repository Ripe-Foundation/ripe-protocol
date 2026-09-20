# Retained Pool-1 claims: required PriceDesk qualification

This supplement adds a shared release invariant from the legacy-vault phase-1 review. It does not change the current PriceDesk prompt's architecture, owner choices, permitted scope or gas/fault model. Read it with `updated-prompt.md` and `implementation-reference.md`; passing ordinary quotes alone does not close this gate. For the separate legacy-compatibility contract task, only focused local dust/behavior fixtures are required; this full PriceDesk/release qualification is not a prerequisite to writing that patch.

The [read-only evidence](evidence/legacy-pool-claims.block-51532106.json) reproduces Base block **51,532,106**, not the latest cutover state. HQ is `0x6162df1b329e157479f8f1407e888260e0ec3d2b`; retained Pool 1 is `0x2a157096af6337b2b4bd47de435520572ed5a439`. The LP cohort is `0xd6c283655b42fa0eb2685f7ab819784f071459dc`, and sGREEN is `0xaa0f13488ce069a7b5a099457c753a7cfbe04d36`. The active desk was `0x2f7901be53cc94aef174f1a0764430840360ef53`; the historical staged candidate was `0xad70893e2f51076b0e9ba18fc593e924593a073f`. That candidate is unqualified and must not be confused with the final configurable replacement.

At this pin, LP has 11 nonzero claims (raw sentinel count 12), and sGREEN has no registered claims (raw count 0). The values below are identical on those two desks. Balances are raw token units and values are **USD-wei**, not whole tokens/dollars. Symbols are labels; full addresses control. Aggregate liabilities and pool custody equal each listed cohort balance in this observation.

| Claim asset | Address | Raw balance | USD-wei value on both desks | Depends on dust floor |
| --- | --- | ---: | ---: | --- |
| VVV | `0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf` | 1 | 1 | Yes |
| AERO | `0x940181a94a35a4569e4529a3cdfb74e38fd98631` | 2 | 1 | No |
| WETH | `0x4200000000000000000000000000000000000006` | 1 | 2627 | No |
| wsuperOETHb | `0x7fcd174e80f264448ebee8c88a7c4476aaf58ea6` | 1 | 2908 | No |
| mcbETH | `0x3bf93770f2d4a794c3d9ebefbaebae2a8f09a5e5` | 1 | 1 | Yes |
| WELL | `0xa88594d404727625a9437c3f886c7643872296ae` | 56 | 1 | Yes |
| cbDOGE | `0xcbd06e5a2b0c65597161de254aa074e489deb510` | 1 | 877566600 | No |
| uSOL | `0x9b8df6e244526ab5f6e6400d331db28c8fdddb55` | 1 | 110 | No |
| undyAERO | `0x96f1a7ce331f40afe866f3b707c223e377661087` | 1 | 1 | Yes |
| VIRTUAL | `0x0b3e328455c4059eeb9e3f84b5543f74e24e7e1b` | 1 | 1 | Yes |
| cbBTC | `0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf` | 12 | 9720534898526400 | No |

Six quotes equal one USD-wei; **five** rely on flooring a positive sub-wei value to one. AERO naturally rounds to one at its two-unit balance. This corrects the review's exact-one count while confirming its five floor-dependent cases. No price-accuracy or cold-gas claim is inferred from these positive `eth_call` results.

The reviewer reports mcbETH is outside the staged 27-asset MissionControl list and undyAERO is expensive to price. Verify both source routes and configuration membership at the fresh pin. Enumeration must come from **the pool's claim registry**, not only MissionControl or a token-symbol allowlist; include any other unconfigured and zero-balance historical entries. Authenticate retained pool bytecode/source as part of the composed release. The historical source commit is `d0957e497261a52e7a7b460eb986a6e9fb27f051` (Vyper 0.4.3); independent planning checks matched Pool 1's full runtime plus canonical-HQ immutable at this pin.

Required acceptance:

1. Refresh the complete address/index/balance inventory at a finalized qualification block/hash. Save both cohorts, raw counts, every registry entry, actual cohort liabilities, aggregate liabilities, custody, decimals/scales, source routes, budgets and candidate code/configuration identity. Record configuration drift; do not silently reuse this historical snapshot.
2. For **every nonzero actual claim balance**, require the final desk's strict `getUsdValue` and applicable conversions to return valid positive values from a verified cold state within their qualified source budgets. Preserve the existing dust floor and arithmetic; test the five historical floor-dependent cases, the naturally one-wei AERO case, and rounding boundaries. Non-strict readiness valuation must preserve its intended zero-price/funding-failure semantics. Do not round away, delete or skip claims to pass.
3. Qualify actual complete Pool-1 deposits, withdrawals, reachable share transfers, single/batched Teller claims, amount reads, Deleverage scans/information/withdrawal preparation and liquidation readiness/settlement. The immutable pool already walks these 11 claims with strict NAV pricing in ordinary funded flows. Include two users, cohort-specific controls, empty sGREEN and first/nonempty sGREEN claim states, real funded state and separately labeled synthetic failure cases.
4. Include the compatibility helper's bounded swap checks and all actual subsequent consumer pricing calls in complete gas bounds. Revision 5 removes the added readiness scan of unrelated non-GREEN claims: neither legacy swap entry point prices or pays them, so their health must not create a new unbounded liquidation gate. The immutable pool's strict ordinary NAV paths still scan claims. Stress those paths with expensive Underscore mixtures and growing registries without assuming the modern 20-claim cap. Use the current prompt's approved normal headroom, per-identity fault model, transaction envelope and independent Robinhood limits; source-level quotes alone are insufficient.
5. Record exact revert/skip/early-return and rollback behavior for unpriceable claims, insufficient backing and caller underfunding. A required ordinary exit failing on the actual supported state blocks release. Preserve strict legacy accounting; changes to skip unknown value require a separate owner decision. Healthy fallback is required where the selected model promises an independent valid route; loss of the only valid source is not evidence that unknown claim value can become zero.
6. Deliver the full result matrix, exact cold-state/reset method, per-source and transaction gas, known growth limits, commands/counts and integrated source/build/configuration pin. The previous undyUSDC issue remains separately open until its required closure evidence passes. Requalify on claim/source/budget/configuration changes that exceed the supported envelope.

These are acceptance requirements for the implementation agent. The attached planning readback used separate read-only calls and proves neither coldness nor gas margin, full transaction success, final candidate correctness or authority to activate. No live mutation is authorized by this supplement.
