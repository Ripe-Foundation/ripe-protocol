from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import boa

from config import BluePrint as source_blueprint
from scripts.utils.robinhood_backends import (
    BoaRobinhoodBackend,
    CURVE_ADDRESS_PROVIDER_ABI,
    CURVE_STABLESWAP_NG_FACTORY_ABI,
    DeterministicRobinhoodBackend,
    LOCAL_GOVERNANCE_REFERENCES,
    ZERO_ADDRESS,
)
from scripts.utils.robinhood_executor import (
    EXPECTED_NAMESPACE_COUNTS,
    EXPECTED_OPERATION_VOCABULARY,
    EXPECTED_STAGE_IDS,
    RobinhoodStageExecutor,
)
from tests.deployment.robinhood_execution_support import (
    MigrationHandoff,
    TEMPORARY_GOVERNANCE,
    bound_mainnet_plan,
    build_bound_plan,
    committed_execution_root,
)


def _execute(plan, root):
    backend = DeterministicRobinhoodBackend()
    executor = RobinhoodStageExecutor(plan, repository_root=root, backend=backend)
    migration = MigrationHandoff()
    for stage in plan["stages"]:
        executor(migration, stage)
    return executor, backend, migration


def test_fully_bound_production_plan_executes_exact_shared_source(
    committed_execution_root, bound_mainnet_plan
):
    root = committed_execution_root
    plan = bound_mainnet_plan
    assert plan["status"] == "complete"
    assert plan["plan_hash"] is not None
    assert plan["artifact"]["executable"] is True
    accepted_temporary_governance = plan["execution_envelope"]["values"][
        "binding:temporary-local-governance"
    ]
    assert accepted_temporary_governance["type"] == "address"
    assert accepted_temporary_governance["value"] == TEMPORARY_GOVERNANCE
    assert accepted_temporary_governance["authority_ref"]
    assert accepted_temporary_governance["evidence_sha256"]
    assert tuple(stage["migration_id"] for stage in plan["stages"]) == EXPECTED_STAGE_IDS
    actions = [action for stage in plan["stages"] for action in stage["actions"]]
    assert len(actions) == 119
    assert Counter(action["kind"] for action in actions)["deployment"] == 38
    assert Counter(action["kind"] for action in actions)["registration"] == 33
    assert {action["operation"] for action in actions} == EXPECTED_OPERATION_VOCABULARY

    executor, backend, migration = _execute(plan, root)
    assert len(executor.results) == len(migration.results) == 119
    assert len(backend.deployments) == 38
    assert sum(len(rows) for rows in backend.registries.values()) == 33
    assert backend.sequence[-1] == "0900:000005:handoff-governance-and-relinquish-deployer"
    assert backend.handed_off is True
    assert all(count == 1 for count in backend.mutation_counts.values())
    for action in actions:
        evidence = executor.results[action["action_id"]][
            "execution_evidence"
        ]
        assert [row["reference"] for row in evidence["outputs"]] == sorted(
            action.get("provides", ())
        )

    deployed = executor.results["0100:000003:deploy-ripe-hq"]["execution_evidence"]
    ledger = executor.results["0200:000000:deploy-ledger"]["execution_evidence"]
    ripe_hq = deployed["deployed_address"]
    assert any(
        item["reference"] == "address:RIPE_HQ"
        and ripe_hq in item["canonical_value"]
        and item["provenance"] == "same-execution-deployment"
        for item in ledger["inputs"]
    )
    assert executor.results["0400:000007:register-chainlink-prices"]["execution_evidence"]["registry_id"] == 1
    assert executor.results["0400:000009:register-curve-prices"]["execution_evidence"]["registry_id"] == 2
    assert executor.results["0400:000013:register-blue-chip-yield-prices"]["execution_evidence"]["registry_id"] == 3
    curve_constructor = executor.results[
        "0400:000004:deploy-curve-prices-unregistered"
    ]["execution_evidence"]
    curve_values = {
        item["reference"]: item["canonical_value"]
        for item in curve_constructor["inputs"]
        if item["reference"].startswith("curve-binding:")
    }
    assert curve_values == {
        "curve-binding:_minPriceChangeTimeLock": "21600",
        "curve-binding:_maxPriceChangeTimeLock": "302400",
    }
    handoff = executor.results[
        "0900:000005:handoff-governance-and-relinquish-deployer"
    ]["execution_evidence"]
    assert "binding:temporary-local-governance" in {
        item["reference"] for item in handoff["inputs"]
    }
    assert [
        item["contract_reference"]
        for item in handoff["authority_relinquishments"]
    ] == list(LOCAL_GOVERNANCE_REFERENCES)
    final_governance = plan["execution_envelope"]["values"][
        "input:Deployment.DP-18.roles.governance"
    ]["value"].lower()
    assert backend.hq_governance == final_governance
    # Departments never hold local governance -- RipeHq governance is the
    # deployer, and LocalGov asserts `_initialGov != hqGov`. Every relinquishment
    # is therefore VACUOUS: a receipt is still recorded, in sequence, so the
    # evidence trail stays complete, but it carries no transaction identity and
    # no state mutation because nothing was sent on chain.
    for sequence, receipt in enumerate(
        handoff["authority_relinquishments"]
    ):
        assert receipt["sequence"] == sequence
        assert receipt["status"] == "complete"
        assert receipt["transaction_identity"] is None
        assert receipt["temporary_governance_before"] == ZERO_ADDRESS
        assert receipt["local_governance_after"] == ZERO_ADDRESS
        assert receipt["ripe_hq_governance_after"] == final_governance
        assert receipt["temporary_can_govern_after"] is False
        assert receipt["final_can_govern_after"] is True
        assert receipt["failure_classification"] is None
    assert handoff["retained_temporary_governance"] == []
    assert set(backend.local_governance.values()) == {ZERO_ADDRESS}
    # No relinquishment transaction was sent, so nothing may be counted as a
    # mutation. A non-empty count here would mean the manifest is claiming
    # writes that never happened.
    assert backend.relinquishment_mutation_counts == {}


def test_temporary_local_governance_constructor_census_is_exact(
    committed_execution_root,
    bound_mainnet_plan,
):
    def artifacts_taking(binding):
        return [
            action["artifact"]
            for stage in bound_mainnet_plan["stages"]
            for action in stage["actions"]
            if binding in action.get("constructor", ())
        ]

    # The temporary deployer is governance for the tokens and RipeHq only,
    # matching Base: it holds authority until the single irreversible handoff
    # in 0900.
    assert artifacts_taking("binding:temporary-local-governance") == [
        "GreenToken",
        "RipeToken",
        "SavingsGreen",
        "RipeHq",
    ]

    # Every department deploys with NO local governance. It cannot take the
    # deployer, because LocalGov asserts `_initialGov != hqGov` and RipeHq
    # governance is the deployer. They remain governable throughout, since
    # LocalGov._getGovernors() also returns RipeHq governance.
    #
    # This is also the exact set of contracts whose Vyper source accepts a
    # _tempGov constructor parameter, asserted against source below.
    expected = [
        "Switchboard",
        "SwitchboardAlpha",
        "SwitchboardBravo",
        "SwitchboardCharlie",
        "SwitchboardDelta",
        "SwitchboardEcho",
        "PriceDesk",
        "ChainlinkPrices",
        "CurvePrices",
        "BlueChipYieldPrices",
        "VaultBook",
    ]
    assert artifacts_taking("binding:no-local-governance") == expected

    production_files = _production_files(committed_execution_root)
    deployed_artifacts = [
        action["artifact"]
        for stage in bound_mainnet_plan["stages"]
        for action in stage["actions"]
        if action["kind"] == "deployment"
    ]
    constructor_census = [
        artifact
        for artifact in deployed_artifacts
        if re.search(
            r"gov\.__init__\(\s*_ripeHq,\s*_tempGov\b",
            Path(production_files[artifact]).read_text(encoding="utf-8"),
        )
    ]
    assert constructor_census == expected
    assert "gov.__init__(_ripeHq, empty(address)" in Path(
        production_files["HumanResources"]
    ).read_text(encoding="utf-8")


def test_profiles_share_source_but_bind_isolated_plan_and_history_identities(
    committed_execution_root, bound_mainnet_plan
):
    root = committed_execution_root
    mainnet = bound_mainnet_plan
    testnet = build_bound_plan(root, "robinhood-testnet")
    assert mainnet["source"]["source_digest"] == testnet["source"]["source_digest"]
    assert mainnet["plan_hash"] != testnet["plan_hash"]
    assert mainnet["profile"]["expected_chain_id"] == 4663
    assert testnet["profile"]["expected_chain_id"] == 46630
    assert EXPECTED_NAMESPACE_COUNTS == {
        "action": 9,
        "address": 147,
        "binding": 58,
        "blueprint": 6,
        "curve": 45,
        "curve-binding": 2,
        "defaults": 7,
        "input": 72,
        "input-prefix": 2,
        "registry": 36,
        "stock": 16,
    }


def test_nonlaunch_surfaces_remain_nonexecuting_and_absent(
    committed_execution_root, bound_mainnet_plan
):
    root = committed_execution_root
    plan = bound_mainnet_plan
    executor, backend, _ = _execute(plan, root)
    assert plan["deferred_stages"] == [
        {
            "migration_id": "1000",
            "semantic_id": "ccip-pools-and-registration",
            "reason": "ccip-deferred-outside-launch-graph",
        }
    ]
    assert not any("uniswap" in item.casefold() for item in backend.deployments)
    assert "address:GREEN_USDG_LP" not in backend.deployments
    assert "address:RIPE_WETH_LP" not in backend.deployments
    assert executor.results["0500:000010:preserve-stock-extension-seam"]["transaction"]["required"] is False
    assert executor.results["0800:000002:omit-psm-activation"]["transaction"]["required"] is False


def _production_files(root: Path) -> dict[str, str]:
    files = {}
    for parent in (root / "contracts", root / "interfaces"):
        for path in parent.rglob("*.vy"):
            if "testing" not in path.parts:
                files[path.stem] = str(path)
    return files


def _local_contract(source: str, *, name: str):
    return boa.loads(source, name=name)


def test_fresh_local_evm_deploys_actual_production_protocol_components(
    committed_execution_root,
):
    root = committed_execution_root
    with boa.env.anchor():
        final_governance = _local_contract(
            """# @version 0.4.3
@external
def authority_marker():
    pass
""",
            name="robinhood_final_governance",
        )
        temporary_governance = _local_contract(
            """# @version 0.4.3
@external
def deployment_authority_marker():
    pass
""",
            name="robinhood_temporary_local_governance",
        )
        sender = temporary_governance.address
        final_sender = final_governance.address
        boa.env.set_balance(sender, 10**24)
        mock_erc20 = root / "contracts/mock/MockErc20.vy"
        mock_feed = root / "contracts/mock/MockChainlinkFeed.vy"
        # The deployer must hold the USDG it seeds the pool with, exactly as on
        # the real chain. MockErc20 credits `_supply * 10 ** decimals` to the
        # deployer, and the approved seed is 100 USDG (6dp), so pass 100 whole
        # units. Leaving this at 0 makes the seed action fail closed with
        # RHX_SEED_FUNDING_INSUFFICIENT, which is the guard working, not a bug.
        seed_usdg, _seed_green = next(
            row.value
            for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
            if row.input_id == "pool.production_liquidity_amount"
        )
        usdg = boa.load(
            str(mock_erc20), sender, "USDG", "USDG", 6, seed_usdg // 10**6
        )
        weth = boa.load(str(mock_erc20), sender, "Wrapped Ether", "WETH", 18, 0)
        # A Morpho V2 vault, not a plain ERC20: 0400 registers this with
        # BlueChipYieldPrices, which reads asset(), decimals(), totalSupply()
        # and convertToAssets() off it. It is never registered as a Ripe asset
        # -- its only other use is as a DefaultsRobinhood constructor argument.
        steakhouse = boa.load(
            str(root / "contracts/mock/MockMorphoV2Vault.vy"),
            usdg.address,
            18,
            1_000 * 10**18,
            10**18,
        )
        eth_feed = boa.load(str(mock_feed), 3_000 * 10**18)
        btc_feed = boa.load(str(mock_feed), 100_000 * 10**18)
        usdg_feed = boa.load(str(mock_feed), 10**18)
        morpho_v2 = boa.load(str(root / "contracts/mock/MockMorphoV2Factory.vy"))
        # The factory must claim the vault, or the feed registration fails
        # closed exactly as it should for a vault Morpho does not recognise.
        morpho_v2.setVault(steakhouse.address, True)
        contributor = boa.load_partial(
            str(root / "contracts/modules/Contributor.vy")
        ).deploy_as_blueprint()
        curve_source = (
            root / "contracts/mock/MockRobinhoodCurveSystem.vy"
        ).read_text().replace(
            "if _id == 7 or _id == 12:",
            "if _id in [7, 11, 12, 13]:",
        ).replace(
            "coin0: public(address)",
            # Declared in the header because Vyper resolves module-level
            # declarations before function bodies.
            "interface SeedToken:\n"
            "    def transferFrom("
            "_f: address, _t: address, _v: uint256) -> bool: nonpayable\n"
            "\n"
            "lpBalanceOf: public(HashMap[address, uint256])\n"
            "lpTotalSupply: public(uint256)\n"
            "coin0: public(address)",
            1,
        ) + """

@external
def deploy_plain_pool(
    _name: String[32],
    _symbol: String[10],
    _coins: DynArray[address, 8],
    _A: uint256,
    _fee: uint256,
    _offpeg_fee_multiplier: uint256,
    _ma_exp_time: uint256,
    _implementation_idx: uint256,
    _asset_types: DynArray[uint8, 8],
    _method_ids: DynArray[bytes4, 8],
    _oracles: DynArray[address, 8],
) -> address:
    assert len(_name) != 0 and len(_symbol) != 0
    assert _A != 0 and _fee != 0 and _offpeg_fee_multiplier != 0
    assert _ma_exp_time != 0 and _implementation_idx == 0
    assert len(_coins) == 2 and len(_asset_types) == 2
    assert len(_method_ids) == 2 and len(_oracles) == 2
    assert _asset_types[0] == 0 and _asset_types[1] == 0
    assert _method_ids[0] == empty(bytes4)
    assert _method_ids[1] == empty(bytes4)
    assert _oracles[0] == empty(address)
    assert _oracles[1] == empty(address)
    self.coin0 = _coins[0]
    self.coin1 = _coins[1]
    self.registeredPool = self
    self.isPoolRegistered = True
    return self


@external
def add_liquidity(
    # DynArray, not uint256[2]: StableSwap-NG's ABI is
    # add_liquidity(uint256[],uint256) and a fixed-size array would compile to
    # a different selector, so the call would find no function and revert empty.
    _amounts: DynArray[uint256, 2], _min_mint_amount: uint256
) -> uint256:
    assert not self.shouldRevert, "pool revert"
    assert extcall SeedToken(self.coin0).transferFrom(
        msg.sender, self, _amounts[0]
    )
    assert extcall SeedToken(self.coin1).transferFrom(
        msg.sender, self, _amounts[1]
    )
    # coin0 is USDG at 6 decimals, coin1 is GREEN at 18.
    minted: uint256 = _amounts[0] * 10**12 + _amounts[1]
    assert minted >= _min_mint_amount, "slippage"
    self.lpBalanceOf[msg.sender] += minted
    self.lpTotalSupply += minted
    return minted


@view
@external
def balanceOf(_owner: address) -> uint256:
    return self.lpBalanceOf[_owner]


@external
def transfer(_to: address, _value: uint256) -> bool:
    assert self.lpBalanceOf[msg.sender] >= _value, "insufficient lp"
    self.lpBalanceOf[msg.sender] -= _value
    self.lpBalanceOf[_to] += _value
    return True
"""
        curve_system = boa.loads(
            curve_source,
            usdg,
            ZERO_ADDRESS,
            10**18,
            name="robinhood_external_curve_system",
        )

        address = lambda value: str(value.address).lower()
        unmapped_backend = BoaRobinhoodBackend(
            boa_module=boa,
            files=_production_files(root),
            sender=sender,
            final_governance_sender=final_sender,
        )
        provider_view = unmapped_backend._external_view(
            address(curve_system),
            interface_name="robinhood_curve_address_provider",
            abi=CURVE_ADDRESS_PROVIDER_ABI,
        )
        factory_view = unmapped_backend._external_view(
            address(curve_system),
            interface_name="robinhood_curve_stableswap_ng_factory",
            abi=CURVE_STABLESWAP_NG_FACTORY_ABI,
        )
        assert str(provider_view.get_address(12)).lower() == address(curve_system)
        assert address(factory_view) == address(curve_system)
        overrides = {
            "address:USDG": ("address", address(usdg)),
            "address:WETH": ("address", address(weth)),
            "address:STEAKHOUSE_USDG_VAULT": ("address", address(steakhouse)),
            "address:NATIVE_ETH_SENTINEL": ("address", boa.env.generate_address("native-eth")),
            "address:BTC_SENTINEL": ("address", boa.env.generate_address("btc")),
            "binding:contributor-template": ("address", address(contributor)),
            "binding:initial-ripe-hq": ("address", ZERO_ADDRESS),
            "binding:temporary-local-governance": (
                "address",
                str(sender).lower(),
            ),
            # The deployer receives the initial GREEN because the deployer is
            # what seeds the pool in 0600. This must be the real local sender,
            # not the fixture's placeholder, or the GREEN is minted to an
            # account the seed cannot spend from.
            "binding:green-supply-recipient": (
                "address",
                str(sender).lower(),
            ),
            "binding:approved-capability-set": ("json", []),
            "binding:bluechip-morpho-factories": ("address-array", [sender, sender]),
            "binding:bluechip-euler-factories": ("address-array", [sender, sender]),
            "binding:bluechip-fluid-resolver": ("address", sender),
            "binding:bluechip-compound-configurator": ("address", sender),
            "binding:bluechip-moonwell-comptroller": ("address", sender),
            "binding:bluechip-aave-provider": ("address", sender),
            "binding:lootbox-min-send-interval": ("uint256", 1),
            "binding:lootbox-send-interval": ("uint256", 0),
            "binding:lootbox-deposit-reward": ("uint256", 0),
            "binding:lootbox-yield-bonus": ("uint256", 0),
            "binding:deleverage-min-bps": ("uint256", 0),
            "binding:deleverage-buffer": ("uint256", 0),
            "binding:deleverage-underscore-spread": ("uint256", 0),
            "binding:deleverage-full-payoff-buffer": ("uint256", 0),
            "binding:deleverage-overage-bps": ("uint256", 0),
            "binding:deleverage-dust-threshold": ("uint256", 0),
            "binding:deleverage-dust-bps": ("uint256", 0),
            "input:Deployment.DP-04.ledger.actionBlockSourceBinding": ("address", ZERO_ADDRESS),
            "input:Deployment.DP-18.roles.governance": ("address", final_sender),
            "input:Deployment.DP-18.roles.safe": ("address", final_sender),
            "input:Deployment.DP-18.roles.guardian": ("address", final_sender),
            "input:Deployment.DP-18.roles.trainingWheelsAllowlist": ("address-array", [sender]),
            "input:Deployment.DP-19.supply.GREEN.recipient": ("address", sender),
            "input:Deployment.DP-19.supply.RIPE.recipient": ("address", sender),
            "input:Deployment.DP-19.supply.SGREEN.recipient": ("address", sender),
            "input:Deployment.DP-21.endaoment.wethIdentity": ("address", address(weth)),
            "input:Deployment.DP-23.external.chainlink.ethUsdFeed": ("address", address(eth_feed)),
            "input:Deployment.DP-23.external.chainlink.btcUsdFeed": ("address", address(btc_feed)),
            "input:Deployment.DP-23.external.chainlink.usdgUsdFeed": ("address", address(usdg_feed)),
            "input:Deployment.DP-23.external.blueChipYield.morphoV2Factory": ("address", address(morpho_v2)),
            "curve:curve.address_provider": ("address", address(curve_system)),
            "curve:pool.address": ("address", None),
            "curve:pool.factory": ("address", address(curve_system)),
            "curve:pool.name": ("string", "Local GREEN / USDG"),
            "curve:pool.symbol": ("string", "LGRNUSDG"),
            "curve:pool.funding_source": ("address", sender),
            "curve:pool.custodian": ("address", sender),
            "curve:pool.approving_account": ("address", sender),
            "curve:pool.withdrawal_authority": ("address", sender),
        }
        for item_id in (7, 11, 12, 13):
            overrides[f"curve:curve.address_provider_binding_{item_id}"] = (
                "json",
                [item_id, f"local-{item_id}", address(curve_system)],
            )
        plan = build_bound_plan(root, overrides=overrides)
        backend = BoaRobinhoodBackend(
            boa_module=boa,
            files=_production_files(root),
            sender=sender,
            final_governance_sender=final_sender,
            external_contracts={
                source_blueprint.ROBINHOOD_ADDRESSES[
                    "CURVE_ADDRESS_PROVIDER"
                ]: curve_system,
                source_blueprint.ROBINHOOD_ADDRESSES[
                    "CURVE_STABLESWAP_NG_FACTORY"
                ]: curve_system,
            },
        )
        executor = RobinhoodStageExecutor(
            plan, repository_root=root, backend=backend
        )
        for stage in plan["stages"]:
            executor(MigrationHandoff(), stage)

        assert len(executor.results) == 119
        assert len(backend.sequence) == 119
        assert len(backend.production_deployments) == 38
        assert backend.handed_off is True
        handoff = executor.results[
            "0900:000005:handoff-governance-and-relinquish-deployer"
        ]["execution_evidence"]
        assert len(LOCAL_GOVERNANCE_REFERENCES) == 11
        assert len(handoff["authority_relinquishments"]) == 11
        assert handoff["retained_temporary_governance"] == []
        assert all(
            backend._address(
                backend.contracts[reference].governance()
            )
            == ZERO_ADDRESS
            for reference in LOCAL_GOVERNANCE_REFERENCES
        )
        assert all(
            {
                backend._address(governor)
                for governor in backend.contracts[reference].getGovernors()
            }
            == {str(final_sender).lower()}
            for reference in LOCAL_GOVERNANCE_REFERENCES
        )
        assert backend._address(
            backend.contracts["address:RIPE_HQ"].governance()
        ) == str(final_sender).lower()
        price_desk = backend.contracts["address:PRICE_DESK"]
        assert [str(price_desk.getAddr(i)).lower() for i in range(1, 4)] == [
            str(backend.contracts[key].address).lower()
            for key in (
                "address:CHAINLINK_PRICES",
                "address:CURVE_PRICES",
                "address:BLUE_CHIP_YIELD_PRICES",
            )
        ]
        assert str(price_desk.getAddr(4)).lower() == ZERO_ADDRESS
        assert str(price_desk.getAddr(5)).lower() == ZERO_ADDRESS
        mission = backend.contracts["address:MISSION_CONTROL"]
        assert list(mission.getPriorityPriceSourceIds()) == [1, 3]
        assert not mission.isSupportedAsset(curve_system)
        chainlink = backend.contracts["address:CHAINLINK_PRICES"]
        curve = backend.contracts["address:CURVE_PRICES"]
        green = backend.contracts["address:GREEN_TOKEN"]
        assert chainlink.getPrice(usdg) > 0
        assert curve.getPrice(green) > 0
        assert not curve.hasPriceFeed(usdg)
        psm = backend.contracts["address:ENDAOMENT_PSM"]
        assert not psm.canMint()
        assert not psm.canRedeem()
        assert not psm.shouldAutoDeposit()
