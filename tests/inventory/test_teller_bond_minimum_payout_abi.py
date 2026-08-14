import json
from pathlib import Path

import pytest

from scripts import check_contract_artifacts as artifact_checker


ROOT = Path(__file__).resolve().parents[2]
TELLER = ROOT / "contracts/core/Teller.vy"
COMMITTED_ABI = ROOT / "scripts/abis/Teller.json"

EXPECTED_BOND_SELECTORS = {
    "purchaseRipeBond(address,uint256)": "0xc7c77bb2",
    "purchaseRipeBond(address,uint256,uint256)": "0xb1e16838",
    "purchaseRipeBond(address,uint256,uint256,address)": "0x2cf0fd55",
    "purchaseRipeBond(address,uint256,uint256,address,uint256)": "0xf464ef52",
}

EXPECTED_INPUTS = [
    "_paymentAsset:address",
    "_paymentAmount:uint256",
    "_lockDuration:uint256",
    "_recipient:address",
    "_minRipePayout:uint256",
]

D3_SIGNATURE = """def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
    _minRipePayout: uint256 = 0,
) -> uint256:
"""

VARIANT_SIGNATURES = {
    "baseline": """def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
) -> uint256:
""",
    "A": """def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
    _minRipePayout: uint256 = 0,
) -> uint256:
""",
    "D3": D3_SIGNATURE,
    "D2": """def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _recipient: address = msg.sender,
    _minRipePayout: uint256 = 0,
) -> uint256:
""",
    "D1": """def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _recipient: address,
    _minRipePayout: uint256 = 0,
) -> uint256:
""",
}

MINIMUM_ASSERTION = (
    "    assert ripePayout >= _minRipePayout"
    " # dev: minimum payout not met\n"
)

D3_ROUTE = """@nonreentrant
@external
def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
    _minRipePayout: uint256 = 0,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    paymentAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(msg.sender))
    assert extcall IERC20(_paymentAsset).transferFrom(msg.sender, a.bondRoom, paymentAmount, default_return_value=True) # dev: token transfer failed
    ripePayout: uint256 = extcall BondRoom(a.bondRoom).purchaseRipeBond(_recipient, _paymentAsset, paymentAmount, _lockDuration, msg.sender, a)
    assert ripePayout >= _minRipePayout # dev: minimum payout not met
    self._performHousekeeping(False, _recipient, True, _recipient == msg.sender, a)
    return ripePayout
"""

C1_SHARED_ROUTE = """@internal
def _purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _recipient: address,
    _minRipePayout: uint256,
    _caller: address,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    paymentAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(_caller))
    assert extcall IERC20(_paymentAsset).transferFrom(_caller, a.bondRoom, paymentAmount, default_return_value=True) # dev: token transfer failed
    ripePayout: uint256 = extcall BondRoom(a.bondRoom).purchaseRipeBond(_recipient, _paymentAsset, paymentAmount, _lockDuration, _caller, a)
    assert ripePayout >= _minRipePayout # dev: minimum payout not met
    self._performHousekeeping(False, _recipient, True, _recipient == _caller, a)
    return ripePayout


@nonreentrant
@external
def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
) -> uint256:
    return self._purchaseRipeBond(_paymentAsset, _paymentAmount, _lockDuration, _recipient, 0, msg.sender)


@nonreentrant
@external
def purchaseRipeBondWithMinPayout(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _recipient: address,
    _minRipePayout: uint256,
) -> uint256:
    return self._purchaseRipeBond(_paymentAsset, _paymentAmount, _lockDuration, _recipient, _minRipePayout, msg.sender)
"""

C2_DUPLICATED_ROUTE = """@nonreentrant
@external
def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    paymentAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(msg.sender))
    assert extcall IERC20(_paymentAsset).transferFrom(msg.sender, a.bondRoom, paymentAmount, default_return_value=True) # dev: token transfer failed
    ripePayout: uint256 = extcall BondRoom(a.bondRoom).purchaseRipeBond(_recipient, _paymentAsset, paymentAmount, _lockDuration, msg.sender, a)
    self._performHousekeeping(False, _recipient, True, _recipient == msg.sender, a)
    return ripePayout


@nonreentrant
@external
def purchaseRipeBondWithMinPayout(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _recipient: address,
    _minRipePayout: uint256,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    paymentAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(msg.sender))
    assert extcall IERC20(_paymentAsset).transferFrom(msg.sender, a.bondRoom, paymentAmount, default_return_value=True) # dev: token transfer failed
    ripePayout: uint256 = extcall BondRoom(a.bondRoom).purchaseRipeBond(_recipient, _paymentAsset, paymentAmount, _lockDuration, msg.sender, a)
    assert ripePayout >= _minRipePayout # dev: minimum payout not met
    self._performHousekeeping(False, _recipient, True, _recipient == msg.sender, a)
    return ripePayout
"""

# Compiler-bound evidence for the repository's pinned Vyper toolchain. A
# compiler bump must deliberately refresh every exact byte count below.
EXPECTED_VARIANTS = {
    "baseline": (24_460, 24_556, [1, 2, 3, 4]),
    "A_no_assert": (24_523, 24_619, [1, 2, 3, 4, 5]),
    "A": (24_536, 24_632, [1, 2, 3, 4, 5]),
    "D3_no_assert": (24_447, 24_543, [2, 3, 4, 5]),
    "D3": (24_460, 24_556, [2, 3, 4, 5]),
    "D2": (24_410, 24_506, [3, 4, 5]),
    "D1": (24_372, 24_468, [4, 5]),
}


@pytest.fixture(scope="module")
def compiled_teller():
    return artifact_checker._compile(TELLER, artifact_checker._vyper_path())


def _bond_entries(abi):
    return [entry for entry in abi if entry.get("name") == "purchaseRipeBond"]


def test_teller_bond_selector_family_is_exact(compiled_teller):
    actual = {
        signature: selector
        for signature, selector in compiled_teller.method_identifiers.items()
        if signature.startswith("purchaseRipeBond(")
    }
    assert actual == EXPECTED_BOND_SELECTORS
    assert "purchaseRipeBond(address)" not in actual


def test_teller_bond_abi_arity_and_argument_order_is_exact(compiled_teller):
    entries = _bond_entries(compiled_teller.abi)
    assert [len(entry["inputs"]) for entry in entries] == [2, 3, 4, 5]
    for entry in entries:
        actual = [
            f'{item["name"]}:{item["type"]}'
            for item in entry["inputs"]
        ]
        assert actual == EXPECTED_INPUTS[: len(actual)]


def test_committed_teller_abi_matches_compiler(compiled_teller):
    committed = json.loads(COMMITTED_ABI.read_text())
    assert artifact_checker._canonical_json_bytes(committed) == (
        artifact_checker._canonical_json_bytes(compiled_teller.abi)
    )


def test_teller_bond_candidate_size_and_selector_proofs_are_reproducible(tmp_path):
    source = TELLER.read_text()
    assert source.count(D3_SIGNATURE) == 1
    assert source.count(MINIMUM_ASSERTION) == 1

    actual = {}
    for name, expected in EXPECTED_VARIANTS.items():
        shape = name.removesuffix("_no_assert")
        variant_source = source.replace(
            D3_SIGNATURE,
            VARIANT_SIGNATURES[shape],
            1,
        )
        if shape == "baseline" or name.endswith("_no_assert"):
            variant_source = variant_source.replace(MINIMUM_ASSERTION, "", 1)

        variant_path = tmp_path / f"Teller_{name}.vy"
        variant_path.write_text(variant_source)
        compiled = artifact_checker._compile(
            variant_path,
            artifact_checker._vyper_path(),
        )
        immutable_size = sum(
            item["length"]
            for module in compiled.code_layout.values()
            for item in module.values()
        )
        arities = sorted(
            signature.count(",") + 1
            for signature in compiled.method_identifiers
            if signature.startswith("purchaseRipeBond(")
        )
        actual[name] = (
            len(compiled.runtime_template),
            len(compiled.runtime_template) + immutable_size,
            arities,
        )
        assert actual[name] == expected

    # Retaining all four legacy selectors and adding arity 5 is already 43
    # bytes over EIP-170 before the assertion. The postcondition costs another
    # 13 bytes. D3 stays under the limit only because removing arity 1 exactly
    # cancels that 13-byte cost.
    assert actual["A_no_assert"][1] - 24_576 == 43
    assert actual["A_no_assert"][0] - actual["baseline"][0] == 63
    assert actual["A"][0] - actual["A_no_assert"][0] == 13
    assert actual["D3"][0] - actual["D3_no_assert"][0] == 13
    assert actual["baseline"][0] - actual["D3_no_assert"][0] == 13


@pytest.mark.parametrize(
    "name, route, expected_template, expected_deployed",
    [
        ("C1", C1_SHARED_ROUTE, 24_632, 24_728),
        ("C2", C2_DUPLICATED_ROUTE, 24_931, 25_027),
    ],
)
def test_nonbreaking_dedicated_selector_candidates_are_measured(
    name,
    route,
    expected_template,
    expected_deployed,
    tmp_path,
):
    source = TELLER.read_text()
    assert source.count(D3_ROUTE) == 1
    variant_path = tmp_path / f"Teller_{name}.vy"
    variant_path.write_text(source.replace(D3_ROUTE, route, 1))
    compiled = artifact_checker._compile(
        variant_path,
        artifact_checker._vyper_path(),
    )
    immutable_size = sum(
        item["length"]
        for module in compiled.code_layout.values()
        for item in module.values()
    )
    bond_signatures = {
        signature: selector
        for signature, selector in compiled.method_identifiers.items()
        if signature.startswith("purchaseRipeBond")
    }
    assert {
        signature.count(",") + 1
        for signature in bond_signatures
        if signature.startswith("purchaseRipeBond(")
    } == {1, 2, 3, 4}
    assert bond_signatures[
        "purchaseRipeBondWithMinPayout(address,uint256,uint256,address,uint256)"
    ] == "0xe103d51f"
    assert (
        len(compiled.runtime_template),
        len(compiled.runtime_template) + immutable_size,
    ) == (
        expected_template,
        expected_deployed,
    )
    assert expected_deployed > 24_576
