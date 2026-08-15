#!/usr/bin/env python3
"""Measure Curve green-ring paths with fresh EVM access counters."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import boa
from boa.interpret import set_cache_dir


ROOT = Path(__file__).resolve().parents[1]
ZERO = "0x0000000000000000000000000000000000000000"
E18 = 10**18


def _deploy(source: Path, capacity: int, stale_blocks: int):
    governance = boa.env.generate_address()
    snapshotter = boa.env.generate_address()
    green = boa.load(
        ROOT / "contracts/mock/MockErc20.vy",
        governance,
        "GREEN",
        "GREEN",
        18,
        1,
    )
    alt = boa.load(
        ROOT / "contracts/mock/MockErc20.vy",
        governance,
        "ALT",
        "ALT",
        18,
        1,
    )
    pool = boa.load(ROOT / "contracts/mock/MockCurveRefPool.vy")
    registry = boa.load(
        ROOT / "contracts/mock/MockCurveRefPoolRegistry.vy",
        governance,
        green,
        alt,
        pool,
    )
    registry.setPool(pool, alt, green)
    registry.setValidRipeAddr(snapshotter, True)
    pool.setBalances(50 * E18, 50 * E18)
    curve = boa.load(
        source,
        registry,
        ZERO,
        registry,
        green,
        alt,
        1,
        100,
    )
    curve.setActionTimeLockAfterSetup(sender=governance)
    action_id = curve.setGreenRefPoolConfig(
        pool,
        capacity,
        60_00,
        stale_blocks,
        10_00,
        100_000 * E18,
        sender=governance,
    )
    boa.env.time_travel(blocks=1)
    assert curve.confirmGreenRefPoolConfig(action_id, sender=governance)
    return curve, pool, governance, snapshotter


def _fill(curve, snapshotter, total: int) -> None:
    for _ in range(total - 1):
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)


def _reset_access_counters() -> None:
    # Direct Boa calls retain warmed storage across calls. This private py-evm
    # hook is intentionally confined to the standalone evidence script because
    # it is incompatible with pytest's snapshot-isolation checkpoints.
    boa.env.evm.vm.state._account_db._reset_access_counters()


def measure(source: Path) -> dict[str, int]:
    result: dict[str, int] = {}

    curve, _, _, snapshotter = _deploy(source, 100, 0)
    _fill(curve, snapshotter, 10)
    _reset_access_counters()
    curve.getCurrentGreenPoolStatus()
    result["view_partial_10_all_fresh"] = curve._computation.get_gas_used()

    curve, pool, governance, snapshotter = _deploy(source, 100, 0)
    _fill(curve, snapshotter, 100)
    _reset_access_counters()
    curve.getCurrentGreenPoolStatus()
    result["view_full_100_all_fresh"] = curve._computation.get_gas_used()

    boa.env.time_travel(blocks=1)
    _reset_access_counters()
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    result["add_snapshot_full_100"] = curve._computation.get_gas_used()

    for _ in range(19):
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    _reset_access_counters()
    curve.getCurrentGreenPoolStatus()
    result["view_wrapped_100_all_fresh"] = curve._computation.get_gas_used()

    action_id = curve.setGreenRefPoolConfig(
        pool,
        99,
        60_00,
        0,
        10_00,
        100_000 * E18,
        sender=governance,
    )
    boa.env.time_travel(blocks=1)
    _reset_access_counters()
    assert curve.confirmGreenRefPoolConfig(action_id, sender=governance)
    result["confirm_clear_100_and_reseed"] = curve._computation.get_gas_used()

    curve, _, _, snapshotter = _deploy(source, 100, 10)
    _fill(curve, snapshotter, 100)
    boa.env.time_travel(blocks=8)
    _reset_access_counters()
    curve.getCurrentGreenPoolStatus()
    result["view_full_100_mostly_stale"] = curve._computation.get_gas_used()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "contracts/priceSources/CurvePrices.vy",
    )
    args = parser.parse_args()

    if cache_dir := os.environ.get("RIPE_BOA_CACHE_DIR"):
        set_cache_dir(cache_dir)
    print(json.dumps(measure(args.source.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
