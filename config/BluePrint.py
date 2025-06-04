ADDYS = {
    "base": {
        "CURVE_ADDRESS_PROVIDER": "0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98",
        "CURVE_STABLE_FACTORY": "0xd2002373543Ce3527023C75e7518C274A51ce712",
        "CURVE_CRYPTO_FACTORY": "0xc9Fe0C63Af9A39402e8a5514f9c43Af0322b665F",
        # default chainlink feeds
        "CHAINLINK_ETH_USD": "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70",
        "CHAINLINK_BTC_USD": "0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F",
        # important tokens / representations
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "BTC": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
    },
    "local": {
        # important tokens / representations
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "BTC": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
    },
}


PARAMS = {
    "base": {
        # ripe hq - gov changes (blocks)
        "RIPE_HQ_MIN_GOV_TIMELOCK": 43_200,  # 1 day on Base
        "RIPE_HQ_MAX_GOV_TIMELOCK": 302_400,  # 7 days on Base
        # ripe hq - registry changes (blocks)
        "RIPE_HQ_MIN_REG_TIMELOCK": 21_600,  # 12 hours on Base
        "RIPE_HQ_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
        # tokens (green / ripe)
        "MIN_HQ_CHANGE_TIMELOCK": 43_200,  # 1 day on Base
        "MAX_HQ_CHANGE_TIMELOCK": 302_400,  # 7 days on Base
        # price desk (timestamps, not blocks!)
        "PRICE_DESK_MIN_STALE_TIME": 60 * 5,  # 5 mins
        "PRICE_DESK_MAX_STALE_TIME": 60 * 60 * 24 * 3,  # 3 days
        # price desk (blocks)
        "PRICE_DESK_MIN_REG_TIMELOCK": 21_600,  # 12 hours on Base
        "PRICE_DESK_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
        # vault book (blocks)
        "VAULT_BOOK_MIN_REG_TIMELOCK": 21_600,  # 12 hours on Base
        "VAULT_BOOK_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
    },
    "local": {
        # ripe hq - gov changes (blocks)
        "RIPE_HQ_MIN_GOV_TIMELOCK": 43_200,
        "RIPE_HQ_MAX_GOV_TIMELOCK": 302_400,
        # ripe hq - registry changes (blocks)
        "RIPE_HQ_MIN_REG_TIMELOCK": 21_600,
        "RIPE_HQ_MAX_REG_TIMELOCK": 302_400,
        # tokens (green / ripe)
        "MIN_HQ_CHANGE_TIMELOCK": 43_200,
        "MAX_HQ_CHANGE_TIMELOCK": 302_400,
        # price desk (timestamps, not blocks!)
        "PRICE_DESK_MIN_STALE_TIME": 60 * 5,
        "PRICE_DESK_MAX_STALE_TIME": 60 * 60 * 24 * 3,
        # price desk (blocks)
        "PRICE_DESK_MIN_REG_TIMELOCK": 21_600,
        "PRICE_DESK_MAX_REG_TIMELOCK": 302_400,
        # vault book (blocks)
        "VAULT_BOOK_MIN_REG_TIMELOCK": 21_600,
        "VAULT_BOOK_MAX_REG_TIMELOCK": 302_400,
    },
}



CORE_TOKENS = {
    "base": {
        # stables
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDBC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
        "USDS": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc",
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "EURC": "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42",
        "CRVUSD": "0x417ac0e078398c154edfadd9ef675d30be60af93",
        "GHO": "0x6Bb7a212910682DCFdbd5BCBb3e28FB4E8da10Ee",
        "SUSDS": "0x5875eEE11Cf8398102FdAd704C9E96607675467a",
        # eth
        "WETH": "0x4200000000000000000000000000000000000006",
        "WSTETH": "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452",
        "CBETH": "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",
        "WEETH": "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
        "EZETH": "0x2416092f143378750bb29b79eD961ab195CcEea5",
        "RETH": "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c",
        "WRSETH": "0xEDfa23602D0EC14714057867A78d01e94176BEA0",
        # btc
        "CBBTC": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        "TBTC": "0x236aa50979d5f3de3bd1eeb40e81137f22ab794b",
        "LBTC": "0xecAc9C5F704e954931349Da37F60E39f515c11c1",
        # other
        "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
        "WELL": "0xA88594D404727625A9437C3f886C7643872296AE",
        "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
    },
}


CURVE_PARAMS = {
    "base": {
        # green pool parameters
        "GREEN_POOL_NAME": "GREEN/USDC Pool",
        "GREEN_POOL_SYMBOL": "GREEN/USDC",
        "GREEN_POOL_A": 100,
        "GREEN_POOL_FEE": 4000000,
        "GREEN_POOL_OFFPEG_MULTIPLIER": 20000000000,
        "GREEN_POOL_MA_EXP_TIME": 600,
        # ripe pool params
        "RIPE_POOL_NAME": "RIPE/WETH Pool",
        "RIPE_POOL_SYMBOL": "RIPE/WETH",
        "RIPE_POOL_A": 2700000,
        "RIPE_POOL_GAMMA": 1300000000000,
        "RIPE_POOL_MID_FEE": 2999999,
        "RIPE_POOL_OUT_FEE": 80000000,
        "RIPE_POOL_FEE_GAMMA": 350000000000000,
        "RIPE_POOL_EXTRA_PROFIT": 100000000000,
        "RIPE_POOL_ADJ_STEP": 100000000000,
        "RIPE_POOL_MA_EXP_TIME": 600,
        "RIPE_POOL_INIT_PRICE": 10 ** 13,
    },
}


WHALES = {
    "base": {
        "usdc": "0x0B0A5886664376F59C351ba3f598C8A8B4D0A6f3",
        "weth": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
    },
}