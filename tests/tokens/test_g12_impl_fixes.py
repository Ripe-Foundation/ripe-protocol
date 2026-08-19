"""Group 12 implementation proofs not already covered by rewritten nodes."""

import boa
import pytest
from eth_account import Account

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


E18 = EIGHTEEN_DECIMALS
HQ_EMPTY_SAVINGS_GREEN = """
# @version 0.4.3

governance: public(address)
greenToken: public(address)
ripeToken: public(address)
savingsGreen: public(address)

@deploy
def __init__(_gov: address, _green: address, _ripe: address, _sg: address):
    self.governance = _gov
    self.greenToken = _green
    self.ripeToken = _ripe
    self.savingsGreen = _sg

@view
@external
def hasPendingGovChange() -> bool:
    return False

@view
@external
def canSetTokenBlacklist(_addr: address) -> bool:
    return False

@view
@external
def canMintGreen(_addr: address) -> bool:
    return False

@view
@external
def canMintRipe(_addr: address) -> bool:
    return False
"""
HQ_MISSING_SAVINGS_GREEN = """
# @version 0.4.3

governance: public(address)
greenToken: public(address)
ripeToken: public(address)

@deploy
def __init__(_gov: address, _green: address, _ripe: address):
    self.governance = _gov
    self.greenToken = _green
    self.ripeToken = _ripe

@view
@external
def hasPendingGovChange() -> bool:
    return False

@view
@external
def canSetTokenBlacklist(_addr: address) -> bool:
    return False

@view
@external
def canMintGreen(_addr: address) -> bool:
    return False

@view
@external
def canMintRipe(_addr: address) -> bool:
    return False
"""
ASSET_MOCK = """
# @version 0.4.3

asset: public(address)

@deploy
def __init__(_asset: address):
    self.asset = _asset
"""


def _fresh_vault(deploy3r, whale, supply=10_000 * E18):
    green = boa.load(
        "contracts/tokens/GreenToken.vy",
        ZERO_ADDRESS,
        deploy3r,
        43_200,
        302_400,
        supply,
        whale,
    )
    sg = boa.load(
        "contracts/tokens/SavingsGreen.vy",
        green,
        ZERO_ADDRESS,
        deploy3r,
        43_200,
        302_400,
        0,
        ZERO_ADDRESS,
    )
    return green, sg


def _drain(savings_green, *holders):
    for holder in holders:
        bal = savings_green.balanceOf(holder)
        if bal:
            savings_green.redeem(bal, holder, holder, sender=holder)


def _sign(token, owner, spender, value):
    deadline = boa.env.evm.patch.timestamp + 3600
    message = {
        "domain": {
            "name": token.name(),
            "version": token.VERSION(),
            "chainId": boa.env.evm.patch.chain_id,
            "verifyingContract": token.address,
        },
        "types": {
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "message": {
            "owner": owner.address,
            "spender": spender,
            "value": value,
            "nonce": token.nonces(owner.address),
            "deadline": deadline,
        },
    }
    return bytes(Account.sign_typed_data(owner.key, full_message=message).signature), deadline


def test_g12_impl_max_views_zero_under_green_gates_and_invalid_receiver(
    savings_green,
    green_token,
    governance,
    switchboard,
    whale,
    alice,
    ripe_hq,
):
    with boa.env.anchor():
        green_token.approve(savings_green, MAX_UINT256, sender=whale)
        savings_green.deposit(10 * E18, alice, sender=whale)

        green_token.pause(True, sender=governance.address)
        assert savings_green.maxDeposit(alice) == 0
        assert savings_green.maxMint(alice) == 0
        assert savings_green.maxWithdraw(alice) == 0
        assert savings_green.maxRedeem(alice) == 0
        green_token.pause(False, sender=governance.address)

        green_token.setBlacklist(savings_green.address, True, sender=switchboard.address)
        assert savings_green.maxDeposit(alice) == 0
        assert savings_green.maxMint(alice) == 0
        assert savings_green.maxWithdraw(alice) == 0
        assert savings_green.maxRedeem(alice) == 0
        green_token.setBlacklist(savings_green.address, False, sender=switchboard.address)

        assert savings_green.maxDeposit(ZERO_ADDRESS) == 0
        assert savings_green.maxMint(ZERO_ADDRESS) == 0
        assert savings_green.maxDeposit(savings_green.address) == 0
        assert savings_green.maxMint(savings_green.address) == 0


def test_g12_impl_empty_vault_and_pre_first_deposit_donation_keep_unlimited_max(
    deploy3r,
    whale,
    alice,
):
    green, sg = _fresh_vault(deploy3r, whale)
    assert sg.totalSupply() == 0
    assert sg.totalAssets() == 0
    assert sg.maxDeposit(alice) == MAX_UINT256
    assert sg.maxMint(alice) == MAX_UINT256

    green.transfer(sg.address, 5 * E18, sender=whale)
    assert sg.totalSupply() == 0
    assert sg.totalAssets() == 5 * E18
    assert sg.maxDeposit(alice) == MAX_UINT256
    assert sg.maxMint(alice) == MAX_UINT256


def test_g12_impl_last_share_burn_reverts_with_assets_and_succeeds_when_empty(
    savings_green,
    green_token,
    switchboard,
    governance,
    whale,
    alice,
    bob,
    sally,
    ripe_hq,
):
    with boa.env.anchor():
        green_token.approve(savings_green, MAX_UINT256, sender=whale)
        _drain(savings_green, whale, alice, bob, sally)
        shares = savings_green.deposit(8 * E18, alice, sender=whale)
        assert savings_green.totalSupply() == shares
        with boa.reverts("cannot strand vault assets"):
            savings_green.burn(shares, sender=alice)
        savings_green.setBlacklist(alice, True, sender=switchboard.address)
        with boa.reverts("cannot strand vault assets"):
            savings_green.burnBlacklistTokens(alice, shares, sender=governance.address)
        savings_green.setBlacklist(alice, False, sender=switchboard.address)
        assert savings_green.balanceOf(alice) == shares
        assert savings_green.redeem(shares, alice, alice, sender=alice) == 8 * E18

        _drain(savings_green, whale, alice, bob, sally)
        shares = savings_green.deposit(4 * E18, alice, sender=whale)
        assert savings_green.totalSupply() == shares
        green_token.burn(green_token.balanceOf(savings_green), sender=savings_green.address)
        assert savings_green.totalAssets() == 0
        assert savings_green.burn(shares, sender=alice)
        assert savings_green.totalSupply() == 0

        shares = savings_green.deposit(3 * E18, alice, sender=whale)
        assert savings_green.totalSupply() == shares
        green_token.burn(green_token.balanceOf(savings_green), sender=savings_green.address)
        savings_green.setBlacklist(alice, True, sender=switchboard.address)
        assert savings_green.burnBlacklistTokens(alice, sender=governance.address)
        assert savings_green.totalSupply() == 0


def test_g12_impl_blacklisted_sgreen_burn_reverts_green_ripe_still_work(
    green_token,
    ripe_token,
    savings_green,
    switchboard,
    whale,
    alice,
    ripe_hq,
):
    with boa.env.anchor():
        green_token.approve(savings_green, MAX_UINT256, sender=whale)
        savings_green.deposit(6 * E18, whale, sender=whale)
        savings_green.deposit(4 * E18, alice, sender=whale)
        snap = (
            savings_green.balanceOf(alice),
            savings_green.totalSupply(),
            savings_green.totalAssets(),
        )
        savings_green.setBlacklist(alice, True, sender=switchboard.address)
        with boa.reverts("sender blacklisted"):
            savings_green.burn(0, sender=alice)
        with boa.reverts("sender blacklisted"):
            savings_green.burn(E18, sender=alice)
        assert (
            savings_green.balanceOf(alice),
            savings_green.totalSupply(),
            savings_green.totalAssets(),
        ) == snap

        green_token.transfer(alice, 2 * E18, sender=whale)
        ripe_token.transfer(alice, 2 * E18, sender=whale)
        green_token.setBlacklist(alice, True, sender=switchboard.address)
        ripe_token.setBlacklist(alice, True, sender=switchboard.address)
        assert green_token.burn(E18, sender=alice)
        assert ripe_token.burn(E18, sender=alice)


def test_g12_impl_green_only_vault_burn_guard_and_hq_admission(
    green_token,
    ripe_token,
    savings_green,
    switchboard,
    governance,
    whale,
    ripe_hq,
):
    """GREEN-only vault-backing guard. HQ with savingsGreen()==empty returns
    False; HQ missing the savingsGreen() getter reverts on staticcall."""
    with boa.env.anchor():
        green_token.approve(savings_green, MAX_UINT256, sender=whale)
        savings_green.deposit(5 * E18, whale, sender=whale)
        vault_green = green_token.balanceOf(savings_green)
        green_supply = green_token.totalSupply()
        sg_supply = savings_green.totalSupply()
        assets = savings_green.totalAssets()
        pps = savings_green.pricePerShare()
        green_token.setBlacklist(savings_green.address, True, sender=switchboard.address)
        with boa.reverts("cannot burn vault backing"):
            green_token.burnBlacklistTokens(savings_green.address, sender=governance.address)
        assert green_token.balanceOf(savings_green) == vault_green
        assert green_token.totalSupply() == green_supply
        assert savings_green.totalSupply() == sg_supply
        assert savings_green.totalAssets() == assets
        assert savings_green.pricePerShare() == pps
        green_token.setBlacklist(savings_green.address, False, sender=switchboard.address)

        mock = boa.loads(ASSET_MOCK, green_token.address)
        green_token.transfer(mock.address, 2 * E18, sender=whale)
        green_token.setBlacklist(mock.address, True, sender=switchboard.address)
        assert green_token.burnBlacklistTokens(mock.address, sender=governance.address)
        assert green_token.balanceOf(mock.address) == 0

        ripe_token.transfer(savings_green.address, 3 * E18, sender=whale)
        ripe_token.setBlacklist(savings_green.address, True, sender=switchboard.address)
        assert ripe_token.burnBlacklistTokens(savings_green.address, sender=governance.address)
        assert ripe_token.balanceOf(savings_green.address) == 0

        empty_ptr = boa.loads(
            HQ_EMPTY_SAVINGS_GREEN,
            governance.address,
            green_token.address,
            ripe_token.address,
            ZERO_ADDRESS,
        )
        assert not green_token.isValidNewRipeHq(empty_ptr.address)

        missing = boa.loads(
            HQ_MISSING_SAVINGS_GREEN,
            governance.address,
            green_token.address,
            ripe_token.address,
        )
        with boa.reverts():
            green_token.isValidNewRipeHq(missing.address)


@pytest.mark.parametrize(
    "gate,reason",
    (
        ("pause", "token paused"),
        ("owner", "owner blacklisted"),
        ("spender", "spender blacklisted"),
    ),
    ids=("pause", "owner-blacklist", "spender-blacklist"),
)
@pytest.mark.parametrize(
    "method",
    ("approve0", "decrease", "permit0"),
    ids=("approve0", "decrease", "permit0"),
)
def test_g12_impl_revoke_to_zero_while_gated(
    green_token,
    switchboard,
    governance,
    whale,
    bob,
    ripe_hq,
    gate,
    method,
    reason,
):
    """One gate × one revoke method, from a live nonzero allowance.
    permit(..., 0) also asserts nonce increment."""
    owner = Account.create()
    with boa.env.anchor():
        green_token.transfer(owner.address, 4 * E18, sender=whale)
        green_token.approve(bob, 3 * E18, sender=owner.address)
        assert green_token.allowance(owner.address, bob) == 3 * E18, (
            f"{gate}/{method}: expected live allowance before revoke"
        )

        if gate == "pause":
            green_token.pause(True, sender=governance.address)
        elif gate == "owner":
            green_token.setBlacklist(owner.address, True, sender=switchboard.address)
        else:
            green_token.setBlacklist(bob, True, sender=switchboard.address)

        with boa.reverts():
            green_token.transferFrom(owner.address, whale, E18, sender=bob)

        if method == "approve0":
            assert green_token.approve(bob, 0, sender=owner.address)
        elif method == "decrease":
            assert green_token.decreaseAllowance(bob, 3 * E18, sender=owner.address)
        else:
            nonce0 = green_token.nonces(owner.address)
            sig0, dl0 = _sign(green_token, owner, bob, 0)
            assert green_token.permit(owner.address, bob, 0, dl0, sig0, sender=bob)
            assert green_token.nonces(owner.address) == nonce0 + 1, (
                f"{gate}/{method}: permit(..., 0) must increment nonce"
            )

        assert green_token.allowance(owner.address, bob) == 0, (
            f"{gate}/{method}: allowance must be zero after revoke"
        )
        with boa.reverts():
            green_token.transferFrom(owner.address, whale, E18, sender=bob)
        with boa.reverts(reason):
            green_token.approve(bob, E18, sender=owner.address)
        with boa.reverts(reason):
            green_token.increaseAllowance(bob, E18, sender=owner.address)
        sig_nz, dl_nz = _sign(green_token, owner, bob, E18)
        with boa.reverts(reason):
            green_token.permit(owner.address, bob, E18, dl_nz, sig_nz, sender=bob)

        if gate == "pause":
            green_token.pause(False, sender=governance.address)
        elif gate == "owner":
            green_token.setBlacklist(owner.address, False, sender=switchboard.address)
        else:
            green_token.setBlacklist(bob, False, sender=switchboard.address)

        with boa.reverts("insufficient allowance"):
            green_token.transferFrom(owner.address, whale, E18, sender=bob)
        green_token.approve(bob, E18, sender=owner.address)
        assert green_token.transferFrom(owner.address, whale, E18, sender=bob), (
            f"{gate}/{method}: fresh post-gate approval must restore delegated use"
        )
