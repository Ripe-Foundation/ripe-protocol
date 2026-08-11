"""Every current manifest a retained consumer reads must be present and usable.

This exists because of a defect that shipped and was caught in review rather
than by a test. An earlier revision of the codebase-simplification branch deleted
the four testnet `current-manifest.json` files as "disposable". They are not:

- `scripts/ccip_send.py` requires an explicit chain/environment pair and loads
  that manifest directly through `_manifest()`;
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
required targeting comes from `scripts.ccip_send.cli` itself.

These tests are offline: they read committed JSON and touch no network, RPC, or
private key. They live at `tests/` root rather than `tests/deployment/` because
`pytest.ini` passes `--ignore=tests/deployment`; root placement keeps the guard
in the lean lane as well as the comprehensive lane. Numbered step manifests are
deliberately not required; only the current manifest of each supported
chain/environment pair.
"""

from __future__ import annotations

import ast
import json
import warnings
from pathlib import Path
from unittest import mock

import boa
import pytest
from eth_utils import is_address
from scripts.utils.migration import Migration


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep offline manifest tests independent of protocol deployment."""


# Methods `scripts/ccip_send.py` calls on the token it resolves: `balanceOf` at
# the balance check and `approve` before the router send. A record can name a
# real file at a real address and still be unusable if the artifact that file
# compiles to lacks these.
CCIP_SEND_TOKEN_METHODS = ("balanceOf", "approve")


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "migration_history"
MIGRATIONS = ROOT / "migrations"

CCIP_RUNNER_CONSUMERS = {
    "deploy_solidity": {
        "migrations/base-mainnet/2026080700_CcipPools.py",
        "migrations/base-sepolia/0001_CcipPool.py",
        "migrations/robinhood-mainnet/2026080700_CcipPools.py",
        "migrations/robinhood-testnet/0001_CcipPool.py",
    },
    "get_address_on_chain": {
        "migrations/base-mainnet/2026080701_CcipWire.py",
        "migrations/base-sepolia/0002_CcipWire.py",
        "migrations/robinhood-mainnet/2026080701_CcipWire.py",
        "migrations/robinhood-testnet/0002_CcipWire.py",
    },
    "get_solidity_contract": {
        "migrations/base-mainnet/2026080701_CcipWire.py",
        "migrations/base-sepolia/0002_CcipWire.py",
        "migrations/robinhood-mainnet/2026080701_CcipWire.py",
        "migrations/robinhood-testnet/0002_CcipWire.py",
    },
    "timestamp": {
        "migrations/base-sepolia/0002_CcipWire.py",
        "migrations/robinhood-testnet/0002_CcipWire.py",
    },
}

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


def _migration_runner_calls(path):
    calls = set()
    tree = ast.parse(path.read_bytes(), filename=str(path))
    for node in ast.walk(tree):
        function = node.func if isinstance(node, ast.Call) else None
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "migration"
        ):
            calls.add(function.attr)
    return calls


def _ccip_send_option(name):
    """Return a `ccip_send` command option from the actual command."""
    cli = _ccip_send_module().cli
    for param in cli.params:
        if param.name == name:
            return param

    raise AssertionError(
        f"scripts/ccip_send.py has no --{name.replace('_', '-')} option; "
        "this guard is bound to an option that no longer exists"
    )


def _assert_record_is_usable(chain, environment, key, mode, record):
    where = f"{chain}/{environment} {key}"

    # Validated the way the consumer validates it, not by shape.
    #
    # A review defeated an earlier `startswith("0x")` and `int(address, 16) != 0`
    # pair by setting an address to "0x1": both passed, and the real consumer
    # then died on `boa.load_partial(...).at("0x1")` with
    # `ValueError: Unknown format '0x1'`. `eth_utils.is_address` is the check
    # that agrees with the consumer -- it requires exactly 20 bytes.
    address = record.get("address")
    assert isinstance(address, str) and is_address(address), (
        f"{where} address {address!r} is not a valid 20-byte address. "
        "boa would reject it at the point of use."
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

    # `file` must be *this record's own* compilation target, not merely some
    # file that exists. The same review repointed a token's `file` at
    # `contracts/core/CreditEngine.vy` -- a real path, so an existence check
    # passed -- and the consumer then built a wrapper with no `balanceOf`, which
    # it calls on the next line.
    #
    # The record carries its own compiler input. `solc_json.settings.outputSelection`
    # names exactly the contract that was compiled to produce this address, so
    # that is the binding. Membership in `solc_json.sources` is deliberately not
    # used: sources also contains imported modules, and pointing `file` at an
    # imported module -- e.g. `contracts/tokens/modules/Erc20Token.vy`, which
    # does expose `balanceOf` and `approve` -- would satisfy a membership test
    # and every method check while still naming the wrong artifact.
    solc_json = record.get("solc_json", {})
    targets = solc_json.get("settings", {}).get("outputSelection", {})
    assert targets, (
        f"{where} is loadable but carries no solc_json.settings.outputSelection "
        "to bind its 'file' against"
    )
    assert source in targets, (
        f"{where} names {source}, which is not this record's compilation target "
        f"({sorted(targets)}). The address was produced by compiling that "
        "target, so this file is not the artifact deployed there."
    )

    # Note on what is deliberately *not* asserted: `solc_json.sources[...]`
    # carries a `sha256sum`, and it does not match the file on disk for several
    # records (every `RipeHq`, and `RipeToken` on three chains). That is correct
    # and expected -- production sources have moved on since those deployments.
    # Asserting equality would fail on valid data and would be a claim about
    # source drift, not about manifest usability, which is what this module
    # guards.


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


def test_ccip_send_requires_explicit_target_and_supported_manifests_resolve(monkeypatch):
    """The CLI must not silently select a chain or manifest environment."""
    assert _ccip_send_option("chain").required
    assert _ccip_send_option("environment").required
    assert _ccip_send_option("amount").required
    token = _ccip_send_option("token").default

    supported = {
        target: declared
        for target, declared in REQUIRED_CURRENT_MANIFESTS.items()
        if declared.get(token) == LOADABLE
    }
    assert supported
    for (chain, environment), declared in sorted(supported.items()):
        contracts = _ccip_send_module()._manifest(chain, environment)
        for key, mode in sorted(declared.items()):
            assert key in contracts, (
                f"ccip_send target {chain}/{environment} cannot resolve {key}"
            )
            _assert_record_is_usable(chain, environment, key, mode, contracts[key])

    # Perform the consumer's own compilation/resolution for one representative
    # supported target; the per-manifest bindings above ensure every other
    # target names its own loadable compiler input.
    chain, environment = "base-mainnet", "v1"
    declared = supported[(chain, environment)]
    assert declared.get(token) == LOADABLE, (
        f"scripts/ccip_send.py defaults to --token {token}, which it loads with "
        f"boa.load_partial, but {chain}/{environment} declares it as "
        f"{declared.get(token)!r} here"
    )

    # `_manifest` is rooted at the repository; changing cwd must not redirect it.
    monkeypatch.chdir(ROOT)
    contracts = _ccip_send_module()._manifest(chain, environment)

    # Finally, perform the consumer's own resolution rather than approximating
    # it. `ccip_send` does exactly this on the token it was told to send:
    #
    #     erc20 = boa.load_partial(manifest["file"]).at(manifest["address"])
    #     ... erc20.balanceOf(sender) ... erc20.approve(router, amount)
    #
    # Anything that survives the checks above but cannot produce a usable token
    # wrapper fails here, at the same call the operator would hit. This compiles
    # one contract; boa caches it, and the lane already compiles this token.
    record = contracts[token]
    with warnings.catch_warnings():
        # `.at()` on an address with no code in this env is expected and warns.
        warnings.simplefilter("ignore")
        erc20 = boa.load_partial(str(ROOT / record["file"])).at(record["address"])

    missing = [m for m in CCIP_SEND_TOKEN_METHODS if not hasattr(erc20, m)]
    assert not missing, (
        f"ccip_send resolves {chain}/{environment} {token} to "
        f"{record['file']}, which compiles to an artifact without {missing}. "
        f"The script calls {list(CCIP_SEND_TOKEN_METHODS)} on it."
    )


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


def test_every_retained_migration_runner_call_resolves_to_a_callable_method():
    consumers = {}
    for path in sorted(MIGRATIONS.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        for method in _migration_runner_calls(path):
            consumers.setdefault(method, set()).add(relative)

    missing = sorted(
        method
        for method in consumers
        if not callable(getattr(Migration, method, None))
    )
    assert not missing, (
        "retained migrations call methods missing from scripts.utils.migration."
        f"Migration: {missing}"
    )

    for method, expected_paths in CCIP_RUNNER_CONSUMERS.items():
        assert consumers.get(method) == expected_paths, (
            f"{method} consumer census changed; update the runner and this "
            "explicit recovery-path inventory together"
        )
