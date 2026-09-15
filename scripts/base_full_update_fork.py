"""Two-wave Base rehearsal. ALL transactions are confined to boa.fork.

Uses the real deployment migrations, without the live runner/history or keys.
Does not migrate user vault positions. Records blockers instead of silently
changing state through storage edits or pretending deployment is qualification.
"""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys

import boa
from dotenv import load_dotenv
from eth_utils import keccak, to_checksum_address, event_abi_to_log_topic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.base_upgrade_fork import Rehearsal, plain, error_text, error_frames, permission_keys, HQ_IDS, ZERO
from scripts.utils.deploy_args import BluePrint
from scripts.utils.fork_reports import fingerprint, require_unoptimized

SUFFIX = "BaseUpgradeCandidate20260914"


def positional(value):
    if isinstance(value, (tuple, list)):
        return [positional(x) for x in value]
    return value


class DeploymentAdapter:
    def __init__(self, run, defaults):
        self.run, self.defaults = run, defaults

    def chain(self):
        return "base-mainnet"

    def blueprint(self):
        return BluePrint("base")

    def get_contract(self, name, address=None):
        if name.endswith(SUFFIX):
            return self.run.new[name.removesuffix(SUFFIX)]
        return self.run.at(name, address)

    def deploy(self, name, *args, label):
        key = label.removesuffix(SUFFIX)
        path = self.defaults if name == "DefaultsBaseLive" else next((ROOT / "contracts").rglob(name + ".vy"))
        return self.run.deploy(key, *args, path=path)

    def deploy_bp(self, name, *, label):
        path = next((ROOT / "contracts").rglob(name + ".vy"))
        bp = boa.load_partial(str(path)).deploy_as_blueprint()
        self.run.new[name] = bp
        code = boa.env.get_code(bp.address)
        self.run.report["deployments"][name] = {"address": str(bp.address), "blueprint": True,
            "deployed_bytes": len(code), "deployed_sha256": hashlib.sha256(code).hexdigest(),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "constructor_args": []}
        self.run.save()
        return bp


class FullUpdate(Rehearsal):
    def attempt(self, name, fn):
        previous_failures = len(self.report.get("blockers", []))
        try:
            fn()
            if len(self.report.get("blockers", [])) > previous_failures:
                raise RuntimeError("REQUIRED_CHILD_CHECK_FAILED:" + name)
            self.report.setdefault("checks", {})[name] = "passed"
        except Exception as e:
            self.report.setdefault("blockers", []).append(name)
            self.report.setdefault("checks", {})[name] = {
                "error": self.sanitized(error_text(e))[:3000],
                "frames": error_frames(e),
            }
            print("BLOCKED", name, self.report["checks"][name]["error"][:400], flush=True)
        self.save()

    def treasury_inventory(self):
        tokens = set()
        transfer = "0x" + keccak(text="Transfer(address,address,uint256)").hex()
        # Incoming transfer logs discover assets not listed in MissionControl,
        # including yield shares. No assume-zero shortcut for unknown holdings.
        for name in ("Endaoment", "EndaomentFunds", "EndaomentPSM"):
            target = self.old[name].address
            logs = self.filtered_logs({
                "topics": [transfer, None, "0x" + str(target)[2:].lower().zfill(64)]}, 0, self.block)
            tokens.update(row["address"] for row in logs if len(row["topics"]) == 3)
        self.tokens = {a: boa.loads_abi('[{"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"account","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},{"type":"function","name":"transfer","stateMutability":"nonpayable","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}]', name="TreasuryToken").at(a) for a in sorted(tokens)}
        self.treasury_before = {n: {} for n in ("Endaoment", "EndaomentFunds", "EndaomentPSM")}
        unsupported = {}
        for a, token in list(self.tokens.items()):
            try:
                balances = {n: token.balanceOf(self.old[n].address) for n in self.treasury_before}
            except Exception as e:
                unsupported[a] = self.sanitized(error_text(e))[:300]
                del self.tokens[a]
                continue
            for n, amount in balances.items():
                self.treasury_before[n][a] = amount
        # Uncallable assets from unsolicited Transfer logs are not silently
        # labelled zero or included in a claim of complete treasury migration.
        self.report["unresolved_transfer_log_tokens"] = unsupported
        if unsupported:
            self.report.setdefault("blockers", []).append("UNRESOLVED_UNCALLABLE_TREASURY_LOG_TOKENS")
        self.report["treasury_before"] = self.treasury_before
        self.report["treasury_native_before"] = {n: boa.env.get_balance(self.old[n].address) for n in self.treasury_before}
        self.save()

    def transfer_treasury(self):
        sb = self.old["Switchboard"]
        charlie = self.at("SwitchboardCharlie", sb.getAddr(3))
        echo = self.at("SwitchboardEcho", sb.getAddr(5))
        queued = []
        mc = self.old["MissionControl"]
        trusted = {str(mc.assets(i)).lower() for i in range(1, int(mc.numAssets()))}
        trusted.update(str(self.hq.getAddr(i)).lower() for i in (1, 2, 3))
        trusted.add(str(self.old["EndaomentPSM"].USDC()).lower())
        trusted.add(str(self.old["EndaomentPSM"].usdcYieldPosition()[1]).lower())
        transferable = {a: t for a, t in self.tokens.items() if a.lower() in trusted}
        self.report["unreviewed_treasury_tokens_not_touched"] = {
            a: {n: row[a] for n, row in self.treasury_before.items() if row[a]}
            for a in self.tokens if a not in transferable and any(row[a] for row in self.treasury_before.values())}
        self.report["psm_underlying_before"] = self.old["EndaomentPSM"].getUnderlyingYieldAmount()
        gov_before = {a: t.balanceOf(self.gov) for a, t in transferable.items()}
        for a, token in transferable.items():
            psm_amount = token.balanceOf(self.old["EndaomentPSM"].address)
            if psm_amount:
                aid = self.transact(charlie.recoverFunds, self.old["EndaomentPSM"].address,
                                    self.new["EndaomentPSM"].address, a)
                queued.append((charlie, aid))
            amount = token.balanceOf(self.old["Endaoment"].address) + token.balanceOf(self.old["EndaomentFunds"].address)
            if amount:
                aid = self.transact(echo.performEndaomentTransfer, a, amount)
                queued.append((echo, aid))
        delay = max([int(board.actionTimeLock()) for board, _ in queued] or [0])
        if delay:
            boa.env.time_travel(blocks=delay, block_delta=2)
        for board, aid in queued:
            self.transact(board.executePendingAction, aid)
        results = {}
        for a, token in transferable.items():
            received = token.balanceOf(self.gov) - gov_before[a]
            if received:
                self.transact(token.transfer, self.new["EndaomentFunds"].address, received)
            assert token.balanceOf(self.gov) == gov_before[a], "governance relay residue"
            assert all(token.balanceOf(self.old[n].address) == 0 for n in self.treasury_before), a
            expected = sum(row[a] for row in self.treasury_before.values())
            actual = token.balanceOf(self.new["EndaomentFunds"].address) + token.balanceOf(self.new["EndaomentPSM"].address)
            assert actual == expected, ("TREASURY_TOKEN_DRIFT", a, expected, actual)
            if expected:
                results[a] = {"before": expected, "after": actual, "equal": True}
        self.report["treasury_conservation"] = results
        yield_asset = str(self.old["EndaomentPSM"].usdcYieldPosition()[1]).lower()
        yield_result = next((r for a, r in results.items() if a.lower() == yield_asset), None)
        yield_entry = next(((a, token) for a, token in transferable.items() if a.lower() == yield_asset), None)
        psm_yield_before = psm_yield_after = psm_yield_remaining = None
        if yield_entry:
            asset, token = yield_entry
            psm_yield_before = self.treasury_before["EndaomentPSM"][asset]
            psm_yield_after = token.balanceOf(self.new["EndaomentPSM"].address)
            psm_yield_remaining = token.balanceOf(self.old["EndaomentPSM"].address)
        self.report["psm_yield_share_handoff"] = {
            "before": psm_yield_before, "new_psm": psm_yield_after, "old_psm": psm_yield_remaining}
        self.report["psm_yield_shares_moved_without_redemption"] = bool(
            yield_result and yield_result["equal"] and psm_yield_before
            and psm_yield_after == psm_yield_before and psm_yield_remaining == 0)
        self.report["psm_underlying_comparison_scope"] = "before/after governance wait; yield accrual may differ, only token-unit conservation asserted"
        self.report["psm_underlying_after"] = self.new["EndaomentPSM"].getUnderlyingYieldAmount()
        assert not any(self.report["treasury_native_before"].values()), "native ETH handoff not yet implemented"
        self.save()

    def register_candidates(self):
        book, sb, desk = self.new["VaultBook"], self.new["Switchboard"], self.new["PriceDesk"]
        entries = [(i, v, "Retained " + str(i)) for i, v in self.vaults.items()]
        entries += [(i, self.new[n], n) for i, n in enumerate(
            ("StabilityPool", "RipeGov", "SimpleErc20", "RebaseErc20", "UnderscoreVault"), 6)]
        for i, contract, description in entries:
            self.transact(book.startAddNewAddressToRegistry, contract.address, description)
            self.transact_expect(i, book.confirmNewAddressToRegistry, contract.address)
        for i, suffix in enumerate(("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"), 1):
            contract = self.new["Switchboard" + suffix]
            self.transact(sb.startAddNewAddressToRegistry, contract.address, suffix)
            self.transact_expect(i, sb.confirmNewAddressToRegistry, contract.address)
        self.sources = {}
        old_desk = self.old["PriceDesk"]
        for i in range(1, int(old_desk.numAddrs())):
            old_address = old_desk.getAddr(i)
            if i == 3 and str(old_address).lower() == ZERO:
                candidate = self.new["BlueChipYieldPrices"]
                self.transact(desk.startAddNewAddressToRegistry, candidate.address, "BlueChip Yield Prices")
                self.transact_expect(3, desk.confirmNewAddressToRegistry, candidate.address)
                self.transact(desk.startAddressDisableInRegistry, 3)
                self.transact(desk.confirmAddressDisableInRegistry, 3)
                continue
            if i == 6:
                self.transact(desk.startAddNewAddressToRegistry, old_address, "Retained legacy Aero RIPE pricing")
                self.transact_expect(6, desk.confirmNewAddressToRegistry, old_address)
                self.report["retained_legacy_aero_slot6"] = str(old_address)
                self.report["aero_ui_only_note"] = "User confirmed Aero is for UI, not collateral. New monitor is deployed separately; retaining legacy RIPE quote during UI handoff is not a collateral migration blocker."
                continue
            names = [n for n, v in self.manifest.items() if v["address"].lower() == str(old_address).lower()]
            assert len(names) == 1, ("UNKNOWN_PRICE_SOURCE", i, old_address)
            name = names[0]
            self.sources[name] = self.at(name, old_address)
            self.transact(desk.startAddNewAddressToRegistry, self.new[name].address, name)
            self.transact_expect(i, desk.confirmNewAddressToRegistry, self.new[name].address)
        self.report["staged_registry_ids"] = {"vaults": {i: str(c.address) for i, c, _ in entries},
                                            "sources": {n: int(desk.getRegId(self.new[n].address)) for n in self.sources}}
        self.save()

    def activate_departments(self):
        replacements = [i for i in HQ_IDS if i != 4]
        # PriceDesk is now included. Vaults at IDs 1-5 are deliberately retained.
        for i in replacements:
            pending = self.hq.pendingAddrUpdate(i)
            if str(pending[0]).lower() != ZERO:
                self.report.setdefault("live_pending_registry_changes", {})[i] = plain(pending)
                self.report.setdefault("blockers", []).append("LIVE_PENDING_REGISTRY_UPDATE_REQUIRES_DECISION:" + str(i))
                assert self.diagnose_replacing_pending, ("LIVE_PENDING_UPDATE", i)
                # Explicit fork-only alternate path, never a production plan.
                self.transact(self.hq.cancelAddressUpdateToRegistry, i)
            self.transact(self.hq.startAddressUpdateToRegistry, i, self.new[HQ_IDS[i]].address)
        for name in ("VaultMigrator", "RipeReserveEngine", "RipeReserveVesting"):
            self.transact(self.hq.startAddNewAddressToRegistry, self.new[name].address, name)
        delay = int(self.hq.registryChangeTimeLock())
        if delay:
            boa.env.time_travel(blocks=delay, block_delta=2)
        for i in [8, 5, 6, 7] + [i for i in replacements if i not in (8, 5, 6, 7)]:
            self.transact(self.hq.confirmAddressUpdateToRegistry, i)
        for i, name in enumerate(("VaultMigrator", "RipeReserveEngine", "RipeReserveVesting"), 25):
            self.transact_expect(i, self.hq.confirmNewAddressToRegistry, self.new[name].address)
        ledger = self.old["Ledger"]
        assert str(self.hq.getAddr(4)).lower() == str(ledger.address).lower()
        assert {n: plain(getattr(ledger, n)()) for n in self.report["ledger_before"]} == self.report["ledger_before"]
        assert {u: plain(ledger.userDebt(u)) for u in self.report["borrowers"]} == self.report["borrowers"]
        assert self.new["MissionControl"].preferredStabVaultId() == 1
        assert self.new["MissionControl"].coreRipeGovVaultId() == 2
        self.report["wave1_active_hq"] = {i: str(self.hq.getAddr(i)) for i in range(1, 28)}
        self.report["ledger_globals_and_borrower_records_equal"] = True
        self.save()

    def configure_oracles(self):
        desk, mc = self.new["PriceDesk"], self.new["MissionControl"]
        # Conversion-dependent sources need scales before confirmation can
        # qualify their prices. Governance may set them before feeds exist.
        for i in range(1, int(mc.numAssets())):
            asset = mc.assets(i)
            if not mc.assetConfig(asset)[-1] and str(asset).lower() != str(desk.ETH()).lower():
                self.attempt("token_scale_" + str(asset), lambda asset=asset: self.transact(desk.syncTokenScale, asset))

        def act(contract, fn, *args):
            aid = contract.actionId()
            self.transact(fn, *args)
            name = fn.name if hasattr(fn, "name") else fn.fn_ast.name
            if name == "addNewPriceFeed":
                self.transact(contract.confirmNewPriceFeed, args[0])
            elif name == "updateStaleTime":
                self.transact(contract.confirmPriceFeedUpdate, args[0])
            elif name == "setGreenRefPoolConfig":
                self.transact(contract.confirmGreenRefPoolConfig, aid)
            else:
                raise RuntimeError("unhandled oracle configuration")

        def copy_source(name):
            old, new = self.sources[name], self.new[name]
            assets = list(old.getPricedAssets())
            source_report = {"old_source": str(old.address), "new_source": str(new.address),
                             "assets": {}, "snapshot_block": self.block}
            self.report.setdefault("oracle_registration_replay", {})[name] = source_report

            def copy_asset(asset):
                getter = ("curveConfig" if name == "CurvePrices" else
                          "priceConfigs" if name in ("BlueChipYieldPrices", "UndyVaultPrices") else
                          "feedConfig" if name != "wsuperOETHbPrices" else None)
                row = source_report["assets"][str(asset)]
                if getter:
                    row["live_config"] = positional(getattr(old, getter)(asset))
                if name == "ChainlinkPrices":
                    c = old.feedConfig(asset)
                    if new.hasPriceFeed(asset):
                        if new.feedConfig(asset)[4] != c[4]:
                            act(new, new.updateStaleTime, asset, c[4])
                    else:
                        act(new, new.addNewPriceFeed, asset, c[0], c[4], c[2], c[3])
                elif name == "CurvePrices":
                    act(new, new.addNewPriceFeed, asset, old.curveConfig(asset)[0])
                elif name in ("PythPrices", "StorkPrices"):
                    c = old.feedConfig(asset)
                    act(new, new.addNewPriceFeed, asset, c[0], c[1])
                elif name == "RedStone":
                    c = old.feedConfig(asset)
                    act(new, new.addNewPriceFeed, asset, c[0], c[3], c[2])
                elif name == "BlueChipYieldPrices":
                    c = old.priceConfigs(asset)
                    act(new, new.addNewPriceFeed, asset, c[0], *c[4:8])
                elif name == "UndyVaultPrices":
                    c = old.priceConfigs(asset)
                    act(new, new.addNewPriceFeed, asset, *c[3:7])
                elif name == "wsuperOETHbPrices":
                    assert new.hasPriceFeed(asset), ("REMOVED_WRAPPED_PRICE_ROUTE", asset)
                assert new.hasPriceFeed(asset), ("FEED_NOT_REGISTERED", name, asset)
                if getter:
                    row["new_config"] = positional(getattr(new, getter)(asset))
                    # Snapshot observations and ring-buffer cursors are state,
                    # not configuration; fresh sources must warm up separately.
                    config_length = {"BlueChipYieldPrices": 8, "UndyVaultPrices": 7}.get(name)
                    assert row["new_config"][:config_length] == row["live_config"][:config_length], ("FEED_CONFIG_DRIFT", name, asset)
                row["registered"] = True

            # A failed registration must not hide subsequent assets. Each
            # failure remains a blocker; this is diagnostic continuation only.
            for asset in assets:
                source_report["assets"][str(asset)] = {"registered": False}
                self.attempt("configure_" + name + "_" + str(asset),
                             lambda asset=asset: copy_asset(asset))
            if name == "CurvePrices":
                c = old.greenRefPoolConfig()
                if str(c[0]).lower() != ZERO:
                    act(new, new.setGreenRefPoolConfig, c[0], *c[5:10])
                    after = new.greenRefPoolConfig()
                    assert positional([after[0], *after[5:10]]) == positional([c[0], *c[5:10]]), "CURVE_GREEN_REFERENCE_CONFIG_DRIFT"
            if name == "wsuperOETHbPrices":
                for binding in ("MCBETH", "SUPER_OETH", "WRAPPED_SUPER_OETH", "VVV"):
                    assert str(getattr(new, binding)()).lower() == str(getattr(old, binding)()).lower(), ("WRAPPED_BINDING_DRIFT", binding)
            missing = [a for a, row in source_report["assets"].items() if not row["registered"]]
            assert not missing, ("INCOMPLETE_SOURCE_REGISTRATION", name, missing)
        for name in ("ChainlinkPrices", "PythPrices", "StorkPrices", "RedStone",
                     "BlueChipYieldPrices", "UndyVaultPrices", "wsuperOETHbPrices", "CurvePrices"):
            if name in self.sources:
                self.attempt("configure_" + name, lambda name=name: copy_source(name))
        prices = {}
        outcomes = {}
        for i in range(1, int(mc.numAssets())):
            asset = mc.assets(i)
            try:
                prices[str(asset)] = desk.getPrice(asset)
                outcomes[str(asset)] = {"value": prices[str(asset)], "outcome": "priced" if prices[str(asset)] else "zero_unresolved", "error": None}
            except Exception as e:
                prices[str(asset)] = 0
                outcomes[str(asset)] = {"value": None, "outcome": "error", "error": self.sanitized(error_text(e))}
        self.report["post_activation_asset_prices"] = prices
        self.report["post_activation_price_outcomes"] = outcomes
        if any(p == 0 for p in prices.values()):
            self.report.setdefault("blockers", []).append("ZERO_POST_ACTIVATION_PRICES")
        self.report.setdefault("blockers", []).append("ORACLE_SNAPSHOT_WARMUP_AND_LIVE_STATE_REPLAY_NOT_QUALIFIED")
        self.save()

    def check_user_positions(self):
        count = 0
        for vid, rows in self.report["positions"].items():
            vault = self.vaults[vid]
            for row in rows.values():
                user, asset = row["user"], row["asset"]
                assert vault.userBalances(user, asset) == row["shares"], ("USER_SHARES_CHANGED", vid, user, asset)
                assert positional(self.old["Ledger"].userDepositPoints(user, vid, asset)) == positional(row["deposit_points"]), ("USER_POINTS_CHANGED", vid, user, asset)
                if vid == 2:
                    assert positional(vault.userGovData(user, asset)) == positional(row["gov_data"]), ("USER_GOV_LOCK_CHANGED", user, asset)
                count += 1
        self.report["unchanged_user_positions"] = {"rows": count, "shares_points_gov_locks_equal": True}
        self.save()

    def replay_permissions_and_audit_pending(self):
        users = {row["user"] for rows in self.report["positions"].values() for row in rows.values()}
        pairs = set()
        tellers = self.registry_history_addresses(self.hq, "RipeHq", 17)
        switchboards = self.registry_history_addresses(self.hq, "RipeHq", 6)
        charlies = set()
        for address in switchboards:
            charlies.update(self.registry_history_addresses(self.at("Switchboard", address), "Switchboard", 3))
        emitter_abis = {}
        for role, emitters in (("Teller", tellers), ("SwitchboardCharlie", charlies)):
            events = {("0x" + event_abi_to_log_topic(e).hex()).lower(): e
                      for e in self.manifest[role]["abi"] if e.get("type") == "event"
                      and e["name"] in ("UserConfigSet", "UserDelegationSet")}
            if len(events) != 2:
                raise RuntimeError("PERMISSION_EVENT_ABI_INCOMPLETE:" + role)
            emitter_abis.update({address: events for address in emitters})
        for emitter, events in emitter_abis.items():
            logs = self.filtered_logs({"address": emitter, "topics": [list(events)]}, 0, self.block)
            found_users, found_pairs = permission_keys(logs, emitter_abis)
            users.update(found_users)
            pairs.update(found_pairs)
        self.report["permission_emitters"] = sorted(emitter_abis)
        users, pairs = sorted(users), sorted(pairs)
        old, new, charlie = self.old["MissionControl"], self.new["MissionControl"], self.new["SwitchboardCharlie"]
        configs = self.batch_read([(old.userConfig, (user,)) for user in users])
        delegations = self.batch_read([(old.userDelegation, pair) for pair in pairs])
        config_count = delegation_count = 0
        for user, config in zip(users, configs):
            if any(config):
                self.action(charlie, charlie.setUserConfig, user, config)
                config_count += 1
            assert tuple(new.userConfig(user)) == tuple(config)
        for (user, delegate), config in zip(pairs, delegations):
            if any(config):
                self.action(charlie, charlie.setUserDelegation, user, delegate, config)
                delegation_count += 1
            assert tuple(new.userDelegation(user, delegate)) == tuple(config)
        self.report["permissions_replayed"] = {"users_checked": len(users), "nonzero_user_configs": config_count,
            "pairs_checked": len(pairs), "nonzero_delegations": delegation_count,
            "coverage": "vault census plus HQ/Switchboard-authenticated emitter history; recorded manifest ABI event layouts"}
        pending = {}
        controllers = {"HumanResources": self.old["HumanResources"]}
        for i, suffix in enumerate(("Alpha", "Bravo", "Charlie", "Delta", "Echo"), 1):
            controllers[suffix] = self.at("Switchboard" + suffix, self.old["Switchboard"].getAddr(i))
        for name, contract in controllers.items():
            count = int(contract.actionId())
            rows = self.batch_read([(contract.pendingActions, (i,)) for i in range(1, count)])
            pending[name] = {i: positional(row) for i, row in enumerate(rows, 1) if row[0] and row[2] >= self.block}
        self.report["live_pending_controller_actions"] = pending
        if any(pending.values()):
            self.report.setdefault("blockers", []).append("LIVE_PENDING_CONTROLLER_ACTIONS_REQUIRE_REPROPOSAL_DECISION")
        hr = {name: {"old": getattr(self.old["HumanResources"], name)(), "new": getattr(self.new["HumanResources"], name)()}
              for name in ("getTotalCompensation", "getTotalClaimed")}
        assert all(row["old"] == row["new"] for row in hr.values()), "HR totals drift"
        self.report["hr_ledger_backed_totals"] = hr
        self.save()

    def replay_boosters(self):
        old = self.at("BondBooster", self.old["BondRoom"].bondBooster())
        event = next(e for e in self.manifest["BondBooster"]["abi"] if e.get("name") == "BondBoostModified")
        logs = self.logs(old.address, ["0x" + event_abi_to_log_topic(event).hex()], 0, self.block)
        users = {to_checksum_address("0x" + row["data"][2:66][-40:]) for row in logs}
        configs = []
        consumed = {}
        for user in users:
            config = old.config(user)
            if config[3] <= boa.env.evm.patch.block_number:
                continue
            used = old.unitsUsed(user)
            if used:
                consumed[user] = {"config": positional(config), "units_used": used}
            else:
                configs.append((user, tuple(config)))
        self.report["booster_consumption_blockers"] = consumed
        if consumed:
            self.report.setdefault("blockers", []).append("ACTIVE_BOOSTER_UNITS_USED_CANNOT_BE_SEEDED_BY_EXISTING_GOV_API")
        delta = self.new["SwitchboardDelta"]
        for start in range(0, len(configs), 50):
            self.action(delta, delta.setManyBondBoosters, [config for _, config in configs[start:start + 50]])
        for user, config in configs:
            assert tuple(self.new["BondBooster"].config(user)) == config, ("BOOSTER_CONFIG_DRIFT", user)
            assert self.new["BondBooster"].unitsUsed(user) == 0, ("BOOSTER_USAGE_DRIFT", user)
        self.report["active_unconsumed_boosters_replayed"] = len(configs)
        self.report["booster_replay_coverage"] = "nonempty readback" if configs else "zero-case only"
        self.save()

    def check_psm(self):
        old, new = self.old["EndaomentPSM"], self.new["EndaomentPSM"]
        echo = self.new["SwitchboardEcho"]
        for side in ("Mint", "Redeem"):
            topic = "0x" + keccak(text=side + "AllowlistUpdated(address,bool)").hex()
            logs = self.logs(old.address, [topic], 0, self.block)
            users = {to_checksum_address("0x" + row["topics"][1][-40:]) for row in logs}
            getter = side.lower() + "Allowlist"
            for user in users:
                allowed = getattr(old, getter)(user)
                if allowed != getattr(new, getter)(user):
                    self.action(echo, getattr(echo, "updatePsm" + side + "Allowlist"), user, allowed)
                assert getattr(new, getter)(user) == allowed
            name = "shouldEnforce" + side + "Allowlist"
            if getattr(old, name)() != getattr(new, name)():
                self.action(echo, getattr(echo, "setPsmShouldEnforce" + side + "Allowlist"), getattr(old, name)())
            self.report.setdefault("psm_allowlists_replayed", {})[side] = len(users)
        names = ("numBlocksPerInterval", "mintFee", "maxIntervalMint", "redeemFee", "maxIntervalRedeem",
                 "usdcYieldPosition", "shouldAutoDeposit", "shouldEnforceMintAllowlist", "shouldEnforceRedeemAllowlist")
        self.report["psm_config_parity"] = {name: {"before": plain(getattr(old, name)()),
            "after": plain(getattr(new, name)())} for name in names}
        for name, row in self.report["psm_config_parity"].items():
            assert row["before"] == row["after"], ("PSM_CONFIG_DRIFT", name)
        for name in ("globalMintInterval", "globalRedeemInterval"):
            prior = getattr(old, name)()
            self.report.setdefault("psm_legacy_intervals", {})[name] = plain(prior)
            if prior[0] and prior[0] + old.numBlocksPerInterval() > boa.env.evm.patch.block_number:
                raise RuntimeError("PSM_ACTIVE_INTERVAL_REQUIRES_HANDOFF:" + name)
        # Do not reopen PSM or Teller until oracle prices, permissions and
        # treasury checks all pass. This is intentional, not successful activation.
        self.report["psm_sales_held_closed_pending_qualification"] = True
        self.save()

    def stage_all(self, defaults):
        self.report["constructor_profile"] = "Base staged migrations; not cutover qualified"
        self.report["input_fingerprint"] = fingerprint(ROOT, [defaults])
        adapter = DeploymentAdapter(self, defaults)
        for filename in ("2026091400_StageBaseUpgrade.py", "2026091401_StageBaseMissionControl.py",
                         "2026091402_StageBaseOraclesPsmReserves.py"):
            spec = importlib.util.spec_from_file_location(filename, ROOT / "migrations/base-mainnet" / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.migrate(adapter)
        self.report["wave1_deployments_complete"] = True
        self.save()


def main():
    require_unoptimized()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", required=True, type=int)
    parser.add_argument("--defaults", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--diagnose-replacing-pending", action="store_true",
                        help="Fork-only alternate path: record/cancel conflicting pending HQ updates; remains a production blocker")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    run = FullUpdate(os.environ["BASE_MAINNET_RPC_URL"], args.block, args.report, overwrite=args.overwrite)
    run.diagnose_replacing_pending = args.diagnose_replacing_pending
    try:
        execute_diagnostic(run, args)
    except Exception as e:
        run.report.update(status="incomplete", fatal_error=run.sanitized(error_text(e)))
        run.save()
        print("INCOMPLETE", run.report["fatal_error"], flush=True)
        return 1
    run.report["status"] = "not_qualified"
    run.save()
    return 2


def execute_diagnostic(run, args):
    assert int(run.rpc_read("eth_chainId", []), 16) == 8453
    header = run.rpc_read("eth_getBlockByNumber", [hex(args.block), False])
    finalized = run.rpc_read("eth_getBlockByNumber", ["finalized", False])
    assert args.block <= int(finalized["number"], 16)
    run.report.update(block_hash=header["hash"], snapshot_finalized=True, vault_migrations=False)
    run.report["full_update_harness_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run.report["migration_source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / "migrations/base-mainnet").glob("20260914*.py"))}
    with boa.fork(run.rpc, block_identifier=args.block):
        assert boa.env.evm.patch.chain_id == 8453
        run.inventory()
        run.attempt("treasury_inventory", run.treasury_inventory)
        run.attempt("deploy_all_candidates", lambda: run.stage_all(args.defaults))
        if run.report.get("wave1_deployments_complete"):
            run.attempt("historical_user_census", run.census)
            run.attempt("treasury_transfer", run.transfer_treasury)
            run.attempt("register_staged_registries", run.register_candidates)
            if run.report.get("checks", {}).get("register_staged_registries") == "passed":
                run.attempt("activate_departments", run.activate_departments)
                if run.report.get("checks", {}).get("activate_departments") == "passed":
                    run.attempt("configure_and_check_oracles", run.configure_oracles)
                    if run.report.get("checks", {}).get("historical_user_census") == "passed":
                        run.attempt("permissions_pending_actions_hr", run.replay_permissions_and_audit_pending)
                    run.attempt("booster_state_handoff", run.replay_boosters)
                    run.attempt("psm_state_handoff", run.check_psm)
                    if run.report.get("checks", {}).get("historical_user_census") == "passed":
                        run.attempt("user_positions_unchanged", run.check_user_positions)


if __name__ == "__main__":
    raise SystemExit(main())
