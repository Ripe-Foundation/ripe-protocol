# DefaultsRobinhood: configuration-source authority

> **11 August 2026 CCIP currentness note:** the deferred-CCIP test description
> below is dated evidence, not current topology. GREEN/RIPE CCIP is confirmed
> live; see [`../ccip-live-state.md`](../ccip-live-state.md).

> [!WARNING]
> **Superseded current-state snapshot.** The identities, counts, constructor
> matrix, and launch values below predate the 2026-08-06 production Vyper
> remediation. The current seven-argument/no-Steakhouse matrix and selected
> values are recorded in
> [`rh-production-vyper-remediation.md`](../rh-production-vyper-remediation.md)
> and the final source. Preserve the remainder as historical evidence only.

## Current `rh` rebind

This rationale is bound to current `rh` commit
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`.
[`DefaultsRobinhood.vy`](../../../../contracts/config/DefaultsRobinhood.vy) last
changed at ancestral configuration-source commit `e4473ce…`; that ancestor is
not the current branch tip.

| Identity | Current value |
| --- | --- |
| Git blob | `c63009f9e03044616da2562767f129d91e0843aa` |
| Source SHA-256 | `4f89a970c19a7fc5a3d6f05035cd252d660ac6c1696ccddb4bd76c6751f356f8` |
| Source size | 13,617 bytes |
| Creation artifact | 2,995 bytes; SHA-256 `8ecc4f51e3764a74cb17ebfa084331a97c89329475f4188c61baf6c4813f2870` |
| Runtime template | 2,687 bytes; SHA-256 `aede1fc73290eeb071e1b67a7c7b367dbec0536e406391a03f12275663370d99` |
| EIP-170 headroom | 21,889 bytes |
| Canonical ABI SHA-256 | `a2b3232606060b9b296666a2cfbc6a328c2b92897ac6e1dcf9f82920a449bddb` |

## Why this contract exists

Ripe contracts consume a `Defaults` interface during fresh deployment. A
Robinhood deployment needs chain-specific default values without adding
Robinhood branches to shared protocol logic or silently reusing Base values.
`DefaultsRobinhood.vy` is therefore a values-and-inventory contract: it
implements the existing interface and contains no divergent protocol execution
flow.

Its presence in source proves only that a compilable candidate exists. It does
not prove that the artifact was deployed, passed to a constructor, registered,
read onchain, or used to configure any production contract.

## The two human-edited value authorities

The repository has exactly two human-edited Robinhood value authorities:

| Authority | Values that belong there |
| --- | --- |
| [`contracts/config/DefaultsRobinhood.vy`](../../../../contracts/config/DefaultsRobinhood.vy) | Values returned through the `Defaults` interface: general permissions and limits, debt defaults, auction terms, reward allocations, RipeGov-vault terms, HR ranges, token/default addresses consumed by those getters, and block- or time-denominated Defaults values |
| [`config/BluePrint.py`](../../../../config/BluePrint.py) | Deployment topology and values outside the `Defaults` interface: component selection, registry slots, constructor arguments, external addresses, symbolic deployment-produced identities, capabilities, ordering, clocks, activation classes, and other deployment assertions |

The division is semantic rather than file-format based. A value does not move
into Defaults merely because a contract eventually consumes it, and a
Defaults-interface value must not be duplicated into Blueprint as another
editable authority.

[`config/robinhood-parameters.json`](../../../../config/robinhood-parameters.json)
is synchronized derived evidence. The generator compiles and reads both source
authorities and validates their topology and assertions. A bare invocation is
the write path: it atomically synchronizes the JSON ledger. `--check` is the
explicit read-only path used by this audit. Neither path renders or overwrites
`DefaultsRobinhood.vy` or uses RPC.

## Fail-closed readiness

The current network-free read-only check:

```sh
python scripts/params/generate_robinhood_defaults.py --check
```

reported:

```text
H04_OK sha256=e5323f5e4eca86773c097a1e6e20c8f9df8dc96556f3d98cb79fb5e66915fea3
configuration_consistent=true deployment_ready=false blockers=80
```

`configuration_consistent=true` means the two readable authorities and their
derived ledger reconcile. It is not a deployment-ready result. Symbolic or
unresolved identities remain blockers; the generator must not substitute zero,
a placeholder, a Base address, or an inferred value merely to produce a ready
status.

The 80 rows are source/configuration-readiness blockers. The separately
integrated deterministic migration planner adds migration bindings and reports
100 executable-plan blockers. The migration sources and deterministic
transaction executor exist in the repository, but no plan has been made
executable and no migration, deployment, history publication, or onchain
configuration has occurred.

This is the required fail-closed boundary:

- compilation does not resolve an external or deployment-produced identity;
- derived evidence cannot promote an unresolved input;
- a selected component is not a deployed component;
- a constructor schedule is not a transaction; and
- a source value is not onchain configuration.

## Current tests and artifact controls

The principal current evidence paths are:

| Path | Git blob | SHA-256 | Responsibility |
| --- | --- | --- | --- |
| [`tests/config/test_defaults_robinhood.py`](../../../../tests/config/test_defaults_robinhood.py) | `c5e8995cabcdc2ac7a8247861af5a713603b8253` | `730086ae75a138913ba1a27805190ad308cf2951799fccfb688095c581125c29` | Source derivation, compiler extraction, authority split, deterministic ledger, current launch inputs, unresolved-input and mutation failures |
| [`tests/deployment/test_robinhood_blueprint.py`](../../../../tests/deployment/test_robinhood_blueprint.py) | `b7d6234f346fbc9ad68a644d65e37b5d377dae19` | `3b6a179fd3f7d4be9485e5e020901b3f75d7ed5de3e0cf58386d8a05f49ccd72` | Current component, registry, constructor, launch-input, and lifecycle topology |
| [`tests/deployment/test_robinhood_omissions.py`](../../../../tests/deployment/test_robinhood_omissions.py) | `187454dee85fe69f964324479f068f66ce7bca99` | `9d807dce53c3f135baf1fe772f2e9a8e25b2a9c976be78e25ae07200efaa320a` | Required omissions and fail-closed capability/activation surfaces, including deferred CCIP promotion |
| `tests/inventory/test_contract_artifacts.py` (retired) | `30e56a30e803e6030abb321b7dd593f08ac83f04` | `e821112fe1c2ac6e1091605f0b20f6c498d0e8d41914d07e196d3fc1be6b6cf8` | Frozen source, compiler, ABI, layout, and bytecode identity for the central contract set |

The central nine-contract artifact checker reconciles the frozen Defaults and
other covered contract identities. The repository-wide ABI export check is not
green at this baseline: the newly integrated shared `Erc20Token.getCCIPAdmin()`
method makes the committed `Erc20Token`, `GreenToken`, `RipeToken`, and
`SavingsGreen` ABI files stale. That separate current discrepancy is documented
in [`erc20-token.md`](erc20-token.md). No protocol suite was rerun for this
documentation refresh.

## Deployment and release boundary

The source may become operational only through separately authorized steps:

1. resolve and approve every constructor and symbolic input;
2. regenerate and review derived evidence without changing source authority;
3. bind exact compiler and creation bytes;
4. deploy with the approved constructor values;
5. verify runtime, immutable getters, and dependent constructor use;
6. perform separately approved registration and configuration; and
7. obtain activation and release authority.

No step is implied by the previous one, and this rationale authorizes none of
them.
