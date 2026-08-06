# RH asset-admission assumptions

> **DRAFT — offline release support, not activation authority.** This
> checklist is an admission precondition for an issuer-controlled RH asset; it
> does not register an asset, bind a vault, change configuration, or approve a
> deployment. The reviewed deployment/activation boundary is recorded in the
> [GuardedErc20 record](../smart-contract-changes/guarded-erc20.md#reviewed-implementation-snapshot).

## Controlling accounting boundary

Admission is **exact-transfer-only**. A successful deposit must credit exactly
the requested amount; a successful withdrawal must prove the vault outflow and
recipient increase are both exactly the returned amount
([GuardedErc20.vy:51-79](../../../../contracts/vaults/GuardedErc20.vy#L51-L79),
[GuardedErc20.vy:82-137](../../../../contracts/vaults/GuardedErc20.vy#L82-L137)).
The Teller coverage independently rejects short receipt, excess receipt, and a
pre-existing donation being used to mask a short current receipt
([test_teller_deposit.py](../../../../tests/core/teller/test_teller_deposit.py),
[test_stock_token_vault_comparison.py:587-684](../../../../tests/vaults/test_stock_token_vault_comparison.py#L587)).

The **truthful-balance boundary** is the exact 32-byte result of
`balanceOf(holder)`. A failed call or any other response length is unknown;
unknown or `custody < total nominal liability` makes the Guarded credit-facing
amount zero and blocks value-moving operations
([GuardedErc20.vy:204-218](../../../../contracts/vaults/GuardedErc20.vy#L204-L218),
[GuardedErc20.vy:233-254](../../../../contracts/vaults/GuardedErc20.vy#L233-L254),
[GuardedErc20.vy:278-292](../../../../contracts/vaults/GuardedErc20.vy#L278-L292)).
That boundary is only as truthful as the token's `balanceOf` implementation;
the vault cannot detect a token that returns a well-formed but false value
([guarded-erc20.md, residual risk](../smart-contract-changes/guarded-erc20.md#residual-risks-and-trust-assumptions)).

`SimpleErc20` is unsuitable by default for an issuer-controlled Stock Token.
Its nominal accounting can retain phantom claims after issuer burn or forced
transfer, and the comparison suite demonstrates stale borrowing power and
zero-backed settlement behavior
([stock-token-vault-decision.md, rejected unchanged](../stock-token-vault-decision.md#rejected-unchanged-simpleerc20),
[test_stock_token_vault_comparison.py:93-256](../../../../tests/vaults/test_stock_token_vault_comparison.py#L93)).
An exception therefore requires a new owner decision and evidence at least as
strong as the Guarded qualification below; this document creates no exception.

## Token-qualification checklist

Each item is fail-closed. Record the deployed token address, chain ID, code
hash, observation block/hash, command, and evidence artifact for every check;
the repository release schema demonstrates those evidence fields
([deployment-manifest-v2.schema.json](../schemas/deployment-manifest-v2.schema.json)).

- [ ] **Identity is pinned.** The release packet binds the exact deployed token
  address and runtime code hash, not a symbol or issuer name. Upgrade/admin
  controls and their current holders are separately enumerated; the test model
  treats administrative burn, forced transfer, pause, blocklists, and behavior
  changes as distinct capabilities
  ([MockStockTokenControls.vy:8-44](../../../../contracts/mock/MockStockTokenControls.vy#L8),
  [test_stock_token_vault_comparison.py:856-892](../../../../tests/vaults/test_stock_token_vault_comparison.py#L856)).

- [ ] **`balanceOf` is exact and truthful.** Calls for the vault and intended
  recipients succeed with exactly 32 bytes across ordinary, paused, blocked,
  and upgrade states. Guarded classifies any failed or malformed observation as
  unknown
  ([GuardedErc20.vy:278-292](../../../../contracts/vaults/GuardedErc20.vy#L278-L292),
  [test_guarded_erc20.py](../../../../tests/vaults/test_guarded_erc20.py)).

- [ ] **Inbound transfer receipt is exact.** For every supported depositor,
  sender, operator, and amount boundary, the vault custody delta equals the
  attempted transfer amount. Short receipt and donation-masking cases revert
  atomically in the maintained comparison coverage
  ([test_stock_token_vault_comparison.py:587-684](../../../../tests/vaults/test_stock_token_vault_comparison.py#L587)).

- [ ] **Outbound delivery is exact.** `transfer` either returns no data or a
  canonical 32-byte `true`, and both vault outflow and recipient receipt equal
  the reported withdrawal. False, malformed, short, oversized, or non-exact
  delivery is rejected
  ([GuardedErc20.vy:121-135](../../../../contracts/vaults/GuardedErc20.vy#L121-L135),
  [GuardedErc20.vy:257-275](../../../../contracts/vaults/GuardedErc20.vy#L257-L275),
  [test_guarded_erc20.py:895-1014](../../../../tests/vaults/test_guarded_erc20.py#L895)).

- [ ] **Issuer loss powers are reproduced.** Administrative burn, redemption,
  seizure/forced transfer, and any other custody-reduction path are exercised
  against the exact token or a pinned fork; all must produce Guarded
  containment rather than phantom credit
  ([test_stock_token_vault_comparison.py:856-934](../../../../tests/vaults/test_stock_token_vault_comparison.py#L856),
  [GuardedErc20.vy:248-254](../../../../contracts/vaults/GuardedErc20.vy#L248-L254)).

- [ ] **Pause and blocklist roles are complete.** Sender, recipient, and
  operator restrictions are tested for deposit, ordinary withdrawal, and
  external auction delivery; failures preserve token, GREEN, debt, and auction
  state until an authorized retry
  ([test_stock_token_vault_comparison.py:419-586](../../../../tests/vaults/test_stock_token_vault_comparison.py#L419),
  [test_stock_token_vault_comparison.py:1275-1351](../../../../tests/vaults/test_stock_token_vault_comparison.py#L1275)).

- [ ] **Surplus behavior is accepted explicitly.** `custody > nominal` remains
  uncredited and cannot substitute for a short current receipt; donation and
  recovery behavior is evidenced before admission
  ([GuardedErc20.vy:66-76](../../../../contracts/vaults/GuardedErc20.vy#L66-L76),
  [test_stock_token_vault_comparison.py:639-684](../../../../tests/vaults/test_stock_token_vault_comparison.py#L639)).

- [ ] **Deficit and total loss are operationally owned.** A one-unit deficit
  freezes Guarded value movement and reports zero credit value, while
  CreditEngine retains the nonempty asset's debt-resolution terms; this does
  not itself settle loss or bad debt
  ([GuardedErc20.vy:93-100](../../../../contracts/vaults/GuardedErc20.vy#L93-L100),
  [CreditEngine.vy:727-769](../../../../contracts/core/CreditEngine.vy#L727-L769),
  [credit-engine.md, debt-health behavior](../smart-contract-changes/credit-engine.md#debt-health-and-liquidation-behavior)).

- [ ] **Auction delivery is not inferred from eligibility.** Eligibility,
  liquidation state, auction creation, purchase, token delivery, and bad-debt
  recognition are recorded as separate transitions; a continuing Guarded
  deficit makes settlement revert atomically
  ([credit-engine.md, complete execution flow](../smart-contract-changes/credit-engine.md#exact-source-delta-and-complete-execution-flow),
  [test_stock_token_vault_comparison.py:719-793](../../../../tests/vaults/test_stock_token_vault_comparison.py#L719)).

- [ ] **Decimals and smallest-unit behavior are pinned.** The exact token
  decimals and one-base-unit deposit/withdraw path are tested; the comparison
  suite includes one-unit and 6/18-decimal boundaries
  ([test_stock_token_vault_comparison.py:685-718](../../../../tests/vaults/test_stock_token_vault_comparison.py#L685),
  [test_stock_token_vault_comparison.py:1355-1380](../../../../tests/vaults/test_stock_token_vault_comparison.py#L1355)).

- [ ] **Price and custody evidence remain separate.** CreditEngine prices only
  a nonzero amount reported by the vault; it does not independently observe
  token custody
  ([CreditEngine.vy:727-744](../../../../contracts/core/CreditEngine.vy#L727-L744),
  [credit-engine.md, direct answers](../smart-contract-changes/credit-engine.md#direct-answers-to-the-owners-questions)).

- [ ] **Monitoring and response authority are bound.** The exact signal
  endpoints, alert destinations, pause/configuration signers, recovery
  authority, and evidence retention are approved in
  [stock-backing-monitoring-runbook.md](stock-backing-monitoring-runbook.md).
  Until those owner fields are resolved, admission remains incomplete.

## Admission decision

Default disposition is **do not admit** if any item is absent, stale, bound to a
different token/runtime, or owner-unresolved. Passing this offline checklist is
technical qualification only; deployment, registry binding, asset
configuration, activation, and monitoring installation remain distinct
owner-controlled actions
([guarded-erc20.md, executive verdict](../smart-contract-changes/guarded-erc20.md#executive-verdict)).
