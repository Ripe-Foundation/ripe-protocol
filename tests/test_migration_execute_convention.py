"""Every state-changing call in a migration must go through the runner.

`migration.execute` and `migration.deploy` both route through `Migration._run`,
which records the call in the transaction log and **skips it if the log says it
already happened**. That is the entire resume mechanism: a migration that dies
partway is re-run, and the steps already broadcast are not broadcast again.

A state-changing call made directly on a contract object bypasses that. It is
not recorded, so it is not skipped, so it executes a second time on every
resume. Whether that is harmless or fatal depends on the method, and for the
one that prompted this module it was fatal:

    vault_book.relinquishGov()            # migrations/base-mainnet/2026081200

`LocalGov.relinquishGov` asserts `msg.sender == self.governance` and then sets
`self.governance = empty(address)`, so the second call reverts with `no perms`.
The failure window is narrow and unrecoverable: if the migration completes its
loop and this call, then fails before `end()` finishes writing manifests, the
resume finds the deploy already logged, the registry already matching, and this
call reverting. The migration can never complete. The only ways out are editing
the migration or forcing a full replay, and a full replay deploys a *second*
VaultBook.

That call ran successfully on base-mainnet, so nothing is broken today; wrapping
it changes resumability and the template the next migration is copied from, not
history. 89 of the 90 migrations already followed the convention. Nothing
enforced it, which is why one didn't.

Deliberately an AST check rather than a runtime one: it costs milliseconds,
needs no chain, and catches the mistake in review rather than partway through a
live deployment. It runs in the lean lane for the same reason -- `pytest.ini`
ignores `tests/deployment`, and a guard on the deploy path should not sit in a
tree the default lane skips.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"

# Methods that change chain state. A read (`old_vb.addrInfo(i)`,
# `vault_book.pendingNewAddr(...)`) is fine unwrapped -- it broadcasts nothing
# and re-running it is free. Only broadcasts need the log.
#
# Kept as an explicit list rather than "any call on a contract object" because
# migrations legitimately read from contracts constantly, and a heuristic that
# tried to tell reads from writes by name would either miss writes or reject
# reads. Add to this list when a migration introduces a new mutating call.
STATE_CHANGING = frozenset({
    "applyChainUpdates",
    "confirmNewAddressToRegistry",
    "finishGov",
    "initiateGov",
    "relinquishGov",
    "setCanMint",
    "setGov",
    "startAddNewAddressToRegistry",
    "transferOwnership",
})


def _unwrapped_state_changes(path):
    """(line, expression) for each bare `<contract>.<mutator>()` statement."""
    found = []
    tree = ast.parse(path.read_bytes(), filename=str(path))
    for node in ast.walk(tree):
        # Only bare expression statements. A mutator passed *as an argument* --
        # `migration.execute(vault_book.relinquishGov)` -- is an ast.Attribute
        # that is never called here, so it is correctly not matched.
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if not isinstance(func, ast.Attribute) or func.attr not in STATE_CHANGING:
            continue
        receiver = func.value
        if isinstance(receiver, ast.Name) and receiver.id != "migration":
            found.append((node.lineno, f"{receiver.id}.{func.attr}()"))
    return found


def test_no_migration_broadcasts_outside_the_transaction_log():
    offenders = []
    for path in sorted(MIGRATIONS.rglob("*.py")):
        for line, expression in _unwrapped_state_changes(path):
            offenders.append(
                f"{path.relative_to(ROOT).as_posix()}:{line} {expression}"
            )

    assert not offenders, (
        "these migrations change state without going through migration.execute, "
        "so the call is absent from the transaction log and will be broadcast "
        "again on every resume: " + "; ".join(offenders)
    )


def test_the_convention_is_actually_load_bearing_here():
    # Guards the guard. If migrations stop being discovered -- renamed tree,
    # changed layout -- the check above passes vacuously, which is the failure
    # mode that let the original slip through in the first place.
    migrations = [
        path
        for path in MIGRATIONS.rglob("*.py")
        if path.name != "__init__.py"
    ]
    assert len(migrations) > 80, (
        f"only {len(migrations)} migrations discovered under {MIGRATIONS}; "
        "the convention check above would be scanning almost nothing"
    )

    executed = sum(
        1
        for path in migrations
        if "migration.execute(" in path.read_text()
    )
    assert executed > 20, (
        f"only {executed} migrations call migration.execute; either the runner "
        "API changed or discovery is broken, and the check above is vacuous"
    )
