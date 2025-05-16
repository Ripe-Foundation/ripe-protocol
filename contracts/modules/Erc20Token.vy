# @version 0.4.1

interface RipeHq:
    def canSetTokenBlacklist(_addr: address) -> bool: view
    def hasPendingGovChange() -> bool: view
    def greenToken() -> address: view
    def ripeToken() -> address: view

event Transfer:
    sender: indexed(address)
    recipient: indexed(address)
    amount: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    amount: uint256

event BlacklistModified:
    addr: indexed(address)
    isBlacklisted: bool

event RipeHqSet:
    prevHq: indexed(address)
    newHq: indexed(address)

_NAME: public(immutable(String[25]))

# ripe protocol
ripeHq: public(address)
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


@deploy
def __init__(
    _tokenName: String[25],
    _initialGov: address,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    _NAME = _tokenName

    assert _initialGov != empty(address) # dev: cannot be 0x0
    self.tempGov = _initialGov

    # initial supply
    if _initialSupply == 0 or _initialSupplyRecipient in [empty(address), self]:
        return

    self.balanceOf[_initialSupplyRecipient] = _initialSupply
    self.totalSupply = _initialSupply
    log Transfer(sender=empty(address), recipient=_initialSupplyRecipient, amount=_initialSupply)


@external
def setRegistryId(_regId: uint256) -> bool:
    # needed to register with RipeHq, can be ignored here
    return True


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
            keccak256(_NAME),
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


###########
# Ripe Hq #
###########


# validation


@view
@external
def isValidRipeHq(_ripeHq: address) -> bool:
    return self._isValidRipeHq(_ripeHq)


@view
@internal
def _isValidRipeHq(_ripeHq: address) -> bool:
    if _ripeHq == empty(address) or not _ripeHq.is_contract:
        return False
    return self in [staticcall RipeHq(_ripeHq).greenToken(), staticcall RipeHq(_ripeHq).ripeToken()]


# initial setup


@external
def setRipeHqOnSetup(_ripeHq: address):
    assert msg.sender == self.tempGov # dev: no perms
    assert self.ripeHq == empty(address) # dev: already set

    assert self._isValidRipeHq(_ripeHq) # dev: invalid ripe hq
    self.ripeHq = _ripeHq

    self.tempGov = empty(address)
    log RipeHqSet(prevHq=empty(address), newHq=_ripeHq)