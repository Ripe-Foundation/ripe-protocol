import hashlib
import json
from pathlib import Path
import time

import pytest

from config.Ccip import (
    CCIP_EVIDENCE_GATES,
    CCIP_HQ_APPEND_WINDOW_GATES,
    CCIP_OWNER_DISPOSITION_GATES,
    CCIP_REQUIRED_EVIDENCE_NAMES,
    CcipEvidenceRecord,
    CcipHqAppendWindow,
    CcipLanePolicy,
    CcipRateLimitPolicy,
)
from scripts.utils import ccip


ROOT = Path(__file__).resolve().parents[1]
WIRE_MIGRATIONS = (
    "migrations/base-mainnet/2026082400_CcipWirePlan.py",
    "migrations/robinhood-mainnet/2026082400_CcipWirePlan.py",
    "migrations/base-sepolia/0002_CcipWire.py",
    "migrations/robinhood-testnet/0002_CcipWire.py",
)
POOL_MIGRATIONS = (
    "migrations/base-mainnet/2026080700_CcipPools.py",
    "migrations/robinhood-mainnet/2026080700_CcipPools.py",
    "migrations/base-sepolia/0001_CcipPool.py",
    "migrations/robinhood-testnet/0001_CcipPool.py",
)


class _ConfiguredPool:
    def __init__(self, selector, remote_pool, remote_token, rate=(False, 0, 0)):
        self.selector = selector
        self.remote_pools = [ccip.encode_address(remote_pool)]
        self.remote_token = ccip.encode_address(remote_token)
        self.rate = rate
        self.rate_admin = "0x0000000000000000000000000000000000000000"
        self.calls = []

    def isSupportedChain(self, selector):
        self.calls.append("isSupportedChain")
        return selector == self.selector

    def getRemoteToken(self, selector):
        self.calls.append("getRemoteToken")
        return self.remote_token

    def getRemotePools(self, selector):
        self.calls.append("getRemotePools")
        return self.remote_pools

    def _bucket(self):
        enabled, capacity, rate = self.rate
        return (capacity, 1, enabled, capacity, rate)

    def getCurrentOutboundRateLimiterState(self, selector):
        self.calls.append("getCurrentOutboundRateLimiterState")
        return self._bucket()

    def getCurrentInboundRateLimiterState(self, selector):
        self.calls.append("getCurrentInboundRateLimiterState")
        return self._bucket()

    def getRateLimitAdmin(self):
        self.calls.append("getRateLimitAdmin")
        return self.rate_admin


class _FinalizedPool(_ConfiguredPool):
    def __init__(
        self,
        address,
        token,
        router,
        rmn_proxy,
        owner,
        selector,
        remote_pool,
        remote_token,
    ):
        super().__init__(selector, remote_pool, remote_token)
        self.address = address
        self._token = token
        self._router = router
        self._rmn_proxy = rmn_proxy
        self._owner = owner
        self.token_decimals = ccip.MAINNET_TOKEN_DECIMALS
        self.allowlist_enabled = False
        self.allowlist = ()

    def getToken(self):
        return self._token

    def getRouter(self):
        return self._router

    def getRmnProxy(self):
        return self._rmn_proxy

    def owner(self):
        return self._owner

    def getTokenDecimals(self):
        return self.token_decimals

    def getAllowListEnabled(self):
        return self.allowlist_enabled

    def getAllowList(self):
        return self.allowlist

    def typeAndVersion(self):
        return "BurnMintTokenPool 1.5.1"

    def canMintGreen(self):
        return False

    def canMintRipe(self):
        return True


def test_mainnet_activation_finalizer_requires_complete_read_only_state(monkeypatch):
    chain = "base-mainnet"
    remote_chain = "robinhood-mainnet"
    token = "0x" + "1" * 40
    pool_address = "0x" + "2" * 40
    remote_pool = "0x" + "3" * 40
    remote_token = "0x" + "4" * 40
    governance = "0x" + "5" * 40
    selector = ccip.CCIP[remote_chain]["CHAIN_SELECTOR"]
    pool = _FinalizedPool(
        pool_address,
        token,
        ccip.CCIP[chain]["ROUTER"],
        ccip.CCIP[chain]["RMN_PROXY"],
        governance,
        selector,
        remote_pool,
        remote_token,
    )

    class Registry:
        pending = ccip.ZERO_ADDRESS

        def getTokenConfig(self, _token):
            return governance, self.pending, pool_address

        def getPool(self, _token):
            return pool_address

    registry = Registry()

    class Hq:
        def governance(self):
            return governance

        def numAddrs(self):
            return 25

        def getRegId(self, _pool):
            return 23

        def getAddr(self, _reg_id):
            return pool_address

        def hqConfig(self, _reg_id):
            return "RIPE pool", False, True, False

        def hasPendingHqConfigChange(self, _reg_id):
            return False

        def pendingNewAddr(self, _pool):
            return "", 0, 0

        def pendingAddrUpdate(self, _reg_id):
            return ccip.ZERO_ADDRESS, 0, 0

        def pendingAddrDisable(self, _reg_id):
            return 0, 0

    hq = Hq()

    class Migration:
        def chain(self):
            return chain

        def get_contract(self, name):
            assert name == "RipeHq"
            return hq

        def get_address(self, name):
            assert name == "RipeToken"
            return token

        def get_solidity_contract(self, name, source_file=None):
            assert name == "RipeCcipBurnMintTokenPool"
            assert source_file == "RipeCcipBurnMintTokenPools.sol"
            return pool

        def get_address_on_chain(self, selected_chain, name):
            assert selected_chain == remote_chain
            return remote_pool if "Pool" in name else remote_token

    monkeypatch.setattr(ccip, "token_admin_registry", lambda _chain: registry)
    pools = (("RIPE", "RipeCcipBurnMintTokenPool", "RipeToken", False, True),)

    ccip.complete_mainnet_activation_preflight(
        Migration(),
        pools,
        "RipeCcipBurnMintTokenPools.sol",
        hq,
        registry,
        governance,
    )
    ccip.require_mainnet_activation_finalized(
        Migration(), pools, "RipeCcipBurnMintTokenPools.sol"
    )

    pool.token_decimals = 17
    with pytest.raises(AssertionError, match="wrong token decimals"):
        ccip.complete_mainnet_activation_preflight(
            Migration(),
            pools,
            "RipeCcipBurnMintTokenPools.sol",
            hq,
            registry,
            governance,
        )
    with pytest.raises(
        RuntimeError,
        match="CCIP_FINALIZATION_POOL_TOKEN_DECIMALS_MISMATCH",
    ):
        ccip.require_mainnet_activation_finalized(
            Migration(), pools, "RipeCcipBurnMintTokenPools.sol"
        )
    pool.token_decimals = ccip.MAINNET_TOKEN_DECIMALS

    for enabled, allowlist in (
        (True, ()),
        (False, ("0x" + "7" * 40,)),
    ):
        pool.allowlist_enabled = enabled
        pool.allowlist = allowlist
        with pytest.raises(AssertionError, match="unexpected allowlist"):
            ccip.complete_mainnet_activation_preflight(
                Migration(),
                pools,
                "RipeCcipBurnMintTokenPools.sol",
                hq,
                registry,
                governance,
            )
        with pytest.raises(
            RuntimeError,
            match="CCIP_FINALIZATION_POOL_ALLOWLIST_MISMATCH",
        ):
            ccip.require_mainnet_activation_finalized(
                Migration(), pools, "RipeCcipBurnMintTokenPools.sol"
            )
    pool.allowlist_enabled = False
    pool.allowlist = ()

    registry.pending = "0x" + "6" * 40
    with pytest.raises(RuntimeError, match="CCIP_FINALIZATION_ADMIN_PENDING"):
        ccip.require_mainnet_activation_finalized(
            Migration(), pools, "RipeCcipBurnMintTokenPools.sol"
        )


def test_supported_lane_is_fully_revalidated():
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)

    ccip.assert_lane_configuration(
        pool,
        selector,
        remote_pool,
        remote_token,
        (False, 0, 0),
        (False, 0, 0),
        "0x0000000000000000000000000000000000000000",
    )

    assert pool.calls == [
        "isSupportedChain",
        "getRemoteToken",
        "getRemotePools",
        "getCurrentOutboundRateLimiterState",
        "getCurrentInboundRateLimiterState",
        "getRateLimitAdmin",
    ]


@pytest.mark.parametrize("mutation", ("token", "extra_pool", "rate", "rate_admin"))
def test_supported_lane_revalidation_rejects_stale_or_wrong_wiring(mutation):
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)
    if mutation == "token":
        pool.remote_token = ccip.encode_address(
            "0x355bB7F0f6c730e4460d620420a300fa08FF82F3"
        )
    elif mutation == "extra_pool":
        pool.remote_pools.append(
            ccip.encode_address("0x4B19f165Bb1Ce3f19Bbe828D150706B9deeEeC95")
        )
    elif mutation == "rate":
        pool.rate = (True, 10**18, 10**15)
    else:
        pool.rate_admin = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"

    with pytest.raises(AssertionError):
        ccip.assert_lane_configuration(
            pool,
            selector,
            remote_pool,
            remote_token,
            (False, 0, 0),
            (False, 0, 0),
            "0x0000000000000000000000000000000000000000",
        )


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS)
def test_wire_migration_revalidates_supported_lane_and_gates_new_mutation(
    relative_path,
):
    source = (ROOT / relative_path).read_text()
    supported_branch = source.index("if lane_is_configured:")
    revalidation = source.index("ccip.assert_lane_configuration(", supported_branch)
    mutation = source.index("ccip.execute_activation_mutation(", supported_branch)

    assert "continue" not in source[supported_branch:revalidation]
    assert mutation < revalidation
    assert "migration.execute(" not in source


def test_activation_mutation_wrapper_checks_gates_before_execute(monkeypatch):
    observed = []

    class _Migration:
        def chain(self):
            return "base-mainnet"

        def execute(self, action, *args):
            observed.append(("execute", action, args))
            return "result"

    monkeypatch.setattr(
        ccip,
        "require_ccip_wiring_gates",
        lambda *binding: observed.append(("gate", binding)) or "policy",
    )

    assert (
        ccip.execute_activation_mutation(
            _Migration(),
            "RIPE",
            "action",
            1,
            2,
            remote_chain="robinhood-mainnet",
        )
        == "result"
    )
    assert observed == [
        (
            "gate",
            ("base-mainnet", "robinhood-mainnet", "RIPE"),
        ),
        ("execute", "action", (1, 2)),
    ]


def test_typed_owner_policy_is_returned_for_its_exact_lane(
    monkeypatch, tmp_path
):
    binding = ("base-mainnet", "robinhood-mainnet", "RIPE")
    policy = CcipLanePolicy(
        *binding,
        outbound=CcipRateLimitPolicy(True, 1_000, 10),
        inbound=CcipRateLimitPolicy(True, 1_100, 11),
        rate_limit_admin="0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
    )
    monkeypatch.setitem(CCIP_OWNER_DISPOSITION_GATES, binding, policy)
    for name in CCIP_REQUIRED_EVIDENCE_NAMES:
        expires_at = 4_000_000_000 if name == "AUTOMATIC_EXECUTION_DESTINATION_GAS" else None
        evidence = {
            "schema_version": 1,
            "gate_name": name,
            "local_chain": binding[0],
            "remote_chain": binding[1],
            "token": binding[2],
            "approved_at": 1,
            "expires_at": expires_at,
        }
        path = tmp_path / f"{name}.json"
        payload = json.dumps(evidence, sort_keys=True).encode()
        path.write_bytes(payload)
        key = (*binding, name)
        monkeypatch.setitem(
            CCIP_EVIDENCE_GATES,
            key,
            CcipEvidenceRecord(
                name,
                *binding,
                evidence_path=str(path),
                evidence_sha256=hashlib.sha256(payload).hexdigest(),
                approved_at=1,
                expires_at=expires_at,
            ),
        )

    class _Migration:
        def chain(self):
            return "base-mainnet"

    assert (
        ccip.require_activation_policy(_Migration(), "RIPE", "robinhood-mainnet")
        is policy
    )
    assert ccip.lane_policy_for_revalidation(*binding) is policy


def test_rate_policy_rejects_values_chainlink_would_revert():
    with pytest.raises(ValueError, match="0 < rate < capacity"):
        CcipRateLimitPolicy(True, 10, 10)
    with pytest.raises(ValueError, match="zero capacity and zero rate"):
        CcipRateLimitPolicy(False, 10, 0)


def test_already_wired_revalidation_uses_observed_baseline_without_owner_choice():
    policy = ccip.lane_policy_for_revalidation(
        "base-mainnet", "robinhood-mainnet", "RIPE"
    )
    assert policy.outbound.as_tuple() == (False, 0, 0)
    assert policy.inbound.as_tuple() == (False, 0, 0)
    assert policy.rate_limit_admin == ("0x0000000000000000000000000000000000000000")


@pytest.mark.parametrize("relative_path", POOL_MIGRATIONS)
def test_every_ccip_pool_deployment_is_policy_gated(relative_path):
    source = (ROOT / relative_path).read_text()
    deploy_offsets = []
    start = 0
    while True:
        offset = source.find("migration.deploy_solidity(", start)
        if offset == -1:
            break
        deploy_offsets.append(offset)
        start = offset + 1

    assert deploy_offsets, f"{relative_path} has no pool deployment"
    gate_offsets = []
    start = 0
    while True:
        offset = source.find("ccip.require_activation_policy(", start)
        if offset == -1:
            break
        gate_offsets.append(offset)
        start = offset + 1

    assert len(gate_offsets) >= len(deploy_offsets)
    assert all(gate < deploy for gate, deploy in zip(gate_offsets, deploy_offsets))
    assert "migration.execute(" not in source


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS)
def test_selected_policy_values_drive_wiring_and_revalidation(relative_path):
    source = (ROOT / relative_path).read_text()
    assert "policy.outbound.as_tuple()" in source
    assert "policy.inbound.as_tuple()" in source
    assert "policy.rate_limit_admin" in source
    assert "NO_RATE_LIMIT" not in source
    assert "CURRENT_RATE_LIMIT_ADMIN" not in source


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS[:2])
def test_mainnet_safe_plan_binds_live_ccip_append_order(relative_path):
    source = (ROOT / relative_path).read_text()
    assert 'POOLS = (\n    ("RIPE"' in source
    preflight = source.index("ccip.require_mainnet_hq_append_preflight(")
    first_mutation = source.index("ccip.execute_activation_mutation(")
    assert preflight < first_mutation
    assert "expected_plan_sha256=hq_append_plan_sha256" in source
    assert "initiateHqConfigChange(uint256,bool,bool,bool)" in source
    assert "confirmHqConfigChange(uint256)" in source
    assert "AFTER registryChangeTimeLock" in source
    assert "AFTER a second registryChangeTimeLock" in source
    assert "must assign RipeHq id" not in source


def test_hq_append_preflight_requires_exact_empty_exclusive_window(monkeypatch):
    zero = "0x0000000000000000000000000000000000000000"

    class _Hq:
        def numAddrs(self):
            return 23

        def getAddr(self, registry_id):
            assert registry_id in (23, 24)
            return zero

    with pytest.raises(RuntimeError, match="CCIP_HQ_APPEND_WINDOW_REQUIRED"):
        ccip.require_mainnet_hq_append_preflight(
            "base-mainnet", _Hq(), ("RIPE", "GREEN")
        )

    window = CcipHqAppendWindow(
        chain="base-mainnet",
        assignments=(("RIPE", 23), ("GREEN", 24)),
        coordination_reference="safe-plan-approval-123",
        exclusive_governance_window=True,
        plan_sha256="ab" * 32,
        starts_at=int(time.time()) - 10,
        expires_at=int(time.time()) + 3600,
    )
    monkeypatch.setitem(CCIP_HQ_APPEND_WINDOW_GATES, "base-mainnet", window)
    assert (
        ccip.require_mainnet_hq_append_preflight(
            "base-mainnet", _Hq(), ("RIPE", "GREEN")
        )
        is window
    )

    with pytest.raises(RuntimeError, match="PARTIAL_STATE"):
        ccip.require_mainnet_hq_append_preflight("base-mainnet", _Hq(), ("GREEN",))
