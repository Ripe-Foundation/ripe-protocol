

ADDYS = {
    "base": {
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
    "sepolia": {
        # important tokens / representations
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "BTC": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
        "USDC": "0x611ce0729f6C052f49536c84a8fD717E619D5dc6",
        "CBBTC": "0x003d1beA6B9C5193cDA8d747A5362eD2932a35d0",
        "GOVERNANCE": "0xa6AC77Fb1Ac34d35F852456560bAef2d77239dcF",
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
    "sepolia": {
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
