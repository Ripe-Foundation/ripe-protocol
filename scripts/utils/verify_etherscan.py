"""Deterministic Etherscan-v2 verification adapter.

The adapter intentionally supports only chains that Etherscan documents as
supported. Robinhood identities are recorded here, but provider selection
fails closed until an official provider contract is implemented and tested.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

import requests


API_URL = "https://api.etherscan.io/v2/api"
DEFAULT_TIMEOUT_SECONDS = 15.0


class VerificationStatus(str, Enum):
    SUCCESS = "success"
    PENDING = "pending"
    UNVERIFIED = "unverified"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"


class KeyPolicy(str, Enum):
    REQUIRED = "required"
    KEYLESS = "keyless"


class VerifierConfigurationError(ValueError):
    """Raised before HTTP when provider or input policy is unsupported."""


@dataclass(frozen=True)
class ChainSpec:
    chain_id: int
    explorer_address_url: str | None
    provider: str | None


@dataclass(frozen=True)
class ProviderPolicy:
    name: str
    key_policy: KeyPolicy
    api_url: str


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    detail: str
    guid: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is VerificationStatus.SUCCESS


CHAIN_SPECS: Mapping[str, ChainSpec] = {
    "eth-mainnet": ChainSpec(1, "https://etherscan.io/address/", "etherscan"),
    "eth-goerli": ChainSpec(5, None, None),
    "eth-sepolia": ChainSpec(
        11155111, "https://sepolia.etherscan.io/address/", "etherscan"
    ),
    "base-mainnet": ChainSpec(
        8453, "https://basescan.org/address/", "etherscan"
    ),
    # Base Goerli and Base Sepolia are distinct networks. Goerli is retired.
    "base-goerli": ChainSpec(84531, None, None),
    "base-sepolia": ChainSpec(
        84532, "https://sepolia.basescan.org/address/", "etherscan"
    ),
    "robinhood-mainnet": ChainSpec(4663, None, None),
    "robinhood-testnet": ChainSpec(46630, None, None),
}

PROVIDER_POLICIES: Mapping[str, ProviderPolicy] = {
    "etherscan": ProviderPolicy(
        name="etherscan",
        key_policy=KeyPolicy.REQUIRED,
        api_url=API_URL,
    )
}

# Compatibility aliases for existing importers.
chain_ids = {name: spec.chain_id for name, spec in CHAIN_SPECS.items()}
contract_base_url = {
    name: spec.explorer_address_url
    for name, spec in CHAIN_SPECS.items()
    if spec.explorer_address_url is not None
}


def _chain_spec(chain: str) -> ChainSpec:
    try:
        return CHAIN_SPECS[chain]
    except KeyError as exc:
        raise VerifierConfigurationError(f"unsupported chain: {chain}") from exc


def _api_key_for_policy(
    policy: ProviderPolicy, api_key: str | None
) -> str:
    if policy.key_policy is KeyPolicy.REQUIRED:
        if not api_key or not api_key.strip():
            raise VerifierConfigurationError(
                f"{policy.name} provider requires an API key; "
                "keyless use is unsupported"
            )
        return api_key
    if policy.key_policy is KeyPolicy.KEYLESS:
        if api_key and api_key.strip():
            raise VerifierConfigurationError(
                f"{policy.name} provider is keyless and must not receive an API key"
            )
        return ""
    raise VerifierConfigurationError(
        f"unsupported key policy for provider: {policy.name}"
    )


def _response_text(payload: Mapping[str, Any]) -> str:
    return " ".join(
        str(payload.get(field, "")) for field in ("message", "result")
    ).strip()


def classify_payload(payload: Mapping[str, Any]) -> VerificationResult:
    detail = _response_text(payload)
    normalized = detail.lower()
    # Provider status is authoritative. A successful ABI or GUID can contain
    # arbitrary source text that happens to resemble an error phrase.
    if payload.get("status") == "1":
        return VerificationResult(VerificationStatus.SUCCESS, detail)
    if "rate limit" in normalized or "max rate" in normalized:
        return VerificationResult(VerificationStatus.RATE_LIMIT, detail)
    if "pending in queue" in normalized or normalized == "pending":
        return VerificationResult(VerificationStatus.PENDING, detail)
    if "not verified" in normalized or "unable to locate contractcode" in normalized:
        return VerificationResult(VerificationStatus.UNVERIFIED, detail)
    return VerificationResult(
        VerificationStatus.PROVIDER_ERROR,
        detail or "provider returned an unclassified response",
    )


class EtherscanVerifier:
    def __init__(
        self,
        *,
        chain: str,
        api_key: str | None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        session: Any = requests,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        spec = _chain_spec(chain)
        if spec.provider != "etherscan":
            raise VerifierConfigurationError(
                f"no supported official verifier provider for chain: {chain}"
            )
        policy = PROVIDER_POLICIES[spec.provider]
        normalized_api_key = _api_key_for_policy(policy, api_key)
        if timeout <= 0:
            raise VerifierConfigurationError("request timeout must be positive")

        self.chain = chain
        self.spec = spec
        self.policy = policy
        self.api_key = normalized_api_key
        self.timeout = timeout
        self.session = session
        self.sleep = sleep

    def _request(
        self,
        method: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any] | VerificationResult:
        try:
            response = self.session.request(
                method,
                self.policy.api_url,
                params=params,
                data=data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout as exc:
            return VerificationResult(VerificationStatus.TIMEOUT, str(exc))
        except (requests.RequestException, ValueError) as exc:
            return VerificationResult(VerificationStatus.PROVIDER_ERROR, str(exc))

        if not isinstance(payload, Mapping):
            return VerificationResult(
                VerificationStatus.PROVIDER_ERROR,
                "provider returned a non-object JSON response",
            )
        return payload

    def lookup(self, contract_address: str) -> VerificationResult:
        payload = self._request(
            "GET",
            params={
                "chainid": self.spec.chain_id,
                "apikey": self.api_key,
                "module": "contract",
                "action": "getabi",
                "address": contract_address,
            },
        )
        if isinstance(payload, VerificationResult):
            return payload
        return classify_payload(payload)

    def _validate_manifest(
        self,
        contract_name: str,
        manifest_data: Mapping[str, Any],
    ) -> tuple[str, Mapping[str, Any]]:
        language = str(manifest_data.get("language", "vyper")).lower()
        code_format = str(manifest_data.get("code_format", "vyper-json")).lower()
        if language != "vyper":
            raise VerifierConfigurationError(
                f"unsupported verification language: {language}"
            )
        if code_format != "vyper-json":
            raise VerifierConfigurationError(
                f"unsupported verification format: {code_format}"
            )
        if not contract_name:
            raise VerifierConfigurationError("contract name is required")

        standard_json = manifest_data.get("solc_json")
        if not isinstance(standard_json, Mapping):
            raise VerifierConfigurationError("manifest solc_json must be an object")
        sources = standard_json.get("sources")
        if not isinstance(sources, Mapping) or not sources:
            raise VerifierConfigurationError(
                "manifest solc_json.sources must be a nonempty object"
            )
        source_path = manifest_data.get("source_path")
        if source_path is None:
            source_path = sorted(str(path) for path in sources)[0]
        if source_path not in sources:
            raise VerifierConfigurationError(
                f"manifest source_path is not in solc_json.sources: {source_path}"
            )
        compiler_version = _compiler_version(manifest_data, standard_json)
        if (
            not isinstance(compiler_version, str)
            or not compiler_version.startswith("vyper:")
            or not compiler_version.removeprefix("vyper:")
        ):
            raise VerifierConfigurationError(
                "manifest compiler_version must be an explicit vyper:<version> string"
            )
        return str(source_path), standard_json

    def verify_manifest(
        self,
        contract_name: str,
        manifest_data: Mapping[str, Any],
        *,
        wait: bool = True,
        max_polls: int = 10,
        poll_interval: float = 5.0,
    ) -> VerificationResult:
        source_path, standard_json = self._validate_manifest(
            contract_name, manifest_data
        )
        address = str(manifest_data.get("address", ""))
        if not address:
            raise VerifierConfigurationError("manifest address is required")

        current = self.lookup(address)
        if current.status is VerificationStatus.SUCCESS:
            return current
        if current.status is not VerificationStatus.UNVERIFIED:
            return current

        payload = self._request(
            "POST",
            params={"chainid": self.spec.chain_id},
            data={
                "chainid": self.spec.chain_id,
                "apikey": self.api_key,
                "module": "contract",
                "action": "verifysourcecode",
                "sourceCode": json.dumps(
                    standard_json,
                    ensure_ascii=True,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "contractaddress": address,
                "codeformat": "vyper-json",
                "contractname": f"{source_path}:{contract_name}",
                "compilerversion": _compiler_version(
                    manifest_data, standard_json
                ),
                "constructorArguements": str(manifest_data.get("args", "")),
            },
        )
        if isinstance(payload, VerificationResult):
            return payload
        submitted = classify_payload(payload)
        if submitted.status is not VerificationStatus.SUCCESS:
            return submitted

        guid = str(payload.get("result", ""))
        if not guid:
            return VerificationResult(
                VerificationStatus.PROVIDER_ERROR,
                "verification submission omitted its GUID",
            )
        if not wait:
            return VerificationResult(
                VerificationStatus.PENDING,
                "verification submitted",
                guid=guid,
            )
        if max_polls < 1:
            raise VerifierConfigurationError(
                "max_polls must be positive when wait=True"
            )

        check_params = {
            "chainid": self.spec.chain_id,
            "apikey": self.api_key,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": guid,
        }
        for attempt in range(max_polls):
            if attempt:
                self.sleep(poll_interval)
            check_payload = self._request("GET", params=check_params)
            if isinstance(check_payload, VerificationResult):
                return check_payload
            result = classify_payload(check_payload)
            if result.status is VerificationStatus.PENDING:
                continue
            return VerificationResult(result.status, result.detail, guid=guid)

        return VerificationResult(
            VerificationStatus.TIMEOUT,
            "verification remained pending after polling budget",
            guid=guid,
        )


def _compiler_version(manifest_data, standard_json):
    """Resolve the vyper:<version> string Etherscan wants.

    The manifest record has never carried a `compiler_version` key --
    `deployed_contracts_manifest` emits address/abi/solc_json/args/file, on this
    branch and on master alike -- so requiring one at the record level rejected
    every manifest in the repository. The value is there, one level down, as
    solc_json.compiler_version in the form `v0.4.3+commit.bff19ea2`.

    A record-level value still wins if one is ever emitted. Otherwise this
    derives it, which is what master did by hardcoding "vyper:0.4.3"; reading
    the recorded version instead keeps a manifest verifiable after the pinned
    compiler moves on.
    """
    explicit = manifest_data.get("compiler_version")
    if isinstance(explicit, str) and explicit:
        return explicit
    recorded = standard_json.get("compiler_version")
    if not isinstance(recorded, str) or not recorded:
        return None
    # "v0.4.3+commit.bff19ea2" -> "vyper:0.4.3"
    return f"vyper:{recorded.lstrip('v').split('+')[0]}"


def create_verifier(
    *,
    chain: str,
    api_key: str | None,
    provider: str = "auto",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    session: Any = requests,
    sleep: Callable[[float], None] = time.sleep,
) -> EtherscanVerifier:
    spec = _chain_spec(chain)
    selected = spec.provider if provider == "auto" else provider
    if provider == "auto" and selected is None:
        raise VerifierConfigurationError(
            f"no supported official verifier provider for chain: {chain}"
        )
    if selected not in PROVIDER_POLICIES:
        raise VerifierConfigurationError(
            f"unsupported verifier provider: {selected or 'none'}"
        )
    if selected != spec.provider:
        raise VerifierConfigurationError(
            f"provider {selected} is not supported for chain: {chain}"
        )
    return EtherscanVerifier(
        chain=chain,
        api_key=api_key,
        timeout=timeout,
        session=session,
        sleep=sleep,
    )


def is_contract_verified(api_key: str, contract_address: str, chain: str) -> bool:
    """Compatibility wrapper over the testable adapter."""
    return create_verifier(chain=chain, api_key=api_key).lookup(
        contract_address
    ).ok


def verify_from_manifest(
    api_key: str,
    contract_name: str,
    manifest_data: Mapping[str, Any],
    chain: str,
) -> bool:
    """Compatibility wrapper over the testable adapter."""
    return create_verifier(chain=chain, api_key=api_key).verify_manifest(
        contract_name, manifest_data
    ).ok
