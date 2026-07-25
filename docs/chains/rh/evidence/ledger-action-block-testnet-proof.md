# S5 Robinhood Testnet Action-Block Probe Evidence

**Status:** Frozen local probe evidence recreated on exact integrated baseline
`02787d3`; authoritative post-H-01 validation and the complete secret-free
authorization template are recorded; live Robinhood testnet proof not
attempted because required approvals and live inputs are absent

**Evidence date:** 24 July 2026

**Network authorized:** Robinhood Chain testnet only, chain ID `46630`

**Production authority:** None

**Recreation branch/baseline:**
`rh-track-6-s5-ledger-guard-recreation` at
`02787d351a3064e35d627e8fbc44150770e61c73`

**Frozen historical evidence:** `rh-track-6-s5-ledger-guard` at
`6652a10e4de2a74ca27be0da94be4331aeef18f6`, tree
`c21fdef7f6156abac1da606492c7e0329315b693`

## 1. Scope and stop

The owner authorized the smallest isolated proof comparing:

1. in-contract native `block.number`;
2. `ArbSys(0x0000000000000000000000000000000000000064).arbBlockNumber()`;
   and
3. each transaction receipt's child-chain `blockNumber`.

The authorization does not cover mainnet, Base, governance, production
contracts, user funds, a production Ledger change, merge, push, or deployment.
The live proof did not start because no exact RPC endpoint, endpoint
fingerprint, signer, signer-fund approval, nonce/predicted address, dated
independent-security/deployment approval, or owner-approved fee parameters and
maximum total fee were provided. The published Robinhood ArbOS profile `61`,
derived expected raw `ArbSys.arbOSVersion()` return `116`, selectors, source
pins, and local artifact hashes are prepared below, but are not execution
authorization. No RPC endpoint or approved signing secret was read, and no
live transaction was signed or broadcast. Focused unit tests used ephemeral
in-memory signing keys solely to verify deterministic transaction journaling;
no key was persisted or printed and no network call occurred.

The result is therefore **inconclusive for live Robinhood behavior**. Local
evidence must not be promoted into a claim about deployed Robinhood `0x64`.

## 2. Isolated files and production exclusion

| File | Purpose |
| --- | --- |
| `contracts/testing/ActionBlockIdentityProbe.vy` | test-only constructor/read/emit probe using the fixed `0x64` ABI |
| `scripts/probes/action_block_identity_probe.py` | local dry-run, read-only preflight, and separately confirmed bounded testnet runner |
| `tests/probes/test_action_block_identity_probe.py` | focused controlled-double, approval, artifact, topology, and packaging tests |
| `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md` | this sanitized evidence record |
| `docs/chains/rh/ledger-guard-security-decision.md` | one-immutable planning correction and updated evidence/Checkpoint 0 disposition |

The probe is not referenced by a production migration, ABI export, deployment
manifest, or production packaging path. Focused tests assert that
`contracts/testing/` is excluded from migration discovery and ABI export. No
production Ledger, interface, migration, manifest, ABI, inventory, dependency,
default, or shared planning file was changed.

`contracts/data/Ledger.vy` has Git blob
`ef02462508e01f59e8f8112ffce0ca8d17d4d0b8` and SHA-256
`00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0`
at frozen evidence commit `6652a10`, recreation baseline `02787d3`, current
branch HEAD, and working tree. The production Ledger is byte-for-byte
untouched.

The exact five-file bytes independently reviewed before hardening were
committed locally, without push, at audit point
`2f6a49b6c82e69bda54f2fd64d2fe03132e0db21`. Their SHA-256 identities were:

- decision record:
  `0b4f8c7b1c6d424b17dffd5c2650cc7c60a48929b2bc5c51ef2d4d94edf946ba`;
- probe source:
  `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5`;
- runner:
  `8406107af89f8bee464a544ae462c27aa61004e268b768c5e7527b1885c1052a`;
- focused tests:
  `ac4665731777a9d7e85e2a36f0383598047198c9d5f3de178594a40da8cb2a12`;
  and
- evidence record:
  `6c4d501d30d6b70753e0e92a9104cd1edab27d623602c6bcb38817fa4091846a`.

The subsequent uncommitted post-review hardening delta changed the runner,
focused tests, decision record, and this evidence record. It did not change the
test-only Vyper probe. The resulting current SHA-256 identities, excluding this
self-referential evidence-file hash, are:

- decision record:
  `d11f70afd00d94a2242b294303302c1deefee134e316b5ed27cf71787613ea20`;
- probe source:
  `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5`;
- runner:
  `135a864356fdfa076acda0009a5e97907afd471215ba5bdfc3dfe1056b4b498b`;
  and
- focused tests:
  `24c5bad958cba5425ec52e060995332302409b1fac01a1967c84b7261a2631b6`.

The final evidence-file hash is reported out of band in the handoff; this file
does not embed its own hash because doing so would be self-referential.

## 3. Exact local artifact identity

The local-only dry-run compiled the probe with these exact inputs and outputs:

| Field | Value |
| --- | --- |
| compiler | `vyper==0.4.3+commit.bff19ea2` |
| compiler settings | `{"compiler_version":null,"debug":null,"enable_decimals":null,"evm_version":null,"experimental_codegen":false,"nonreentrancy_by_default":null,"optimize":"gas"}` |
| source path | `contracts/testing/ActionBlockIdentityProbe.vy` |
| source SHA-256 | `0x95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` |
| ABI SHA-256 | `0x2c237ba7e43aa009c69eabe950c733c79415b7eab37e874e065494273a45b359` |
| canonical compiler-input identity SHA-256 | `0xf251237b97029e29122f5578c38817e518abcc3062c6d32019de028bdef79a65` |
| creation bytecode keccak-256 | `0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333` |
| creation bytecode length | `375` bytes |
| runtime bytecode keccak-256 | `0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56` |
| runtime bytecode length | `252` bytes |
| ArbSys address | `0x0000000000000000000000000000000000000064` |
| `arbBlockNumber()` selector | `0xa3b1b31d` |
| `arbOSVersion()` selector | `0x051038f2` |
| Robinhood published ArbOS profile | `61` |
| pinned Nitro `arbOSVersion()` offset | `55` |
| required approved raw `ArbSys.arbOSVersion()` return | `116` (`61 + 55`) |

The approval parser requires these creation/runtime hashes to be copied
exactly into a secret-free approval file. A mismatch stops before RPC contact
or signing. Approval schema version `2` separately requires
`robinhood_published_arb_os_profile=61` and
`expected_arb_sys_arb_os_version_return=116`; the runner rejects any pair that
does not satisfy the pinned-source relationship `61 + 55 = 116`.

## 4. Local fail-closed evidence

The Vyper probe constructor calls and decodes the fixed
`ArbSys(0x64).arbBlockNumber()` path. Controlled doubles established:

| `0x64` behavior | Construction | Later observation | Native fallback |
| --- | --- | --- | --- |
| compatible `uint256` response | succeeds | succeeds and emits both identities | not used |
| missing code | reverts | reverts | none |
| reverting runtime | reverts | reverts | none |
| one-byte malformed return | reverts | reverts | none |
| incompatible selector/runtime | reverts | reverts | none |

These are local EVM/compiler facts only. They do not establish that
Robinhood's deployed `0x64` is present or compatible.

### 4.1 Preflight and transaction-journal hardening

Focused local tests establish:

- dry-run records `rpc_endpoint_read=false` and
  `signing_secret_read=false`;
- every RPC POST refuses HTTP redirects rather than silently changing the
  owner-approved endpoint;
- successful read-only preflight records `rpc_endpoint_read=true` and
  `signing_secret_read=false`;
- execution loads the signing secret only after preflight succeeds, then
  records both fields as true;
- preflight calls both fixed ArbSys selectors and stops unless observed
  raw `arbOSVersion()` equals `116`; the approval separately records the
  published Robinhood ArbOS profile `61`, the pinned Nitro offset `55`, and the
  derived expected raw return `61 + 55 = 116`;
- raw `61`, another incompatible value, a malformed response, and a reverting
  version call each fail closed before nonce/address or signing checks;
- pending nonce disagreement, code already present at the predicted deployment
  address, and signer balance below the approved total-fee cap each fail closed
  during preflight;
- `web3_clientVersion` is recorded only as observed evidence, with an explicit
  statement that it does not prove the pinned Nitro build;
- before every `eth_sendRawTransaction`, the exact signed transaction's locally
  derived hash, nonce, and intended action are written to the sanitized progress
  file;
- a valid RPC-returned transaction hash must equal the locally derived hash;
- an ambiguous RPC failure after possible acceptance leaves the deterministic
  transaction identity journaled; and
- if the second observation in a two-transaction burst fails during broadcast,
  both the first and second signed transaction identities remain journaled; and
- an observation-burst fee-cap stop persists the final stop result, next-burst
  worst-case fee, and projected total fee before raising.

No raw signed transaction or signing secret is written to the progress record.

## 5. Commands and sanitized results

Commands were run from
`/Users/wigglez/dev/ripe-protocol-track-6-s5-ledger-guard-recreation` with the
non-secret `ETHERSCAN_API_KEY=local-placeholder` required by repository plugin
import. The authoritative interpreter was the retained, previously approved
H-01 Candidate A environment:

```text
/private/tmp/h01-final-review.dL2pqo/candidate/bin/python
Python 3.12.0
Vyper 0.4.3 / compiler 0.4.3+commit.bff19ea2
Titanoboa 0.2.7
pytest 8.4.2
cbor2 5.9.0
python -m pip check: no broken requirements
```

No package was installed or refreshed. The audit-point result set, binding to
local commit `2f6a49b6c82e69bda54f2fd64d2fe03132e0db21`, was:

| Command/suite | Result |
| --- | --- |
| `python -m py_compile scripts/probes/action_block_identity_probe.py tests/probes/test_action_block_identity_probe.py` | exit `0` |
| `python scripts/probes/action_block_identity_probe.py --dry-run` | exit `0`; `rpc_contacted=false`, `rpc_endpoint_read=false`, `signing_secret_read=false`, `broadcast_enabled=false` |
| `python -m pytest -q tests/deployment/test_dependency_gate.py` | 16 passed in 1.46 s |
| `python -m pytest -q tests/probes/test_action_block_identity_probe.py` | 30 passed in 27.35 s; 64.23 s wall |
| `python -m pytest -q tests/probes` | 70 passed in 31.65 s; 73.79 s wall |
| `python -m pytest -q tests/data/test_ledger.py` | 101 passed in 28.53 s; 65.69 s wall |
| `python -m pytest -q tests/config/test_switchboard_delta.py` | 109 passed in 113.05 s; 150.48 s wall; 3 cache-redirection assert-rewrite warnings |
| `python -m pytest -q tests/core/teller/test_teller_deposit.py` | 26 passed in 28.89 s; 66.21 s wall |
| `python -m pytest -q tests/core/teller/test_teller_withdraw.py` | 32 passed in 32.05 s; 68.86 s wall |
| `python -m pytest -q tests/core/teller/test_teller_rebalance.py` | 22 passed in 28.98 s; 65.82 s wall |
| `python -m pytest -q tests/core/creditEngine/test_credit_borrow.py` | 39 passed in 30.96 s; 68.19 s wall |
| `python -m pytest -q tests/core/creditEngine/test_credit_repay.py` | 17 passed in 29.96 s; 67.97 s wall |
| `python -m pytest -q tests/vaults/modules/test_stab_vault_claims.py` | 51 passed in 33.01 s; 71.41 s wall |
| `python -m pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 28.47 s; 69.08 s wall |
| `python -m pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed in 26.74 s; 27.96 s wall |
| `python -m pytest --collect-only -q` | 2,768 selected / 2,910 total; 142 deselected in 5.07 s; 6.51 s wall |
| complete serial `python -m pytest -q -p no:cacheprovider` | 2,768 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 313.58 s; 373.49 s wall |

The separate uncommitted post-review hardening delta produced:

| Command/suite | Result |
| --- | --- |
| `python -m py_compile scripts/probes/action_block_identity_probe.py tests/probes/test_action_block_identity_probe.py` | exit `0` |
| `python scripts/probes/action_block_identity_probe.py --dry-run` | exit `0`; no RPC/secret read; all source and artifact hashes unchanged |
| `python -m pytest -q tests/deployment/test_dependency_gate.py` | 16 passed in 1.49 s; 2.37 s wall |
| `python -m pytest -q tests/probes/test_action_block_identity_probe.py` | 35 passed in 26.90 s; 63.98 s wall |
| `python -m pytest -q tests/probes` | 75 passed in 31.24 s; 73.04 s wall |
| `python -m pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 27.18 s; 64.62 s wall |
| `python scripts/check_block_clock_inventory.py --check` | expected exit `1`; the same seven `INV-CADENCE-NEW` findings and one `INV-PATH-NEW` finding, all caused by the authorized test-only probe package |
| `python -m pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed in 26.08 s; 26.97 s wall |
| eight required targeted regression files | 397 passed, 3 cache-redirection assert-rewrite warnings in 52.59 s; 91.64 s wall |
| `python -m pytest --collect-only -q` | 2,773 selected / 2,915 total; 142 deselected, 3 cache-redirection assert-rewrite warnings in 1.23 s; 2.36 s wall |
| complete serial `python -m pytest -q -p no:cacheprovider` | 2,773 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 297.06 s; 352.63 s wall |

The probe contract and all five compiled artifact identities in section 3 are
unchanged. Merging the probe package while the eight S2 findings remain would
break the clean-S2 invariant consumed by other workstreams. A future merge
therefore requires an owner-approved probe-inventory or removal disposition;
this record does not authorize Stage C or an inventory edit.

The dry-run reproduced exactly:

```text
required_chain_id=46630
native_value_wei=0
token_transfer=false
arb_block_number_selector=0xa3b1b31d
arb_os_version_selector=0x051038f2
robinhood_published_arb_os_profile=61
pinned_nitro_arb_sys_version_offset=55
required_approved_arb_sys_arb_os_version_return=116
version_return_derivation=61 + 55 = 116
creation_bytecode_keccak256=0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333
runtime_bytecode_keccak256=0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56
```

The S2 checker exited `1` with exactly seven `INV-CADENCE-NEW` findings and one
`INV-PATH-NEW` finding. They cover the new test-only contract path, its
`readActionBlocks` identifier, five runner result keys, and the matching test
identifier. This is an expected consequence of leaving the S2 inventory
untouched under the Stage A/Stage C boundary, not a production inclusion. It
remains a blocker for later inventory reconciliation; it was not bypassed or
hidden.

The five-file probe package therefore must not merge into `rh` while these
findings remain. Doing so would break the clean-S2 invariant used by other
workstream gates. Before any future integration, the owner must approve a
reviewed disposition for the probe files and their inventory treatment; this
record does not authorize that Stage C-adjacent decision or any inventory edit.

The inherited `ripe-lite` interpreter was tested diagnostically and is not
authoritative: its H-01 gate reported 15 passed and one failed because installed
`cbor2 5.7.0` did not match the integrated lock's `5.9.0`. No dependency was
changed. The retained H-01 Candidate A interpreter matched the lock and passed
16/16. A first `switchboard_delta` collection attempt also hit the managed
sandbox's protected default Titanoboa cache. The unchanged suite passed after
preloading Boa solely to set its cache to
`/private/tmp/s5-recreation-cache/titanoboa`; that preload produced the three
reported `PytestAssertRewriteWarning` lines and no test skip or xfail.

The displayed dry-run lines are a sanitized rendering of the runner's JSON
report. They contain no RPC URL, credential, private key, or secret.

## 6. Live topology matrix

| Required observation | Status | Evidence |
| --- | --- | --- |
| emitted ArbSys value equals every receipt child `blockNumber` | **NOT ATTEMPTED / INCONCLUSIVE** | no approved RPC or transaction |
| two separate transactions in the same child block share ArbSys identity | **NOT ATTEMPTED / INCONCLUSIVE** | no approved transaction bound or fees |
| transactions in successive child blocks have distinct ArbSys identities | **NOT ATTEMPTED / INCONCLUSIVE** | no approved transaction bound or fees |
| successive child blocks share native ancestor `block.number` | **NOT ATTEMPTED / INCONCLUSIVE** | no live observations |
| bounded repeated/advancing-value observation | **NOT ATTEMPTED / INCONCLUSIVE** | no live observations; no maximum claim made |

No probe address, deployment transaction, observation transaction, receipt,
timestamp, or fee exists to record. Those fields are not zero and are not
fabricated; they are absent because execution stopped before RPC preflight.

## 7. Runner preflight and execution gates

The runner accepts three mutually exclusive modes:

- `--dry-run`: local compilation only; rejects live approval flags and does
  not read RPC or signer environment variables and reports both access fields
  false;
- `--preflight`: read-only RPC checks after a complete secret-free approval
  file; reports endpoint access true and signing-secret access false; and
- `--execute --confirm-live-testnet --output <sanitized-json>`: testnet
  broadcast only after the same preflight succeeds; only then is the approved
  signing secret loaded and both access fields become true. The required output
  is updated before each send and as RPC results/receipts arrive so a stopped
  attempt retains sanitized progress evidence.

It fails closed unless all of the following match:

- exact chain ID `46630`;
- exact approved RPC endpoint SHA-256 and owner reference;
- exact `ArbSys(0x64).arbOSVersion()` agreement with an explicitly approved
  raw return `116`, derived from separately approved published Robinhood ArbOS
  profile `61` plus the pinned Nitro offset `55`;
- approved signer address and explicit approval to use its existing testnet gas
  funds;
- exact pending nonce and predicted CREATE address, with no existing code;
- exact creation and runtime bytecode hashes;
- fixed `0x64`/`arbBlockNumber()` 32-byte response;
- deployment and observation gas estimates within approved limits;
- zero native value and no token transfer;
- approved EIP-1559 fee limits and maximum total fee; and
- an owner-approved bound of 4–16 observation transactions.

For every deployment or observation, signing deterministically produces the
raw transaction locally; only its keccak-256 hash, nonce, and intended action
are persisted before `eth_sendRawTransaction`. The RPC-returned hash must match
that local hash. A timeout/error after submission is marked as acceptance
ambiguous, and a second-burst-send failure cannot erase either signed
transaction identity. Both conditions stop further broadcasting.

Observations are attempted in bounded two-transaction bursts to seek a
same-child pair. If the allowed bound does not yield every required topology,
the result is `inconclusive-within-approved-bound`; the runner does not weaken
or manufacture a conclusion. Its bounded-observation summary expressly does
not claim that any observed jump or repetition is a protocol maximum.

## 8. Dated source pins

These source identities were pinned on 24 July 2026:

| Source | Pin |
| --- | --- |
| Robinhood published Nitro image | `offchainlabs/nitro-node:v3.11.2-3599aca` |
| Robinhood published ArbOS profile | `61` |
| Pinned Nitro `ArbSys.arbOSVersion()` offset | `55` |
| Derived expected raw `ArbSys.arbOSVersion()` return | `116` (`61 + 55`) |
| Offchain Labs Nitro | `3599acae1ad2fab4059fc46453c9cd3294126641` |
| Nitro precompile interfaces | `7e88c8cc53c2e96201a23c638f1536557b9cb68b` |

At the pinned Nitro commit, `precompiles/ArbSys.go` computes
`55 + c.State.ArbOSVersion()`; the pinned `ArbSys.sol` interface independently
documents the same `55` offset. The expected raw return is therefore derived,
not assumed: Robinhood profile `61 + 55 = 116`. These pins support the expected
ABI and address but do not replace the missing live Robinhood testnet
observation. A future preflight records the RPC's observed
`web3_clientVersion`, but that self-reported string is not accepted as proof
that the endpoint runs the pinned Nitro build. The independently approved and
directly observed raw `arbOSVersion()` return comparison is a separate hard
gate.

## 9. Inputs and approvals required before any RPC contact

The owner and independent security/deployment reviewers must provide or approve
all of the following in a secret-free approval record:

1. exact Robinhood testnet RPC endpoint label, environment-variable name, and
   SHA-256 fingerprint;
2. explicitly approved published Robinhood ArbOS profile `61` and expected raw
   `ArbSys.arbOSVersion()` return `116`, with the relationship
   `61 + 55 = 116` tied to the pinned Nitro source;
3. exact testnet signer address and private-key environment-variable name,
   without exposing the key;
4. explicit approval to use that signer and its existing testnet gas funds;
5. a freshly approved pending nonce and predicted probe deployment address;
6. the exact artifact hashes in section 3;
7. deployment and observation gas limits;
8. maximum fee per gas, maximum priority fee, and an explicit maximum total fee
   in wei;
9. bounded observation transaction count, from 4 through 16;
10. receipt timeout of at most 300 seconds; and
11. a dated owner approval reference for this exact testnet-only scope.

Only after those inputs exist may the operator run read-only `--preflight`.
The live command remains separately gated by `--confirm-live-testnet`. No one
should place a URL or private key in the approval file, command line, evidence
record, or repository.

## 10. Secret-free live-proof authorization packet

The packet below is the complete §8.2 field set and the exact runner schema,
with all immutable local facts populated. It is deliberately **not executable
authorization**: every unavailable or unapproved live value is `null` or
`false`, and `live_testnet_approved` is false. The runner therefore rejects it
before reading an RPC environment variable. A later operator must copy the
packet to a non-repository, access-controlled location, replace every pending
field from dated approvals, independently recompute the endpoint fingerprint,
nonce-derived address, artifact identities, and worst-case fee bound, and
obtain review of the completed packet hash. Neither an RPC URL nor a private
key belongs in the packet.

The proposed environment-variable names are non-secret labels. They are not
evidence that either variable exists, and this recreation did not inspect
either one.

<!-- BEGIN S5_SECRET_FREE_AUTHORIZATION_PACKET -->
```json
{
  "schema_version": 2,
  "scope": "robinhood-testnet-action-block-proof",
  "network": "Robinhood Chain testnet",
  "chain_id": 46630,
  "robinhood_published_arb_os_profile": 61,
  "expected_arb_sys_arb_os_version_return": 116,
  "live_testnet_approved": false,
  "owner_approval_reference": null,
  "approval_provenance": {
    "owner": {
      "name": "Mick Hagen",
      "approved": false,
      "decision_date": null,
      "reference": null
    },
    "independent_security": {
      "reviewer_name": null,
      "approved": false,
      "decision_date": null,
      "reference": null
    },
    "deployment": {
      "approver_name": null,
      "approved": false,
      "decision_date": null,
      "reference": null
    }
  },
  "rpc": {
    "approved": false,
    "label": null,
    "url_environment_variable": "ROBINHOOD_TESTNET_RPC_URL",
    "url_sha256": null
  },
  "signer": {
    "approved": false,
    "funding_approved": false,
    "address": null,
    "private_key_environment_variable": "ROBINHOOD_TESTNET_PRIVATE_KEY",
    "expected_nonce": null
  },
  "probe": {
    "expected_address": null,
    "source_sha256": "0x95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5",
    "abi_sha256": "0x2c237ba7e43aa009c69eabe950c733c79415b7eab37e874e065494273a45b359",
    "compiler_inputs_sha256": "0xf251237b97029e29122f5578c38817e518abcc3062c6d32019de028bdef79a65",
    "creation_bytecode_keccak256": "0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333",
    "runtime_bytecode_keccak256": "0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56",
    "arb_sys_address": "0x0000000000000000000000000000000000000064",
    "arb_block_number_selector": "0xa3b1b31d",
    "arb_os_version_selector": "0x051038f2"
  },
  "fees": {
    "owner_approved": false,
    "deployment_gas_limit": null,
    "observation_gas_limit": null,
    "max_fee_per_gas_wei": null,
    "max_priority_fee_per_gas_wei": null,
    "max_total_fee_wei": null
  },
  "execution": {
    "max_observation_transactions": 16,
    "receipt_timeout_seconds": 300,
    "topology_cases": [
      "each emitted ArbSys value equals its receipt blockNumber",
      "two separate transactions included in one child block",
      "transactions included in successive child blocks",
      "successive child blocks sharing one native ancestor block.number",
      "bounded repeated and advancing values without a protocol-maximum claim"
    ],
    "stop_on_inconclusive_bound": true,
    "native_value_wei": 0,
    "token_transfer": false
  },
  "source_pins": {
    "evidence_date": "2026-07-24",
    "robinhood_node_image": "offchainlabs/nitro-node:v3.11.2-3599aca",
    "nitro_commit": "3599acae1ad2fab4059fc46453c9cd3294126641",
    "arb_sys_interface_commit": "7e88c8cc53c2e96201a23c638f1536557b9cb68b",
    "pinned_nitro_arb_sys_version_offset": 55,
    "version_return_derivation": "61 + 55 = 116"
  }
}
```
<!-- END S5_SECRET_FREE_AUTHORIZATION_PACKET -->

The exact newline-terminated JSON body above has SHA-256
`5e8a7b5993cd8ccff1ef05980d1eb24d3133bdecf98e2b1c6b6a0a670ec9e321`.
It parses as JSON but fails runner authorization by design because live and
approval fields remain false or null. Direct local parser validation returned
`packet_fail_closed=live Robinhood testnet execution is not approved` before
any endpoint or signing-secret read.

The proposed maximum is 16 observation transactions plus one deployment
transaction. The owner may approve a smaller observation bound from 4 through
16; the exact approved value must replace the proposal before preflight. The
worst-case total fee is:

```text
(deployment_gas_limit
 + observation_gas_limit * max_observation_transactions)
* max_fee_per_gas_wei
```

That value must be less than or equal to the separately approved
`max_total_fee_wei`. Preflight must also prove that the signer balance covers
the approved cap and that the current base fee plus priority cap does not exceed
the approved maximum fee per gas.

Before any RPC contact, an independent security reviewer must verify this
completed packet against the exact five-file hashes, baseline `02787d3`, the
pinned Nitro derivation, and runner behavior. The owner, that reviewer, and the
deployment approver must each supply a dated name/reference and approve the
same completed packet hash. Before execution, the operator must retain the
sanitized preflight report and obtain confirmation that its observed nonce,
predicted address, chain ID, raw ArbSys version `116`, artifact hashes, gas
estimates, and fee arithmetic still match the approved packet.

## 11. Remaining Checkpoint 0 blockers

No Checkpoint 0 row is closed. The integrated owner packet records the owner
states below, while every named independent-security, operations, live-proof,
deployment, final-evidence, and external-review gate remains open:

0. owner approved; independent-security validation of the exact recreation
   remains pending;
1. owner approved; independent-security acceptance of the one-immutable source
   discriminator remains pending;
2. owner approved in principle; the live `0x64`/receipt proof, approved profile
   `61`, observed derived raw return `116`, and security closure remain pending;
3. owner approved; independent-security acceptance of current any-touch arming
   semantics remains pending;
4. owner approved; independent-security confirmation of the unchanged
   six-action high-risk set remains pending;
5. owner approved; security acceptance of the preserved Underscore exemption
   and initial RH omission remains pending;
6. owner approved; security acceptance and mandatory Stage B reachability
   evidence for current identity/zero-address behavior remain pending;
7. owner directly accepted the external-housekeeping risk; independent-security
   approval remains pending;
8. owner approved; security and operations approval of unchanged
   Boolean/governance/defaults and source-getter-only diagnostics remain
   pending;
9. owner directly accepted fail-closed repayment/liquidation unavailability;
   independent-security approval remains pending;
10. owner approved the permanent deployed-Base Ledger exception; security and
    operations ownership remain pending;
11. H-01 integration and exact-baseline recreation are satisfied; independent
    S5 security review of this five-file recreation remains pending;
12. owner approved the exact Stage B file ceiling; independent-security
    approval remains pending; and
13. owner approved in principle; the completed live proof, final evidence,
    deployment approval, testnet soak, and explicit targeted-external-review
    decision remain pending.

Until those blockers close, the result remains no Stage B, no production
Ledger implementation, no merge, no push, no deployment, and no governance
action.
