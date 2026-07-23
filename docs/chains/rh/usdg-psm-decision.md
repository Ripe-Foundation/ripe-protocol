# Robinhood USDG PSM price-path decision

**Decision:** `go — existing feed`

**Implementation status:** Approval-gated; no Robinhood PSM has been deployed,
registered, funded, or enabled by this track

**Evidence date:** 23 July 2026

**Branch:** `rh-track-4-usdg-psm`

**Starting commit:** `d6efb34b5c28741fb25b053ea9b10af084fe7e53`

## Decision

Use canonical Robinhood USDG and the official standard Chainlink `USDG / USD`
proxy `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` through the existing shared
`ChainlinkPrices` and `PriceDesk` contracts. No Robinhood-only core contract,
`chain.id` branch, new oracle dependency, or new adapter is technically
required.

This is a technical recommendation, not launch authorization. The PSM remains
omitted from Robinhood until the owner approves the issuer/admin risk,
market-price depeg policy, stale-price ceiling, economic parameters,
SavingsGreen disposition, shared live-version/naming work, and implementation
specification below.

If implementation is approved, the selected staging posture is **deploy
disabled, then register without GREEN mint authority**. Do not omit the PSM
after approving the existing-feed implementation, because registration is
needed for governed configuration and the component has an approved
dependency. Do not grant `RipeHq` GREEN-mint authority or enable either user
flag until every precondition in the enablement sequence passes.

## Evidence summary

[`usdg-public-evidence.md`](usdg-public-evidence.md) establishes:

- canonical mainnet USDG at
  `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`;
- canonical testnet USDG at
  `0x7E955252E15c84f5768B83c41a71F9eba181802F`;
- six decimals and exact, fee-free, non-rebasing ordinary ERC-20 transfers;
- observable pause, freeze/wipe, supply, reward, admin, and upgrade controls;
- an official, operational, eight-decimal standard Chainlink USDG/USD proxy on
  Robinhood mainnet with a published 86,400-second heartbeat; and
- no public official Robinhood testnet USDG feed listing.

## Four price-path outcomes

| Outcome | Existing contracts reused | New shared code | Configuration and deployment work | Primary risks | Required tests | Launch posture |
| --- | --- | --- | --- | --- | --- | --- |
| Existing Chainlink feed | `PriceDesk` (CM-015), `ChainlinkPrices` (CM-016), `EndaomentPSM` (CM-048) | No oracle logic | Register only approved source; configure exact proxy and stale ceiling; deploy/configure PSM | Feed/admin availability, stale tolerance, market-price depeg behavior | Real-proxy fork, decimals, failure rounds, PSM depeg/reserve tests | **Selected: `go — existing feed`**, activation gated |
| Existing reviewed adapter | Shared `PriceSource` interface only | Semantic changes would be new code | Would need exact-network product/config | Label-level reuse; mismatched pool/wrapper/oracle premise | Adapter-specific integration/adversarial tests | Rejected; none matches USDG better than the exact feed |
| New fixed/capped adapter | `PriceDesk` routing | Yes | Separate spec, implementation, registration and monitoring | Silent $1 assumption, clamp direction, governance/manipulation/failure policy | Unit/property/fork/depeg/recovery tests | Not needed; would remain conditional |
| PSM disabled or omitted | No price dependency if omitted; shared disabled code if deployed | No | Keep unregistered/absent, or register with both flags and HQ mint authority off | No PSM conversion utility; registered dormant authority if poorly configured | Negative reachability and manifest tests | Current posture until approvals; fallback if any gate fails |

### Fixed/capped adapter disposition

A new shared fixed/capped adapter is technically viable only as a separately
specified fallback if the owner rejects the existing feed. It is not approved
or needed by this decision. Its specification would have to resolve, without
assuming `$1`:

- the authoritative reference or fixed-price premise;
- which upward and downward depegs are recognized;
- any cap, floor, or clamp and its effect on both PSM directions;
- stale, unavailable, disputed, zero-price, and reverting-source behavior;
- update/governance authority and validation;
- timelock, immediate pause, disable, and recovery paths;
- events, state assertions, monitoring, and alert ownership;
- decimal normalization and rounding boundaries;
- market manipulation and issuer-admin/upgrade threats; and
- market-closure, thin-liquidity, and venue-disagreement policy.

Until such a specification, implementation, review, and tests are approved,
that outcome remains `conditional — new adapter specification required`.

## Current PSM accounting

### Decimal compatibility

`EndaomentPSM` treats the reserve as six decimals and GREEN as 18 decimals:

- mint nominal conversion:
  `reserveAfterFee * 10**18 // 10**6`;
- redemption nominal conversion:
  `greenIn * 10**6 // 10**18`;
- `PriceDesk.getUsdValue` reads runtime token decimals and returns 18-decimal
  USD; and
- `PriceDesk.getAssetAmount` reads runtime token decimals and returns reserve
  atomic units.

For USDG's verified six decimals, whole-token conversions are exact. Integer
division rounds down. `PriceDesk.getUsdValue` returns one wei of 18-decimal USD
when a positive numerator is smaller than the token-decimal denominator, but
the PSM's subsequent six-decimal nominal minimum/cap and nonzero assertions
still govern executable dust.

USDG's exact `transfer`/`transferFrom` behavior is compatible. A future token
upgrade that adds fees, rebasing, or non-exact transfers would invalidate this
conclusion and must be a monitored activation invariant.

### Fees, limits, rollover, and liquidity

For a regular user:

- mint fee is `input * mintFee // 10_000`, retained by the PSM;
- redeem fee is `grossReserveOut * redeemFee // 10_000`, retained by the PSM;
- mint interval storage counts GREEN actually minted;
- redeem interval storage counts GREEN paid/burned, not reserve output;
- the mint and redeem buckets are global and independent;
- an interval remains active while
  `start + numBlocksPerInterval > block.number`; equality starts a new bucket;
- multiple calls at the same block number share one capacity bucket; and
- reserve insufficiency after the no-yield withdrawal attempt reverts
  atomically with `insufficient USDC`.

At a 100% fee, the corresponding maximum view returns zero to avoid division by
zero. Actual user operations also reach a zero post-fee amount and revert.

### Directional price behavior

Assumptions for the representative table:

- one USDG input or one GREEN payment;
- zero fees, sufficient balances/reserves, flags enabled, no allowlist, and an
  ordinary recipient;
- `C` is remaining GREEN interval capacity;
- `R` is available USDG reserve units expressed as whole tokens; and
- floor division may remove atomic dust.

Code paths are `EndaomentPSM.vy:219-276,285-306` for mint,
`:374-441,450-476` for redemption/maxima, and
`PriceDesk.vy:79-124,142-187` for conversion/routing.

| USDG oracle price | Regular mint for 1 USDG | Regular redeem for 1 GREEN | Regular max mint input before user-balance cap | Regular max redeem payment before user-balance cap | Classification |
| ---: | ---: | ---: | ---: | ---: | --- |
| `$0.90` | `0.90 GREEN` | `1.00 USDG` | `max(C / 0.90, C) = 1.111111… C USDG`; input capacity expands, but output remains capped at `C` GREEN | `min(C, 0.90 R GREEN)` | Mint follows market; redemption floors USDG at `$1`; reserve-side capacity contracts |
| `$1.00` | `1.00 GREEN` | `1.00 USDG` | `C USDG` | `min(C, R GREEN)` | At peg |
| `$1.10` | `1.00 GREEN` | `0.909090… USDG` | `max(C / 1.10, C) = C USDG`; no contraction because nominal branch wins | `min(C, R GREEN)` | Mint caps USDG at `$1`; redemption follows market; reserve capacity capped nominally |

The apparent below-peg max-mint expansion is deliberate accounting: more
below-peg USDG may enter, while the price-valued GREEN minted remains bounded
by the interval. It is not an expansion of GREEN capacity.

Fees apply after choosing the directional price:

- mint maximum gross-up:
  `baseReserveCapacity * 10_000 // (10_000 - mintFee)`;
- actual mint values only `reserveAfterFee`;
- redeem maximum gross-up:
  `maxGreenBackedByReserve * 10_000 // (10_000 - redeemFee)`; and
- actual reserve output then deducts the fee.

The maximum views may be one atomic unit conservative/optimistic around integer
division. Implementation tests must assert the last executable unit and first
reverting unit at each selected fee.

### Failure and special-case matrix

| Condition | Mint execution / max view | Redeem execution / max view | Result |
| --- | --- | --- | --- |
| No source registered anywhere | Strict mint pricing returns zero rather than raising; mint reverts `zero mint amount`. Mint max uses nominal `C` because `max(0, nominal)`. | Strict redemption cannot proceed because reserve-backed max is zero; max view is zero | Execution disabled by zero, but mint max alone is misleading |
| Feed configured but stale/nonpositive/future/incomplete | `ChainlinkPrices` returns zero with `hasFeed=true`; strict mint raises `has price config, no price`. Mint max still uses nominal `C` | Reserve max is zero; redemption reaches zero amount. Direct strict conversion would raise | Zero/revert fail closed |
| Feed or PriceDesk source confirmed disabled | The feed/source is absent, so behavior matches “no source”: mint reverts on zero output while mint max reports nominal `C` | Max view is zero; execution cannot obtain a nonzero payment allowance | Returns zero, then user path reverts |
| Price-source call itself reverts | Revert propagates through `PriceDesk` | Revert propagates | Reverts |
| Price source is `PriceSourceData.pause(true)` only | Reads continue; pause is not checked by `getPrice` | Reads continue | **Not a runtime oracle kill switch** |
| PSM contract paused | Both user operations fail before pricing | Both user operations fail before pricing | Immediate stop via `SwitchboardCharlie.pause` |
| Insufficient idle reserve, no yield configured | Not relevant to mint; received USDG remains idle | Internal yield withdrawal returns zero, then balance assertion fails | Reverts atomically |
| Mint/redeem allowlist enabled | Checks `msg.sender` for ordinary recipient | Checks `msg.sender` for ordinary recipient | Depends on owner-selected allowlist |
| SavingsGreen requested/payment | Uses ERC-4626 path only if deployed/configured; mint falls back to direct GREEN at `<= 1 GREEN` | Converts max GREEN to shares, transfers shares, redeems to GREEN, then burns GREEN | Depends on unresolved SavingsGreen decision |
| Recipient is recognized Underscore earn vault | No fee or allowlist; unlimited mint input capacity; still `min(market, $1)` output pricing | No fee/allowlist/interval; `max(market reserve amount, 1:1)` output; still reserve-limited | Forbidden privilege on Robinhood |

The external max-view boolean `_isUnderscoreVault` is caller-supplied and is
not authorization. Operator tools must never treat a `true` view result as
proof that an address has runtime privilege.

## USDG naming disposition

Passing USDG through the existing `USDC` immutable and six-decimal arithmetic
is mechanically safe, but the current interfaces are operationally ambiguous:

- contract storage/getters and method arguments use `USDC`/`usdc`;
- events expose `usdcIn`, `usdcOut`, and `usdcFee`;
- the checked-in `EndaomentPSM` ABI preserves those labels;
- `Endaoment.transferFundsToEndaomentPSM` asks the PSM for `USDC()`;
- `Deleverage` calls `getUsdcYieldPositionVaultToken()`;
- `SwitchboardEcho` exposes `setPsmUsdcYieldPosition` and
  `transferUsdcToEndaomentFundsInPsm`;
- `scripts/params/general.py` prints `USDC Address` and
  `usdcYieldPosition`; and
- `scripts/params/params_utils.py` documents USDC-specific decimals.

**Decision:** a shared, chain-agnostic reserve-asset naming revision is
required before Robinhood operator tooling is considered launch-ready. Do not
fork or rename only the Robinhood contract.

The follow-on shared specification should preserve legacy Base ABI selectors
where compatibility requires them, add canonical reserve-asset aliases/output,
make manifests and operator reports display the actual token symbol/address,
and define whether new generic events are emitted alongside legacy events.
Full selector/event replacement is a live-version decision and is not
authorized here.

## Yield-disabled and Base-only isolation

### Required immutable/deployment state

Deploy `EndaomentPSM` with:

```text
reserve asset = canonical USDG
_usdcYieldLegoId = 0
_usdcYieldVaultToken = 0x0000000000000000000000000000000000000000
canMint = false                 # constructor behavior
canRedeem = false               # constructor behavior
shouldAutoDeposit = true        # constructor behavior; must be changed below
```

Both yield fields must be zero in constructor inputs. The constructor stores a
position only when both are nonzero. `SwitchboardEcho.setPsmUsdcYieldPosition`
rejects `legoId == 0`, so governance cannot use that wrapper to clear an
accidentally inherited Base position. Reject the deployment before
registration if either field is nonzero.

After registry insertion but before funding or feature enablement, execute and
confirm the timelocked `setPsmShouldAutoDeposit(false)` action. Assert all
three values after confirmation.

With `(0, zero)`:

- automatic and explicit internal deposits return zero before approvals or
  external calls;
- internal withdrawals return zero;
- the external `withdrawFromYield` wrapper reverts `zero amount`;
- `getUnderlyingYieldAmount()` returns zero;
- `getAvailableUsdc()` is exactly the idle USDG balance;
- redemption cannot synthesize liquidity and reverts if idle USDG is short;
- `Deleverage` sees a zero PSM yield-vault token, so its special branch that
  routes matching collateral to the PSM is unreachable; and
- no Underscore lego lookup can service a yield call.

The inherited generic `DeptBasics.recoverFunds` path can recover USDG without
using a yield position and does not require the PSM to be unpaused; the
`SwitchboardCharlie` recovery action is governance-timelocked. By contrast,
`transferUsdcToEndaomentFunds` requires the PSM to be unpaused and a valid Ripe
caller. The recovery runbook must distinguish these paths and must never treat
Base Endaoment routing as the Robinhood emergency default.

### Underscore

`DefaultsRobinhood.underscoreRegistry()` must return zero, the Robinhood
manifest must omit Underscore registry/lego/vault addresses, and
`MissionControl.underscoreRegistry()` must be asserted zero before each
enablement. With zero, `_isUnderscoreVault` returns false before any external
registry call, so the unlimited mint-capacity, fee, allowlist, and interval
bypasses are unreachable.

The zero value is governed mutable state, not a permanent code invariant.
Monitoring must alert on any nonzero change and the PSM must be paused before
such a change can become effective.

### Endaoment and treasury paths

Do not deploy/register Base-only `Endaoment`, partner-liquidity, Curve,
Aerodrome, or Underscore routes merely to fund the PSM. The existing
`Endaoment.transferFundsToEndaomentPSM` pulls the reserve address from the PSM
and can transfer EndaomentFunds balances, but it also imports Base treasury
surface. Robinhood funding should use a narrowly specified governance/custody
funding step and confirm the exact USDG balance delta.

The PSM's own `transferUsdcToEndaomentFunds` remains callable by any valid Ripe
address and is not yield-dependent. The Robinhood component/registry spec must
either deploy the required generic EndaomentFunds recovery destination and
constrain callers, or revise the shared recovery surface. It must not
accidentally install the full Base Endaoment feature set.

## SavingsGreen dependency

This track does not decide whether CM-003 SavingsGreen is deployed.

- If SavingsGreen exists, test both direct GREEN and ERC-4626 mint/payment
  paths, share rounding, the strict `greenToMint > 1e18` threshold, approvals,
  and failure atomicity.
- If SavingsGreen is omitted, user interfaces and smoke scripts must always
  pass `_wantsSavingsGreen=false` and `_isPaymentSavingsGreen=false`.
  Implementation tests must prove `true` fails closed without affecting the
  ordinary GREEN paths. A valid zero/sentinel registry strategy for RipeHq
  token slot 2 must come from the owner-level SavingsGreen decision.

## Configuration recommendation and owner inputs

No numeric production fee or capacity was approved by this track.

| Setting | Staging value/posture | Activation bound or required input | Owner gate |
| --- | --- | --- | --- |
| `canMint` | `false` | Enable only after HQ authority sequence passes | Yes |
| `canRedeem` | `false` | Enable only after reserve funding and redemption smoke | Yes |
| `mintFee` / `redeemFee` | Constructor values must be explicitly recorded; no silent Base copy | Owner supplies `0..10,000` bps; implementation must test selected value and 100% fail-closed edge | Yes |
| `maxIntervalMint` | Nonzero constructor placeholder, but no authority/flag | Must be no more than the approved GREEN exposure increase per economic interval | Yes |
| `maxIntervalRedeem` | Nonzero constructor placeholder, but flag off | Must be no more than the lesser of approved outflow and immediately funded idle reserve after fee/price stress | Yes |
| `numBlocksPerInterval` | Track 3 provisional `7,200` | Intended economic duration is one day; final value belongs to shared clock spec using BN-027/BN-028 | Yes |
| Mint/redeem allowlists | Enforced during initial canary unless owner explicitly approves public access | Seed only approved canary addresses; sender is checked | Yes |
| Feed stale time | No silent default | Owner approves a positive ceiling around the published 86,400-second heartbeat; both global and feed settings must be at or below that ceiling because code takes `max` | Yes |
| Sequencer/restart policy | No separate uptime feed is present in the current public RDD or current Ripe adapter | Owner approves monitoring and post-restart freshness/soak assertions before activation | Yes |
| Yield | `(0, zero)`, auto-deposit `false` | No other value allowed | Architecture invariant |
| Underscore | registry zero | No other value allowed | Architecture invariant |

Cap inputs must be derived from an owner-approved loss/exposure envelope,
funded reserve, expected block cadence, and emergency response time. This track
does not invent those economic numbers.

## Governance and safe deployment order

`SwitchboardEcho` initiates a timelocked action for every PSM setting and
governance executes it after confirmation. Lite access may initiate
`canMint=false`, `canRedeem=false`, or `shouldAutoDeposit=false`; enabling or
economic changes require governance. `SwitchboardCharlie.pause` provides an
immediate PSM-wide pause for an authorized lite signer; unpause requires
governance. `RipeHq` separately gates GREEN mint authority through a
registry-timelocked HQ config, creating two-factor mint authorization.

The safe order is:

1. **Freeze inputs.** Pin canonical USDG proxy/implementation/code hashes,
   Chainlink proxy/aggregator/round, Ripe release commit, Track 3 matrix, and
   final owner-approved parameters. Abort on drift pending review.
2. **Deploy/configure pricing first.** Deploy shared `ChainlinkPrices` if not
   already part of the Robinhood inventory, register only approved price
   sources in `PriceDesk`, and timelock-add canonical USDG with the exact
   standard proxy, `needsEthToUsd=false`, `needsBtcToUsd=false`, and approved
   stale time.
3. **Validate pricing while no PSM exists.** Assert pair, decimals, positive
   complete round, timestamp, effective stale time, normalization to
   18 decimals, source priority, no competing USDG source, and expected zero /
   strict-revert behavior for mock failure states. Note that
   `PriceSourceData.pause` is not a read kill switch.
4. **Deploy PSM disabled and unregistered.** Constructor inputs must use
   canonical USDG, owner-recorded nonzero bounded caps/interval, and
   `(yieldLegoId=0, vaultToken=zero)`. Assert `canMint=false`,
   `canRedeem=false`, `shouldAutoDeposit=true`, exact reserve address, code
   hash, and zero balance.
5. **Register address without mint authority.** Insert it at the canonical
   EndaomentPSM registry slot (Track 3 CM-048 / current `Addys` ID 22). Keep HQ
   config `canMintGreen=false`, `canMintRipe=false`, and
   `canSetTokenBlacklist=false`. This registration is needed so
   `SwitchboardEcho` resolves the target.
6. **Finish disabled configuration.** Timelock-confirm
   `shouldAutoDeposit=false`, fees, caps, interval, and allowlists. Reassert
   `(0, zero)`, `MissionControl.underscoreRegistry()==zero`, both flags false,
   no pending actions, and no Base addresses in the manifest.
7. **Fund only after disabled-state smoke checks.** Transfer the exact
   owner-approved canonical USDG amount through the approved custody path.
   Compare sender/PSM balance deltas exactly and recheck token pause/freeze,
   implementation, source, and price.
8. **Redeem canary, if approved.** With HQ mint authority still false, enable
   only redemption through its timelock, execute a bounded allowlisted
   GREEN-to-USDG smoke, verify fee/output/burn/reserve/event deltas, then
   disable again until production approval.
9. **Mint canary, if approved.** Keep HQ mint authority false; timelock-enable
   the PSM's `canMint`, verify that actual GREEN minting still fails atomically
   at the RipeHq gate, then initiate/confirm HQ `canMintGreen=true` last.
   Execute one bounded allowlisted USDG-to-GREEN smoke and verify every delta.
10. **Public activation is a separate gate.** Change allowlist posture and
    production flags only after canary review. Monitor token implementation,
    pause/freeze/admin roles, feed aggregator/round age/answer, effective stale
    time, PSM flags/caps/buckets/reserve, HQ authority, yield fields,
    auto-deposit, and Underscore registry.

Emergency order is: immediately pause `EndaomentPSM` through
`SwitchboardCharlie`; if mint-system-wide danger exists, disable
`RipeHq.mintEnabled`; then initiate the slower PSM flag, HQ authority, feed, or
source disable actions as appropriate. Oracle module pause alone is
insufficient.

## Exact follow-on repository work

All changes below require a separately approved implementation specification:

1. Add chain-data-only `contracts/config/DefaultsRobinhood.vy` (CM-049), with
   canonical USDG, zero Underscore, no Base DEX/yield/treasury addresses, an
   owner-approved price stale time, and Track 3 clock values.
2. Extend the blueprint/deploy-argument layer for Robinhood mainnet/testnet;
   current `config/BluePrint.py` and `scripts/migrate.py` enumerate Base/Ethereum
   environments and are not Robinhood-ready.
3. Add Robinhood migration directories and manifests that deploy the same
   selected shared bytecode, configure CM-015/CM-016, deploy CM-048 with
   `(0, zero)`, register it without HQ mint authority, and encode the staged
   order above. Never copy
   `migrations/base-mainnet/2026011400_EndaomentPSM.py`, which hardcodes Base
   USDC, lego 13, a Base vault token, and 43,200 blocks.
4. Add explicit address/parameter manifest validation rejecting Base USDC,
   Base Chainlink proxy, any Base yield vault/lego, Curve/Aerodrome, Endaoment
   partner routes, and nonzero Underscore on Robinhood.
5. Implement the approved shared reserve-asset naming/ABI/operator-output
   revision; regenerate `scripts/abis/EndaomentPSM.json`,
   `scripts/abis/Endaoment.json`, `scripts/abis/SwitchboardEcho.json`, and any
   affected shared ABI.
6. Update `scripts/params/general.py`, `params_utils.py`, deployment/price
   reports, and smoke output to say USDG or generic reserve asset based on the
   actual token. Remove the hardcoded “USDC Address” interpretation.
7. Add unit/property tests for `$0.90/$1.00/$1.10`, fee/cap boundary rounding,
   no source, configured-zero, stale, future, incomplete, disabled, and
   reverting feeds; exact last-unit interval capacity; insufficient idle
   reserves; and 100% fee behavior.
8. Add canonical testnet-USDG plus clearly labeled mock-feed tests, and a
   pinned mainnet-fork integration test against
   `0x61B7…9aD2`, including 8-to-18 feed and 6-to-18 token normalization.
9. Add issuer-control mocks/tests for pause, freeze/blocklist, wipe/burn,
   supply changes, and implementation drift. Prove atomic failure for both PSM
   directions.
10. Add no-yield/Underscore/Base-isolation tests covering auto-deposit,
    explicit deposit/withdraw/view/reserve paths, Deleverage's zero-token
    routing branch, forbidden privileged max-view use, and manifest
    reachability.
11. Add staged deployment smoke scripts with read-only preflight mode and
    separate approval/broadcast mode. Assertions must cover the sequence above
    and emit no secrets.
12. Run full Base regression tests because naming/live-version changes are
    shared. Record temporary or permanent Base-versus-Robinhood bytecode drift
    in the owner-approved component matrix; this track approves none.

## Tests run for this decision

The six contract suites required by the brief were executed from the isolated
worktree:

```text
226 passed:
  test_endaoment_psm_mint.py
  test_endaoment_psm_redeem.py
  test_endaoment_psm_config.py
  test_endaoment_psm_views.py
  test_transfer_funds_to_endaoment_psm.py

18 passed:
  test_chainlink_prices.py

62 passed (additional governance/isolation confidence):
  test_switchboard_echo.py
  test_deleverage_specific_assets.py

19 passed (additional mint-authority confidence):
  test_ripe_hq.py
```

The initial Chainlink run could not write Titanoboa's default compiler cache
under the sandbox. It was rerun unchanged with `boa.interpret.set_cache_dir`
pointing to `/tmp/ripe-track4-titanoboa`; all 18 tests passed. No production or
test file was edited.

Existing tests cover much of the generic behavior, including depeg direction,
fees, interval rollover, SavingsGreen, privileged recipients, no-yield views,
staleness, decimals, round/timestamp validation, and timelocks. They do not
replace the Robinhood/USDG-specific follow-on tests listed above.

There is no standalone PriceDesk test file at the starting commit. Its
conversion and routing paths are exercised transitively by the PSM and price
source suites; the follow-on work above requires explicit PriceDesk-level USDG
failure and rounding coverage.

## Cross-track reconciliation

Track 3 is clean at commit
`19111bf1735d8e921276570c656107b53e8578ee`. Reconcile this decision into its
stable inventory as follows:

| Track 3 ID | Reconciliation |
| --- | --- |
| CM-015 `PriceDesk` | Remains `reused unchanged`; configure only approved Robinhood sources |
| CM-016 `ChainlinkPrices` | Resolve “any approved USDG feed” to the official mainnet proxy in this record; source remains unchanged |
| CM-048 `EndaomentPSM` | Change dependency from unresolved to technically approved existing feed; retain `deferred` until owner risk/parameter/implementation gates pass; stage deployed/registered disabled |
| CM-049 `DefaultsRobinhood` | Add canonical USDG, zero yield/Underscore, approved stale time, and no Base addresses |
| BN-027 / BN-028 | Intended duration remains one economic day; provisional `7,200` is not accepted here and must be finalized by the shared clock specification |

Track 1 outreach is unnecessary for USDG feed availability because current
public official evidence answers the question. Track 2 does not block this
decision. The owner-level SavingsGreen decision remains a dependency.

## Owner approvals still required

Stop before implementation or external state change. The owner must separately
approve:

- observable USDG issuer/admin/upgrade risk;
- current asymmetric market-price depeg behavior;
- the effective stale-price ceiling and monitoring policy;
- mint/redeem fees, capacities, interval value, initial reserve, and allowlists;
- SavingsGreen deployed/omitted behavior;
- deployed-and-registered-disabled posture and the exact authority sequence;
- the shared reserve naming/live-version revision; and
- the implementation/test/smoke specification.

If any approval is declined or any pinned identity/interface changes, fallback
is `omitted — do not deploy or register` until a revised decision is approved.
A fixed/capped adapter is not an implicit fallback.

## `rh-summary.md` items eligible for owner review

Do not mark these in this track. After reviewing this record, the owner may:

1. close `rh-summary.md:89-93`, **“Resolve the USDG price path”**, by approving
   `existing Chainlink feed`;
2. close the research/decision portion of `rh-summary.md:205`, **“Keep the
   existing USDC-named storage, methods, and events only if…”**, by accepting
   the required shared naming revision rather than accepting ambiguity; and
3. treat the evidence/analysis portion of `rh-summary.md:290`, **“USDG pricing
   and PSM behavior are validated…”**, as review-complete, while leaving the
   checkbox open until Robinhood-specific implementation tests or a verifiably
   disabled deployment pass.

Items `204`, `206-211`, and the overall section exit condition are **not**
eligible for closure: no deploy, config, funding, implementation, or
Robinhood-specific runtime test was authorized or performed.
