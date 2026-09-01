"""SC-04 exact-token qualification against the pinned Base deployment.

Run this module by itself. The repository's default marker expression excludes
``fork_qualification`` and would otherwise produce a vacuous zero-test run::

    pytest -q -s --fork base -m fork_qualification -p no:cacheprovider \
        tests/vaults/fork/test_shares_vault_exact_token_qualification.py

Commit ``80052e41`` preserved the pre-fix ``4 failed, 5 passed`` polarity and
its evidence corpus. This post-fix module turns those four cases into passing
directional characterizations and compatibility-path acceptance tests.

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

from conf_utils import clear_transient_storage, filter_logs


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
        "user_asset_registered": vault.isUserInVaultAsset(user, token.address),
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


def _predict_transfer(row, index, amount, sender_balance, recipient_balance,
                      sender_accounting, recipient_accounting):
    """Mirror the deployed indexed-token transfer math from pre-state."""
    if row["kind"] == "aave-indexed-supply":
        scale = 10**27
        accounting_amount = (amount * scale + index - 1) // index
        sender_accounting_after = sender_accounting - accounting_amount
        recipient_accounting_after = recipient_accounting + accounting_amount
    else:
        scale = COMET_INDEX_SCALE
        sender_accounting_after = (sender_balance - amount) * scale // index
        recipient_accounting_after = (
            (recipient_balance + amount) * scale // index
        )
    sender_after = sender_accounting_after * index // scale
    recipient_after = recipient_accounting_after * index // scale
    return {
        "transfer_amount": amount,
        "sender_after": sender_after,
        "recipient_after": recipient_after,
        "sender_accounting_after": sender_accounting_after,
        "recipient_accounting_after": recipient_accounting_after,
        "outflow": sender_balance - sender_after,
        "inflow": recipient_after - recipient_balance,
    }


def _compatible_plan(row, index, nominal, sender_balance, recipient_balance,
                     sender_accounting, recipient_accounting, is_full):
    """Model the governance-admitted Rebase vault's direct transfer."""
    plan = _predict_transfer(
        row,
        index,
        nominal,
        sender_balance,
        recipient_balance,
        sender_accounting,
        recipient_accounting,
    )
    valid = (
        abs(plan["outflow"] - nominal) <= 2
        and abs(plan["inflow"] - nominal) <= 2
    )
    return plan if valid else None


def _exact_deposit_amount(row, token, sender, vault, target):
    """Find a nearby amount whose modeled recipient custody inflow is exact."""
    index = _index(row)
    sender_balance = token.balanceOf(sender)
    recipient_balance = token.balanceOf(vault)
    sender_accounting = _accounting_state(row, sender)
    recipient_accounting = _accounting_state(row, vault)
    for amount in range(target, target + 10_000):
        if amount > sender_balance:
            break
        plan = _predict_transfer(
            row,
            index,
            amount,
            sender_balance,
            recipient_balance,
            sender_accounting,
            recipient_accounting,
        )
        if plan["inflow"] == amount:
            return amount
    raise AssertionError("no nearby exact-custody deposit amount")


def _preserves_remaining_claim(total_shares, withdrawal_shares,
                               vault_balance, vault_outflow):
    remaining_shares = total_shares - withdrawal_shares
    if remaining_shares == 0:
        return True
    claim_before = (
        remaining_shares * (vault_balance + 1) // (total_shares + 10**8)
    )
    claim_after = (
        remaining_shares * (vault_balance - vault_outflow + 1)
        // (remaining_shares + 10**8)
    )
    return claim_after >= claim_before


def _claim_from_shares(shares, total_shares, vault_balance):
    if shares == 0 or total_shares == 0:
        return 0
    return shares * (vault_balance + 1) // (total_shares + 10**8)


def _comet_attainable_exit_plans(
    row,
    token,
    vault,
    exiting_user,
    theoretical_claim,
    vault_balance,
    recipient_balance,
    user_shares,
    total_shares,
):
    """Find the highest real-Comet delivery that conserves the peer claim.

    Compound's balance is principal times index, rounded down. Searching the
    64 base units immediately below the theoretical share claim is exhaustive
    for the observed boundary by a wide margin: the admitted transfer delta is
    two units and the pinned/current Comet index is less than two scale units.
    The first result models burning every exiting share; the second is already
    executable by the current partial-withdrawal path and therefore retains
    only the shares its actual vault outflow consumes.
    """
    index = _index(row)
    vault_principal = token.userBasic(vault.address)[0]
    recipient_principal = token.userBasic(exiting_user)[0]
    remaining_shares = total_shares - user_shares
    remaining_claim_before = _claim_from_shares(
        remaining_shares, total_shares, vault_balance
    )
    full_burn_candidates = []
    current_path_candidates = []
    lower_bound = max(1, theoretical_claim - 64)
    for transfer_argument in range(theoretical_claim, lower_bound - 1, -1):
        plan = _predict_transfer(
            row,
            index,
            transfer_argument,
            vault_balance,
            recipient_balance,
            vault_principal,
            recipient_principal,
        )
        if (
            abs(plan["outflow"] - transfer_argument) > 2
            or abs(plan["inflow"] - transfer_argument) > 2
            or plan["inflow"] > theoretical_claim
            or plan["outflow"] == 0
        ):
            continue
        shares_required = vault.amountToShares(
            token.address, plan["outflow"], True
        )
        remaining_claim_after_full_burn = _claim_from_shares(
            remaining_shares,
            remaining_shares,
            vault_balance - plan["outflow"],
        )
        candidate = {
            **plan,
            "index": index,
            "shares_required": shares_required,
            "remaining_claim_before": remaining_claim_before,
            "remaining_claim_after_full_burn": remaining_claim_after_full_burn,
            "full_burn_safe": (
                remaining_claim_after_full_burn >= remaining_claim_before
            ),
        }
        if candidate["full_burn_safe"]:
            full_burn_candidates.append(candidate)
        if (
            transfer_argument < theoretical_claim
            and shares_required <= user_shares
            and _preserves_remaining_claim(
                total_shares,
                shares_required,
                vault_balance,
                plan["outflow"],
            )
        ):
            current_path_candidates.append(candidate)

    assert full_burn_candidates
    assert current_path_candidates
    best_full_burn = max(
        full_burn_candidates,
        key=lambda candidate: (
            candidate["inflow"], candidate["transfer_amount"]
        ),
    )
    best_current_path = max(
        current_path_candidates,
        key=lambda candidate: (
            candidate["inflow"], candidate["transfer_amount"]
        ),
    )
    return best_full_burn, best_current_path


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
            accounting_units = (amount * scale + index - 1) // index
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
    _function("getUsdValue", ("address", "uint256", "bool"), ("uint256",)),
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
    _function("accrueAccount", ("address",), (), "nonpayable"),
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
def test_real_token_direct_transfer_model_characterization(env):
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
    model_failures = []

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
                                    predicted = _predict_transfer(
                                        row,
                                        index,
                                        amount,
                                        sender_before,
                                        recipient_before,
                                        sender_accounting_before,
                                        recipient_accounting_before,
                                    )
                                    realized = {
                                        "transfer_amount": amount,
                                        "sender_after": sender_after,
                                        "recipient_after": recipient_after,
                                        "sender_accounting_after": sender_accounting_after,
                                        "recipient_accounting_after": recipient_accounting_after,
                                        "outflow": outflow,
                                        "inflow": inflow,
                                    }
                                    if realized != predicted:
                                        model_failures.append(
                                            {
                                                "token": row["symbol"],
                                                "state": state_name,
                                                "amount": amount,
                                                "predicted": predicted,
                                                "realized": realized,
                                            }
                                        )
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
    assert all_mismatches, "the pinned indexed-token corpus unexpectedly became exact"
    assert not model_failures, (
        f"{len(model_failures)} deployed-model mismatches; evidence={evidence_path}; "
        f"first={model_failures[0]}"
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
    executed_tokens = []
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
                vault_withdraw_before = token.balanceOf(
                    rebase_erc20_vault.address
                )
                recipient_withdraw_before = token.balanceOf(user)
                vault_principal_withdraw_before = token.userBasic(
                    rebase_erc20_vault.address
                )[0]
                recipient_principal_withdraw_before = token.userBasic(user)[0]
                plan = _compatible_plan(
                    row,
                    i1,
                    withdrawal_amount,
                    vault_withdraw_before,
                    recipient_withdraw_before,
                    vault_principal_withdraw_before,
                    recipient_principal_withdraw_before,
                    True,
                )
                assert plan is not None
                before_withdrawal = _vault_path_state(
                    row, token, user, rebase_erc20_vault, ledger
                )
                withdrawn = teller.withdraw(
                    token.address,
                    MAX_UINT256,
                    user,
                    rebase_erc20_vault.address,
                    4,
                    sender=user,
                )
                direct_outflow = vault_withdraw_before - token.balanceOf(
                    rebase_erc20_vault.address
                )
                direct_inflow = token.balanceOf(user) - recipient_withdraw_before
                assert withdrawn == direct_outflow == plan["outflow"]
                assert direct_inflow == plan["inflow"]
                assert withdrawal_amount - direct_inflow <= 2
                assert rebase_erc20_vault.userBalances(user, token.address) == 0
                assert rebase_erc20_vault.getTotalAmountForUser(user, token.address) == 0
                executed_tokens.append(row["symbol"])
                path = {
                    "success": True,
                    "reported_custody_outflow": withdrawn,
                    "recipient_delivery": direct_inflow,
                    "theoretical_nominal": withdrawal_amount,
                    "maximum_attainable_delivery": plan["inflow"],
                    "transfer_argument": plan["transfer_amount"],
                    "exiting_user_difference": withdrawal_amount - direct_inflow,
                    "before": before_withdrawal,
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

    assert "cWETHv3" in executed_tokens
    _write_evidence("compound-crafted-reachable-withdrawal.json", evidence)


@pytest.base
@pytest.mark.fork_qualification
def test_compound_cweth_full_withdrawal_delivers_maximum_attainable_claim(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Real Comet accrual cannot trap the sole holder at a rounding boundary."""
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
        partial_amount = 10 ** 17
        partial_shares_before = rebase_erc20_vault.userBalances(
            user, token.address
        )
        partial_vault_before = token.balanceOf(rebase_erc20_vault.address)
        partial_recipient_before = token.balanceOf(user)
        partial_withdrawn = teller.withdraw(
            token.address,
            partial_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        partial_outflow = partial_vault_before - token.balanceOf(
            rebase_erc20_vault.address
        )
        partial_delivery = token.balanceOf(user) - partial_recipient_before
        assert partial_withdrawn == partial_outflow
        assert abs(partial_outflow - partial_amount) <= 2
        assert abs(partial_delivery - partial_amount) <= 2
        assert 0 < rebase_erc20_vault.userBalances(
            user, token.address
        ) < partial_shares_before
        boa.env.time_travel(blocks=1)

        withdrawal_amount = rebase_erc20_vault.getTotalAmountForUser(
            user, token.address
        )
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(user)

        withdrawn = teller.withdraw(
            token.address,
            MAX_UINT256,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        )
        vault_outflow = vault_before - token.balanceOf(rebase_erc20_vault.address)
        recipient_delivery = token.balanceOf(user) - recipient_before
        assert withdrawn == vault_outflow
        assert abs(vault_outflow - withdrawal_amount) <= 2
        assert abs(recipient_delivery - withdrawal_amount) <= 2
        assert rebase_erc20_vault.userBalances(user, token.address) == 0
        assert rebase_erc20_vault.totalBalances(token.address) == 0
        assert rebase_erc20_vault.getTotalAmountForUser(user, token.address) == 0

        vault_event = filter_logs(
            teller, "RebaseErc20VaultWithdrawal"
        )[-1]
        teller_event = filter_logs(teller, "TellerWithdrawal")[-1]
        assert vault_event.amount == vault_outflow
        assert teller_event.amount == vault_outflow

        # Registration cleanup is deferred only while Lootbox owns claimable
        # deposit-point state; the normal claim path removes it.
        teller.claimLoot(user, False, sender=user)
        assert not ledger.isParticipatingInVault(user, 4)
        assert not rebase_erc20_vault.isUserInVaultAsset(user, token.address)


@pytest.base
@pytest.mark.fork_qualification
def test_indexed_multi_holder_repetition_preserves_remaining_claims(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Repeated bounded withdrawals cannot externalize rounding to peers."""
    clear_transient_storage()
    with boa.env.anchor():
        setGeneralConfig()
        row = _row("aBasUSDC")
        token = _position_token(row)
        alice = env.generate_address("sc04-aave-repeat-alice")
        bob = env.generate_address("sc04-aave-repeat-bob")
        accrual_actor = env.generate_address("sc04-aave-repeat-accrual")
        for account in (alice, bob):
            _source_position(row, account, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
        )
        for account in (alice, bob):
            deposit_amount = _exact_deposit_amount(
                row,
                token,
                account,
                rebase_erc20_vault.address,
                1_000_000,
            )
            assert token.approve(teller.address, deposit_amount, sender=account)
            assert teller.deposit(
                token.address,
                deposit_amount,
                account,
                rebase_erc20_vault.address,
                4,
                sender=account,
            ) == deposit_amount

        boa.env.time_travel(seconds=30 * 24 * 60 * 60)
        _source_position(row, accrual_actor, 100_000)
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
            _canDeposit=False,
        )
        cumulative_reported = 0
        cumulative_vault_outflow = 0
        success_count = 0
        fail_closed_count = 0
        for withdrawing_user, remaining_user in ((alice, bob), (bob, alice)):
            for amount in range(1, 49):
                remaining_claim_before = rebase_erc20_vault.getTotalAmountForUser(
                    remaining_user, token.address
                )
                shares_before = rebase_erc20_vault.userBalances(
                    withdrawing_user, token.address
                )
                remaining_shares_before = rebase_erc20_vault.userBalances(
                    remaining_user, token.address
                )
                total_shares_before = rebase_erc20_vault.totalBalances(
                    token.address
                )
                vault_before = token.balanceOf(rebase_erc20_vault.address)
                recipient_before = token.balanceOf(withdrawing_user)
                state_before = (
                    shares_before,
                    remaining_shares_before,
                    total_shares_before,
                    vault_before,
                    recipient_before,
                    ledger.isParticipatingInVault(withdrawing_user, 4),
                    ledger.isParticipatingInVault(remaining_user, 4),
                )
                plan = _compatible_plan(
                    row,
                    _index(row),
                    amount,
                    vault_before,
                    recipient_before,
                    token.scaledBalanceOf(rebase_erc20_vault.address),
                    token.scaledBalanceOf(withdrawing_user),
                    False,
                )
                if plan is None:
                    with pytest.raises(Exception):
                        teller.withdraw(
                            token.address,
                            amount,
                            withdrawing_user,
                            rebase_erc20_vault.address,
                            4,
                            sender=withdrawing_user,
                        )
                    assert (
                        rebase_erc20_vault.userBalances(
                            withdrawing_user, token.address
                        ),
                        rebase_erc20_vault.userBalances(
                            remaining_user, token.address
                        ),
                        rebase_erc20_vault.totalBalances(token.address),
                        token.balanceOf(rebase_erc20_vault.address),
                        token.balanceOf(withdrawing_user),
                        ledger.isParticipatingInVault(withdrawing_user, 4),
                        ledger.isParticipatingInVault(remaining_user, 4),
                    ) == state_before
                    fail_closed_count += 1
                    boa.env.time_travel(blocks=1)
                    continue
                expected_shares = rebase_erc20_vault.amountToShares(
                    token.address, plan["outflow"], True
                )
                if not _preserves_remaining_claim(
                    total_shares_before,
                    expected_shares,
                    vault_before,
                    plan["outflow"],
                ):
                    with pytest.raises(Exception):
                        teller.withdraw(
                            token.address,
                            amount,
                            withdrawing_user,
                            rebase_erc20_vault.address,
                            4,
                            sender=withdrawing_user,
                        )
                    assert (
                        rebase_erc20_vault.userBalances(
                            withdrawing_user, token.address
                        ),
                        rebase_erc20_vault.userBalances(
                            remaining_user, token.address
                        ),
                        rebase_erc20_vault.totalBalances(token.address),
                        token.balanceOf(rebase_erc20_vault.address),
                        token.balanceOf(withdrawing_user),
                        ledger.isParticipatingInVault(withdrawing_user, 4),
                        ledger.isParticipatingInVault(remaining_user, 4),
                    ) == state_before
                    fail_closed_count += 1
                    boa.env.time_travel(blocks=1)
                    continue
                withdrawn = teller.withdraw(
                    token.address,
                    amount,
                    withdrawing_user,
                    rebase_erc20_vault.address,
                    4,
                    sender=withdrawing_user,
                )
                vault_outflow = vault_before - token.balanceOf(
                    rebase_erc20_vault.address
                )
                recipient_delivery = (
                    token.balanceOf(withdrawing_user) - recipient_before
                )
                assert withdrawn == vault_outflow == plan["outflow"]
                assert recipient_delivery == plan["inflow"]
                assert abs(recipient_delivery - amount) <= 2
                assert abs(vault_outflow - amount) <= 2
                assert (
                    shares_before
                    - rebase_erc20_vault.userBalances(
                        withdrawing_user, token.address
                    )
                    == expected_shares
                )
                assert rebase_erc20_vault.getTotalAmountForUser(
                    remaining_user, token.address
                ) >= remaining_claim_before
                cumulative_reported += withdrawn
                cumulative_vault_outflow += vault_outflow
                success_count += 1
                boa.env.time_travel(blocks=1)
        assert cumulative_reported == cumulative_vault_outflow
        # This exact (96, 0) result was reproduced with the untouched test at
        # the PR base.  The old ``fail_closed_count > 0`` assertion was already
        # red there; fork_qualification is excluded from hosted CI.  The
        # branch assertions above remain the load-bearing conservation proof.
        # No fail-closed branch executes on this pinned Aave trajectory; the
        # real Comet matrix below carries the forked fail-closed coverage.
        assert (success_count, fail_closed_count) == (2 * 48, 0), (
            "pinned Aave repetition polarity drifted: "
            f"successes={success_count}, fail_closed={fail_closed_count}"
        )

        bob_claim_before = rebase_erc20_vault.getTotalAmountForUser(
            bob, token.address
        )
        alice_theoretical = rebase_erc20_vault.getTotalAmountForUser(
            alice, token.address
        )
        alice_before = token.balanceOf(alice)
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        withdrawn = teller.withdraw(
            token.address,
            MAX_UINT256,
            alice,
            rebase_erc20_vault.address,
            4,
            sender=alice,
        )
        assert withdrawn == vault_before - token.balanceOf(rebase_erc20_vault.address)
        assert abs((token.balanceOf(alice) - alice_before) - alice_theoretical) <= 1
        assert rebase_erc20_vault.userBalances(alice, token.address) == 0
        assert rebase_erc20_vault.getTotalAmountForUser(
            bob, token.address
        ) >= bob_claim_before

    with boa.env.anchor():
        setGeneralConfig()
        row = _row("cWETHv3")
        token = _position_token(row)
        alice = env.generate_address("sc04-comet-repeat-alice")
        bob = env.generate_address("sc04-comet-repeat-bob")
        accrual_actor = env.generate_address("sc04-comet-repeat-accrual")
        for account in (alice, bob):
            _source_position(row, account, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
        )
        deposit_amount, exact_granularity = _compound_exact_recipient_amount(
            row, _index(row)
        )
        for account in (alice, bob):
            token.allow(teller.address, True, sender=account)
            assert teller.deposit(
                token.address,
                deposit_amount,
                account,
                rebase_erc20_vault.address,
                4,
                sender=account,
            ) == deposit_amount

        boa.env.time_travel(seconds=30 * 24 * 60 * 60)
        _source_position(
            row,
            accrual_actor,
            max(exact_granularity, row["large_recipient_seed"] // 100),
        )
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
            _canDeposit=False,
        )
        for amount in (
            1,
            2,
            3,
            4,
            5,
            9,
            10,
            11,
            17,
            10**17 - 1,
            10**17,
            10**17 + 1,
        ):
            token.accrueAccount(rebase_erc20_vault.address, sender=alice)
            index = _index(row)
            vault_before = token.balanceOf(rebase_erc20_vault.address)
            recipient_before = token.balanceOf(alice)
            plan = _compatible_plan(
                row,
                index,
                amount,
                vault_before,
                recipient_before,
                token.userBasic(rebase_erc20_vault.address)[0],
                token.userBasic(alice)[0],
                False,
            )
            state_before = _vault_path_state(
                row, token, alice, rebase_erc20_vault, ledger
            )
            bob_claim_before = rebase_erc20_vault.getTotalAmountForUser(
                bob, token.address
            )
            if plan is None:
                with pytest.raises(Exception):
                    teller.withdraw(
                        token.address,
                        amount,
                        alice,
                        rebase_erc20_vault.address,
                        4,
                        sender=alice,
                    )
                assert _vault_path_state(
                    row, token, alice, rebase_erc20_vault, ledger
                ) == state_before
                boa.env.time_travel(blocks=1)
                continue

            shares_before = rebase_erc20_vault.userBalances(alice, token.address)
            expected_shares = rebase_erc20_vault.amountToShares(
                token.address, plan["outflow"], True
            )
            withdrawn = teller.withdraw(
                token.address,
                amount,
                alice,
                rebase_erc20_vault.address,
                4,
                sender=alice,
            )
            assert withdrawn == vault_before - token.balanceOf(
                rebase_erc20_vault.address
            ) == plan["outflow"]
            assert token.balanceOf(alice) - recipient_before == plan["inflow"]
            assert abs(plan["inflow"] - amount) <= 2
            assert abs(plan["outflow"] - amount) <= 2
            assert (
                shares_before - rebase_erc20_vault.userBalances(alice, token.address)
                == expected_shares
            )
            assert rebase_erc20_vault.getTotalAmountForUser(
                bob, token.address
            ) >= bob_claim_before
            boa.env.time_travel(blocks=1)

        token.accrueAccount(rebase_erc20_vault.address, sender=alice)
        bob_claim_before = rebase_erc20_vault.getTotalAmountForUser(
            bob, token.address
        )
        alice_theoretical = rebase_erc20_vault.getTotalAmountForUser(
            alice, token.address
        )
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(alice)
        alice_shares_before = rebase_erc20_vault.userBalances(
            alice, token.address
        )
        total_shares_before = rebase_erc20_vault.totalBalances(token.address)
        plan = _compatible_plan(
            row,
            _index(row),
            alice_theoretical,
            vault_before,
            recipient_before,
            token.userBasic(rebase_erc20_vault.address)[0],
            token.userBasic(alice)[0],
            True,
        )
        assert plan is not None
        charged_shares = min(
            alice_shares_before,
            rebase_erc20_vault.amountToShares(
                token.address, plan["outflow"], True
            ),
        )
        assert not _preserves_remaining_claim(
            total_shares_before,
            charged_shares,
            vault_before,
            plan["outflow"],
        )
        with pytest.raises(Exception):
            teller.withdraw(
                token.address,
                MAX_UINT256,
                alice,
                rebase_erc20_vault.address,
                4,
                sender=alice,
            )
        assert token.balanceOf(rebase_erc20_vault.address) == vault_before
        assert token.balanceOf(alice) == recipient_before
        assert rebase_erc20_vault.userBalances(
            alice, token.address
        ) == alice_shares_before
        assert rebase_erc20_vault.getTotalAmountForUser(
            bob, token.address
        ) == bob_claim_before


@pytest.base
@pytest.mark.fork_qualification
def test_comet_multi_holder_full_exit_boundary_matrix(
    env,
    teller,
    ledger,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Real Comet rounding blocks both holder orders without peer loss.

    The matrix uses only genuine Comet supplies and Teller deposits. It proves
    the exact atomic failure for both full request forms, models the maximum
    attainable full-burn policy, and separately executes the current
    minimum-residual-share path without changing production code.
    """
    row = _row("cWETHv3")
    scenarios = (
        ("equal-alice-first", (1, 1), 0),
        ("one-to-three-small-first", (1, 3), 0),
        ("one-to-three-large-first", (1, 3), 1),
    )
    # Deliberate durable fork evidence: regenerate these constants only after
    # intentionally reviewing pinned-state or trajectory changes.  A separate
    # (3, 1)/index-0 row is omitted because proportional share minting makes it
    # numerically identical to the retained (1, 3)/index-1 reverse direction.
    expected_boundaries = {
        "equal-alice-first": {
            "exiting_shares": 70_041_336_344_010_946_410_520_739,
            "shares_required": 70_041_336_344_010_946_414_089_965,
            "theoretical_claim": 701_349_496_595_795_698,
            "maximum_outflow": 701_349_496_595_795_698,
            "maximum_delivery": 701_349_496_595_795_696,
            "remaining_claim": 1_001_349_500_312_253_986,
            "residual_shares": 96_297_298,
        },
        "one-to-three-small-first": {
            "exiting_shares": 70_041_336_344_010_946_430_177_810,
            "shares_required": 70_041_336_344_010_946_462_270_217,
            "theoretical_claim": 701_349_496_595_795_699,
            "maximum_outflow": 701_349_496_595_795_699,
            "maximum_delivery": 701_349_496_595_795_697,
            "remaining_claim": 3_004_048_500_936_761_960,
            "residual_shares": 67_774_117,
        },
        "one-to-three-large-first": {
            "exiting_shares": 270_043_924_182_749_579_630_177_810,
            "shares_required": 270_043_924_182_749_579_707_541_946,
            "theoretical_claim": 2_704_048_497_220_303_673,
            "maximum_outflow": 2_704_048_497_220_303_673,
            "maximum_delivery": 2_704_048_497_220_303_671,
            "remaining_claim": 1_001_349_500_312_253_986,
            "residual_shares": 22_502_388,
        },
    }
    evidence = {
        "remote_block": REMOTE_BLOCK_IDENTITY,
        "token": row["token"],
        "underlying": row["underlying"],
        "scenarios": [],
    }

    for label, proportions, exiting_index in scenarios:
        clear_transient_storage()
        with boa.env.anchor():
            setGeneralConfig()
            token = _position_token(row)
            holders = (
                env.generate_address(f"der03-{label}-alice"),
                env.generate_address(f"der03-{label}-bob"),
            )
            exiting_user = holders[exiting_index]
            remaining_user = holders[1 - exiting_index]
            accrual_actor = env.generate_address(f"der03-{label}-accrual")
            for account in holders:
                _source_position(row, account, row["sender_seed"])

            setAssetConfig(
                token.address,
                _vaultIds=[4],
                _stakersPointsAlloc=0,
                _voterPointsAlloc=0,
                _minDepositBalance=0,
            )
            i0 = _index(row)
            assert row["pinned_index"] == 1_051_980_553_867_343
            assert i0 == 1_051_980_790_231_110
            assert i0 > row["pinned_index"]
            price_desk = _at(
                f"der03-price-desk-{label}", PRICE_DESK, PRICE_DESK_ABI
            )
            pinned_underlying_price = price_desk.getUsdValue(
                to_checksum_address(row["underlying"]), 10**row["decimals"], True
            )
            assert pinned_underlying_price != 0
            deposit_unit, exact_granularity = _compound_exact_recipient_amount(
                row, i0
            )
            deposits = []
            for account, proportion in zip(holders, proportions):
                deposit_amount = deposit_unit * proportion
                token.allow(teller.address, True, sender=account)
                sender_before = token.balanceOf(account)
                vault_before = token.balanceOf(rebase_erc20_vault.address)
                shares_before = rebase_erc20_vault.userBalances(
                    account, token.address
                )
                reported = teller.deposit(
                    token.address,
                    deposit_amount,
                    account,
                    rebase_erc20_vault.address,
                    4,
                    sender=account,
                )
                sender_after = token.balanceOf(account)
                vault_after = token.balanceOf(rebase_erc20_vault.address)
                shares_after = rebase_erc20_vault.userBalances(
                    account, token.address
                )
                assert reported == deposit_amount
                sender_outflow = sender_before - sender_after
                assert abs(sender_outflow - deposit_amount) <= 2
                assert vault_after - vault_before == deposit_amount
                assert shares_after > shares_before
                assert ledger.isParticipatingInVault(account, 4)
                deposits.append(
                    {
                        "holder": account,
                        "proportion": proportion,
                        "amount": deposit_amount,
                        "vault_inflow": vault_after - vault_before,
                        "sender_outflow": sender_outflow,
                        "shares_minted": shares_after - shares_before,
                    }
                )

            boa.env.time_travel(seconds=30 * 24 * 60 * 60)
            _source_position(
                row,
                accrual_actor,
                max(exact_granularity, row["large_recipient_seed"] // 100),
            )
            token.accrueAccount(rebase_erc20_vault.address, sender=exiting_user)
            i1 = _index(row)
            assert i1 == 1_053_386_730_362_703
            assert i1 > i0
            setAssetConfig(
                token.address,
                _vaultIds=[4],
                _stakersPointsAlloc=0,
                _voterPointsAlloc=0,
                _minDepositBalance=0,
                _canDeposit=False,
            )

            partials = []
            partial_requests = (
                1,
                2,
                3,
                4,
                5,
                9,
                10,
                11,
                17,
                10**17 - 1,
                10**17,
                10**17 + 1,
            )
            for partial_index, requested in enumerate(partial_requests):
                token.accrueAccount(
                    rebase_erc20_vault.address, sender=exiting_user
                )
                vault_before = token.balanceOf(rebase_erc20_vault.address)
                recipient_before = token.balanceOf(exiting_user)
                exiting_shares_before = rebase_erc20_vault.userBalances(
                    exiting_user, token.address
                )
                remaining_claim_before = rebase_erc20_vault.getTotalAmountForUser(
                    remaining_user, token.address
                )
                plan = _compatible_plan(
                    row,
                    _index(row),
                    requested,
                    vault_before,
                    recipient_before,
                    token.userBasic(rebase_erc20_vault.address)[0],
                    token.userBasic(exiting_user)[0],
                    False,
                )
                shares_required = 0
                if plan is not None and plan["outflow"] != 0:
                    shares_required = rebase_erc20_vault.amountToShares(
                        token.address, plan["outflow"], True
                    )
                can_execute = (
                    plan is not None
                    and plan["outflow"] != 0
                    and shares_required <= exiting_shares_before
                )
                if not can_execute:
                    state_before = _vault_path_state(
                        row,
                        token,
                        exiting_user,
                        rebase_erc20_vault,
                        ledger,
                    )
                    with pytest.raises(Exception):
                        teller.withdraw(
                            token.address,
                            requested,
                            exiting_user,
                            rebase_erc20_vault.address,
                            4,
                            sender=exiting_user,
                        )
                    assert _vault_path_state(
                        row,
                        token,
                        exiting_user,
                        rebase_erc20_vault,
                        ledger,
                    ) == state_before
                    assert rebase_erc20_vault.getTotalAmountForUser(
                        remaining_user, token.address
                    ) == remaining_claim_before
                    partials.append(
                        {
                            "sequence": partial_index + 1,
                            "requested": requested,
                            "success": False,
                        }
                    )
                    clear_transient_storage()
                    boa.env.time_travel(blocks=1)
                    continue
                reported = teller.withdraw(
                    token.address,
                    requested,
                    exiting_user,
                    rebase_erc20_vault.address,
                    4,
                    sender=exiting_user,
                )
                actual_outflow = vault_before - token.balanceOf(
                    rebase_erc20_vault.address
                )
                actual_delivery = token.balanceOf(exiting_user) - recipient_before
                assert reported == actual_outflow == plan["outflow"]
                assert actual_delivery == plan["inflow"]
                assert (
                    exiting_shares_before
                    - rebase_erc20_vault.userBalances(exiting_user, token.address)
                    == shares_required
                )
                remaining_claim_after = rebase_erc20_vault.getTotalAmountForUser(
                    remaining_user, token.address
                )
                assert remaining_claim_after >= remaining_claim_before
                partials.append(
                    {
                        "sequence": partial_index + 1,
                        "requested": requested,
                        "success": True,
                        "vault_outflow": actual_outflow,
                        "recipient_inflow": actual_delivery,
                        "shares_burned": shares_required,
                        "remaining_claim_before": remaining_claim_before,
                        "remaining_claim_after": remaining_claim_after,
                    }
                )
                boa.env.time_travel(blocks=1)

            token.accrueAccount(rebase_erc20_vault.address, sender=exiting_user)
            theoretical_claim = rebase_erc20_vault.getTotalAmountForUser(
                exiting_user, token.address
            )
            vault_before = token.balanceOf(rebase_erc20_vault.address)
            recipient_before = token.balanceOf(exiting_user)
            exiting_shares = rebase_erc20_vault.userBalances(
                exiting_user, token.address
            )
            remaining_shares = rebase_erc20_vault.userBalances(
                remaining_user, token.address
            )
            total_shares = rebase_erc20_vault.totalBalances(token.address)
            remaining_claim_before = rebase_erc20_vault.getTotalAmountForUser(
                remaining_user, token.address
            )
            theoretical_plan = _compatible_plan(
                row,
                _index(row),
                theoretical_claim,
                vault_before,
                recipient_before,
                token.userBasic(rebase_erc20_vault.address)[0],
                token.userBasic(exiting_user)[0],
                True,
            )
            assert theoretical_plan is not None
            shares_required_for_theoretical_outflow = (
                rebase_erc20_vault.amountToShares(
                    token.address, theoretical_plan["outflow"], True
                )
            )
            assert shares_required_for_theoretical_outflow > exiting_shares
            assert not _preserves_remaining_claim(
                total_shares,
                min(exiting_shares, shares_required_for_theoretical_outflow),
                vault_before,
                theoretical_plan["outflow"],
            )

            failed_state = {
                "exiting": _vault_path_state(
                    row,
                    token,
                    exiting_user,
                    rebase_erc20_vault,
                    ledger,
                ),
                "remaining_shares": remaining_shares,
                "remaining_claim": remaining_claim_before,
                "remaining_participating": ledger.isParticipatingInVault(
                    remaining_user, 4
                ),
                "total_shares": total_shares,
                "vault_custody": vault_before,
                "recipient_balance": recipient_before,
            }
            failed_requests = []
            for request_label, request_amount in (
                ("theoretical", theoretical_claim),
                ("max_uint256", MAX_UINT256),
            ):
                clear_transient_storage()
                with boa.env.anchor():
                    with boa.reverts("remaining holder loss"):
                        teller.withdraw(
                            token.address,
                            request_amount,
                            exiting_user,
                            rebase_erc20_vault.address,
                            4,
                            sender=exiting_user,
                        )
                    assert {
                        "exiting": _vault_path_state(
                            row,
                            token,
                            exiting_user,
                            rebase_erc20_vault,
                            ledger,
                        ),
                        "remaining_shares": rebase_erc20_vault.userBalances(
                            remaining_user, token.address
                        ),
                        "remaining_claim": rebase_erc20_vault.getTotalAmountForUser(
                            remaining_user, token.address
                        ),
                        "remaining_participating": ledger.isParticipatingInVault(
                            remaining_user, 4
                        ),
                        "total_shares": rebase_erc20_vault.totalBalances(
                            token.address
                        ),
                        "vault_custody": token.balanceOf(
                            rebase_erc20_vault.address
                        ),
                        "recipient_balance": token.balanceOf(exiting_user),
                    } == failed_state
                    assert filter_logs(
                        teller, "RebaseErc20VaultWithdrawal"
                    ) == []
                    assert filter_logs(teller, "TellerWithdrawal") == []
                clear_transient_storage()
                failed_requests.append(
                    {"label": request_label, "amount": request_amount}
                )

            best_full_burn, best_current_path = _comet_attainable_exit_plans(
                row,
                token,
                rebase_erc20_vault,
                exiting_user,
                theoretical_claim,
                vault_before,
                recipient_before,
                exiting_shares,
                total_shares,
            )
            residual = theoretical_claim - best_full_burn["inflow"]
            assert residual == 2
            assert best_full_burn["index"] == 1_053_386_808_660_061
            assert best_full_burn["remaining_claim_after_full_burn"] >= (
                remaining_claim_before
            )

            # The current path can deliver the same bounded economic maximum,
            # but it must retain the exact residual shares required by actual
            # vault outflow. Execute it through Teller and prove peer value.
            clear_transient_storage()
            with boa.env.anchor():
                reported = teller.withdraw(
                    token.address,
                    best_current_path["transfer_amount"],
                    exiting_user,
                    rebase_erc20_vault.address,
                    4,
                    sender=exiting_user,
                )
                actual_outflow = vault_before - token.balanceOf(
                    rebase_erc20_vault.address
                )
                actual_delivery = token.balanceOf(exiting_user) - recipient_before
                residual_shares = rebase_erc20_vault.userBalances(
                    exiting_user, token.address
                )
                remaining_claim_after = rebase_erc20_vault.getTotalAmountForUser(
                    remaining_user, token.address
                )
                assert reported == actual_outflow == best_current_path["outflow"]
                assert actual_delivery == best_current_path["inflow"]
                assert residual_shares == (
                    exiting_shares - best_current_path["shares_required"]
                )
                assert residual_shares > 0
                assert remaining_claim_after >= remaining_claim_before
                residual_claim = rebase_erc20_vault.getTotalAmountForUser(
                    exiting_user, token.address
                )
                assert residual_claim == 0
                assert ledger.isParticipatingInVault(exiting_user, 4)
                assert rebase_erc20_vault.isUserInVaultAsset(
                    exiting_user, token.address
                )
                withdrawal_event = filter_logs(teller, "TellerWithdrawal")[-1]
                assert not withdrawal_event.isDepleted

                # The first non-final holder is now registered with positive
                # shares but a zero raw-token claim. The peer is still not a
                # sole holder and therefore cannot cross its own Comet
                # boundary. There is no automatic progression to a clean last
                # holder at this observed index: both terminal requests remain
                # blocked. Future Comet accrual can eventually make the zero
                # raw-unit claim round up, so this is a point-in-time proof.
                blocked_state = (
                    _vault_path_state(
                        row,
                        token,
                        exiting_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                    _vault_path_state(
                        row,
                        token,
                        remaining_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                )
                clear_transient_storage()
                with boa.reverts("no withdrawal amount"):
                    teller.withdraw(
                        token.address,
                        MAX_UINT256,
                        exiting_user,
                        rebase_erc20_vault.address,
                        4,
                        sender=exiting_user,
                    )
                assert (
                    _vault_path_state(
                        row,
                        token,
                        exiting_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                    _vault_path_state(
                        row,
                        token,
                        remaining_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                ) == blocked_state
                # The state tuple above is the load-bearing atomicity proof.
                # Titanoboa/EVM rollback discards reverted logs, so these log
                # checks document that framework guarantee rather than an
                # independent contract property.
                assert filter_logs(teller, "RebaseErc20VaultWithdrawal") == []
                assert filter_logs(teller, "TellerWithdrawal") == []
                clear_transient_storage()
                with boa.reverts("remaining holder loss"):
                    teller.withdraw(
                        token.address,
                        MAX_UINT256,
                        remaining_user,
                        rebase_erc20_vault.address,
                        4,
                        sender=remaining_user,
                    )
                assert (
                    _vault_path_state(
                        row,
                        token,
                        exiting_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                    _vault_path_state(
                        row,
                        token,
                        remaining_user,
                        rebase_erc20_vault,
                        ledger,
                    ),
                ) == blocked_state
                assert filter_logs(teller, "RebaseErc20VaultWithdrawal") == []
                assert filter_logs(teller, "TellerWithdrawal") == []
                executable_residual = {
                    "evidence_kind": "executed_current_contract_path",
                    "requested": best_current_path["transfer_amount"],
                    "vault_outflow": actual_outflow,
                    "recipient_inflow": actual_delivery,
                    "shares_burned": best_current_path["shares_required"],
                    "shares_retained": residual_shares,
                    "raw_claim_retained": residual_claim,
                    "is_depleted": withdrawal_event.isDepleted,
                    "ledger_participating": ledger.isParticipatingInVault(
                        exiting_user, 4
                    ),
                    "user_asset_registered": (
                        rebase_erc20_vault.isUserInVaultAsset(
                            exiting_user, token.address
                        )
                    ),
                    "residual_holder_max_exit": "no withdrawal amount",
                    "remaining_holder_max_exit": "remaining holder loss",
                    "remaining_claim_before": remaining_claim_before,
                    "remaining_claim_after": remaining_claim_after,
                }
            clear_transient_storage()

            residual_usd_value = (
                residual * pinned_underlying_price // 10**row["decimals"]
            )
            scenario_evidence = {
                "label": label,
                "ownership_proportions": proportions,
                "exiting_holder_index": exiting_index,
                "pinned_inventory_index": row["pinned_index"],
                "i0": i0,
                "i0_minus_pinned_inventory": i0 - row["pinned_index"],
                "i1": i1,
                "pinned_underlying_price_usd_18": pinned_underlying_price,
                "deposits": deposits,
                "partials": partials,
                "boundary": {
                    "exiting_shares": exiting_shares,
                    "remaining_shares": remaining_shares,
                    "total_shares": total_shares,
                    "vault_token_balance": vault_before,
                    "theoretical_nominal_claim": theoretical_claim,
                    "theoretical_transfer_plan": theoretical_plan,
                    "shares_required_for_theoretical_outflow": (
                        shares_required_for_theoretical_outflow
                    ),
                    "failed_requests": failed_requests,
                    "remaining_claim_before": remaining_claim_before,
                    "modeled_maximum_attainable_full_burn": {
                        "evidence_kind": "modeled_not_executed",
                        **best_full_burn,
                    },
                    "residual_base_units": residual,
                    "residual_underlying_usd_18": residual_usd_value,
                    "executed_minimum_residual_share_path": executable_residual,
                },
            }
            expected = expected_boundaries[label]
            assert {
                "exiting_shares": exiting_shares,
                "shares_required": shares_required_for_theoretical_outflow,
                "theoretical_claim": theoretical_claim,
                "maximum_outflow": best_full_burn["outflow"],
                "maximum_delivery": best_full_burn["inflow"],
                "remaining_claim": remaining_claim_before,
                "residual_shares": executable_residual["shares_retained"],
            } == expected
            evidence["scenarios"].append(scenario_evidence)
            _write_evidence(
                "der03-comet-multi-holder-exit-liveness.json", evidence
            )
        clear_transient_storage()

    assert len(evidence["scenarios"]) == len(scenarios)


@pytest.base
@pytest.mark.fork_qualification
def test_comet_actual_outflow_propagates_through_auction_and_credit_callers(
    env,
    teller,
    auction_house,
    credit_engine,
    credit_redeem,
    rebase_erc20_vault,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    """Downstream callers consume the custody amount charged to shares."""
    with boa.env.anchor():
        setGeneralConfig()
        row = _row("cWETHv3")
        token = _position_token(row)
        user = env.generate_address("sc04-comet-caller-user")
        auction_recipient = env.generate_address("sc04-comet-auction-recipient")
        credit_recipient = env.generate_address("sc04-comet-credit-recipient")
        _source_position(row, user, row["sender_seed"])
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
        )
        mock_price_source.setPrice(token.address, 10**18)
        deposit_amount, _ = _compound_exact_recipient_amount(row, _index(row))
        token.allow(teller.address, True, sender=user)
        assert teller.deposit(
            token.address,
            deposit_amount,
            user,
            rebase_erc20_vault.address,
            4,
            sender=user,
        ) == deposit_amount

        auction_house.inject_function(
            """
@external
def sc04TransferCollateral(
    _fromUser: address,
    _toUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _targetUsdValue: uint256,
) -> (uint256, uint256, bool, bool):
    a: addys.Addys = addys._getAddys()
    return self._transferCollateral(
        _fromUser,
        _toUser,
        _vaultId,
        _vaultAddr,
        _asset,
        False,
        _targetUsdValue,
        a,
    )
            """
        )

        requested = 10**15
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(auction_recipient)
        usd_value, amount_sent, depleted, exhausted = (
            auction_house.inject.sc04TransferCollateral(
                user,
                auction_recipient,
                4,
                rebase_erc20_vault.address,
                token.address,
                requested,
                sender=user,
            )
        )
        auction_delivery = token.balanceOf(auction_recipient) - recipient_before
        assert amount_sent == vault_before - token.balanceOf(
            rebase_erc20_vault.address
        )
        assert abs(amount_sent - requested) <= 2
        assert abs(auction_delivery - requested) <= 2
        assert usd_value == amount_sent
        assert not depleted
        assert not exhausted

        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(credit_recipient)
        amount_sent = credit_engine.transferOrWithdrawViaRedemption(
            False,
            token.address,
            user,
            credit_recipient,
            requested,
            4,
            rebase_erc20_vault.address,
            credit_engine.getAddys(),
            sender=credit_redeem.address,
        )
        credit_delivery = token.balanceOf(credit_recipient) - recipient_before
        assert amount_sent == vault_before - token.balanceOf(
            rebase_erc20_vault.address
        )
        assert abs(amount_sent - requested) <= 2
        assert abs(credit_delivery - requested) <= 2


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
                    "minimum_balance_reject_count": 0,
                    "minimum_balance_rejects": [],
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
                        shares_before_partial = rebase_erc20_vault.userBalances(
                            user, token.address
                        )
                        total_shares_before_partial = rebase_erc20_vault.totalBalances(
                            token.address
                        )
                        vault_before_partial = token.balanceOf(rebase_erc20_vault.address)
                        recipient_before_partial = token.balanceOf(user)
                        vault_scaled_before_partial = token.scaledBalanceOf(
                            rebase_erc20_vault.address
                        )
                        recipient_scaled_before_partial = token.scaledBalanceOf(user)
                        plan = _compatible_plan(
                            row,
                            i1,
                            partial_amount,
                            vault_before_partial,
                            recipient_before_partial,
                            vault_scaled_before_partial,
                            recipient_scaled_before_partial,
                            False,
                        )
                        ledger_before_partial = (
                            ledger.isParticipatingInVault(user, 4),
                            ledger.numUserVaults(user),
                            rebase_erc20_vault.getNumUserAssets(user),
                        )
                        if plan is not None:
                            expected_shares = rebase_erc20_vault.amountToShares(
                                token.address, plan["outflow"], True
                            )
                            remaining_shares = shares_before_partial - expected_shares
                            remaining_total_shares = (
                                total_shares_before_partial - expected_shares
                            )
                            remaining_vault_balance = (
                                vault_before_partial - plan["outflow"]
                            )
                            predicted_remaining_claim = 0
                            if remaining_shares != 0:
                                predicted_remaining_claim = (
                                    remaining_shares
                                    * (remaining_vault_balance + 1)
                                    // (remaining_total_shares + 10**8)
                                )
                            if (
                                remaining_shares != 0
                                and predicted_remaining_claim
                                < row["deployed_min_deposit"]
                            ):
                                with pytest.raises(Exception) as exc_info:
                                    teller.withdraw(
                                        token.address,
                                        partial_amount,
                                        user,
                                        rebase_erc20_vault.address,
                                        4,
                                        sender=user,
                                    )
                                assert "too small a balance" in str(exc_info.value)
                                assert (
                                    rebase_erc20_vault.userBalances(
                                        user, token.address
                                    )
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
                                partial_results[
                                    "minimum_balance_reject_count"
                                ] += 1
                                partial_results["minimum_balance_rejects"].append(
                                    {
                                        "amount": partial_amount,
                                        "predicted_remaining_claim": (
                                            predicted_remaining_claim
                                        ),
                                        "minimum_balance": row[
                                            "deployed_min_deposit"
                                        ],
                                        "status": (
                                            "atomically rejected by Teller minimum"
                                        ),
                                    }
                                )
                                continue
                            withdrawn = teller.withdraw(
                                token.address,
                                partial_amount,
                                user,
                                rebase_erc20_vault.address,
                                4,
                                sender=user,
                            )
                            assert withdrawn == plan["outflow"]
                            assert (
                                vault_before_partial
                                - token.balanceOf(rebase_erc20_vault.address)
                                == plan["outflow"]
                            )
                            assert (
                                token.balanceOf(user) - recipient_before_partial
                                == plan["inflow"]
                            )
                            assert abs(plan["inflow"] - partial_amount) <= 2
                            assert (
                                shares_before_partial
                                - rebase_erc20_vault.userBalances(user, token.address)
                                == expected_shares
                            )
                            assert (
                                total_shares_before_partial
                                - rebase_erc20_vault.totalBalances(token.address)
                                == expected_shares
                            )
                            partial_results["success_count"] += 1
                        else:
                            with pytest.raises(Exception):
                                teller.withdraw(
                                    token.address,
                                    partial_amount,
                                    user,
                                    rebase_erc20_vault.address,
                                    4,
                                    sender=user,
                                )
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
                                    "status": "failed closed outside compatible bound",
                                }
                            )

                    if partial_results["sample_count"] % 100 == 0:
                        _write_evidence(
                            "aave-deposit-accrual-withdrawal.json", evidence
                        )

                assert (
                    partial_results["success_count"]
                    + partial_results["mismatch_count"]
                    + partial_results["minimum_balance_reject_count"]
                    == partial_results["sample_count"]
                )

                plan = _compatible_plan(
                    row,
                    i1,
                    withdrawal_amount,
                    vault_before_withdrawal,
                    recipient_before,
                    vault_scaled_before_withdrawal,
                    recipient_scaled_before,
                    True,
                )
                assert plan is not None
                withdrawn = teller.withdraw(
                    token.address,
                    MAX_UINT256,
                    user,
                    rebase_erc20_vault.address,
                    4,
                    sender=user,
                )
                realized_outflow = (
                    vault_before_withdrawal
                    - token.balanceOf(rebase_erc20_vault.address)
                )
                realized_delivery = token.balanceOf(user) - recipient_before
                assert withdrawn == realized_outflow == plan["outflow"]
                assert realized_delivery == plan["inflow"]
                assert abs(realized_delivery - withdrawal_amount) <= 1
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
                    "num_user_assets": rebase_erc20_vault.getNumUserAssets(user),
                    "participating": ledger.isParticipatingInVault(user, 4),
                    "user_asset_registered": rebase_erc20_vault.isUserInVaultAsset(
                        user, token.address
                    ),
                }
                assert cleanup["num_user_assets"] == 0
                assert not cleanup["participating"]
                assert not cleanup["user_asset_registered"]
                direct = {
                    "transfer_argument": plan["transfer_amount"],
                    "vault_outflow": realized_outflow,
                    "recipient_inflow": realized_delivery,
                    "theoretical_nominal": withdrawal_amount,
                    "maximum_attainable_delivery": plan["inflow"],
                }
                path_result = {
                    "success": True,
                    "reported_custody_outflow": withdrawn,
                    "depletion": depletion,
                    "deferred_registration_cleanup": cleanup,
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
def test_aave_usdc_deposit_mints_only_against_exact_vault_receipt(
    env,
    teller,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """Aave's one-unit sender rounding does not under-back minted shares."""
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
        vault_after = token.balanceOf(rebase_erc20_vault.address)
        user_after = token.balanceOf(user)
        shares_minted = rebase_erc20_vault.userBalances(user, token.address)
        assert deposited == deposit_amount
        assert vault_after - vault_before == deposit_amount
        assert user_before - user_after - deposit_amount in (0, 1)
        assert shares_minted == rebase_erc20_vault.amountToShares(
            token.address, deposit_amount, False
        )
        assert rebase_erc20_vault.getTotalAmountForUser(
            user, token.address
        ) <= vault_after


@pytest.base
@pytest.mark.fork_qualification
def test_aave_usdc_partial_withdrawal_accounts_custody_not_representation(
    env,
    teller,
    rebase_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
):
    """The amount-3 path charges 3 while accepting recipient-side +1."""
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

        # Disabling new deposits must not trap a legitimate existing position.
        setAssetConfig(
            token.address,
            _vaultIds=[4],
            _stakersPointsAlloc=0,
            _voterPointsAlloc=0,
            _minDepositBalance=0,
            _canDeposit=False,
        )

        boa.env.time_travel(seconds=30 * 24 * 60 * 60)
        _source_position(
            row,
            accrual_actor,
            max(10_000, row["large_recipient_seed"] // 100),
        )
        vault_before = token.balanceOf(rebase_erc20_vault.address)
        recipient_before = token.balanceOf(user)
        user_shares_before = rebase_erc20_vault.userBalances(user, token.address)
        total_shares_before = rebase_erc20_vault.totalBalances(token.address)
        expected_shares = rebase_erc20_vault.amountToShares(
            token.address, withdrawal_amount, True
        )

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
        assert token.balanceOf(user) - recipient_before == withdrawn + 1
        assert (
            user_shares_before
            - rebase_erc20_vault.userBalances(user, token.address)
            == expected_shares
        )
        assert (
            total_shares_before
            - rebase_erc20_vault.totalBalances(token.address)
            == expected_shares
        )
        assert rebase_erc20_vault.getTotalAmountForUser(
            user, token.address
        ) <= token.balanceOf(rebase_erc20_vault.address)
        assert filter_logs(teller, "RebaseErc20VaultWithdrawal")[-1].amount == 3
        assert filter_logs(teller, "TellerWithdrawal")[-1].amount == 3
