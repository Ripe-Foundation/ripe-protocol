# Across settlement-path evaluation for GREEN and RIPE

Status: **Research finding — no decision, no authorization, no deployment**

Evaluation date: 2026-08-18

Scope: whether Across can settle a GREEN or RIPE bridge transfer between Base
mainnet (8453) and Robinhood mainnet (4663), and what onboarding would require.

Evidence snapshot:
[`evidence/across-live-snapshot-20260818.json`](evidence/across-live-snapshot-20260818.json)

Evidence file SHA-256:
`197df8d75d97410811b7b1f0aa93e2b785bf26424629c61b3f3bedaf33b83c2e`.

## Source pins

All contract statements below are bound to a single upstream commit. `master`
is not an acceptable pin and is not used as authority here.

| Property | Value |
| --- | --- |
| Repository | `https://github.com/across-protocol/contracts` |
| Commit | `8aa73521538caff624f76d1fc9e6f8984a1b01be` |
| Commit date | 2026-08-14T19:29:30+02:00 |
| Package version | `@across-protocol/contracts` 5.0.27 |

Token and network facts are read from `across-protocol/constants`
(`src/networks.ts`, `src/tokens.ts`). Live API responses were captured verbatim
at **2026-08-18T17:58:53Z** and are reproduced in the evidence JSON. API results
are point-in-time and are not a durable supported-route authority; see
"Operational consequences".

## Determination

**Across cannot repay a GREEN or RIPE relayer on the origin chain, or on any
other chain, without Across DAO governance onboarding. Origin-chain repayment is
not an escape hatch — it is gated identically to every other repayment chain.**

This is a governance and token-registration blocker, **not** a custom
HubPool/canonical-bridge adapter engineering task. That distinction is the
decision-relevant part: adapter work is something Ripe could perform; the actual
blocker is an external governance action plus an Ethereum mainnet GREEN/RIPE
deployment that Ripe has already rejected on trust-boundary grounds.

## Proof chain

Each step is necessary; breaking any one of them blocks repayment.

1. A relayer is repaid only by `SpokePool.executeRelayerRefundLeaf`
   (`contracts/spoke-pools/SpokePool.sol:1276`). Its sibling
   `claimRelayerRefund` (`:1324`) only pays out balances already accrued from a
   transfer that failed during a prior bundle execution; it cannot originate a
   refund. There is no permissionless expired-deposit claim.
2. `executeRelayerRefundLeaf` verifies a Merkle proof against
   `rootBundles[rootBundleId].relayerRefundRoot`, which is written only by
   `SpokePool.relayRootBundle` (`:375`), declared `onlyAdmin`.
3. The single non-test caller of `relayRootBundle` is `HubPool.executeRootBundle`
   (`contracts/hub-pool/HubPool.sol:683`), reached by adapter `delegatecall` and
   only when `groupIndex == 0`.
4. `executeRootBundle` calls `_sendTokensToChainAndUpdatePooledTokenTrackers`
   **before** that relay step. That function begins each loop iteration with an
   unconditional route check:

   ```solidity
   address l2Token = poolRebalanceRoutes[_poolRebalanceRouteKey(l1Token, chainId)];
   require(l2Token != address(0), "Route not whitelisted");
   ```

   The check runs **before** the `if (netSendAmounts[i] > 0)` branch. An
   origin-chain repayment carries `netSendAmount <= 0` — nothing needs bridging,
   because the deposited funds already sit in the origin SpokePool — but the leaf
   still reverts with `"Route not whitelisted"`. Zero-value settlement does not
   bypass registration.
5. Because the revert happens before the `groupIndex == 0` relay, the
   `relayerRefundRoot` never reaches the SpokePool at all.
6. `setPoolRebalanceRoute` (`HubPool.sol:349`) and
   `enableL1TokenForLiquidityProvision` (`:395`) are both `onlyOwner`, i.e.
   Across DAO governance.

## Why onboarding is worse than an adapter problem

`poolRebalanceRoutes` is keyed `(l1Token, destinationChainId)`, where `l1Token`
is an **Ethereum mainnet** address. GREEN and RIPE have no Ethereum mainnet
deployment: `config/Ccip.py` defines exactly four networks (`base-mainnet`,
`robinhood-mainnet`, `base-sepolia`, `robinhood-testnet`).

Onboarding GREEN/RIPE to Across therefore requires an Ethereum mainnet GREEN and
RIPE — which under the current topology means a **third** mint-authorized CCIP
pool pair. That is a strictly larger version of the second mint-critical trust
boundary that
[`ccip-integration-decision.md`](ccip-integration-decision.md) explicitly
rejected. The rejection reasoning applies with more force here, not less.

The canonical-bridge adapter is *not* the blocker. `relayTokens` only fires when
`netSendAmounts[i] > 0`; a self-relay design would never trigger it. Across V4
also removed per-chain custom adapters in favour of a universal verifier, and
Robinhood Chain is already onboarded (`CHAIN_IDs.ROBINHOOD: 4663` in
`constants/src/networks.ts`). **The chain is not the problem. The token is.**

## The permissionless-deposit footgun

`SpokePool._depositV3` (`:1383`) validates depositor, non-zero output token,
quote timestamp, fill deadline and exclusivity — and performs **no token
allowlist check**. Route enablement is dead code
(`SpokePool.sol:92`, `DEPRECATED_enabledDepositRoutes`). `_fillRelay` likewise
has no token check.

Consequently `deposit(GREEN, ...)` **succeeds on-chain**. It does not revert. It
then becomes unrecoverable by the proof chain above, absent Across admin action.

**A successful contract deposit is not evidence of a supported route.** Any
integration must fail closed against the live route allowlist and must never
construct a deposit for an arbitrary token.

## Live facts as captured 2026-08-18T17:58:53Z

Supported routes are bidirectional and cover exactly three assets each way:

| Direction | Routes |
| --- | --- |
| 8453 -> 4663 | USDC->USDG, WETH->WETH, ETH->ETH |
| 4663 -> 8453 | USDG->USDC, WETH->WETH, ETH->ETH |

Neither GREEN nor RIPE appears in `constants/src/tokens.ts`.

Observed quotes:

| Route | Notional | Total fee | Components | Est. fill |
| --- | ---: | ---: | --- | ---: |
| WETH->WETH | 1 WETH | 1.083 bps | 0.788 capital + 0.250 LP + 0.046 gas | 0 s |
| USDC->USDG | 1,000 USDC | 6.057 bps | 1.000 capital + 0.057 gas + ~5 conversion | 1 s |

`HubPool.liveness` is `7200` (2 hours) — the settlement window, not the
user-visible fill. `MAX_EXCLUSIVITY_PERIOD_SECONDS` is `31_536_000` (365 days).

**Capacity is inventory-dependent and volatile.** Two captures roughly 40 minutes
apart returned materially different single-transfer caps:

| Route | Earlier capture | 17:58:53Z capture |
| --- | ---: | ---: |
| USDC->USDG `maxDeposit` | ~73,417 USDC | ~41,420 USDC |
| WETH->WETH `maxDeposit` | ~38.5 WETH | ~165.4 WETH |

Any sizing assumption must be read live, never cached as a constant.

## Operational consequences

1. Treat provider route support as an **allowlisted live API result**, not a
   contract capability. The contract will accept what the protocol will not
   settle.
2. Reject GREEN and RIPE explicitly for Across at the integration boundary. Do
   not rely on a route lookup returning empty; fail closed on an allowlist hit.
3. Do not cache `maxDeposit`. Read it per quote.
4. Across remains usable for the supported collateral routes (USDC/USDG,
   ETH/WETH). Those touch no Ripe mint path and require no `RipeHq`
   registration.

## Scope limits

- This evaluates the **V4** settlement path only, which is what the pinned repo
  implements and what the live Base/Robinhood SpokePools serve.
- Across V5 exists: `SpokePool` carries a `nonV5Fill` modifier (`:315`) and
  `_isV5Message` (`:1835`) that route V5-tagged messages away from the V4 fill
  entrypoints. The V5 Gateway/executor is **out of tree** —
  `contracts/external/interfaces/IAcrossV5Executor.sol` states the canonical
  definition lives in the Across V5 periphery repository, which is not public as
  of this evaluation. **The V5 settlement path is therefore unverified here and
  must not be assumed to share these properties.**
- No transaction was constructed, signed, simulated or broadcast. No Across
  contact was made. No onboarding was requested.
