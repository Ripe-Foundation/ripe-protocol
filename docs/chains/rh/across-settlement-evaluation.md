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
is an **Ethereum mainnet** address.

### Ethereum mainnet GREEN/RIPE: what is and is not established

This distinction matters because an earlier revision of this document
overstated it. Stated precisely:

**Established (repository scope).** No Ethereum mainnet GREEN or RIPE deployment
is *configured in this repository*. The full deployment surface —
`config/Ccip.py`, `migrations/`, and `migration_history/` — defines exactly four
networks: `base-mainnet`, `base-sepolia`, `robinhood-mainnet`,
`robinhood-testnet`. There is no Ethereum mainnet migration namespace or history
directory. The only `eth-mainnet` strings in the tree are generic
explorer/verifier tooling entries (`scripts/migrate.py:164`,
`scripts/utils/verify_etherscan.py:67`, `scripts/utils/safe_account.py:36`), not
deployment configuration.

**Established (bounded external check).** `eth_getCode` on Ethereum mainnet
returns `0x` for both Base token addresses —
GREEN `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` and
RIPE `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` (public RPC
`ethereum-rpc.publicnode.com`, 2026-08-18). This rules out an *address-identical*
deployment only.

**Not established.** That no GREEN or RIPE token exists anywhere on Ethereum
mainnet at some other address. Repository configuration is evidence of what this
repository deploys, not proof of global non-existence. Closing this requires an
owner statement or an external registry check, neither of which is in scope
here.

### Why the determination holds either way

The conclusion does not depend on the open question above. Even if an Ethereum
mainnet GREEN/RIPE already existed, Across onboarding would still require:

1. Across DAO governance to call `setPoolRebalanceRoute` and
   `enableL1TokenForLiquidityProvision` (both `onlyOwner`); **and**
2. that mainnet token to be mint-authorized as the HubPool settlement anchor, so
   HubPool-side supply can be created and destroyed against spoke balances.

Requirement 2 is the trust-boundary problem. Under the current topology it means
a **third** mint-authorized pool pair — a strictly larger version of the second
mint-critical boundary that
[`ccip-integration-decision.md`](ccip-integration-decision.md) explicitly
rejected. The blocker is the governance action plus the mint-authority
implication, not the mere existence or non-existence of a mainnet token.

The canonical-bridge adapter is *not* the blocker. `relayTokens` only fires when
`netSendAmounts[i] > 0`; a self-relay design would never trigger it. Across V4
also removed per-chain custom adapters in favour of a universal verifier, and
Robinhood Chain is already onboarded (`CHAIN_IDs.ROBINHOOD: 4663` in
`constants/src/networks.ts`). **The chain is not the problem. The token is.**

## The permissionless-deposit footgun

`SpokePool._depositV3` (`:1383`) checks the depositor *address format*, non-zero
output token, quote timestamp, fill deadline and exclusivity — and performs **no
token allowlist check**. Route enablement is dead code
(`SpokePool.sol:92`, `DEPRECATED_enabledDepositRoutes`). `_fillRelay` likewise
has no token check.

Consequently `deposit(GREEN, ...)` **succeeds on-chain**. It does not revert. It
then becomes unrecoverable by the proof chain above, absent Across admin action.

**A successful contract deposit is not evidence of a supported route.** Any
integration must fail closed against the live route allowlist and must never
construct a deposit for an arbitrary token.

## `depositor` is caller-supplied and controls the funds — critical

An earlier revision of this document said `_depositV3` "validates depositor".
That wording was too loose and could be read as binding. It does not bind.

`depositor` is an ordinary parameter of both `deposit()` (`:533`) and
`depositV3()` (`:611`). The only check is
`params.depositor.checkAddress()`, which resolves to
`isValidAddress` in `contracts/libraries/AddressConverters.sol:19`:

```solidity
return uint256(_bytes32) >> 160 == 0;
```

That asserts the upper 12 bytes are zero — a **format check**. It does not bind
`depositor` to `msg.sender`, and it does not reject the zero address. Funds are
pulled from `msg.sender`
(`safeTransferFrom(msg.sender, address(this), params.inputAmount)`), so the payer
and the recorded `depositor` are independent.

`depositor` carries two distinct authorities:

1. **Refund beneficiary on expiry.** Across documents that expired deposits are
   sent to the depositor address on the origin chain, roughly 90 minutes after
   `fillDeadline`.
2. **Authority to rewrite the fill.** `speedUpDeposit` (`:1573` path) and
   `fillRelayWithUpdatedDeposit` (`:1107`) both call
   `_verifyUpdateV3DepositMessage`, which verifies the EIP-712 signature against
   `relayData.depositor` (`:1593` → `SignatureChecker.isValidSignatureNow`). A
   valid depositor signature sets `updatedRecipient` and `updatedOutputAmount`,
   and `_transferTokensToRecipient` pays
   `recipientToSend = relayExecution.updatedRecipient`.

**Therefore a deposit whose `depositor` is an attacker delivers the user's funds
to the attacker on the ordinary success path.** Calldata naming the user as
`recipient` and an attacker as `depositor` looks correct to a recipient-only
check; the attacker then signs an update redirecting `updatedRecipient` to
itself, any relayer fills to that address, and settlement proceeds normally.
This needs no expiry, no exclusivity manipulation, and no relayer collusion.

Mitigation is a hard equality assertion, not a sanity check:

- **`depositor` MUST equal the connected signing address**, refuse-to-sign, with
  at least the force of the `recipient` assertion. `depositor != 0` is
  insufficient — a non-zero attacker address is the actual attack, and a zero
  `depositor` separately burns the refund leg.
- `recipient` validation alone is **not** load-bearing. It secures neither the
  refund path nor the updated-fill path.

Not a finding, checked and cleared: `depositor == address(0)` does not yield
universal signature forgery. `_verifyDepositorSignature` uses OpenZeppelin
`SignatureChecker.isValidSignatureNow` rather than raw `ecrecover`, so an invalid
signature reverts rather than recovering to the zero address.

## API surface: `/suggested-fees` is legacy — implement against the Swap API

The quotes captured below were taken from `GET /suggested-fees`. **That endpoint
is no longer actively maintained.** Across' current API reference carries the
notice:

> The `/suggested-fees` API is no longer actively maintained. New integrations
> should use the Swap API instead.

Source: <https://docs.across.to/api-reference/suggested-fees/get>, read
2026-08-18. The named replacement is the Swap API
(`/api-reference/swap/approval/get`); Across also publishes a "Migrate from
Suggested Fees to the Swap API" guide.

Consequences, and the distinction between them:

- **The captured evidence below remains valid** as a point-in-time observation of
  route support, fee magnitude, fill latency and capacity. It is used here only
  to characterise Across, not as an integration contract.
- **Implementation must not target `/suggested-fees`.** Any `ripe-api` route
  allowlist, quote proxy, or capacity read must be built against the Swap API.
  Fee/limit field names and shapes are not assumed to carry over; they must be
  re-derived against the supported endpoint before any integration relies on
  them.
- The fail-closed allowlist rule is unchanged by the endpoint migration. It is a
  property of the settlement model, not of a particular API version.

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

## Disposition

**Across GREEN/RIPE token bridging is rejected.** This document is the technical
basis for that rejection; the decision itself is recorded by the bridge
integration synthesis, not established here.

Across is retained in scope **only** as a collateral-movement rail for its
already-supported routes. Those routes carry no Ripe token, touch no mint path,
and require no `RipeHq` registration or Across governance action. Moving
collateral and then minting GREEN locally is a distinct acquisition flow, not a
faster GREEN bridge, and must not be described as one. CCIP remains the only
direct GREEN/RIPE transfer route.

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
