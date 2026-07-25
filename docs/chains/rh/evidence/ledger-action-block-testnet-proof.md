# S5 Robinhood Testnet Action-Block Probe Evidence

**Status:** Frozen local probe evidence recreated on exact integrated baseline
`02787d3`; authoritative post-H-01 validation, exact-package independent
review, and the complete secret-free authorization template are recorded; live
Robinhood testnet proof not attempted because required approvals and live
inputs are absent

**Evidence date:** 24 July 2026

**Provenance correction:** 25 July 2026

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

The subsequent post-review hardening delta changed the runner, focused tests,
decision record, and this evidence record. It did not change the test-only
Vyper probe. It was committed locally at
`0a3414ade0ba6914f8f69b7cdc1205ea3499a26e`, tree
`e63fb85e0fb3097daf48957bfbcaa2ad8de48a84`. The exact SHA-256 identities in
that commit were:

- decision record:
  `d11f70afd00d94a2242b294303302c1deefee134e316b5ed27cf71787613ea20`;
- probe source:
  `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5`;
- runner:
  `135a864356fdfa076acda0009a5e97907afd471215ba5bdfc3dfe1056b4b498b`;
- focused tests:
  `24c5bad958cba5425ec52e060995332302409b1fac01a1967c84b7261a2631b6`;
  and
- evidence record:
  `eeabc12cc987e287ed8a1864a95328ef080659efe43d07bca2795d5c07751e13`.

The audit-point commit was authorized on 24 July 2026 when the owner replied
verbatim to the numbered local-commit question:

> 1. yes
> 2. no attribution

The owner reconfirmed that authority on 25 July 2026:

> My previous authorization of commit
> `2f6a49b6c82e69bda54f2fd64d2fe03132e0db21` also remains valid.

The hardening commit was authorized on 24 July 2026 with the verbatim
instruction:

> The post-review hardening delta is independently approved at the reported
> current hashes. Focused verification reproduced `35 passed`, and the
> standalone S2 checker reproduced exactly seven `INV-CADENCE-NEW` plus one
> `INV-PATH-NEW` finding.
>
> Commit exactly the four currently modified hardening files to
> `rh-track-6-s5-ledger-guard-recreation`, preserving the existing test-only
> Vyper probe unchanged. Return the new commit/tree, five final hashes, exact
> commit scope, and clean worktree status. Do not merge, begin Stage B/C, edit
> the inventory, contact an RPC, sign, broadcast, or modify production Ledger.
>
> After that commit, stop. The next substantive action remains the separately
> authorized Robinhood testnet proof. The probe should be retained until that
> proof is complete. Inventory treatment, current-`rh` reconciliation, Stage B
> implementation, Checkpoint 0 closure, and Gate 2 remain separately gated.

That instruction relied on a reported independent-approval status that was
incorrect at the time. Commit `0a3414a` was made before the contemplated
independent re-review, which was a sequencing deviation from the agreed
uncommitted-delta review boundary. An independent re-review supplied on
24 July 2026 subsequently inspected and approved the exact package at
`0a3414a`, reproducing `35/35` focused tests, `75/75` complete probe tests, and
the exact seven `INV-CADENCE-NEW` plus one `INV-PATH-NEW` S2 result. Per owner
instruction, the reviewer's identity is intentionally neither named nor
inferred. That identity omission does not make the exact-package approval
pending and does not close any broader Checkpoint 0 security decision that the
review did not explicitly approve.

On 25 July 2026, the owner ratified the sequence verbatim:

> 1. I explicitly ratify commit
> `0a3414ade0ba6914f8f69b7cdc1205ea3499a26e` despite the sequencing
> deviation. Record the chronology accurately: I authorized the commit based
> on the independent-approval status reported at that time, while the
> independent approval of the exact post-hardening package actually arrived
> afterward. No revert is required. My previous authorization of commit
> `2f6a49b6c82e69bda54f2fd64d2fe03132e0db21` also remains valid.

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

The committed post-review hardening delta produced:

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
states below. The exact `0a3414a` package review is complete, while every
broader independent-security decision and the remaining operations,
live-proof, deployment, final-evidence, and external-review gates stay open:

0. owner approved; review of the exact `0a3414a` package is complete, while
   independent-security approval of the broader row-0 owner-direction decision
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
11. H-01 integration, exact-baseline recreation, and independent review of the
    exact `0a3414a` package are satisfied; final hash review of this provenance
    correction and formal row disposition remain pending;
12. owner approved the exact Stage B file ceiling; independent-security
    approval remains pending; and
13. owner approved in principle; the completed live proof, final evidence,
    deployment approval, testnet soak, and explicit targeted-external-review
    decision remain pending.

Until those blockers close, the result remains no Stage B, no production
Ledger implementation, no merge, no push, no deployment, and no governance
action.

## 12. Current reconciled row 2 authorization package — pending

This section supersedes section 10 only as the packet to complete for the next
live-proof decision. Section 10 remains historical evidence of the reviewed
`02787d3` recreation package. The current branch is reconciled through
`e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369`; current S5 HEAD at preparation
time is `444b3c91711ab79fc0fa2c36063dd11701481f51`. No incoming reconciliation
changed the probe contract, runner, focused tests, or production Ledger.

No endpoint or signing-secret environment value was read to prepare this
section. No RPC was contacted, no transaction was signed or broadcast, and
every live authorization field remains false or null. The complete packet is
therefore intentionally rejected before either environment variable is read.
The shell-level removal of those two variables from test child processes is
recorded command provenance, not a fact recoverable from result artifacts
afterward; the independently reproducible runner output and tests prove that
dry-run does not read either value and that broadcast remains disabled.

### 12.1 Field classification

| Class | Fields | Meaning |
| --- | --- | --- |
| **verified local/source fact** | network name; chain ID `46630`; source, ABI, compiler-input, creation, and runtime hashes; exact `0x64` address; selectors; published profile `61`; pinned offset `55`; derived raw return `116`; 4–16 runner bound; 300-second maximum; zero-value/no-token rule; endpoint-fingerprint algorithm; redirect prohibition; deterministic pre-broadcast journal/hash comparison; stop behavior | reproduced from the exact local package, runner/tests, integrated profile boundary, and dated source pins; these values are not live endpoint proof |
| **proposed operational value** | endpoint label; environment-variable names; deployment gas limit `500000`; observation gas limit `100000`; 16 observations; 300-second timeout; nonce-selection rule; retry policy; cleanup/retention procedure | a decision-ready bounded proposal, not owner approval and not a claim that live gas estimates fit these ceilings |
| **owner-supplied/approved value** | exact endpoint fingerprint; signer address and approval; funding approval; exact nonce; derived probe address; priority/max/aggregate fee caps; dated approval references; completed-packet approvers | intentionally missing; no value is invented or inferred |
| **live observed value** | endpoint identity responses; `web3_clientVersion`; raw `arbOSVersion()`; pending nonce; balance; code occupancy; gas estimates; deployed address/transactions; receipts; native/ArbSys values; timestamps and actual fees | unavailable until a separately approved preflight/execution; `web3_clientVersion` is evidence only, never proof of the pinned Nitro build |

The proposed gas limits are conservative test-fixture ceilings, not measured
Robinhood estimates. Preflight must stop if either live estimate exceeds its
ceiling. The exact fee caps remain owner-supplied because inventing them without
a dated network observation and explicit approval would defeat the fee gate.
`ROBINHOOD_TESTNET_PRIVATE_KEY` is a probe-runner-specific proposed name, not
an H-02 network-profile binding. H-02 supplies no fixed signing-key environment
name for this proof.

### 12.2 Complete secret-free packet

The endpoint fingerprint procedure is exact: the owner selects the endpoint,
places its full URL only in `ROBINHOOD_TESTNET_RPC_URL`, computes lowercase
hex `SHA-256` over the exact UTF-8 URL bytes with no newline or normalization,
and puts only that 64-hex fingerprint in `rpc.url_sha256`. The runner hashes the
environment value before the first JSON-RPC call and stops on disagreement.
The URL and credential must never appear in a command line, packet, journal,
test output, evidence record, or repository. HTTP redirects are disabled and a
3xx response is a hard failure.

The nonce rule is also exact: the owner must approve one signer address, its
exact pending nonce, and the corresponding CREATE address derived as the final
20 bytes of `keccak256(rlp([signer_address, expected_nonce]))`. The derived
address is entered in `probe.expected_address`; preflight independently reads
the pending nonce, recomputes the address, and proves `eth_getCode` is `0x`.
The signer must have at least the owner-approved aggregate fee cap in existing
testnet gas funds. No token transfer and no transaction value are permitted;
only the bounded testnet gas cost is allowed.

<!-- BEGIN S5_CURRENT_SECRET_FREE_AUTHORIZATION_PACKET -->
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
      "approved": false,
      "decision_date": null,
      "reference": null
    },
    "independent_security": {
      "approved": false,
      "decision_date": null,
      "reference": null
    },
    "deployment": {
      "approved": false,
      "decision_date": null,
      "reference": null
    }
  },
  "rpc": {
    "approved": false,
    "label": "robinhood-testnet-owner-selected-endpoint",
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
    "deployment_gas_limit": 500000,
    "observation_gas_limit": 100000,
    "max_fee_per_gas_wei": null,
    "max_priority_fee_per_gas_wei": null,
    "max_total_fee_wei": null
  },
  "execution": {
    "max_observation_transactions": 16,
    "receipt_timeout_seconds": 300,
    "topology_cases": [
      "each emitted ArbSys value equals its receipt blockNumber",
      "two separate transactions included in one child block share one ArbSys identity",
      "transactions included in successive child blocks have distinct ArbSys identities",
      "successive child blocks share one native ancestor block.number",
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
<!-- END S5_CURRENT_SECRET_FREE_AUTHORIZATION_PACKET -->

The exact newline-terminated JSON body above has SHA-256
`277f3628853b5ff06d65f22611358e08e521fe05afc0dd91b58692dd91026534`.
It parses as JSON and is intentionally non-executable.

Before preflight, the owner-supplied fields must replace every null and all
eight approval Booleans must be true:

1. `live_testnet_approved`;
2. `approval_provenance.owner.approved`;
3. `approval_provenance.independent_security.approved`;
4. `approval_provenance.deployment.approved`;
5. `rpc.approved`;
6. `signer.approved`;
7. `signer.funding_approved`; and
8. `fees.owner_approved`.

Each provenance role requires its dated decision and nonempty reference, and
`owner_approval_reference` must match the owner provenance reference. The
owner must approve:

- exact endpoint fingerprint and the proposed endpoint label;
- exact signer address and use of its existing testnet gas funds;
- exact pending nonce and independently derived probe address;
- maximum priority fee, maximum fee per gas, and aggregate fee cap in wei;
- the proposed `500000` deployment and `100000` observation gas ceilings;
- the proposed 16-observation/17-total-transaction ceiling and 300-second
  receipt timeout; and
- the completed packet SHA-256 and exact testnet-only scope.

The minimum funding is the approved `max_total_fee_wei`; the worst-case formula
remains:

```text
(500000 + 100000 * 16) * max_fee_per_gas_wei
<= max_total_fee_wei
<= signer_balance_wei
```

The fee packet is invalid if the aggregate cap is below that formula, if the
priority fee exceeds the max fee, or if the latest base fee plus priority cap
exceeds the max fee. Gas estimation, transaction formation, and every
observation remain bounded by those same ceilings.

### 12.3 Fail-closed execution and evidence contract

The runner may perform no blind transaction retry. It may poll a known
locally-derived transaction hash for its receipt within the approved timeout,
but it must never resend after an ambiguous `eth_sendRawTransaction` failure
without separate reconciliation and new approval. Before each send it writes
the signed transaction's deterministic local hash, nonce, and intended action
to the sanitized journal. The RPC-returned hash must equal the local hash. An
ambiguous acceptance failure, a failure while sending the second transaction
in a burst, or a local/RPC hash disagreement stops the run with every prepared
transaction still recorded.

The following are hard stops, not warnings:

1. endpoint SHA-256 disagreement, redirect, transport error, wrong chain ID, or
   incompatible RPC identity;
2. source/compiler/artifact hash disagreement;
3. approved profile other than `61`, expected raw return other than the pinned
   derivation `61 + 55 = 116`, missing/reverting/malformed
   `arbOSVersion()`, or observed raw return other than `116`;
4. missing/reverting/malformed `arbBlockNumber()` or disagreement between
   `0x64` and receipt child-block identity;
5. pending nonce disagreement, predicted-address disagreement, or nonempty
   code at the predicted address;
6. unapproved signer/funding, signer address mismatch, or signer balance below
   the aggregate cap;
7. gas estimate above its approved limit, fee arithmetic outside any approved
   cap, or projected/actual total fee above the aggregate cap;
8. signed/local/RPC transaction-hash disagreement or any ambiguous possible
   acceptance; and
9. any attempt to touch mainnet, Base, governance, production contracts, token
   value, or user funds.

Within the 16-observation bound, sanitized evidence must attempt and record:

- direct equality of every emitted in-contract ArbSys value and that
  transaction receipt's `blockNumber`;
- two distinct transactions in one child block with the same ArbSys identity;
- transactions in successive child blocks with distinct ArbSys identities;
- successive child blocks sharing one native ancestor `block.number`;
- bounded repeated and advancing values without treating the largest observed
  repetition or jump as a protocol maximum; and
- deployed address, deployment and observation transaction hashes, locally
  derived hashes, nonces, actions, exact source/ABI/compiler/bytecode hashes,
  chain/RPC label and fingerprint, raw version result, receipt block numbers,
  native/ArbSys values, timestamps, gas, effective fee, total fee, and dated
  source pins.

If the topology is not observed within the approved bound, the outcome is
`INCONCLUSIVE`; the bound is not extended and the conclusion is not weakened.
The minimal probe has no destruction function, so no onchain cleanup
transaction exists or is authorized. Post-run cleanup means ending this packet's
signer/endpoint authority, clearing transient process access to both
environment values, and retaining the deployed test-only address as dated
evidence. Retain only the sanitized packet, preflight report, transaction
journal, receipts/observations, totals, hashes, and decision references; retain
no URL, credential, signing secret, or other secret.

**Copy-ready owner authorization sentence (not yet approved):**

> I authorize only the Robinhood Chain testnet action-block proof described by
> the completed secret-free packet with SHA-256
> `[COMPLETED_PACKET_SHA256]`, using endpoint label
> `[APPROVED_ENDPOINT_LABEL]` whose exact URL is held only in
> `ROBINHOOD_TESTNET_RPC_URL` and hashes to `[ENDPOINT_SHA256]`, approved signer
> `[SIGNER_ADDRESS]` whose private key is held only in
> `ROBINHOOD_TESTNET_PRIVATE_KEY`, nonce `[NONCE]`, predicted deployment
> address `[PREDICTED_ADDRESS]`, deployment gas limit `[DEPLOYMENT_GAS]`,
> observation gas limit `[OBSERVATION_GAS]`, maximum priority fee
> `[MAX_PRIORITY_FEE_WEI]` wei, maximum fee `[MAX_FEE_PER_GAS_WEI]` wei,
> aggregate fee cap `[MAX_TOTAL_FEE_WEI]` wei, at most
> `[OBSERVATION_COUNT]` observation transactions plus one deployment, and a
> receipt timeout of `[TIMEOUT_SECONDS]` seconds. I approve use of only that
> signer's existing Robinhood testnet gas funds up to the aggregate cap. The
> run must enforce chain ID `46630`, exact `0x64`, published profile `61`,
> pinned offset `55`, raw `arbOSVersion()` return `116`, the packet's artifact
> hashes, deterministic pre-broadcast transaction journaling and hash
> agreement, no redirects, every stated stop condition, zero transaction value
> and token transfer, bounded inconclusive topology handling, and sanitized
> evidence retention. This authorizes no mainnet or Base action, user-fund or
> governance action, production Ledger work, Stage B/C, merge, push,
> deployment other than the test-only probe, cleanup transaction, or reuse of
> the signer/endpoint outside this exact proof.

Until that sentence is completed with exact values and explicitly adopted,
row 2 remains open and neither preflight nor execution is authorized.

## 13. Exact `cb3fe739` H-02 reconciliation evidence — 25 July 2026

This section records the owner-authorized reconciliation and complete
non-live validation after rows 8 and 10 were approved and committed. It does
not modify or complete the section 12 row 2 packet, authorize preflight, or
record live evidence. Decision-record section 20 quotes the controlling owner
reconciliation instruction verbatim.

### 13.1 Identity, scope, and merge

Immediately before merge:

```text
branch: rh-track-6-s5-ledger-guard-recreation
HEAD: fe66f595e58acf840ed9928e6bb60e28be4ebf05
local rh: cb3fe7392c44613aaeec49bd2486369fe0da3556
cached origin/rh: cb3fe7392c44613aaeec49bd2486369fe0da3556
live origin refs/heads/rh: cb3fe7392c44613aaeec49bd2486369fe0da3556
merge-base: e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369
topology, rh...HEAD: 2 left / 10 right
worktree/index: clean
```

The incoming range contained exact H-02 correction commit
`5c1ba54c5d34670ddba13ce84e46f490f8a8aaa4` and its `rh` merge
`cb3fe7392c44613aaeec49bd2486369fe0da3556`. Complete path scope and
post-merge SHA-256 values:

| Incoming path | SHA-256 |
| --- | --- |
| `config/network_profiles.py` | `9c19d237eaa049a9d521fc3ab8ef868e6ee35ab6ba48c45e61180fa2daf8c42a` |
| `docs/chains/rh/evidence/network-profile-cli-implementation.md` | `79cf2f7e5c362b8880f2c460abac946126bf2f329425a82e3c8f5bd4da9a8de7` |
| `scripts/console.py` | `a7f0c2b15db0634398dbf975bd40fe5cb449a96e7da6ff5a1c9159df75ec5f6a` |
| `scripts/migrate.py` | `6401e3fe35f29981378bb187a4070b1b0a75e6f7105204269e65aeef4aa6a12c` |
| `tests/deployment/test_base_profile_regression.py` | `6da51a700e7a8a914ee541b594fa4bb4cb45df6b2a62842695898f2e467f9ecb` |
| `tests/deployment/test_network_profiles.py` | `9178b2a13c7c6a6102c21d592d609ccd2ab1dea099450397f17ca9ddd81dd7c6` |
| `tests/deployment/test_secret_handling.py` | `ac27dcb31f4c17459cb45847ec904237bf790225b53184d3d2e2e4e95cdee2f3` |

The incoming diff was whitespace-clean and exactly 378 insertions / 10
deletions. It added no S5-owned path and produced no conflict. The authorized
normal merge was:

```text
merge: f934cf4513f55db66ffb120a51b1c4fe9791c9ed
tree: aca2bd5aa0d4cc6fc83363eb638e3a9fc4c4915a
first parent: fe66f595e58acf840ed9928e6bb60e28be4ebf05
second parent: cb3fe7392c44613aaeec49bd2486369fe0da3556
subject: Merge commit 'cb3fe7392c44613aaeec49bd2486369fe0da3556' into rh-track-6-s5-ledger-guard-recreation
```

`fe66f595…` and both merge parents are ancestors of `f934cf4…`. After merge
and after all validation, local/cached/live `rh` remained exact `cb3fe739…`,
the merge-base was `cb3fe739…`, and the branch was 11 ahead / 0 behind.

### 13.2 Locked runtime and exact commands

The existing integrated H-01 Candidate A interpreter was reused without
installation or modification:

```text
interpreter: /private/tmp/h01-final-review.dL2pqo/candidate/bin/python
Python: 3.12.0
Vyper: 0.4.3
pytest: 8.4.2
Titanoboa: 0.2.7
cbor2: 5.9.0
requirements.txt SHA-256:
  d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce
pip check: No broken requirements found.
task root: /private/tmp/s5-cb3-validation
task-root mode: 0700
```

Every non-H-02 pytest command used this exact launcher shape, with the table's
literal cache path and pytest arguments substituted:

```bash
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  -u BASE_MAINNET_RPC_URL -u BASE_SEPOLIA_RPC_URL \
  -u ROBINHOOD_MAINNET_RPC_URL -u ROBINHOOD_TESTNET_RPC_URL \
  -u ROBINHOOD_TESTNET_PRIVATE_KEY -u DEPLOYER_PRIVATE_KEY \
  -u PYTHON_DOTENV_DISABLED \
  ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-final-review.dL2pqo/candidate/bin/python -c \
  'from boa.interpret import set_cache_dir; set_cache_dir("<CACHE>"); import pytest; raise SystemExit(pytest.main(<ARGS>))'
```

The integrated H-02 suite used the same launcher but set
`PYTHON_DOTENV_DISABLED=1` instead of unsetting it, matching H-02's profile
test boundary. No environment-variable value was printed or recorded.

| Scope | `<CACHE>` and exact `<ARGS>` | Result |
| --- | --- | --- |
| H-01 | `/private/tmp/s5-cb3-validation/boa-h01`; `["-q","-p","no:cacheprovider","tests/deployment/test_dependency_gate.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-h01"]` | `16 passed, 3 warnings in 1.60s` |
| H-02 combined | `/private/tmp/s5-cb3-validation/boa-h02`; `["-q","-p","no:cacheprovider","tests/deployment/test_network_profiles.py","tests/deployment/test_secret_handling.py","tests/deployment/test_base_profile_regression.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-h02"]` | `99 passed, 3 warnings in 13.62s` |
| focused S5 probe | `/private/tmp/s5-cb3-validation/boa-focused`; `["-q","-p","no:cacheprovider","tests/probes/test_action_block_identity_probe.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-focused"]` | `35 passed, 3 warnings in 27.55s` |
| complete probes | `/private/tmp/s5-cb3-validation/boa-probes`; `["-q","-p","no:cacheprovider","tests/probes","--basetemp=/private/tmp/s5-cb3-validation/pytest-probes"]` | `75 passed, 3 warnings in 31.99s` |
| S1 | `/private/tmp/s5-cb3-validation/boa-s1`; `["-q","-p","no:cacheprovider","tests/clock/test_clock_profiles.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-s1"]` | `57 passed, 3 warnings in 103.91s` |
| S2 | `/private/tmp/s5-cb3-validation/boa-s2`; `["-q","-p","no:cacheprovider","tests/inventory/test_block_clock_inventory.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-s2"]` | `60 passed, 3 warnings in 25.47s` |
| nine-file target | `/private/tmp/s5-cb3-validation/boa-targeted`; `["-q","-p","no:cacheprovider","tests/data/test_ledger.py","tests/config/test_switchboard_delta.py","tests/core/teller/test_teller_deposit.py","tests/core/teller/test_teller_withdraw.py","tests/core/teller/test_teller_rebalance.py","tests/core/creditEngine/test_credit_borrow.py","tests/core/creditEngine/test_credit_repay.py","tests/vaults/modules/test_stab_vault_claims.py","tests/core/deleverage/test_deleverage_swap_collateral.py","--basetemp=/private/tmp/s5-cb3-validation/pytest-targeted"]` | `437 passed, 3 warnings in 134.58s` |
| collection | `/private/tmp/s5-cb3-validation/boa-collection`; `["--collect-only","-q","-p","no:cacheprovider","--basetemp=/private/tmp/s5-cb3-validation/pytest-collection"]` | `2,872/3,014 collected, 142 deselected, 3 warnings in 1.55s` |
| full serial | `/private/tmp/s5-cb3-validation/boa-full`; `["-q","-p","no:cacheprovider","--basetemp=/private/tmp/s5-cb3-validation/pytest-full"]` | `2,872 passed, 142 deselected, 3 warnings in 304.53s` |

The standalone checker command was:

```bash
PYTHONPATH=. \
  /private/tmp/h01-final-review.dL2pqo/candidate/bin/python \
  scripts/check_block_clock_inventory.py --check
```

It produced expected exit `1` in 1.33 seconds wall time with exactly:

- seven `INV-CADENCE-NEW` findings: one test-only Vyper identifier, five
  runner evidence keys, and one focused-test identifier; and
- one `INV-PATH-NEW` for
  `contracts/testing/ActionBlockIdentityProbe.vy`.

Every finding belonged to the isolated S5 probe package; there was no ninth
finding and no production/incoming-H-02 finding. Inventory remains unchanged
and the eight findings remain assigned to separately gated Stage C.

Every pytest command reported only the three established
`PytestAssertRewriteWarning` notices for `_hypothesis_globals`, `hypothesis`,
and `boa`, which were already imported by the cache-redirection launcher. The
outer login shell also printed its pre-existing pyenv-shim rehash warning, and
`pip check` printed the pre-existing disabled-user-cache warning before
reporting no broken requirements. Neither warning changed the locked
interpreter, collected tests, or results.

### 13.3 Unchanged S5 identities and stop

The exact S5 and inventory identities at merge commit `f934cf4…` were:

| Path/artifact | Identity |
| --- | --- |
| production `contracts/data/Ledger.vy` | SHA-256 `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0`; Git blob `ef02462508e01f59e8f8112ffce0ca8d17d4d0b8` |
| `contracts/testing/ActionBlockIdentityProbe.vy` | SHA-256 `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5`; Git blob `82a56a6770d07b6330ca19d55df10f05bef5e105` |
| `scripts/probes/action_block_identity_probe.py` | SHA-256 `135a864356fdfa076acda0009a5e97907afd471215ba5bdfc3dfe1056b4b498b`; Git blob `0bea5c3fb3991097e1e4ae0e57fdcbaf36779f74` |
| `tests/probes/test_action_block_identity_probe.py` | SHA-256 `24c5bad958cba5425ec52e060995332302409b1fac01a1967c84b7261a2631b6`; Git blob `5ccfb6eafbf05dcf260dfd5658723c7e587c8d93` |
| probe ABI | SHA-256 `0x2c237ba7e43aa009c69eabe950c733c79415b7eab37e874e065494273a45b359` |
| probe compiler inputs | SHA-256 `0xf251237b97029e29122f5578c38817e518abcc3062c6d32019de028bdef79a65` |
| probe creation bytecode | Keccak-256 `0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333` |
| probe runtime bytecode | Keccak-256 `0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56` |
| `config/block-clock-inventory.json` | SHA-256 `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb`; Git blob `e3e08b2e45aebcdddbf16faa6fcf99e2f908e6a9` |
| committed row 2 JSON body | SHA-256 `277f3628853b5ff06d65f22611358e08e521fe05afc0dd91b58692dd91026534` |

Before this documentation update, the committed decision record was
`e99d8917132aae49bccb7ddab2fb57e2bf7e27c0c54a499226fcf3cabb77f0b2`
and this evidence record was
`457675670886304a9f00f13fd78c6cbcfabcbb47a6babeed6a4c087b2a6f4b8c`.
The new documentation hashes are reported out of band because an evidence file
cannot include its own complete hash without self-reference.

No RPC endpoint or signing-secret value was read; no signer, signature,
broadcast, deployment, registration, configuration, governance action,
production change, inventory edit, Stage B, Stage C, push, merge into `rh`, or
Base migration occurred. Row 2 remains pending and Stage B remains
unauthorized.

## 14. Row 2 packet-validation correction evidence — 25 July 2026

### 14.1 Exact defect and authorized scope

At clean documentation commit
`646c7a745fcdde8e5cf0ce859f990f1e541987b3`, local `rh`, cached
`origin/rh`, and the one explicitly requested live `origin/rh` check all
resolved to `cb3fe7392c44613aaeec49bd2486369fe0da3556`. The S5 branch was
12 ahead / 0 behind `rh`.

A local dummy-public-data diagnostic showed that the prior
`parse_approval()` accepted:

- owner, independent-security, and deployment provenance approvals all false;
  and
- corrupted packet source/ABI/compiler identities, ArbSys address/selectors,
  source offset, zero-value/no-token assertions, and bounded-stop assertion.

The diagnostic did not read an endpoint environment value or signing secret,
contact an RPC, derive a signer from a private key, run preflight, sign,
broadcast, deploy, or transact. The owner then authorized a correction limited
to:

- `scripts/probes/action_block_identity_probe.py`;
- `tests/probes/test_action_block_identity_probe.py`;
- `docs/chains/rh/ledger-guard-security-decision.md`; and
- this evidence record.

`contracts/testing/ActionBlockIdentityProbe.vy` was not modified.

### 14.2 Corrected fail-closed contract

The one parser shared by the preflight and execution CLI paths now rejects
unless all eight Booleans are exactly true:

```text
live_testnet_approved
approval_provenance.owner.approved
approval_provenance.independent_security.approved
approval_provenance.deployment.approved
rpc.approved
signer.approved
signer.funding_approved
fees.owner_approved
```

Each provenance block requires a strict `YYYY-MM-DD` decision date and nonempty
reference, and the top-level owner reference must match the owner provenance
reference. No reviewer-name field is required.

The parser accepts an approval-packet hash only as lowercase `0x` followed by
exactly 64 lowercase hexadecimal digits. Before any environment, RPC, nonce,
signer, or secret access, it compares the packet's exact values with reviewed
runner constants:

| Packet fact | Required value |
| --- | --- |
| source SHA-256 | `0x95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` |
| ABI SHA-256 | `0x2c237ba7e43aa009c69eabe950c733c79415b7eab37e874e065494273a45b359` |
| compiler-input SHA-256 | `0xf251237b97029e29122f5578c38817e518abcc3062c6d32019de028bdef79a65` |
| creation-bytecode Keccak-256 | `0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333` |
| runtime-bytecode Keccak-256 | `0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56` |
| ArbSys address | `0x0000000000000000000000000000000000000064` |
| `arbBlockNumber()` selector | `0xa3b1b31d` |
| `arbOSVersion()` selector | `0x051038f2` |
| source-pin date | `2026-07-24` |
| Robinhood node image | `offchainlabs/nitro-node:v3.11.2-3599aca` |
| Nitro commit | `3599acae1ad2fab4059fc46453c9cd3294126641` |
| ArbSys interface commit | `7e88c8cc53c2e96201a23c638f1536557b9cb68b` |
| published profile / offset / raw return | `61 / 55 / 116`, exact derivation `61 + 55 = 116` |
| topology | exact ordered five cases from section 12 |
| execution assertions | `native_value_wei=0`, `token_transfer=false`, `stop_on_inconclusive_bound=true` |

After parsing and before reading the endpoint environment variable, both
live-capable CLI paths compile the probe and compare all five artifact
identities with the hardcoded reviewed constants. Preflight repeats the
compiled-versus-packet comparison before its first RPC call. The endpoint
fingerprint uses the same strict lowercase `0x` plus 64-hex format.

Runtime/RPC block, receipt, and transaction hashes use a separate helper. It
accepts valid mixed-case hexadecimal, normalizes to lowercase before evidence
storage or equality comparison, and rejects malformed values. Deterministic
local-versus-RPC transaction-hash equality remains exact after normalization;
this compatibility behavior does not relax any approval-packet hash rule.

### 14.3 Tests and local-only results

The 52 added focused cases cover:

- every one of the eight approval Booleans;
- each provenance date/reference and the owner-reference equality;
- malformed and uppercase values for every one of the five artifact hashes;
- valid-format but wrong values for every artifact hash;
- wrong ArbSys address and both selectors;
- every dated Nitro/source pin;
- topology list, zero native value, no-token rule, and inconclusive-bound stop;
- preflight and execution CLI rejection before artifact compilation,
  environment, RPC, or secret access; and
- local compiled drift in each of the five identities before RPC;
- uppercase endpoint/artifact approval hashes failing before access;
- valid mixed-case RPC transaction hashes normalizing before exact local-hash
  comparison and sanitized storage; and
- malformed RPC/runtime hashes remaining rejected.

All local commands explicitly removed the Robinhood endpoint and signing-key
variables from their child environments. The locked H-01 Candidate A
interpreter remained:

```text
/private/tmp/h01-final-review.dL2pqo/candidate/bin/python
Python 3.12.0
Vyper 0.4.3 / compiler 0.4.3+commit.bff19ea2
Titanoboa 0.2.7
pytest 8.4.2
cbor2 5.9.0
```

Exact results:

| Command/scope | Result |
| --- | --- |
| `python -m py_compile` for runner and focused tests | exit `0` |
| focused `tests/probes/test_action_block_identity_probe.py` | 87 tests; 0 failures, 0 errors, 0 skips; JUnit time `27.157s` |
| complete `tests/probes` | 127 tests; 0 failures, 0 errors, 0 skips; JUnit time `32.237s` |
| runner `--dry-run` | exit `0`; exact five artifact identities reproduced; no endpoint/RPC/secret/broadcast access |
| `git diff --check` | clean |

The dry-run again reported:

```text
rpc_contacted=false
rpc_endpoint_read=false
signing_secret_read=false
broadcast_enabled=false
maximum_supported_observation_transactions=16
deployment_transactions=1
native_value_wei=0
token_transfer=false
```

Post-correction identities:

| File/artifact | Identity |
| --- | --- |
| unchanged Vyper probe SHA-256 | `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` |
| corrected runner SHA-256 | `c43bb256110416001a55ad3a23a9e295921329b2ee82779def9f199bd1e22f98` |
| corrected focused tests SHA-256 | `7d06040b9b01613fcb37b6cd86e078299cf45526be39acbcbf10ebac9ddef628` |
| unchanged creation-bytecode Keccak-256 | `0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333` |
| unchanged runtime-bytecode Keccak-256 | `0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56` |
| unchanged section 12 JSON-body SHA-256 | `277f3628853b5ff06d65f22611358e08e521fe05afc0dd91b58692dd91026534` |

The current section 12 packet still contains false/null live fields and is
non-executable. No operator value was requested, supplied, inferred, or read.
The next permissible step is independent exact-hash review of these four
unstaged files. Only after an exact-byte commit is separately authorized may
the owner complete the secret-free packet for a new hash review. Preflight,
execution, row 2 closure, Stage B/C, inventory work, push, merge, production,
deployment, configuration, governance, signing, and broadcast remain
prohibited.
