# @version 0.4.1

interface RipeHq:
    def canSetTokenBlacklist(_addr: address) -> bool: view
    def canMintGreen(_addr: address) -> bool: view
    def canMintRipe(_addr: address) -> bool: view
    def hasPendingGovChange() -> bool: view
    def greenToken() -> address: view
    def governance() -> address: view
    def ripeToken() -> address: view

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

event InitialRipeHqSet:
    hq: indexed(address)
    timeLock: uint256

event HqChangeTimeLockModified:
    numBlocks: uint256

# ripe hq
ripeHq: public(address)

# config
pendingHq: public(PendingHq)
hqChangeTimeLock: public(uint256)
tempGov: address

# blacklist
blacklisted: public(HashMap[address, bool])

# erc20
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# eip-712
nonces: public(HashMap[address, uint256])
DOMAIN_TYPE_HASH: constant(bytes32) = keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)')
PERMIT_TYPE_HASH: constant(bytes32) = keccak256('Permit(address owner,address spender,uint256 amount,uint256 nonce,uint256 expiry)')
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001

TOKEN_NAME: immutable(String[25])
MIN_HQ_TIME_LOCK: immutable(uint256)
MAX_HQ_TIME_LOCK: immutable(uint256)


@deploy
def __init__(
    _tokenName: String[25],
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialGov: address,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    TOKEN_NAME = _tokenName
    MIN_HQ_TIME_LOCK = _minHqTimeLock
    MAX_HQ_TIME_LOCK = _maxHqTimeLock

    assert _initialGov != empty(address) # dev: cannot be 0x0
    self.tempGov = _initialGov

    # initial supply
    if _initialSupply == 0 or _initialSupplyRecipient in [empty(address), self]:
        return

    self.balanceOf[_initialSupplyRecipient] = _initialSupply
    self.totalSupply = _initialSupply
    log Transfer(sender=empty(address), recipient=_initialSupplyRecipient, amount=_initialSupply)


########
# Core #
########


@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    assert _amount != 0 # dev: cannot transfer 0
    assert _recipient not in [self, empty(address)] # dev: invalid recipient

    assert not self.blacklisted[msg.sender] # dev: sender blacklisted
    assert not self.blacklisted[_recipient] # dev: recipient blacklisted

    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_recipient] += _amount

    log Transfer(sender=msg.sender, recipient=_recipient, amount=_amount)
    return True


@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    assert _amount != 0 # dev: cannot transfer 0
    assert _recipient not in [self, empty(address)] # dev: invalid recipient

    assert not self.blacklisted[_sender] # dev: sender blacklisted
    assert not self.blacklisted[msg.sender] # dev: spender blacklisted
    assert not self.blacklisted[_recipient] # dev: recipient blacklisted

    self.balanceOf[_sender] -= _amount
    self.balanceOf[_recipient] += _amount
    self.allowance[_sender][msg.sender] -= _amount

    log Transfer(sender=_sender, recipient=_recipient, amount=_amount)
    return True


@external
def approve(_spender: address, _amount: uint256) -> bool:
    assert _spender != empty(address) # dev: invalid spender
    assert self.allowance[msg.sender][_spender] == 0 or _amount == 0 # dev: invalid approve
    self.allowance[msg.sender][_spender] = _amount
    log Approval(owner=msg.sender, spender=_spender, amount=_amount)
    return True


@external
def decreaseAllowance(_spender: address, _amount: uint256) -> bool:
    assert _spender != empty(address) # dev: invalid spender

    currentAllowance: uint256 = self.allowance[msg.sender][_spender]
    newAllowance: uint256 = currentAllowance - min(_amount, currentAllowance)

    self.allowance[msg.sender][_spender] = newAllowance
    log Approval(owner=msg.sender, spender=_spender, amount=newAllowance)
    return True


@external
def increaseAllowance(_spender: address, _amount: uint256) -> bool:
    assert _spender != empty(address) # dev: invalid spender
    assert _amount != 0 # dev: cannot increase by 0

    currentAllowance: uint256 = self.allowance[msg.sender][_spender]
    newAllowance: uint256 = currentAllowance + min(_amount, max_value(uint256) - currentAllowance)

    self.allowance[msg.sender][_spender] = newAllowance
    log Approval(owner=msg.sender, spender=_spender, amount=newAllowance)
    return True


#####################
# Minting / Burning #
#####################


@internal
def _mint(_recipient: address, _amount: uint256) -> bool:
    assert _recipient not in [self, empty(address)] # dev: invalid recipient
    assert not self.blacklisted[_recipient] # dev: blacklisted

    self.totalSupply += _amount
    self.balanceOf[_recipient] += _amount

    log Transfer(sender=empty(address), recipient=_recipient, amount=_amount)
    return True


@external
def burn(_amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= _amount
    self.totalSupply -= _amount
    log Transfer(sender=msg.sender, recipient=empty(address), amount=_amount)
    return True


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
    return keccak256(
        concat(
            DOMAIN_TYPE_HASH,
            keccak256(TOKEN_NAME),
            keccak256("1.0"),
            abi_encode(chain.id, self)
        )
    )


@external
def permit(
    _owner: address,
    _spender: address,
    _amount: uint256,
    _expiry: uint256,
    _signature: Bytes[65],
) -> bool:

    # see https://eips.ethereum.org/EIPS/eip-2612
    assert _owner != empty(address) # dev: invalid owner
    assert _expiry == 0 or _expiry >= block.timestamp # dev: permit expired

    nonce: uint256 = self.nonces[_owner]
    digest: bytes32 = keccak256(
        concat(
            b'\x19\x01',
            self._domainSeparator(),
            keccak256(
                abi_encode(
                    PERMIT_TYPE_HASH,
                    _owner,
                    _spender,
                    _amount,
                    nonce,
                    _expiry,
                )
            )
        )
    )

    # NOTE: signature is packed as r, s, v
    r: bytes32 = convert(slice(_signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_signature, 64, 1), uint8)

    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize=32,
        is_static_call=True # a view function
    )

    assert len(response) == 32  # dev: invalid ecrecover response length
    assert abi_decode(response, address) == _owner  # dev: invalid signature

    self.allowance[_owner][_spender] = _amount
    self.nonces[_owner] = nonce + 1

    log Approval(owner=_owner, spender=_spender, amount=_amount)
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
def setHqChangeTimeLock(_numBlocks: uint256) -> bool:
    ripeHq: address = self.ripeHq
    assert msg.sender == staticcall RipeHq(ripeHq).governance() # dev: no perms
    assert not staticcall RipeHq(ripeHq).hasPendingGovChange() # dev: pending gov change
    return self._setHqChangeTimeLock(_numBlocks)


@internal
def _setHqChangeTimeLock(_numBlocks: uint256) -> bool:
    assert self._isValidHqChangeTimeLock(_numBlocks) # dev: invalid time lock
    self.hqChangeTimeLock = _numBlocks
    log HqChangeTimeLockModified(numBlocks=_numBlocks)
    return True


# validation


@view
@external
def isValidHqChangeTimeLock(_numBlocks: uint256) -> bool:
    return self._isValidHqChangeTimeLock(_numBlocks)


@view
@internal
def _isValidHqChangeTimeLock(_numBlocks: uint256) -> bool:
    return _numBlocks >= MIN_HQ_TIME_LOCK and _numBlocks <= MAX_HQ_TIME_LOCK


# views


@view
@external
def minHqTimeLock() -> uint256:
    return MIN_HQ_TIME_LOCK


@view
@external
def maxHqTimeLock() -> uint256:
    return MAX_HQ_TIME_LOCK


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
    assert self._setHqChangeTimeLock(timeLock) # dev: invalid time lock

    self.tempGov = empty(address)
    log InitialRipeHqSet(hq=_newHq, timeLock=timeLock)
    return True


@external
def setRegistryId(_regId: uint256) -> bool:
    # needed to register with RipeHq (AddressRegistry module), can be ignored here
    return True