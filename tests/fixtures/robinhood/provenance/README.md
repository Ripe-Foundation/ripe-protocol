# Robinhood historical authority fixtures

These fixtures keep the Robinhood defaults tests reproducible in a fresh clone.
The PR #66 and launch-input commits named in
`historical-authority-baselines.json` are not ancestors of the current `rh`
history, so a normal full-depth checkout cannot load them with `git show`.

`defaults-robinhood-pr66.vy.snapshot.base64` is a lossless base64 encoding of
the exact historical Vyper blob, including its original trailing whitespace.
The JSON fixture binds it to its commit, tree, blob object, path, and SHA-256.

The launch ledger is much larger, so the JSON stores a lossless projection for
the assertions that consume it:

- all 33 removed record identities and destinations;
- the prior destination, status, and semantic value for all 16 reconciled
  records; and
- a canonical SHA-256 over the same fields for all 387 stable records.

The tests pin the source metadata, counts, and projection digest independently.
Updating either fixture therefore requires an explicit provenance-baseline
change, not merely a locally available Git object.
