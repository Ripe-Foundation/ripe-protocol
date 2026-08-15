"""SC-04 exact-token qualification against the pinned Base deployment.

Run this module by itself. The repository's default marker expression excludes
``fork_qualification`` and would otherwise produce a vacuous zero-test run::

    pytest -q -s --fork base -m fork_qualification -p no:cacheprovider \
        tests/vaults/fork/test_shares_vault_exact_token_qualification.py

At the pinned baseline the intentional red expectations are:

* ``test_fail_first_real_token_direct_transfer_matrix``;
* ``test_fail_first_compound_cweth_full_withdrawal_must_succeed_exactly``;
* ``test_fail_first_aave_usdc_deposit_must_charge_exact_requested_amount``;
* ``test_fail_first_aave_usdc_partial_withdrawal_must_deliver_exact_amount``.

The other five tests pass, so ``4 failed, 5 passed`` is the expected baseline
polarity. Any different failing identity or count is unexpected and requires
investigation.

The token markets, balances, indexes, and deployed vault inventory come from
the real Base fork. Teller, Ledger, MissionControl, and SharesVault are fresh
local deployments of the pinned source. The corpus tests deliberately use
local admission configuration because the deployed per-asset deposit switch is
off. The headline trajectory amounts clear the deployed minimum floors.

The direct layer carries the full cross-product corpus. Teller and SharesVault
use narrower, explicitly recorded corpora and pre-states; their results must
not be described as covering the direct layer's zero/small/large/adversarial
cross-product.

Each invocation writes evidence to a fresh run directory under pytest's base
temporary directory and prints that directory. Set ``SC04_EVIDENCE_BASE`` to
choose a different parent; a unique child is still created, so concurrent or
subset runs cannot silently overwrite another run's evidence.
"""

import json
import os
import random
import socket
import subprocess
import time
from math import gcd
from pathlib import Path

import boa
import pytest
import requests
from eth_utils import keccak, to_checksum_address


BASE_BLOCK = 49_972_042
BASE_BLOCK_HASH = "0xdc0108d12d0669337c1ac95169d613aa8c9e3947f74d079b917f73541f362bb8"
BASE_BLOCK_TIMESTAMP = 1_786_733_431
DEFAULT_BASE_RPC = "https://base-mainnet.public.blastapi.io"
CORPUS_SEED = 0x5C04_2026
RANDOM_SAMPLE_COUNT = 128
EVIDENCE_BASE_ENV = "SC04_EVIDENCE_BASE"
EVIDENCE_ROOT = None
MAX_UINT256 = 2**256 - 1
COMET_INDEX_SCALE = 10**15
EIP1967_IMPLEMENTATION_SLOT = (
    int.from_bytes(keccak(text="eip1967.proxy.implementation"), "big") - 1
)

VAULT_BOOK = to_checksum_address("0xB758e30C14825519b895Fd9928d5d8748A71a944")
MISSION_CONTROL = to_checksum_address("0xB59b84B526547b6dcb86CCF4004d48E619156CF3")
DEPLOYED_REBASE_VAULT = to_checksum_address("0xce2E96C9F6806731914A7b4c3E4aC1F296d98597")
AAVE_POOL = to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5")
RIPE_HQ = to_checksum_address("0x6162df1b329E157479F8f1407E888260E0EC3d2b")
PRICE_DESK = to_checksum_address("0x2F7901BE53cC94AEF174f1a0764430840360Ef53")

# These inputs exercise Deleverage._calcAmountToPay's live production formula
# with a non-integer result. The resulting USD target is then converted by the
# deployed PriceDesk through the exact getAssetAmount call made by
# Deleverage._getMaxAssetAmount. Position-token pricing is also recorded: all
# six disabled assets currently return zero, so the corresponding underlying
# conversion is the nonzero protocol-arithmetic corpus replayed below.
DELEVERAGE_DEBT = 800_123_456_789_012_345
DELEVERAGE_COLLATERAL_VALUE = 900_987_654_321_098_765
DELEVERAGE_TARGET_LTV = 7_800
DELEVERAGE_SCALE = 10_000

TOKEN_ROWS = (
    {
        "symbol": "cAEROv3",
        "token": "0x784efeB622244d2348d4F2522f8860B96fbEcE89",
        "kind": "compound-base-supply",
        "underlying": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
        "decimals": 18,
        "implementation": "0xddbc9dd0e1400e6d8441289e2b5f47b4839350cd",
        "runtime_length": 1_878,
        "runtime_hash": "0x64952234eab8f3aed74355c49119f627965640b1efeb6b28430b5a31b0d3b192",
        "implementation_length": 18_599,
        "implementation_hash": "0xdbf3822c690579e26b22c194dff9c0c795471a9b5934e59cf0b954c2191939ca",
        "pinned_index": 1_100_259_157_657_077,
        "deployed_deposit_config": (
            True, False, True, True, 3_000 * 10**18, 30_000 * 10**18,
            15, 5, False, 10**18,
        ),
        "deployed_min_deposit": 10**18,
        "underlying_donor": "0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6",
        "sender_seed": 2_000 * 10**18,
        "large_recipient_seed": 10 * 10**18,
    },
    {
        "symbol": "aBascbBTC",
        "token": "0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6",
        "kind": "aave-indexed-supply",
        "underlying": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        "decimals": 8,
        "implementation": "0x273e4b97c3f5280aff4949aa19a27ff54968458d",
        "runtime_length": 1_909,
        "runtime_hash": "0x4f2154b879ed2f2db9154d9664b5abfaae3128751c1645c4c17f646316bb8b62",
        "implementation_length": 10_477,
        "implementation_hash": "0xb766d075565868563fa6712eed3c6c90afb71dc004230146eb77d8c6ed721145",
        "pinned_index": 1_002_021_374_940_094_109_315_446_882,
        "deployed_deposit_config": (
            True, False, True, True, 2_500_000, 25_000_000,
            15, 5, False, 25,
        ),
        "deployed_min_deposit": 25,
        "underlying_donor": "0xF877ACaFA28c19b96727966690b2f44d35aD5976",
        "sender_seed": 1_000_000,
        "large_recipient_seed": 100_000,
    },
    {
        "symbol": "aBasUSDC",
        "token": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB",
        "kind": "aave-indexed-supply",
        "underlying": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6,
        "implementation": "0x273e4b97c3f5280aff4949aa19a27ff54968458d",
        "runtime_length": 1_933,
        "runtime_hash": "0x59d2fd2a4bad76f979bc2c1da50504e072f4b3bb64f5429302a384ad9c0706f2",
        "implementation_length": 10_477,
        "implementation_hash": "0xb766d075565868563fa6712eed3c6c90afb71dc004230146eb77d8c6ed721145",
        "pinned_index": 1_142_276_842_837_302_625_037_345_846,
        "deployed_deposit_config": (
            True, False, True, True, 3_000_000_000, 30_000_000_000,
            15, 5, False, 1_000_000,
        ),
        "deployed_min_deposit": 1_000_000,
        "underlying_donor": "0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
        "sender_seed": 2_000 * 10**6,
        "large_recipient_seed": 10 * 10**6,
    },
    {
        "symbol": "aBasWETH",
        "token": "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7",
        "kind": "aave-indexed-supply",
        "underlying": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "implementation": "0x273e4b97c3f5280aff4949aa19a27ff54968458d",
        "runtime_length": 1_933,
        "runtime_hash": "0x59d2fd2a4bad76f979bc2c1da50504e072f4b3bb64f5429302a384ad9c0706f2",
        "implementation_length": 10_477,
        "implementation_hash": "0xb766d075565868563fa6712eed3c6c90afb71dc004230146eb77d8c6ed721145",
        "pinned_index": 1_048_809_605_180_194_069_784_772_579,
        "deployed_deposit_config": (
            True, False, True, True, 800_000_000_000_000_000,
            8_000_000_000_000_000_000, 15, 5, False, 80_000_000_000_000,
        ),
        "deployed_min_deposit": 80_000_000_000_000,
        "underlying_donor": "0x628ff693426583D9a7FB391E54366292F509D457",
        "sender_seed": 10 * 10**18,
        "large_recipient_seed": 10**18,
    },
    {
        "symbol": "cUSDCv3",
        "token": "0xb125E6687d4313864e53df431d5425969c15Eb2F",
        "kind": "compound-base-supply",
        "underlying": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6,
        "implementation": "0x079990620d904fb1fde68b6d54a5f8647134cde9",
        "runtime_length": 1_878,
        "runtime_hash": "0x64952234eab8f3aed74355c49119f627965640b1efeb6b28430b5a31b0d3b192",
        "implementation_length": 18_599,
        "implementation_hash": "0x957e1a5765a79e3306ba4fcbc20c23c0c8df3705bb1d201c9c3e70c3156d4d35",
        "pinned_index": 1_115_151_034_453_416,
        "deployed_deposit_config": (
            True, False, True, True, 6_000_000_000, 60_000_000_000,
            15, 5, False, 10_000,
        ),
        "deployed_min_deposit": 10_000,
        "underlying_donor": "0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
        "sender_seed": 2_000 * 10**6,
        "large_recipient_seed": 10 * 10**6,
    },
    {
        "symbol": "cWETHv3",
        "token": "0x46e6b214b524310239732D51387075E0e70970bf",
        "kind": "compound-base-supply",
        "underlying": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "implementation": "0x23590479b97e93603d43060500a70ef8fd6ec142",
        "runtime_length": 1_878,
        "runtime_hash": "0x64952234eab8f3aed74355c49119f627965640b1efeb6b28430b5a31b0d3b192",
        "implementation_length": 18_599,
        "implementation_hash": "0xf74cb990ffdc007f8f7a1179506a05eef4dd9749ea240df4b05288f9244920d3",
        "pinned_index": 1_051_980_553_867_343,
        "deployed_deposit_config": (
            True, False, True, True, 800_000_000_000_000_000,
            8_000_000_000_000_000_000, 15, 5, False, 80_000_000_000_000,
        ),
        "deployed_min_deposit": 80_000_000_000_000,
        "underlying_donor": "0x628ff693426583D9a7FB391E54366292F509D457",
        "sender_seed": 10 * 10**18,
        "large_recipient_seed": 10**18,
    },
)

REMOTE_BLOCK_IDENTITY = {}


def _row(symbol):
    return next(row for row in TOKEN_ROWS if row["symbol"] == symbol)


def _write_evidence(filename, evidence):
    """Atomically checkpoint evidence so a later assertion keeps prior work."""
    if EVIDENCE_ROOT is None:
        raise RuntimeError("SC-04 evidence root was not initialized")
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_ROOT / filename
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(evidence, indent=2, default=str) + "\n")
    temporary.replace(path)
    return path


def _remote_block_identity(rpc):
    response = requests.post(
        rpc,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBlockByNumber",
            "params": [hex(BASE_BLOCK), False],
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    assert "error" not in payload, payload.get("error")
    block = payload["result"]
    identity = {
        "number": int(block["number"], 16),
        "hash": block["hash"].lower(),
        "timestamp": int(block["timestamp"], 16),
    }
    assert identity == {
        "number": BASE_BLOCK,
        "hash": BASE_BLOCK_HASH,
        "timestamp": BASE_BLOCK_TIMESTAMP,
    }
    return identity


def _runtime_identity(address):
    runtime = bytes(boa.env.get_code(to_checksum_address(address)))
    return {"length": len(runtime), "hash": "0x" + keccak(runtime).hex()}


def _proxy_implementation(address):
    value = boa.env.get_storage(
        to_checksum_address(address), EIP1967_IMPLEMENTATION_SLOT
    )
    return to_checksum_address(value.to_bytes(32, "big")[-20:])


def _compound_exact_recipient_amount(row, index):
    """Smallest index-exact multiple at or above one token/current floor."""
    granularity = index // gcd(index, COMET_INDEX_SCALE)
    target = max(10 ** row["decimals"], row["deployed_min_deposit"])
    amount = ((target + granularity - 1) // granularity) * granularity
    return amount, granularity


def _exact_delta_revert(amount, outflow, inflow):
    if outflow != amount:
        return "invalid vault outflow"
    if inflow != amount:
        return "invalid recipient delivery"
    return None


def _vault_path_state(row, token, user, vault, ledger):
    return {
        "user_shares": vault.userBalances(user, token.address),
        "total_shares": vault.totalBalances(token.address),
        "claim": vault.getTotalAmountForUser(user, token.address),
        "participating": ledger.isParticipatingInVault(user, 4),
        "num_user_vaults": ledger.numUserVaults(user),
        "num_user_assets": vault.getNumUserAssets(user),
        "vault_observable": token.balanceOf(vault.address),
        "recipient_observable": token.balanceOf(user),
        "vault_accounting": _accounting_state(row, vault.address),
        "recipient_accounting": _accounting_state(row, user),
    }


def _function(name, inputs, outputs, mutability="view"):
    return {
        "type": "function",
        "name": name,
        "stateMutability": mutability,
        "inputs": [{"name": f"arg{i}", "type": value} for i, value in enumerate(inputs)],
        "outputs": [{"name": f"out{i}", "type": value} for i, value in enumerate(outputs)],
    }


def _at(name, address, functions):
    return boa.loads_abi(json.dumps(functions), name=name).at(to_checksum_address(address))


def _position_token(row):
    abi = AAVE_TOKEN_ABI if row["kind"] == "aave-indexed-supply" else COMET_ABI
    return _at(f"sc04_position_{row['symbol']}", row["token"], abi)


def _underlying_token(row):
    return _at(f"sc04_underlying_{row['symbol']}", row["underlying"], ERC20_ABI)


def _index(row):
    if row["kind"] == "aave-indexed-supply":
        pool = _at(f"sc04_pool_{row['symbol']}", AAVE_POOL, AAVE_POOL_ABI)
        return pool.getReserveNormalizedIncome(to_checksum_address(row["underlying"]))
    return _position_token(row).totalsBasic()[0]


def _accounting_state(row, account):
    token = _position_token(row)
    if row["kind"] == "aave-indexed-supply":
        return token.scaledBalanceOf(account)
    return token.userBasic(account)[0]


def _source_position(row, user, underlying_amount):
    token = _position_token(row)
    underlying = _underlying_token(row)
    donor = to_checksum_address(row["underlying_donor"])

    assert underlying.balanceOf(donor) >= underlying_amount
    assert underlying.transfer(user, underlying_amount, sender=donor)
    if row["kind"] == "aave-indexed-supply":
        pool = _at(f"sc04_supply_pool_{row['symbol']}", AAVE_POOL, AAVE_POOL_ABI)
        assert underlying.approve(pool.address, underlying_amount, sender=user)
        pool.supply(underlying.address, underlying_amount, user, 0, sender=user)
    else:
        assert underlying.approve(token.address, underlying_amount, sender=user)
        token.supply(underlying.address, underlying_amount, sender=user)
    return token.balanceOf(user)


def _adversarial_underlying_amount(row, index):
    scale = 10**27 if row["kind"] == "aave-indexed-supply" else 10**15
    best_amount = 2
    best_remainder = -1
    for amount in range(2, 100_001):
        if row["kind"] == "aave-indexed-supply":
            accounting_units = (amount * scale + index // 2) // index
        else:
            accounting_units = amount * scale // index
        if accounting_units == 0:
            continue
        remainder = accounting_units * index % scale
        if remainder > best_remainder:
            best_amount = amount
            best_remainder = remainder
    return best_amount


def _amount_corpus(balance, decimals):
    assert balance > 1_000
    values = set(range(1, 1_001))
    rng = random.Random(CORPUS_SEED + decimals)
    max_random = max(1, balance - 17)
    max_exponent = max(0, len(str(max_random)) - 1)
    for _ in range(RANDOM_SAMPLE_COUNT):
        exponent = rng.randint(0, max_exponent)
        upper = min(max_random, 10 ** (exponent + 1) - 1)
        lower = min(upper, 10**exponent)
        values.add(rng.randint(max(1, lower), max(1, upper)))

    unit = 10**decimals
    for boundary in (unit, 10 * unit, 100 * unit):
        for delta in range(-16, 17):
            candidate = boundary + delta
            if 0 < candidate <= balance:
                values.add(candidate)

    for divisor in (2, 3, 5, 7, 10):
        quotient = balance // divisor
        for delta in range(-2, 3):
            candidate = quotient + delta
            if 0 < candidate <= balance:
                values.add(candidate)

    for delta in range(0, 17):
        candidate = balance - delta
        if candidate > 0:
            values.add(candidate)
    return sorted(values)


def _deleverage_target_repay_amount():
    collateral_adjusted = (
        DELEVERAGE_COLLATERAL_VALUE * DELEVERAGE_TARGET_LTV // DELEVERAGE_SCALE
    )
    if DELEVERAGE_DEBT <= collateral_adjusted:
        return DELEVERAGE_DEBT
    return min(
        (DELEVERAGE_DEBT - collateral_adjusted)
        * DELEVERAGE_SCALE
        // (DELEVERAGE_SCALE - DELEVERAGE_TARGET_LTV),
        DELEVERAGE_DEBT,
    )


def _deleverage_derived_amount(row):
    ripe_hq = _at("sc04_ripe_hq", RIPE_HQ, RIPE_HQ_ABI)
    assert ripe_hq.getAddr(7) == PRICE_DESK
    price_desk = _at("sc04_price_desk", PRICE_DESK, PRICE_DESK_ABI)
    target_repay_amount = _deleverage_target_repay_amount()
    position_asset_amount = price_desk.getAssetAmount(
        to_checksum_address(row["token"]), target_repay_amount, True
    )
    underlying_asset_amount = price_desk.getAssetAmount(
        to_checksum_address(row["underlying"]), target_repay_amount, True
    )
    assert position_asset_amount == 0
    assert underlying_asset_amount > 0
    return {
        "debt": DELEVERAGE_DEBT,
        "collateral_value": DELEVERAGE_COLLATERAL_VALUE,
        "target_ltv": DELEVERAGE_TARGET_LTV,
        "target_repay_amount": target_repay_amount,
        "position_asset_amount": position_asset_amount,
        "underlying_asset_amount": underlying_asset_amount,
    }


ERC20_ABI = (
    _function("symbol", (), ("string",)),
    _function("decimals", (), ("uint8",)),
    _function("balanceOf", ("address",), ("uint256",)),
    _function("transfer", ("address", "uint256"), ("bool",), "nonpayable"),
    _function("approve", ("address", "uint256"), ("bool",), "nonpayable"),
)

VAULT_ABI = (
    _function("getNumVaultAssets", (), ("uint256",)),
    _function("vaultAssets", ("uint256",), ("address",)),
    _function("doesVaultHaveAnyFunds", (), ("bool",)),
    _function("totalBalances", ("address",), ("uint256",)),
)

VAULT_BOOK_ABI = (_function("getAddr", ("uint256",), ("address",)),)

RIPE_HQ_ABI = (_function("getAddr", ("uint256",), ("address",)),)

PRICE_DESK_ABI = (
    _function("getAssetAmount", ("address", "uint256", "bool"), ("uint256",)),
)

MISSION_CONTROL_ABI = (
    _function("isSupportedAssetInVault", ("uint256", "address"), ("bool",)),
    _function(
        "getTellerDepositConfig",
        ("uint256", "address", "address"),
        (
            "(bool,bool,bool,bool,uint256,uint256,uint256,uint256,bool,uint256)",
        ),
    ),
)

AAVE_TOKEN_ABI = ERC20_ABI + (
    _function("UNDERLYING_ASSET_ADDRESS", (), ("address",)),
    _function("POOL", (), ("address",)),
    _function("scaledBalanceOf", ("address",), ("uint256",)),
)

AAVE_POOL_ABI = (
    _function("getReserveNormalizedIncome", ("address",), ("uint256",)),
    _function("supply", ("address", "uint256", "address", "uint16"), (), "nonpayable"),
)

COMET_ABI = ERC20_ABI + (
    _function("baseToken", (), ("address",)),
    _function("allow", ("address", "bool"), (), "nonpayable"),
    _function(
        "totalsBasic",
        (),
        ("(uint64,uint64,uint64,uint64,uint104,uint104,uint40,uint8)",),
    ),
    _function(
        "userBasic",
        ("address",),
        ("(int104,uint64,uint64,uint16,uint8)",),
    ),
    _function("supply", ("address", "uint256"), (), "nonpayable"),
)


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def env(pytestconfig, request, tmp_path_factory):
    global EVIDENCE_ROOT

    module_path = Path(__file__).resolve()
    foreign_items = [
        str(item.path)
        for item in request.session.items
        if Path(item.path).resolve() != module_path
    ]
    if foreign_items:
        raise pytest.UsageError(
            "SC-04 owns the session fork and must run alone; foreign selected "
            f"tests include {foreign_items[:3]}"
        )

    configured_evidence_base = os.environ.get(EVIDENCE_BASE_ENV)
    evidence_base = (
        Path(configured_evidence_base).resolve()
        if configured_evidence_base
        else tmp_path_factory.getbasetemp()
    )
    EVIDENCE_ROOT = evidence_base / (
        f"sc04-evidence-{time.time_ns()}-{os.getpid()}"
    )
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=False)
    print(f"SC04_EVIDENCE_ROOT={EVIDENCE_ROOT}")

    rpc = pytestconfig.getoption("--rpc") or os.environ.get(
        "SC04_BASE_RPC_URL", DEFAULT_BASE_RPC
    )
    REMOTE_BLOCK_IDENTITY.clear()
    REMOTE_BLOCK_IDENTITY.update(_remote_block_identity(rpc))
    port = _free_port()
    process = subprocess.Popen(
        [
            "anvil",
            "--silent",
            "--port",
            str(port),
            "--fork-url",
            rpc,
            "--fork-block-number",
            str(BASE_BLOCK),
            "--timestamp",
            str(BASE_BLOCK_TIMESTAMP),
            "--no-rate-limit",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    uri = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise RuntimeError(f"SC-04 Anvil exited during startup: {stderr}")
            try:
                requests.post(
                    uri,
                    json={"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
                    timeout=1,
                ).raise_for_status()
                break
            except requests.RequestException:
                time.sleep(0.1)
        else:
            raise RuntimeError("SC-04 Anvil did not start within 30 seconds")

        with boa.fork(uri, block_identifier=BASE_BLOCK) as forked_env:
            yield forked_env
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)


@pytest.base
@pytest.mark.fork_qualification
def test_deployed_rebase_vault_inventory_and_accounting_identity(env):
    vault_book = _at("sc04_vault_book", VAULT_BOOK, VAULT_BOOK_ABI)
    mission_control = _at("sc04_mission_control", MISSION_CONTROL, MISSION_CONTROL_ABI)
    vault = _at("sc04_deployed_rebase_vault", DEPLOYED_REBASE_VAULT, VAULT_ABI)
    pool = _at("sc04_aave_pool", AAVE_POOL, AAVE_POOL_ABI)
    evidence = {
        "remote_block": REMOTE_BLOCK_IDENTITY,
        "vault_book": VAULT_BOOK,
        "mission_control": MISSION_CONTROL,
        "rebase_vault": DEPLOYED_REBASE_VAULT,
        "does_vault_have_any_funds": vault.doesVaultHaveAnyFunds(),
        "tokens": {},
    }

    assert REMOTE_BLOCK_IDENTITY["hash"] == BASE_BLOCK_HASH
    assert REMOTE_BLOCK_IDENTITY["timestamp"] == BASE_BLOCK_TIMESTAMP
    assert boa.env.evm.patch.block_number == BASE_BLOCK
    assert boa.env.evm.patch.timestamp == BASE_BLOCK_TIMESTAMP
    assert vault_book.getAddr(4) == DEPLOYED_REBASE_VAULT
    assert vault.getNumVaultAssets() == len(TOKEN_ROWS) == 6
    assert not vault.doesVaultHaveAnyFunds()

    for index, row in enumerate(TOKEN_ROWS, start=1):
        token_address = to_checksum_address(row["token"])
        underlying = to_checksum_address(row["underlying"])
        token = _at(f"sc04_{row['symbol']}", token_address, ERC20_ABI)
        token_runtime = _runtime_identity(token_address)
        implementation = _proxy_implementation(token_address)
        implementation_runtime = _runtime_identity(implementation)

        assert vault.vaultAssets(index) == token_address
        assert token.symbol() == row["symbol"]
        assert token.decimals() == row["decimals"]
        assert token_runtime == {
            "length": row["runtime_length"],
            "hash": row["runtime_hash"],
        }
        assert implementation == to_checksum_address(row["implementation"])
        assert implementation_runtime == {
            "length": row["implementation_length"],
            "hash": row["implementation_hash"],
        }
        assert mission_control.isSupportedAssetInVault(4, token_address)
        deposit_config = mission_control.getTellerDepositConfig(4, token_address, env.eoa)
        assert tuple(deposit_config) == row["deployed_deposit_config"]
        assert vault.totalBalances(token_address) == 0

        if row["kind"] == "aave-indexed-supply":
            indexed = _at(f"sc04_indexed_{row['symbol']}", token_address, AAVE_TOKEN_ABI)
            assert indexed.UNDERLYING_ASSET_ADDRESS() == underlying
            assert indexed.POOL() == AAVE_POOL
            normalized_income = pool.getReserveNormalizedIncome(underlying)
            assert normalized_income == row["pinned_index"]
            assert normalized_income > 10**27
            assert normalized_income % 10**27 != 0
            accounting = {
                "mechanism": row["kind"],
                "pool": AAVE_POOL,
                "pinned_index": normalized_income,
                "scale": 10**27,
            }
        else:
            comet = _at(f"sc04_comet_{row['symbol']}", token_address, COMET_ABI)
            assert comet.baseToken() == underlying
            base_supply_index = comet.totalsBasic()[0]
            assert base_supply_index == row["pinned_index"]
            assert base_supply_index > 10**15
            assert base_supply_index % 10**15 != 0
            accounting = {
                "mechanism": row["kind"],
                "comet": token_address,
                "pinned_index": base_supply_index,
                "scale": COMET_INDEX_SCALE,
            }

        evidence["tokens"][row["symbol"]] = {
            "enumeration_index": index,
            "token": token_address,
            "symbol": token.symbol(),
            "decimals": token.decimals(),
            "underlying_or_base": underlying,
            "supported": True,
            "deposit_config": tuple(deposit_config),
            "total_shares": vault.totalBalances(token_address),
            "observable_custody": token.balanceOf(DEPLOYED_REBASE_VAULT),
            "runtime": token_runtime,
            "implementation": implementation,
            "implementation_runtime": implementation_runtime,
            "accounting": accounting,
        }
        _write_evidence("deployed-inventory.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_fail_first_real_token_direct_transfer_matrix(env):
    evidence = {
        "block": BASE_BLOCK,
        "block_hash": BASE_BLOCK_HASH,
        "timestamp": BASE_BLOCK_TIMESTAMP,
        "seed": CORPUS_SEED,
        "random_samples": RANDOM_SAMPLE_COUNT,
        "scope": {
            "layer": "direct token transfer characterization",
            "amounts": "full deterministic corpus",
            "recipient_states": ["zero", "small", "large", "adversarial"],
            "ripe_share_reachability": "not implied by this layer",
        },
        "deleverage_formula": {
            "debt": DELEVERAGE_DEBT,
            "collateral_value": DELEVERAGE_COLLATERAL_VALUE,
            "target_ltv": DELEVERAGE_TARGET_LTV,
            "scale": DELEVERAGE_SCALE,
            "target_repay_amount": _deleverage_target_repay_amount(),
            "price_desk": PRICE_DESK,
        },
        "tokens": {},
    }
    all_mismatches = []

    with boa.env.anchor():
        for row in TOKEN_ROWS:
            with boa.env.anchor():
                token = _position_token(row)
                sender = env.generate_address(f"sc04-direct-sender-{row['symbol']}")
                supplied = row["sender_seed"]
                sender_balance = _source_position(row, sender, supplied)
                assert sender_balance > 1_000
                deleverage_derived = _deleverage_derived_amount(row)
                assert deleverage_derived["underlying_asset_amount"] <= sender_balance

                index = _index(row)
                scale = 10**27 if row["kind"] == "aave-indexed-supply" else 10**15
                recipient_specs = (
                    ("zero", 0),
                    ("small", 1_003),
                    ("large", row["large_recipient_seed"]),
                    ("adversarial", _adversarial_underlying_amount(row, index)),
                )
                token_evidence = {
                    "kind": row["kind"],
                    "index": index,
                    "scale": scale,
                    "index_remainder": index % scale,
                    "sender_balance": sender_balance,
                    "deleverage_derived": deleverage_derived,
                    "recipient_states": {},
                }
                evidence["tokens"][row["symbol"]] = token_evidence

                for state_name, recipient_supply in recipient_specs:
                    with boa.env.anchor():
                        recipient = env.generate_address(
                            f"sc04-direct-recipient-{row['symbol']}-{state_name}"
                        )
                        if recipient_supply:
                            _source_position(row, recipient, recipient_supply)

                        recipient_state = _accounting_state(row, recipient)
                        recipient_remainder = recipient_state * index % scale
                        corpus = sorted(
                            set(_amount_corpus(token.balanceOf(sender), row["decimals"]))
                            | {deleverage_derived["underlying_asset_amount"]}
                        )
                        state_mismatches = []

                        for amount in corpus:
                            with boa.env.anchor():
                                sender_before = token.balanceOf(sender)
                                recipient_before = token.balanceOf(recipient)
                                sender_accounting_before = _accounting_state(row, sender)
                                recipient_accounting_before = _accounting_state(row, recipient)
                                try:
                                    result = token.transfer(recipient, amount, sender=sender)
                                    sender_after = token.balanceOf(sender)
                                    recipient_after = token.balanceOf(recipient)
                                    sender_accounting_after = _accounting_state(row, sender)
                                    recipient_accounting_after = _accounting_state(row, recipient)
                                    outflow = sender_before - sender_after
                                    inflow = recipient_after - recipient_before
                                    if result is not True or outflow != amount or inflow != amount:
                                        mismatch = {
                                            "token": row["symbol"],
                                            "state": state_name,
                                            "amount": amount,
                                            "result": result,
                                            "sender_before": sender_before,
                                            "sender_after": sender_after,
                                            "recipient_before": recipient_before,
                                            "recipient_after": recipient_after,
                                            "outflow": outflow,
                                            "inflow": inflow,
                                            "sender_accounting_before": sender_accounting_before,
                                            "sender_accounting_after": sender_accounting_after,
                                            "recipient_accounting_before": (
                                                recipient_accounting_before
                                            ),
                                            "recipient_accounting_after": (
                                                recipient_accounting_after
                                            ),
                                        }
                                        state_mismatches.append(mismatch)
                                        all_mismatches.append(mismatch)
                                except Exception as exc:
                                    mismatch = {
                                        "token": row["symbol"],
                                        "state": state_name,
                                        "amount": amount,
                                        "revert": type(exc).__name__,
                                        "message": str(exc),
                                    }
                                    state_mismatches.append(mismatch)
                                    all_mismatches.append(mismatch)

                        token_evidence["recipient_states"][state_name] = {
                            "underlying_seed": recipient_supply,
                            "observable_balance": token.balanceOf(recipient),
                            "accounting_state": recipient_state,
                            "fractional_remainder": recipient_remainder,
                            "sample_count": len(corpus),
                            "mismatch_count": len(state_mismatches),
                            "mismatches": state_mismatches,
                        }
                        _write_evidence(
                            "direct-transfer-characterization.json", evidence
                        )

    evidence_path = _write_evidence("direct-transfer-characterization.json", evidence)
    assert not all_mismatches, (
        f"{len(all_mismatches)} exact-delta mismatches; evidence={evidence_path}; "
        f"first={all_mismatches[0]}"
    )


@pytest.base
@pytest.mark.fork_qualification
def test_compound_teller_deposit_custody_mismatch_is_atomic(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    evidence = {}
    with boa.env.anchor():
        setGeneralConfig()
        for row in (item for item in TOKEN_ROWS if item["kind"] == "compound-base-supply"):
            with boa.env.anchor():
                token = _position_token(row)
                user = env.generate_address(f"sc04-compound-depositor-{row['symbol']}")
                _source_position(row, user, row["sender_seed"])
                setAssetConfig(
                    token.address,
                    _vaultIds=[4],
                    _stakersPointsAlloc=0,
                    _voterPointsAlloc=0,
                    _minDepositBalance=0,
                )
                token.allow(teller.address, True, sender=user)
                deleverage_derived = _deleverage_derived_amount(row)
                amounts = sorted(
                    set(range(1, 1_001))
                    | {deleverage_derived["underlying_asset_amount"]}
                )
                failures = []
                first_before = None
                first_after = None
                evidence[row["symbol"]] = {
                    "scope": {
                        "ripe_contracts": "fresh local pinned-source fixtures",
                        "amounts": "raw 1..1000 plus one protocol-derived amount",
                        "vault_prestate": "empty",
                        "local_min_deposit": 0,
                        "deployed_min_deposit": row["deployed_min_deposit"],
                    },
                    "sample_count": len(amounts),
                    "failure_count": 0,
                    "failure_amounts": failures,
                    "deleverage_derived": deleverage_derived,
                }
                for amount in amounts:
                    with boa.env.anchor():
                        before = {
                            "user_observable": token.balanceOf(user),
                            "user_principal": token.userBasic(user)[0],
                            "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                            "vault_principal": token.userBasic(rebase_erc20_vault.address)[0],
                            "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                            "total_shares": rebase_erc20_vault.totalBalances(token.address),
                            "participating": ledger.isParticipatingInVault(user, 4),
                            "num_user_vaults": ledger.numUserVaults(user),
                            "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                        }
                        with pytest.raises(Exception) as exc_info:
                            teller.deposit(
                                token.address,
                                amount,
                                user,
                                rebase_erc20_vault.address,
                                4,
                                sender=user,
                            )
                        assert "custody mismatch" in str(exc_info.value)

                        after = {
                            "user_observable": token.balanceOf(user),
                            "user_principal": token.userBasic(user)[0],
                            "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                            "vault_principal": token.userBasic(rebase_erc20_vault.address)[0],
                            "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                            "total_shares": rebase_erc20_vault.totalBalances(token.address),
                            "participating": ledger.isParticipatingInVault(user, 4),
                            "num_user_vaults": ledger.numUserVaults(user),
                            "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                        }
                        assert after == before
                        failures.append(amount)
                        evidence[row["symbol"]]["failure_count"] = len(failures)
                        if first_before is None:
                            first_before = before
                            first_after = after
                        if len(failures) % 100 == 0:
                            _write_evidence(
                                "compound-teller-atomicity.json", evidence
                            )
                evidence[row["symbol"]] = {
                    "scope": {
                        "ripe_contracts": "fresh local pinned-source fixtures",
                        "amounts": "raw 1..1000 plus one protocol-derived amount",
                        "vault_prestate": "empty",
                        "local_min_deposit": 0,
                        "deployed_min_deposit": row["deployed_min_deposit"],
                    },
                    "sample_count": len(amounts),
                    "failure_count": len(failures),
                    "failure_amounts": failures,
                    "index": token.totalsBasic()[0],
                    "revert": "custody mismatch",
                    "deleverage_derived": deleverage_derived,
                    "first_before": first_before,
                    "first_after": first_after,
                }
                _write_evidence("compound-teller-atomicity.json", evidence)

    _write_evidence("compound-teller-atomicity.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_compound_index_exact_deposit_reaches_real_withdrawal_boundary(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Prove dust failures do not make Compound share creation unreachable."""
    evidence = {}
    mismatch_tokens = []
    with boa.env.anchor():
        setGeneralConfig()
        for row in (
            item for item in TOKEN_ROWS if item["kind"] == "compound-base-supply"
        ):
            with boa.env.anchor():
                token = _position_token(row)
                user = env.generate_address(
                    f"sc04-compound-exact-depositor-{row['symbol']}"
                )
                accrual_actor = env.generate_address(
                    f"sc04-compound-exact-accrual-{row['symbol']}"
                )
                _source_position(row, user, row["sender_seed"])
                setAssetConfig(
                    token.address,
                    _vaultIds=[4],
                    _stakersPointsAlloc=0,
                    _voterPointsAlloc=0,
                    _minDepositBalance=row["deployed_min_deposit"],
                )
                token.allow(teller.address, True, sender=user)

                i0 = _index(row)
                deposit_amount, exact_granularity = _compound_exact_recipient_amount(
                    row, i0
                )
                assert deposit_amount >= row["deployed_min_deposit"]
                assert deposit_amount % exact_granularity == 0

                available_balance = token.balanceOf(user)
                if deposit_amount > available_balance:
                    evidence[row["symbol"]] = {
                        "scope": {
                            "ripe_contracts": "fresh local pinned-source fixtures",
                            "admission": "locally enabled with deployed minimum floor",
                            "funding": "real Comet base-asset supplies",
                        },
                        "deposit": {
                            "i0": i0,
                            "exact_granularity": exact_granularity,
                            "minimum_exact_amount_at_deployed_floor": deposit_amount,
                            "deployed_min_deposit": row["deployed_min_deposit"],
                            "available_real_market_funding": available_balance,
                            "status": (
                                "not executed: minimum exact amount exceeds "
                                "available real-market funding"
                            ),
                        },
                        "coverage_limitation": (
                            "No crafted exact trajectory is claimed for this "
                            "token at the pinned block."
                        ),
                    }
                    _write_evidence(
                        "compound-crafted-reachable-withdrawal.json", evidence
                    )
                    continue

                depositor_before = token.balanceOf(user)
                vault_before = token.balanceOf(rebase_erc20_vault.address)
                depositor_principal_before = token.userBasic(user)[0]
                vault_principal_before = token.userBasic(
                    rebase_erc20_vault.address
                )[0]
                deposited = teller.deposit(
                    token.address,
                    deposit_amount,
                    user,
                    rebase_erc20_vault.address,
                    4,
                    sender=user,
                )
                depositor_after = token.balanceOf(user)
                vault_after = token.balanceOf(rebase_erc20_vault.address)
                depositor_principal_after = token.userBasic(user)[0]
                vault_principal_after = token.userBasic(
                    rebase_erc20_vault.address
                )[0]
                shares_minted = rebase_erc20_vault.userBalances(
                    user, token.address
                )

                assert deposited == deposit_amount
                assert vault_after - vault_before == deposit_amount
                assert shares_minted > 0
                assert ledger.isParticipatingInVault(user, 4)

                boa.env.time_travel(seconds=30 * 24 * 60 * 60)
                accrual_seed = max(
                    exact_granularity, row["large_recipient_seed"] // 100
                )
                _source_position(row, accrual_actor, accrual_seed)
                i1 = _index(row)
                assert i1 > i0
                assert i1 % COMET_INDEX_SCALE != 0

                withdrawal_amount = rebase_erc20_vault.getTotalAmountForUser(
                    user, token.address
                )
                with boa.env.anchor():
                    direct_vault_before = token.balanceOf(
                        rebase_erc20_vault.address
                    )
                    direct_recipient_before = token.balanceOf(user)
                    assert token.transfer(
                        user,
                        withdrawal_amount,
                        sender=rebase_erc20_vault.address,
                    )
                    direct_outflow = direct_vault_before - token.balanceOf(
                        rebase_erc20_vault.address
                    )
                    direct_inflow = (
                        token.balanceOf(user) - direct_recipient_before
                    )

                expected_revert = _exact_delta_revert(
                    withdrawal_amount, direct_outflow, direct_inflow
                )
                before_withdrawal = _vault_path_state(
                    row, token, user, rebase_erc20_vault, ledger
                )
                if expected_revert is None:
                    withdrawn = teller.withdraw(
                        token.address,
                        MAX_UINT256,
                        user,
                        rebase_erc20_vault.address,
                        4,
                        sender=user,
                    )
                    assert withdrawn == withdrawal_amount
                    path = {"success": True, "amount": withdrawn}
                else:
                    mismatch_tokens.append(row["symbol"])
                    with pytest.raises(Exception) as exc_info:
                        teller.withdraw(
                            token.address,
                            MAX_UINT256,
                            user,
                            rebase_erc20_vault.address,
                            4,
                            sender=user,
                        )
                    assert expected_revert in str(exc_info.value)
                    after_withdrawal = _vault_path_state(
                        row, token, user, rebase_erc20_vault, ledger
                    )
                    assert after_withdrawal == before_withdrawal
                    path = {
                        "success": False,
                        "revert": expected_revert,
                        "atomic_before": before_withdrawal,
                        "atomic_after": after_withdrawal,
                    }

                evidence[row["symbol"]] = {
                    "scope": {
                        "ripe_contracts": "fresh local pinned-source fixtures",
                        "admission": "locally enabled with deployed minimum floor",
                        "funding": "real Comet base-asset supplies",
                    },
                    "deposit": {
                        "i0": i0,
                        "exact_granularity": exact_granularity,
                        "amount": deposit_amount,
                        "deployed_min_deposit": row["deployed_min_deposit"],
                        "depositor_before": depositor_before,
                        "depositor_after": depositor_after,
                        "depositor_outflow": depositor_before - depositor_after,
                        "vault_before": vault_before,
                        "vault_after": vault_after,
                        "vault_inflow": vault_after - vault_before,
                        "depositor_principal_before": depositor_principal_before,
                        "depositor_principal_after": depositor_principal_after,
                        "vault_principal_before": vault_principal_before,
                        "vault_principal_after": vault_principal_after,
                        "shares_minted": shares_minted,
                    },
                    "accrual": {
                        "seconds": 30 * 24 * 60 * 60,
                        "market_action": "real Comet supply",
                        "actor_seed": accrual_seed,
                        "i1": i1,
                    },
                    "withdrawal": {
                        "amount": withdrawal_amount,
                        "direct_vault_outflow": direct_outflow,
                        "direct_recipient_inflow": direct_inflow,
                        "path": path,
                    },
                }
                _write_evidence(
                    "compound-crafted-reachable-withdrawal.json", evidence
                )

    assert {"cAEROv3", "cWETHv3"}.issubset(mismatch_tokens)
    _write_evidence("compound-crafted-reachable-withdrawal.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_fail_first_compound_cweth_full_withdrawal_must_succeed_exactly(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Canonical red expectation: a reachable full withdrawal must not lock."""
    row = _row("cWETHv3")
    with boa.env.anchor():
        setGeneralConfig()
        token = _position_token(row)
        user = env.generate_address("sc04-fail-first-compound-cweth-user")
        accrual_actor = env.generate_address(
            "sc04-fail-first-compound-cweth-accrual"
        )
        _source_position(row, user, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=row["deployed_min_deposit"],
        )
        token.allow(teller.address, True, sender=user)

        deposit_amount, exact_granularity = _compound_exact_recipient_amount(
            row, _index(row)
        )
        assert deposit_amount <= token.balanceOf(user)
        teller.deposit(
            token.address,
            deposit_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        assert rebase_erc20_vault.userBalances(user, token.address) > 0
        assert ledger.isParticipatingInVault(user, 4)

        boa.env.time_travel(seconds=30 * 24 * 60 * 60)
        _source_position(
            row,
            accrual_actor,
            max(exact_granularity, row["large_recipient_seed"] // 100),
        )
        withdrawal_amount = rebase_erc20_vault.getTotalAmountForUser(
            user, token.address
        )
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(user)

        # Intentionally unwrapped: the current production-compatible path
        # reverts "invalid vault outflow", making this acceptance test red.
        withdrawn = teller.withdraw(
            token.address,
            MAX_UINT256,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        assert withdrawn == withdrawal_amount
        assert vault_before - token.balanceOf(rebase_erc20_vault.address) == withdrawn
        assert token.balanceOf(user) - recipient_before == withdrawn
        assert rebase_erc20_vault.userBalances(user, token.address) == 0
        assert not ledger.isParticipatingInVault(user, 4)


@pytest.base
@pytest.mark.fork_qualification
def test_aave_teller_deposit_raw_unit_corpus(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    evidence = {}
    with boa.env.anchor():
        setGeneralConfig()
        for row in (item for item in TOKEN_ROWS if item["kind"] == "aave-indexed-supply"):
            with boa.env.anchor():
                token = _position_token(row)
                user = env.generate_address(f"sc04-aave-corpus-depositor-{row['symbol']}")
                _source_position(row, user, row["sender_seed"])
                setAssetConfig(
                    token.address,
                    _vaultIds=[4],
                    _stakersPointsAlloc=0,
                    _voterPointsAlloc=0,
                    _minDepositBalance=0,
                )
                deleverage_derived = _deleverage_derived_amount(row)
                amounts = sorted(
                    set(range(1, 1_001))
                    | {deleverage_derived["underlying_asset_amount"]}
                )

                results = {
                    "sample_count": len(amounts),
                    "success_count": 0,
                    "custody_mismatch_count": 0,
                    "excess_depositor_outflow_count": 0,
                    "success_amounts": [],
                    "custody_mismatch_amounts": [],
                    "excess_depositor_outflows": [],
                }
                scope = {
                    "ripe_contracts": "fresh local pinned-source fixtures",
                    "amounts": "raw 1..1000 plus one protocol-derived amount",
                    "vault_prestate": "empty",
                    "local_min_deposit": 0,
                    "deployed_min_deposit": row["deployed_min_deposit"],
                    "warning": (
                        "successful Teller deposits can silently overcharge the "
                        "depositor because Teller checks only vault inflow"
                    ),
                }
                token_evidence = {
                    "scope": scope,
                    "index": _index(row),
                    "deleverage_derived": deleverage_derived,
                    **results,
                }
                evidence[row["symbol"]] = token_evidence
                for amount in amounts:
                    with boa.env.anchor():
                        assert token.approve(teller.address, amount, sender=user)
                        before = {
                            "user_observable": token.balanceOf(user),
                            "user_scaled": token.scaledBalanceOf(user),
                            "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                            "vault_scaled": token.scaledBalanceOf(rebase_erc20_vault.address),
                            "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                            "total_shares": rebase_erc20_vault.totalBalances(token.address),
                            "participating": ledger.isParticipatingInVault(user, 4),
                        }
                        try:
                            deposited = teller.deposit(
                                token.address,
                                amount,
                                user,
                                rebase_erc20_vault.address,
                                4,
                                sender=user,
                            )
                        except Exception as exc:
                            assert "custody mismatch" in str(exc)
                            after = {
                                "user_observable": token.balanceOf(user),
                                "user_scaled": token.scaledBalanceOf(user),
                                "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                                "vault_scaled": token.scaledBalanceOf(rebase_erc20_vault.address),
                                "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                                "total_shares": rebase_erc20_vault.totalBalances(token.address),
                                "participating": ledger.isParticipatingInVault(user, 4),
                            }
                            assert after == before
                            results["custody_mismatch_count"] += 1
                            results["custody_mismatch_amounts"].append(amount)
                            processed = (
                                results["success_count"]
                                + results["custody_mismatch_count"]
                            )
                            if processed % 100 == 0:
                                token_evidence.update(results)
                                _write_evidence(
                                    "aave-teller-deposit-raw-corpus.json",
                                    evidence,
                                )
                            continue

                        user_after = token.balanceOf(user)
                        vault_after = token.balanceOf(rebase_erc20_vault.address)
                        outflow = before["user_observable"] - user_after
                        inflow = vault_after - before["vault_observable"]
                        shares = rebase_erc20_vault.userBalances(user, token.address)
                        assert deposited == amount
                        assert inflow == amount
                        assert shares > 0
                        assert ledger.isParticipatingInVault(user, 4)
                        results["success_count"] += 1
                        results["success_amounts"].append(amount)
                        if outflow != amount:
                            results["excess_depositor_outflow_count"] += 1
                            results["excess_depositor_outflows"].append(
                                {
                                    "amount": amount,
                                    "outflow": outflow,
                                    "delta": outflow - amount,
                                    "user_scaled_before": before["user_scaled"],
                                    "user_scaled_after": token.scaledBalanceOf(user),
                                    "silent_depositor_overcharge": True,
                                }
                            )

                        processed = (
                            results["success_count"]
                            + results["custody_mismatch_count"]
                        )
                        if processed % 100 == 0:
                            token_evidence.update(results)
                            _write_evidence(
                                "aave-teller-deposit-raw-corpus.json", evidence
                            )

                assert (
                    results["success_count"] + results["custody_mismatch_count"]
                    == len(amounts)
                )
                evidence[row["symbol"]] = {
                    "scope": scope,
                    "index": _index(row),
                    "deleverage_derived": deleverage_derived,
                    **results,
                }
                _write_evidence(
                    "aave-teller-deposit-raw-corpus.json", evidence
                )

    _write_evidence("aave-teller-deposit-raw-corpus.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_aave_successful_teller_deposit_real_accrual_and_withdrawal_trajectory(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    deposit_amounts = {
        "aBascbBTC": 100_000,
        "aBasUSDC": 1_000_000,
        "aBasWETH": 10**18,
    }
    evidence = {}

    with boa.env.anchor():
        setGeneralConfig()
        for row in (item for item in TOKEN_ROWS if item["kind"] == "aave-indexed-supply"):
            with boa.env.anchor():
                token = _position_token(row)
                user = env.generate_address(f"sc04-aave-depositor-{row['symbol']}")
                accrual_actor = env.generate_address(f"sc04-aave-accrual-{row['symbol']}")
                _source_position(row, user, row["sender_seed"])
                setAssetConfig(
                    token.address,
                    _vaultIds=[4],
                    _stakersPointsAlloc=0,
                    _voterPointsAlloc=0,
                    _minDepositBalance=row["deployed_min_deposit"],
                )
                deleverage_derived = _deleverage_derived_amount(row)

                deposit_amount = deposit_amounts[row["symbol"]]
                assert token.approve(teller.address, deposit_amount, sender=user)
                i0 = _index(row)
                depositor_before = token.balanceOf(user)
                vault_before = token.balanceOf(rebase_erc20_vault.address)
                depositor_scaled_before = token.scaledBalanceOf(user)
                vault_scaled_before = token.scaledBalanceOf(rebase_erc20_vault.address)

                deposited = teller.deposit(
                    token.address,
                    deposit_amount,
                    user,
                    rebase_erc20_vault.address,
                    4,
                    sender=user,
                )
                depositor_after = token.balanceOf(user)
                vault_after = token.balanceOf(rebase_erc20_vault.address)
                depositor_scaled_after = token.scaledBalanceOf(user)
                vault_scaled_after = token.scaledBalanceOf(
                    rebase_erc20_vault.address
                )
                shares_minted = rebase_erc20_vault.userBalances(user, token.address)
                total_shares = rebase_erc20_vault.totalBalances(token.address)

                assert deposited == deposit_amount
                assert vault_after - vault_before == deposit_amount
                assert depositor_before - depositor_after == deposit_amount + 1
                assert shares_minted > 0
                assert total_shares == shares_minted
                assert ledger.isParticipatingInVault(user, 4)

                boa.env.time_travel(seconds=30 * 24 * 60 * 60)
                accrual_seed = max(10_000, row["large_recipient_seed"] // 100)
                _source_position(row, accrual_actor, accrual_seed)
                i1 = _index(row)
                assert i1 > i0
                assert i1 % 10**27 != 0

                withdrawal_amount = rebase_erc20_vault.getTotalAmountForUser(
                    user, token.address
                )
                recipient_before = token.balanceOf(user)
                recipient_scaled_before = token.scaledBalanceOf(user)
                vault_before_withdrawal = token.balanceOf(rebase_erc20_vault.address)
                vault_scaled_before_withdrawal = token.scaledBalanceOf(
                    rebase_erc20_vault.address
                )

                partial_results = {
                    "sample_count": 0,
                    "success_count": 0,
                    "mismatch_count": 0,
                    "mismatches": [],
                    "deleverage_derived_amount": deleverage_derived[
                        "underlying_asset_amount"
                    ],
                }
                token_evidence = {
                    "scope": {
                        "ripe_contracts": "fresh local pinned-source fixtures",
                        "admission": "locally enabled with deployed minimum floor",
                        "local_min_deposit": row["deployed_min_deposit"],
                        "withdrawal_recipient_state": (
                            "depositor's real remainder-bearing residual balance"
                        ),
                        "partial_amounts": (
                            "raw 1..1000 plus one protocol-derived amount"
                        ),
                        "not_covered_here": (
                            "direct layer's zero/small/large/adversarial "
                            "recipient cross-product"
                        ),
                        "cleanup_scope": (
                            "local zero staker/voter points allocation; one-call "
                            "Lootbox cleanup is not generalized to production "
                            "nonzero points"
                        ),
                    },
                    "deleverage_derived": deleverage_derived,
                    "deposit": {
                        "i0": i0,
                        "amount": deposit_amount,
                        "depositor_before": depositor_before,
                        "depositor_after": depositor_after,
                        "depositor_outflow": depositor_before - depositor_after,
                        "vault_before": vault_before,
                        "vault_after": vault_after,
                        "vault_inflow": vault_after - vault_before,
                        "depositor_scaled_before": depositor_scaled_before,
                        "depositor_scaled_after": depositor_scaled_after,
                        "vault_scaled_before": vault_scaled_before,
                        "vault_scaled_after": vault_scaled_after,
                        "shares_minted": shares_minted,
                        "silent_depositor_overcharge": (
                            depositor_before - depositor_after != deposit_amount
                        ),
                    },
                    "accrual": {
                        "seconds": 30 * 24 * 60 * 60,
                        "market_action": "real Aave Pool supply",
                        "actor_seed": accrual_seed,
                        "i1": i1,
                    },
                    "withdrawal": {
                        "amount": withdrawal_amount,
                        "vault_before": vault_before_withdrawal,
                        "recipient_before": recipient_before,
                        "vault_scaled_before": vault_scaled_before_withdrawal,
                        "recipient_scaled_before": recipient_scaled_before,
                        "partial_raw_unit_corpus": partial_results,
                    },
                }
                evidence[row["symbol"]] = token_evidence
                _write_evidence(
                    "aave-deposit-accrual-withdrawal.json", evidence
                )
                partial_amounts = sorted(
                    set(range(1, 1_001))
                    | {deleverage_derived["underlying_asset_amount"]}
                )
                for partial_amount in partial_amounts:
                    if partial_amount >= withdrawal_amount:
                        break
                    partial_results["sample_count"] += 1
                    with boa.env.anchor():
                        direct_vault_before = token.balanceOf(rebase_erc20_vault.address)
                        direct_recipient_before = token.balanceOf(user)
                        assert token.transfer(
                            user,
                            partial_amount,
                            sender=rebase_erc20_vault.address,
                        )
                        direct_outflow = direct_vault_before - token.balanceOf(
                            rebase_erc20_vault.address
                        )
                        direct_inflow = token.balanceOf(user) - direct_recipient_before

                    if direct_outflow != partial_amount:
                        partial_expected_revert = "invalid vault outflow"
                    elif direct_inflow != partial_amount:
                        partial_expected_revert = "invalid recipient delivery"
                    else:
                        partial_expected_revert = None

                    with boa.env.anchor():
                        shares_before_partial = rebase_erc20_vault.userBalances(
                            user, token.address
                        )
                        total_shares_before_partial = rebase_erc20_vault.totalBalances(
                            token.address
                        )
                        vault_before_partial = token.balanceOf(rebase_erc20_vault.address)
                        recipient_before_partial = token.balanceOf(user)
                        ledger_before_partial = (
                            ledger.isParticipatingInVault(user, 4),
                            ledger.numUserVaults(user),
                            rebase_erc20_vault.getNumUserAssets(user),
                        )
                        if partial_expected_revert is None:
                            expected_shares = rebase_erc20_vault.amountToShares(
                                token.address, partial_amount, True
                            )
                            withdrawn = teller.withdraw(
                                token.address,
                                partial_amount,
                                user,
                                rebase_erc20_vault.address,
                                4,
                                sender=user,
                            )
                            assert withdrawn == partial_amount
                            assert (
                                vault_before_partial
                                - token.balanceOf(rebase_erc20_vault.address)
                                == partial_amount
                            )
                            assert (
                                token.balanceOf(user) - recipient_before_partial
                                == partial_amount
                            )
                            assert (
                                shares_before_partial
                                - rebase_erc20_vault.userBalances(user, token.address)
                                == expected_shares
                            )
                            partial_results["success_count"] += 1
                        else:
                            with pytest.raises(Exception) as exc_info:
                                teller.withdraw(
                                    token.address,
                                    partial_amount,
                                    user,
                                    rebase_erc20_vault.address,
                                    4,
                                    sender=user,
                                )
                            assert partial_expected_revert in str(exc_info.value)
                            assert (
                                rebase_erc20_vault.userBalances(user, token.address)
                                == shares_before_partial
                            )
                            assert (
                                rebase_erc20_vault.totalBalances(token.address)
                                == total_shares_before_partial
                            )
                            assert (
                                token.balanceOf(rebase_erc20_vault.address)
                                == vault_before_partial
                            )
                            assert token.balanceOf(user) == recipient_before_partial
                            assert (
                                ledger.isParticipatingInVault(user, 4),
                                ledger.numUserVaults(user),
                                rebase_erc20_vault.getNumUserAssets(user),
                            ) == ledger_before_partial
                            partial_results["mismatch_count"] += 1
                            partial_results["mismatches"].append(
                                {
                                    "amount": partial_amount,
                                    "vault_outflow": direct_outflow,
                                    "recipient_inflow": direct_inflow,
                                    "revert": partial_expected_revert,
                                }
                            )

                    if partial_results["sample_count"] % 100 == 0:
                        _write_evidence(
                            "aave-deposit-accrual-withdrawal.json", evidence
                        )

                assert (
                    partial_results["success_count"]
                    + partial_results["mismatch_count"]
                    == partial_results["sample_count"]
                )

                with boa.env.anchor():
                    assert token.transfer(
                        user,
                        withdrawal_amount,
                        sender=rebase_erc20_vault.address,
                    )
                    direct_vault_after = token.balanceOf(rebase_erc20_vault.address)
                    direct_recipient_after = token.balanceOf(user)
                    direct = {
                        "vault_outflow": vault_before_withdrawal - direct_vault_after,
                        "recipient_inflow": direct_recipient_after - recipient_before,
                        "vault_scaled_after": token.scaledBalanceOf(
                            rebase_erc20_vault.address
                        ),
                        "recipient_scaled_after": token.scaledBalanceOf(user),
                    }

                if direct["vault_outflow"] != withdrawal_amount:
                    expected_revert = "invalid vault outflow"
                elif direct["recipient_inflow"] != withdrawal_amount:
                    expected_revert = "invalid recipient delivery"
                else:
                    expected_revert = None

                atomic_before = {
                    "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                    "total_shares": rebase_erc20_vault.totalBalances(token.address),
                    "vault_data_balance": rebase_erc20_vault.totalBalances(token.address),
                    "participating": ledger.isParticipatingInVault(user, 4),
                    "num_user_vaults": ledger.numUserVaults(user),
                    "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                    "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                    "recipient_observable": token.balanceOf(user),
                    "vault_scaled": token.scaledBalanceOf(rebase_erc20_vault.address),
                    "recipient_scaled": token.scaledBalanceOf(user),
                }
                if expected_revert is None:
                    withdrawn = teller.withdraw(
                        token.address,
                        MAX_UINT256,
                        user,
                        rebase_erc20_vault.address,
                        4,
                        sender=user,
                    )
                    assert withdrawn == withdrawal_amount
                    depletion = {
                        "user_shares": rebase_erc20_vault.userBalances(
                            user, token.address
                        ),
                        "total_shares": rebase_erc20_vault.totalBalances(
                            token.address
                        ),
                        "remaining_claim": rebase_erc20_vault.getTotalAmountForUser(
                            user, token.address
                        ),
                        "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                        "participating": ledger.isParticipatingInVault(user, 4),
                        "user_asset_registered": rebase_erc20_vault.isUserInVaultAsset(
                            user, token.address
                        ),
                        "vault_observable_dust": token.balanceOf(
                            rebase_erc20_vault.address
                        ),
                    }
                    assert depletion["user_shares"] == 0
                    assert depletion["total_shares"] == 0
                    assert depletion["remaining_claim"] == 0
                    # Teller updates reward points on withdrawal; Lootbox owns
                    # later registration cleanup so claimable points are not
                    # orphaned. This fixture deliberately assigns zero staker
                    # and voter points, so one claim can clean immediately;
                    # production-nonzero points can require later claims.
                    assert depletion["num_user_assets"] == 1
                    assert depletion["participating"]
                    assert depletion["user_asset_registered"]

                    claimed_loot = teller.claimLoot(user, False, sender=user)
                    cleanup = {
                        "scope": (
                            "one-call cleanup under local zero staker/voter "
                            "points allocation"
                        ),
                        "claimed_loot": claimed_loot,
                        "num_user_assets": rebase_erc20_vault.getNumUserAssets(
                            user
                        ),
                        "participating": ledger.isParticipatingInVault(user, 4),
                        "user_asset_registered": (
                            rebase_erc20_vault.isUserInVaultAsset(
                                user, token.address
                            )
                        ),
                    }
                    assert cleanup["num_user_assets"] == 0
                    assert not cleanup["participating"]
                    assert not cleanup["user_asset_registered"]
                    path_result = {
                        "success": True,
                        "amount": withdrawn,
                        "depletion": depletion,
                        "deferred_registration_cleanup": cleanup,
                    }
                else:
                    with pytest.raises(Exception) as exc_info:
                        teller.withdraw(
                            token.address,
                            MAX_UINT256,
                            user,
                            rebase_erc20_vault.address,
                            4,
                            sender=user,
                        )
                    assert expected_revert in str(exc_info.value)
                    atomic_after = {
                        "user_shares": rebase_erc20_vault.userBalances(user, token.address),
                        "total_shares": rebase_erc20_vault.totalBalances(token.address),
                        "vault_data_balance": rebase_erc20_vault.totalBalances(token.address),
                        "participating": ledger.isParticipatingInVault(user, 4),
                        "num_user_vaults": ledger.numUserVaults(user),
                        "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                        "vault_observable": token.balanceOf(rebase_erc20_vault.address),
                        "recipient_observable": token.balanceOf(user),
                        "vault_scaled": token.scaledBalanceOf(rebase_erc20_vault.address),
                        "recipient_scaled": token.scaledBalanceOf(user),
                    }
                    assert atomic_after == atomic_before
                    path_result = {
                        "success": False,
                        "revert": expected_revert,
                        "atomic_before": atomic_before,
                        "atomic_after": atomic_after,
                    }

                token_evidence["withdrawal"].update(
                    {"direct": direct, "path": path_result}
                )
                _write_evidence(
                    "aave-deposit-accrual-withdrawal.json", evidence
                )

    _write_evidence("aave-deposit-accrual-withdrawal.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_fail_first_aave_usdc_deposit_must_charge_exact_requested_amount(
    env,
    teller,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Canonical red expectation for the silent depositor overcharge."""
    row = _row("aBasUSDC")
    deposit_amount = 1_000_000
    with boa.env.anchor():
        setGeneralConfig()
        token = _position_token(row)
        user = env.generate_address("sc04-fail-first-aave-usdc-depositor")
        _source_position(row, user, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=row["deployed_min_deposit"],
        )
        assert token.approve(teller.address, deposit_amount, sender=user)
        user_before = token.balanceOf(user)
        vault_before = token.balanceOf(rebase_erc20_vault.address)

        deposited = teller.deposit(
            token.address,
            deposit_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        assert deposited == deposit_amount
        assert (
            user_before - token.balanceOf(user) == deposit_amount
        ), "Aave depositor was silently charged more than the requested amount"
        assert (
            token.balanceOf(rebase_erc20_vault.address) - vault_before
            == deposit_amount
        )


@pytest.base
@pytest.mark.fork_qualification
def test_fail_first_aave_usdc_partial_withdrawal_must_deliver_exact_amount(
    env,
    teller,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Canonical red expectation for a representative withdrawal mismatch."""
    row = _row("aBasUSDC")
    deposit_amount = 1_000_000
    withdrawal_amount = 3
    with boa.env.anchor():
        setGeneralConfig()
        token = _position_token(row)
        user = env.generate_address("sc04-fail-first-aave-usdc-withdrawer")
        accrual_actor = env.generate_address(
            "sc04-fail-first-aave-usdc-accrual"
        )
        _source_position(row, user, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=row["deployed_min_deposit"],
        )
        assert token.approve(teller.address, deposit_amount, sender=user)
        teller.deposit(
            token.address,
            deposit_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )

        boa.env.time_travel(seconds=30 * 24 * 60 * 60)
        _source_position(
            row,
            accrual_actor,
            max(10_000, row["large_recipient_seed"] // 100),
        )
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(user)

        # Intentionally unwrapped: this currently reverts
        # "invalid recipient delivery" for the pinned state.
        withdrawn = teller.withdraw(
            token.address,
            withdrawal_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        assert withdrawn == withdrawal_amount
        assert vault_before - token.balanceOf(rebase_erc20_vault.address) == withdrawn
        assert token.balanceOf(user) - recipient_before == withdrawn
