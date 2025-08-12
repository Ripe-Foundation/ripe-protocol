import os
from datetime import datetime, timedelta

import httpx
from ape import Contract, project
from ape.types import HexBytes
from silverback import SilverbackBot

bot = SilverbackBot()

prices = project.PythPrices.deployments[-1]

ASSET = Contract(os.environ["ASSET_ADDRESS"])
PRICE_FEED_ID = prices.feedConfig(ASSET).feedId

HEARTBEAT_TIMEOUT = timedelta(seconds=int(os.environ.get("HEARTBEAT_TIMEOUT", "3600")))
PRICE_CHANGE_THRESHOLD = float(
    os.environ.get("PRICE_CHANGE_THESHOLD", "5.0")
)  # percent


async def check_and_update_pricefeed() -> dict[str, int | float]:
    result = await bot.state.pyth_api.get(
        "/updates/price/latest", params={"ids[]": [PRICE_FEED_ID.hex()]}
    )
    result.raise_for_status()
    data = result.json()
    current_price = int(data["parsed"][0]["price"]["price"])
    published_time = datetime.fromtimestamp(data["parsed"][0]["price"]["publish_time"])

    if (  # Update if:
        # 1) Time since last update was greater than a threshold
        published_time - bot.state.last_update > HEARTBEAT_TIMEOUT
        # 2) Price change % of most recent update was greater than a threshold
        or (abs(current_price - bot.state.last_price) / bot.state.last_price)
        > PRICE_CHANGE_THRESHOLD / 100
    ):
        prices.updatePythPrice(
            HexBytes(data["binary"]["data"][0]),
            sender=bot.signer,
            confirmations_required=0,
        )
        bot.state.last_update = published_time
        bot.state.last_price = current_price

    return dict(current_price=current_price)


@bot.on_startup()
async def set_initial_conds(_):
    bot.state.pyth_api = httpx.AsyncClient(
        base_url="https://hermes.pyth.network/v2",
        transport=httpx.AsyncHTTPTransport(retries=10),
    )

    # TODO: delete
    result = await bot.state.pyth_api.get(
        "/updates/price/latest", params={"ids[]": [PRICE_FEED_ID.hex()]}
    )
    result.raise_for_status()
    data = result.json()
    bot.state.last_price = int(data["parsed"][0]["price"]["price"])
    bot.state.last_update = datetime.fromtimestamp(
        data["parsed"][0]["price"]["publish_time"]
    )

    # bot.state.last_update = prices.PythPriceUpdated[-1].transaction.datetime
    # bot.state.last_price = prices.getPrice(ASSET)
    return await check_and_update_pricefeed()


@bot.cron(os.environ.get("HEARTBEAT_CHECK_CRON", "0 * * * *"))  # defaults to every hour
async def check_heartbeat(_):
    return await check_and_update_pricefeed()
