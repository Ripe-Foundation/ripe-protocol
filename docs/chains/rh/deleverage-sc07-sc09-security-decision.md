# SC-07/SC-09 Deleverage security decision

**Decision date:** 14 August 2026

**Integration allocation confirmed:** 15 August 2026 as RH-D038 by the
canonical decision-register owner after rechecking the open remediation set

**Status:** owner-authorized bounded remediation implemented in draft PR #145;
independent review, integration, deployment, configuration, activation, and
release remain separate gates

**Authority:** explicit owner instruction for the SC-07/SC-09 task and explicit
follow-up instruction to address every PR review finding

## Decision

The owner reopened the parked Deleverage lane only for the bounded SC-07 and
SC-09 remediation in draft PR #145.

SC-07 requires every capture-interact-settle path to refresh the complete debt
struct and current interest immediately before settlement, revert atomically
when the planned debt amount changed, and settle from the refreshed values when
the amount did not change. The shared Deleverage reentrancy domain covers the
four debt-writing external routes and `swapCollateral`; it is defense in depth
and does not replace the refresh invariant.

SC-09 adopts the existing Stability Pool liquidation-availability boundary:

- optional broad Deleverage and withdrawal-assist preflight classify Stability
  Pool vaults with `MissionControl.isStabVaultId`;
- they probe a cohort with `getUserAssetAndAmountAtIndex` and skip a zero amount;
- a zero caused by a claim-price outage, a paused pool, or aggregate claim
  custody deficit means that cohort is unavailable for optional participation;
- healthy ordinary collateral remains usable and is valued strictly;
- any error after actual cohort processing begins propagates and reverts the
  complete transaction; and
- direct Stability Pool claim, withdrawal, deposit, explicit redemption, and
  explicitly requested strict processing paths remain fail-closed.

This is not a general catch-all for vault errors. Malformed registration,
ordinary-vault price failure, transfer failure, burn or redeem failure, and
accounting failure are not converted into skips.

## Scope retained outside the reopening

RH-D011's zero-cooldown launch posture remains unchanged. This decision does
not authorize a nonzero cooldown, Underscore inclusion, any of the four
zero-valued controls, the provisional H-09 fork path, another Deleverage feature,
or deployment, configuration, activation, or release. All such work remains
parked unless separately reopened.

The only production source authorized by this decision is
`contracts/core/Deleverage.vy`. Test mocks, focused regressions, governed
artifact records, the BasicVault consumer inventory, and this decision/status
record are supporting evidence rather than additional production scope.

## Deployability and chain compatibility

The final candidate compiles to a 24,213-byte runtime template plus 96 bytes of
immutable data: 24,309 deployed bytes, 267 bytes below the EIP-170 limit. It
therefore satisfies the repository's ordinary 200-byte minimum-headroom policy;
no Deleverage override, exact-identity waiver, or residual-risk exception is
used. Any later source, compiler, dependency, constructor, runtime identity, or
size change requires a fresh measurement and must continue to satisfy the
ordinary floor unless a separate owner-authorized waiver is added.

The final artifact identities are source SHA-256
`b035d9bb2ee20a4cab0575c468fe6a06e7e8e5a097f2ec9b00cc841e8bed44b1`,
runtime-template SHA-256
`25f605c232750990f9a0a66a14143a529d4303e79ce02d0a8d8f0c18329094e2`,
and immutable-bound deployed-runtime SHA-256
`2fb68a6f9c9a6b8789c5c7f4ba986b38281002834e9ca7d9fd8c21d4b232df5d`.
They use Vyper `0.4.3+commit.bff19ea2`, the source `codesize` pragma, and the
constructor/immutable values frozen by `capture_contract_runtimes.py` and
`config/contract-artifact-expectations.json`.

The candidate is compatible with the recorded Robinhood MissionControl, where
the Stability Pool classifier is present and populated. Before changing the
Robinhood Deleverage registry pointer, deployment verification must establish
`MissionControl.isStabVaultId(1) == true` against the intended addresses.

The recorded Base MissionControl predates this classifier. This Deleverage must
not replace Base Deleverage unless Base MissionControl is first upgraded to
expose and correctly populate `isStabVaultId`. This record grants no such Base
upgrade authority.

## Public view integration note

`getDeleverageInfo` keeps the same ABI but now reports only collateral currently
available to optional broad deleveraging. An unavailable Stability Pool cohort
is omitted from both the maximum amount and weighted LTV until its price,
pause, or aggregate claim-custody condition recovers. Consumers must not treat
the tuple as an inventory of every nominal user position.

A repository-wide consumer search on 15 August 2026 found no SDK, frontend,
indexer, keeper, or other off-chain caller. The only non-test references are the
contract's internal withdrawal-assist call, the unchanged ABI entry in
`scripts/abis/Deleverage.json`, and ABI/source copies in the immutable Robinhood
migration-history manifest. Any consumer maintained outside this repository
must adopt the availability semantics above before a release using these bytes.

## Evidence and lifecycle boundary

The candidate evidence is maintained in:

- `contracts/core/Deleverage.vy`;
- `tests/core/deleverage/test_deleverage_sc07_reentrancy.py`;
- `tests/core/deleverage/test_deleverage_sc09_stab_availability.py`;
- `tests/core/deleverage/test_deleverage_swap_collateral.py`;
- `docs/chains/rh/hardening/basic-vault-consumer-inventory.md`;
- `config/contract-artifact-expectations.json`; and
- `tests/inventory/test_contract_artifacts.py`.

Local and CI validation qualify repository bytes only. Neither passing tests nor
the owner decision authorizes a registry mutation, deployment, configuration,
activation, or release.
