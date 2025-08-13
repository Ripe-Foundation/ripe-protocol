from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS
from web3 import Web3
from scripts.utils.safe_account import SafeAccount


def migrate(migration: Migration):
    ripe_gov = migration.get_contract("RipeGov")
    ripe_token = migration.get_address("RipeToken")
    ripe_lp_token = '0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9'

    w3 = Web3(Web3.HTTPProvider(migration.rpc()))
    logs = w3.eth.get_logs({
        'address': ripe_gov.address,
        'fromBlock': 0,
        'toBlock': 'latest',
        'topics': ['0x9921dca351cd680bd40e27fee8874329e29fa22138c6c9f33ede3bb72ffcb815']
    })

    # Extract unique wallet addresses from logs
    ripe_users = set()
    ripe_lp_users = set()

    for log in logs:
        # Extract user address from topic 1 (remove padding) and convert to checksum
        user_address = Web3.to_checksum_address("0x" + log['topics'][1].hex()[-40:])
        asset_address = Web3.to_checksum_address("0x" + log['topics'][2].hex()[-40:])
        if asset_address.lower() == ripe_token.lower():
            ripe_users.add(user_address)
        else:
            ripe_lp_users.add(user_address)

    print("ripe_users", len(ripe_users))
    print("ripe_lp_users", len(ripe_lp_users))

    balances = []

    ripe_count = 0
    ripe_issues = 0
    for user in ripe_users:
        balance = ripe_gov.getUserLootBoxShare(user, ripe_token)
        if balance == 0:
            continue

        ripe_count += 1
        if balance < 1000000000:
            ripe_issues += 1
            balances.append((user, ripe_token, balance))

    lp_count = 0
    lp_issues = 0
    for user in ripe_lp_users:
        balance = ripe_gov.getUserLootBoxShare(user, ripe_lp_token)
        if balance == 0:
            continue
        lp_count += 1
        if balance < 1000000000:
            lp_issues += 1
            balances.append((user, ripe_lp_token, balance))

    print("ripe_count", ripe_count)
    print("ripe_issues", ripe_issues)
    print("lp_count", lp_count)
    print("lp_issues", lp_issues)
    print(len(balances))

    # safe_account = SafeAccount(
    #     migration.blueprint().ADDYS["GOVERNANCE"],
    #     migration.rpc(),
    # )

    # # Contract ABI for updateDepositPoints
    # abi = [{
    #     "type": "function",
    #     "inputs": [
    #         {"name": "_user", "type": "address"},
    #         {"name": "_vaultId", "type": "uint256"},
    #         {"name": "_asset", "type": "address"}
    #     ],
    #     "name": "updateDepositPoints",
    #     "payable": False
    # }]

    # contract = w3.eth.contract(
    #     address=migration.get_address("SwitchboardCharlie"),
    #     abi=abi
    # )

    # transactions = []
    # for user, asset, balance in balances:
    #     # Encode the method call WITHOUT gas estimation
    #     # Use encodeABI instead of build_transaction to avoid gas estimation
    #     data = contract.encode_abi('updateDepositPoints', [user, 2, asset])

    #     tx = {
    #         'to': '0xB96D9862838f17Ca51603EEECd54E99f33D3461d',
    #         'value': 0,
    #         'data': data,
    #         'operation': 0
    #     }
    #     transactions.append(tx)

    # print(f"Created {len(transactions)} transactions")
    # print(f"First transaction: {transactions[0] if transactions else 'No transactions'}")

    # # Now you can use these transactions with your batch method
    # if transactions:
    #     print("Ready to send batch transactions!")
    #     # Uncomment when you're ready to send:
    #     result = safe_account.send_batch_transactions(transactions)
    #     print(f"Batch result: {result}")
