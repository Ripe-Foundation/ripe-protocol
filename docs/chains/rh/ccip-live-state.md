# CCIP live state and remaining operational gates

Status: **LIVE TOPOLOGY CONFIRMED; OPERATIONAL DISPOSITIONS REMAIN OPEN**

Evidence snapshot: [ccip-live-snapshot-20260811.json](evidence/ccip-live-snapshot-20260811.json)

Evidence file SHA-256:
`41acd8763b41d45ecef8541d1a31b8ac58cc582cc0a333d3f5f2f31f9e7357fa`.
The derived ledger validates this exact digest plus schema, chain/topology,
reciprocal wiring, and token-specific capability fields before accepting the
external fact.

This document supersedes older “not deployed,” “disabled,” and “owner-parked” CCIP
status statements. Those older documents remain historical decision and research
records; they are not current-state authority.

## Confirmed live topology

Read-only public-chain queries on 2026-08-11 confirmed the following on both Base
mainnet (chain ID 8453) and Robinhood mainnet (chain ID 4663):

| Token | RipeHq ID | Base pool | Robinhood pool | Capability |
| --- | ---: | --- | --- | --- |
| RIPE | 23 | `0x6E3f8465aF365a2C400C361783ea51ad44b3C836` | `0xE51aF1311832818A6D366081Fc535CA56357a6EE` | RIPE only |
| GREEN | 24 | `0xEF56E5036728718Baa577257Ff4FA9259E9e895f` | `0x4B19f165Bb1Ce3f19Bbe828D150706B9deeEeC95` | GREEN only |

Each TokenAdminRegistry currently points the local token at the matching pool. Each
token administrator and pool owner is the governance Safe, with no pending token
administrator. Each pool reports
`BurnMintTokenPool 1.5.1`, uses the
configured router and RMN proxy, supports exactly the peer selector, and contains the
reciprocal remote token and pool. The exact RipeHq registration and capability-event
transactions, snapshot blocks, runtime hashes, and addresses are in the JSON evidence.

The repository candidate/reference implementation is
`solidity/src/RipeCcipBurnMintTokenPools.sol`, which inherits the vendored 1.5.1
source. The 1.6.1 example under `docs/chains/rh/examples/` is superseded design
research. Neither repository file is proof of exact live-pool creation provenance.
The topology, capability, reported type/version, and runtime-hash evidence above does
not resolve the exact live source set, compiler version/settings, constructor
arguments, or creation bytecode/artifact identity.

## What “live” does and does not mean

Registration, token-pool routing, remote wiring, ownership, and RipeHq mint
capabilities are active onchain. That corrects the old repository status.

It does **not** prove operational readiness, authorize another transaction, or prove
that an arbitrary transfer will execute automatically. In particular, no cross-chain
send was performed while producing this evidence.

## Open owner and evidence gates

1. **Rate limits and rate-limit administration.** All four pools currently have
   inbound and outbound rate limiting disabled (`false, 0, 0`), and every
   `rateLimitAdmin` is the zero address. The owner must explicitly select a policy or
   explicitly accept that posture. This repository does not choose or apply one.
2. **Automatic-execution destination gas.** The historical isolated mock measured
   `releaseOrMint` at 78,813 gas warm and 95,902 gas cold. The cold pool call alone
   exceeded the historical 90,000 combined default before real RipeHq work and
   OffRamp balance checks. Operational readiness requires accepted measurement of the
   full real-token OffRamp path and confirmation of the configured destination-token
   gas overhead/margin. The mock numbers are risk evidence, not a production limit.
3. **Live transaction backend.** `scripts/ccip_send.py` validates exact decimal
   amounts, manifests, profile identity, and RPC chain ID, then supports fork
   simulation only. Live mode fails with `CCIP_LIVE_SIGNER_UNBOUND`; no private-key or
   Safe backend is implied by an account label.
4. **Exact live creation identity.** The repository contains a candidate/reference
   implementation, but the exact source set, compiler version/settings, constructor
   arguments, and creation bytecode/artifact identity for the four live pools have not
   been bound. Runtime hashes and current topology/capability reads do not establish
   that creation provenance.
5. **Historical transaction provenance.** Current TokenAdminRegistry pool assignments
   and remote mappings were read and match, but this snapshot does not yet bind the
   exact historical `setPool` and `applyChainUpdates` transaction hashes. The current
   mutation gate requires that provenance; removing the gate instead requires a
   separate explicit owner policy change.

None of these gates should be silently converted into a default. Rate-policy changes,
signer integration, new transactions, and release approval each require their own
explicit authority.
