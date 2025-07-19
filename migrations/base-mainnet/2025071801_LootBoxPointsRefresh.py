from scripts.utils import log
from scripts.utils.migration import Migration
from web3 import Web3


def get_users(migration: Migration):
    training_wheels = migration.get_contract("TrainingWheels")
    w3 = Web3(Web3.HTTPProvider(migration.rpc()))
    logs = w3.eth.get_logs({
        'address': training_wheels.address,
        'fromBlock': 0,
        'toBlock': 'latest',
        'topics': ['0xdd4795cf306d6af3e71f88ee4848ae18eae42903a3493efe10096b29b4b5c1ae']
    })

    # Extract unique wallet addresses from logs
    unique_addresses = set()

    for log in logs:
        # Extract user address from topic 1 (remove padding)
        user_address = "0x" + log['topics'][1].hex()[-40:]
        unique_addresses.add(user_address)

    # Convert set to sorted list
    return sorted(list(unique_addresses))


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()
    ledger = migration.get_contract("Ledger")

    users = get_users(migration)

    assets = [
        [1, migration.get_address("SavingsGreen"), migration.get_contract("StabilityPool")],
        [1, migration.get_address("GreenPool"), migration.get_contract("StabilityPool")],
        [2, migration.get_address("RipeToken"), migration.get_contract("RipeGov")],
        [2, migration.get_address("RipePool"), migration.get_contract("RipeGov")],
        [3, blueprint.CORE_TOKENS["USDC"], migration.get_contract("SimpleErc20")],
        [3, blueprint.CORE_TOKENS["WETH"], migration.get_contract("SimpleErc20")],
        [3, blueprint.CORE_TOKENS["CBBTC"], migration.get_contract("SimpleErc20")],
    ]

    users_to_reset = []
    assets_to_reset = []
    for asset in assets:
        assets_to_reset.append((asset[1], asset[0]))
        for user in users:
            if not ledger.isParticipatingInVault(user, asset[0]):
                continue
            if not asset[2].isUserInVaultAsset(user, asset[1]):
                continue
            users_to_reset.append((user, asset[1], asset[0]))

    migration.deploy(
        "Lootbox",
        hq,
    )

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    limit = 40
    for i in range(0, len(users_to_reset), limit):
        migration.execute(switchboard_delta.resetManyUserBalancePoints, users_to_reset[i:i+limit])
    migration.execute(switchboard_delta.resetManyAssetPoints, assets_to_reset)
    migration.execute(switchboard_delta.resetManyUserBorrowPoints, users)

    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.relinquishGov)
