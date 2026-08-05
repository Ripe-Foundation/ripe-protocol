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
  amount during a custody deficit. Nominal position discovery and reward
  bookkeeping remain nominal by design.
- Typed `balanceOf` observations and typed `transfer` calls are used directly;
  there are no raw token calls or token-call wrapper helpers in `BasicVault`.
- Existing authorization, pause, nonreentrancy, bounded over-request, event,
  storage-layout, and atomic rollback behavior remains in the Simple wrapper.

## Artifact identity

The protected `SimpleErc20` candidate compiles with repository Vyper `0.4.3`.
Its shared `BasicVault` input is Git blob
`9c8299accd5a65cbfbc96c4cdc1849bb125523b8`, SHA-256
`0b13c91ef72cfc139de1d4c036e01e3d371349ba549b144d1aa0ff47cc855044`.

| Identity | Candidate value |
| --- | --- |
| Source Git blob | `7525765d45f00aa9ef6b5a98857ce048db0cdc62` |
| Source SHA-256 | `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22` |
| Transitive compiler integrity | `a90380f263697bf286ef4ab9076caf8554e38c4bcf0cef90e30dc8a9461a16ed` |
| Creation size / SHA-256 | 9,557 bytes / `d6cca5f074b5395f7f1dbde6e42639cfc9b89a84068c4bb577f92d36e345f0ac` |
| Runtime template size / SHA-256 | 9,390 bytes / `3e21a9c930c878bb84883f66fab1f3cff0a9abf173034d927d3d660b020f0da1` |
| EIP-170 headroom | 15,186 bytes |
| Canonical ABI SHA-256 | `cf0daef1095087a92ec3d0c327009d8a1d7ec6c3dc04b430debfd4bc25c88b57` |
| Selector count / SHA-256 | 34 / `884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b` |

The public interface and persistent, transient, and immutable layouts remain
the canonical `SimpleErc20` layouts. The runtime changes because the shared
safety behavior is compiled into each future Simple deployment.
