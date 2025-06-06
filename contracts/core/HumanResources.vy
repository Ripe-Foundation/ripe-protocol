# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__
exports: gov.__interface__
exports: timeLock.__interface__

initializes: addys
initializes: deptBasics[addys := addys]
initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

from interfaces import Department

# struct ContributorTerms:
#     isFrozen: bool
#     isManager: bool
#     isContributor: bool
#     isRipe: bool
#     isRipeManager: bool
#     isRipeContributor: bool

# # pending
# pendingContributor: public(HashMap[uint256, ContributorTerms]) # aid -> config


@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)

    # NOTE: This is a temporary Human Resources contract. Real one coming soon.


##########
# Create #
##########


# initiate 

# @external
# def initiateNewContributor(

# ) -> uint256:
#     assert gov._canGovern(msg.sender) # dev: no perms

#     aid: uint256 = timeLock._initiateAction()
#     self.pendingContributor[aid] = ContributorTerms(

#     )

#     confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)









# stuff


@external
def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256:
    # TODO: add vault to ledger, update deposit points, do all the things teller would do
    return 0


@external
def cashRipeCheck(_amount: uint256, _lockDuration: uint256) -> bool:
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


# THINGS TO ADD TO SWITCHBOARD FOUR

# OTHER CONTRIBUTOR THINGS
# cashRipeCheck for contributor
# cancelRipeTransfer for contributor
# cancelOwnershipChange for contributor
# setManager for contributor

# THINGS ONLY HR CAN DO
# setIsFrozen
# cancelPaycheck