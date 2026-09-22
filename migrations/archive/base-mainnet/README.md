# Superseded Base staging migrations

These five September staging files are retained unchanged for deployment provenance
and historical diagnostics, but removed from the runnable Base migration directory.
The standard runner only scans `migrations/base-mainnet`, not this archive.
Do not execute these files against live Base or reuse their candidate labels.
Their staging checkpoints and candidate entries were removed from current history
for redeployment. They remain recoverable from Git at commit `b946b3b7`; use that
revision for historical diagnostics requiring those records. Canonical live-contract
entries and older completion records are retained. No completion records are fabricated.

The fresh deploy-only flow starts at
`2026092100_DeployBaseDefaultsMissionControlFoxtrot.py`.
