# Robinhood Curve launch migration handoff

**Audience:** separate migration-source workstream

**Authority:** interface and ordering handoff only

**Candidate baseline:** commit `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree `7454b5456ebb6cd02d716a64b408629ab501629e`

**Execution authority:** none

Do not edit or execute `migrations/robinhood/**` from this Curve authority
workstream. The stopped migration-source worktree
`/private/tmp/rh-shared-migration-source.5FxyDn` is bound to the pre-Curve
baseline and must not be modified or treated as current.

## Exact rebind rule

After this authority package is integrated into `rh`, the migration owner must:

1. obtain the exact integrated `origin/rh` commit and tree from the owner;
2. verify local `rh`, cached `origin/rh`, and credential-free live `origin/rh`
   all resolve to that commit/tree;
3. verify the integrated tree contains the reviewed Curve authority patch and
   unchanged `contracts/priceSources/CurvePrices.vy` hash
   `f6e8234be8e433ed344f6f61d9cf04d20a4327c773759bb6aced44b9f65ebd0c`;
4. create a new isolated mode-0700 worktree from that exact integrated commit,
   or rebind the stopped worktree only under explicit owner authority; and
5. regenerate the deterministic plan from `config/BluePrint.py`. Do not
   cherry-pick or infer values from this document.

The LP candidate branch `codex/rh-lp-launch-admission` at commit
`75c870e9d9f336ad074b9ae35bad5081fd25a8db` (tree
`5be037da60f910c58347982348c69d8bd5088f2d`) adds
`docs/chains/rh/qualification/lp-launch-admission.md` and modifies the status,
synthesis, decision register, quick-start, dashboard README, and handoff-doc
tests. It is not integrated into this baseline and must rebind to the new
GREEN-only Curve disposition without admitting either LP or making either LP
an oracle. Do not modify that worktree from this handoff.

## Required executable order

Each step is plan-only until an exact later authorization separately permits
execution.

1. Bind the verified official Curve AddressProvider, registries, and factory
   infrastructure from the approved Blueprint identities; do not deploy a
   replacement Curve factory stack.
2. Deploy `CurvePrices` with the exact Blueprint constructor bindings.
3. Create the GREEN/USDG StableSwapNG pool using only owner-approved values.
4. Record the factory return and verify the deployment-produced pool address,
   runtime, registry handler, factory, and provenance.
5. Bind approved custody, funding, slippage, minimum-mint, withdrawal, and
   retained-liquidity controls before transferring or approving assets.
6. Register `ChainlinkPrices` first and assert returned PriceDesk ID 1.
7. Register `CurvePrices` second and assert returned PriceDesk ID 2.
8. Configure and confirm only the GREEN Curve feed for the verified pool.
9. Prove USDG has a live Chainlink feed and no Curve feed.
10. Prove Curve dynamic rates, GREEN reference snapshots, Endaoment
    stabilization, Curve LP pricing, LP admission, and PSM Curve authority are
    all inactive.
11. Register `BlueChipYieldPrices` third and assert returned PriceDesk ID 3.
12. Apply and read back priority IDs exactly `[1, 3]`.
13. Run H-08 source/artifact/constructor/registry/topology/omission and
    inactive-capability assertions.
14. Run H-09 archive-fork qualification only after the endpoint, immutable
    block pin, identity manifest, and exact external inputs receive separate
    authorization.
15. Stop before deployment execution unless a later instruction names the
    exact plan, profile, accounts/signers, provider, allowed actions, evidence,
    and stop rules.

There is no legal sparse-slot, zero-address, dummy, unrelated-placeholder, or
registration-reordering substitute for steps 6, 7, and 11.

## Abort criteria

Abort before the next mutation if any of the following occurs:

- baseline, source, compiler, ABI, creation/runtime bytecode, constructor, or
  plan hash differs from the reviewed packet;
- chain ID is not 4663 or an external Curve identity/runtime is unverified;
- AddressProvider IDs 7, 11, 12, or 13 differ from the approved packet;
- the pool factory/handler, CREATE provenance, returned address, coin order,
  token decimals, A, fee, off-peg multiplier, or `ma_exp_time` differs;
- any pool name, symbol, funding, custody, approving account, minimum mint,
  slippage, withdrawal, retained liquidity, or observation blocker is open;
- any registry confirmation returns an ID other than 1, 2, or 3 in the exact
  expected order;
- Curve has or is pending a USDG feed, any LP feed, or any feed other than
  GREEN;
- Chainlink USDG is missing, zero, stale, reverting, or identity-drifted;
- priorities differ from `[1, 3]`;
- reference-pool, dynamic-rate, stabilizer, PSM Curve, LP, Stock, or Uniswap
  capability is nonzero, reachable, or pending;
- a safe/unsafe GREEN failure produces a nonzero fallback value; or
- a required action would use an unapproved RPC, account, key, signer, token
  transfer, pool funding, deployment, registration, or external mutation.

## Rollback truth

- Before PriceDesk registration, abort leaves no Ripe pricing authority. Any
  deployed but unregistered contract or pool is an external artifact requiring
  a separate custody/unwind decision.
- After ID 2 registration, pausing Curve does not stop ordinary price reads.
  The authority rollback is the governed PriceDesk ID 2 disable.
- After ID 2 disable, confirm GREEN returns zero with no approved fallback and
  USDG remains Chainlink-priced. Do not place BlueChipYield, zero, or another
  contract into ID 2.
- AddressRegistry preserves the sequential ID; recovery uses a governed update
  of ID 2 to the reverified Curve contract, followed by the complete
  post-recovery checks. It does not append a new source to regain ID 2.
- If GREEN feed configuration itself is wrong but the Curve contract is sound,
  keep ID 2 disabled while the governed Curve feed update/disable is resolved.
- Pool liquidity, approvals, custody, and withdrawal are not rolled back by an
  oracle registry change. Their unwind requires the separately approved
  liquidity/custody runbook.
- No rollback step grants migration execution, role transfer, activation, or
  release authority.
