#!/usr/bin/env python3
"""Validate the canonical Robinhood parameter manifest and render defaults.

The committed manifest is deliberately blocked until every generation-bearing
identity and value is approved.  Consequently the real command validates the
whole manifest and then fails without creating output.  Rendering is exposed
for fully-bound synthetic test fixtures only.

This module is standard-library-only.  Importing it performs no environment,
filesystem, clock, provider, account, RPC, or network access.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "h04-robinhood-parameters-v2"
BASELINE_COMMIT = "a86650b187c523f27c92f05bfe959d06840025a6"
BASELINE_TREE = "cb640ed3d8e7074cc6fb78ac118a4d45566ba421"
PHASE_A_SHA256 = (
    "8281011aaa4bc3c9edcc5d183d86a9f510d727e63318b53e4e6c5684c9d7be2e"
)
R2_SHA256 = "05069136bf2bcbbd1a0dcc698fe84c31ba54cb1daaa9d4587e143fbc54f71e0e"
R2_REPOSITORY_PATH = "review-archives/h04/h04-group2-proposal-R2.md"
H04_REVIEW_COMMIT = "81ad3ff758c2a3a08577ce5b9dc0ae0eff31a038"
OWNER_APPROVAL_SHA256 = (
    "0c031e44d3f68a1620cab2abd2f4407442ecd9fb1615d903f2195a690165795f"
)
OWNER_APPROVAL_DATE = "2026-07-29"
OWNER_POLICY_APPROVAL = {
    "status": "approved",
    "date": OWNER_APPROVAL_DATE,
    "provenance": (
        "Owner approval 2026-07-29; exact authorization bytes SHA-256 "
        + OWNER_APPROVAL_SHA256
    ),
}

DECISION_KEYS = ("id", "status", "operative")
BINDING_SCHEDULE_KEYS = (
    "id",
    "records",
    "owner",
    "reviewer_class",
    "classification",
    "lifecycle_phase",
    "prerequisite",
    "closure_artifacts",
    "invalidation",
)


def _record_ids(*numbers: int) -> list[str]:
    return [f"P-H04-{number:03d}" for number in numbers]


EXPECTED_DECISION_REGISTRY = [
    {
        "id": f"D-H04-{number:02d}",
        "status": "approved",
        "operative": True,
    }
    for number in range(1, 19)
] + [
    {
        "id": "D-H04-19",
        "status": "retired_non_operative",
        "operative": False,
    },
] + [
    {
        "id": f"D-H04-{number:02d}",
        "status": "approved",
        "operative": True,
    }
    for number in (20, 21)
]

EXPECTED_BINDING_SCHEDULES = [
    {
        "id": "BS-H04-CORE-TOKEN-IDENTITIES-RC",
        "records": _record_ids(56, 112, 143, 174, 303),
        "owner": "OWN-H05",
        "reviewer_class": "protocol",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before Defaults render and H-05 plan freeze",
        "closure_artifacts": [
            "exact Robinhood GREEN, RIPE and sGREEN addresses",
            "source, runtime, ABI and compiler identities",
            "token metadata",
            "RipeHq and plan placement",
            "cross-record equality",
            "H-05 typed plan and H-06 binding",
            "no Base address",
        ],
        "invalidation": [
            "token artifact",
            "constructor",
            "metadata",
            "registry",
            "chain",
            "plan change",
        ],
    },
    {
        "id": "BS-H04-LP-ARTIFACTS-RC",
        "records": _record_ids(
            64,
            236,
            240,
            241,
            242,
            267,
            271,
            272,
            273,
            301,
            393,
            394,
            395,
            396,
        ),
        "owner": "OWN-H04",
        "reviewer_class": "protocol with mandatory oracle co-review",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before launch plan closes",
        "closure_artifacts": [
            "exact LP token and pool addresses",
            "constituents",
            "decimals",
            "deposit limits",
            "oracle/feed artifacts",
            "price-source placement",
            "pool evidence",
            "cross-record equality and H-05/H-06 binding",
        ],
        "invalidation": [
            "LP",
            "pool",
            "constituent",
            "decimals",
            "oracle",
            "feed",
            "limits",
            "plan drift",
        ],
    },
    {
        "id": "BS-H04-TRAINING-WHEELS-OP",
        "records": _record_ids(79, 413, 414),
        "owner": "OWN-H04 with OWN-SECOPS",
        "reviewer_class": "security",
        "classification": "operator_deployment",
        "lifecycle_phase": "operator/deployment",
        "prerequisite": "before testnet",
        "closure_artifacts": [
            "fresh contract source/runtime/ABI/compiler hashes",
            "exact address",
            "default-deny proof",
            "exact allowlist",
            "governance handoff",
            "deployer relinquishment",
            "P079/P413 equality",
        ],
        "invalidation": [
            "code",
            "address",
            "allowlist",
            "governance",
            "handoff drift",
        ],
    },
    {
        "id": "BS-H04-GOVERNANCE-ROLES-OP",
        "records": _record_ids(409, 410, 411),
        "owner": "OWN-SECOPS",
        "reviewer_class": "security",
        "classification": "operator_deployment",
        "lifecycle_phase": "operator/deployment",
        "prerequisite": "before testnet/production handoff",
        "closure_artifacts": [
            "exact governance, Safe and guardian addresses",
            "Safe owners and threshold",
            "custody and response policy",
            "role matrix",
            "handoff receipts",
            "deployer-authority loss",
        ],
        "invalidation": [
            "address",
            "threshold",
            "membership",
            "custody",
            "scope",
            "handoff drift",
        ],
    },
    {
        "id": "BS-H04-PSM-PARAMETERS-RC",
        "records": _record_ids(361, 362, 363, 364, 365, 367),
        "owner": "OWN-H04",
        "reviewer_class": "risk with protocol/security review",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before PSM staging",
        "closure_artifacts": [
            "exact fees",
            "mint/redeem capacities",
            "interval",
            "reserve amount",
            "source and custody",
            "units and risk rationale",
            "disabled-capability proof",
            "no activation",
        ],
        "invalidation": [
            "reserve",
            "decimals",
            "risk",
            "fee",
            "interval",
            "custody",
            "PSM-source drift",
        ],
    },
    {
        "id": "BS-H04-PSM-ALLOWLIST-OP",
        "records": _record_ids(366),
        "owner": "OWN-SECOPS",
        "reviewer_class": "security",
        "classification": "operator_deployment",
        "lifecycle_phase": "operator/deployment",
        "prerequisite": "before PSM staging",
        "closure_artifacts": [
            "exact address collection and membership purpose",
            "default-deny proof",
            "custody/monitoring",
            "no Base or placeholder address",
        ],
        "invalidation": [
            "membership",
            "custody",
            "role",
            "PSM-policy drift",
        ],
    },
    {
        "id": "BS-H04-PSM-SEQUENCE-OP",
        "records": _record_ids(370),
        "owner": "OWN-H05",
        "reviewer_class": "deployment",
        "classification": "operator_deployment",
        "lifecycle_phase": "operator/deployment",
        "prerequisite": "before pre-activation configuration",
        "closure_artifacts": [
            "exact typed H-05 plan",
            "order and hash",
            "dependency and postcondition assertions",
            "PSM remains disabled",
            "H-06 binding",
            "separate execution authority",
        ],
        "invalidation": [
            "plan",
            "order",
            "dependency",
            "artifact",
            "disabled-postcondition drift",
        ],
    },
    {
        "id": "BS-H04-SUPPLY-RECIPIENTS-OP",
        "records": _record_ids(416, 418, 420),
        "owner": "OWN-SECOPS",
        "reviewer_class": "security",
        "classification": "operator_deployment",
        "lifecycle_phase": "operator/deployment",
        "prerequisite": "before H-05 execution",
        "closure_artifacts": [
            "exact constructor address inputs",
            "custody rationale",
            "H-05 plan binding",
            "zero-address rejection",
            "proof paired quantities are exactly zero",
        ],
        "invalidation": [
            "recipient",
            "custody",
            "constructor",
            "amount",
            "plan drift",
        ],
    },
    {
        "id": "BS-H04-ENDAOMENT-METADATA-RC",
        "records": _record_ids(422, 423, 424, 425),
        "owner": "OWN-H04",
        "reviewer_class": "protocol",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before Endaoment deployment",
        "closure_artifacts": [
            "chain-specific WETH address and code identity",
            "native name, symbol and decimals",
            "authoritative chain evidence",
            "H-05/H-06 binding",
        ],
        "invalidation": [
            "chain",
            "WETH",
            "metadata",
            "artifact",
            "plan drift",
        ],
    },
    {
        "id": "BS-H04-STOCK-ACTIVATION-PARKED",
        "records": _record_ids(*range(371, 382), *range(383, 389)),
        "owner": "OWN-T8",
        "reviewer_class": (
            "track8 with mandatory oracle/risk/security review if reopened"
        ),
        "classification": "parked",
        "lifecycle_phase": "separately parked future work",
        "prerequisite": "no deadline",
        "closure_artifacts": [
            "cannot close under current authority",
            "reopening requires a new owner decision",
            "exact M2-M5 artifacts",
            (
                "AAPL identity/feed/decimals/P8/caps/vault/risk/auction/routes"
            ),
            "composed proofs",
            (
                "separate treatment of parked settlement, loss and bad-debt "
                "questions"
            ),
        ],
        "invalidation": [
            "Track 8",
            "oracle",
            "risk",
            "token",
            "vault",
            "settlement",
            "policy change",
        ],
    },
    {
        "id": "BS-H04-S5-DEFAULTS-BIND-RC",
        "records": _record_ids(310),
        "owner": "OWN-S5",
        "reviewer_class": "protocol with security/H-05/H-06 review",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before CM-008 enters H-05",
        "closure_artifacts": [
            "one exact future DefaultsRobinhood address shared by Ledger and MissionControl",
            "manifest/source/ABI/compiler/creation/runtime hashes",
            "exact Ledger 0x64/no-fallback proof",
            "H-05 plan and H-06 manifest hashes",
        ],
        "invalidation": [
            "Defaults",
            "Ledger",
            "ABI",
            "compiler",
            "address",
            "0x64 semantic",
            "plan",
            "manifest drift",
        ],
    },
    {
        "id": "BS-H04-STABILITY-PLAN-RC",
        "records": _record_ids(390),
        "owner": "OWN-H05",
        "reviewer_class": "protocol",
        "classification": "release_candidate",
        "lifecycle_phase": "release candidate",
        "prerequisite": "before H-05 plan freeze",
        "closure_artifacts": [
            "exact specialStabPoolId or separately approved absence",
            "registry topology",
            "stability-plan assertions",
            "H-05/H-06 binding",
        ],
        "invalidation": [
            "vault",
            "registry",
            "stability",
            "plan drift",
        ],
    },
    {
        "id": "BS-H04-REWARDS-PROMOTION-RC",
        "records": _record_ids(399),
        "owner": "OWN-REWARDS",
        "reviewer_class": "rewards with security review",
        "classification": "release_candidate",
        "lifecycle_phase": "separately reviewed release candidate",
        "prerequisite": "within the seven-day reward promotion",
        "closure_artifacts": [
            "exact promotion values",
            "allocation conservation",
            "artifacts",
            "execution plan",
            "monitoring",
            "separate activation approval",
        ],
        "invalidation": [
            "reward economics",
            "token",
            "plan",
            "promotion-window drift",
        ],
    },
    {
        "id": "BS-H04-CCIP-PARKED",
        "records": _record_ids(403),
        "owner": "OWN-T1",
        "reviewer_class": "security",
        "classification": "parked",
        "lifecycle_phase": "separately parked future work",
        "prerequisite": "no deadline",
        "closure_artifacts": [
            "cannot close under current authority",
            "explicit CCIP reopening",
            "supported release/toolchain",
            "exact artifacts",
            "roles",
            "peers",
            "limits",
            "registration",
            "security review",
            "separate activation authority",
        ],
        "invalidation": [
            "CCIP release",
            "toolchain",
            "router",
            "peer",
            "role",
            "limit",
            "directive change",
        ],
    },
]
BINDING_SCHEDULES_SHA256 = (
    "f6605710bb6a3f7274d66bfcbb8104fdd21f9a78cf043736474a2f5a6e14e167"
)

RECORD_KEYS = (
    "id",
    "h03_ref",
    "destination",
    "description",
    "value",
    "unit",
    "status",
    "source",
    "owner",
    "reviewer_class",
    "approval",
    "launch_phase",
    "blockers",
    "zero_semantics",
    "base_comparison",
    "conversion",
    "generated_repr",
    "consumers",
    "invalidation",
)
TOP_KEYS = (
    "schema_version",
    "baseline",
    "decision_registry",
    "binding_schedules",
    "parameters",
)
BASELINE_KEYS = (
    "commit",
    "tree",
    "branch",
    "phase_a_evidence_sha256",
    "controlling_r2_path",
    "controlling_r2_sha256",
)
DESTINATION_KEYS = ("kind", "path")
SOURCE_KEYS = ("citation", "commit")
OWNER_KEYS = ("kind", "id")

STATUS_VALUE_KINDS = {
    "approved": {"concrete"},
    "disabled": {"concrete"},
    "omitted": {"typed_null"},
    "blocked": {"typed_null"},
    "unresolved": {"typed_null"},
    "derived": {"derived"},
    "inherited": {"inherited"},
    "not_applicable": {"typed_null"},
}
DESTINATION_KINDS = {"defaults_field", "deployment_input", "assertion"}
UNIT_KINDS = {
    "blocks",
    "seconds",
    "basis_points",
    "token_base_units",
    "percentage_allocation",
    "boolean",
    "address",
    "registry_id",
    "hash",
    "count",
    "rate_per_block_1e6",
}
REVIEWER_CLASSES = {
    "protocol",
    "risk",
    "security",
    "deployment",
    "oracle",
    "rewards",
    "track8",
    "evidence",
}
LAUNCH_PHASES = {
    "deployed initial value",
    "pre-activation configuration",
    "atomic Stock activation",
    "within-seven-day separately reviewed CCIP promotion",
    "within-seven-day separately reviewed reward activation",
    "post-launch release",
    "omitted",
    "blocked",
}
ZERO_KINDS = {
    "not_zero",
    "legitimate_zero",
    "legitimate_false",
    "legitimate_empty",
    "not_applicable",
}
BASE_COMPARISON_KINDS = {
    "same",
    "converted",
    "different_approved",
    "not_applicable",
    "blocked_no_inheritance",
}
CONVERSION_KINDS = {
    "identity",
    "ceil_base_blocks_div_6",
    "seconds_unchanged",
    "formula",
    "not_applicable",
}
BLOCKERS = {
    "B-H04-PARAMS",
    "B-H04-ROLES",
    "B-H04-SUPPLY",
    "B-H04-STOCK",
    "B-H04-LP",
    "B-H04-ORACLE",
    "B-H04-PSM",
    "B-H04-PSM-SEQ",
    "B-H04-S5-BIND",
    "B-H04-PLAN-BINDINGS",
    "B-H04-REWARD-PROMO",
    "B-H04-CCIP",
}

EXPECTED_CANONICAL_COUNTS = {
    "status": {
        "approved": 152,
        "disabled": 150,
        "omitted": 34,
        "blocked": 60,
        "derived": 1,
        "not_applicable": 31,
    },
    "approval": {
        "approved": 367,
        "pending_binding": 61,
    },
}

EXPECTED_OPERATIVE_BLOCKERS = {
    **{
        f"P-H04-{number:03d}": ["B-H04-PSM"]
        for number in range(361, 368)
    },
    "P-H04-370": ["B-H04-PSM-SEQ"],
    **{
        f"P-H04-{number:03d}": ["B-H04-ROLES"]
        for number in (56, 79, 409, 410, 411, 413, 414, 416, 418, 420)
    },
    "P-H04-064": ["B-H04-LP", "B-H04-ORACLE"],
    **{
        f"P-H04-{number:03d}": ["B-H04-PLAN-BINDINGS"]
        for number in (112, 143, 174, 303)
    },
    **{
        f"P-H04-{number:03d}": [
            "B-H04-SUPPLY",
            "B-H04-PLAN-BINDINGS",
        ]
        for number in range(422, 426)
    },
    **{
        f"P-H04-{number:03d}": ["B-H04-STOCK"]
        for number in (*range(371, 382), *range(383, 389))
    },
    "P-H04-310": ["B-H04-S5-BIND"],
    **{
        f"P-H04-{number:03d}": ["B-H04-LP", "B-H04-ORACLE"]
        for number in (
            236,
            240,
            241,
            242,
            267,
            271,
            272,
            273,
            301,
            393,
            394,
            395,
            396,
        )
    },
    "P-H04-390": ["B-H04-PARAMS", "B-H04-PLAN-BINDINGS"],
    "P-H04-399": ["B-H04-REWARD-PROMO"],
    "P-H04-403": ["B-H04-CCIP"],
}

GEN_CONFIG_FIELDS = (
    "perUserMaxVaults",
    "perUserMaxAssetsPerVault",
    "priceStaleTime",
    "canDeposit",
    "canWithdraw",
    "canBorrow",
    "canRepay",
    "canClaimLoot",
    "canLiquidate",
    "canRedeemCollateral",
    "canRedeemInStabPool",
    "canBuyInAuction",
    "canClaimInStabPool",
)
AUCTION_FIELDS = ("hasParams", "startDiscount", "maxDiscount", "delay", "duration")
GEN_DEBT_FIELDS = (
    "perUserDebtLimit",
    "globalDebtLimit",
    "minDebtAmount",
    "numAllowedBorrowers",
    "maxBorrowPerInterval",
    "numBlocksPerInterval",
    "minDynamicRateBoost",
    "maxDynamicRateBoost",
    "increasePerDangerBlock",
    "maxBorrowRate",
    "maxLtvDeviation",
    "keeperFeeRatio",
    "minKeeperFee",
    "maxKeeperFee",
    "isDaowryEnabled",
    "ltvPaybackBuffer",
)
BOND_FIELDS = (
    "asset",
    "amountPerEpoch",
    "canBond",
    "minRipePerUnit",
    "maxRipePerUnit",
    "maxRipePerUnitLockBonus",
    "epochLength",
    "shouldAutoRestart",
    "restartDelayBlocks",
)
REWARD_FIELDS = (
    "arePointsEnabled",
    "ripePerBlock",
    "borrowersAlloc",
    "stakersAlloc",
    "votersAlloc",
    "genDepositorsAlloc",
    "autoStakeRatio",
    "autoStakeDurationRatio",
    "stabPoolRipePerDollarClaimed",
)
LOCK_FIELDS = (
    "minLockDuration",
    "maxLockDuration",
    "maxLockBoost",
    "canExit",
    "exitFee",
)
GOV_FIELDS = (
    "asset",
    *(f"config.lockTerms.{field}" for field in LOCK_FIELDS),
    "config.assetWeight",
    "config.shouldFreezeWhenBadDebt",
)
HR_FIELDS = (
    "contribTemplate",
    "maxCompensation",
    "minCliffLength",
    "maxStartDelay",
    "minVestingLength",
    "maxVestingLength",
)
DEBT_TERM_FIELDS = (
    "ltv",
    "redemptionThreshold",
    "liqThreshold",
    "liqFee",
    "borrowRate",
    "daowry",
)
ASSET_FIELDS = (
    "asset",
    "config.vaultIds",
    "config.stakersPointsAlloc",
    "config.voterPointsAlloc",
    "config.perUserDepositLimit",
    "config.globalDepositLimit",
    "config.minDepositBalance",
    *(f"config.debtTerms.{field}" for field in DEBT_TERM_FIELDS),
    "config.shouldBurnAsPayment",
    "config.shouldTransferToEndaoment",
    "config.shouldSwapInStabPools",
    "config.shouldAuctionInstantly",
    "config.canDeposit",
    "config.canWithdraw",
    "config.canRedeemCollateral",
    "config.canRedeemInStabPool",
    "config.canBuyInAuction",
    "config.canClaimInStabPool",
    "config.specialStabPoolId",
    *(f"config.customAuctionParams.{field}" for field in AUCTION_FIELDS),
    "config.whitelist",
    "config.isNft",
)
GOV_ROWS = ("RIPE", "RIPE_WETH_LP")
ASSET_ROWS = (
    "AAPL",
    "GREEN",
    "RIPE",
    "SGREEN",
    "USDG",
    "GREEN_USDG_LP",
    "RIPE_WETH_LP",
)
RENDERED_ASSET_ROWS = (
    "GREEN",
    "RIPE",
    "SGREEN",
    "GREEN_USDG_LP",
    "RIPE_WETH_LP",
)

FORBIDDEN_BASE_ADDRESSES = {
    "0x02981db1a99a14912b204437e7a2e02679b57668",
    "0x0b3e328455c4059eeb9e3f84b5543f74e24e7e1b",
    "0x1c419aef78b44f30d8f3dfa2ab13d3538466dc48",
    "0x1cb8dab80f19fc5aca06c2552aecd79015008ea8",
    "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2",
    "0x2255b0006a3da38aa184e0f9d5e056c2d0448065",
    "0x2a0a59d6b975828e781ecac125dba40d7ee5ddc0",
    "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",
    "0x3fb0fc9d3ddd543ad1b748ed2286a022f4638493",
    "0x4200000000000000000000000000000000000006",
    "0x44cf3c4f000dfd76a35d03298049d37be688d6f9",
    "0x4965578d80e54b5ebe3bb5d7b1b3e0425559c1d1",
    "0x4ed4e862860bed51a9570b96d89af5e1b0efefed",
    "0x6f5ef229d7f07183bf91df68702d01e9bda37ca2",
    "0x765824ad2ed0ecb70ecc25b0cf285832b335d6a9",
    "0x7fcd174e80f264448ebee8c88a7c4476aaf58ea6",
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
    "0x96f1a7ce331f40afe866f3b707c223e377661087",
    "0x9b8df6e244526ab5f6e6400d331db28c8fdddb55",
    "0xa88594d404727625a9437c3f886c7643872296ae",
    "0xaa0f13488ce069a7b5a099457c753a7cfbe04d36",
    "0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf",
    "0xb33852cfd0c22647aac501a6af59bc4210a686bf",
    "0xcb17c9db87b595717c857a08468793f5bab6445f",
    "0xcb585250f852c6c6bf90434ab21a00f02833a4af",
    "0xcbada732173e39521cdbe8bf59a6dc85a9fc7b8c",
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
    "0xcbd06e5a2b0c65597161de254aa074e489deb510",
    "0xd1eac76497d06cf15475a5e3984d5bc03de7c707",
    "0xd6c283655b42fa0eb2685f7ab819784f071459dc",
}


class ManifestError(ValueError):
    """A stable fail-closed manifest or rendering error."""


def convert_base_blocks(base_blocks: int) -> int:
    """Convert approved nonzero Base block counts to Robinhood block counts."""
    if type(base_blocks) is not int or base_blocks < 0:
        raise ManifestError("H04_BLOCK_CONVERSION_INPUT")
    if base_blocks == 0:
        return 0
    return max(1, (base_blocks + 5) // 6)


def _expect_keys(value: Mapping[str, Any], keys: Sequence[str], code: str) -> None:
    if set(value) != set(keys):
        raise ManifestError(code)


def _reject_null(value: Any) -> None:
    if value is None:
        raise ManifestError("H04_NULL_FORBIDDEN")
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_null(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_null(nested)


def _reject_sensitive_or_placeholder_text(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        forbidden = (
            "todo",
            "tbd",
            "dummy",
            "placeholder",
            "/users/",
            "/home/",
            "localhost",
            "http://",
            "https://",
            "rpc",
            "api_key",
            "private_key",
            "mnemonic",
        )
        if any(token in lowered for token in forbidden):
            raise ManifestError("H04_FORBIDDEN_TEXT")
        if re.fullmatch(r"0x0{40}", lowered):
            raise ManifestError("H04_ZERO_ADDRESS_LITERAL")
        if lowered in FORBIDDEN_BASE_ADDRESSES:
            raise ManifestError("H04_BASE_ADDRESS_LEAK")
    elif isinstance(value, Mapping):
        for nested in value.values():
            _reject_sensitive_or_placeholder_text(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_sensitive_or_placeholder_text(nested)


def canonical_default_paths() -> tuple[str, ...]:
    paths: list[str] = []
    paths.extend(f"Defaults.genConfig.{field}" for field in GEN_CONFIG_FIELDS)
    paths.extend(f"Defaults.genDebtConfig.{field}" for field in GEN_DEBT_FIELDS)
    paths.extend(
        f"Defaults.genDebtConfig.genAuctionParams.{field}"
        for field in AUCTION_FIELDS
    )
    paths.extend(
        (
            "Defaults.ripeAvailForRewards",
            "Defaults.ripeAvailForHr",
            "Defaults.ripeAvailForBonds",
        )
    )
    paths.extend(f"Defaults.ripeBondConfig.{field}" for field in BOND_FIELDS)
    paths.extend(f"Defaults.rewardsConfig.{field}" for field in REWARD_FIELDS)
    for row in GOV_ROWS:
        paths.extend(
            f"Defaults.ripeGovVaultConfigs[{row}].{field}" for field in GOV_FIELDS
        )
    paths.extend(f"Defaults.hrConfig.{field}" for field in HR_FIELDS)
    paths.extend(
        (
            "Defaults.underscoreRegistry",
            "Defaults.trainingWheels",
            "Defaults.shouldCheckLastTouch",
        )
    )
    for row in ASSET_ROWS:
        paths.extend(
            f"Defaults.assetConfigs[{row}].{field}" for field in ASSET_FIELDS
        )
    paths.extend(
        (
            "Defaults.priorityLiqAssetVaults[0].vaultId",
            "Defaults.priorityLiqAssetVaults[0].asset",
            "Defaults.priorityStabVaults[0].vaultId",
            "Defaults.priorityStabVaults[0].asset",
            "Defaults.priorityStabVaults[1].vaultId",
            "Defaults.priorityStabVaults[1].asset",
            "Defaults.priorityPriceSourceIds[0]",
            "Defaults.liteSigners[0]",
        )
    )
    return tuple(paths)


def canonical_default_templates() -> tuple[str, ...]:
    paths: list[str] = []
    paths.extend(f"Defaults.genConfig.{field}" for field in GEN_CONFIG_FIELDS)
    paths.extend(f"Defaults.genDebtConfig.{field}" for field in GEN_DEBT_FIELDS)
    paths.extend(
        f"Defaults.genDebtConfig.genAuctionParams.{field}"
        for field in AUCTION_FIELDS
    )
    paths.extend(
        (
            "Defaults.ripeAvailForRewards",
            "Defaults.ripeAvailForHr",
            "Defaults.ripeAvailForBonds",
        )
    )
    paths.extend(f"Defaults.ripeBondConfig.{field}" for field in BOND_FIELDS)
    paths.extend(f"Defaults.rewardsConfig.{field}" for field in REWARD_FIELDS)
    paths.extend(
        f"Defaults.ripeGovVaultConfigs[*].{field}" for field in GOV_FIELDS
    )
    paths.extend(f"Defaults.hrConfig.{field}" for field in HR_FIELDS)
    paths.extend(
        (
            "Defaults.underscoreRegistry",
            "Defaults.trainingWheels",
            "Defaults.shouldCheckLastTouch",
        )
    )
    paths.extend(f"Defaults.assetConfigs[*].{field}" for field in ASSET_FIELDS)
    paths.extend(
        (
            "Defaults.priorityLiqAssetVaults[*].vaultId",
            "Defaults.priorityLiqAssetVaults[*].asset",
            "Defaults.priorityStabVaults[*].vaultId",
            "Defaults.priorityStabVaults[*].asset",
            "Defaults.priorityPriceSourceIds[*]",
            "Defaults.liteSigners[*]",
        )
    )
    if len(paths) != 109 or len(set(paths)) != 109:
        raise ManifestError("H04_INTERNAL_109_CENSUS")
    return tuple(paths)


def default_selectors() -> tuple[str, ...]:
    return (
        "genConfig",
        "genDebtConfig",
        "ripeAvailForRewards",
        "ripeAvailForHr",
        "ripeAvailForBonds",
        "ripeBondConfig",
        "rewardsConfig",
        "ripeGovVaultConfigs",
        "hrConfig",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "assetConfigs",
        "priorityLiqAssetVaults",
        "priorityStabVaults",
        "priorityPriceSourceIds",
        "liteSigners",
    )


def _validate_value(value: Mapping[str, Any]) -> str:
    kind = value.get("kind")
    if kind == "concrete":
        _expect_keys(value, ("kind", "raw"), "H04_VALUE_KEYS")
        raw = value["raw"]
        if type(raw) not in (bool, int, str):
            raise ManifestError("H04_CONCRETE_TYPE")
        if type(raw) is int and raw < 0:
            raise ManifestError("H04_NEGATIVE_VALUE")
    elif kind == "typed_null":
        _expect_keys(value, ("kind", "reason"), "H04_VALUE_KEYS")
        if not isinstance(value["reason"], str) or not value["reason"]:
            raise ManifestError("H04_TYPED_NULL_REASON")
    elif kind == "derived":
        _expect_keys(value, ("kind", "formula", "inputs"), "H04_VALUE_KEYS")
        if not isinstance(value["formula"], str) or not value["formula"]:
            raise ManifestError("H04_DERIVED_FORMULA")
        if not isinstance(value["inputs"], list) or not value["inputs"]:
            raise ManifestError("H04_DERIVED_INPUTS")
    elif kind == "inherited":
        _expect_keys(value, ("kind", "inherited_from"), "H04_VALUE_KEYS")
        if not isinstance(value["inherited_from"], str):
            raise ManifestError("H04_INHERITED_SOURCE")
    else:
        raise ManifestError("H04_VALUE_KIND")
    return str(kind)


def _validate_unit(unit: Mapping[str, Any]) -> None:
    kind = unit.get("kind")
    if kind not in UNIT_KINDS:
        raise ManifestError("H04_UNIT_KIND")
    if kind in {"basis_points", "percentage_allocation"}:
        _expect_keys(unit, ("kind", "denominator"), "H04_UNIT_KEYS")
        if unit["denominator"] != 10_000:
            raise ManifestError("H04_BPS_DENOMINATOR")
    elif kind == "rate_per_block_1e6":
        _expect_keys(unit, ("kind", "denominator"), "H04_UNIT_KEYS")
        if unit["denominator"] != 1_000_000:
            raise ManifestError("H04_RATE_DENOMINATOR")
    else:
        _expect_keys(unit, ("kind",), "H04_UNIT_KEYS")


def _validate_approval(approval: Mapping[str, Any], status: str) -> None:
    approval_status = approval.get("status")
    if approval_status == "approved":
        keys = tuple(approval)
        if set(keys) not in (
            {"status", "date", "provenance"},
            {"status", "date", "provenance", "schedule_id"},
        ):
            raise ManifestError("H04_APPROVAL_KEYS")
        if status in {"blocked", "unresolved"}:
            raise ManifestError("H04_BLOCKED_APPROVAL")
        if not re.fullmatch(r"20\d\d-\d\d-\d\d", str(approval["date"])):
            raise ManifestError("H04_APPROVAL_DATE")
        if "schedule_id" in approval and not isinstance(
            approval["schedule_id"], str
        ):
            raise ManifestError("H04_SCHEDULE_ID")
    elif approval_status == "pending_binding":
        _expect_keys(
            approval,
            ("status", "schedule_id"),
            "H04_APPROVAL_KEYS",
        )
        if status not in {"blocked", "unresolved", "derived", "inherited"}:
            raise ManifestError("H04_PENDING_BINDING_APPROVAL")
        if not isinstance(approval["schedule_id"], str):
            raise ManifestError("H04_SCHEDULE_ID")
    else:
        raise ManifestError("H04_APPROVAL_STATUS")


def _validate_generated_repr(
    generated: Mapping[str, Any],
    destination_kind: str,
    status: str,
) -> None:
    kind = generated.get("kind")
    if kind == "vyper":
        _expect_keys(generated, ("kind", "repr"), "H04_GENERATED_KEYS")
        if destination_kind != "defaults_field":
            raise ManifestError("H04_NONDEFAULT_GENERATED")
        if status in {"blocked", "unresolved", "not_applicable", "omitted"}:
            raise ManifestError("H04_UNRESOLVED_GENERATED")
        if not isinstance(generated["repr"], str) or not generated["repr"]:
            raise ManifestError("H04_GENERATED_REPR")
    elif kind == "not_generated":
        _expect_keys(generated, ("kind", "reason"), "H04_GENERATED_KEYS")
        if not isinstance(generated["reason"], str) or not generated["reason"]:
            raise ManifestError("H04_NOT_GENERATED_REASON")
    else:
        raise ManifestError("H04_GENERATED_KIND")


def _validate_record(record: Mapping[str, Any]) -> None:
    _expect_keys(record, RECORD_KEYS, "H04_RECORD_KEYS")
    if not re.fullmatch(r"P-H04-\d{3}", str(record["id"])):
        raise ManifestError("H04_RECORD_ID")
    if not re.fullmatch(r"CM-0(?:[0-5]\d|60)", str(record["h03_ref"])):
        raise ManifestError("H04_H03_REFERENCE")

    destination = record["destination"]
    if not isinstance(destination, Mapping):
        raise ManifestError("H04_DESTINATION_TYPE")
    _expect_keys(destination, DESTINATION_KEYS, "H04_DESTINATION_KEYS")
    destination_kind = destination["kind"]
    if destination_kind not in DESTINATION_KINDS:
        raise ManifestError("H04_DESTINATION_KIND")
    if not isinstance(destination["path"], str) or not destination["path"]:
        raise ManifestError("H04_DESTINATION_PATH")

    if not isinstance(record["description"], str) or not record["description"]:
        raise ManifestError("H04_DESCRIPTION")
    if not isinstance(record["value"], Mapping):
        raise ManifestError("H04_VALUE_TYPE")
    value_kind = _validate_value(record["value"])
    status = record["status"]
    if status not in STATUS_VALUE_KINDS:
        raise ManifestError("H04_STATUS")
    if value_kind not in STATUS_VALUE_KINDS[status]:
        raise ManifestError("H04_STATUS_VALUE_KIND")

    if not isinstance(record["unit"], Mapping):
        raise ManifestError("H04_UNIT_TYPE")
    _validate_unit(record["unit"])

    source = record["source"]
    if not isinstance(source, Mapping):
        raise ManifestError("H04_SOURCE_TYPE")
    _expect_keys(source, SOURCE_KEYS, "H04_SOURCE_KEYS")
    if not isinstance(source["citation"], str) or not source["citation"]:
        raise ManifestError("H04_SOURCE_CITATION")
    if not re.fullmatch(r"[0-9a-f]{40}", str(source["commit"])):
        raise ManifestError("H04_SOURCE_COMMIT")

    owner = record["owner"]
    if not isinstance(owner, Mapping):
        raise ManifestError("H04_OWNER_TYPE")
    _expect_keys(owner, OWNER_KEYS, "H04_OWNER_KEYS")
    if owner["kind"] not in {"decision", "workstream"}:
        raise ManifestError("H04_OWNER_KIND")
    if not isinstance(owner["id"], str) or not owner["id"]:
        raise ManifestError("H04_OWNER_ID")
    if record["reviewer_class"] not in REVIEWER_CLASSES:
        raise ManifestError("H04_REVIEWER_CLASS")
    if not isinstance(record["approval"], Mapping):
        raise ManifestError("H04_APPROVAL_TYPE")
    _validate_approval(record["approval"], status)
    if record["launch_phase"] not in LAUNCH_PHASES:
        raise ManifestError("H04_LAUNCH_PHASE")
    if not isinstance(record["blockers"], list):
        raise ManifestError("H04_BLOCKERS_TYPE")
    if len(record["blockers"]) != len(set(record["blockers"])):
        raise ManifestError("H04_DUPLICATE_BLOCKER")
    if any(blocker not in BLOCKERS for blocker in record["blockers"]):
        raise ManifestError("H04_UNKNOWN_BLOCKER")
    if status in {"blocked", "unresolved"} and not record["blockers"]:
        raise ManifestError("H04_MISSING_BLOCKER")
    zero = record["zero_semantics"]
    if not isinstance(zero, Mapping):
        raise ManifestError("H04_ZERO_TYPE")
    _expect_keys(zero, ("kind", "explanation"), "H04_ZERO_KEYS")
    if zero["kind"] not in ZERO_KINDS or not zero["explanation"]:
        raise ManifestError("H04_ZERO_SEMANTICS")
    raw = record["value"].get("raw")
    if raw == 0 and type(raw) is int and zero["kind"] != "legitimate_zero":
        raise ManifestError("H04_ZERO_UNTYPED")
    if raw is False and zero["kind"] != "legitimate_false":
        raise ManifestError("H04_FALSE_UNTYPED")
    if (
        raw == "[]"
        and record["id"] == "P-H04-412"
        and zero["kind"] != "legitimate_empty"
    ):
        raise ManifestError("H04_EMPTY_UNTYPED")
    if raw not in (0, False) and zero["kind"] in {
        "legitimate_zero",
        "legitimate_false",
        "legitimate_empty",
    }:
        if (
            raw != "empty(address)"
            and raw != "[]"
            and not (
                raw == "[]"
                and zero["kind"] == "legitimate_empty"
            )
        ):
            raise ManifestError("H04_ZERO_SEMANTICS_MISMATCH")

    comparison = record["base_comparison"]
    if not isinstance(comparison, Mapping):
        raise ManifestError("H04_BASE_COMPARISON_TYPE")
    _expect_keys(
        comparison,
        ("kind", "detail"),
        "H04_BASE_COMPARISON_KEYS",
    )
    if comparison["kind"] not in BASE_COMPARISON_KINDS:
        raise ManifestError("H04_BASE_COMPARISON")
    conversion = record["conversion"]
    if not isinstance(conversion, Mapping):
        raise ManifestError("H04_CONVERSION_TYPE")
    kind = conversion.get("kind")
    if kind not in CONVERSION_KINDS:
        raise ManifestError("H04_CONVERSION_KIND")
    if kind == "ceil_base_blocks_div_6":
        _expect_keys(
            conversion,
            ("kind", "base_blocks", "rh_blocks"),
            "H04_CONVERSION_KEYS",
        )
        if convert_base_blocks(conversion["base_blocks"]) != conversion["rh_blocks"]:
            raise ManifestError("H04_BLOCK_CONVERSION")
        if record["unit"]["kind"] != "blocks":
            raise ManifestError("H04_BLOCK_CONVERSION_DOMAIN")
    elif kind == "formula":
        _expect_keys(conversion, ("kind", "formula"), "H04_CONVERSION_KEYS")
    else:
        _expect_keys(conversion, ("kind",), "H04_CONVERSION_KEYS")
    if record["unit"]["kind"] == "seconds" and kind != "seconds_unchanged":
        raise ManifestError("H04_SECONDS_CONVERSION")
    if record["unit"]["kind"] == "rate_per_block_1e6" and kind != "identity":
        raise ManifestError("H04_DANGER_SLOPE_CONVERSION")

    generated = record["generated_repr"]
    if not isinstance(generated, Mapping):
        raise ManifestError("H04_GENERATED_TYPE")
    _validate_generated_repr(generated, destination_kind, status)
    for field in ("consumers", "invalidation"):
        value = record[field]
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
            or len(value) != len(set(value))
        ):
            raise ManifestError(f"H04_{field.upper()}")


def binding_schedules_digest(schedules: Sequence[Mapping[str, Any]]) -> str:
    encoded = (
        json.dumps(schedules, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_decision_registry(registry: Any) -> None:
    if not isinstance(registry, list):
        raise ManifestError("H04_DECISION_REGISTRY_TYPE")
    for decision in registry:
        if not isinstance(decision, Mapping):
            raise ManifestError("H04_DECISION_REGISTRY_RECORD")
        _expect_keys(decision, DECISION_KEYS, "H04_DECISION_REGISTRY_KEYS")
    if registry != EXPECTED_DECISION_REGISTRY:
        raise ManifestError("H04_DECISION_LIFECYCLE")
    ids = [decision["id"] for decision in registry]
    if len(ids) != len(set(ids)):
        raise ManifestError("H04_DUPLICATE_DECISION")


def _validate_binding_schedules(schedules: Any) -> dict[str, str]:
    if not isinstance(schedules, list):
        raise ManifestError("H04_BINDING_SCHEDULES_TYPE")
    for schedule in schedules:
        if not isinstance(schedule, Mapping):
            raise ManifestError("H04_BINDING_SCHEDULE_RECORD")
        _expect_keys(
            schedule,
            BINDING_SCHEDULE_KEYS,
            "H04_BINDING_SCHEDULE_KEYS",
        )
    ownership: dict[str, str] = {}
    schedule_ids: set[str] = set()
    for schedule in schedules:
        schedule_id = str(schedule["id"])
        if schedule_id in schedule_ids:
            raise ManifestError("H04_DUPLICATE_SCHEDULE_ID")
        schedule_ids.add(schedule_id)
        records = schedule["records"]
        if (
            not isinstance(records, list)
            or not records
            or len(records) != len(set(records))
        ):
            raise ManifestError("H04_SCHEDULE_RECORD_SET")
        for record_id in records:
            if not isinstance(record_id, str) or not re.fullmatch(
                r"P-H04-\d{3}", record_id
            ):
                raise ManifestError("H04_SCHEDULE_RECORD_ID")
            if record_id in ownership:
                raise ManifestError("H04_DUPLICATE_SCHEDULE_OWNERSHIP")
            ownership[record_id] = schedule_id
    if len(schedules) != 14 or len(ownership) != 61:
        raise ManifestError("H04_BINDING_SCHEDULE_CENSUS")
    if schedules != EXPECTED_BINDING_SCHEDULES:
        raise ManifestError("H04_BINDING_SCHEDULE_SEMANTICS")
    if binding_schedules_digest(schedules) != BINDING_SCHEDULES_SHA256:
        raise ManifestError("H04_BINDING_SCHEDULE_DIGEST")
    return ownership


def _validate_policy_transitions(lookup_by_id: Mapping[str, Mapping[str, Any]]) -> None:
    lite = lookup_by_id["P-H04-305"]
    if (
        lite["status"] != "omitted"
        or lite["value"]["kind"] != "typed_null"
        or lite["blockers"]
        or lite["approval"] != OWNER_POLICY_APPROVAL
        or lite["owner"] != {"kind": "decision", "id": "D-H04-15"}
    ):
        raise ManifestError("H04_LITE_SIGNER_POLICY")

    deployment_signers = lookup_by_id["P-H04-412"]
    if (
        deployment_signers["status"] != "approved"
        or deployment_signers["value"] != {"kind": "concrete", "raw": "[]"}
        or deployment_signers["unit"] != {"kind": "address"}
        or deployment_signers["zero_semantics"]["kind"] != "legitimate_empty"
        or deployment_signers["blockers"]
        or deployment_signers["approval"] != OWNER_POLICY_APPROVAL
        or deployment_signers["owner"]
        != {"kind": "decision", "id": "D-H04-15"}
    ):
        raise ManifestError("H04_LITE_SIGNER_CROSS_BOUNDARY")

    for record_id in ("P-H04-415", "P-H04-417", "P-H04-419"):
        record = lookup_by_id[record_id]
        if (
            record["status"] != "approved"
            or record["value"] != {"kind": "concrete", "raw": 0}
            or record["zero_semantics"]["kind"] != "legitimate_zero"
            or record["blockers"]
            or record["approval"] != OWNER_POLICY_APPROVAL
            or record["owner"] != {"kind": "decision", "id": "D-H04-16"}
        ):
            raise ManifestError("H04_NO_PREMINT_POLICY")

    for number in range(81, 112):
        record = lookup_by_id[f"P-H04-{number:03d}"]
        if (
            record["status"] != "omitted"
            or record["value"]["kind"] != "typed_null"
            or record["blockers"]
            or record["approval"] != OWNER_POLICY_APPROVAL
            or record["owner"] != {"kind": "decision", "id": "D-H04-17"}
            or record["launch_phase"] != "omitted"
        ):
            raise ManifestError("H04_STOCK_LAUNCH_OMISSION")


def validate_manifest(
    manifest: Mapping[str, Any],
    *,
    require_canonical_state: bool = True,
) -> Mapping[str, Any]:
    """Validate the entire closed schema and all cross-record invariants."""
    _reject_null(manifest)
    _expect_keys(manifest, TOP_KEYS, "H04_TOP_KEYS")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("H04_SCHEMA_VERSION")
    baseline = manifest["baseline"]
    if not isinstance(baseline, Mapping):
        raise ManifestError("H04_BASELINE_TYPE")
    _expect_keys(baseline, BASELINE_KEYS, "H04_BASELINE_KEYS")
    expected_baseline = {
        "commit": BASELINE_COMMIT,
        "tree": BASELINE_TREE,
        "branch": "rh",
        "phase_a_evidence_sha256": PHASE_A_SHA256,
        "controlling_r2_path": R2_REPOSITORY_PATH,
        "controlling_r2_sha256": R2_SHA256,
    }
    if dict(baseline) != expected_baseline:
        raise ManifestError("H04_BASELINE_IDENTITY")
    _reject_sensitive_or_placeholder_text(baseline)
    _validate_decision_registry(manifest["decision_registry"])
    schedule_ownership = _validate_binding_schedules(
        manifest["binding_schedules"]
    )
    parameters = manifest["parameters"]
    if not isinstance(parameters, list) or not parameters:
        raise ManifestError("H04_PARAMETERS")
    _reject_sensitive_or_placeholder_text(parameters)
    for record in parameters:
        if not isinstance(record, Mapping):
            raise ManifestError("H04_RECORD_TYPE")
        _validate_record(record)
    ids = [record["id"] for record in parameters]
    expected_ids = [f"P-H04-{index:03d}" for index in range(1, len(ids) + 1)]
    if ids != expected_ids:
        raise ManifestError("H04_ID_ORDER")
    lookup_by_id = {record["id"]: record for record in parameters}
    if set(schedule_ownership) - set(lookup_by_id):
        raise ManifestError("H04_UNKNOWN_SCHEDULE_RECORD")

    referenced_ownership: dict[str, str] = {}
    for record in parameters:
        approval = record["approval"]
        schedule_id = approval.get("schedule_id")
        if schedule_id is None:
            if record["id"] in schedule_ownership:
                raise ManifestError("H04_MISSING_SCHEDULE_OWNERSHIP")
            continue
        if schedule_id not in {
            schedule["id"] for schedule in manifest["binding_schedules"]
        }:
            raise ManifestError("H04_UNKNOWN_SCHEDULE_ID")
        if schedule_ownership.get(record["id"]) != schedule_id:
            raise ManifestError("H04_SCHEDULE_REVERSE_REFERENCE")
        if record["id"] in referenced_ownership:
            raise ManifestError("H04_DUPLICATE_SCHEDULE_OWNERSHIP")
        referenced_ownership[record["id"]] = str(schedule_id)
    if referenced_ownership != schedule_ownership:
        raise ManifestError("H04_MISSING_SCHEDULE_REVERSE_REFERENCE")

    _validate_policy_transitions(lookup_by_id)
    destinations = [record["destination"]["path"] for record in parameters]
    if len(destinations) != len(set(destinations)):
        raise ManifestError("H04_DUPLICATE_DESTINATION")
    expected_defaults = canonical_default_paths()
    actual_defaults = tuple(
        record["destination"]["path"]
        for record in parameters
        if record["destination"]["kind"] == "defaults_field"
    )
    if actual_defaults != expected_defaults:
        raise ManifestError("H04_DEFAULT_ORDER_OR_CENSUS")
    deployment_rows = [
        record
        for record in parameters
        if record["destination"]["kind"] != "defaults_field"
    ]
    covered_dp = {
        match.group(1)
        for record in deployment_rows
        if (
            match := re.match(
                r"Deployment\.(DP-(?:0[1-9]|1[0-9]|2[0-2]))(?:\.|$)",
                record["destination"]["path"],
            )
        )
    }
    if covered_dp != {f"DP-{index:02d}" for index in range(1, 23)}:
        raise ManifestError("H04_DP_CENSUS")
    if require_canonical_state:
        status_counts = dict(Counter(record["status"] for record in parameters))
        approval_counts = dict(
            Counter(record["approval"]["status"] for record in parameters)
        )
        if status_counts != EXPECTED_CANONICAL_COUNTS["status"]:
            raise ManifestError("H04_STATUS_CENSUS")
        if approval_counts != EXPECTED_CANONICAL_COUNTS["approval"]:
            raise ManifestError("H04_APPROVAL_CENSUS")
        for record_id, blockers in EXPECTED_OPERATIVE_BLOCKERS.items():
            if lookup_by_id[record_id]["blockers"] != blockers:
                raise ManifestError("H04_OPERATIVE_BLOCKER_BINDING")
        if any(
            blocker.startswith("D-H04-")
            for record in parameters
            for blocker in record["blockers"]
        ):
            raise ManifestError("H04_DECISION_AS_OPERATIVE_BLOCKER")

    normalized = {
        re.sub(r"\[[^]]+\]", "[*]", path) for path in actual_defaults
    }
    if normalized != set(canonical_default_templates()):
        raise ManifestError("H04_109_PARITY")
    selectors = {
        path.split(".", 2)[1].split("[", 1)[0] for path in actual_defaults
    }
    if selectors != set(default_selectors()) or len(selectors) != 17:
        raise ManifestError("H04_17_SELECTOR_PARITY")

    lookup = {
        record["destination"]["path"]: record for record in parameters
    }
    allocations = (
        "borrowersAlloc",
        "stakersAlloc",
        "votersAlloc",
        "genDepositorsAlloc",
    )
    reward_values = [
        lookup[f"Defaults.rewardsConfig.{field}"]["value"]["raw"]
        for field in allocations
    ]
    if any(value != 0 for value in reward_values):
        if sum(reward_values) != 10_000:
            raise ManifestError("H04_REWARD_ALLOCATION")
    for field in allocations:
        record = lookup[f"Defaults.rewardsConfig.{field}"]
        if record["status"] != "disabled" or record["zero_semantics"]["kind"] != (
            "legitimate_zero"
        ):
            raise ManifestError("H04_REWARD_DISABLED_ZERO")
    return manifest


def load_manifest(path: Path) -> Mapping[str, Any]:
    data = path.read_bytes()
    try:
        parsed = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError("H04_JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ManifestError("H04_TOP_TYPE")
    return validate_manifest(parsed)


def _record_map(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        record["destination"]["path"]: record
        for record in manifest["parameters"]
    }


def required_generation_paths() -> tuple[str, ...]:
    paths = list(
        path
        for path in canonical_default_paths()
        if "[AAPL]" not in path
        and "[USDG]" not in path
        and "priorityLiqAssetVaults" not in path
        and path != "Defaults.liteSigners[0]"
    )
    return tuple(paths)


def _repr(lookup: Mapping[str, Mapping[str, Any]], path: str) -> str:
    record = lookup[path]
    if record["status"] in {"blocked", "unresolved"}:
        raise ManifestError(f"H04_UNRESOLVED_GENERATION:{path}")
    generated = record["generated_repr"]
    if generated["kind"] != "vyper":
        raise ManifestError(f"H04_MISSING_GENERATED_REPR:{path}")
    return str(generated["repr"])


def _struct(name: str, fields: Sequence[tuple[str, str]], indent: int = 8) -> str:
    del indent
    inner = ", ".join(f"{key}={value}" for key, value in fields)
    return f"cs.{name}({inner})"


def _auction(
    lookup: Mapping[str, Mapping[str, Any]], prefix: str, indent: int
) -> str:
    return _struct(
        "AuctionParams",
        [(field, _repr(lookup, f"{prefix}.{field}")) for field in AUCTION_FIELDS],
        indent,
    )


def render_defaults(manifest: Mapping[str, Any]) -> str:
    """Render a fully bound, already validated synthetic manifest."""
    validate_manifest(manifest, require_canonical_state=False)
    lookup = _record_map(manifest)
    for path in required_generation_paths():
        record = lookup[path]
        if record["status"] in {"blocked", "unresolved"}:
            raise ManifestError(f"H04_UNRESOLVED_GENERATION:{path}")

    lines = [
        "# @version 0.4.3",
        "",
        '"""Generated only from the reviewed Robinhood parameter manifest."""',
        "",
        "import interfaces.ConfigStructs as cs",
        "",
    ]

    gen_config = _struct(
        "GenConfig",
        [
            (field, _repr(lookup, f"Defaults.genConfig.{field}"))
            for field in GEN_CONFIG_FIELDS
        ],
    )
    lines.extend(
        (
            "@view",
            "@external",
            "def genConfig() -> cs.GenConfig:",
            f"    return {gen_config}",
            "",
        )
    )
    debt_fields = [
        (field, _repr(lookup, f"Defaults.genDebtConfig.{field}"))
        for field in GEN_DEBT_FIELDS
    ]
    debt_fields.append(
        (
            "genAuctionParams",
            _auction(
                lookup,
                "Defaults.genDebtConfig.genAuctionParams",
                12,
            ),
        )
    )
    lines.extend(
        (
            "@view",
            "@external",
            "def genDebtConfig() -> cs.GenDebtConfig:",
            f"    return {_struct('GenDebtConfig', debt_fields)}",
            "",
        )
    )
    for selector in (
        "ripeAvailForRewards",
        "ripeAvailForHr",
        "ripeAvailForBonds",
    ):
        lines.extend(
            (
                "@view",
                "@external",
                f"def {selector}() -> uint256:",
                f"    return {_repr(lookup, f'Defaults.{selector}')}",
                "",
            )
        )
    for selector, struct_name, fields in (
        ("ripeBondConfig", "RipeBondConfig", BOND_FIELDS),
        ("rewardsConfig", "RipeRewardsConfig", REWARD_FIELDS),
        ("hrConfig", "HrConfig", HR_FIELDS),
    ):
        rendered = _struct(
            struct_name,
            [
                (field, _repr(lookup, f"Defaults.{selector}.{field}"))
                for field in fields
            ],
        )
        lines.extend(
            (
                "@view",
                "@external",
                f"def {selector}() -> cs.{struct_name}:",
                f"    return {rendered}",
                "",
            )
        )

    gov_entries = []
    for row in GOV_ROWS:
        prefix = f"Defaults.ripeGovVaultConfigs[{row}]"
        lock = _struct(
            "LockTerms",
            [
                (
                    field,
                    _repr(lookup, f"{prefix}.config.lockTerms.{field}"),
                )
                for field in LOCK_FIELDS
            ],
            16,
        )
        config = _struct(
            "RipeGovVaultConfig",
            (
                ("lockTerms", lock),
                (
                    "assetWeight",
                    _repr(lookup, f"{prefix}.config.assetWeight"),
                ),
                (
                    "shouldFreezeWhenBadDebt",
                    _repr(lookup, f"{prefix}.config.shouldFreezeWhenBadDebt"),
                ),
            ),
            12,
        )
        gov_entries.append(
            _struct(
                "RipeGovVaultConfigEntry",
                (
                    ("asset", _repr(lookup, f"{prefix}.asset")),
                    ("config", config),
                ),
                8,
            )
        )
    lines.extend(
        (
            "@view",
            "@external",
            "def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]:",
            "    return [",
            *[f"        {entry}," for entry in gov_entries],
            "    ]",
            "",
        )
    )
    for selector, return_type in (
        ("underscoreRegistry", "address"),
        ("trainingWheels", "address"),
        ("shouldCheckLastTouch", "bool"),
    ):
        lines.extend(
            (
                "@view",
                "@external",
                f"def {selector}() -> {return_type}:",
                f"    return {_repr(lookup, f'Defaults.{selector}')}",
                "",
            )
        )

    asset_entries = []
    for row in RENDERED_ASSET_ROWS:
        prefix = f"Defaults.assetConfigs[{row}]"
        debt = _struct(
            "DebtTerms",
            [
                (
                    field,
                    _repr(lookup, f"{prefix}.config.debtTerms.{field}"),
                )
                for field in DEBT_TERM_FIELDS
            ],
            16,
        )
        auction = _auction(
            lookup,
            f"{prefix}.config.customAuctionParams",
            16,
        )
        config_fields: list[tuple[str, str]] = []
        for field in ASSET_FIELDS[1:]:
            if field.startswith("config.debtTerms."):
                if field.endswith(".ltv"):
                    config_fields.append(("debtTerms", debt))
                continue
            if field.startswith("config.customAuctionParams."):
                if field.endswith(".hasParams"):
                    config_fields.append(("customAuctionParams", auction))
                continue
            name = field.removeprefix("config.")
            config_fields.append((name, _repr(lookup, f"{prefix}.{field}")))
        config = _struct("AssetConfig", config_fields, 12)
        asset_entries.append(
            _struct(
                "AssetConfigEntry",
                (
                    ("asset", _repr(lookup, f"{prefix}.asset")),
                    ("config", config),
                ),
                8,
            )
        )
    lines.extend(
        (
            "@view",
            "@external",
            "def assetConfigs() -> DynArray[cs.AssetConfigEntry, 50]:",
            "    return [",
            *[f"        {entry}," for entry in asset_entries],
            "    ]",
            "",
            "@view",
            "@external",
            "def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:",
            "    return []",
            "",
        )
    )
    stab_entries = []
    for index in (0, 1):
        prefix = f"Defaults.priorityStabVaults[{index}]"
        stab_entries.append(
            _struct(
                "VaultLite",
                (
                    ("vaultId", _repr(lookup, f"{prefix}.vaultId")),
                    ("asset", _repr(lookup, f"{prefix}.asset")),
                ),
                8,
            )
        )
    lines.extend(
        (
            "@view",
            "@external",
            "def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:",
            "    return [",
            *[f"        {entry}," for entry in stab_entries],
            "    ]",
            "",
            "@view",
            "@external",
            "def priorityPriceSourceIds() -> DynArray[uint256, 10]:",
            "    return ["
            + _repr(lookup, "Defaults.priorityPriceSourceIds[0]")
            + "]",
            "",
            "@view",
            "@external",
            "def liteSigners() -> DynArray[address, 10]:",
            "    return []",
            "",
        )
    )
    rendered = "\n".join(lines)
    lowered = rendered.lower()
    if "defaultsbase" in lowered or "defaultslocal" in lowered:
        raise ManifestError("H04_BASE_LOCAL_NAME_LEAK")
    if any(address in lowered for address in FORBIDDEN_BASE_ADDRESSES):
        raise ManifestError("H04_BASE_ADDRESS_LEAK")
    return rendered


def atomic_replace_output(
    rendered: str,
    output: Path,
    *,
    canonical_output: Path,
) -> None:
    """Atomically replace only the caller-declared canonical output."""
    if output.resolve() != canonical_output.resolve():
        raise ManifestError("H04_NONCANONICAL_TARGET")
    if output.name in {"DefaultsBase.vy", "DefaultsLocal.vy"}:
        raise ManifestError("H04_FORBIDDEN_TARGET")
    if output.name != "DefaultsRobinhood.vy":
        raise ManifestError("H04_NONCANONICAL_TARGET")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=".DefaultsRobinhood.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _repository_paths() -> tuple[Path, Path]:
    repository = Path(__file__).resolve().parents[2]
    return (
        repository / "config" / "robinhood-parameters.json",
        repository / "contracts" / "config" / "DefaultsRobinhood.vy",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and render canonical Robinhood defaults"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate deterministically without writing",
    )
    args = parser.parse_args(argv)
    manifest_path, output_path = _repository_paths()
    try:
        if args.check and output_path.exists():
            raise ManifestError("H04_STALE_DEFAULTS_ROBINHOOD")
        manifest = load_manifest(manifest_path)
        rendered = render_defaults(manifest)
        if args.check:
            print("H04_OK")
            return 0
        atomic_replace_output(
            rendered,
            output_path,
            canonical_output=output_path,
        )
        print("H04_WRITTEN")
        return 0
    except ManifestError as exc:
        print(f"H04_BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
