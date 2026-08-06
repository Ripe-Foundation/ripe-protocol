from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


class ProfileEnvironment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    MAINNET = "mainnet"


class PathState(str, Enum):
    ABSENT = "absent"
    EXISTING = "existing"
    PROPOSED = "proposed"


class VerifierProvider(str, Enum):
    UNSUPPORTED = "unsupported"
    ETHERSCAN_V2 = "etherscan_v2"
    BLOCKSCOUT = "blockscout"


class Operation(str, Enum):
    PROFILE_INSPECTION = "profile_inspection"
    LOCAL_RUNTIME = "local_runtime"
    REPOSITORY_READ = "repository_read"
    MIGRATION_PLAN = "migration_plan"
    MIGRATION_FORK = "migration_fork"
    MIGRATION_LIVE = "migration_live"
    CONSOLE_EXPLORATION = "console_exploration"
    CONSOLE_EVIDENCE = "console_evidence"
    VERIFICATION = "verification"


class OperationOutcome(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    BLOCKED_PENDING_POLICY = "blocked_pending_policy"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class NetworkIdentity:
    profile_id: str
    chain_id: int | None
    environment: ProfileEnvironment


@dataclass(frozen=True, slots=True)
class RpcPolicy:
    env_name: str | None
    allowed_operations: frozenset[Operation]
    require_chain_id_match: bool


@dataclass(frozen=True, slots=True)
class RepositoryPolicy:
    blueprint_id: str | None
    migration_dir: PurePosixPath | None
    migration_state: PathState
    history_dir: PurePosixPath | None
    history_state: PathState


@dataclass(frozen=True, slots=True)
class ForkPolicy:
    require_source_chain_id_match: bool
    pin_required_for_evidence: bool
    latest_allowed_for_exploration: bool
    dirty_allowed_for_exploration: bool
    allow_submission: bool = False


@dataclass(frozen=True, slots=True)
class VerifierPolicy:
    provider: VerifierProvider
    adapter_id: str | None
    api_key_env_name: str | None
    operation_outcome: OperationOutcome


@dataclass(frozen=True, slots=True)
class OperationPolicy:
    operation: Operation
    outcome: OperationOutcome
    requires_rpc: bool = False
    requires_identity: bool = False
    requires_repository: bool = False
    requires_account: bool = False
    requires_verifier: bool = False


@dataclass(frozen=True, slots=True)
class NetworkProfile:
    identity: NetworkIdentity
    rpc: RpcPolicy
    repository: RepositoryPolicy
    fork: ForkPolicy
    verifier: VerifierPolicy
    operations: tuple[OperationPolicy, ...]
    live_account_backend_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProfileAlias:
    alias: str
    canonical_profile_id: str


@dataclass(frozen=True, slots=True)
class VerifiedNetworkIdentity:
    profile_id: str
    operation: Operation
    expected_chain_id: int
    observed_chain_id: int


@dataclass(frozen=True, slots=True)
class ResolvedRepositoryPaths:
    profile_id: str
    migration_dir: Path
    history_dir: Path


@dataclass(frozen=True, slots=True)
class RedactedRpc:
    _value: str
    profile_id: str
    operation: Operation
    reference: str

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return (
            f"<rpc profile={self.profile_id} operation={self.operation.value} "
            f"reference={self.reference} redacted>"
        )

    def __repr__(self) -> str:
        return (
            "RedactedRpc("
            f"profile_id={self.profile_id!r}, "
            f"operation={self.operation.value!r}, "
            f"reference={self.reference!r}, value='<redacted>')"
        )


class NetworkProfileError(RuntimeError):
    __slots__ = (
        "code",
        "profile_id",
        "operation",
        "expected_chain_id",
        "observed_chain_id",
        "env_name",
    )

    def __init__(
        self,
        code: str,
        *,
        profile_id: str | None = None,
        operation: Operation | None = None,
        expected_chain_id: int | None = None,
        observed_chain_id: int | None = None,
        env_name: str | None = None,
    ) -> None:
        self.code = code
        self.profile_id = _safe_profile_label(profile_id)
        self.operation = operation
        self.expected_chain_id = expected_chain_id
        self.observed_chain_id = observed_chain_id
        self.env_name = env_name
        super().__init__(str(self))

    def __str__(self) -> str:
        fields = [self.code]
        if self.profile_id is not None:
            fields.append(f"profile={self.profile_id}")
        if self.operation is not None:
            fields.append(f"operation={self.operation.value}")
        if self.expected_chain_id is not None:
            fields.append(f"expected_chain_id={self.expected_chain_id}")
        if self.observed_chain_id is not None:
            fields.append(f"observed_chain_id={self.observed_chain_id}")
        if self.env_name is not None:
            fields.append(f"env={self.env_name}")
        return " ".join(fields)

    def __repr__(self) -> str:
        return f"NetworkProfileError({str(self)!r})"


def _safe_profile_label(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return "<invalid>"
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        return value
    return "<invalid>"


def _policy(
    operation: Operation,
    outcome: OperationOutcome,
    *,
    rpc: bool = False,
    identity: bool = False,
    repository: bool = False,
    account: bool = False,
    verifier: bool = False,
) -> OperationPolicy:
    return OperationPolicy(
        operation,
        outcome,
        rpc,
        identity,
        repository,
        account,
        verifier,
    )


_SUPPORTED = OperationOutcome.SUPPORTED
_UNSUPPORTED = OperationOutcome.UNSUPPORTED
_BLOCKED = OperationOutcome.BLOCKED_PENDING_POLICY


def _operations(*policies: OperationPolicy) -> tuple[OperationPolicy, ...]:
    operation_map = {
        operation: _policy(
            operation,
            _SUPPORTED
            if operation is Operation.PROFILE_INSPECTION
            else _UNSUPPORTED,
        )
        for operation in Operation
    }
    operation_map.update({policy.operation: policy for policy in policies})
    return tuple(operation_map[operation] for operation in Operation)


def _rpc_policy(
    env_name: str | None, operations: tuple[OperationPolicy, ...]
) -> RpcPolicy:
    return RpcPolicy(
        env_name,
        frozenset(
            policy.operation for policy in operations if policy.requires_rpc
        ),
        env_name is not None,
    )


_LOCAL_OPERATIONS = _operations(
    _policy(
        Operation.LOCAL_RUNTIME,
        _SUPPORTED,
        identity=True,
        account=True,
    ),
)

_BASE_MAINNET_OPERATIONS = _operations(
    _policy(
        Operation.REPOSITORY_READ,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
    ),
    _policy(
        Operation.MIGRATION_FORK,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
        account=True,
    ),
    # Base has deployed and verified through this path since v1. The H-02
    # profile work classed both as blocked while the Robinhood launch controls
    # were being designed; that scope never included stopping Base releases.
    # Robinhood stays blocked -- see _ROBINHOOD_OPERATIONS.
    _policy(
        Operation.MIGRATION_LIVE,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
        account=True,
    ),
    _policy(
        Operation.CONSOLE_EXPLORATION,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
    ),
    _policy(
        Operation.CONSOLE_EVIDENCE,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
    ),
    # VERIFICATION stays blocked deliberately. scripts/verify.py has no
    # submission path -- it selects a route, echoes the manifest, then raises
    # H02_OPERATION_INVALID unconditionally. The real implementation lives in
    # scripts/utils/verify_etherscan.py (verify_from_manifest) and is tested by
    # tests/deployment/test_verifier_adapters.py, but nothing calls it.
    # Marking this SUPPORTED would advertise a capability the CLI lacks and
    # disclose the manifest path before dead-ending. Flip it only together with
    # wiring verify.py to verify_from_manifest.
    _policy(Operation.VERIFICATION, _BLOCKED, verifier=True),
)

_BASE_SEPOLIA_OPERATIONS = _operations(
    _policy(
        Operation.CONSOLE_EXPLORATION,
        _SUPPORTED,
        rpc=True,
        identity=True,
    ),
)

_ROBINHOOD_OPERATIONS = _operations(
    _policy(Operation.MIGRATION_PLAN, _SUPPORTED),
    _policy(
        Operation.REPOSITORY_READ, _BLOCKED, repository=True
    ),
    # Owner-approved for launch. Robinhood is deployed from a Ledger that is
    # also RipeHq governance until the 0900 handoff, exactly as Base was.
    _policy(
        Operation.MIGRATION_FORK,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
        account=True,
    ),
    _policy(
        Operation.MIGRATION_LIVE,
        _SUPPORTED,
        rpc=True,
        identity=True,
        repository=True,
        account=True,
    ),
    _policy(
        Operation.CONSOLE_EXPLORATION,
        _SUPPORTED,
        rpc=True,
        identity=True,
    ),
    _policy(
        Operation.CONSOLE_EVIDENCE,
        _BLOCKED,
        rpc=True,
        identity=True,
        repository=True,
    ),
    _policy(Operation.VERIFICATION, _BLOCKED, verifier=True),
)


NETWORK_PROFILES: tuple[NetworkProfile, ...] = (
    NetworkProfile(
        identity=NetworkIdentity(
            "local", None, ProfileEnvironment.LOCAL
        ),
        rpc=_rpc_policy(None, _LOCAL_OPERATIONS),
        repository=RepositoryPolicy(
            None, None, PathState.ABSENT, None, PathState.ABSENT
        ),
        fork=ForkPolicy(False, False, True, True),
        verifier=VerifierPolicy(
            VerifierProvider.UNSUPPORTED,
            None,
            None,
            _UNSUPPORTED,
        ),
        operations=_LOCAL_OPERATIONS,
    ),
    NetworkProfile(
        identity=NetworkIdentity(
            "base-mainnet", 8453, ProfileEnvironment.MAINNET
        ),
        rpc=_rpc_policy("BASE_MAINNET_RPC_URL", _BASE_MAINNET_OPERATIONS),
        repository=RepositoryPolicy(
            "base",
            PurePosixPath("migrations/base-mainnet"),
            PathState.EXISTING,
            PurePosixPath("migration_history/base-mainnet/v1"),
            PathState.EXISTING,
        ),
        fork=ForkPolicy(True, True, True, True),
        verifier=VerifierPolicy(
            VerifierProvider.ETHERSCAN_V2,
            "etherscan_v2",
            "ETHERSCAN_API_KEY",
            _BLOCKED,
        ),
        # Required whenever MIGRATION_LIVE is SUPPORTED: the registry refuses to
        # enable live deployment without naming the approved signing backends.
        # These are the three scripts/migrate.py can select between.
        live_account_backend_ids=("env-private-key", "ledger", "safe"),
        operations=_BASE_MAINNET_OPERATIONS,
    ),
    NetworkProfile(
        identity=NetworkIdentity(
            "base-sepolia", 84532, ProfileEnvironment.TEST
        ),
        rpc=_rpc_policy("BASE_SEPOLIA_RPC_URL", _BASE_SEPOLIA_OPERATIONS),
        repository=RepositoryPolicy(
            None, None, PathState.ABSENT, None, PathState.ABSENT
        ),
        fork=ForkPolicy(True, True, True, True),
        verifier=VerifierPolicy(
            VerifierProvider.ETHERSCAN_V2,
            "etherscan_v2",
            "ETHERSCAN_API_KEY",
            _UNSUPPORTED,
        ),
        operations=_BASE_SEPOLIA_OPERATIONS,
    ),
    NetworkProfile(
        identity=NetworkIdentity(
            "robinhood-mainnet", 4663, ProfileEnvironment.MAINNET
        ),
        rpc=_rpc_policy(
            "ROBINHOOD_MAINNET_RPC_URL", _ROBINHOOD_OPERATIONS
        ),
        repository=RepositoryPolicy(
            # Its own migration directory, like base-mainnet. While this shared
            # migrations/robinhood with the testnet profile, two invariants were
            # mutually exclusive: a named blueprint requires EXISTING, and a
            # SHARED source requires PROPOSED -- so a Robinhood migration could
            # never both name its blueprint and be executable.
            "robinhood",
            PurePosixPath("migrations/robinhood-mainnet"),
            PathState.EXISTING,
            PurePosixPath("migration_history/robinhood-mainnet/v1"),
            PathState.EXISTING,
        ),
        fork=ForkPolicy(True, True, True, True),
        # The Ledger is the approved deployer; env-private-key stays for the
        # deterministic fixtures. No Safe: the Safe RECEIVES governance at the
        # 0900 handoff, it does not sign the deployment.
        live_account_backend_ids=("env-private-key", "ledger"),
        verifier=VerifierPolicy(
            VerifierProvider.BLOCKSCOUT,
            "blockscout",
            None,
            _BLOCKED,
        ),
        operations=_ROBINHOOD_OPERATIONS,
    ),
    NetworkProfile(
        identity=NetworkIdentity(
            "robinhood-testnet", 46630, ProfileEnvironment.TEST
        ),
        rpc=_rpc_policy(
            "ROBINHOOD_TESTNET_RPC_URL", _ROBINHOOD_OPERATIONS
        ),
        repository=RepositoryPolicy(
            # The testnet profile keeps the declarative source; only mainnet
            # moved to its own imperative directory. Nothing shares a source
            # now, so the PROPOSED-for-shared rule no longer applies to either.
            None,
            PurePosixPath("migrations/robinhood"),
            PathState.PROPOSED,
            PurePosixPath("migration_history/robinhood-testnet/v1"),
            PathState.PROPOSED,
        ),
        fork=ForkPolicy(True, True, True, True),
        # The Ledger is the approved deployer; env-private-key stays for the
        # deterministic fixtures. No Safe: the Safe RECEIVES governance at the
        # 0900 handoff, it does not sign the deployment.
        live_account_backend_ids=("env-private-key", "ledger"),
        verifier=VerifierPolicy(
            VerifierProvider.BLOCKSCOUT,
            "blockscout",
            None,
            _BLOCKED,
        ),
        operations=_ROBINHOOD_OPERATIONS,
    ),
)

PROFILE_ALIASES: tuple[ProfileAlias, ...] = ()
NETWORK_PROFILE_IDS: tuple[str, ...] = tuple(
    profile.identity.profile_id for profile in NETWORK_PROFILES
)


def canonical_profile_ids() -> tuple[str, ...]:
    return NETWORK_PROFILE_IDS


def get_profile(value: str) -> NetworkProfile:
    if not isinstance(value, str):
        raise NetworkProfileError("H02_PROFILE_INVALID")
    normalized = value.casefold()
    for profile in NETWORK_PROFILES:
        if profile.identity.profile_id == normalized:
            return profile
    for alias in PROFILE_ALIASES:
        if alias.alias == normalized:
            return get_profile(alias.canonical_profile_id)
    raise NetworkProfileError("H02_PROFILE_UNKNOWN", profile_id=normalized)


def validate_registry(
    profiles: tuple[NetworkProfile, ...] = NETWORK_PROFILES,
    aliases: tuple[ProfileAlias, ...] = PROFILE_ALIASES,
) -> None:
    if not isinstance(profiles, tuple) or not profiles:
        raise NetworkProfileError("H02_PROFILE_INVALID")
    if not isinstance(aliases, tuple):
        raise NetworkProfileError("H02_PROFILE_INVALID")

    profile_ids: set[str] = set()
    chain_ids: set[int] = set()
    history_owners: dict[PurePosixPath, str] = {}
    source_owners: dict[PurePosixPath, list[NetworkProfile]] = {}

    for profile in profiles:
        if not isinstance(profile, NetworkProfile):
            raise NetworkProfileError("H02_PROFILE_INVALID")
        if (
            not isinstance(profile.identity, NetworkIdentity)
            or not isinstance(profile.rpc, RpcPolicy)
            or not isinstance(profile.repository, RepositoryPolicy)
            or not isinstance(profile.fork, ForkPolicy)
            or not isinstance(profile.verifier, VerifierPolicy)
            or not isinstance(profile.operations, tuple)
        ):
            raise NetworkProfileError("H02_PROFILE_INVALID")
        identity = profile.identity
        profile_id = identity.profile_id
        if not isinstance(identity.environment, ProfileEnvironment):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if not isinstance(profile_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,63}", profile_id
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile_id in profile_ids:
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        profile_ids.add(profile_id)

        if profile_id == "local":
            if (
                identity.chain_id is not None
                or identity.environment is not ProfileEnvironment.LOCAL
            ):
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )
        elif (
            not isinstance(identity.chain_id, int)
            or isinstance(identity.chain_id, bool)
            or identity.chain_id <= 0
            or identity.chain_id in chain_ids
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        else:
            chain_ids.add(identity.chain_id)

        if any(
            not isinstance(policy, OperationPolicy)
            for policy in profile.operations
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        operation_map = {
            policy.operation: policy for policy in profile.operations
        }
        if (
            len(operation_map) != len(Operation)
            or set(operation_map) != set(Operation)
            or len(profile.operations) != len(Operation)
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        for policy in profile.operations:
            if (
                not isinstance(policy.operation, Operation)
                or not isinstance(policy.outcome, OperationOutcome)
                or policy.outcome is OperationOutcome.INVALID
                or any(
                    not isinstance(flag, bool)
                    for flag in (
                        policy.requires_rpc,
                        policy.requires_identity,
                        policy.requires_repository,
                        policy.requires_account,
                        policy.requires_verifier,
                    )
                )
            ):
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )

        if (
            not isinstance(profile.rpc.allowed_operations, frozenset)
            or not isinstance(profile.rpc.require_chain_id_match, bool)
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        expected_rpc_operations = frozenset(
            policy.operation
            for policy in profile.operations
            if policy.requires_rpc
        )
        if expected_rpc_operations != profile.rpc.allowed_operations:
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile.rpc.env_name is None:
            if profile.rpc.allowed_operations:
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )
        elif not isinstance(profile.rpc.env_name, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_]*_RPC_URL", profile.rpc.env_name
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile.rpc.require_chain_id_match != (
            profile.rpc.env_name is not None
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )

        repository = profile.repository
        if repository.blueprint_id is not None and (
            not isinstance(repository.blueprint_id, str)
            or not re.fullmatch(
                r"[a-z0-9][a-z0-9_-]{0,63}",
                repository.blueprint_id,
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        for path, state in (
            (repository.migration_dir, repository.migration_state),
            (repository.history_dir, repository.history_state),
        ):
            if not isinstance(state, PathState):
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )
            if (state is PathState.ABSENT) != (path is None):
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )
            if path is not None and (
                not isinstance(path, PurePosixPath)
                or path.is_absolute()
                or ".." in path.parts
            ):
                raise NetworkProfileError(
                    "H02_PROFILE_INVALID", profile_id=profile_id
                )
        if (
            repository.blueprint_id is not None
            and repository.migration_state is not PathState.EXISTING
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )

        if repository.history_dir is not None:
            if repository.history_dir in history_owners:
                raise NetworkProfileError(
                    "H02_HISTORY_ALIAS", profile_id=profile_id
                )
            history_owners[repository.history_dir] = profile_id
        if repository.migration_dir is not None:
            source_owners.setdefault(repository.migration_dir, []).append(
                profile
            )

        if any(
            not isinstance(flag, bool)
            for flag in (
                profile.fork.require_source_chain_id_match,
                profile.fork.pin_required_for_evidence,
                profile.fork.latest_allowed_for_exploration,
                profile.fork.dirty_allowed_for_exploration,
                profile.fork.allow_submission,
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile.fork.allow_submission:
            raise NetworkProfileError(
                "H02_FORK_SUBMISSION_FORBIDDEN", profile_id=profile_id
            )
        if (
            not isinstance(profile.verifier.provider, VerifierProvider)
            or not isinstance(
                profile.verifier.operation_outcome, OperationOutcome
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile.verifier.adapter_id is not None and (
            not isinstance(profile.verifier.adapter_id, str)
            or not re.fullmatch(
                r"[a-z0-9][a-z0-9_]{0,63}",
                profile.verifier.adapter_id,
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if profile.verifier.api_key_env_name is not None and (
            not isinstance(profile.verifier.api_key_env_name, str)
            or not re.fullmatch(
                r"[A-Z][A-Z0-9_]*_API_KEY",
                profile.verifier.api_key_env_name,
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if (
            not profile.live_account_backend_ids
            and operation_map[Operation.MIGRATION_LIVE].outcome
            is OperationOutcome.SUPPORTED
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if (
            not isinstance(profile.live_account_backend_ids, tuple)
            or any(
                not isinstance(backend_id, str) or not backend_id
                for backend_id in profile.live_account_backend_ids
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if (
            operation_map[Operation.VERIFICATION].outcome
            is not profile.verifier.operation_outcome
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )
        if (
            profile.verifier.provider is VerifierProvider.UNSUPPORTED
            and (
                profile.verifier.adapter_id is not None
                or profile.verifier.api_key_env_name is not None
            )
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=profile_id
            )

    for source, owners in source_owners.items():
        if len(owners) < 2:
            continue
        owner_ids = {owner.identity.profile_id for owner in owners}
        if owner_ids != {"robinhood-mainnet", "robinhood-testnet"} or any(
            owner.repository.migration_state is not PathState.PROPOSED
            for owner in owners
        ):
            raise NetworkProfileError("H02_PROFILE_INVALID")

    alias_names: set[str] = set()
    for alias in aliases:
        if not isinstance(alias, ProfileAlias):
            raise NetworkProfileError("H02_PROFILE_INVALID")
        if (
            not isinstance(alias.alias, str)
            or not isinstance(alias.canonical_profile_id, str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", alias.alias)
            or alias.alias in profile_ids
            or alias.alias in alias_names
            or alias.canonical_profile_id not in profile_ids
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID", profile_id=alias.alias
            )
        alias_names.add(alias.alias)


def operation_decision(
    profile: NetworkProfile,
    operation: Operation,
) -> OperationPolicy:
    if not isinstance(operation, Operation):
        raise NetworkProfileError(
            "H02_OPERATION_INVALID", profile_id=profile.identity.profile_id
        )
    for policy in profile.operations:
        if policy.operation is operation:
            return policy
    raise NetworkProfileError(
        "H02_OPERATION_INVALID",
        profile_id=profile.identity.profile_id,
        operation=operation,
    )


def require_operation(
    profile: NetworkProfile,
    operation: Operation,
) -> OperationPolicy:
    policy = operation_decision(profile, operation)
    if policy.outcome is OperationOutcome.SUPPORTED:
        return policy
    code = {
        OperationOutcome.UNSUPPORTED: "H02_OPERATION_UNSUPPORTED",
        OperationOutcome.BLOCKED_PENDING_POLICY: "H02_OPERATION_BLOCKED",
        OperationOutcome.INVALID: "H02_OPERATION_INVALID",
    }[policy.outcome]
    raise NetworkProfileError(
        code,
        profile_id=profile.identity.profile_id,
        operation=operation,
    )


def _validate_rpc_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https", "ws", "wss"} and bool(
            parsed.netloc
        )
    except (TypeError, ValueError):
        return False


def resolve_rpc_reference(
    profile: NetworkProfile,
    operation: Operation,
    environ: Mapping[str, str],
    explicit_rpc: str | None = None,
) -> RedactedRpc:
    policy = require_operation(profile, operation)
    if not policy.requires_rpc:
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )

    if explicit_rpc is not None:
        value = explicit_rpc
        reference = "--rpc"
    else:
        env_name = profile.rpc.env_name
        if env_name is None:
            raise NetworkProfileError(
                "H02_RPC_ENV_MISSING",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        try:
            value = environ[env_name]
        except KeyError:
            raise NetworkProfileError(
                "H02_RPC_ENV_MISSING",
                profile_id=profile.identity.profile_id,
                operation=operation,
                env_name=env_name,
            ) from None
        reference = env_name

    if not value or not _validate_rpc_url(value):
        raise NetworkProfileError(
            "H02_RPC_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
            env_name=reference,
        )
    return RedactedRpc(value, profile.identity.profile_id, operation, reference)


def _normalize_chain_id(value: int | str) -> int:
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, int):
        chain_id = value
    elif isinstance(value, str):
        chain_id = int(value, 0)
    else:
        raise ValueError
    if chain_id <= 0:
        raise ValueError
    return chain_id


def verify_chain_identity(
    profile: NetworkProfile,
    operation: Operation,
    rpc: RedactedRpc | None,
    chain_id_reader: Callable[[str], int | str],
    *,
    local_chain_id: int | None = None,
) -> VerifiedNetworkIdentity:
    policy = require_operation(profile, operation)
    if not policy.requires_identity:
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )

    if profile.identity.chain_id is None:
        if local_chain_id is None:
            raise NetworkProfileError(
                "H02_LOCAL_CHAIN_ID_REQUIRED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        try:
            observed_chain_id = _normalize_chain_id(local_chain_id)
        except (TypeError, ValueError):
            raise NetworkProfileError(
                "H02_CHAIN_ID_INVALID",
                profile_id=profile.identity.profile_id,
                operation=operation,
            ) from None
        return VerifiedNetworkIdentity(
            profile.identity.profile_id,
            operation,
            observed_chain_id,
            observed_chain_id,
        )

    if rpc is None or (
        rpc.profile_id != profile.identity.profile_id
        or rpc.operation is not operation
    ):
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    try:
        observed_value = chain_id_reader(rpc.value)
    except Exception:
        raise NetworkProfileError(
            "H02_RPC_CONNECT_FAILED",
            profile_id=profile.identity.profile_id,
            operation=operation,
            expected_chain_id=profile.identity.chain_id,
            env_name=rpc.reference,
        ) from None
    try:
        observed_chain_id = _normalize_chain_id(observed_value)
    except (TypeError, ValueError):
        raise NetworkProfileError(
            "H02_CHAIN_ID_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
            expected_chain_id=profile.identity.chain_id,
        ) from None

    if observed_chain_id != profile.identity.chain_id:
        raise NetworkProfileError(
            "H02_CHAIN_ID_MISMATCH",
            profile_id=profile.identity.profile_id,
            operation=operation,
            expected_chain_id=profile.identity.chain_id,
            observed_chain_id=observed_chain_id,
        )
    return VerifiedNetworkIdentity(
        profile.identity.profile_id,
        operation,
        profile.identity.chain_id,
        observed_chain_id,
    )


def validate_fork_request(
    profile: NetworkProfile,
    operation: Operation,
    *,
    evidence_mode: bool,
    block_number: int | None,
    allow_dirty: bool,
    submission_requested: bool = False,
) -> None:
    require_operation(profile, operation)
    if submission_requested or profile.fork.allow_submission:
        raise NetworkProfileError(
            "H02_FORK_SUBMISSION_FORBIDDEN",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if evidence_mode:
        if (
            profile.fork.pin_required_for_evidence
            and (block_number is None or block_number <= 0)
        ):
            raise NetworkProfileError(
                "H02_FORK_PIN_REQUIRED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        if allow_dirty:
            raise NetworkProfileError(
                "H02_DIRTY_EVIDENCE_FORBIDDEN",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
    else:
        if (
            block_number is None
            and not profile.fork.latest_allowed_for_exploration
        ):
            raise NetworkProfileError(
                "H02_FORK_PIN_REQUIRED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        if allow_dirty and not profile.fork.dirty_allowed_for_exploration:
            raise NetworkProfileError(
                "H02_OPERATION_INVALID",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )


def validate_verified_identity(
    profile: NetworkProfile,
    operation: Operation,
    identity: VerifiedNetworkIdentity | None,
    *,
    require_account: bool = False,
) -> OperationPolicy:
    policy = require_operation(profile, operation)
    if not policy.requires_identity:
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if require_account and not policy.requires_account:
        raise NetworkProfileError(
            "H02_ACCOUNT_BACKEND_UNAPPROVED",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if not isinstance(identity, VerifiedNetworkIdentity) or (
        identity.profile_id != profile.identity.profile_id
        or identity.operation is not operation
        or identity.expected_chain_id != identity.observed_chain_id
        or (
            profile.identity.chain_id is not None
            and identity.expected_chain_id != profile.identity.chain_id
        )
    ):
        raise NetworkProfileError(
            "H02_CHAIN_ID_MISMATCH",
            profile_id=profile.identity.profile_id,
            operation=operation,
            expected_chain_id=profile.identity.chain_id,
        )
    return policy


def repository_paths(
    profile: NetworkProfile,
    operation: Operation,
    *,
    root: Path,
    identity: VerifiedNetworkIdentity | None,
) -> ResolvedRepositoryPaths:
    policy = require_operation(profile, operation)
    if not policy.requires_repository:
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if policy.requires_identity:
        validate_verified_identity(profile, operation, identity)

    repository = profile.repository
    if (
        repository.migration_state is PathState.PROPOSED
        or repository.history_state is PathState.PROPOSED
    ):
        raise NetworkProfileError(
            "H02_OPERATION_BLOCKED",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if (
        repository.migration_state is not PathState.EXISTING
        or repository.history_state is not PathState.EXISTING
        or repository.migration_dir is None
        or repository.history_dir is None
    ):
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )

    migration_dir = root / repository.migration_dir
    history_dir = root / repository.history_dir
    if not migration_dir.is_dir() or not history_dir.is_dir():
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    return ResolvedRepositoryPaths(
        profile.identity.profile_id, migration_dir, history_dir
    )


def validate_manifest_assertions(
    profile: NetworkProfile,
    manifest_name: str,
    *,
    operation: Operation,
    environment: str | None = None,
) -> None:
    operation_decision(profile, operation)
    if (
        environment is not None
        and (
            profile.repository.history_dir is None
            or environment != profile.repository.history_dir.name
        )
    ):
        raise NetworkProfileError(
            "H02_HISTORY_ALIAS",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if not isinstance(manifest_name, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", manifest_name
    ):
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )


def static_manifest_path(
    profile: NetworkProfile,
    manifest_name: str,
    *,
    operation: Operation,
    environment: str | None = None,
) -> PurePosixPath:
    require_operation(profile, operation)
    validate_manifest_assertions(
        profile,
        manifest_name,
        operation=operation,
        environment=environment,
    )
    repository = profile.repository
    if repository.history_state is PathState.PROPOSED:
        raise NetworkProfileError(
            "H02_OPERATION_BLOCKED",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    if (
        repository.history_state is not PathState.EXISTING
        or repository.history_dir is None
    ):
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )
    return repository.history_dir / f"{manifest_name}-manifest.json"


def manifest_path(
    profile: NetworkProfile,
    manifest_name: str,
    *,
    root: Path,
    identity: VerifiedNetworkIdentity,
    operation: Operation = Operation.REPOSITORY_READ,
) -> Path:
    relative_path = static_manifest_path(
        profile, manifest_name, operation=operation
    )
    paths = repository_paths(
        profile, operation, root=root, identity=identity
    )
    return paths.history_dir / relative_path.name


validate_registry()
