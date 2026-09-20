"""Base upgrade rehearsal. All writes execute inside Titanoboa's local fork.

No wallet key, signing, network environment, or live transaction submission is
used. The report distinguishes deployments, compatibility probes and completed
migrations; successful deployment alone is never qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from contextlib import contextmanager

import boa
from boa.contracts.abi.abi_contract import ABIContractFactory
from dotenv import load_dotenv
import requests
from eth_utils import event_abi_to_log_topic, to_checksum_address
from eth_utils.abi import collapse_if_tuple
from eth_abi import decode, encode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.utils.base_activation import department_confirmation_order
from scripts.utils.fork_reports import (
    SANITIZER_VERSION, fingerprint, require_new_report, require_unoptimized, sanitize,
)
ZERO = "0x" + "00" * 20
HQ_IDS = {4: "Ledger", 5: "MissionControl", 6: "Switchboard", 7: "PriceDesk",
          8: "VaultBook", 9: "AuctionHouse", 10: "AuctionHouseNFT", 11: "Boardroom",
          12: "BondRoom", 13: "CreditEngine", 14: "Endaoment", 15: "HumanResources",
          16: "Lootbox", 17: "Teller", 18: "Deleverage", 19: "CreditRedeem",
          20: "TellerUtils", 21: "EndaomentFunds", 22: "EndaomentPSM"}


def plain(v):
    if hasattr(v, "_asdict"):
        return {k: plain(x) for k, x in v._asdict().items()}
    if hasattr(v, "address"):
        return str(v.address)
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, (tuple, list)):
        return [plain(x) for x in v]
    if isinstance(v, bytes):
        return "0x" + v.hex()
    return v


def error_text(error):
    try:
        return str(error)
    except Exception:
        try:
            return str(error.stack_trace.last_frame.pretty_vm_reason)
        except Exception:
            return type(error).__name__ + " (trace rendering failed)"


def error_frames(error):
    frames = []
    def visit(frame):
        c = frame.computation
        if c.is_error:
            frames.append({"address": "0x" + c.msg.code_address.hex(),
                "selector": "0x" + c.msg.data_as_bytes[:4].hex(),
                "error": repr(c._error), "output": "0x" + c.output.hex()})
        for child in frame.children:
            visit(child)
    if hasattr(error, "call_trace"):
        visit(error.call_trace)
    return frames


def decode_event(row, abi):
    """Reject malformed topic/data layouts rather than indexing blindly."""
    indexed = [entry for entry in abi["inputs"] if entry.get("indexed")]
    other = [entry for entry in abi["inputs"] if not entry.get("indexed")]
    if len(row["topics"]) != len(indexed) + 1:
        raise RuntimeError("EVENT_TOPIC_SHAPE:" + abi["name"])
    if row["topics"][0].lower() != ("0x" + event_abi_to_log_topic(abi).hex()).lower():
        raise RuntimeError("EVENT_SIGNATURE:" + abi["name"])
    result = {}
    for entry, topic in zip(indexed, row["topics"][1:]):
        result[entry["name"]] = decode([entry["type"]], bytes.fromhex(topic[2:]))[0]
    types = [collapse_if_tuple(entry) for entry in other]
    raw = bytes.fromhex(row["data"][2:])
    values = decode(types, raw)
    if encode(types, values) != raw:
        raise RuntimeError("EVENT_DATA_SHAPE:" + abi["name"])
    result.update((entry["name"], value) for entry, value in zip(other, values))
    return result


def permission_keys(logs, emitter_abis):
    users, pairs = set(), set()
    for row in logs:
        abi = emitter_abis.get(row["address"].lower(), {}).get(row["topics"][0].lower())
        if row["address"].lower() not in emitter_abis:
            continue  # Foreign same-signature events are not authority.
        if abi is None:
            raise RuntimeError("UNSUPPORTED_AUTHENTICATED_PERMISSION_EVENT")
        values = decode_event(row, abi)
        user = to_checksum_address(values["user"])
        users.add(user)
        if abi["name"] == "UserDelegationSet":
            pairs.add((user, to_checksum_address(values["delegate"])))
    return users, pairs


def remediation_sets(rows, locked_depositors):
    debt = [row["user"] for row in rows if not row["healthy"]]
    checks = [row["user"] for row in rows if not row["healthy"] or row["locked"]]
    return debt, list(dict.fromkeys(checks + list(locked_depositors)))


class Rehearsal:
    def __init__(self, rpc, block, output, *, overwrite=False):
        require_unoptimized()
        require_new_report(output, overwrite)
        self.rpc, self.block, self.output = rpc, block, output
        self.manifest = json.loads((ROOT / "migration_history/base-mainnet/v1/current-manifest.json").read_text())["contracts"]
        self.report = {"status": "incomplete", "live_writes": False, "block": block,
                       "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                       "deployments": {}, "probes": [], "completed_migrations": []}
        self.old, self.new = {}, {}
        self.report["sanitizer_version"] = SANITIZER_VERSION
        self.report["constructor_profile"] = "historical compatibility experiment, not staging qualification"

    def sanitized(self, value):
        return sanitize(plain(value), self.rpc, ROOT)

    @contextmanager
    def diagnostic_branch(self, name):
        if getattr(self, "_diagnostic_branch_active", False):
            raise RuntimeError("NESTED_DIAGNOSTIC_BRANCH_UNSUPPORTED")
        self._diagnostic_branch_active = True
        start = len(self.report.get("fork_transactions", []))
        try:
            with boa.env.anchor():
                yield
        finally:
            for row in self.report.get("fork_transactions", [])[start:]:
                row.update(branch_id=name, state_rolled_back=True)
            self._diagnostic_branch_active = False
            self.save()

    def read_saved_input(self, path, role):
        content = Path(path).read_bytes()
        self.report.setdefault("consumed_inputs", []).append({
            "role": role, "path": str(path), "sha256": hashlib.sha256(content).hexdigest()})
        return json.loads(content)

    def transact_expect(self, expected, fn, *args):
        actual = self.transact(fn, *args)
        if actual != expected:
            raise RuntimeError(f"UNEXPECTED_TRANSACTION_RESULT:{actual}:{expected}")
        return actual

    def save(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(json.dumps(self.sanitized(self.report), indent=2) + "\n")

    def rpc_read(self, method, params):
        assert method in {"eth_chainId", "eth_getBlockByNumber", "eth_getLogs"}
        response = requests.post(self.rpc, json={"jsonrpc": "2.0", "id": 1,
            "method": method, "params": params}, timeout=90)
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise RuntimeError(result["error"])
        return result["result"]

    def at(self, name, address=None):
        entry = self.manifest[name]
        return ABIContractFactory(name, entry["abi"]).at(address or entry["address"])

    def deploy(self, name, *args, path=None):
        print("Deploying", name, flush=True)
        if path is None:
            matches = list((ROOT / "contracts").rglob(name + ".vy"))
            assert len(matches) == 1, name
            path = matches[0]
        c = boa.load(str(path), *args)
        size = len(boa.env.get_code(c.address))
        assert size <= 24576, (name, size)
        self.new[name] = c
        self.report["deployments"][name] = {"address": str(c.address), "runtime_bytes": size,
            "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "constructor_args": plain(args), "constructor_profile": self.report["constructor_profile"]}
        self.save()
        return c

    def inventory(self):
        h = self.at("RipeHq")
        self.hq, self.gov = h, h.governance()
        self.report["governance"] = str(self.gov)
        self.report["hq_delay_blocks"] = h.registryChangeTimeLock()
        for i, name in HQ_IDS.items():
            self.old[name] = self.at(name, h.getAddr(i))
        self.report["active_hq"] = {n: str(c.address) for n, c in self.old.items()}
        self.vaults = {}
        book = self.old["VaultBook"]
        for i in range(1, book.getNumAddrs() + 1):
            address = book.getAddr(i)
            names = [n for n, v in self.manifest.items() if v["address"].lower() == str(address).lower()]
            assert names, (i, address)
            self.vaults[i] = self.at(names[0], address)
        l = self.old["Ledger"]
        self.report["ledger_before"] = {n: plain(getattr(l, n)()) for n in
            ["totalDebt", "badDebt", "ripeRewards", "globalDepositPoints", "globalBorrowPoints",
             "ripeAvailForRewards", "ripeAvailForHr", "ripeAvailForBonds"]}
        self.report["borrowers"] = {str(l.borrowers(i)): plain(l.userDebt(l.borrowers(i)))
            for i in range(1, l.getNumBorrowers() + 1)}
        self.report["vaults"] = {}
        for i, v in self.vaults.items():
            assets = [v.vaultAssets(j) for j in range(1, v.getNumVaultAssets() + 1)]
            self.report["vaults"][i] = {"address": str(v.address), "assets": {
                str(a): {"total_shares_or_balance": v.totalBalances(a)} for a in assets}}
        pool = self.vaults[1]
        claims = []
        for asset in self.report["vaults"][1]["assets"]:
            for index in range(1, pool.numClaimableAssets(asset)):
                claim_asset = pool.claimableAssets(asset, index)
                claims.append({"deposit_asset": asset, "claim_asset": str(claim_asset),
                               "raw_claim_balance": pool.claimableBalances(asset, claim_asset)})
        self.report["legacy_stability_claim_inventory"] = claims
        self.save()
        print("Inventory:", len(self.report["borrowers"]), "borrowers;", len(self.vaults), "vaults", flush=True)

    def logs(self, address, topics, start, end):
        return self.filtered_logs({"address": str(address), "topics": [topics]}, start, end)

    def filtered_logs(self, log_filter, start, end):
        """Bounded, adaptive retrieval; incomplete discovery always raises."""
        coverage = {"filter": log_filter, "start": start, "end": end,
                    "completed_ranges": [], "complete": False}
        self.report.setdefault("log_discovery", []).append(coverage)

        def fetch(lo, hi):
            rows = None
            error = RuntimeError("INVALID_LOG_RESPONSE")
            for attempt in range(4):
                try:
                    rows = self.rpc_read("eth_getLogs", [dict(log_filter, fromBlock=hex(lo), toBlock=hex(hi))])
                    break
                except (RuntimeError, requests.HTTPError) as e:
                    message = str(e).lower()
                    if "429" not in message and "rate limit" not in message and "throttl" not in message:
                        # Range errors are handled below; permanent errors propagate.
                        error = e
                        break
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
            try:
                if rows is None:
                    raise error
                coverage["completed_ranges"].append([lo, hi])
                return rows
            except RuntimeError as e:
                message = str(e).lower()
                if hi <= lo or not any(x in message for x in ["size", "limit", "range", "too many"]):
                    raise
                middle = (lo + hi) // 2
                return fetch(lo, middle) + fetch(middle + 1, hi)
        try:
            unique = {}
            for lo in range(start, end + 1, 50_000):
                for row in fetch(lo, min(end, lo + 49_999)):
                    unique[(row["blockHash"], row["transactionHash"], row["logIndex"])] = row
            coverage["complete"] = True
            return sorted(unique.values(), key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"], 16)))
        except Exception as e:
            coverage["error"] = self.sanitized(error_text(e))
            raise
        finally:
            self.save()

    def registry_history_addresses(self, registry, abi_name, slot):
        addresses = {str(registry.getAddr(slot)).lower()}
        events = [e for e in self.manifest[abi_name]["abi"] if e.get("type") == "event"
                  and e["name"] in ("NewAddressConfirmed", "AddressUpdateConfirmed")]
        if len(events) != 2:
            raise RuntimeError("REGISTRY_HISTORY_ABI_INCOMPLETE:" + abi_name)
        for event in events:
            rows = self.logs(registry.address, ["0x" + event_abi_to_log_topic(event).hex()], 0, self.block)
            for row in rows:
                if row["address"].lower() != str(registry.address).lower():
                    raise RuntimeError("FOREIGN_REGISTRY_LOG")
                decoded = decode_event(row, event)
                if decoded["regId"] == slot:
                    addresses.update(str(decoded[name]).lower() for name in ("addr", "newAddr", "prevAddr") if name in decoded)
        addresses.discard(ZERO)
        return addresses

    def batch_read(self, calls):
        """Pinned read-only RPC batches for the historical census, never fork writes."""
        values = []
        for offset in range(0, len(calls), 50):
            group = calls[offset:offset + 50]
            payload = [{"jsonrpc": "2.0", "id": i, "method": "eth_call", "params": [
                {"to": str(fn.contract.address), "data": "0x" + fn.prepare_calldata(*args).hex()},
                hex(self.block)]} for i, (fn, args) in enumerate(group)]
            result = requests.post(self.rpc, json=payload, timeout=90).json()
            assert isinstance(result, list), "RPC batch rejected"
            by_id = {r["id"]: r for r in result}
            for i, (fn, _) in enumerate(group):
                r = by_id[i]
                if "error" in r:
                    raise RuntimeError((fn.name, r["error"]))
                outputs = fn._abi["outputs"]
                decoded = decode([collapse_if_tuple(x) for x in outputs], bytes.fromhex(r["result"][2:]))
                value = decoded[0] if len(outputs) == 1 else decoded
                values.append(value)
        return values

    def census(self):
        self.report["positions"] = {}
        for vid, vault in self.vaults.items():
            print("Census vault", vid, flush=True)
            abi = next(v["abi"] for v in self.manifest.values() if v["address"].lower() == str(vault.address).lower())
            events = {}
            for e in abi:
                if e["type"] != "event":
                    continue
                indexed = [x for x in e["inputs"] if x.get("indexed")]
                slots = [j+1 for j, x in enumerate(indexed) if x["name"] in {"user", "fromUser", "toUser"}]
                if slots:
                    events["0x" + event_abi_to_log_topic(e).hex()] = slots
            assert events, vid
            logs = self.logs(vault.address, list(events), 0, self.block)
            users = set()
            for log in logs:
                for slot in events[log["topics"][0]]:
                    users.add(to_checksum_address("0x" + log["topics"][slot][-40:]))
            users = sorted(users)
            print("Found", len(users), "historical users; reading pinned state in batches", flush=True)
            counts = self.batch_read([(vault.getNumUserAssets, (u,)) for u in users])
            slots = [(u, j) for u, n in zip(users, counts) for j in range(1, n+1)]
            assets = self.batch_read([(vault.userAssets, slot) for slot in slots])
            keys = [(u, to_checksum_address(a)) for (u, _), a in zip(slots, assets)]
            shares = self.batch_read([(vault.userBalances, k) for k in keys])
            amounts = self.batch_read([(vault.getTotalAmountForUser, k) for k in keys])
            points = self.batch_read([(self.old["Ledger"].userDepositPoints, (u, vid, a)) for u, a in keys])
            gov = self.batch_read([(vault.userGovData, k) for k in keys]) if vid == 2 else [None]*len(keys)
            positions = {}
            for (u, a), s, amount, p, g in zip(keys, shares, amounts, points, gov):
                row = {"user": u, "asset": a, "shares": s, "amount": amount, "deposit_points": p}
                if g is not None:
                    row["gov_data"] = g
                positions[u + ":" + a] = row
            self.report["positions"][vid] = positions
            self.report["vaults"][vid]["census_users"] = len(users)
            self.reconcile_positions(vid, positions)
            self.save()
            print("Reconciled vault", vid, len(users), "historical users", len(positions), "registered positions", flush=True)

    def reconcile_positions(self, vid, positions):
        registered = {a.lower(): a for a in self.report["vaults"][vid]["assets"]}
        discovered = {r["asset"].lower(): r["asset"] for r in positions.values()}
        orphaned = set(discovered) - set(registered)
        checks = {}
        self.report.setdefault("census_reconciliation", {})[vid] = checks
        for key, asset in (registered | discovered).items():
            total = sum(r["shares"] for r in positions.values() if r["asset"].lower() == key)
            row = {"user_total": total, "orphaned": key in orphaned, "complete": False}
            checks[asset] = row
            try:
                expected = self.vaults[vid].totalBalances(asset)
                row["authoritative_total"] = expected
                row["complete"] = total == expected and not row["orphaned"]
            except Exception as e:
                row["error"] = self.sanitized(error_text(e))
        self.save()
        if not all(row["complete"] for row in checks.values()):
            raise RuntimeError(f"INCOMPLETE_CENSUS:{vid}")

    def transact(self, fn, *args, sender=None):
        name = fn.name if hasattr(fn, "name") else fn.fn_ast.name
        sender = self.gov if sender is None else sender
        gas_before = boa.env.get_gas_used()
        row = {"target": str(fn.contract.address), "method": name, "args": plain(args),
               "sender": str(sender), "block": boa.env.evm.patch.block_number,
               "state_rolled_back": False}
        self.report.setdefault("fork_transactions", []).append(row)
        try:
            result = fn(*args, sender=sender)
            row.update(call_reverted=False, result=plain(result))
        except Exception as exc:
            row.update(call_reverted=True, error=self.sanitized(error_text(exc)))
            raise
        finally:
            row["execution_gas"] = boa.env.get_gas_used() - gas_before
            self.save()
        if result is False:
            row["soft_failure"] = True
            self.save()
            raise RuntimeError("SOFT_FAILURE:" + name)
        return result

    def compatibility_probe(self):
        """Isolated core switch; treasury and user migrations are not claimed complete."""
        replacements = [5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20]
        try:
            confirmation_order = department_confirmation_order(replacements)
        except RuntimeError as error:
            raise RuntimeError(
                "BASE_COMPATIBILITY_PROBE_REQUIRES_FULL_UPDATE: current-source "
                "dependencies require scripts/base_full_update_fork.py; " + str(error)
            ) from error
        book, sb = self.new["VaultBook"], self.new["Switchboard"]
        for vid, v in self.vaults.items():
            self.transact(book.startAddNewAddressToRegistry, v.address, "Retained " + str(vid))
            self.transact_expect(vid, book.confirmNewAddressToRegistry, v.address)
        for vid, n in [(6, "StabilityPool"), (7, "RipeGov")]:
            self.transact(book.startAddNewAddressToRegistry, self.new[n].address, n)
            self.transact_expect(vid, book.confirmNewAddressToRegistry, self.new[n].address)
        for vid, suffix in enumerate(["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"], 1):
            c = self.new["Switchboard" + suffix]
            self.transact(sb.startAddNewAddressToRegistry, c.address, suffix)
            self.transact_expect(vid, sb.confirmNewAddressToRegistry, c.address)
        # Core integration diagnostic: stateful treasury departments deliberately
        # remain routed to the originals until their separate custody handoff.
        for i in replacements:
            pending = self.hq.pendingAddrUpdate(i)
            if pending[0] != ZERO:
                self.report.setdefault("existing_pending_hq_updates", {})[i] = plain(pending)
                self.save()
                if not getattr(self, "diagnose_replacing_pending", False):
                    raise RuntimeError(f"PENDING_HQ_UPDATE_REQUIRES_DISPOSITION:{i}")
                self.report["fork_only_alternate_pending_scenario"] = True
                self.transact(self.hq.cancelAddressUpdateToRegistry, i)
            self.transact(self.hq.startAddressUpdateToRegistry, i, self.new[HQ_IDS[i]].address)
        self.transact(self.hq.startAddNewAddressToRegistry, self.new["VaultMigrator"].address, "VaultMigrator")
        boa.env.time_travel(blocks=self.hq.registryChangeTimeLock(), block_delta=2)
        borrowers = list(self.report["borrowers"])
        sample = borrowers[:3]
        if "positions" in self.report:
            sample = list(dict.fromkeys([r["user"] for rows in self.report["positions"].values()
                                        for r in rows.values() if r["shares"]]))[:10] + sample
        sample = list(dict.fromkeys(sample))
        self.report["reward_sample"] = {"users": sample, "selection": "up to ten funded-position users plus first three borrowers; deduplicated; not complete continuity"}
        expected = {}
        borrow_expected = {}
        for u in sample:
            try:
                expected[u] = self.old["Lootbox"].getClaimableLoot(u)
            except Exception as e:
                expected[u] = {"legacy_error": type(e).__name__}
            borrow_expected[u] = self.old["Lootbox"].getClaimableBorrowLoot(u)
        # No block advances within this diagnostic switch, so old/new reward
        # reads have identical timestamps and stored Ledger balances.
        for i in confirmation_order:
            self.transact(self.hq.confirmAddressUpdateToRegistry, i)
        self.transact_expect(25, self.hq.confirmNewAddressToRegistry, self.new["VaultMigrator"].address)
        assert str(self.hq.getAddr(4)).lower() == str(self.old["Ledger"].address).lower()
        ledger = self.old["Ledger"]
        ledger_after = {n: plain(getattr(ledger, n)()) for n in self.report["ledger_before"]}
        debt_after = {u: plain(ledger.userDebt(u)) for u in self.report["borrowers"]}
        assert ledger_after == self.report["ledger_before"], "core switch changed Ledger globals"
        assert debt_after == self.report["borrowers"], "core switch changed stored borrower debt"
        self.report["core_storage_parity"] = {"ledger_globals_equal": True,
            "borrower_records_equal": True, "borrowers_checked": len(debt_after)}
        comparisons = []
        for u in sample:
            row = {"user": u, "before": expected[u]}
            row["borrow_before"] = borrow_expected[u]
            try:
                row["after"] = self.new["Lootbox"].getClaimableLoot(u)
                row["borrow_after"] = self.new["Lootbox"].getClaimableBorrowLoot(u)
                row["equal"] = row["before"] == row["after"] and row["borrow_before"] == row["borrow_after"]
            except Exception as e:
                row["error"] = self.sanitized(error_text(e))[:2000]
                row["equal"] = False
            comparisons.append(row)
        self.report["probes"].append({"name": "retained_ledger_reward_continuity",
            "results": comparisons, "passed": all(r["equal"] for r in comparisons)})
        self.report["status"] = "compatibility_probe_only_not_qualified"
        self.save()
        if not all(r["equal"] for r in comparisons):
            self.report.setdefault("blockers", []).append("REWARD_CONTINUITY_FAILED")

    def action(self, board, fn, *args):
        aid = self.transact(fn, *args)
        delay = board.actionTimeLock()
        if delay:
            boa.env.time_travel(blocks=delay, block_delta=2)
        self.transact(board.executePendingAction, aid)

    def borrower_audit(self):
        """Enumerate every current borrower, without stopping at unhealthy users."""
        ce, ledger = self.new["CreditEngine"], self.old["Ledger"]
        audit = {"block": boa.env.evm.patch.block_number,
                 "timestamp": boa.env.evm.patch.timestamp, "users": [], "errors": []}
        self.report["borrower_audit"] = audit
        for user in self.report["borrowers"]:
            row = {"user": user, "stored_debt": plain(ledger.userDebt(user)), "positions": []}
            try:
                terms = ce.getUserBorrowTerms(user, False)
                row.update(healthy=ce.hasGoodDebtHealth(user),
                           current_debt=ce.getUserDebtAmount(user),
                           collateral_value=terms[0], max_debt=terms[1],
                           current_terms=plain(terms), locked=ledger.isLockedAccount(user))
                row["debt_above_limit"] = max(0, row["current_debt"] - row["max_debt"])
                for vid, positions in self.report["positions"].items():
                    for position in positions.values():
                        if position["user"].lower() != user.lower() or not position["shares"]:
                            continue
                        p = dict(position, vault_id=vid)
                        p["amount"] = self.vaults[vid].getTotalAmountForUser(user, p["asset"])
                        row["positions"].append(p)
                audit["users"].append(row)
                print("Borrower", user, "healthy", row["healthy"], flush=True)
            except Exception as e:
                row["error"] = self.sanitized(error_text(e))[:1500]
                audit["errors"].append(row)
            self.save()
        # Cover account locks even for depositors with no current borrowing.
        depositors = sorted({p["user"] for ps in self.report["positions"].values()
                             for p in ps.values() if p["shares"]})
        locked = self.batch_read([(ledger.isLockedAccount, (u,)) for u in depositors])
        audit["funded_depositors_checked_for_locks"] = len(depositors)
        audit["locked_depositors"] = [u for u, flag in zip(depositors, locked) if flag]
        audit["borrowers_expected"] = len(self.report["borrowers"])
        audit["complete"] = len(audit["users"]) == audit["borrowers_expected"] and not audit["errors"]
        _, self.audit_candidates = remediation_sets(audit["users"], audit["locked_depositors"])
        self.save()

    def remediate_blockers(self):
        """Governance-funded repayments and an actual deleverage attempt, fork only."""
        main_user = "0x28E2b238a3a7634C6C7e23b895790505B1C31Cd0"
        if "borrower_audit" in self.report:
            assert self.report["borrower_audit"]["complete"]
            audit = self.report["borrower_audit"]
            users, self.audit_candidates = remediation_sets(audit["users"], audit["locked_depositors"])
        else:
            saved = self.read_saved_input(ROOT / "docs/chains/base/fork-rehearsal/borrower-blockers.json", "borrower_blockers")
            assert saved["source_block"] == self.block
            users, self.audit_candidates = remediation_sets(saved["affected_users"], saved["locked_depositors"])
        assert main_user.lower() in {u.lower() for u in users}, "main borrower status changed; review remediation"
        self.report["debt_remediation_users"] = users
        self.report["migration_check_users"] = self.audit_candidates
        if getattr(self, "audit_only_migrations", False):
            self.ordinary_candidate_users = {u.lower() for u in self.audit_candidates}
        mc, ce, teller, charlie = [self.new[n] for n in
                                 ["MissionControl", "CreditEngine", "Teller", "SwitchboardCharlie"]]
        green = self.at("GreenToken", self.hq.getAddr(1))
        result = {"caller": str(self.gov), "repayments": [],
                  "safe_green_before": green.balanceOf(self.gov)}
        self.report["remediation"] = result
        original_configs = {u: tuple(self.old["MissionControl"].userConfig(u)) for u in users}
        # Replay actual user policy lost by the diagnostic fresh MC constructor.
        for u, config in original_configs.items():
            if tuple(mc.userConfig(u)) != config:
                self.action(charlie, charlie.setUserConfig, u, config)
        if teller.isPaused():
            self.transact(charlie.pause, teller.address, False)
        before = ce.getUserDebtAmount(main_user)
        try:
            repaid = self.transact(teller.deleverageManyUsers, [(main_user, 5 * 10**18)])
            result["deleverage"] = {"repaid": repaid, "healthy_after": ce.hasGoodDebtHealth(main_user)}
        except Exception as e:
            result["deleverage"] = {"reverted": True, "error": self.sanitized(error_text(e))[:1500],
                                    "frames": error_frames(e)}
        result["deleverage"]["debt_before"] = before
        result["deleverage"]["debt_after"] = ce.getUserDebtAmount(main_user)
        self.save()
        if result["deleverage"].get("reverted"):
            # Governance is not automatically a trusted collateral operator.
            # Rehearse an explicit, temporary delegation, restored after the call.
            original = tuple(self.old["MissionControl"].userDelegation(main_user, self.gov))
            temporary = list(original)
            temporary[1] = True  # canBorrow is also the deleverage permission
            self.action(charlie, charlie.setUserDelegation, main_user, self.gov, tuple(temporary))
            sg = str(self.hq.getAddr(2))
            ripe = str(self.hq.getAddr(3))
            sg_before = self.vaults[1].getTotalAmountForUser(main_user, sg)
            ripe_before = self.vaults[2].getTotalAmountForUser(main_user, ripe)
            lock_before = tuple(self.vaults[2].userGovData(main_user, ripe))
            try:
                repaid = self.transact(teller.deleverageWithSpecificAssets, [(1, sg, 10**18)], main_user)
                result["delegated_deleverage"] = {"repaid": repaid,
                    "healthy_after": ce.hasGoodDebtHealth(main_user),
                    "debt_after": ce.getUserDebtAmount(main_user),
                    "sgreen_before": sg_before,
                    "sgreen_after": self.vaults[1].getTotalAmountForUser(main_user, sg)}
                assert self.vaults[2].getTotalAmountForUser(main_user, ripe) == ripe_before
                assert tuple(self.vaults[2].userGovData(main_user, ripe)) == lock_before
                result["delegated_deleverage"]["ripe_balance_and_lock_unchanged"] = True
            except Exception as e:
                result["delegated_deleverage"] = {"reverted": True,
                    "error": self.sanitized(error_text(e))[:1500], "frames": error_frames(e)}
            self.action(charlie, charlie.setUserDelegation, main_user, self.gov, original)
            assert tuple(mc.userDelegation(main_user, self.gov)) == original
            result["delegated_deleverage"]["delegation_restored"] = True
            self.save()
        for u in users:
            if u.lower() == main_user.lower():
                continue
            boa.env.time_travel(blocks=1, block_delta=2)
            original = original_configs[u]
            temporary = list(original)
            temporary[1] = True
            self.action(charlie, charlie.setUserConfig, u, tuple(temporary))
            debt = ce.getUserDebtAmount(u)
            assert green.balanceOf(self.gov) >= debt, "Safe GREEN insufficient; no synthetic funding supplied"
            positions = [(vid, p["asset"], self.vaults[vid].getTotalAmountForUser(u, p["asset"]))
                         for vid, ps in self.report["positions"].items() for p in ps.values()
                         if p["user"].lower() == u.lower() and p["shares"]]
            gov_positions = {a: tuple(self.vaults[2].userGovData(u, a)) for vid, a, _ in positions if vid == 2}
            safe_before = green.balanceOf(self.gov)
            self.transact(green.approve, teller.address, debt)
            self.transact(teller.repay, debt, u, False, False)
            assert ce.getUserDebtAmount(u) == 0, "repayment left debt"
            assert green.allowance(self.gov, teller.address) == 0, "allowance residue"
            self.action(charlie, charlie.setUserConfig, u, original)
            assert tuple(mc.userConfig(u)) == original, "permission not restored"
            for vid, asset, amount in positions:
                assert self.vaults[vid].getTotalAmountForUser(u, asset) == amount, "repayment changed deposit"
            for asset, data in gov_positions.items():
                assert tuple(self.vaults[2].userGovData(u, asset)) == data, "repayment changed gov position"
            result["repayments"].append({"user": u, "green_spent": safe_before - green.balanceOf(self.gov),
                "debt_after": 0, "healthy_after": ce.hasGoodDebtHealth(u),
                "deposits_and_locks_unchanged": True, "permissions_restored": True})
            self.save()
        result["safe_green_after"] = green.balanceOf(self.gov)
        self.transact(charlie.pause, teller.address, True)
        self.save()

    def legacy_probe(self):
        """Exercise actual legacy bytecode; no source impersonation or storage edits."""
        assert "positions" in self.report, "legacy probe requires census"
        mc = self.new["MissionControl"]
        alpha, bravo, charlie, echo = [self.new["Switchboard" + x]
                                      for x in ["Alpha", "Bravo", "Charlie", "Echo"]]
        source, target = self.vaults[2], self.new["RipeGov"]
        if not self.new["Teller"].isPaused():
            self.transact(charlie.pause, self.new["Teller"].address, True)
        rows = list(self.report["positions"][2].values())
        funded = [r for r in rows if r["shares"]]
        configs = {}
        for asset in dict.fromkeys(r["asset"] for r in funded):
            cfg = mc.assetConfig(asset)
            configs[asset] = (tuple(cfg), tuple(mc.ripeGovVaultConfig(asset)))
            # Membership changes require zero allocations for ordinary earners.
            # This governance method checkpoints the old row before clearing it.
            if mc.rewardVaultId(asset):
                self.action(charlie, charlie.setRewardVaultId, asset, 0)
            cfg = mc.assetConfig(asset)
            self.action(bravo, bravo.setAssetDepositParams, asset,
                        list(cfg[0]) + [7], *tuple(cfg)[1:6])
        self.action(charlie, charlie.setCoreRipeGovVaultId, 7)
        self.transact(charlie.pause, target.address, True)
        assert target.getNumVaultAssets() == 0, "target not virgin"
        for asset, (_, config) in configs.items():
            terms, weight, freeze = config
            minimum = min(r["gov_data"][4][0] for r in funded if r["asset"] == asset)
            assert minimum > 0, "cannot wind down zero-minimum legacy lock"
            self.action(alpha, alpha.setRipeGovVaultConfig, asset, weight, freeze,
                        minimum - 1, terms[1], terms[2], terms[4], terms[3])
        self.transact(charlie.pause, self.new["VaultMigrator"].address, False)
        users = list(dict.fromkeys(r["user"] for r in funded))
        if getattr(self, "only_user", None):
            users = [u for u in users if u.lower() == self.only_user.lower()]
            assert users, "selected user has no funded legacy position"
        self.report["legacy_migration"] = {"status": "running", "users": len(users), "results": []}
        if getattr(self, "audit_only_migrations", False):
            selected = [u for u in users if u.lower() in {x.lower() for x in self.audit_candidates}]
            results = []
            self.report["isolated_legacy_blocker_trials"] = results
            for user in selected:
                with self.diagnostic_branch("legacy_trial:" + user):
                    boa.env.time_travel(blocks=1, block_delta=2)
                    row = {"user": user, "block": boa.env.evm.patch.block_number,
                           "branch_id": "legacy_trial:" + user, "state_rolled_back": True}
                    try:
                        row["positions_moved"] = self.transact(echo.migrateLegacyRipeGovPositions, [user])
                        row["reverted"] = False
                    except Exception as e:
                        row["reverted"] = True
                        row["error"] = self.sanitized(error_text(e))[:1500]
                        row["frames"] = error_frames(e)
                    results.append(row)
                    self.save()
            self.report["legacy_migration"]["status"] = "isolated_candidates_only_all_changes_rolled_back"
            return
        for user in users:
            boa.env.time_travel(blocks=1, block_delta=2)
            self.report["legacy_migration"]["attempt"] = {"user": user,
                "healthy_before": self.new["CreditEngine"].hasGoodDebtHealth(user),
                "collateral_and_debt_before": plain(self.new["CreditEngine"].getUserCollateralValueAndDebtAmount(user))}
            self.save()
            snapshots = []
            for r in funded:
                if r["user"] != user:
                    continue
                a = r["asset"]
                snapshots.append((a, source.getTotalAmountForUser(user, a), tuple(source.userGovData(user, a))))
            print("Migrating legacy user", user, flush=True)
            count = self.transact(echo.migrateLegacyRipeGovPositions, [user])
            assert count == len(snapshots), "migration skipped funded positions"
            for asset, amount, gd in snapshots:
                after = tuple(target.userGovData(user, asset))
                assert source.userBalances(user, asset) == 0, "source balance remains"
                assert target.getTotalAmountForUser(user, asset) == amount, "underlying amount drift"
                assert after[3:] == gd[3:], "original unlock or terms changed"
            self.report["legacy_migration"]["results"].append({"user": user, "positions": count,
                "underlying_and_locks_equal": True})
            self.save()
        for asset, (_, config) in configs.items():
            terms, weight, freeze = config
            self.action(alpha, alpha.setRipeGovVaultConfig, asset, weight, freeze,
                        terms[0], terms[1], terms[2], terms[4], terms[3])
        self.report["legacy_migration"]["status"] = "positions_moved_routes_and_rewards_not_finalized"
        self.save()

    def stage(self, defaults_path):
        h, g = self.hq.address, ZERO
        defaults = self.deploy("BaseForkDefaults", self.old["MissionControl"].hrConfig()[0], path=defaults_path)
        mc = self.deploy("MissionControl", h, defaults.address)
        self.report["config_comparison"] = {}
        old = self.old["MissionControl"]
        for n in ["genConfig", "genDebtConfig", "hrConfig", "ripeBondConfig", "rewardsConfig", "totalPointsAllocs"]:
            before, after = plain(getattr(old, n)()), plain(getattr(mc, n)())
            assert before == after, ("CONFIG_DRIFT", n, before, after)
            self.report["config_comparison"][n] = "equal"
        for i in range(1, old.numAssets()):
            a = old.assets(i)
            assert tuple(old.assetConfig(a)) == tuple(mc.assetConfig(a)), ("ASSET_DRIFT", a)
        self.deploy("Switchboard", h, g, 1, 1000000)
        for name in ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"]:
            args = [h, g, 1, 1000000]
            if name == "Alpha":
                args = [h, g, 1, 31536000, 1, 1000000, 4]
            self.deploy("Switchboard" + name, *args)
        self.deploy("VaultBook", h, g, 1, 1000000)
        self.deploy("StabilityPool", h)
        self.deploy("RipeGov", h)
        self.deploy("VaultMigrator", h, True, self.vaults[2].address)
        for n in ["AuctionHouse", "AuctionHouseNFT", "Boardroom", "CreditRedeem", "TellerUtils", "EndaomentFunds"]:
            self.deploy(n, h)
        self.deploy("BondRoom", h, self.old["BondRoom"].bondBooster())
        self.deploy("CreditEngine", h, 2)
        self.deploy("HumanResources", h, 1, 1000000)
        loot = self.old["Lootbox"]
        self.deploy("Lootbox", h, 1, loot.underscoreSendInterval(), loot.undyDepositRewardsAmount(), loot.undyYieldBonusAmount())
        self.deploy("Teller", h, True, 2)
        d = self.old["Deleverage"]
        self.deploy("Deleverage", h, d.minDeleverageBps(), d.deleverageBuffer(), d.deleverageCooldown(), d.underscoreSafeSpreadBps(), 10**15, 100, 0, 0)
        e = self.old["Endaoment"]
        self.deploy("Endaoment", h, e.WETH(), e.ETH(), 2)
        self.report["status"] = "staged_only_not_qualified"
        self.save()

    def stability_probe(self):
        """Test deposit movement without treating stranded claim rights as success."""
        source, target = self.vaults[1], self.new["StabilityPool"]
        mc = self.new["MissionControl"]
        bravo, charlie, echo = [self.new["Switchboard" + n] for n in ["Bravo", "Charlie", "Echo"]]
        if not self.new["Teller"].isPaused():
            self.transact(charlie.pause, self.new["Teller"].address, True)
        if self.new["VaultMigrator"].isPaused():
            self.transact(charlie.pause, self.new["VaultMigrator"].address, False)
        rows = [r for r in self.report["positions"][1].values() if r["shares"]]
        result = {"status": "running", "target_id": 6, "results": [],
                  "claim_inventory_before": self.report["legacy_stability_claim_inventory"]}
        self.report["stability_migration"] = result
        if getattr(self, "stability_residual", False):
            # Real Safe funding only. Keep its newly created position in source.
            lp = "0xd6c283655B42FA0eb2685F7AB819784F071459dc"
            assert source.userBalances(self.gov, lp) == 0, "governance already has a source position"
            green = self.at("GreenToken", self.hq.getAddr(1))
            assert source.claimableBalances(lp, green.address) == 0, "material GREEN claims remain"
            pool_abi = [dict(type="function", name=n, stateMutability=mut,
                inputs=[dict(name="arg"+str(i), type=t) for i,t in enumerate(ins)],
                outputs=[dict(type=out)]) for n,ins,out,mut in [
                ("coins",["uint256"],"address","view"),
                ("balanceOf",["address"],"uint256","view"),
                ("approve",["address","uint256"],"bool","nonpayable"),
                ("calc_token_amount",["uint256[]","bool"],"uint256","view"),
                ("add_liquidity",["uint256[]","uint256"],"uint256","nonpayable")]]
            pool = ABIContractFactory("ResidualCurvePool", pool_abi).at(lp)
            coins = [pool.coins(i) for i in range(2)]
            green_index = [str(c).lower() for c in coins].index(str(green.address).lower())
            minimum = mc.assetConfig(lp)[5]
            min_value = self.old["PriceDesk"].getUsdValue(lp, minimum, True)
            payment = max(10**17, min_value * 102 // 100)
            assert payment <= 5 * 10**18, "residual seed exceeds 5 GREEN diagnostic cap"
            amounts = [0, 0]; amounts[green_index] = payment
            quote = pool.calc_token_amount(amounts, True)
            assert quote * 99 // 100 >= minimum, "seed below minimum deposit"
            assert green.balanceOf(self.gov) >= payment, "governance needs GREEN for residual"
            wallet_before = pool.balanceOf(self.gov)
            green_before = green.balanceOf(self.gov)
            self.transact(green.approve, pool.address, payment)
            self.transact(pool.add_liquidity, amounts, quote * 99 // 100)
            minted = pool.balanceOf(self.gov) - wallet_before
            assert minted >= minimum
            teller = self.new["Teller"]
            config = tuple(self.old["MissionControl"].userConfig(self.gov))
            if tuple(mc.userConfig(self.gov)) != config:
                self.action(charlie, charlie.setUserConfig, self.gov, config)
            self.transact(charlie.pause, teller.address, False)
            self.transact(pool.approve, teller.address, minted)
            self.transact(teller.deposit, lp, minted, self.gov, source.address, 1)
            self.transact(charlie.pause, teller.address, True)
            result["residual"] = {"owner": str(self.gov), "asset": lp,
                "green_spent": green_before-green.balanceOf(self.gov), "lp_deposited": minted,
                "source_shares": source.userBalances(self.gov, lp), "excluded_from_migration": True}
            self.save()
        for asset in dict.fromkeys(r["asset"] for r in rows):
            config = mc.assetConfig(asset)
            if config[1] or config[2]:
                self.action(charlie, charlie.setRewardVaultId, asset, 0)
                config = mc.assetConfig(asset)
            self.action(bravo, bravo.setAssetDepositParams, asset,
                        list(config[0]) + [6], *tuple(config)[1:6])
        self.action(charlie, charlie.setPreferredStabVaultId, 6)
        for user in dict.fromkeys(r["user"] for r in rows):
            boa.env.time_travel(blocks=1, block_delta=2)
            result["attempt"] = {"user": user}
            self.save()
            before = {r["asset"]: source.getTotalAmountForUser(user, r["asset"])
                      for r in rows if r["user"] == user}
            debt = self.new["CreditEngine"].getUserDebtAmount(user)
            print("Migrating stability", user, flush=True)
            result["attempt"]["source_amounts"] = before
            result["attempt"]["source_totals"] = {asset: source.totalBalances(asset) for asset in before}
            self.save()
            try:
                count = self.transact(echo.migrateVaultPositions, [user], 1, 6)
            except Exception as e:
                result["status"] = "blocked"
                result["claim_inventory_at_failure"] = [{**r,
                    "source_remaining": source.claimableBalances(r["deposit_asset"], r["claim_asset"]),
                    "target_received": target.claimableBalances(r["deposit_asset"], r["claim_asset"])}
                    for r in result["claim_inventory_before"]]
                frame = getattr(getattr(e, "stack_trace", None), "last_frame", None)
                result["attempt"]["diagnostic"] = {k: str(getattr(frame, k, None))
                    for k in ["error_detail", "dev_reason", "source_node"]}
                self.save()
                raise
            assert count == len(before), "stability migration skipped assets"
            result["attempt"]["balances"] = [{"asset": asset, "before": amount,
                "source_shares_after": source.userBalances(user, asset),
                "target_amount_after": target.getTotalAmountForUser(user, asset)}
                for asset, amount in before.items()]
            self.save()
            for asset, amount in before.items():
                assert source.userBalances(user, asset) == 0, "stability source remains"
            equal = all(r["before"] == r["target_amount_after"] for r in result["attempt"]["balances"])
            if not equal and "STABILITY_UNDERLYING_DRIFT" not in self.report.setdefault("blockers", []):
                self.report["blockers"].append("STABILITY_UNDERLYING_DRIFT")
            assert self.new["CreditEngine"].getUserDebtAmount(user) == debt, "stability debt drift"
            result["results"].append({"user": user, "positions": count,
                "balances": result["attempt"]["balances"],
                "underlying_equal": equal, "current_debt_equal": True})
            self.save()
        result["claim_inventory_after"] = [{**r,
            "source_remaining": source.claimableBalances(r["deposit_asset"], r["claim_asset"]),
            "target_received": target.claimableBalances(r["deposit_asset"], r["claim_asset"])}
            for r in result["claim_inventory_before"]]
        if result.get("residual"):
            lp = result["residual"]["asset"]
            assert source.totalBalances(lp) == source.userBalances(self.gov, lp), "non-governance shares left"
            assert all(source.totalBalances(a) == 0 for a in self.report["vaults"][1]["assets"] if a.lower() != lp.lower())
            assert all(r["source_remaining"] == r["raw_claim_balance"] and r["target_received"] == 0
                       for r in result["claim_inventory_after"]), "residual claims changed"
            result["residual"]["final_amount"] = source.getTotalAmountForUser(self.gov, lp)
            result["status"] = "users_moved_governance_residual_retained_routes_not_finalized"
        elif any(r["source_remaining"] or r["target_received"] != r["raw_claim_balance"]
               for r in result["claim_inventory_after"]):
            self.report.setdefault("blockers", []).append("STABILITY_CLAIM_HANDOFF_NOT_PRESERVED")
            result["status"] = "deposit_moves_completed_claim_handoff_failed"
        else:
            result["status"] = "deposit_moves_completed_not_qualified"
        self.save()

    def ordinary_probe(self):
        """Separate ordinary-vault test, deliberately excluding Stability claims."""
        assert "positions" in self.report
        mc, book = self.new["MissionControl"], self.new["VaultBook"]
        bravo, charlie, echo = [self.new["Switchboard" + n] for n in ["Bravo", "Charlie", "Echo"]]
        if not self.new["Teller"].isPaused():
            self.transact(charlie.pause, self.new["Teller"].address, True)
        if self.new["VaultMigrator"].isPaused():
            self.transact(charlie.pause, self.new["VaultMigrator"].address, False)
        self.report["ordinary_migration"] = {}
        for vid, filename in [(3, "SimpleErc20"), (4, "RebaseErc20"), (5, "SimpleErc20")]:
            source = self.vaults[vid]
            target = self.deploy("OrdinaryTarget" + str(vid), self.hq.address,
                                 path=ROOT / "contracts/vaults" / (filename + ".vy"))
            self.transact(book.startAddNewAddressToRegistry, target.address, "New ordinary " + str(vid))
            target_id = self.transact(book.confirmNewAddressToRegistry, target.address)
            rows = [r for r in self.report["positions"][vid].values() if r["shares"]]
            for asset in dict.fromkeys(r["asset"] for r in rows):
                config = mc.assetConfig(asset)
                if config[1] or config[2]:
                    self.action(charlie, charlie.setRewardVaultId, asset, 0)
                    config = mc.assetConfig(asset)
                self.action(bravo, bravo.setAssetDepositParams, asset,
                            list(config[0]) + [target_id], *tuple(config)[1:6])
            result = {"target_id": target_id, "status": "running", "results": []}
            self.report["ordinary_migration"][vid] = result
            users = list(dict.fromkeys(r["user"] for r in rows))
            if getattr(self, "ordinary_candidate_users", None) is not None:
                users = [u for u in users if u.lower() in self.ordinary_candidate_users]
            if getattr(self, "only_user", None):
                users = [u for u in users if u.lower() == self.only_user.lower()]
            for user in users:
                boa.env.time_travel(blocks=1, block_delta=2)
                result["attempt"] = {"user": user,
                    "healthy_before": self.new["CreditEngine"].hasGoodDebtHealth(user)}
                self.save()
                before = {r["asset"]: source.getTotalAmountForUser(user, r["asset"])
                          for r in rows if r["user"] == user}
                print("Migrating ordinary", vid, user, flush=True)
                expected_debt = self.new["CreditEngine"].getUserDebtAmount(user)
                count = self.transact(echo.migrateVaultPositions, [user], vid, target_id)
                assert count == len(before), "ordinary migration skipped funded assets"
                for asset, amount in before.items():
                    assert source.userBalances(user, asset) == 0, "ordinary source remains"
                    assert target.getTotalAmountForUser(user, asset) == amount, "ordinary underlying drift"
                assert self.new["CreditEngine"].getUserDebtAmount(user) == expected_debt, "migration changed current debt"
                result["results"].append({"user": user, "positions": count, "underlying_equal": True,
                    "current_debt_equal": True})
                self.save()
            result["status"] = "positions_moved_routes_and_rewards_not_finalized"
            self.save()


def main():
    require_unoptimized()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--block", type=int, required=True)
    p.add_argument("--allow-unfinalized-diagnostic", action="store_true")
    p.add_argument("--defaults", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--diagnose-replacing-pending", action="store_true")
    p.add_argument("--census", action="store_true")
    p.add_argument("--census-input", type=Path)
    p.add_argument("--probe", action="store_true")
    p.add_argument("--legacy-probe", action="store_true")
    p.add_argument("--ordinary-probe", action="store_true")
    p.add_argument("--stability-probe", action="store_true")
    p.add_argument("--stability-residual", action="store_true")
    p.add_argument("--borrower-audit", action="store_true")
    p.add_argument("--audit-blocker-migrations", action="store_true")
    p.add_argument("--remediate-blockers", action="store_true")
    p.add_argument("--only-user", help="Isolate a failing user; never full qualification")
    a = p.parse_args()
    unsupported = (
        "probe", "legacy_probe", "ordinary_probe", "stability_probe",
        "stability_residual", "borrower_audit", "audit_blocker_migrations",
        "remediate_blockers",
    )
    selected = ["--" + name.replace("_", "-") for name in unsupported if getattr(a, name)]
    if selected:
        p.error(
            "BASE_COMPATIBILITY_PROBE_REQUIRES_FULL_UPDATE: "
            + ", ".join(selected)
            + " requires scripts/base_full_update_fork.py for current-source dependencies"
        )
    load_dotenv(ROOT / ".env")
    r = Rehearsal(os.environ["BASE_MAINNET_RPC_URL"], a.block, a.report, overwrite=a.overwrite)
    r.diagnose_replacing_pending = a.diagnose_replacing_pending
    r.report["input_fingerprint"] = fingerprint(ROOT, [a.defaults])
    r.only_user = a.only_user
    r.stability_residual = a.stability_residual
    assert not a.stability_residual or a.stability_probe
    r.audit_only_migrations = a.audit_blocker_migrations
    if a.audit_blocker_migrations:
        assert (a.borrower_audit or a.remediate_blockers) and a.legacy_probe
    if a.only_user:
        r.report["only_user"] = a.only_user
    try:
        assert int(r.rpc_read("eth_chainId", []), 16) == 8453
        header = r.rpc_read("eth_getBlockByNumber", [hex(a.block), False])
        finalized = int(r.rpc_read("eth_getBlockByNumber", ["finalized", False])["number"], 16)
        r.report["snapshot_finalized"] = a.block <= finalized
        assert a.block <= finalized or a.allow_unfinalized_diagnostic, "snapshot not finalized"
        r.report["block_hash"] = header["hash"]
        with boa.fork(r.rpc, block_identifier=a.block):
            assert boa.env.evm.patch.chain_id == 8453
            r.inventory()
            if a.census_input:
                cached = r.read_saved_input(a.census_input, "census")
                assert cached["block"] == a.block and cached["block_hash"] == header["hash"]
                for vid, vault in r.report["vaults"].items():
                    assert cached["vaults"][str(vid)]["address"] == vault["address"]
                    for asset, entry in vault["assets"].items():
                        total = sum(x["shares"] for x in cached["positions"][str(vid)].values()
                                    if x["asset"] == asset)
                        assert total == entry["total_shares_or_balance"], "cached census mismatch"
                r.report["positions"] = {int(k): v for k, v in cached["positions"].items()}
                for vid, positions in r.report["positions"].items():
                    r.reconcile_positions(vid, positions)
            if a.census:
                r.census()
            r.stage(a.defaults)
            if a.probe:
                r.compatibility_probe()
            if a.borrower_audit:
                assert a.probe and (a.census or a.census_input)
                r.borrower_audit()
            if a.remediate_blockers:
                assert a.probe and (a.census or a.census_input)
                r.remediate_blockers()
            if a.legacy_probe:
                assert a.probe and (a.census or a.census_input)
                r.legacy_probe()
            if a.stability_probe:
                assert a.probe and (a.census or a.census_input)
                r.stability_probe()
            if a.ordinary_probe:
                assert a.probe and (a.census or a.census_input)
                r.ordinary_probe()
    except Exception as e:
        r.report["status"] = "blocked"
        r.report["error_type"] = type(e).__name__
        r.report["error_frames"] = error_frames(e)
        # URLs and provider credentials are never written into the public report.
        r.report["error"] = r.sanitized(error_text(e))[:6000]
        r.save()
        print("REHEARSAL BLOCKED:", type(e).__name__, r.report["error"][:1500], flush=True)
        return 1
    if r.report.get("blockers"):
        r.report["status"] = "not_qualified"
        r.save()
        return 2
    r.save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
