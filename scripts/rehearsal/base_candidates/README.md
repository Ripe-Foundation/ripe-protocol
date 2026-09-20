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
Retain Base's **1.5M/1.5M immutable floors for the approved implementation and
rehearsal scope**. Production qualification and any owner decision to lower those
floors remain separate. No later decision to lower them is recorded; record the
final decision and its date when established. Lowering a deployed immutable floor
requires a replacement PriceDesk; source overrides cannot lower it.
Assess any proposed replacement floors together with Curve and Undy overrides
before qualifying a final deployment.
