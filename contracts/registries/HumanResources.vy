# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    # NOTE: This is a temporary Human Resources contract. Real one coming soon.


# stuff


@external
def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256:
    # TODO: add vault to ledger, update deposit points, do all the things teller would do
    return 0


@external
def cashCheck(_amount: uint256, _lockDuration: uint256) -> bool:
    # mint, deposit (similar to lootbox deposit)
    return True


@external
def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool):
    # TODO: refund after cancel paycheck
    # burn position in ripe gov vault if _shouldBurnPosition
    pass


@view
@external
def hasRipeBalance(_contributor: address) -> bool:
    # TODO: get balance from vault
    return True