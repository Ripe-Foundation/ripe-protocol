import requests
import json
import time

api_url = "https://api.etherscan.io/v2/api"

chain_ids = {
    "eth-mainnet": 1,
    "eth-goerli": 5,
    "eth-sepolia": 11155111,
    "base-mainnet": 8453,
    "base-goerli": 84532,
    "base-sepolia": 84532,
}


contract_base_url = {
    "eth-mainnet": "https://etherscan.io/address/",
    "eth-goerli": "https://goerli.etherscan.io/address/",
    "eth-sepolia": "https://sepolia.etherscan.io/address/",
    "base-mainnet": "https://basescan.org/address/",
    "base-goerli": "https://goerli.basescan.org/address/",
    "base-sepolia": "https://sepolia.basescan.org/address/",
}


def is_contract_verified(api_key: str, contract_address: str, chain: str) -> bool:
    """Check if contract is already verified"""
    chain_id = chain_ids.get(chain, chain_ids["eth-mainnet"])

    params = {
        "chainid": chain_id,
        "apikey": api_key,
        "module": "contract",
        "action": "getabi",
        "address": contract_address,
    }

    response = requests.get(api_url, params=params)
    result = response.json()

    return result.get("status") == "1"


def verify_from_manifest(api_key: str, contract_name: str, manifest_data: dict, chain: str) -> bool:
    """Verify contract using manifest data"""

    print("Address: ", manifest_data["address"], 'url: ', contract_base_url[chain] + manifest_data["address"])

    # Check if already verified
    if is_contract_verified(api_key, manifest_data["address"], chain):
        return True

    # Prepare verification request
    contract_file = next(iter(manifest_data["solc_json"]["sources"].keys()))

    chain_id = chain_ids.get(chain, chain_ids["eth-mainnet"])
    params = {
        "apikey": api_key,
        "module": "contract",
        "action": "verifysourcecode",
        "sourceCode": json.dumps(manifest_data["solc_json"]),
        "contractaddress": manifest_data["address"],
        "codeformat": "vyper-json",
        "contractname": f"{contract_file}:{contract_name}",  # Format: contractfile.vy:contractname
        "compilerversion": "vyper:0.4.3",
        "constructorArguements": manifest_data.get("args", ""),
        "optimizationUsed": "1",
        "runs": "200",
        "evmversion": ""
    }

    try:
        # Submit verification request
        response = requests.post(api_url, params={"chainid": chain_id}, data=params)
        result = response.json()

        if result["status"] != "1":
            print(f"Verification submission failed: {result['result']}")
            return False

        guid = result["result"]
        print(f"Verification submitted. GUID: {guid}")

        # Check verification status
        check_params = {
            "chainid": chain_id,
            "apikey": api_key,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": guid,
        }

        # Poll for verification result
        for _ in range(10):  # Try 10 times
            time.sleep(5)  # Wait 5 seconds between checks
            check_response = requests.get(api_url, params=check_params)
            check_result = check_response.json()

            if check_result["result"] == "Pass - Verified":
                print(f"{contract_name} verified successfully!")
                return True
            elif check_result["result"] != "Pending in queue":
                print(f"Verification failed: {check_result['result']}")
                # Print more details if available
                if "message" in check_result:
                    print(f"Error message: {check_result['message']}")
                return False

        print("Verification timed out")
        return False

    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False
