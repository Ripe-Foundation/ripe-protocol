# Base candidate rehearsal drafts

These scripts are loaded by path by local tests and `base_full_update_fork.py`.
They are deliberately outside the live migration runner's directory. Qualification
and explicit deployment authorization must precede adding a production migration
with a fresh timestamp, labels and journal.

`oracles_psm_reserves.py` preserves the reviewed, non-budget behavior of frozen
`2026091402`. The historical file cannot become a shared mutable implementation:
its executed journal and seven-argument constructor must remain reproducible.
A structural parity regression pins the current draft to that historical body
outside its named budget/label changes. Shared current budget validation and
readbacks live in `price_desk_budgets.py` and are used by both drafts.

`price_desk_gas_bridge.py` retains existing sources and stages a paused compatible
Teller. Both drafts apply and read back the profile's source overrides before
relinquishing temporary governance. Full constructor/default/override tests use
real PriceDesk and Teller contracts with explicit local dependency doubles.

The per-profile table in `config/BluePrint.py` is provisional rehearsal input.
It does not qualify live sources, approve a deployment, or authorize activation.
Base's lower immutable floors remain an owner decision; any changed floor must
be assessed together with Curve and Undy overrides before deploying a final desk.
