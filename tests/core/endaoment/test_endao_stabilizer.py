import hashlib
import json
from pathlib import Path

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, MAX_UINT256, ZERO_ADDRESS
from config.BluePrint import CORE_TOKENS, CURVE_PARAMS, ADDYS, WHALES
from conf_env import FORKS
from conf_utils import ensure_token_scale, filter_logs


CURVE_STABLE_FACTORY_ABI = """
[
    {
        "type": "function",
        "name": "deploy_plain_pool",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_name", "type": "string"},
            {"name": "_symbol", "type": "string"},
            {"name": "_coins", "type": "address[]"},
            {"name": "_A", "type": "uint256"},
            {"name": "_fee", "type": "uint256"},
            {"name": "_offpeg_fee_multiplier", "type": "uint256"},
            {"name": "_ma_exp_time", "type": "uint256"},
            {"name": "_implementation_idx", "type": "uint256"},
            {"name": "_asset_types", "type": "uint8[]"},
            {"name": "_method_ids", "type": "bytes4[]"},
            {"name": "_oracles", "type": "address[]"}
        ],
        "outputs": [{"name": "", "type": "address"}]
    }
]
"""

CURVE_STABLE_POOL_ABI = """
[
    {
        "type": "function",
        "name": "add_liquidity",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_amounts", "type": "uint256[]"},
            {"name": "_min_mint_amount", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "add_liquidity",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_amounts", "type": "uint256[]"},
            {"name": "_min_mint_amount", "type": "uint256"},
            {"name": "_receiver", "type": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "exchange",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_i", "type": "int128"},
            {"name": "_j", "type": "int128"},
            {"name": "_dx", "type": "uint256"},
            {"name": "_min_dy", "type": "uint256"},
            {"name": "_receiver", "type": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "calc_token_amount",
        "stateMutability": "view",
        "inputs": [
            {"name": "_amounts", "type": "uint256[]"},
            {"name": "_is_deposit", "type": "bool"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "calc_withdraw_one_coin",
        "stateMutability": "view",
        "inputs": [
            {"name": "_burn_amount", "type": "uint256"},
            {"name": "i", "type": "int128"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "remove_liquidity_imbalance",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_amounts", "type": "uint256[]"},
            {"name": "_max_burn_amount", "type": "uint256"},
            {"name": "_receiver", "type": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "get_balances",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256[]"}]
    },
    {
        "type": "function",
        "name": "balances",
        "stateMutability": "view",
        "inputs": [{"name": "i", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "balanceOf",
        "stateMutability": "view",
        "inputs": [{"name": "_owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "transfer",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}]
    },
    {
        "type": "function",
        "name": "totalSupply",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "coins",
        "stateMutability": "view",
        "inputs": [{"name": "i", "type": "uint256"}],
        "outputs": [{"name": "", "type": "address"}]
    },
    {
        "type": "function",
        "name": "N_COINS",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "A",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "ma_exp_time",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "D_ma_time",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "fee",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "offpeg_fee_multiplier",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    }
]
"""

BASE_RIPE_HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
CALC_TOKEN_AMOUNT_SELECTOR = bytes.fromhex("3db06dd8")
STABILIZER_KEEPER_GAS_BUDGET = 5_000_000


STABILIZER_LP_TOKEN_SOURCE = """
# @version 0.4.3

BALANCE: immutable(uint256)
TOTAL_SUPPLY: immutable(uint256)

@deploy
def __init__(_balance: uint256, _totalSupply: uint256):
    BALANCE = _balance
    TOTAL_SUPPLY = _totalSupply

@view
@external
def balanceOf(_owner: address) -> uint256:
    return BALANCE

@view
@external
def totalSupply() -> uint256:
    return TOTAL_SUPPLY
"""


STABILIZER_CURVE_PRICES_SOURCE = """
# @version 0.4.3

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

POOL: immutable(address)
LP_TOKEN: immutable(address)
GREEN_BALANCE: immutable(uint256)
GREEN_RATIO: immutable(uint256)
GREEN_INDEX: immutable(uint256)
STABILIZER_ADJUST_WEIGHT: immutable(uint256)
STABILIZER_MAX_POOL_DEBT: immutable(uint256)

@deploy
def __init__(
    _pool: address,
    _lpToken: address,
    _greenBalance: uint256,
    _greenRatio: uint256,
    _greenIndex: uint256,
    _stabilizerAdjustWeight: uint256,
    _stabilizerMaxPoolDebt: uint256,
):
    POOL = _pool
    LP_TOKEN = _lpToken
    GREEN_BALANCE = _greenBalance
    GREEN_RATIO = _greenRatio
    GREEN_INDEX = _greenIndex
    STABILIZER_ADJUST_WEIGHT = _stabilizerAdjustWeight
    STABILIZER_MAX_POOL_DEBT = _stabilizerMaxPoolDebt

@view
@external
def getGreenStabilizerConfig() -> StabilizerConfig:
    return StabilizerConfig(
        pool=POOL,
        lpToken=LP_TOKEN,
        greenBalance=GREEN_BALANCE,
        greenRatio=GREEN_RATIO,
        greenIndex=GREEN_INDEX,
        stabilizerAdjustWeight=STABILIZER_ADJUST_WEIGHT,
        stabilizerMaxPoolDebt=STABILIZER_MAX_POOL_DEBT,
    )
"""


STABILIZER_POOL_SOURCE = """
# @version 0.4.3

interface IERC20:
    def transferFrom(_from: address, _to: address, _amount: uint256) -> bool: nonpayable

GREEN: immutable(address)

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
lpTotalSupply: uint256
virtualPrice: uint256
lpMintedPerAdd: uint256
nextVirtualPrice: uint256
addCallCount: public(uint256)
lastGreenAdded: public(uint256)

@deploy
def __init__(
    _green: address,
    _virtualPrice: uint256,
    _lpMintedPerAdd: uint256,
    _nextVirtualPrice: uint256,
):
    GREEN = _green
    self.virtualPrice = _virtualPrice
    self.lpMintedPerAdd = _lpMintedPerAdd
    self.nextVirtualPrice = _nextVirtualPrice

@external
def seedLp(_holder: address, _amount: uint256):
    self.balances[_holder] += _amount
    self.lpTotalSupply += _amount

@view
@external
def balanceOf(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def totalSupply() -> uint256:
    return self.lpTotalSupply

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
    self.balances[_from] -= _amount
    self.balances[_to] += _amount
    return True

@view
@external
def get_virtual_price() -> uint256:
    return self.virtualPrice

@external
def add_liquidity(
    _amounts: DynArray[uint256, 2],
    _minLpAmountOut: uint256,
    _recipient: address = msg.sender,
) -> uint256:
    greenAmount: uint256 = _amounts[0]
    assert extcall IERC20(GREEN).transferFrom(msg.sender, self, greenAmount)
    self.balances[_recipient] += self.lpMintedPerAdd
    self.lpTotalSupply += self.lpMintedPerAdd
    self.addCallCount += 1
    self.lastGreenAdded = greenAmount
    if self.nextVirtualPrice != 0:
        self.virtualPrice = self.nextVirtualPrice
    return self.lpMintedPerAdd
"""


STABILIZER_REMOVAL_POOL_SOURCE = """
# @version 0.4.3

interface IERC20:
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable
    def balanceOf(_owner: address) -> uint256: view

GREEN: immutable(address)
BURN_NUMERATOR: immutable(uint256)
VIRTUAL_PRICE: immutable(uint256)
QUOTE_REVERTS: immutable(bool)
BURN_DENOMINATOR: constant(uint256) = 10 ** 18

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
lpTotalSupply: uint256
lastGreenRemoved: public(uint256)
lastLpBurned: public(uint256)
executionExtraBurn: public(uint256)
executionQuoteMode: public(uint256)

@deploy
def __init__(
    _green: address,
    _burnNumerator: uint256,
    _virtualPrice: uint256,
    _quoteReverts: bool,
):
    GREEN = _green
    BURN_NUMERATOR = _burnNumerator
    VIRTUAL_PRICE = _virtualPrice
    QUOTE_REVERTS = _quoteReverts

@external
def seedLp(_holder: address, _amount: uint256):
    self.balances[_holder] += _amount
    self.lpTotalSupply += _amount

@external
def setExecutionExtraBurn(_amount: uint256):
    self.executionExtraBurn = _amount

@external
def setExecutionQuoteMode(_mode: uint256):
    assert _mode <= 2
    self.executionQuoteMode = _mode

@view
@external
def balanceOf(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def totalSupply() -> uint256:
    return self.lpTotalSupply

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
    self.balances[_from] -= _amount
    self.balances[_to] += _amount
    return True

@view
@external
def get_virtual_price() -> uint256:
    return VIRTUAL_PRICE

@view
@external
def calc_token_amount(
    _amounts: DynArray[uint256, 2],
    _isDeposit: bool,
) -> uint256:
    assert not _isDeposit
    assert not QUOTE_REVERTS
    assert _amounts[0] <= staticcall IERC20(GREEN).balanceOf(self)
    approved: uint256 = self.allowances[msg.sender][self]
    if approved != 0:
        assert self.executionQuoteMode != 1
        if self.executionQuoteMode == 2:
            return approved
    return _amounts[0] * BURN_NUMERATOR // BURN_DENOMINATOR

@external
def remove_liquidity_imbalance(
    _amounts: DynArray[uint256, 2],
    _maxLpBurnAmount: uint256,
    _recipient: address = msg.sender,
) -> uint256:
    greenAmount: uint256 = _amounts[0]
    lpBurned: uint256 = greenAmount * BURN_NUMERATOR // BURN_DENOMINATOR + 1 + self.executionExtraBurn
    assert lpBurned <= _maxLpBurnAmount
    self.balances[msg.sender] -= lpBurned
    self.lpTotalSupply -= lpBurned
    assert extcall IERC20(GREEN).transfer(_recipient, greenAmount)
    self.lastGreenRemoved = greenAmount
    self.lastLpBurned = lpBurned
    return lpBurned
"""


STABILIZER_QUOTE_SHAPE_SOURCE = """
# @version 0.4.3

MODE: immutable(uint256)

@deploy
def __init__(_mode: uint256):
    MODE = _mode

@view
@external
@raw_return
def calc_token_amount(
    _amounts: DynArray[uint256, 2],
    _isDeposit: bool,
) -> Bytes[96]:
    assert not _isDeposit
    response: bytes32 = convert(7, bytes32)
    if MODE == 0:
        return b""
    if MODE == 1:
        return slice(response, 0, 31)
    if MODE == 2:
        return slice(response, 0, 32)
    if MODE == 3:
        return concat(response, convert(9, bytes32))
    return concat(response, convert(9, bytes32), convert(11, bytes32))
"""


def _signed_lp_position(lp_balance, green_balance, pool_debt, virtual_price):
    if pool_debt > green_balance:
        lp_debt = (pool_debt - green_balance) * EIGHTEEN_DECIMALS // virtual_price
        if lp_debt > lp_balance:
            return True, lp_debt - lp_balance
        return False, lp_balance - lp_debt

    lp_surplus = (green_balance - pool_debt) * EIGHTEEN_DECIMALS // virtual_price
    return False, lp_balance + lp_surplus


def _max_executable_green(pool, green_index, upper, lp_balance):
    low = 0
    high = upper
    while low < high:
        midpoint = high - (high - low) // 2
        amounts = [0, 0]
        amounts[green_index] = midpoint
        try:
            quote = pool.calc_token_amount(amounts, False)
        except Exception:
            high = midpoint - 1
            continue
        if quote < lp_balance:  # execution burns quote + one wei LP
            low = midpoint
        else:
            high = midpoint - 1
    return low


def _count_selector_calls(computation, selector):
    data = bytes(getattr(computation.msg, "data", b""))
    count = int(data[:4] == selector)
    return count + sum(
        _count_selector_calls(child, selector)
        for child in getattr(computation, "children", ())
    )


def _quoted_green_amounts(computation, green_index=0):
    data = bytes(getattr(computation.msg, "data", b""))
    quoted = []
    if data[:4] == CALC_TOKEN_AMOUNT_SELECTOR:
        array_offset = int.from_bytes(data[4:36], "big")
        array_start = 4 + array_offset
        array_length = int.from_bytes(data[array_start : array_start + 32], "big")
        assert green_index < array_length
        value_start = array_start + 32 * (green_index + 1)
        quoted.append(int.from_bytes(data[value_start : value_start + 32], "big"))
    for child in getattr(computation, "children", ()):
        quoted.extend(_quoted_green_amounts(child, green_index))
    return quoted


def _install_stabilizer_transition_harness(
    curve_prices,
    green_token,
    lp_minted,
    initial_virtual_price=EIGHTEEN_DECIMALS,
    next_virtual_price=0,
    green_balance=40 * EIGHTEEN_DECIMALS,
    green_ratio=40_00,
    green_index=0,
):
    pool = boa.loads(
        STABILIZER_POOL_SOURCE,
        green_token.address,
        initial_virtual_price,
        lp_minted,
        next_virtual_price,
        name="stabilizer transition pool",
    )
    mock_curve_prices = boa.loads(
        STABILIZER_CURVE_PRICES_SOURCE,
        pool.address,
        pool.address,
        green_balance,
        green_ratio,
        green_index,
        HUNDRED_PERCENT,
        1_000_000 * EIGHTEEN_DECIMALS,
        name="stabilizer transition config",
    )
    boa.env.set_code(curve_prices.address, boa.env.get_code(mock_curve_prices.address))
    return pool


def _seed_stabilizer_transition(
    curve_prices,
    green_token,
    ledger,
    endaoment,
    endaoment_funds,
    initial_lp,
    initial_debt,
    lp_minted,
    leftover_green=0,
    initial_virtual_price=EIGHTEEN_DECIMALS,
    next_virtual_price=0,
):
    pool = _install_stabilizer_transition_harness(
        curve_prices,
        green_token,
        lp_minted,
        initial_virtual_price,
        next_virtual_price,
    )
    if initial_lp != 0:
        pool.seedLp(endaoment_funds, initial_lp)
    if leftover_green != 0:
        green_token.mint(
            endaoment_funds,
            leftover_green,
            sender=endaoment.address,
        )
    if initial_debt != 0:
        ledger.updateGreenPoolDebt(
            pool.address,
            initial_debt,
            True,
            sender=endaoment.address,
        )
    return pool


def _install_stabilizer_view_mocks(
    curve_prices,
    lp_total_supply,
    green_index=1,
    green_balance=15_000 * EIGHTEEN_DECIMALS,
    pool=None,
):
    lp_balance = 200 * EIGHTEEN_DECIMALS
    green_ratio = 75_00
    stabilizer_adjust_weight = 50_00
    if pool is None:
        pool = boa.env.generate_address()
    lp_token = boa.loads(
        STABILIZER_LP_TOKEN_SOURCE,
        lp_balance,
        lp_total_supply,
        name="stabilizer lp supply mock",
    )
    mock_curve_prices = boa.loads(
        STABILIZER_CURVE_PRICES_SOURCE,
        pool,
        lp_token.address,
        green_balance,
        green_ratio,
        green_index,
        stabilizer_adjust_weight,
        1_000_000 * EIGHTEEN_DECIMALS,
        name="stabilizer config mock",
    )
    boa.env.set_code(
        curve_prices.address,
        boa.env.get_code(mock_curve_prices.address),
    )
    return pool, lp_token, lp_balance


def _install_stabilizer_removal_harness(
    curve_prices,
    green_token,
    green_balance,
    green_ratio,
    burn_numerator=2 * EIGHTEEN_DECIMALS,
    adjust_weight=HUNDRED_PERCENT,
    green_index=0,
    quote_reverts=False,
):
    virtual_price = EIGHTEEN_DECIMALS
    if burn_numerator != 0:
        virtual_price = (
            EIGHTEEN_DECIMALS * EIGHTEEN_DECIMALS // burn_numerator - 1
        )
    pool = boa.loads(
        STABILIZER_REMOVAL_POOL_SOURCE,
        green_token.address,
        burn_numerator,
        virtual_price,
        quote_reverts,
        name="stabilizer removal pool",
    )
    mock_curve_prices = boa.loads(
        STABILIZER_CURVE_PRICES_SOURCE,
        pool.address,
        pool.address,
        green_balance,
        green_ratio,
        green_index,
        adjust_weight,
        1_000_000 * EIGHTEEN_DECIMALS,
        name="stabilizer removal config",
    )
    boa.env.set_code(curve_prices.address, boa.env.get_code(mock_curve_prices.address))
    return pool


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance, price_desk, switchboard_bravo):
    usdc = boa.load_abi("scripts/abis/Erc20Token.json", name="usdc").at(
        CORE_TOKENS[fork]["USDC"]
    )
    assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governance.address)
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)
    ensure_token_scale(price_desk, usdc, switchboard_bravo.address)
    return usdc


@pytest.fixture(scope="module")
def deployed_green_pool(
    green_token,
    deploy3r,
    usdc_token,
    fork,
):
    factory = boa.loads_abi(
        CURVE_STABLE_FACTORY_ABI,
        name="curve stable factory",
    ).at(ADDYS[fork]["CURVE_STABLE_FACTORY"])

    implementation_idx = 0
    green_pool_deploy = factory.deploy_plain_pool(
        CURVE_PARAMS[fork]["GREEN_POOL_NAME"],
        CURVE_PARAMS[fork]["GREEN_POOL_SYMBOL"],
        [usdc_token, green_token],
        CURVE_PARAMS[fork]["GREEN_POOL_A"],
        CURVE_PARAMS[fork]["GREEN_POOL_FEE"],
        CURVE_PARAMS[fork]["GREEN_POOL_OFFPEG_MULTIPLIER"],
        CURVE_PARAMS[fork]["GREEN_POOL_MA_EXP_TIME"],
        implementation_idx,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        sender=deploy3r,
    )
    boa.loads_abi(CURVE_STABLE_POOL_ABI, name="green pool").at(
        green_pool_deploy
    )
    return green_pool_deploy


@pytest.fixture(scope="module")
def addSeedGreenLiq(
    green_token,
    deployed_green_pool,
    whale,
    fork,
    usdc_token,
    bob,
):
    def addSeedGreenLiq(_usdcAmount=None, _greenAmount=None):
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        # usdc
        usdc_amount = _usdcAmount
        if usdc_amount is None:
            usdc_amount = 10_000 * (10 ** usdc_token.decimals())
        usdc_token.transfer(bob, usdc_amount, sender=WHALES[fork]["usdc"])
        usdc_token.approve(green_pool, usdc_amount, sender=bob)

        # green
        green_amount = _greenAmount
        if green_amount is None:
            green_amount = 10_000 * EIGHTEEN_DECIMALS
        if green_amount != 0:
            green_token.transfer(bob, green_amount, sender=whale)
            green_token.approve(green_pool, green_amount, sender=bob)

        # add liquidity
        green_pool.add_liquidity([usdc_amount, green_amount], 0, bob, sender=bob)

    yield addSeedGreenLiq


@pytest.fixture(scope="module")
def swapGreenForUsdc(
    green_token,
    deployed_green_pool,
    whale,
    bob,
):
    def swapGreenForUsdc(_greenAmount):
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        green_token.transfer(bob, _greenAmount, sender=whale)
        green_token.approve(green_pool, _greenAmount, sender=bob)
        received_usdc = green_pool.exchange(1, 0, _greenAmount, 0, bob, sender=bob)

        return received_usdc

    yield swapGreenForUsdc


@pytest.fixture(scope="module")
def swapUsdcForGreen(
    deployed_green_pool,
    fork,
    usdc_token,
    bob,
):
    def swapUsdcForGreen(_usdcAmount):
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        usdc_token.transfer(bob, _usdcAmount, sender=WHALES[fork]["usdc"])
        usdc_token.approve(green_pool, _usdcAmount, sender=bob)
        received_green = green_pool.exchange(0, 1, _usdcAmount, 0, bob, sender=bob)

        return received_green

    yield swapUsdcForGreen


@pytest.fixture(scope="module")
def setGreenRefConfig(
    deployed_green_pool,
    curve_prices,
    governance,
):
    def setGreenRefConfig(
        _stabilizerAdjustWeight = 50_00,
        _stabilizerMaxPoolDebt = 1_000_000 * EIGHTEEN_DECIMALS,
    ):
        aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 50_00, 0, _stabilizerAdjustWeight, _stabilizerMaxPoolDebt, sender=governance.address)
        boa.env.time_travel(blocks=curve_prices.actionTimeLock())
        assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    yield setGreenRefConfig


@pytest.fixture(scope="module", autouse=True)
def setup_mock_undy_v2(mock_undy_v2):
    # legacy curve underscore lego is 10
    mock_undy_v2.setUseThisLegoId(10)


####################
# Green Stabilizer #
####################


def test_green_amount_to_remove_zero_lp_supply_returns_zero(
    endaoment,
    endaoment_funds,
    curve_prices,
):
    with boa.env.anchor():
        pool, lp_token, lp_balance = _install_stabilizer_view_mocks(
            curve_prices,
            0,
        )
        data = curve_prices.getGreenStabilizerConfig()

        assert data.pool == pool != ZERO_ADDRESS
        assert data.greenBalance != 0
        assert data.greenRatio > HUNDRED_PERCENT // 2
        assert data.stabilizerAdjustWeight > 0
        assert lp_token.balanceOf(endaoment_funds) == lp_balance != 0
        assert lp_token.totalSupply() == 0
        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0


def test_green_amount_to_remove_unsupported_quote_fails_closed(
    endaoment,
    endaoment_funds,
    curve_prices,
):
    lp_total_supply = 1_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool, lp_token, lp_balance = _install_stabilizer_view_mocks(
            curve_prices,
            lp_total_supply,
        )
        data = curve_prices.getGreenStabilizerConfig()
        assert data.pool == pool != ZERO_ADDRESS
        assert data.greenBalance != 0
        assert data.greenRatio > HUNDRED_PERCENT // 2
        assert data.stabilizerAdjustWeight > 0
        assert lp_token.balanceOf(endaoment_funds) == lp_balance != 0
        assert lp_token.totalSupply() == lp_total_supply != 0
        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0


def test_green_amount_to_remove_invalid_green_index_fails_closed(
    endaoment,
    endaoment_funds,
    curve_prices,
):
    with boa.env.anchor():
        pool, lp_token, lp_balance = _install_stabilizer_view_mocks(
            curve_prices,
            1_000 * EIGHTEEN_DECIMALS,
            green_index=2,
        )

        assert pool != ZERO_ADDRESS
        assert lp_token.balanceOf(endaoment_funds) == lp_balance != 0
        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0


def test_green_amount_to_remove_invalid_index_precedes_snapshot_arithmetic(
    endaoment,
    curve_prices,
):
    with boa.env.anchor():
        _install_stabilizer_view_mocks(
            curve_prices,
            1_000 * EIGHTEEN_DECIMALS,
            green_index=2,
            green_balance=MAX_UINT256,
        )

        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0


def test_green_amount_to_add_invalid_index_is_external_noop(
    endaoment,
    endaoment_funds,
    curve_prices,
    green_token,
    switchboard_delta,
):
    with boa.env.anchor():
        pool = _install_stabilizer_transition_harness(
            curve_prices,
            green_token,
            2 * EIGHTEEN_DECIMALS,
            green_index=2,
        )
        before = (
            pool.addCallCount(),
            green_token.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            pool.balanceOf(endaoment_funds),
        )

        assert endaoment.getGreenAmountToAddInStabilizer() == 0
        assert not endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
        assert not filter_logs(endaoment, "StabilizerPoolLiqAdded")
        assert (
            pool.addCallCount(),
            green_token.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            pool.balanceOf(endaoment_funds),
        ) == before


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (0, 0),
        (1, 0),
        (2, 3_000 * EIGHTEEN_DECIMALS),
        (3, 0),
        (4, 0),
    ],
    ids=["empty", "short", "exact-32", "oversized-64", "oversized-96"],
)
def test_sc19_quote_return_shape_is_exactly_one_word(
    endaoment,
    endaoment_funds,
    curve_prices,
    mode,
    expected,
):
    with boa.env.anchor():
        quote_pool = boa.loads(
            STABILIZER_QUOTE_SHAPE_SOURCE,
            mode,
            name=f"stabilizer quote shape {mode}",
        )
        _, lp_token, lp_balance = _install_stabilizer_view_mocks(
            curve_prices,
            1_000 * EIGHTEEN_DECIMALS,
            green_index=0,
            pool=quote_pool.address,
        )
        before = (
            lp_token.balanceOf(endaoment_funds),
            lp_token.totalSupply(),
        )

        assert lp_balance == 200 * EIGHTEEN_DECIMALS
        assert endaoment.getGreenAmountToRemoveInStabilizer() == expected
        assert (
            lp_token.balanceOf(endaoment_funds),
            lp_token.totalSupply(),
        ) == before


def test_sc19_proportional_policy_allowance_preserves_exact_value(
    endaoment,
    endaoment_funds,
    curve_prices,
    green_token,
):
    lp_balance = 200 * EIGHTEEN_DECIMALS
    lp_total_supply = 1_000 * EIGHTEEN_DECIMALS
    pool_green = 15_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            burn_numerator=EIGHTEEN_DECIMALS // 100,
            adjust_weight=50_00,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(
            boa.env.generate_address(),
            lp_total_supply - lp_balance,
        )
        green_token.mint(pool.address, pool_green, sender=endaoment.address)

        desired_weighted = 5_000 * EIGHTEEN_DECIMALS
        proportional_allowance = pool_green * lp_balance // lp_total_supply
        expected = min(desired_weighted, proportional_allowance)

        assert proportional_allowance == 3_000 * EIGHTEEN_DECIMALS
        assert endaoment.getGreenAmountToRemoveInStabilizer() == expected


def test_sc19_full_request_fast_path_matches_full_search(
    endaoment,
    endaoment_funds,
    curve_prices,
    green_token,
):
    lp_balance = 200 * EIGHTEEN_DECIMALS
    lp_total_supply = 1_000 * EIGHTEEN_DECIMALS
    pool_green = 15_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            burn_numerator=EIGHTEEN_DECIMALS // 100,
            adjust_weight=50_00,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), lp_total_supply - lp_balance)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)

        expected = 3_000 * EIGHTEEN_DECIMALS
        full_search_result = _max_executable_green(
            pool,
            0,
            expected,
            lp_balance,
        )
        requested = endaoment.getGreenAmountToRemoveInStabilizer()
        quote_calls = _quoted_green_amounts(endaoment._computation)

        assert full_search_result == expected
        assert requested == full_search_result
        assert quote_calls == [requested]


def test_sc19_reverting_full_request_falls_through_to_search(
    endaoment,
    endaoment_funds,
    curve_prices,
    green_token,
    switchboard_delta,
):
    lp_balance = 200 * EIGHTEEN_DECIMALS
    lp_total_supply = 1_000 * EIGHTEEN_DECIMALS
    reported_pool_green = 1_000 * EIGHTEEN_DECIMALS
    quoteable_pool_green = 100 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            reported_pool_green,
            75_00,
            burn_numerator=EIGHTEEN_DECIMALS,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), lp_total_supply - lp_balance)
        green_token.mint(
            pool.address,
            quoteable_pool_green,
            sender=endaoment.address,
        )

        full_request = reported_pool_green * lp_balance // lp_total_supply
        assert full_request == 200 * EIGHTEEN_DECIMALS
        with boa.reverts():
            pool.calc_token_amount([full_request, 0], False)

        full_search_result = _max_executable_green(
            pool,
            0,
            full_request,
            lp_balance,
        )
        requested = endaoment.getGreenAmountToRemoveInStabilizer()
        quote_calls = _quoted_green_amounts(endaoment._computation)

        assert full_search_result == quoteable_pool_green
        assert requested == full_search_result
        assert quote_calls[0] == full_request
        assert requested in quote_calls
        assert len(quote_calls) > 1
        requested_quote = pool.calc_token_amount([requested, 0], False)
        assert requested_quote < lp_balance
        with boa.reverts():
            pool.calc_token_amount([requested + 1, 0], False)
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
        assert log.greenAmountRemoved == quoteable_pool_green
        assert log.lpBurned == quoteable_pool_green + 1
        assert log.debtRepaid == 0


def test_sc19_reverting_quote_is_external_noop_with_no_state_change(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    lp_balance = 100 * EIGHTEEN_DECIMALS
    pool_debt = 1_000 * EIGHTEEN_DECIMALS
    pool_green = 1_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            quote_reverts=True,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), 9_900 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
        before = (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        )

        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
        assert not endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
        assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")
        assert (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        ) == before


@pytest.mark.parametrize(
    "execution_quote_mode",
    (1, 2),
    ids=("reverts", "quote-equals-lp-balance"),
)
def test_sc19_execution_requote_failure_or_unsafe_quote_is_atomic_noop(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
    execution_quote_mode,
):
    lp_balance = 100 * EIGHTEEN_DECIMALS
    pool_debt = 20 * EIGHTEEN_DECIMALS
    pool_green = 1_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            burn_numerator=2 * EIGHTEEN_DECIMALS,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), 9_900 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
        pool.setExecutionQuoteMode(execution_quote_mode)

        # Sizing occurs before LP approval and therefore succeeds. The mock
        # changes behavior only for the execution-bound quote after approval.
        assert endaoment.getGreenAmountToRemoveInStabilizer() == pool_debt
        before = (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            pool.lastGreenRemoved(),
            pool.lastLpBurned(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            green_token.totalSupply(),
            ledger.greenPoolDebt(pool.address),
        )

        assert not endaoment.stabilizeGreenRefPool(
            sender=switchboard_delta.address
        )
        assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")
        assert (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            pool.lastGreenRemoved(),
            pool.lastLpBurned(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            green_token.totalSupply(),
            ledger.greenPoolDebt(pool.address),
        ) == before


def test_sc19_missing_ng_quote_selector_is_external_noop(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    lp_balance = 100 * EIGHTEEN_DECIMALS
    pool_debt = 1_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_transition_harness(
            curve_prices,
            green_token,
            0,
            green_balance=1_000 * EIGHTEEN_DECIMALS,
            green_ratio=75_00,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), 9_900 * EIGHTEEN_DECIMALS)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
        before = (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            ledger.greenPoolDebt(pool.address),
        )

        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
        assert not endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
        assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")
        assert (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            ledger.greenPoolDebt(pool.address),
        ) == before


def test_sc19_zero_lp_capacity_is_external_noop_with_no_state_change(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    pool_debt = 20 * EIGHTEEN_DECIMALS
    pool_green = 100 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
        )
        pool.seedLp(boa.env.generate_address(), 100 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
        before = (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        )

        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
        assert not endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
        assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")
        assert (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        ) == before


@pytest.mark.parametrize(
    "pool_debt",
    [
        20 * EIGHTEEN_DECIMALS,
        (100 * EIGHTEEN_DECIMALS - 1) // 2,
        1_000 * EIGHTEEN_DECIMALS,
    ],
    ids=["debt-below-capacity", "debt-equals-capacity", "debt-exceeds-capacity"],
)
def test_sc19_debt_request_is_capped_to_executable_lp_capacity(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
    pool_debt,
):
    lp_balance = 100 * EIGHTEEN_DECIMALS
    pool_green = 1_000 * EIGHTEEN_DECIMALS
    burn_numerator = 2 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            burn_numerator,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), 9_900 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )

        requested = endaoment.getGreenAmountToRemoveInStabilizer()
        executable_cap = (lp_balance - 1) * EIGHTEEN_DECIMALS // burn_numerator
        quoted_burn_at_cap = (
            executable_cap * burn_numerator // EIGHTEEN_DECIMALS
        )
        quoted_burn_above_cap = (
            (executable_cap + 1) * burn_numerator // EIGHTEEN_DECIMALS
        )
        expected_request = min(pool_debt, executable_cap)
        assert requested == expected_request > 0
        assert quoted_burn_at_cap + 1 <= lp_balance
        assert quoted_burn_above_cap + 1 > lp_balance
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
        expected_burn = requested * burn_numerator // EIGHTEEN_DECIMALS + 1
        assert pool.lastGreenRemoved() == requested
        assert pool.lastLpBurned() == expected_burn
        assert log.greenAmountRemoved == requested
        assert log.lpBurned == expected_burn
        assert log.debtRepaid == requested
        assert ledger.greenPoolDebt(pool.address) == pool_debt - requested
        assert pool.balanceOf(endaoment.address) == 0
        assert green_token.balanceOf(endaoment.address) == 0
        assert pool.balanceOf(endaoment_funds) == lp_balance - log.lpBurned


def test_sc19_execution_quote_bound_reverts_on_quote_execution_mismatch(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    lp_balance = 100 * EIGHTEEN_DECIMALS
    pool_debt = 20 * EIGHTEEN_DECIMALS
    pool_green = 1_000 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            pool_green,
            75_00,
            burn_numerator=2 * EIGHTEEN_DECIMALS,
        )
        pool.seedLp(endaoment_funds, lp_balance)
        pool.seedLp(boa.env.generate_address(), 9_900 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, pool_green, sender=endaoment.address)
        ledger.updateGreenPoolDebt(
            pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
        pool.setExecutionExtraBurn(1)
        before = (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        )

        with boa.reverts():
            endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        assert (
            pool.balanceOf(endaoment_funds),
            pool.balanceOf(endaoment.address),
            pool.totalSupply(),
            pool.allowance(endaoment.address, pool.address),
            green_token.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment.address),
            green_token.balanceOf(pool.address),
            ledger.greenPoolDebt(pool.address),
        ) == before


def test_sc19_zero_quote_accounts_for_stableswap_rounding_burn(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    pool_debt = 20 * EIGHTEEN_DECIMALS
    with boa.env.anchor():
        pool = _install_stabilizer_removal_harness(
            curve_prices,
            green_token,
            100 * EIGHTEEN_DECIMALS,
            75_00,
            0,
        )
        pool.seedLp(endaoment_funds, 10 * EIGHTEEN_DECIMALS)
        pool.seedLp(boa.env.generate_address(), 90 * EIGHTEEN_DECIMALS)
        green_token.mint(pool.address, 100 * EIGHTEEN_DECIMALS, sender=endaoment.address)
        ledger.updateGreenPoolDebt(pool.address, pool_debt, True, sender=endaoment.address)

        requested = endaoment.getGreenAmountToRemoveInStabilizer()
        assert requested == pool_debt
        assert pool.calc_token_amount([requested, 0], False) == 0
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
        assert log.greenAmountRemoved == pool_debt
        assert log.lpBurned == 1
        assert log.debtRepaid == pool_debt
        assert ledger.greenPoolDebt(pool.address) == 0
        assert pool.balanceOf(endaoment_funds) == 10 * EIGHTEEN_DECIMALS - 1


@pytest.base
@pytest.mark.fork_qualification
def test_sc19_base_pool_runtime_equivalence(
    fork,
    deploy3r,
):
    assert fork == "base"
    live_hq = boa.load_abi("scripts/abis/RipeHq.json", name="live Base RipeHq").at(
        BASE_RIPE_HQ
    )
    live_price_desk = boa.load_abi(
        "scripts/abis/PriceDesk.json",
        name="live Base PriceDesk",
    ).at(live_hq.getAddr(7))
    live_curve_prices = boa.load_abi(
        "scripts/abis/CurvePrices.json",
        name="live Base CurvePrices",
    ).at(live_price_desk.getAddr(2))
    production_pool_address = live_curve_prices.greenRefPoolConfig().pool
    production_pool = boa.loads_abi(
        CURVE_STABLE_POOL_ABI,
        name="production configured GREEN pool",
    ).at(production_pool_address)
    factory_address = ADDYS[fork]["CURVE_STABLE_FACTORY"]
    factory = boa.loads_abi(
        CURVE_STABLE_FACTORY_ABI,
        name="curve stable factory equivalence",
    ).at(factory_address)
    live_green = live_hq.getAddr(1)

    equivalent_pool_address = factory.deploy_plain_pool(
        CURVE_PARAMS[fork]["GREEN_POOL_NAME"],
        CURVE_PARAMS[fork]["GREEN_POOL_SYMBOL"],
        [CORE_TOKENS[fork]["USDC"], live_green],
        CURVE_PARAMS[fork]["GREEN_POOL_A"],
        CURVE_PARAMS[fork]["GREEN_POOL_FEE"],
        CURVE_PARAMS[fork]["GREEN_POOL_OFFPEG_MULTIPLIER"],
        CURVE_PARAMS[fork]["GREEN_POOL_MA_EXP_TIME"],
        0,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        sender=deploy3r,
    )
    production_code = boa.env.get_code(production_pool_address)
    equivalent_code = boa.env.get_code(equivalent_pool_address)
    production_balances = list(production_pool.get_balances())
    production_probe = min(production_balances[1] // 100, EIGHTEEN_DECIMALS)
    assert production_probe > 0
    production_quote = production_pool.calc_token_amount(
        [0, production_probe], False
    )
    production_one_coin = production_pool.calc_withdraw_one_coin(
        production_pool.totalSupply() // 10_000, 1
    )

    assert production_pool_address != ZERO_ADDRESS
    assert production_pool.N_COINS() == 2
    assert production_pool.coins(0) == CORE_TOKENS[fork]["USDC"]
    assert production_pool.coins(1) == live_green
    assert production_pool.A() == CURVE_PARAMS[fork]["GREEN_POOL_A"]
    assert production_pool.fee() == CURVE_PARAMS[fork]["GREEN_POOL_FEE"]
    assert (
        production_pool.offpeg_fee_multiplier()
        == CURVE_PARAMS[fork]["GREEN_POOL_OFFPEG_MULTIPLIER"]
    )
    assert production_pool.ma_exp_time() == CURVE_PARAMS[fork]["GREEN_POOL_MA_EXP_TIME"]
    assert production_pool.D_ma_time() != 0
    assert production_quote > 0
    assert production_one_coin > 0
    # StableSwap-NG appends a per-deployment salt and EIP-712 domain separator.
    # All executable logic and pool-math/configuration immutables precede them.
    per_pool_identity_size = 64
    assert len(production_code) == len(equivalent_code)
    assert production_code[:-per_pool_identity_size] == equivalent_code[:-per_pool_identity_size]
    assert production_code[-per_pool_identity_size:] != equivalent_code[-per_pool_identity_size:]

    print(
        "SC19_POOL_EQUIVALENCE",
        json.dumps(
            {
                "chain_id": 8453,
                "fork_block": FORKS[fork]["block"],
                "production_pool": str(production_pool_address),
                "equivalent_fresh_pool": str(equivalent_pool_address),
                "factory": factory_address,
                "runtime_size": len(production_code),
                "production_runtime_sha256": hashlib.sha256(
                    production_code
                ).hexdigest(),
                "fresh_runtime_sha256": hashlib.sha256(equivalent_code).hexdigest(),
                "logic_and_math_immutable_sha256": hashlib.sha256(
                    production_code[:-per_pool_identity_size]
                ).hexdigest(),
                "exact_runtime_equivalence": False,
                "runtime_difference": "final 64-byte per-pool salt and EIP-712 domain separator only",
                "production_balances": production_balances,
                "production_calc_token_amount_probe": production_quote,
                "production_calc_withdraw_one_coin_probe": production_one_coin,
                "family": "Curve StableSwap-NG",
            },
            sort_keys=True,
        ),
    )


@pytest.base
@pytest.mark.fork_qualification
@pytest.mark.parametrize(
    ("green_swap", "lp_divisor", "pool_debt", "use_keeper_route", "cap_binds"),
    [
        (5_000 * EIGHTEEN_DECIMALS, 20, 20_000 * EIGHTEEN_DECIMALS, False, True),
        (8_000 * EIGHTEEN_DECIMALS, 33, 20_000 * EIGHTEEN_DECIMALS, True, True),
        (5_000 * EIGHTEEN_DECIMALS, 20, 0, True, False),
    ],
    ids=[
        "case1-cap-binds",
        "case2-material-imbalance-fees",
        "case3-full-request-fast-path",
    ],
)
def test_sc19_base_executable_request_real_pool(
    fork,
    addSeedGreenLiq,
    setGreenRefConfig,
    swapGreenForUsdc,
    endaoment,
    endaoment_funds,
    curve_prices,
    deployed_green_pool,
    green_token,
    ledger,
    switchboard_delta,
    switchboard_echo,
    governance,
    bob,
    green_swap,
    lp_divisor,
    pool_debt,
    use_keeper_route,
    cap_binds,
):
    assert fork == "base"
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    seed_lp = green_pool.balanceOf(bob)
    probe_amount = 100 * EIGHTEEN_DECIMALS
    balanced_quote = green_pool.calc_token_amount([0, probe_amount], False)
    with boa.env.anchor():
        balanced_burn = green_pool.remove_liquidity_imbalance(
            [0, probe_amount],
            MAX_UINT256,
            bob,
            sender=bob,
        )
        assert balanced_burn == balanced_quote + 1

    lp_balance = seed_lp // lp_divisor
    green_pool.transfer(endaoment_funds, lp_balance, sender=bob)
    swapGreenForUsdc(green_swap)
    data = curve_prices.getGreenStabilizerConfig()
    assert data.greenIndex == 1
    imbalanced_quote = green_pool.calc_token_amount([0, probe_amount], False)
    with boa.env.anchor():
        imbalanced_burn = green_pool.remove_liquidity_imbalance(
            [0, probe_amount],
            MAX_UINT256,
            bob,
            sender=bob,
        )
        assert imbalanced_burn == imbalanced_quote + 1
    assert imbalanced_quote != balanced_quote

    if pool_debt != 0:
        ledger.updateGreenPoolDebt(
            green_pool.address,
            pool_debt,
            True,
            sender=endaoment.address,
        )
    total_pool_balance = data.greenBalance * HUNDRED_PERCENT // data.greenRatio
    target_balance = total_pool_balance // 2
    desired_weighted = (
        (data.greenBalance - target_balance)
        * 2
        * data.stabilizerAdjustWeight
        // HUNDRED_PERCENT
    )
    policy_allowance = max(
        pool_debt,
        data.greenBalance * lp_balance // green_pool.totalSupply(),
    )
    desired_uncapped = min(desired_weighted, policy_allowance)
    executable_cap = _max_executable_green(
        green_pool,
        data.greenIndex,
        desired_uncapped,
        lp_balance,
    )
    requested = endaoment.getGreenAmountToRemoveInStabilizer()
    cap_amounts = [0, 0]
    cap_amounts[data.greenIndex] = executable_cap
    cap_quote = green_pool.calc_token_amount(cap_amounts, False)
    above_amounts = list(cap_amounts)
    above_amounts[data.greenIndex] += 1
    above_quote = green_pool.calc_token_amount(above_amounts, False)
    funds_green_before = green_token.balanceOf(endaoment_funds)
    pool_green_before = green_token.balanceOf(green_pool)
    assert requested == executable_cap > 0
    assert desired_weighted >= executable_cap
    assert policy_allowance >= executable_cap
    assert cap_quote + 1 <= lp_balance
    if cap_binds:
        assert desired_uncapped > executable_cap
        assert pool_debt > executable_cap
        assert above_quote + 1 > lp_balance
    else:
        assert desired_uncapped == executable_cap
    log_contract = endaoment
    entrypoint = "Endaoment.stabilizeGreenRefPool"
    if use_keeper_route:
        assert switchboard_echo.stabilizeGreenRefPoolInEndaoment(
            sender=governance.address
        )
        stabilize_computation = switchboard_echo._computation
        log_contract = switchboard_echo
        entrypoint = "SwitchboardEcho.stabilizeGreenRefPoolInEndaoment"
        echo_log = filter_logs(
            switchboard_echo,
            "EndaomentStabilizerPerformed",
        )[0]
        assert echo_log.success
        assert echo_log.caller == governance.address
    else:
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
        stabilize_computation = endaoment._computation
    stabilize_gas = stabilize_computation.get_gas_used()
    quote_calls = _count_selector_calls(
        stabilize_computation,
        CALC_TOKEN_AMOUNT_SELECTOR,
    )
    assert stabilize_gas > 0
    assert 0 < quote_calls <= 257
    assert stabilize_gas <= STABILIZER_KEEPER_GAS_BUDGET
    if not cap_binds:
        # One sizing quote plus one execution-bound re-quote.
        assert quote_calls == 2

    log = filter_logs(log_contract, "StabilizerPoolLiqRemoved")[0]
    actual_lp_burned = lp_balance - green_pool.balanceOf(endaoment_funds)
    actual_green_received = pool_green_before - green_token.balanceOf(green_pool)
    assert actual_lp_burned == cap_quote + 1 == log.lpBurned
    assert actual_lp_burned <= lp_balance
    assert actual_green_received == executable_cap == log.greenAmountRemoved
    assert log.debtRepaid == min(executable_cap, pool_debt)
    assert ledger.greenPoolDebt(green_pool.address) == pool_debt - log.debtRepaid
    assert green_token.balanceOf(endaoment_funds) == (
        funds_green_before + actual_green_received - log.debtRepaid
    )
    assert green_pool.balanceOf(endaoment.address) == 0
    assert green_token.balanceOf(endaoment.address) == 0

    print(
        "SC19_BASE_POSTFIX",
        json.dumps(
            {
                "chain_id": 8453,
                "fork_block": FORKS[fork]["block"],
                "controlled_pool": str(green_pool.address),
                "factory": ADDYS["base"]["CURVE_STABLE_FACTORY"],
                "pool_balances": list(green_pool.get_balances()),
                "pool_debt": pool_debt,
                "lp_balance": lp_balance,
                "desired_weighted_adjustment": desired_weighted,
                "policy_allowance": policy_allowance,
                "desired_uncapped_removal": desired_uncapped,
                "executable_cap": executable_cap,
                "quote_at_cap": cap_quote,
                "quote_at_cap_plus_one": above_quote,
                "balanced_quote": balanced_quote,
                "balanced_actual_burn": balanced_burn,
                "imbalanced_quote": imbalanced_quote,
                "imbalanced_actual_burn": imbalanced_burn,
                "actual_green_received": actual_green_received,
                "actual_lp_burned": actual_lp_burned,
                "debt_repaid": log.debtRepaid,
                "stabilize_gas": stabilize_gas,
                "quote_calls": quote_calls,
                "fast_path_used": not cap_binds,
                "entrypoint": entrypoint,
                "post_fix_result": (
                    "exact executable cap succeeded"
                    if cap_binds
                    else "full executable request succeeded with two quotes"
                ),
            },
            sort_keys=True,
        ),
    )


@pytest.base
@pytest.mark.fork_qualification
def test_sc19_base_production_pool_direct_external_path(
    fork,
    endaoment,
    endaoment_funds,
    curve_prices,
    governance,
    ripe_hq_deploy,
    usdc_token,
    bob,
    ledger,
    switchboard_delta,
):
    live_hq = boa.load_abi("scripts/abis/RipeHq.json", name="live Base RipeHq direct").at(
        BASE_RIPE_HQ
    )
    live_price_desk = boa.load_abi(
        "scripts/abis/PriceDesk.json", name="live Base PriceDesk direct"
    ).at(live_hq.getAddr(7))
    live_curve_prices = boa.load_abi(
        "scripts/abis/CurvePrices.json", name="live Base CurvePrices direct"
    ).at(live_price_desk.getAddr(2))
    production_pool_address = live_curve_prices.greenRefPoolConfig().pool
    live_green_address = live_hq.getAddr(1)
    live_green = boa.load_abi(
        "scripts/abis/GreenToken.json", name="live GREEN direct"
    ).at(live_green_address)
    pool = boa.loads_abi(CURVE_STABLE_POOL_ABI, name="direct production GREEN pool").at(
        production_pool_address
    )

    # Align the local Endaoment system with the production pool's live GREEN
    # address for this fork-only direct-attachment qualification.
    assert ripe_hq_deploy.startAddressUpdateToRegistry(
        1, live_green_address, sender=governance.address
    )
    boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
    assert ripe_hq_deploy.confirmAddressUpdateToRegistry(1, sender=governance.address)

    seed_usdc = 100_000 * 10 ** usdc_token.decimals()
    seed_green = 100_000 * EIGHTEEN_DECIMALS
    swap_amount = 500_000 * EIGHTEEN_DECIMALS
    live_green.mint(
        bob, seed_green + swap_amount, sender=live_hq.getAddr(13)
    )
    usdc_token.transfer(bob, seed_usdc, sender=WHALES[fork]["usdc"])
    usdc_token.approve(pool, seed_usdc, sender=bob)
    live_green.approve(pool, seed_green, sender=bob)
    minted_lp = pool.add_liquidity([seed_usdc, seed_green], 0, bob, sender=bob)
    lp_balance = minted_lp // 100
    assert lp_balance > 0
    pool.transfer(endaoment_funds, lp_balance, sender=bob)

    live_green.approve(pool, swap_amount, sender=bob)
    pool.exchange(1, 0, swap_amount, 0, bob, sender=bob)

    aid = curve_prices.setGreenRefPoolConfig(
        production_pool_address,
        10,
        50_00,
        0,
        HUNDRED_PERCENT,
        2_000_000 * EIGHTEEN_DECIMALS,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    data = curve_prices.getGreenStabilizerConfig()
    assert data.pool == production_pool_address
    assert data.greenRatio > HUNDRED_PERCENT // 2

    pool_debt = 1_000_000 * EIGHTEEN_DECIMALS
    ledger.updateGreenPoolDebt(pool.address, pool_debt, True, sender=endaoment.address)
    total_pool_balance = data.greenBalance * HUNDRED_PERCENT // data.greenRatio
    target_balance = total_pool_balance // 2
    desired_weighted = (data.greenBalance - target_balance) * 2
    policy_allowance = max(
        pool_debt,
        data.greenBalance * lp_balance // pool.totalSupply(),
    )
    desired_uncapped = min(desired_weighted, policy_allowance)
    executable_cap = _max_executable_green(
        pool, data.greenIndex, desired_uncapped, lp_balance
    )
    requested = endaoment.getGreenAmountToRemoveInStabilizer()
    cap_amounts = [0, 0]
    cap_amounts[data.greenIndex] = executable_cap
    cap_quote = pool.calc_token_amount(cap_amounts, False)
    above_amounts = list(cap_amounts)
    above_amounts[data.greenIndex] += 1
    above_quote = pool.calc_token_amount(above_amounts, False)
    pool_green_before = live_green.balanceOf(pool)

    assert requested == executable_cap > 0
    assert desired_uncapped > executable_cap
    assert cap_quote + 1 <= lp_balance
    assert above_quote + 1 > lp_balance
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    stabilize_computation = endaoment._computation
    stabilize_gas = stabilize_computation.get_gas_used()
    quote_calls = _count_selector_calls(
        stabilize_computation,
        CALC_TOKEN_AMOUNT_SELECTOR,
    )
    assert stabilize_gas > 0
    assert 0 < quote_calls <= 257
    assert stabilize_gas <= STABILIZER_KEEPER_GAS_BUDGET

    log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
    actual_lp_burned = lp_balance - pool.balanceOf(endaoment_funds)
    actual_green_received = pool_green_before - live_green.balanceOf(pool)
    assert actual_lp_burned == cap_quote + 1 == log.lpBurned
    assert actual_green_received == executable_cap == log.greenAmountRemoved
    assert log.debtRepaid == executable_cap
    assert ledger.greenPoolDebt(pool.address) == pool_debt - executable_cap
    assert pool.balanceOf(endaoment.address) == 0
    assert live_green.balanceOf(endaoment.address) == 0

    print(
        "SC19_BASE_PRODUCTION_DIRECT",
        json.dumps(
            {
                "chain_id": 8453,
                "fork_block": FORKS[fork]["block"],
                "production_pool": str(production_pool_address),
                "production_runtime_sha256": hashlib.sha256(
                    boa.env.get_code(production_pool_address)
                ).hexdigest(),
                "pool_balances": list(pool.get_balances()),
                "pool_debt": pool_debt,
                "lp_balance": lp_balance,
                "desired_weighted_adjustment": desired_weighted,
                "policy_allowance": policy_allowance,
                "desired_uncapped_removal": desired_uncapped,
                "executable_cap": executable_cap,
                "quote_at_cap": cap_quote,
                "quote_at_cap_plus_one": above_quote,
                "actual_green_received": actual_green_received,
                "actual_lp_burned": actual_lp_burned,
                "debt_repaid": log.debtRepaid,
                "stabilize_gas": stabilize_gas,
                "quote_calls": quote_calls,
            },
            sort_keys=True,
        ),
    )


# These boundary regressions intentionally use the real Base Curve factory and
# production Endaoment entry points, so they remain in the Base fork lane.
@pytest.base
def test_endao_stabilizer_add_green_rounded_zero_ratio(
    setGreenRefConfig,
    endaoment,
    curve_prices,
    addSeedGreenLiq,
    usdc_token,
    deployed_green_pool,
):
    green_amount = 1 * EIGHTEEN_DECIMALS
    initial_usdc_amount = 9_999 * (10 ** usdc_token.decimals())
    rounding_usdc_amount = 1 * (10 ** usdc_token.decimals())
    addSeedGreenLiq(initial_usdc_amount, green_amount)
    setGreenRefConfig(
        _stabilizerAdjustWeight=50_00,
        _stabilizerMaxPoolDebt=10_000 * EIGHTEEN_DECIMALS,
    )
    addSeedGreenLiq(rounding_usdc_amount, 0)

    green_pool = boa.env.lookup_contract(deployed_green_pool)
    pool_balances = green_pool.get_balances()
    green_balance, green_ratio = curve_prices.getCurvePoolData()
    normalized_total_pool_balance = green_balance + pool_balances[0] * (
        10 ** (18 - usdc_token.decimals())
    )
    assert curve_prices.greenRefPoolConfig().pool == deployed_green_pool
    assert green_balance == pool_balances[1] != 0
    assert green_balance * HUNDRED_PERCENT < normalized_total_pool_balance
    assert green_ratio == 0
    assert endaoment.getGreenAmountToAddInStabilizer() == 0


@pytest.base
def test_endao_stabilizer_action_rounded_zero_ratio_is_noop(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    usdc_token,
    green_token,
    whale,
    bob,
    switchboard_delta,
    deployed_green_pool,
    ledger,
):
    green_amount = 1 * EIGHTEEN_DECIMALS
    initial_usdc_amount = 9_999 * (10 ** usdc_token.decimals())
    rounding_usdc_amount = 1 * (10 ** usdc_token.decimals())
    addSeedGreenLiq(initial_usdc_amount, green_amount)
    setGreenRefConfig(
        _stabilizerAdjustWeight=50_00,
        _stabilizerMaxPoolDebt=10_000 * EIGHTEEN_DECIMALS,
    )
    addSeedGreenLiq(rounding_usdc_amount, 0)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    staged_green = 7 * EIGHTEEN_DECIMALS
    staged_lp = green_pool.balanceOf(bob) // 2
    assert staged_lp != 0
    green_token.transfer(endaoment_funds, staged_green, sender=whale)
    green_pool.transfer(endaoment_funds, staged_lp, sender=bob)

    pool_balances = green_pool.get_balances()
    green_balance, green_ratio = curve_prices.getCurvePoolData()
    normalized_total_pool_balance = green_balance + pool_balances[0] * (
        10 ** (18 - usdc_token.decimals())
    )
    assert green_balance == pool_balances[1] != 0
    assert green_balance * HUNDRED_PERCENT < normalized_total_pool_balance
    assert green_ratio == 0

    pool_debt_before = ledger.greenPoolDebt(green_pool)
    green_supply_before = green_token.totalSupply()
    pool_balances_before = green_pool.get_balances()
    funds_green_before = green_token.balanceOf(endaoment_funds)
    funds_lp_before = green_pool.balanceOf(endaoment_funds)
    endaoment_green_before = green_token.balanceOf(endaoment)
    endaoment_lp_before = green_pool.balanceOf(endaoment)

    assert not endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    assert ledger.greenPoolDebt(green_pool) == pool_debt_before
    assert green_token.totalSupply() == green_supply_before
    assert green_pool.get_balances() == pool_balances_before
    assert green_token.balanceOf(endaoment_funds) == funds_green_before
    assert green_pool.balanceOf(endaoment_funds) == funds_lp_before
    assert green_token.balanceOf(endaoment) == endaoment_green_before == 0
    assert green_pool.balanceOf(endaoment) == endaoment_lp_before == 0
    assert not filter_logs(endaoment, "StabilizerPoolLiqAdded")
    assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")


@pytest.base
def test_endao_stabilizer_add_green_smallest_nonzero_ratio(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    usdc_token,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
):
    green_amount = 1 * EIGHTEEN_DECIMALS
    usdc_amount = 9_999 * (10 ** usdc_token.decimals())
    max_pool_debt = 10_000 * EIGHTEEN_DECIMALS
    leftover_green = 1_000 * EIGHTEEN_DECIMALS
    addSeedGreenLiq(usdc_amount, green_amount)
    setGreenRefConfig(
        _stabilizerAdjustWeight=50_00,
        _stabilizerMaxPoolDebt=max_pool_debt,
    )
    green_token.transfer(endaoment_funds, leftover_green, sender=whale)

    data = curve_prices.getGreenStabilizerConfig()
    pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    actual_leftover_green = green_token.balanceOf(endaoment_funds)
    assert data.greenRatio == 1
    assert data.stabilizerMaxPoolDebt > pool_debt

    total_pool_balance = data.greenBalance * HUNDRED_PERCENT // data.greenRatio
    target_balance = total_pool_balance // 2
    green_adjust_full = (target_balance - data.greenBalance) * 2
    green_adjust_weighted = (
        green_adjust_full * data.stabilizerAdjustWeight // HUNDRED_PERCENT
    )
    debt_avail = data.stabilizerMaxPoolDebt - pool_debt
    expected = min(green_adjust_weighted, debt_avail + actual_leftover_green)

    assert expected == 4_999 * EIGHTEEN_DECIMALS
    assert endaoment.getGreenAmountToAddInStabilizer() == expected


@pytest.base
def test_endao_stabilizer_add_green_fifty_percent_boundary(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
):
    addSeedGreenLiq()
    max_pool_debt = 50_000 * EIGHTEEN_DECIMALS
    leftover_green = 1_000 * EIGHTEEN_DECIMALS
    setGreenRefConfig(
        _stabilizerAdjustWeight=100_00,
        _stabilizerMaxPoolDebt=max_pool_debt,
    )
    green_token.transfer(endaoment_funds, leftover_green, sender=whale)

    data = curve_prices.getGreenStabilizerConfig()
    pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    # At exactly 50%, the downstream target math also resolves to zero. This
    # test documents the explicit API boundary and proves no capacity cap is
    # independently forcing the result.
    assert data.greenRatio == 50_00
    assert data.stabilizerAdjustWeight != 0
    assert data.stabilizerMaxPoolDebt > pool_debt
    assert data.stabilizerMaxPoolDebt - pool_debt > 0
    assert green_token.balanceOf(endaoment_funds) == leftover_green
    assert endaoment.getGreenAmountToAddInStabilizer() == 0


@pytest.base
def test_endao_stabilizer_add_green(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    deployed_green_pool,
    ledger,
    green_token,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # imablance pool, has more usdc
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)

    # check the imbalanced pool state
    na, new_ratio = curve_prices.getCurvePoolData()
    _test(new_ratio, 25_00)

    # test expected green amount using the configured debt and leftover capacity
    data = curve_prices.getGreenStabilizerConfig()
    pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    leftover_green = green_token.balanceOf(endaoment_funds)
    assert 0 < data.greenRatio < 50_00
    assert data.stabilizerMaxPoolDebt > pool_debt
    debt_avail = data.stabilizerMaxPoolDebt - pool_debt
    total_pool_balance = data.greenBalance * HUNDRED_PERCENT // data.greenRatio
    target_balance = total_pool_balance // 2
    green_adjust_full = (target_balance - data.greenBalance) * 2
    green_adjust_weighted = (
        green_adjust_full * data.stabilizerAdjustWeight // HUNDRED_PERCENT
    )
    expected_green_amount = min(
        green_adjust_weighted,
        debt_avail + leftover_green,
    )
    assert endaoment.getGreenAmountToAddInStabilizer() == expected_green_amount
    _test(expected_green_amount, 10_000 * EIGHTEEN_DECIMALS)

    # stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    assert log.pool == green_pool.address
    _test(log.greenAmountAdded, 10_000 * EIGHTEEN_DECIMALS) # 100% weight
    assert log.lpReceived != 0
    assert log.poolDebtAdded == log.greenAmountAdded

    # test ledger pool debt
    assert ledger.greenPoolDebt(green_pool) == log.poolDebtAdded

    # test lp balance
    assert green_pool.balanceOf(endaoment_funds) == log.lpReceived


@pytest.base
def test_endao_stabilizer_remove_green(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    swapGreenForUsdc,
    _test,
    switchboard_delta,
    green_token,
    deployed_green_pool,
    bob,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # move seed lp into endaoment_funds
    green_pool.transfer(endaoment_funds, green_pool.balanceOf(bob), sender=bob)
    pre_lp = green_pool.balanceOf(endaoment_funds)

    # imablance pool, has more green
    large_green_swap = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)

    # check the imbalanced pool state
    na, new_ratio = curve_prices.getCurvePoolData()
    _test(new_ratio, 75_00)

    # test expected green amount
    expected_green_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    _test(expected_green_amount, 5_000 * EIGHTEEN_DECIMALS) # 50% weight

    # stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
    assert log.pool == green_pool.address
    _test(log.greenAmountRemoved, 5_000 * EIGHTEEN_DECIMALS) # 50% weight
    assert log.lpBurned != 0
    assert log.debtRepaid == 0

    # test balances
    assert green_pool.balanceOf(endaoment_funds) == pre_lp - log.lpBurned
    assert green_token.balanceOf(endaoment_funds) == log.greenAmountRemoved


@pytest.base
def test_endao_stabilizer_balanced_pool(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    switchboard_delta,
):
    # Balanced pool should not trigger stabilization
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Pool is already balanced (50/50), so stabilizer should return False
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result # No adjustment needed


@pytest.base
def test_endao_stabilizer_no_config(
    endaoment,
    switchboard_delta,
):
    # Should return False when no stabilizer config is set
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result


@pytest.base
def test_endao_stabilizer_different_weights(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
):
    # Test with 25% weight
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=25_00)
    
    # Create imbalance
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Test expected green amount with 25% weight
    expected_green_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(expected_green_amount, 2_500 * EIGHTEEN_DECIMALS) # 25% of 10k
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, 2_500 * EIGHTEEN_DECIMALS) # 25% weight


@pytest.base
def test_endao_stabilizer_max_debt_reached(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    ledger,
    deployed_green_pool,
):
    # Test when max pool debt is reached
    addSeedGreenLiq()
    max_debt = 5_000 * EIGHTEEN_DECIMALS  # Set low max debt
    setGreenRefConfig(_stabilizerAdjustWeight=100_00, _stabilizerMaxPoolDebt=max_debt)
    
    # Create imbalance
    large_usdc_swap = 6_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Expected green should be limited by max debt
    expected_green_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(expected_green_amount, max_debt) # Limited by max debt
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, max_debt)
    
    # Pool debt should equal max debt
    assert ledger.greenPoolDebt(deployed_green_pool) == max_debt


@pytest.base
def test_endao_stabilizer_with_leftover_green(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
):
    # Test when endaoment already has green tokens
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Give endaoment some green tokens
    leftover_green = 3_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, leftover_green, sender=whale)
    
    # Create imbalance
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, 10_000 * EIGHTEEN_DECIMALS)
    
    # Pool debt should only be the newly minted amount
    expected_new_debt = 10_000 * EIGHTEEN_DECIMALS - leftover_green
    _test(log.poolDebtAdded, expected_new_debt)
    assert ledger.greenPoolDebt(deployed_green_pool) == log.poolDebtAdded


@pytest.base
def test_endao_stabilizer_remove_with_debt_repayment(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapGreenForUsdc,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    deployed_green_pool,
    bob,
    ledger,
):
    # First create some pool debt by adding liquidity
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create imbalance and add liquidity to create debt
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    # Check debt was created
    pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert pool_debt > 0
    
    # Move all LP tokens to endaoment
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    green_pool.transfer(endaoment, green_pool.balanceOf(bob), sender=bob)
    
    # Now create opposite imbalance (more green)
    large_green_swap = 8_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    # Set different weight for removal
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Stabilize (should remove liquidity and repay debt)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
    assert log.debtRepaid > 0
    assert log.greenAmountRemoved > 0
    
    # Pool debt should be reduced by exactly the amount repaid
    new_pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    expected_new_debt = pool_debt - log.debtRepaid
    assert new_pool_debt == expected_new_debt
    assert new_pool_debt < pool_debt  # Additional safety check


@pytest.base
def test_endao_stabilizer_no_lp_tokens_to_remove(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapGreenForUsdc,
    switchboard_delta,
):
    # Test when endaoment has no LP tokens but pool needs rebalancing
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Create imbalance (more green)
    large_green_swap = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    # Endaoment has no LP tokens, so should return False
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result


@pytest.base
def test_endao_stabilizer_view_functions(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    addSeedGreenLiq,
    swapUsdcForGreen,
    swapGreenForUsdc,
    usdc_token,
    _test,
    deployed_green_pool,
    bob,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=75_00)
    
    # Test add scenario
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(add_amount, 7_500 * EIGHTEEN_DECIMALS) # 75% of 10k
    
    # Should return 0 for remove in this scenario
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount == 0
    
    # Now test remove scenario
    # First rebalance pool and give endaoment_funds LP tokens
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    green_pool.transfer(endaoment_funds, green_pool.balanceOf(bob), sender=bob)
    
    # Swap back to balance, then create opposite imbalance
    large_green_swap = 8_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount > 0
    
    # Should return 0 for add in this scenario
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    assert add_amount == 0


@pytest.base
def test_endao_stabilizer_no_config_view_functions(
    endaoment,
):
    # View functions should return 0 when no config is set
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    assert add_amount == 0
    
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount == 0


@pytest.base
def test_endao_stabilizer_permissions(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    alice,
):
    # Test that only switchboard can call stabilizer
    addSeedGreenLiq()
    setGreenRefConfig()
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.stabilizeGreenRefPool(sender=alice)


@pytest.base
def test_endao_stabilizer_paused_contract(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    switchboard_delta,
):
    # Test that stabilizer respects contract pause
    addSeedGreenLiq()
    setGreenRefConfig()
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)


#############
# Pool Debt #
#############


@pytest.base
def test_endao_repay_pool_debt_directly(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
    _test,
):
    # Test the repayPoolDebt function directly
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create debt by stabilizing an imbalanced pool
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    # Check debt was created
    initial_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert initial_debt > 0
    
    # Give endaoment_funds extra green for repayment
    extra_green = 5_000 * EIGHTEEN_DECIMALS  # Enough to cover any repayment
    green_token.transfer(endaoment_funds, extra_green, sender=whale)
    green_balance_before = green_token.balanceOf(endaoment_funds)
    
    # Repay partial debt (request more than we plan to actually repay)
    requested_repay = min(3_000 * EIGHTEEN_DECIMALS, initial_debt)
    assert endaoment.repayPoolDebt(deployed_green_pool, requested_repay, sender=switchboard_delta.address)

    # Check event was emitted
    log = filter_logs(endaoment, "PoolDebtRepaid")[0]
    assert log.pool == deployed_green_pool
    actual_repay_amount = log.amount  # This is what was actually repaid
    
    # The actual repay amount should be the minimum of requested, available green, and debt
    expected_repay = min(requested_repay, green_balance_before, initial_debt)
    _test(log.amount, expected_repay)

    # Check debt was reduced by exactly the actual repay amount
    final_debt = ledger.greenPoolDebt(deployed_green_pool)
    expected_debt = initial_debt - actual_repay_amount
    assert final_debt == expected_debt

    # Check green was burned (balance should decrease)
    green_balance_after = green_token.balanceOf(endaoment_funds)
    green_burned = green_balance_before - green_balance_after
    _test(green_burned, actual_repay_amount)


@pytest.base 
def test_endao_repay_pool_debt_max_amount(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
    _test,
):
    # Test repaying more than the debt (should only repay what's owed)
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create debt
    large_usdc_swap = 3_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    initial_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert initial_debt > 0
    
    # Give endaoment way more green than needed
    excess_green = initial_debt + (5_000 * EIGHTEEN_DECIMALS)
    green_token.transfer(endaoment, excess_green, sender=whale)
    
    # Try to repay more than the debt
    huge_repay_amount = initial_debt * 2
    assert endaoment.repayPoolDebt(deployed_green_pool, huge_repay_amount, sender=switchboard_delta.address)

    # Check that only the actual debt amount was burned
    log = filter_logs(endaoment, "PoolDebtRepaid")[0]
    _test(log.amount, initial_debt)  # Should equal initial debt, not huge_repay_amount

    # Should only repay the actual debt amount
    final_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert final_debt == 0  # All debt should be repaid


#####################
# Partner Liquidity #
#####################


def test_endao_mint_partner_liquidity_basic(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    green_token,
    mock_price_source,
    _test,
):
    # Test basic mintPartnerLiquidity functionality
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    pre_bal = alpha_token.balanceOf(partner)
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, amount)
    
    # Check balances
    assert alpha_token.balanceOf(endaoment_funds) == amount
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert alpha_token.balanceOf(partner) == pre_bal - amount


def test_endao_mint_partner_liquidity_max_amount(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    green_token,
    _test,
    mock_price_source,
):
    # Test mintPartnerLiquidity with max_value(uint256)
    partner = alpha_token_whale
    asset = alpha_token
    partner_balance = alpha_token.balanceOf(partner)
    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, partner_balance, sender=partner)
    
    # Mint partner liquidity with max amount
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.partnerAmount, partner_balance)
    _test(log.greenMinted, green_minted)
    _test(green_minted, partner_balance * 2)
    
    # Check balances
    assert alpha_token.balanceOf(endaoment_funds) == partner_balance
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert alpha_token.balanceOf(partner) == 0  # All transferred


def test_endao_mint_partner_liquidity_different_decimals(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    charlie_token,  # 6 decimals
    charlie_token_whale,
    green_token,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity with tokens of different decimals
    partner = charlie_token_whale
    asset = charlie_token
    amount = 1_000 * (10 ** charlie_token.decimals())  # 1M tokens with 6 decimals
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    pre_bal = charlie_token.balanceOf(partner)
    charlie_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, 1000 * EIGHTEEN_DECIMALS)
    
    # Check balances
    assert charlie_token.balanceOf(endaoment_funds) == amount
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert charlie_token.balanceOf(partner) == pre_bal - amount


def test_endao_mint_partner_liquidity_permissions(
    endaoment,
    alpha_token,
    alpha_token_whale,
    alice,
):
    # Test that only switchboard can call mintPartnerLiquidity
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=alice)


def test_endao_mint_partner_liquidity_paused_contract(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test that mintPartnerLiquidity respects contract pause
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_no_approval(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test mintPartnerLiquidity without approval
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # No approval given - should revert
    with boa.reverts("transfer failed"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_insufficient_approval(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test mintPartnerLiquidity with insufficient approval
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    insufficient_approval = amount // 2
    
    # Approve less than requested amount
    alpha_token.approve(endaoment, insufficient_approval, sender=partner)
    
    # Should revert due to insufficient approval
    with boa.reverts("transfer failed"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_zero_balance(
    endaoment,
    switchboard_delta,
    alpha_token,
    alice,  # alice has no alpha tokens
):
    # Test mintPartnerLiquidity with partner having zero balance
    partner = alice
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Should revert due to zero balance
    with boa.reverts("no asset to add"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_usd_value_calculation(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    price_desk,
    mock_price_source,
    _test,
):
    # Test that the USD value calculation is correct
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Set a price for the asset
    price_per_token = 2 * EIGHTEEN_DECIMALS  # $2 per token
    mock_price_source.setPrice(alpha_token, price_per_token)
    
    # Get expected USD value from price desk
    expected_usd_value = price_desk.getUsdValue(asset, amount, True)
    assert expected_usd_value > 0
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)

    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.greenMinted, expected_usd_value)

    # Check that green minted equals USD value
    _test(green_minted, expected_usd_value)


@pytest.base
def test_endao_add_partner_liquidity_basic(
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    _test,
    fork,
    alice,
    usdc_token,
    ledger,
):
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # usdc
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(alice, usdc_amount, sender=usdc_whale)

    # setup
    partner = alice
    asset = usdc_token
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Approve endaoment to spend partner's tokens
    usdc_token.approve(endaoment, amount, sender=partner)

    # Mint partner liquidity
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, partner, asset, amount, 0, green_pool, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    assert log.lpBalance == liquidityAdded

    _test(log.partnerAmount, liqAmountA)
    _test(liqAmountA, amount)
    _test(log.greenAmount, liqAmountB)
    _test(liqAmountB, 1_000 * EIGHTEEN_DECIMALS)
    
    # Check balances
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    _test(log.lpBalance // 2, green_pool.balanceOf(partner))
    _test(log.lpBalance // 2, green_pool.balanceOf(endaoment_funds))

    _test(ledger.greenPoolDebt(green_pool), 1_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_partner_liquidity_preserves_existing_base_pool_reserves(
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    bob,
    addSeedGreenLiq,
):
    """Only LP minted by this Base-fork action may be split with its partner."""
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    addSeedGreenLiq()

    reserve_lp = green_pool.balanceOf(bob)
    assert reserve_lp != 0
    green_pool.transfer(endaoment_funds, reserve_lp, sender=bob)

    partner = boa.env.generate_address()
    amount = 10_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(partner, amount, sender=WHALES[fork]["usdc"])
    usdc_token.approve(endaoment, amount, sender=partner)

    lp_received, _, _ = endaoment.addPartnerLiquidity(
        10,
        green_pool,
        partner,
        usdc_token,
        amount,
        0,
        green_pool,
        sender=switchboard_delta.address,
    )

    partner_share = lp_received // 2
    vault_share = lp_received - partner_share
    assert green_pool.balanceOf(partner) == partner_share
    assert green_pool.balanceOf(endaoment_funds) == reserve_lp + vault_share
    assert green_pool.balanceOf(endaoment) == 0


@pytest.base
def test_endao_add_partner_liquidity_permissions(
    endaoment,
    deployed_green_pool,
    alice,
    bob,
    usdc_token,
    fork,
):
    # Test that only switchboard can call addPartnerLiquidity
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Setup partner with tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, green_pool, sender=bob)


@pytest.base
def test_endao_add_partner_liquidity_paused_contract(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test that addPartnerLiquidity respects contract pause
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Setup partner with tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_no_approval(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test addPartnerLiquidity without token approval
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens but no approval
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    
    # Should revert due to no approval
    with boa.reverts("transfer failed"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_insufficient_balance(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
):
    # Test addPartnerLiquidity when partner has insufficient balance
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Partner has no tokens but gives approval
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_max_amount(
    addSeedGreenLiq,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity with max_value(uint256)
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    partner_balance = 5_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens
    usdc_token.transfer(alice, partner_balance, sender=usdc_whale)
    usdc_token.approve(endaoment, partner_balance, sender=alice)
    
    # Add partner liquidity with max amount (should use all partner's balance)
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, MAX_UINT256, 0, green_pool, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, partner_balance)
    _test(log.greenAmount, 5_000 * EIGHTEEN_DECIMALS)
    
    # Check partner has no tokens left
    assert usdc_token.balanceOf(alice) == 0
    
    # Check pool debt was added
    _test(ledger.greenPoolDebt(green_pool), 5_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_min_lp_amount(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test addPartnerLiquidity with minimum LP amount requirement
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Set unrealistically high minimum LP amount (should fail)
    unrealistic_min_lp = 1_000_000 * EIGHTEEN_DECIMALS
    
    # Should revert due to insufficient LP amount received
    with boa.reverts():  # The exact error depends on the lego implementation
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, unrealistic_min_lp, green_pool, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_lp_sharing(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
    _test,
):
    # Test that LP tokens are properly shared between partner and endaoment_funds
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 2_000 * (10 ** usdc_token.decimals())

    # Record initial LP balances
    initial_partner_lp = green_pool.balanceOf(alice)
    initial_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Give partner tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Add partner liquidity
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address)
    
    # Check LP tokens were shared 50/50
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    total_lp_received = log.lpBalance

    partner_lp_received = green_pool.balanceOf(alice) - initial_partner_lp
    endaoment_funds_lp_received = green_pool.balanceOf(endaoment_funds) - initial_endaoment_funds_lp

    # Each should get half of the LP tokens
    _test(partner_lp_received, total_lp_received // 2)
    _test(endaoment_funds_lp_received, total_lp_received // 2)

    # Total should add up (accounting for potential rounding)
    assert partner_lp_received + endaoment_funds_lp_received >= total_lp_received - 1
    assert partner_lp_received + endaoment_funds_lp_received <= total_lp_received


@pytest.base
def test_endao_add_partner_liquidity_multiple_partners(
    addSeedGreenLiq,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    bob,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test multiple partners adding liquidity sequentially
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount1 = 1_000 * (10 ** usdc_token.decimals())
    amount2 = 1_500 * (10 ** usdc_token.decimals())
    
    # First partner
    usdc_token.transfer(alice, amount1, sender=usdc_whale)
    usdc_token.approve(endaoment, amount1, sender=alice)
    
    liquidityAdded1, liqAmountA1, liqAmountB1 = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount1, 0, green_pool, sender=switchboard_delta.address)
    
    # Second partner
    usdc_token.transfer(bob, amount2, sender=usdc_whale)
    usdc_token.approve(endaoment, amount2, sender=bob)
    
    liquidityAdded2, liqAmountA2, liqAmountB2 = endaoment.addPartnerLiquidity(10, green_pool, bob, usdc_token, amount2, 0, green_pool, sender=switchboard_delta.address)
    
    # Verify both operations succeeded by checking that they returned valid results
    assert liquidityAdded1 > 0
    assert liquidityAdded2 > 0
    assert liqAmountA1 == amount1
    assert liqAmountA2 == amount2
    assert liqAmountB1 > 0  # Green tokens minted
    assert liqAmountB2 > 0  # Green tokens minted
    
    # Check total pool debt
    total_expected_debt = 1_000 * EIGHTEEN_DECIMALS + 1_500 * EIGHTEEN_DECIMALS
    _test(ledger.greenPoolDebt(green_pool), total_expected_debt)
    
    # Check both partners received LP tokens
    assert green_pool.balanceOf(alice) > 0
    assert green_pool.balanceOf(bob) > 0


@pytest.base
def test_endao_add_partner_liquidity_asset_price_validation(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    alpha_token,  # Use alpha_token which doesn't have a price by default
    alpha_token_whale,
):
    # Test that addPartnerLiquidity validates asset has a price
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Give partner tokens but don't set price (getUsdValue will return 0)
    alpha_token.transfer(alice, amount, sender=alpha_token_whale)
    alpha_token.approve(endaoment, amount, sender=alice)
    
    # Should revert due to invalid asset (no USD value)
    with boa.reverts("invalid asset"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, alpha_token, amount, 0, green_pool, sender=switchboard_delta.address)


##################################
# Partner Liquidity - Self Tests #
##################################


@pytest.base
def test_endao_mint_partner_liquidity_self_as_partner(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    usdc_token,
    green_token,
    fork,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity where partner is Endaoment itself
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    mock_price_source.setPrice(usdc_token, 1 * EIGHTEEN_DECIMALS)

    # Transfer funds into Endaoment before calling it
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)

    pre_usdc_balance = usdc_token.balanceOf(endaoment)
    pre_green_balance = green_token.balanceOf(endaoment_funds)

    # Mint partner liquidity with endaoment as partner
    green_minted = endaoment.mintPartnerLiquidity(endaoment, usdc_token, amount, sender=switchboard_delta.address)

    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == endaoment.address
    assert log.asset == usdc_token.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, amount * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals()))

    # Check balances - USDC stays in endaoment, green goes to endaoment_funds
    assert usdc_token.balanceOf(endaoment) == pre_usdc_balance  # No transfer needed
    assert green_token.balanceOf(endaoment_funds) == pre_green_balance + green_minted


@pytest.base
def test_endao_mint_partner_liquidity_self_max_amount(
    endaoment,
    switchboard_delta,
    usdc_token,
    fork,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity with max amount where partner is Endaoment itself
    usdc_whale = WHALES[fork]["usdc"]
    amount = 2_500 * (10 ** usdc_token.decimals())
    mock_price_source.setPrice(usdc_token, 1 * EIGHTEEN_DECIMALS)

    # Transfer funds into Endaoment
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    endaoment_balance = usdc_token.balanceOf(endaoment)
    
    # Mint partner liquidity with max amount
    green_minted = endaoment.mintPartnerLiquidity(endaoment, usdc_token, sender=switchboard_delta.address)
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.partnerAmount, endaoment_balance)
    _test(log.greenMinted, green_minted)
    
    # Check all USDC balance was used
    expected_green = endaoment_balance * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals())
    _test(green_minted, expected_green)


@pytest.base
def test_endao_mint_partner_liquidity_self_insufficient_balance(
    endaoment,
    switchboard_delta,
    usdc_token,
):
    # Test mintPartnerLiquidity where Endaoment has insufficient balance
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Don't transfer any funds to Endaoment
    assert usdc_token.balanceOf(endaoment) == 0
    
    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.mintPartnerLiquidity(endaoment, usdc_token, amount, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_self_as_partner(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity where partner is Endaoment itself
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment before calling it
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with endaoment as partner
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address
    )
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    assert log.partner == endaoment.address
    assert log.asset == usdc_token.address
    assert log.lpBalance == liquidityAdded
    _test(log.partnerAmount, amount)
    _test(log.greenAmount, 1_000 * EIGHTEEN_DECIMALS)
    
    # Check balances - all assets should be consumed, all LP should go to endaoment_funds
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    # Endaoment_funds should get ALL the LP tokens (not split since partner is self)
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Check pool debt was added
    _test(ledger.greenPoolDebt(green_pool), 1_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_max_amount(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity with max amount where partner is Endaoment itself
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 3_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    endaoment_balance = usdc_token.balanceOf(endaoment)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with max amount
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, MAX_UINT256, 0, green_pool, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, endaoment_balance)
    _test(log.greenAmount, 3_000 * EIGHTEEN_DECIMALS)

    # All LP tokens should go to endaoment_funds
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Check pool debt
    _test(ledger.greenPoolDebt(green_pool), 3_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_with_existing_green(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    # Test addPartnerLiquidity where EndaomentFunds already has green tokens
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 1_000 * (10 ** usdc_token.decimals())
    green_amount = 500 * EIGHTEEN_DECIMALS

    # Transfer USDC to Endaoment and existing Green to EndaomentFunds
    usdc_token.transfer(endaoment, usdc_amount, sender=usdc_whale)
    green_token.transfer(endaoment_funds, green_amount, sender=whale)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with endaoment as partner
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, usdc_amount)
    _test(log.greenAmount, 1_000 * EIGHTEEN_DECIMALS)  # Full amount needed

    # Check balances
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    # All LP tokens should go to endaoment_funds
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Pool debt should only be for newly minted green (1000 - 500 = 500)
    expected_new_debt = 1_000 * EIGHTEEN_DECIMALS - green_amount
    _test(ledger.greenPoolDebt(green_pool), expected_new_debt)


@pytest.base
def test_endao_add_partner_liquidity_self_insufficient_balance(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
):
    # Test addPartnerLiquidity where Endaoment has insufficient balance
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Don't transfer any funds to Endaoment
    assert usdc_token.balanceOf(endaoment) == 0

    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.addPartnerLiquidity(10, green_pool, endaoment, usdc_token, amount, 0, green_pool, sender=switchboard_delta.address)


###################################
# Profit Invariant Tests          #
###################################


def test_green_stabilizer_underwater_worsening_reverts_atomically(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    initial_lp = 100 * EIGHTEEN_DECIMALS
    initial_debt = 200 * EIGHTEEN_DECIMALS
    green_added = 20 * EIGHTEEN_DECIMALS
    lp_minted = 10 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        pool = _install_stabilizer_transition_harness(
            curve_prices,
            green_token,
            lp_minted,
        )
        pool.seedLp(endaoment_funds, initial_lp)
        ledger.updateGreenPoolDebt(
            pool.address,
            initial_debt,
            True,
            sender=endaoment.address,
        )

        # The public view measures EndaomentFunds before the action. The internal
        # snapshot measures the same assets after _prepareEndaomentFunds pulls them.
        assert pool.balanceOf(endaoment_funds) == initial_lp
        assert pool.balanceOf(endaoment) == 0
        assert green_token.balanceOf(endaoment_funds) == 0
        assert green_token.balanceOf(endaoment) == 0
        initial_is_deficit, initial_position = _signed_lp_position(
            pool.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment_funds),
            ledger.greenPoolDebt(pool),
            pool.get_virtual_price(),
        )
        assert initial_is_deficit
        assert initial_position == 100 * EIGHTEEN_DECIMALS
        assert endaoment.calcProfitForStabilizer() == 0
        assert endaoment.getGreenAmountToAddInStabilizer() == green_added

        pre_state = {
            "pool_debt": ledger.greenPoolDebt(pool),
            "green_supply": green_token.totalSupply(),
            "funds_lp": pool.balanceOf(endaoment_funds),
            "endaoment_lp": pool.balanceOf(endaoment),
            "funds_green": green_token.balanceOf(endaoment_funds),
            "endaoment_green": green_token.balanceOf(endaoment),
            "pool_green": green_token.balanceOf(pool),
            "lp_supply": pool.totalSupply(),
            "add_calls": pool.addCallCount(),
        }

        with boa.reverts("stabilizer was not profitable"):
            endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        # Check the reverted computation's log surface before any later contract
        # calls. State equality below remains the independent atomicity evidence.
        assert not filter_logs(endaoment, "StabilizerPoolLiqAdded")
        assert not filter_logs(endaoment, "StabilizerPoolLiqRemoved")

        # Reversion must roll back debt, minting, Curve state, and both custody moves.
        assert ledger.greenPoolDebt(pool) == pre_state["pool_debt"]
        assert green_token.totalSupply() == pre_state["green_supply"]
        assert pool.balanceOf(endaoment_funds) == pre_state["funds_lp"]
        assert pool.balanceOf(endaoment) == pre_state["endaoment_lp"] == 0
        assert green_token.balanceOf(endaoment_funds) == pre_state["funds_green"]
        assert green_token.balanceOf(endaoment) == pre_state["endaoment_green"] == 0
        assert green_token.balanceOf(pool) == pre_state["pool_green"]
        assert pool.totalSupply() == pre_state["lp_supply"]
        assert pool.addCallCount() == pre_state["add_calls"]


@pytest.mark.parametrize(
    "initial_lp,lp_minted,initial_is_deficit,initial_position,"
    "final_is_deficit,final_position",
    [
        (
            100 * EIGHTEEN_DECIMALS,
            20 * EIGHTEEN_DECIMALS,
            True,
            100 * EIGHTEEN_DECIMALS,
            True,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            30 * EIGHTEEN_DECIMALS,
            True,
            100 * EIGHTEEN_DECIMALS,
            True,
            90 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            120 * EIGHTEEN_DECIMALS,
            True,
            100 * EIGHTEEN_DECIMALS,
            False,
            0,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            130 * EIGHTEEN_DECIMALS,
            True,
            100 * EIGHTEEN_DECIMALS,
            False,
            10 * EIGHTEEN_DECIMALS,
        ),
        (
            300 * EIGHTEEN_DECIMALS,
            20 * EIGHTEEN_DECIMALS,
            False,
            100 * EIGHTEEN_DECIMALS,
            False,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            300 * EIGHTEEN_DECIMALS,
            30 * EIGHTEEN_DECIMALS,
            False,
            100 * EIGHTEEN_DECIMALS,
            False,
            110 * EIGHTEEN_DECIMALS,
        ),
    ],
    ids=[
        "same-deficit",
        "smaller-deficit",
        "deficit-to-break-even",
        "deficit-to-surplus",
        "same-surplus",
        "larger-surplus",
    ],
)
def test_green_stabilizer_allows_nonworsening_signed_positions(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
    initial_lp,
    lp_minted,
    initial_is_deficit,
    initial_position,
    final_is_deficit,
    final_position,
):
    initial_debt = 200 * EIGHTEEN_DECIMALS
    green_added = 20 * EIGHTEEN_DECIMALS
    final_debt = initial_debt + green_added
    final_lp = initial_lp + lp_minted

    with boa.env.anchor():
        pool = _seed_stabilizer_transition(
            curve_prices,
            green_token,
            ledger,
            endaoment,
            endaoment_funds,
            initial_lp,
            initial_debt,
            lp_minted,
        )

        # The pre-call public view reads nonempty EndaomentFunds custody. The
        # internal pre-action snapshot will read the same LP after it is pulled.
        assert pool.balanceOf(endaoment_funds) == initial_lp != 0
        assert pool.balanceOf(endaoment) == 0
        assert green_token.balanceOf(endaoment_funds) == 0
        assert green_token.balanceOf(endaoment) == 0
        derived_initial = _signed_lp_position(
            pool.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment_funds),
            ledger.greenPoolDebt(pool),
            pool.get_virtual_price(),
        )
        assert derived_initial == (initial_is_deficit, initial_position)
        expected_initial_profit = 0 if initial_is_deficit else initial_position
        assert endaoment.calcProfitForStabilizer() == expected_initial_profit
        assert endaoment.getGreenAmountToAddInStabilizer() == green_added
        initial_green_supply = green_token.totalSupply()

        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        assert pool.addCallCount() == 1
        assert pool.lastGreenAdded() == green_added
        assert ledger.greenPoolDebt(pool) == final_debt
        assert pool.balanceOf(endaoment) == 0
        assert green_token.balanceOf(endaoment) == 0
        assert pool.balanceOf(endaoment_funds) == final_lp
        assert green_token.balanceOf(endaoment_funds) == 0
        assert green_token.balanceOf(pool) == green_added
        assert green_token.totalSupply() == initial_green_supply + green_added
        derived_final = _signed_lp_position(
            pool.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment_funds),
            ledger.greenPoolDebt(pool),
            pool.get_virtual_price(),
        )
        assert derived_final == (final_is_deficit, final_position)
        expected_final_profit = 0 if final_is_deficit else final_position
        # After success, the public view reads the returned EndaomentFunds custody.
        assert endaoment.calcProfitForStabilizer() == expected_final_profit


@pytest.mark.parametrize(
    "initial_lp,expected_initial,expected_final_is_deficit,expected_final",
    [
        (
            300 * EIGHTEEN_DECIMALS,
            100 * EIGHTEEN_DECIMALS,
            False,
            90 * EIGHTEEN_DECIMALS,
        ),
        (
            205 * EIGHTEEN_DECIMALS,
            5 * EIGHTEEN_DECIMALS,
            True,
            5 * EIGHTEEN_DECIMALS,
        ),
    ],
    ids=["smaller-solvent-position", "solvent-to-deficit"],
)
def test_green_stabilizer_rejects_worsening_solvent_positions(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
    initial_lp,
    expected_initial,
    expected_final_is_deficit,
    expected_final,
):
    initial_debt = 200 * EIGHTEEN_DECIMALS
    green_added = 20 * EIGHTEEN_DECIMALS
    lp_minted = 10 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        pool = _seed_stabilizer_transition(
            curve_prices,
            green_token,
            ledger,
            endaoment,
            endaoment_funds,
            initial_lp,
            initial_debt,
            lp_minted,
        )
        assert pool.balanceOf(endaoment_funds) == initial_lp
        assert pool.balanceOf(endaoment) == 0
        assert _signed_lp_position(
            pool.balanceOf(endaoment_funds),
            green_token.balanceOf(endaoment_funds),
            ledger.greenPoolDebt(pool),
            pool.get_virtual_price(),
        ) == (False, expected_initial)
        assert endaoment.calcProfitForStabilizer() == expected_initial
        assert endaoment.getGreenAmountToAddInStabilizer() == green_added

        hypothetical_final = _signed_lp_position(
            initial_lp + lp_minted,
            0,
            initial_debt + green_added,
            pool.get_virtual_price(),
        )
        assert hypothetical_final == (
            expected_final_is_deficit,
            expected_final,
        )

        with boa.reverts("stabilizer was not profitable"):
            endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        # Query the reverted computation's logs before subsequent state reads.
        assert not filter_logs(endaoment, "StabilizerPoolLiqAdded")

        assert ledger.greenPoolDebt(pool) == initial_debt
        assert pool.balanceOf(endaoment_funds) == initial_lp
        assert pool.balanceOf(endaoment) == 0
        assert green_token.balanceOf(endaoment_funds) == 0
        assert green_token.balanceOf(endaoment) == 0
        assert green_token.balanceOf(pool) == 0
        assert pool.totalSupply() == initial_lp
        assert pool.addCallCount() == 0


@pytest.mark.artifact
def test_calc_profit_for_stabilizer_abi_is_current(endaoment):
    abi = endaoment.abi
    assert abi == json.loads(Path("scripts/abis/Endaoment.json").read_text())
    assert next(
        entry for entry in abi if entry.get("name") == "calcProfitForStabilizer"
    ) == {
        "stateMutability": "view",
        "type": "function",
        "name": "calcProfitForStabilizer",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    }


def test_calc_profit_for_stabilizer_preserves_public_view_semantics(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
):
    cases = [
        # label, LP in EndaomentFunds, GREEN in EndaomentFunds, debt, result,
        # expected signed position
        (
            "underwater",
            100 * EIGHTEEN_DECIMALS,
            0,
            200 * EIGHTEEN_DECIMALS,
            0,
            (True, 100 * EIGHTEEN_DECIMALS),
        ),
        (
            "ordinary-profit",
            300 * EIGHTEEN_DECIMALS,
            0,
            200 * EIGHTEEN_DECIMALS,
            100 * EIGHTEEN_DECIMALS,
            (False, 100 * EIGHTEEN_DECIMALS),
        ),
        (
            "break-even",
            200 * EIGHTEEN_DECIMALS,
            0,
            200 * EIGHTEEN_DECIMALS,
            0,
            (False, 0),
        ),
        (
            "zero-lp-green-surplus",
            0,
            20 * EIGHTEEN_DECIMALS,
            10 * EIGHTEEN_DECIMALS,
            0,
            (False, 10 * EIGHTEEN_DECIMALS),
        ),
    ]

    for label, lp_balance, green_balance, pool_debt, expected, position in cases:
        with boa.env.anchor():
            pool = _seed_stabilizer_transition(
                curve_prices,
                green_token,
                ledger,
                endaoment,
                endaoment_funds,
                lp_balance,
                pool_debt,
                EIGHTEEN_DECIMALS,
                leftover_green=green_balance,
            )
            assert pool.balanceOf(endaoment_funds) == lp_balance, label
            assert green_token.balanceOf(endaoment_funds) == green_balance, label
            assert pool.balanceOf(endaoment) == 0, label
            assert green_token.balanceOf(endaoment) == 0, label
            assert _signed_lp_position(
                pool.balanceOf(endaoment_funds),
                green_token.balanceOf(endaoment_funds),
                ledger.greenPoolDebt(pool),
                pool.get_virtual_price(),
            ) == position, label
            assert endaoment.calcProfitForStabilizer() == expected, label


def test_stabilizer_zero_virtual_price_fails_closed_in_view_and_internal_path(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    leftover_green = 20 * EIGHTEEN_DECIMALS
    pool_debt = 10 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        pool = _seed_stabilizer_transition(
            curve_prices,
            green_token,
            ledger,
            endaoment,
            endaoment_funds,
            0,
            pool_debt,
            20 * EIGHTEEN_DECIMALS,
            leftover_green=leftover_green,
            initial_virtual_price=0,
        )
        assert pool.balanceOf(endaoment_funds) == 0
        assert green_token.balanceOf(endaoment_funds) == leftover_green
        assert pool.balanceOf(endaoment) == 0
        assert green_token.balanceOf(endaoment) == 0

        # The refactor intentionally makes the old zero-LP surplus corner fail
        # closed in both the external report and the internal safety snapshot.
        # Vyper 0.4.3 implements the nonzero division denominator as this
        # compiler clamp, so pin it instead of accepting an arbitrary revert.
        with boa.reverts(compiler="clamp gt 0"):
            endaoment.calcProfitForStabilizer()
        with boa.reverts(compiler="clamp gt 0"):
            endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        assert ledger.greenPoolDebt(pool) == pool_debt
        assert green_token.balanceOf(endaoment_funds) == leftover_green
        assert green_token.balanceOf(endaoment) == 0
        assert green_token.balanceOf(pool) == 0
        assert pool.addCallCount() == 0


def test_green_stabilizer_uses_each_snapshots_current_virtual_price(
    endaoment,
    endaoment_funds,
    curve_prices,
    ledger,
    green_token,
    switchboard_delta,
):
    initial_virtual_price = EIGHTEEN_DECIMALS
    final_virtual_price = 11 * EIGHTEEN_DECIMALS // 10
    initial_lp = 100 * EIGHTEEN_DECIMALS
    initial_debt = 200 * EIGHTEEN_DECIMALS
    green_added = 20 * EIGHTEEN_DECIMALS
    lp_minted = 5 * EIGHTEEN_DECIMALS
    final_lp = initial_lp + lp_minted
    final_debt = initial_debt + green_added

    with boa.env.anchor():
        pool = _seed_stabilizer_transition(
            curve_prices,
            green_token,
            ledger,
            endaoment,
            endaoment_funds,
            initial_lp,
            initial_debt,
            lp_minted,
            initial_virtual_price=initial_virtual_price,
            next_virtual_price=final_virtual_price,
        )
        assert pool.balanceOf(endaoment_funds) == initial_lp
        assert pool.balanceOf(endaoment) == 0
        assert _signed_lp_position(
            initial_lp,
            0,
            initial_debt,
            initial_virtual_price,
        ) == (True, 100 * EIGHTEEN_DECIMALS)
        assert endaoment.calcProfitForStabilizer() == 0
        assert endaoment.getGreenAmountToAddInStabilizer() == green_added

        # At a constant 1e18 virtual price, this action would worsen the deficit.
        assert _signed_lp_position(
            final_lp,
            0,
            final_debt,
            initial_virtual_price,
        ) == (True, 115 * EIGHTEEN_DECIMALS)

        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

        assert pool.get_virtual_price() == final_virtual_price
        assert pool.addCallCount() == 1
        assert pool.lastGreenAdded() == green_added
        assert pool.balanceOf(endaoment) == 0
        assert pool.balanceOf(endaoment_funds) == final_lp
        assert _signed_lp_position(
            final_lp,
            0,
            final_debt,
            final_virtual_price,
        ) == (True, 95 * EIGHTEEN_DECIMALS)

        initial_green_value = (
            initial_lp * initial_virtual_price // EIGHTEEN_DECIMALS
        ) - initial_debt
        final_green_value = (
            final_lp * final_virtual_price // EIGHTEEN_DECIMALS
        ) - final_debt
        assert initial_green_value == -100 * EIGHTEEN_DECIMALS
        assert final_green_value == -(1045 * EIGHTEEN_DECIMALS // 10)
        assert final_green_value < initial_green_value


@pytest.base
def test_green_stabilizer_profit_never_decreases_on_add(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    addSeedGreenLiq,
):
    """Test that profit never decreases when adding green liquidity

    This test verifies a critical invariant: when the stabilizer adds green liquidity
    to rebalance the pool, the net profit position should never decrease.

    Profit is calculated as: (LP balance - LP debt equivalent) + net green balance
    Where LP debt is derived from (pool debt - green balance) / virtual price
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create imbalance by adding USDC to pool (pool will have more USDC than green)
    usdc_add_amount = 50_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, usdc_add_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, usdc_add_amount, sender=endaoment.address)

    amounts = [usdc_add_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Calculate initial profit using the new view function
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_lp = green_pool.balanceOf(endaoment_funds)
    initial_green = green_token.balanceOf(endaoment_funds)
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Run stabilizer to add green
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()
    new_lp = green_pool.balanceOf(endaoment_funds)
    new_green = green_token.balanceOf(endaoment_funds)
    new_debt = ledger.greenPoolDebt(green_pool)

    # CRITICAL INVARIANT: Profit should never decrease when stabilizing
    assert new_profit >= initial_profit, \
        f"Profit decreased! Initial: {initial_profit}, New: {new_profit}, " \
        f"LP change: {new_lp - initial_lp}, Green change: {new_green - initial_green}, " \
        f"Debt change: {new_debt - initial_debt}"


@pytest.base
def test_green_stabilizer_profit_never_decreases_on_remove(
    setGreenRefConfig,
    mock_price_source,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test that profit never decreases when removing green liquidity

    This test verifies that when the stabilizer removes green liquidity (and potentially
    repays debt), the net profit position should never decrease. This is important because
    removing liquidity can repay debt, which should improve or maintain the profit position.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    mock_price_source.setPrice(usdc_token, EIGHTEEN_DECIMALS)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # First create pool debt by adding partner liquidity
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    # Create imbalance by adding green to pool (pool will have more green than USDC)
    green_add_amount = 50_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)

    amounts = [0, green_add_amount]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Calculate initial profit
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_lp = green_pool.balanceOf(endaoment_funds)
    initial_green = green_token.balanceOf(endaoment_funds)
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Run stabilizer to remove green (and potentially repay debt)
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()
    new_lp = green_pool.balanceOf(endaoment_funds)
    new_green = green_token.balanceOf(endaoment_funds)
    new_debt = ledger.greenPoolDebt(green_pool)

    # CRITICAL INVARIANT: Profit should never decrease, especially when repaying debt
    assert new_profit >= initial_profit, \
        f"Profit decreased! Initial: {initial_profit}, New: {new_profit}, " \
        f"LP change: {new_lp - initial_lp}, Green change: {new_green - initial_green}, " \
        f"Debt change: {new_debt - initial_debt}"


@pytest.base
def test_green_stabilizer_profit_with_extreme_imbalance(
    setGreenRefConfig,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    addSeedGreenLiq,
):
    """Test profit invariant with extreme pool imbalance (>80% one side)

    This is a stress test to ensure the profit invariant holds even when the pool
    is severely imbalanced. In extreme conditions, slippage and price impact are high,
    but the stabilizer should still maintain or improve the profit position.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create extreme imbalance
    extreme_amount = 500_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, extreme_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, extreme_amount, sender=endaoment.address)

    amounts = [extreme_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Check pool ratio (index 0 is USDC, index 1 is GREEN in amounts array)
    # But get_balances() might return them differently, so let's calculate correctly
    balances = green_pool.get_balances()
    # Normalize to 18 decimals for comparison
    usdc_normalized = balances[0] * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals())
    green_normalized = balances[1]
    total = usdc_normalized + green_normalized
    usdc_percentage = (usdc_normalized * 100) // total if total > 0 else 0

    # Verify we have extreme imbalance
    assert usdc_percentage > 80, f"Not extreme enough: {usdc_percentage}% USDC (balances: {balances[0]} USDC, {balances[1]} GREEN)"

    # Calculate initial profit
    initial_profit = endaoment.calcProfitForStabilizer()

    # Run stabilizer on extremely imbalanced pool
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()

    # Even with extreme imbalance and high slippage, profit should not decrease
    assert new_profit >= initial_profit, \
        f"Profit decreased with extreme imbalance! Initial: {initial_profit}, New: {new_profit}, " \
        f"Pool imbalance: {usdc_percentage}% USDC"


###################################
# Pool Debt Integrity Tests       #
###################################


@pytest.base
def test_pool_debt_multiple_operations(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    ledger,
    _test,
):
    """Test pool debt tracking across multiple add/remove operations"""
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Add partner liquidity 3 times
    for i in range(3):
        usdc_amount = 5_000 * (10 ** usdc_token.decimals())
        partner = boa.env.generate_address()

        # Transfer to partner and approve endaoment
        usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
        usdc_token.approve(endaoment, usdc_amount, sender=partner)

        endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    # Total debt should be ~3 * 5000 GREEN (in 18 decimals)
    total_debt = ledger.greenPoolDebt(green_pool)
    expected_debt = 3 * 5_000 * EIGHTEEN_DECIMALS

    # Allow 1% tolerance for curve pool pricing
    _test(total_debt, expected_debt, 100)  # 1% tolerance

    # Debt should never be negative
    assert total_debt >= 0


@pytest.base
def test_pool_debt_repayment_reduces_debt(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    """Test that repaying pool debt correctly reduces the debt"""
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create initial debt
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    initial_debt = ledger.greenPoolDebt(green_pool)
    assert initial_debt > 0

    # Transfer green to endaoment for repayment
    repay_amount = 5_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, repay_amount, sender=whale)

    # Repay debt
    endaoment.repayPoolDebt(green_pool, repay_amount, sender=switchboard_delta.address)

    # Debt should have decreased
    new_debt = ledger.greenPoolDebt(green_pool)
    debt_reduction = initial_debt - new_debt

    # Debt reduction should equal repay amount
    _test(debt_reduction, repay_amount)

    # New debt should be initial - repay
    assert new_debt == initial_debt - repay_amount


@pytest.base
def test_pool_debt_cannot_over_repay(
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    """Test that repaying more than debt only reduces debt to zero

    repayPoolDebt() pulls green from endaoment_funds, burns only up to the debt amount,
    and returns any leftover green back to endaoment_funds.
    """
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create debt
    usdc_amount = 5_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    debt = ledger.greenPoolDebt(green_pool)
    assert debt > 0

    # Try to repay more than debt - transfer to endaoment_funds (where assets are stored)
    excessive_repay = debt * 2
    green_token.transfer(endaoment_funds, excessive_repay, sender=whale)

    initial_green_balance = green_token.balanceOf(endaoment_funds)

    # Repay excessive amount - contract will only burn up to debt amount
    success = endaoment.repayPoolDebt(green_pool, excessive_repay, sender=switchboard_delta.address)

    # Should succeed
    assert success

    # Debt should be zero
    assert ledger.greenPoolDebt(green_pool) == 0

    # Only the actual debt should have been burned, rest should remain in endaoment_funds
    final_green_balance = green_token.balanceOf(endaoment_funds)
    green_burned = initial_green_balance - final_green_balance
    _test(debt, green_burned)


@pytest.base
def test_pool_debt_integrity_during_stabilizer_remove(
    setGreenRefConfig,
    mock_price_source,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test that debt is properly repaid during green removal"""
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    mock_price_source.setPrice(usdc_token, EIGHTEEN_DECIMALS)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create debt via partner liquidity
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    initial_debt = ledger.greenPoolDebt(green_pool)
    assert initial_debt > 0

    # Create imbalance (more green in pool)
    green_add_amount = 50_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)

    amounts = [0, green_add_amount]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Run stabilizer to remove green (which should repay debt)
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Debt should have decreased or stayed same (never increase)
    new_debt = ledger.greenPoolDebt(green_pool)
    assert new_debt <= initial_debt


###################################
# State Consistency Tests         #
###################################


@pytest.base
def test_stabilizer_add_then_remove_sequence(
    setGreenRefConfig,
    mock_price_source,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test stabilizer operation sequence: add → remove

    This test verifies that profit never decreases through a full sequence of stabilizer
    operations: adding green to rebalance, then removing green to rebalance in the opposite
    direction. This tests the cumulative effect of multiple stabilizer actions.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    mock_price_source.setPrice(usdc_token, EIGHTEEN_DECIMALS)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # First create pool debt
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, green_pool, sender=switchboard_delta.address)

    # Record initial state
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Step 1: Create imbalance (more USDC) and add green
    usdc_add_amount = 30_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, usdc_add_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, usdc_add_amount, sender=endaoment.address)
    amounts = [usdc_add_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Check profit and debt after adding
    after_add_profit = endaoment.calcProfitForStabilizer()
    after_add_debt = ledger.greenPoolDebt(green_pool)

    # Step 2: Create opposite imbalance (more green) and remove
    green_add_amount = 40_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)
    amounts2 = [0, green_add_amount]
    green_pool.add_liquidity(amounts2, 0, sender=endaoment.address)

    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Check final profit and debt after removing
    final_profit = endaoment.calcProfitForStabilizer()
    final_debt = ledger.greenPoolDebt(green_pool)

    # Verify profit invariants throughout the sequence
    assert after_add_profit >= initial_profit, \
        f"Profit decreased after adding! Initial: {initial_profit}, After add: {after_add_profit}"
    assert final_profit >= after_add_profit, \
        f"Profit decreased after removing! After add: {after_add_profit}, Final: {final_profit}"

    # Verify debt behavior
    assert after_add_debt >= initial_debt, "Adding green should increase debt"
    assert final_debt <= after_add_debt, "Removing green should repay debt"
