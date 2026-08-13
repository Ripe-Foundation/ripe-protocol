# BasicVault reward-suppression correction and replacement exact CreditEngine waiver

**Decision:** owner accepted B-AUD-008 on 13 August 2026 and granted a
replacement exact RH-D029 waiver on 13 August 2026 for the combined
B-AUD-008 plus B-OBS-045 / AUD-010 CreditEngine.

**Scope:** exact combined candidate on `codex/rh-third-party-repay-refund`,
rebased onto `f937cbae239913e448c61abfdb0e8f561cdd9ee8`.

**Original review base:** `f9152f27ab8b14ede0ce562974430d57168960b0`

**Original B-AUD-008 PR target base:**
`c3bc780d5b3b59193389c917fd6543312f5ee6c3`

**Replacement composition base:** `f937cbae239913e448c61abfdb0e8f561cdd9ee8`

**Lifecycle authority:** the owner's 13 August 2026 instruction to merge pull
request 115, followed by the express grant of the replacement four-byte waiver,
authorizes the governing-record updates, branch update, and integration of this
exact package into `rh-audit-remediation`. It does not authorize deployment,
configuration, activation, or release.

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

Standard repayments distinguish the debtor from the payer supplying GREEN or
sGREEN. When repayment is capped at the debtor's outstanding debt, the exact
surplus returns to the payer. Self-repayment, auction repayment, department
repayment, permission checks, refund-token selection, event ABI, ordering, and
atomic rollback remain unchanged.

## Exact production-source identities

| Source | SHA-256 |
| --- | --- |
| `contracts/vaults/modules/BasicVault.vy` | `414d4565a07d0b4042c356a6f383d4c5ba968781e6202a262b28a9017c7e38c0` |
| `contracts/core/CreditEngine.vy` | `8c1255de86fe776bb8999dec603d3de43c2c07c0551c2d6eb7fed93f5f17f447` |

## Exact CreditEngine size waiver

The standard 200-byte headroom policy remains unchanged. The owner accepted a
replacement exception for this exact combined CreditEngine version. It
supersedes the prior eight-byte B-AUD-008 identity and is not cumulative:

| Identity | Value |
| --- | --- |
| EIP-170 limit | 24,576 bytes |
| Runtime template | 24,476 bytes |
| Runtime-template SHA-256 | `1d98babadc2a30d2d3bc46bee6aa3f6941f8209aeb0b33c83c91201ebf1fcdc2` |
| Deployed runtime, including 96 immutable bytes | 24,572 bytes |
| Remaining headroom | **4 bytes** |
| Complete deployed-runtime SHA-256 at deterministic HQ `0x00000000000000000000000000000000000000A1` | `22d73db8db9ca7bc877cedf189f135d6a4ebfac3cf3e522424a9be130049524f` |

The deterministic HQ is a reproducibility input, not a production address. The
waiver permits zero growth. Any source, compiler-output, runtime-template,
deployed-size, constructor-bound deployed-code, or relevant toolchain change
invalidates this identity and requires either restoration of at least 200 bytes
of headroom or another express owner decision.

## Governed artifact refresh

The combined candidate was captured from its clean rebased source using the
repository's deterministic 18-contract Boa deployment graph. The targeted
artifact updater regenerated the CreditEngine record from that captured runtime;
the combined governed-ledger diff changes only the CreditEngine record. The
ledger's captured CreditEngine deployed hash uses its declared
production-capture HQ; the waiver hash above uses the separate deterministic
`0x…00A1` HQ required by the exact-waiver test.

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
bounded-gas zero-amount path. The combined gate also covers payer-directed
GREEN/sGREEN refunds, maximum-payment handling, interest, permissions, complete
refund-failure rollback, real-auction behavior, and department repayment. Exact
command results are recorded in the task handoff; this record does not convert
local test evidence into deployment or release authority.
