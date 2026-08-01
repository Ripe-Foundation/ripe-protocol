# DefaultsRobinhood: configuration-source authority

## Current `rh` rebind

This rationale is bound to current `rh` commit
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`.
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
authorities, validates their topology and assertions, and writes only the JSON
ledger when explicitly run in write mode. It never renders or overwrites
`DefaultsRobinhood.vy` and never uses RPC.

## Fail-closed readiness

The current network-free check reported:

```text
H04_OK sha256=0750856092889476e3ec8e54305e74dc0152c576dfa687a8c08934fc85c0893c
configuration_consistent=true deployment_ready=false blockers=58
```

`configuration_consistent=true` means the two readable authorities and their
derived ledger reconcile. It is not a deployment-ready result. Symbolic or
unresolved identities remain blockers; the generator must not substitute zero,
a placeholder, a Base address, or an inferred value merely to produce a ready
status.

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
| [`tests/config/test_defaults_robinhood.py`](../../../../tests/config/test_defaults_robinhood.py) | `d5a5061e2414516d9f23ee8ea71b31ee5e8daad7` | `d20b52b9ef66f35d4ab2a0daa8506be4cf3d8f3148d918fe2717e923558fe956` | Source derivation, compiler extraction, authority split, deterministic ledger, unresolved-input and mutation failures |
| [`tests/deployment/test_robinhood_blueprint.py`](../../../../tests/deployment/test_robinhood_blueprint.py) | `82d2ee133ab7b2e56183cc4a807cdb28f09a04cd` | `43c80d4516b203e64301bf00001928518624da43ea838939464e7ac1ba69465e` | Component, registry, constructor, and lifecycle topology |
| [`tests/deployment/test_robinhood_omissions.py`](../../../../tests/deployment/test_robinhood_omissions.py) | `5b1fc4a502820c4df2668b6f1c69a7bf14511d90` | `4ac1d402147315c07e1d7f370388239eff085d3dbd4f10f75d8cae46a970c473` | Required omissions and fail-closed capability/activation surfaces |
| [`tests/inventory/test_contract_artifacts.py`](../../../../tests/inventory/test_contract_artifacts.py) | `3eb4a93c0d5bd400586a1b1aa980432ac2aa0284` | `ecbd803c2e002eac39a565e3d2bbf419af16319952a0c7ef0867e5c50b61ac86` | Source, compiler, ABI, layout, and bytecode identity |

The current artifact checker reconciles the committed ABI and compiler outputs.
No protocol suite was rerun for this documentation refresh.

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
