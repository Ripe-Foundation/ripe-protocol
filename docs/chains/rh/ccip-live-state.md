# CCIP live state and remaining operational gates

Status: **LIVE TOPOLOGY AND PRODUCTION TRANSFERS CONFIRMED; OPERATIONAL DISPOSITIONS REMAIN OPEN**

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
send was performed while producing the original 2026-08-11 topology evidence.

## 2026-08-19 production-transfer update

The owner subsequently supplied four production CCIP messages, one for each
token and direction. This corrects any later inference that the live path had
never been exercised. At the `2026-08-19T17:13:01Z` cutoff:

| Direction | Token | Message ID | State | Delivery / receipt |
| --- | --- | --- | --- | --- |
| Robinhood -> Base | RIPE | `0x43423eb2827630c5888d6f183ac8a9d2e233b7d117a362dd16f0e40d54fd58fe` | `SUCCESS` | 1,132 seconds; `0x95dde4aa866dd848125749f6af87e9a34f1cc808c93662cd00e95b60e600ec34` |
| Robinhood -> Base | GREEN | `0x880f6d8445e45b75823b75b8b463af00278d1da5f1be14c04840c11ca740a9bb` | `SUCCESS` | 1,165 seconds; `0xc1e5c55ec8b5572d309c1d5349c2ac8b02ab73f47fa6f12f3c957bd65584d31c` |
| Base -> Robinhood | RIPE | `0x56fd97fe36fb08033fb0533883b16c501e01e413ce87d872d3ae74a3491ec97f` | `SUCCESS` | 1,198 seconds; `0xda735ce964a4de0b28d4cfc7337ef801f2c8720012063f56376130ee37fd4323` |
| Base -> Robinhood | GREEN | `0x351ed02f27de5eda6bd62fdba5df3f6af7f9f948e57b1b0b8c8d5cdf40a506bd` | `SUCCESS` | 1,486 seconds; `0xebf2ae00014222409eb6173ca5503034590b935c8fb208f1b6f68ac7081a0067` |

All four successful destination transactions called the relevant OffRamp with
selector `0xf58e03fc`, decoded as `execute(bytes32[2],bytes)`, and had successful
receipts using 190,229, 190,262, 168,365, and 168,398 total transaction gas.
Each CCIP message carried a `90,000` destination token-gas amount. These are
automatic executions, not owner manual retries.

This proves that both live token pools completed both directions with the
current configuration. It does not turn four live observations into a
worst-case gas proof. The evidence and links are recorded in
[`ccip-live-transfers-20260819.json`](evidence/ccip-live-transfers-20260819.json).
Its SHA-256 digest is
`b24b1a512c80b0ba45192132fd5bda357b66d3ea7adbe5393b2edc47a1444ce2`.

The latency variance is intra-lane, not merely directional. Base -> Robinhood
sequences 1806 and 1807 were sent 96 seconds apart but arrived 384 seconds
apart; their delivery times differ by 288 seconds (19m58s versus 24m46s).
Commit-round batching is a plausible explanation—a message just missing a
round waits for the next—but these four transfers do not prove that mechanism or
bound its tail. Before any fast-lane refill buffer or stage-B age cap is fixed,
measure source finality and commit/execution round timing across consecutive
sequence numbers and multiple rounds. Configure from the observed tail plus an
explicit margin, not from the maximum or midpoint of this four-message sample.

## Open owner and evidence gates

1. **Rate limits and rate-limit administration.** All four pools currently have
   inbound and outbound rate limiting disabled (`false, 0, 0`), and every
   `rateLimitAdmin` is the zero address. The owner must explicitly select a policy or
   explicitly accept that posture. This repository does not choose or apply one.
2. **Automatic-execution destination gas.** The 2026-08-19 production messages
   prove successful automatic execution for RIPE and GREEN in both directions.
   The historical isolated mock measured `releaseOrMint` at 78,813 gas warm and
   95,902 gas cold, while all four successful messages carried a `90,000` destination
   token-gas amount. Operational readiness still requires accepted measurement
   of the worst-case full real-token OffRamp path and confirmation of the
   configured destination-token gas overhead/margin. The mock numbers are risk
   evidence, not a production limit, and the live total transaction gas is not
   the same quantity as the pool subcall allowance.
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
