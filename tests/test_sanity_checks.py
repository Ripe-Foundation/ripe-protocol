import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256


def test_savings_green(
    green_token,
    savings_green,
    whale,
    sally,
):
    # token
    assert savings_green.asset() == green_token.address
    assert savings_green.totalAssets() == 0

    # deposit
    amount = 1_000 * EIGHTEEN_DECIMALS
    green_token.approve(savings_green, amount, sender=whale)
    assert savings_green.deposit(amount, sender=whale) != 0

    assert savings_green.totalAssets() == amount
    assert green_token.balanceOf(savings_green) == amount
    sgreen_bal = savings_green.balanceOf(whale)
    assert sgreen_bal != 0

    # transfer sgreen to sally
    savings_green.transfer(sally, sgreen_bal, sender=whale)
    assert savings_green.balanceOf(sally) == sgreen_bal
    assert savings_green.balanceOf(whale) == 0

    # withdraw
    assert savings_green.redeem(MAX_UINT256, sender=sally) == amount
    assert savings_green.balanceOf(sally) == 0
    assert green_token.balanceOf(sally) == amount
    assert green_token.balanceOf(savings_green) == 0


def test_control_room_utils(
    control_room_data,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    alpha_token,
):
    # general config
    setGeneralConfig(7, 14, 0, False, True)
    gen_config = control_room_data.genConfig()
    assert gen_config.perUserMaxVaults == 7
    assert gen_config.perUserMaxAssetsPerVault == 14
    assert gen_config.canDeposit == False
    assert gen_config.canWithdraw == True

    # general debt config
    setGeneralDebtConfig(50, 100, 5, 20, 10, 500)
    gen_debt_config = control_room_data.genDebtConfig()
    assert gen_debt_config.perUserDebtLimit == 50
    assert gen_debt_config.globalDebtLimit == 100
    assert gen_debt_config.minDebtAmount == 5
    assert gen_debt_config.numAllowedBorrowers == 20
    assert gen_debt_config.maxBorrowPerInterval == 10
    assert gen_debt_config.numBlocksPerInterval == 500
    assert gen_debt_config.genAuctionParams.hasParams == True
    
    # asset config
    setAssetConfig(alpha_token, 44, 66, 100, 200)
    asset_config = control_room_data.assetConfig(alpha_token)
    assert asset_config.stakersPointsAlloc == 44
    assert asset_config.voterPointsAlloc == 66
    assert asset_config.perUserDepositLimit == 100
    assert asset_config.globalDepositLimit == 200
    assert asset_config.debtTerms.ltv == 50_00

    # ripe rewards config
    setRipeRewardsConfig(True, 10, 20, 30, 40, 50)
    rewards_config = control_room_data.rewardsConfig()
    assert rewards_config.arePointsEnabled == True
    assert rewards_config.ripePerBlock == 10
    assert rewards_config.borrowersAlloc == 20
    assert rewards_config.stakersAlloc == 30
    assert rewards_config.votersAlloc == 40
    assert rewards_config.genDepositorsAlloc == 50

    # total points allocs
    total_points_allocs = control_room_data.totalPointsAllocs()
    assert total_points_allocs.stakersPointsAllocTotal == 44
    assert total_points_allocs.voterPointsAllocTotal == 66