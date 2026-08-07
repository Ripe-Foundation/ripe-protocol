from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.export_abis import AbiExportError, _compile_abi, check_abis, export_abis


ROOT = Path(__file__).resolve().parents[2]
SOURCE = """# @version 0.4.3
@external
def answer() -> uint256:
    return 42
"""


def make_contracts(tmp_path: Path) -> Path:
    contracts = tmp_path / "contracts"
    (contracts / "a").mkdir(parents=True)
    (contracts / "b").mkdir()
    (contracts / "a" / "Alpha.vy").write_text(SOURCE)
    (contracts / "b" / "Beta.vy").write_text(SOURCE)
    return contracts


def test_two_clean_exports_have_identical_bytes_and_sorted_outputs(tmp_path):
    contracts = make_contracts(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_report = export_abis(contracts, first)
    second_report = export_abis(contracts, second)

    assert [path.name for path in first_report.exported] == [
        "Alpha.json",
        "Beta.json",
    ]
    assert {
        path.name: path.read_bytes() for path in first_report.exported
    } == {
        path.name: path.read_bytes() for path in second_report.exported
    }
    assert all(not path.read_bytes().endswith(b"\n") for path in first_report.exported)


def test_output_collision_fails_before_writing(tmp_path):
    contracts = make_contracts(tmp_path)
    (contracts / "b" / "Alpha.vy").write_text(SOURCE)
    output = tmp_path / "abis"

    with pytest.raises(AbiExportError, match="ABI output collision"):
        export_abis(contracts, output)
    assert not output.exists()


def test_compile_failure_is_nonzero_and_writes_nothing(tmp_path):
    contracts = make_contracts(tmp_path)
    (contracts / "a" / "Alpha.vy").write_text("not valid vyper")
    output = tmp_path / "abis"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_abis.py",
            "--contracts-dir",
            str(contracts),
            "--output-dir",
            str(output),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "ABI_EXPORT_FAILED" in result.stderr
    assert not output.exists()


def test_missing_changed_and_stale_outputs_are_detected(tmp_path):
    contracts = make_contracts(tmp_path)
    output = tmp_path / "abis"
    export_abis(contracts, output)

    (output / "Alpha.json").unlink()
    with pytest.raises(AbiExportError, match="missing ABI output: Alpha.json"):
        check_abis(contracts, output)

    export_abis(contracts, output)
    (output / "Alpha.json").write_text("[]\n")
    with pytest.raises(AbiExportError, match="changed ABI output: Alpha.json"):
        check_abis(contracts, output)

    export_abis(contracts, output)
    (output / "Stale.json").write_text("[]\n")
    with pytest.raises(AbiExportError, match="stale ABI output: Stale.json"):
        check_abis(contracts, output)
    with pytest.raises(AbiExportError, match="stale ABI output"):
        export_abis(contracts, output)


def test_explicit_legacy_output_is_exact_hash_bound(tmp_path):
    contracts = make_contracts(tmp_path)
    output = tmp_path / "abis"
    export_abis(contracts, output)
    legacy = output / "Legacy.json"
    legacy.write_bytes(b"[]")
    frozen = {"Legacy.json": hashlib.sha256(legacy.read_bytes()).hexdigest()}

    assert len(check_abis(contracts, output, legacy_output_sha256=frozen).exported) == 3
    legacy.write_bytes(b"[{}]")
    with pytest.raises(AbiExportError, match="changed legacy ABI output"):
        check_abis(contracts, output, legacy_output_sha256=frozen)


def test_mock_and_testing_sources_are_excluded_but_standalone_modules_export(tmp_path):
    contracts = make_contracts(tmp_path)
    for directory in ("mock", "testing", "modules"):
        (contracts / directory).mkdir()
        (contracts / directory / f"{directory.title()}.vy").write_text(SOURCE)
    output = tmp_path / "abis"

    report = export_abis(contracts, output)
    assert {path.name for path in report.exported} == {
        "Alpha.json",
        "Beta.json",
        "Modules.json",
    }
    assert {path.parent.name for path in report.skipped} == {"mock", "testing"}


def test_solidity_input_is_explicitly_unsupported(tmp_path):
    contracts = make_contracts(tmp_path)
    (contracts / "a" / "Unsupported.sol").write_text("contract Unsupported {}")

    with pytest.raises(AbiExportError, match="unsupported Solidity ABI input"):
        export_abis(contracts, tmp_path / "abis")


def test_repository_default_abi_directory_is_byte_current():
    # 53, not 52: rh added contracts/config/DefaultsRobinhoodLive.vy without
    # exporting its ABI, which left this parity check red on rh itself. The
    # missing scripts/abis/DefaultsRobinhoodLive.json is exported here, so the
    # census is one larger. The 52 ABIs present at 610b43f are all retained; the
    # simplification cleanup removes no ABI.
    report = check_abis(ROOT / "contracts", ROOT / "scripts" / "abis")
    assert len(report.exported) == 53
    exported_names = {path.name for path in report.exported}
    assert exported_names >= {
        "Addys.json",
        "Contributor.json",
        "DefaultsRobinhood.json",
        "Erc20Token.json",
        "LocalGov.json",
        "UniswapV2Prices.json",
    }
    assert "GuardedErc20.json" not in exported_names
    assert "DefaultsBaseSepolia.json" in {
        path.name for path in report.exported
    }
    assert {
        path.relative_to(ROOT / "contracts").as_posix()
        for path in report.skipped
        if "modules" in path.relative_to(ROOT / "contracts").parts
    } == {
        "modules/DeptBasics.vy",
        "modules/TimeLock.vy",
        "priceSources/modules/PriceSourceData.vy",
        "registries/modules/AddressRegistry.vy",
        "tokens/modules/Erc4626Token.vy",
        "vaults/modules/BasicVault.vy",
        "vaults/modules/SharesVault.vy",
        "vaults/modules/StabVault.vy",
        "vaults/modules/VaultData.vy",
    }


def test_uniswap_v2_abi_is_independently_byte_current_and_old_abi_is_absent():
    contracts = ROOT / "contracts"
    source = contracts / "priceSources" / "UniswapV2Prices.vy"
    abi = ROOT / "scripts" / "abis" / "UniswapV2Prices.json"
    assert abi.read_bytes() == _compile_abi(source, contracts)
    assert not (
        ROOT / "scripts" / "abis" / "RobinhoodUniswapV2RipePrices.json"
    ).exists()
