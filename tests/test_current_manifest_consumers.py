"""Every current manifest a retained consumer reads must be present and usable.

This exists because of a defect that shipped and was caught in review rather
than by a test. An earlier revision of the codebase-simplification branch deleted
the four testnet `current-manifest.json` files as "disposable". They are not:

- `scripts/ccip_send.py` defaults to `--chain base-sepolia --environment v2` and
  loads that manifest directly through `_manifest()`;
- `migrations/base-sepolia/0002_CcipWire.py` and
  `migrations/robinhood-testnet/0002_CcipWire.py` instruct the operator to re-run
  the step later with `--start-timestamp`, which resolves `RipeToken`, `RipeHq`,
  and `RipeTokenPool` locally and `RipeTokenPool`/`RipeToken` on the remote chain.

Deleting them turned a documented recovery path into a `FileNotFoundError`, and
no test objected. Neither lane was green at the time, so the accurate statement
is that this produced **no new red** — the deletion was invisible to the suite.

`REQUIRED_CURRENT_MANIFESTS` records *how* each key is consumed, because that
decides what has to be valid in the record. A first revision of this module
checked only addresses, and a review defeated it twice: renaming the default
manifest's `RipeToken.file` to `file_missing` left every test green even though
`ccip_send` would die at `boa.load_partial`, and changing the real `--chain`
default to a nonexistent chain also left every test green, because the defaults
were retyped here as constants instead of read from the command. Both are closed
below: the modes distinguish an address-only read from a `load_partial`, and the
defaults come from `scripts.ccip_send.cli` itself.

These tests are offline: they read committed JSON and touch no network, RPC, or
private key. They live at `tests/` root rather than `tests/deployment/` for one
reason — `pytest.ini` passes `--ignore=tests/deployment`, and the automatic pull
request workflow runs only the lean lane, so a guard placed there would never run
in CI. Numbered step manifests are deliberately not required; only the current
manifest of each supported chain/environment pair.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "migration_history"

# How a consumer reads a record, which is what decides the record's obligations.
#
#   ADDRESS_ONLY -- reached through `migration.get_address`,
#                   `get_address_on_chain`, or `get_solidity_contract`, all of
#                   which take the address and get the ABI elsewhere. These
#                   records legitimately carry no `file`, and `RipeTokenPool`
#                   in fact does not; requiring one would be wrong.
#   LOADABLE     -- reached through `boa.load_partial(record["file"]).at(
#                   record["address"])`, which is what `migration.get_contract`
#                   and `scripts/ccip_send.py` both do. The `file` must exist,
#                   or the consumer raises at the point of use.
ADDRESS_ONLY = "address_only"
LOADABLE = "loadable"

REQUIRED_CURRENT_MANIFESTS = {
    ("base-mainnet", "v1"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "GreenToken": LOADABLE,
    },
    ("base-sepolia", "v1"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "GreenToken": LOADABLE,
    },
    ("base-sepolia", "v2"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "RipeTokenPool": ADDRESS_ONLY,
    },
    ("robinhood-mainnet", "v1"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "GreenToken": LOADABLE,
    },
    ("robinhood-testnet", "v1"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "GreenToken": LOADABLE,
    },
    ("robinhood-testnet", "v2"): {
        "RipeToken": LOADABLE,
        "RipeHq": LOADABLE,
        "RipeTokenPool": ADDRESS_ONLY,
    },
}


def _ccip_send_module():
    """`scripts.ccip_send`, imported without its module-level dotenv side effect.

    The module calls `dotenv.load_dotenv()` at import. That is right for an
    operator running the script and wrong for a test lane, where it would read
    the developer's `.env` into `os.environ` for every subsequent test in the
    process. Patching it keeps this guard inert on first import; if some earlier
    test already imported the module, this is a harmless no-op.
    """
    with mock.patch("dotenv.load_dotenv"):
        import scripts.ccip_send as module

    return module


def _ccip_send_option_default(name):
    """The live default of a `ccip_send` command option, read from the command.

    Not retyped as a constant here. The point of this guard is to fail when the
    script's real target moves, which a copied constant cannot do.
    """
    cli = _ccip_send_module().cli
    for param in cli.params:
        if param.name == name:
            return param.default

    raise AssertionError(
        f"scripts/ccip_send.py has no --{name.replace('_', '-')} option; "
        "this guard is bound to an option that no longer exists"
    )


def _assert_record_is_usable(chain, environment, key, mode, record):
    where = f"{chain}/{environment} {key}"

    address = record.get("address")
    assert isinstance(address, str) and address.startswith("0x"), (
        f"{where} has no usable address: {address!r}"
    )
    assert int(address, 16) != 0, f"{where} is the zero address"

    if mode == ADDRESS_ONLY:
        return

    assert mode == LOADABLE, f"{where} declares unknown mode {mode!r}"
    source = record.get("file")
    assert isinstance(source, str) and source, (
        f"{where} is read through boa.load_partial(record['file']) but the "
        f"record has no 'file' key (has: {sorted(record)})"
    )
    assert (ROOT / source).is_file(), (
        f"{where} points at {source}, which does not exist. Its consumer calls "
        "boa.load_partial on that path and would raise at the point of use."
    )


@pytest.mark.parametrize(("chain", "environment"), sorted(REQUIRED_CURRENT_MANIFESTS))
def test_required_current_manifest_resolves_every_field_its_consumers_read(
    chain, environment
):
    path = HISTORY / chain / environment / "current-manifest.json"
    assert path.is_file(), (
        f"{path.relative_to(ROOT)} is missing. A retained consumer reads it; "
        "see this module's docstring before deleting it."
    )

    contracts = json.loads(path.read_bytes())["contracts"]
    expected = REQUIRED_CURRENT_MANIFESTS[(chain, environment)]

    missing = sorted(key for key in expected if key not in contracts)
    assert not missing, f"{chain}/{environment} manifest lacks {missing}"

    for key, mode in sorted(expected.items()):
        _assert_record_is_usable(chain, environment, key, mode, contracts[key])


def test_ccip_send_default_target_is_declared_and_fully_resolvable(monkeypatch):
    """The script's own defaults, resolved the way the script resolves them."""
    chain = _ccip_send_option_default("chain")
    environment = _ccip_send_option_default("environment")
    token = _ccip_send_option_default("token")

    assert (chain, environment) in REQUIRED_CURRENT_MANIFESTS, (
        f"scripts/ccip_send.py defaults to {chain}/{environment}, which is not a "
        f"declared target here. Either the default moved and this table must "
        f"follow it, or the default now points at a manifest nothing guarantees."
    )
    declared = REQUIRED_CURRENT_MANIFESTS[(chain, environment)]
    assert declared.get(token) == LOADABLE, (
        f"scripts/ccip_send.py defaults to --token {token}, which it loads with "
        f"boa.load_partial, but {chain}/{environment} declares it as "
        f"{declared.get(token)!r} here"
    )

    # `_manifest` builds a path relative to the working directory, so pin it.
    monkeypatch.chdir(ROOT)
    contracts = _ccip_send_module()._manifest(chain, environment)

    for key, mode in sorted(declared.items()):
        assert key in contracts, (
            f"ccip_send default target {chain}/{environment} cannot resolve {key}"
        )
        _assert_record_is_usable(chain, environment, key, mode, contracts[key])

    # The exact two fields the script dereferences on the token it was told to
    # send: `record["file"]` and `record["address"]`, in that order.
    record = contracts[token]
    assert (ROOT / record["file"]).is_file()
    assert int(record["address"], 16) != 0


def test_every_committed_current_manifest_is_declared_here():
    # The reverse direction: a current manifest on disk that nothing declares is
    # either a new supported target that belongs above, or a leftover.
    on_disk = {
        (p.parent.parent.name, p.parent.name)
        for p in HISTORY.glob("*/*/current-manifest.json")
    }
    assert on_disk == set(REQUIRED_CURRENT_MANIFESTS), (
        f"committed current manifests {sorted(on_disk)} do not match the "
        f"declared set {sorted(REQUIRED_CURRENT_MANIFESTS)}"
    )
