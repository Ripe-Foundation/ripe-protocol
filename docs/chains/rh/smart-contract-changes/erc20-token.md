# Erc20Token: CCIP admin-discovery hook

> [!IMPORTANT]
> This page records the source and compiler effects present in current `rh`.
> It does not establish Chainlink acceptance, token-admin registration, a CCIP
> pool, mint/burn capability, remote-chain configuration, deployment,
> activation, or release.

## Current identity and exact delta

This rationale is bound to current local, cached, and live `rh` commit
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`, verified on 3 August 2026.
The one-path commit has parent
`27f21ccc782e45fe65634cfec3f3fb4eb9f083a0`, tree
`1600413e0ee015aa4e68a5e4515523433a8f8a3f`.

| Identity | Current value |
| --- | --- |
| Production source | [`contracts/tokens/modules/Erc20Token.vy`](../../../../contracts/tokens/modules/Erc20Token.vy) |
| Git blob | `f00e5655567612e3f8c95182de75701424eeea2b` |
| Source SHA-256 | `54ffb5d2dcdf5dd2c5990e0bcd3a67b0ebcbae32b8dc3ef6c00d2e84ea447af7` |
| Source size | 17,435 bytes |
| Parent Git blob / SHA-256 | `0758a13ad2537cc3d7679b80aabe27f298371664` / `dc32f4ea2a0b8128a82e206cee0c699ddf9b756d7ac51a1bace665e4192e85b1` |
| Commit scope | 11 inserted lines in this source only; no committed ABI or test update; final line terminator removed |
| Added selector | `getCCIPAdmin()` = `0x8fd6a6ac` |
| EOF identity | Parent ends with LF (`0x0a`); current source ends with `)` (`0x29`) and has no final LF |

The only functional addition is an external view:

```vyper
@view
@external
def getCCIPAdmin() -> address:
    return staticcall RipeHq(self.ripeHq).governance()
```

It stores no new admin and adds no setter. For a token whose `ripeHq` is
correctly initialized, the returned address follows the current RipeHq
governance getter. The source change does not grant mint, burn, blacklist,
pause, pool, registry, or remote-chain permissions.

The Git numstat is `11` insertions / `0` deletions. That count does not expose
the accompanying loss of the final newline. The missing LF does not alter the
Vyper behavior described here, but it is a real source-byte and formatting
change. Restoring it would create another production-source identity and is
therefore not folded into this documentation-only refresh.

## Authorization and decision status

> [!WARNING]
> The integrated hook is ahead of the repository's recorded precondition and
> owner decision. Its presence in `rh` must not be read as approval.

The governing Track-1 document remains **Draft for owner review** and says to
add `getCCIPAdmin()` only if Chainlink confirms it is required and assisted
registration is unavailable or inappropriate. The named
`ccip-chainlink-response-record.md` does not exist, the prepared question
packet remains unsent, and no repository decision record establishes either
precondition. [`RH-D008`](../decision-register.md#L129-L139)
approves only a complete-or-disabled launch posture; it does not select this
hook or a Token Admin Registry path.

The implementation is shared rather than Robinhood-only, so it complies with
the repository's source-shape rule. It does not yet satisfy the standing
default in [`rh-summary.md`](../../rh-summary.md), which requires an explicit
owner decision and a **tested** shared token revision with the resulting Base
live-version policy resolved. At this baseline there is no direct behavior
test, four committed ABIs are stale, and the Base policy remains open.

Consequently, an owner must choose one of two separately controlled source
dispositions: ratify the shared hook and close its evidence/ABI/Base-policy
gaps, or authorize a source reversion and rebind the documentation and
artifacts to the resulting commit. This audit makes neither choice and does not
alter the production source.

## Why the interface matters

`getCCIPAdmin()` is a Chainlink Token Admin Registry discovery surface.
[Chainlink's current registration documentation](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/registration-administration)
uses it for the self-service administrator proposal flow. Source presence is
not proof that Chainlink accepts the exact token, registry, admin, network, or
registration sequence. Assisted registration, self-service registration, and
the exact production process remain external and separately controlled facts.

The change is made in the shared token module rather than in a
Robinhood-specific GREEN or RIPE wrapper. Current `master` retains the parent
module blob, so `master..rh` contains a real shared-source divergence. Existing
immutable Base deployments are unaffected by repository source changes and do
not acquire this selector.

## Complete related-document drift map

Nine planning documents outside this directory mention the hook or its token-
source premise. This table distinguishes controlling conditions, current Base
facts, neutral inventory, and statements stale for current `rh`; it avoids
treating every mention as the same kind of drift.

| Document | Current disposition after `0642f086…` |
| --- | --- |
| [`track-1-chainlink-ccip-confirmation.md`](../track-1-chainlink-ccip-confirmation.md) | Controlling draft condition remains unresolved: add the hook only after the stated Chainlink finding, and stop for an owner decision. The current source moved ahead of that condition. |
| [`rh-summary.md`](../../rh-summary.md) | Controlling checklist remains open and requires a tested shared revision plus explicit Base live-version policy if the hook is unavoidable. The source has the required shared form, but the owner decision, tests, current ABIs, and Base policy are missing. |
| [`minimal-contract-change-reassessment.md`](../minimal-contract-change-reassessment.md) | Its recommendation to keep GREEN/RIPE unchanged absent a Chainlink finding and owner decision remains the recorded policy; its unchanged-source description is stale for current `rh`. |
| [`component-matrix.md`](../component-matrix.md) | CM-001/002's `reused unchanged` classification and the CCIP decision row's unchanged-source premise are stale for the effective compiler graph: the direct token blobs are unchanged, but their imported shared module changed. Its shared-revision requirement and rejection of a Robinhood-only hook remain current and are satisfied in form. |
| [`block-number-inventory.md`](../block-number-inventory.md) | The CCIP row's statement that token source can remain unchanged is stale for current `rh`; the shared-source/Base-policy boundary remains applicable. |
| [`ccip-integration-decision.md`](../ccip-integration-decision.md) | The preference for no token change and the same existing Robinhood implementation is stale as a current forward-source claim. Its facts about immutable Base deployments and its rejection of a Robinhood-only hook remain current; the integrated change is shared. |
| [`ccip-public-evidence.md`](../ccip-public-evidence.md) | The observed Base deployments' lack of `owner()`/`getCCIPAdmin()` remains true. The document's hypothetical modified-Robinhood-token case is now an integrated repository-source fact and needs decision reconciliation. |
| [`ccip-chainlink-question-packet.md`](../ccip-chainlink-question-packet.md) | Claims about the immutable Base tokens remain accurate. The question about using assisted registration for unchanged Robinhood deployments reflects the pre-change plan, not current `rh` source identity; the packet remains unsent. |
| [`track-3-phase-0-inventory.md`](../track-3-phase-0-inventory.md) | This is neutral inventory/question framing, not a false unchanged-source claim. Its instruction to leave the admin path pending Track 1 remains unresolved. |

This documentation-only refresh does not silently rewrite those broader
planning and decision authorities. They require a separately scoped
reconciliation once the owner selects ratification or reversion; until then,
this page is the current source-identity and drift record, not authorization.

## Complete transitive compiler impact

Three production token sources export and initialize `Erc20Token`: GREEN,
RIPE, and sGREEN. The sGREEN artifact therefore also exposes the selector even
though current repository policy permanently omits sGREEN from CCIP. Fresh
Vyper `0.4.3+commit.bff19ea2` compilation produced:

| Compiled source | Runtime bytes | EIP-170 headroom | Runtime SHA-256 | Canonical ABI SHA-256 |
| --- | ---: | ---: | --- | --- |
| `Erc20Token.vy` | 6,767 | 17,809 | `d13a59c2961a981a444ce6defd59a2d4c4d0a0b079f5cb322dc2c4fc2715c7fb` | `49c87121ab8eec9d6472e7e7401e54d78bf47022d54346ae1020dce01f546f39` |
| `GreenToken.vy` | 7,085 | 17,491 | `74f3f1c818d951f6c5c2e755e0b1667f3f1b13f91cc483da7923809bb7038f16` | `5b399bea8005b337b822e7d7b00b165650d6b4e9af1d170b29878870d0a152e2` |
| `RipeToken.vy` | 7,085 | 17,491 | `0338e28a3787286430139234127c9953945bca3fd7d4084cbd19fdfc62943962` | `5b399bea8005b337b822e7d7b00b165650d6b4e9af1d170b29878870d0a152e2` |
| `SavingsGreen.vy` | 10,602 | 13,974 | `214218d00cc1cce8fa32160769e73c686c532bc13790f42ad4a4f83c14e6fc92` | `9234529ab0fc8a20a1b78ff1c1609a43629f5f6fd756debbe89b6606031f19cd` |

The direct `GreenToken.vy`, `RipeToken.vy`, and `SavingsGreen.vy` Git blobs do
not differ from `master`; their compiled outputs differ because the imported
module changed. The new function adds one ABI entry and one selector to each
compiled artifact without changing the module's persistent storage,
constructor, events, or existing function signatures.

## Current artifact and test discrepancy

The repository-wide deterministic ABI check is currently red. The committed
files do not contain `getCCIPAdmin`, while fresh compiler output does:

| ABI file | Committed SHA-256 | Fresh expected SHA-256 | Function count |
| --- | --- | --- | ---: |
| `scripts/abis/Erc20Token.json` | `96670320212e8a8867a93cc3cb5aa4ca01e683ee7fdc5d1d03618145f25a189e` | `ecc2a6e8232f98557b6f980b8cd8dd952af062992df4411d30faa9c058fc6a3d` | 39 committed / 40 compiled |
| `scripts/abis/GreenToken.json` | `0dc0574262c08b83e5faa6dd82b071d9c0fa7362a692fbd63fa042af80b392d7` | `4e7f92104baa377132c09ec5596a9afaeae8b726f58fd9a7d9b000c9fc20114b` | 40 committed / 41 compiled |
| `scripts/abis/RipeToken.json` | `0dc0574262c08b83e5faa6dd82b071d9c0fa7362a692fbd63fa042af80b392d7` | `4e7f92104baa377132c09ec5596a9afaeae8b726f58fd9a7d9b000c9fc20114b` | 40 committed / 41 compiled |
| `scripts/abis/SavingsGreen.json` | `fe6a276feacb7fa256e7add75495424689a72b0405bf583984463127aaf5704b` | `9593466f4a1d5d07038dddecdb201a2b651447e45518802aee6a29cb725a6d15` | 64 committed / 65 compiled |

The focused repository test fails with four exact diagnostics:

```text
changed ABI output: Erc20Token.json
changed ABI output: GreenToken.json
changed ABI output: RipeToken.json
changed ABI output: SavingsGreen.json
```

No checked-in test invokes `getCCIPAdmin`, and the source commit changed no
test. The current nine-contract frozen artifact gate does not cover these token
artifacts, so its green result does not close the ABI or behavior gap.

The repository's only GitHub Actions workflow builds, tests, and lints the
Robinhood handoff dashboard. It does not run the protocol ABI export test,
contract artifact checker, or direct token tests. No current CI gate therefore
detects this four-file discrepancy or the missing hook behavior coverage.

## Current disposition and required follow-up

The hook is an integrated production-source fact, but it is neither owner-
ratified nor release-ready evidence. Before any deployment or CCIP registration
claim:

1. the owner must ratify this shared revision or separately authorize its
   reversion;
2. if ratified, record why the Track-1 precondition is satisfied or explicitly
   superseded, and resolve the immutable Base live-version policy;
3. regenerate and review the four deterministic ABI outputs;
4. add direct tests for initialized admin discovery, governance changes,
   uninitialized/invalid HQ behavior, and all three transitive token exports;
5. bind creation/runtime, ABI, selector, layout, and compiler-input identities
   for the exact GREEN, RIPE, and sGREEN artifacts;
6. explicitly preserve sGREEN's CCIP exclusion despite its inherited selector;
7. decide whether to restore the conventional final LF in the separately
   reviewed source revision; and
8. keep CCIP pools, remotes, rate limits, mint/burn capabilities, registration,
   deployment, activation, and release separately gated.

This audit does not implement those non-documentation corrections and does not
authorize any onchain or external Chainlink action.

## Reproducible checks

```sh
git diff --stat 27f21ccc782e45fe65634cfec3f3fb4eb9f083a0..0642f086d19e3cc62faaf67da096b6511e405320
git diff 27f21ccc782e45fe65634cfec3f3fb4eb9f083a0..0642f086d19e3cc62faaf67da096b6511e405320 -- contracts/tokens/modules/Erc20Token.vy
git diff --check 27f21ccc782e45fe65634cfec3f3fb4eb9f083a0..0642f086d19e3cc62faaf67da096b6511e405320 -- contracts/tokens/modules/Erc20Token.vy
python scripts/check_contract_artifacts.py
pytest -q -p no:cacheprovider tests/deployment/test_abi_export.py::test_repository_default_abi_directory_is_byte_current
```

The ABI test requires the repository's ordinary local test-harness setup. It
was rerun for this audit with private temporary caches and localhost-bind
permission; no public RPC, signer, account, or protocol state was used.
