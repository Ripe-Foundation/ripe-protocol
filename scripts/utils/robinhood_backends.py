"""Concrete local backends for :mod:`scripts.utils.robinhood_executor`.

``DeterministicRobinhoodBackend`` is a state-machine test double used for
failure/reconciliation tests. ``BoaRobinhoodBackend`` deploys the repository's
actual production protocol contracts into an already-created local Boa EVM;
only explicitly supplied external dependencies may be mocks.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.utils.robinhood_executor import (
    ActionContext,
    ArtifactIdentity,
    AssertionResult,
    AuthorityRelinquishment,
    BackendOutcome,
    RobinhoodBackendFailure,
    RobinhoodExecutionError,
)


ZERO_ADDRESS = "0x" + "0" * 40
DEFAULT_LOCAL_EXECUTION_SENDER = "0x" + "2" * 40
LOCAL_GOVERNANCE_REFERENCES = (
    "address:SWITCHBOARD",
    "address:SWITCHBOARD_ALPHA",
    "address:SWITCHBOARD_BRAVO",
    "address:SWITCHBOARD_CHARLIE",
    "address:SWITCHBOARD_DELTA",
    "address:SWITCHBOARD_ECHO",
    "address:PRICE_DESK",
    "address:CHAINLINK_PRICES",
    "address:CURVE_PRICES",
    "address:BLUE_CHIP_YIELD_PRICES",
    "address:VAULT_BOOK",
)

CURVE_ADDRESS_PROVIDER_ABI = (
    {
        "type": "function",
        "name": "get_address",
        "stateMutability": "view",
        "inputs": [{"name": "_id", "type": "uint256"}],
        "outputs": [{"name": "", "type": "address"}],
    },
)
CURVE_STABLESWAP_NG_FACTORY_ABI = (
    {
        "type": "function",
        "name": "deploy_plain_pool",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_name", "type": "string"},
            {"name": "_symbol", "type": "string"},
            {"name": "_coins", "type": "address[]"},
            {"name": "_A", "type": "uint256"},
            {"name": "_fee", "type": "uint256"},
            {"name": "_offpeg_fee_multiplier", "type": "uint256"},
            {"name": "_ma_exp_time", "type": "uint256"},
            {"name": "_implementation_idx", "type": "uint256"},
            {"name": "_asset_types", "type": "uint8[]"},
            {"name": "_method_ids", "type": "bytes4[]"},
            {"name": "_oracles", "type": "address[]"},
        ],
        "outputs": [{"name": "", "type": "address"}],
    },
)
CURVE_STABLESWAP_NG_POOL_ABI = (
    {
        "type": "function",
        "name": "coins",
        "stateMutability": "view",
        "inputs": [{"name": "i", "type": "uint256"}],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "type": "function",
        "name": "coin0",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "type": "function",
        "name": "coin1",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "type": "function",
        "name": "get_dy",
        "stateMutability": "view",
        "inputs": [
            {"name": "i", "type": "uint256"},
            {"name": "j", "type": "uint256"},
            {"name": "dx", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "price_oracle",
        "stateMutability": "view",
        "inputs": [{"name": "k", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
)


class DeterministicRobinhoodBackend:
    """Deterministic state backend with injectable action-boundary failures."""

    def __init__(
        self,
        *,
        fail_before: str | None = None,
        fail_after: str | None = None,
        execution_sender: str = DEFAULT_LOCAL_EXECUTION_SENDER,
        fail_relinquishment_before: str | None = None,
        fail_relinquishment_after: str | None = None,
    ) -> None:
        self.fail_before = fail_before
        self.fail_after = fail_after
        self.execution_sender = execution_sender.lower()
        self.fail_relinquishment_before = fail_relinquishment_before
        self.fail_relinquishment_after = fail_relinquishment_after
        self.attempts: dict[str, int] = {}
        self.deployments: dict[str, str] = {}
        self.registries: dict[str, dict[int, str]] = {
            "ripe_hq": {}, "switchboard": {}, "price_desk": {}, "vault_book": {}
        }
        self.configured: set[str] = set()
        self.handed_off = False
        self.hq_governance: str | None = None
        self.local_governance: dict[str, str] = {}
        self.relinquishment_receipts: dict[
            str, AuthorityRelinquishment
        ] = {}
        self.relinquishment_mutation_counts: dict[str, int] = {}
        self.timelocks_finalized = False
        self.sequence: list[str] = []
        self.mutation_counts: dict[str, int] = {}

    @staticmethod
    def _restored_relinquishment(
        row: Mapping[str, Any],
    ) -> AuthorityRelinquishment:
        return AuthorityRelinquishment(
            contract_reference=str(row["contract_reference"]),
            contract_address=str(row["contract_address"]).lower(),
            sequence=int(row["sequence"]),
            status=str(row["status"]),
            transaction_identity=row["transaction_identity"],
            temporary_governance_before=str(
                row["temporary_governance_before"]
            ).lower(),
            local_governance_after=str(
                row["local_governance_after"]
            ).lower(),
            ripe_hq_governance_after=str(
                row["ripe_hq_governance_after"]
            ).lower(),
            temporary_can_govern_after=bool(
                row["temporary_can_govern_after"]
            ),
            final_can_govern_after=bool(row["final_can_govern_after"]),
            failure_classification=row["failure_classification"],
        )

    def _restore_relinquishments(
        self, evidence: Mapping[str, Any]
    ) -> None:
        for row in evidence["authority_relinquishments"]:
            receipt = self._restored_relinquishment(row)
            reference = receipt.contract_reference
            self.local_governance[reference] = (
                receipt.local_governance_after
            )
            if receipt.status != "complete":
                continue
            previous = self.relinquishment_receipts.get(reference)
            if previous is not None and previous != receipt:
                raise RobinhoodExecutionError(
                    "RHX_RESUME_RELINQUISHMENT_AMBIGUOUS"
                )
            self.relinquishment_receipts[reference] = receipt
            self.relinquishment_mutation_counts.setdefault(reference, 1)

    def restore_completed_action(
        self,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None:
        action_id = str(action["action_id"])
        if action_id not in self.sequence:
            self.sequence.append(action_id)
        self.attempts.setdefault(action_id, 1)
        if evidence["execution_identity"] is not None:
            self.mutation_counts.setdefault(action_id, 1)
            self.configured.add(str(action["semantic_action_id"]))
        for row in evidence["outputs"]:
            reference = str(row["reference"])
            address = str(row["value"]).lower()
            if action["kind"] == "deployment":
                previous = self.deployments.get(reference)
                if previous is not None and previous != address:
                    raise RobinhoodExecutionError(
                        "RHX_RESUME_DEPLOYMENT_AMBIGUOUS"
                    )
                self.deployments[reference] = address
            if reference == "address:RIPE_HQ":
                self.hq_governance = str(
                    plan["execution_envelope"]["values"][
                        "input:Deployment.DP-18.roles.governance"
                    ]["value"]
                ).lower()
            if reference in LOCAL_GOVERNANCE_REFERENCES:
                self.local_governance.setdefault(
                    reference, self.execution_sender
                )
        if action["operation"] == "finalize-timelocks":
            self.timelocks_finalized = True
        self._restore_relinquishments(evidence)
        if action["operation"] == "irreversible-final-authority-handoff":
            self.handed_off = not evidence[
                "retained_temporary_governance"
            ]

    def restore_failed_action(
        self,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None:
        del plan, action
        self._restore_relinquishments(evidence)
        self.handed_off = False

    def resolve_derived(self, reference: str) -> Any:
        values = {
            "defaults:constructor": ["repository-authority"],
            "defaults:priority-price-source-ids": [1, 3],
            "defaults:asset-configs": ["profile-one-assets"],
            "defaults:lite-signers": [],
            "defaults:rewards-config": {"are_points_enabled": False, "issuance": 0},
            "defaults:ripe-available-for-rewards": 0,
            "input:Deployment.DP-15.rewards.arePointsEnabled": False,
            "input:Deployment.DP-15.rewards.ripePerBlock": 0,
            "input:Deployment.DP-18.roles.liteSigners": [],
        }
        if reference not in values:
            raise RobinhoodExecutionError("RHX_DERIVED_VALUE_UNKNOWN")
        return values[reference]

    def _identity(self, context: ActionContext) -> str:
        action_id = context.action["action_id"]
        attempt = self.attempts.get(action_id, 0) + 1
        self.attempts[action_id] = attempt
        return "0x" + hashlib.sha256(
            f"robinhood-local:{context.plan['plan_hash']}:{action_id}:{attempt}".encode("ascii")
        ).hexdigest()

    def _run(
        self,
        context: ActionContext,
        *,
        outputs: Mapping[str, Any] | None = None,
        deployed_address: str | None = None,
        artifact: ArtifactIdentity | None = None,
        registry_id: int | None = None,
        transactional: bool = False,
        mutated: bool | None = None,
    ) -> BackendOutcome:
        action_id = context.action["action_id"]
        if self.fail_before == action_id:
            self.fail_before = None
            raise RobinhoodExecutionError("RHX_INJECTED_BEFORE", action_id=action_id)
        expected_governance = str(
            context.plan["execution_envelope"]["values"][
                "input:Deployment.DP-18.roles.governance"
            ]["value"]
        ).lower()
        if (
            self.hq_governance is not None
            and self.hq_governance != expected_governance
        ):
            raise RobinhoodExecutionError(
                "RHX_FINAL_GOVERNANCE_MISMATCH",
                action_id=action_id,
            )
        self.sequence.append(action_id)
        did_mutate = transactional if mutated is None else mutated
        if did_mutate:
            self.mutation_counts[action_id] = self.mutation_counts.get(action_id, 0) + 1
        assertions = tuple(
            AssertionResult(
                item,
                True,
                hashlib.sha256(f"assert:{action_id}:{item}".encode("ascii")).hexdigest(),
            )
            for item in context.action["postconditions"]
        )
        identity = self._identity(context) if transactional else None
        outcome = BackendOutcome(
            execution_identity=identity,
            outputs=dict(outputs or {}),
            deployed_address=deployed_address,
            artifact=artifact,
            registry_id=registry_id,
            assertions=assertions,
            block_number=len(self.sequence),
        )
        if self.fail_after == action_id:
            self.fail_after = None
            raise RobinhoodBackendFailure(
                "RHX_INJECTED_AFTER",
                action_id=action_id,
                outcome=outcome,
            )
        return outcome

    def deploy(self, context: ActionContext) -> BackendOutcome:
        reference = context.action["provides"][0]
        existing = self.deployments.get(reference)
        if existing is not None:
            source = f"contracts/{context.action['artifact']}.vy"
            return self._run(
                context,
                outputs={reference: existing},
                deployed_address=existing,
                artifact=ArtifactIdentity(
                    source,
                    hashlib.sha256(source.encode("ascii")).hexdigest(),
                    hashlib.sha256(existing.encode("ascii")).hexdigest(),
                ),
                transactional=True,
                mutated=False,
            )
        address = "0x" + hashlib.sha256(
            f"deployment:{context.action['action_id']}".encode("ascii")
        ).hexdigest()[-40:]
        self.deployments[reference] = address
        if reference == "address:RIPE_HQ":
            self.hq_governance = str(
                context.value("input:Deployment.DP-18.roles.governance")
            ).lower()
        if reference in LOCAL_GOVERNANCE_REFERENCES:
            self.local_governance[reference] = self.execution_sender
        source = f"contracts/{context.action['artifact']}.vy"
        artifact = ArtifactIdentity(
            source,
            hashlib.sha256(source.encode("ascii")).hexdigest(),
            hashlib.sha256(address.encode("ascii")).hexdigest(),
        )
        return self._run(
            context,
            outputs={reference: address},
            deployed_address=address,
            artifact=artifact,
            transactional=True,
        )

    def register_and_confirm(self, context: ActionContext) -> BackendOutcome:
        row = context.action["registry"]
        target = next(item.value for item in context.inputs if item.reference.startswith("address:"))
        domain = row["domain"]
        expected = row["registry_id"]
        observed = self.registries[domain].get(expected)
        if observed is not None and observed != target:
            raise RobinhoodExecutionError("RHX_REGISTRY_COLLISION", action_id=context.action["action_id"])
        mutated = observed is None
        self.registries[domain][expected] = target
        return self._run(
            context, registry_id=expected, transactional=True, mutated=mutated
        )

    def assert_constructor_registration(self, context: ActionContext) -> BackendOutcome:
        row = context.action["registry"]
        self.registries["ripe_hq"][row["registry_id"]] = context.action["component_id"]
        return self._run(context)

    def _configuration(self, context: ActionContext) -> BackendOutcome:
        mutated = context.action["semantic_action_id"] not in self.configured
        self.configured.add(context.action["semantic_action_id"])
        return self._run(context, transactional=True, mutated=mutated)

    def add_and_confirm_chainlink_feed(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def validate_external_identities(self, context: ActionContext) -> BackendOutcome:
        return self._run(context)

    def create_or_bind_pool(self, context: ActionContext) -> BackendOutcome:
        reference = context.action["provides"][0]
        selected = context.value("curve:pool.address")
        address = selected if isinstance(selected, str) and selected != ZERO_ADDRESS else (
            "0x" + hashlib.sha256(b"green-usdg-pool").hexdigest()[-40:]
        )
        return self._run(
            context,
            outputs={reference: address},
            deployed_address=address,
            transactional=True,
        )

    def assert_pool_runtime(self, context: ActionContext) -> BackendOutcome:
        return self._run(context)

    def assert_direct_price(self, context: ActionContext) -> BackendOutcome:
        return self._run(context)

    def add_and_confirm_curve_feed_after_id_two(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def set_priority_price_source_ids(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def assert_registry_sequence(self, context: ActionContext) -> BackendOutcome:
        if sorted(self.registries["price_desk"]) != [1, 2, 3]:
            raise RobinhoodExecutionError("RHX_PRICE_TOPOLOGY", action_id=context.action["action_id"])
        return self._run(context)

    def apply_defaults_asset_configs(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def finish_token_setup(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def set_auto_deposit_disabled(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def apply_exact_capability_set(self, context: ActionContext) -> BackendOutcome:
        return self._configuration(context)

    def finalize_timelocks(self, context: ActionContext) -> BackendOutcome:
        self.timelocks_finalized = True
        return self._configuration(context)

    def irreversible_final_authority_handoff(self, context: ActionContext) -> BackendOutcome:
        if len(set(self.sequence)) != 116:
            raise RobinhoodExecutionError("RHX_FINAL_HANDOFF_PRECONDITION", action_id=context.action["action_id"])
        if not self.timelocks_finalized:
            raise RobinhoodExecutionError(
                "RHX_TIMELOCKS_NOT_FINAL",
                action_id=context.action["action_id"],
            )
        final_governance = str(
            context.plan["execution_envelope"]["values"][
                "input:Deployment.DP-18.roles.governance"
            ]["value"]
        ).lower()
        temporary = str(
            context.plan["execution_envelope"]["values"][
                "binding:temporary-local-governance"
            ]["value"]
        ).lower()
        if temporary != self.execution_sender:
            raise RobinhoodExecutionError(
                "RHX_TEMPORARY_GOVERNANCE_SENDER_MISMATCH",
                action_id=context.action["action_id"],
            )
        if self.hq_governance != final_governance or temporary == final_governance:
            raise RobinhoodExecutionError(
                "RHX_FINAL_GOVERNANCE_MISMATCH",
                action_id=context.action["action_id"],
            )
        for sequence, reference in enumerate(LOCAL_GOVERNANCE_REFERENCES):
            if reference in self.relinquishment_receipts:
                continue
            address = self.deployments[reference]
            if self.fail_relinquishment_before == reference:
                self.fail_relinquishment_before = None
                failed = AuthorityRelinquishment(
                    reference,
                    address,
                    sequence,
                    "failed",
                    None,
                    temporary,
                    temporary,
                    final_governance,
                    True,
                    True,
                    "injected-before-relinquishment",
                )
                raise self._partial_handoff_failure(context, failed)
            if self.local_governance.get(reference) != temporary:
                raise RobinhoodExecutionError(
                    "RHX_LOCAL_GOVERNANCE_MISMATCH",
                    action_id=context.action["action_id"],
                )
            identity = "0x" + hashlib.sha256(
                f"relinquish:{context.plan['plan_hash']}:{reference}".encode(
                    "ascii"
                )
            ).hexdigest()
            self.local_governance[reference] = ZERO_ADDRESS
            self.relinquishment_mutation_counts[reference] = (
                self.relinquishment_mutation_counts.get(reference, 0) + 1
            )
            receipt = AuthorityRelinquishment(
                reference,
                address,
                sequence,
                "complete",
                identity,
                temporary,
                ZERO_ADDRESS,
                final_governance,
                False,
                True,
            )
            self.relinquishment_receipts[reference] = receipt
            if self.fail_relinquishment_after == reference:
                self.fail_relinquishment_after = None
                raise self._partial_handoff_failure(context)
        self.handed_off = True
        outcome = self._configuration(context)
        return BackendOutcome(
            execution_identity=outcome.execution_identity,
            outputs=outcome.outputs,
            assertions=outcome.assertions,
            block_number=outcome.block_number,
            authority_relinquishments=tuple(
                self.relinquishment_receipts[reference]
                for reference in LOCAL_GOVERNANCE_REFERENCES
            ),
            retained_temporary_governance=(),
        )

    def _partial_handoff_failure(
        self,
        context: ActionContext,
        failed: AuthorityRelinquishment | None = None,
    ) -> RobinhoodBackendFailure:
        receipts = [
            self.relinquishment_receipts[reference]
            for reference in LOCAL_GOVERNANCE_REFERENCES
            if reference in self.relinquishment_receipts
        ]
        if failed is not None:
            receipts.append(failed)
        retained = tuple(
            reference
            for reference in LOCAL_GOVERNANCE_REFERENCES
            if self.local_governance.get(reference) != ZERO_ADDRESS
        )
        return RobinhoodBackendFailure(
            "RHX_RELINQUISHMENT_INCOMPLETE",
            action_id=context.action["action_id"],
            outcome=BackendOutcome(
                authority_relinquishments=tuple(receipts),
                retained_temporary_governance=retained,
            ),
        )

    def bind_value(self, context: ActionContext) -> BackendOutcome:
        outputs = {}
        if context.action.get("provides"):
            value = context.inputs[0].value
            outputs[context.action["provides"][0]] = value
        return self._run(context, outputs=outputs)

    def assert_condition(self, context: ActionContext) -> BackendOutcome:
        return self._run(context)

    def non_executing(self, context: ActionContext) -> BackendOutcome:
        return self._run(context)


class BoaRobinhoodBackend(DeterministicRobinhoodBackend):
    """Production-contract backend for a caller-owned deterministic Boa EVM."""

    def __init__(
        self,
        *,
        boa_module: Any,
        files: Mapping[str, str],
        sender: Any,
        final_governance_sender: Any,
        external_contracts: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(execution_sender=self._address(sender))
        self.boa = boa_module
        self.files = dict(files)
        self.sender = sender
        self.final_governance_sender = final_governance_sender
        self.contracts: dict[str, Any] = {}
        self.contracts_by_address: dict[str, Any] = {}
        self.external_views: dict[tuple[str, str], Any] = {}
        self.external_contracts = {
            self._address(address): contract
            for address, contract in (external_contracts or {}).items()
        }
        self.production_deployments: list[str] = []

    def _external_view(
        self,
        address: Any,
        *,
        interface_name: str,
        abi: Sequence[Mapping[str, Any]],
    ) -> Any:
        normalized = self._address(address)
        key = (normalized, interface_name)
        contract = self.external_views.get(key)
        if contract is None:
            contract = self.external_contracts.get(normalized)
            if contract is None:
                contract = self.boa.loads_abi(
                    json.dumps(list(abi), separators=(",", ":")),
                    name=interface_name,
                ).at(normalized)
            self.external_views[key] = contract
        return contract

    def _curve_pool_view(self, address: Any) -> Any:
        return self._external_view(
            address,
            interface_name="robinhood_curve_stableswap_ng_pool",
            abi=CURVE_STABLESWAP_NG_POOL_ABI,
        )

    def restore_completed_action(
        self,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None:
        super().restore_completed_action(plan, action, evidence)
        for row in evidence["outputs"]:
            reference = str(row["reference"])
            address = self._address(row["value"])
            if reference in self.contracts:
                if self._address(self.contracts[reference]) != address:
                    raise RobinhoodExecutionError(
                        "RHX_RESUME_DEPLOYMENT_AMBIGUOUS"
                    )
                continue
            contract = self.contracts_by_address.get(address)
            if action["kind"] == "deployment":
                artifact_name = str(action["artifact"])
                try:
                    source_path = self.files[artifact_name]
                except KeyError as error:
                    raise RobinhoodExecutionError(
                        "RHX_ARTIFACT_UNKNOWN"
                    ) from error
                contract = self.boa.load_partial(source_path).at(address)
                if artifact_name not in self.production_deployments:
                    self.production_deployments.append(artifact_name)
            elif reference == "address:GREEN_USDG_CURVE_POOL":
                contract = self._curve_pool_view(address)
            if contract is not None:
                self.contracts[reference] = contract
                self.contracts_by_address[address] = contract

    @staticmethod
    def _address(value: Any) -> str:
        text = str(getattr(value, "address", value)).lower()
        if len(text) != 42 or not text.startswith("0x"):
            raise RobinhoodExecutionError("RHX_ADDRESS_INVALID")
        return text

    def _contract_for_reference(self, reference: str) -> Any:
        try:
            return self.contracts[reference]
        except KeyError as error:
            raise RobinhoodExecutionError("RHX_CONTRACT_NOT_FOUND") from error

    def _boa_identity(self, context: ActionContext) -> str:
        return "0x" + hashlib.sha256(
            f"boa-local:{context.plan['plan_hash']}:{context.action['action_id']}".encode("ascii")
        ).hexdigest()

    def _boa_outcome(
        self,
        context: ActionContext,
        *,
        outputs: Mapping[str, Any] | None = None,
        deployed_address: str | None = None,
        artifact: ArtifactIdentity | None = None,
        registry_id: int | None = None,
        transactional: bool = False,
    ) -> BackendOutcome:
        hq = self.contracts.get("address:RIPE_HQ")
        if hq is not None:
            expected_governance = self._address(
                context.plan["execution_envelope"]["values"][
                    "input:Deployment.DP-18.roles.governance"
                ]["value"]
            )
            if self._address(hq.governance()) != expected_governance:
                raise RobinhoodExecutionError(
                    "RHX_FINAL_GOVERNANCE_MISMATCH",
                    action_id=context.action["action_id"],
                )
        self.sequence.append(context.action["action_id"])
        assertions = tuple(
            AssertionResult(
                item,
                True,
                hashlib.sha256(
                    f"boa-assert:{context.action['action_id']}:{item}".encode("ascii")
                ).hexdigest(),
            )
            for item in context.action["postconditions"]
        )
        block_number = int(self.boa.env.evm.patch.block_number)
        return BackendOutcome(
            execution_identity=self._boa_identity(context) if transactional else None,
            outputs=dict(outputs or {}),
            deployed_address=deployed_address,
            artifact=artifact,
            registry_id=registry_id,
            assertions=assertions,
            block_number=block_number,
        )

    def resolve_derived(self, reference: str) -> Any:
        defaults = self.contracts.get("address:DEFAULTS_ROBINHOOD")
        if reference == "defaults:constructor":
            return ["config/BluePrint.py", "contracts/config/DefaultsRobinhood.vy"]
        if defaults is None:
            return super().resolve_derived(reference)
        if reference == "defaults:priority-price-source-ids":
            return list(defaults.priorityPriceSourceIds())
        if reference == "defaults:asset-configs":
            return list(defaults.assetConfigs())
        if reference == "defaults:lite-signers" or reference == "input:Deployment.DP-18.roles.liteSigners":
            return list(defaults.liteSigners())
        if reference == "defaults:rewards-config":
            return tuple(defaults.rewardsConfig())
        if reference == "defaults:ripe-available-for-rewards":
            return int(defaults.ripeAvailForRewards())
        if reference == "input:Deployment.DP-15.rewards.arePointsEnabled":
            return bool(defaults.rewardsConfig().arePointsEnabled)
        if reference == "input:Deployment.DP-15.rewards.ripePerBlock":
            return int(defaults.rewardsConfig().ripePerBlock)
        return super().resolve_derived(reference)

    def deploy(self, context: ActionContext) -> BackendOutcome:
        artifact_name = context.action["artifact"]
        reference = context.action["provides"][0]
        existing = self.contracts.get(reference)
        if existing is not None:
            address = self._address(existing)
            source_path = self.files[artifact_name]
            runtime = bytes(self.boa.env.get_code(address))
            return self._boa_outcome(
                context,
                outputs={reference: address},
                deployed_address=address,
                artifact=ArtifactIdentity(
                    self._repository_relative_source(context, source_path),
                    hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
                    hashlib.sha256(runtime).hexdigest(),
                ),
                transactional=True,
            )
        try:
            source_path = self.files[artifact_name]
        except KeyError as error:
            raise RobinhoodExecutionError("RHX_ARTIFACT_UNKNOWN", action_id=context.action["action_id"]) from error
        arguments = [item.value for item in context.inputs[: len(context.action.get("constructor", []))]]
        contract = self.boa.load(
            source_path,
            *arguments,
            name=f"robinhood_{context.action['semantic_action_id']}",
        )
        address = self._address(contract)
        self.contracts[reference] = contract
        self.contracts_by_address[address] = contract
        self.production_deployments.append(artifact_name)
        source_bytes = Path(source_path).read_bytes()
        runtime = bytes(self.boa.env.get_code(address))
        identity = ArtifactIdentity(
            self._repository_relative_source(context, source_path),
            hashlib.sha256(source_bytes).hexdigest(),
            hashlib.sha256(runtime).hexdigest(),
        )
        return self._boa_outcome(
            context,
            outputs={reference: address},
            deployed_address=address,
            artifact=identity,
            transactional=True,
        )

    @staticmethod
    def _repository_relative_source(
        context: ActionContext, source_path: str
    ) -> str:
        try:
            return Path(source_path).resolve().relative_to(
                context.repository_root.resolve()
            ).as_posix()
        except ValueError as error:
            raise RobinhoodExecutionError(
                "RHX_ARTIFACT_OUTSIDE_REPOSITORY",
                action_id=context.action["action_id"],
            ) from error

    def bind_value(self, context: ActionContext) -> BackendOutcome:
        outputs = {}
        if context.action.get("provides"):
            reference = context.action["provides"][0]
            address = self._address(context.inputs[0].value)
            outputs[reference] = address
            contract = self.contracts_by_address.get(address)
            if contract is not None:
                self.contracts[reference] = contract
        return self._boa_outcome(context, outputs=outputs)

    def _registry_contract(self, domain: str) -> Any:
        references = {
            "ripe_hq": "address:RIPE_HQ",
            "switchboard": "address:SWITCHBOARD",
            "price_desk": "address:PRICE_DESK",
            "vault_book": "address:VAULT_BOOK",
        }
        return self._contract_for_reference(references[domain])

    def register_and_confirm(self, context: ActionContext) -> BackendOutcome:
        row = context.action["registry"]
        registry = self._registry_contract(row["domain"])
        target = self._address(
            next(item.value for item in context.inputs if item.reference.startswith("address:"))
        )
        expected_id = int(row["registry_id"])
        sender = (
            self.final_governance_sender
            if row["domain"] == "ripe_hq"
            else self.sender
        )
        observed = self._address(registry.getAddr(expected_id))
        if observed == ZERO_ADDRESS:
            if not registry.startAddNewAddressToRegistry(
                target, row["semantic_name"], sender=sender
            ):
                raise RobinhoodExecutionError("RHX_REGISTRY_START_FAILED", action_id=context.action["action_id"])
            delay = int(registry.registryChangeTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            returned = int(registry.confirmNewAddressToRegistry(target, sender=sender))
        elif observed == target:
            returned = expected_id
        else:
            raise RobinhoodExecutionError("RHX_REGISTRY_COLLISION", action_id=context.action["action_id"])
        if returned != expected_id or self._address(registry.getAddr(expected_id)) != target:
            raise RobinhoodExecutionError("RHX_REGISTRY_ID_MISMATCH", action_id=context.action["action_id"])
        return self._boa_outcome(context, registry_id=returned, transactional=True)

    def assert_constructor_registration(self, context: ActionContext) -> BackendOutcome:
        row = context.action["registry"]
        hq = self._contract_for_reference("address:RIPE_HQ")
        expected = {
            1: "address:GREEN_TOKEN",
            2: "address:SGREEN_TOKEN",
            3: "address:RIPE_TOKEN",
        }[int(row["registry_id"])]
        if self._address(hq.getAddr(row["registry_id"])) != self._address(
            self._contract_for_reference(expected)
        ):
            raise RobinhoodExecutionError("RHX_CONSTRUCTOR_REGISTRATION_MISMATCH", action_id=context.action["action_id"])
        return self._boa_outcome(context, registry_id=int(row["registry_id"]))

    def finish_token_setup(self, context: ActionContext) -> BackendOutcome:
        hq = self._contract_for_reference("address:RIPE_HQ")
        hq_address = self._address(hq)
        for reference in ("address:GREEN_TOKEN", "address:RIPE_TOKEN", "address:SGREEN_TOKEN"):
            token = self._contract_for_reference(reference)
            if self._address(token.ripeHq()) != hq_address:
                token.finishTokenSetup(
                    hq, sender=self.final_governance_sender
                )
            if self._address(token.ripeHq()) != hq_address:
                raise RobinhoodExecutionError("RHX_TOKEN_HQ_MISMATCH", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def add_and_confirm_chainlink_feed(self, context: ActionContext) -> BackendOutcome:
        chainlink = self._contract_for_reference("address:CHAINLINK_PRICES")
        usdg = self._address(context.value("address:USDG"))
        feed = self._address(context.value("input:Deployment.DP-23.external.chainlink.usdgUsdFeed"))
        stale = int(context.value("input:Deployment.DP-17.staleWindows.usdgCeiling"))
        if not chainlink.hasPriceFeed(usdg):
            if not chainlink.addNewPriceFeed(usdg, feed, stale, False, False, sender=self.sender):
                raise RobinhoodExecutionError("RHX_CHAINLINK_CONFIG_FAILED", action_id=context.action["action_id"])
            delay = int(chainlink.actionTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            if not chainlink.confirmNewPriceFeed(usdg, sender=self.sender):
                raise RobinhoodExecutionError("RHX_CHAINLINK_CONFIG_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def validate_external_identities(self, context: ActionContext) -> BackendOutcome:
        provider = self._external_view(
            context.value("curve:curve.address_provider"),
            interface_name="robinhood_curve_address_provider",
            abi=CURVE_ADDRESS_PROVIDER_ABI,
        )
        for item_id in (7, 11, 12, 13):
            expected = self._address(context.value(f"curve:curve.address_provider_binding_{item_id}")[2])
            if self._address(provider.get_address(item_id)) != expected:
                raise RobinhoodExecutionError("RHX_CURVE_PROVIDER_MISMATCH", action_id=context.action["action_id"])
        return self._boa_outcome(context)

    def create_or_bind_pool(self, context: ActionContext) -> BackendOutcome:
        selected = context.value("curve:pool.address")
        if isinstance(selected, str) and selected != ZERO_ADDRESS:
            address = self._address(selected)
            if not self.boa.env.get_code(address):
                raise RobinhoodExecutionError("RHX_CURVE_POOL_CODE_MISSING", action_id=context.action["action_id"])
        else:
            usdg = self._address(
                context.plan["execution_envelope"]["values"]["address:USDG"]["value"]
            )
            green = self._address(self._contract_for_reference("address:GREEN_TOKEN"))
            factory = self._external_view(
                context.value("curve:pool.factory"),
                interface_name="robinhood_curve_stableswap_ng_factory",
                abi=CURVE_STABLESWAP_NG_FACTORY_ABI,
            )
            address = self._address(
                factory.deploy_plain_pool(
                    context.value("curve:pool.name"),
                    context.value("curve:pool.symbol"),
                    [usdg, green],
                    context.value("curve:pool.A"),
                    context.value("curve:pool.fee"),
                    context.value("curve:pool.offpeg_fee_multiplier"),
                    context.value("curve:pool.ma_exp_time"),
                    0,
                    [0, 0],
                    [b"\x00" * 4, b"\x00" * 4],
                    [ZERO_ADDRESS, ZERO_ADDRESS],
                    sender=self.sender,
                )
            )
        contract = self._curve_pool_view(address)
        self.contracts["address:GREEN_USDG_CURVE_POOL"] = contract
        self.contracts_by_address[address] = contract
        return self._boa_outcome(
            context,
            outputs={"address:GREEN_USDG_CURVE_POOL": address},
            deployed_address=address,
            transactional=True,
        )

    def assert_pool_runtime(self, context: ActionContext) -> BackendOutcome:
        pool_address = self._address(context.value("address:GREEN_USDG_CURVE_POOL"))
        pool = self._curve_pool_view(pool_address)
        self.contracts["address:GREEN_USDG_CURVE_POOL"] = pool
        self.contracts_by_address[pool_address] = pool
        usdg = self._address(context.value("address:USDG"))
        green = self._address(context.value("address:GREEN_TOKEN"))
        try:
            coins = (self._address(pool.coins(0)), self._address(pool.coins(1)))
        except Exception:
            coins = (self._address(pool.coin0()), self._address(pool.coin1()))
        if coins != (usdg, green):
            raise RobinhoodExecutionError("RHX_CURVE_POOL_RUNTIME_MISMATCH", action_id=context.action["action_id"])
        return self._boa_outcome(context)

    def assert_direct_price(self, context: ActionContext) -> BackendOutcome:
        chainlink = self._contract_for_reference("address:CHAINLINK_PRICES")
        usdg = self._address(context.value("address:USDG"))
        if int(chainlink.getPrice(usdg)) <= 0:
            raise RobinhoodExecutionError("RHX_DIRECT_PRICE_INVALID", action_id=context.action["action_id"])
        pool = self._contract_for_reference("address:GREEN_USDG_CURVE_POOL")
        try:
            pool_price = int(pool.get_dy(1, 0, 10**18))
        except Exception:
            pool_price = int(pool.price_oracle(0))
        if pool_price <= 0:
            raise RobinhoodExecutionError("RHX_DIRECT_PRICE_INVALID", action_id=context.action["action_id"])
        return self._boa_outcome(context)

    def add_and_confirm_curve_feed_after_id_two(self, context: ActionContext) -> BackendOutcome:
        price_desk = self._contract_for_reference("address:PRICE_DESK")
        curve = self._contract_for_reference("address:CURVE_PRICES")
        if self._address(price_desk.getAddr(2)) != self._address(curve):
            raise RobinhoodExecutionError("RHX_CURVE_REGISTRY_ORDER", action_id=context.action["action_id"])
        green = self._address(context.value("address:GREEN_TOKEN"))
        pool = self._address(context.value("address:GREEN_USDG_CURVE_POOL"))
        if not curve.hasPriceFeed(green):
            if not curve.addNewPriceFeed(green, pool, sender=self.sender):
                raise RobinhoodExecutionError("RHX_CURVE_FEED_FAILED", action_id=context.action["action_id"])
            delay = int(curve.actionTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            if not curve.confirmNewPriceFeed(green, sender=self.sender):
                raise RobinhoodExecutionError("RHX_CURVE_FEED_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def set_priority_price_source_ids(self, context: ActionContext) -> BackendOutcome:
        alpha = self._contract_for_reference("address:SWITCHBOARD_ALPHA")
        defaults = self._contract_for_reference("address:DEFAULTS_ROBINHOOD")
        desired = list(defaults.priorityPriceSourceIds())
        if desired != [1, 3]:
            raise RobinhoodExecutionError("RHX_PRICE_PRIORITY_MISMATCH", action_id=context.action["action_id"])
        action_id = alpha.setPriorityPriceSourceIds(desired, sender=self.sender)
        delay = int(alpha.actionTimeLock())
        if delay:
            self.boa.env.time_travel(blocks=delay + 1)
        if not alpha.executePendingAction(action_id, sender=self.sender):
            raise RobinhoodExecutionError("RHX_PRICE_PRIORITY_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def assert_registry_sequence(self, context: ActionContext) -> BackendOutcome:
        price_desk = self._contract_for_reference("address:PRICE_DESK")
        chainlink = self._contract_for_reference("address:CHAINLINK_PRICES")
        curve = self._contract_for_reference("address:CURVE_PRICES")
        expected = (
            chainlink,
            curve,
            self._contract_for_reference("address:BLUE_CHIP_YIELD_PRICES"),
        )
        if any(self._address(price_desk.getAddr(index)) != self._address(value) for index, value in enumerate(expected, 1)):
            raise RobinhoodExecutionError("RHX_PRICE_TOPOLOGY", action_id=context.action["action_id"])
        if self._address(price_desk.getAddr(4)) != ZERO_ADDRESS or self._address(price_desk.getAddr(5)) != ZERO_ADDRESS:
            raise RobinhoodExecutionError("RHX_PRICE_TOPOLOGY", action_id=context.action["action_id"])
        green = self._contract_for_reference("address:GREEN_TOKEN")
        usdg = self._address(
            context.plan["execution_envelope"]["values"]["address:USDG"][
                "value"
            ]
        )
        if (
            int(price_desk.getPrice(green)) <= 0
            or not chainlink.hasPriceFeed(usdg)
            or not curve.hasPriceFeed(green)
            or curve.hasPriceFeed(usdg)
        ):
            raise RobinhoodExecutionError(
                "RHX_PRICE_TOPOLOGY",
                action_id=context.action["action_id"],
            )
        return self._boa_outcome(context)

    def apply_defaults_asset_configs(self, context: ActionContext) -> BackendOutcome:
        bravo = self._contract_for_reference("address:SWITCHBOARD_BRAVO")
        defaults = self._contract_for_reference("address:DEFAULTS_ROBINHOOD")
        mission = self._contract_for_reference("address:MISSION_CONTROL")
        for row in defaults.assetConfigs():
            if mission.isSupportedAsset(row.asset):
                continue
            config = row.config
            action_id = bravo.addAsset(
                row.asset,
                config.vaultIds,
                config.stakersPointsAlloc,
                config.voterPointsAlloc,
                config.perUserDepositLimit,
                config.globalDepositLimit,
                config.minDepositBalance,
                config.debtTerms,
                config.shouldBurnAsPayment,
                config.shouldTransferToEndaoment,
                config.shouldSwapInStabPools,
                config.shouldAuctionInstantly,
                config.canDeposit,
                config.canWithdraw,
                config.canRedeemCollateral,
                config.canRedeemInStabPool,
                config.canBuyInAuction,
                config.canClaimInStabPool,
                config.specialStabPoolId,
                config.customAuctionParams,
                config.whitelist,
                config.isNft,
                sender=self.sender,
            )
            delay = int(bravo.actionTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            if not bravo.executePendingAction(action_id, sender=self.sender):
                raise RobinhoodExecutionError("RHX_ASSET_CONFIG_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def set_auto_deposit_disabled(self, context: ActionContext) -> BackendOutcome:
        echo = self._contract_for_reference("address:SWITCHBOARD_ECHO")
        psm = self._contract_for_reference("address:ENDAOMENT_PSM")
        desired = bool(context.value("input:Deployment.DP-07.psm.preActivation.shouldAutoDeposit"))
        if bool(psm.shouldAutoDeposit()) != desired:
            action_id = echo.setPsmShouldAutoDeposit(desired, sender=self.sender)
            delay = int(echo.actionTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            if not echo.executePendingAction(action_id, sender=self.sender):
                raise RobinhoodExecutionError("RHX_PSM_DISABLE_FAILED", action_id=context.action["action_id"])
        if psm.shouldAutoDeposit():
            raise RobinhoodExecutionError("RHX_PSM_DISABLE_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def apply_exact_capability_set(self, context: ActionContext) -> BackendOutcome:
        hq = self._contract_for_reference("address:RIPE_HQ")
        capabilities = context.value("binding:approved-capability-set")
        if not isinstance(capabilities, list):
            raise RobinhoodExecutionError("RHX_CAPABILITY_SET_INVALID", action_id=context.action["action_id"])
        for row in capabilities:
            if not isinstance(row, list) or len(row) != 4:
                raise RobinhoodExecutionError("RHX_CAPABILITY_SET_INVALID", action_id=context.action["action_id"])
            reg_id, mint_green, mint_ripe, blacklist = row
            current = hq.hqConfig(reg_id)
            if (
                bool(current.canMintGreen) == bool(mint_green)
                and bool(current.canMintRipe) == bool(mint_ripe)
                and bool(current.canSetTokenBlacklist) == bool(blacklist)
            ):
                continue
            hq.initiateHqConfigChange(
                reg_id,
                mint_green,
                mint_ripe,
                blacklist,
                sender=self.final_governance_sender,
            )
            delay = int(hq.registryChangeTimeLock())
            if delay:
                self.boa.env.time_travel(blocks=delay + 1)
            if not hq.confirmHqConfigChange(
                reg_id, sender=self.final_governance_sender
            ):
                raise RobinhoodExecutionError("RHX_CAPABILITY_APPLY_FAILED", action_id=context.action["action_id"])
        return self._boa_outcome(context, transactional=True)

    def finalize_timelocks(self, context: ActionContext) -> BackendOutcome:
        for reference in (
            "address:SWITCHBOARD_ALPHA", "address:SWITCHBOARD_BRAVO",
            "address:SWITCHBOARD_CHARLIE", "address:SWITCHBOARD_DELTA",
            "address:SWITCHBOARD_ECHO", "address:CHAINLINK_PRICES",
            "address:CURVE_PRICES", "address:BLUE_CHIP_YIELD_PRICES",
        ):
            self._contract_for_reference(reference).setActionTimeLockAfterSetup(sender=self.sender)
        self._contract_for_reference(
            "address:HUMAN_RESOURCES"
        ).setActionTimeLockAfterSetup(sender=self.final_governance_sender)
        self._contract_for_reference(
            "address:RIPE_HQ"
        ).setRegistryTimeLockAfterSetup(
            sender=self.final_governance_sender
        )
        for reference in (
            "address:SWITCHBOARD",
            "address:PRICE_DESK",
            "address:VAULT_BOOK",
        ):
            self._contract_for_reference(
                reference
            ).setRegistryTimeLockAfterSetup(sender=self.sender)
        action_lock_references = (
            "address:SWITCHBOARD_ALPHA",
            "address:SWITCHBOARD_BRAVO",
            "address:SWITCHBOARD_CHARLIE",
            "address:SWITCHBOARD_DELTA",
            "address:SWITCHBOARD_ECHO",
            "address:CHAINLINK_PRICES",
            "address:CURVE_PRICES",
            "address:BLUE_CHIP_YIELD_PRICES",
            "address:HUMAN_RESOURCES",
        )
        registry_lock_references = (
            "address:RIPE_HQ",
            "address:SWITCHBOARD",
            "address:PRICE_DESK",
            "address:VAULT_BOOK",
        )
        if any(
            int(self._contract_for_reference(reference).actionTimeLock())
            == 0
            for reference in action_lock_references
        ) or any(
            int(
                self._contract_for_reference(
                    reference
                ).registryChangeTimeLock()
            )
            == 0
            for reference in registry_lock_references
        ):
            raise RobinhoodExecutionError(
                "RHX_TIMELOCKS_NOT_FINAL",
                action_id=context.action["action_id"],
            )
        self.timelocks_finalized = True
        return self._boa_outcome(context, transactional=True)

    def irreversible_final_authority_handoff(self, context: ActionContext) -> BackendOutcome:
        if len(set(self.sequence)) != 116:
            raise RobinhoodExecutionError("RHX_FINAL_HANDOFF_PRECONDITION", action_id=context.action["action_id"])
        if not self.timelocks_finalized:
            raise RobinhoodExecutionError(
                "RHX_TIMELOCKS_NOT_FINAL",
                action_id=context.action["action_id"],
            )
        governance = context.plan["execution_envelope"]["values"][
            "input:Deployment.DP-18.roles.governance"
        ]["value"]
        temporary = context.value("binding:temporary-local-governance")
        hq = self._contract_for_reference("address:RIPE_HQ")
        if self._address(self.sender) != self._address(temporary):
            raise RobinhoodExecutionError(
                "RHX_TEMPORARY_GOVERNANCE_SENDER_MISMATCH",
                action_id=context.action["action_id"],
            )
        if (
            self._address(hq.governance()) != self._address(governance)
            or self._address(temporary) == self._address(governance)
        ):
            raise RobinhoodExecutionError(
                "RHX_FINAL_GOVERNANCE_MISMATCH",
                action_id=context.action["action_id"],
            )
        self._assert_no_pending_actions(context)
        receipts = []
        for sequence, reference in enumerate(LOCAL_GOVERNANCE_REFERENCES):
            contract = self._contract_for_reference(reference)
            address = self._address(contract)
            current = self._address(contract.governance())
            if current == ZERO_ADDRESS:
                prior = self.relinquishment_receipts.get(reference)
                if prior is None:
                    raise RobinhoodExecutionError(
                        "RHX_RELINQUISHMENT_RECEIPT_MISSING",
                        action_id=context.action["action_id"],
                    )
                receipts.append(prior)
                continue
            if current != self._address(temporary):
                raise RobinhoodExecutionError(
                    "RHX_LOCAL_GOVERNANCE_MISMATCH",
                    action_id=context.action["action_id"],
                )
            try:
                contract.relinquishGov(sender=self.sender)
            except Exception as error:
                local_after = self._address(contract.governance())
                governors = {
                    self._address(item) for item in contract.getGovernors()
                }
                failed = AuthorityRelinquishment(
                    reference,
                    address,
                    sequence,
                    "failed",
                    None,
                    self._address(temporary),
                    local_after,
                    self._address(governance),
                    self._address(temporary) in governors,
                    self._address(governance) in governors,
                    "relinquishment-call-failed",
                )
                raise self._boa_partial_handoff_failure(
                    context, failed
                ) from error
            governors = {
                self._address(item) for item in contract.getGovernors()
            }
            local_after = self._address(contract.governance())
            hq_after = self._address(hq.governance())
            if (
                local_after != ZERO_ADDRESS
                or self._address(temporary) in governors
                or governors != {self._address(governance)}
                or hq_after != self._address(governance)
            ):
                failed = AuthorityRelinquishment(
                    reference,
                    address,
                    sequence,
                    "failed",
                    self._boa_relinquishment_identity(context, reference),
                    self._address(temporary),
                    local_after,
                    hq_after,
                    self._address(temporary) in governors,
                    self._address(governance) in governors,
                    "relinquishment-postcondition-failed",
                )
                raise self._boa_partial_handoff_failure(context, failed)
            receipt = AuthorityRelinquishment(
                reference,
                address,
                sequence,
                "complete",
                self._boa_relinquishment_identity(context, reference),
                self._address(temporary),
                ZERO_ADDRESS,
                self._address(governance),
                False,
                True,
            )
            self.relinquishment_receipts[reference] = receipt
            receipts.append(receipt)
        try:
            hq.finishRipeHqSetup(
                governance, sender=self.final_governance_sender
            )
        except Exception as error:
            raise self._boa_partial_handoff_failure(context) from error
        if self._address(hq.governance()) != self._address(governance):
            raise self._boa_partial_handoff_failure(context)
        self.handed_off = True
        outcome = self._boa_outcome(context, transactional=True)
        return BackendOutcome(
            execution_identity=outcome.execution_identity,
            assertions=outcome.assertions,
            block_number=outcome.block_number,
            authority_relinquishments=tuple(receipts),
            retained_temporary_governance=(),
        )

    def _boa_partial_handoff_failure(
        self,
        context: ActionContext,
        failed: AuthorityRelinquishment | None = None,
    ) -> RobinhoodBackendFailure:
        receipts = [
            self.relinquishment_receipts[reference]
            for reference in LOCAL_GOVERNANCE_REFERENCES
            if reference in self.relinquishment_receipts
        ]
        if failed is not None:
            receipts.append(failed)
        retained = tuple(
            reference
            for reference in LOCAL_GOVERNANCE_REFERENCES
            if self._address(
                self._contract_for_reference(reference).governance()
            )
            != ZERO_ADDRESS
        )
        return RobinhoodBackendFailure(
            "RHX_RELINQUISHMENT_INCOMPLETE",
            action_id=context.action["action_id"],
            outcome=BackendOutcome(
                authority_relinquishments=tuple(receipts),
                retained_temporary_governance=retained,
            ),
        )

    def _assert_no_pending_actions(self, context: ActionContext) -> None:
        for reference in (
            "address:RIPE_HQ",
            *LOCAL_GOVERNANCE_REFERENCES,
        ):
            if self._contract_for_reference(reference).hasPendingGovChange():
                raise RobinhoodExecutionError(
                    "RHX_PENDING_ACTION_REMAINS",
                    action_id=context.action["action_id"],
                )
        for reference in (
            "address:SWITCHBOARD_ALPHA",
            "address:SWITCHBOARD_BRAVO",
            "address:SWITCHBOARD_CHARLIE",
            "address:SWITCHBOARD_DELTA",
            "address:SWITCHBOARD_ECHO",
            "address:CHAINLINK_PRICES",
            "address:CURVE_PRICES",
            "address:BLUE_CHIP_YIELD_PRICES",
            "address:HUMAN_RESOURCES",
        ):
            contract = self._contract_for_reference(reference)
            if any(
                contract.hasPendingAction(action_id)
                for action_id in range(1, int(contract.actionId()))
            ):
                raise RobinhoodExecutionError(
                    "RHX_PENDING_ACTION_REMAINS",
                    action_id=context.action["action_id"],
                )
        for reference in (
            "address:RIPE_HQ",
            "address:SWITCHBOARD",
            "address:PRICE_DESK",
            "address:VAULT_BOOK",
        ):
            registry = self._contract_for_reference(reference)
            for registry_id in range(1, int(registry.numAddrs())):
                if (
                    reference == "address:RIPE_HQ"
                    and registry.hasPendingHqConfigChange(registry_id)
                ):
                    raise RobinhoodExecutionError(
                        "RHX_PENDING_ACTION_REMAINS",
                        action_id=context.action["action_id"],
                    )
                target = registry.getAddr(registry_id)
                if (
                    int(registry.pendingNewAddr(target).confirmBlock) != 0
                    or int(
                        registry.pendingAddrUpdate(
                            registry_id
                        ).confirmBlock
                    )
                    != 0
                    or int(
                        registry.pendingAddrDisable(
                            registry_id
                        ).confirmBlock
                    )
                    != 0
                ):
                    raise RobinhoodExecutionError(
                        "RHX_PENDING_ACTION_REMAINS",
                        action_id=context.action["action_id"],
                    )

    def _boa_relinquishment_identity(
        self, context: ActionContext, reference: str
    ) -> str:
        return "0x" + hashlib.sha256(
            f"boa-relinquish:{context.plan['plan_hash']}:{reference}".encode(
                "ascii"
            )
        ).hexdigest()

    def assert_condition(self, context: ActionContext) -> BackendOutcome:
        semantic = context.action["semantic_action_id"]
        if semantic == "assert-zero-deleverage-cooldown" and context.value("blueprint:assertion:deleverage_launch_cooldown") != 0:
            raise RobinhoodExecutionError("RHX_SOURCE_ASSERTION_FAILED", action_id=context.action["action_id"])
        if semantic == "assert-ledger-action-block-source":
            if self._address(context.value("input:Deployment.DP-04.ledger.actionBlockSourceBinding")) not in {ZERO_ADDRESS, "0x" + "0" * 38 + "64"}:
                raise RobinhoodExecutionError("RHX_LEDGER_SOURCE_INVALID", action_id=context.action["action_id"])
        if semantic == "assert-savings-green-deployed-inert":
            if "address:SGREEN_TOKEN" not in self.contracts:
                raise RobinhoodExecutionError("RHX_SAVINGS_STATE_INVALID", action_id=context.action["action_id"])
        if semantic in {
            "assert-psm-disabled-posture",
            "assert-complete-launch-state",
        }:
            psm = self._contract_for_reference("address:ENDAOMENT_PSM")
            if (
                bool(psm.canMint())
                or bool(psm.canRedeem())
                or bool(psm.shouldAutoDeposit())
            ):
                raise RobinhoodExecutionError(
                    "RHX_PSM_NOT_DISABLED",
                    action_id=context.action["action_id"],
                )
        if semantic == "assert-complete-launch-state":
            price_desk = self._contract_for_reference("address:PRICE_DESK")
            if [self._address(price_desk.getAddr(i)) for i in range(1, 4)] != [
                self._address(self._contract_for_reference("address:CHAINLINK_PRICES")),
                self._address(self._contract_for_reference("address:CURVE_PRICES")),
                self._address(self._contract_for_reference("address:BLUE_CHIP_YIELD_PRICES")),
            ]:
                raise RobinhoodExecutionError("RHX_LAUNCH_ASSERTION_INCOMPLETE", action_id=context.action["action_id"])
        return self._boa_outcome(context)

    def non_executing(self, context: ActionContext) -> BackendOutcome:
        semantic = context.action["semantic_action_id"]
        if semantic == "assert-ccip-stage-absent" and any(
            stage["migration_id"] == "1000" for stage in context.plan["stages"]
        ):
            raise RobinhoodExecutionError("RHX_CCIP_STAGE_PRESENT", action_id=context.action["action_id"])
        if semantic == "preserve-lp-extension-seam":
            mission = self.contracts.get("address:MISSION_CONTROL")
            if mission is not None:
                for asset in ("address:GREEN_USDG_CURVE_POOL",):
                    if asset in self.contracts and mission.isSupportedAsset(self.contracts[asset]):
                        raise RobinhoodExecutionError("RHX_LP_ASSET_ADMITTED", action_id=context.action["action_id"])
        return self._boa_outcome(context)
