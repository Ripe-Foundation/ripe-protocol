"""Retained RipeGov compatibility using authenticated historical dependencies.

Known legacy checkpoint/zero-weight/pause behavior is documented explicitly;
passing those boundary tests does not assert that inherited behavior is fixed.
"""

import boa
import pytest
import hashlib
import json
from pathlib import Path
from constants import EIGHTEEN_DECIMALS as WAD, MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs
from conf_legacy_pool import calls_to
from core.auctionHouse import test_base_legacy_vault_compat as legacy_tests
from core.auctionHouse.test_base_legacy_vault_compat import (
    mature,
    legacy_gov_state,
    assert_legacy_gov_call,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "legacy_governance"
PROVENANCE = json.loads((FIXTURES / "provenance.json").read_text())


def authenticate_sources():
    for source, expected in PROVENANCE["source_sha256"].items():
        assert hashlib.sha256((FIXTURES / source).read_bytes()).hexdigest() == expected


@pytest.fixture
def legacy_gov_env(historical_ledger, legacy_env, setRipeRewardsConfig):
    legacy_env.ledger = historical_ledger
    return legacy_tests.legacy_gov_env.__wrapped__(legacy_env, setRipeRewardsConfig)


@pytest.fixture
def historical_ledger(ledger, ripe_hq_deploy, defaults):
    authenticate_sources()
    root = (FIXTURES / "ledger").resolve()
    previous = boa.interpret._search_path
    try:
        boa.interpret.set_search_path([str(root)])
        d = boa.load_partial(str(root / "contracts/data/Ledger.vy"))
    finally:
        boa.interpret.set_search_path(previous)
    c = d.deploy(ripe_hq_deploy, defaults)
    code = boa.env.get_code(c.address)
    prefix = len(d.compiler_data.bytecode_runtime)
    assert code[prefix : prefix + 32] == int(ripe_hq_deploy.address, 16).to_bytes(
        32, "big"
    )
    canonical = (
        code[:prefix]
        + bytes.fromhex(
            "0000000000000000000000006162df1b329e157479f8f1407e888260e0ec3d2b"
        )
        + code[prefix + 32 :]
    )
    assert (
        hashlib.sha256(canonical).hexdigest()
        == "a8cacd456cc038a74eba236eacbbe50cbde8af4d0f9cc4cb22f98653a67b0b5d"
    )
    # Restore the historical runtime only inside this test's anchored VM.
    # Overriding the session-wide Ledger fixture would leak its HQ binding into
    # unrelated modern-ledger tests when they run in the same pytest session.
    assert (
        d.compiler_data.storage_layout["storage_layout"]
        == ledger.compiler_data.storage_layout["storage_layout"]
    )
    previous_contract = boa.env.lookup_contract(ledger.address)
    try:
        with boa.env.anchor():
            boa.env.set_code(ledger.address, code)
            yield d.at(ledger.address)
    finally:
        # Boa does not anchor its address-to-source registry. Restore it after
        # the runtime so later tests decode modern Ledger reverts correctly.
        boa.env.register_contract(ledger.address, previous_contract)


def deposit(e, user, asset=None, amount=100 * WAD, lock=1000):
    asset = e.ripe if asset is None else asset
    if asset == e.ripe:
        asset.transfer(user, amount, sender=e.whale)
    else:
        asset.mint(user, amount, sender=e.gov.address)
    asset.approve(e.teller, amount, sender=user)
    assert e.teller.depositIntoGovVault(asset, amount, lock, sender=user) == amount


@pytest.fixture
def two_assets(legacy_gov_env):
    e = legacy_gov_env
    e.configure(e.lp, _vaultIds=[2], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    e.mc.setRipeGovVaultConfig(
        e.lp, 15000, False, (100, 1_000_000, 20000, True, 1000), sender=e.alpha.address
    )
    return e


@pytest.mark.parametrize("asset_name", ["ripe", "lp"])
def test_retained_deposit_and_withdraw(two_assets, asset_name):
    e = two_assets
    asset = getattr(e, asset_name)
    deposit(e, e.bob, asset)
    assert e.ripe_gov.getTotalAmountForUser(e.bob, asset) == 100 * WAD
    with boa.reverts("not reached unlock"):
        e.teller.withdraw(asset, MAX_UINT256, e.bob, e.ripe_gov, sender=e.bob)
    boa.env.time_travel(blocks=1000)
    assert (
        e.teller.withdraw(asset, MAX_UINT256, e.bob, e.ripe_gov, sender=e.bob)
        == 100 * WAD
    )
    assert e.ripe_gov.userBalances(e.bob, asset) == 0
    assert asset.balanceOf(e.bob) == 100 * WAD


@pytest.mark.parametrize("auto_stake", [False, True])
def test_retained_positive_rewards(two_assets, setRipeRewardsConfig, auto_stake):
    e = two_assets
    setRipeRewardsConfig(
        _ripePerBlock=WAD,
        _borrowersAlloc=0,
        _stakersAlloc=5000,
        _votersAlloc=5000,
        _genDepositorsAlloc=0,
    )
    e.ledger.setRipeAvailForRewards(100_000 * WAD, sender=e.alpha.address)
    deposit(e, e.bob, e.ripe)
    deposit(e, e.bob, e.lp)
    boa.env.time_travel(blocks=100)
    claimable = e.lootbox.getClaimableLoot(e.bob)
    assert claimable > 0
    before = e.ripe.totalSupply()
    custody = e.ripe.balanceOf(e.ripe_gov)
    e.teller.claimLoot(e.bob, auto_stake, sender=e.bob)
    minted = e.ripe.totalSupply() - before
    assert minted == claimable
    if auto_stake:
        assert e.ripe.balanceOf(e.ripe_gov) - custody == minted
    else:
        assert e.ripe.balanceOf(e.bob) == minted
    assert e.ledger.userDepositPoints(
        e.bob, 2, e.ripe
    ).lastBalance == e.ripe_gov.getUserLootBoxShare(e.bob, e.ripe)


def test_retained_modern_accrual_disable_is_unsupported(
    legacy_gov_env, switchboard_echo
):
    e = legacy_gov_env
    with boa.reverts():
        switchboard_echo.isValidRipeGovPointAccrualDisable(2, ZERO_ADDRESS)
    with boa.reverts():
        switchboard_echo.disableRipeGovPointAccrualGlobally(2, sender=e.gov.address)


@pytest.mark.parametrize("operation", ["adjust", "release"])
@pytest.mark.parametrize("base_policy", [False, True])
def test_retained_legacy_lock_leaves_stale_reward_checkpoint(
    legacy_gov_env, setRipeRewardsConfig, operation, base_policy
):
    e = legacy_gov_env
    setRipeRewardsConfig(
        _ripePerBlock=WAD,
        _borrowersAlloc=0,
        _stakersAlloc=5000,
        _votersAlloc=5000,
        _genDepositorsAlloc=0,
    )
    if base_policy:
        setRipeRewardsConfig(
            _ripePerBlock=7_500_000_000_000_000,
            _borrowersAlloc=1000,
            _stakersAlloc=9000,
            _votersAlloc=0,
            _genDepositorsAlloc=0,
        )
        e.mc.setRipeGovVaultConfig(
            e.ripe,
            10000,
            True,
            (43200, 47304000, 20000, True, 8000),
            sender=e.alpha.address,
        )
    e.ledger.setRipeAvailForRewards(100_000 * WAD, sender=e.alpha.address)
    deposit(e, e.bob, lock=100)
    deposit(e, e.alice, lock=100)
    boa.env.time_travel(blocks=10)
    if operation == "adjust":
        e.teller.adjustLock(
            e.ripe, 800000 if base_policy else 800, e.bob, 2, sender=e.bob
        )
    else:
        e.teller.releaseLock(e.ripe, e.bob, 2, sender=e.bob)
    saved = e.ledger.userDepositPoints(e.bob, 2, e.ripe)
    live = e.ripe_gov.getUserLootBoxShare(e.bob, e.ripe)
    assert saved.lastBalance != live
    if operation == "adjust":
        assert saved.lastBalance < live
    else:
        assert saved.lastBalance > live
    # Compare the uncorrected flow with a final-state checkpoint in the same block.
    with boa.env.anchor():
        e.lootbox.updateDepositPoints(
            e.bob, 2, e.ripe_gov, e.ripe, sender=e.teller.address
        )
        assert e.ledger.userDepositPoints(e.bob, 2, e.ripe).lastBalance == live
        boa.env.time_travel(blocks=20)
        corrected = e.lootbox.getClaimableLoot(e.bob)
        supply = e.ripe.totalSupply()
        e.teller.claimLoot(e.bob, False, sender=e.bob)
        assert e.ripe.totalSupply() - supply == corrected
    boa.env.time_travel(blocks=20)
    latest = e.lootbox.getLatestDepositPoints(e.bob, 2, e.ripe)[0]
    assert latest.balancePoints - saved.balancePoints == saved.lastBalance * 20
    uncorrected = e.lootbox.getClaimableLoot(e.bob)
    assert uncorrected != corrected
    if operation == "adjust":
        assert uncorrected < corrected
    else:
        assert uncorrected > corrected
    supply = e.ripe.totalSupply()
    e.teller.claimLoot(e.bob, False, sender=e.bob)
    assert e.ripe.totalSupply() - supply == uncorrected
    print(
        {
            "operation": operation,
            "base_emissions_and_lock_policy": base_policy,
            "saved": saved.lastBalance,
            "live": live,
            "uncorrected": uncorrected,
            "corrected": corrected,
        }
    )


def test_retained_legacy_zero_weight_keeps_accruing(legacy_gov_env):
    e = legacy_gov_env
    deposit(e, e.bob)
    boa.env.time_travel(blocks=100)
    gd = e.ripe_gov.userGovData(e.bob, e.ripe)
    zero = e.ripe_gov.getLatestGovPoints(
        gd.lastShares, gd.lastPointsUpdate, gd.unlock, gd.lastTerms, 0
    )
    full = e.ripe_gov.getLatestGovPoints(
        gd.lastShares, gd.lastPointsUpdate, gd.unlock, gd.lastTerms, 10000
    )
    assert zero == full and zero > 0


def test_retained_paused_legacy_still_allows_lock_update(legacy_gov_env):
    e = legacy_gov_env
    deposit(e, e.bob)
    e.ripe_gov.pause(True, sender=e.alpha.address)
    before = e.ripe_gov.userGovData(e.bob, e.ripe).unlock
    e.teller.adjustLock(e.ripe, 2000, e.bob, 2, sender=e.bob)
    assert e.ripe_gov.userGovData(e.bob, e.ripe).unlock > before
    e.teller.releaseLock(e.ripe, e.bob, 2, sender=e.bob)
    assert e.ripe_gov.userGovData(e.bob, e.ripe).unlock == 0


@pytest.fixture
def historical_contributor_env(legacy_gov_env, human_resources, switchboard_delta):
    e = legacy_gov_env
    e.hr = human_resources
    e.delta = switchboard_delta
    authenticate_sources()
    deployer = boa.load_partial(str(FIXTURES / "Contributor.vy"))
    assert (
        hashlib.sha256(deployer.compiler_data.bytecode_runtime).hexdigest()
        == PROVENANCE["contributor"]["compiled_runtime_sha256"]
    )
    bp = deployer.deploy_as_blueprint()
    vesting = 2 * 365 * 24 * 3600
    compensation = 1000 * WAD
    e.mc.setHrConfig(
        (bp.address, compensation, 1, 100, 1, vesting), sender=e.delta.address
    )
    e.ledger.setRipeAvailForHr(2 * compensation, sender=e.delta.address)
    aid = e.hr.initiateNewContributor(
        e.bob,
        e.alice,
        compensation,
        0,
        vesting,
        90 * 24 * 3600,
        365 * 24 * 3600,
        200_000,
        sender=e.gov.address,
    )
    mature(e.hr, aid)
    assert e.hr.confirmNewContributor(aid, sender=e.gov.address)
    addr = filter_logs(e.hr, "NewContributorConfirmed")[0].contributorAddr
    e.contributor = deployer.at(addr)
    code = boa.env.get_code(addr)
    words = b"".join(
        v.to_bytes(32, "big") for v in PROVENANCE["contributor"]["immutable_words"]
    )
    assert (
        hashlib.sha256(code[:-96] + words).hexdigest()
        == PROVENANCE["contributor"]["runtime_sha256"]
    )
    return e


@pytest.mark.parametrize("operation", ["transfer", "cancel"])
def test_retained_historical_contributor_callbacks(
    historical_contributor_env, operation
):
    e = historical_contributor_env
    c = e.contributor
    t = c.unlockTime() + 1 if operation == "transfer" else c.startTime() + 100
    boa.env.time_travel(seconds=t - boa.env.evm.patch.timestamp)
    claimed = c.cashRipeCheck(sender=e.bob)
    assert claimed > 0 and e.ripe_gov.getTotalAmountForUser(c, e.ripe) == claimed
    if operation == "transfer":
        c.initiateRipeTransfer(False, sender=e.bob)
        boa.env.time_travel(
            blocks=c.pendingRipeTransfer().confirmBlock - boa.env.evm.patch.block_number
        )
        c.confirmRipeTransfer(False, sender=e.bob)
        assert e.ripe_gov.getTotalAmountForUser(e.bob, e.ripe) == claimed
    else:
        aid = e.delta.cancelPaycheckForContributor(c, sender=e.gov.address)
        mature(e.delta, aid)
        assert e.delta.executePendingAction(aid, sender=e.gov.address)
        assert e.ripe.balanceOf(e.ripe_gov) == 0
    assert e.ripe_gov.userBalances(c, e.ripe) == 0


def contributor_state(e):
    c = e.contributor
    return (
        legacy_gov_state(e, (c.address, e.bob)),
        e.ripe.balanceOf(e.hr),
        e.ripe.allowance(e.hr, e.teller),
        e.ledger.ripeAvailForHr(),
        c.compensation(),
        c.totalClaimed(),
        c.endTime(),
        c.pendingRipeTransfer(),
        e.hr.legacyContributorRipeGovVaultId(c),
    )


def cash_legacy_contributor(e, timestamp):
    boa.env.time_travel(seconds=timestamp - boa.env.evm.patch.timestamp)
    before = e.ripe.totalSupply()
    claimed = e.contributor.cashRipeCheck(sender=e.bob)
    assert claimed > 0 and claimed == e.contributor.totalClaimed()
    assert e.ripe.totalSupply() == before + claimed
    assert e.ripe_gov.getTotalAmountForUser(e.contributor, e.ripe) == claimed
    assert e.ripe.balanceOf(e.ripe_gov) == claimed
    assert e.ripe.balanceOf(e.hr) == 0 and e.ripe.allowance(e.hr, e.teller) == 0
    assert (
        e.ripe_gov.userGovData(e.contributor, e.ripe).unlock
        > boa.env.evm.patch.block_number
    )
    return claimed


@pytest.mark.parametrize("paused_ledger", [False, True])
def test_historical_hr_callback_transfers_contributor_position(
    historical_contributor_env, paused_ledger
):
    e = historical_contributor_env
    c = e.contributor
    claimed = cash_legacy_contributor(e, c.unlockTime() + 1)
    shares = e.ripe_gov.userBalances(c, e.ripe)
    before = contributor_state(e)
    with boa.reverts("not allowed"):
        e.ripe_gov.transferContributorRipeTokens(c, e.bob, 200_000, sender=e.bob)
    assert contributor_state(e) == before
    c.initiateRipeTransfer(False, sender=e.bob)
    boa.env.time_travel(
        blocks=c.pendingRipeTransfer().confirmBlock - boa.env.evm.patch.block_number
    )
    assert e.ripe_gov.userGovData(c, e.ripe).unlock > boa.env.evm.patch.block_number
    if paused_ledger:
        e.ledger.pause(True, sender=e.alpha.address)
        before = contributor_state(e)
        # Contributor labels a failed HR call with its own dev reason.
        with boa.reverts("could not transfer"):
            c.confirmRipeTransfer(False, sender=e.bob)
        assert_legacy_gov_call(
            c._computation,
            e,
            "transferContributorRipeTokens",
            "address,address,uint256",
            e.hr,
        )
        registrations = calls_to(
            c._computation, e.ledger.address, "addVaultToUser(address,uint256)"
        )
        assert len(registrations) == 1 and registrations[0].is_error
        assert contributor_state(e) == before
        e.ledger.pause(False, sender=e.alpha.address)
    supply, budget = e.ripe.totalSupply(), e.ledger.ripeAvailForHr()
    c.confirmRipeTransfer(False, sender=e.bob)
    assert_legacy_gov_call(
        c._computation,
        e,
        "transferContributorRipeTokens",
        "address,address,uint256",
        e.hr,
    )
    assert e.ripe_gov.userBalances(c, e.ripe) == 0
    assert (
        e.ripe_gov.userBalances(e.bob, e.ripe)
        == shares
        == e.ripe_gov.totalBalances(e.ripe)
    )
    assert e.ripe_gov.getTotalAmountForUser(e.bob, e.ripe) == claimed
    assert (
        e.ripe_gov.userGovData(e.bob, e.ripe).unlock
        == boa.env.evm.patch.block_number + 200_000
    )
    assert e.ledger.indexOfVault(e.bob, 2) != 0
    # HR checkpoints the emptied position; Lootbox removes its registry row
    # later during claimLoot, after any accrued reward entitlement is settled.
    assert e.ledger.indexOfVault(c, 2) != 0
    assert e.ledger.userDepositPoints(c, 2, e.ripe).lastBalance == 0
    owner_points = e.ripe_gov.getUserLootBoxShare(e.bob, e.ripe)
    assert e.ledger.userDepositPoints(e.bob, 2, e.ripe).lastBalance == owner_points > 0
    assert e.ledger.assetDepositPoints(2, e.ripe).lastBalance == owner_points
    assert not c.hasPendingRipeTransfer()
    assert c.totalClaimed() == claimed and e.ledger.ripeAvailForHr() == budget
    assert e.ripe.balanceOf(e.ripe_gov) == claimed and e.ripe.totalSupply() == supply
    assert e.ripe.balanceOf(e.hr) == e.ripe.balanceOf(e.bob) == 0


@pytest.mark.parametrize("paused_ledger", [False, True])
def test_historical_hr_callback_cancels_burns_and_restores_budget(
    historical_contributor_env, paused_ledger
):
    e = historical_contributor_env
    c = e.contributor
    compensation = c.compensation()
    claimed = cash_legacy_contributor(
        e, c.startTime() + (c.cliffTime() - c.startTime()) // 2
    )
    before = contributor_state(e)
    with boa.reverts("not allowed"):
        e.ripe_gov.withdrawContributorTokensToBurn(c, sender=e.bob)
    assert contributor_state(e) == before
    aid = e.delta.cancelPaycheckForContributor(c, sender=e.gov.address)
    mature(e.delta, aid)
    assert boa.env.evm.patch.timestamp < c.cliffTime()
    assert e.ripe_gov.userGovData(c, e.ripe).unlock > boa.env.evm.patch.block_number
    if paused_ledger:
        e.ledger.pause(True, sender=e.alpha.address)
        before = contributor_state(e)
        with boa.reverts("not activated"):
            e.delta.executePendingAction(aid, sender=e.gov.address)
        assert_legacy_gov_call(
            e.delta._computation, e, "withdrawContributorTokensToBurn", "address", e.hr
        )
        assert contributor_state(e) == before and e.delta.hasPendingAction(aid)
        e.ledger.pause(False, sender=e.alpha.address)
    supply, budget = e.ripe.totalSupply(), e.ledger.ripeAvailForHr()
    assert e.delta.executePendingAction(aid, sender=e.gov.address)
    trace = e.delta._computation
    assert_legacy_gov_call(trace, e, "withdrawContributorTokensToBurn", "address", e.hr)
    burns = calls_to(trace, e.ripe.address, "burn(uint256)")
    assert len(burns) == 1 and not burns[0].is_error
    assert burns[0].msg.sender == bytes.fromhex(e.hr.address[2:])
    assert e.ripe.totalSupply() == supply - claimed
    assert (
        e.ripe.balanceOf(e.ripe_gov)
        == e.ripe.balanceOf(e.hr)
        == e.ripe.balanceOf(e.bob)
        == 0
    )
    assert e.ripe_gov.userBalances(c, e.ripe) == e.ripe_gov.totalBalances(e.ripe) == 0
    # The points checkpoint clears the earning balance; registry cleanup is
    # deferred until Lootbox claims any accrued entitlement.
    assert e.ledger.indexOfVault(c, 2) != 0
    assert e.ledger.userDepositPoints(c, 2, e.ripe).lastBalance == 0
    assert e.ledger.assetDepositPoints(2, e.ripe).lastBalance == 0
    assert e.ledger.ripeAvailForHr() == budget + compensation == 2 * compensation
    assert (
        c.compensation() == 0 and c.totalClaimed() == claimed and c.getClaimable() == 0
    )
    assert not e.delta.hasPendingAction(aid)


def test_retained_base_defaults_initialize_existing_vault_routes(
    legacy_gov_env,
    contributor_template,
    switchboard,
):
    e = legacy_gov_env
    defaults = boa.load("contracts/config/DefaultsBaseLive.vy", contributor_template)
    candidate = boa.load("contracts/data/MissionControl.vy", e.hq, ZERO_ADDRESS)
    setup = boa.load(
        "contracts/config/SwitchboardFoxtrot.vy", e.hq, ZERO_ADDRESS, 1, 1000
    )
    assert candidate.coreRipeGovVaultId() == 2
    assert candidate.isRipeGovVaultId(2)
    assert candidate.numAssets() == 1
    before = (e.hq.getAddr(4), e.book.getAddr(2), e.book.getRegId(e.ripe_gov))
    switchboard.startAddressUpdateToRegistry(6, setup, sender=e.gov.address)
    boa.env.time_travel(blocks=switchboard.registryChangeTimeLock())
    assert switchboard.confirmAddressUpdateToRegistry(6, sender=e.gov.address)
    setup.startDefaultsInitialization(candidate, defaults, sender=e.gov.address)
    with boa.reverts("governance or temporary setup governor"):
        setup.initConfig(sender=e.bob)
    with boa.reverts("once, after staging"):
        setup.initRewards(sender=e.gov.address)
    for _ in range(12):
        if setup.initStep() == 5:
            break
        setup.initConfig(sender=e.gov.address)
    assert setup.initStep() == 5 and not setup.rewardsInitialized()
    assert candidate.rewardsConfig().ripePerBlock == 0
    assert candidate.coreRipeGovVaultId() == 2 and candidate.isRipeGovVaultId(2)
    for entry in defaults.ripeGovVaultConfigs():
        asset = entry.asset
        assert candidate.assetConfig(asset).vaultIds == [2]
        assert candidate.rewardVaultId(asset) == 2
        assert candidate.ripeGovVaultConfig(asset) == entry.config
    assert before == (e.hq.getAddr(4), e.book.getAddr(2), e.book.getRegId(e.ripe_gov))
    assert e.book.isValidRegId(2)
    with boa.reverts("confirm MC first"):
        setup.initRewards(sender=e.gov.address)
    e.hq.startAddressUpdateToRegistry(5, candidate, sender=e.gov.address)
    boa.env.time_travel(blocks=e.hq.registryChangeTimeLock())
    assert e.hq.confirmAddressUpdateToRegistry(5, sender=e.gov.address)
    setup.initRewards(sender=e.gov.address)
    assert (
        setup.rewardsInitialized()
        and candidate.rewardsConfig() == defaults.rewardsConfig()
    )
    with boa.reverts("once, after staging"):
        setup.initRewards(sender=e.gov.address)
    assert before == (e.hq.getAddr(4), e.book.getAddr(2), e.book.getRegId(e.ripe_gov))


@pytest.mark.parametrize("at_cliff", [False, True])
def test_historical_cancellation_boundary(historical_contributor_env, at_cliff):
    e = historical_contributor_env
    c = e.contributor
    boa.env.time_travel(
        seconds=c.cliffTime() - boa.env.evm.patch.timestamp - int(not at_cliff)
    )
    before_budget, supply = e.ledger.ripeAvailForHr(), e.ripe.totalSupply()
    with boa.reverts("no perms"):
        c.cancelPaycheck(sender=e.sally)
    c.cancelPaycheck(sender=e.delta.address)
    claimed = c.totalClaimed()
    assert (claimed > 0) == at_cliff
    assert e.ripe_gov.getTotalAmountForUser(c, e.ripe) == claimed
    assert e.ripe.totalSupply() - supply == claimed
    assert e.ledger.ripeAvailForHr() - before_budget == 1000 * WAD - claimed
    assert c.compensation() == claimed


def test_historical_transfer_delay_and_authorization(historical_contributor_env):
    e = historical_contributor_env
    c = e.contributor
    boa.env.time_travel(seconds=c.unlockTime() - boa.env.evm.patch.timestamp)
    c.cashRipeCheck(sender=e.bob)
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(False, sender=e.bob)
    boa.env.time_travel(seconds=1)
    with boa.reverts("no perms"):
        c.initiateRipeTransfer(False, sender=e.sally)
    c.initiateRipeTransfer(False, sender=e.bob)
    before = contributor_state(e)
    with boa.reverts("time delay not reached"):
        c.confirmRipeTransfer(False, sender=e.bob)
    assert contributor_state(e) == before
    boa.env.time_travel(
        blocks=c.pendingRipeTransfer().confirmBlock - boa.env.evm.patch.block_number
    )
    with boa.reverts("no perms"):
        c.confirmRipeTransfer(False, sender=e.sally)
    c.confirmRipeTransfer(False, sender=e.bob)
    assert not c.hasPendingRipeTransfer()
    assert e.ripe_gov.userBalances(c, e.ripe) == 0


@pytest.mark.parametrize("paused_ledger", [False, True])
def test_historical_ledger_stability_bonus_stakes_in_retained_gov(
    historical_ledger, legacy_env, setRipeRewardsConfig, paused_ledger
):
    legacy_env.ledger = historical_ledger
    e = legacy_tests.legacy_claim_env.__wrapped__(legacy_env, setRipeRewardsConfig)
    if paused_ledger:
        legacy_tests.test_paused_ledger_rolls_back_legacy_claim_and_reward_mint(e)
    else:
        legacy_tests.test_legacy_claim_mints_rewards_and_stakes_in_retained_vault2(e)
