# BasicVault reward-suppression correction and exact CreditEngine waiver

**Decision:** owner accepted on 13 August 2026

**Scope:** exact local B-AUD-008 candidate on
`codex/rh-basic-vault-reward-suppression`

**Original review base:** `f9152f27ab8b14ede0ce562974430d57168960b0`

**PR target base:** `c3bc780d5b3b59193389c917fd6543312f5ee6c3`

**Lifecycle authority:** the owner's 13 August 2026 PR instruction authorizes
commit, branch push, and PR publication for this exact package. It does not
authorize integration, deployment, configuration, activation, or release.

## Accepted behavior

When a BasicVault's actual token custody is below its nominal total balances,
`getUserLootBoxShare` returns zero for every affected user without mutating the
nominal user or vault ledger. Restoring custody automatically restores the
current reward share. Configured reward allocations and points already recorded
in Lootbox are not rewritten.

CreditEngine does not use the suppressed reward getter as a position oracle.
For a zero usable amount, it requires both a vault-wide zero usable amount and a
nominal position reported by `doesUserHaveBalance` before marking the account as
having quarantined collateral. This preserves quarantine behavior while keeping
reward accounting separate from collateral and forced-action eligibility.

## Exact production-source identities

| Source | SHA-256 |
| --- | --- |
| `contracts/vaults/modules/BasicVault.vy` | `414d4565a07d0b4042c356a6f383d4c5ba968781e6202a262b28a9017c7e38c0` |
| `contracts/core/CreditEngine.vy` | `cc1ecad3b798bef4fd9788f1885e32736beea833fe9672c7840f555d89ad13e4` |

## Exact CreditEngine size waiver

The standard 200-byte headroom policy remains unchanged. The owner accepted an
exception for this exact CreditEngine version:

| Identity | Value |
| --- | --- |
| EIP-170 limit | 24,576 bytes |
| Runtime template | 24,472 bytes |
| Runtime-template SHA-256 | `9acae4cc64812f5fbe6039d7d83bc341b5d0b1a0ee31b999616f2d9724254ecf` |
| Deployed runtime, including 96 immutable bytes | 24,568 bytes |
| Remaining headroom | **8 bytes** |
| Complete deployed-runtime SHA-256 at deterministic HQ `0x00000000000000000000000000000000000000A1` | `d8a4631991ee69c5a8e8dd08619e41c1099a2e20cbe32b659c35e92cb7d0b06b` |

The deterministic HQ is a reproducibility input, not a production address. The
waiver permits zero growth. Any source, compiler-output, runtime-template,
deployed-size, constructor-bound deployed-code, or relevant toolchain change
invalidates this identity and requires either restoration of at least 200 bytes
of headroom or another express owner decision.

## Governed artifact refresh

The strict artifact updater ran from a disposable clean source freeze containing
only the two production-source changes above and an authenticated capture of all
18 required deployed runtimes. The governed ledger changed only the CreditEngine
record and the transitive SimpleErc20 record. The ledger's captured CreditEngine
deployed hash uses its declared production-capture HQ; the waiver hash above uses
the separate deterministic `0x…00A1` HQ required by the exact-waiver test.

The controlling machine records are:

- `config/contract-artifact-expectations.json`;
- `tests/inventory/test_contract_artifacts.py`; and
- `tests/test_vault_pointer_runtime_sizes.py`.

## Validation boundary

The focused package covers current reward-share suppression and recovery,
nominal-state preservation, zero-LTV reward-only shortfall behavior, normalized
share checkpointing, configured-allocation preservation, quarantine detection
and recovery, borrow/withdraw/liquidation/redemption/deleverage containment,
healthy-asset continuity, rounding dust, backing-observation failures, and the
bounded-gas zero-amount path. Exact command results are recorded in the task
handoff; this record does not convert local test evidence into deployment or
release authority.
