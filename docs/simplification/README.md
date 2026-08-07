# RH codebase simplification

- **Branch:** `codex/rh-codebase-simplification`
- **Baseline:** `610b43f4508e85628a1362532a79d68d71ea902c` (`rh` / `origin/rh` at plan time)
- **Authorizing plan:** [`implementation-plan.md`](implementation-plan.md) — the exact
  bytes of `RH-CODEBASE-SIMPLIFICATION-PLAN.md` used to authorize this run
  (SHA-256 `52b9d33f2157b463a6cf26c8fe37783b4ce81bcd6157f5e841be73392ee13e4e`).
- **Extraction manifest:** [`extracted-files.tsv`](extracted-files.tsv)

Nothing was archived inside the repository. Every extracted path is recovered
from Git history at the baseline commit.

## Recovery

`extracted-files.tsv` records one row per extracted path with its category,
original path, Git mode, baseline blob ID, byte length, SHA-256, and recovery
commit.

Restore a single file:

```bash
git show 610b43f4508e85628a1362532a79d68d71ea902c:migration_history/base-mainnet/v1/1004-manifest.json > /tmp/1004-manifest.json
```

Restore an entire extracted category back into the working tree:

```bash
git checkout 610b43f4508e85628a1362532a79d68d71ea902c -- migration_history/base-mainnet/v1 migration_history/robinhood-mainnet/v1
git checkout 610b43f4508e85628a1362532a79d68d71ea902c -- docs/chains/rh/dashboard .github/workflows/rh-handoff-dashboard.yml
```

Verify every row in the manifest recovers with matching bytes:

```bash
python - <<'EOF'
import csv, hashlib, subprocess
bad = []
for row in csv.DictReader(open("docs/simplification/extracted-files.tsv"), delimiter="\t"):
    blob = subprocess.run(
        ["git", "cat-file", "blob", f"{row['recovery_commit']}:{row['original_path']}"],
        capture_output=True, check=True,
    ).stdout
    if (len(blob) != int(row["byte_length"])
            or hashlib.sha256(blob).hexdigest() != row["sha256"]):
        bad.append(row["original_path"])
print("mismatches:", bad or "none")
EOF
```

## What was extracted

| Category | Files | Notes |
| --- | ---: | --- |
| `migration-history-step-manifest` | 66 | 59 Base + 7 Robinhood numeric step manifests. Both `current-manifest.json` files, both `v1` directories, and every `config/network_profiles.py` declaration are retained unchanged. |
| `dashboard-application` | 26 | The parked `docs/chains/rh/dashboard/` Next.js application. |
| `dashboard-workflow` | 1 | `.github/workflows/rh-handoff-dashboard.yml`. `.github/workflows/python-tests.yml` is retained. |

## What was deliberately retained

- All production Vyper, `interfaces/`, and every `migrations/` source file.
- All 52 checked-in ABIs under `scripts/abis/`, plus the artifact
  checker/updater/exporter and their expectation file.
- All 34 `contracts/mock/` files — every one has a retained consumer.
- `requirements.in`, `requirements.txt`, and the frozen dependency-security
  evidence.
- `scripts/migrate.py`, `scripts/check_deployment.py`,
  `scripts/utils/migration_runner.py`, and `scripts/utils/manifest_schema.py`,
  all unchanged.
- The block-clock process package, the probe package, `tests/deployment/fork/`,
  and `tests/vaults/test_stock_token_vault_comparison.py`. Each is a conditional
  plan candidate that a retained consumer or a committed authority blocked; the
  end-of-task report records the evidence for each de-scope.
