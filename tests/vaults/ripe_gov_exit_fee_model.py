"""Independent test model for RipeGov early-exit accounting."""

DECIMAL_OFFSET = 10**8
HUNDRED_PERCENT = 100_00
UINT256_MAX = 2**256 - 1


class UInt256Overflow(ArithmeticError):
    pass


def claim(shares, total_shares, total_balance):
    """Return the SharesVault floored asset claim without calling production code."""
    return shares * (total_balance + 1) // (total_shares + DECIMAL_OFFSET)


def target_claim(claim_before, exit_fee):
    """Return the floored fee-adjusted target claim."""
    return claim_before * (HUNDRED_PERCENT - exit_fee) // HUNDRED_PERCENT


def maximal_retained_shares(
    user_shares_before,
    remaining_shares,
    total_balance,
    target,
):
    """Find the largest attainable post-release balance by monotonic search.

    This is intentionally an inequality oracle, not a rearrangement of the
    production closed form.
    """
    low = 0
    high = user_shares_before
    while low < high:
        candidate = (low + high + 1) // 2
        candidate_claim = claim(
            candidate,
            remaining_shares + candidate,
            total_balance,
        )
        if candidate_claim <= target:
            low = candidate
        else:
            high = candidate - 1
    return low


def assert_exact_exit_claim(
    user_shares_before,
    total_shares_before,
    total_balance,
    exit_fee,
    user_shares_after,
    total_shares_after,
):
    """Assert production early-exit accounting, including full-fee complete burn."""
    if exit_fee == HUNDRED_PERCENT:
        assert user_shares_after == 0
        assert total_shares_after == total_shares_before - user_shares_before
        return

    claim_before = claim(user_shares_before, total_shares_before, total_balance)
    target = target_claim(claim_before, exit_fee)
    remaining_shares = total_shares_before - user_shares_before
    expected = maximal_retained_shares(
        user_shares_before,
        remaining_shares,
        total_balance,
        target,
    )
    assert user_shares_after == expected
    assert total_shares_before - total_shares_after == (
        user_shares_before - user_shares_after
    )
    assert claim(user_shares_after, total_shares_after, total_balance) <= target
    if user_shares_after < user_shares_before:
        assert target < claim(
            user_shares_after + 1,
            total_shares_after + 1,
            total_balance,
        )


def _checked_add(left, right):
    result = left + right
    if result > UINT256_MAX:
        raise UInt256Overflow("uint256 addition overflow")
    return result


def _checked_sub(left, right):
    if right > left:
        raise UInt256Overflow("uint256 subtraction underflow")
    return left - right


def _checked_mul(left, right):
    result = left * right
    if result > UINT256_MAX:
        raise UInt256Overflow("uint256 multiplication overflow")
    return result


def checked_target_claim(claim_before, exit_fee):
    numerator = _checked_mul(claim_before, HUNDRED_PERCENT - exit_fee)
    return numerator // HUNDRED_PERCENT


def checked_shares_to_amount(shares, total_shares, total_balance):
    numerator = _checked_mul(shares, _checked_add(total_balance, 1))
    denominator = _checked_add(total_shares, DECIMAL_OFFSET)
    return numerator // denominator


def checked_amount_to_shares(
    amount,
    total_shares,
    total_balance,
    should_round_up,
):
    numerator = _checked_mul(amount, _checked_add(total_shares, DECIMAL_OFFSET))
    denominator = _checked_add(total_balance, 1)
    shares = numerator // denominator
    if should_round_up and numerator % denominator != 0:
        shares = _checked_add(shares, 1)
    return shares


def checked_closed_form_retained_shares(
    user_shares,
    total_shares,
    total_balance,
    exit_fee,
):
    """Model the production operation sequence with checked uint256 arithmetic.

    Maximality is verified by ``maximal_retained_shares``; this separate model
    exists only to characterize the checked-arithmetic boundaries of the
    closed-form implementation.
    """
    claim_before = checked_shares_to_amount(
        user_shares,
        total_shares,
        total_balance,
    )
    if exit_fee == HUNDRED_PERCENT:
        return 0
    if claim_before == 0:
        raise ValueError("no claim")

    target = checked_target_claim(claim_before, exit_fee)
    claim_ceiling = _checked_add(target, 1)
    remaining_shares = _checked_sub(total_shares, user_shares)
    virtual_total_balance = _checked_sub(total_balance, claim_ceiling)
    exclusive_upper_bound = checked_amount_to_shares(
        claim_ceiling,
        remaining_shares,
        virtual_total_balance,
        True,
    )
    return _checked_sub(exclusive_upper_bound, 1)
