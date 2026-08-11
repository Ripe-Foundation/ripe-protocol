# Migration runner remediation

Status: implementation evidence for PR #67; no deployment or release authority.

The operator migration path now treats the canonical network profile as the
authority for the RPC environment variable, chain ID, migration namespace,
history namespace, blueprint, and allowed live signer backends. The endpoint's
`eth_chainId` response is verified before a private key, Ledger, migration
history, or Boa execution environment is opened. `--chain` remains only as a
compatibility spelling of `--profile`; it cannot select a different repository
or blueprint.

Live Safe proposal submission is not implemented by this runner. `--safe` is
therefore fork-only impersonation, and the Base profile no longer advertises a
live Safe backend. A live Safe path may be added only with its own proposal,
signature, nonce, finality, and reconciliation qualification.

Normal execution resumes from prior transaction logs and strictly after the
latest numeric completed-migration manifest. `--force-replay` (with deprecated
alias `--is-retry`) is the only path that ignores a transaction log. A history
containing only `current-manifest.json` has no trustworthy completion cursor,
so auto-resume fails with `MIGRATION_RESUME_CHECKPOINT_REQUIRED` and requires
an explicit reviewed start timestamp.

Legacy migrations now write deployments to a timestamp-scoped pending manifest
while the step is running. A pending manifest never replaces `current`, and a
numbered completion checkpoint is written only by `Migration.end()`. The
current index is published before the numeric completion marker so a process
failure cannot make auto-resume skip past an older current index. An incomplete
pending/log pair and force-replay over a pending journal both fail closed.

State-changing calls make one attempt by default. A caller may supply a larger
retry budget only after establishing that its operation is idempotent or
receipt-reconciled; this prevents a provider exception raised after broadcast
from silently replaying an ordinary migration action. A successful callable
whose selected ABI entry declares no outputs is journaled with the durable
`MIGRATION_TRANSACTION_CONFIRMED_NO_OUTPUT` marker. Any other post-call
`None` raises `MIGRATION_TRANSACTION_RESULT_MISSING` immediately and is never
retried, appended to the log, or printed as confirmed. An actual call exception
raises `MIGRATION_TRANSACTION_FAILED` when its explicit attempt budget is
exhausted.

Robinhood's imperative path also fails before signer construction while any
selected external address in `config/BluePrint.py` remains classified as an
unverified fact. `config.robinhood_launch.address()` independently enforces the
same rule for each migration consumer. Resolution requires a reviewed source
authority update, not a code-path bypass.

The Ledger signing smoke and live Defaults snapshot generator now require
chain ID `4663`. Any other chain exits before a signature request or live-state
read is accepted as Robinhood evidence.

This remediation does not authorize replaying historical Robinhood migrations,
promoting replacement candidates before governance activation, or submitting
transactions. Those lifecycle and activation postconditions remain separate
integration gates.
