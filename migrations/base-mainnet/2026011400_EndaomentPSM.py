from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    endaoment_psm = migration.deploy(
        "EndaomentPSM",
        hq,
        43_200,  # 1 day in blocks
        0,  # mint fee
        100_000 * 10**18,  # max interval mint
        0,  # redeem fee
        100_000 * 10**18,  # max interval redeem
        migration.blueprint().CORE_TOKENS["USDC"],
        13,  # usdc yield lego id
        '0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf',  # usdc yield vault token
    )
