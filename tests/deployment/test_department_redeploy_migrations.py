from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from scripts.migrate import (
    _isolate_fork_history,
    _requires_robinhood_launch_facts,
)


ROOT = Path(__file__).resolve().parents[2]
ZERO_ADDRESS = "0x" + "0" * 40


def _addr(index: int) -> str:
    return f"0x{index:040x}"


def _load(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DEPLOY = _load(
    "migrations/robinhood-mainnet/2026082100_RedeployDepartments.py",
    "full_redeploy_candidates",
)
PROMOTE = _load(
    "migrations/robinhood-mainnet/2026082101_PromoteDepartments.py",
    "full_redeploy_promotion",
)


class _Contract:
    def __init__(self, address):
        self.address = address


class _Registry(_Contract):
    def __init__(self, address, slots, *, registry_lock=0):
        super().__init__(address)
        self.slots = dict(slots)
        self.registry_lock = registry_lock

    def getAddr(self, reg_id):
        return self.slots[reg_id]

    def registryChangeTimeLock(self):
        return self.registry_lock

    def governance(self):
        return ZERO_ADDRESS


class _ActionComponent(_Contract):
    def __init__(self, address, action_lock):
        super().__init__(address)
        self.action_lock = action_lock

    def actionTimeLock(self):
        return self.action_lock

    def governance(self):
        return ZERO_ADDRESS


class _MissionControl(_Contract):
    def __init__(self, address, contributor):
        super().__init__(address)
        self.contributor = contributor

    def hrConfig(self):
        return (self.contributor, 0, 0, 0, 0, 0)


class _Psm(_Contract):
    def USDC(self):
        return _addr(800)


class _PriceDesk(_Contract):
    def ETH(self):
        return _addr(801)


class _Chainlink(_ActionComponent):
    def __init__(self, address, action_lock=0):
        super().__init__(address, action_lock)

    def WETH(self):
        return _addr(802)

    def BTC(self):
        return _addr(803)

    def feedConfig(self, asset):
        feed = _addr(804) if asset == _addr(801) else _addr(805)
        return (feed, 8, False, False, 86_400)

    def getPricedAssets(self):
        return (_addr(801), _addr(802), _addr(803), _addr(806))


class _Curve(_ActionComponent):
    ASSETS = (_addr(902), _addr(908))

    def __init__(self, address, action_lock=0):
        super().__init__(address, action_lock)

    def getPricedAssets(self):
        return self.ASSETS

    def curveConfig(self, _asset):
        return (
            _addr(908),
            _addr(908),
            2,
            (_addr(909), _addr(902), ZERO_ADDRESS, ZERO_ADDRESS),
            1,
            True,
        )

    def greenRefPoolConfig(self):
        return (
            _addr(908),
            _addr(908),
            1,
            _addr(909),
            6,
            10,
            6000,
            7200,
            7500,
            5_000_000 * 10**18,
        )


class _PromotionMigration:
    def __init__(self):
        self.deployer = _addr(900)
        self.addresses = {
            "Contributor": _addr(901),
            "GreenToken": _addr(902),
            "SavingsGreen": _addr(903),
            "RipeToken": _addr(904),
        }
        next_address = 1_000
        for name in PROMOTE.CANONICAL_SOURCE_PATHS:
            self.addresses[PROMOTE.candidate_label(name)] = _addr(next_address)
            next_address += 1

        self.hq = _Registry(
            _addr(999),
            {
                reg_id: self.addresses[PROMOTE.candidate_label(name)]
                for name, reg_id in PROMOTE.HQ_ACTIVATED
            },
        )
        self.contracts = {
            "RipeHq": self.hq,
            "EndaomentPSM": _Psm(_addr(905)),
            "PriceDesk": _PriceDesk(_addr(906)),
            "ChainlinkPrices": _Chainlink(_addr(907)),
            "CurvePrices": _Curve(_addr(908)),
        }
        for root_name, children, lock in (
            (
                "Switchboard",
                PROMOTE.SWITCHBOARD_CHILDREN,
                0,
            ),
            ("PriceDesk", PROMOTE.PRICE_SOURCE_CHILDREN, 0),
            ("VaultBook", PROMOTE.VAULT_CHILDREN, 0),
        ):
            label = PROMOTE.candidate_label(root_name)
            self.contracts[label] = _Registry(
                self.addresses[label],
                {
                    reg_id: self.addresses[PROMOTE.candidate_label(name)]
                    for name, reg_id in children
                },
                registry_lock=lock,
            )
        for name, _reg_id in PROMOTE.SWITCHBOARD_CHILDREN:
            label = PROMOTE.candidate_label(name)
            self.contracts[label] = _ActionComponent(
                self.addresses[label], 0
            )
        chainlink_label = PROMOTE.candidate_label("ChainlinkPrices")
        self.contracts[chainlink_label] = _Chainlink(
            self.addresses[chainlink_label], 0
        )
        curve_label = PROMOTE.candidate_label("CurvePrices")
        self.contracts[curve_label] = _Curve(
            self.addresses[curve_label], 0
        )
        hr_label = PROMOTE.candidate_label("HumanResources")
        self.contracts[hr_label] = _ActionComponent(
            self.addresses[hr_label], 0
        )
        mc_label = PROMOTE.candidate_label("MissionControl")
        self.contracts[mc_label] = _MissionControl(
            self.addresses[mc_label], self.addresses["Contributor"]
        )
        self.promotions = None

    def account(self):
        return self.deployer

    def get_address(self, name):
        return self.addresses[name]

    def get_contract(self, name):
        return self.contracts[name]

    def promote_candidates(self, promotions):
        self.promotions = promotions


def test_full_redeploy_boundary_is_every_hq_slot_except_tokens_and_pools():
    assert [reg_id for _name, reg_id in DEPLOY.HQ_REPLACEMENTS] == list(
        range(4, 23)
    )
    assert DEPLOY.HQ_REPLACEMENTS[0] == ("Ledger", 4)
    assert DEPLOY.HQ_REPLACEMENTS[-1] == ("EndaomentPSM", 22)
    assert {name for name, _reg_id in DEPLOY.HQ_REPLACEMENTS}.isdisjoint(
        {
            "RipeHq",
            "GreenToken",
            "SavingsGreen",
            "RipeToken",
            "GreenUsdgPool",
            "RipeCcipBurnMintTokenPool",
            "GreenCcipBurnMintTokenPool",
        }
    )


def test_full_redeploy_includes_all_active_children_and_clones_live_feeds():
    assert DEPLOY.SWITCHBOARD_CHILDREN == tuple(
        (f"Switchboard{name}", index)
        for index, name in enumerate(
            ("Alpha", "Bravo", "Charlie", "Delta", "Echo"), start=1
        )
    )
    assert DEPLOY.PRICE_SOURCE_CHILDREN == (
        ("ChainlinkPrices", 1),
        ("CurvePrices", 2),
        ("UniswapV2Prices", 3),
    )
    assert DEPLOY.VAULT_CHILDREN == (
        ("StabilityPool", 1),
        ("RipeGov", 2),
        ("SimpleErc20", 3),
    )
    source = Path(DEPLOY.__file__).read_text()
    assert "active_chainlink.getPricedAssets()" in source
    assert "active_chainlink.feedConfig(asset)" in source
    assert "active_curve.getPricedAssets()" in source
    assert "active_curve.curveConfig(asset)" in source
    assert "active_curve.greenRefPoolConfig()" in source
    assert "CHAINLINK_EXTRA_FEEDS" not in source


def test_deploy_script_has_no_old_balance_or_liquidation_gate():
    source = Path(DEPLOY.__file__).read_text()
    for forbidden in (
        "balanceOf(",
        "hasBalance(",
        "numFungLiqUsers(",
        "DEPARTMENT_REDEPLOY_ACTIVE_AUCTIONS",
    ):
        assert forbidden not in source


def test_deploy_script_uses_readable_calls_and_only_relinquishes_local_gov():
    source = Path(DEPLOY.__file__).read_text()
    assert "relinquishGov" in source
    assert "setActionTimeLockAfterSetup" not in source
    assert "setRegistryTimeLockAfterSetup" not in source
    assert "_calldata" not in source
    assert "eth_abi" not in source


def test_promotion_is_one_authenticated_32_candidate_batch():
    migration = _PromotionMigration()
    PROMOTE.migrate(migration)

    assert len(migration.promotions) == 32
    specs = {spec.canonical_name: spec for spec in migration.promotions}
    assert set(specs) == set(PROMOTE.CANONICAL_SOURCE_PATHS)
    assert specs["Ledger"].registry_id == 4
    assert specs["Ledger"].expected_constructor_args[1] == migration.get_address(
        PROMOTE.candidate_label("DefaultsRobinhoodLive")
    )
    assert specs["DefaultsRobinhoodLive"].activation_candidate_label == (
        PROMOTE.candidate_label("MissionControl")
    )
    assert specs["BondBooster"].activation_candidate_label == (
        PROMOTE.candidate_label("BondRoom")
    )
    assert specs["SwitchboardDelta"].registry_name == PROMOTE.candidate_label(
        "Switchboard"
    )
    assert specs["UniswapV2Prices"].registry_name == PROMOTE.candidate_label(
        "PriceDesk"
    )


def test_migration_helper_allows_exact_defaults_and_bond_booster_witnesses():
    from scripts.utils.migration import _DISTINCT_ACTIVATION_POLICIES

    assert (
        "DefaultsRobinhoodLive",
        "contracts/config/DefaultsRobinhoodLive.vy",
        "contracts/data/MissionControl.vy",
        "RipeHq",
        5,
        1,
    ) in _DISTINCT_ACTIVATION_POLICIES
    assert (
        "BondBooster",
        "contracts/config/BondBooster.vy",
        "contracts/core/BondRoom.vy",
        "RipeHq",
        12,
        1,
    ) in _DISTINCT_ACTIVATION_POLICIES


def test_fork_history_is_copied_outside_the_live_namespace(tmp_path):
    live = tmp_path / "live"
    live.mkdir()
    current = live / "current-manifest.json"
    current.write_text('{"contracts": {}}')

    isolated = _isolate_fork_history(live, "robinhood-mainnet")

    assert isolated != live
    assert isolated.parent.parent != live
    assert (isolated / current.name).read_bytes() == current.read_bytes()
    (isolated / "2026082100-manifest.json").write_text("fork only")
    assert not (live / "2026082100-manifest.json").exists()


@pytest.mark.parametrize("start", (None, "", "0", 0, "not-a-timestamp"))
def test_launch_or_invalid_start_requires_complete_external_facts(start):
    assert _requires_robinhood_launch_facts(start)


@pytest.mark.parametrize("start", ("2026082100", 2026082100, "0011"))
def test_forward_migration_validates_only_facts_it_consumes(start):
    assert not _requires_robinhood_launch_facts(start)
