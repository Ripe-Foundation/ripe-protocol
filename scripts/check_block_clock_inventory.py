#!/usr/bin/env python3
"""Deterministically validate the reviewed block-clock inventory.

The checker intentionally uses only Python's standard library.  The JSON ledger is
the reviewed source of truth; this module discovers current source state and
refuses to create or update semantic classifications.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_PRODUCTION_COUNTS = (102, 97, 18)
EXPECTED_TIMESTAMP_COUNTS = (37, 37, 11)
EXPECTED_BN_IDS = {f"BN-{number:03d}" for number in range(1, 33)}
EXPECTED_CAD_IDS = {"CAD-001"}
EXPECTED_TS_IDS = {f"TS-{number:03d}" for number in range(1, 12)}
TRACK3_REVIEW_COMMIT = "c3040041a1254a774e0a305060330d6ab9cc04ca"
HARDENING_REVIEW_COMMIT = "db7ae895d1b32ae6708f2405274c32c1e3f5222e"
H04_REVIEW_COMMIT = "81ad3ff758c2a3a08577ce5b9dc0ae0eff31a038"
PROFILE1_CONFIGURATION_PROVENANCE_COMMIT = (
    "059b4aa0809c8df28250dc47e3abfe7836f0938c"
)
SOURCE_AUTHORITY_REVIEW_COMMIT = (
    "74c4120fbfa1ade859dc32f61acdf567c139fe02"
)
PR61_REVIEW_COMMIT = "2c36e4aa06395d5075c348aab71d468fa099775f"
PR61_PRODUCTION_SOURCE_SHA256 = {
    "contracts/config/SwitchboardDelta.vy": (
        "12604c00353b2b4e7519ffd316883e1e64394af53dd79f2c9866765d7385eb79"
    ),
    "contracts/core/AuctionHouse.vy": (
        "e5a1603d27e22abc3fa0bf98971dbc16732afe8647b1fe323916216036998921"
    ),
    "contracts/core/Deleverage.vy": (
        "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138"
    ),
}
PR61_BASELINE_SOURCE_SHA256 = {
    "contracts/config/SwitchboardDelta.vy": (
        "2c76e1a2b985884adc2db1b419776eddf7bd6c355268dc527d573453421bfbe1"
    ),
    "contracts/core/AuctionHouse.vy": (
        "dc871e77efdf4320f98f5f4296dbe4c07689e434f9c4eae7c9ed971b85ee9cae"
    ),
    "contracts/core/Deleverage.vy": (
        "eb28c2d22a695c3148acfc00b54507d3b2f3e4462aeae119ba4183d09832815b"
    ),
}
PR61_DIRECT_RECORD_COUNT = 8
PR61_DIRECT_RECORDS_SHA256 = (
    "36df35fbdf7b17da04f9f27191e411b3cb44a93df145906b90ca6fa887315d36"
)
PR61_CADENCE_RECORD_COUNT = 16
PR61_CADENCE_RECORDS_SHA256 = (
    "81e512c04a0c791a00138bd874b74470a0f805be3c23b83b49df85f522188f2e"
)
PR61_SECONDS_RECORD_COUNT = 11
PR61_SECONDS_RECORDS_SHA256 = (
    "a8ee8276a6059a7d0907d272d4cc08e13f2e777e0be8889ea85d0fd9b42466c4"
)
PR61_PATH_RECORD_COUNT = 3
PR61_PATH_RECORDS_SHA256 = (
    "67ff2a2167be043054d066e81329c8ee260d2e64a395dba55a57a727f009343e"
)
H04_CADENCE_RECORD_COUNT = 116
H04_CADENCE_RECORDS_SHA256 = (
    "d0d0e3ca3ac472b1a709a9525e9ad38d5b76c5337b4e540c3ca10b7c0dcddf05"
)
H04_CAD_SITE_COUNT = 6
H04_CAD_SITES_SHA256 = (
    "8ffb9dd92c225d4cacea6827194bf3b42eb5cb2efaf6729f6aa1f083503f42ee"
)
# The H-04 constants above are immutable historical identities. The current
# source-authority batch replaces those JSON-first records with an exact,
# separately fingerprinted source-derived projection.
SOURCE_AUTHORITY_DIRECT_RECORD_COUNT = 3
SOURCE_AUTHORITY_DIRECT_RECORDS_SHA256 = (
    "223f29872a37ab6af14e2b25f560e94b112ce074c5d00f60454c253e36f88125"
)
SOURCE_AUTHORITY_CADENCE_RECORD_COUNT = 121
SOURCE_AUTHORITY_CADENCE_RECORDS_SHA256 = (
    "2ffc6436b552ecef9ab7c62d68c8cbc567a19b15144081643f4f02fb25d2a5e3"
)
SOURCE_AUTHORITY_SECONDS_RECORD_COUNT = 12
SOURCE_AUTHORITY_SECONDS_RECORDS_SHA256 = (
    "c16f93204ceab299209ba8daf2f97968f7535be49d8ef39a5bbf0680eb0f6ebc"
)
SOURCE_AUTHORITY_PATH_RECORD_COUNT = 1
SOURCE_AUTHORITY_PATH_RECORDS_SHA256 = (
    "31ffdb4ad933cc33f74b5897f1e7881de00d52428d86076c15cab88521f00137"
)
SOURCE_AUTHORITY_CAD_SITE_COUNT = 5
SOURCE_AUTHORITY_CAD_SITES_SHA256 = (
    "7bd4eb03d20abaf7b1776e7032b9c66a39fd3dae9975ebc1a3e688cf75140e7c"
)
EXPECTED_PRODUCTION_ROOTS = ["contracts"]
EXPECTED_EXCLUDED_PRODUCTION_GLOBS = [
    "contracts/mock/**",
    "contracts/testing/**",
]
EXPECTED_ALLOWED_NONPRODUCTION_GLOBS = [
    "tests/**",
    "contracts/mock/**",
    "contracts/testing/**",
]
# Exact non-production reference examples excluded from every clock count.
# Both the path and the content SHA-256 are frozen: adding, moving, or
# editing an excluded example requires a reviewed checker change.
EXCLUDED_CCIP_EXAMPLE_PATH = (
    "docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy"
)
EXCLUDED_CCIP_EXAMPLE_SHA256 = (
    "7f3b46af23b9456869b0a72578d3ae295cbfb8ff112d0f7bddd1d66a4afb1e18"
)
EXCLUDED_EXAMPLE_CONTENT_HASHES = {
    EXCLUDED_CCIP_EXAMPLE_PATH: EXCLUDED_CCIP_EXAMPLE_SHA256,
}
EXPECTED_INTERFACE_ROOTS = ["interfaces"]
EXPECTED_CADENCE_ROOTS = [
    "contracts",
    "config",
    "interfaces",
    "migrations",
    "migration_history",
    "scripts",
    "tests",
    "README.md",
]
EXPECTED_CADENCE_EXCLUDED_GLOBS = [
    "config/block-clock-inventory.json",
    "migration_history/base-mainnet/**",
    "scripts/check_block_clock_inventory.py",
    "tests/inventory/test_block_clock_inventory.py",
]
EXPECTED_REVIEW_AUTHORITIES = {
    "directOccurrences": "protocol/security",
    "timestampContext": "protocol/security",
    "cadenceCandidates": {
        "CAD-001": "risk/oracle",
        "other": "protocol/security",
    },
    "secondsUnitCandidates": "protocol/security",
    "allowedMixedClockFunctions": "protocol/security",
    "vyperPathClassifications": "engineering/tooling",
}
EXPECTED_REVIEW_PROVENANCE = {
    "track3ReviewCommit": TRACK3_REVIEW_COMMIT,
    "hardeningApprovalCommit": HARDENING_REVIEW_COMMIT,
    "pr61ReviewCommit": PR61_REVIEW_COMMIT,
    "sourceAuthorityReviewCommit": SOURCE_AUTHORITY_REVIEW_COMMIT,
}
S5_REVIEW_ARTIFACT_SHA256 = (
    "e2c7b92b3ca51f903e0cdb8eb5c5eda3d6c1f2e644a6ee424ea67fe8e8ea9a76"
)
S5_REVIEW_ARTIFACT_FIELD = "s5ReviewArtifactSha256"
S5_LEGACY_INVENTORY_SHA256 = (
    "924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4"
)
M2_GUARDED_ERC20_PATH = "contracts/vaults/GuardedErc20.vy"
M2_GUARDED_ERC20_SHA256 = (
    "0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed"
)
M3_CREDIT_ENGINE_PATH = "contracts/core/CreditEngine.vy"
M3_CREDIT_ENGINE_SHA256 = (
    "7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d"
)
# Exact pre-M3 CreditEngine ledger record content hash, used only to
# reconstruct the frozen S5 legacy fingerprint.  Any deviation from the one
# reviewed M3 record disables that reconstruction and fails closed.
M3_CREDIT_ENGINE_BASELINE_SHA256 = (
    "23129f8f6e87805bc47712d06f7ddf6c0de920866ad36ca78ee96e9c57ef96d8"
)
POST_S5_PRODUCTION_INVENTORY_SHA256 = (
    "07fc837ee5c9c56a4cf979c64e3d678753eeb6c263e4100d7a1f0cb4704f2122"
)
CURRENT_PRODUCTION_INVENTORY_SHA256 = (
    "a1f264788bf1189f554cd7a4952fada353c1d39afb02b032d6dfd145ae902ecb"
)
CURRENT_BINDINGS_SCHEMA_VERSION = 1
CURRENT_BINDINGS_STATE_SHA256 = (
    "f5809ea7953ced8ea5ec0526cad0c3a22713b1391bf1c745e2c4ab2f73305441"
)
EXPECTED_CURRENT_SOURCE_BINDINGS: tuple[Mapping[str, Any], ...] = (
    {
        "path": "contracts/mock/MockMorphoV2Factory.vy",
        "classification": "mock",
        "historicalContentSha256": None,
        "currentContentSha256": (
            "d4afb38408b542ef123ba5df453de8ed8a871116e85f916be983c934a0f4da60"
        ),
    },
    {
        "path": "contracts/mock/MockMorphoV2Vault.vy",
        "classification": "mock",
        "historicalContentSha256": None,
        "currentContentSha256": (
            "d5c84d5c58f996b5cad7db1928de3fc8b144fd6322beccaad86396ab3cab5dac"
        ),
    },
    {
        "path": "contracts/mock/MockYieldRegistry.vy",
        "classification": "mock",
        "historicalContentSha256": (
            "8c416252720cf6329dd739e445174458f86c5d47dd52ccc31e4cdde4a879a3a0"
        ),
        "currentContentSha256": (
            "b645e1bc1f9fdb036da47a508f54dac43e000b362463e095ddb434b358de7c5d"
        ),
    },
    {
        "path": "contracts/priceSources/BlueChipYieldPrices.vy",
        "classification": "production",
        "historicalContentSha256": (
            "077a51b7587ef6a3ceb87c920955160944274b3d4560abf098ce904b713d3b56"
        ),
        "currentContentSha256": (
            "abe188bf7edd973f6d68e58e39767e948471542030f6c2447ab98616c303e8be"
        ),
    },
)
EXPECTED_CURRENT_TIMESTAMP_BINDINGS: tuple[Mapping[str, Any], ...] = (
    {
        "id": "TS-004",
        "path": "contracts/priceSources/BlueChipYieldPrices.vy",
        "function": "_addPriceSnapshot",
        "normalizedExpression": "block.timestamp",
        "ordinalInFunction": 1,
        "historicalReviewedLine": 787,
        "currentLine": 914,
        "currentLineText": (
            "    if config.lastSnapshot.lastUpdate == block.timestamp:"
        ),
        "currentLineSha256": (
            "30c571ae6e9ac9dc525f53ca3d264eaee4ad0e30a8929d0df113ecb42f495ae3"
        ),
    },
    {
        "id": "TS-004",
        "path": "contracts/priceSources/BlueChipYieldPrices.vy",
        "function": "_addPriceSnapshot",
        "normalizedExpression": "block.timestamp",
        "ordinalInFunction": 2,
        "historicalReviewedLine": 791,
        "currentLine": 922,
        "currentLineText": (
            "        if not didAdd or nextSnapshotAt > block.timestamp:"
        ),
        "currentLineSha256": (
            "79164ed349a9ccb009cbc82ebc610255a02514ebacc2f8582bce5ffd12da51d9"
        ),
    },
    {
        "id": "TS-004",
        "path": "contracts/priceSources/BlueChipYieldPrices.vy",
        "function": "_getLatestSnapshot",
        "normalizedExpression": "block.timestamp",
        "ordinalInFunction": 1,
        "historicalReviewedLine": 848,
        "currentLine": 960,
        "currentLineText": "    currentTimestamp: uint256 = block.timestamp",
        "currentLineSha256": (
            "65ce5080501ffbf935fe37b404bdfb79352808b02a346518e3fd6324216c42a6"
        ),
    },
    {
        "id": "TS-004",
        "path": "contracts/priceSources/BlueChipYieldPrices.vy",
        "function": "_getWeightedPrice",
        "normalizedExpression": "block.timestamp",
        "ordinalInFunction": 1,
        "historicalReviewedLine": 750,
        "currentLine": 868,
        "currentLineText": "            if block.timestamp > staleAt:",
        "currentLineSha256": (
            "9d3d995977312a61f6a54cde9bc61e19ccdc4d13b32aa06d5fde76125c52c174"
        ),
    },
)
S5_REVIEW_DIRECT_KEYS = {
    ("contracts/data/Ledger.vy", "_getActionBlock", "block.number", 1),
}
S5_RECONCILED_DIRECT_KEYS = S5_REVIEW_DIRECT_KEYS | {
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "block.number",
        1,
    ),
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "block.number",
        2,
    ),
}
PROFILE1_CONFIGURATION_CADENCE_KEY = (
    "tests/deployment/test_robinhood_omissions.py",
    "test_profile1_predeployment_safety_envelope_is_atomic_and_fail_closed",
    "reviewed-cadence-identifier",
    "numBlocksPerInterval",
    '"numBlocksPerInterval",',
    1,
)
PROFILE1_CONFIGURATION_CADENCE_RECORD_COUNT = 1
PROFILE1_CONFIGURATION_CADENCE_RECORDS_SHA256 = (
    "9b799b5681ec1279eac6f3a44d0f3dc79babfeaf28bbd33064ab24954c11d118"
)
SOURCE_AUTHORITY_CADENCE_PATHS = frozenset(
    {
        "config/robinhood-parameters.json",
        "contracts/config/DefaultsRobinhood.vy",
        "scripts/abis/DefaultsRobinhood.json",
        "scripts/params/generate_robinhood_defaults.py",
        "tests/config/test_defaults_robinhood.py",
    }
)
SOURCE_AUTHORITY_BLUEPRINT_CADENCE_KEYS = frozenset(
    {
        (
            "config/BluePrint.py",
            "<module>",
            "block-default-key",
            '"timelock_base_headroom_blocks":',
            '"timelock_base_headroom_blocks": 366,',
            1,
        ),
        (
            "config/BluePrint.py",
            "<module>",
            "block-default-key",
            '"base_blocks_per_robinhood_block":',
            '"base_blocks_per_robinhood_block": 6,',
            1,
        ),
        (
            "config/BluePrint.py",
            "<module>",
            "reviewed-cadence-identifier",
            "numBlocksPerInterval",
            "'Deployment.DP-08.psm.numBlocksPerInterval': "
            "RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_"
            "NUMBLOCKSPERINTERVAL'), 'blocked'),",
            1,
        ),
        (
            "config/BluePrint.py",
            "<module>",
            "reviewed-cadence-identifier",
            "ripePerBlock",
            "'Deployment.DP-15.rewards.ripePerBlock': "
            "RobinhoodInput(SourceReference('Defaults.rewardsConfig."
            "ripePerBlock'), 'approved'),",
            1,
        ),
        (
            "config/BluePrint.py",
            "<module>",
            "reviewed-cadence-identifier",
            "ripePerBlock",
            "'Deployment.DP-15.rewards.ripePerBlock': "
            "RobinhoodInput(SourceReference('Defaults.rewardsConfig."
            "ripePerBlock'), 'approved'),",
            2,
        ),
    }
)
REVIEWER_REMEDIATION_CADENCE_KEYS = {
    PROFILE1_CONFIGURATION_CADENCE_KEY,
    (
        "config/contract-artifact-expectations.json",
        "<module>",
        "block-default-key",
        '"MIN_UNDERSCORE_SEND_INTERVAL":',
        '"MIN_UNDERSCORE_SEND_INTERVAL": {',
        1,
    ),
    (
        "config/contract-artifact-expectations.json",
        "<module>",
        "reviewed-cadence-identifier",
        "MIN_UNDERSCORE_SEND_INTERVAL",
        '"MIN_UNDERSCORE_SEND_INTERVAL": {',
        1,
    ),
    (
        "config/contract-artifact-expectations.json",
        "<module>",
        "block-default-key",
        '"underscoreSendInterval":',
        '"underscoreSendInterval": {',
        1,
    ),
    *{
        (
            "scripts/proposals/lootbox-deployment-profiles.json",
            "<module>",
            "block-default-key",
            '"underscore_send_interval":',
            '"underscore_send_interval": {',
            ordinal,
        )
        for ordinal in (1, 2, 3)
    },
    (
        "scripts/proposals/lootbox_deployment_profiles.py",
        "<module>",
        "block-default-key",
        '"underscore_send_interval":',
        '"underscore_send_interval": 0,',
        1,
    ),
    (
        "scripts/proposals/lootbox_deployment_profiles.py",
        "<module>",
        "block-default-key",
        '"underscore_send_interval":',
        '"underscore_send_interval": 43_200,',
        1,
    ),
    (
        "scripts/proposals/lootbox_deployment_profiles.py",
        "<module>",
        "block-default-key",
        '"underscore_send_interval":',
        '"underscore_send_interval": 0,',
        2,
    ),
}
REVIEWER_REMEDIATION_CADENCE_KEY_COUNT = 10
REVIEWER_REMEDIATION_CADENCE_KEYS_SHA256 = (
    "cb64d7b0dbd1d8e278b83b248ec7c457137a24a16aa7247cc2deab9fa9b5c4df"
)
PR61_ARTIFACT_EXPECTATIONS_PATH = "config/contract-artifact-expectations.json"
PR61_ARTIFACT_EXPECTATIONS_SHA256 = (
    "9f205beb9a1aadc2b4bab676d2c1e5277b576547a1e74e91818262f073815fe7"
)
CURRENT_ARTIFACT_EXPECTATIONS_SHA256 = (
    "267034af0256258ae7746e0912ce3f3753471f129845b2dd600e5e768c598ed4"
)
DEFAULTS_ROBINHOOD_ARTIFACT_RECORD_SHA256 = (
    "a6f847c6106d40b3b6f18d3cec90bca891f916c54a5d05c2b99dc75f79e001b9"
)
PR61_ARTIFACT_LAYOUT_METADATA_RECORD_COUNT = 8
PR61_ARTIFACT_LAYOUT_METADATA_RECORDS_SHA256 = (
    "ba0c2ed22b4a6647f89672ac55d945a2e4349350ce4bd343e3630a8294c21fbf"
)
PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORD_COUNT = 11
PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORDS_SHA256 = (
    "29713297c33a355261fd2958e2140a1ec5623e511469d929ff5df61affe82948"
)
PR61_ARTIFACT_LAYOUT_METADATA_CADENCE_KEYS = frozenset(
    {
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"lastDeleverageBlock":',
            '"lastDeleverageBlock": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"timeLock":',
            '"timeLock": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"MAX_ACTION_TIMELOCK":',
            '"MAX_ACTION_TIMELOCK": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"MIN_ACTION_TIMELOCK":',
            '"MIN_ACTION_TIMELOCK": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"govChangeTimeLock":',
            '"govChangeTimeLock": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"timeLock":',
            '"timeLock": {',
            2,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"actionTimeLock":',
            '"actionTimeLock": {',
            1,
        ),
        (
            PR61_ARTIFACT_EXPECTATIONS_PATH,
            "<module>",
            "block-default-key",
            '"expiration":',
            '"expiration": {',
            1,
        ),
    }
)
S5_REVIEW_CADENCE_KEYS = {
    (
        "contracts/data/Ledger.vy",
        "<module>",
        "cadence-comment",
        "per block",
        "# one action per block",
        1,
    ),
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "cadence-comment",
        "per block",
        "assert self.lastTouch[_user] != actionBlock # dev: one action per block",
        1,
    ),
    (
        "contracts/testing/ActionBlockIdentityProbe.vy",
        "readActionBlocks",
        "block-unit-identifier",
        "readActionBlocks",
        "def readActionBlocks() -> (uint256, uint256):",
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "preflight",
        "block-default-key",
        '"latest_block":',
        '"latest_block": {',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"child_block":',
        '"child_block": child,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"first_child_block":',
        '"first_child_block": first_block,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"second_child_block":',
        '"second_child_block": second_block,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"distinct_child_blocks":',
        '"distinct_child_blocks": len(set(arb_values)),',
        1,
    ),
    (
        "tests/core/creditEngine/test_credit_borrow.py",
        "test_borrow_guard_runs_before_credit_effects_and_rejects_second_action",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/creditEngine/test_credit_repay.py",
        "test_repay_low_risk_succeeds_between_checked_actions_and_rearms_guard",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_action_block.py",
        "test_external_housekeeping_valid_caller_can_select_victim_and_risk_flag",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_rebalance.py",
        "test_rebalance_after_effects_guard_rejection_rolls_back_every_leg",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_withdraw.py",
        "test_low_risk_deposit_arms_same_action_block_withdraw_rejection",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_withdraw.py",
        "test_checked_withdraw_rejects_second_same_action_block_and_rolls_back",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger.py",
        "test_ledger_check_and_update_last_touch_mixed_check_modes",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_identity_not_native_block_controls_equality",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_preserves_low_high_and_high_low_high_ordering",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_preserves_low_high_and_high_low_high_ordering",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        2,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_keeps_users_isolated_within_one_action_block",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_keeps_users_isolated_within_one_action_block",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        2,
    ),
    (
        "tests/probes/test_action_block_identity_probe.py",
        "test_probe_emits_native_and_arb_sys_values_from_compatible_double",
        "block-unit-identifier",
        "readActionBlocks",
        "native_view, arb_view = probe.readActionBlocks()",
        1,
    ),
    (
        "tests/vaults/modules/test_stab_vault_claims.py",
        "test_claim_after_effects_guard_rejection_rolls_back_second_claim",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
}
S5_RECONCILED_CADENCE_KEYS = S5_REVIEW_CADENCE_KEYS | {
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "cadence-comment",
        "per block",
        "assert self.lastTouch[_user] != block.number # dev: one action per block",
        1,
    ),
}
S5_REVIEW_PATHS = {"contracts/testing/ActionBlockIdentityProbe.vy"}
PLACEHOLDERS = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "not applicable",
    "placeholder",
    "skipped",
    "tbd",
    "todo",
    "unknown",
}
SOURCE_SUFFIXES = {".json", ".md", ".py", ".vy", ".vyi"}
VYPER_SUFFIXES = {".vy", ".vyi"}
DIRECT_PATTERN = re.compile(r"\bblock\s*\.\s*number\b")
TIMESTAMP_PATTERN = re.compile(r"\bblock\s*\.\s*timestamp\b")
FUNCTION_PATTERN = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_./]*)", re.MULTILINE
)
SECONDS_IDENTIFIER_PATTERN = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*_IN_SECONDS\b"
)
CADENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "block-unit-identifier",
        re.compile(
            r"\b(?:"
            r"[A-Z][A-Z0-9_]*_BLOCKS?|"
            r"[a-z][A-Za-z0-9_]*Blocks"
            r")\b"
        ),
    ),
    (
        "reviewed-cadence-identifier",
        re.compile(
            r"\b(?:MIN_UNDERSCORE_SEND_INTERVAL|ONE_DAY|staleBlocks|"
            r"numBlocksPerInterval|ripePerBlock|increasePerDangerBlock)\b"
        ),
    ),
    (
        "block-default-key",
        re.compile(
            r"""["'](?=[A-Za-z_][A-Za-z0-9_]*["']\s*:)[A-Za-z0-9_]*"""
            r"""(?:TIMELOCK|BLOCKS?|INTERVAL|DURATION|DELAY|EXPIRY|"""
            r"""EXPIRATION)["']\s*:""",
            re.IGNORECASE,
        ),
    ),
    (
        "cadence-comment",
        re.compile(
            r"(?:\b(?:Base|Robinhood)\b.{0,80}\bcadence\b|"
            r"\b\d+\s*(?:s|seconds?)\s*/\s*block\b|"
            r"\bblocks?\s+per\s+(?:day|hour|interval)\b|"
            r"\bper[- ]block\b)",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    code: str
    domain: str
    path: str = "-"
    function: str = "-"
    line: int = 0
    snippet: str = "-"
    candidate: str = "UNMAPPED"
    expected: str = "-"
    actual: str = "-"
    remediation: str = "obtain semantic review before updating the inventory"

    def render(self) -> str:
        snippet = json.dumps(self.snippet, ensure_ascii=True)
        remediation = json.dumps(self.remediation, ensure_ascii=True)
        return (
            f"CLOCK_INVENTORY_FAIL code={self.code} domain={self.domain} "
            f"path={self.path} function={self.function} line={self.line} "
            f"candidate={self.candidate} expected={self.expected} "
            f"actual={self.actual} snippet={snippet} remediation={remediation}"
        )


@dataclass(frozen=True)
class Occurrence:
    path: str
    function: str
    normalized_expression: str
    ordinal: int
    line: int
    column: int
    snippet: str

    @property
    def key(self) -> tuple[str, str, str, int]:
        return (
            self.path,
            self.function,
            self.normalized_expression,
            self.ordinal,
        )


@dataclass(frozen=True)
class Candidate:
    path: str
    function: str
    pattern: str
    matched_text: str
    normalized_snippet: str
    ordinal: int
    line: int
    classification: str

    @property
    def key(self) -> tuple[str, str, str, str, str, int]:
        return (
            self.path,
            self.function,
            self.pattern,
            self.matched_text,
            self.normalized_snippet,
            self.ordinal,
        )


@dataclass
class CheckResult:
    findings: list[Finding]
    success_lines: list[str]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def output(self) -> str:
        lines = (
            self.success_lines
            if self.ok
            else [finding.render() for finding in sorted(self.findings, key=_finding_key)]
        )
        return "\n".join(lines)


def _finding_key(finding: Finding) -> tuple[Any, ...]:
    return (
        finding.code,
        finding.domain,
        finding.path,
        finding.function,
        finding.line,
        finding.candidate,
        finding.snippet,
    )


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def _matches_glob(path: str, pattern: str) -> bool:
    if pattern.endswith("/**") and (
        path == pattern[:-3] or path.startswith(pattern[:-2])
    ):
        return True
    return fnmatch.fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern)


def classify_path(
    path: str,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    interface_roots: Sequence[str] = EXPECTED_INTERFACE_ROOTS,
    allowed_nonproduction_globs: Sequence[str] = EXPECTED_ALLOWED_NONPRODUCTION_GLOBS,
) -> str:
    if path in EXCLUDED_EXAMPLE_CONTENT_HASHES:
        return "excluded"
    for root in interface_roots:
        normalized_root = root.rstrip("/")
        if path == normalized_root or path.startswith(f"{normalized_root}/"):
            return "interface"
    for glob in allowed_nonproduction_globs:
        if not _matches_glob(path, glob):
            continue
        parts = PurePosixPath(glob.lower()).parts
        if "mock" in parts:
            return "mock"
        if "testing" in parts:
            return "testing"
        if "tests" in parts:
            return "test"
        return "excluded"
    for glob in excluded_production_globs:
        if not _matches_glob(path, glob):
            continue
        normalized_glob = glob.lower()
        if "mock" in PurePosixPath(normalized_glob).parts:
            return "mock"
        if "testing" in PurePosixPath(normalized_glob).parts:
            return "testing"
        return "excluded"
    for root in production_roots:
        normalized_root = root.rstrip("/")
        if path == normalized_root or path.startswith(f"{normalized_root}/"):
            return "production"
    if Path(path).suffix in VYPER_SUFFIXES:
        return "unclassified"
    if path.startswith("config/"):
        return "config"
    if path.startswith("migrations/"):
        return "migration"
    if path.startswith("scripts/"):
        return "tooling"
    return "other"


def _iter_files(root: Path, relative_roots: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for relative_root in relative_roots:
        base = root / relative_root
        if base.is_file():
            files.add(base)
        elif base.is_dir():
            for candidate in base.rglob("*"):
                if candidate.is_file() and not any(
                    part in {".git", ".hypothesis", ".pytest_cache", ".venv", "__pycache__", "out"}
                    for part in candidate.relative_to(root).parts
                ):
                    files.add(candidate)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _line_functions(lines: Sequence[str]) -> list[str]:
    current = "<module>"
    signature_depth = 0
    functions: list[str] = []
    for line in lines:
        match = FUNCTION_PATTERN.match(line)
        if match:
            current = match.group(1)
            signature_depth = line.count("(") - line.count(")")
        elif signature_depth:
            signature_depth += line.count("(") - line.count(")")
        elif line and not line[0].isspace():
            current = "<module>"
        functions.append(current)
    return functions


def _scan_expression_files(
    root: Path,
    paths: Iterable[Path],
    pattern: re.Pattern[str],
) -> list[Occurrence]:
    occurrences: list[Occurrence] = []
    ordinals: dict[tuple[str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            for match in pattern.finditer(line):
                normalized = _normalize_whitespace(match.group(0))
                ordinal_key = (relative, function, normalized)
                ordinal = ordinals.get(ordinal_key, 0) + 1
                ordinals[ordinal_key] = ordinal
                occurrences.append(
                    Occurrence(
                        path=relative,
                        function=function,
                        normalized_expression=normalized,
                        ordinal=ordinal,
                        line=line_number,
                        column=match.start() + 1,
                        snippet=_normalize_whitespace(line),
                    )
                )
    return occurrences


def _scan_fixed_counts(paths: Iterable[Path], needle: str) -> tuple[int, int, int]:
    occurrences = 0
    matching_lines = 0
    matching_files = 0
    for path in paths:
        text = _read_text(path)
        file_occurrences = text.count(needle)
        if file_occurrences:
            matching_files += 1
            occurrences += file_occurrences
            matching_lines += sum(1 for line in text.splitlines() if needle in line)
    return occurrences, matching_lines, matching_files


def _candidate_from_record(record: Mapping[str, Any]) -> tuple[str, str, str, str, str, int]:
    return (
        str(record.get("path", "")),
        str(record.get("function", "")),
        str(record.get("pattern", "")),
        str(record.get("matchedText", "")),
        str(record.get("normalizedSnippet", "")),
        int(record.get("ordinalInFunction", 0)),
    )


def _candidate_semantic_ids(record: Mapping[str, Any]) -> tuple[str, ...]:
    semantic_ids = record.get("semanticIds", [])
    if not isinstance(semantic_ids, list):
        return ()
    return tuple(sorted(str(item) for item in semantic_ids if str(item)))


def _candidate_label(record: Mapping[str, Any]) -> str:
    semantic_ids = _candidate_semantic_ids(record)
    if semantic_ids:
        return ",".join(semantic_ids)
    return str(record.get("reviewDomain", record.get("id", "UNMAPPED")))


def _key_set_fingerprint(keys: set[Any]) -> str:
    serialized = json.dumps(
        [list(key) if isinstance(key, tuple) else key for key in sorted(keys)],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _scan_candidates(
    root: Path,
    paths: Iterable[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    excluded_globs: Sequence[str],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    ordinals: dict[tuple[str, str, str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.suffix not in SOURCE_SUFFIXES or any(
            _matches_glob(relative, glob) for glob in excluded_globs
        ):
            continue
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            normalized_snippet = _normalize_whitespace(line)
            for pattern_name, pattern in CADENCE_PATTERNS:
                for match in pattern.finditer(line):
                    matched_text = _normalize_whitespace(match.group(0))
                    key = (
                        relative,
                        function,
                        pattern_name,
                        matched_text,
                        normalized_snippet,
                    )
                    ordinal = ordinals.get(key, 0) + 1
                    ordinals[key] = ordinal
                    candidates.append(
                        Candidate(
                            path=relative,
                            function=function,
                            pattern=pattern_name,
                            matched_text=matched_text,
                            normalized_snippet=normalized_snippet,
                            ordinal=ordinal,
                            line=line_number,
                            classification=classification,
                        )
                    )
    return candidates


def _scan_seconds_candidates(
    root: Path,
    paths: Iterable[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    excluded_globs: Sequence[str],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    ordinals: dict[tuple[str, str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.suffix not in SOURCE_SUFFIXES or any(
            _matches_glob(relative, glob) for glob in excluded_globs
        ):
            continue
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            normalized_snippet = _normalize_whitespace(line)
            for match in SECONDS_IDENTIFIER_PATTERN.finditer(line):
                matched_text = match.group(0)
                key = (relative, function, matched_text, normalized_snippet)
                ordinal = ordinals.get(key, 0) + 1
                ordinals[key] = ordinal
                candidates.append(
                    Candidate(
                        path=relative,
                        function=function,
                        pattern="seconds-unit-identifier",
                        matched_text=matched_text,
                        normalized_snippet=normalized_snippet,
                        ordinal=ordinal,
                        line=line_number,
                        classification=classification,
                    )
                )
    return candidates


def _record_key(record: Mapping[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(record.get("path", "")),
        str(record.get("function", "")),
        str(record.get("normalizedExpression", "")),
        int(record.get("ordinalInFunction", 0)),
    )


def _validate_s5_review_value(
    record: Mapping[str, Any],
    *,
    expected: bool,
    domain: str,
    candidate: str,
    findings: list[Finding],
) -> None:
    has_field = S5_REVIEW_ARTIFACT_FIELD in record
    value = record.get(S5_REVIEW_ARTIFACT_FIELD)
    if expected and value != S5_REVIEW_ARTIFACT_SHA256:
        findings.append(
            Finding(
                code="INV-SCHEMA-S5-PROVENANCE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=S5_REVIEW_ARTIFACT_SHA256,
                actual=json.dumps(value, sort_keys=True),
                remediation=(
                    "restore the exact lowercase frozen Gate 1 artifact SHA-256 "
                    "for this enumerated S5 reconciliation record"
                ),
            )
        )
    elif not expected and has_field:
        findings.append(
            Finding(
                code="INV-SCHEMA-S5-PROVENANCE-SCOPE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected="field-absent",
                actual=json.dumps(value, sort_keys=True),
                remediation=(
                    "remove S5 review provenance from records outside the exact "
                    "Gate 1 reconciliation set"
                ),
            )
        )


# The legacy-fingerprint exception is bound to the one reviewed CCIP record
# tuple; adding another path to EXCLUDED_EXAMPLE_CONTENT_HASHES does not
# remove that record from legacy fingerprint authority.
def _is_reviewed_ccip_excluded_record(record: Mapping[str, Any]) -> bool:
    return (
        str(record.get("path", "")) == EXCLUDED_CCIP_EXAMPLE_PATH
        and record.get("classification") == "excluded"
        and record.get("contentSha256") == EXCLUDED_CCIP_EXAMPLE_SHA256
    )


def _is_h04_cadence_path(path: str) -> bool:
    """Match only the three H-04 files with actual cadence candidates."""

    return (
        path == "config/robinhood-parameters.json"
        or path == "scripts/params/generate_robinhood_defaults.py"
        or path == "tests/config/test_defaults_robinhood.py"
    )


def _h04_cadence_records(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if _is_h04_cadence_path(str(record.get("path", "")))
    ]


def _h04_cad_sites(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        site
        for record in data["indirectCadence"]
        for site in record.get("sites", [])
        if isinstance(site, Mapping)
        and _is_h04_cadence_path(str(site.get("path", "")))
    ]


def _source_authority_direct_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["directOccurrences"]
        if str(record.get("path", ""))
        == "contracts/config/DefaultsRobinhood.vy"
    ]


def _source_authority_cadence_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if str(record.get("path", "")) in SOURCE_AUTHORITY_CADENCE_PATHS
        or _candidate_from_record(record)
        in SOURCE_AUTHORITY_BLUEPRINT_CADENCE_KEYS
    ]


def _source_authority_seconds_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["secondsUnitCandidates"]
        if str(record.get("path", ""))
        == "contracts/config/DefaultsRobinhood.vy"
    ]


def _source_authority_path_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["vyperPathClassifications"]
        if str(record.get("path", ""))
        == "contracts/config/DefaultsRobinhood.vy"
    ]


def _source_authority_cad_sites(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        site
        for record in data["indirectCadence"]
        for site in record.get("sites", [])
        if isinstance(site, Mapping)
        and str(site.get("path", "")) in SOURCE_AUTHORITY_CADENCE_PATHS
    ]


def _is_exact_source_authority_batch(data: Mapping[str, Any]) -> bool:
    direct = _source_authority_direct_records(data)
    cadence = _source_authority_cadence_records(data)
    seconds = _source_authority_seconds_records(data)
    paths = _source_authority_path_records(data)
    sites = _source_authority_cad_sites(data)
    return (
        len(direct) == SOURCE_AUTHORITY_DIRECT_RECORD_COUNT
        and _records_fingerprint(direct)
        == SOURCE_AUTHORITY_DIRECT_RECORDS_SHA256
        and len(cadence) == SOURCE_AUTHORITY_CADENCE_RECORD_COUNT
        and _records_fingerprint(cadence)
        == SOURCE_AUTHORITY_CADENCE_RECORDS_SHA256
        and len(seconds) == SOURCE_AUTHORITY_SECONDS_RECORD_COUNT
        and _records_fingerprint(seconds)
        == SOURCE_AUTHORITY_SECONDS_RECORDS_SHA256
        and len(paths) == SOURCE_AUTHORITY_PATH_RECORD_COUNT
        and _records_fingerprint(paths)
        == SOURCE_AUTHORITY_PATH_RECORDS_SHA256
        and len(sites) == SOURCE_AUTHORITY_CAD_SITE_COUNT
        and _records_fingerprint(sites) == SOURCE_AUTHORITY_CAD_SITES_SHA256
    )


def _exact_source_authority_record_fingerprints(
    data: Mapping[str, Any],
) -> tuple[
    frozenset[str],
    frozenset[str],
    frozenset[str],
    frozenset[str],
    frozenset[str],
]:
    if not _is_exact_source_authority_batch(data):
        return (frozenset(),) * 5
    return (
        frozenset(
            _record_fingerprint(record)
            for record in _source_authority_direct_records(data)
        ),
        frozenset(
            _record_fingerprint(record)
            for record in _source_authority_cadence_records(data)
        ),
        frozenset(
            _record_fingerprint(record)
            for record in _source_authority_seconds_records(data)
        ),
        frozenset(
            _record_fingerprint(record)
            for record in _source_authority_path_records(data)
        ),
        frozenset(
            _record_fingerprint(site)
            for site in _source_authority_cad_sites(data)
        ),
    )


def _records_fingerprint(records: Sequence[Mapping[str, Any]]) -> str:
    encoded = (
        json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_fingerprint(record: Mapping[str, Any]) -> str:
    return _records_fingerprint([record])


PR61_CADENCE_PATHS = frozenset(
    {
        "contracts/config/SwitchboardDelta.vy",
        "contracts/core/Deleverage.vy",
        "scripts/abis/SwitchboardDelta.json",
        "tests/config/test_switchboard_delta.py",
    }
)
PR61_NEW_CONSTRUCTOR_CADENCE_KEY = (
    "contracts/core/Deleverage.vy",
    "__init__",
    "block-unit-identifier",
    "MAX_COOLDOWN_BLOCKS",
    "assert _deleverageCooldown <= MAX_COOLDOWN_BLOCKS # dev: cooldown too large",
    1,
)
PR61_REMOVED_TEST_CADENCE_KEY = (
    "tests/core/deleverage/test_deleverage_for_withdrawal.py",
    "test_set_deleverage_cooldown_rejects_over_max",
    "block-unit-identifier",
    "MAX_COOLDOWN_BLOCKS",
    '"""Test that setDeleverageCooldown rejects values over '
    'MAX_COOLDOWN_BLOCKS (7_200)"""',
    1,
)
PR61_DIRECT_BASELINE_LINES = {
    (
        "contracts/config/SwitchboardDelta.vy",
        "setStartEpochAtBlock",
        "block.number",
        1,
    ): 915,
    (
        "contracts/core/AuctionHouse.vy",
        "_createOrUpdateFungAuction",
        "block.number",
        1,
    ): 917,
    (
        "contracts/core/AuctionHouse.vy",
        "_buyFungibleAuction",
        "block.number",
        1,
    ): 1100,
    (
        "contracts/core/AuctionHouse.vy",
        "_buyFungibleAuction",
        "block.number",
        2,
    ): 1100,
    (
        "contracts/core/AuctionHouse.vy",
        "_buyFungibleAuction",
        "block.number",
        3,
    ): 1119,
    (
        "contracts/core/Deleverage.vy",
        "deleverageForWithdrawal",
        "block.number",
        1,
    ): 520,
    (
        "contracts/core/Deleverage.vy",
        "deleverageForWithdrawal",
        "block.number",
        2,
    ): 520,
    (
        "contracts/core/Deleverage.vy",
        "deleverageForWithdrawal",
        "block.number",
        3,
    ): 583,
}
PR61_CADENCE_BASELINE_LINES = {
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "block-unit-identifier",
        "restartDelayBlocks",
        "restartDelayBlocks: uint256",
        1,
    ): 217,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "block-unit-identifier",
        "MAX_COOLDOWN_BLOCKS",
        "MAX_COOLDOWN_BLOCKS: constant(uint256) = 7_200 # ~1 day at 12s/block",
        1,
    ): 447,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "cadence-comment",
        "12s/block",
        "MAX_COOLDOWN_BLOCKS: constant(uint256) = 7_200 # ~1 day at 12s/block",
        1,
    ): 447,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setDeleverageCooldown",
        "block-unit-identifier",
        "MAX_COOLDOWN_BLOCKS",
        "assert _blocks <= MAX_COOLDOWN_BLOCKS # dev: cooldown too large",
        1,
    ): 605,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setRipeBondConfig",
        "block-unit-identifier",
        "restartDelayBlocks",
        "restartDelayBlocks=_restartDelayBlocks,",
        1,
    ): 874,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setRipeBondConfig",
        "block-unit-identifier",
        "restartDelayBlocks",
        "restartDelayBlocks=_restartDelayBlocks,",
        2,
    ): 885,
    (
        "contracts/config/SwitchboardDelta.vy",
        "executePendingAction",
        "block-unit-identifier",
        "restartDelayBlocks",
        "config.restartDelayBlocks = p.restartDelayBlocks",
        1,
    ): 1288,
    (
        "contracts/config/SwitchboardDelta.vy",
        "executePendingAction",
        "block-unit-identifier",
        "restartDelayBlocks",
        "config.restartDelayBlocks = p.restartDelayBlocks",
        2,
    ): 1288,
    (
        "contracts/core/Deleverage.vy",
        "<module>",
        "block-unit-identifier",
        "MAX_COOLDOWN_BLOCKS",
        "MAX_COOLDOWN_BLOCKS: constant(uint256) = 7_200 # ~1 day at 12s/block",
        1,
    ): 195,
    (
        "contracts/core/Deleverage.vy",
        "<module>",
        "cadence-comment",
        "12s/block",
        "MAX_COOLDOWN_BLOCKS: constant(uint256) = 7_200 # ~1 day at 12s/block",
        1,
    ): 195,
    (
        "scripts/abis/SwitchboardDelta.json",
        "<module>",
        "block-unit-identifier",
        "restartDelayBlocks",
        '"name": "restartDelayBlocks",',
        2,
    ): 2788,
    (
        "tests/config/test_switchboard_delta.py",
        "test_set_deleverage_cooldown_rejects_over_max",
        "block-unit-identifier",
        "MAX_COOLDOWN_BLOCKS",
        '"""Test that setDeleverageCooldown rejects values over '
        'MAX_COOLDOWN_BLOCKS (7_200)"""',
        1,
    ): 2717,
}
PR61_SECONDS_BASELINE_LINES = {
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "DAY_IN_SECONDS",
        "DAY_IN_SECONDS: constant(uint256) = 60 * 60 * 24",
        1,
    ): 451,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "DAY_IN_SECONDS",
        "WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS",
        1,
    ): 452,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "WEEK_IN_SECONDS",
        "WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS",
        1,
    ): 452,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "DAY_IN_SECONDS",
        "MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS",
        1,
    ): 453,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "MONTH_IN_SECONDS",
        "MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS",
        1,
    ): 453,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "DAY_IN_SECONDS",
        "YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS",
        1,
    ): 454,
    (
        "contracts/config/SwitchboardDelta.vy",
        "<module>",
        "seconds-unit-identifier",
        "YEAR_IN_SECONDS",
        "YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS",
        1,
    ): 454,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setMinCliffLength",
        "seconds-unit-identifier",
        "WEEK_IN_SECONDS",
        "assert _minCliffLength > WEEK_IN_SECONDS # dev: invalid min cliff length",
        1,
    ): 674,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setMaxStartDelay",
        "seconds-unit-identifier",
        "MONTH_IN_SECONDS",
        "assert _maxStartDelay <= 3 * MONTH_IN_SECONDS # dev: invalid max start delay",
        1,
    ): 686,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setVestingLengthBoundaries",
        "seconds-unit-identifier",
        "MONTH_IN_SECONDS",
        "assert _minVestingLength > MONTH_IN_SECONDS # dev: invalid min vesting length",
        1,
    ): 699,
    (
        "contracts/config/SwitchboardDelta.vy",
        "setVestingLengthBoundaries",
        "seconds-unit-identifier",
        "YEAR_IN_SECONDS",
        "assert _maxVestingLength <= 5 * YEAR_IN_SECONDS # dev: invalid max vesting length",
        1,
    ): 700,
}


def _pr61_direct_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["directOccurrences"]
        if str(record.get("path", "")) in PR61_PRODUCTION_SOURCE_SHA256
    ]


def _pr61_cadence_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if str(record.get("path", "")) in PR61_CADENCE_PATHS
    ]


def _pr61_seconds_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["secondsUnitCandidates"]
        if str(record.get("path", ""))
        == "contracts/config/SwitchboardDelta.vy"
    ]


def _pr61_path_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["vyperPathClassifications"]
        if str(record.get("path", "")) in PR61_PRODUCTION_SOURCE_SHA256
    ]


def _is_exact_pr61_reconciliation(data: Mapping[str, Any]) -> bool:
    direct_records = _pr61_direct_records(data)
    cadence_records = _pr61_cadence_records(data)
    seconds_records = _pr61_seconds_records(data)
    path_records = _pr61_path_records(data)
    removed_test_present = any(
        _candidate_from_record(record) == PR61_REMOVED_TEST_CADENCE_KEY
        for record in data["cadenceCandidates"]
    )
    return (
        data.get("reviewProvenance") == EXPECTED_REVIEW_PROVENANCE
        and len(direct_records) == PR61_DIRECT_RECORD_COUNT
        and _records_fingerprint(direct_records)
        == PR61_DIRECT_RECORDS_SHA256
        and len(cadence_records) == PR61_CADENCE_RECORD_COUNT
        and _records_fingerprint(cadence_records)
        == PR61_CADENCE_RECORDS_SHA256
        and len(seconds_records) == PR61_SECONDS_RECORD_COUNT
        and _records_fingerprint(seconds_records)
        == PR61_SECONDS_RECORDS_SHA256
        and len(path_records) == PR61_PATH_RECORD_COUNT
        and _records_fingerprint(path_records) == PR61_PATH_RECORDS_SHA256
        and not removed_test_present
    )


def _pr61_artifact_layout_metadata_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if _candidate_from_record(record)
        in PR61_ARTIFACT_LAYOUT_METADATA_CADENCE_KEYS
    ]


def _pr61_artifact_expectations_cadence_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if str(record.get("path", "")) == PR61_ARTIFACT_EXPECTATIONS_PATH
    ]


def _profile1_configuration_cadence_records(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if _candidate_from_record(record)
        == PROFILE1_CONFIGURATION_CADENCE_KEY
    ]


def _is_exact_reviewer_remediation_cadence_registry(
    data: Mapping[str, Any],
) -> bool:
    profile1_records = _profile1_configuration_cadence_records(data)
    return (
        len(REVIEWER_REMEDIATION_CADENCE_KEYS)
        == REVIEWER_REMEDIATION_CADENCE_KEY_COUNT
        and _key_set_fingerprint(set(REVIEWER_REMEDIATION_CADENCE_KEYS))
        == REVIEWER_REMEDIATION_CADENCE_KEYS_SHA256
        and len(profile1_records)
        == PROFILE1_CONFIGURATION_CADENCE_RECORD_COUNT
        and _records_fingerprint(profile1_records)
        == PROFILE1_CONFIGURATION_CADENCE_RECORDS_SHA256
    )


def _is_exact_pr61_artifact_layout_metadata(
    data: Mapping[str, Any],
    root: Path = ROOT,
) -> bool:
    records = _pr61_artifact_layout_metadata_records(data)
    path_records = _pr61_artifact_expectations_cadence_records(data)
    artifact_path = root / PR61_ARTIFACT_EXPECTATIONS_PATH
    try:
        artifact_bytes = artifact_path.read_bytes()
        artifact_data = json.loads(artifact_bytes)
        defaults_record = artifact_data["contracts"]["DefaultsRobinhood"]
        legacy_projection = copy.deepcopy(artifact_data)
        legacy_projection["contracts"].pop("DefaultsRobinhood")
        legacy_bytes = (
            json.dumps(legacy_projection, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return False
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    legacy_sha256 = hashlib.sha256(legacy_bytes).hexdigest()
    return (
        _is_exact_pr61_reconciliation(data)
        and _is_exact_reviewer_remediation_cadence_registry(data)
        and set(artifact_data["contracts"])
        == {
            "AuctionHouse",
            "CreditEngine",
            "Deleverage",
            "DefaultsRobinhood",
            "GuardedErc20",
            "Ledger",
            "Lootbox",
            "SwitchboardDelta",
            "Teller",
        }
        and legacy_sha256 == PR61_ARTIFACT_EXPECTATIONS_SHA256
        and artifact_sha256 == CURRENT_ARTIFACT_EXPECTATIONS_SHA256
        and _record_fingerprint(defaults_record)
        == DEFAULTS_ROBINHOOD_ARTIFACT_RECORD_SHA256
        and len(records) == PR61_ARTIFACT_LAYOUT_METADATA_RECORD_COUNT
        and _records_fingerprint(records)
        == PR61_ARTIFACT_LAYOUT_METADATA_RECORDS_SHA256
        and len(path_records)
        == PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORD_COUNT
        and _records_fingerprint(path_records)
        == PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORDS_SHA256
    )


def _pr61_baseline_setter_record() -> dict[str, Any]:
    return {
        "path": "contracts/core/Deleverage.vy",
        "function": "setDeleverageCooldown",
        "pattern": "block-unit-identifier",
        "matchedText": "MAX_COOLDOWN_BLOCKS",
        "normalizedSnippet": (
            "assert _blocks <= MAX_COOLDOWN_BLOCKS # dev: cooldown too large"
        ),
        "ordinalInFunction": 1,
        "reviewedLine": 1227,
        "classification": "production",
        "semanticIds": [],
        "reviewDomain": "cadence-surface",
        "semanticReview": {
            "owner": "protocol/security",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _pr61_removed_test_record() -> dict[str, Any]:
    return {
        "path": "tests/core/deleverage/test_deleverage_for_withdrawal.py",
        "function": "test_set_deleverage_cooldown_rejects_over_max",
        "pattern": "block-unit-identifier",
        "matchedText": "MAX_COOLDOWN_BLOCKS",
        "normalizedSnippet": (
            '"""Test that setDeleverageCooldown rejects values over '
            'MAX_COOLDOWN_BLOCKS (7_200)"""'
        ),
        "ordinalInFunction": 1,
        "reviewedLine": 3348,
        "classification": "test",
        "semanticIds": [],
        "reviewDomain": "cadence-surface",
        "semanticReview": {
            "owner": "protocol/security",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _restore_pr61_legacy_inventory(legacy: dict[str, Any]) -> None:
    for record in legacy["directOccurrences"]:
        baseline_line = PR61_DIRECT_BASELINE_LINES.get(_record_key(record))
        if baseline_line is not None:
            record["reviewedLine"] = baseline_line

    restored_cadence: list[dict[str, Any]] = []
    for record in legacy["cadenceCandidates"]:
        key = _candidate_from_record(record)
        if key == PR61_NEW_CONSTRUCTOR_CADENCE_KEY:
            restored_cadence.append(_pr61_baseline_setter_record())
            continue
        baseline_line = PR61_CADENCE_BASELINE_LINES.get(key)
        if baseline_line is not None:
            record["reviewedLine"] = baseline_line
        restored_cadence.append(record)
    insert_at = next(
        (
            index
            for index, record in enumerate(restored_cadence)
            if str(record.get("path", ""))
            == "tests/core/endaoment/test_endaoment_psm_config.py"
        ),
        len(restored_cadence),
    )
    restored_cadence.insert(insert_at, _pr61_removed_test_record())
    legacy["cadenceCandidates"] = restored_cadence

    for record in legacy["secondsUnitCandidates"]:
        baseline_line = PR61_SECONDS_BASELINE_LINES.get(
            _candidate_from_record(record)
        )
        if baseline_line is not None:
            record["reviewedLine"] = baseline_line

    for record in legacy["vyperPathClassifications"]:
        path = str(record.get("path", ""))
        if path in PR61_BASELINE_SOURCE_SHA256:
            record["contentSha256"] = PR61_BASELINE_SOURCE_SHA256[path]
            record["semanticReview"]["commit"] = HARDENING_REVIEW_COMMIT

    legacy["reviewProvenance"].pop("pr61ReviewCommit", None)


def _is_exact_h04_cadence_batch(data: Mapping[str, Any]) -> bool:
    records = _h04_cadence_records(data)
    sites = _h04_cad_sites(data)
    return (
        len(records) == H04_CADENCE_RECORD_COUNT
        and _records_fingerprint(records) == H04_CADENCE_RECORDS_SHA256
        and len(sites) == H04_CAD_SITE_COUNT
        and _records_fingerprint(sites) == H04_CAD_SITES_SHA256
    )


def _exact_reviewed_h04_record_fingerprints(
    data: Mapping[str, Any],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return exact tuple authority only for the fully frozen reviewed batch."""

    if not _is_exact_h04_cadence_batch(data):
        return frozenset(), frozenset()
    return (
        frozenset(
            _record_fingerprint(record)
            for record in _h04_cadence_records(data)
        ),
        frozenset(
            _record_fingerprint(site) for site in _h04_cad_sites(data)
        ),
    )


def _is_reviewed_m2_production_record(record: Mapping[str, Any]) -> bool:
    return dict(record) == {
        "path": M2_GUARDED_ERC20_PATH,
        "classification": "production",
        "contentSha256": M2_GUARDED_ERC20_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _is_reviewed_m3_production_record(record: Mapping[str, Any]) -> bool:
    return dict(record) == {
        "path": M3_CREDIT_ENGINE_PATH,
        "classification": "production",
        "contentSha256": M3_CREDIT_ENGINE_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


# CreditEngine predates S5, so its exact pre-M3 record is part of the frozen
# legacy fingerprint.  The reviewed M3 record is substituted back to the exact
# baseline record for that computation only; any other CreditEngine record is
# left in place so the legacy fingerprint fails closed.
def _m3_baseline_credit_engine_record() -> dict[str, Any]:
    return {
        "path": M3_CREDIT_ENGINE_PATH,
        "classification": "production",
        "contentSha256": M3_CREDIT_ENGINE_BASELINE_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _s5_legacy_inventory_fingerprint(
    data: Mapping[str, Any],
    root: Path = ROOT,
) -> str:
    (
        exact_source_direct,
        exact_source_cadence,
        exact_source_seconds,
        exact_source_paths,
        exact_source_sites,
    ) = (
        _exact_source_authority_record_fingerprints(data)
    )
    exact_pr61_reconciliation = _is_exact_pr61_reconciliation(data)
    exact_pr61_artifact_metadata = _is_exact_pr61_artifact_layout_metadata(
        data, root
    )
    exact_reviewer_remediation_keys = (
        REVIEWER_REMEDIATION_CADENCE_KEYS
        if _is_exact_reviewer_remediation_cadence_registry(data)
        else frozenset()
    )
    exact_pr61_artifact_metadata_keys = (
        PR61_ARTIFACT_LAYOUT_METADATA_CADENCE_KEYS
        if exact_pr61_artifact_metadata
        else frozenset()
    )
    legacy = copy.deepcopy(dict(data))
    if exact_pr61_reconciliation:
        _restore_pr61_legacy_inventory(legacy)
    # currentBindings is an additive live-source identity layer. It is never
    # part of the immutable historical serialization or its fingerprint.
    legacy.pop("currentBindings", None)
    legacy.pop("expectedProductionCounts", None)
    if exact_source_cadence:
        legacy["reviewProvenance"].pop(
            "sourceAuthorityReviewCommit", None
        )
    legacy["directOccurrences"] = [
        record
        for record in legacy["directOccurrences"]
        if _record_key(record) not in S5_RECONCILED_DIRECT_KEYS
        and _record_fingerprint(record) not in exact_source_direct
    ]
    legacy["cadenceCandidates"] = [
        record
        for record in legacy["cadenceCandidates"]
        if _candidate_from_record(record)
        not in (
            S5_RECONCILED_CADENCE_KEYS
            | exact_reviewer_remediation_keys
            | exact_pr61_artifact_metadata_keys
        )
        and _record_fingerprint(record) not in exact_source_cadence
    ]
    legacy["secondsUnitCandidates"] = [
        record
        for record in legacy["secondsUnitCandidates"]
        if _record_fingerprint(record) not in exact_source_seconds
    ]
    if exact_source_sites:
        for record in legacy["indirectCadence"]:
            record["sites"] = [
                site
                for site in record["sites"]
                if _record_fingerprint(site) not in exact_source_sites
            ]
    legacy["vyperPathClassifications"] = [
        _m3_baseline_credit_engine_record()
        if _is_reviewed_m3_production_record(record)
        else record
        for record in legacy["vyperPathClassifications"]
        if str(record.get("path", "")) not in S5_REVIEW_PATHS
        and not _is_reviewed_ccip_excluded_record(record)
        and not _is_reviewed_m2_production_record(record)
        and _record_fingerprint(record) not in exact_source_paths
    ]
    encoded = (
        json.dumps(legacy, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _post_s5_production_inventory_fingerprint(
    data: Mapping[str, Any],
) -> str:
    records = [
        record
        for record in data["vyperPathClassifications"]
        if record.get("classification") == "production"
    ]
    encoded = (
        json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _check_post_s5_production_inventory_fingerprint(
    data: Mapping[str, Any],
) -> list[Finding]:
    fingerprint = _post_s5_production_inventory_fingerprint(data)
    if fingerprint == CURRENT_PRODUCTION_INVENTORY_SHA256:
        return []
    return [
        Finding(
            code="INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
            domain="schema",
            expected=CURRENT_PRODUCTION_INVENTORY_SHA256,
            actual=fingerprint,
            remediation=(
                "restore the exact current production-classification ledger "
                "or obtain review for a new controlling fingerprint"
            ),
        )
    ]


def _validate_s5_review_provenance(
    data: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    direct_records = data["directOccurrences"]
    cadence_records = data["cadenceCandidates"]
    path_records = data["vyperPathClassifications"]

    direct_keys = {_record_key(record) for record in direct_records}
    cadence_keys = {_candidate_from_record(record) for record in cadence_records}
    path_keys = {str(record.get("path", "")) for record in path_records}
    for domain, expected, actual in (
        ("direct", S5_REVIEW_DIRECT_KEYS, direct_keys),
        ("cadence", S5_REVIEW_CADENCE_KEYS, cadence_keys),
        ("classification", S5_REVIEW_PATHS, path_keys),
    ):
        missing = expected - actual
        if missing:
            findings.append(
                Finding(
                    code="INV-SCHEMA-S5-SET",
                    domain=domain,
                    candidate=f"missing={len(missing)}",
                    expected=_key_set_fingerprint(expected),
                    actual=_key_set_fingerprint(actual & expected),
                    remediation=(
                        "restore every exact record covered by the 28 reviewed "
                        "S5 inventory dispositions"
                    ),
                )
            )

    for record in direct_records:
        key = _record_key(record)
        _validate_s5_review_value(
            record,
            expected=key in S5_REVIEW_DIRECT_KEYS,
            domain="direct",
            candidate=str(record.get("id", "UNMAPPED")),
            findings=findings,
        )
    for record in cadence_records:
        key = _candidate_from_record(record)
        _validate_s5_review_value(
            record,
            expected=key in S5_REVIEW_CADENCE_KEYS,
            domain="cadence",
            candidate=_candidate_label(record),
            findings=findings,
        )
    for record in path_records:
        path = str(record.get("path", ""))
        _validate_s5_review_value(
            record,
            expected=path in S5_REVIEW_PATHS,
            domain="classification",
            candidate=path,
            findings=findings,
        )
    for domain, collection in (
        ("indirect", data["indirectCadence"]),
        ("timestamp", data["timestampContext"]),
        ("seconds", data["secondsUnitCandidates"]),
        ("mixed", data["allowedMixedClockFunctions"]),
    ):
        for record in collection:
            _validate_s5_review_value(
                record,
                expected=False,
                domain=domain,
                candidate=str(record.get("id", _candidate_label(record))),
                findings=findings,
            )


def _check_s5_legacy_inventory_fingerprint(
    data: Mapping[str, Any],
    root: Path = ROOT,
) -> list[Finding]:
    fingerprint = _s5_legacy_inventory_fingerprint(data, root)
    if fingerprint == S5_LEGACY_INVENTORY_SHA256:
        return []
    return [
        Finding(
            code="INV-SCHEMA-S5-LEGACY-FINGERPRINT",
            domain="schema",
            expected=S5_LEGACY_INVENTORY_SHA256,
            actual=fingerprint,
            remediation=(
                "restore every inventory byte outside the exact S5 "
                "reconciliation set"
            ),
        )
    ]


def _placeholder(value: Any) -> bool:
    return not isinstance(value, str) or value.strip().lower() in PLACEHOLDERS


def _validate_semantic_review(
    record: Mapping[str, Any],
    domain: str,
    candidate: str,
    findings: list[Finding],
    expected_owner: str | None = None,
    expected_commit: str | None = None,
) -> None:
    review = record.get("semanticReview")
    if not isinstance(review, Mapping):
        findings.append(
            Finding(
                code="INV-SCHEMA-REVIEW",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                actual="missing",
                remediation="add the immutable reviewed owner, status, and commit",
            )
        )
        return
    if expected_owner is not None and review.get("owner") != expected_owner:
        findings.append(
            Finding(
                code="INV-SCHEMA-OWNER",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=expected_owner,
                actual=str(review.get("owner", "missing")),
                remediation="restore the approved semantic-review authority",
            )
        )
    if expected_commit is not None and review.get("commit") != expected_commit:
        findings.append(
            Finding(
                code="INV-SCHEMA-PROVENANCE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=expected_commit,
                actual=str(review.get("commit", "missing")),
                remediation="restore the immutable commit that actually reviewed this record",
            )
        )
    for field in ("owner", "status", "commit"):
        value = review.get(field)
        invalid = _placeholder(value)
        if field == "commit" and isinstance(value, str):
            invalid = invalid or re.fullmatch(r"[0-9a-f]{40}", value) is None
        if invalid:
            findings.append(
                Finding(
                    code="INV-SCHEMA-PLACEHOLDER",
                    domain=domain,
                    path=str(record.get("path", "-")),
                    candidate=candidate,
                    expected=f"reviewed-{field}",
                    actual=json.dumps(value, sort_keys=True),
                    remediation="obtain the named semantic owner's review; do not self-approve",
                )
            )
    status = str(review.get("status", "")).strip().lower()
    if status == "ignore":
        justification = review.get("justification")
        if _placeholder(justification):
            findings.append(
                Finding(
                    code="INV-SCHEMA-IGNORE",
                    domain=domain,
                    path=str(record.get("path", "-")),
                    candidate=candidate,
                    actual="ignore-without-reviewed-justification",
                    remediation="obtain semantic-owner review and a non-placeholder justification",
                )
            )
    elif status != "reviewed":
        findings.append(
            Finding(
                code="INV-SCHEMA-STATUS",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected="reviewed",
                actual=status or "missing",
                remediation="obtain semantic-owner review; skipped or invented statuses are invalid",
            )
        )


def _load_inventory(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [
            Finding(
                code="INV-SCHEMA-READ",
                domain="schema",
                path=path.as_posix(),
                actual=type(exc).__name__,
                remediation="restore the reviewed inventory file",
            )
        ]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [
            Finding(
                code="INV-SCHEMA-JSON",
                domain="schema",
                path=path.as_posix(),
                line=exc.lineno,
                actual=exc.msg.replace(" ", "_"),
                remediation="repair JSON without changing semantic classifications",
            )
        ]
    if not isinstance(data, dict):
        return None, [
            Finding(
                code="INV-SCHEMA-TYPE",
                domain="schema",
                path=path.as_posix(),
                expected="object",
                actual=type(data).__name__,
            )
        ]
    return data, []


def _current_binding_timestamp_key(
    record: Mapping[str, Any],
) -> tuple[str, str, str, int]:
    try:
        ordinal = int(record.get("ordinalInFunction", 0))
    except (TypeError, ValueError):
        ordinal = 0
    return (
        str(record.get("path", "")),
        str(record.get("function", "")),
        str(record.get("normalizedExpression", "")),
        ordinal,
    )


def _current_bindings_payload(bindings: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": bindings.get("schemaVersion"),
        "sourcePaths": bindings.get("sourcePaths"),
        "timestampLines": bindings.get("timestampLines"),
    }


def _current_bindings_fingerprint(bindings: Mapping[str, Any]) -> str:
    encoded = (
        json.dumps(
            _current_bindings_payload(bindings),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_current_bindings(
    data: Mapping[str, Any], root: Path
) -> list[Finding]:
    findings: list[Finding] = []
    bindings = data.get("currentBindings")
    if not isinstance(bindings, Mapping):
        return [
            Finding(
                code="INV-SCHEMA-CURRENT-BINDINGS",
                domain="schema",
                expected="exact-currentBindings-object",
                actual=type(bindings).__name__,
            )
        ]

    expected_keys = {
        "schemaVersion",
        "currentStateSha256",
        "sourcePaths",
        "timestampLines",
    }
    source_bindings = bindings.get("sourcePaths")
    timestamp_bindings = bindings.get("timestampLines")
    valid_shape = (
        set(bindings) == expected_keys
        and bindings.get("schemaVersion") == CURRENT_BINDINGS_SCHEMA_VERSION
        and isinstance(source_bindings, list)
        and all(isinstance(record, Mapping) for record in source_bindings)
        and isinstance(timestamp_bindings, list)
        and all(isinstance(record, Mapping) for record in timestamp_bindings)
    )
    if not valid_shape:
        return [
            Finding(
                code="INV-SCHEMA-CURRENT-BINDINGS",
                domain="schema",
                expected="schema=1+exact-keys+source-list+timestamp-list",
                actual="malformed",
            )
        ]

    current_fingerprint = _current_bindings_fingerprint(bindings)
    recorded_fingerprint = bindings.get("currentStateSha256")
    if (
        recorded_fingerprint != CURRENT_BINDINGS_STATE_SHA256
        or current_fingerprint != CURRENT_BINDINGS_STATE_SHA256
    ):
        findings.append(
            Finding(
                code="INV-SCHEMA-CURRENT-BINDINGS-FINGERPRINT",
                domain="schema",
                expected=CURRENT_BINDINGS_STATE_SHA256,
                actual=(
                    f"recorded={recorded_fingerprint},"
                    f"computed={current_fingerprint}"
                ),
            )
        )

    if (
        source_bindings != list(EXPECTED_CURRENT_SOURCE_BINDINGS)
        or timestamp_bindings != list(EXPECTED_CURRENT_TIMESTAMP_BINDINGS)
    ):
        findings.append(
            Finding(
                code="INV-SCHEMA-CURRENT-BINDINGS",
                domain="schema",
                expected="ordered-source=4+ordered-timestamp=4",
                actual=(
                    f"source={len(source_bindings)},"
                    f"timestamp={len(timestamp_bindings)}"
                ),
                remediation=(
                    "restore the exact eight current bindings; no adjacent "
                    "path or timestamp inherits this authority"
                ),
            )
        )

    source_keys = [str(record.get("path", "")) for record in source_bindings]
    timestamp_keys = [
        _current_binding_timestamp_key(record)
        for record in timestamp_bindings
    ]
    if (
        len(source_keys) != len(set(source_keys))
        or len(timestamp_keys) != len(set(timestamp_keys))
    ):
        findings.append(
            Finding(
                code="INV-SCHEMA-CURRENT-BINDINGS-DUPLICATE",
                domain="schema",
                expected="unique-source=4+unique-timestamp=4",
                actual=(
                    f"source={len(set(source_keys))},"
                    f"timestamp={len(set(timestamp_keys))}"
                ),
            )
        )

    historical_paths: dict[str, list[Mapping[str, Any]]] = {}
    for record in data["vyperPathClassifications"]:
        historical_paths.setdefault(str(record.get("path", "")), []).append(record)

    for binding in EXPECTED_CURRENT_SOURCE_BINDINGS:
        path = str(binding["path"])
        classification = str(binding["classification"])
        historical_sha256 = binding["historicalContentSha256"]
        historical_records = historical_paths.get(path, [])
        historical_ok = (
            not historical_records
            if historical_sha256 is None
            else len(historical_records) == 1
            and historical_records[0].get("classification") == classification
            and historical_records[0].get("contentSha256") == historical_sha256
        )
        if not historical_ok:
            findings.append(
                Finding(
                    code="INV-CURRENT-HISTORICAL-SOURCE",
                    domain="classification",
                    path=path,
                    expected=str(historical_sha256),
                    actual=json.dumps(historical_records, sort_keys=True),
                )
            )

        source = root / path
        try:
            actual_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError:
            actual_sha256 = "missing"
        if actual_sha256 != binding["currentContentSha256"]:
            findings.append(
                Finding(
                    code="INV-CURRENT-SOURCE-HASH",
                    domain="classification",
                    path=path,
                    expected=str(binding["currentContentSha256"]),
                    actual=actual_sha256,
                )
            )
        actual_classification = classify_path(
            path,
            EXPECTED_PRODUCTION_ROOTS,
            EXPECTED_EXCLUDED_PRODUCTION_GLOBS,
        )
        if actual_classification != classification:
            findings.append(
                Finding(
                    code="INV-CURRENT-SOURCE-CLASSIFICATION",
                    domain="classification",
                    path=path,
                    expected=classification,
                    actual=actual_classification,
                )
            )

    historical_timestamps: dict[
        tuple[str, str, str, int], list[Mapping[str, Any]]
    ] = {}
    for record in data["timestampContext"]:
        historical_timestamps.setdefault(_record_key(record), []).append(record)
    occurrence_cache: dict[str, dict[tuple[str, str, str, int], Occurrence]] = {}

    for binding in EXPECTED_CURRENT_TIMESTAMP_BINDINGS:
        key = _current_binding_timestamp_key(binding)
        historical_records = historical_timestamps.get(key, [])
        historical_ok = (
            len(historical_records) == 1
            and historical_records[0].get("id") == binding["id"]
            and historical_records[0].get("reviewedLine")
            == binding["historicalReviewedLine"]
        )
        if not historical_ok:
            findings.append(
                Finding(
                    code="INV-CURRENT-HISTORICAL-TIMESTAMP",
                    domain="timestamp",
                    path=key[0],
                    function=key[1],
                    expected=str(binding["historicalReviewedLine"]),
                    actual=json.dumps(historical_records, sort_keys=True),
                )
            )

        source = root / key[0]
        try:
            lines = source.read_bytes().splitlines(keepends=True)
            current_line = int(binding["currentLine"])
            raw_line = lines[current_line - 1]
            line_sha256 = hashlib.sha256(raw_line).hexdigest()
            line_text = raw_line.decode("utf-8")
            if line_text.endswith("\n"):
                line_text = line_text[:-1]
            if line_text.endswith("\r"):
                line_text = line_text[:-1]
        except (OSError, IndexError, UnicodeDecodeError, ValueError):
            current_line = int(binding["currentLine"])
            line_sha256 = "missing"
            line_text = "missing"

        if key[0] not in occurrence_cache:
            try:
                occurrences = _scan_expression_files(
                    root, [source], TIMESTAMP_PATTERN
                )
            except OSError:
                occurrences = []
            occurrence_cache[key[0]] = {
                occurrence.key: occurrence for occurrence in occurrences
            }
        occurrence = occurrence_cache[key[0]].get(key)
        if (
            line_sha256 != binding["currentLineSha256"]
            or line_text != binding["currentLineText"]
            or occurrence is None
            or occurrence.line != current_line
        ):
            findings.append(
                Finding(
                    code="INV-CURRENT-TIMESTAMP-LINE",
                    domain="timestamp",
                    path=key[0],
                    function=key[1],
                    line=current_line,
                    candidate=str(binding["id"]),
                    expected=(
                        f"line={binding['currentLine']},"
                        f"sha256={binding['currentLineSha256']},"
                        f"text={json.dumps(binding['currentLineText'])}"
                    ),
                    actual=(
                        f"line={occurrence.line if occurrence else 'missing'},"
                        f"sha256={line_sha256},text={json.dumps(line_text)}"
                    ),
                )
            )
    return findings


def _current_source_binding_records(
    data: Mapping[str, Any],
) -> Sequence[Mapping[str, Any]]:
    return data["currentBindings"]["sourcePaths"]


def _timestamp_records_for_current_state(
    data: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    bindings = {
        _current_binding_timestamp_key(record): record
        for record in data["currentBindings"]["timestampLines"]
    }
    current_records: list[Mapping[str, Any]] = []
    for historical in data["timestampContext"]:
        current = dict(historical)
        binding = bindings.get(_record_key(historical))
        if binding is not None:
            current["reviewedLine"] = binding["currentLine"]
            current["reviewedSnippet"] = _normalize_whitespace(
                str(binding["currentLineText"])
            )
        current_records.append(current)
    return current_records


def _validate_schema(
    data: Mapping[str, Any],
    root: Path = ROOT,
) -> list[Finding]:
    findings: list[Finding] = []
    version = data.get("schemaVersion")
    if version != EXPECTED_SCHEMA_VERSION:
        findings.append(
            Finding(
                code="INV-SCHEMA-VERSION",
                domain="schema",
                expected=str(EXPECTED_SCHEMA_VERSION),
                actual=str(version),
                remediation="use a separately reviewed checker/schema migration",
            )
        )
        return findings
    expected_counts = data.get("expectedProductionCounts")
    actual_counts = (
        expected_counts.get("occurrences") if isinstance(expected_counts, Mapping) else None,
        expected_counts.get("lines") if isinstance(expected_counts, Mapping) else None,
        expected_counts.get("files") if isinstance(expected_counts, Mapping) else None,
    )
    if actual_counts != EXPECTED_PRODUCTION_COUNTS:
        findings.append(
            Finding(
                code="INV-SCHEMA-BASELINE",
                domain="schema",
                expected="/".join(map(str, EXPECTED_PRODUCTION_COUNTS)),
                actual="/".join(map(str, actual_counts)),
                remediation="reconcile source drift with the semantic owner; do not update counts mechanically",
            )
        )
    collections = {
        "direct": data.get("directOccurrences"),
        "indirect": data.get("indirectCadence"),
        "timestamp": data.get("timestampContext"),
        "cadence": data.get("cadenceCandidates"),
        "seconds": data.get("secondsUnitCandidates"),
        "mixed": data.get("allowedMixedClockFunctions"),
        "classification": data.get("vyperPathClassifications"),
    }
    for domain, value in collections.items():
        if not isinstance(value, list) or not value:
            findings.append(
                Finding(
                    code="INV-SCHEMA-COLLECTION",
                    domain=domain,
                    expected="nonempty-list",
                    actual=type(value).__name__,
                )
            )
        elif any(not isinstance(record, Mapping) for record in value):
            findings.append(
                Finding(
                    code="INV-SCHEMA-RECORD",
                    domain=domain,
                    expected="object-records",
                    actual="non-object-record",
                )
            )
    if findings:
        return findings
    source_direct = _source_authority_direct_records(data)
    source_cadence = _source_authority_cadence_records(data)
    source_seconds = _source_authority_seconds_records(data)
    source_paths = _source_authority_path_records(data)
    source_sites = _source_authority_cad_sites(data)
    exact_source_authority_batch = _is_exact_source_authority_batch(data)
    exact_reviewer_remediation_registry = (
        _is_exact_reviewer_remediation_cadence_registry(data)
    )
    if not exact_source_authority_batch:
        findings.append(
            Finding(
                code="INV-SCHEMA-SOURCE-AUTHORITY-BATCH",
                domain="cadence",
                expected=(
                    f"direct={SOURCE_AUTHORITY_DIRECT_RECORD_COUNT}/"
                    f"{SOURCE_AUTHORITY_DIRECT_RECORDS_SHA256},"
                    f"cadence={SOURCE_AUTHORITY_CADENCE_RECORD_COUNT}/"
                    f"{SOURCE_AUTHORITY_CADENCE_RECORDS_SHA256},"
                    f"seconds={SOURCE_AUTHORITY_SECONDS_RECORD_COUNT}/"
                    f"{SOURCE_AUTHORITY_SECONDS_RECORDS_SHA256},"
                    f"paths={SOURCE_AUTHORITY_PATH_RECORD_COUNT}/"
                    f"{SOURCE_AUTHORITY_PATH_RECORDS_SHA256},"
                    f"cad_sites={SOURCE_AUTHORITY_CAD_SITE_COUNT}/"
                    f"{SOURCE_AUTHORITY_CAD_SITES_SHA256}"
                ),
                actual=(
                    f"direct={len(source_direct)}/"
                    f"{_records_fingerprint(source_direct)},"
                    f"cadence={len(source_cadence)}/"
                    f"{_records_fingerprint(source_cadence)},"
                    f"seconds={len(source_seconds)}/"
                    f"{_records_fingerprint(source_seconds)},"
                    f"paths={len(source_paths)}/"
                    f"{_records_fingerprint(source_paths)},"
                    f"cad_sites={len(source_sites)}/"
                    f"{_records_fingerprint(source_sites)}"
                ),
                remediation=(
                    "restore the exact reviewed source-authority inventory batch; "
                    "no adjacent record or path inherits this authority"
                ),
            )
        )
    if not _is_exact_pr61_reconciliation(data):
        pr61_direct = _pr61_direct_records(data)
        pr61_cadence = _pr61_cadence_records(data)
        pr61_seconds = _pr61_seconds_records(data)
        pr61_paths = _pr61_path_records(data)
        findings.append(
            Finding(
                code="INV-SCHEMA-PR61-RECONCILIATION",
                domain="schema",
                expected=(
                    f"direct={PR61_DIRECT_RECORD_COUNT}/"
                    f"{PR61_DIRECT_RECORDS_SHA256},"
                    f"cadence={PR61_CADENCE_RECORD_COUNT}/"
                    f"{PR61_CADENCE_RECORDS_SHA256},"
                    f"seconds={PR61_SECONDS_RECORD_COUNT}/"
                    f"{PR61_SECONDS_RECORDS_SHA256},"
                    f"paths={PR61_PATH_RECORD_COUNT}/"
                    f"{PR61_PATH_RECORDS_SHA256}"
                ),
                actual=(
                    f"direct={len(pr61_direct)}/"
                    f"{_records_fingerprint(pr61_direct)},"
                    f"cadence={len(pr61_cadence)}/"
                    f"{_records_fingerprint(pr61_cadence)},"
                    f"seconds={len(pr61_seconds)}/"
                    f"{_records_fingerprint(pr61_seconds)},"
                    f"paths={len(pr61_paths)}/"
                    f"{_records_fingerprint(pr61_paths)}"
                ),
                remediation=(
                    "restore the exact PR #61 Gate 1 reconciliation batch; "
                    "no adjacent record or future path inherits its authority"
                ),
            )
        )
    exact_pr61_artifact_metadata = (
        _is_exact_pr61_artifact_layout_metadata(data, root)
    )
    if not exact_pr61_artifact_metadata:
        metadata_records = _pr61_artifact_layout_metadata_records(data)
        artifact_path_records = _pr61_artifact_expectations_cadence_records(
            data
        )
        artifact_path = root / PR61_ARTIFACT_EXPECTATIONS_PATH
        try:
            artifact_sha256 = hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest()
        except OSError:
            artifact_sha256 = "missing"
        findings.append(
            Finding(
                code="INV-SCHEMA-PR61-ARTIFACT-METADATA",
                domain="schema",
                path=PR61_ARTIFACT_EXPECTATIONS_PATH,
                expected=(
                    f"records={PR61_ARTIFACT_LAYOUT_METADATA_RECORD_COUNT}/"
                    f"{PR61_ARTIFACT_LAYOUT_METADATA_RECORDS_SHA256},"
                    f"path_records="
                    f"{PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORD_COUNT}/"
                    f"{PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORDS_SHA256},"
                    f"legacy_artifact={PR61_ARTIFACT_EXPECTATIONS_SHA256},"
                    f"current_artifact={CURRENT_ARTIFACT_EXPECTATIONS_SHA256},"
                    f"general_registry="
                    f"{REVIEWER_REMEDIATION_CADENCE_KEY_COUNT}/"
                    f"{REVIEWER_REMEDIATION_CADENCE_KEYS_SHA256},"
                    "pr61_reconciliation=exact"
                ),
                actual=(
                    f"records={len(metadata_records)}/"
                    f"{_records_fingerprint(metadata_records)},"
                    f"path_records={len(artifact_path_records)}/"
                    f"{_records_fingerprint(artifact_path_records)},"
                    f"current_artifact={artifact_sha256},"
                    f"general_registry="
                    f"{len(REVIEWER_REMEDIATION_CADENCE_KEYS)}/"
                    f"{_key_set_fingerprint(set(REVIEWER_REMEDIATION_CADENCE_KEYS))},"
                    f"pr61_reconciliation="
                    f"{'exact' if _is_exact_pr61_reconciliation(data) else 'drifted'}"
                ),
                remediation=(
                    "restore the exact eight-record PR #61 artifact-layout "
                    "projection plus the exact authorized DefaultsRobinhood "
                    "artifact record, general remediation registry, and provenance"
                ),
            )
        )
        findings.extend(_check_s5_legacy_inventory_fingerprint(data, root))
    expected_path_config = (
        EXPECTED_PRODUCTION_ROOTS,
        EXPECTED_EXCLUDED_PRODUCTION_GLOBS,
        EXPECTED_ALLOWED_NONPRODUCTION_GLOBS,
        EXPECTED_INTERFACE_ROOTS,
        EXPECTED_CADENCE_ROOTS,
        EXPECTED_CADENCE_EXCLUDED_GLOBS,
    )
    actual_path_config = (
        data.get("productionRoots"),
        data.get("excludedProductionGlobs"),
        data.get("allowedNonProductionGlobs"),
        data.get("interfaceRoots"),
        data.get("cadenceRoots"),
        data.get("cadenceExcludedGlobs"),
    )
    if actual_path_config != expected_path_config:
        findings.append(
            Finding(
                code="INV-SCHEMA-PATH-CONFIG",
                domain="classification",
                expected=json.dumps(expected_path_config, separators=(",", ":")),
                actual=json.dumps(actual_path_config, separators=(",", ":")),
                remediation="restore the reviewed path roots and exclusions; paths may not evade discovery",
            )
        )
    if data.get("reviewAuthorities") != EXPECTED_REVIEW_AUTHORITIES:
        findings.append(
            Finding(
                code="INV-SCHEMA-AUTHORITY",
                domain="schema",
                expected=json.dumps(
                    EXPECTED_REVIEW_AUTHORITIES, sort_keys=True, separators=(",", ":")
                ),
                actual=json.dumps(
                    data.get("reviewAuthorities"), sort_keys=True, separators=(",", ":")
                ),
                remediation="restore the approved semantic-review ownership mapping",
            )
        )
    if data.get("reviewProvenance") != EXPECTED_REVIEW_PROVENANCE:
        findings.append(
            Finding(
                code="INV-SCHEMA-PROVENANCE",
                domain="schema",
                expected=json.dumps(
                    EXPECTED_REVIEW_PROVENANCE,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                actual=json.dumps(
                    data.get("reviewProvenance"),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                remediation="restore the Track 3 review and owner-approval commit references",
            )
        )
    documentation = data.get("schemaDocumentation")
    required_documentation = {
        "pathModel",
        "cadenceCoverage",
        "historicalExclusions",
        "functionAttribution",
        "reviewAuthorities",
        "reviewProvenance",
    }
    if not isinstance(documentation, Mapping) or any(
        _placeholder(documentation.get(field))
        for field in required_documentation
    ):
        findings.append(
            Finding(
                code="INV-SCHEMA-DOCUMENTATION",
                domain="schema",
                expected="non-placeholder-discovery-and-review-caveats",
                actual=type(documentation).__name__,
                remediation="restore the reviewed schema documentation and declared exclusions",
            )
        )
    expected_pattern_config = [
        {"name": name, "expression": pattern.pattern}
        for name, pattern in CADENCE_PATTERNS
    ]
    if data.get("cadencePatterns") != expected_pattern_config:
        findings.append(
            Finding(
                code="INV-SCHEMA-PATTERNS",
                domain="indirect",
                expected="reviewed-pattern-definitions",
                actual="changed",
                remediation="obtain semantic and tooling review before changing cadence discovery",
            )
        )
    _validate_s5_review_provenance(data, findings)

    direct_records = data["directOccurrences"]
    direct_keys: dict[tuple[str, str, str, int], list[Mapping[str, Any]]] = {}
    for record in direct_records:
        if not isinstance(record, Mapping):
            findings.append(
                Finding(code="INV-SCHEMA-RECORD", domain="direct", actual=type(record).__name__)
            )
            continue
        key = _record_key(record)
        direct_keys.setdefault(key, []).append(record)
        _validate_semantic_review(
            record,
            "direct",
            str(record.get("id", "UNMAPPED")),
            findings,
            "protocol/security",
            TRACK3_REVIEW_COMMIT,
        )
    for key, records in direct_keys.items():
        if len(records) != 1:
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain="direct",
                    path=key[0],
                    function=key[1],
                    candidate=",".join(sorted(str(record.get("id")) for record in records)),
                    expected="1",
                    actual=str(len(records)),
                )
            )
    duplicate_domains: tuple[
        tuple[
            str,
            Sequence[Mapping[str, Any]],
            Callable[[Mapping[str, Any]], tuple[Any, ...]],
        ],
        ...,
    ] = (
        ("timestamp", data["timestampContext"], _record_key),
        (
            "indirect",
            data["indirectCadence"],
            lambda record: (str(record.get("id", "")),),
        ),
        ("cadence", data["cadenceCandidates"], _candidate_from_record),
        ("seconds", data["secondsUnitCandidates"], _candidate_from_record),
        (
            "mixed",
            data["allowedMixedClockFunctions"],
            lambda record: (
                str(record.get("path", "")),
                str(record.get("function", "")),
            ),
        ),
    )
    for domain, records, key_function in duplicate_domains:
        records_by_key: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
        for record in records:
            records_by_key.setdefault(key_function(record), []).append(record)
        for key, duplicate_records in records_by_key.items():
            if len(duplicate_records) == 1:
                continue
            first = duplicate_records[0]
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain=domain,
                    path=str(first.get("path", "-")),
                    function=str(first.get("function", "-")),
                    candidate=_candidate_label(first),
                    expected="1",
                    actual=str(len(duplicate_records)),
                    snippet=json.dumps(key, ensure_ascii=True),
                )
            )

    bn_ids = {str(record.get("id")) for record in direct_records if isinstance(record, Mapping)}
    cad_ids = {
        str(record.get("id"))
        for record in data["indirectCadence"]
        if isinstance(record, Mapping)
    }
    ts_ids = {
        str(record.get("id"))
        for record in data["timestampContext"]
        if isinstance(record, Mapping)
    }
    for domain, expected, actual in (
        ("direct", EXPECTED_BN_IDS, bn_ids),
        ("indirect", EXPECTED_CAD_IDS, cad_ids),
        ("timestamp", EXPECTED_TS_IDS, ts_ids),
    ):
        if actual != expected:
            findings.append(
                Finding(
                    code="INV-SCHEMA-ID-SET",
                    domain=domain,
                    expected=",".join(sorted(expected)),
                    actual=",".join(sorted(actual)),
                    remediation="reconcile stable IDs with the reviewed Track 3 inventory; never renumber",
                )
            )
    for domain, records, expected_owner, expected_commit in (
        (
            "indirect",
            data["indirectCadence"],
            "risk/oracle",
            TRACK3_REVIEW_COMMIT,
        ),
        (
            "timestamp",
            data["timestampContext"],
            "protocol/security",
            TRACK3_REVIEW_COMMIT,
        ),
        (
            "seconds",
            data["secondsUnitCandidates"],
            "protocol/security",
            HARDENING_REVIEW_COMMIT,
        ),
        (
            "mixed",
            data["allowedMixedClockFunctions"],
            "protocol/security",
            HARDENING_REVIEW_COMMIT,
        ),
        (
            "classification",
            data["vyperPathClassifications"],
            "engineering/tooling",
            HARDENING_REVIEW_COMMIT,
        ),
    ):
        for record in records:
            if isinstance(record, Mapping):
                record_expected_commit = expected_commit
                if (
                    domain == "classification"
                    and str(record.get("path", ""))
                    in PR61_PRODUCTION_SOURCE_SHA256
                ):
                    record_expected_commit = PR61_REVIEW_COMMIT
                elif (
                    domain == "classification"
                    and str(record.get("path", ""))
                    == "contracts/config/DefaultsRobinhood.vy"
                    and exact_source_authority_batch
                ):
                    record_expected_commit = SOURCE_AUTHORITY_REVIEW_COMMIT
                elif (
                    domain == "seconds"
                    and str(record.get("path", ""))
                    == "contracts/config/DefaultsRobinhood.vy"
                    and exact_source_authority_batch
                ):
                    record_expected_commit = SOURCE_AUTHORITY_REVIEW_COMMIT
                _validate_semantic_review(
                    record,
                    domain,
                    str(record.get("id", _candidate_label(record))),
                    findings,
                    expected_owner,
                    record_expected_commit,
                )
    for record in data["cadenceCandidates"]:
        semantic_ids = _candidate_semantic_ids(record)
        expected_owner = "risk/oracle" if "CAD-001" in semantic_ids else "protocol/security"
        expected_commit = (
            TRACK3_REVIEW_COMMIT
            if "CAD-001" in semantic_ids
            else (
                SOURCE_AUTHORITY_REVIEW_COMMIT
                if exact_source_authority_batch
                and (
                    str(record.get("path", ""))
                    in SOURCE_AUTHORITY_CADENCE_PATHS
                    or _candidate_from_record(record)
                    in SOURCE_AUTHORITY_BLUEPRINT_CADENCE_KEYS
                )
                else (
                PROFILE1_CONFIGURATION_PROVENANCE_COMMIT
                if _candidate_from_record(record)
                == PROFILE1_CONFIGURATION_CADENCE_KEY
                and exact_reviewer_remediation_registry
                else (
                        PR61_REVIEW_COMMIT
                        if _candidate_from_record(record)
                        == PR61_NEW_CONSTRUCTOR_CADENCE_KEY
                        else HARDENING_REVIEW_COMMIT
                )
                )
            )
        )
        _validate_semantic_review(
            record,
            "cadence",
            _candidate_label(record),
            findings,
            expected_owner,
            expected_commit,
        )
    reviewed_semantic_ids = EXPECTED_BN_IDS | EXPECTED_CAD_IDS | EXPECTED_TS_IDS
    for domain, records in (
        ("cadence", data["cadenceCandidates"]),
        ("seconds", data["secondsUnitCandidates"]),
    ):
        for record in records:
            semantic_ids_value = record.get("semanticIds")
            semantic_ids = _candidate_semantic_ids(record)
            invalid_semantic_ids = (
                not isinstance(semantic_ids_value, list)
                or len(semantic_ids) != len(semantic_ids_value)
                or len(semantic_ids) != len(set(semantic_ids))
                or not set(semantic_ids).issubset(reviewed_semantic_ids)
            )
            if (
                "semanticId" in record
                or invalid_semantic_ids
                or record.get("reviewDomain") != "cadence-surface"
            ):
                findings.append(
                    Finding(
                        code="INV-SCHEMA-SEMANTIC-LINK",
                        domain=domain,
                        path=str(record.get("path", "-")),
                        candidate=_candidate_label(record),
                        expected="semanticIds-list+cadence-surface-domain",
                        actual=(
                            f"semanticId={record.get('semanticId', 'absent')},"
                            f"semanticIds={json.dumps(semantic_ids_value)},"
                            f"reviewDomain={record.get('reviewDomain')}"
                        ),
                        remediation="use reviewed stable IDs only; do not invent pseudo-identifiers",
                    )
                )
    cad_sites_by_key: dict[
        tuple[str, str, str, str, str, int],
        list[tuple[str, Mapping[str, Any]]],
    ] = {}
    for record in data["indirectCadence"]:
        sites_value = record.get("sites")
        if not isinstance(sites_value, list) or not sites_value:
            findings.append(
                Finding(
                    code="INV-SCHEMA-COLLECTION",
                    domain="indirect",
                    candidate=str(record.get("id", "UNMAPPED")),
                    expected="nonempty-sites-list",
                    actual=type(sites_value).__name__,
                )
            )
            continue
        for site in sites_value:
            if not isinstance(site, Mapping):
                findings.append(
                    Finding(
                        code="INV-SCHEMA-RECORD",
                        domain="indirect",
                        candidate=str(record.get("id", "UNMAPPED")),
                        expected="object-site-record",
                        actual=type(site).__name__,
                    )
                )
                continue
            cad_sites_by_key.setdefault(
                _candidate_from_record(site), []
            ).append((str(record.get("id", "UNMAPPED")), site))
    for key, sites in cad_sites_by_key.items():
        if len(sites) == 1:
            continue
        stable_id, first = sites[0]
        findings.append(
            Finding(
                code="INV-SCHEMA-DUPLICATE",
                domain="indirect",
                path=str(first.get("path", "-")),
                function=str(first.get("function", "-")),
                candidate=stable_id,
                expected="1",
                actual=str(len(sites)),
                snippet=json.dumps(key, ensure_ascii=True),
                remediation="remove the redundant reviewed cadence-site row",
            )
        )
    cad_site_keys = set(cad_sites_by_key)
    reviewed_cad_keys = {
        _candidate_from_record(record)
        for record in data["cadenceCandidates"]
        if isinstance(record, Mapping)
        and "CAD-001" in _candidate_semantic_ids(record)
    }
    if cad_site_keys != reviewed_cad_keys:
        findings.append(
            Finding(
                code="INV-SCHEMA-CAD-SITES",
                domain="indirect",
                candidate="CAD-001",
                expected=(
                    f"count={len(reviewed_cad_keys)},"
                    f"sha256={_key_set_fingerprint(reviewed_cad_keys)}"
                ),
                actual=(
                    f"count={len(cad_site_keys)},"
                    f"sha256={_key_set_fingerprint(cad_site_keys)}"
                ),
                remediation="restore the reviewed CAD-001 site mapping; do not suppress cadence candidates",
            )
        )
    path_records = [
        record
        for record in data["vyperPathClassifications"]
        if isinstance(record, Mapping)
    ]
    path_names = [str(record.get("path", "")) for record in path_records]
    if len(path_names) != len(set(path_names)) or any(not name for name in path_names):
        findings.append(
            Finding(
                code="INV-SCHEMA-PATH-RECORD",
                domain="classification",
                expected="unique-nonempty-paths",
                actual=str(len(path_names)),
            )
        )
    for record in path_records:
        classification = record.get("classification")
        content_hash = record.get("contentSha256")
        reviewed_excluded = classification == "excluded" and (
            content_hash
            == EXCLUDED_EXAMPLE_CONTENT_HASHES.get(str(record.get("path", "")))
        )
        if (
            classification not in {
                "production",
                "mock",
                "testing",
                "test",
                "interface",
            }
            and not reviewed_excluded
        ) or not (
            isinstance(content_hash, str)
            and re.fullmatch(r"[0-9a-f]{64}", content_hash)
        ):
            findings.append(
                Finding(
                    code="INV-SCHEMA-PATH-RECORD",
                    domain="classification",
                    path=str(record.get("path", "-")),
                    expected="reviewed-classification+sha256",
                    actual=f"{classification}:{content_hash}",
                )
            )
    findings.extend(_validate_current_bindings(data, root))
    return findings


def _current_vyper_classifications(
    root: Path,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in _iter_files(root, ["."]):
        if path.suffix not in VYPER_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        records[relative] = {
            "classification": classify_path(
                relative, production_roots, excluded_production_globs
            ),
            "contentSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return records


def _check_path_classifications(
    root: Path,
    records: Sequence[Mapping[str, Any]],
    current_records: Sequence[Mapping[str, Any]],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> list[Finding]:
    findings: list[Finding] = []
    expected = {
        str(record.get("path")): {
            "classification": str(record.get("classification")),
            "contentSha256": str(record.get("contentSha256")),
        }
        for record in records
    }
    for record in current_records:
        path = str(record.get("path"))
        if path not in expected:
            expected[path] = {
                "classification": str(record.get("classification")),
                "contentSha256": str(record.get("currentContentSha256")),
            }
    actual = _current_vyper_classifications(
        root, production_roots, excluded_production_globs
    )
    missing = set(expected) - set(actual)
    added = set(actual) - set(expected)
    consumed_missing: set[str] = set()
    consumed_added: set[str] = set()
    for old_path in sorted(missing):
        old_hash = expected[old_path]["contentSha256"]
        matches = [
            new_path
            for new_path in sorted(added)
            if actual[new_path]["contentSha256"] == old_hash
        ]
        if len(matches) != 1:
            continue
        new_path = matches[0]
        consumed_missing.add(old_path)
        consumed_added.add(new_path)
        findings.append(
            Finding(
                code="INV-PATH-MOVED",
                domain="classification",
                path=new_path,
                snippet=f"{old_path}->{new_path}",
                expected=expected[old_path]["classification"],
                actual=actual[new_path]["classification"],
                remediation=(
                    "obtain engineering/tooling path review and protocol/security "
                    "review for any production-boundary move"
                ),
            )
        )
    for path in sorted(added - consumed_added):
        findings.append(
            Finding(
                code="INV-PATH-NEW",
                domain="classification",
                path=path,
                actual=actual[path]["classification"],
                remediation=(
                    "obtain engineering/tooling path review and semantic-owner "
                    "review before adding the Vyper source"
                ),
            )
        )
    for path in sorted(missing - consumed_missing):
        findings.append(
            Finding(
                code="INV-PATH-MISSING",
                domain="classification",
                path=path,
                expected=expected[path]["classification"],
                actual="missing",
                remediation=(
                    "obtain engineering/tooling path review and semantic-owner "
                    "review before removing the Vyper source"
                ),
            )
        )
    for path in sorted(set(expected) & set(actual)):
        if expected[path]["classification"] != actual[path]["classification"]:
            findings.append(
                Finding(
                    code="INV-PATH-CLASSIFICATION",
                    domain="classification",
                    path=path,
                    expected=expected[path]["classification"],
                    actual=actual[path]["classification"],
                    remediation=(
                        "obtain engineering/tooling path review and protocol/security "
                        "review for any production-boundary classification change"
                    ),
                )
            )
        if (
            expected[path]["classification"] == "excluded"
            and expected[path]["contentSha256"] != actual[path]["contentSha256"]
        ):
            findings.append(
                Finding(
                    code="INV-PATH-EXCLUDED-CONTENT",
                    domain="classification",
                    path=path,
                    expected=expected[path]["contentSha256"],
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "obtain engineering/tooling review before changing an "
                        "excluded reference example; its content hash is frozen"
                    ),
                )
            )
        if (
            path == M2_GUARDED_ERC20_PATH
            and actual[path]["contentSha256"] != M2_GUARDED_ERC20_SHA256
        ):
            findings.append(
                Finding(
                    code="INV-PATH-M2-CONTENT",
                    domain="classification",
                    path=path,
                    expected=M2_GUARDED_ERC20_SHA256,
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "restore the exact reviewed GuardedErc20 source bytes; "
                        "changing the M2 production identity requires new review"
                    ),
                )
            )
        if (
            path == M3_CREDIT_ENGINE_PATH
            and actual[path]["contentSha256"] != M3_CREDIT_ENGINE_SHA256
        ):
            findings.append(
                Finding(
                    code="INV-PATH-M3-CONTENT",
                    domain="classification",
                    path=path,
                    expected=M3_CREDIT_ENGINE_SHA256,
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "restore the exact reviewed CreditEngine source bytes; "
                        "changing the M3 production identity requires new review"
                    ),
                )
            )
    return findings


def _production_vyper_files(
    root: Path,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> tuple[list[Path], list[Finding]]:
    production: list[Path] = []
    findings: list[Finding] = []
    for path in _iter_files(root, ["."]):
        if path.suffix not in VYPER_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        if classification == "production" and path.suffix == ".vy":
            production.append(path)
        elif classification == "unclassified":
            findings.append(
                Finding(
                    code="INV-PATH-UNCLASSIFIED",
                    domain="classification",
                    path=relative,
                    actual="vyper",
                    remediation="obtain path-classification review before adding or moving the contract",
                )
            )
    return sorted(production), findings


def _check_imports(root: Path, production_paths: Sequence[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in production_paths:
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        lines = text.splitlines()
        for match in IMPORT_PATTERN.finditer(text):
            target = match.group(1).replace("/", ".")
            if "contracts.mock" not in target and "contracts.testing" not in target:
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    code="INV-IMPORT-PROD-NONPROD",
                    domain="import",
                    path=relative,
                    line=line,
                    snippet=_normalize_whitespace(lines[line - 1]),
                    actual=target,
                    remediation="remove the production dependency on mock/testing code and obtain review",
                )
            )
    return findings


def _compare_occurrences(
    actual: Sequence[Occurrence],
    expected_records: Sequence[Mapping[str, Any]],
    domain: str,
    new_code: str,
    missing_code: str,
    move_code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    actual_by_key = {occurrence.key: occurrence for occurrence in actual}
    expected_by_key = {_record_key(record): record for record in expected_records}

    for key in sorted(actual_by_key):
        occurrence = actual_by_key[key]
        record = expected_by_key.get(key)
        if record is None:
            findings.append(
                Finding(
                    code=new_code,
                    domain=domain,
                    path=occurrence.path,
                    function=occurrence.function,
                    line=occurrence.line,
                    snippet=occurrence.snippet,
                    actual=occurrence.normalized_expression,
                )
            )
            continue
        reviewed_line = int(record.get("reviewedLine", 0))
        if reviewed_line != occurrence.line:
            findings.append(
                Finding(
                    code=move_code,
                    domain=domain,
                    path=occurrence.path,
                    function=occurrence.function,
                    line=occurrence.line,
                    snippet=occurrence.snippet,
                    candidate=str(record.get("id", "UNMAPPED")),
                    expected=str(reviewed_line),
                    actual=str(occurrence.line),
                    remediation="obtain semantic review of the moved occurrence; line remains diagnostic, not identity",
                )
            )

    for key in sorted(expected_by_key):
        if key in actual_by_key:
            continue
        record = expected_by_key[key]
        findings.append(
            Finding(
                code=missing_code,
                domain=domain,
                path=key[0],
                function=key[1],
                line=int(record.get("reviewedLine", 0)),
                snippet=str(record.get("reviewedSnippet", key[2])),
                candidate=str(record.get("id", "UNMAPPED")),
                expected=key[2],
                actual="missing",
            )
        )
    return findings


def _compare_candidates(
    actual: Sequence[Candidate],
    expected_records: Sequence[Mapping[str, Any]],
    domain: str,
    new_code: str,
    missing_code: str,
    move_code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    actual_by_key = {candidate.key: candidate for candidate in actual}
    expected_by_key: dict[tuple[str, str, str, str, str, int], Mapping[str, Any]] = {}
    for record in expected_records:
        key = _candidate_from_record(record)
        if key in expected_by_key:
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain=domain,
                    path=key[0],
                    function=key[1],
                    snippet=key[4],
                )
            )
        expected_by_key[key] = record
    for key in sorted(actual_by_key):
        candidate = actual_by_key[key]
        record = expected_by_key.get(key)
        if record is None:
            findings.append(
                Finding(
                    code=new_code,
                    domain=domain,
                    path=candidate.path,
                    function=candidate.function,
                    line=candidate.line,
                    snippet=candidate.normalized_snippet,
                    actual=(
                        f"{candidate.classification}:"
                        f"{candidate.pattern}:{candidate.matched_text}"
                    ),
                    remediation=(
                        "obtain probe/mock review before inventorying this non-production cadence dependency"
                        if candidate.classification in {"mock", "testing", "test"}
                        else "obtain semantic-owner review before inventorying this cadence dependency"
                    ),
                )
            )
            continue
        reviewed_line = int(record.get("reviewedLine", 0))
        if reviewed_line != candidate.line:
            findings.append(
                Finding(
                    code=move_code,
                    domain=domain,
                    path=candidate.path,
                    function=candidate.function,
                    line=candidate.line,
                    snippet=candidate.normalized_snippet,
                    candidate=_candidate_label(record),
                    expected=str(reviewed_line),
                    actual=str(candidate.line),
                )
            )
    for key in sorted(expected_by_key):
        if key in actual_by_key:
            continue
        record = expected_by_key[key]
        findings.append(
            Finding(
                code=missing_code,
                domain=domain,
                path=key[0],
                function=key[1],
                line=int(record.get("reviewedLine", 0)),
                snippet=key[4],
                candidate=_candidate_label(record),
                expected=f"{key[2]}:{key[3]}",
                actual="missing",
            )
        )
    return findings


def _mixed_clock_functions(
    root: Path, production_paths: Sequence[Path]
) -> list[tuple[str, str]]:
    mixed: list[tuple[str, str]] = []
    for path in production_paths:
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        lines = text.splitlines()
        functions = _line_functions(lines)
        bodies: dict[str, list[str]] = {}
        for function, line in zip(functions, lines):
            bodies.setdefault(function, []).append(line)
        for function, body_lines in bodies.items():
            body = "\n".join(body_lines)
            if DIRECT_PATTERN.search(body) and TIMESTAMP_PATTERN.search(body):
                mixed.append((relative, function))
    return sorted(mixed)


def _nonproduction_counts(
    root: Path,
    all_files: Sequence[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> dict[str, tuple[int, int, int]]:
    grouped: dict[str, list[Path]] = {"mock": [], "testing": [], "test": []}
    for path in all_files:
        relative = path.relative_to(root).as_posix()
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        if classification in grouped and path.suffix in SOURCE_SUFFIXES:
            grouped[classification].append(path)
    return {
        classification: _scan_fixed_counts(paths, "block.number")
        for classification, paths in grouped.items()
    }


def check_repository(
    repository_root: Path | str,
    inventory_path: Path | str | None = None,
) -> CheckResult:
    root = Path(repository_root).resolve()
    inventory = (
        Path(inventory_path).resolve()
        if inventory_path is not None
        else root / "config" / "block-clock-inventory.json"
    )
    data, findings = _load_inventory(inventory)
    if data is None:
        return CheckResult(findings=findings, success_lines=[])
    findings.extend(_validate_schema(data, root))
    if findings:
        return CheckResult(findings=findings, success_lines=[])

    production_roots = [str(item) for item in data["productionRoots"]]
    excluded_production_globs = [
        str(item) for item in data["excludedProductionGlobs"]
    ]
    findings.extend(
        _check_path_classifications(
            root,
            data["vyperPathClassifications"],
            _current_source_binding_records(data),
            production_roots,
            excluded_production_globs,
        )
    )
    production_paths, classification_findings = _production_vyper_files(
        root, production_roots, excluded_production_globs
    )
    findings.extend(classification_findings)
    findings.extend(_check_imports(root, production_paths))

    direct_actual = _scan_expression_files(
        root, production_paths, DIRECT_PATTERN
    )
    fixed_counts = _scan_fixed_counts(production_paths, "block.number")
    expected_counts = data["expectedProductionCounts"]
    active_expected = (
        int(expected_counts["occurrences"]),
        int(expected_counts["lines"]),
        int(expected_counts["files"]),
    )
    if fixed_counts != active_expected:
        findings.append(
            Finding(
                code="INV-DIRECT-COUNT",
                domain="direct",
                expected="/".join(map(str, active_expected)),
                actual="/".join(map(str, fixed_counts)),
                remediation="reconcile the fixed-string source delta with protocol/security",
            )
        )
    if len(direct_actual) != fixed_counts[0]:
        first = next(
            (
                occurrence
                for occurrence in direct_actual
                if occurrence.normalized_expression != "block.number"
            ),
            direct_actual[0] if direct_actual else None,
        )
        findings.append(
            Finding(
                code="INV-PARSER-FIXED-DISAGREE",
                domain="direct",
                path=first.path if first else "-",
                function=first.function if first else "-",
                line=first.line if first else 0,
                snippet=first.snippet if first else "-",
                expected=str(fixed_counts[0]),
                actual=str(len(direct_actual)),
                remediation="repair discovery so the parser cannot suppress a fixed-string delta",
            )
        )
    findings.extend(
        _compare_occurrences(
            direct_actual,
            data["directOccurrences"],
            "direct",
            "INV-DIRECT-NEW",
            "INV-DIRECT-MISSING",
            "INV-DIRECT-MOVE",
        )
    )

    timestamp_actual = _scan_expression_files(
        root, production_paths, TIMESTAMP_PATTERN
    )
    timestamp_counts = _scan_fixed_counts(production_paths, "block.timestamp")
    expected_timestamp_counts = data.get("expectedTimestampCounts", {})
    timestamp_expected = (
        int(expected_timestamp_counts.get("occurrences", -1)),
        int(expected_timestamp_counts.get("lines", -1)),
        int(expected_timestamp_counts.get("files", -1)),
    )
    if timestamp_expected != EXPECTED_TIMESTAMP_COUNTS:
        findings.append(
            Finding(
                code="INV-SCHEMA-TIMESTAMP-BASELINE",
                domain="timestamp",
                expected="/".join(map(str, EXPECTED_TIMESTAMP_COUNTS)),
                actual="/".join(map(str, timestamp_expected)),
            )
        )
    if timestamp_counts != timestamp_expected:
        findings.append(
            Finding(
                code="INV-TIMESTAMP-COUNT",
                domain="timestamp",
                expected="/".join(map(str, timestamp_expected)),
                actual="/".join(map(str, timestamp_counts)),
            )
        )
    findings.extend(
        _compare_occurrences(
            timestamp_actual,
            _timestamp_records_for_current_state(data),
            "timestamp",
            "INV-TIMESTAMP-NEW",
            "INV-TIMESTAMP-MISSING",
            "INV-TIMESTAMP-MOVE",
        )
    )

    cadence_roots = [str(item) for item in data["cadenceRoots"]]
    cadence_paths = _iter_files(root, cadence_roots)
    cadence_excluded_globs = [
        str(item) for item in data.get("cadenceExcludedGlobs", [])
    ]
    cadence_actual = _scan_candidates(
        root,
        cadence_paths,
        production_roots,
        excluded_production_globs,
        cadence_excluded_globs,
    )
    findings.extend(
        _compare_candidates(
            cadence_actual,
            data["cadenceCandidates"],
            "indirect",
            "INV-CADENCE-NEW",
            "INV-CADENCE-MISSING",
            "INV-CADENCE-MOVE",
        )
    )
    seconds_actual = _scan_seconds_candidates(
        root,
        cadence_paths,
        production_roots,
        excluded_production_globs,
        cadence_excluded_globs,
    )
    findings.extend(
        _compare_candidates(
            seconds_actual,
            data.get("secondsUnitCandidates", []),
            "timestamp-units",
            "INV-SECONDS-UNIT-NEW",
            "INV-SECONDS-UNIT-MISSING",
            "INV-SECONDS-UNIT-MOVE",
        )
    )

    actual_mixed = set(_mixed_clock_functions(root, production_paths))
    expected_mixed = {
        (str(record["path"]), str(record["function"]))
        for record in data.get("allowedMixedClockFunctions", [])
    }
    for path, function in sorted(actual_mixed - expected_mixed):
        findings.append(
            Finding(
                code="INV-MIXED-CLOCK-NEW",
                domain="timestamp",
                path=path,
                function=function,
                actual="NUMBER+timestamp",
                remediation="obtain protocol/security review of the cross-domain dependency",
            )
        )
    for path, function in sorted(expected_mixed - actual_mixed):
        findings.append(
            Finding(
                code="INV-MIXED-CLOCK-MISSING",
                domain="timestamp",
                path=path,
                function=function,
                expected="reviewed-NUMBER+timestamp",
                actual="missing",
            )
        )

    all_files = _iter_files(root, ["."])
    nonproduction = _nonproduction_counts(
        root, all_files, production_roots, excluded_production_globs
    )
    nonproduction_cadence = {
        classification: sum(
            1
            for candidate in cadence_actual
            if candidate.classification == classification
        )
        for classification in ("mock", "testing", "test")
    }
    findings.extend(_check_s5_legacy_inventory_fingerprint(data, root))
    findings.extend(_check_post_s5_production_inventory_fingerprint(data))
    success_lines = [
        (
            "CLOCK_INVENTORY_OK "
            f"schema={data['schemaVersion']} "
            f"production_occurrences={fixed_counts[0]} "
            f"production_lines={fixed_counts[1]} "
            f"production_files={fixed_counts[2]} "
            f"bn_ids={len(EXPECTED_BN_IDS)} "
            f"bn_records={len(data['directOccurrences'])} "
            f"indirect_ids={len(EXPECTED_CAD_IDS)} "
            f"cadence_candidates={len(cadence_actual)} "
            f"seconds_unit_candidates={len(seconds_actual)} "
            f"timestamp_ids={len(EXPECTED_TS_IDS)} "
            f"timestamp_occurrences={timestamp_counts[0]} "
            f"mixed_clock_functions={len(actual_mixed)} "
            f"vyper_paths={len(data['vyperPathClassifications'])} "
            "current_bindings=4/4 "
            f"current_state_sha256={CURRENT_BINDINGS_STATE_SHA256} "
            "post_s5_production_records="
            f"{sum(record.get('classification') == 'production' for record in data['vyperPathClassifications'])} "
            "post_s5_production_sha256="
            f"{_post_s5_production_inventory_fingerprint(data)}"
        ),
        (
            "CLOCK_INVENTORY_NONPROD "
            + " ".join(
                (
                    f"{classification}="
                    f"{nonproduction[classification][0]}/"
                    f"{nonproduction[classification][1]}/"
                    f"{nonproduction[classification][2]}"
                )
                for classification in ("mock", "testing", "test")
            )
        ),
        (
            "CLOCK_INVENTORY_NONPROD_CADENCE "
            + " ".join(
                f"{classification}={nonproduction_cadence[classification]}"
                for classification in ("mock", "testing", "test")
            )
        ),
    ]
    return CheckResult(findings=findings, success_lines=success_lines)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the reviewed block-clock inventory"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the repository and exit nonzero on drift",
    )
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("--check is required")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    _parse_args(sys.argv[1:] if argv is None else argv)
    repository_root = Path(__file__).resolve().parents[1]
    result = check_repository(repository_root)
    print(result.output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
