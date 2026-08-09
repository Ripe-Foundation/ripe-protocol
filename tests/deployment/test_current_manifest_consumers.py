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

Deleting them turned a documented recovery path into a `FileNotFoundError`. The
whole suite stayed green, because nothing exercised it.

These tests are offline: they read committed JSON and touch no network, RPC, or
private key. Numbered step manifests are deliberately not required — only the
current manifest of each supported chain/environment pair.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "migration_history"

# Chain/environment pairs a retained consumer can be pointed at, with the
# contract keys that consumer resolves. Adding a chain here without committing
# its current manifest fails, which is the point.
REQUIRED_CURRENT_MANIFESTS = {
    ("base-mainnet", "v1"): ("RipeToken", "RipeHq", "GreenToken"),
    ("base-sepolia", "v1"): ("RipeToken", "RipeHq", "GreenToken"),
    ("base-sepolia", "v2"): ("RipeToken", "RipeHq", "RipeTokenPool"),
    ("robinhood-mainnet", "v1"): ("RipeToken", "RipeHq", "GreenToken"),
    ("robinhood-testnet", "v1"): ("RipeToken", "RipeHq", "GreenToken"),
    ("robinhood-testnet", "v2"): ("RipeToken", "RipeHq", "RipeTokenPool"),
}

# scripts/ccip_send.py option defaults. If these move, this pair moves with them.
CCIP_SEND_DEFAULT_CHAIN = "base-sepolia"
CCIP_SEND_DEFAULT_ENVIRONMENT = "v2"


@pytest.mark.parametrize(
    ("chain", "environment"), sorted(REQUIRED_CURRENT_MANIFESTS)
)
def test_required_current_manifest_exists_and_resolves_its_keys(
    chain, environment
):
    path = HISTORY / chain / environment / "current-manifest.json"
    assert path.is_file(), (
        f"{path.relative_to(ROOT)} is missing. A retained consumer reads it; "
        "see this module's docstring before deleting it."
    )

    contracts = json.loads(path.read_bytes())["contracts"]
    missing = [
        key
        for key in REQUIRED_CURRENT_MANIFESTS[(chain, environment)]
        if key not in contracts
    ]
    assert not missing, f"{chain}/{environment} manifest lacks {missing}"

    for key in REQUIRED_CURRENT_MANIFESTS[(chain, environment)]:
        address = contracts[key]["address"]
        assert isinstance(address, str) and address.startswith("0x")
        assert int(address, 16) != 0, f"{chain}/{environment} {key} is the zero address"


def test_ccip_send_default_target_resolves_through_its_own_helper():
    # Exercise the real lookup ccip_send performs, not a reimplementation.
    from scripts.ccip_send import _manifest

    contracts = _manifest(CCIP_SEND_DEFAULT_CHAIN, CCIP_SEND_DEFAULT_ENVIRONMENT)
    for key in ("RipeToken", "RipeHq", "RipeTokenPool"):
        assert key in contracts, (
            f"ccip_send default target {CCIP_SEND_DEFAULT_CHAIN}/"
            f"{CCIP_SEND_DEFAULT_ENVIRONMENT} cannot resolve {key}"
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
