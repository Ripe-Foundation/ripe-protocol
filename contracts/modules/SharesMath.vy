# @version 0.4.1

DECIMAL_OFFSET: constant(uint256) = (10 ** 8)

@deploy
def __init__():
    pass


@view
@internal
def _amountToShares(
    _asset: address,
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc shares
    numerator: uint256 = _amount * totalShares
    shares: uint256 = numerator // totalBalance

    # rounding
    if _shouldRoundUp and (numerator % totalBalance != 0):
        shares += 1

    return shares


@view
@internal
def _sharesToAmount(
    _asset: address,
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc amount
    numerator: uint256 = _shares * totalBalance
    amount: uint256 = numerator // totalShares

    # rounding
    if _shouldRoundUp and (numerator % totalShares != 0):
        amount += 1

    return amount