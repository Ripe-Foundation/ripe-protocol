# BasicVault fail-closed nominal ERC-20 candidate

> [!IMPORTANT]
> **Feature-branch candidate only.** This source change does not upgrade an
> immutable deployed vault, integrate into `rh`, deploy a contract, configure
> an asset, or activate a launch route.

## Decision

`BasicVault` is now the single safety implementation for future nominal ERC-20
vaults. `SimpleErc20` composes that module directly, and the separate
`GuardedErc20` contract and ABI are removed.

The protection is automatic and fail-closed: while observed vault custody is
below aggregate nominal liabilities for an asset, value-bearing views return
zero and deposit, withdrawal, and internal-balance movement revert. Restoring
enough backing makes the vault usable again; no permanent brick flag is stored.

## Reviewer follow-up behavior

- A registered asset whose user balance reaches zero still returns its asset
  identity with amount zero. CreditEngine therefore retains that asset's debt
  terms, including the lowest-LTV floor, until Lootbox performs the existing
  asset deregistration flow.
- Stability Pool's indexed getter now reports its actual user asset and amount.
  CreditEngine explicitly excludes stability vault ID `1` from collateral and
  debt-term calculations, while AuctionHouse phase 2 can still process an
  otherwise eligible Stability Pool position.
- An all-deficient position does not set `inLiquidation` when liquidation
  seizes nothing and creates no auction. A later permissionless liquidation
  can retry after backing is restored.
- An auction created while healthy remains active if its asset later becomes
  deficient. Purchases spend zero and roll back through Teller while deficient;
  restored backing makes the same auction fillable again. Switchboard pause is
  available for cancellation but is not required for recovery.

## Shared behavior

- Deposits credit exactly the requested amount only when existing custody
  covers existing nominal liability plus that amount. Pre-existing surplus is
  never silently credited.
- Withdrawals require pre-operation solvency, retain the existing
  `VaultData` reduction path, use typed ERC-20 `transfer`, and require exact
  vault outflow plus exact recipient receipt.
- Recipient policy is not hard-coded in `BasicVault`; authorized callers may
  deliver to any address that satisfies exact ERC-20 receipt accounting.
- Internal movement retains the existing nominal reduction/addition path,
  requires solvency, rejects self-transfer, and never moves custody.
- `getTotalAmountForUser` and `getUserAssetAndAmountAtIndex` return zero usable
  amount during a custody deficit. Nominal position discovery remains nominal.
- Deposit reward bookkeeping currently remains nominal during a custody
  deficit. This preserves the pre-existing Lootbox accounting model; changing
  it is an economic-policy decision because points already accrued before the
  deficit is observed cannot be retroactively removed by a view change. The
  owner decision on whether to stop future accrual during a deficit remains
  open; this candidate does not silently change it.
- Typed `balanceOf` observations and typed `transfer` calls are used directly;
  there are no raw token calls or token-call wrapper helpers in `BasicVault`.
- Vyper's typed ABI decoder accepts trailing return data and reads the first
  word. A 64-byte `balanceOf` response is therefore not rejected solely for its
  length. As with a well-shaped 32-byte lie, governance approval cannot make a
  dishonest or upgraded token's reported balance cryptographically truthful.
- Exact recipient delivery is intentional fail-closed behavior. If an approved
  token later becomes fee-on-transfer, rebasing-on-transfer, or otherwise
  changes delivery semantics, withdrawal reverts atomically until the asset or
  implementation policy is changed.
- Existing authorization, pause, nonreentrancy, bounded over-request, event,
  storage-layout, and atomic rollback behavior remains in the Simple wrapper.

## Artifact identity

The protected `SimpleErc20` candidate compiles with repository Vyper `0.4.3`.
Its shared `BasicVault` input is Git blob
`a5a51ee20c598e9bf40908fc6c38f1c0634bf665`, SHA-256
`6a6abdde4887fb5339125c7268e0258175e3b66c9f060b6ab6e8262f58269ea8`.

| Identity | Candidate value |
| --- | --- |
| Source Git blob | `7525765d45f00aa9ef6b5a98857ce048db0cdc62` |
| Source SHA-256 | `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22` |
| Transitive compiler integrity | `adccab16427994b7a2bb3c5f0742a0b98d174a77713eb304eddfecd4c7681cab` |
| Creation size / SHA-256 | 9,535 bytes / `cafe6aa7cf76416d18e021935d0ab65c7a9e81a8130aab811c000d04b20973ed` |
| Runtime template size / SHA-256 | 9,368 bytes / `750c6a05e9a400a54e25d5f1020d99a3d7ad1ef8372ee86583f79024e60674b6` |
| EIP-170 headroom | 15,208 bytes |
| Canonical ABI SHA-256 | `cf0daef1095087a92ec3d0c327009d8a1d7ec6c3dc04b430debfd4bc25c88b57` |
| Selector count / SHA-256 | 34 / `884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b` |

The public interface and persistent, transient, and immutable layouts remain
the canonical `SimpleErc20` layouts. The runtime changes because the shared
safety behavior is compiled into each future Simple deployment.

AuctionHouse is separately pinned by final compiler output and deployed-code
measurement at 24,556 runtime bytes, leaving 20 bytes of EIP-170 headroom. The
test deploys and measures the exact code; the arithmetic equality is only a
secondary consistency assertion.

## Baseline verification caveat

The feature base `1e36c0c3dd168dbf292456eb5760b02d1f1e4a80` was not a green
test baseline. Its failures included a stale GuardedErc20 artifact identity,
four stale token ABIs missing `getCCIPAdmin`, and two environment-dependent
deployment checks. The
candidate's green-suite result is therefore evidence that the candidate is
internally healthy, not proof of “no regressions versus a green base.” Those
artifact, ABI, and execution-plan repairs are disclosed ride-alongs; the old
GuardedErc20 seal did not describe the GuardedErc20 bytes present in that base.
