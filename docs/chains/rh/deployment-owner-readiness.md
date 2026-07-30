# Robinhood deployment-owner readiness handoff

**Readiness:** Ready to begin deployment preparation.

**Frozen protocol/pause baseline:** commit
`ae0cb49bad9ad615deb11cbca5d3a2c20e38bb4c`, tree
`a6a34a385b48819bbf66249d518d76da3806b033`, signed tag
`rh-pause-2026-07-30`

**Current machine authority:** [`status.yaml`](status.yaml)

This is a preparation handoff, not deployment authority. The documentation-only
commit containing this file is a descendant of the frozen baseline. Its exact
authority commit is derived by the dashboard generator after commit; it is not
hardcoded here. Publication of that feature commit will not integrate it into
`rh`. A later independent review controls integration, and any later `rh`
descendant must be reconciled before it is treated as current.

No Robinhood deployment or migration has occurred. No production configuration
or activation has occurred. No RPC, account, key, or signer action has occurred.
No Sites project, version, deployment, or access state is changed by this
handoff.

## Upstream and integration relationship

PR #61 is merged and closed. Its final head is
`7293cf87c3c5afb06c3aeac90ffb0cd0cd27e253`, and its squash merge on `master`
is `91eda49ccd34a25090582aff0695075c4c806011`.

The corrected PR was imported into `rh` at the historical integration ancestor
`ad831669943ccfe7b9ed57454995dfce51630a66`, tree
`3467f4a75aa37203d615407d5baf9c5fc9035639`. That ancestor is not the present
branch authority. The frozen protocol/pause baseline is `ae0cb49…`.

At current `master` and the frozen `rh` baseline, these production paths are
blob-identical:

- `contracts/core/Deleverage.vy` — blob
  `b43d373039b352d6eab240be714134764901b947`;
- `contracts/core/AuctionHouse.vy` — blob
  `48cbbbca22c87e490ef0f88aae4f643ab5b87987`; and
- `contracts/config/SwitchboardDelta.vy` — blob
  `4e234df7626eb332836aceb5cbca2daaef2a0390`.

The upstream change touched five Base-only migration and history paths. They
are intentionally outside the Robinhood parity requirement:

1. `migration_history/base-mainnet/v1/2026072800-manifest.json`
2. `migration_history/base-mainnet/v1/2026072801-manifest.json`
3. `migration_history/base-mainnet/v1/current-manifest.json`
4. `migrations/base-mainnet/2026072800_DeleverageAuctionHouse.py`
5. `migrations/base-mainnet/2026072801_RedeploySBDeltaForDeleverage.py`

At current `master` and the frozen `rh` baseline, four of those paths differ:
the three history paths and
`migrations/base-mainnet/2026072800_DeleverageAuctionHouse.py`.
`migrations/base-mainnet/2026072801_RedeploySBDeltaForDeleverage.py` is
byte-identical. The fifth differing path among the squash merge's 23 touched
paths is `tests/conf_core.py`, reflecting independent `rh` branch evolution,
not a production-contract delta.

All five migration/history paths remain Base provenance. Their presence,
absence, bytes, or tree relationship does not create Robinhood migration
authority. Do not merge `master` into `rh` or import Base migration history
merely for parity. Robinhood planning and any future history remain isolated
and require their own approved identities.

## What the deployment owner owns

The coworker owns the complete deployment-preparation lane in this order:

1. **Bind final chain and protocol inputs.** Freeze the Robinhood chain, token,
   asset, pool, contract-address, and approved parameter bindings. Keep every
   unresolved value explicit; do not invent or substitute it.
2. **Bind authorities and operators.** Freeze governance, signer, role,
   `TrainingWheels`, lite-signer, emergency, and operator assignments. This is
   an authority map and ceremony input, not permission to access a key, account,
   signer, RPC endpoint, or live role.
3. **Dispose and represent the dormant Deleverage controls.** Own the final
   disposition and separately approved machine representation of
   `fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps`. Preserve
   all four at zero and deferred unless a separate approval changes them.
4. **Generate final `DefaultsRobinhood`.** Generate it deterministically only
   after every required approved identity and parameter exists.
   `DefaultsRobinhood.vy` remains absent and fail-closed until then.
5. **Finalize deterministic migration and release planning.** Produce exact
   executable plans, assertions, stops, and isolated history interfaces while
   preserving the no-execution boundary. H-05 is deterministic predeployment
   planning, not migration execution.
6. **Bind H-06 to the intended environment.** Qualify the final operator,
   machine, and selected volume against the frozen release candidate. Existing
   H-06 evidence qualifies a macOS/APFS class only.
7. **Freeze deployment artifacts and offline verification.** Bind exact
   bytecode, constructor inputs, ABIs, verifier adapters, manifests, and offline
   proof interfaces without submitting a live verification.
8. **Rehearse on testnet and capture evidence.** Rehearse the exact plan,
   failure stops, assertions, rollback truth, and evidence capture only after a
   separate exact testnet authorization.
9. **Complete security-operations readiness.** Freeze monitoring, escalation,
   pause, emergency, incident, kill, and accountable-operator procedures.
10. **Assemble the production release packet.** Own rollback and abort
    criteria, the signer ceremony, final review inputs, and eventual deployment
    execution. Production execution remains subject to separate exact
    authorization.

The owner must keep unresolved identity, authority, security, rehearsal, and
release gates visible. A complete document row is not a substitute for its
missing machine input or evidence.

## Parallel inputs

Two waves may continue in parallel and do not prevent deployment preparation
from starting:

- smart-contract reassessment; and
- Robinhood fork and external-integration qualification.

The deployment owner must consume relevant findings before an affected
artifact, configuration, rehearsal, external-integration, or release gate
closes. “Nonblocking to start” does not mean “irrelevant to finish.”

## Parked and nonblocking

Keep these lanes parked:

- CCIP;
- zero-backing settlement and bad-debt policy;
- Sites account/workspace recovery; and
- dashboard deployment or access changes.

Do not reopen or implement them through deployment preparation. The first two
retain their historical technical evidence. The Sites lanes retain the exact
known project provenance without attempting recovery, replacement, version
creation, deployment, or access changes.

## Truths that remain controlling

- No Robinhood deployment has occurred.
- No Robinhood migration has been executed.
- No production configuration or activation has occurred.
- No RPC, account, key, or signer action has occurred.
- PR #61's production contract changes are integrated into `rh`.
- The four Deleverage payoff/dust controls remain zero and deferred.
- The historical `deleverageCooldown == 0` decision remains closed and is not
  reopened.
- H-05 remains deterministic predeployment planning, not execution.
- H-06 still requires final operator, machine, and volume binding.
- `DefaultsRobinhood.vy` remains absent and fail-closed until all approved
  inputs exist.
- Ready to begin deployment preparation does not mean ready to deploy,
  authorized to deploy, deployed, activated, or configured in production.

## Next handoff

Begin with a read-only binding register against the frozen protocol/pause
baseline and the ten ownership steps above. Use
[`robinhood-deployment-support-specification.md`](robinhood-deployment-support-specification.md),
[`robinhood-deployment-validation-plan.md`](robinhood-deployment-validation-plan.md),
[`robinhood-manifest-operator-runbook.md`](robinhood-manifest-operator-runbook.md),
and
[`hardening/release-packet-evidence-checklist.md`](hardening/release-packet-evidence-checklist.md)
as detailed implementation and evidence interfaces. Any production-contract,
configuration, migration, RPC, signer, testnet, production, or Sites action
requires its own controlling authority.
