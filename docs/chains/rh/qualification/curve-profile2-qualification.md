# Robinhood Curve and Profile 2 qualification

**Evidence date:** 30 July 2026  
**Status:** read-only architectural qualification; no live fork, RPC, pool,
deployment, registration, configuration, or activation was performed  
**Frozen Ripe commit:** `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`  
**Frozen Ripe tree:** `b68dffdddbdc7c5ae8423db049099c1632b478c9`

## 1. Executive recommendation

Launch **Profile 1 only**. Keep Curve absent from `PriceDesk` ID 2, leave
dynamic rates on their existing base-rate fallback, leave the Curve
stabilizer disabled, and preserve Chainlink as the only PSM price authority.

Qualify **Profile 2 shortly after launch** as a separately authorized
follow-on. Its first live-capable stage should be observation-only: discover
or construct the pool only in a disposable fork, exercise it, and read its
state without registering `CurvePrices` in `PriceDesk`. Promotion to a
protocol price source, dynamic-rate producer, Teller reference-snapshot
producer, or Endaoment stabilizer requires separate acceptance of each
downstream capability.

`CurvePrices.vy` should remain unchanged. The official Robinhood Curve graph
matches the registries the shared source already understands. A
Robinhood-specific adapter would duplicate registry and pool semantics without
fixing the real qualification issue: Robinhood's EVM `block.number` is a
periodically updated estimate of the Ethereum L1 number. Unchanged
`CurvePrices` is acceptable only if Profile 2 deliberately uses that
L1-derived number as its snapshot/staleness/danger clock and the complete
repeated-number and jump matrix below passes. Failure to reproduce all clock
surfaces is a stop condition, not a reason to patch around the fork engine.

The current official Curve Robinhood manifest has `pools: null` and
`tokens: null`. It proves infrastructure, not a USDG/GREEN pool. Therefore:

- a pool must not be guessed from an address or token labels;
- the 100 USDG + 100 GREEN seed matches Base migration quantities and is the
  deterministic fork vector, but does not by itself approve Robinhood
  production-liquidity sufficiency;
- a live pool discovered later is acceptable only after its factory lineage,
  implementation, parameters, coin ordering, LP identity, admin and custody
  are proven;
- `B-LP-ARTIFACTS` and `B-ORACLE-FREEZE` already make the launch LP a hard
  stop. I recommend formally reopening M0 decision 9 and moving both LP
  activations to Profile 2; until the owner approves that governance change,
  Profile 1 launch remains blocked. This report does not make the change.

### Option disposition

| Option | Disposition | Reason |
| --- | --- | --- |
| Profile 1 only at launch | **Recommend** | Preserves the reviewed empty ID 2, base-rate fallback, disabled stabilizer and Chainlink PSM authority. |
| Profile 2 at launch | **Reject** | No qualified USDG/GREEN identity, live graph proof, custody decision, four-clock fork proof or final owner parameters exist. |
| Profile 2 shortly after launch | **Recommend, gated** | Captures the useful market and stabilization evidence without expanding launch blast radius. |
| Curve observation-only | **First Profile 2 stage** | Reads pool state and compares outputs without giving Curve protocol authority. |
| Curve as protocol price source | **Conditional later stage** | Requires explicit per-asset `PriceDesk` ordering and all downstream rate/snapshot/stabilizer gates. |
| Unchanged `CurvePrices` | **Recommend conditionally** | Registry graph is compatible; the L1-derived clock semantics must be intentional and proven. |
| Robinhood-specific Curve adapter | **Do not implement** | No registry incompatibility is established; it would create new source, artifact and audit surface. |
| No Curve integration | **Permanent fallback** | Safe if any graph, pool, clock, liquidity, admin or owner gate fails; PSM remains functional through Chainlink. |

## 2. Exact baseline and authoritative sources

### Baseline

The isolated worktree was created from the exact frozen commit on
`codex/rh-curve-profile2-qualification`, and its root was mode `0700`.
`HEAD^{tree}` matched the requested tree before research began. The primary
worktree remained on `rh...origin/rh` and clean.

At this baseline:

- `CurvePrices`, `PriceDesk`, `CreditEngine`, `Teller`, `Endaoment`, and
  `EndaomentPSM` declare Vyper `0.4.3`; this documentation-only task did not
  rebuild them;
- the canonical production Vyper inventory contains **99 exact `block.number`
  occurrences on 94 lines in 17 files**. This is the enforcing
  `config/block-clock-inventory.json` population, which excludes both
  `contracts/mock/**` and `contracts/testing/**`; the testing-only
  `ActionBlockIdentityProbe.vy` contributes a separate 2 occurrences / 2
  lines / 1 file and must not be relabeled production;
- four occurrences are in `CurvePrices.vy`: staleness, same-number
  suppression, danger elapsed-number accumulation, and snapshot update;
- Robinhood profiles exist for mainnet chain ID `4663` and testnet chain ID
  `46630`, but their shared migration path and separate history paths are
  `proposed`; Robinhood repository reads, migration forks, console evidence,
  verification, and live migration remain `blocked_pending_policy`.

### Primary sources

Official external sources used:

- [Curve Robinhood deployment manifest at the pinned curve-core commit](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/deployments/prod/robinhood.yaml)
  and the [current manifest](https://github.com/curvefi/curve-core/blob/main/deployments/prod/robinhood.yaml).
  On 30 July 2026 the pinned and fetched `origin/main` paths both resolved to
  Git blob `7789bfe2dc8130bc92071fa960e273924ed05c4b`; the file SHA-256 was
  `167828674a73459da927fc616c3804d05cd61129332e995229a597920109096d`.
  That exact content declared no pools or tokens.
- [curve-lite at `5a9e1ab34c1319de69b987900d859ad2e965d0e2`](https://github.com/curvefi/curve-lite/tree/5a9e1ab34c1319de69b987900d859ad2e965d0e2),
  including the
  [StableSwapNG factory](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/amm/stableswap/factory/factory_v_100.vy),
  [v7 implementation](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/amm/stableswap/implementation/implementation_v_700.vy),
  [AddressProvider](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/registries/address_provider/address_provider_v_201.vy),
  [MetaRegistry](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/registries/metaregistry/metaregistry_v_110.vy),
  and registry handlers.
- Curve's pinned
  [AddressProvider update](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/scripts/deploy/registries/address_provider.py),
  [MetaRegistry update](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/scripts/deploy/registries/metaregistry.py),
  and [StableSwap deployment](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/scripts/deploy/amm/stableswap.py)
  scripts.
- Robinhood's official [chain overview](https://docs.robinhood.com/chain/),
  [contract list](https://docs.robinhood.com/chain/contracts/),
  [Ethereum differences](https://docs.robinhood.com/chain/differences-from-ethereum/),
  [protocol contracts](https://docs.robinhood.com/chain/protocol-contracts/),
  and [transaction finality](https://docs.robinhood.com/chain/transaction-finality/).
- Vyper's versioned [0.3.10 contract/pragma documentation](https://docs.vyperlang.org/en/v0.3.10/structure-of-a-contract.html),
  official [compiler outputs and storage-layout documentation](https://docs.vyperlang.org/en/stable/compiling-a-contract.html),
  and official
  [`create_from_blueprint` semantics](https://docs.vyperlang.org/en/latest/built-in-functions.html#create-from-blueprint).
- Paxos's official [Robinhood USDG deployment entry](https://docs.paxos.com/guides/stablecoin/usdg/mainnet)
  and [USDG contract repository](https://github.com/paxosglobal/usdg-contract).

Ripe authority used from this exact tree:

- `contracts/priceSources/CurvePrices.vy`;
- `contracts/registries/PriceDesk.vy`;
- `contracts/core/CreditEngine.vy`, `Teller.vy`, `Endaoment.vy`, and
  `EndaomentPSM.vy`;
- `tests/priceSources/curve/`, `tests/core/creditEngine/test_credit_dyn_rate.py`,
  `tests/core/endaoment/test_endao_stabilizer.py`, and Teller tests;
- `config/BluePrint.py` and
  `migrations/base-mainnet/2001_CurvePools.py` for the shipped Base Curve
  precedent;
- `config/block-clock-inventory.json`,
  `scripts/check_block_clock_inventory.py`, `docs/chains/rh/status.yaml`, and
  `docs/chains/rh/block-number-inventory.md` for the canonical clock boundary;
- `config/network_profiles.py` and `config/robinhood_blueprint.py`;
- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`,
  `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`,
  `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`,
  `docs/chains/rh/robinhood-deployment-validation-plan.md`,
  `docs/chains/rh/usdg-public-evidence.md`, and
  `docs/chains/rh/usdg-psm-decision.md`.

The machine inventory controls the 99/94/17 figure; dated prose is contextual
evidence and does not supersede that gate. The checker returned
`CLOCK_INVENTORY_OK` at this frozen tree.

### Research checkout disclosure

Official Curve source was inspected in two clean detached local clones:

- `/private/tmp/curve-core-rh-qualification` at
  `6222dda9959091db94d61f6d6378234a624cdd66`;
- `/private/tmp/curve-lite-rh-qualification` at
  `5a9e1ab34c1319de69b987900d859ad2e965d0e2`.

The clone utility initially created both roots as mode `0755`; review caught
that process residue and their roots were tightened to `0700`. They are clean,
read-only research residue outside the Ripe worktree, not deliverables or Ripe
modifications. No dependency was installed and no artifact was built from
them in this task.

## 3. Curve deployment/artifact graph

### Required AddressProvider bindings

The official AddressProvider is
`0x4574921eb950d3Fd5B01562162EC566Cb8bc3648`. The complete official binding
set and its relevance are:

| ID | Required address | Meaning | Ripe relevance |
| ---: | --- | --- | --- |
| 2 | `0xFF5Cb29241F002fFeD2eAa224e3e996D24A6E8d1` | Exchange Router | Graph proof only |
| 4 | `0x193110Ce1542d7371e1515BD6A2E470fDefc310D` | Fee Distributor / DAO vault | Fee/custody proof |
| 7 | `0xe6dA14500f0b5783E2325F9C5a7eE5d99DA0fB42` | MetaRegistry | Read directly by `CurvePrices` |
| 11 | `0x6E28493348446503db04A49621d8e6C9A40015FB` | TricryptoNG factory | Cached by `CurvePrices` |
| 12 | `0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD` | StableSwapNG factory | Pool factory; cached by `CurvePrices` |
| 13 | `0xe7FBd704B938cB8fe26313C3464D4b7B7348c88C` | TwoCryptoNG factory | Cached by `CurvePrices` |
| 18 | `0x129578f94C253b8Bc903Bf2b73D07BF2583cc11d` | Spot Rate Provider | Graph proof only |
| 20 | `0x41D2c5128A7241EC1f7CE346B162C347C19548B7` | Child Gauge Factory | MetaRegistry constructor relation |
| 21 | `0xabc336d4C71ad275695744d32DdB1d8266Db1cbF` | Ownership Admin | Authority proof |
| 22 | `0xabc336d4C71ad275695744d32DdB1d8266Db1cbF` | Parameter Admin | Authority proof |
| 23 | `0xabc336d4C71ad275695744d32DdB1d8266Db1cbF` | Emergency Admin | Authority proof |
| 24 | `0x193110Ce1542d7371e1515BD6A2E470fDefc310D` | CurveDAO vault | Custody proof |
| 26 | `0xB2Be7692B07b640C9f2ee1187cee2fAec741F872` | Deposit-and-stake zap | Graph proof only |
| 27 | `0x2AF43209B366A4491CCe0A97C5a7B6059fd21295` | StableSwap meta zap | Graph proof only |

IDs 19 (CRV) and 25 (crvUSD) are null in the Robinhood configuration and are
not added. IDs 0, 1, 3, 5, 6, 8, 9, 10, 14, 15, 16, and 17 are unbound by the
official update script. `CurvePrices` intentionally tolerates empty legacy
IDs 3 and 6. A live fork must enumerate every existing ID and reject an
unexpected nonzero binding, not merely check the six IDs the Ripe constructor
reads.

### Registry and implementation closure

The minimum relevant closure is:

```text
AddressProvider 0x4574...3648
└── ID 7 MetaRegistry 0xe6dA...fB42
    ├── registry[0] StableSwap handler 0x46FE...a4aE
    │   └── base registry / factory 0x8271...E8aD
    │       ├── pool_implementations[0] 0xFC68...C2df (v7 blueprint)
    │       ├── metapool_implementations[0] 0x845b...21BF
    │       ├── math 0xe460...3650
    │       └── views 0xC945...93c0
    ├── registry[1] Tricrypto handler 0xBBbe...4dD6
    │   └── factory 0x6E28...5FB → blueprint 0x2861...C1f
    └── registry[2] TwoCrypto handler 0x7e59...c934
        └── factory 0xe7FB...c88C → blueprint 0x5F87...4f94
```

For H-07, an address match is insufficient. The evidence bundle must bind:

1. curve-core commit `6222dda9959091db94d61f6d6378234a624cdd66`;
2. every manifest `contract_github_url`, including the curve-lite commit or
   exceptional source commit declared by that row;
3. exact source closure and imports;
4. compiler `0.3.10`, EVM target `shanghai`, and the exact optimization mode;
5. ABI, creation bytecode, runtime bytecode, and runtime code hash;
6. ERC-5202 blueprint preamble `0xFE7100`, blueprint initcode identity, and
   `code_offset=3`;
7. constructor encoding and decoded constructor values;
8. factory implementation pointers, math/views pointers, fee receiver and
   admin;
9. MetaRegistry length/order, each handler constructor/base-registry pointer,
   and AddressProvider reverse bindings;
10. the pool's factory row, implementation pointer, coin list, parameter
    getters, LP-token relation, deployment event/index and runtime hash.

Several manifest rows record optimization as `UNKNOWN`. H-07 therefore needs
verified compiler input or a reproducible byte-for-byte build; choosing a
default optimization mode is not allowed. Any missing closure or mismatch is
`RB-H07-CURVE-GRAPH`.

## 4. USDG/GREEN pool specification

### Identity and construction

Canonical Robinhood USDG is
`0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, a six-decimal upgradeable
token. GREEN must be the exact final Robinhood deployment identity; it is not
available from the Curve manifest.

The candidate is a two-coin StableSwapNG plain pool created through
`0x8271...E8aD.deploy_plain_pool`:

| Input | Qualified candidate |
| --- | --- |
| Name / symbol | Owner-fixed strings within factory limits (`String[32]`, `String[10]`); exact bytes are identity inputs |
| Coin 0 | canonical USDG |
| Coin 1 | final GREEN |
| `A` | `100` |
| `fee` | `4_000_000` = 0.04% at 1e10 precision |
| `offpeg_fee_multiplier` | `20_000_000_000` = 2x; approximately 0.08% maximum dynamic fee at extreme imbalance |
| `ma_exp_time` | **`600` minimum-change candidate**, matching the shipped Base migration; separately test `866`, which is the correct input only if the owner explicitly requires a 600-second EMA half-life (`600 / ln(2)`) |
| implementation index | `0`, only after getter proves the pinned v7 blueprint |
| asset types | `[0, 0]` (standard ERC-20) |
| method IDs | `[0x00000000, 0x00000000]` |
| rate oracles | `[zero, zero]` |
| derived multipliers | USDG `10^30`; GREEN `10^18`, subject to live decimals proof |
| default D oracle window | `62_324`, approximately a 12-hour half-life; assert after construction |

USDG-first ordering makes `price_oracle(0)` the GREEN-in-USDG observation that
the shared adapter expects when GREEN is coin 1. `CurvePrices` independently
finds the GREEN index for reserve-ratio snapshots. For this StableSwapNG plain
implementation, the pool address is also the LP-token address; prove that
through the handler's `get_lp_token(pool)` and the pool ERC-20 getters.

The factory uses `create_from_blueprint` without a salt. Per Vyper, absence of
the optional salt means EVM `CREATE`, not `CREATE2`. The pool address therefore
depends on factory address and nonce/deployment order; the parameter tuple
alone does not determine it. “Deterministic identity” means:

- pin the fork block/hash and factory runtime/state;
- record `pool_count`, factory nonce if exposed by the engine, transaction
  sender, calldata, value and preceding transactions;
- predict or capture the CREATE address;
- require the deployment event and `pool_list[prePoolCount]` to equal it;
- rerun from a fresh identical fork and require the same address, runtime
  hash, getters, event and state root evidence.

A discovered live pool is accepted only through the same provenance checks.
The official manifest's current `pools: null` is not evidence that no pool can
exist onchain; it is evidence that no pool is declared by that manifest.

### Base precedent versus Robinhood

`config/BluePrint.py:132-152` and
`migrations/base-mainnet/2001_CurvePools.py` are the closest shipped Ripe
precedent. They must be visible whenever Robinhood deliberately follows or
diverges from Base:

| Input or action | Shipped Base migration | Robinhood disposition |
| --- | --- | --- |
| `A` / fee / off-peg | `100` / `4_000_000` / `20_000_000_000` | Reuse as the minimum-change candidate. |
| `ma_exp_time` | `600` | Use `600` provisionally; compare `866` on a fresh fork. Selecting `866` is an explicit semantic change to a ten-minute half-life, not a correction to Base. |
| snapshots / danger | `10` / `6_000` bps | Reuse as fork candidates. |
| `staleBlocks` | `43_200`, copied from Base's one-day HQ timelock | **Do not reuse on Robinhood.** Use the separately approved/calibrated L1-number value, provisionally `7_200`. |
| stabilizer adjustment | `5_000` bps | Use `5_000` as the minimum-change candidate. Keep `7_500` only as a deliberate stress/alternative vector pending a separate economic decision. |
| maximum pool debt | `1_000 GREEN` | Reuse as a fork candidate, not live approval. |
| seed | 100 USDC + 100 GREEN | The same quantities are the conditional USDG/GREEN deterministic fork seed. Base precedent does not prove they are sufficient Robinhood production liquidity. |
| LP recipient | Endaoment | Endaoment is the shared-path candidate; bind the exact Robinhood Endaoment/custody identity before funding. |
| price feeds | GREEN→pool and LP-token→pool | Both are separate `CurvePrices` feeds. Each add/confirm path is governed and timelocked. |
| asset posture | LP deposit/withdraw enabled, zero debt terms; LP transferred to Endaoment | Robinhood's approved launch row is deposit-only/zero-LTV but remains blocked on its own artifact/oracle/custody inputs. |

The Base migration registers both GREEN and the LP token in `CurvePrices`.
Accordingly, the approved Robinhood GREEN/USDG LP launch row has no established
Curve price under a strict Profile 1 configuration with ID 2 empty. This is
not an incidental documentation gap; it is part of the existing
`B-LP-ARTIFACTS` and `B-ORACLE-FREEZE` hard launch stop.

### Fees, authority, liquidity and custody

StableSwapNG sends half of swap fees to the factory fee receiver. The factory
admin can change pool fee/off-peg multiplier, ramp/stop `A`, and change the
price and D moving-average windows. It also controls implementations and
views. Fork qualification must read current getters; manifest constructor
arguments do not prove current admin or pending ownership state.

Use **100 USDG + 100 GREEN as the deterministic fork seed**, matching the
quantities in the shipped Base migration. Also run larger balanced and
asymmetric seeds. This precedent does not by itself approve the adequacy of
Robinhood production liquidity: a live amount, source of funds, exact
Endaoment/custody recipient, minimum-mint/slippage bound, withdrawal authority,
fee-destination acceptance and monitoring owner still require binding. No
amount in this report authorizes funding.

The adjacent conditional external-integration vector also includes official
Robinhood WETH
`0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`, a fork-pinned Chainlink
WETH/USD observation, a **test-only** RIPE/USD compatibility value of `1e13`,
and separate RIPE/WETH cases with $100 and $10 of value per side. The fixed
RIPE value must never be registered or represented as a production oracle.
Those cases qualify shared Curve plumbing and thin-liquidity behavior; they do
not add a RIPE/WETH launch pool to this recommendation.

### USDG storage-layout prerequisite

Existing dated Ripe evidence already pins canonical USDG at Robinhood block
`17,572,269` to implementation
`0x68184C449E1a8f34fA18d289737129FD27B66f8F`, proxy runtime hash
`0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6`,
and implementation runtime hash
`0x3a551ac5c744af57e68a1d1431ac403c0f516ffd7d224a75746aee11fc4f3baf`.
That is a valid historical starting point, not current-at-future-pin layout
proof.

Prefer a funded canonical holder or an approved canonical bridge/faucet path
in an authorized test environment. If deterministic mainnet-fork seeding
requires a storage overlay, all of these are mandatory:

1. pin proxy address, implementation slot/value, proxy and implementation
   runtime hashes, and all relevant admin/upgrade roles at the fork block;
2. bind the exact Paxos implementation source, compiler, settings and
   machine-readable storage layout to that runtime;
3. prove by getter/differential tests that the candidate balance mapping is
   slot `1` and total supply is slot `2` for that exact implementation;
4. compute the actor mapping location from the exact Solidity layout;
5. change one actor balance and total supply by the identical atomic delta;
6. prove the actor getter and `totalSupply()` changed by exactly that delta,
   all sampled other balances and allowances are unchanged, and proxy code,
   implementation pointer, roles, pause/freeze state and all other sampled
   storage are unchanged;
7. destroy the fork after evidence export.

The slot numbers are qualification candidates, not authorization to write
them. Any source/runtime/layout/getter disagreement is
`RB-USDG-OVERLAY-LAYOUT`; do not probe alternative slots. USDG upgrade drift
invalidates the overlay proof and requires a fresh layout qualification.

## 5. Profile 1 versus Profile 2 decision

### Profile 1 launch

Profile 1 retains:

- Chainlink at `PriceDesk` ID 1;
- empty/reserved IDs 2–5, especially Curve at ID 2;
- no `CurvePrices` deployment or registration;
- `CreditEngine.getDynamicBorrowRate` returning the supplied base rate;
- Teller's Curve reference-pool housekeeping branch returning before an
  external call;
- Endaoment's Curve stabilizer disabled/unreachable;
- USDG priced only through the approved Chainlink USDG/USD feed for PSM use;
- PSM activation, if separately approved, in redemption-first and
  GREEN-mint-last order.

The GREEN/USDG LP is already tracked, not a new ambiguity:

- `I-GREEN-USDG-LP` is blocked on `B-LP-ARTIFACTS` and
  `B-ORACLE-FREEZE`;
- DP-14 and `S-024-LP-ZERO-LTV` preserve the deposit-only, explicit-zero-LTV
  launch role;
- `B-LP-ARTIFACTS` is an existing **hard launch stop** owned through H-04;
- that lifecycle is approved M0 decision 9 and `D-H04-13`.

This Curve qualification is a closure path for those existing blockers.
However, closing them with a protocol-active `CurvePrices` route would promote
part of Profile 2 into launch, contrary to the risk-minimizing recommendation
above. My recommendation is therefore to keep Profile 1 as the launch
protocol profile and ask the owner to formally reopen M0 decision 9 to move
both LP activations into the Profile 2 follow-on. Until that governance change
or a separately accepted launch Curve slice occurs, `B-LP-ARTIFACTS` remains
a hard launch stop. Reclassification is not bookkeeping and this report does
not perform it.

### Profile 2 staged follow-on

| Stage | Curve state | Protocol consequence | Promotion gate |
| --- | --- | --- | --- |
| P2-A | Fork observation only; no Ripe registration | None | Graph, pool, swap, reserve, EMA and replay matrix |
| P2-B | Deploy/configure `CurvePrices` but keep ID 2 empty | Direct governed inspection only; no `PriceDesk` consumer can resolve it | Ripe artifact/config review and negative reachability |
| P2-C | Register ID 2; configure only explicitly approved asset rows | Curve becomes a possible protocol source and Teller housekeeping producer | Ordering/failure, clock, staleness and snapshot acceptance |
| P2-D | Enable dynamic-rate parameters | Debt rates respond to reserve status/danger count | Independent risk parameters, cap and jump tests |
| P2-E | Enable Endaoment stabilizer | GREEN mint/burn, pool liquidity and Ledger debt become active | Role, cap, custody, profit, pool-admin and emergency tests |

Observation-only must not be mislabeled as a protocol oracle. Registration
does not by itself authorize dynamic rates or stabilization.

## 6. CurvePrices and block-clock analysis

`CurvePrices` is structurally compatible with the official graph:

- it resolves AddressProvider IDs 7, 11, 12 and 13 and tolerates empty legacy
  IDs 3 and 6. The pinned
  [AddressProvider `get_address`](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/registries/address_provider/address_provider_v_201.vy#L115-L124)
  explicitly returns `empty(address)` for an undefined/unset ID rather than
  reverting;
- it caches those registry addresses as constructor immutables; a later
  AddressProvider update does not update an existing `CurvePrices`, so any
  binding drift requires an explicit keep/redeploy decision;
- it validates pools through the MetaRegistry and handler/factory graph. The
  pinned
  [MetaRegistry constants](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/registries/metaregistry/metaregistry_v_110.vy#L60-L61)
  are exactly `MAX_REGISTRIES=10` and `MAX_COINS=8`, matching
  `CurvePrices`' fixed `address[10]` handler and `address[8]` coin return
  widths;
- StableSwapNG pricing uses `price_oracle(0)` with the alternate asset's
  `PriceDesk` price;
- GREEN reference status uses normalized raw reserves, not the Curve EMA;
- staleness excludes a snapshot only when
  `block.number > update + staleBlocks`; equality remains fresh;
- if every ring-buffer entry is stale, it returns the last snapshot ratio
  rather than zero;
- a second snapshot at the same EVM number returns `false`;
- consecutive in-danger snapshots add
  `current block.number - prior update`; a safe snapshot resets the danger
  count.

Robinhood documents that EVM `block.number` is an estimate of the L1 Ethereum
number and updates periodically. Actual Robinhood child-block identity is
available from ArbSys precompile `0x0000000000000000000000000000000000000064`
via `arbBlockNumber()`.

The clocks have different roles:

| Clock | Use | Profile 2 implication |
| --- | --- | --- |
| EVM `NUMBER` / L1 estimate | `CurvePrices` suppression, staleness and danger; multiple other Ripe intervals | Repeats suppress L2-transaction samples; jumps advance all elapsed danger at once. |
| ArbSys child block | Actual Robinhood L2 execution block | Observe and reconcile; do not substitute into unchanged `CurvePrices`. |
| `block.timestamp` | Curve EMA, A ramps, and Ripe interest/time paths | Must advance independently and monotonically in replay. |
| RPC/header provenance | Fork pin, parent/child identity and replay evidence | Must bind all observed clock values to one pinned source block. |

For a nominal one-day L1-number window, `staleBlocks=7_200` is the candidate.
Use `10` snapshots, danger trigger `6_000` bps, minimum-change stabilizer
adjustment weight `5_000` bps, and a `1_000 GREEN` maximum pool debt.
Separately exercise the prior conditional `7_500` bps adjustment vector as a
deliberate alternative. These are fork inputs, not approved live parameters.

**Never copy Base's `staleBlocks=43_200` into Robinhood.** Under the planning
rate of about 7,200 L1-number increments per day, it permits roughly six days
of stale snapshots. Also reject `staleBlocks=0` for activation: the source
accepts zero but interprets it as “staleness disabled.”

### Reference configuration lifecycle and bounds

The governed `setGreenRefPoolConfig` → `confirmGreenRefPoolConfig` transition
is a timelocked two-step action with `cancelGreenRefPoolConfig`; confirmation
also attempts the initial snapshot. Validation requires:

- GREEN in an exactly two-underlying-token pool;
- `maxNumSnapshots` in `[1, 100]`;
- `dangerTrigger` in `[5_000, 9_999]` bps;
- `stabilizerAdjustWeight` in `[1, 10_000]` bps;
- `stabilizerMaxPoolDebt` in `[1, 25_000_000e18]`;
- a working pool balance read and nonzero derived ratio.

There is no nonzero validation bound on `staleBlocks`, so manifest and
activation assertions must supply it. GREEN and LP price-feed additions have
their own governed add/confirm/cancel timelocks; reference-pool confirmation
does not register either feed.

Unchanged source is acceptable because the L1-number behavior can be made
explicit and calibrated. It is not acceptable if an operator expects one
snapshot per Robinhood child block. The harness must preserve and replay RPC
child identity, L1 identity, EVM `NUMBER`, timestamp and ArbSys number. If it
cannot, stop with `RB-CLOCK-CURVE`. Do not introduce a Robinhood adapter or
mock a single counter as all four clocks.

## 7. PriceDesk and dynamic-rate sequencing

### ID 2 ordering and failure

`PriceDesk` evaluates configured priority IDs first, then unused source IDs in
ascending registry order. The first nonzero price wins.

| Configuration/result | Behavior |
| --- | --- |
| ID 2 empty | Skipped; Curve has no effect. |
| Priorities `[1, 2]` | Chainlink wins when nonzero; Curve is fallback. |
| Priorities `[2, 1]` | Curve wins when nonzero; Chainlink is fallback. |
| No priorities | ID 1 precedes ID 2, so Chainlink wins when nonzero. |
| Curve returns `(0, false)` | Continue to another source; no Curve feed is asserted. |
| Curve returns `(0, true)` | Continue; if no source returns nonzero and raising is required, revert `has price config, no price`. |
| Curve call reverts | Revert propagates; there is no `try/catch` fallback. |
| Curve returns a nonzero malformed/manipulated value | It wins if ordered first; ordering is therefore a risk decision, not just availability. |

For USDG, keep priority/source configuration Chainlink-only and do not add a
Curve USDG feed. Curve pool state may be observed in fork assertions but must
not become a PSM pricing route. For GREEN or an LP, each Curve registration
needs an explicit priority list and failure policy; registry ID semantics must
never be repurposed.

The no-Curve-USDG rule also prevents recursion. To price GREEN from the
USDG/GREEN pool, `_getSingleTokenPrice` calls `PriceDesk.getPrice` for the
alternate asset USDG. If the same Curve pool is also configured as USDG's
Curve feed, USDG pricing calls back through GREEN and can recurse instead of
reaching an independent reference. The allowed feed shape is:

```text
USDG -> Chainlink only
GREEN -> Curve USDG/GREEN pool -> PriceDesk(USDG) -> Chainlink
LP token -> Curve USDG/GREEN pool -> independent constituent price
```

The fork must inspect both `PriceDesk` priority rows and
`CurvePrices.curveConfig(USDG)`; a call-routing assertion alone is
insufficient.

### Dynamic rate

`CreditEngine` hardcodes Curve at `PriceDesk` ID 2:

1. empty ID 2 → exact base rate;
2. weighted ratio zero or below the danger trigger → exact base rate;
3. at the trigger → base plus the minimum dynamic multiplier;
4. above the trigger → interpolate from minimum to maximum multiplier;
5. add `increasePerDangerBlock × numBlocksInDanger × 10_000 / 1_000_000`;
6. cap the combined result at `maxBorrowRate`.

The conditional vector is:

```text
minDynamicRateBoost = 10_000
maxDynamicRateBoost = 50_000
increasePerDangerBlock = 10
maxBorrowRate = 10_000
```

The values use Ripe's existing units and must be checked against a nonzero
base-rate table. The current tests also show that weighted ratios above 100%
can interpolate beyond the nominal maximum multiplier before the final borrow
rate cap. Profile 2 acceptance must cover that edge.

Sequence P2-C registration before any P2-D activation, observe base fallback
with dynamic fields inert, then activate one bounded config under a recorded
owner decision. Removing/disabling ID 2 must immediately restore the base-rate
path.

## 8. Teller, Endaoment, and PSM integration

### Teller snapshots

Every Teller deposit and withdrawal asks `PriceDesk` to add the transacted
asset's ordinary price snapshot. Separately, the common Teller housekeeping
path reads `PriceDesk` ID 2 and, when nonzero, calls
`CurvePrices.addGreenRefPoolSnapshot`. The frozen source has 22 direct
housekeeping action call sites plus the externally callable housekeeping
wrapper. The blast radius includes deposits, withdrawals, borrows, repayments,
liquidation flows, claims and other shared Teller actions—not only
deposit/withdraw.

- Before Curve registration, the reference-pool call is absent and
  deposit/withdraw behavior remains Profile 1 behavior.
- After registration, every housekeeping opportunity attempts a GREEN
  reference snapshot.
- Multiple successful transactions under one EVM L1-derived number result in
  one reference snapshot; later attempts return `false` and must not revert or
  corrupt Teller accounting.
- Ordinary asset-source snapshots and the GREEN reference-pool snapshot are
  different mechanisms and need separate assertions.

The liveness dependency is direct. `_getCurvePoolData` performs unguarded
static calls to `pool.balances(greenIndex)` and
`pool.balances(1-greenIndex)`. If a previously accepted pool later reverts,
returns malformed data or loses compatible code, the revert propagates through
`addGreenRefPoolSnapshot` and can block the entire housekeeping-backed Teller
surface.

`CurvePrices.pause(true)` is the immediate Teller-liveness escape hatch:
`addGreenRefPoolSnapshot` then returns `false` before touching the pool. The
pause method is callable only by an admitted Switchboard address. It does
**not** clear the existing reference status or make CreditEngine return the
base rate; restoring base-rate behavior additionally requires disabling
`PriceDesk` ID 2 through its own controlled path. While paused, Curve feed and
reference-config set/confirm/cancel methods reject, so the P2-C incident
runbook must prove this order:

1. pause `CurvePrices` and confirm representative Teller actions recover;
2. disable ID 2 if dynamic-rate authority must be removed;
3. diagnose/replace the pool or config under a separately reviewed transition;
4. re-enable only after the complete pool/config/Teller matrix passes.

Fork evidence must record requested, received, credited and withdrawn asset
amounts, PriceDesk source events/state, reference snapshot update/index and the
four clocks before and after each call. It must also record representative
borrow, repay, liquidation, claim and external-housekeeping outcomes.

### Endaoment

The stabilizer is a distinct high-authority activation:

- caller must be the authorized Switchboard route;
- `PriceDesk` ID 2 and the GREEN reference-pool config must exist;
- Endaoment must have GREEN mint/burn authority and the correct Ledger debt
  identity;
- EndaomentFunds must be the approved custody source/destination;
- LP and GREEN balances/approvals must be exact;
- below 50% GREEN reserve, it can add GREEN and mint only the amount needed
  after using available GREEN, bounded by `stabilizerMaxPoolDebt`;
- above 50%, it can remove liquidity and burn/reconcile GREEN debt;
- the transaction requires **non-decreasing** calculated profit:
  `newProfit >= initialProfit`; both values are `uint256`, so “nonnegative” is
  not the operative invariant;
- `stabilizerAdjustWeight=5_000` is the minimum-change candidate,
  `7_500` is an explicit alternative/stress vector, and
  `maxPoolDebt=1_000 GREEN` is a fork candidate only.

Activation depends on pool liquidity, Curve factory admin acceptance, a
custody/funding decision, profit/slippage bounds, mint-cap reconciliation,
pause/recovery runbooks and monitoring. Base partner-liquidity, yield, Aero
and Underscore routes are not dependencies and must remain absent.

### PSM

The PSM's reserve valuation goes through `PriceDesk`; for Robinhood the
approved authority is the official Chainlink USDG/USD feed. The PSM uses
conservative direction-dependent conversion around one dollar, six-decimal
USDG accounting, and separate mint/redeem interval capacity.

Curve is **observation only** for the PSM:

- no Curve USDG price row;
- no priority that can route USDG valuation to ID 2;
- no “pool at peg” substitution for a stale, zero or reverting Chainlink
  feed;
- no activation coupling between PSM and Profile 2;
- assertions may compare Curve spot/EMA to Chainlink and PSM outputs but
  disagreement must not change PSM execution.

Changing this principle requires a separate owner decision, oracle
specification, economic analysis, implementation/registration plan and
adversarial test package. This report does not authorize it.

## 9. Complete fork-test matrix

All cases run on fresh, mode-`0700`, pinned, read-only-parent forks. State
changes exist only inside the disposable child fork. Export sanitized evidence
before destruction.

| ID | Setup / action | Required assertions | Stop condition |
| --- | --- | --- | --- |
| G-01 | Pin Robinhood block number/hash and chain ID 4663 | RPC/header identity, parent hash, timestamp, EVM number and ArbSys child number recorded | Any identity drift |
| G-02 | Read every AddressProvider populated ID and description | Exact table in section 3; expected empty/null IDs remain empty | Unexpected or missing binding |
| G-03 | Traverse MetaRegistry | Length 3; handler order Stable/Tricrypto/TwoCrypto; exact base factories | Handler/order/pointer mismatch |
| G-04 | Read factory pointers/admin/fee receiver | Exact implementations, math/views, admin, fee receiver, pool count | Manifest/current-state mismatch without approved rebind |
| G-05 | Rebuild all graph artifacts twice | Compiler/source/settings/ABI/creation/runtime/blueprint hashes identical | `RB-H07-CURVE-GRAPH` |
| G-06 | Decode constructors and blueprint preambles | Exact arguments, ERC-5202 prefix, `code_offset=3` lineage | Unknown optimization or byte mismatch |
| G-07 | Bind canonical USDG | Proxy/implementation/code hashes, decimals 6, roles, pause/freeze state | Upgrade or identity mismatch |
| U-01 | Qualify USDG funded-holder path | Exact actor transfer delta; no mutation required | No authorized source of test funds |
| U-02 | If necessary, prove overlay layout without retaining changes | Slots 1/2 source- and getter-proved; one balance and supply delta only | `RB-USDG-OVERLAY-LAYOUT` |
| P-01 | Search factory/MetaRegistry for USDG/GREEN pool | Any candidate has exact coins/order/factory/implementation/parameters/runtime | Label-only or foreign factory |
| P-02 | If absent, fork-create exact candidate | Pre-count/index/event/CREATE address/runtime/getters all agree | Nondeterministic identity |
| P-03 | Fresh-fork replay P-02 | Same pool address, hashes, getters, events and state deltas | Replay differs |
| P-04 | Add 100 USDG + 100 GREEN | Exact token/pool/LP deltas; balanced virtual price and 50% GREEN reserve ratio | Fee-on-transfer or rounding mismatch outside spec |
| P-05 | Repeat with larger balanced seed | Scale behavior, minimum mint and LP custody reconcile | Hidden size dependency |
| P-06 | USDG→GREEN swaps, small through material fractions | Quotes/execution/fees/reserves/spot/EMA monotonic and bounded | Wrong coin direction or unexplained delta |
| P-07 | GREEN→USDG swaps | Symmetric evidence and fee accounting | Same |
| P-08 | Reserve stress in both directions | 60% danger boundary, near-empty reserve, quote/revert behavior, off-peg fee rise | Invariant, precision or liquidity failure |
| P-09 | Compare off-peg multiplier 1x vs 2x in separate forks | Balanced fee unchanged; stressed fee rises toward configured bound | Unexplained fee path |
| P-10 | Compare `ma_exp_time` 600 and 866 on separate fresh forks | Exact timestamp-driven trajectories; 600 matches Base, while 866 corresponds to a 600-second half-life | Either input is mislabeled or a live choice is made without owner semantics |
| P-11 | EMA time steps and no-swap periods | Spot/last/oracle/D oracle, timestamp and caps behave per v7 source | Clock or admin-setting mismatch |
| P-12 | On separate forks, run RIPE/WETH with pinned WETH/USD, test-only RIPE/USD `1e13`, and $100 then $10 value per side | Shared graph/adapter behavior, both swap directions and thin-liquidity failures are explicit; no fixed RIPE feed is registered | Fixed test value escapes the harness or pool is mislabeled launch-ready |
| C-01 | Record several L2 tx under one EVM number | ArbSys advances as observed while EVM number repeats | Harness collapses clocks |
| C-02 | Call reference snapshot twice at same EVM number | First eligible call updates; second returns false with no state mutation | Revert or duplicate snapshot |
| C-03 | Advance EVM number by +1 while child/timestamp are recorded | Exactly one new snapshot; index and update correct | Cross-clock inconsistency |
| C-04 | Jump EVM number across consecutive danger samples | Danger increases by exact EVM-number delta once | Wrong delta/underflow |
| C-05 | Insert safe snapshot after danger | Danger resets; new status and ring entry correct | Residual danger |
| C-06 | Test staleness at `update+7_200` and `+7_201` | Fresh at equality; excluded after; fallback-to-last explicit when all stale | Off-by-one or zero/unsafe fallback |
| C-07 | Set `staleBlocks=0` on a negative fork | Snapshots never age out, proving zero disables staleness | Zero enters a Profile 2 activation manifest |
| C-08 | Set Base `staleBlocks=43_200` on a negative Robinhood fork | Demonstrate the approximately six-day L1-number window | Base value is copied into Robinhood |
| C-09 | Fill/wrap 10-snapshot ring | Correct weighting, order, stale filtering and last snapshot | Index/weight corruption |
| C-10 | Replay exact clock trace | Same snapshots, weighted ratio, danger and rates | `RB-CLOCK-CURVE` |
| C-11 | Exercise reference-config boundary values | Accept snapshots 1/100, danger 5000/9999, weight 1/10000 and debt 1 atomic unit / `25_000_000e18`; reject values outside each range and non-two-coin/non-GREEN/broken pools | Invalid config is accepted or valid boundary rejected |
| C-12 | Set, premature-confirm, cancel, re-set and confirm reference config | Timelock blocks early confirmation; cancel clears pending state; confirmation stores exact values and attempts one initial snapshot | One-step or stale-pending configuration |
| D-01 | Profile 1, ID 2 empty | Dynamic rate equals base for multiple bases; Teller no Curve call | Any Curve effect |
| D-02 | ID 2 registered, weighted ratio 0/below 6000 | Base-rate fallback exact | Boost below trigger |
| D-03 | Ratios 6000, midpoint, 10000, >10000 | Min/interpolated/max-or-above multiplier and final cap match source | Arithmetic mismatch |
| D-04 | Danger counts 0, 1, 10, jump-sized | Additive boost, integer steps and cap exact | Cadence/rounding mismatch |
| D-05 | Disable ID 2 after activation in child fork | Immediate return to base-rate path | Residual dynamic authority |
| O-01 | PriceDesk priority `[1,2]`, `[2,1]`, empty list | First nonzero source follows exact ordering | Registry/priority ambiguity |
| O-02 | Curve `(0,false)`, `(0,true)`, revert, nonzero | Continue/raise/propagate/win behavior matches section 7 | Silent unexpected fallback |
| O-03 | USDG PSM price calls with Curve present | Only Chainlink source is called/accepted | Any Curve authority |
| O-04 | Inspect feed graph and attempt mutual USDG/GREEN Curve configuration on a negative fork | Production candidate has no `curveConfig(USDG)` and USDG priorities exclude ID 2; negative graph demonstrates recursion/failure | Mutual Curve feed or recursive pricing shape |
| O-05 | Add/cancel and add/premature-confirm/confirm GREEN and LP Curve feeds | Separate governed timelocks, pending state, validation and final pool bindings are exact for each asset | One-step, shared-pending or unvalidated feed registration |
| T-01 | Teller deposit before Curve registration | Requested/received/credited and ordinary snapshots reconcile; no ref snapshot | Hidden ID 2 call |
| T-02 | Teller deposit after registration, fresh EVM number | Same asset accounting plus one reference snapshot | Accounting/snapshot coupling |
| T-03 | Two deposits and withdrawal under repeated EVM number | All asset accounting succeeds; reference snapshot suppressed after first | Cross-L2 denial or duplicate |
| T-04 | Withdrawal after EVM jump/staleness | Delivery exact; reference status/rate observes documented jump only | Snapshot causes withdrawal failure |
| T-05 | After valid activation, make the configured pool balance getter revert or return malformed data | Representative deposit, withdrawal, borrow, repay, liquidation, claim and external-housekeeping calls revert atomically while unpaused, proving the full blast radius | Any partial state or unrecorded affected path |
| T-06 | With the T-05 fault present, execute the P2-C pause/disable/recovery runbook | Switchboard pause makes snapshots return false before pool access and restores Teller liveness; ID 2 disable restores base rates; config methods reject while paused; re-enable only after repair tests | No callable liveness escape, stale dynamic authority, or unsafe re-enable |
| E-01 | Stabilizer below 50%, available GREEN sufficient | Adds bounded GREEN, no mint/debt increase, LP/custody exact, and `newProfit >= initialProfit` | Unneeded mint or profit decrease |
| E-02 | Below 50%, GREEN shortfall | Mint/debt delta exact and ≤1,000 GREEN cap; pool moves toward target | Cap/authority breach |
| E-03 | Above 50% GREEN | Remove/burn/debt/custody deltas exact and `newProfit >= initialProfit` | Debt/custody mismatch or profit decrease |
| E-04 | Unauthorized, disabled, zero-pool, zero-balance, cap exceeded | Fail closed/false exactly as source; no partial state | Reachability or partial mutation |
| S-01 | PSM mint/redeem at USDG prices 0.90/1.00/1.10 | Existing conservative Chainlink-driven conversions and caps | Curve affects output |
| S-02 | Chainlink zero/stale/revert while Curve looks healthy | Existing PSM/PriceDesk failure; no Curve rescue | Curve becomes fallback |
| S-03 | Vary pool spot/EMA with Chainlink fixed | PSM output unchanged; observation discrepancy recorded | Observation changes authority |
| X-01 | Snapshot all fork state/evidence, end process and destroy fork | No persistent child state, key, account, deployment or external write; hashes retained | Fork cannot be destroyed cleanly |
| X-02 | Recreate from the original pin and rerun selected cases | Deterministic address, outputs and evidence hashes | Nondeterministic replay |

Reserve-fraction stress must include trades sized from small fractions through
material depletion in both directions, not only fixed token amounts. Every
failure records the smallest divergent input and leaves the parent fork pin
unchanged.

## 10. Owner-input packet

Unknowns are classified here rather than guessed.

| Owner input | Required decision/evidence | Deadline |
| --- | --- | --- |
| Profile lifecycle | Approve Profile 1 launch and P2-A→P2-E separate promotions; recommended path formally reopens M0 decision 9 and moves both LP activations to Profile 2 | Before launch graph freeze |
| Curve source pins | Approve curve-core `6222dda…` and all manifest-declared curve-lite source commits or exact replacements | Before H-07 build |
| Live fork pin/access | Approved mainnet block/hash, sanitized endpoint policy and disposable fork engine | Before any live fork |
| Clock model | Accept L1-derived EVM number for Curve snapshots/stale/danger; approve 7,200/day calibration and stop code; explicitly reject zero and copied Base 43,200 | Before P2-C |
| Pool identity | Exact name, symbol, coin order, factory/implementation, parameter tuple and create/discovery route | Before P-01/P-02 |
| Pool economics | A, fee, off-peg multiplier, price/D EMA windows and acceptable admin mutability; Base/minimum-change `ma_exp_time=600`, with 866 requiring an explicit ten-minute-half-life decision | Before pool qualification closes |
| Liquidity/custody | 100/100 fork and Base precedent distinguished from approved production amount; source, exact Endaoment/custodian, min mint/slippage, withdrawal and fee policy | Before any non-disposable funding |
| GREEN | Final address, code/runtime/artifact, supply recipient and mint/custody authority | Before P-01 |
| USDG | Revalidate the dated block-17,572,269 implementation/code-hash evidence at the new pin; prove layout and issuer/admin/upgrade acceptance; choose holder or overlay policy | Before U-01/U-02 |
| PriceDesk | Per-asset priorities, whether any Curve row may be authoritative, and failure policy | Before P2-C |
| Dynamic rate | Approve min/max boost, danger slope, max rate and effective rate/cadence report | Before P2-D |
| Reference pool | Approve values within snapshots 1–100, danger 5,000–9,999 bps, weight 1–10,000 bps and debt `[1, 25_000_000e18]` atomic units; bind nonzero stale count, timelock/cancel evidence and monitoring | Before P2-C |
| Teller incident control | Bind the admitted Switchboard pause caller and rehearse pause → Teller recovery → ID 2 disable → repair → guarded re-enable across the full housekeeping surface | Before P2-C |
| Endaoment | Use Base/minimum-change 5,000 bps adjustment unless a separate decision selects 7,500; approve 1,000 GREEN cap or replacement, roles, custody, non-decreasing-profit/slippage and emergency posture | Before P2-E |
| PSM | Reaffirm Chainlink-only USDG authority and observation-only Curve relationship | Before P2-C and PSM activation |
| H-07/H-09 | Approve exact artifact evidence schema, fork evidence ceiling and independent review | Before qualification is called complete |

No individual unknown requires speculative implementation. An undecided input
keeps its corresponding stage closed while Profile 1 remains available,
subject to the LP lifecycle reconciliation.

## 11. Launch and follow-on acceptance criteria

### Profile 1 launch acceptance

- frozen launch commit/tree and all normal deployment gates are separately
  approved;
- PriceDesk ID 1 is exact Chainlink and IDs 2–5 are empty/reserved;
- no `CurvePrices`, pool, Curve config, dynamic producer or stabilizer is
  deployed/registered/active;
- base-rate fallback tests pass with ID 2 empty;
- Teller deposits/withdrawals and housekeeping pass without Curve calls;
- PSM USDG pricing is Chainlink-only, with its separate disabled/staged
  activation gates;
- M0 decision 9 is formally reopened and both LP activations are moved to
  Profile 2, or the existing `B-LP-ARTIFACTS` hard stop remains open and
  launch does not proceed;
- manifests and operator assertions reject accidental Curve reachability.

### P2-A observation acceptance

- G-01 through G-07, U-01 or qualified U-02, P-01 through P-12, C-01 through
  C-10, X-01 and X-02 pass;
- H-07 graph closure is independently reproducible;
- fork pin and all four clocks replay deterministically;
- no Ripe registry, pricing, rate, Teller, Endaoment or PSM authority changes.

### P2-C protocol-source acceptance

- P2-A accepted;
- unchanged `CurvePrices` artifact and constructor inputs are frozen;
- exact pool and GREEN reference config are owner-approved;
- C-11/C-12, O-01 through O-05, D-01/D-02, and T-01 through T-06 pass;
- L1-derived clock semantics and residual sampling risk are explicitly
  accepted;
- USDG remains Chainlink-only and S-02/S-03 pass;
- Switchboard pause and ID 2 disable runbooks are bound to accountable
  operators and return Teller/rates to safe Profile 1 behavior.

### P2-D dynamic-rate acceptance

- P2-C accepted and observed under a defined soak window;
- D-03 through D-05 pass for approved parameters, repeated numbers, jumps and
  >100% ratio;
- effective raw/runtime/reporting units reconcile;
- rate cap and emergency disable are independently rehearsed.

### P2-E stabilizer acceptance

- P2-D need not be active, but P2-C and pool/custody acceptance are mandatory;
- E-01 through E-04 pass with exact roles, cap, liquidity and custody;
- GREEN supply and Ledger pool debt reconcile after every action;
- Curve admin mutability and issuer/custody risks are accepted;
- pause, disable, withdrawal and recovery runbooks pass before activation.

Any follow-on gate failure leaves or returns the system to the last accepted
stage. Passing fork tests qualifies a candidate; it does not deploy, register,
activate, or release it.

## 12. Residual risks and explicit non-actions

### Residual risks

- Curve infrastructure and pool administration can change after the manifest
  and fork pin; runtime getters and code hashes are point-in-time.
- USDG is upgradeable and has issuer/admin/pause/freeze/supply controls.
- A thin USDG/GREEN pool is manipulable. Curve EMA, raw reserve ratio and
  Chainlink can disagree for economically meaningful periods.
- `CurvePrices` fallback to the last ratio when all snapshots are stale is
  availability-preserving, not a fresh market observation.
- copied Base `staleBlocks=43_200` permits roughly six days of age under the
  Robinhood L1-number planning cadence; zero disables staleness entirely.
- L1-derived number repetition reduces sampling granularity; jumps concentrate
  danger accrual. Brief unsafe excursions between accepted samples can be
  missed.
- once ID 2 is registered, an unguarded revert from the configured pool's
  balance getters can block the 22 direct Teller housekeeping-backed action
  sites plus external housekeeping. `CurvePrices` pause restores snapshot
  liveness but does not itself clear dynamic-rate authority.
- `PriceDesk` propagates source reverts and a first nonzero source wins; a
  priority mistake can change protocol valuation broadly.
- Dynamic multipliers can exceed the nominal maximum when weighted ratio is
  above 100% before the final borrow-rate cap.
- Endaoment stabilization adds GREEN mint/burn, liquidity, debt, custody,
  slippage and external-admin blast radius.
- Deterministic fork creation does not make a future live pool address
  deterministic unless the factory nonce/order is also controlled.
- Official-manifest `pools: null` may lag onchain permissionless deployment;
  discovery must not be confused with official provenance.

### Exact blockers to live fork qualification

1. Robinhood `MIGRATION_FORK`, repository evidence and verification operations
   are still policy-blocked; migration/history paths are proposed and no
   Robinhood blueprint is bound in the network profile.
2. No approved live fork block/hash, endpoint policy or four-clock-capable fork
   engine is bound to this qualification.
3. H-07 does not yet supply the complete reproducible Curve graph, including
   exact optimization inputs for manifest rows marked `UNKNOWN`.
4. Current onchain AddressProvider/MetaRegistry/factory/admin/runtime state has
   not been read at an approved pin.
5. No official-manifest USDG/GREEN pool identity exists; final GREEN identity,
   pool strings, creation/discovery path, nonce/order and artifact are unset.
6. Historical USDG implementation and runtime hashes exist at block
   `17,572,269`, but they require future-pin revalidation; compiler-derived
   layout and a funded-holder or exact overlay path remain unqualified.
7. Base identifies Endaoment as the shared LP recipient candidate, but the
   exact Robinhood custody identity, liquidity source/amount, slippage and
   withdrawal authority are not bound.
8. PriceDesk ordering, clock calibration, reference-pool, dynamic-rate and
   Endaoment parameters, plus the P2-C Teller pause/disable runbook, lack final
   owner/operator binding.
9. Final integrated deployment/default/migration/operator/artifact/fork
   evidence baselines and the independent H-09 qualification ceiling remain
   prerequisites to calling a live candidate qualified.

### Explicit non-actions

This work did not connect to RPC, inspect a private endpoint, create or fund a
pool, deploy or call a live contract, mutate a fork, use an account or signer,
edit a contract/configuration/manifest/inventory/migration/existing document,
stage, commit, push, verify, register, configure, activate, release, or change
external state. The only repository content created is this report.

## Controlling owner disposition

**Recorded:** 30 July 2026  
**Authority:** explicit owner disposition for this qualification task  
**Effect:** controls the listed qualification decisions without rewriting the
research or historical evidence above

1. Profile 1 is approved as the Robinhood launch profile.
2. Profile 2 is approved as a staged near-term follow-on.
3. M0 decision 9 is formally reopened solely to move both LP activations from
   the launch-critical profile into Profile 2.
4. `CurvePrices` remains unchanged.
5. Chainlink remains the sole PSM price authority. Curve remains an
   observation and reference input unless separately reconsidered.
6. The preferred Profile 2 candidates are:
   - `ma_exp_time = 600`;
   - `stabilizerAdjustWeight = 5_000`.
7. The mandatory alternative fork-test vectors are:
   - `ma_exp_time = 866`;
   - `stabilizerAdjustWeight = 7_500`.
8. `staleBlocks = 7_200` is approved as the preferred qualification
   candidate, not as frozen production configuration.
9. Real Robinhood fork clock proof is required before
   `staleBlocks = 7_200` may be frozen for deployment.
10. These values are explicitly rejected:
    - `staleBlocks = 0`, because it disables staleness;
    - Base `staleBlocks = 43_200`, because it creates an unacceptable
      approximately six-day Robinhood hazard under the documented clock
      behavior.
11. The P2-C Switchboard-pause and PriceDesk-ID-2-disable incident runbook,
    including recovery tests, is required before Profile 2 activation.
12. This disposition does not authorize Curve deployment, pool creation,
    liquidity funding, Profile 2 activation, configuration, RPC use, or any
    external action.
