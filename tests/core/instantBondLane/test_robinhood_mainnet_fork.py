"""Opt-in Robinhood mainnet-fork coverage for the Instant Bond Lane.

The suite never broadcasts.  RPC is used only to bind an exact historical block and
to hydrate Titanoboa's disposable local fork.  All deployments, registrations,
configuration changes, token balance changes, purchases, and time travel occur only
inside that local overlay and are rolled back before the test returns.

Required opt-in inputs:

* RIPE_IBL_RH_FORK_MODE=read-only-mainnet-fork
* RIPE_IBL_RH_FORK_RPC_URL=<archive-capable Robinhood mainnet endpoint>
* RIPE_IBL_RH_FORK_BLOCK_NUMBER=<decimal child-chain block number>
* RIPE_IBL_RH_FORK_BLOCK_HASH=<0x-prefixed block hash>
* RIPE_IBL_RH_FORK_MANIFEST=<path to the accepted rh deployment manifest>
* RIPE_IBL_RH_FORK_MANIFEST_SHA256=<lowercase manifest SHA-256>
* RIPE_IBL_RH_FORK_PAYMENT_TOKEN=<accepted canonical payment-token proxy>
* RIPE_IBL_RH_FORK_PAYMENT_DECIMALS=<accepted decimal count>
* RIPE_IBL_RH_FORK_EPOCH_LENGTH=<accepted EVM-NUMBER epoch length>

Without the exact opt-in the tests are skipped before any network access.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest
import requests
from boa.environment import Env
from boa.rpc import EthereumRPC


MODE_ENV = "RIPE_IBL_RH_FORK_MODE"
MODE = "read-only-mainnet-fork"
RPC_ENV = "RIPE_IBL_RH_FORK_RPC_URL"
BLOCK_NUMBER_ENV = "RIPE_IBL_RH_FORK_BLOCK_NUMBER"
BLOCK_HASH_ENV = "RIPE_IBL_RH_FORK_BLOCK_HASH"
MANIFEST_ENV = "RIPE_IBL_RH_FORK_MANIFEST"
MANIFEST_SHA256_ENV = "RIPE_IBL_RH_FORK_MANIFEST_SHA256"
PAYMENT_TOKEN_ENV = "RIPE_IBL_RH_FORK_PAYMENT_TOKEN"
PAYMENT_DECIMALS_ENV = "RIPE_IBL_RH_FORK_PAYMENT_DECIMALS"
EPOCH_LENGTH_ENV = "RIPE_IBL_RH_FORK_EPOCH_LENGTH"

ROBINHOOD_MAINNET_CHAIN_ID = 4_663
RIPE_TOKEN_ID = 3
MISSION_CONTROL_ID = 5
SWITCHBOARD_ID = 6
VAULT_BOOK_ID = 8
ENDAOMENT_FUNDS_ID = 21
SWITCHBOARD_ALPHA_ID = 1
SWITCHBOARD_CHARLIE_ID = 3
MAX_UINT256 = 2**256 - 1
IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)

_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
_HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_READ_ONLY_RPC_METHODS = frozenset(
    {
        "eth_chainId",
        "eth_getBlockByHash",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getStorageAt",
    }
)
_READ_ONLY_FORK_RPC_METHODS = frozenset(
    {
        "debug_traceCall",
        "eth_chainId",
        "eth_getBalance",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getStorageAt",
        "eth_getTransactionCount",
    }
)

ERC20_ABI = """
[
  {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},
  {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"account","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
  {"type":"function","name":"totalSupply","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint256"}]},
  {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
  {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}
]
"""


@dataclass(frozen=True, slots=True)
class ForkInputs:
    rpc_url: str
    block_number: int
    block_hash: str
    evm_number: int
    timestamp: int
    ripe_hq: str
    payment_token: str
    payment_decimals: int
    epoch_length: int


class ReadOnlyForkRPC(EthereumRPC):
    """Titanoboa transport that cannot call a state-changing RPC method."""

    @staticmethod
    def _validate_method(method: str) -> None:
        if method not in _READ_ONLY_FORK_RPC_METHODS:
            raise AssertionError(f"non-read-only fork RPC method rejected: {method}")

    def fetch(self, method, params):
        self._validate_method(method)
        try:
            return super().fetch(method, params)
        except requests.RequestException:
            raise requests.HTTPError(
                f"read-only fork RPC transport failure for {method}"
            ) from None

    def fetch_multi(self, payloads):
        payloads = list(payloads)
        for method, _params in payloads:
            self._validate_method(method)
        try:
            return super().fetch_multi(payloads)
        except requests.RequestException:
            raise requests.HTTPError(
                "read-only fork RPC batch transport failure"
            ) from None


def _required_environment(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        pytest.fail(f"missing required Robinhood fork input: {name}")
    return value


def _parse_positive_integer(name: str) -> int:
    raw = _required_environment(name)
    if not raw.isdecimal():
        pytest.fail(f"invalid positive integer Robinhood fork input: {name}")
    value = int(raw)
    if value <= 0:
        pytest.fail(f"invalid positive integer Robinhood fork input: {name}")
    return value


def _parse_nonnegative_integer(name: str) -> int:
    raw = _required_environment(name)
    if not raw.isdecimal():
        pytest.fail(f"invalid nonnegative integer Robinhood fork input: {name}")
    return int(raw)


def _parse_address(name: str) -> str:
    value = _required_environment(name)
    if _ADDRESS.fullmatch(value) is None:
        pytest.fail(f"invalid address Robinhood fork input: {name}")
    return value


def _rpc(rpc_url: str, method: str, params: list[object]) -> object:
    if method not in _READ_ONLY_RPC_METHODS:
        raise AssertionError(f"non-read-only RPC method rejected: {method}")
    try:
        response = requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        pytest.fail(f"JSON-RPC transport failure for {method}")
    if not isinstance(payload, dict):
        pytest.fail(f"invalid JSON-RPC response for {method}")
    if "error" in payload:
        error = payload["error"]
        code = error.get("code") if isinstance(error, dict) else "unknown"
        pytest.fail(
            f"JSON-RPC error for {method} (code {code}); "
            "the endpoint must retain state for the exact pinned block"
        )
    if set(payload) - {"jsonrpc", "id", "result"} or "result" not in payload:
        pytest.fail(f"invalid JSON-RPC response for {method}")
    return payload["result"]


def _load_manifest() -> dict[str, object]:
    manifest_path = Path(_required_environment(MANIFEST_ENV)).resolve()
    expected_sha256 = _required_environment(MANIFEST_SHA256_ENV)
    if _SHA256.fullmatch(expected_sha256) is None:
        pytest.fail(f"invalid SHA-256 Robinhood fork input: {MANIFEST_SHA256_ENV}")
    try:
        raw = manifest_path.read_bytes()
    except OSError:
        pytest.fail("accepted Robinhood deployment manifest is unreadable")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        pytest.fail("accepted Robinhood deployment manifest hash mismatch")
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        pytest.fail("accepted Robinhood deployment manifest is invalid JSON")
    if not isinstance(manifest, dict) or set(manifest) != {"contracts"}:
        pytest.fail("accepted Robinhood deployment manifest has unexpected shape")
    return manifest


@pytest.fixture(scope="module")
def rh_fork_inputs() -> ForkInputs:
    mode = os.environ.get(MODE_ENV)
    if mode is None or mode == "disabled":
        pytest.skip(
            f"Robinhood fork disabled; set {MODE_ENV}={MODE} with exact pinned inputs"
        )
    if mode != MODE:
        pytest.fail(f"invalid Robinhood fork opt-in mode: {MODE_ENV}")

    rpc_url = _required_environment(RPC_ENV)
    block_number = _parse_positive_integer(BLOCK_NUMBER_ENV)
    block_hash = _required_environment(BLOCK_HASH_ENV)
    if _HASH.fullmatch(block_hash) is None:
        pytest.fail(f"invalid block hash Robinhood fork input: {BLOCK_HASH_ENV}")

    manifest = _load_manifest()
    contracts = manifest["contracts"]
    if not isinstance(contracts, dict):
        pytest.fail("accepted Robinhood deployment manifest contracts are invalid")
    try:
        ripe_hq = contracts["RipeHq"]["address"]
    except (KeyError, TypeError):
        pytest.fail("accepted Robinhood deployment manifest has no RipeHq address")
    if not isinstance(ripe_hq, str) or _ADDRESS.fullmatch(ripe_hq) is None:
        pytest.fail("accepted Robinhood deployment manifest RipeHq address is invalid")

    payment_token = _parse_address(PAYMENT_TOKEN_ENV)
    payment_decimals = _parse_nonnegative_integer(PAYMENT_DECIMALS_ENV)
    if payment_decimals > 73:
        pytest.fail("accepted Robinhood payment-token decimals exceed lane support")
    epoch_length = _parse_positive_integer(EPOCH_LENGTH_ENV)

    try:
        endaoment_psm_args = contracts["EndaomentPSM"]["args"]
    except (KeyError, TypeError):
        pytest.fail("accepted Robinhood deployment manifest has no EndaomentPSM args")
    if (
        not isinstance(endaoment_psm_args, str)
        or len(endaoment_psm_args) < 7 * 64
        or len(endaoment_psm_args) % 64 != 0
        or re.fullmatch(r"[0-9a-fA-F]+", endaoment_psm_args) is None
    ):
        pytest.fail("accepted Robinhood EndaomentPSM constructor args are invalid")
    payment_token_word = endaoment_psm_args[6 * 64 : 7 * 64]
    if payment_token_word[:24] != "0" * 24:
        pytest.fail("accepted Robinhood EndaomentPSM payment token is not an address")
    manifest_payment_token = "0x" + payment_token_word[24:]
    if manifest_payment_token.lower() != payment_token.lower():
        pytest.fail("accepted Robinhood payment token does not match the manifest")

    observed_chain_id = int(_rpc(rpc_url, "eth_chainId", []), 16)
    if observed_chain_id != ROBINHOOD_MAINNET_CHAIN_ID:
        pytest.fail("Robinhood fork endpoint returned the wrong chain ID")

    block_tag = hex(block_number)
    block = _rpc(rpc_url, "eth_getBlockByNumber", [block_tag, False])
    by_hash = _rpc(rpc_url, "eth_getBlockByHash", [block_hash, False])
    if not isinstance(block, dict) or not isinstance(by_hash, dict):
        pytest.fail("pinned Robinhood fork block is unavailable")
    if block.get("hash", "").lower() != block_hash.lower() or by_hash != block:
        pytest.fail("pinned Robinhood fork block identity mismatch")
    if int(block.get("number", "0x0"), 16) != block_number:
        pytest.fail("pinned Robinhood fork block number mismatch")
    l1_block_number = block.get("l1BlockNumber")
    if not isinstance(l1_block_number, str):
        pytest.fail("pinned Robinhood block has no EVM NUMBER identity")
    evm_number = int(l1_block_number, 16)
    timestamp = int(block.get("timestamp", "0x0"), 16)
    if evm_number <= 0 or timestamp <= 0:
        pytest.fail("pinned Robinhood fork clock identity is invalid")

    for address, label in ((ripe_hq, "RipeHq"), (payment_token, "payment token")):
        code = _rpc(rpc_url, "eth_getCode", [address, block_tag])
        if not isinstance(code, str) or code in {"0x", "0x0"}:
            pytest.fail(f"pinned Robinhood {label} has no code")

    implementation_word = _rpc(
        rpc_url,
        "eth_getStorageAt",
        [payment_token, IMPLEMENTATION_SLOT, block_tag],
    )
    if not isinstance(implementation_word, str) or len(implementation_word) != 66:
        pytest.fail("pinned Robinhood payment-token implementation slot is invalid")
    implementation = "0x" + implementation_word[-40:]
    if int(implementation, 16) == 0:
        pytest.fail("pinned Robinhood payment-token implementation is unset")
    implementation_code = _rpc(
        rpc_url, "eth_getCode", [implementation, block_tag]
    )
    if not isinstance(implementation_code, str) or implementation_code in {"0x", "0x0"}:
        pytest.fail("pinned Robinhood payment-token implementation has no code")

    return ForkInputs(
        rpc_url=rpc_url,
        block_number=block_number,
        block_hash=block_hash.lower(),
        evm_number=evm_number,
        timestamp=timestamp,
        ripe_hq=ripe_hq,
        payment_token=payment_token,
        payment_decimals=payment_decimals,
        epoch_length=epoch_length,
    )


@pytest.fixture(scope="module")
def rh_fork(rh_fork_inputs):
    # Use a fresh Env because the repository's session-scoped local fixture is
    # intentionally dirty.  The restricted transport makes broadcasting
    # impossible even if a future harness change accidentally requests it.
    fork_env = Env()
    fork_env.fork_rpc(
        ReadOnlyForkRPC(rh_fork_inputs.rpc_url),
        block_identifier=rh_fork_inputs.block_number,
    )
    with boa.set_env(fork_env):
        # Titanoboa receives the RPC child height as its header number. Robinhood
        # contracts execute with Arbitrum's ancestor-chain EVM NUMBER instead.
        boa.env.evm.patch.block_number = rh_fork_inputs.evm_number
        boa.env.evm.patch.timestamp = rh_fork_inputs.timestamp
        yield rh_fork_inputs


def _live_contracts(inputs: ForkInputs) -> SimpleNamespace:
    hq = boa.load_partial("contracts/registries/RipeHq.vy").at(inputs.ripe_hq)
    ripe_token = boa.load_partial("contracts/tokens/RipeToken.vy").at(
        hq.getAddr(RIPE_TOKEN_ID)
    )
    mission_control = boa.load_partial("contracts/data/MissionControl.vy").at(
        hq.getAddr(MISSION_CONTROL_ID)
    )
    switchboard = boa.load_partial("contracts/registries/Switchboard.vy").at(
        hq.getAddr(SWITCHBOARD_ID)
    )
    vault_book = boa.load_partial("contracts/registries/VaultBook.vy").at(
        hq.getAddr(VAULT_BOOK_ID)
    )
    ripe_gov_vault_id = mission_control.coreRipeGovVaultId()
    assert ripe_gov_vault_id != 0
    ripe_gov = boa.load_partial("contracts/vaults/RipeGov.vy").at(
        vault_book.getAddr(ripe_gov_vault_id)
    )
    payment_token = boa.loads_abi(ERC20_ABI, name="ForkPaymentToken").at(
        inputs.payment_token
    )
    return SimpleNamespace(
        hq=hq,
        ripe_token=ripe_token,
        mission_control=mission_control,
        switchboard=switchboard,
        vault_book=vault_book,
        ripe_gov_vault_id=ripe_gov_vault_id,
        ripe_gov=ripe_gov,
        payment_token=payment_token,
    )


def _advance_blocks(blocks: int) -> None:
    if blocks > 0:
        boa.env.time_travel(blocks=blocks)


def _register(registry, address, description: str, governance) -> int:
    delay = registry.registryChangeTimeLock()
    assert registry.startAddNewAddressToRegistry(
        address, description, sender=governance
    )
    _advance_blocks(delay)
    return registry.confirmNewAddressToRegistry(address, sender=governance)


def _fork_config(scale: int) -> tuple[object, ...]:
    # Synthetic test-only economics. The fork test validates integration and
    # settlement; deployment calibration remains a separate owner decision.
    return (
        True,
        10 * scale,
        scale,
        100_000 * 10**18,
        10 * 10**18,
        4 * 10**18,
        8_000,
        2_000,
        800,
        800,
        300,
        300,
        400,
        12,
        1_000,
    )


def _deploy_local_lane(inputs: ForkInputs, live: SimpleNamespace) -> SimpleNamespace:
    operator = boa.env.generate_address("ibl-rh-fork-operator")
    boa.env.set_balance(operator, 100 * 10**18)
    current_number = boa.env.evm.patch.block_number
    genesis = current_number - current_number % inputs.epoch_length

    lane = boa.load(
        "contracts/core/InstantBondLane.vy",
        live.hq,
        live.payment_token,
        genesis,
        inputs.epoch_length,
        name="robinhood_fork_instant_bond_lane",
        sender=operator,
    )
    alpha = boa.load_partial("contracts/config/SwitchboardAlpha.vy").at(
        live.switchboard.getAddr(SWITCHBOARD_ALPHA_ID)
    )
    foxtrot = boa.load(
        "contracts/config/SwitchboardFoxtrot.vy",
        live.hq,
        operator,
        alpha.minActionTimeLock(),
        alpha.maxActionTimeLock(),
        lane,
        name="robinhood_fork_switchboard_foxtrot",
        sender=operator,
    )
    assert foxtrot.setActionTimeLockAfterSetup(sender=operator)

    governance = live.hq.governance()
    assert str(governance).lower() != "0x0000000000000000000000000000000000000000"
    foxtrot_reg_id = _register(
        live.switchboard, foxtrot, "Switchboard Foxtrot", governance
    )
    assert live.switchboard.getAddr(foxtrot_reg_id) == foxtrot.address
    assert live.switchboard.isSwitchboardAddr(foxtrot)

    lane_reg_id = _register(live.hq, lane, "Instant Bond Lane", governance)
    hq_delay = live.hq.registryChangeTimeLock()
    live.hq.initiateHqConfigChange(
        lane_reg_id, False, True, False, sender=governance
    )
    _advance_blocks(hq_delay)
    assert live.hq.confirmHqConfigChange(lane_reg_id, sender=governance)
    assert live.hq.canMintRipe(lane)

    charlie = live.switchboard.getAddr(SWITCHBOARD_CHARLIE_ID)
    lane.pause(False, sender=charlie)

    config = _fork_config(lane.PAYMENT_SCALE())
        action_id = foxtrot.setInstantBondConfig(config, sender=operator)
    _advance_blocks(foxtrot.actionTimeLock())
    assert foxtrot.executePendingAction(action_id, sender=operator)
    assert tuple(lane.config()) == config

    return SimpleNamespace(
        lane=lane,
        foxtrot=foxtrot,
        operator=operator,
        genesis=genesis,
        lane_reg_id=lane_reg_id,
        foxtrot_reg_id=foxtrot_reg_id,
    )


def test_read_only_fork_transport_rejects_broadcast_before_network(monkeypatch):
    def unexpected_network_access(*_args, **_kwargs):
        raise AssertionError("transport reached the network")

    monkeypatch.setattr(requests.Session, "post", unexpected_network_access)
    rpc = ReadOnlyForkRPC("https://not-used.invalid")

    with pytest.raises(AssertionError, match="non-read-only fork RPC method"):
        rpc.fetch("eth_sendRawTransaction", ["0x"])
    with pytest.raises(AssertionError, match="non-read-only fork RPC method"):
        rpc.fetch_multi(
            [
                ("eth_chainId", []),
                ("eth_sendTransaction", [{}]),
            ]
        )


@pytest.mark.fork_qualification
def test_robinhood_mainnet_fork_binds_topology_token_and_evm_clock(rh_fork):
    live = _live_contracts(rh_fork)
    assert live.hq.address == rh_fork.ripe_hq
    assert live.payment_token.address == rh_fork.payment_token
    assert live.payment_token.decimals() == rh_fork.payment_decimals
    assert live.payment_token.address != live.ripe_token.address
    assert live.vault_book.getAddr(live.ripe_gov_vault_id) == live.ripe_gov.address
    assert live.vault_book.getRegId(live.ripe_gov) == live.ripe_gov_vault_id
    assert live.vault_book.isVaultBookAddr(live.ripe_gov)
    assert live.mission_control.isSupportedAssetInVault(
        live.ripe_gov_vault_id, live.ripe_token
    )
    assert live.ripe_gov.isSupportedVaultAsset(live.ripe_token)
    assert str(live.hq.getAddr(ENDAOMENT_FUNDS_ID)).lower() != (
        "0x0000000000000000000000000000000000000000"
    )

    # With no prior shares and zero requested duration, this public RipeGov helper
    # returns block.number exactly and observes the patched EVM NUMBER domain.
    observed_number = live.ripe_gov.getWeightedLockOnTokenDeposit(
        0, 0, (0, 0, 0, False, 0), 0, 0
    )
    assert observed_number == rh_fork.evm_number
    assert observed_number != rh_fork.block_number


@pytest.mark.fork_qualification
def test_robinhood_mainnet_fork_executes_and_rolls_back_full_purchase_paths(rh_fork):
    live = _live_contracts(rh_fork)
    baseline = {
        "hq_num_addrs": live.hq.numAddrs(),
        "switchboard_num_addrs": live.switchboard.numAddrs(),
        "payment_supply": live.payment_token.totalSupply(),
    }

    with boa.env.anchor():
        deployed = _deploy_local_lane(rh_fork, live)
        lane = deployed.lane
        scale = lane.PAYMENT_SCALE()
        assert lane.PAYMENT_DECIMALS() == rh_fork.payment_decimals
        assert lane.PAYMENT_TOKEN() == live.payment_token.address
        assert lane.EPOCH_LENGTH() == rh_fork.epoch_length
        assert lane.GENESIS_BLOCK() % lane.EPOCH_LENGTH() == 0

        endaoment_funds = live.hq.getAddr(ENDAOMENT_FUNDS_ID)
        unlocked_buyer = boa.env.generate_address("ibl-rh-fork-unlocked-buyer")
        locked_buyer = boa.env.generate_address("ibl-rh-fork-locked-buyer")
        purchase_amount = scale
        for buyer in (unlocked_buyer, locked_buyer):
            boa.deal(live.payment_token, buyer, 2 * purchase_amount)
            assert live.payment_token.approve(lane, MAX_UINT256, sender=buyer)

        payment_before = live.payment_token.balanceOf(endaoment_funds)
        unlocked_ripe_before = live.ripe_token.balanceOf(unlocked_buyer)
        unlocked_quote = lane.previewBuyNow(purchase_amount, 0)
        assert unlocked_quote.available
        assert unlocked_quote.actualLock == 0
        unlocked_payout = lane.buyNow(
            purchase_amount,
            0,
            unlocked_quote.epoch,
            unlocked_quote.totalRipe,
            boa.env.evm.patch.block_number,
            sender=unlocked_buyer,
        )
        assert unlocked_payout == unlocked_quote.totalRipe
        assert live.ripe_token.balanceOf(unlocked_buyer) == (
            unlocked_ripe_before + unlocked_payout
        )

        locked_vault_before = live.ripe_gov.getTotalAmountForUser(
            locked_buyer, live.ripe_token
        )
        locked_quote = lane.previewBuyNow(purchase_amount, MAX_UINT256)
        assert locked_quote.available
        assert locked_quote.actualLock > 0
        assert locked_quote.bonusRipe > 0
        locked_payout = lane.buyNow(
            purchase_amount,
            MAX_UINT256,
            locked_quote.epoch,
            locked_quote.totalRipe,
            boa.env.evm.patch.block_number,
            sender=locked_buyer,
        )
        assert locked_payout == locked_quote.totalRipe
        purchase = next(
            log
            for log in lane.get_logs()
            if type(log).__name__ == "InstantBondPurchased"
        )
        assert purchase.ripeGovVaultId == live.ripe_gov_vault_id
        assert live.ripe_gov.getTotalAmountForUser(
            locked_buyer, live.ripe_token
        ) == locked_vault_before + locked_payout

        assert live.payment_token.balanceOf(endaoment_funds) == (
            payment_before + 2 * purchase_amount
        )
        assert lane.epochAcceptedPayment() == 2 * purchase_amount
        assert lane.cumulativeMinted() == unlocked_payout + locked_payout
        assert live.payment_token.balanceOf(lane) == 0
        assert live.ripe_token.balanceOf(lane) == 0
        assert live.ripe_token.allowance(
            lane, live.hq.getAddr(17)
        ) == 0

    assert live.hq.numAddrs() == baseline["hq_num_addrs"]
    assert live.switchboard.numAddrs() == baseline["switchboard_num_addrs"]
    assert live.payment_token.totalSupply() == baseline["payment_supply"]
