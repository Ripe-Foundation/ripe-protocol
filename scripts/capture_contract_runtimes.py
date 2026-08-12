#!/usr/bin/env python3
"""Capture one sealed, provenance-bound RH deployed-runtime generation."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import check_contract_artifacts as checker


DEFAULT_OUTPUT = Path("/private/tmp/pr67-final-runtime-capture")
CAPTURE_SCHEMA_VERSION = 1
CAPTURE_MANIFEST = "capture-manifest.json"

ZERO = "0x0000000000000000000000000000000000000000"
HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
DEFAULTS = "0xAb7527f779B9C6F473054f9D03fF39BC2123A95C"
DEPLOYER = "0x2944fB9511f2C703a3A3bd88BB0f3b2d22a79237"
GOVERNANCE = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"

GREEN = "0x355bB7F0f6c730e4460d620420a300fa08FF82F3"
SGREEN = "0x290a52380A88f743813B8C3e9F6B0e61DB5FDF73"
RIPE = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"
WETH = "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"
CONTRIBUTOR = "0x2593D4eeEeaB39Eb5F86B76AE54C6f0F1A7cC567"
TRAINING_WHEELS = "0x987DEa46AEfA442B67Faa5Db6F71024e5be01406"
RIPE_WETH_POOL = "0xba6F6CBa1a4104000847d4fdccB676E99166CEcE"
MORPHO_V2 = "0x0FBad98595b0186dA120E41f77C102beb49f803c"
ARB_SYS = "0x0000000000000000000000000000000000000064"


def _input(name: str, abi_type: str, value: Any) -> Mapping[str, Any]:
    return {"name": name, "type": abi_type, "value": value}


CONSTRUCTOR_INPUTS: Mapping[str, Sequence[Mapping[str, Any]]] = {
    "AuctionHouse": [_input("_ripeHq", "address", HQ)],
    "BlueChipYieldPrices": [
        _input("_ripeHq", "address", HQ),
        _input("_tempGov", "address", DEPLOYER),
        _input("_minPriceChangeTimeLock", "uint256", 600),
        _input("_maxPriceChangeTimeLock", "uint256", 50_400),
        _input("_morphoAddrs", "address[2]", [ZERO, ZERO]),
        _input("_eulerAddrs", "address[2]", [ZERO, ZERO]),
        _input("_fluidAddr", "address", ZERO),
        _input("_compoundV3Addr", "address", ZERO),
        _input("_moonwellAddr", "address", ZERO),
        _input("_aaveV3Addr", "address", ZERO),
        _input("_morphoV2Addr", "address", MORPHO_V2),
    ],
    "CreditEngine": [_input("_ripeHq", "address", HQ)],
    "DefaultsRobinhood": [
        _input("_contribTemplate", "address", CONTRIBUTOR),
        _input("_trainingWheels", "address", TRAINING_WHEELS),
        _input("_ripeToken", "address", RIPE),
        _input("_greenToken", "address", GREEN),
        _input("_sgreenToken", "address", SGREEN),
        _input("_usdgToken", "address", USDG),
        _input("_wethToken", "address", WETH),
    ],
    "Deleverage": [
        _input("_ripeHq", "address", HQ),
        _input("_minDeleverageBps", "uint256", 0),
        _input("_deleverageBuffer", "uint256", 0),
        _input("_deleverageCooldown", "uint256", 0),
        _input("_underscoreSafeSpreadBps", "uint256", 100),
        _input("_deleverageFullPayoffBuffer", "uint256", 10**15),
        _input("_deleverageOverageBps", "uint256", 100),
        _input("_deleverageDustThreshold", "uint256", 0),
        _input("_deleverageDustBps", "uint256", 0),
    ],
    "Ledger": [
        _input("_ripeHq", "address", HQ),
        _input("_defaults", "address", DEFAULTS),
        _input("_actionBlockSource", "address", ARB_SYS),
    ],
    "Lootbox": [
        _input("_ripeHq", "address", HQ),
        _input("_minUnderscoreSendInterval", "uint256", 1),
        _input("_underscoreSendInterval", "uint256", 0),
        _input("_undyDepositRewardsAmount", "uint256", 0),
        _input("_undyYieldBonusAmount", "uint256", 0),
    ],
    "MissionControl": [
        _input("_ripeHq", "address", HQ),
        _input("_defaults", "address", DEFAULTS),
    ],
    "RipeGov": [_input("_ripeHq", "address", HQ)],
    "SimpleErc20": [_input("_ripeHq", "address", HQ)],
    "StabilityPool": [_input("_ripeHq", "address", HQ)],
    "SwitchboardAlpha": [
        _input("_ripeHq", "address", HQ),
        _input("_tempGov", "address", DEPLOYER),
        _input("_minStaleTime", "uint256", 300),
        _input("_maxStaleTime", "uint256", 604_800),
        _input("_minConfigTimeLock", "uint256", 600),
        _input("_maxConfigTimeLock", "uint256", 50_400),
    ],
    "SwitchboardBravo": [
        _input("_ripeHq", "address", HQ),
        _input("_tempGov", "address", DEPLOYER),
        _input("_minConfigTimeLock", "uint256", 600),
        _input("_maxConfigTimeLock", "uint256", 50_400),
    ],
    "SwitchboardCharlie": [
        _input("_ripeHq", "address", HQ),
        _input("_tempGov", "address", DEPLOYER),
        _input("_minConfigTimeLock", "uint256", 600),
        _input("_maxConfigTimeLock", "uint256", 50_400),
    ],
    "SwitchboardDelta": [
        _input("_ripeHq", "address", HQ),
        _input("_tempGov", "address", ZERO),
        _input("_minConfigTimeLock", "uint256", 600),
        _input("_maxConfigTimeLock", "uint256", 50_400),
    ],
    "Teller": [
        _input("_ripeHq", "address", HQ),
        _input("_shouldPause", "bool", True),
    ],
    "UniswapV2Prices": [
        _input("_ripeHq", "address", HQ),
        _input("_ripeWethPool", "address", RIPE_WETH_POOL),
        _input("_ripeToken", "address", RIPE),
        _input("_wethToken", "address", WETH),
    ],
    "VaultMigrator": [
        _input("_ripeHq", "address", HQ),
        _input("_shouldPause", "bool", False),
        _input("_legacyRipeGovVault", "address", ZERO),
    ],
}


def _prospective(
    *,
    initial: Mapping[str, Any] | None = None,
    post_deploy_actions: Sequence[str] = (),
    required_readbacks: Sequence[str] = (),
) -> Mapping[str, Any]:
    return {
        "initial": dict(initial or {}),
        "post_deploy_actions": list(post_deploy_actions),
        "required_readbacks": list(required_readbacks),
        "runtime_identity_limit": (
            "deployed runtime binds code and immutable code-data only; "
            "storage and post-deploy state require executor receipt/readbacks"
        ),
    }


_FINALIZE_LOCAL_GOV = (
    "setActionTimeLockAfterSetup(600)",
    "relinquishGov()",
)
PROSPECTIVE_STATE: Mapping[str, Mapping[str, Any]] = {
    "AuctionHouse": _prospective(required_readbacks=(f"getRipeHq()=={HQ}",)),
    "BlueChipYieldPrices": _prospective(
        initial={"governance": DEPLOYER, "actionTimeLock": 0},
        post_deploy_actions=_FINALIZE_LOCAL_GOV,
        required_readbacks=("governance()==0x0", "actionTimeLock()==600"),
    ),
    "CreditEngine": _prospective(required_readbacks=(f"getRipeHq()=={HQ}",)),
    "DefaultsRobinhood": _prospective(),
    "Deleverage": _prospective(
        initial={
            "minDeleverageBps": 0,
            "deleverageBuffer": 0,
            "deleverageCooldown": 0,
            "underscoreSafeSpreadBps": 100,
            "deleverageFullPayoffBuffer": 10**15,
            "deleverageOverageBps": 100,
            "deleverageDustThreshold": 0,
            "deleverageDustBps": 0,
        },
        required_readbacks=("all eight Deleverage policy getters",),
    ),
    "Ledger": _prospective(
        initial={"defaults": DEFAULTS, "actionBlockSource": ARB_SYS},
        required_readbacks=(
            f"getRipeHq()=={HQ}",
            f"ACTION_BLOCK_SOURCE()=={ARB_SYS}",
            "getArbActionBlock() through the Robinhood RPC",
        ),
    ),
    "Lootbox": _prospective(
        initial={
            "minUnderscoreSendInterval": 1,
            "underscoreSendInterval": 0,
            "hasUnderscoreRewards": False,
        },
        required_readbacks=("Underscore rewards remain disabled",),
    ),
    "MissionControl": _prospective(
        initial={"defaults": DEFAULTS},
        required_readbacks=(
            f"getRipeHq()=={HQ}",
            "Defaults-derived configuration equals the approved live snapshot",
        ),
    ),
    "RipeGov": _prospective(required_readbacks=(f"getRipeHq()=={HQ}",)),
    "SimpleErc20": _prospective(required_readbacks=(f"getRipeHq()=={HQ}",)),
    "StabilityPool": _prospective(required_readbacks=(f"getRipeHq()=={HQ}",)),
    "SwitchboardAlpha": _prospective(
        initial={"governance": DEPLOYER, "actionTimeLock": 0},
        post_deploy_actions=_FINALIZE_LOCAL_GOV,
        required_readbacks=("governance()==0x0", "actionTimeLock()==600"),
    ),
    "SwitchboardBravo": _prospective(
        initial={"governance": DEPLOYER, "actionTimeLock": 0},
        post_deploy_actions=_FINALIZE_LOCAL_GOV,
        required_readbacks=("governance()==0x0", "actionTimeLock()==600"),
    ),
    "SwitchboardCharlie": _prospective(
        initial={"governance": DEPLOYER, "actionTimeLock": 0},
        post_deploy_actions=_FINALIZE_LOCAL_GOV,
        required_readbacks=("governance()==0x0", "actionTimeLock()==600"),
    ),
    "SwitchboardDelta": _prospective(
        initial={"governance": ZERO, "actionTimeLock": 0},
        post_deploy_actions=("RipeHq governance sets actionTimeLock to 600",),
        required_readbacks=("governance()==0x0", "actionTimeLock()==600"),
    ),
    "Teller": _prospective(
        initial={"isPaused": True},
        required_readbacks=("isPaused()==True",),
    ),
    "UniswapV2Prices": _prospective(
        initial={"isMonitoringOnly": True, "actionTimeLock": 0},
        required_readbacks=(
            "isMonitoringOnly()==True",
            "RIPE/WETH immutable identities match constructor inputs",
            "getPriceAndHasFeed(RIPE)==(0,False)",
        ),
    ),
    "VaultMigrator": _prospective(
        initial={"isPaused": False, "legacyRipeGovVault": ZERO},
        required_readbacks=("isPaused()==False", f"LEGACY_RIPE_GOV_VAULT()=={ZERO}"),
    ),
}


def _json_value(value: Any) -> Any:
    return json.loads(checker._canonical_json_bytes(value))


def expected_capture_provenance() -> Mapping[str, Mapping[str, Any]]:
    if set(CONSTRUCTOR_INPUTS) != checker.DEPLOYED_RUNTIME_CONTRACTS:
        raise checker.ArtifactCheckError(
            "capture constructor-input census does not match the exact runtime set"
        )
    if set(PROSPECTIVE_STATE) != checker.DEPLOYED_RUNTIME_CONTRACTS:
        raise checker.ArtifactCheckError(
            "capture prospective-state census does not match the exact runtime set"
        )

    records = {}
    for name in sorted(checker.DEPLOYED_RUNTIME_CONTRACTS):
        inputs = _json_value(CONSTRUCTOR_INPUTS[name])
        prospective_state = _json_value(PROSPECTIVE_STATE[name])
        records[name] = {
            "source_path": checker.GOVERNED_SOURCES[name],
            "constructor_inputs": inputs,
            "constructor_inputs_sha256": checker._json_sha256(inputs),
            "prospective_state": prospective_state,
            "prospective_state_sha256": checker._json_sha256(prospective_state),
        }
    return records


def _constructor_values(name: str) -> list[Any]:
    return [entry["value"] for entry in CONSTRUCTOR_INPUTS[name]]


def _git(*arguments: str) -> str:
    return checker._run(["git", *arguments], cwd=ROOT).strip()


def _require_capture_context(output: Path) -> Mapping[str, str]:
    if Path.cwd().resolve() != ROOT.resolve():
        raise checker.ArtifactCheckError(
            f"capture must run from the repository root: {ROOT}"
        )
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise checker.ArtifactCheckError("capture output must remain outside the repository")
    if output.exists():
        raise checker.ArtifactCheckError(
            f"capture output already exists; use a fresh path: {output}"
        )

    source_status = _git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        "contracts",
        "interfaces",
    )
    if source_status:
        raise checker.ArtifactCheckError(
            "capture requires clean tracked and untracked contract/interface sources: "
            + source_status.replace("\n", "; ")
        )
    return {
        "root": str(ROOT.resolve()),
        "head": _git("rev-parse", "HEAD^{commit}"),
        "tree": _git("rev-parse", "HEAD^{tree}"),
        "source_status": source_status,
    }


def _deploy_graph():
    import boa
    from boa.interpret import set_cache_dir

    cache_dir = os.environ.get("RIPE_AUDIT_CACHE")
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        set_cache_dir(cache_dir)

    boa.env.eoa = DEPLOYER
    # RipeHq's constructor validates that its three seed registry addresses
    # already contain code. Their behavior is irrelevant to runtime capture;
    # install minimal deterministic code at the exact constructor addresses.
    seed_source = "# @version 0.4.3\n\n@deploy\ndef __init__():\n    pass\n"
    for label, address in (("green", GREEN), ("sgreen", SGREEN), ("ripe", RIPE)):
        boa.loads(
            seed_source,
            name=f"runtime_capture_{label}_seed",
            override_address=address,
        )
    boa.load(
        "contracts/registries/RipeHq.vy",
        GREEN,
        SGREEN,
        RIPE,
        GOVERNANCE,
        3_600,
        50_400,
        3_600,
        50_400,
        override_address=HQ,
    )
    boa.load(
        "contracts/config/DefaultsRobinhoodLive.vy",
        override_address=DEFAULTS,
    )
    pair = boa.load(
        "contracts/mock/MockUniswapV2Pair.vy",
        override_address=RIPE_WETH_POOL,
    )
    pair.configureIdentity(ZERO, WETH, RIPE)

    deployed = {}
    for index, name in enumerate(sorted(checker.DEPLOYED_RUNTIME_CONTRACTS), 1):
        deployed[name] = boa.load(
            checker.GOVERNED_SOURCES[name],
            *_constructor_values(name),
            override_address=f"0x{0xC000 + index:040x}",
        )
    return boa, deployed


def _fsync_directory(path: Path) -> None:
    directory_fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def capture(output: Path) -> Path:
    repository = _require_capture_context(output)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            dir=output.parent,
            prefix=f".{output.name}.capture-",
        )
    )
    stage.chmod(0o700)
    try:
        boa, deployed = _deploy_graph()
        provenance = expected_capture_provenance()
        records = {}
        for name in sorted(checker.DEPLOYED_RUNTIME_CONTRACTS):
            runtime = bytes(boa.env.get_code(deployed[name].address))
            if not runtime:
                raise checker.ArtifactCheckError(f"{name}: empty deployed runtime")
            runtime_name = f"{name}.runtime"
            checker._atomic_write_bytes(stage / runtime_name, runtime)
            source = ROOT / checker.GOVERNED_SOURCES[name]
            records[name] = {
                **provenance[name],
                "source_sha256": checker._sha256(source.read_bytes()),
                "runtime_file": runtime_name,
                "runtime_sha256": checker._sha256(runtime),
                "runtime_size": len(runtime),
            }

        expected_runtime_files = {
            f"{name}.runtime" for name in checker.DEPLOYED_RUNTIME_CONTRACTS
        }
        actual_runtime_files = {path.name for path in stage.iterdir()}
        if actual_runtime_files != expected_runtime_files:
            raise checker.ArtifactCheckError(
                "capture runtime-file census mismatch before completion"
            )

        manifest = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "status": "complete",
            "repository": repository,
            "capture_script": {
                "path": "scripts/capture_contract_runtimes.py",
                "sha256": checker._sha256(Path(__file__).read_bytes()),
            },
            "toolchain": {
                "python": os.path.realpath(os.sys.executable),
                "titanoboa": importlib.metadata.version("titanoboa"),
                "vyper": checker._run(
                    [str(checker._vyper_path()), "--version"]
                ).strip(),
            },
            "governed_contracts": sorted(checker.GOVERNED_CONTRACTS),
            "runtime_contracts": sorted(checker.DEPLOYED_RUNTIME_CONTRACTS),
            "template_identity_contracts": ["DefaultsRobinhoodLive"],
            "contracts": records,
        }
        checker._atomic_write_bytes(
            stage / CAPTURE_MANIFEST,
            json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n",
        )
        expected_complete_files = expected_runtime_files | {CAPTURE_MANIFEST}
        if {path.name for path in stage.iterdir()} != expected_complete_files:
            raise checker.ArtifactCheckError(
                "capture output census mismatch after completion"
            )
        _fsync_directory(stage)
        os.replace(stage, output)
        _fsync_directory(output.parent)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    print(
        f"captured {len(checker.DEPLOYED_RUNTIME_CONTRACTS)} runtimes "
        f"and {CAPTURE_MANIFEST} in {output}"
    )
    return output / CAPTURE_MANIFEST


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"fresh output directory outside the repository (default: {DEFAULT_OUTPUT})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        capture(args.output_dir)
    except (checker.ArtifactCheckError, OSError, ValueError) as exc:
        print(f"RUNTIME_CAPTURE_FAILED: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
