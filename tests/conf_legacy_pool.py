"""Local Base fixture using the authenticated historical Pool-1 and RipeGov-2 sources."""
from contextlib import contextmanager
from importlib.metadata import version
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest
from eth_utils import keccak

from constants import EIGHTEEN_DECIMALS as WAD, ZERO_ADDRESS

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "legacy_pool"
PROVENANCE = json.loads((FIXTURE_ROOT / "provenance.json").read_text())


def storage_write(contract, module, name, keys, value):
    """Synthetic boundary state, anchored to the compiled layout, not eval()."""
    layout = contract.compiler_data.storage_layout["storage_layout"]
    if module:
        layout = layout[module]
    slot = layout[name]["slot"]
    for key in keys:
        if hasattr(key, "address"):
            key = key.address
        key = int(key, 16) if isinstance(key, str) else key
        slot = int.from_bytes(keccak(slot.to_bytes(32, "big") + key.to_bytes(32, "big")), "big")
    if hasattr(value, "address"):
        value = value.address
    if isinstance(value, str):
        value = int(value, 16)
    boa.env.set_storage(contract.address, slot, value)


def call_tree(computation):
    yield computation
    for child in computation.children:
        yield from call_tree(child)


def calls_to(computation, address, signature):
    selector = keccak(text=signature)[:4]
    target = bytes.fromhex(str(address).removeprefix("0x"))
    return [c for c in call_tree(computation)
            if c.msg.code_address == target and bytes(c.msg.data)[:4] == selector]


@pytest.fixture
def base_chain():
    previous = boa.env.evm.patch.chain_id
    boa.env.evm.patch.chain_id = 8453
    try:
        yield
    finally:
        boa.env.evm.patch.chain_id = previous


@contextmanager
def legacy_search_path():
    """Boa 0.2.7 has no public getter for its raw override.

    get_search_paths() includes sys.path and is not the setter's inverse. Keep
    this private read contained and restore the identical object, including None.
    """
    assert version("titanoboa") == "0.2.7"
    previous = boa.interpret._search_path
    try:
        boa.interpret.set_search_path([str(FIXTURE_ROOT.resolve())])
        yield
    finally:
        boa.interpret.set_search_path(previous)


def _legacy_deployer(record):
    for path, expected in PROVENANCE["sources"].items():
        assert hashlib.sha256((FIXTURE_ROOT / path).read_bytes()).hexdigest() == expected
    with legacy_search_path():
        deployer = boa.load_partial(str(FIXTURE_ROOT / record["source_file"]))
    runtime = deployer.compiler_data.bytecode_runtime
    assert len(runtime) == record["compiled_runtime_bytes"]
    assert hashlib.sha256(runtime).hexdigest() == record["compiled_runtime_sha256"]
    return deployer


def _deploy_legacy_vault(deployer, hq, record):
    vault = deployer.deploy(hq)
    code = boa.env.get_code(vault.address)
    assert code[-32:] == int(hq.address, 16).to_bytes(32, "big")
    canonical = code[:-32] + bytes.fromhex(record["immutable_word"])
    assert hashlib.sha256(canonical).hexdigest() == record["deployed_sha256"]
    assert len(code) == record["deployed_bytes"]
    return vault


@pytest.fixture(scope="session")
def legacy_pool_deployer():
    return _legacy_deployer(PROVENANCE["pool"])


@pytest.fixture(scope="session")
def legacy_ripe_gov_deployer():
    return _legacy_deployer(PROVENANCE["ripe_gov"])


@pytest.fixture
def legacy_pool(base_chain, legacy_pool_deployer, ripe_hq):
    return _deploy_legacy_vault(legacy_pool_deployer, ripe_hq, PROVENANCE["pool"])


@pytest.fixture
def legacy_ripe_gov(base_chain, legacy_ripe_gov_deployer, ripe_hq):
    return _deploy_legacy_vault(legacy_ripe_gov_deployer, ripe_hq, PROVENANCE["ripe_gov"])


@pytest.fixture
def legacy_env(
    legacy_pool, legacy_ripe_gov, ripe_hq, governance, simple_erc20_vault,
    rebase_erc20_vault, mission_control, switchboard_alpha, switchboard_charlie,
    teller, auction_house, deleverage, credit_engine, ledger, lootbox,
    green_token, savings_green, ripe_token, price_desk, mock_price_source, endaoment_funds,
    alpha_token, alpha_token_whale, bob, alice, sally, whale,
    setGeneralConfig, setGeneralDebtConfig, setAssetConfig, createDebtTerms,
    performDeposit,
):
    book = boa.load("contracts/registries/VaultBook.vy", ripe_hq, ZERO_ADDRESS, 1, 1000, legacy_pool)
    for i, vault in enumerate((legacy_pool, legacy_ripe_gov, simple_erc20_vault, rebase_erc20_vault), 1):
        book.startAddNewAddressToRegistry(vault, f"local vault {i}", sender=governance.address)
        assert book.confirmNewAddressToRegistry(vault, sender=governance.address) == i
    book.setRegistryTimeLockAfterSetup(sender=governance.address)
    ripe_hq.startAddressUpdateToRegistry(8, book, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(8, sender=governance.address)
    assert mission_control.isStabVaultId(1)

    lp = boa.load("contracts/mock/MockErc20.vy", governance, "Legacy LP", "LLP", 18, 10**9)
    price_desk.syncTokenScale(lp, sender=governance.address)
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    zero_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    for token in (lp, savings_green):
        setAssetConfig(token, _vaultIds=[1], _debtTerms=zero_terms,
                       _shouldTransferToEndaoment=token == lp,
                       _shouldBurnAsPayment=token == savings_green,
                       _shouldSwapInStabPools=False, _shouldAuctionInstantly=False)
        mock_price_source.setPrice(token, WAD)
    setAssetConfig(alpha_token, _vaultIds=[3],
                   _debtTerms=createDebtTerms(50_00, 60_00, 80_00, 0, 0, 0))
    mock_price_source.setPrice(alpha_token, WAD)
    mock_price_source.setPrice(green_token, WAD)
    mission_control.setPriorityStabVaults([(1, lp), (1, savings_green)], sender=switchboard_alpha.address)
    mission_control.setPriorityLiqAssetVaults([], sender=switchboard_alpha.address)
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)
    deleverage.setMinDeleverageBps(0, sender=switchboard_alpha.address)
    deleverage.setDeleverageBuffer(0, sender=switchboard_alpha.address)
    deleverage.setDeleverageCooldown(0, sender=switchboard_alpha.address)

    e = SimpleNamespace(pool=legacy_pool, book=book, hq=ripe_hq, gov=governance,
        mc=mission_control, alpha=switchboard_alpha, charlie=switchboard_charlie,
        teller=teller, ah=auction_house, dl=deleverage, ce=credit_engine,
        ledger=ledger, lootbox=lootbox, green=green_token, sg=savings_green,
        ripe=ripe_token, ripe_gov=legacy_ripe_gov,
        pd=price_desk, prices=mock_price_source, funds=endaoment_funds, lp=lp,
        collateral=alpha_token, ordinary=simple_erc20_vault,
        bob=bob, alice=alice, sally=sally, whale=whale,
        configure=setAssetConfig, terms=createDebtTerms)

    def deposit(user, amount, token=None):
        token = lp if token is None else token
        if token == savings_green:
            green_token.mint(user, amount, sender=auction_house.address)
            green_token.approve(savings_green, amount, sender=user)
            amount = savings_green.deposit(amount, user, sender=user)
        else:
            token.mint(user, amount, sender=governance.address)
        token.approve(teller, amount, sender=user)
        assert teller.deposit(token, amount, user, legacy_pool, sender=user) == amount
        return amount

    def borrower(user, debt=300 * WAD, collateral=1000 * WAD):
        performDeposit(user, collateral, alpha_token, alpha_token_whale, simple_erc20_vault)
        teller.borrow(debt, user, False, sender=user)

    def token(name="Claim", decimals=18):
        asset = boa.load("contracts/mock/MockErc20.vy", governance, name, name, decimals, 10**9)
        price_desk.syncTokenScale(asset, sender=governance.address)
        return asset

    def claim(asset, amount, cohort=None, paid=1):
        cohort = lp if cohort is None else cohort
        sender = auction_house.address if asset == green_token else governance.address
        asset.mint(legacy_pool, amount, sender=sender)
        assert legacy_pool.swapForLiquidatedCollateral(
            cohort, paid, asset, amount, whale, green_token, savings_green,
            sender=auction_house.address) == paid

    def ready(cohort=None, incoming=None):
        return book.canAcceptLiquidationAsset(legacy_pool, lp if cohort is None else cohort,
                                              alpha_token if incoming is None else incoming)

    def nav(user=None, index=1, is_stab=True):
        return book.getDeleverageTraversalAsset(bob if user is None else user, legacy_pool, index, is_stab)

    e.deposit, e.borrower, e.token, e.claim, e.ready, e.nav = deposit, borrower, token, claim, ready, nav
    return e
