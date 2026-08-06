# Track 4: USDG PSM Price-Path Decision

**Status:** Draft for owner review

**Prepared:** 23 July 2026

**Planning baseline:** `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2`

## Fresh-agent instruction

Treat this document as the task contract. Determine whether the Robinhood deployment can safely enable `EndaomentPSM` with canonical USDG and, if so, which current price path and configuration it should use.

This is a research, code-analysis, and decision-specification track. Do not implement a new price adapter, modify production contracts or defaults, fund the PSM, enable minting or redemption, broadcast a transaction, or contact an external party without explicit owner authorization.

Use a dedicated branch or worktree named `rh-track-4-usdg-psm`. Do not edit `docs/chains/rh-summary.md` or files owned by the other Robinhood tracks. Commit deliverables to the track branch with clear messages; never push directly to or merge into the shared `rh` or `master` branch. The owner reviews and integrates the work.

## Worktree bootstrap

The owner must commit this approved brief to the `rh` integration branch before kickoff. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Confirm that branch `rh-track-4-usdg-psm` and path `/Users/wigglez/dev/ripe-protocol-track-4-usdg-psm` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
4. Create the isolated worktree from the committed `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-4-usdg-psm \
     /Users/wigglez/dev/ripe-protocol-track-4-usdg-psm \
     rh
   ```

5. Verify the new worktree's branch, commit, and clean status. Record the full starting commit in the deliverables.
6. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-4-usdg-psm`.

Do not modify or commit from the integration worktree. Leave the track worktree and branch in place for owner review; do not remove or merge them yourself.

## Objective

Produce two artifacts:

1. `docs/chains/rh/usdg-public-evidence.md`
2. `docs/chains/rh/usdg-psm-decision.md`

Together, they must answer:

- What is the current canonical USDG contract on each intended Robinhood environment?
- Is its decimal and transfer behavior compatible with the existing `EndaomentPSM` reserve interface?
- Is a current, production-appropriate price source available through the existing Ripe pricing system?
- How does the current PSM behave when USDG is below, at, or above one dollar?
- Can the Base-specific yield and privileged integration paths be verifiably disabled?
- Should the Robinhood PSM use an existing Chainlink feed, an already-reviewed reusable adapter, a separately specified new fixed/capped adapter, or remain disabled or omitted?
- What exact repository work follows from the selected outcome?

This track does not authorize a PSM launch. It produces the evidence and decision record needed to approve or reject a later implementation specification.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md) and the selected architecture in Hightop Notes.
- Preserve one canonical, chain-portable production contract source.
- Prefer `DefaultsRobinhood`, constructor arguments, governed configuration, and deployment inputs over Robinhood-specific core contracts or `chain.id` branches.
- Use canonical six-decimal USDG as the reserve asset only after re-verifying the deployed contract.
- Do not inherit Base's USDC yield lego or yield-vault configuration.
- Do not assume that a price feed available on another chain or through an incompatible Chainlink product is usable on Robinhood.
- Do not treat a fixed one-dollar price as harmless. Its depeg behavior, failure mode, governance, pause path, and monitoring surface must be explicit.
- If no price path is approved, keep both PSM minting and redemption disabled or omit the PSM according to the approved component matrix.
- Keep `EndaomentPSM` separate from Base-only Endaoment treasury, partner-liquidity, Underscore, and yield routes.
- This is a technical review, not legal, accounting, credit, or investment advice. Record observable issuer and administrator controls without deciding whether their risk is acceptable for launch.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the required architecture. Do not use the larger federated design in `random/hood/hood-chain.md` as the controlling plan.

## Required repository reading

Read and verify the current versions of:

- `docs/chains/rh-summary.md`
- `contracts/core/EndaomentPSM.vy`
- `contracts/core/Endaoment.vy`
- `contracts/core/Deleverage.vy`
- `contracts/config/SwitchboardEcho.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `contracts/registries/PriceDesk.vy`
- `contracts/priceSources/ChainlinkPrices.vy`
- `contracts/priceSources/modules/PriceSourceData.vy`
- `contracts/data/MissionControl.vy`
- `contracts/registries/RipeHq.vy`
- `contracts/modules/Addys.vy`
- the defaults-generation and migration scripts under `scripts/params/` and `scripts/`
- all current `EndaomentPSM`, PriceDesk, and Chainlink price-source tests, including:
  - `tests/core/endaoment/test_endaoment_psm_mint.py`
  - `tests/core/endaoment/test_endaoment_psm_redeem.py`
  - `tests/core/endaoment/test_endaoment_psm_config.py`
  - `tests/core/endaoment/test_endaoment_psm_views.py`
  - `tests/core/endaoment/test_transfer_funds_to_endaoment_psm.py`
  - `tests/priceSources/test_chainlink_prices.py`

Use repository search to find additional PSM, USDC, USDG, yield-position, Underscore, and price-source call sites rather than assuming this list is exhaustive.

Record the actual starting commit. If relevant code has changed since the planning baseline, describe the delta before relying on this brief's code observations.

## Phase A: Verify canonical USDG and the intended environments

- [ ] Record the intended Robinhood mainnet and test environment, including current chain IDs and official RPC or explorer sources.
- [ ] Identify canonical USDG on each intended environment from current issuer, Robinhood, and onchain evidence.
- [ ] Record the token proxy and implementation addresses, deployment type, implementation code hash, name, symbol, decimals, and total-supply behavior.
- [ ] Confirm that the token actually uses six decimals; do not rely only on the July 2026 research snapshot.
- [ ] Determine whether a suitable USDG contract exists on the intended test environment or whether testnet work requires a clearly labeled mock.
- [ ] Inspect observable transfer, pause, blocklist, clawback, forced-transfer, forced-redemption, mint/burn, upgrade, and administrator controls.
- [ ] Check for transfer fees, rebasing, hooks, nonstandard return behavior, or other mechanics relevant to PSM accounting.
- [ ] Distinguish verified current facts from issuer documentation, historical facts, and inference.

Use current primary sources and dated read-only onchain calls. Do not use signing keys or broadcast transactions.

Write the evidence to:

`docs/chains/rh/usdg-public-evidence.md`

Every time-sensitive claim must include its retrieval date, network, and direct source. Record reproducible calls where practical. Never include RPC secrets, API keys, or private credentials.

## Phase B: Determine the available price paths

Evaluate each of the following as a distinct outcome:

1. an existing Chainlink feed that is compatible with Ripe's current `ChainlinkPrices` contract;
2. an existing, already-reviewed Ripe price adapter that can be reused without Robinhood-specific logic;
3. a new shared fixed/capped adapter that requires a separate implementation specification; or
4. no approved path, leaving the PSM disabled or omitted.

### Existing Chainlink feed

- [ ] Verify from current official sources whether a USDG/USD or equivalent feed exists on the exact intended Robinhood network.
- [ ] Record the feed or proxy address, pair direction, answer decimals, heartbeat or expected update behavior, access model, and current operational status.
- [ ] Verify the aggregator and proxy state through read-only onchain calls.
- [ ] Confirm whether the product is a standard AggregatorV3-compatible feed usable by `ChainlinkPrices`, a Data Stream, or another product with different integration requirements.
- [ ] Trace Ripe's stale-price, nonpositive-answer, future-timestamp, incomplete-round, decimal-normalization, and feed-disable behavior.
- [ ] Do not infer Robinhood availability from a feed that exists only on another chain.

### Existing reusable adapter

- [ ] Inventory current Ripe price sources and determine whether any existing implementation can price USDG without semantic changes.
- [ ] Record the exact interface, governance path, update mechanism, failure behavior, audit or production history, and required configuration.
- [ ] Reject label-level reuse where the contract's assumptions do not match USDG.
- [ ] Treat a materially changed adapter as a new implementation, not an existing path.

### New fixed/capped adapter

Do not design or implement the final contract in this track. Determine whether this is a viable candidate and enumerate the decisions its separate specification must resolve:

- authoritative reference or fixed-price premise;
- which depeg directions the adapter recognizes;
- cap, floor, or clamp behavior;
- stale, unavailable, disputed, or zero-price behavior;
- governance and update authority;
- timelock, pause, disable, and recovery paths;
- event and monitoring requirements;
- decimal and rounding behavior;
- manipulation and issuer-admin threat models; and
- behavior during market closure, thin liquidity, or venue disagreement.

If a new adapter is the recommended path, the conclusion for enabling the PSM must remain conditional until that adapter has its own approved specification, implementation, review, and tests.

## Phase C: Trace the current PSM behavior

Produce a code-grounded PSM behavior analysis before recommending any price path.

### Reserve and accounting compatibility

- [ ] Verify every six-to-eighteen-decimal conversion against USDG's current token behavior.
- [ ] Trace mint fees, redeem fees, per-interval limits, interval rollover, reserve accounting, rounding, and insufficient-liquidity behavior.
- [ ] Inventory the existing USDC-named storage, methods, events, ABIs, scripts, and operator-facing outputs, then determine whether using those interfaces for USDG is safe and operationally unambiguous or requires a shared, chain-agnostic rename.
- [ ] Identify every user category or allowlist that receives different PSM treatment.
- [ ] Identify the configuration and call paths for minting to GREEN versus SavingsGreen.
- [ ] Identify the configuration and call paths for paying with GREEN versus SavingsGreen.
- [ ] Record any dependency on the separate Phase-0 SavingsGreen decision without deciding that question here.

### Directional price and depeg behavior

Build an explicit behavior table for representative prices below peg, at peg, and above peg—for example `$0.90`, `$1.00`, and `$1.10`—covering:

- regular-user mint output;
- regular-user redemption output;
- mint and redeem maximum views;
- the mint-capacity calculation's `max(usdcFromPriceDesk, usdcInGreenDecimals)` result, including whether available capacity expands or contracts in each depeg scenario;
- fee calculations;
- any privileged or special caller behavior;
- PriceDesk returning zero;
- no registered source;
- stale, disabled, or reverting source; and
- reserve insufficiency.

For every row, cite the exact code path and state whether the result:

- follows market price;
- caps USDG at one dollar;
- floors USDG at one dollar;
- reverts;
- returns zero; or
- depends on another unresolved setting.

Do not assume that symmetric oracle inputs produce symmetric mint and redemption behavior.

### Yield and Base-only integration isolation

- [ ] Prove the configuration needed to make the USDG yield lego ID zero and the yield-vault token the zero address.
- [ ] Resolve the initial `shouldAutoDeposit` state and specify how deployment or governance sets it to `false`.
- [ ] Trace every deposit, withdrawal, available-reserve, emergency, and view path with no yield position configured.
- [ ] Trace any `Deleverage` interaction with the PSM yield-vault token and verify the zero-yield configuration's consequences.
- [ ] Identify any Endaoment funding or withdrawal path that could accidentally inherit Base treasury or partner-liquidity assumptions.
- [ ] Determine whether Underscore-specific PSM privileges—including the unlimited interval mint-capacity bypass—are absent, disabled, or still reachable on Robinhood.

### Enablement and deployment order

- [ ] Verify the constructor defaults for `canMint`, `canRedeem`, `shouldAutoDeposit`, and Department mint authority.
- [ ] Trace the `SwitchboardEcho` governance and timelock path for every required PSM setting.
- [ ] Determine whether a disabled PSM should still be deployed and registered as a GREEN-minting Department or should be omitted entirely.
- [ ] Specify the safe order for deploying or registering the price source, validating price behavior, funding reserves, registering the PSM, and enabling mint or redeem flags.
- [ ] Identify state assertions and smoke checks required before each enablement step.
- [ ] Record the intended economic duration of `numBlocksPerInterval`, but leave block-clock implementation and chain-specific values to the shared clock specification informed by Track 3.

## Phase D: Compare outcomes and recommend a decision

Compare all four price-path outcomes in one decision table:

| Outcome | Existing contracts reused | New shared code | Configuration and deployment work | Primary risks | Required tests | Launch posture |
| --- | --- | --- | --- | --- | --- | --- |
| Existing Chainlink feed | | | | | | |
| Existing reviewed adapter | | | | | | |
| New fixed/capped adapter | | | | | | |
| PSM disabled or omitted | | | | | | |

The recommendation must use one of these conclusions:

- `go — existing feed`;
- `go — existing adapter`;
- `conditional — new adapter specification required`;
- `disabled — deploy but do not enable`;
- `omitted — do not deploy or register`; or
- `blocked — evidence or owner decision missing`.

Do not collapse `disabled` and `omitted`. A deployed and registered PSM has a different authority and operational surface from a component that does not exist.

## Deliverable A: Public evidence

Create:

`docs/chains/rh/usdg-public-evidence.md`

It must include:

- repository branch and full starting commit;
- research and onchain retrieval dates;
- intended networks and chain IDs;
- canonical USDG identity and contract facts;
- observable token administrator and transfer controls;
- standard-feed availability and compatibility evidence;
- existing-adapter inventory;
- reproducible read-only calls;
- source links;
- contradictions, inferences, and unresolved facts; and
- a short statement of what the evidence does and does not establish.

## Deliverable B: Decision record

Create:

`docs/chains/rh/usdg-psm-decision.md`

It must include:

- selected outcome and status;
- evidence summary;
- rejected alternatives and reasons;
- the directional price/depeg behavior table;
- USDG decimal and accounting compatibility;
- whether retaining the USDC-named storage, methods, events, and operational interfaces for USDG is acceptable or requires a shared rename revision;
- exact yield-disabled configuration;
- proposed mint/redeem flags, fees, interval capacities, and allowlist posture, with owner decisions clearly marked;
- SavingsGreen dependency;
- Underscore and Base-only path disposition;
- disabled-versus-omitted decision;
- safe deployment and enablement sequence;
- required `DefaultsRobinhood`, migration, manifest, smoke-script, and test work;
- shared-contract and live-version implications;
- risks, assumptions, and monitoring-state requirements that affect repository interfaces;
- unresolved owner or external decisions;
- required follow-on specifications; and
- the exact `rh-summary.md` items eligible for owner review.

If a numeric launch parameter is not already approved, provide a bounded recommendation or required decision input rather than silently selecting a production value.

## Cross-track interface

- Track 3 owns the canonical component matrix, clock inventory, and component-status terminology. This track supplies the USDG/PSM evidence and recommendation; do not edit Track 3's artifacts in its worktree.
- If Track 3 finishes first, use its stable row and inventory IDs in the decision record. Otherwise mark the references `pending Track 3` and provide an explicit reconciliation list.
- Track 1 owns Chainlink outreach. If USDG feed availability requires a nonpublic Chainlink answer, draft a concise question addendum for the owner to route through Track 1. Do not initiate duplicate outreach.
- Track 2 owns Stock Token transferability and does not block this track.
- The later shared block-clock specification owns the implementation of `numBlocksPerInterval`; this track owns the PSM's intended economic and safety requirements.
- The owner-level SavingsGreen decision controls whether the optional SavingsGreen PSM paths are configured. Document both consequences without deciding the broader component question here.

Do not wait for another track if an explicit `pending Track N` field allows the analysis to continue.

## Approval gates

Stop and obtain owner approval before:

- sending any external question or message;
- selecting a nonpublic or commercially restricted price service;
- implementing or installing a new adapter or oracle dependency;
- changing production contracts, defaults, migrations, or tests;
- deploying, registering, funding, or enabling the PSM;
- using a signing key or broadcasting a transaction; or
- accepting a fixed-price, depeg, administrator-risk, or live-version policy.

Read-only public research and read-only onchain verification may proceed without separate approval.

## Stop conditions

Stop and involve the owner if:

- canonical USDG identity or decimals cannot be verified;
- the intended network lacks canonical USDG;
- a proposed feed address, product, pair direction, or compatibility cannot be verified;
- the only viable path requires a new contract design;
- USDG behavior is incompatible with the PSM's reserve accounting;
- a yield-disabled configuration is not safe under current code;
- an enabled PSM would retain an unintended Base-only or Underscore privilege;
- the result requires a Robinhood-only core contract or `chain.id` branch;
- enabling the PSM requires unresolved issuer, governance, custody, or pricing-risk acceptance; or
- current code contradicts the selected architecture in a way that materially changes scope.

Otherwise, record uncertainty and continue with the remaining analysis.

## Validation

- [ ] Every external claim is dated and tied to a current primary source.
- [ ] Canonical USDG identity is supported by both source evidence and read-only onchain state where possible.
- [ ] Feed availability is verified for the exact network and product interface.
- [ ] Every candidate path is traced through the existing PriceDesk and PSM call flow.
- [ ] The depeg table covers both directions and distinguishes ordinary from special callers.
- [ ] Six-decimal, rounding, fee, interval, reserve, and stale-price behavior are code-grounded.
- [ ] The no-yield configuration is traced through all relevant runtime paths.
- [ ] Disabled and omitted outcomes are analyzed separately.
- [ ] Recommendations and owner approvals are clearly separated.
- [ ] Cross-track pending items have explicit reconciliation instructions.
- [ ] File paths, contract names, fields, and current defaults are verified against the starting commit.
- [ ] Markdown and whitespace checks pass.

## Completion criteria

This track is complete only when:

- both deliverables are complete, current, and reproducible;
- the canonical token and available price paths are verified or precisely blocked;
- current PSM price, reserve, yield-disabled, and enablement behavior is fully traced;
- all four price-path outcomes are compared;
- a clear decision conclusion is recorded without exceeding an approval gate;
- any new-adapter path is handed off to a separate specification rather than implemented;
- the component-matrix and block-clock reconciliation items are explicit; and
- the completion report identifies the exact `rh-summary.md` checkboxes eligible for owner review and closure.

Do not mark any checkbox in `rh-summary.md` yourself.
