"""Render the pinned borrower audit; RPC calls only retrieve token metadata."""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]


def amount(value, decimals=18):
    return format(Decimal(value) / Decimal(10) ** decimals, "f")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ordinary-trial", type=Path)
    args = parser.parse_args()
    report = json.loads(args.input.read_text())
    audit = report["borrower_audit"]
    assert audit["complete"], "Do not publish an incomplete borrower scan"
    load_dotenv(ROOT / ".env")
    web3 = Web3(Web3.HTTPProvider(os.environ["BASE_MAINNET_RPC_URL"]))
    assert web3.eth.chain_id == 8453
    assert web3.eth.get_block(report["block"]).hash.hex().removeprefix("0x") == report["block_hash"].removeprefix("0x")
    token_abi = [{"type": "function", "name": name, "inputs": [],
                  "outputs": [{"type": typ}], "stateMutability": "view"}
                 for name, typ in [("symbol", "string"), ("decimals", "uint8")]]
    affected = [u for u in audit["users"] if not u["healthy"] or u["locked"]]
    metadata = {}
    for address in sorted({p["asset"] for u in affected for p in u["positions"]}):
        token = web3.eth.contract(address=address, abi=token_abi)
        decimals = token.functions.decimals().call(block_identifier=report["block"])
        try:
            symbol = token.functions.symbol().call(block_identifier=report["block"])
        except Exception:
            symbol = address
        metadata[address] = {"symbol": symbol, "decimals": decimals}
    trials = {r["user"].lower(): r for r in report.get("isolated_legacy_blocker_trials", [])}
    ordinary = json.loads(args.ordinary_trial.read_text()) if args.ordinary_trial else None
    for user in affected:
        user["has_funded_positions"] = bool(user["positions"])
        user["legacy_trial"] = trials.get(user["user"].lower())
        if ordinary and ordinary.get("only_user", "").lower() == user["user"].lower():
            user["ordinary_trial"] = {"status": ordinary["status"],
                "error_frames": ordinary.get("error_frames", []),
                "migration": ordinary.get("ordinary_migration", {})}
        for position in user["positions"]:
            token = metadata[position["asset"]]
            position.update(token)
            position["token_amount"] = amount(position["amount"], token["decimals"])
    output = {"live_writes": False, "source_block": report["block"],
              "source_block_hash": report["block_hash"], "evaluation_block": audit["block"],
              "borrowers_checked": audit["borrowers_expected"], "errors": audit["errors"],
              "locked_depositors": audit["locked_depositors"],
              "funded_depositors_checked_for_locks": audit["funded_depositors_checked_for_locks"],
              "affected_users": affected, "all_borrowers": audit["users"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(output, indent=2) + "\n")
    lines = ["# Base borrower / migration blocker audit", "",
             f"Pinned Base block: **{report['block']:,}**. Debt evaluated on the local fork at "
             f"**{audit['block']:,}**, after the simulated registry timelock. Not a current live balance quote.", "",
             f"Checked all **{audit['borrowers_expected']} borrowers**, with no read errors, and "
             f"**{audit['funded_depositors_checked_for_locks']} funded depositors** for account locks.", "",
             "Amounts below are exact decimal conversions. Debt and borrowing capacity are in GREEN; "
             "collateral value is the CreditEngine's USD value, not the total market value of every deposit. "
             "A failed borrowing-LTV check does not by itself imply liquidation eligibility.", "",
             "Accounts with no funded positions have debt-health issues but no deposited position to migrate. "
             "This is exhaustive for the scanned debt-health/account-lock conditions, not every possible migration error.", ""]
    for u in affected:
        lines += [f"## {u['user']}", "",
                  f"- Current debt: **{amount(u['current_debt'])} GREEN**",
                  f"- Principal: {amount(u['stored_debt']['principal'])} GREEN",
                  f"- Borrowing capacity: {amount(u['max_debt'])} GREEN",
                  f"- Debt above capacity: {amount(u['debt_above_limit'])} GREEN",
                  f"- Eligible collateral value: ${amount(u['collateral_value'])}",
                  f"- Account locked: {u['locked']}; stored liquidation flag: {u['stored_debt']['inLiquidation']}", ""]
        if not u["positions"]:
            lines += ["**No funded vault positions in the reconciled census.**", ""]
        else:
            lines += ["| Vault | Asset | Deposited amount | Token address |", "| --- | --- | ---: | --- |"]
            for p in u["positions"]:
                lines.append(f"| {p['vault_id']} | {p['symbol']} | {p['token_amount']} | `{p['asset']}` |")
            lines.append("")
        if u["legacy_trial"]:
            lines += [f"Isolated RipeGov migration reverted: **{u['legacy_trial']['reverted']}**.", ""]
        if "ordinary_trial" in u:
            lines += [f"Isolated ordinary migration: **{u['ordinary_trial']['status']}** "
                      "(see JSON for the call trace).", ""]
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(f"Reported {len(affected)} unhealthy/locked borrowers; "
          f"{sum(bool(u['positions']) for u in affected)} with funded positions")


if __name__ == "__main__":
    main()
