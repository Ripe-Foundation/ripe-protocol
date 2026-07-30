# Robinhood deployment: cold-agent handoff

**Frozen protocol/pause subject:**
`ae0cb49bad9ad615deb11cbca5d3a2c20e38bb4c`
**Subject tree:** `a6a34a385b48819bbf66249d518d76da3806b033`
**Current machine authority:** [`status.yaml`](status.yaml)
**Private presentation mirror:** [Robinhood program status](https://ripe-robinhood-status.mickhagen.chatgpt.site)

Ready to begin deployment preparation. PR #61 is merged and closed on `master`,
and its production contract changes are integrated into `rh`. Nothing has been
deployed, migrated, configured in production, activated, or released on
Robinhood.

## Mandatory bootstrap

1. Start read-only. Verify local `rh`, cached `origin/rh`, and credential-free
   live `rh` before creating a worktree or editing.
2. Read [`status.yaml`](status.yaml), [`START-HERE.md`](START-HERE.md),
   [`deployment-owner-readiness.md`](deployment-owner-readiness.md),
   [`current-owner-priorities.md`](current-owner-priorities.md), and the exact
   assigned brief/evidence only.
3. Treat historical commit, tree, test, machine, and fingerprint rows as
   evidence of their recorded checkpoint—not current facts—unless reverified.
4. Keep the frozen protocol baseline, documentation authority, signed feature
   publication, `rh` integration, later descendants, planning, deployment,
   configuration, activation, and release as distinct lifecycle states.
5. Never repair, clean, reset, restore, or overwrite unexpected state. Stop and
   report drift outside the authorized scope.

## Current counts

- 28 workstreams and 19 RH-D decisions.
- All 18 H-03 blockers remain open.
- H-04 has 21 lifecycle rows: 20 approved operative, one retired
  non-operative (`D-H04-19`), zero open, plus 14 binding schedules.
- Nine hard gates and ten dashboard handoff documents.
- Four parked lanes and zero live actions.

## Current lifecycle facts

- H-04 schema v2 is integrated. Required identities, `TrainingWheels`, and
  `liteSigners` remain unresolved, so `DefaultsRobinhood.vy` remains absent and
  fail-closed.
- H-05 deterministic reports are integrated predeployment planning. No
  Robinhood migration history exists; do not execute migrations.
- H-06 qualifies a candidate macOS/APFS operator/storage class only. Final
  operator, machine, volume, publication, deployment, and release authority
  remain open.
- M4 composed-route proof is integrated. M5 configuration/freeze, H-07-H-11,
  SecOps, rehearsal, and release preparation remain.
- The historical S4 zero-cooldown decision remains closed.
- CCIP and zero-backing settlement/bad-debt policy are deferred and
  nonblocking.
- Sites account/workspace recovery and dashboard deployment are parked and
  nonblocking.

## Four-control gap

`fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps` remain zero
and deferred. They lack Robinhood machine-facing parameter/planning
representation. Record this as a blocker for a separately authorized machine
implementation track. The deployment owner owns its final disposition and
binding, but must preserve zero values until separate approval.

## Deployment-owner start

The coworker owns the ten-step preparation sequence in
[`deployment-owner-readiness.md`](deployment-owner-readiness.md), from final
input and authority binding through deterministic artifacts, H-06 binding,
rehearsal, SecOps, and the restricted-release packet. Smart-contract
reassessment and Robinhood fork/external-integration qualification may proceed
in parallel; they do not block preparation from starting, but relevant findings
must be consumed before affected gates close.

## Current checked identities

- Block-clock counts: 99 occurrences, 94 lines, 17 files.
- Historical S5 fingerprint:
  `924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4`.
- Current post-S5 fingerprint:
  `07fc837ee5c9c56a4cf979c64e3d678753eeb6c263e4100d7a1f0cb4704f2122`.
- Direct artifact set: AuctionHouse, CreditEngine, Deleverage, GuardedErc20,
  Ledger, Lootbox, SwitchboardDelta, and Teller.
- Deleverage deployed runtime: 24,569 bytes; seven bytes EIP-170 headroom.

## Prohibited inference

Do not infer any address, role, signer, feed, cap, rate, cadence, allocation,
artifact, runtime, parameter, plan row, account, RPC endpoint, activation
value, or release authority. Do not substitute Base values or placeholders.
H-05 plan construction is not execution; H-06 class qualification is not final
operator binding; ready to begin deployment preparation is not ready to deploy
or authorization to deploy.

## Stop conditions

Stop before mutation if:

- local, cached, and live authority do not match the assignment;
- a supplied patch, manifest, mode, byte, count, or fingerprint seal drifts;
- the needed path is outside the explicit file ceiling;
- an unexpected tracked, untracked, ignored, or unmerged path overlaps the
  assignment;
- a historical-evidence rewrite would be required;
- a dependency, contract, ABI, interface, configuration, defaults, migration,
  manifest, deployment, activation, release, RPC, account, or signer change is
  needed; or
- the four-control machine gap would need implementation without separate
  authority.

## Handoff contract

Final reports must name the exact base/ref identities, documentation
publication lifecycle, changed paths, generated ignored outputs, validation
results, historical-preservation proof, current counts/hashes/fingerprints,
machine-facing gap, Sites visibility, residual risks, and the independent
review boundary. No Sites action belongs in this handoff.
