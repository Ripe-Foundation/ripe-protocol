# Removed paths

Single index of everything the codebase-simplification branch removed from the
active tree, so a grep for a path that no longer exists lands somewhere useful.

Nothing here was ever deployed, and no production contract was modified. Every
file remains in git history and is recoverable with `git show <commit>:<path>`.
Archived copies are also kept outside the repo at
`~/dev/ripe-protocol-review-archives/rh-machete-chop/`.

## Deployment manifests: what is kept and why

Step manifests are removed on an ongoing basis as rh produces them. Only the
`current-manifest.json` of each chain/version is read at runtime, by
`prepare_defaults.py`, `verify_blockscout.py`, `ccip_send.py`, and `console.py`.

**Mainnet `current-manifest.json` files are retained. Testnet manifests are
removed entirely** — `base-sepolia` v1/v2 and `robinhood-testnet` v1/v2, step
manifests and current manifests alike. Those chains are disposable; if one is
needed again it is redeployed, which regenerates its manifest. Two manifests
remain in the tree, `base-mainnet/v1` and `robinhood-mainnet/v1`.

### Why removing step manifests does not break a deployment

The migration machinery never reads a *previous* step's numbered manifest.
`Migration.__init__` loads prior state from `current-manifest.json`
(`scripts/utils/migration.py:31`), which is the cumulative merge of every step.
The `previous_timestamp` argument is assigned to `self._previous_timestamp` and
never read anywhere else. The only numbered read is a step loading its *own*
file in `_append_manifest` (`migration.py:281`), and it is wrapped in a
`try/except` that falls back to `{}` and rebuilds.

What is genuinely lost is per-step attribution: `current-manifest.json` gives
the final address, ABI, and constructor arguments for each contract, but not
which step deployed it, and not each generation of a redeployed contract. That
history is intact in git — `git show <commit>:<path>` — and in the archives.

### Caveat for whoever repairs the resume path

`MigrationRunner._latest_manifest_timestamp()` derives the deployment resume
point by scanning the history directory for `*-manifest.json` and taking the
highest integer prefix. **It is already broken and was before this branch:** it
calls `int(timestamp)` on every match, and `current-manifest.json` yields
`int('current')`, a `ValueError`, whenever a numbered manifest and a current
manifest coexist — which was always the case. Operators must pass an explicit
start timestamp today.

Removing the numbered manifests does not change that: the function now returns
the string `'current'`, which raises at `int(start_timestamp)` in
`_filtered_migration_filenames` instead. Behaviour is unchanged, but the failure
moves.

If that resume derivation is ever fixed, **do not assume the numbered manifests
are on disk.** The resume pointer now lives in `current-manifest.json` and in
git history. A correct fix should read the current manifest, or restore the step
manifests deliberately for the chains that need them, rather than silently
depending on files this branch removed.

Historical planning and gate records elsewhere under `docs/chains/rh/` still cite
these paths. Those citations were accurate on the dates they were written and are
deliberately left intact; the affected documents carry a removal overlay at the
top pointing here.

**175 files removed.**

## Block-clock inventory (4)

- `config/block-clock-inventory.json`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- `scripts/check_block_clock_inventory.py`
- `tests/inventory/test_block_clock_inventory.py`

## Deployment manifests (83)

- `migration_history/base-mainnet/v1/0000-manifest.json`
- `migration_history/base-mainnet/v1/1004-manifest.json`
- `migration_history/base-mainnet/v1/1005-manifest.json`
- `migration_history/base-mainnet/v1/1006-manifest.json`
- `migration_history/base-mainnet/v1/1007-manifest.json`
- `migration_history/base-mainnet/v1/1008-manifest.json`
- `migration_history/base-mainnet/v1/1009-manifest.json`
- `migration_history/base-mainnet/v1/1010-manifest.json`
- `migration_history/base-mainnet/v1/1011-manifest.json`
- `migration_history/base-mainnet/v1/1012-manifest.json`
- `migration_history/base-mainnet/v1/1013-manifest.json`
- `migration_history/base-mainnet/v1/1014-manifest.json`
- `migration_history/base-mainnet/v1/1015-manifest.json`
- `migration_history/base-mainnet/v1/1016-manifest.json`
- `migration_history/base-mainnet/v1/1017-manifest.json`
- `migration_history/base-mainnet/v1/2001-manifest.json`
- `migration_history/base-mainnet/v1/2025071501-manifest.json`
- `migration_history/base-mainnet/v1/2025071502-manifest.json`
- `migration_history/base-mainnet/v1/2025071503-manifest.json`
- `migration_history/base-mainnet/v1/2025071504-manifest.json`
- `migration_history/base-mainnet/v1/2025071505-manifest.json`
- `migration_history/base-mainnet/v1/2025071506-manifest.json`
- `migration_history/base-mainnet/v1/2025071601-manifest.json`
- `migration_history/base-mainnet/v1/2025071602-manifest.json`
- `migration_history/base-mainnet/v1/2025071801-manifest.json`
- `migration_history/base-mainnet/v1/2025072001-manifest.json`
- `migration_history/base-mainnet/v1/2025072201-manifest.json`
- `migration_history/base-mainnet/v1/2025072301-manifest.json`
- `migration_history/base-mainnet/v1/2025072701-manifest.json`
- `migration_history/base-mainnet/v1/2025072901-manifest.json`
- `migration_history/base-mainnet/v1/2025080401-manifest.json`
- `migration_history/base-mainnet/v1/2025080800-manifest.json`
- `migration_history/base-mainnet/v1/2025080900-manifest.json`
- `migration_history/base-mainnet/v1/2025080901-manifest.json`
- `migration_history/base-mainnet/v1/2025081200-manifest.json`
- `migration_history/base-mainnet/v1/2025081800-manifest.json`
- `migration_history/base-mainnet/v1/2025082000-manifest.json`
- `migration_history/base-mainnet/v1/2025090300-manifest.json`
- `migration_history/base-mainnet/v1/2025090400-manifest.json`
- `migration_history/base-mainnet/v1/2025102000-manifest.json`
- `migration_history/base-mainnet/v1/2025102200-manifest.json`
- `migration_history/base-mainnet/v1/2025111100-manifest.json`
- `migration_history/base-mainnet/v1/2025112400-manifest.json`
- `migration_history/base-mainnet/v1/2025112500-manifest.json`
- `migration_history/base-mainnet/v1/2025120200-manifest.json`
- `migration_history/base-mainnet/v1/2025120400-manifest.json`
- `migration_history/base-mainnet/v1/2025120700-manifest.json`
- `migration_history/base-mainnet/v1/2025120900-manifest.json`
- `migration_history/base-mainnet/v1/2026010900-manifest.json`
- `migration_history/base-mainnet/v1/2026011400-manifest.json`
- `migration_history/base-mainnet/v1/2026021300-manifest.json`
- `migration_history/base-mainnet/v1/2026021900-manifest.json`
- `migration_history/base-mainnet/v1/2026022000-manifest.json`
- `migration_history/base-mainnet/v1/2026030500-manifest.json`
- `migration_history/base-mainnet/v1/2026043000-manifest.json`
- `migration_history/base-mainnet/v1/2026072800-manifest.json`
- `migration_history/base-mainnet/v1/2026072801-manifest.json`
- `migration_history/base-mainnet/v1/2026080700-manifest.json`
- `migration_history/base-mainnet/v1/3001-manifest.json`
- `migration_history/base-mainnet/v1/3002-manifest.json`
- `migration_history/base-sepolia/v1/0000-manifest.json`
- `migration_history/base-sepolia/v1/0002-manifest.json`
- `migration_history/base-sepolia/v1/0003-manifest.json`
- `migration_history/base-sepolia/v1/current-manifest.json`
- `migration_history/base-sepolia/v2/0000-manifest.json`
- `migration_history/base-sepolia/v2/0001-manifest.json`
- `migration_history/base-sepolia/v2/current-manifest.json`
- `migration_history/robinhood-mainnet/v1/0000-manifest.json`
- `migration_history/robinhood-mainnet/v1/0001-manifest.json`
- `migration_history/robinhood-mainnet/v1/0002-manifest.json`
- `migration_history/robinhood-mainnet/v1/0003-manifest.json`
- `migration_history/robinhood-mainnet/v1/0004-manifest.json`
- `migration_history/robinhood-mainnet/v1/0005-manifest.json`
- `migration_history/robinhood-mainnet/v1/0006-manifest.json`
- `migration_history/robinhood-mainnet/v1/0008-manifest.json`
- `migration_history/robinhood-mainnet/v1/0009-manifest.json`
- `migration_history/robinhood-mainnet/v1/0010-manifest.json`
- `migration_history/robinhood-mainnet/v1/2026080700-manifest.json`
- `migration_history/robinhood-testnet/v1/0000-manifest.json`
- `migration_history/robinhood-testnet/v1/current-manifest.json`
- `migration_history/robinhood-testnet/v2/0000-manifest.json`
- `migration_history/robinhood-testnet/v2/0001-manifest.json`
- `migration_history/robinhood-testnet/v2/current-manifest.json`

## Evidence records (13)

- `docs/chains/rh/evidence/ccip-solidity-reference-round-3-review.md`
- `docs/chains/rh/evidence/dependency-exception-exit-preflight.md`
- `docs/chains/rh/evidence/h01-exception-retirement-feasibility.md`
- `docs/chains/rh/evidence/ledger-action-block-mainnet-fork.json`
- `docs/chains/rh/evidence/ledger-action-block-testnet-fork.json`
- `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md`
- `docs/chains/rh/evidence/network-profile-cli-implementation.md`
- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`
- `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`
- `docs/chains/rh/evidence/robinhood-manifest-macos-release-qualification.md`
- `docs/chains/rh/evidence/robinhood-manifest-phase-a.md`
- `docs/chains/rh/evidence/robinhood-migration-phase-a.md`
- `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`

## Handoff dashboard (26)

- `docs/chains/rh/dashboard/.gitignore`
- `docs/chains/rh/dashboard/.openai/hosting.json`
- `docs/chains/rh/dashboard/README.md`
- `docs/chains/rh/dashboard/app/chatgpt-auth.ts`
- `docs/chains/rh/dashboard/app/globals.css`
- `docs/chains/rh/dashboard/app/handoff/[slug]/route.ts`
- `docs/chains/rh/dashboard/app/layout.tsx`
- `docs/chains/rh/dashboard/app/page.tsx`
- `docs/chains/rh/dashboard/app/status-view.mjs`
- `docs/chains/rh/dashboard/build/sites-vite-plugin.ts`
- `docs/chains/rh/dashboard/eslint.config.mjs`
- `docs/chains/rh/dashboard/next.config.ts`
- `docs/chains/rh/dashboard/package-lock.json`
- `docs/chains/rh/dashboard/package.json`
- `docs/chains/rh/dashboard/postcss.config.mjs`
- `docs/chains/rh/dashboard/public/favicon.svg`
- `docs/chains/rh/dashboard/public/og.png`
- `docs/chains/rh/dashboard/scripts/sync-status.mjs`
- `docs/chains/rh/dashboard/tests/ci-contract.test.mjs`
- `docs/chains/rh/dashboard/tests/handoff-docs.test.mjs`
- `docs/chains/rh/dashboard/tests/integration-seal.test.mjs`
- `docs/chains/rh/dashboard/tests/rendered-html.test.mjs`
- `docs/chains/rh/dashboard/tests/status-source.test.mjs`
- `docs/chains/rh/dashboard/tsconfig.json`
- `docs/chains/rh/dashboard/vite.config.ts`
- `docs/chains/rh/dashboard/worker/index.ts`

## Probe package (9)

- `contracts/testing/ActionBlockIdentityProbe.vy`
- `contracts/testing/StockTokenTransferProbe.vy`
- `scripts/probes/aapl-robinhood-mainnet-fork.json`
- `scripts/probes/action_block_identity_probe.py`
- `scripts/probes/stock_token_transfer_probe.py`
- `tests/probes/conftest.py`
- `tests/probes/test_action_block_identity_probe.py`
- `tests/probes/test_probe_tooling.py`
- `tests/probes/test_stock_token_transfer_probe.py`

## Review records (39)

- `docs/chains/rh/qualification/canonical-launch-input-verification.md`
- `docs/chains/rh/qualification/canonical-launch-input-verification.tsv`
- `docs/chains/rh/qualification/curve-profile2-qualification.md`
- `docs/chains/rh/qualification/fork-suite-coverage-census.md`
- `docs/chains/rh/qualification/lp-launch-admission.md`
- `docs/chains/rh/qualification/network-token-oracle-authority.md`
- `docs/chains/rh/qualification/psm-liquidity-activation.md`
- `docs/chains/rh/reassessment/guarded-erc20-vault-architecture.md`
- `docs/chains/rh/reassessment/ledger-chain-abstraction.md`
- `docs/chains/rh/reassessment/psm-lite-permission-split.md`
- `docs/chains/rh/reassessment/teller-balance-measurement.md`
- `docs/chains/rh/reassessment/uniswap-price-source-decision.md`
- `docs/chains/rh/stock-token-m0-evidence.md`
- `docs/chains/rh/stock-token-m0-raw-evidence.json`
- `docs/chains/rh/stock-token-transferability-evidence.md`
- `docs/chains/rh/stock-token-vault-change-specification.md`
- `docs/chains/rh/stock-token-vault-change-validation-plan.md`
- `docs/chains/rh/stock-token-vault-comparison.md`
- `docs/chains/rh/stock-token-vault-decision.md`
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`
- `docs/chains/rh/track-1-chainlink-ccip-confirmation.md`
- `docs/chains/rh/track-2-stock-token-transferability.md`
- `docs/chains/rh/track-3-phase-0-inventory.md`
- `docs/chains/rh/track-4-usdg-psm-price-path.md`
- `docs/chains/rh/track-5-stock-token-vault-comparison.md`
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- `docs/chains/rh/track-6-s4-deleverage-cooldown.md`
- `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`
- `docs/chains/rh/track-6-s5-ledger-guard.md`
- `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`
- `docs/chains/rh/track-7-h2-network-profiles-cli.md`
- `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`
- `docs/chains/rh/track-7-robinhood-deployment-support.md`
- `docs/chains/rh/track-8-m0-owner-decision-packet.md`
- `docs/chains/rh/track-8-m1-exact-receipt.md`
- `docs/chains/rh/track-8-stock-token-vault-change.md`

## Workflows (1)

- `.github/workflows/rh-handoff-dashboard.yml`
