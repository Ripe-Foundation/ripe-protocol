# @version 0.4.1

implements: IERC20
from ethereum.ercs import IERC20

interface RipeHq:
    def canSetTokenBlacklist(_addr: address) -> bool: view
    def canMintGreen(_addr: address) -> bool: view
    def canMintRipe(_addr: address) -> bool: view
    def hasPendingGovChange() -> bool: view
    def greenToken() -> address: view
    def governance() -> address: view
    def ripeToken() -> address: view

interface ERC1271:
    def isValidSignature(_hash: bytes32, _signature: Bytes[65]) -> bytes4: view

# erc20

struct PendingHq:
    newHq: address
    initiatedBlock: uint256
    confirmBlock: uint256

event Transfer:
    sender: indexed(address)
    recipient: indexed(address)
    amount: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    amount: uint256

# ripe 

event BlacklistModified:
    addr: indexed(address)
    isBlacklisted: bool

event HqChangeInitiated:
    prevHq: indexed(address)
    newHq: indexed(address)
    confirmBlock: uint256

event HqChangeConfirmed:
    prevHq: indexed(address)
    newHq: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event HqChangeCancelled:
    cancelledHq: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event TokenPauseModified:
    isPaused: bool

event InitialRipeHqSet:
    hq: indexed(address)
    timeLock: uint256

event HqChangeTimeLockModified:
    prevTimeLock: uint256
    newTimeLock: uint256

# ripe hq
ripeHq: public(address)

# config
blacklisted: public(HashMap[address, bool])
isPaused: public(bool)
pendingHq: public(PendingHq)
hqChangeTimeLock: public(uint256)
tempGov: address

MIN_HQ_TIME_LOCK: immutable(uint256)
MAX_HQ_TIME_LOCK: immutable(uint256)

# erc20
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# token info
TOKEN_NAME: public(immutable(String[64]))
TOKEN_SYMBOL: public(immutable(String[32]))
TOKEN_DECIMALS: public(immutable(uint8))
VERSION: public(constant(String[8])) = "v1.0.0"

# eip-712
nonces: public(HashMap[address, uint256])
EIP712_TYPEHASH: constant(bytes32) = keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
EIP2612_TYPEHASH: constant(bytes32) = keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)")
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001
ERC1271_MAGIC_VAL: constant(bytes4) = 0x1626ba7e

CACHED_DOMAIN_SEPARATOR: immutable(bytes32)
NAME_HASH: immutable(bytes32)
VERSION_HASH: constant(bytes32) = keccak256(VERSION)
CACHED_CHAIN_ID: immutable(uint256)


@deploy
def __init__(
    _tokenName: String[64],
    _tokenSymbol: String[32],
    _tokenDecimals: uint8,
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    # token info
    TOKEN_NAME = _tokenName
    TOKEN_SYMBOL = _tokenSymbol
    TOKEN_DECIMALS = _tokenDecimals

    MIN_HQ_TIME_LOCK = _minHqTimeLock
    MAX_HQ_TIME_LOCK = _maxHqTimeLock

    # set initial gov (green / ripe tokens)
    if _initialGov != empty(address):
        assert _ripeHq == empty(address) # dev: cannot set initial gov and ripe hq
        self.tempGov = _initialGov

    # set ripe hq
    if _ripeHq != empty(address):
        assert self._isValidNewRipeHq(_ripeHq, empty(address)) # dev: invalid ripe hq
        assert _initialGov == empty(address) # dev: cannot set initial gov and ripe hq
        self.ripeHq = _ripeHq

    # initial supply
    if _initialSupply != 0 and _initialSupplyRecipient not in [empty(address), self]:
        self.balanceOf[_initialSupplyRecipient] = _initialSupply
        self.totalSupply = _initialSupply
        log Transfer(sender=empty(address), recipient=_initialSupplyRecipient, amount=_initialSupply)

    # domain separator
    NAME_HASH = keccak256(_tokenName)
    CACHED_CHAIN_ID = chain.id
    CACHED_DOMAIN_SEPARATOR = keccak256(
        abi_encode(
            EIP712_TYPEHASH,
            NAME_HASH,
            VERSION_HASH,
            CACHED_CHAIN_ID,
            self,
        )
    )


##############
# Token Info #
##############


@view
@external
def name() -> String[64]:
    return TOKEN_NAME


@view
@external
def symbol() -> String[32]:
    return TOKEN_SYMBOL


@view
@external
def decimals() -> uint8:
    return TOKEN_DECIMALS


#############
# Transfers #
#############


@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self._transfer(msg.sender, _recipient, _amount)
    return True


@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    assert not self.blacklisted[msg.sender] # dev: spender blacklisted
    self._spendAllowance(_sender, msg.sender, _amount)
    self._transfer(_sender, _recipient, _amount)
    return True


@internal
def _transfer(_sender: address, _recipient: address, _amount: uint256):
    assert not self.isPaused # dev: token paused
    assert _amount != 0 # dev: cannot transfer 0 amount
    assert _recipient not in [self, empty(address)] # dev: invalid recipient

    assert not self.blacklisted[_sender] # dev: sender blacklisted
    assert not self.blacklisted[_recipient] # dev: recipient blacklisted

    senderBalance: uint256 = self.balanceOf[_sender]
    assert senderBalance >= _amount # dev: insufficient funds
    self.balanceOf[_sender] = senderBalance - _amount
    self.balanceOf[_recipient] += _amount

    log Transfer(sender=_sender, recipient=_recipient, amount=_amount)


#############
# Allowance #
#############


# approvals


@external
def approve(_spender: address, _amount: uint256) -> bool:
    self._validateNewApprovals(msg.sender, _spender)
    self._approve(msg.sender, _spender, _amount)
    return True


@internal
def _approve(_owner: address, _spender: address, _amount: uint256):
    self.allowance[_owner][_spender] = _amount
    log Approval(owner=_owner, spender=_spender, amount=_amount)


@internal
def _spendAllowance(_owner: address, _spender: address, _amount: uint256):
    currentAllowance: uint256 = self.allowance[_owner][_spender]
    if currentAllowance != max_value(uint256):
        assert currentAllowance >= _amount # dev: insufficient allowance
        self._approve(_owner, _spender, currentAllowance - _amount)


# increase / decrease allowance


@external
def increaseAllowance(_spender: address, _amount: uint256) -> bool:
    self._validateNewApprovals(msg.sender, _spender)
    currentAllowance: uint256 = self.allowance[msg.sender][_spender]
    maxIncrease: uint256 = max_value(uint256) - currentAllowance
    newAllowance: uint256 = currentAllowance + min(_amount, maxIncrease)
    if newAllowance != currentAllowance:
        self._approve(msg.sender, _spender, newAllowance)
    return True


@external
def decreaseAllowance(_spender: address, _amount: uint256) -> bool:
    self._validateNewApprovals(msg.sender, _spender)
    currentAllowance: uint256 = self.allowance[msg.sender][_spender]
    newAllowance: uint256 = currentAllowance - min(_amount, currentAllowance)
    if newAllowance != currentAllowance:
        self._approve(msg.sender, _spender, newAllowance)
    return True


# validation


@view
@internal
def _validateNewApprovals(_owner: address, _spender: address):
    assert not self.isPaused # dev: token paused
    assert not self.blacklisted[_owner] # dev: owner blacklisted
    assert not self.blacklisted[_spender] # dev: spender blacklisted
    assert _spender != empty(address) # dev: invalid spender


#####################
# Minting / Burning #
#####################


# mint tokens


@internal
def _mint(_recipient: address, _amount: uint256) -> bool:
    assert _recipient not in [self, empty(address)] # dev: invalid recipient
    assert not self.blacklisted[_recipient] # dev: blacklisted
    assert not self.isPaused # dev: token paused

    self.balanceOf[_recipient] += _amount
    self.totalSupply += _amount
    log Transfer(sender=empty(address), recipient=_recipient, amount=_amount)
    return True


# burn tokens


@external
def burn(_amount: uint256) -> bool:
    assert not self.isPaused # dev: token paused
    self._burn(msg.sender, _amount)
    return True


@internal
def _burn(_owner: address, _amount: uint256):
    self.balanceOf[_owner] -= _amount
    self.totalSupply -= _amount
    log Transfer(sender=_owner, recipient=empty(address), amount=_amount)


###########
# EIP 712 #
###########


@view
@external
def DOMAIN_SEPARATOR() -> bytes32:
    return self._domainSeparator()


@view
@internal
def _domainSeparator() -> bytes32:
    if chain.id != CACHED_CHAIN_ID:
        return keccak256(
            abi_encode(
                EIP712_TYPEHASH,
                NAME_HASH,
                VERSION_HASH,
                chain.id,
                self,
            )
        )
    return CACHED_DOMAIN_SEPARATOR


@external
def permit(
    _owner: address,
    _spender: address,
    _value: uint256,
    _deadline: uint256,
    _signature: Bytes[65],
) -> bool:
    self._validateNewApprovals(_owner, _spender)
    assert _owner != empty(address) and block.timestamp <= _deadline # dev: permit expired

    nonce: uint256 = self.nonces[_owner]
    digest: bytes32 = keccak256(
        concat(
            b"\x19\x01",
            self._domainSeparator(),
            keccak256(abi_encode(EIP2612_TYPEHASH, _owner, _spender, _value, nonce, _deadline)),
        )
    )

    if _owner.is_contract:
        assert staticcall ERC1271(_owner).isValidSignature(digest, _signature) == ERC1271_MAGIC_VAL # dev: invalid signature

    else:
        r: bytes32 = convert(slice(_signature, 0, 32), bytes32)
        s: bytes32 = convert(slice(_signature, 32, 32), bytes32)
        v: uint8 = convert(slice(_signature, 64, 1), uint8)

        response: Bytes[32] = raw_call(
            ECRECOVER_PRECOMPILE,
            abi_encode(digest, v, r, s),
            max_outsize = 32,
            is_static_call = True # a view function
        )
        assert len(response) == 32  # dev: invalid ecrecover response length
        assert abi_decode(response, address) == _owner  # dev: invalid signature

    self.nonces[_owner] = nonce + 1
    self._approve(_owner, _spender, _value)
    return True


#############
# Blacklist #
#############


@external
def setBlacklist(_addr: address, _shouldBlacklist: bool) -> bool:
    assert staticcall RipeHq(self.ripeHq).canSetTokenBlacklist(msg.sender) # dev: no perms

    assert _addr not in [self, empty(address)] # dev: invalid blacklist recipient
    self.blacklisted[_addr] = _shouldBlacklist
    log BlacklistModified(addr=_addr, isBlacklisted=_shouldBlacklist)
    return True


@external
def burnBlacklistTokens(_addr: address, _amount: uint256 = max_value(uint256)) -> bool:
    assert msg.sender == staticcall RipeHq(self.ripeHq).governance() # dev: no perms
    assert self.blacklisted[_addr] # dev: not blacklisted

    amount: uint256 = min(_amount, self.balanceOf[_addr])
    assert amount != 0 # dev: cannot burn 0 tokens
    self._burn(_addr, amount)
    return True


###################
# Ripe Hq Changes #
###################


@view
@external
def hasPendingHqChange() -> bool:
    return self.pendingHq.confirmBlock != 0


# initiate hq change


@external
def initiateHqChange(_newHq: address):
    assert msg.sender == staticcall RipeHq(self.ripeHq).governance() # dev: no perms

    # validate new hq
    prevHq: address = self.ripeHq
    assert self._isValidNewRipeHq(_newHq, prevHq) # dev: invalid new hq

    confirmBlock: uint256 = block.number + self.hqChangeTimeLock
    self.pendingHq = PendingHq(
        newHq= _newHq,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log HqChangeInitiated(prevHq=prevHq, newHq=_newHq, confirmBlock=confirmBlock)


# confirm hq change


@external
def confirmHqChange() -> bool:
    assert msg.sender == staticcall RipeHq(self.ripeHq).governance() # dev: no perms

    data: PendingHq = self.pendingHq
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time lock not reached

    # validate new hq one more time
    prevHq: address = self.ripeHq
    if not self._isValidNewRipeHq(data.newHq, prevHq):
        self.pendingHq = empty(PendingHq)
        return False

    # set new ripe hq
    self.ripeHq = data.newHq
    self.pendingHq = empty(PendingHq)
    log HqChangeConfirmed(prevHq=prevHq, newHq=data.newHq, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)
    return True


# cancel hq change


@external
def cancelHqChange():
    assert msg.sender == staticcall RipeHq(self.ripeHq).governance() # dev: no perms

    data: PendingHq = self.pendingHq
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingHq = empty(PendingHq)
    log HqChangeCancelled(cancelledHq=data.newHq, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


# validation


@view
@external
def isValidNewRipeHq(_newHq: address) -> bool:
    return self._isValidNewRipeHq(_newHq, self.ripeHq)


@view
@internal
def _isValidNewRipeHq(_newHq: address, _prevHq: address) -> bool:

    # same hq, or invalid new hq
    if _newHq == _prevHq or _newHq == empty(address) or not _newHq.is_contract:
        return False

    # if current hq has pending gov change, cannot change ripe hq now
    if _prevHq != empty(address) and staticcall RipeHq(_prevHq).hasPendingGovChange():
        return False

    # if new hq has pending gov change, or is not set, cannot change ripe hq now
    if staticcall RipeHq(_newHq).hasPendingGovChange() or staticcall RipeHq(_newHq).governance() == empty(address):
        return False

    # tokens must be set
    if staticcall RipeHq(_newHq).greenToken() == empty(address) or staticcall RipeHq(_newHq).ripeToken() == empty(address):
        return False

    # make sure it has the necessary interfaces
    assert not staticcall RipeHq(_newHq).canSetTokenBlacklist(empty(address)) # dev: invalid interface
    assert not staticcall RipeHq(_newHq).canMintGreen(empty(address)) # dev: invalid interface
    assert not staticcall RipeHq(_newHq).canMintRipe(empty(address)) # dev: invalid interface

    return True


####################
# Time Lock Config #
####################


@external
def setHqChangeTimeLock(_newTimeLock: uint256) -> bool:
    ripeHq: address = self.ripeHq
    assert msg.sender == staticcall RipeHq(ripeHq).governance() # dev: no perms
    assert not staticcall RipeHq(ripeHq).hasPendingGovChange() # dev: pending gov change
    return self._setHqChangeTimeLock(_newTimeLock, self.hqChangeTimeLock)


@internal
def _setHqChangeTimeLock(_newTimeLock: uint256, _prevTimeLock: uint256) -> bool:
    assert self._isValidHqChangeTimeLock(_newTimeLock, _prevTimeLock) # dev: invalid time lock
    self.hqChangeTimeLock = _newTimeLock
    log HqChangeTimeLockModified(prevTimeLock=_prevTimeLock, newTimeLock=_newTimeLock)
    return True


# validation


@view
@external
def isValidHqChangeTimeLock(_newTimeLock: uint256) -> bool:
    return self._isValidHqChangeTimeLock(_newTimeLock, self.hqChangeTimeLock)


@view
@internal
def _isValidHqChangeTimeLock(_newTimeLock: uint256, _prevTimeLock: uint256) -> bool:
    if _newTimeLock == _prevTimeLock:
        return False
    return _newTimeLock >= MIN_HQ_TIME_LOCK and _newTimeLock <= MAX_HQ_TIME_LOCK


# views


@view
@external
def minHqTimeLock() -> uint256:
    return MIN_HQ_TIME_LOCK


@view
@external
def maxHqTimeLock() -> uint256:
    return MAX_HQ_TIME_LOCK


#########
# Pause #
#########


@external
def pause(_shouldPause: bool):
    assert msg.sender == staticcall RipeHq(self.ripeHq).governance() # dev: no perms
    assert _shouldPause != self.isPaused # dev: no change
    self.isPaused = _shouldPause
    log TokenPauseModified(isPaused=_shouldPause)


###############
# Token Setup #
###############


@external
def finishTokenSetup(_newHq: address, _timeLock: uint256 = 0) -> bool:
    assert msg.sender == self.tempGov # dev: no perms

    prevHq: address = self.ripeHq
    assert prevHq == empty(address) # dev: already set

    # set hq
    assert self._isValidNewRipeHq(_newHq, prevHq) # dev: invalid ripe hq
    self.ripeHq = _newHq

    # set time lock
    timeLock: uint256 = _timeLock
    if timeLock == 0:
        timeLock = MIN_HQ_TIME_LOCK
    prevTimeLock: uint256 = self.hqChangeTimeLock
    if timeLock != prevTimeLock:
        assert self._setHqChangeTimeLock(timeLock, prevTimeLock) # dev: invalid time lock

    self.tempGov = empty(address)
    log InitialRipeHqSet(hq=_newHq, timeLock=timeLock)
    return True
