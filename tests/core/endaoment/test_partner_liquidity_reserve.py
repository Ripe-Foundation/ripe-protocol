from pathlib import Path
from types import SimpleNamespace

import boa
import pytest
import vyper.ast as vy_ast
from vyper.compiler.output import build_abi_output

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


LEGO_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Mintable:
    def mint(_to: address, _amount: uint256): nonpayable

LP_TOKEN: immutable(address)

returnedLpToken: public(address)
actualLpAmount: public(uint256)
reportedLpAmount: public(uint256)
lastRecipient: public(address)
deliverLpByTransfer: public(bool)
fillBps: public(uint256)

@deploy
def __init__(_lpToken: address):
    LP_TOKEN = _lpToken
    self.returnedLpToken = _lpToken
    self.actualLpAmount = 2
    self.reportedLpAmount = 2
    self.fillBps = 10_000

@external
def configure(_returnedLpToken: address, _actualLpAmount: uint256, _reportedLpAmount: uint256):
    self.returnedLpToken = _returnedLpToken
    self.actualLpAmount = _actualLpAmount
    self.reportedLpAmount = _reportedLpAmount

@external
def setDeliverLpByTransfer(_shouldTransfer: bool):
    self.deliverLpByTransfer = _shouldTransfer

@external
def configureFill(_fillBps: uint256):
    assert _fillBps <= 10_000
    self.fillBps = _fillBps

@view
@external
def getAddr(_id: uint256) -> address:
    return self

@view
@external
def isValidAddr(_addr: address) -> bool:
    return True

@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _recipient: address,
) -> (address, uint256, uint256, uint256, uint256):
    requestedA: uint256 = _amountA * self.fillBps // 10_000
    requestedB: uint256 = _amountB * self.fillBps // 10_000
    balanceABefore: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    balanceBBefore: uint256 = staticcall IERC20(_tokenB).balanceOf(self)
    assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, requestedA)
    assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, requestedB)
    addedA: uint256 = staticcall IERC20(_tokenA).balanceOf(self) - balanceABefore
    addedB: uint256 = staticcall IERC20(_tokenB).balanceOf(self) - balanceBBefore
    assert self.reportedLpAmount >= _minLpAmount  # dev: insufficient lp amount

    self.lastRecipient = _recipient
    if self.actualLpAmount != 0:
        if self.deliverLpByTransfer:
            assert extcall IERC20(LP_TOKEN).transfer(_recipient, self.actualLpAmount)
        else:
            extcall Mintable(LP_TOKEN).mint(_recipient, self.actualLpAmount)

    return self.returnedLpToken, self.reportedLpAmount, addedA, addedB, 0
"""


# Minimal executable model of the deployed Base Underscore Curve Lego's
# contribution accounting at 0x4e0C4B96FAdc84D41144C1aE868aA1411c1d0743.
# Its manifest-embedded Curve.vy source SHA-256 is
# aaadabed405acd96ce34c186a570b5684f8b015d7e83938412c75d05ffa701c9.
# The load-bearing behavior is preserved: amounts are selected before the
# Lego transferFrom, only balance above the pre-call inventory is refunded,
# and the remaining gross amount is reported without measuring venue receipt.
GROSS_REPORTING_CURVE_LEGO_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Venue:
    def addLiquidity(_tokenA: address, _tokenB: address, _amountA: uint256, _amountB: uint256, _recipient: address) -> uint256: nonpayable

LP_TOKEN: immutable(address)

lastReportedA: public(uint256)
lastReportedB: public(uint256)

@deploy
def __init__(_lpToken: address):
    LP_TOKEN = _lpToken

@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _recipient: address,
) -> (address, uint256, uint256, uint256, uint256):
    preBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    preBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)

    liqAmountA: uint256 = min(_amountA, staticcall IERC20(_tokenA).balanceOf(msg.sender))
    liqAmountB: uint256 = min(_amountB, staticcall IERC20(_tokenB).balanceOf(msg.sender))
    if liqAmountA != 0:
        assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, liqAmountA)
        assert extcall IERC20(_tokenA).approve(_pool, liqAmountA)
    if liqAmountB != 0:
        assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, liqAmountB)
        assert extcall IERC20(_tokenB).approve(_pool, liqAmountB)

    lpAmount: uint256 = extcall Venue(_pool).addLiquidity(_tokenA, _tokenB, liqAmountA, liqAmountB, _recipient)
    assert lpAmount >= _minLpAmount

    if liqAmountA != 0:
        assert extcall IERC20(_tokenA).approve(_pool, 0)
        currentBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
        if currentBalanceA > preBalanceA:
            refundA: uint256 = currentBalanceA - preBalanceA
            assert extcall IERC20(_tokenA).transfer(msg.sender, refundA)
            liqAmountA -= refundA
    if liqAmountB != 0:
        assert extcall IERC20(_tokenB).approve(_pool, 0)
        currentBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)
        if currentBalanceB > preBalanceB:
            refundB: uint256 = currentBalanceB - preBalanceB
            assert extcall IERC20(_tokenB).transfer(msg.sender, refundB)
            liqAmountB -= refundB

    self.lastReportedA = liqAmountA
    self.lastReportedB = liqAmountB
    return LP_TOKEN, lpAmount, liqAmountA, liqAmountB, 0
"""


PARTIAL_FILL_VENUE_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Mintable:
    def mint(_to: address, _amount: uint256): nonpayable

LP_TOKEN: immutable(address)
fillBps: public(uint256)

@deploy
def __init__(_lpToken: address):
    LP_TOKEN = _lpToken
    self.fillBps = 10_000

@external
def setFillBps(_fillBps: uint256):
    assert _fillBps <= 10_000
    self.fillBps = _fillBps

@external
def addLiquidity(_tokenA: address, _tokenB: address, _amountA: uint256, _amountB: uint256, _recipient: address) -> uint256:
    amountA: uint256 = _amountA * self.fillBps // 10_000
    amountB: uint256 = _amountB * self.fillBps // 10_000
    if amountA != 0:
        assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, amountA)
    if amountB != 0:
        assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, amountB)
    extcall Mintable(LP_TOKEN).mint(_recipient, 2)
    return 2
"""


CONTROLLED_DELTA_TOKEN_SOURCE = """
# @version 0.4.3

name: public(constant(String[32])) = "Controlled Delta"
symbol: public(constant(String[8])) = "DELTA"
decimals: public(constant(uint8)) = 6

TARGET: immutable(address)
MODE: immutable(uint256)
DELTA: immutable(uint256)

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
totalSupply: public(uint256)

@deploy
def __init__(_target: address, _mode: uint256, _delta: uint256):
    TARGET = _target
    MODE = _mode
    DELTA = _delta

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount
    self.totalSupply += _amount

@view
@external
def balanceOf(_owner: address) -> uint256:
    return self.balances[_owner]

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _move(_from: address, _to: address, _amount: uint256):
    self.balances[_from] -= _amount
    if _to != TARGET or MODE == 0:
        self.balances[_to] += _amount
    elif MODE == 1:  # controlled underdelivery
        self.balances[_to] += _amount - DELTA
    elif MODE == 2:  # success with zero delivery
        pass
    elif MODE == 3:  # malicious recipient-balance decrease
        self.balances[_to] -= DELTA
    else:  # controlled overdelivery
        self.balances[_to] += _amount + DELTA

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self._move(msg.sender, _to, _amount)
    return True

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    if msg.sender != _from:
        self.allowances[_from][msg.sender] -= _amount
    self._move(_from, _to, _amount)
    return True
"""


REENTRANT_SWITCHBOARD_TOKEN_SOURCE = """
# @version 0.4.3

decimals: public(constant(uint8)) = 6

interface Endaoment:
    def mintPartnerLiquidity(_partner: address, _asset: address, _amount: uint256) -> uint256: nonpayable

TARGET: immutable(address)
CALLBACK_PARTNER: immutable(address)
CALLBACK_AMOUNT: immutable(uint256)

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
entered: bool

@deploy
def __init__(_target: address, _callbackPartner: address, _callbackAmount: uint256):
    TARGET = _target
    CALLBACK_PARTNER = _callbackPartner
    CALLBACK_AMOUNT = _callbackAmount

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@view
@external
def balanceOf(_owner: address) -> uint256:
    return self.balances[_owner]

@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self.balances[msg.sender] -= _amount
    self.balances[_to] += _amount
    return True

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    if msg.sender != _from:
        self.allowances[_from][msg.sender] -= _amount
    if not self.entered:
        self.entered = True
        extcall Endaoment(TARGET).mintPartnerLiquidity(CALLBACK_PARTNER, self, CALLBACK_AMOUNT)
    self.balances[_from] -= _amount
    self.balances[_to] += _amount
    return True
"""


DUAL_ROLE_LEGO_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Endaoment:
    def repayPoolDebt(_pool: address, _amount: uint256) -> bool: nonpayable
    def transferFundsToGov(_asset: address, _amount: uint256) -> (uint256, uint256): nonpayable

interface Mintable:
    def mint(_to: address, _amount: uint256): nonpayable

TARGET: immutable(address)
LP_TOKEN: immutable(address)
VENUE: immutable(address)
DEBT_POOL: immutable(address)
DIVERT_AMOUNT: immutable(uint256)
MODE: immutable(uint256)

@deploy
def __init__(
    _target: address,
    _lpToken: address,
    _venue: address,
    _debtPool: address,
    _divertAmount: uint256,
    _mode: uint256,
):
    TARGET = _target
    LP_TOKEN = _lpToken
    VENUE = _venue
    DEBT_POOL = _debtPool
    DIVERT_AMOUNT = _divertAmount
    MODE = _mode

@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _recipient: address,
) -> (address, uint256, uint256, uint256, uint256):
    assert _amountB > DIVERT_AMOUNT
    assert extcall IERC20(_tokenA).transferFrom(msg.sender, VENUE, _amountA)
    assert extcall IERC20(_tokenB).transferFrom(msg.sender, VENUE, _amountB - DIVERT_AMOUNT)
    if MODE == 1:
        assert extcall Endaoment(TARGET).repayPoolDebt(DEBT_POOL, DIVERT_AMOUNT)
    else:
        moved: uint256 = 0
        value: uint256 = 0
        moved, value = extcall Endaoment(TARGET).transferFundsToGov(_tokenB, DIVERT_AMOUNT)
        assert moved == DIVERT_AMOUNT
    extcall Mintable(LP_TOKEN).mint(_recipient, 2)
    return LP_TOKEN, 2, _amountA, _amountB, 0
"""


ONE_ASSET = 10**6
ONE_GREEN = EIGHTEEN_DECIMALS
LEGO_ID = 1
ROOT = Path(__file__).resolve().parents[3]


def _endaoment_without_lock(function_name):
    source = (ROOT / "contracts/core/Endaoment.vy").read_text()
    marker = f"@nonreentrant\n@external\ndef {function_name}("
    replacement = f"@external\ndef {function_name}("
    assert source.count(marker) == 1
    return source.replace(marker, replacement, 1)


def _install_endaoment_lock_mutant(ctx, function_name):
    mutant = boa.loads(
        _endaoment_without_lock(function_name),
        ctx.endaoment.getRipeHq(),
        ctx.endaoment.WETH(),
        ctx.endaoment.ETH(),
        name=f"endaoment_without_{function_name}_lock",
    )
    boa.env.set_code(ctx.endaoment.address, boa.env.get_code(mutant.address))


def test_endaoment_external_mutation_surface_uses_one_reentrancy_lock():
    source_path = ROOT / "contracts/core/Endaoment.vy"
    module = vy_ast.parse_to_ast(source_path.read_text())
    checked = set()
    for function in module.get_descendants(vy_ast.nodes.FunctionDef):
        decorators = {
            getattr(decorator, "id", "") for decorator in function.decorator_list
        }
        if "external" not in decorators or {"view", "pure"} & decorators:
            continue
        if function.name == "__default__":
            # The receive-only fallback has no state mutation or external call.
            continue
        checked.add(function.name)
        assert "nonreentrant" in decorators, function.name

    abi = build_abi_output(boa.load_partial(source_path).compiler_data)
    abi_mutators = {
        item["name"]
        for item in abi
        if item.get("type") == "function"
        and item.get("stateMutability") in {"nonpayable", "payable"}
    }
    # This catches state-changing functions introduced indirectly through a
    # module export as well as ordinary functions declared in this source.
    assert abi_mutators == checked
    assert {
        "pause",
        "recoverFunds",
        "recoverFundsMany",
        "transferFundsToGov",
        "transferFundsToVault",
        "transferFundsToEndaomentPSM",
        "repayPoolDebt",
        "mintPartnerLiquidity",
        "addPartnerLiquidity",
        "stabilizeGreenRefPool",
    } <= checked


@pytest.fixture
def partner_liquidity_env(
    endaoment,
    endaoment_funds,
    mission_control,
    switchboard_alpha,
    switchboard,
    switchboard_delta,
    switchboard_echo,
    charlie_token,
    green_token,
    mock_price_source,
    ledger,
    governance,
    mock_registry,
    ripe_hq_deploy,
):
    lp_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "Partner LP",
        "PLP",
        18,
        0,
    )
    wrong_lp_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "Wrong LP",
        "WLP",
        18,
        0,
    )
    lego = boa.loads(LEGO_SOURCE, lp_token.address)
    lp_token.setMinter(lego.address, True, sender=governance.address)

    # Use distinct registry, Lego book, and admitted Lego layers without
    # changing the intentionally empty Robinhood production default.
    lego_book = boa.load(
        "contracts/mock/MockRegistry.vy",
        ripe_hq_deploy,
        mock_registry.registryChangeTimeLock(),
        mock_registry.minRegistryTimeLock(),
        mock_registry.maxRegistryTimeLock(),
        name="partner_liquidity_lego_book",
    )
    lego_book.startAddNewAddressToRegistry(
        lego.address,
        "Partner liquidity Lego",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=lego_book.registryChangeTimeLock())
    assert lego_book.confirmNewAddressToRegistry(
        lego.address,
        sender=governance.address,
    ) == LEGO_ID

    # The top-level Underscore registry resolves the Lego book at registry ID 3.
    for target, description in (
        (lp_token.address, "Test registry placeholder one"),
        (wrong_lp_token.address, "Test registry placeholder two"),
        (lego_book.address, "Lego book"),
    ):
        mock_registry.startAddNewAddressToRegistry(
            target,
            description,
            sender=governance.address,
        )
    boa.env.time_travel(blocks=mock_registry.registryChangeTimeLock())
    assert mock_registry.confirmNewAddressToRegistry(
        lp_token.address,
        sender=governance.address,
    ) == 1
    assert mock_registry.confirmNewAddressToRegistry(
        wrong_lp_token.address,
        sender=governance.address,
    ) == 2
    assert mock_registry.confirmNewAddressToRegistry(
        lego_book.address,
        sender=governance.address,
    ) == 3
    assert mock_registry.getAddr(3) == lego_book.address
    assert lego_book.getAddr(LEGO_ID) == lego.address
    assert lego_book.isValidAddr(lego.address)

    mission_control.setUnderscoreRegistry(
        mock_registry.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(charlie_token.address, ONE_GREEN)

    return SimpleNamespace(
        endaoment=endaoment,
        endaoment_funds=endaoment_funds,
        switchboard_delta=switchboard_delta,
        switchboard=switchboard,
        switchboard_echo=switchboard_echo,
        asset=charlie_token,
        green=green_token,
        lp=lp_token,
        wrong_lp=wrong_lp_token,
        lego=lego,
        lego_book=lego_book,
        ledger=ledger,
        governance=governance,
        price_source=mock_price_source,
    )


def _fund_partner(ctx, partner, amount=ONE_ASSET):
    ctx.asset.mint(partner, amount, sender=ctx.governance.address)
    ctx.asset.approve(ctx.endaoment.address, amount, sender=partner)


def _add_partner_liquidity(ctx, partner, amount=ONE_ASSET):
    return ctx.endaoment.addPartnerLiquidity(
        LEGO_ID,
        ctx.lp.address,
        partner,
        ctx.asset.address,
        amount,
        0,
        ctx.lp.address,
        sender=ctx.switchboard_delta.address,
    )


def _controlled_delta_token(ctx, mode, delta):
    token = boa.loads(
        CONTROLLED_DELTA_TOKEN_SOURCE,
        ctx.endaoment_funds.address,
        mode,
        delta,
        name=f"controlled_delta_mode_{mode}",
    )
    ctx.price_source.setPrice(token.address, EIGHTEEN_DECIMALS)
    return token


def _use_gross_reporting_curve_lego(ctx):
    venue = boa.loads(PARTIAL_FILL_VENUE_SOURCE, ctx.lp.address)
    lego = boa.loads(GROSS_REPORTING_CURVE_LEGO_SOURCE, ctx.lp.address)
    ctx.lp.setMinter(venue.address, True, sender=ctx.governance.address)
    ctx.lego_book.startAddressUpdateToRegistry(
        LEGO_ID,
        lego.address,
        sender=ctx.governance.address,
    )
    boa.env.time_travel(blocks=ctx.lego_book.registryChangeTimeLock())
    assert ctx.lego_book.confirmAddressUpdateToRegistry(
        LEGO_ID,
        sender=ctx.governance.address,
    )
    return lego, venue


def _install_dual_role_lego(ctx, venue, debt_pool, divert_amount, mode):
    lego = boa.loads(
        DUAL_ROLE_LEGO_SOURCE,
        ctx.endaoment.address,
        ctx.lp.address,
        venue,
        debt_pool,
        divert_amount,
        mode,
        name=f"dual_role_lego_mode_{mode}",
    )
    ctx.lp.setMinter(lego.address, True, sender=ctx.governance.address)
    ctx.lego_book.startAddressUpdateToRegistry(
        LEGO_ID,
        lego.address,
        sender=ctx.governance.address,
    )
    ctx.switchboard.startAddNewAddressToRegistry(
        lego.address,
        "Dual-role callback Lego",
        sender=ctx.governance.address,
    )
    boa.env.time_travel(
        blocks=max(
            ctx.lego_book.registryChangeTimeLock(),
            ctx.switchboard.registryChangeTimeLock(),
        )
    )
    assert ctx.lego_book.confirmAddressUpdateToRegistry(
        LEGO_ID,
        sender=ctx.governance.address,
    )
    assert ctx.switchboard.confirmNewAddressToRegistry(
        lego.address,
        sender=ctx.governance.address,
    ) != 0
    assert ctx.switchboard.isSwitchboardAddr(lego.address)
    return lego


def test_endaoment_locked_pause_wrapper_preserves_department_behavior(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    assert not ctx.endaoment.isPaused()

    with boa.reverts("no perms"):
        ctx.endaoment.pause(True, sender=alice)
    assert not ctx.endaoment.isPaused()

    assert ctx.endaoment.pause(True, sender=ctx.switchboard_delta.address) is None
    log = filter_logs(ctx.endaoment, "DepartmentPauseModified")[0]
    assert log.isPaused
    assert ctx.endaoment.isPaused()

    with boa.reverts("no change"):
        ctx.endaoment.pause(True, sender=ctx.switchboard_delta.address)
    assert ctx.endaoment.isPaused()

    assert ctx.endaoment.pause(False, sender=ctx.switchboard_delta.address) is None
    assert not ctx.endaoment.isPaused()


def test_endaoment_locked_recovery_wrappers_preserve_transfers_and_events(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    asset_amount = 17 * ONE_ASSET
    lp_amount = 23
    ctx.asset.mint(
        ctx.endaoment.address,
        asset_amount,
        sender=ctx.governance.address,
    )

    assert (
        ctx.endaoment.recoverFunds(
            alice,
            ctx.asset.address,
            sender=ctx.switchboard_delta.address,
        )
        is None
    )
    assert ctx.asset.balanceOf(ctx.endaoment.address) == 0
    assert ctx.asset.balanceOf(alice) == asset_amount
    log = filter_logs(ctx.endaoment, "DepartmentFundsRecovered")[0]
    assert log.asset == ctx.asset.address
    assert log.recipient == alice
    assert log.balance == asset_amount

    ctx.asset.mint(
        ctx.endaoment.address,
        asset_amount,
        sender=ctx.governance.address,
    )
    ctx.lp.mint(
        ctx.endaoment.address,
        lp_amount,
        sender=ctx.governance.address,
    )
    assert (
        ctx.endaoment.recoverFundsMany(
            alice,
            [ctx.asset.address, ctx.lp.address],
            sender=ctx.switchboard_delta.address,
        )
        is None
    )
    assert ctx.asset.balanceOf(ctx.endaoment.address) == 0
    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
    assert ctx.asset.balanceOf(alice) == 2 * asset_amount
    assert ctx.lp.balanceOf(alice) == lp_amount
    logs = filter_logs(ctx.endaoment, "DepartmentFundsRecovered")
    assert [(log.asset, log.recipient, log.balance) for log in logs] == [
        (ctx.asset.address, alice, asset_amount),
        (ctx.lp.address, alice, lp_amount),
    ]


def test_endaoment_locked_recovery_wrappers_preserve_revert_behavior(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    amount = 11 * ONE_ASSET
    ctx.asset.mint(ctx.endaoment.address, amount, sender=ctx.governance.address)

    with boa.reverts("no perms"):
        ctx.endaoment.recoverFunds(
            alice,
            ctx.asset.address,
            sender=alice,
        )
    with boa.reverts("invalid recipient or asset"):
        ctx.endaoment.recoverFunds(
            ZERO_ADDRESS,
            ctx.asset.address,
            sender=ctx.switchboard_delta.address,
        )
    with boa.reverts("invalid recipient or asset"):
        ctx.endaoment.recoverFunds(
            alice,
            ZERO_ADDRESS,
            sender=ctx.switchboard_delta.address,
        )
    with boa.reverts("nothing to recover"):
        ctx.endaoment.recoverFunds(
            alice,
            ctx.wrong_lp.address,
            sender=ctx.switchboard_delta.address,
        )

    assert (
        ctx.endaoment.recoverFundsMany(
            alice,
            [],
            sender=ctx.switchboard_delta.address,
        )
        is None
    )
    assert ctx.asset.balanceOf(ctx.endaoment.address) == amount


def test_sc18_mint_partner_liquidity_values_actual_received_amount(
    partner_liquidity_env,
    alice,
    whale,
):
    ctx = partner_liquidity_env
    nominal_amount = 100 * EIGHTEEN_DECIMALS
    fee_bps = 1_000
    expected_received = nominal_amount * (10_000 - fee_bps) // 10_000
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        ctx.governance.address,
        0,
        name="sc18_fee_on_transfer_asset",
    )
    fee_token.transfer(alice, nominal_amount, sender=ctx.governance.address)
    fee_token.setTransferFee(fee_bps, sender=ctx.governance.address)
    fee_token.approve(ctx.endaoment.address, nominal_amount, sender=alice)
    ctx.price_source.setPrice(fee_token.address, EIGHTEEN_DECIMALS)
    reserve = 30 * EIGHTEEN_DECIMALS
    ctx.green.transfer(ctx.endaoment_funds.address, reserve, sender=whale)

    partner_before = fee_token.balanceOf(alice)
    funds_before = fee_token.balanceOf(ctx.endaoment_funds.address)
    supply_before = ctx.green.totalSupply()

    green_minted = ctx.endaoment.mintPartnerLiquidity(
        alice,
        fee_token.address,
        nominal_amount,
        sender=ctx.switchboard_delta.address,
    )

    received = fee_token.balanceOf(ctx.endaoment_funds.address) - funds_before
    log = filter_logs(ctx.endaoment, "PartnerLiquidityMinted")[0]
    assert partner_before - fee_token.balanceOf(alice) == nominal_amount
    assert received == expected_received < nominal_amount
    expected_minted = received - reserve
    assert green_minted == expected_minted
    assert ctx.green.totalSupply() - supply_before == expected_minted
    assert log.partnerAmount == received
    assert log.usdValue == received
    assert log.greenMinted == expected_minted


@pytest.mark.parametrize(
    "reserve",
    [0, ONE_GREEN // 2, ONE_GREEN, ONE_GREEN * 2],
    ids=["none", "partial", "equal", "greater"],
)
def test_sc18_exact_transfer_preserves_green_reserve_shortfall(
    partner_liquidity_env,
    alice,
    whale,
    reserve,
):
    ctx = partner_liquidity_env
    if reserve:
        ctx.green.transfer(ctx.endaoment_funds.address, reserve, sender=whale)
    _fund_partner(ctx, alice)
    supply_before = ctx.green.totalSupply()

    minted = ctx.endaoment.mintPartnerLiquidity(
        alice,
        ctx.asset.address,
        ONE_ASSET,
        sender=ctx.switchboard_delta.address,
    )

    expected = max(ONE_GREEN - reserve, 0)
    log = filter_logs(ctx.endaoment, "PartnerLiquidityMinted")[0]
    assert minted == expected
    assert ctx.green.totalSupply() - supply_before == expected
    assert log.partnerAmount == ONE_ASSET
    assert log.usdValue == ONE_GREEN
    assert log.greenMinted == expected


@pytest.mark.parametrize("mode", [2, 3], ids=["zero-delivery", "recipient-decrease"])
def test_sc18_nonpositive_recipient_delta_reverts_atomically(
    partner_liquidity_env,
    alice,
    mode,
):
    ctx = partner_liquidity_env
    token = _controlled_delta_token(ctx, mode, 1)
    nominal = 100 * ONE_ASSET
    token.mint(alice, nominal)
    token.mint(ctx.endaoment_funds.address, 10)
    token.approve(ctx.endaoment.address, nominal, sender=alice)
    before = (
        token.balanceOf(alice),
        token.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
    )

    with boa.reverts("no asset received"):
        ctx.endaoment.mintPartnerLiquidity(
            alice,
            token.address,
            nominal,
            sender=ctx.switchboard_delta.address,
        )

    assert (
        token.balanceOf(alice),
        token.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
    ) == before


def test_sc18_positive_overdelivery_is_valued_consistently(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    bonus = 7 * ONE_ASSET
    nominal = 100 * ONE_ASSET
    token = _controlled_delta_token(ctx, 4, bonus)
    token.mint(alice, nominal)
    token.approve(ctx.endaoment.address, nominal, sender=alice)

    minted = ctx.endaoment.mintPartnerLiquidity(
        alice,
        token.address,
        nominal,
        sender=ctx.switchboard_delta.address,
    )

    actual = nominal + bonus
    expected_value = actual * 10**12
    log = filter_logs(ctx.endaoment, "PartnerLiquidityMinted")[0]
    assert token.balanceOf(ctx.endaoment_funds.address) == actual
    assert minted == expected_value
    assert log.partnerAmount == actual
    assert log.usdValue == expected_value
    assert log.greenMinted == expected_value


def test_sc18_dual_role_switchboard_token_cannot_reenter(
    partner_liquidity_env,
    alice,
    bob,
):
    ctx = partner_liquidity_env
    nested_amount = 25 * ONE_ASSET
    token = boa.loads(
        REENTRANT_SWITCHBOARD_TOKEN_SOURCE,
        ctx.endaoment.address,
        bob,
        nested_amount,
    )
    nominal = 100 * ONE_ASSET
    token.mint(alice, nominal)
    token.mint(bob, nested_amount)
    token.approve(ctx.endaoment.address, nominal, sender=alice)
    token.approve(ctx.endaoment.address, nested_amount, sender=bob)
    ctx.price_source.setPrice(token.address, EIGHTEEN_DECIMALS)

    ctx.switchboard.startAddNewAddressToRegistry(
        token.address,
        "Dual-role callback token",
        sender=ctx.governance.address,
    )
    boa.env.time_travel(blocks=ctx.switchboard.registryChangeTimeLock())
    ctx.switchboard.confirmNewAddressToRegistry(
        token.address,
        sender=ctx.governance.address,
    )
    assert ctx.switchboard.isSwitchboardAddr(token.address)

    before = (
        token.balanceOf(alice),
        token.balanceOf(bob),
        token.balanceOf(ctx.endaoment_funds.address),
        token.allowance(alice, ctx.endaoment.address),
        token.allowance(bob, ctx.endaoment.address),
        ctx.green.totalSupply(),
    )
    with boa.reverts():
        ctx.endaoment.mintPartnerLiquidity(
            alice,
            token.address,
            nominal,
            sender=ctx.switchboard_delta.address,
        )
    assert (
        token.balanceOf(alice),
        token.balanceOf(bob),
        token.balanceOf(ctx.endaoment_funds.address),
        token.allowance(alice, ctx.endaoment.address),
        token.allowance(bob, ctx.endaoment.address),
        ctx.green.totalSupply(),
    ) == before

    # Mutation evidence: with only this entrypoint's lock removed, every
    # prerequisite is valid and the nested mint completes. This proves the
    # protected revert above is caused by the shared reentrancy lock.
    with boa.env.anchor():
        _install_endaoment_lock_mutant(ctx, "mintPartnerLiquidity")
        minted = ctx.endaoment.mintPartnerLiquidity(
            alice,
            token.address,
            nominal,
            sender=ctx.switchboard_delta.address,
        )
        expected_value = nominal * 10**12
        assert minted == expected_value
        assert token.balanceOf(alice) == 0
        assert token.balanceOf(bob) == 0
        assert token.balanceOf(ctx.endaoment_funds.address) == (
            nominal + nested_amount
        )
        assert token.allowance(alice, ctx.endaoment.address) == 0
        assert token.allowance(bob, ctx.endaoment.address) == 0
        nested_value = nested_amount * 10**12
        assert ctx.green.totalSupply() == (
            before[-1] + expected_value + nested_value
        )


def _cross_entry_state(ctx, partner, venue, lego, debt_pool):
    return (
        ctx.asset.balanceOf(partner),
        ctx.asset.balanceOf(ctx.endaoment.address),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.asset.balanceOf(venue),
        ctx.asset.balanceOf(lego.address),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.green.balanceOf(venue),
        ctx.green.balanceOf(lego.address),
        ctx.green.balanceOf(ctx.governance.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
        ctx.ledger.greenPoolDebt(debt_pool),
        ctx.lp.balanceOf(partner),
        ctx.lp.balanceOf(ctx.endaoment.address),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
        ctx.lp.totalSupply(),
        ctx.asset.allowance(ctx.endaoment.address, lego.address),
        ctx.green.allowance(ctx.endaoment.address, lego.address),
    )


@pytest.mark.parametrize(
    ("destination", "mode"),
    (("repayPoolDebt", 1), ("transferFundsToGov", 2)),
    ids=("pool-debt", "governance-transfer"),
)
def test_sc18_dual_role_lego_cross_entry_reverts_atomically_and_is_mutation_sensitive(
    partner_liquidity_env,
    alice,
    destination,
    mode,
):
    ctx = partner_liquidity_env
    venue = boa.env.generate_address()
    debt_pool = ctx.wrong_lp.address
    partner_amount = 100 * ONE_ASSET
    green_amount = 100 * ONE_GREEN
    divert_amount = 25 * ONE_GREEN
    lego = _install_dual_role_lego(
        ctx,
        venue,
        debt_pool,
        divert_amount,
        mode,
    )
    _fund_partner(ctx, alice, partner_amount)

    # The debt route needs exactly the action's GREEN in custody. The
    # governance route needs one extra diverted tranche so its nested pull is
    # fully executable while the action's own remainder stays refundable.
    reserve = green_amount if mode == 1 else green_amount + divert_amount
    assert ctx.green.mint(
        ctx.endaoment_funds.address,
        reserve,
        sender=ctx.endaoment.address,
    )
    if mode == 1:
        ctx.ledger.updateGreenPoolDebt(
            debt_pool,
            divert_amount,
            True,
            sender=ctx.endaoment.address,
        )

    before = _cross_entry_state(ctx, alice, venue, lego, debt_pool)
    with boa.reverts():
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            partner_amount,
            0,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )
    assert ctx.endaoment._computation.is_error
    assert not ctx.endaoment.get_logs()
    assert _cross_entry_state(ctx, alice, venue, lego, debt_pool) == before

    # Remove only the nested destination's lock. The attack then completes,
    # proving that the protected revert above is not caused by an invalid Lego
    # setup, missing debt, insufficient custody, or an unusable allowance.
    with boa.env.anchor():
        _install_endaoment_lock_mutant(ctx, destination)
        result = ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            partner_amount,
            0,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )
        assert result == (2, partner_amount, green_amount)
        assert ctx.asset.balanceOf(venue) == partner_amount
        assert ctx.green.balanceOf(venue) == green_amount - divert_amount
        assert ctx.asset.balanceOf(lego.address) == 0
        assert ctx.green.balanceOf(lego.address) == 0
        assert ctx.lp.balanceOf(alice) == before[13] + 1
        assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == before[15] + 1
        assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
        assert ctx.asset.allowance(ctx.endaoment.address, lego.address) == 0
        assert ctx.green.allowance(ctx.endaoment.address, lego.address) == 0
        assert ctx.ledger.greenPoolDebt(ctx.lp.address) == before[11]
        if mode == 1:
            assert ctx.ledger.greenPoolDebt(debt_pool) == 0
            assert ctx.green.totalSupply() == before[10] - divert_amount
            assert ctx.green.balanceOf(ctx.governance.address) == before[9]
        else:
            assert ctx.ledger.greenPoolDebt(debt_pool) == before[12]
            assert ctx.green.totalSupply() == before[10]
            assert ctx.green.balanceOf(ctx.governance.address) == (
                before[9] + divert_amount
            )


def test_sc18_self_partner_uses_only_endaoment_controlled_balance(
    partner_liquidity_env,
):
    ctx = partner_liquidity_env
    controlled = ONE_ASSET
    ctx.asset.mint(ctx.endaoment.address, controlled, sender=ctx.governance.address)

    minted = ctx.endaoment.mintPartnerLiquidity(
        ctx.endaoment.address,
        ctx.asset.address,
        controlled * 2,
        sender=ctx.switchboard_delta.address,
    )

    log = filter_logs(ctx.endaoment, "PartnerLiquidityMinted")[0]
    assert minted == ONE_GREEN
    assert log.partnerAmount == controlled
    assert ctx.asset.balanceOf(ctx.endaoment.address) == controlled
    assert ctx.asset.balanceOf(ctx.endaoment_funds.address) == 0


def test_sc18_green_cannot_alias_partner_asset_custody(
    partner_liquidity_env,
    alice,
    whale,
):
    ctx = partner_liquidity_env
    ctx.green.transfer(alice, ONE_GREEN, sender=whale)
    ctx.green.approve(ctx.endaoment.address, ONE_GREEN, sender=alice)

    with boa.reverts("invalid partner asset"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.green.address,
            ONE_GREEN,
            0,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )


def test_sc18_direct_mint_rejects_green_for_external_partner_atomically(
    partner_liquidity_env,
    alice,
    whale,
):
    ctx = partner_liquidity_env
    ctx.green.transfer(alice, ONE_GREEN, sender=whale)
    ctx.green.approve(ctx.endaoment.address, ONE_GREEN, sender=alice)
    before = (
        ctx.green.balanceOf(alice),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.green.allowance(alice, ctx.endaoment.address),
        ctx.green.totalSupply(),
    )

    with boa.reverts("invalid partner asset"):
        ctx.endaoment.mintPartnerLiquidity(
            alice,
            ctx.green.address,
            ONE_GREEN,
            sender=ctx.switchboard_delta.address,
        )

    assert (
        ctx.green.balanceOf(alice),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.green.allowance(alice, ctx.endaoment.address),
        ctx.green.totalSupply(),
    ) == before


def test_sc18_direct_mint_rejects_green_for_endaoment_partner_atomically(
    partner_liquidity_env,
    whale,
):
    ctx = partner_liquidity_env
    ctx.green.transfer(ctx.endaoment.address, ONE_GREEN, sender=whale)
    before = (
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
    )

    with boa.reverts("invalid partner asset"):
        ctx.endaoment.mintPartnerLiquidity(
            ctx.endaoment.address,
            ctx.green.address,
            ONE_GREEN,
            sender=ctx.switchboard_delta.address,
        )

    assert (
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
    ) == before


def test_sc18_add_partner_liquidity_composes_with_received_delta(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    nominal = ONE_ASSET
    shortfall = ONE_ASSET // 5
    received = nominal - shortfall
    token = _controlled_delta_token(ctx, 1, shortfall)
    token.mint(alice, nominal)
    token.approve(ctx.endaoment.address, nominal, sender=alice)
    supply_before = ctx.green.totalSupply()

    lp_received, amount_a, amount_b = ctx.endaoment.addPartnerLiquidity(
        LEGO_ID,
        ctx.lp.address,
        alice,
        token.address,
        nominal,
        0,
        ctx.lp.address,
        sender=ctx.switchboard_delta.address,
    )

    expected_green = received * 10**12
    log = filter_logs(ctx.endaoment, "PartnerLiquidityAdded")[0]
    assert (lp_received, amount_a, amount_b) == (2, received, expected_green)
    assert ctx.green.totalSupply() - supply_before == expected_green
    assert ctx.ledger.greenPoolDebt(ctx.lp.address) == expected_green
    assert log.partnerAmount == received
    assert log.greenAmount == expected_green


def test_sc18_composed_fee_route_reverts_with_preexisting_inventory(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    nominal = 100 * EIGHTEEN_DECIMALS
    fee_bps = 1_000
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        ctx.governance.address,
        0,
        name="sc18_composed_fee_asset",
    )
    fee_token.transfer(alice, nominal, sender=ctx.governance.address)
    fee_token.transfer(
        ctx.endaoment.address,
        nominal,
        sender=ctx.governance.address,
    )
    fee_token.setTransferFee(fee_bps, sender=ctx.governance.address)
    fee_token.approve(ctx.endaoment.address, nominal, sender=alice)
    ctx.price_source.setPrice(fee_token.address, EIGHTEEN_DECIMALS)
    before = (
        fee_token.balanceOf(alice),
        fee_token.balanceOf(ctx.endaoment.address),
        fee_token.balanceOf(ctx.endaoment_funds.address),
        fee_token.balanceOf(ctx.lego.address),
        fee_token.balanceOf(ctx.governance.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
    )

    with boa.reverts("partner asset accounting"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            fee_token.address,
            nominal,
            0,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )

    assert (
        fee_token.balanceOf(alice),
        fee_token.balanceOf(ctx.endaoment.address),
        fee_token.balanceOf(ctx.endaoment_funds.address),
        fee_token.balanceOf(ctx.lego.address),
        fee_token.balanceOf(ctx.governance.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
    ) == before


def test_sc18_upstream_curve_gross_report_is_not_net_venue_receipt(
    partner_liquidity_env,
    alice,
):
    """Lock the counterexample that keeps RH Lego/asset configuration blocked."""
    ctx = partner_liquidity_env
    lego, venue = _use_gross_reporting_curve_lego(ctx)
    gross = 100 * ONE_ASSET
    downstream_fee = 10 * ONE_ASSET
    inventory = 25 * ONE_ASSET
    token = boa.loads(
        CONTROLLED_DELTA_TOKEN_SOURCE,
        venue.address,
        1,
        downstream_fee,
        name="sc18_venue_fee_asset",
    )
    token.mint(alice, gross)
    token.mint(lego.address, inventory)
    token.approve(ctx.endaoment.address, gross, sender=alice)
    ctx.price_source.setPrice(token.address, EIGHTEEN_DECIMALS)
    supply_before = ctx.green.totalSupply()

    result = ctx.endaoment.addPartnerLiquidity(
        LEGO_ID,
        venue.address,
        alice,
        token.address,
        gross,
        0,
        ctx.lp.address,
        sender=ctx.switchboard_delta.address,
    )

    green_contribution = gross * 10**12
    assert result == (2, gross, green_contribution)
    assert lego.lastReportedA() == gross
    assert token.balanceOf(venue.address) == gross - downstream_fee
    assert token.balanceOf(venue.address) < lego.lastReportedA()
    assert token.balanceOf(lego.address) == inventory
    assert token.balanceOf(ctx.endaoment_funds.address) == 0
    assert ctx.green.balanceOf(venue.address) == green_contribution
    assert ctx.green.totalSupply() - supply_before == green_contribution
    assert ctx.ledger.greenPoolDebt(venue.address) == green_contribution
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1


def test_sc18_upstream_curve_legitimate_partial_fill_refunds_and_accounts_net(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    lego, venue = _use_gross_reporting_curve_lego(ctx)
    gross = 100 * ONE_ASSET
    fill_bps = 6_000
    contributed_asset = gross * fill_bps // 10_000
    contributed_green = 100 * ONE_GREEN * fill_bps // 10_000
    inventory = 25 * ONE_ASSET
    venue.setFillBps(fill_bps)
    ctx.asset.mint(lego.address, inventory, sender=ctx.governance.address)
    _fund_partner(ctx, alice, gross)
    supply_before = ctx.green.totalSupply()

    result = ctx.endaoment.addPartnerLiquidity(
        LEGO_ID,
        venue.address,
        alice,
        ctx.asset.address,
        gross,
        0,
        ctx.lp.address,
        sender=ctx.switchboard_delta.address,
    )

    assert result == (2, contributed_asset, contributed_green)
    assert lego.lastReportedA() == contributed_asset
    assert lego.lastReportedB() == contributed_green
    assert ctx.asset.balanceOf(venue.address) == contributed_asset
    assert ctx.green.balanceOf(venue.address) == contributed_green
    assert ctx.asset.balanceOf(lego.address) == inventory
    assert ctx.asset.balanceOf(ctx.endaoment_funds.address) == (
        gross - contributed_asset
    )
    assert ctx.green.balanceOf(ctx.endaoment_funds.address) == 0
    assert ctx.green.totalSupply() - supply_before == contributed_green
    assert ctx.ledger.greenPoolDebt(venue.address) == contributed_green
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1


@pytest.mark.parametrize(
    "green_reserve",
    [0, 30 * ONE_GREEN],
    ids=["no-reserve", "reserve-first"],
)
def test_sc18_partial_fill_reconciles_contributions_debt_and_refunds(
    partner_liquidity_env,
    alice,
    whale,
    green_reserve,
):
    ctx = partner_liquidity_env
    nominal = 100 * ONE_ASSET
    fill_bps = 6_000
    expected_asset = nominal * fill_bps // 10_000
    expected_green = 100 * ONE_GREEN * fill_bps // 10_000
    expected_minted = expected_green - green_reserve
    expected_asset_refund = nominal - expected_asset
    ctx.lego.configureFill(fill_bps)
    if green_reserve != 0:
        ctx.green.transfer(
            ctx.endaoment_funds.address,
            green_reserve,
            sender=whale,
        )
    _fund_partner(ctx, alice, nominal)
    supply_before = ctx.green.totalSupply()

    result = _add_partner_liquidity(ctx, alice, nominal)

    log = filter_logs(ctx.endaoment, "PartnerLiquidityAdded")[0]
    assert result == (2, expected_asset, expected_green)
    assert ctx.asset.balanceOf(ctx.lego.address) == expected_asset
    assert ctx.asset.balanceOf(ctx.endaoment_funds.address) == expected_asset_refund
    assert ctx.asset.balanceOf(ctx.endaoment.address) == 0
    assert ctx.green.balanceOf(ctx.lego.address) == expected_green
    assert ctx.green.balanceOf(ctx.endaoment.address) == 0
    assert ctx.green.balanceOf(ctx.endaoment_funds.address) == 0
    assert ctx.green.totalSupply() - supply_before == expected_minted
    assert ctx.ledger.greenPoolDebt(ctx.lp.address) == expected_minted
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1
    assert log.partnerAmount == expected_asset
    assert log.greenAmount == expected_green
    assert log.lpBalance == 2


def test_partner_receives_only_current_action_share(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)

    lp_received, _, _ = _add_partner_liquidity(ctx, alice)

    # The read-only pre-fix audit proof executes this same 1,000-plus-two setup
    # against the base contract and observes 501 LP paid to the partner. This
    # fixed-contract regression asserts the corrected side of that comparison.
    assert lp_received == 2
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_001
    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
    assert filter_logs(ctx.endaoment, "PartnerLiquidityAdded")[0].lpBalance == 2


def test_sequential_partner_actions_do_not_redistribute_reserves(
    partner_liquidity_env,
    alice,
    bob,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)
    _fund_partner(ctx, bob)

    _add_partner_liquidity(ctx, alice)
    alice_after_first = ctx.lp.balanceOf(alice)
    _add_partner_liquidity(ctx, bob)

    assert alice_after_first == 1
    assert ctx.lp.balanceOf(alice) == alice_after_first
    assert ctx.lp.balanceOf(bob) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_002


def test_unsolicited_endaoment_lp_is_not_split_or_swept(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 73, sender=ctx.governance.address)
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 73
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_001


def test_incorrect_returned_lp_token_reverts(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.wrong_lp.address, 2, 2)
    _fund_partner(ctx, alice)

    with boa.reverts("unexpected lp token"):
        _add_partner_liquidity(ctx, alice)


@pytest.mark.parametrize(
    ("actual_lp", "reported_lp"),
    [(2, 3), (3, 2)],
    ids=["over-reported", "under-reported-external-lp"],
)
def test_reported_lp_amount_must_match_exact_external_call_delta(
    partner_liquidity_env,
    alice,
    actual_lp,
    reported_lp,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, actual_lp, reported_lp)
    _fund_partner(ctx, alice)

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)


def test_rebase_like_lp_balance_change_during_external_call_reverts(
    partner_liquidity_env,
    alice,
):
    """A balance increase beyond the Lego report cannot join this cohort."""
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 20, sender=ctx.governance.address)
    ctx.lego.configure(ctx.lp.address, 4, 2)
    _fund_partner(ctx, alice)

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 20


def test_fee_on_transfer_lp_short_receipt_reverts_atomically(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    fee_lp = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        ctx.governance.address,
        5_000,  # 50% makes a two-unit transfer deliver exactly one unit.
        name="partner_fee_lp",
    )
    fee_lego = boa.loads(LEGO_SOURCE, fee_lp.address)
    fee_lego.setDeliverLpByTransfer(True)
    fee_lp.transfer(fee_lego.address, 10, sender=ctx.governance.address)

    ctx.lego_book.startAddressUpdateToRegistry(
        LEGO_ID,
        fee_lego.address,
        sender=ctx.governance.address,
    )
    boa.env.time_travel(blocks=ctx.lego_book.registryChangeTimeLock())
    assert ctx.lego_book.confirmAddressUpdateToRegistry(
        LEGO_ID,
        sender=ctx.governance.address,
    )
    _fund_partner(ctx, alice)

    balances_before = (
        fee_lp.balanceOf(fee_lego.address),
        fee_lp.balanceOf(ctx.endaoment.address),
        fee_lp.balanceOf(ctx.endaoment_funds.address),
        ctx.asset.balanceOf(alice),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(fee_lp.address),
    )
    with boa.reverts("lp amount mismatch"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            fee_lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            0,
            fee_lp.address,
            sender=ctx.switchboard_delta.address,
        )
    balances_after = (
        fee_lp.balanceOf(fee_lego.address),
        fee_lp.balanceOf(ctx.endaoment.address),
        fee_lp.balanceOf(ctx.endaoment_funds.address),
        ctx.asset.balanceOf(alice),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(fee_lp.address),
    )
    assert balances_after == balances_before


def test_minimum_lp_failure_reverts_atomically(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    balances_before = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )

    with boa.reverts("insufficient lp amount"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            3,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )

    balances_after = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )
    assert balances_after == balances_before


def test_zero_reported_lp_amount_reverts_cleanly(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 0, 0)
    _fund_partner(ctx, alice)

    with boa.reverts("no liquidity added"):
        _add_partner_liquidity(ctx, alice)


def test_odd_lp_output_favors_endaoment_funds(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 3, 3)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2


def test_one_unit_lp_output_goes_entirely_to_endaoment_funds(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 1, 1)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(alice) == 0
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1


def test_endaoment_partner_returns_all_current_lp_to_funds(
    partner_liquidity_env,
):
    ctx = partner_liquidity_env
    ctx.asset.mint(
        ctx.endaoment.address,
        ONE_ASSET,
        sender=ctx.governance.address,
    )

    _add_partner_liquidity(ctx, ctx.endaoment.address)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2


def test_validation_failure_rolls_back_all_accounting(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 13, sender=ctx.governance.address)
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    ctx.lego.configure(ctx.lp.address, 3, 2)
    _fund_partner(ctx, alice)

    balances_before = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment.address),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment.address),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)

    balances_after = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment.address),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment.address),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )
    assert balances_after == balances_before


def test_successful_pool_debt_equals_green_minted_for_current_action(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    supply_before = ctx.green.totalSupply()
    debt_before = ctx.ledger.greenPoolDebt(ctx.lp.address)

    _add_partner_liquidity(ctx, alice)

    green_minted = ctx.green.totalSupply() - supply_before
    debt_added = ctx.ledger.greenPoolDebt(ctx.lp.address) - debt_before
    assert green_minted == ONE_GREEN
    assert debt_added == green_minted


def test_ordinary_add_liquidity_still_sends_lp_to_endaoment_funds(
    partner_liquidity_env,
    whale,
):
    ctx = partner_liquidity_env
    ctx.asset.mint(
        ctx.endaoment_funds.address,
        ONE_ASSET,
        sender=ctx.governance.address,
    )
    ctx.green.transfer(
        ctx.endaoment_funds.address,
        ONE_GREEN,
        sender=whale,
    )

    lp_received, _, _, _ = ctx.endaoment.addLiquidity(
        LEGO_ID,
        ctx.lp.address,
        ctx.asset.address,
        ctx.green.address,
        ONE_ASSET,
        ONE_GREEN,
        0,
        0,
        0,
        sender=ctx.switchboard_delta.address,
    )

    assert lp_received == 2
    assert ctx.lego.lastRecipient() == ctx.endaoment_funds.address
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2
    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0


def test_endaoment_rejects_zero_expected_lp_token(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    with boa.reverts("invalid lp token"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            0,
            ZERO_ADDRESS,
            sender=ctx.switchboard_delta.address,
        )


def test_paused_endaoment_blocks_partner_liquidity_locally(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    ctx.endaoment.pause(True, sender=ctx.switchboard_delta.address)

    with boa.reverts("contract paused"):
        _add_partner_liquidity(ctx, alice)


def test_switchboard_echo_stores_and_passes_expected_lp_token(
    partner_liquidity_env,
    governance,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)

    aid = ctx.switchboard_echo.addPartnerLiquidityInEndaoment(
        LEGO_ID,
        ctx.lp.address,
        alice,
        ctx.asset.address,
        ONE_ASSET,
        0,
        ctx.lp.address,
        sender=governance.address,
    )
    assert ctx.switchboard_echo.pendingEndaoPartnerPoolActions(aid) == (
        LEGO_ID,
        ctx.lp.address,
        alice,
        ctx.asset.address,
        ONE_ASSET,
        0,
        ctx.lp.address,
    )

    boa.env.time_travel(blocks=ctx.switchboard_echo.actionTimeLock())
    assert ctx.switchboard_echo.executePendingAction(
        aid,
        sender=governance.address,
    )
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1
