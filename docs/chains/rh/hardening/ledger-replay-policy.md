# Ledger historical and native replay policy

> **DRAFT — policy artifact only.** This file does not edit a historical
> migration, create a new migration, deploy Ledger, or authorize a replay. The
> current Ledger record identifies those actions as separate release controls
> ([ledger.md, shared source and migration compatibility](../smart-contract-changes/ledger.md#shared-source-base-divergence-and-migration-compatibility)).

## Binding rules

1. The historical Base migration
   [`migrations/base-mainnet/1004_Ledger.py`](../../../../migrations/base-mainnet/1004_Ledger.py)
   remains byte-for-byte unchanged and bound to the original two-argument
   Ledger source or compiled artifact. The migration passes only RipeHq and
   Defaults, while current source requires a third action-block-source argument
   ([ledger.md, Base divergence and migration compatibility](../smart-contract-changes/ledger.md#shared-source-base-divergence-and-migration-compatibility)).

2. Historical replay must never resolve the old contract name to current
   three-argument source. Adding zero to the old migration would deploy new
   creation/runtime code under an old migration identity rather than reproduce
   the historical artifact
   ([ledger.md, Base divergence and migration compatibility](../smart-contract-changes/ledger.md#shared-source-base-divergence-and-migration-compatibility)).

3. Every future native deployment of current Ledger requires a **new
   migration** that passes
   `0x0000000000000000000000000000000000000000` explicitly as
   `_actionBlockSource`. In zero mode, current Ledger uses native
   `block.number`
   ([Ledger.vy:189-230](../../../../contracts/data/Ledger.vy#L189),
   [test_ledger_action_block.py:79-99](../../../../tests/data/test_ledger_action_block.py#L79)).

4. The RH deployment path is separately controlled and passes exact
   `0x0000000000000000000000000000000000000064`; the draft profile rejects zero
   and sampled unsupported values and requires the immutable readback
   ([ledger-robinhood-profile.json](../../../../scripts/proposals/ledger-robinhood-profile.json),
   [test_ledger_robinhood_profile.py:76-96](../../../../tests/deployment_profiles/test_ledger_robinhood_profile.py#L76)).

5. `ACTION_BLOCK_SOURCE` is a two-mode discriminator, not an arbitrary provider:
   constructor values are limited to zero or exact `0x64`, and `0x64` mode
   probes the exact ArbSys ABI during construction
   ([Ledger.vy:130-132](../../../../contracts/data/Ledger.vy#L130),
   [Ledger.vy:189-222](../../../../contracts/data/Ledger.vy#L189)).

## Required replay evidence

| Replay class | Mandatory evidence | Fail-closed condition |
| --- | --- | --- |
| Historical Base | Historical migration bytes/hash, original Ledger source/artifact identity, original two encoded arguments, compiler/version/settings, reproduced creation/runtime identity, and explicit proof current source was not substituted; the divergence is documented in the Ledger record ([ledger.md, Base divergence and migration compatibility](../smart-contract-changes/ledger.md#shared-source-base-divergence-and-migration-compatibility)) | Any current-source resolution, added third word, missing original artifact, or identity mismatch |
| Future native | New migration identity/path, current Ledger source/artifact hashes, three-word constructor encoding with final word zero, immutable readback zero, native action-block tests, and owner approval ([Ledger.vy:189-230](../../../../contracts/data/Ledger.vy#L189), [test_ledger_action_block.py:79-99](../../../../tests/data/test_ledger_action_block.py#L79)) | Reuse of historical migration identity, implicit/missing third argument, or nonzero source |
| RH | Separately controlled RH plan/profile, exact three-word constructor encoding ending in `0x64`, constructor probe, immutable readback, local artifact bundle, live qualification when authorized, and owner approval ([ledger-local-artifact-bundle.json](ledger-local-artifact-bundle.json), [test_ledger_artifact_bundle.py](../../../../tests/deployment_profiles/test_ledger_artifact_bundle.py)) | Zero/wrong source, missing readback/probe, or treating local reproduction as deployment evidence |

The local RH artifact bundle is labeled local reproduction evidence, not
deployment evidence
([build_ledger_artifact_bundle.py:1-7](../../../../scripts/proposals/build_ledger_artifact_bundle.py#L1),
[ledger-local-artifact-bundle.json](ledger-local-artifact-bundle.json)).
No rule here authorizes a native or RH migration; exact migration IDs,
networks, signers, and approval records remain owner-controlled inputs.
