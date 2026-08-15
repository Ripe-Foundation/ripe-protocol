import hashlib
import json
from pathlib import Path
import re
import time
from dataclasses import dataclass


# Chainlink CCIP infrastructure, per chain.
#
# The mainnet entries were derived on chain, not from a directory: the router
# and RMN proxy were read off the BurnMintTokenPools already deployed on each
# chain (13 of 15 agree on Base, 7 of 8 on Robinhood -- the outliers are pools
# still pointing at a superseded router), the chain selector off an OffRamp's
# static config, and every address was then confirmed by its typeAndVersion().
# LINK is omitted rather than guessed: nothing in these migrations reads it,
# and both explorers list several name-squatting "ChainLink Token" entries.
#
# Every value below was read straight off the chain it belongs to (router / rmn proxy
# from the `BurnMintTokenPool 1.5.1` pools deployed via the CCIP token manager UI, token
# admin registry from the OnRamp static config, registry module from the
# `RegistryModuleAdded` event on the token admin registry).

CCIP = {
    "base-mainnet": {
        "CHAIN_SELECTOR": 15971525489660198786,
        "ROUTER": "0x881e3A65B4d4a04dD529061dd0071cf975F58bCD",
        "RMN_PROXY": "0xC842c69d54F83170C42C4d556B4F6B2ca53Dd3E8",
        "TOKEN_ADMIN_REGISTRY": "0x6f6C373d09C07425BaAE72317863d7F6bb731e37",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x1A5f2d0c090dDB7ee437051DA5e6f03b6bAE1A77",
        # No pool to retire: nothing CCIP-shaped is registered in RipeHq here.
        "PREVIOUS_RIPE_POOL": None,
        "REMOTE_CHAINS": ["robinhood-mainnet"],
    },
    "robinhood-mainnet": {
        "CHAIN_SELECTOR": 6180753054346818345,
        "ROUTER": "0x06fC836cf9839B1cd891C440A0a45242DA6Ae1c9",
        "RMN_PROXY": "0xe8464c353210Cc398A45dB2454FBc5BCd25fFf20",
        "TOKEN_ADMIN_REGISTRY": "0x1912C3cFafE8A76A32a92861d815aC2837F237Ca",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x3237c0D7B58BEc8Dc17F00103B784Bd6678f789E",
        "PREVIOUS_RIPE_POOL": None,
        "REMOTE_CHAINS": ["base-mainnet"],
    },
    "base-sepolia": {
        "CHAIN_SELECTOR": 10344971235874465080,
        "ROUTER": "0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93",
        "RMN_PROXY": "0x99360767a4705f68CcCb9533195B761648d6d807",
        "TOKEN_ADMIN_REGISTRY": "0x736D0bBb318c1B27Ff686cd19804094E66250e17",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x176ae8C6C11DD2c031B924CE1A0A43188035f3f6",
        # fee tokens the FeeQuoter accepts, besides the native coin
        "LINK": "0xE4aB69C077896252FAFBD49EFD26B5D171A32410",
        # the stock chainlink pool the ripe pool replaces (no `canMintRipe()`)
        "PREVIOUS_RIPE_POOL": "0x4DFd9eBB670F22b0cf53A53088E38636855CC600",
        "REMOTE_CHAINS": ["robinhood-testnet"],
    },
    "robinhood-testnet": {
        "CHAIN_SELECTOR": 2032988798112970440,
        "ROUTER": "0x30D197C6F5bE050D5525dD94d01760FaCdB67e7C",
        "RMN_PROXY": "0x934c1B8f6913070528CC24081E0b78d57D3A97A3",
        "TOKEN_ADMIN_REGISTRY": "0xad4c7a1430D140Fc5121C0697B2f7Efc655c0070",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x00094197A82faDE614C214CFE27719dEDa898686",
        "LINK": "0xD610B8f58689de7755947C05342A2DFaC30ebD57",
        "PREVIOUS_RIPE_POOL": "0x8BcA5FC8933e19aa99cf95E0BaDE1aAB5309Be3d",
        "REMOTE_CHAINS": ["base-sepolia"],
    },
}


# Exact RipeHq registry topology confirmed on both live chains. These values
# are duplicated in Vyper and parameter tooling because those consumers cannot
# import this Python module; offline topology tests bind every copy together.
CCIP_POOL_HQ_IDS = {
    "RIPE": 23,
    "GREEN": 24,
}

CCIP_LIVE_POOL_CAPABILITIES = {
    "RIPE": {"canMintGreen": False, "canMintRipe": True},
    "GREEN": {"canMintGreen": True, "canMintRipe": False},
}


# Current live rate-limit state, represented as
# `RateLimiter.Config(isEnabled, capacity, rate)`. This is evidence of the
# deployed configuration, not an endorsement of unlimited operation. The
# owner must explicitly choose (or explicitly accept) a production policy for
# each token and direction before operational readiness can be claimed.
NO_RATE_LIMIT = (False, 0, 0)
CURRENT_RATE_LIMIT_ADMIN = "0x0000000000000000000000000000000000000000"


_ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MAX_UINT128 = 2**128 - 1
_MAX_RECEIVER_PROOF_LIFETIME = 7 * 24 * 60 * 60
_MAX_HQ_APPEND_WINDOW_LIFETIME = 7 * 24 * 60 * 60


def _require_address(value, field, *, allow_zero=True):
    if not isinstance(value, str) or not _ADDRESS_RE.fullmatch(value):
        raise ValueError(f"{field} must be a 20-byte EVM address")
    if not allow_zero and int(value, 16) == 0:
        raise ValueError(f"{field} must not be the zero address")


@dataclass(frozen=True)
class CcipRateLimitPolicy:
    """An owner-selected Chainlink `RateLimiter.Config`."""

    is_enabled: bool
    capacity: int
    rate: int

    def __post_init__(self):
        if type(self.is_enabled) is not bool:
            raise ValueError("is_enabled must be bool")
        for field, value in (("capacity", self.capacity), ("rate", self.rate)):
            if type(value) is not int or not 0 <= value <= _MAX_UINT128:
                raise ValueError(f"{field} must be a uint128")
        if self.is_enabled:
            if self.capacity == 0 or self.rate == 0 or self.rate >= self.capacity:
                raise ValueError("enabled rate limits require 0 < rate < capacity")
        elif self.capacity != 0 or self.rate != 0:
            raise ValueError(
                "disabled rate limits must use zero capacity and zero rate"
            )

    def as_tuple(self):
        return (self.is_enabled, self.capacity, self.rate)


@dataclass(frozen=True)
class CcipLanePolicy:
    """Owner choice bound to one local chain, peer, token, and both directions."""

    local_chain: str
    remote_chain: str
    token: str
    outbound: CcipRateLimitPolicy
    inbound: CcipRateLimitPolicy
    rate_limit_admin: str

    def __post_init__(self):
        if self.local_chain not in CCIP:
            raise ValueError(f"unknown local CCIP chain {self.local_chain!r}")
        if self.remote_chain not in CCIP[self.local_chain]["REMOTE_CHAINS"]:
            raise ValueError(
                f"{self.remote_chain!r} is not a configured peer for "
                f"{self.local_chain!r}"
            )
        if self.token not in CCIP_LIVE_POOL_CAPABILITIES:
            raise ValueError(f"unknown CCIP token label {self.token!r}")
        if type(self.outbound) is not CcipRateLimitPolicy:
            raise ValueError("outbound must be a CcipRateLimitPolicy")
        if type(self.inbound) is not CcipRateLimitPolicy:
            raise ValueError("inbound must be a CcipRateLimitPolicy")
        _require_address(self.rate_limit_admin, "rate_limit_admin")

    @property
    def binding(self):
        return (self.local_chain, self.remote_chain, self.token)


# Deliberately unresolved owner choices. Each entry binds the local pool, its
# peer, the token, independent inbound/outbound limits, and the pool-wide rate
# limit administrator. Current deployed values are evidence only and cannot be
# promoted into an owner decision merely by setting a truthy acknowledgement.
CCIP_REQUIRED_POLICY_BINDINGS = (
    ("base-mainnet", "robinhood-mainnet", "RIPE"),
    ("base-mainnet", "robinhood-mainnet", "GREEN"),
    ("robinhood-mainnet", "base-mainnet", "RIPE"),
    ("robinhood-mainnet", "base-mainnet", "GREEN"),
    ("base-sepolia", "robinhood-testnet", "RIPE"),
    ("robinhood-testnet", "base-sepolia", "RIPE"),
)
CCIP_OWNER_DISPOSITION_GATES = {
    binding: None for binding in CCIP_REQUIRED_POLICY_BINDINGS
}


@dataclass(frozen=True)
class CcipHqAppendWindow:
    """Governance coordination required to preserve append-only HQ ids."""

    chain: str
    assignments: tuple
    coordination_reference: str
    exclusive_governance_window: bool
    plan_sha256: str
    starts_at: int
    expires_at: int

    def __post_init__(self):
        if self.chain not in ("base-mainnet", "robinhood-mainnet"):
            raise ValueError("HQ append windows are only defined for live chains")
        if not isinstance(self.assignments, tuple):
            raise ValueError("assignments must be an ordered tuple")
        if (
            not isinstance(self.coordination_reference, str)
            or not self.coordination_reference.strip()
        ):
            raise ValueError("coordination_reference must identify the approved window")
        if self.exclusive_governance_window is not True:
            raise ValueError("the HQ append window must be exclusive")
        if not isinstance(self.plan_sha256, str) or not _SHA256_RE.fullmatch(
            self.plan_sha256
        ):
            raise ValueError("plan_sha256 must be a lowercase SHA-256 digest")
        if type(self.starts_at) is not int or self.starts_at <= 0:
            raise ValueError("starts_at must be a positive Unix timestamp")
        if type(self.expires_at) is not int or self.expires_at <= self.starts_at:
            raise ValueError("expires_at must be later than starts_at")
        if self.expires_at - self.starts_at > _MAX_HQ_APPEND_WINDOW_LIFETIME:
            raise ValueError("HQ append window lifetime must not exceed 7 days")


# `confirmNewAddressToRegistry(address)` does not accept an expected id. If a
# pool is ever absent, the static Safe plan must therefore stop until governance
# explicitly reserves an exclusive append window covering exactly ids 23/24.
CCIP_HQ_APPEND_WINDOW_GATES = {
    "base-mainnet": None,
    "robinhood-mainnet": None,
}

CCIP_REQUIRED_EVIDENCE_NAMES = (
    "AUTOMATIC_EXECUTION_DESTINATION_GAS",
    "LIVE_POOL_SOURCE_COMPILER_CONSTRUCTOR_IDENTITY",
    "HISTORICAL_TRANSACTION_PROVENANCE",
    "SOURCE_LICENSE_LEGAL_CONCLUSIONS",
)


@dataclass(frozen=True)
class CcipEvidenceRecord:
    """Reviewed evidence bound to one exact local pool and peer direction."""

    gate_name: str
    local_chain: str
    remote_chain: str
    token: str
    evidence_path: str
    evidence_sha256: str
    approved_at: int
    expires_at: int | None = None

    def __post_init__(self):
        if self.gate_name not in CCIP_REQUIRED_EVIDENCE_NAMES:
            raise ValueError(f"unknown CCIP evidence gate {self.gate_name!r}")
        if self.binding not in CCIP_REQUIRED_POLICY_BINDINGS:
            raise ValueError(f"unknown CCIP evidence binding {self.binding!r}")
        if not isinstance(self.evidence_path, str) or not self.evidence_path.strip():
            raise ValueError("evidence_path must identify the reviewed artifact")
        if not isinstance(self.evidence_sha256, str) or not _SHA256_RE.fullmatch(
            self.evidence_sha256
        ):
            raise ValueError("evidence_sha256 must be a lowercase SHA-256 digest")
        if type(self.approved_at) is not int or self.approved_at <= 0:
            raise ValueError("approved_at must be a positive Unix timestamp")
        if self.expires_at is not None and (
            type(self.expires_at) is not int or self.expires_at <= self.approved_at
        ):
            raise ValueError("expires_at must be later than approved_at")
        if (
            self.gate_name == "AUTOMATIC_EXECUTION_DESTINATION_GAS"
            and self.expires_at is None
        ):
            raise ValueError("destination-gas evidence must have an expiry")

    @property
    def binding(self):
        return (self.local_chain, self.remote_chain, self.token)

    @property
    def gate_key(self):
        return (*self.binding, self.gate_name)


# A single acknowledgement must never close evidence for every chain, token,
# and direction. Each required binding has four independently reviewed records.
CCIP_EVIDENCE_GATES = {
    (*binding, gate_name): None
    for binding in CCIP_REQUIRED_POLICY_BINDINGS
    for gate_name in CCIP_REQUIRED_EVIDENCE_NAMES
}

# A code-empty destination and an operator acknowledgement are useful fork
# preflight checks, but neither proves that the intended recipient controls the
# address. A future live-send backend must bind independent receiver-control
# evidence and clear this gate; fork tooling must never clear it implicitly.
CCIP_LIVE_SEND_EVIDENCE_GATES = {
    "DESTINATION_RECEIVER_CONTROL_PROOF": None,
}


@dataclass(frozen=True)
class CcipReceiverControlProof:
    """Independent receiver-control evidence bound to one exact live lane."""

    source_chain: str
    destination_chain: str
    receiver: str
    evidence_path: str
    evidence_sha256: str
    issued_at: int
    expires_at: int

    def __post_init__(self):
        if self.source_chain not in CCIP:
            raise ValueError(f"unknown source chain {self.source_chain!r}")
        if self.destination_chain not in CCIP[self.source_chain]["REMOTE_CHAINS"]:
            raise ValueError(
                f"{self.destination_chain!r} is not a configured peer for "
                f"{self.source_chain!r}"
            )
        _require_address(self.receiver, "receiver", allow_zero=False)
        if not isinstance(self.evidence_path, str) or not self.evidence_path.strip():
            raise ValueError("evidence_path must identify the receiver-control artifact")
        if not isinstance(self.evidence_sha256, str) or not _SHA256_RE.fullmatch(
            self.evidence_sha256
        ):
            raise ValueError("evidence_sha256 must be a lowercase SHA-256 digest")
        if type(self.issued_at) is not int or self.issued_at <= 0:
            raise ValueError("issued_at must be a positive Unix timestamp")
        if type(self.expires_at) is not int or self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be later than issued_at")
        if self.expires_at - self.issued_at > _MAX_RECEIVER_PROOF_LIFETIME:
            raise ValueError("receiver-control proof lifetime must not exceed 7 days")


def _policy_binding(local_chain, remote_chain, token):
    binding = (local_chain, remote_chain, token)
    if binding not in CCIP_OWNER_DISPOSITION_GATES:
        raise RuntimeError(f"CCIP_OWNER_DISPOSITION_UNKNOWN_BINDING: {binding!r}")
    return binding


def _validated_lane_policy(binding, value):
    if type(value) is not CcipLanePolicy:
        raise RuntimeError(
            f"CCIP_OWNER_DISPOSITION_INVALID: {binding!r} must contain a CcipLanePolicy"
        )
    if value.binding != binding:
        raise RuntimeError(
            "CCIP_OWNER_DISPOSITION_BINDING_MISMATCH: "
            f"gate {binding!r}, policy {value.binding!r}"
        )
    return value


def require_ccip_owner_disposition(local_chain, remote_chain, token):
    """Return the exact typed owner policy or block a new CCIP mutation."""
    binding = _policy_binding(local_chain, remote_chain, token)
    value = CCIP_OWNER_DISPOSITION_GATES[binding]
    if value is None:
        raise RuntimeError(f"CCIP_OWNER_DISPOSITION_REQUIRED: {binding!r}")
    return _validated_lane_policy(binding, value)


def ccip_revalidation_policy(local_chain, remote_chain, token):
    """Use a selected policy when present, otherwise the observed live baseline."""
    binding = _policy_binding(local_chain, remote_chain, token)
    value = CCIP_OWNER_DISPOSITION_GATES[binding]
    if value is not None:
        return _validated_lane_policy(binding, value)
    no_limit = CcipRateLimitPolicy(False, 0, 0)
    return CcipLanePolicy(
        local_chain,
        remote_chain,
        token,
        outbound=no_limit,
        inbound=no_limit,
        rate_limit_admin=CURRENT_RATE_LIMIT_ADMIN,
    )


def _read_evidence(path, *, error_prefix):
    evidence_path = Path(path)
    try:
        payload = evidence_path.read_bytes()
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"{error_prefix}_UNREADABLE: {path}") from exc
    try:
        evidence = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{error_prefix}_INVALID_JSON: {path}") from exc
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 1:
        raise RuntimeError(f"{error_prefix}_INVALID_SCHEMA: {path}")
    return payload, evidence


def _validated_scoped_evidence(key, value, *, now):
    if type(value) is not CcipEvidenceRecord:
        raise RuntimeError(
            f"CCIP_EVIDENCE_INVALID: {key!r} must contain a CcipEvidenceRecord"
        )
    if value.gate_key != key:
        raise RuntimeError(
            f"CCIP_EVIDENCE_BINDING_MISMATCH: expected {key!r}, "
            f"record binds {value.gate_key!r}"
        )
    payload, evidence = _read_evidence(
        value.evidence_path, error_prefix="CCIP_EVIDENCE"
    )
    if hashlib.sha256(payload).hexdigest() != value.evidence_sha256:
        raise RuntimeError(f"CCIP_EVIDENCE_DIGEST_MISMATCH: {key!r}")
    expected_fields = {
        "gate_name": value.gate_name,
        "local_chain": value.local_chain,
        "remote_chain": value.remote_chain,
        "token": value.token,
        "approved_at": value.approved_at,
        "expires_at": value.expires_at,
    }
    if any(evidence.get(field) != expected for field, expected in expected_fields.items()):
        raise RuntimeError(f"CCIP_EVIDENCE_ARTIFACT_BINDING_MISMATCH: {key!r}")
    if now < value.approved_at or (
        value.expires_at is not None and now >= value.expires_at
    ):
        raise RuntimeError(f"CCIP_EVIDENCE_STALE: {key!r}")
    return value


def require_ccip_wiring_gates(local_chain, remote_chain, token, *, now=None):
    """Block a new lane until its typed owner choice and evidence are bound."""
    policy = require_ccip_owner_disposition(local_chain, remote_chain, token)
    binding = (local_chain, remote_chain, token)
    unresolved = [
        name
        for name in CCIP_REQUIRED_EVIDENCE_NAMES
        if CCIP_EVIDENCE_GATES[(*binding, name)] is None
    ]
    if unresolved:
        raise RuntimeError("CCIP_EVIDENCE_REQUIRED: " + ", ".join(sorted(unresolved)))
    observed_at = int(time.time()) if now is None else now
    if type(observed_at) is not int:
        raise RuntimeError("CCIP_EVIDENCE_INVALID_TIME")
    for name in CCIP_REQUIRED_EVIDENCE_NAMES:
        key = (*binding, name)
        _validated_scoped_evidence(key, CCIP_EVIDENCE_GATES[key], now=observed_at)
    return policy


def require_ccip_hq_append_window(chain, *, expected_plan_sha256=None, now=None):
    """Require an explicit exclusive Safe/governance append commitment."""
    if chain not in CCIP_HQ_APPEND_WINDOW_GATES:
        raise RuntimeError(f"CCIP_HQ_APPEND_WINDOW_UNKNOWN_CHAIN: {chain!r}")
    window = CCIP_HQ_APPEND_WINDOW_GATES[chain]
    if window is None:
        raise RuntimeError(f"CCIP_HQ_APPEND_WINDOW_REQUIRED: {chain}")
    if type(window) is not CcipHqAppendWindow:
        raise RuntimeError(
            f"CCIP_HQ_APPEND_WINDOW_INVALID: {chain} must contain a CcipHqAppendWindow"
        )
    expected = tuple(CCIP_POOL_HQ_IDS.items())
    if window.chain != chain or window.assignments != expected:
        raise RuntimeError(
            f"CCIP_HQ_APPEND_WINDOW_BINDING_MISMATCH: expected {(chain, expected)!r}"
        )
    if expected_plan_sha256 is not None and window.plan_sha256 != expected_plan_sha256:
        raise RuntimeError(
            "CCIP_HQ_APPEND_WINDOW_PLAN_MISMATCH: "
            f"expected {expected_plan_sha256}, got {window.plan_sha256}"
        )
    observed_at = int(time.time()) if now is None else now
    if type(observed_at) is not int:
        raise RuntimeError("CCIP_HQ_APPEND_WINDOW_INVALID_TIME")
    if observed_at < window.starts_at or observed_at >= window.expires_at:
        raise RuntimeError(f"CCIP_HQ_APPEND_WINDOW_STALE: {chain}")
    return window


def require_ccip_live_send_evidence(
    source_chain, destination_chain, receiver, *, now=None
):
    """Require fresh receiver evidence bound to this exact destination."""
    proof = CCIP_LIVE_SEND_EVIDENCE_GATES["DESTINATION_RECEIVER_CONTROL_PROOF"]
    if proof is None:
        raise RuntimeError(
            "CCIP_LIVE_SEND_EVIDENCE_REQUIRED: DESTINATION_RECEIVER_CONTROL_PROOF"
        )
    if type(proof) is not CcipReceiverControlProof:
        raise RuntimeError(
            "CCIP_LIVE_SEND_EVIDENCE_INVALID: "
            "DESTINATION_RECEIVER_CONTROL_PROOF must contain a "
            "CcipReceiverControlProof"
        )
    expected = (source_chain, destination_chain, receiver.lower())
    actual = (
        proof.source_chain,
        proof.destination_chain,
        proof.receiver.lower(),
    )
    if actual != expected:
        raise RuntimeError(
            "CCIP_LIVE_SEND_EVIDENCE_BINDING_MISMATCH: "
            f"expected {expected!r}, proof binds {actual!r}"
        )
    payload, evidence = _read_evidence(
        proof.evidence_path, error_prefix="CCIP_LIVE_SEND_EVIDENCE"
    )
    if hashlib.sha256(payload).hexdigest() != proof.evidence_sha256:
        raise RuntimeError("CCIP_LIVE_SEND_EVIDENCE_DIGEST_MISMATCH")
    expected_fields = {
        "source_chain": proof.source_chain,
        "destination_chain": proof.destination_chain,
        "receiver": proof.receiver.lower(),
        "issued_at": proof.issued_at,
        "expires_at": proof.expires_at,
    }
    actual_fields = dict(evidence)
    if isinstance(actual_fields.get("receiver"), str):
        actual_fields["receiver"] = actual_fields["receiver"].lower()
    if any(actual_fields.get(field) != value for field, value in expected_fields.items()):
        raise RuntimeError("CCIP_LIVE_SEND_EVIDENCE_ARTIFACT_BINDING_MISMATCH")
    observed_at = int(time.time()) if now is None else now
    if type(observed_at) is not int:
        raise RuntimeError("CCIP_LIVE_SEND_EVIDENCE_INVALID_TIME")
    if observed_at < proof.issued_at or observed_at >= proof.expires_at:
        raise RuntimeError(
            "CCIP_LIVE_SEND_EVIDENCE_STALE: receiver-control proof is not current"
        )
    return proof
