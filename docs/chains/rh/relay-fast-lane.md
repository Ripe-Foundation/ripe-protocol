# Relay fast lane for GREEN and RIPE

**Status:** Evaluation and prototype. Not authorized, not audited, not integrated.
No onboarding requested, no funds committed.

**Date:** 2026-08-20 · **Chains:** Base (8453) ↔ Robinhood (4663)

Detailed findings live in
[`bridge-integration-security-review.md`](bridge-integration-security-review.md).
Raw measurements are pinned under [`evidence/`](evidence/).

---

## The short version

CCIP already moves GREEN and RIPE and is the only approved route. It works —
four production transfers were executed, 18m52s–24m46s per hop. A fast lane is
about latency, nothing else.

Fast bridges are fast because a **solver pays the user on the destination chain
out of inventory it already holds**, then reclaims the user's deposit on the
origin chain hours later. Nothing is minted and no message is proved. That is
the whole trick.

Nobody else holds GREEN or RIPE inventory. So a fast lane means **Ripe runs the
solver** — which is why this is a treasury question wearing an infrastructure
costume, and why the technical work is small compared to the decision.

**Across cannot do this at all** and is not a fallback; see the end of this
document.

---

## How Relay works

Moving 100 GREEN from Base to Robinhood:

```
1. DEPOSIT   (Base)       user → RelayDepository        100 GREEN escrowed
                          permissionless; Relay cannot block it

2. FILL      (Robinhood)  Ripe's float → user           ~100 GREEN paid
                          ← USER IS DONE. Seconds.
                          Relay is not in this path.

──────── the user has left; everything below is Ripe getting repaid ────────

3. ATTEST    (Relay hub)  Relay's attestor credits Ripe's solver alias
                          requires an ORACLE_ROLE signature

4. WITHDRAW  (Base)       RelayDepository → Ripe        100 GREEN reclaimed
                          requires Relay's allocator signature
```

The user never receives the tokens they deposited. They get Ripe's float on the
destination; their deposit becomes Ripe's on the origin. Ripe's net GREEN
position is therefore **flat** — the same total, held in the wrong proportion
across two chains.

**If Relay never signs step 4, the user was still paid at step 2.** A Relay
failure after a fill is a Ripe balance-sheet loss, never a user-facing one.
Before a fill it is the reverse: the deposit is escrowed and there is no
permissionless timeout refund, so a fill Ripe declines leaves the user's tokens
waiting on a Relay-authorised recovery. The UI must never present "deposit
accepted" as a guaranteed fill.

### Whose contracts

| | Contract | Controlled by | Holds |
| --- | --- | --- | --- |
| Relay's | `RelayDepository` `0x4cd0…bc31` (same address both chains) | Relay EOAs | the **user's** deposit |
| Relay's | `RelayHub` / `RelayOracle` / `RelayAllocator` (chain 537713) | Relay | the ledger of who is owed what |
| Ripe's | `FastLaneFloat.vy` | Ripe governance | **Ripe's float** |

### Permissionless to fund, permissioned to withdraw

Anyone may deposit — `depositErc20` pulls tokens and emits an event, no
allowlist. Nothing leaves without Relay: `execute(CallRequest, signature)` is
gated on `allocator.isValidSignatureNow(...)`, and it is the **only** exit in the
281-line contract. No timeout, no rescue, no dispute path.

Becoming a solver needs no approval — the alias is derived, not registered, and
`suspended` is a denylist. But being allowed to fill is worth little when being
repaid runs through Relay's key on every single withdrawal. **Ripe can do the
filling alone; it can never do the getting-repaid alone.**

---

## What Relay gives us today, unmodified

GREEN and RIPE already quote on Relay with no listing and no contact — both
chains report `tokenSupport: All`. But Relay is not bridging our token. It is
bridging **ETH**, with a DEX swap bolted on each end:

```
Base:       GREEN --[KyberSwap]--> ETH
Bridge:     ETH  Base → Robinhood     ← the only leg Relay's solver fills
Robinhood:  ETH  --[0x aggregator]--> GREEN
```

Measured 2026-08-19 ([`evidence/relay-swap-lane-quotes-20260819.json`](evidence/relay-swap-lane-quotes-20260819.json)):

| Size | Full route | Base leg (GREEN→ETH) | Robinhood leg (ETH→GREEN) |
| --- | --- | --- | --- |
| ~$100 | −1.36% | +0.14% | −1.53% |
| ~$1,000 | **−85.81%** | −0.02% | **−86.12%** |
| ~$10,000 | −98.58% | −20.56% | `NO_SWAP_ROUTES_FOUND` |

**The entire constraint is the GREEN pool on Robinhood.** Base is healthy to
~$5,000. RIPE is worse in kind, not degree: unusable at any size — 13.22% at
1 RIPE, 20.92% at 10 — consistent with there being no RIPE venue on Robinhood.

Two consequences:

1. **Deepening the Robinhood GREEN pool improves this route immediately**, with
   no Relay involvement, no contract, no solver key and no audit. It is by far
   the cheapest lever available and it is entirely ours to pull.
2. **The swap lane must not be exposed as a GREEN bridge.** A user "bridging"
   this way is selling GREEN into one Ripe pool and buying it out of another —
   two trades against our own liquidity, moving the Robinhood price ~86% at
   1,000 GREEN. It also sells into the pool that prices Ripe's borrow rate on
   Base (M-5), and it is an opaque aggregator route of exactly the class the
   security review refuses pending recursive decode.

Detection must key on **route shape, not cost**: `swapImpact` reads −0.34% on
the approved pure-bridge collateral route and ~0.00% on a genuinely deep swap,
so it separates neither direction.

The load-bearing check is **`(chainId, address)` identity**: every leg's input
and output currency must equal the endpoint Ripe configured for that leg. A
route that is genuinely a bridge has identity legs by construction — USDC→USDC,
USDG→USDG — and anything else is a swap. Do not compare token *symbols*: they
are attacker-controlled metadata on the token contract, so a symbol match proves
nothing about which asset moved.

`router != 'relay'` is a useful **observed heuristic** on top, not a proof. Every
swap leg we sampled named a third-party aggregator and every bridge leg named
`relay`, but that is Relay's current labelling, not a guarantee — a first-party
Relay swap would presumably label itself `relay` and defeat it. Note also that
the aggregator name is not stable across identical calls (`kyberswap` on one,
`okxEvm` on the next), so allowlisting aggregator names is not an option
either.

---

## What a direct lane requires

A float of the token on **each chain**, in a Ripe-controlled contract — not
deposited into Relay's. Size it to the peak *one-way* imbalance over one CCIP
round trip, not to volume: balanced flow barely moves it, one-directional flow
drains the destination side and CCIP refills it.

**CCIP does not go away. It becomes the multiplier on committed capital.** Halve
the round trip, halve the float.

Per token per chain, so GREEN and RIPE across two chains is four deployments.

---

## What we built

[`contracts/core/FastLaneFloat.vy`](../../../contracts/core/FastLaneFloat.vy) —
Vyper 0.4.3, 53 tests. Holds the float and pays a fill against a solver-signed
order.

**It cannot verify that the origin deposit happened.** There is no proof of it
on this chain; it pays against a signature. So:

> **The caps are the security boundary. The signature is not.**

Per-fill amount, aggregate notional, outstanding entry count and entry age. If
the solver key is compromised, those bound the loss; everything else only
narrows the blast radius.

Design points worth knowing:

- **One timestamp per entry, set at fill, never reset.** Age always means "time
  since we paid the user," which makes the ledger chronological by construction
  and the oldest lookup O(1) — so the age cap cannot be turned into a gas
  griefing vector against the hot path.
- **`fill` reads `RipeHq.mintEnabled` and the token's live `ripeHq`.** A fill is
  a plain transfer that ignores `mintEnabled`, while the CCIP refill is blocked
  by it — uncoupled, disabling minting would stop replenishment while the float
  kept draining at full rate.
- **A drain floor** reserves inventory using `balanceOf` rather than the
  contract's own counters. It is not the refill-failure control — the aggregate
  cap is — but it is the only bound that survives the ledger being wrong.
- **Asymmetric levers.** Guardians pause and burn the solver key immediately;
  unpausing, raising any cap, rotating the solver and moving float all serve a
  timelock, and every queued action is void if anything was tightened after it
  was queued.
- **One-way retirement.** A retired instance cannot be rekeyed back into
  service, and float leaves only to an address fixed at deploy — there is no
  arbitrary-call path anywhere in the contract.

---

## What blocks it

**Two vendor questions, both unanswered, both hard blockers:**

1. **Custom `fillContract`.** Signed quotes encode a Relay router in
   `output.extraData`, and `extraData` is inside the signed order id, so it
   cannot be substituted afterwards. Is there a configuration path that emits
   *our* payout address?
2. **Exact-output quoting**, so `minimumAmount == expectedAmount`. Ordinary
   exact-input quotes leave them unequal; the Oracle validates only
   `paidAmount >= minimumAmount`.

Until those are answered, `FillOrder` stays a **local placeholder that is
explicitly not Relay-compatible** — not canonical `OrderV1`, not EIP-191, no
order-id calldata suffix. A real Relay signature will not verify, and Relay's
Oracle cannot attest a transaction shaped like this one. Porting the canonical
schema against pinned SDK vectors is deliberately deferred rather than guessed.

One requirement the port must inherit, because it was learned the expensive way:
**bound order age, not time-to-expiry.** `deadline <= now + horizon` combined with
`now <= deadline` admits exactly `[deadline - horizon, deadline]`, so a year-old
order is merely inadmissible until its final window and then fills — at a moment
the signer chose by picking the deadline. Age is only knowable from a signed
issuance value. If canonical `OrderV1` carries no issuance field, freshness
cannot be approximated from the deadline; the lane needs one from elsewhere,
because that approximation is the defect.

**Restoration is a balance proof, not a receipt proof.** Clearing exposure
requires the float to have actually risen, so a mistaken governor cannot recycle
capacity — but it binds amount, not origin. An authenticated CCIP receiver is
still required (H-5).

**Four more questions for Relay,** none blocking but all needed before sign-off:
ERC-1271 solver support or a restricted withdrawal receiver; key custody of
`allocator` `0x63C1…1b56` and `owner` `0xF61A…775A`; withdrawal cadence, since
our age cap is parameterised on it; and whether a bug bounty exists — none was
found.

---

## Custody exposure

The `RelayDepository` is a **shared pool**, not a segregated account, and it
already holds other participants' funds. Its `allocator` and `owner` are bare
EOAs; `setAllocator` is single-step with no timelock, and `execute()` takes an
arbitrary call array. One key moves the whole pooled balance on a chain.

That exposure exists from the moment Ripe's receivable is non-zero, regardless
of size, which is why the **age** cap matters more than the notional one. Relay's
own team confirmed in writing (Zellic finding 3.3 response) that production
custody is a permissioned signer. Every published audit explicitly excludes key
custody, so only Relay can answer it.

---

## Why not Across

Not an integration gap — the repayment path is closed by construction. A relayer
is repaid only via `SpokePool.executeRelayerRefundLeaf`, whose root comes from
`HubPool.executeRootBundle`, which runs
`require(poolRebalanceRoutes[l1Token, chainId] != 0, "Route not whitelisted")`
**before** the `netSendAmounts > 0` branch — so even a zero-value self-relay
reverts. That mapping is keyed by an **Ethereum mainnet** token and set by
`onlyOwner`, i.e. Across DAO. It needs an Ethereum GREEN/RIPE that does not
exist plus a governance vote we do not control.

The dangerous part is that `SpokePool._depositV3` has **no token allowlist** and
route enablement is dead code, so `deposit(GREEN, ...)` **succeeds on-chain** and
is then unrecoverable. Blocking it is one governance call per chain —
`setBlacklist(<SpokePool>, True)` — and ordering is the entire value: applied
before any protocol token reaches the SpokePool it is preventive; applied after,
it converts stranded-pending into stranded-permanently.

Across remains useful for **collateral only** (USDC↔USDG, WETH↔WETH), where its
live routes already match Ripe's selected asset set.
