# Superseded Base staging migrations

These five September staging files are retained unchanged for deployment provenance
and historical diagnostics, but removed from the runnable Base migration directory.
The standard runner only scans `migrations/base-mainnet`, not this archive.
Do not execute these files against live Base or reuse their candidate labels.
Existing deployment logs/manifests are preserved; no completion records are fabricated.

The fresh deploy-only flow starts at
`2026092100_DeployBaseDefaultsMissionControlFoxtrot.py`.
