# Yield-price snapshot remediation evidence and operating boundary

**Candidate:** PR #142, `codex/rh-sc-05-17-23` into
`rh-audit-remediation`

**Scope:** SC-05 snapshot-ring reset safety, SC-17 observation-interval TWAP,
and SC-23 age-bounded fallback behavior in `BlueChipYieldPrices` and
`UndyVaultPrices`.

**Lifecycle boundary:** this record binds candidate behavior and review
evidence. It does not authorize deployment, feed registration, activation, or
release.

## RH-D033 owner decision: BlueChip compiler profile

On 14 August 2026, after the gas-versus-size comparison was independently
reproduced, the owner approved compiling the BlueChip SC-05/SC-17/SC-23
candidate with Vyper's `codesize` optimizer. This is a compiler-profile
decision, not an EIP-170 headroom waiver: the deployed candidate retains 1,837
bytes, above the repository's ordinary 200-byte floor.

| Measurement | `codesize` | `gas` | Difference |
| --- | ---: | ---: | ---: |
| Runtime template | 22,259 | 23,335 | `codesize` saves 1,076 bytes |
| Deployed headroom | 1,837 | 761 | `codesize` adds 1,076 bytes |
| Full 25-entry traversal plus nested PriceDesk lookup | 59,759 | 59,504 | +255 gas |
| Fresh-fallback path | 39,303 | 39,048 | +255 gas |
| Capacity-changing confirmation | 130,353 | 130,098 | +255 gas |

The accepted trade is a constant 255-gas increase on the three measured
top-level paths in exchange for materially safer code-size margin and continued
compliance with the existing runtime ceiling and headroom guardrails. A later
optimizer change, a material change to this trade, or a fall below the normal
headroom floor reopens RH-D033.

The current source-only clarification changes source, Git-blob, compiler-input,
and creation-artifact identities while leaving runtime bytes unchanged:

| Identity | Current candidate value |
| --- | --- |
| Source SHA-256 | `f73a608e2f61a97dc57526011c82840b79e4228d3925375abe6d46e8931c57b0` |
| Source Git blob | `ecf043a614838802c50b24187fa0556ee6466fea` |
| Compiler-input integrity | `00fbbc1aaba3103468d83b29f41fd258a9751e7c7c0213f16fc3149d318d3775` |
| Creation bytes / SHA-256 | 23,871 / `b38f0668830875bb42fd93df3a56395e93ede1ff7e3545dfb42b33d2a021529e` |
| Runtime template bytes / SHA-256 | 22,259 / `afd1c6c61a2da3f5a172f24917e1bc10377270924edc1c1aa7dc4cc4b585d74b` |
| Deployed runtime bytes / SHA-256 | 22,739 / `649c0c2c7303e8fcb2bb5d86764a00bae5f62cdb1251b1018cde862ba00761a4` |
| EIP-170 headroom | 1,837 bytes |

Relative to the exact `rh-audit-remediation` parent, deployed runtime grows by
35 bytes (22,704 to 22,739). Under a constant `gas` profile, the candidate
would instead deploy at 23,815 bytes and retain 761 bytes of headroom.

## Confirmation semantics

Confirmation distinguishes structural invalidity from a transient seed read:

- A structural or interface revalidation failure cancels the pending action
  and returns `False`, preserving the pre-existing cancellation policy.
- A snapshot-based new feed or capacity change must obtain a valid nonzero
  seed. A transient invalid seed reverts atomically; the live configuration,
  ring, pending proposal, and timelock remain available for retry or explicit
  cancellation.
- An unchanged-capacity update does not take a confirmation snapshot. It
  preserves the live ring, cursor, `lastSnapshot`, and throttle anchor exactly,
  including observations added while the proposal was pending.
- Aave V3 and Compound V3 remain snapshotless. New registration and capacity
  changes clear all 25 residual slots, leave `lastSnapshot` empty and
  `nextIndex` zero, and do not install a seed.

## Delay and freshness configuration

The adapters intentionally permit `0 < staleTime < minSnapshotDelay`. The
resulting interval is fail-closed: this source returns zero after the inclusive
freshness deadline and before the next snapshot is eligible; PriceDesk may use
a later healthy source or leave the asset unpriced.

The pre-expiry-refresh predicate is
`staleTime == 0 or minSnapshotDelay <= staleTime`. For a finite freshness
window, it guarantees that a replacement is eligible no later than the last
timestamp at which the old observation remains fresh. Equality is safe because
the old observation is fresh and a replacement is eligible at the same
timestamp. Focused tests pin equality, a true stale-and-replacement-ineligible
timestamp when `staleTime=8` and `minSnapshotDelay=10`, eligibility one second
later, and the intentional no-expiration behavior when `staleTime == 0`.

## Zero-supply bootstrap invariant

A fresh zero-supply ERC-4626 snapshot may supply a bootstrap PPS through
`lastSnapshot`, even though zero-supply observations are excluded from the ring
TWAP. This is the pre-existing empty-vault policy retained by SC-17. It remains
bounded by SC-23 freshness and by the normal live-PPS minimum composition, so
it cannot bypass the current-vault PPS clamp. Transition tests use two distinct
nonzero-supply PPS observations and independently derive an interval-weighted
output different from the latest fallback, proving that the supply-ineligible
bootstrap is excluded and the nonzero-supply ring takes over.

## RH-D034 owner decision: conditional acceptance of SC-17 timing residual

On 14 August 2026, after reviewing the executable timing analysis and the
attacker prerequisites, the owner accepted retaining SC-17's
observation-interval TWAP in this candidate. The acceptance is conditional on
feed-level operating controls; it is not a claim that duration weighting makes
snapshot timing intrinsically safe.

Before any snapshot-backed feed is activated, the activation package must:

1. configure a finite, nonzero `staleTime`;
2. prove `minSnapshotDelay <= staleTime`;
3. qualify the selected vault's PPS against temporary downward manipulation,
   and withhold activation if a value-increasing depression is practical;
4. bind a monitored honest-refresh SLA shorter than the freshness window;
5. bind alerts for abnormal PPS changes and missed refreshes plus tested
   pause/disable incident procedures; and
6. keep Undy disabled until a separate activation package binds its exact
   artifact, configuration, refresh operation, and protocol-specific risk.

No exact parameter values, vault, deployment, registration, activation, or
release are approved by RH-D034. A feed that cannot satisfy every applicable
condition must leave SC-17 inactive for that feed and pursue a separately
reviewed sampling or lower-bound design.

### Accepted residual behavior

Duration weighting removes total-supply inflation as an influence multiplier,
but snapshot timing remains a control surface. Ordinary allowed Teller deposits
and withdrawals attempt a snapshot after normal Teller validation. Once
`minSnapshotDelay` has elapsed, a user can therefore time an eligible attempt
while PPS is temporarily depressed, restore PPS, and let that observation gain
duration weight.

Direct evidence covers BlueChip Morpho, Euler, and Fluid through their shared
ERC-4626 path; Moonwell's separate live-rate minimum path has a dedicated
duration/clamp regression; Morpho V2 shares the checked ERC-4626 composition
after its defensive reads. Undy has the same Teller/PriceDesk production-path
test and its own upward/downward timing analysis. Aave V3 and Compound V3 are
not affected because they do not use snapshots.

The upward case is capped by the final live-PPS minimum where applicable. A
depressed observation is liquidation-relevant and may be value-increasing for
an attacker. An honest later snapshot dilutes it only after another eligible
sampling event; absent refresh, it remains eligible through
`lastUpdate + staleTime` inclusively. The maximum freshness-bounded exposure is
therefore the configured nonzero `staleTime`; `staleTime == 0` has no expiry and
is unbounded. `minSnapshotDelay` sets the earliest honest refresh cadence, not
an automatic refresh.

RH-D034 accepts this residual for the source candidate subject to the activation
conditions above. It does not permit those conditions to be replaced by a
claim that the final live-PPS minimum protects the downward case. A symmetric
downside clamp is not assumed safe because it could conceal a genuine vault
loss.

## Arithmetic and artifact scope

BlueChip retains its broad checked/fail-soft helpers. For Undy, this candidate's
new guarantee is narrower: duration calculation, numerator/denominator
accumulation, and fallback freshness arithmetic fail soft. This record does not
claim that every pre-existing Undy conversion, delay, throttle, or final-price
operation is contract-wide fail-soft. A broader conversion is a prerequisite
assessment for any future Undy activation.

The exact Undy size and hash reported by the focused fixture are informational
measurements, not a governed deployment identity. No Undy artifact-expectation
entry is added. Any future activation must bind exact source, compiler,
constructor inputs, runtime, and operating configuration.

The Morpho V2 validation multiplications are intentional representability
probes for later supply/PPS and underlying-price/PPS composition. Their products
are discarded because only fail-closed compatibility is needed during
validation; the production source now states that invariant directly.

## Gas budgets and SC-06 handoff

The explicit gas-marked test enforces ceilings of 75,000 for the full traversal,
50,000 for the fresh fallback, and 165,000 for capacity-changing confirmation.
These provide approximately 25% margin over the reproduced measurements and
must run in an explicit CI lane because `pytest.ini` excludes `gas` by default.

The 59,759 figure is a top-level call that includes nested PriceDesk work. It is
not a PriceDesk `raw_call` stipend. SC-06 must measure the actual
PriceDesk-to-BlueChip source frame in the worst supported ring state, account
for nested lookup and caller overhead, add a documented margin, and apply the
EIP-150 63/64 forwarding rule before selecting a stipend.

## Integration handoffs

- Before promotion onto `rh`, regenerate
  `docs/chains/rh/smart-contract-changes/blue-chip-yield-prices.md` against the
  final `rh` commit and tree, source blob and SHA-256, optimizer, creation and
  runtime identities, deployed runtime, and EIP-170 headroom.
- PR #142 has no CI checks because the workflow currently targets only `rh`.
  The owner must either land the recommended branch-trigger prerequisite and
  require final-head green checks, or record an explicit CI exception and a
  named closure point.
- The pre-existing Deleverage 23,241-versus-23,261 size assertion is unrelated
  to this remediation and is tracked separately in GitHub issue #148; PR #142
  must not change that contract or test.
