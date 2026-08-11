# GREEN and RIPE CCIP BurnMint pool reference subclasses

> **Historical 1.6.1 reference review.** This page does not describe the
> current live source or lifecycle. The deployed pools use the repository's
> vendored 1.5.1 production source; see
> [../ccip-live-state.md](../ccip-live-state.md) for confirmed topology and
> remaining operational gates. The exact-hash analysis below remains useful
> only for the superseded reference artifact it names.

> [!IMPORTANT]
> This page documents a changed Solidity reference source in current `rh`.
> The file is independently reviewed example code, not an authorized production
> Solidity package, deployment artifact, registered pool, activated CCIP route,
> or release.

## Current identity and source scope

This rationale is bound to current local, cached, and live `rh` commit
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`, verified on 3 August 2026.
The source was added by historical reference-package commit
`8d1d2d40c3ca795a37b8cb5bbed54c5e805cddaa`, whose parent is
`70dd76516ca9b4af8c0797c327bf15732634e5f6` and whose tree is
`68a0d26e35d0437eea62eb4495e68ad25cbf85d1`.

| Identity | Current value |
| --- | --- |
| Reference source | [`docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol`](../examples/RipeCcipBurnMintTokenPools.sol) |
| Git blob | `9914be95aab65e48438b5be9e3e7defa221696b7` |
| Source SHA-256 | `28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77` |
| Source size | 1,784 bytes / 49 lines |
| Addition scope | One Solidity file, two reference contracts, 49 inserted lines |
| Current repository status | Exact-hash reviewed reference; not production-ready or deployment-authorized |

The file contains two contracts and is therefore covered by one source-level
rationale page:

| Contract | Source range | Ripe capability views |
| --- | --- | --- |
| `GreenCcipBurnMintTokenPool` | [lines 11–27](../examples/RipeCcipBurnMintTokenPools.sol#L11-L27) | `canMintGreen() == true`; `canMintRipe() == false` |
| `RipeCcipBurnMintTokenPool` | [lines 33–49](../examples/RipeCcipBurnMintTokenPools.sol#L33-L49) | `canMintGreen() == false`; `canMintRipe() == true` |

Both contracts pass the standard five constructor arguments through to
Chainlink's `BurnMintTokenPool`. The two capability methods are the only
Ripe-specific methods:

| Method | Selector |
| --- | --- |
| `canMintGreen()` | `0x40fd6f94` |
| `canMintRipe()` | `0x3b6fccc0` |

## Why this reference exists

RipeHq authorizes GREEN and RIPE minting through different capability views.
A CCIP BurnMint pool must remain the direct token-mint caller, so each pool
needs the matching RipeHq capability while rejecting the other token's
capability. The selected reference inherits Chainlink's concrete pool instead
of reproducing its bridge state machine.

The active Solidity reference supersedes the from-scratch
[`ExampleGreenCcipBurnMintPool.vy`](../examples/ExampleGreenCcipBurnMintPool.vy),
which remains frozen historical comparison code. The Vyper example introduced
a larger independent bridge surface, finite bounds, a nonstandard sixth
constructor argument, and a timestamp-conversion difference. Neither example
is an admitted production component.

## Dated compiler and review evidence

The Round-3 independent review
is bound to the current source SHA-256. It reported this exact profile:

| Property | Reviewed result |
| --- | --- |
| Chainlink pool source | `@chainlink/contracts-ccip@1.6.1`; source commit `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3` |
| Shared dependency | `@chainlink/contracts@1.4.0` |
| Compiler | solc `0.8.26`; EVM `paris`; optimizer `80_000`; via IR; metadata hash disabled |
| Each Ripe subclass runtime / creation | 17,472 / 18,952 bytes |
| EIP-170 runtime headroom | 7,104 bytes |
| ABI delta | Only `canMintGreen()` and `canMintRipe()` |
| Storage delta | None; eight inherited entries remain |
| Reviewed scenarios | 28 passing isolated integration scenarios |

These are dated exact-hash review results, not a fresh repository build. The
review harness and dependencies are not committed repository inputs. Current
`rh` still has no authorized production dependency lock, Solidity build
configuration, committed test/gas harness, deterministic ABI/artifact export,
or explorer-verification package for these subclasses.

## Current lifecycle and authorization boundary

[`RH-D008`](../decision-register.md#L129-L139) approves only a complete-or-
disabled launch posture. The pools remain deferred and CCIP remains disabled
unless every production, support, gas, testnet, operational, and promotion gate
closes. Reference-source review does not satisfy those gates.

The pool reference and `Erc20Token.getCCIPAdmin()` are separate changes. The
pools implement the direct mint/burn integration and Ripe capability views;
the token hook affects Token Admin Registry discovery. Neither one proves or
authorizes the other's registration or deployment.

No deployment, pool ownership transfer, Token Admin Registry proposal,
administrator acceptance, remote-pool mapping, rate-limit setting, mint
capability, or activation is established by this file.

## Open gaps and required follow-up

Before this reference can become production code, a separately authorized
package must:

1. bind an exact supported Chainlink release, Solidity dependency lock,
   compiler/EVM/optimizer/IR/metadata profile, license notices, and source tree;
2. commit reproducible compilation, ABI/artifact export, storage/selector-delta,
   inherited-behavior, real-token/RipeHq integration, gas, and verification
   tests;
3. resolve the reviewed cold `releaseOrMint` measurement of 95,902 gas, which
   exceeded the documented 90,000 combined default before the full production
   path;
4. obtain Chainlink confirmation for the subclass, lane/release, registration,
   token-gas, failed-message, and retirement procedures;
5. bind exact pool/token/router/RMN/owner/admin/remote/rate-limit identities and
   the deployment and rollback sequence; and
6. pass independent production-package review, testnet rehearsal, monitoring,
   activation, and release gates.

The repository's only GitHub Actions workflow runs the Python/Vyper test lanes
on manual dispatch and does not compile or test this Solidity reference. None of
the evidence on this page is continuously enforced by repository CI.

## Reproducible source checks

```sh
git diff --name-status \
  91eda49ccd34a25090582aff0695075c4c806011..\
  0642f086d19e3cc62faaf67da096b6511e405320 -- '*.sol'
git log -1 --format='%H %P %T' -- \
  docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol
git hash-object docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol
shasum -a 256 docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol
wc -c docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol
```

Reproducing the historical compiler results requires the separately pinned
dependency environment described by the Round-3 review; this repository does
not currently contain that build package.
