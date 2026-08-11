import copy
import os
from pathlib import PurePosixPath

import boa.contracts
import boa.contracts.abi
from mergedeep import merge
import boa
from scripts.utils import log
from scripts.utils import json_file
from scripts.utils import solidity
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.migration_helpers import (deployed_contracts_manifest,
                                             execute_transaction)
from scripts.utils.manifest_schema import (
    ManifestError,
    validate_execution_handoff,
)
from scripts.utils.migration_runner import (
    MigrationPlanError,
    validate_execution_plan_artifact,
)


_ROBINHOOD_HISTORY_SUFFIXES = (
    PurePosixPath("migration_history/robinhood-mainnet/v1"),
    PurePosixPath("migration_history/robinhood-testnet/v1"),
)


def _is_robinhood_v2_history_path(history_path):
    normalized = PurePosixPath(str(history_path).replace("\\", "/"))
    return any(
        normalized == suffix
        or normalized.parts[-len(suffix.parts):] == suffix.parts
        for suffix in _ROBINHOOD_HISTORY_SUFFIXES
    )


class Migration:
    def __init__(self, deploy_args: DeployArgs, files, timestamp, previous_timestamp, history_path):
        self._hq = None
        self._files = files
        self._timestamp = timestamp
        self._previous_timestamp = previous_timestamp
        self._history_path = history_path
        self._deploy_args = deploy_args
        self._count = 0
        self._transactions = []
        self._contracts = {}
        self._contract_files = {}
        self._args = {}
        self._manifest_v2 = _is_robinhood_v2_history_path(history_path)
        self._manifest_v2_results = {}
        self.gas = 0

        if self._manifest_v2:
            self._previous_manifest = {}
            return

        try:
            filename = self._manifest_filename('current')
            log.h3(f"Loading previous manifest {filename}")
            self._previous_manifest = json_file.load(filename)
        except:
            self._previous_manifest = {}

        pending_filename = self._pending_manifest_filename()
        has_pending_manifest = os.path.exists(pending_filename)
        if has_pending_manifest:
            if self._deploy_args.ignore_logs:
                raise RuntimeError("MIGRATION_FORCE_REPLAY_PENDING")
            try:
                pending_manifest = json_file.load(pending_filename)
            except Exception:
                raise RuntimeError("MIGRATION_PENDING_MANIFEST_INVALID") from None
            self._previous_manifest = merge(
                {}, self._previous_manifest, pending_manifest
            )

        loaded_log = False
        try:
            self._load_log_file()
            loaded_log = True
            log.h3(f"Log file {self._log_filename()} loaded")
        except:
            log.h3(f"No previous log file: {self._log_filename()}")
        if has_pending_manifest and not loaded_log:
            raise RuntimeError("MIGRATION_RESUME_STATE_INCOMPLETE")

    def rpc(self):
        return self._deploy_args.rpc

    def handoff_manifest_v2_action_result(self, semantic_plan, action_result):
        """
        Validate and retain one typed Robinhood result for an H-06 record.

        This is an in-memory semantic handoff only. It never submits, retries,
        writes history, or promotes current.
        """
        if not self._manifest_v2:
            raise ManifestError("H06_HANDOFF_PROFILE_REQUIRED")
        validated = validate_execution_handoff(
            semantic_plan,
            action_result,
        )
        action_id = validated["action_id"]
        if action_id in self._manifest_v2_results:
            raise ManifestError("H06_HANDOFF_ACTION_DUPLICATE")
        self._manifest_v2_results[action_id] = validated
        return validated

    def manifest_v2_action_results(self):
        """Return validated typed results in semantic action-ID order."""
        if not self._manifest_v2:
            raise ManifestError("H06_HANDOFF_PROFILE_REQUIRED")
        return tuple(
            self._manifest_v2_results[action_id]
            for action_id in sorted(self._manifest_v2_results)
        )

    def apply_robinhood_stage(self, stage):
        """Hand one shared literal stage to a separately authorized executor.

        Static planning reads the exact same ``MIGRATION_STAGE`` literal.  The
        Network policy remains controlling.  The CLI installs the dedicated
        executor only after its profile, identity, account, plan, repository,
        envelope, and history gates succeed.  Merely importing or invoking a
        Robinhood migration can never fall through to legacy transactions.
        """
        if not self._manifest_v2:
            raise ManifestError("H06_HANDOFF_PROFILE_REQUIRED")
        execution_plan = getattr(
            self._deploy_args, "robinhood_execution_plan", None
        )
        repository_root = getattr(
            self._deploy_args, "robinhood_repository_root", None
        )
        if execution_plan is None or repository_root is None:
            raise ManifestError("H06_PRODUCTION_PLAN_REQUIRED")
        try:
            validate_execution_plan_artifact(
                execution_plan, repository_root=repository_root
            )
        except MigrationPlanError:
            raise ManifestError("H06_PRODUCTION_PLAN_REQUIRED") from None
        executor = getattr(self._deploy_args, "robinhood_stage_executor", None)
        if executor is None:
            raise ManifestError("H06_EXECUTION_HANDOFF_REQUIRED")
        return executor(self, stage)

    def execute(self, transaction, *args, **kwargs):
        """
        Executes a transaction or skips if already executed.
        Returns the transaction receipt.
        """
        tx = self._run('', transaction, *args, **kwargs)
        self._save_log_file()

        return tx

    def _register_contract(self, name, label, contract, args):
        self._contract_files[label] = name
        self._contracts[label] = contract
        self._args[label] = args
        self._append_manifest(label)
        self._save_log_file()
        return contract

    def deploy_bp(self, name):
        """
        Deploys contract with given name as blueprint or skips if already deployed
        Returns the deployed contract.
        """
        args = []
        kwargs = {}

        def deploy_bp_wrapper(*args, **kwargs):
            c = boa.load_partial(self._files[name]).deploy_as_blueprint()
            return c

        contract = self._run(name, deploy_bp_wrapper, *args, **kwargs)
        return self._register_contract(name, name, contract, args)

    def deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        label = kwargs.get("label", name)
        # remove label from kwargs
        kwargs.pop("label", None)

        contract = self._run(name, boa.load, self._files[name], *args, name=label, **kwargs)
        return self._register_contract(name, label, contract, args)

    def deploy_solidity(self, name, *args, **kwargs):
        """
        Deploys the Solidity contract with given name and args (built from `solidity/`
        with foundry) or skips if already deployed.
        Returns the deployed contract.
        """
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_EXECUTION_FORBIDDEN")

        label = kwargs.pop("label", name)
        source_file = kwargs.pop("source_file", None)

        next_transaction = self._count + 1
        log.h2(
            f"Transaction {next_transaction} for migration with timestamp {self._timestamp} - Deploying {name}"
        )

        if self._curr_transaction():
            log.h3(f"Skipping transaction {next_transaction}")
            self._count += 1
            return solidity.at(name, self.get_address(label), source_file)

        contract = solidity.deploy(
            name,
            *args,
            sender=self._deploy_args.sender.address,
            source_file=source_file,
        )
        log.h3(f"Contract {name} deployed at {contract.address}")

        self._transactions.append(str(contract.address))
        self._count += 1

        # Solidity contracts are recorded by address only. The manifest stores
        # Vyper compiler output for everything else, and Foundry artifacts have
        # no equivalent (use `get_solidity_contract` to load them back).
        self.include_contract(label, str(contract.address))
        self._save_log_file()

        return contract

    def get_solidity_contract(self, name, address=None, source_file=None, label=None):
        """
        Returns a previously deployed Solidity contract, with the ABI from
        `solidity/`.
        """
        address = address or self.get_address(label or name)
        return solidity.at(name, address, source_file)

    def get_address_on_chain(self, chain, name):
        """
        Address of a contract deployed by another chain's migrations in the
        same environment.
        """
        filename = self._manifest_filename("current").replace(
            os.path.join("", self.chain(), ""), os.path.join("", chain, "")
        )
        return json_file.load(filename)["contracts"][name]["address"]

    def soft_deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        contract = self._run(name, boa.load, self._files[name], *args, name=name, **kwargs)
        self._append_manifest(name)
        self._save_log_file()
        return contract

    def get_address(self, name):
        return self._previous_manifest["contracts"][name]["address"]

    def get_contract(self, name, address=None):
        file = self._previous_manifest["contracts"][name]["file"]
        address = address or self.get_address(name)
        return boa.load_partial(file).at(address)

    def end(self):
        """
        Ends the migration and saves the manifest file
        """
        if self._manifest_v2:
            log.info(f"Gas spent for migration: {self.gas}")
            return self.gas

        # A numbered manifest is a completed-migration checkpoint. During the
        # migration, deployments live only in a timestamp-scoped pending file;
        # neither a partial step nor a failed retry may become `current`.
        pending_filename = self._pending_manifest_filename()
        final_manifest = self._previous_manifest
        if os.path.exists(pending_filename):
            try:
                final_manifest = json_file.load(pending_filename)
            except Exception:
                raise RuntimeError("MIGRATION_PENDING_MANIFEST_INVALID") from None
        # Publish current first and the numeric completion marker last. If the
        # process dies between them, auto-resume selects this same migration
        # and its log/pending journal completes the checkpoint; it never skips
        # ahead with an old current manifest.
        json_file.save(self._manifest_filename("current"), final_manifest)
        json_file.save(
            self._manifest_filename(self._timestamp), final_manifest
        )

        if os.path.exists(pending_filename):
            os.remove(pending_filename)
        if os.path.exists(self._log_filename()):
            os.remove(self._log_filename())

        log.info(f"Gas spent for migration: {self.gas}")

        return self.gas

    def account(self):
        return self._deploy_args.sender

    def chain(self):
        return self._deploy_args.chain

    def timestamp(self):
        return self._timestamp

    def blueprint(self):
        return self._deploy_args.blueprint

    def include_contract(self, name, address):
        self._contracts[name] = address
        self._append_manifest(name)

    def promote_candidate(
        self,
        canonical_name,
        candidate_label,
        registry,
        registry_id,
        activation_candidate_label=None,
    ):
        """Promote a complete candidate record after authoritative readback.

        Deployment and registry activation are intentionally separate steps.
        This helper advances the canonical manifest label only after the live
        registry points at the candidate, and copies the candidate record as a
        whole so stale ABI, source, compiler, or constructor metadata cannot
        survive from the previous canonical deployment.
        """
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_MANIFEST_WRITE_FORBIDDEN")

        contracts = self._previous_manifest.get("contracts")
        if not isinstance(contracts, dict):
            raise RuntimeError("MIGRATION_MANIFEST_CONTRACTS_MISSING")
        if candidate_label not in contracts:
            raise RuntimeError("MIGRATION_CANDIDATE_CONTRACT_MISSING")

        activation_label = activation_candidate_label or candidate_label
        if activation_label not in contracts:
            raise RuntimeError(
                "MIGRATION_ACTIVATION_CANDIDATE_CONTRACT_MISSING"
            )

        candidate = contracts[candidate_label]
        if not isinstance(candidate, dict):
            raise RuntimeError("MIGRATION_CANDIDATE_RECORD_INVALID")
        candidate_address = candidate.get("address")
        if (
            not isinstance(candidate_address, str)
            or len(candidate_address) != 42
            or not candidate_address.startswith("0x")
        ):
            raise RuntimeError("MIGRATION_CANDIDATE_ADDRESS_INVALID")
        try:
            address_value = int(candidate_address[2:], 16)
        except ValueError:
            raise RuntimeError("MIGRATION_CANDIDATE_ADDRESS_INVALID") from None
        if address_value == 0:
            raise RuntimeError("MIGRATION_CANDIDATE_ADDRESS_INVALID")

        activation_candidate = contracts[activation_label]
        if not isinstance(activation_candidate, dict):
            raise RuntimeError(
                "MIGRATION_ACTIVATION_CANDIDATE_RECORD_INVALID"
            )
        activation_address = activation_candidate.get("address")
        if (
            not isinstance(activation_address, str)
            or len(activation_address) != 42
            or not activation_address.startswith("0x")
        ):
            raise RuntimeError(
                "MIGRATION_ACTIVATION_CANDIDATE_ADDRESS_INVALID"
            )
        try:
            activation_value = int(activation_address[2:], 16)
        except ValueError:
            raise RuntimeError(
                "MIGRATION_ACTIVATION_CANDIDATE_ADDRESS_INVALID"
            ) from None
        if activation_value == 0:
            raise RuntimeError(
                "MIGRATION_ACTIVATION_CANDIDATE_ADDRESS_INVALID"
            )

        registry_address = str(registry.getAddr(registry_id))
        if registry_address.lower() != activation_address.lower():
            raise RuntimeError("MIGRATION_CANDIDATE_REGISTRY_MISMATCH")

        # A canonical label may be absent when this is the first deployment of
        # a new component.  The candidate and its activation witness still
        # have to be complete, nonzero manifest records and the authoritative
        # registry readback above must prove the activation before the label is
        # created.  Existing canonicals follow this exact same replacement
        # path, so no stale metadata can leak into either case.
        promoted_manifest = copy.deepcopy(self._previous_manifest)
        promoted_manifest["contracts"][canonical_name] = copy.deepcopy(
            candidate
        )
        self._previous_manifest = promoted_manifest
        json_file.save(self._pending_manifest_filename(), promoted_manifest)
        log.h3(
            f"{candidate_label} promoted to {canonical_name} in pending manifest "
            f"after {activation_label} registry readback"
        )
        return candidate_address

    def include_abis(self, contracts):
        keys = self._contracts.keys()
        for contract in contracts:
            if not contract in keys:
                self._contracts[contract] = ''
            self._append_manifest(contract)

    def _curr_transaction(self):
        """
        Returns the current transaction if it's been already executed.
        """
        if self._count == len(self._transactions):
            return None
        return self._transactions[self._count]

    def _clean_message(self, message, contract_name, *args):
        if contract_name != '':
            return f"Deploying {contract_name}"

        if 'ABI ' in message:
            try:
                abi_part = message.split('ABI ')[1]
                parts = abi_part.split('.vy.')
                contract_name = parts[0].split('/')[-1]
                return f"{contract_name}.{parts[1]} - {args}"
            except:
                return message

        return message

    def _run(self, contract_name, transaction,  *args, **kwargs):
        """
        Executes a transaction or skips if already executed.
        Returns the transaction receipt as string.
        """
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_EXECUTION_FORBIDDEN")

        next_transaction = self._count + 1
        message = self._clean_message(str(transaction), contract_name, *args)

        log.h2(
            f"Transaction {next_transaction} for migration with timestamp {self._timestamp} - {message}"
        )

        tx = self._curr_transaction()

        if not tx:
            # Only include sender in kwargs if contract_name is empty
            if contract_name == '':
                kwargs['sender'] = self._deploy_args.sender.address

            tx = execute_transaction(transaction, *args, **kwargs)
            if tx is None:
                raise RuntimeError("MIGRATION_TRANSACTION_RESULT_MISSING")
            self._transactions.append(tx)
            gas = 0
            if contract_name != '':
                if hasattr(tx, '_computation') and tx._computation is not None:
                    gas = tx._computation.get_gas_used()
                log.h3(
                    f"Contract {contract_name} deployed at {tx.address}"
                )
            else:
                log.h3(
                    f"Transaction confirmed"
                )
                try:
                    contract_name = message.split('.')[0]
                    contract = self._contracts[contract_name]
                    gas = contract._computation.get_gas_used()
                except:
                    pass
            self.gas += gas

        else:
            log.h3(f"Skipping transaction {next_transaction}")
            if contract_name != '':
                self._count += 1
                return self.get_contract(kwargs['name'])

        self._count += 1
        return tx

    def _log_filename(self):
        return os.path.join(self._history_path, f"{self._timestamp}-log.json")

    def _manifest_filename(self, name):
        return os.path.join(self._history_path, f"{name}-manifest.json")

    def _pending_manifest_filename(self):
        return os.path.join(
            self._history_path, f"{self._timestamp}-pending-manifest.json"
        )

    def _append_manifest(self, contract_name):
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_MANIFEST_WRITE_FORBIDDEN")

        contract = self._contracts[contract_name]
        contracts = {contract_name: contract}

        manifest = deployed_contracts_manifest(contracts, self._contract_files, self._args, self._files)
        merged_manifest = merge({}, self._previous_manifest, manifest)
        self._previous_manifest = merged_manifest

        json_file.save(self._pending_manifest_filename(), merged_manifest)

        log.h3(f"{contract_name} added to pending manifest")
        return merged_manifest

    def _load_log_file(self):
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_LOG_FORBIDDEN")
        if self._deploy_args.ignore_logs:
            raise RuntimeError("MIGRATION_LOG_REPLAY_REQUESTED")
        logs = json_file.load(self._log_filename())
        self._transactions = logs["transactions"]

    def _save_log_file(self):
        if self._manifest_v2:
            raise ManifestError("H06_LEGACY_LOG_FORBIDDEN")
        json_file.save(
            self._log_filename(),
            {
                "transactions": [str(tx) for tx in self._transactions],
            },
        )

    def getArgument(self, name):
        return self._deploy_args[name]
