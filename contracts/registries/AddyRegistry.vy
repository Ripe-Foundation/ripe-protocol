# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__
exports: registry.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry


@deploy
def __init__(
    _initialGov: address,
    _minGovChangeDelay: uint256,
    _maxGovChangeDelay: uint256,
    _minRegistryChangeDelay: uint256,
    _maxRegistryChangeDelay: uint256,
):
    # initialize gov
    gov.__init__(_initialGov, empty(address), _minGovChangeDelay, _maxGovChangeDelay)

    # initialize registry
    registry.__init__(_minRegistryChangeDelay, _maxRegistryChangeDelay, "AddyRegistry.vy")


# TEMPORARY
# TELLER: 1
# LEDGER: 2
# VAULT_BOOK: 3
# VALIDATOR: 4
# LOOTBOX: 5
# CONTROL_ROOM: 6
# PRICE_DESK: 7


############
# New Addy #
############


@external
def registerNewAddy(_addr: address, _description: String[64]) -> bool:
    """
    @notice Initiates the registration process for a new address
    @dev Only callable by governance. Sets up a pending registration that requires confirmation after a delay period
    @param _addr The address to register
    @param _description A short description of the address (max 64 characters)
    @return True if the registration was successfully initiated, False if the address is invalid
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._registerNewAddy(_addr, _description)


@external
def confirmNewAddy(_addr: address) -> uint256:
    """
    @notice Confirms a pending address registration after the required delay period
    @dev Only callable by governance. Finalizes the registration by assigning an ID
    @param _addr The address to confirm registration for
    @return The assigned ID for the registered address, or 0 if confirmation fails
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmNewAddy(_addr)


@external
def cancelPendingNewAddy(_addr: address) -> bool:
    """
    @notice Cancels a pending address registration
    @dev Only callable by governance. Removes the pending registration and emits a cancellation event
    @param _addr The address whose pending registration should be cancelled
    @return True if the cancellation was successful, reverts if no pending registration exists
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelPendingNewAddy(_addr)


###############
# Update Addy #
###############


@external
def updateAddyAddr(_addyId: uint256, _newAddr: address) -> bool:
    """
    @notice Initiates an address update for an existing registered address
    @dev Only callable by governance. Sets up a pending update that requires confirmation after a delay period
    @param _addyId The ID of the address to update
    @param _newAddr The new address to set
    @return True if the update was successfully initiated, False if the update is invalid
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._updateAddyAddr(_addyId, _newAddr)


@external
def confirmAddyUpdate(_addyId: uint256) -> bool:
    """
    @notice Confirms a pending address update after the required delay period
    @dev Only callable by governance. Finalizes the update by updating the address info
    @param _addyId The ID of the address to confirm update for
    @return True if the update was successfully confirmed, False if confirmation fails
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddyUpdate(_addyId)


@external
def cancelPendingAddyUpdate(_addyId: uint256) -> bool:
    """
    @notice Cancels a pending address update
    @dev Only callable by governance. Removes the pending update and emits a cancellation event
    @param _addyId The ID of the address whose pending update should be cancelled
    @return True if the cancellation was successful, reverts if no pending update exists
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelPendingAddyUpdate(_addyId)


################
# Disable Addy #
################


@external
def disableAddyAddr(_addyId: uint256) -> bool:
    """
    @notice Initiates the disable process for an existing registered address
    @dev Only callable by governance. Sets up a pending disable that requires confirmation after a delay period
    @param _addyId The ID of the address to disable
    @return True if the disable was successfully initiated, False if the disable is invalid
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._disableAddyAddr(_addyId)


@external
def confirmAddyDisable(_addyId: uint256) -> bool:
    """
    @notice Confirms a pending address disable after the required delay period
    @dev Only callable by governance. Finalizes the disable by clearing the address
    @param _addyId The ID of the address to confirm disable for
    @return True if the disable was successfully confirmed, False if confirmation fails
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddyDisable(_addyId)


@external
def cancelPendingAddyDisable(_addyId: uint256) -> bool:
    """
    @notice Cancels a pending address disable
    @dev Only callable by governance. Removes the pending disable and emits a cancellation event
    @param _addyId The ID of the address whose pending disable should be cancelled
    @return True if the cancellation was successful, reverts if no pending disable exists
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelPendingAddyDisable(_addyId)


################
# Change Delay #
################


@external
def setAddyChangeDelay(_numBlocks: uint256) -> bool:
    """
    @notice Sets the delay period required for address changes
    @dev Only callable by governance. The delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY
    @param _numBlocks The number of blocks to set as the delay period
    @return True if the delay was successfully set, reverts if delay is invalid
    """
    assert msg.sender == gov.governance # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@external
def setAddyChangeDelayToMin() -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)