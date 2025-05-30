import os

import boa.contracts
import boa.contracts.abi
from mergedeep import merge
import boa
from boa.deployments import get_deployments_db
from scripts.utils import log
from scripts.utils import json_file
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.migration_helpers import (deployed_contracts_manifest,
                                             execute_transaction)


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
        self.gas = 0

        self._previous_manifest = {}
        if previous_timestamp:
            filename = self._manifest_filename('current')
            log.h3(f"Loading previous manifest {filename}")
            self._previous_manifest = json_file.load(filename)

        try:
            self._load_log_file()
            log.h3(f"Log file {self._log_filename()} loaded")
        except:
            log.h3(f"No previous log file: {self._log_filename()}")

    def execute(self, transaction, *args, **kwargs):
        """
        Executes a transaction or skips if already executed.
        Returns the transaction receipt.
        """
        tx = self._run('', transaction, *args, **kwargs)
        self._save_log_file()

        return tx

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
        self._contracts[name] = contract
        self._args[name] = args
        self._save_log_file()
        return contract

    def deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        label = kwargs.get("label", name)
        # remove label from kwargs
        kwargs.pop("label", None)

        contract = self._run(name, boa.load, self._files[name], *args, name=label, **kwargs)
        self._contract_files[label] = name
        self._contracts[label] = contract
        self._args[label] = args
        self._save_log_file()
        return contract

    def soft_deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        contract = self._run(name, boa.load, self._files[name], *args, name=name, **kwargs)
        self._save_log_file()
        return contract

    def get_address(self, name):
        return self._previous_manifest["contracts"][name]["address"]

    def get_contract(self, name):
        return boa.load_partial(self._files[name]).at(self.get_address(name))

    def end(self):
        """
        Ends the migration and saves the manifest file
        """

        self._save_manifest()

        if os.path.exists(self._log_filename()):
            # Delete the log file
            os.remove(self._log_filename())

        log.info(f"Gas spent for migration: {self.gas}")

        return self.gas

    def account(self):
        return self._deploy_args.sender

    def chain(self):
        return self._deploy_args.chain

    def blueprint(self):
        return self._deploy_args.blueprint

    def include_contract(self, name, address):
        self._contracts[name] = address

    def include_abis(self, contracts):
        keys = self._contracts.keys()
        for contract in contracts:
            if not contract in keys:
                self._contracts[contract] = ''

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
            self._transactions.append(str(tx))
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

        self._count += 1

        return tx

    def _log_filename(self):
        return os.path.join(self._history_path, f"{self._timestamp}-log.json")

    def _manifest_filename(self, name):
        return os.path.join(self._history_path, f"{name}-manifest.json")

    def _save_manifest(self):
        log.info(f"\n--- Generating manifest ---\n")

        manifest = deployed_contracts_manifest(self._contracts, self._contract_files, self._args, self._files)
        merged_manifest = merge({}, self._previous_manifest, manifest)
        json_file.save(self._manifest_filename(
            self._timestamp), merged_manifest)
        json_file.save(self._manifest_filename("current"), merged_manifest)
        return merged_manifest

    def _load_log_file(self):
        if self._deploy_args.ignore_logs:
            raise ('no logs')
        logs = json_file.load(self._log_filename())
        self._transactions = logs["transactions"]
        self._contracts = logs["contracts"]

    def _save_log_file(self):
        json_file.save(
            self._log_filename(),
            {
                "transactions": [str(tx) for tx in self._transactions],
                "contracts": {k: v.address if hasattr(v, 'address') else v for k, v in self._contracts.items()}
            },
        )

    def getArgument(self, name):
        return self._deploy_args[name]
