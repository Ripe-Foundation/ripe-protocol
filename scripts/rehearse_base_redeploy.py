"""Rehearse the funded Base redeployment against one immutable chain block.

This script never connects a signing key and never broadcasts.  It deploys the
2026082402 candidates inside a Boa fork, performs the Safe activation sequence,
migrates the live user state, and fails on the first reconciliation mismatch.

Run with::

    python -m scripts.rehearse_base_redeploy
"""

from __future__ import annotations

import json
import os
import warnings
from collections import defaultdict
from pathlib import Path

import boa
import boa.deployments
from eth_utils import to_checksum_address
from web3 import Web3
from web3._utils.events import get_event_data

from scripts.migrate import _isolate_fork_history
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.migration_helpers import get_vyper_abi, load_vyper_files
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.mock_account import MockAccount


ROOT = Path(__file__).resolve().parents[1]
BLOCK = 50_418_602
BLOCK_HASH = "0x0a3b747494d6b5945b7c8d1c076e7a2dfdf33eacb2bb9598ca4a5189c7ddff84"
SAFE = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"
DEPLOYER = "0xEF3cB7750FF6158d9f9B27651BbBA2299096483B"
HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
OLD_MISSION_CONTROL = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
OLD_TELLER = "0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13"
OLD_PRICE_DESK = "0x2F7901BE53cC94AEF174f1a0764430840360Ef53"
MC_DEPLOY_BLOCK = 39_183_390

SOURCE_VAULTS = {
    1: ("StabilityPool", "0x2a157096af6337b2b4bd47de435520572ed5a439"),
    2: ("RipeGov", "0xe42b3dC546527EB70D741B185Dc57226cA01839D"),
    3: ("SimpleErc20", "0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD"),
    4: ("RebaseErc20", "0xce2E96C9F6806731914A7b4c3E4aC1F296d98597"),
    5: ("SimpleErc20", "0x4549A368c00f803862d457C4C0c659a293F26C66"),
}
TARGET_VAULT_IDS = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10}

GREEN_POOL = "0xd6c283655B42FA0eb2685F7AB819784F071459dc"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
MAX_UINT = 2**256 - 1

# The active GREEN/USDC Stability Pool cohort has these eleven liabilities at
# the pinned block.  The live contracts remain the authority: preflight checks
# every pair is still nonzero before the fork mutates anything.
STABILITY_CLAIM_ASSETS = (
    "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf",  # VVV
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631",  # AERO
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6",  # wrappedSuperOETH
    "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5",  # mcBETH
    "0xA88594D404727625A9437C3f886C7643872296AE",  # WELL
    "0xcbD06E5A2B0C65597161de254AA074E489dEb510",  # cbDOGE
    "0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55",  # USOL
    "0x96F1a7ce331F40afe866F3b707c223e377661087",  # undyAERO
    "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",  # VIRTUAL
    "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33BF",  # cbBTC
)

ENDAOMENT_ASSETS = (
    USDC,
    "0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8",  # undyEURC
    "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0",  # RIPE
    GREEN_POOL,
    "0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707",  # GREEN
)

CANDIDATE = "Candidate2026082402"
CACHE = Path(f"/tmp/ripe-base-redeploy-{BLOCK}.json")


def _address(value) -> str:
    return str(getattr(value, "address", value)).lower()


def _batch(values, size):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT / ".env", override=False)


def _event_abis(path, names=None):
    abi = get_vyper_abi(path)
    return {
        item["name"]: item
        for item in abi
        if item.get("type") == "event"
        and (names is None or item["name"] in names)
    }


def _deployment_block(w3, address):
    low, high = 0, BLOCK
    while low < high:
        middle = (low + high) // 2
        if w3.eth.get_code(address, block_identifier=middle):
            high = middle
        else:
            low = middle + 1
    return low


def _logs(w3, address, topics, start):
    """Fetch a narrow event stream, splitting only when the RPC asks us to."""
    result = []

    def fetch(first, last):
        try:
            result.extend(w3.eth.get_logs({
                "fromBlock": first,
                "toBlock": last,
                "address": to_checksum_address(address),
                "topics": [topics],
            }))
        except Exception:
            if first == last:
                raise
            middle = (first + last) // 2
            fetch(first, middle)
            fetch(middle + 1, last)

    fetch(start, BLOCK)
    return result


def _topic(abi):
    inputs = ",".join(item["type"] for item in abi["inputs"])
    return Web3.to_hex(Web3.keccak(text=f'{abi["name"]}({inputs})'))


def _discover_live_state(rpc):
    state = {
        "block": BLOCK,
        "block_hash": BLOCK_HASH,
        "vault_users": {},
    }
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        assert cached.get("block") == BLOCK
        assert cached.get("block_hash", "").lower() == BLOCK_HASH.lower()
        if cached.get("complete"):
            return cached
        state.update(cached)

    print("[census] reading live users and MissionControl events")
    paths = {
        "StabilityPool": "contracts/vaults/StabilityPool.vy",
        "RipeGov": "contracts/vaults/RipeGov.vy",
        "SimpleErc20": "contracts/vaults/SimpleErc20.vy",
        "RebaseErc20": "contracts/vaults/RebaseErc20.vy",
    }
    # Compile the small ABI set before opening the long-running RPC census.
    # This keeps compiler subprocesses out of the provider's connection phase.
    vault_abis = {name: _event_abis(path) for name, path in paths.items()}
    teller_abis = _event_abis(
        "contracts/core/Teller.vy", {"UserConfigSet", "UserDelegationSet"}
    )
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 120}))
    assert w3.eth.chain_id == 8453
    block = w3.eth.get_block(BLOCK)
    assert block.hash.hex().lower().removeprefix("0x") == BLOCK_HASH.lower().removeprefix("0x")

    for vault_id, (contract_name, address) in SOURCE_VAULTS.items():
        if str(vault_id) in state["vault_users"]:
            continue
        abis = vault_abis[contract_name]
        user_events = {
            _topic(abi): abi
            for abi in abis.values()
            if any(item.get("indexed") and item["name"] == "user" for item in abi["inputs"])
        }
        start = _deployment_block(w3, address)
        logs = _logs(w3, address, list(user_events), start)
        users = set()
        for entry in logs:
            decoded = get_event_data(w3.codec, user_events[Web3.to_hex(entry["topics"][0])], entry)
            user = decoded["args"].get("user")
            if user:
                users.add(to_checksum_address(user))
        state["vault_users"][str(vault_id)] = sorted(users)
        CACHE.write_text(json.dumps(state, indent=2, sort_keys=True))
        print(f"[census] vault {vault_id}: {len(users)} historical users")

    topic_map = {_topic(abi): abi for abi in teller_abis.values()}
    config_events = {}
    delegation_events = {}
    for entry in _logs(w3, OLD_TELLER, list(topic_map), MC_DEPLOY_BLOCK):
        decoded = get_event_data(w3.codec, topic_map[Web3.to_hex(entry["topics"][0])], entry)
        args = decoded["args"]
        if decoded["event"] == "UserConfigSet":
            config_events[to_checksum_address(args["user"])] = [
                bool(args["canAnyoneDeposit"]),
                bool(args["canAnyoneRepayDebt"]),
                bool(args["canAnyoneBondForUser"]),
            ]
        else:
            key = f'{to_checksum_address(args["user"])}:{to_checksum_address(args["delegate"])}'
            delegation_events[key] = [
                bool(args["canWithdraw"]),
                bool(args["canBorrow"]),
                bool(args["canClaimFromStabPool"]),
                bool(args["canClaimLoot"]),
            ]

    state["user_configs"] = config_events
    state["user_delegations"] = delegation_events
    state["complete"] = True
    CACHE.write_text(json.dumps(state, indent=2, sort_keys=True))
    print(
        f"[census] {len(config_events)} user configs and "
        f"{len(delegation_events)} delegations"
    )
    return state


def _at(path, address):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"casted bytecode does not match compiled bytecode at ",
            category=UserWarning,
        )
        return boa.load_partial(path).at(address)


def _erc20(address):
    return boa.load_abi("scripts/abis/Erc20Token.json", name="token").at(address)


def _candidate(manifest, name):
    record = manifest["contracts"][f"{name}{CANDIDATE}"]
    return _at(record["file"], record["address"])


def _current_block():
    return boa.env.evm.patch.block_number


def _advance_to(block):
    if block > _current_block():
        # Advance the protocol's block-based timelocks without aging external
        # oracle observations. A static fork cannot receive the Chainlink
        # updates that Base will receive during the real 21,600-block wait;
        # aging timestamp here would therefore manufacture stale feeds that
        # cannot occur in the same way on the updating live chain.
        boa.env.time_travel(
            blocks=block - _current_block(),
            block_delta=0,
        )


def _execute_action(board, method, *args):
    action = int(method(*args, sender=SAFE))
    _advance_to(int(board.getActionConfirmationBlock(action)))
    assert board.executePendingAction(action, sender=SAFE)
    return action


def _positions(vault, users):
    result = {}
    for user in users:
        positions = {}
        endpoint = int(vault.numUserAssets(user))
        for index in range(1, endpoint):
            asset, has_balance = vault.getUserAssetAtIndexAndHasBalance(user, index)
            if has_balance:
                amount = int(vault.getTotalAmountForUser(user, asset))
                if amount:
                    positions[_address(asset)] = amount
        if positions:
            result[_address(user)] = positions
    return result


def _active_users(vault, candidates):
    return sorted(_positions(vault, candidates))


def _snapshot_mc_state(old_mc, census):
    configs = {}
    for user in census["user_configs"]:
        value = tuple(old_mc.userConfig(user))
        if any(value):
            configs[_address(user)] = value

    delegations = {}
    for key in census["user_delegations"]:
        user, delegate = key.split(":")
        value = tuple(old_mc.userDelegation(user, delegate))
        if any(value):
            delegations[(_address(user), _address(delegate))] = value
    return configs, delegations


def _migrate_mc_state(migrator, new_mc, configs, delegations):
    print(f"[state] copying {len(configs)} user configs")
    for users in _batch(list(configs), 25):
        assert int(migrator.migrateMissionControlUserConfigs(users, sender=SAFE)) == len(users)
    for user, expected in configs.items():
        assert tuple(new_mc.userConfig(user)) == expected

    pairs = list(delegations)
    print(f"[state] copying {len(pairs)} user delegations")
    for group in _batch(pairs, 25):
        users = [pair[0] for pair in group]
        delegates = [pair[1] for pair in group]
        assert int(migrator.migrateMissionControlUserDelegations(users, delegates, sender=SAFE)) == len(group)
    for (user, delegate), expected in delegations.items():
        assert tuple(new_mc.userDelegation(user, delegate)) == expected


def _move_protocol_funds(hq, manifest):
    old_switchboard = _at("contracts/registries/Switchboard.vy", hq.getAddr(6))
    old_charlie = _at("contracts/config/SwitchboardCharlie.vy", old_switchboard.getAddr(3))
    old_echo = _at("contracts/config/SwitchboardEcho.vy", old_switchboard.getAddr(5))
    old_funds = hq.getAddr(21)
    old_psm = hq.getAddr(22)
    new_funds = _candidate(manifest, "EndaomentFunds")
    new_psm = _candidate(manifest, "EndaomentPSM")

    moved = {}
    print("[funds] moving the old EndaomentFunds balances through Endaoment")
    for asset in ENDAOMENT_ASSETS:
        token = _erc20(asset)
        amount = int(token.balanceOf(old_funds))
        if not amount:
            continue
        safe_before = int(token.balanceOf(SAFE))
        _execute_action(old_echo, old_echo.performEndaomentTransfer, asset, amount)
        assert int(token.balanceOf(SAFE)) == safe_before + amount
        assert token.transfer(new_funds, amount, sender=SAFE)
        assert int(token.balanceOf(old_funds)) == 0
        assert int(token.balanceOf(new_funds)) == amount
        moved[_address(asset)] = amount

    psm_token = _erc20(USDC)
    psm_amount = int(psm_token.balanceOf(old_psm))
    if psm_amount:
        _execute_action(old_charlie, old_charlie.recoverFunds, old_psm, new_psm, USDC)
    assert int(psm_token.balanceOf(old_psm)) == 0
    assert int(psm_token.balanceOf(new_psm)) == psm_amount
    return moved, psm_amount


def _start_registry_activation(hq, manifest):
    replacements = (
        ("MissionControl", 5), ("Switchboard", 6), ("PriceDesk", 7),
        ("VaultBook", 8), ("AuctionHouse", 9), ("AuctionHouseNFT", 10),
        ("Boardroom", 11), ("BondRoom", 12), ("CreditEngine", 13),
        ("Endaoment", 14), ("HumanResources", 15), ("Lootbox", 16),
        ("Teller", 17), ("Deleverage", 18), ("CreditRedeem", 19),
        ("TellerUtils", 20), ("EndaomentFunds", 21), ("EndaomentPSM", 22),
    )
    print("[safe] starting 18 HQ replacements and VaultMigrator")
    for name, registry_id in replacements:
        assert hq.startAddressUpdateToRegistry(
            registry_id, _candidate(manifest, name), sender=SAFE
        )
    migrator = _candidate(manifest, "VaultMigrator")
    assert hq.startAddNewAddressToRegistry(migrator, "VaultMigrator", sender=SAFE)
    confirm = max(
        max(int(hq.pendingAddrUpdate(i).confirmBlock) for _, i in replacements),
        int(hq.pendingNewAddr(migrator).confirmBlock),
    )
    _advance_to(confirm)
    return replacements, migrator


def _activate_state(hq, manifest, migrator, census, old_mc):
    # Deliberately activate these before every other department.  The old
    # PriceDesk, Teller, and VaultBook remain authoritative while the new
    # MissionControl authorizes VaultMigrator's temporary claim delegation.
    print("[safe] activating MissionControl and VaultMigrator")
    assert hq.confirmAddressUpdateToRegistry(5, sender=SAFE)
    assert int(hq.confirmNewAddressToRegistry(migrator, sender=SAFE)) == 25
    new_mc = _candidate(manifest, "MissionControl")
    configs, delegations = _snapshot_mc_state(old_mc, census)
    _migrate_mc_state(migrator, new_mc, configs, delegations)
    return new_mc, configs, delegations


def _activate_oracles(hq, manifest, old_curve):
    print("[safe] activating PriceDesk and copying Curve routes")
    assert hq.confirmAddressUpdateToRegistry(7, sender=SAFE)
    curve = _candidate(manifest, "CurvePrices")
    routes = [(asset, old_curve.curveConfig(asset).pool) for asset in old_curve.getPricedAssets()]
    for asset, pool in routes:
        assert curve.addNewPriceFeed(asset, pool, sender=SAFE)
        assert curve.confirmNewPriceFeed(asset, sender=SAFE)
    ref = old_curve.greenRefPoolConfig()
    assert curve.setGreenRefPoolConfig(
        ref.pool,
        int(ref.maxNumSnapshots),
        int(ref.dangerTrigger),
        int(ref.staleBlocks),
        int(ref.stabilizerAdjustWeight),
        int(ref.stabilizerMaxPoolDebt),
        sender=SAFE,
    )
    assert curve.confirmGreenRefPoolConfig(len(routes) + 1, sender=SAFE)


def _settle_stability_claims(hq, migrator, source_stability, stability_users):
    eligible = [
        user for user in stability_users
        if source_stability.doesUserHaveBalance(user, GREEN_POOL)
    ]
    claims = [
        (GREEN_POOL, asset, MAX_UINT)
        for asset in STABILITY_CLAIM_ASSETS
        if int(source_stability.claimableBalances(GREEN_POOL, asset)) != 0
    ]
    assert len(claims) == len(STABILITY_CLAIM_ASSETS)
    assert _address(hq.getAddr(17)) == _address(OLD_TELLER)
    print(f"[claims] settling {len(claims)} assets for {len(eligible)} depositors")

    before_pool = {
        _address(asset): int(_erc20(asset).balanceOf(source_stability))
        for asset in STABILITY_CLAIM_ASSETS
    }
    before_users = {
        (_address(user), _address(asset)): int(_erc20(asset).balanceOf(user))
        for user in eligible
        for asset in STABILITY_CLAIM_ASSETS
    }
    for claim_index, claim_batch in enumerate(_batch(claims, 10), start=1):
        print(f"[claims] executing claim group {claim_index}")
        for users in _batch(eligible, 25):
            assert int(migrator.settleStabilityPoolClaims(
                users, 1, claim_batch, sender=SAFE
            )) != 0

    residual_usd = 0
    prices = _at("contracts/registries/PriceDesk.vy", hq.getAddr(7))
    for asset in STABILITY_CLAIM_ASSETS:
        residual = int(source_stability.claimableBalances(GREEN_POOL, asset))
        print(f"[claims] residual {asset}: {residual}")
        residual_usd += int(prices.getUsdValue(asset, residual))
        pool_delta = before_pool[_address(asset)] - int(_erc20(asset).balanceOf(source_stability))
        user_delta = sum(
            int(_erc20(asset).balanceOf(user)) - before_users[(_address(user), _address(asset))]
            for user in eligible
        )
        assert pool_delta == user_delta
    print(f"[claims] aggregate residual USD (1e18): {residual_usd}")
    assert residual_usd <= 10**6
    return eligible


def _finish_registry_activation(hq, replacements):
    print("[safe] activating the remaining HQ generation")
    for name, registry_id in replacements:
        if registry_id in (5, 7):
            continue
        assert hq.confirmAddressUpdateToRegistry(registry_id, sender=SAFE), name


def _promote(history, files, deploy_args):
    print("[manifest] authenticating and promoting the active generation")
    runner = MigrationRunner(
        str(ROOT / "migrations/base-mainnet"), str(history), files
    )
    runner.run(deploy_args, "2026082403", "2026082403", False)


def _configure_target_routes(mc, bravo, charlie, source_positions):
    target_ids = defaultdict(set)
    for source_id, positions in source_positions.items():
        for user_positions in positions.values():
            for asset in user_positions:
                target_ids[asset].add(TARGET_VAULT_IDS[source_id])

    print(f"[vaults] adding target routes for {len(target_ids)} assets")
    for asset, targets in target_ids.items():
        config = mc.assetConfig(asset)
        vault_ids = list(config.vaultIds)
        for target in sorted(targets):
            if target not in vault_ids:
                vault_ids.append(target)
        _execute_action(
            bravo,
            bravo.setAssetDepositParams,
            asset,
            vault_ids,
            int(config.stakersPointsAlloc),
            int(config.voterPointsAlloc),
            int(config.perUserDepositLimit),
            int(config.globalDepositLimit),
            int(config.minDepositBalance),
        )

    _execute_action(charlie, charlie.setPreferredStabVaultId, 6)
    _execute_action(charlie, charlie.setCoreRipeGovVaultId, 7)


def _install_legacy_ripe_wind_down(mc, alpha, ripe_assets):
    original = {}
    for asset in ripe_assets:
        config = mc.ripeGovVaultConfig(asset)
        original[asset] = tuple(config)
        terms = config.lockTerms
        assert int(terms.minLockDuration) < int(terms.maxLockDuration)
        _execute_action(
            alpha,
            alpha.setRipeGovVaultConfig,
            asset,
            int(config.assetWeight),
            bool(config.shouldFreezeWhenBadDebt),
            int(terms.minLockDuration) + 1,
            int(terms.maxLockDuration),
            int(terms.maxLockBoost),
            int(terms.exitFee),
            bool(terms.canExit),
        )
    return original


def _restore_ripe_config(alpha, original):
    for asset, config in original.items():
        asset_weight, freeze, terms = config
        _execute_action(
            alpha,
            alpha.setRipeGovVaultConfig,
            asset,
            int(asset_weight),
            bool(freeze),
            int(terms.minLockDuration),
            int(terms.maxLockDuration),
            int(terms.maxLockBoost),
            int(terms.exitFee),
            bool(terms.canExit),
        )


def _slot_batches(users, positions, maximum=20):
    batch = []
    slots = 0
    for user in users:
        count = len(positions.get(_address(user), {}))
        if batch and slots + count > maximum:
            yield batch
            batch, slots = [], 0
        batch.append(user)
        slots += count
    if batch:
        yield batch


def _migrate_vaults(echo, migrator, charlie, sources, targets, users, positions):
    print("[vaults] migrating StabilityPool, ordinary, and Underscore positions")
    for source_id in (1, 3, 4, 5):
        active = sorted(positions[source_id])
        for group in _batch(active, 25):
            expected = sum(len(positions[source_id][_address(user)]) for user in group)
            result = int(echo.migrateVaultPositions(
                group, source_id, TARGET_VAULT_IDS[source_id], sender=SAFE
            ))
            assert result == expected

    print("[vaults] migrating legacy RipeGov positions with preserved terms")
    assert charlie.pause(targets[2], True, sender=SAFE)
    for group in _slot_batches(sorted(positions[2]), positions[2]):
        expected = sum(len(positions[2][_address(user)]) for user in group)
        assert int(echo.migrateLegacyRipeGovPositions(group, sender=SAFE)) == expected

    for source_id, source in sources.items():
        assert _positions(source, users[source_id]) == {}
    for source_id, expected_positions in positions.items():
        target_positions = _positions(targets[source_id], list(expected_positions))
        if source_id != 2:
            assert target_positions == expected_positions
        else:
            for user, assets in expected_positions.items():
                for asset, amount in assets.items():
                    assert target_positions[user][asset] == amount


def _restore_operational_state(manifest, alpha, echo, charlie, moved, psm_amount):
    credit = _candidate(manifest, "CreditEngine")
    if int(credit.buybackRatio()) != 2_000:
        _execute_action(alpha, alpha.setBuybackRatio, 2_000)

    psm = _candidate(manifest, "EndaomentPSM")
    if not psm.canMint():
        _execute_action(echo, echo.setPsmCanMint, True)
    if not psm.canRedeem():
        _execute_action(echo, echo.setPsmCanRedeem, True)
    if not psm.shouldEnforceRedeemAllowlist():
        _execute_action(echo, echo.setPsmShouldEnforceRedeemAllowlist, True)

    new_funds = _candidate(manifest, "EndaomentFunds")
    for asset, amount in moved.items():
        assert int(_erc20(asset).balanceOf(new_funds)) == amount
    assert int(_erc20(USDC).balanceOf(psm)) == psm_amount

    # Migration is complete: target RipeGov and Teller return to operation;
    # sources and VaultMigrator are closed.
    targets = {
        2: _candidate(manifest, "RipeGov"),
    }
    teller = _candidate(manifest, "Teller")
    migrator = _candidate(manifest, "VaultMigrator")
    assert charlie.pause(targets[2], False, sender=SAFE)
    assert charlie.pause(teller, False, sender=SAFE)
    assert charlie.pause(migrator, True, sender=SAFE)
    for _, address in SOURCE_VAULTS.values():
        source = _at("contracts/vaults/StabilityPool.vy", address) if _address(address) == _address(SOURCE_VAULTS[1][1]) else _at("contracts/vaults/SimpleErc20.vy", address)
        if not source.isPaused():
            assert charlie.pause(address, True, sender=SAFE)


def main():
    _load_dotenv()
    rpc = os.environ.get("BASE_MAINNET_RPC_URL")
    if not rpc:
        raise RuntimeError("BASE_MAINNET_RPC_URL is not configured")

    census = _discover_live_state(rpc)
    history = _isolate_fork_history(
        ROOT / "migration_history/base-mainnet/v1", "base-mainnet-rehearsal"
    )
    files = load_vyper_files()
    deploy_args = DeployArgs(
        MockAccount(DEPLOYER),
        "base-mainnet",
        False,
        "base",
        rpc,
        local_preview=True,
    )
    boa.deployments.set_deployments_db(boa.deployments.DeploymentsDB(":memory:"))

    with boa.fork(rpc, block_identifier=BLOCK, allow_dirty=True):
        boa.env.set_balance(DEPLOYER, 100 * 10**18)
        boa.env.set_balance(SAFE, 100 * 10**18)

        hq = _at("contracts/registries/RipeHq.vy", HQ)
        old_mc = _at("contracts/data/MissionControl.vy", OLD_MISSION_CONTROL)
        old_curve = _at("contracts/priceSources/CurvePrices.vy", "0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d")
        sources = {
            vault_id: _at(f"contracts/vaults/{name}.vy", address)
            for vault_id, (name, address) in SOURCE_VAULTS.items()
        }
        cached_active = census.get("active_users")
        if cached_active:
            users = {
                vault_id: cached_active[str(vault_id)]
                for vault_id in SOURCE_VAULTS
            }
        else:
            users = {
                vault_id: _active_users(
                    sources[vault_id], census["vault_users"][str(vault_id)]
                )
                for vault_id in SOURCE_VAULTS
            }
            census["active_users"] = {
                str(vault_id): value for vault_id, value in users.items()
            }
            CACHE.write_text(json.dumps(census, indent=2, sort_keys=True))
        print("[preflight] active users:", {key: len(value) for key, value in users.items()})

        debt_before = int(_at("contracts/data/Ledger.vy", hq.getAddr(4)).totalDebt())
        old_psm = _at("contracts/core/EndaomentPSM.vy", hq.getAddr(22))
        old_psm_state = (
            bool(old_psm.canMint()), bool(old_psm.canRedeem()),
            bool(old_psm.shouldEnforceRedeemAllowlist()),
        )
        assert old_psm_state == (True, True, True)

        print("[deploy] running 2026082402 inside the pinned fork")
        runner = MigrationRunner(
            str(ROOT / "migrations/base-mainnet"), str(history), files
        )
        runner.run(deploy_args, "2026082402", "2026082402", False)
        manifest = json.loads((history / "current-manifest.json").read_text())

        moved, psm_amount = _move_protocol_funds(hq, manifest)
        replacements, migrator = _start_registry_activation(hq, manifest)
        new_mc, configs, delegations = _activate_state(
            hq, manifest, migrator, census, old_mc
        )
        claim_users = _settle_stability_claims(
            hq, migrator, sources[1], users[1]
        )
        _activate_oracles(hq, manifest, old_curve)
        _finish_registry_activation(hq, replacements)
        _promote(history, files, deploy_args)

        # Claims can create fresh RIPE positions in the legacy governance vault.
        users[2] = sorted(set(users[2]) | set(claim_users))
        source_positions = {
            vault_id: _positions(sources[vault_id], users[vault_id])
            for vault_id in SOURCE_VAULTS
        }
        print(
            "[preflight] positions after claims:",
            {key: sum(map(len, value.values())) for key, value in source_positions.items()},
        )

        switchboard = _candidate(manifest, "Switchboard")
        alpha = _candidate(manifest, "SwitchboardAlpha")
        bravo = _candidate(manifest, "SwitchboardBravo")
        charlie = _candidate(manifest, "SwitchboardCharlie")
        echo = _candidate(manifest, "SwitchboardEcho")
        assert _address(switchboard.getAddr(1)) == _address(alpha)

        targets = {
            1: _candidate(manifest, "StabilityPool"),
            2: _candidate(manifest, "RipeGov"),
            3: _candidate(manifest, "SimpleErc20"),
            4: _candidate(manifest, "RebaseErc20"),
            5: _candidate(manifest, "UnderscoreVault"),
        }
        _configure_target_routes(new_mc, bravo, charlie, source_positions)
        ripe_assets = sorted({asset for positions in source_positions[2].values() for asset in positions})
        ripe_config = _install_legacy_ripe_wind_down(new_mc, alpha, ripe_assets)
        _migrate_vaults(echo, migrator, charlie, sources, targets, users, source_positions)
        _restore_ripe_config(alpha, ripe_config)
        _restore_operational_state(manifest, alpha, echo, charlie, moved, psm_amount)

        ledger = _at("contracts/data/Ledger.vy", hq.getAddr(4))
        assert int(ledger.totalDebt()) >= debt_before
        for user, expected in configs.items():
            assert tuple(new_mc.userConfig(user)) == expected
        for (user, delegate), expected in delegations.items():
            assert tuple(new_mc.userDelegation(user, delegate)) == expected
        assert _address(hq.getAddr(23)) == "0x6e3f8465af365a2c400c361783ea51ad44b3c836"
        assert _address(hq.getAddr(24)) == "0xef56e5036728718baa577257ff4fa9259e9e895f"
        print("[PASS] funded Base redeployment reconciled at", BLOCK, BLOCK_HASH)


if __name__ == "__main__":
    main()
