import hashlib

import boa
import pytest

from constants import EIGHTEEN_DECIMALS as WAD, ZERO_ADDRESS
from conf_legacy_pool import PROVENANCE, calls_to, storage_write


def deploy_book(hq, binding):
    return boa.load("contracts/registries/VaultBook.vy", hq, ZERO_ADDRESS, 1, 1000, binding)


def test_historical_runtime_and_missing_modern_selector(legacy_pool, ripe_hq, stability_pool):
    code = boa.env.get_code(legacy_pool.address)
    canonical = code[:-32] + bytes.fromhex(PROVENANCE["pool"]["immutable_word"])
    assert hashlib.sha256(canonical).hexdigest() == PROVENANCE["pool"]["deployed_sha256"]
    assert legacy_pool.getRipeHq() == ripe_hq.address
    assert "canAcceptLiquidationAsset" not in {x.get("name") for x in legacy_pool.abi}
    with boa.reverts():
        boa.load_partial("contracts/vaults/StabilityPool.vy").at(legacy_pool.address).canAcceptLiquidationAsset(ZERO_ADDRESS, ZERO_ADDRESS)


@pytest.mark.parametrize("chain", [8453, 1, 42161])
@pytest.mark.parametrize("bound", [False, True])
def test_constructor_chain_and_binding(base_chain, legacy_pool, ripe_hq, chain, bound):
    boa.env.evm.patch.chain_id = chain
    if bound and chain != 8453:
        with boa.reverts("legacy pool only on Base"):
            deploy_book(ripe_hq, legacy_pool)
    else:
        deploy_book(ripe_hq, legacy_pool if bound else ZERO_ADDRESS)


def test_constructor_rejects_wrong_hq_and_noncontract(base_chain, legacy_pool_deployer, ripe_hq, bob):
    other = legacy_pool_deployer.deploy(bob)
    with boa.reverts("invalid legacy hq"):
        deploy_book(ripe_hq, other)
    with boa.reverts("invalid legacy pool"):
        deploy_book(ripe_hq, bob)


@pytest.mark.parametrize("missing", ["indexOfAsset", "claimableBalances", "totalClaimableBalances", "isPaused", "vaultAssets", "getUserAssetAtIndexAndHasBalance"])
def test_constructor_requires_legacy_getters(base_chain, ripe_hq, missing):
    methods = {
        "indexOfAsset": "def indexOfAsset(a: address) -> uint256:\n    return 0",
        "claimableBalances": "def claimableBalances(a: address, b: address) -> uint256:\n    return 0",
        "totalClaimableBalances": "def totalClaimableBalances(a: address) -> uint256:\n    return 0",
        "isPaused": "def isPaused() -> bool:\n    return False",
        "vaultAssets": "def vaultAssets(i: uint256) -> address:\n    return empty(address)",
        "getUserAssetAtIndexAndHasBalance": "def getUserAssetAtIndexAndHasBalance(u: address, i: uint256) -> (address, bool):\n    return empty(address), False",
    }
    source = f"@external\n@view\ndef getRipeHq() -> address:\n    return {ripe_hq.address}\n"
    for name, body in methods.items():
        if name != missing:
            source += "\n@external\n@view\n" + body + "\n"
    candidate = boa.loads(source)
    with boa.reverts():
        deploy_book(ripe_hq, candidate)


@pytest.mark.parametrize("corruption", ["unregistered", "wrong_id", "wrong_address", "invalid_row"])
def test_bound_identity_is_checked_before_dispatch(legacy_env, corruption):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD)
    if corruption == "unregistered":
        storage_write(e.book, "registry", "addrToRegId", [e.pool], 0)
    elif corruption == "wrong_id":
        storage_write(e.book, "registry", "addrToRegId", [e.pool], 2)
    elif corruption == "wrong_address":
        storage_write(e.book, "registry", "addrInfo", [1], e.ordinary)
    else:
        storage_write(e.book, "registry", "numAddrs", [], 1)
    assert e.ready() is False
    assert e.book.hasStabilityPoolInterface(e.pool, e.lp, e.collateral) is False
    for is_stab in (True, False):
        assert e.nav(is_stab=is_stab) == (ZERO_ADDRESS, 0)


def test_zero_binding_and_identical_unbound_pool_do_not_select_legacy(legacy_env, legacy_pool_deployer):
    e = legacy_env
    unbound = legacy_pool_deployer.deploy(e.hq)
    assert boa.env.get_code(unbound.address) == boa.env.get_code(e.pool.address)
    zero_book = deploy_book(e.hq, ZERO_ADDRESS)
    for book, pool in ((zero_book, e.pool), (e.book, unbound)):
        with boa.reverts():
            book.canAcceptLiquidationAsset(pool, e.lp, e.collateral)
        with boa.reverts():
            book.hasStabilityPoolInterface(pool, e.lp, e.collateral)
        assert book.getDeleverageTraversalAsset(e.bob, pool, 1, True) == (ZERO_ADDRESS, 0)


def test_empty_and_paused_pool_has_structural_support(legacy_env):
    e = legacy_env
    assert e.pool.vaultAssets(1) == ZERO_ADDRESS
    for paused in (False, True):
        if paused:
            e.pool.pause(True, sender=e.alpha.address)
        assert e.book.hasStabilityPoolInterface(e.pool, e.sg, ZERO_ADDRESS)
        assert e.book.hasStabilityPoolInterface(e.pool, e.sg, e.sg)
        assert not e.ready(e.sg)


@pytest.mark.parametrize("result", [False, True])
def test_modern_forwarding_decodes_false_as_support_without_registry_membership(legacy_env, result):
    e = legacy_env
    pool = boa.loads(f'''
@external
@view
def canAcceptLiquidationAsset(a: address, b: address) -> bool:
    assert a == {e.lp.address} and b == {e.collateral.address}
    return {result}
@external
@view
def getUserAssetAndAmountAtIndex(u: address, i: uint256) -> (address, uint256):
    assert u == {e.bob} and i == 7
    return {e.lp.address}, 123456789
@external
@view
def getUserAssetAtIndexAndHasBalance(u: address, i: uint256) -> (address, bool):
    assert u == {e.bob}
    return {e.lp.address}, i == 7
''')
    assert e.book.getRegId(pool) == 0
    assert e.book.canAcceptLiquidationAsset(pool, e.lp, e.collateral) is result
    assert e.book.hasStabilityPoolInterface(pool, e.lp, e.collateral)
    assert e.book.getDeleverageTraversalAsset(e.bob, pool, 7, True) == (e.lp.address, 123456789)
    assert e.book.getDeleverageTraversalAsset(e.bob, pool, 7, False) == (e.lp.address, 1)
    assert e.book.getDeleverageTraversalAsset(e.bob, pool, 8, False) == (e.lp.address, 0)


@pytest.mark.parametrize("body", [
    "@external\n@view\ndef unrelated() -> bool:\n    return True",
    "@external\n@view\ndef canAcceptLiquidationAsset(a: address, b: address):\n    pass",
    "@external\n@view\ndef canAcceptLiquidationAsset(a: address, b: address) -> uint256:\n    return 2",
    "@external\n@view\ndef canAcceptLiquidationAsset(a: address, b: address) -> bool:\n    raise \"modern readiness reverted\"",
])
def test_modern_missing_unexpected_and_reverting_methods_are_not_legacy(legacy_env, body):
    e = legacy_env
    pool = boa.loads(body)
    with boa.reverts():
        e.book.canAcceptLiquidationAsset(pool, e.lp, e.collateral)
    with boa.reverts():
        e.book.hasStabilityPoolInterface(pool, e.lp, e.collateral)
    for is_stab in (True, False):
        with boa.reverts():
            e.book.getDeleverageTraversalAsset(e.bob, pool, 1, is_stab)


def test_legacy_traversal_returns_nav_not_presence_or_cash_cap(legacy_env):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD)
    claim = e.token()
    e.prices.setPrice(claim, WAD)
    e.claim(claim, 200 * WAD, paid=10 * WAD)
    assert e.pool.getUserAssetAndAmountAtIndex(e.bob, 1) == (ZERO_ADDRESS, 0)
    assert e.pool.getUserAssetAtIndexAndHasBalance(e.bob, 1) == (e.lp.address, True)
    nav = e.pool.getTotalAmountForUser(e.bob, e.lp)
    assert nav == 290 * WAD > e.lp.balanceOf(e.pool)
    for is_stab in (True, False):
        assert e.nav(is_stab=is_stab) == (e.lp.address, nav)
    assert e.nav(index=9) == (ZERO_ADDRESS, 0)
    assert e.nav(user=e.alice) == (ZERO_ADDRESS, 0)
    assert e.ce.getUserBorrowTerms(e.bob, False).collateralVal == 0
    # A real floor to zero stays zero; no arbitrary dust threshold is added.
    storage_write(e.pool, "vaultData", "userBalances", [e.bob, e.lp], 1)
    assert e.pool.getTotalAmountForUser(e.bob, e.lp) == 0
    assert e.nav() == (e.lp.address, 0)
    storage_write(e.pool, "vaultData", "userBalances", [e.bob, e.lp], 0)
    assert e.nav() == (e.lp.address, 0)


@pytest.mark.parametrize("condition", ["paused", "cash_empty", "reserved", "over_reserved"])
def test_traversal_skips_before_strict_nav(legacy_env, condition):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD)
    claim = e.token()
    e.claim(claim, WAD)
    e.prices.setShouldRevert(claim, True)
    if condition == "paused":
        e.pool.pause(True, sender=e.alpha.address)
    elif condition == "cash_empty":
        e.lp.transfer(e.whale, e.lp.balanceOf(e.pool), sender=e.pool.address)
    else:
        storage_write(e.pool, "stabVault", "totalClaimableBalances", [e.lp],
                      e.lp.balanceOf(e.pool) + (condition == "over_reserved"))
    assert e.nav() == (e.lp.address, 0)
    assert not calls_to(e.book._computation, e.pool.address, "getTotalAmountForUser(address,address)")
    with boa.reverts("has price config, no price"):
        e.pool.getTotalAmountForUser(e.bob, e.lp)


def test_positive_custody_nav_keeps_strict_price_failures(legacy_env):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD)
    claim = e.token()
    e.claim(claim, WAD)
    e.prices.setShouldRevert(claim, True)
    assert e.ready()
    with boa.reverts("has price config, no price"):
        e.nav()
    with boa.reverts("has price config, no price"):
        e.dl.getDeleverageInfo(e.bob)


def test_real_modern_empty_and_paused_pool_support(vault_book, stability_pool, savings_green, switchboard_alpha):
    for paused in (False, True):
        if paused:
            stability_pool.pause(True, sender=switchboard_alpha.address)
        assert vault_book.hasStabilityPoolInterface(stability_pool, savings_green, ZERO_ADDRESS)
        assert not vault_book.canAcceptLiquidationAsset(stability_pool, savings_green, ZERO_ADDRESS)


def test_green_and_sgreen_readiness_uses_token_conversions(legacy_env):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD, e.sg)
    e.prices.setPrice(e.sg, 0)
    assert e.sg.convertToAssets(e.sg.balanceOf(e.pool)) > 0
    assert e.ready(e.sg)
    assert not calls_to(e.book._computation, e.pd.address, "getUsdValue(address,uint256)")
    e.configure(e.green, _vaultIds=[1], _debtTerms=e.terms(0, 0, 0, 0, 0, 0), _shouldBurnAsPayment=True)
    e.green.mint(e.bob, 100 * WAD, sender=e.ah.address)
    e.green.approve(e.teller, 100 * WAD, sender=e.bob)
    e.teller.deposit(e.green, 100 * WAD, e.bob, e.pool, sender=e.bob)
    e.prices.setPrice(e.green, 0)
    assert e.ready(e.green)
    assert not calls_to(e.book._computation, e.pd.address, "getUsdValue(address,uint256)")
