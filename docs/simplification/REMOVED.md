# Removed paths

Single index of everything the codebase-simplification branch removed from the
active tree, so a grep for a path that no longer exists lands somewhere useful.

No contract listed here was ever deployed, and no production contract was
modified. The only `.vy` files in this index are
`contracts/testing/ActionBlockIdentityProbe.vy` and
`contracts/testing/StockTokenTransferProbe.vy`; both were checked against the
**full history** — `git log --all -S` over `migrations/` and
`migration_history/` returns zero hits for either. That method matters: an
earlier revision of this branch asserted the same thing about
`contracts/mock/MockSGreenPrice.vy` on the strength of a single-commit tree
search, and it was wrong — that file *was* deployed and registered on Base
Sepolia v1. It is retained, and is no longer listed here. Every
file remains in git history and is recoverable with `git show <commit>:<path>`.
Archived copies are also kept outside the repo at
`~/dev/ripe-protocol-review-archives/rh-machete-chop/`.

## Deployment manifests: what is kept and why

**Step manifests are retained for the mainnets.** An earlier revision of this
branch pruned every numbered manifest, keeping only `current-manifest.json`.
That was reversed on owner instruction: per-step attribution -- which migration
deployed which contract, and each generation of a redeployed one -- is history
worth keeping, and its absence is also what left
`MigrationRunner._latest_manifest_timestamp()` with nothing to resume from.

60 `base-mainnet/v1` and 11 `robinhood-mainnet/v1` step manifests were recovered
from git (`origin/master` and the commits that removed them: `51616b9`,
`cc7a0a7`, `075c146`) and are committed again.

**Step manifests keep the record, not the compiler output.** Restored at full
fidelity they were 133.6 MB, because `abi` and `solc_json` are ~99.5% of the
bytes. Both were stripped from the numbered manifests, leaving `address`,
`file` and `args` -- which contract, from which source, with which constructor
arguments, at which step. That is 0.6 MB, and it is the part that is actually
history: `abi` and `solc_json` are reproducible by compiling `file` at that
commit.

Nothing read either field from a step manifest. `abi` has no manifest reader
anywhere -- `export_abis.py` compiles from source. `solc_json` is only consumed
by the Etherscan verifier, which also requires an explicit
`compiler_version` string; `deployed_contracts_manifest` has never emitted one,
on this branch or on `master`, so `verify_manifest` raises
`VerifierConfigurationError` against every manifest in the repository,
including the current ones. Stripping `solc_json` removes bytes no working path
could use.

`current-manifest.json` is untouched and keeps all five fields. It is the
runtime authority, and it is what a future `compiler_version` fix would make
verifiable. The base-sepolia and
robinhood-testnet step manifests are not retained; 31 of them are unreadable
from any commit reachable here, and the rest are testnet churn.

Only the `current-manifest.json` of each chain/version is read at runtime, by
`prepare_defaults.py`, `verify.py`, `verify_blockscout.py`, `console.py`, and
`Migration.__init__` itself. `verify.py` belongs on that list because its
`--manifest` option defaults to `current` (`scripts/migrate.py:131-135`), so an
operator verifying a deployment reads the current manifest unless they name
another one.

**Every `current-manifest.json` is retained — mainnet and testnet alike.** Six
remain: `base-mainnet/v1`, `base-sepolia/v1`, `base-sepolia/v2`,
`robinhood-mainnet/v1`, `robinhood-testnet/v1`, `robinhood-testnet/v2`. Only
numbered and timestamped step manifests are removed.

An earlier revision of this branch deleted the four testnet current manifests as
"disposable". **That was wrong and has been reverted.** Retained tooling reads
them: `migrations/base-sepolia/0002_CcipWire.py` and
`migrations/robinhood-testnet/0002_CcipWire.py` instruct operators to re-run the
step later with `--start-timestamp`, which needs the manifest to resolve local
and remote `RipeToken`, `RipeHq`, and `RipeTokenPool` addresses. Deleting them
turned a documented recovery path into a `FileNotFoundError`. The test suite did
not catch it because nothing exercised the readers; an independent review did.

`scripts/ccip_send.py` was a second reader — it defaulted to `--chain
base-sepolia --environment v2` and loaded that manifest directly — and it has
since been deleted as dead code, because its own broadcast path never executed
(`get_account(account)` passed one argument to a three-argument signature, so
every real invocation raised `TypeError`). **That removes a consumer, not the
requirement.** The CcipWire recovery path above still resolves against all six
manifests, so none of them became disposable when `ccip_send.py` went. Do not
re-derive "nothing reads these" from its absence; that is the exact inference
that produced the reverted deletion. `tests/test_current_manifest_consumers.py`
now pins the set in both directions — every declared manifest must be present
and usable, and every manifest on disk must be declared.

### Disposition of `scripts/ccip_send.py` — deprecated, owner decision closed

"It was broken" is why it was safe to delete this week. It is not a finding that
the capability is unwanted, and those are different claims. Recording the
difference, because the deletion rationale was doing duty for a disposition it
never established.

**The gap is real and specific.** The tool's own opening line states it:
Chainlink's Transporter UI only lists tokens Chainlink has onboarded, so a
self-served token like RIPE has to call `Router.ccipSend()` itself. RIPE and
GREEN are not onboarded. With the script gone there is no in-repo path to move
them across a lane — the remaining CCIP surface is the `CcipWire` migrations,
which wire pools and hand ownership to the Safe, and pool wiring is not a token
send. Anyone needing one now hand-builds the router call. No runbook ever
documented the script, so nothing operator-facing broke, but that absence is
also why the gap is easy to miss.

**The deleted implementation should not come back unchanged.** Three defects,
each independently disqualifying for a tool that moves value:

1. The broadcast path never executed. `get_account(account)` passed one argument
   to a three-argument signature, so every real send raised `TypeError`. The
   `--fork --as-address` simulation path skipped that call and did work, so the
   accurate statement is that it could dry-run and could never send.
2. `rpc` defaulted to
   `f"https://{chain}.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}"`,
   which becomes `.../v2/None` when the key is unset. It fails open on RPC
   configuration rather than refusing.
3. It read a raw `<NAME>_PRIVATE_KEY` hot key and broadcast by default —
   `--fork` was opt-in, so the bare invocation was a live send with no
   confirmation step.

**Recommendation: deprecate the implementation, keep the gap on the books.**
Restoring 154 lines that have never moved a token buys nothing; the recovery
point is recorded in `extracted-files.tsv`. If bridging is wanted, it is a
separate change that fixes account loading, requires an explicit RPC rather than
synthesising one, defaults to dry-run, and confirms before broadcast. That is
new work with a real blast radius, which is why it does not belong in a cleanup.
### Deployment re-run posture — owner decision (2026-08-12)

Extending a deployed history is **allowed**. Redeploying one by accident is
**not**, and they are the same command: `--start-timestamp` defaults to `0`, and
the runner selects every migration with a timestamp `>= 0` — all 13 for
`robinhood-mainnet`, all 66 for `base-mainnet`. A bare
`migrate --chain <chain>` is therefore a full redeploy, not a resume.

Nothing corrects for that on its own. The numbered step manifests are pruned by
the policy above, `end()` deletes the transaction log on success, and
`current-manifest.json` records contracts with no step attribution, so nothing
says which migration ran last. `_latest_manifest_timestamp()` cannot help
either: with only a current manifest present it yields `"current"`, and
`int("current")` raises.

What does survive is `current-manifest.json` itself, written by
`_append_manifest` on the first successful step. So that is the signal:

- History has a `current-manifest.json` → refuse, unless the caller passes an
  explicit `--start-timestamp` or `--is-retry`.
- No current manifest → first deployment, nothing to protect, runs as before.

`MigrationRunner` enforces it and `Migration` fails closed for any other caller.
This replaces an earlier version that hard-coded the two Robinhood v1 paths; the
manifest check needs no list and covers Base, whose 66-migration redeploy was
the larger exposure.

    python -m scripts.migrate --chain robinhood-mainnet --start-timestamp 2026081200
    python -m scripts.migrate --chain robinhood-mainnet --is-retry

**Owner decision (2026-08-12): deprecated, not to be rebuilt.** The script was
scaffolding for exercising a lane before it was live, not an operator tool. The
lanes are now deployed and wired — `config/Ccip.py` declares both mainnet and
both testnet lanes with their routers and chain selectors, and the eight
`CcipPool`/`CcipWire` migrations deploy the token pools on each side and hand
ownership to the Safe.

That closes the gap recorded above rather than leaving it outstanding. It was a
real gap in repository terms and not an operational one: with pools wired and
Safe-owned, moving RIPE or GREEN across a lane is a Safe transaction against the
live router, not a laptop script holding a raw `<NAME>_PRIVATE_KEY` and
broadcasting by default. The three defects listed above are moot; the recovery
point stays in `extracted-files.tsv` for reference only.

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

**119 files removed.**

The two `Deployment tooling` sections below are this PR's removals — the unused
H-02/H-06/H-08 deployment machinery. Everything above and below them predates it.
Recovery metadata for the 19 (git mode, blob id, byte length, sha256, and a
commit each is retrievable from) is in `extracted-files.tsv` under the
`deployment-tooling` and `deployment-tooling-test` categories.

## Block-clock inventory (4)

- `config/block-clock-inventory.json`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- `scripts/check_block_clock_inventory.py`
- `tests/inventory/test_block_clock_inventory.py`

## Deployment manifests (8)

- `migration_history/base-sepolia/v1/0000-manifest.json`
- `migration_history/base-sepolia/v1/0002-manifest.json`
- `migration_history/base-sepolia/v1/0003-manifest.json`
- `migration_history/base-sepolia/v2/0000-manifest.json`
- `migration_history/base-sepolia/v2/0001-manifest.json`
- `migration_history/robinhood-testnet/v1/0000-manifest.json`
- `migration_history/robinhood-testnet/v2/0000-manifest.json`
- `migration_history/robinhood-testnet/v2/0001-manifest.json`

## Deployment tooling (11)

- `scripts/ccip_send.py`
- `scripts/check_deployment.py`
- `scripts/params/validate_robinhood_reward_launch_plan.py`
- `scripts/proposals/__init__.py`
- `scripts/proposals/build_ledger_artifact_bundle.py`
- `scripts/proposals/ledger-robinhood-profile.json`
- `scripts/proposals/ledger_robinhood_profile.py`
- `scripts/proposals/lootbox-deployment-profiles.json`
- `scripts/proposals/lootbox_deployment_profiles.py`
- `scripts/utils/deployment_assertions.py`
- `scripts/utils/manifest_schema.py`

## Deployment tooling tests (8)

- `tests/deployment/test_current_manifest_promotion.py`
- `tests/deployment/test_manifest_schema.py`
- `tests/deployment/test_post_deployment_assertions.py`
- `tests/deployment/test_registry_topology.py`
- `tests/deployment_profiles/conftest.py`
- `tests/deployment_profiles/test_ledger_artifact_bundle.py`
- `tests/deployment_profiles/test_ledger_robinhood_profile.py`
- `tests/deployment_profiles/test_lootbox_deployment_profiles.py`

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
