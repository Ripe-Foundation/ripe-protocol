# Track 7 H-03 Robinhood blueprint — Phase A checkpoint

**Status:** The complete R6 Phase A package and `D-H03-004-R6` were approved
at exact brief SHA-256
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`
and pre-provenance evidence SHA-256
`9b8bc27522c24ed40cfadb2e594e450ffab2e4f947c036affac7cf9bdacd46ad`.
The authorized provenance-only amendment produced evidence SHA-256
`c9724a4b85ff0d8e26505133f845a78cf573910a991a2548e1d8e96afeaa592c`;
independent exact-diff/hash review approved it, and the two documents were
published on the R6 feature branch in commit
`2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`.

Post-publication review found stale pre-approval status language in this
evidence record. The evidence-only chronology correction received complete-file
independent exact-hash review and fresh owner approval, was published in commit
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4`, and was integrated into `rh`
through merge `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. Its integrated SHA-256 is
`ed81dad7aaad41150ee49d20134916c9660e283ac77f85a2b0e5fe757ab2036c`.

H-03 Phase A is therefore approved and integrated. This lifecycle/provenance
correction records that completed chronology and the final H-01 authority
without changing the approved H-03 model. It is a new unstaged and uncommitted
one-file candidate requiring complete-file independent exact-hash review,
owner approval, commit, reconciliation, and integration before Phase B. The
approved brief remains byte-identical; all 18 downstream blockers remain
open, H-03 Phase B exact-lock validation remains pending, and Phase B remains
unauthorized and unstarted.

**Prepared:** 25 July 2026; R6 corrected 26 July 2026; lifecycle reconciled
27 July 2026

**Controlling baseline:** `7098211db5693f986b65ec7a9e897f3518e9538c`,
tree `c07329ed9fcc2dc99afbef3f7888f478024d1ede` (final integrated H-01
retirement-transition baseline; historical R6 planning/reconciliation
baseline `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` and rejected R5 baseline
`332ae2bc8e0ce4b694766d6d20759295d9267ec3` remain ancestors)

**Branch:** `rh-track-7-h3-r6-lifecycle-correction`

**Worktree:**
`/Users/wigglez/dev/ripe-protocol-track-7-h3-r6-lifecycle-correction`

**Historical approval provenance:** The owner approved `D-H03-001` through `D-H03-004`
on 25 July 2026 exactly as presented in the independently reviewed Phase A
evidence at SHA-256
`29061e3e0142251388ed2d2ffc17fabfad5f118a5d9e3f07752bc6581a1f534a`.

The approval is limited to the symbolic H-03 blueprint, its immutable Python
schema, and its tests. It does not approve any concrete address, contract
artifact, new component or VaultBook ID, parameter, role, signer, migration,
registry transaction, deployment, configuration, or activation.

Under that approval this record was then revised once for two non-blocking
editorial findings raised in the same review. Historically, Section 14 then
directed Phase B to append the Section 5.2.1 source crosswalk, and Section 11
received the approved `D-H03-001` artifact/slot split. The former
Phase-B-deferred crosswalk procedure was later rejected and is fully
superseded by R4's complete Phase A per-path authority; the artifact/slot split
remains controlling. No disposition, identifier, count, blocker, owner,
topology cell, diagnostic, decision, or validation figure changed in that
historical editorial pass.

**Correction pass — 25 July 2026 (second).** Under a documentation/evidence-only
owner authorization of 25 July 2026, this record was reconciled to exact `rh`
`332ae2bc8e0ce4b694766d6d20759295d9267ec3` by fast-forward without rebase or
history rewriting, and corrected for five independent cross-track/adversarial
review findings: canonical surface records, typed component relations,
deterministic blockers/owners/statuses, the complete Phase A source-class/path
authority, and the restored seven-day fast-follow phase. That authorization
approved the corrective direction only. It did not approve the final schema,
the new canonical inventories, Phase B, implementation files, a commit, push,
deployment, configuration, or any live action.

`D-H03-001` through `D-H03-003` remained approved after that pass, while
`D-H03-004` was reopened and `D-H03-004-R1` remained pending.

**Correction pass — 25 July 2026 (R2).** A subsequent deep review rejected the
R1 schema and inventories at SHA-256
`569a00894b548b45e7639aaf3ad2c407e9112a5434aaaf4853b1f294f41bb100`.
The owner then authorized a direct H-03-only correction, including the exact
two-line controlling-brief amendment that replaces untyped dependency IDs
with phase-qualified component relations. This R2 pass:

- narrows canonical surfaces to launch- or security-relevant boundaries;
- adds semantic meaning and H-04's exact eight-phase lifecycle vocabulary;
- narrows runtime relations to `runtime_security` and requires source proof;
- makes symbolic-input and component ownership deterministic;
- replaces component-wide source state with per-path source records;
- restores omitted constructor/configuration input identities;
- corrects Stock reward, LP, USDG, PSM, CCIP, and provenance assertions; and
- removes every Phase-B-deferred source-crosswalk instruction.

That authorization approved the corrective work, not these final bytes,
`D-H03-004-R2`, Phase B, implementation, a commit, push, deployment,
configuration, or live action. The resulting R2 artifact and amended brief
were later rejected at the exact hashes recorded below.

**Correction pass — 25 July 2026 (R3).** Independent review rejected R2 at
exact evidence SHA-256
`269fc569c2cb0aa20d3b15f90e10005a8bd5a756ed5a02b8809ac227fe93a359`
and brief SHA-256
`9f441023032dab1d52848155186fe3a365a8b4f3e543934914732ee96cec8721`.
The reviewer found stale mutable M1 provenance, unauthorized nonblocking
PSM/LP semantics, a wrong PSM auto-deposit lifecycle, no dedicated Teller
exact-receipt assertion, seven missing trusted-producer edges, inexact
relation proofs, missing constructor inputs, an incomplete source crosswalk,
an internally contradictory evidence field, fail-open file/drift gates, and
stale controlling-brief status.

The initial R3 candidate attempted to correct those findings without selecting
a production value or widening H-03 into implementation. A later exact-hash
review rejected that candidate at evidence SHA-256
`dfc5a553d3543e18e994576ce330a326acc201e6a8745a7df69adb410cff3b81`
and brief SHA-256
`094978eb9aec26389494da671f5fb53aa60dfaf538f6a65a2aadef9dd727d82e`.
That review found three invalid or insufficiently proved relations; broad
non-mechanical source aliases; omitted RipeHq mint and per-contract capability
states; an omitted Teller initial-pause input; stale controlling-brief gates;
conflated zero-LTV and omitted-borrow LP states; the wrong CM-054 source
classification; and minor count, wording, and blast-radius defects. The
initial R3 candidate was never approved.

The final R3 candidate recorded those intended corrections, but independent
review rejected its canonical relation graph and six other findings at exact
evidence SHA-256
`a8e39f3ab4cb341923d16d289ece823638d4e981c837d1a26644dbbc455f531d`
and brief SHA-256
`746e262b410bcf3b0e73179cb6df905deaa679cc01acd50d0b2263bd23e56d5d`.
It was never approved.

**Correction pass — 26 July 2026 (R4a).** R4a modified only this evidence
record. It regenerated the canonical relation graph from source across all 60
components, producing 43 grouped proof rows and 267 expanded relations at
evidence SHA-256
`199a089ded8841822cfab822b74357db72c51d63471eaa93d725942f22e359ab`.
The brief remained byte-identical to rejected R3. The graph's proofs and
counts reproduce, but its invariant-enforcer-to-governed-counterpart
orientation is a schema-semantics choice. R4a is therefore not approved until
the owner ratifies or rejects `D-H03-005`.

**Correction pass — 26 July 2026 (R4b).** R4b preserves the R4a relation
candidate and corrects the remaining R3 findings without beginning Phase B:
CM-056 uses the three exact H-02 history roots and their
`config/network_profiles.py` authority; both approved LP assets receive an
ordinary-only Teller invariant and trusted-route mutation family; reward
launch state is separated from its possible seven-day promotion action; stale
M0/PSM language is removed; approval provenance uses an independent
post-amendment exact-diff/hash gate; and the global-mint terminal sequence is
an explicit unapproved owner proposal in `D-H03-006`. R4b is correction work
only. It does not approve `D-H03-004-R4`, either pending owner decision, Phase
B, a commit, push, deployment, configuration, or any live action.

Independent review rejected R4b at brief SHA-256
`6c52679aca8e05d806705bc962edd522c5d633c7b54a5e3a74940cd0fd2711af`
and evidence SHA-256
`c2d658943b7812651e5cbcbc8b000985666243d8b478672e22fe891c21fe50b5`.
R4b was never approved.

**Correction pass — 26 July 2026 (R5).** The owner approved the typed
caller-to-callee and authority-dependency semantics in `D-H03-005` and the
terminal global-mint order in `D-H03-006`, then authorized one complete
documentation-only correction. R5 regenerates the full relation graph as
explicit per-edge records, corrects every identified proof and orientation
defect, carries unresolved TrainingWheels and special-StabilityPool bindings
as `B-H04-PARAMS` blockers, and reconciles the schema, counts, status,
supersession, validation, and hash-continuity language. R5 does not approve
`D-H03-004-R5`, begin Phase B, modify implementation, stage, commit, push,
merge, deploy, configure, or perform a live action.

Independent review rejected R5 at brief SHA-256
`0fdc573ea4955bf78976f0bcff18accb6bf90857e160bedf3035e37327a7d4a0`
and evidence SHA-256
`ad31229f5fda9a262ba00e20482a99a6f486fbf92644b342cf132684f7f82cb5`.
R5 was never approved.

**Correction pass — 26 July 2026 (R6).** R6 was created in a fresh isolated
branch/worktree from exact integrated `rh`
`c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`. The rejected R5 brief and
evidence were copied byte-for-byte as inputs, then corrected only for:

- unsupported `R-282`, replacing the false Switchboard dependency with the
  exact Endaoment admitted-authority dependency while preserving the separate
  Endaoment-to-EndaomentFunds direct call;
- the truncated Section 7A.3 generic-target exclusion/blocker rule;
- the exact integrated H-04 lifecycle vocabulary and distinct CCIP and reward
  promotion actions; and
- all mechanically dependent counts, assertions, provenance, and handoffs.

Independent re-review then reproduced every state, hash, inventory, proof,
path, citation, and scope claim against the first complete R6 candidate at
brief SHA-256
`43f29ba8b7cc7a7cc4497a2dc4d1ff3c7086bbae20505d16ae16e161919d51b6`
and evidence SHA-256
`a9c2b2d7628b5a00594b25604f31d8ca34c9ffd1cf3ec3976df9f23498684418`.
It found one semantic convention implicit: the two CCIP capabilities on
launch-deployed GREEN and RIPE tokens use the controlling CCIP-promotion
lifecycle while their disabled disposition must already hold at launch.
Because integrated H-04 authority assigns the CCIP-promotion lifecycle to all
six exact CCIP surfaces, this clarification preserves that assignment and
adds the explicit continuous launch-disabled rule, assertion, mutation
coverage, zero reward-surface cardinality explanation, and
owner-attestation provenance note. It changes no canonical record, ID,
disposition, lifecycle assignment, count, blocker, owner, evidence authority,
or proof tuple. The pre-clarification R6 hashes were never approved and are
superseded by the clarified R6 candidate.

The owner then approved `D-H03-004-R6` and the complete clarified R6 package
at exact brief SHA-256
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`
and evidence SHA-256
`9b8bc27522c24ed40cfadb2e594e450ffab2e4f947c036affac7cf9bdacd46ad`.
The authorized provenance-only amendment inserted the decision ID, owner
role, date, and reviewed hashes; independent review confirmed that reversing
only that amendment reproduced the approved evidence candidate exactly. The
post-amendment evidence SHA-256
`c9724a4b85ff0d8e26505133f845a78cf573910a991a2548e1d8e96afeaa592c`
and byte-identical brief were committed and pushed only to the R6 feature
branch in commit `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`, tree
`59210354b205f17c996fcdfe6e8af6a7cb756532`, with parent
`c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`. `rh` was not changed.

**Post-publication status correction — 26 July 2026.** Review of the published
commit found that several pre-approval status statements were not reconciled
with the inserted approval provenance. This correction changes only this
evidence file but necessarily changes bytes outside the former
provenance-only block. The published commit remains immutable historical
provenance. The corrected complete file received independent exact-hash review
and fresh owner approval, was committed and pushed in
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4`, and was integrated into `rh`
through merge `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. The correction did not reopen
the substantive owner decision, change any model record, close any downstream
blocker, satisfy H-03 Phase B exact-lock validation, or authorize Phase B.

**Integrated lifecycle reconciliation — 27 July 2026.** Final controlling
`rh` is `7098211db5693f986b65ec7a9e897f3518e9538c`, tree
`c07329ed9fcc2dc99afbef3f7888f478024d1ede`. This one-file correction records
the completed R6 review, approval, publication, chronology correction, and
integration plus the final H-01 exception authority. It changes no substantive
H-03 decision or inventory. These revised bytes remain unstaged, uncommitted,
and unapproved pending complete-file independent exact-hash review.

## 1. Scope and checkpoint result

This record is Phase A evidence only. Its integrated R6 content specifies the approved
smallest immutable public API, complete CM-001–060 graph, topology
constraints, blocker ownership, and Phase B test ceiling. The current
lifecycle/provenance correction does not change that substantive content.
This record is not an executable blueprint, address file, defaults or
parameter manifest, migration plan, manifest, production-value freeze,
deployment approval, or activation approval.

Phase A found no need to change a production contract, H-02 file,
`config/BluePrint.py`, migration, manifest, history, default, ABI, generated
artifact, Track 8 record, or `docs/chains/rh-summary.md`. The only Phase A
paths published in commit `2c8468a…` were this evidence record and the
corrected controlling brief. Commit `d65e4db…` changed only this evidence
record, and merge `8e4a965…` integrated the resulting two-document authority.
The current lifecycle/provenance correction again changes only this evidence
record; the brief remains byte-identical to the approved and integrated blob.

The proposed component primary-disposition counts are:

| Primary deployment disposition | Count | Meaning here |
| --- | ---: | --- |
| `required` | 38 | Selected graph artifact or non-onchain support surface; concrete values remain separately owned |
| `omitted` | 16 | No Robinhood artifact, registry row, route, approval, capability, or manifest contract record |
| `deferred` | 5 | Outside initial launch and requires a separately reviewed later release or promotion |
| `blocked` | 1 | CM-008 cannot select a deployable source until S5 implementation and proof close |
| `disabled` as a primary deployment disposition | 0 | Zero components carry `disabled` as their primary deployment disposition. This is not a claim that nothing is disabled: `required` components may still contain disabled sub-surfaces, which Section 7 enumerates per row and models as `SurfaceDisposition` records rather than as a component-level state |

`required` is the executable-schema spelling of “selected.” Required
topology-preserving artifacts with inactive product surfaces are not flattened
to `disabled`: their deployment is required and their named sub-surfaces are
separately disabled or blocked.

## 2. Authority order and current reconciliation

The source-backed reconciliation uses this order:

1. the 25 July 2026 Phase A authorization and current owner-approved launch
   graph;
2. the integrated Track 8 M0 owner-decision packet, with reviewed decisions at
   `c5c8b699b229792dc61e66af35502684ea3c8155`, final closure at
   `11824aa672809ad49ad7b2f823b9fb02c6e4608b`, and integration merge
   `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369`;
3. the current integrated Track 8 specification, validation plan, M0 evidence,
   and sanitized raw evidence;
4. the integrated Track 8 M1 brief plus the dated owner approval of
   `M1-D01`–`M1-D07` as provenance only; implementation remains open;
5. integrated Track 1 Chainlink/CCIP decision and evidence authorities;
6. integrated H-02, H-01, S1, S2, S3, S4, and current pre-implementation S5
   authority;
7. the integrated H-04/S6 brief for exact lifecycle vocabulary and parameter
   ownership;
8. the H-03 brief and Track 7 support specification/validation plan; and
9. the older component-matrix recommendations where not superseded.

Consequences:

- H-02's original implementation is integrated at merge
  `6c3052668555a7104ea12a7fb1a7c641c7e6b304`. Its focused second audit is
  closed by reviewed feature commit
  `5c1ba54c5d34670ddba13ce84e46f490f8a8aaa4` and integration merge
  `cb3fe7392c44613aaeec49bd2486369fe0da3556`.
- The final H-02 correction removes Base Sepolia's Base-mainnet blueprint
  alias, requires any nonempty `blueprint_id` to have an existing migration
  namespace, and hardens sanitized teardown diagnostics. It does not change
  either Robinhood profile ID, either Robinhood repository policy, the
  Robinhood `blueprint_id=None` state, or the H-02 functions/types consumed by
  H-03. The former `B-H02-AUDIT` blocker is therefore closed, and the proposed
  H-03 API and component/topology conclusions are unchanged.
- Track 8 M0 is closed, not open. The proposed containment artifact is
  unimplemented, and M1–M5 deployment/activation proof remains open.
- **Track 8 M1 — integrated brief only is stable authority.** The owner
  approved `M1-D01` through `M1-D07` and authorized M1 Phase A, but the M1
  Phase A evidence remains mutable and untracked in its separate worktree.
  It changed during R2 review and is therefore neither frozen evidence nor an
  H-03 authority. H-03 records M1 implementation, Gate 1, integration,
  deployment, and activation as unknown/incomplete behind `B-T8-M1` and uses
  only the integrated M1 brief plus dated owner provenance. Any mutable M1
  hash observed during review is informational only and must not enter the
  executable graph.
- The historical `332ae2bc… → c0d0e708…` advance added exactly two H-01 evidence
  artifacts and reconciles one S6/H-04 brief. Across the range,
  `docs/chains/rh/evidence/h01-exception-retirement-feasibility.md` and
  `docs/chains/rh/evidence/dependency-exception-exit-preflight.md` are the two
  H-01 evidence additions, while
  `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md` is the sole
  lifecycle/parameter authority reconciliation. No contract, H-02, H-03, S5,
  Teller, Ledger, or Track 8 implementation byte changes.
- The owner-authorized, independently reviewed H-01 dependency implementation
  is integrated at `d62777646cba1ae448fb9e26519c6fa295f437df`, tree
  `01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61`. The final exception-retirement
  transition is integrated at `7098211db5693f986b65ec7a9e897f3518e9538c`,
  tree `c07329ed9fcc2dc99afbef3f7888f478024d1ede`; it changes no dependency
  package byte.
- Under that effective transition, the Click, Pygments, and Pymdown Snippets
  exceptions are retired and non-operative. The pytest and Pymdown b64
  exceptions remain retained and operative. Package remediation and repository
  exception retirement do not establish GitHub/Dependabot alert closure, and
  no alert is claimed closed, dismissed, resolved, or otherwise changed.
- The integrated S6/H-04 reconciliation supplies the exact eight lifecycle
  phases and identifies two distinct nonautomatic actions: GREEN/RIPE CCIP
  promotion and reward activation. This changes the R5 lifecycle spellings
  and adds the missing CCIP `PromotionRecord`; it changes no launch-state
  disposition.
- AAPL is the only initial Stock Token. Later Stock Tokens are omitted pending
  token-specific review.
- Chain-native sGREEN deposit and withdrawal, GREEN Stability Pool, RIPE
  governance vault, USDG PSM mint/redeem, and the two named LP deposit-only
  routes are launch requirements. This supersedes older “decision open” or
  inert-scaffold language.
- USDG is PSM/LP-only and is not ordinary Teller collateral.
- Stock remains excluded from CreditRedeem, Stability Pool custody/swaps,
  trusted or Department deposit routes, Underscore, and every unapproved route.
- GREEN/RIPE CCIP is a nonblocking, separately promoted post-launch target.
  It remains disabled if incomplete. sGREEN is never CCIP-enabled.
- Rewards are globally disabled at launch. Later activation is a separately
  reviewed target, not an H-03 permission.
- S4 remains no-code with a named zero-cooldown assertion. S5 remains
  pre-implementation and blocks a fresh Robinhood Ledger artifact.
- Base deployments and Base blueprint values remain unchanged.

## 3. Bootstrap identities, hashes, and environment

### 3.1 Git and prerequisite identities

At the original bootstrap, before worktree creation:

| Check | Result |
| --- | --- |
| Integration worktree | Clean |
| Local `rh` | `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` |
| Tracking `origin/rh` | `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` |
| Live remote `refs/heads/rh` | `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` |
| Expected baseline | Exact match |
| Requested branch before creation | Absent |
| Requested worktree path before creation | Absent |
| H-03 file owner overlap | None found |

The isolated worktree was created from local `rh` at
`e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369`.

On 25 July 2026, after the H-02 focused audit closed, the owner authorized
reconciliation to exact current `rh`
`cb3fe7392c44613aaeec49bd2486369fe0da3556`. The untracked Phase A evidence
was preserved, the H-03 branch was fast-forwarded without rebase or history
rewrite, and the evidence was restored byte-identically before this
reconciliation update.

The branch was later fast-forwarded, again without rebase or history rewrite,
to exact current `rh`
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`. At this R5 freeze, local `rh`,
tracking `origin/rh`, H-03 HEAD, and merge-base all resolve to `332ae2bc…`;
the branch is zero commits ahead/behind `rh`. The delta after `cb3fe739…`
contains the Track 8 M1 brief only and touches no H-03-owned production or
implementation file. No Phase B module/test exists.

On 26 July 2026, R6 was bootstrapped independently from clean integrated
`rh` at `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`, tree
`b2c2358f565e27ad6a5c787a9a0d1396af513076`. Local `rh`, cached
`origin/rh`, and live `origin/rh` matched. The exact R6 local branch, cached
and live remote branch, worktree registration, and filesystem path were all
absent before creation. The rejected R5 worktree was not reused or modified;
its two input hashes matched the frozen values in Section 3.2 before they were
copied byte-for-byte.

At the prepublication R6 candidate freeze, local `rh`, cached `origin/rh`,
live `origin/rh`, R6 HEAD, and merge-base all resolved to `c0d0e708…`. No
Phase B module/test existed. The R6 worktree then contained two unstaged
documentation changes: this untracked evidence record and the corrected
tracked H-03 brief.

After exact-hash approval, the provenance amendment, independent confirmation,
and the authorized feature publication, the R6 branch advanced by exactly one
two-document commit to `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`;
local, tracking, and live feature refs matched. Integrated `rh` remained
`c0d0e708…` at that publication checkpoint.

The complete-file chronology correction was later committed at
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4` and integrated through merge
`8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. At this lifecycle-correction
bootstrap, clean local, cached, and live `rh` all resolve to
`7098211db5693f986b65ec7a9e897f3518e9538c`, tree
`c07329ed9fcc2dc99afbef3f7888f478024d1ede`. The requested branch/worktree
were absent before creation. The approved brief and integrated evidence
matched their declared hashes, and no Phase B module/test exists.

Prerequisite integration identities present in that ancestry:

| Prerequisite | Integrated identity |
| --- | --- |
| H-01 dependency security | merge `575d47b82055b42da2bddf1535d8076cd7cf4c63` |
| S1 clock harness | merge `f03e128905de395b7162110cab42582866e7ccc4` |
| S2 checked inventory | merge `454fbeb8e1bc1401fe1db0c44b98e9c487f3c504` |
| S3 Lootbox floor | merge `3e6e6f230169fc445d0b29454457480c62efd89a` |
| H-02 network profiles/CLI safety | original merge `6c3052668555a7104ea12a7fb1a7c641c7e6b304`; reviewed correction `5c1ba54c5d34670ddba13ce84e46f490f8a8aaa4`; correction merge `cb3fe7392c44613aaeec49bd2486369fe0da3556` |
| Track 8 M0 owner closure | reviewed decisions `c5c8b699b229792dc61e66af35502684ea3c8155`; closure `11824aa672809ad49ad7b2f823b9fb02c6e4608b`; integration merge `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` |
| Track 8 M1 brief | `332ae2bc8e0ce4b694766d6d20759295d9267ec3`, documentation only; decision approval is owner-attested; mutable worktree evidence is non-authoritative and M1 remains blocked |
| H-01 exception retirement/preflight evidence | feature commits `2b6920c2fc9044cbfb6f715c03674e96027084e3` and `495905d351e1d627e34fc6a8505992c07916c4fd`; integration merges `b8add98` and `60dc7c4` |
| H-01 dependency implementation | owner-authorized integrated commit `d62777646cba1ae448fb9e26519c6fa295f437df`, tree `01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61` |
| H-01 exception-retirement transition | integrated commit `7098211db5693f986b65ec7a9e897f3518e9538c`, tree `c07329ed9fcc2dc99afbef3f7888f478024d1ede` |
| S6/H-04 reconciled brief | feature commit `d7809b82f0e2adc660b1e40fe0e4e28d6056b35a`; integrated at `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| H-03 R6 Phase A | publication `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`; chronology correction `d65e4dbd6ab832cc65265b9bda443cd8031b20e4`; integration merge `8e4a965f034dc3d11b60fbb674ebbb4095b57d98` |

### 3.2 Frozen file hashes

Unless explicitly labeled candidate or rejected, hashes are SHA-256 of
integrated baseline files. The R6 starting hashes prove byte continuity from
the rejected R5 candidate, and the R5 starting hashes preserve continuity from
rejected R4b. The approved and post-amendment R6 hashes are recorded in the
status/history and designated provenance block. Feature publication at
`2c8468a…`, chronology correction at `d65e4db…`, and integration through
`8e4a965…` preserve their distinct lifecycle roles. Because the current
lifecycle correction changes non-provenance bytes, its final hash must be
reported outside this self-referential file and receive complete-file review
and fresh owner approval before any follow-up commit, reconciliation, or
integration.

| Authority/input | SHA-256 |
| --- | --- |
| R6 starting brief / rejected R5 brief | `0fdc573ea4955bf78976f0bcff18accb6bf90857e160bedf3035e37327a7d4a0` |
| R6 starting evidence / rejected R5 evidence | `ad31229f5fda9a262ba00e20482a99a6f486fbf92644b342cf132684f7f82cb5` |
| Approved and integrated H-03 brief | `f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5` |
| Integrated H-03 evidence before this lifecycle correction | `ed81dad7aaad41150ee49d20134916c9660e283ac77f85a2b0e5fe757ab2036c` |
| R5 starting brief / rejected R4b brief | `6c52679aca8e05d806705bc962edd522c5d633c7b54a5e3a74940cd0fd2711af` |
| R5 starting evidence / rejected R4b evidence | `c2d658943b7812651e5cbcbc8b000985666243d8b478672e22fe891c21fe50b5` |
| R4b starting brief / rejected R3 brief | `746e262b410bcf3b0e73179cb6df905deaa679cc01acd50d0b2263bd23e56d5d` |
| R4b starting evidence / completed R4a candidate | `199a089ded8841822cfab822b74357db72c51d63471eaa93d725942f22e359ab` |
| Rejected R3 evidence | `a8e39f3ab4cb341923d16d289ece823638d4e981c837d1a26644dbbc455f531d` |
| Rejected H-03 brief after the two-line R2 amendment | `9f441023032dab1d52848155186fe3a365a8b4f3e543934914732ee96cec8721` |
| H-03 brief before that amendment | `84055f1c1ad3505b38250bf2d2a4851fae8d3358642237ef37da76e59ab5ba4b` |
| Track 7 deployment-support brief | `d84e59bc79caf555fbb51e61fd78840f40be0c08f69be73cf1706da63e95e72b` |
| Track 7 support specification | `1e3fc931ecab674e3ec61640f5c649458d1d6793eecb30465614455090312906` |
| Track 7 validation plan | `5ffbcfc14cb33e9a5cdc5f2c300cf3d1f9bae90fd90e14d04a408cbe274a94fb` |
| H-02 brief | `f37597f37d6cf785f50bac0954709e2f60dde7ab836ed2c699cab45e5d105b59` |
| H-02 implementation evidence | `79cf2f7e5c362b8880f2c460abac946126bf2f329425a82e3c8f5bd4da9a8de7` |
| `config/network_profiles.py` | `9c19d237eaa049a9d521fc3ab8ef868e6ee35ab6ba48c45e61180fa2daf8c42a` |
| H-02 network-profile tests | `9178b2a13c7c6a6102c21d592d609ccd2ab1dea099450397f17ca9ddd81dd7c6` |
| H-02 secret-handling tests | `ac27dcb31f4c17459cb45847ec904237bf790225b53184d3d2e2e4e95cdee2f3` |
| H-02 Base regression tests | `6da51a700e7a8a914ee541b594fa4bb4cb45df6b2a62842695898f2e467f9ecb` |
| `scripts/migrate.py` | `6401e3fe35f29981378bb187a4070b1b0a75e6f7105204269e65aeef4aa6a12c` |
| `scripts/console.py` | `a7f0c2b15db0634398dbf975bd40fe5cb449a96e7da6ff5a1c9159df75ec5f6a` |
| `scripts/verify.py` | `5db7f0f50d509ca96560a22534647e0c36109dc8232a1bc790c8e7ddd4237edb` |
| `scripts/utils/migration_helpers.py` | `559c7648f871e6b71b7d13f306290fee7c0d3fbe6d13182996964ba5b79465db` |
| Existing Base/local `config/BluePrint.py` | `26db41634bc716cf21ba0f948ace40f8bc4869ae02ee3fa4ef178f499280cb05` |
| Component matrix | `33747982b11a1f9430619710b8b2007113dfb5961a90162def4c852c1b6b18e6` |
| Track 8 brief | `c885c25f5a19f0531a15ce947534a4a054bf6e18ef7f198734d879dfd6a52637` |
| Track 8 specification | `84e3368991803a92ffe2f82f47ef762045cdd9ed90ddd6a833e1531c866d4059` |
| Track 8 validation plan | `675f31c7245243b286649b95f1d621c42fc9a662bc3f70cf446c76bb028325bf` |
| Track 8 M0 evidence | `1ca5ec599e7bab406dd63e2d220251bb085ac2fbf9416bc8f4585632e283e4be` |
| Track 8 M0 sanitized raw evidence | `9ea333b4e84330f56c3a3d70e68823cfdba9c37948508e692450e01b3e994cba` |
| Track 8 M0 owner-decision packet | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` |
| Track 8 M1 exact-receipt brief | `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270` |
| H-04/S6 defaults and parameters brief | `2d9a1e0777751265b4aacc1c65434349e19c7c91f2a1d796bf9ff0f4bb349010` |
| Track 1 Chainlink/CCIP confirmation | `9ba6dced9650ab4df381044336d8a1466fb1c38c2d9eafc11859e21c1c876c26` |
| Track 1 CCIP integration decision | `d2e0b25b9146fdfd06553da39fc106f0b45751013990dc7e21a578f8ae196b83` |
| Track 1 CCIP public evidence | `d7e08e3dc7d28d78db2c5486f77d7efe1d2c7d0f37fcad3ff2ce58119f069094` |
| Track 1 CCIP Chainlink question packet | `47c650fb1427e939da2fd0d82344e06b6b72b9c69bf0b1fac1798920ff55df44` |
| H-01 `requirements.in` | `1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9` |
| H-01 `requirements.txt` | `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` |
| H-01 dependency gate | `8860b81b694d0fd8f1a6bb886b819c13b4817f7f4522ab74a712cad03dbe2582` |
| H-01 dependency preflight brief | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| H-01 dependency evidence | `81baca680d8f21c309d87e83f25366ea50c8d27700cd3e0d6ea7001a1892b41c` |
| H-01 exception-retirement feasibility evidence | `9b9ad56d73d8a7418dcc0e452b3affb927979ce53fd90fcd5f84f9b9dfcfbfec` |
| H-01 exception-exit preflight evidence | `6522a11207b6e0735e443ffb9cc4566f3be8090e3e1d35305b92150b24305491` |
| Base current manifest, comparison evidence only | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |

### 3.3 Historical R5 exact-lock environment and R6 dependency boundary

For the historical R5 run, the ambient environment did not match the complete
H-01 lock, so it was not used. A mode-0700 disposable environment under
`/private/tmp` was installed only from the exact integrated
`requirements.txt`. Its versions were:

| Runtime/package | Version |
| --- | --- |
| Python | 3.12.0 |
| pip | 23.2.1 |
| Vyper | 0.4.3 |
| Titanoboa | 0.2.7 |
| pytest | 8.4.2 |
| python-dotenv | 1.2.2 |
| cbor2 | 5.9.0 |
| requests | 2.33.0 |
| urllib3 | 2.7.0 |
| idna | 3.15 |
| pymdown-extensions | 10.16.1 |

`python -m pip check` passed. The active environment and dependency files were
not changed. Public package retrieval was the only outbound dependency
bootstrap activity and was expressly allowed by the Phase A authorization.
No downloaded or network-derived protocol value is evidence in this record.

R6 is documentation-only and did not install dependencies or claim an
exact-lock green test run from the ambient environment. The later H-01 package
and exception-retirement transition are now integrated at the exact identities
above. They retain Click `8.3.3`, Pygments `2.20.0`, Pymdown Extensions
`10.21.3`, pytest `8.4.2`, Titanoboa `0.2.7`, and Vyper `0.4.3`; retire the
Click, Pygments, and Pymdown Snippets exceptions; and retain the pytest and
Pymdown b64 exceptions as operative. They make no GitHub/Dependabot
alert-closure claim.

The H-01 transition inherited and validated its exact package interval, but
that is not the H-03 Phase B validation gate. Fresh exact-lock environment and
dependency-gate validation against the corrected, integrated H-03 authority
remains required before Phase B begins; the later three-file implementation
must be validated in that same exact lock before Gate 1. No such H-03 Phase B
exact-lock run is claimed here.

## 4. Baseline and isolated-worktree validation

All pytest commands were serial. Relevant RPC/account/key environment
variables were absent; the non-secret explorer placeholder required by the
existing test harness was used; Boa cache and pytest basetemps were isolated
under `/private/tmp`. No test contacted a protocol RPC or explorer.

| Gate | Untouched integration baseline | Isolated H-03 worktree |
| --- | --- | --- |
| H-01 dependency gate | 16 passed; 3 warnings (observed); 1.44 s | 16 passed; 3 warnings (observed); 1.38 s |
| H-02 targeted suite, including Base regression | 95 passed; 3 warnings (observed); 13.42 s | 95 passed; 3 warnings (observed); 12.46 s |
| S1 clock profiles | 57 passed; 3 warnings (observed); 104.77 s | 57 passed; 3 warnings (observed); 25.47 s |
| S2 checked-inventory tests | 60 passed; 3 warnings (observed); 25.70 s | 60 passed; 3 warnings (observed); 24.42 s |
| S2 inventory script | `CLOCK_INVENTORY_OK`; production occurrences 100, production lines 95, production files 17, block-number IDs 32, records 100, indirect IDs 1, cadence candidates 455, seconds-unit candidates 58, timestamp IDs 11, timestamp occurrences 37, mixed-clock functions 4, Vyper paths 92 | Identical |
| Collection | 2,833 collected/selected; 142 deselected; 3 warnings (observed); 1.29 s | 2,833 collected/selected; 142 deselected; 3 warnings (observed); 5.16 s |
| Full suite | 2,833 passed; 142 deselected; 3 warnings (observed); 304.35 s | 2,833 passed; 142 deselected; 3 warnings (observed); 299.16 s |

There were no skips or xfails. The three warnings in these broader runs are the
established pytest assertion-rewrite warnings for already imported
`_hypothesis_globals`, `hypothesis`, and `boa`.

The warning count is recorded as observed launcher/import-order evidence, not
as an acceptance invariant. A clean invocation may emit zero of these warnings
without weakening or invalidating the gate; the selected/collected/pass counts
and absence of unexpected skips, xfails, or failures are authoritative.

The H-08-owned `tests/deployment/test_registry_topology.py` does not exist at
this baseline. That is expected and is not an H-03 failure. Phase A did not
create, skip, or xfail a substitute.

### 4.1 Reconciliation validation on 25 July 2026

After H-02's post-integration correction merged into `rh`, the H-03 branch was
fast-forwarded without rebase or history rewrite to exact commit
`cb3fe7392c44613aaeec49bd2486369fe0da3556`. The untracked Phase A evidence
file was preserved byte-for-byte across that operation and then updated only
for this reconciliation. The branch, local `rh`, cached `origin/rh`, and live
remote `origin/rh` all resolved to that exact commit before validation.

Validation used a fresh mode-`0700` CPython 3.12.0 environment installed from
the integrated lock. All 92 locked distributions matched exactly and
`python -m pip check` reported no broken requirements. Boa cache and every
pytest basetemp were isolated beneath the same private `/private/tmp`
directory. Relevant RPC/account/key environment variables were absent and the
existing non-secret explorer placeholder was used. No test contacted a
protocol RPC or explorer.

| Reconciliation gate | Result |
| --- | --- |
| H-01 dependency gate | 16 passed; 3 warnings (observed); 1.55 s |
| Integrated H-02 suite, including Base regression | 99 passed; 3 warnings (observed); 13.48 s |
| S1 clock profiles | 57 passed; 3 warnings (observed); 41.20 s |
| S2 checked-inventory tests | 60 passed; 3 warnings (observed); 25.37 s |
| S2 inventory script | `CLOCK_INVENTORY_OK`; production occurrences 100, production lines 95, production files 17, block-number IDs 32, records 100, indirect IDs 1, cadence candidates 455, seconds-unit candidates 58, timestamp IDs 11, timestamp occurrences 37, mixed-clock functions 4, Vyper paths 92 |
| Collection | 2,837 collected/selected; 142 deselected; 3 warnings (observed); 5.46 s |
| Full suite | 2,837 passed; 142 deselected; 3 warnings (observed); 300.61 s |

There were no skips or xfails. The three warnings are the same established
pytest assertion-rewrite warnings for already imported
`_hypothesis_globals`, `hypothesis`, and `boa`. H-02's correction increased
the selected suite from the historical 2,833 cases above to 2,837. No H-03
module or test file existed or was created during reconciliation.

As above, the warning count is observational and may vary with import order.
It is not a required invariant and a zero-warning run is not a failure.

### 4.2 R4b current-environment regression on 26 July 2026

R4b reran the complete currently applicable serial battery with all relevant
RPC variables absent, `ETHERSCAN_API_KEY=local-placeholder`, a private
Titanoboa cache, isolated pytest basetemps, and no network or dependency
change. The three Phase B H-03 files and the H-08 topology test correctly do
not exist, so their steps are not applicable and were not synthesized,
skipped, or xfailed.

| R4b gate | Result |
| --- | --- |
| Base profile regression | 30 passed; 3 warnings; 7.46 s |
| Integrated H-02 suite | 98 passed, 1 skipped, 3 warnings; 12.08 s |
| H-01 dependency gate | 15 passed, 1 failed, 3 warnings; 1.47 s |
| S1 clock profiles | 57 passed; 3 warnings; 27.36 s |
| S2 checked-inventory tests | 60 passed; 3 warnings; 23.89 s |
| S2 inventory script | `CLOCK_INVENTORY_OK`; production occurrences 100, production lines 95, production files 17, block-number IDs 32, records 100, indirect IDs 1, cadence candidates 455, seconds-unit candidates 58, timestamp IDs 11, timestamp occurrences 37, mixed-clock functions 4, Vyper paths 92 |
| Existing Base blueprint/deploy-args import | `BLUEPRINT_DEPLOY_ARGS_IMPORT_OK` |
| Collection | 2,837 selected of 2,979 collected; 142 deselected; 3 warnings; 1.14 s |
| Full suite | 2,835 passed, 1 failed, 1 skipped, 142 deselected, 3 warnings; 280.70 s |

Both non-green results are reproduced environment gates, not H-03 document
regressions. `test_selected_and_held_versions_match_lock_and_runtime` fails
because the existing `ripe-lite` runtime has cbor2 5.7.0, idna 3.10,
python-dotenv 1.1.0, requests 2.32.5, urllib3 2.5.0, and wheel 0.45.1 while
the unchanged approved lock requires 5.9.0, 3.15, 1.2.2, 2.33.0, 2.7.0, and
0.46.2, respectively. The H-02 skip is
`tests/deployment/test_secret_handling.py:692`, because IPython 9.8.0 is
absent from the active environment. The exact-lock green results in Sections
3.3–4.1 remain the
reviewed baseline; R4b did not install packages or make the network request
that a fresh exact-lock environment would require. Phase B and release gates
must use the approved exact lock and return to fully green/no-skip results.

### 4.3 R5 current-environment regression on 26 July 2026

R5 replayed the same complete currently applicable serial battery. Every
pytest command used a separate mode-`0700` basetemp and Titanoboa cache under
`/private/tmp`, all four configured RPC variables and credential variables
were absent, and `ETHERSCAN_API_KEY=local-placeholder` was the documented
non-secret offline collection value. No network or dependency change was
made. The uncreated Phase B H-03 and H-08 files remain inapplicable.

| R5 gate | Result |
| --- | --- |
| Base profile regression | 30 passed; 3 warnings; 7.72 s |
| Integrated H-02 suite | 98 passed, 1 skipped, 3 warnings; 12.77 s |
| H-01 dependency gate | 15 passed, 1 failed, 3 warnings; 1.53 s |
| S1 clock profiles | 57 passed; 3 warnings; 99.40 s |
| S2 checked-inventory tests | 60 passed; 3 warnings; 24.68 s |
| S2 inventory script | `CLOCK_INVENTORY_OK`; production occurrences 100, production lines 95, production files 17, block-number IDs 32, records 100, indirect IDs 1, cadence candidates 455, seconds-unit candidates 58, timestamp IDs 11, timestamp occurrences 37, mixed-clock functions 4, Vyper paths 92 |
| Existing Base blueprint/deploy-args import | `BLUEPRINT_DEPLOY_ARGS_IMPORT_OK` |
| Collection | 2,837 selected of 2,979 collected; 142 deselected; 3 warnings; 1.45 s |
| Full suite | 2,835 passed, 1 failed, 1 skipped, 142 deselected, 3 warnings; 282.74 s |

The only failure and skip are the same environment gates documented in
Section 4.2: the active `ripe-lite` versions do not match the approved lock,
and IPython 9.8.0 is absent. No H-03 document assertion failed. The three
warnings are the established assertion-rewrite warnings caused by importing
Boa before pytest to redirect its compiler cache. R5 does not reinterpret
this current-environment replay as the exact-lock green release gate.

### 4.4 Prepublication R6 documentation-only mechanical validation on 26 July 2026

R6 installed no dependency and ran no pytest or exact-lock claim. The
documentation-only validators independently reproduced:

- 60 unique component records: 38 required, 16 omitted, 5 deferred, and
  1 blocked;
- 94 unique surfaces with kind counts 7 artifact, 18 capability, 43 route,
  3 permission, 7 configuration, 7 registration, and 9 behavioral invariant;
- surface dispositions 10 required, 20 omitted, 29 disabled, 5 deferred, and
  30 blocked;
- surface lifecycle cardinalities 29 deployed-initial, 17 pre-activation,
  4 atomic Stock activation, 6 CCIP promotion, 0 reward activation,
  5 post-launch, 20 omitted, and 13 blocked;
- exactly two deferred promotions: CCIP over its six exact surfaces and
  rewards over its seven exact surfaces;
- 288 sequential, field-complete, unique typed relations over 284
  phase-qualified triples, with kind/phase counts stated in Section 7A.3 and
  the exact 34-source/26-no-edge partition;
- 712 canonical relation-table proof references / 415 unique ranges /
  46 files and 735 complete-Section-7A.3 proof references / 434 unique ranges /
  62 files, with every file read and every cited range in bounds;
- 103 path records with exact 92/6/5 kind, 91/7/4/1 state, and 53/35/9/3/3
  source-class cardinalities;
- 48 symbolic inputs, 24 assertion IDs, 18 blockers, 11 owner IDs,
  21 evidence IDs, and 38 registry expectations, with no duplicate, dangling,
  orphaned, or unused canonical ID;
- all 43 mutation-matrix rows resolving to the complete 14-diagnostic API;
  and
- all 793 file/range citations in this complete evidence record resolving
  across 66 files with valid bounds.

At the prepublication candidate freeze, the exact two-file Git scope check
found only the tracked brief modification and untracked evidence record, with
no staged path. `git diff --check` reported no whitespace error. The required
untracked
`git diff --no-index --check /dev/null <evidence>` returned the expected
status 1 for a nonempty file and emitted no whitespace diagnostic. Markdown
fences, tables, local links, and conflict-marker checks passed. The
sensitive-literal scan found no EVM address, URL, PEM marker, private-key
literal, RPC value, or credential value; the two historical
`ETHERSCAN_API_KEY` local-placeholder references are the documented non-secret
offline test placeholder.

The later approval/provenance/publication/correction/integration sequence is
recorded in the status, Section 3.1, Section 10, and Sections 17–18. The
current lifecycle correction must rerun the applicable documentation checks
and be reviewed as a complete new evidence candidate. H-03 Phase B exact-lock
validation remains a required gate under Section 3.3 and is not claimed here.

## 5. Integrated H-02 API and approved R6 H-03 API

### 5.1 H-02 public surface consumed

Integrated `config/network_profiles.py` exposes frozen/slot-based
`NetworkIdentity`, `RepositoryPolicy`, and `NetworkProfile` records; the
`ProfileEnvironment` and `PathState` enums; immutable `NETWORK_PROFILES`;
`canonical_profile_ids()`; `get_profile(value)`; `validate_registry()`; and
`NetworkProfileError`.

The exact accepted H-03 profile IDs will be:

- `robinhood-mainnet`
- `robinhood-testnet`

Both resolve through `get_profile`. Both currently carry the proposed shared
`migrations/robinhood` namespace, separate proposed history namespaces, and a
`repository.blueprint_id` of `None`. There are no aliases. H-03 will not mutate
H-02 or create another profile registry.

H-02 lookup case-folds its input. H-03 must first require exact membership in
its two-ID tuple and only then call `get_profile`; this deliberately rejects
case variants and any future alias.

### 5.2 Approved R6 immutable schema

Phase B may define only these closed enums and frozen, slot-based dataclasses:

| Type | Closed values or fields |
| --- | --- |
| `Disposition` | `required`, `omitted`, `disabled`, `deferred`, `blocked` |
| `SurfaceKind` | `artifact`, `capability`, `route`, `permission`, `configuration`, `registration`, `behavioral_invariant` |
| `LifecyclePhase` | `deployed_initial_value`, `pre_activation_configuration`, `atomic_stock_activation`, `within_seven_day_separately_reviewed_ccip_promotion`, `within_seven_day_separately_reviewed_reward_activation`, `post_launch_release`, `omitted`, `blocked` |
| `RelationPhase` | `constructor`, `bootstrap`, `post_deployment_setup`, `registration_order`, `runtime_security` |
| `RelationKind` | `construction_dependency`, `bootstrap_dependency`, `setup_dependency`, `registration_order_dependency`, `direct_execution`, `authority_dependency`, `indirect_security_dependency` |
| `SourcePathState` | `existing`, `reviewed_planned`, `external_pending`, `absent` |
| `SourcePathKind` | `file`, `directory`, `none` |
| `SourceClass` | `shared_contract`, `chain_specific_config`, `external_integration`, `non_onchain_tooling`, `external_artifact` |
| `RegistryDomain` | `ripe_hq`, `vault_book`, `price_desk`, `switchboard` |
| `RegistryIdAuthority` | `source_hard_coded`, `registration_order`, `provisional_reservation` |
| `ComponentRelation` | `relation_id`, `kind`, `phase`, `target_component_id`, `source_proof_refs`, `basis`, `evidence_authority_ids` |
| `SourcePathRecord` | `path`, `path_kind`, `path_state`, `source_class`, `evidence_id` |
| `SymbolicInput` | `field_id`, `semantic_class`, `consumers`, `primary_owner_id`, `co_owner_ids`, `deadline_gate`, `status`, `blocker_ids` |
| `Blocker` | `blocker_id`, `primary_owner_id`, `co_owner_ids`, `summary`, `deadline_gate` |
| `SurfaceRecord` | `surface_id`, `component_id`, `kind`, `semantic_meaning`, `disposition`, `lifecycle_phase`, `blocker_ids`, `assertion_ids` |
| `PromotionRecord` | `promotion_id`, `surface_ids`, `promotion_phase`, `disposition`, `primary_owner_id`, `co_owner_ids`, `blocker_ids`, `assertion_ids` |
| `RegistryExpectation` | `domain`, `registry_id`, `semantic_name`, `authority`, `component_id`, `disposition` |
| `ComponentRecord` | `component_id`, `name`, `source_paths`, `deployment`, `registry_expectations`, `surfaces`, `relations`, `blocker_ids`, `primary_owner_id`, `co_owner_ids`, `negative_assertion_ids`, `downstream_slices`, `controlling_evidence_ids` |
| `RobinhoodBlueprint` | `blueprint_id`, `profile_ids`, `symbolic_inputs`, `blockers`, `promotions`, `components` |

These eight `LifecyclePhase` values are the exact enum-safe spellings of
H-04/S6's controlling vocabulary. H-03 must not collapse them into generic
`launch`, `fast_follow`, `later_release`, or `not_applicable` buckets.
For a `SurfaceRecord`, `lifecycle_phase` identifies the controlling checkpoint
at which that row's recorded disposition is evaluated; it is not implicit
permission to transition to another disposition. A possible transition is
represented separately by a `PromotionRecord`.

If a surface is a member of a `PromotionRecord`, uses that promotion's phase,
and already exists on a launch-deployed component, a `disabled` disposition
is a continuous pre-promotion invariant: it must hold at
`deployed_initial_value` and through the promotion checkpoint. This exact
rule applies to `S-001-CCIP-CAP` and `S-002-CCIP-CAP`. The other four CCIP
members are deferred artifact, registration, or toolchain surfaces. The
promotion-phase label on the two token capabilities therefore records their
controlling reviewed action without leaving their launch state unspecified.

Reward surfaces use the other permitted representation: all seven carry
`disabled` at `deployed_initial_value`, while only their separate
`PromotionRecord` carries
`within_seven_day_separately_reviewed_reward_activation`. This removes the
former ambiguity in which a launch-disabled reward surface carried a
seven-day lifecycle that could be misread as either current state or earliest
activation.

All collection fields are tuples. No mutable mapping or list is stored. Lookup
indexes, if desired, are derived and returned read-only; the primary component
tuple remains the sole component authority. A nested `SurfaceRecord` repeats
its parent `component_id` only so validation can detect a surface moved between
components; the value must equal its containing record.

`SymbolicInput.consumers` is the sole component-to-input relation. Components
do not duplicate a parallel input-ID list. Every input has one exact primary
`OWN-*` ID, an immutable tuple of exact co-owner IDs, one status, one deadline
gate, at least one consumer, and only declared blockers. Composite prose,
`same`, slash-separated abbreviations, and undeclared owner aliases are
invalid.

`ComponentRecord.relations` replaces the former untyped `dependencies` list.
Every relation has one stable relation ID, one kind, one phase, an exact CM
target, a nonempty immutable `source_proof_refs` tuple, a semantic basis, and
a nonempty tuple of declared evidence-authority IDs. Each proof tuple member
resolves to exact repository `path:line` or `path:start-end` source; the
display order in Section 7A.3 is the immutable tuple order. A workflow, slice,
tool, replacement fact, or future-release statement is never a target.
Selected-source to omitted-target relations are allowed only when direct
source proves a launch-disabled or fail-closed route. Replacement and
supersession facts otherwise live in deployment disposition, blockers,
downstream ownership, or controlling evidence.

Relations are included if and only if they materially constrain deployment
construction/bootstrap/setup/order or a launch/security invariant. They do not
model the complete runtime call graph. Ordinary calls are excluded; runtime
records survive only when their presence or absence controls custody,
accounting, mint/burn authority, governance/configuration authority,
valuation, debt, liquidation, auction settlement, collateral redemption,
deleverage, rewards, registry semantics, a required launch route, or a
fail-closed/omitted route. An unprovable proposed relation is omitted and,
where a launch binding is required, recorded as a blocker rather than guessed.

Approved `D-H03-005` fixes the semantics. `direct_execution` points from the
operational caller to the callee. `authority_dependency` points from a
governed contract to the registry/controller whose check governs it. A
controller points to a target only for a source-proved direct call; a
configuration writer does not point to downstream consumers. Registry
membership is represented by `registration_order_dependency` and Section 8,
not fictitious runtime calls. A transitive assertion uses
`indirect_security_dependency` only when its proof tuple covers every source
hop. Phase B may not reinterpret or regroup these records.

H-03 does not define an executable total deployment order or claim acyclicity.
The token/RipeHq pair remains the worked example: RipeHq takes token addresses,
while token HQ assignment has distinct bootstrap/setup constraints. H-05 owns
the executable sequence and must revalidate every relation from source.

`SourcePathRecord` is per exact path, not per component. This permits a
component to carry existing, reviewed-planned, external-pending, and absent
records without flattening them into one state. `path=None` is valid only with
`path_kind=none` and state `external_pending` or `absent`; `existing` and
`reviewed_planned` require exact repository-relative file or directory paths.
Directories are explicit paths, not globs. Every evidence ID resolves in
Section 6.1.

Canonical surfaces are included if and only if their state must survive into
H-04/H-05/H-08/H-09 and the boundary is launch- or security-relevant.
Ordinary absence already implied by an omitted component is excluded; the
component disposition and its negative assertions prove that absence. Every
surviving surface has explicit semantic meaning and one exact lifecycle phase.
An omitted component may not contain a `required` surface.

A promotion record is included only when an owner-selected launch-disabled or
deferred surface has a separately reviewed later action. Its referenced
surface set is exact and nonempty; its disposition remains `deferred`; an
elapsed deadline never mutates the referenced launch state. The current
canonical promotion inventory contains exactly two records in Section 7A.2.1:
one for GREEN/RIPE CCIP promotion and one for reward activation.

#### 5.2.1 Per-field necessity and downstream consumer rationale

The schema is limited to facts H-04, H-05, H-08, or H-09 must consume or H-03
must validate before handoff:

| Field group | Why it is necessary |
| --- | --- |
| dispositions, surface kind, semantic meaning, lifecycle phase | preserve required artifact versus inactive/omitted/deferred/blocked behavior and identify when each recorded surface state must hold |
| promotion ID, exact surface IDs, phase, disposition, owners, blockers, assertions | separate a possible later reviewed action from launch-disabled state and prevent elapsed time from self-activating it |
| relation ID, kind, phase, target, proof, basis, evidence authorities | let H-05 rederive only deployment/security-critical constraints, preserve caller/authority/indirect semantics, and reject ambiguous grouping |
| path, kind, state, class, evidence | let H-05 package and H-09 hash exact existing/planned/external authorities without globs or mixed-state flattening |
| symbolic ID, class, consumers, primary/co-owners, deadline, status, blockers | preserve every unresolved constructor/configuration fact and prevent an implementation agent from selecting or silently losing it |
| blocker ID, owners, summary, deadline | provide one fail-closed cross-slice closure authority |
| registry domain, ID, semantic name, authority, component, disposition | distinguish hard-coded, order-derived, and reserved topology and prohibit semantic substitution |
| component ID/name/deployment | preserve the exact CM-001–060 authority and deployment posture |
| component surfaces/relations/source paths | bind each canonical boundary to exactly one component and make missing/extra records fail |
| component blockers/owners/assertions/downstream/evidence | make responsibility, negative proof, supersession, and handoff deterministic |
| blueprint ID/profile IDs/record tuples | identify the immutable graph and reject aliases, Base, local, or future profiles |

The complete R6 surfaces, promotions, source paths, symbolic inputs, blockers,
owners, component rows, and explicit typed relation records are
all displayed in Phase A. Phase B may encode only approved records; it may not
derive, append, or silently correct an unseen crosswalk. Any ambiguity,
missing proof, path-class disagreement, relation-kind/orientation change, or
inventory change requires a new reviewed Phase A amendment.

### 5.3 Exact approved R6 public API

`config/robinhood_blueprint.py` should expose:

```text
ROBINHOOD_BLUEPRINT_ID: str = "robinhood-v1"
ROBINHOOD_PROFILE_IDS: tuple[str, str]
ROBINHOOD_BLUEPRINT: RobinhoodBlueprint
get_robinhood_blueprint(profile_id: str) -> RobinhoodBlueprint
get_component(component_id: str) -> ComponentRecord
get_symbolic_input(field_id: str) -> SymbolicInput
get_blocker(blocker_id: str) -> Blocker
get_promotion(promotion_id: str) -> PromotionRecord
validate_blueprint(
    blueprint: RobinhoodBlueprint = ROBINHOOD_BLUEPRINT,
) -> None
RobinhoodBlueprintError(RuntimeError)
```

`get_robinhood_blueprint` returns the same immutable singleton for both exact
profiles. The module imports only H-02 `get_profile` for identity
confirmation. It does not read environment, filesystem, Git, accounts, Boa,
RPC, migration state, manifests, defaults, or addresses.

`RobinhoodBlueprintError` subclasses `RuntimeError` deliberately, matching
H-02 `NetworkProfileError`. A caller that validates a network profile and its
blueprint under one `except RuntimeError` boundary therefore cannot miss an
H-03 validation failure. H-03 adds no richer exception hierarchy.

Approved R6 stable validation diagnostics:

| Code | Failure |
| --- | --- |
| `H03_PROFILE_EXACT` | nonexact, aliased, Base, local, unknown, or case-varied profile |
| `H03_COMPONENT_SET` | missing, extra, noncontiguous, or duplicate CM ID |
| `H03_IMMUTABLE` | non-tuple or mutable nested state |
| `H03_DISPOSITION` | invalid or flattened deployment/surface status |
| `H03_SYMBOLIC_FIELD` | missing, value-bearing, consumerless, unowned, multiply owned, prose-owned, mixed-status, or un-gated symbolic field, or unresolved consumer ID |
| `H03_ADDRESS_LITERAL` | address-shaped string or forbidden Base/local value |
| `H03_RELATION` | missing/duplicate relation ID; unknown kind, phase, target, proof, or evidence authority; workflow/slice/prose target; wrong orientation; incomplete indirect proof tuple; phase-confused record; duplicate typed identity; or a deleted canonical record |
| `H03_SURFACE_SET` | missing, extra, duplicate, unknown-kind/lifecycle, absent semantic meaning, component mismatch, field-incomplete record, or deleted canonical surface |
| `H03_PROMOTION_SET` | missing, extra, duplicate, field-incomplete, nondeferred, wrong-phase, cross-assigned or wrong surface set, unowned, unblocked, or self-activating promotion |
| `H03_SOURCE_AUTHORITY` | missing component/path record, unknown evidence ID, wrong class/kind/state, invented path, broad glob, existing-versus-planned confusion, invalid absent path, or claimed-existing missing path |
| `H03_BLOCKER` | unresolved blocker or component without exact accountable primary/co-owner IDs |
| `H03_REGISTRY_TOPOLOGY` | shifted ID, wrong semantic name/authority class, placeholder, or reused reservation |
| `H03_OMISSION_SURFACE` | omitted component has a deployable/callable surface |
| `H03_TRACK8_GATE` | Stock or other M0-selected surface represented as active before later gates |

### 5.4 Existing and future consumers

The repository-wide use map shows:

- `scripts/utils/deploy_args.py` imports `PARAMS`, `ADDYS`, `CURVE_PARAMS`,
  `CORE_TOKENS`, and `YIELD_TOKENS` from `config/BluePrint.py` and wraps them in
  its unrelated mutable `BluePrint` class.
- `scripts/migrate.py` and `scripts/console.py` consume H-02
  `repository.blueprint_id`; they do not import the proposed module.
- `scripts/params/params_utils.py`, the Base migrations, shared test fixtures,
  and contract/unit tests consume the existing Base/local dictionaries.
- `WHALES` has test-only consumers; it has no production deployment consumer.
- No current file imports `config.robinhood_blueprint`.

Therefore H-03 need not modify a consumer. H-04, H-05, and H-09 will consume
the new API read-only in their separately reviewed slices. H-05 owns any
future mapping between H-02 repository policy and the blueprint; H-03 must not
set `repository.blueprint_id`.

This boundary is also required by integrated H-02 validation: both Robinhood
profiles currently have `PathState.PROPOSED`, and `migrations/robinhood` does
not yet exist. H-02 therefore rejects any non-`None`
`repository.blueprint_id` until H-05 creates and reviews that namespace.
`ROBINHOOD_BLUEPRINT_ID` identifies the H-03 immutable graph only; it cannot be
copied into H-02 repository policy by H-03 or adopted by a consumer before the
H-05 namespace gate closes. Its exact H-03 value is `robinhood-v1`, which
satisfies H-02's lowercase identifier grammar but does not make it an approved
H-02 `repository.blueprint_id`.

## 6. Stable evidence, owner, blocker, and symbolic-input IDs

### 6.1 Evidence IDs

| ID | Exact authority |
| --- | --- |
| `E-CM` | `docs/chains/rh/component-matrix.md`, matching CM row |
| `E-T7` | `docs/chains/rh/robinhood-deployment-support-specification.md`, Sections 13, 15, and 18 H-03 |
| `E-VP` | `docs/chains/rh/robinhood-deployment-validation-plan.md`, NEG-016–025, NEG-031, NEG-033–037 |
| `E-H03` | controlling H-03 brief, topology and mandatory-unresolved sections |
| `E-H02` | integrated H-02 network-profile implementation and evidence frozen in Section 3.2 |
| `E-S1` | integrated S1 clock-profile harness and its checked profile authority |
| `E-S2` | integrated S2 checked block-clock inventory and enforcement tests |
| `E-M0` | integrated Track 8 M0 owner-decision packet, Sections 2–7.1 |
| `E-T8` | integrated Track 8 specification Sections 23.4, 23.6–23.9 and validation plan |
| `E-M1` | integrated Track 8 M1 exact-receipt brief and dated owner-decision provenance only; mutable or uncommitted M1 worktree evidence is explicitly excluded |
| `E-H04` | integrated H-04/S6 defaults/parameters brief, especially exact A4 lifecycle vocabulary and parameter ownership |
| `E-T1` | integrated Track 1 Chainlink/CCIP confirmation, decision, public-evidence, and question-packet authorities frozen in Section 3.2 |
| `E-S3` | integrated Lootbox-floor implementation record/source |
| `E-S4` | integrated no-code deleverage-cooldown decision |
| `E-S5` | current S5 guard brief and owner packet |
| `E-SRC` | exact repository source path at baseline; a record using this ID carries that path directly, while relation records carry any required line/range proof separately |
| `E-SRC-HQ` | `contracts/modules/Addys.vy:40-61`; `contracts/registries/RipeHq.vy:100-127`; `contracts/registries/RipeHq.vy:214-277`; `contracts/registries/RipeHq.vy:378-424`; `tests/conf_core.py:144-180`; `docs/chains/rh/robinhood-deployment-support-specification.md:1042`; `docs/chains/rh/robinhood-deployment-support-specification.md:1048`; `docs/chains/rh/robinhood-deployment-support-specification.md:1064`; `docs/chains/rh/robinhood-deployment-support-specification.md:1069`; `docs/chains/rh/robinhood-deployment-support-specification.md:1073-1074` |
| `E-SRC-REG` | `contracts/registries/modules/AddressRegistry.vy:120-139`; `contracts/registries/modules/AddressRegistry.vy:156-198` |
| `E-SRC-VB` | `contracts/core/Teller.vy:213-214`; `contracts/core/CreditEngine.vy:184`; `contracts/core/CreditRedeem.vy:110`; `contracts/vaults/modules/StabVault.vy:95`; `contracts/core/BondRoom.vy:102`; `contracts/core/HumanResources.vy:127`; `contracts/core/Lootbox.vy:192`; `migrations/base-mainnet/1008_VaultBook.py:38-54`; `tests/conf_core.py:658-675` |
| `E-SRC-PD` | `contracts/core/Teller.vy:215`; `contracts/core/CreditEngine.vy:185`; `contracts/core/Endaoment.vy:148`; `contracts/config/SwitchboardAlpha.vy:407`; `migrations/base-mainnet/1007_PriceDesk.py:41-42`; `migrations/base-mainnet/1007_PriceDesk.py:53-55`; `migrations/base-mainnet/1007_PriceDesk.py:70-71`; `migrations/base-mainnet/1007_PriceDesk.py:82-83`; `migrations/base-mainnet/1007_PriceDesk.py:94-95`; `tests/conf_core.py:753-786` |
| `E-SRC-SB` | `contracts/config/SwitchboardBravo.vy:184`; `migrations/base-mainnet/1006_Switchboard.py:27-64`; `migrations/base-mainnet/2025120200_New_Switchboards.py:71-72`; `tests/conf_core.py:484-505` |

Evidence IDs are exact immutable `ComponentRecord.controlling_evidence_ids`
tuple members. Every value must resolve to this Section 6.1 table; prose,
wildcards, undeclared aliases, and implied expansion are invalid. The tuple
binds each executable component row to the reviewed authority that controls
its disposition without copying narrative rationale into the module. H-09
must still review the blueprint and this evidence record together.
`D-H03-004-R6` approved this single, deterministic schema/evidence boundary at
the published hashes recorded above. `D-H03-005` and `D-H03-006` separately
approve the modeling semantics and launch order, and their representations
were included in that exact R6 package approval and integrated through
`8e4a965…`. None of those approvals extends automatically to the current
lifecycle/provenance candidate, downstream blocker closure, H-03 Phase B
exact-lock validation, implementation, or Phase B authorization.

### 6.2 Owner IDs

| ID | Accountable owner class |
| --- | --- |
| `OWN-H03` | H-03 blueprint/tooling owner and reviewers |
| `OWN-H04` | H-04/S6 defaults and parameter-manifest owners |
| `OWN-H05` | H-05 migration namespace/order/plan owner |
| `OWN-H08` | post-deployment topology/assertion owner |
| `OWN-H09` | clean-deployment and release-evidence owner |
| `OWN-T1` | Track 1 CCIP/toolchain owners |
| `OWN-T8` | Track 8 containment, vault, Stock route, and activation owners |
| `OWN-S5` | S5 Ledger source/implementation/proof owners |
| `OWN-ORACLE` | oracle/product-risk/security owners |
| `OWN-SECOPS` | security, governance, deployment, and operations owners |
| `OWN-REWARDS` | product/economics/tokenomics/rewards owners |

### 6.3 Blocker IDs

| Blocker | Primary owner | Co-owners | Deadline gate | Open gate and downstream effect |
| --- | --- | --- | --- | --- |
| `B-S5-LEDGER` | `OWN-S5` | `OWN-SECOPS` | before CM-008 enters an H-05 plan | Fresh Robinhood Ledger source/provider implementation and all S5 proof are absent; CM-008 is not deployable |
| `B-H04-PARAMS` | `OWN-H04` | `OWN-ORACLE`, `OWN-SECOPS` | before H-05 plan freeze | Defaults, cadence, timelock, fee, cap, reward, oracle, risk, TrainingWheels target, special-StabilityPool ID, and other concrete values are not H-03-owned |
| `B-H05-PLAN` | `OWN-H05` | `OWN-H04` | before any migration execution | No migration order, namespace execution plan, registry transaction, or manifest record is approved |
| `B-T8-M1` | `OWN-T8` | `OWN-SECOPS` | before Track 8 M4 composed proof | Exact Teller receipt boundary unimplemented and unauthorized |
| `B-T8-M2` | `OWN-T8` | `OWN-H05` | before Track 8 M5 activation | Guarded Stock vault source/artifact/ABI/runtime and registry placement unimplemented and unauthorized |
| `B-T8-M3` | `OWN-T8` | `OWN-SECOPS` | before Track 8 M4 composed proof | CreditEngine containment change unimplemented and unauthorized |
| `B-T8-M4` | `OWN-T8` | `OWN-H09` | before Track 8 M5 activation | Composed local/adversarial/exact-token proof absent |
| `B-T8-M5` | `OWN-T8` | `OWN-SECOPS`, `OWN-H09` | before Stock activation | Robinhood configuration, release evidence, deployment, and activation unapproved |
| `B-T8-FREEZE` | `OWN-T8` | `OWN-ORACLE`, `OWN-H04` | at final pre-activation freeze | Final AAPL identity revalidation, feed pin, exact cap integers, vault identity, and config hashes are post-M0 |
| `B-ORACLE-FREEZE` | `OWN-ORACLE` | `OWN-H04`, `OWN-H05` | before the oracle plan is frozen | Exact feed/runtime/decimals/heartbeat/failure evidence and LP oracle selection are not frozen for deployment |
| `B-LP-ARTIFACTS` | `OWN-H04` | `OWN-H05`, `OWN-ORACLE` | before the launch plan can close | Both launch LP artifacts, creation venue, runtime, and composed proof are absent |
| `B-PSM-SEQUENCE` | `OWN-H05` | `OWN-H04`, `OWN-T8`, `OWN-SECOPS` | before launch plan can close | `D-H03-006` fixes the sequence, but deployed PSM/runtime/config proof, governed auto-deposit-off action, redemption-first proof, final PSM capability-tuple mutation, complete re-verification, and final global-mint activation proof remain absent |
| `B-REWARD-PROMOTION` | `OWN-REWARDS` | `OWN-SECOPS` | at `within_seven_day_separately_reviewed_reward_activation` | Rewards are launch-disabled; later validation, monitoring, kill procedure, and owner approval are absent |
| `B-T1-CCIP` | `OWN-T1` | `OWN-SECOPS` | at `within_seven_day_separately_reviewed_ccip_promotion` | CCIP source/package/admin/remote/capability/promotion evidence remains separately owned |
| `B-T1-TOOLCHAIN` | `OWN-T1` | `OWN-SECOPS` | before any CCIP artifact is built | Canonical pinned Solidity toolchain remains unapproved |
| `B-H08-PROOF` | `OWN-H08` | `OWN-H09` | after approved deployment fixtures exist | Read-only deployed topology and negative-reachability proof does not yet exist |
| `B-H09-RELEASE` | `OWN-H09` | `OWN-SECOPS` | before testnet or production activation | Clean deployment, reproducibility, adversarial, Base regression, smoke/soak, and release proof do not yet exist |
| `B-SECOPS-HANDOFF` | `OWN-SECOPS` | `OWN-H05` | before testnet or production handoff | Exact public authorities, capability handoff, monitoring, and operational approvals are not frozen |

Closed blocker, recorded for provenance only: `B-H02-AUDIT` covered the former
parallel H-02 post-integration audit condition. It was closed by integrated
H-02 correction merge `cb3fe7392c44613aaeec49bd2486369fe0da3556`, as traced in
Section 2. The table above lists only open gates, so `B-H02-AUDIT` is
deliberately absent from it and from the Phase B `RobinhoodBlueprint.blockers`
tuple; it must not be reintroduced as a runtime `Blocker` record.

### 6.4 Historical R1 symbolic fields — superseded, non-normative

The following table is retained only as supersession history. It is not an
input to Phase B. Section 7A.1 replaces it with deterministic primary/co-owner
IDs, exact consumers, stable missing constructor/configuration fields, exact
deadline gates, and one status per input.

These are schema field IDs, not values. An input may be `required` even while
its concrete value is withheld until the listed deadline. The Section 7
`Deployment; symbolic inputs` cells are the sole consumer authority:
`SymbolicInput.consumers` is derived by inverting every exact `I-*` token in
those cells. This table does not independently declare consumer tuples.
Phase B tests must prove the inverse mapping is complete and bidirectionally
identical; a field absent from Section 7 or any extra/missing edge fails with
`H03_SYMBOLIC_FIELD`.

| Field ID | Semantic class | Owner; deadline | Current status/blocker |
| --- | --- | --- | --- |
| `I-GREEN` | GREEN deployment identity | H-05/SECOPS; before H-05 execution | required; `B-H05-PLAN`, `B-SECOPS-HANDOFF` |
| `I-RIPE` | RIPE deployment identity | H-05/SECOPS; before H-05 execution | required; same |
| `I-SGREEN` | chain-native sGREEN deployment identity | H-05; before H-05 execution | required; `B-H05-PLAN` |
| `I-GOV-HANDOFF` | public governance/capability handoff references, never a private account | SECOPS; before testnet/prod handoff | required; `B-SECOPS-HANDOFF` |
| `I-CLOCK-PARAMS` | registry/governance/config timing classes | H-04/S6; before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-TRAINING-WHEELS` | launch-control policy and public authority classes | H-04/SECOPS; before testnet | required; `B-H04-PARAMS`, `B-SECOPS-HANDOFF` |
| `I-LEDGER-BLOCK-SOURCE` | action-block provider/source/discriminator for fresh Ledger | S5; before the Ledger component can become required | blocked; `B-S5-LEDGER` |
| `I-RH-DEFAULTS` | DefaultsRobinhood artifact identity and complete typed manifest | H-04/S6; before H-05 | required; `B-H04-PARAMS` |
| `I-CHAINLINK-CORE` | Robinhood native/BTC sentinel metadata and adapter constructor classes | ORACLE/H-04; before oracle plan | required; `B-ORACLE-FREEZE` |
| `I-AAPL-TOKEN` | symbolic approved initial Stock identity | T8; revalidate at final freeze | required; `B-T8-FREEZE` |
| `I-AAPL-FEED` | symbolic approved AAPL/USD feed identity/provenance | T8/ORACLE; final freeze | required; `B-T8-FREEZE`, `B-ORACLE-FREEZE` |
| `I-AAPL-RISK` | one-vault, exposure, LTV, route, and review configuration fields | T8/H-04; before M5 | blocked; `B-H04-PARAMS`, `B-T8-FREEZE`, `B-T8-M5` |
| `I-STOCK-VAULT-ARTIFACT` | proposed isolated guarded vault source/artifact/runtime | T8; before M2/M5 | blocked; `B-T8-M2` |
| `I-STOCK-VAULT-SLOT` | approved VaultBook placement/name for the guarded artifact | T8/H-05; before M5 plan | blocked; `B-T8-M2`, `B-H05-PLAN` |
| `I-USDG` | symbolic canonical USDG identity | T8/H-05; before PSM/LP plan | required; `B-H05-PLAN` |
| `I-USDG-FEED` | symbolic approved USDG/USD feed identity/provenance | ORACLE; final freeze | required; `B-ORACLE-FREEZE` |
| `I-PSM-CONFIG` | reserve, interval, fee, cap, allowlist, and no-yield configuration classes | H-04/T8; before PSM staging | required; `B-H04-PARAMS`, `B-PSM-SEQUENCE` |
| `I-WETH` | symbolic Robinhood WETH constituent identity; no WETH feed or independent vault asset selected | H-04/H-05; before LP plan | required; `B-H05-PLAN` |
| `I-GREEN-USDG-LP` | LP artifact/runtime/oracle and ordinary deposit-only config | H-04/H-05/ORACLE; before launch plan | blocked; `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` |
| `I-RIPE-WETH-LP` | LP artifact/runtime/oracle and ordinary deposit-only config | H-04/H-05/ORACLE; before launch plan | blocked; same |
| `I-ASSET-CONFIG-NONSTOCK` | typed asset/vault/LTV/route settings for approved non-Stock launch assets | H-04/T8; before M5 | required; `B-H04-PARAMS` |
| `I-ASSET-CONFIG-STOCK` | typed asset/vault/LTV/route settings for the approved initial Stock asset | H-04/T8; before M5 | blocked; `B-H04-PARAMS`, `B-T8-M5` |
| `I-STABILITY-CONFIG` | GREEN Stability Pool launch config and Stock exclusions | H-04/T8; before M5 | required; `B-H04-PARAMS`, `B-T8-M5` |
| `I-RIPE-GOV-CONFIG` | RIPE governance-vault launch config | H-04; before H-05/M5 | required; `B-H04-PARAMS` |
| `I-AUCTION-CREDIT-NONSTOCK` | non-Stock auction and credit parameters | H-04/T8; before M5 | required; `B-H04-PARAMS` |
| `I-AUCTION-CREDIT-STOCK` | Stock containment settings for auction and credit | H-04/T8; before M5 | blocked; `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` |
| `I-LOOTBOX-CONFIG` | integrated S3 constructor/config fields without embedding values | H-04/S3 owner; before H-05 | required; `B-H04-PARAMS` |
| `I-REWARDS-PROMOTION` | later rewards config, validation, monitoring, and kill package | REWARDS/SECOPS; separately reviewed post-launch fast-follow promotion | deferred; `B-REWARD-PROMOTION` |
| `I-CCIP-ARTIFACTS` | GREEN/RIPE pool source/package/artifacts | T1; separate promotion | deferred; `B-T1-CCIP`, `B-T1-TOOLCHAIN` |
| `I-CCIP-REGISTRATION` | admin, remote, rate/capability, supply, and promotion evidence | T1/SECOPS; separate promotion | deferred; `B-T1-CCIP` |
| `I-MIGRATION-PLAN` | Robinhood namespace, exact order, receipts, and registry assertions | H-05; before any plan execution | blocked; `B-H05-PLAN` |
| `I-MANIFEST-HISTORY` | independent RH manifest/history schema and roots | H-05/H-09; before rehearsal | blocked; `B-H05-PLAN`, `B-H09-RELEASE` |
| `I-VERIFY-EXPORT` | ABI/export/verifier adapter and evidence policy | later Track 7 tooling; before verification | blocked; `B-H09-RELEASE`; CCIP portion also `B-T1-TOOLCHAIN` |
| `I-RELEASE-PROOF` | H-08/H-09 topology, clean deployment, adversarial, Base regression, and release evidence | H-08/H-09; before testnet/prod | blocked; `B-H08-PROOF`, `B-H09-RELEASE` |

### 6.5 Historical R1 surface inventory — superseded, non-normative

The 112-record table below is retained only to show what R2 replaced. It is not
canonical, must not be encoded in Phase B, and must not be used for counts or
validation. Section 7A.2 is the sole current surface authority.

`SurfaceKind` is closed: `artifact`, `capability`, `route`, `permission`,
`configuration`, `registration`. Every disabled or blocked capability of a
required component is an explicit record below, never prose alone. The set is
canonical and complete: exactly 112 records across all 60 components,
each with a stable unique `surface_id`, one exact disposition, its exact
blockers, and its exact negative assertions. Deleting a whole record is a
failure even when every remaining record is internally valid.

Counts by kind: `artifact` 23, `capability` 12, `configuration` 13, `permission` 4, `registration` 7, `route` 53.
Counts by disposition: `blocked` 19, `deferred` 7, `disabled` 29, `omitted` 48, `required` 9.

| Surface ID | Component | Kind | Disposition | Blockers | Negative assertions | Exact surface |
| --- | --- | --- | --- | --- | --- | --- |
| `S-001-CCIP-POOL` | CM-001 | `artifact` | `deferred` | `B-T1-CCIP` | NEG-025 | GREEN CCIP BurnMint pool artifact |
| `S-001-CCIP-CAP` | CM-001 | `capability` | `disabled` | `B-T1-CCIP` | NEG-025 | GREEN pool/direct mint-burn capability |
| `S-001-MINT-HANDOFF` | CM-001 | `capability` | `blocked` | `B-SECOPS-HANDOFF` | NEG-017, NEG-031 | GREEN mint capability handoff |
| `S-002-CCIP-POOL` | CM-002 | `artifact` | `deferred` | `B-T1-CCIP` | NEG-025 | RIPE CCIP BurnMint pool artifact |
| `S-002-CCIP-CAP` | CM-002 | `capability` | `disabled` | `B-T1-CCIP` | NEG-025 | RIPE pool/direct mint-burn capability |
| `S-002-MINT-HANDOFF` | CM-002 | `capability` | `blocked` | `B-SECOPS-HANDOFF` | NEG-017, NEG-031 | RIPE mint capability handoff |
| `S-003-DEPOSIT` | CM-003 | `route` | `required` | none | NEG-033 | chain-native sGREEN deposit |
| `S-003-WITHDRAW` | CM-003 | `route` | `required` | none | NEG-033 | chain-native sGREEN withdrawal |
| `S-003-CCIP` | CM-003 | `capability` | `omitted` | none | NEG-033 | sGREEN CCIP enablement, permanently excluded |
| `S-003-REWARDS` | CM-003 | `route` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | sGREEN launch reward accrual |
| `S-004-CAP-PREHANDOFF` | CM-004 | `permission` | `blocked` | `B-SECOPS-HANDOFF` | NEG-017, NEG-031 | any HQ capability before exact handoff |
| `S-004-SPARSE-ID` | CM-004 | `registration` | `omitted` | none | NEG-031, NEG-036 | placeholder or sparse-ID registration |
| `S-006-ALLOWLIST` | CM-006 | `configuration` | `blocked` | `B-H04-PARAMS`, `B-SECOPS-HANDOFF` | NEG-017 | TrainingWheels allowlist entries |
| `S-008-RH-ARTIFACT` | CM-008 | `artifact` | `blocked` | `B-S5-LEDGER` | NEG-017, NEG-031 | fresh Robinhood Ledger deployable source |
| `S-008-PROVIDER-FALLBACK` | CM-008 | `route` | `omitted` | `B-S5-LEDGER` | NEG-017 | action-block provider fallback |
| `S-008-BASE-MIGRATION` | CM-008 | `route` | `omitted` | none | NEG-016 | Base Ledger state migration |
| `S-009-VALUES` | CM-009 | `configuration` | `blocked` | `B-H04-PARAMS` | NEG-017 | all production configuration values |
| `S-009-UNSUPPORTED-ASSET` | CM-009 | `route` | `disabled` | `B-T8-M5` | NEG-021, NEG-024 | unsupported asset and route flags |
| `S-010-UNREVIEWED-CHILD` | CM-010 | `registration` | `omitted` | none | NEG-031, NEG-036 | unreviewed Switchboard child registration |
| `S-011-ORACLE-ACTIONS` | CM-011 | `route` | `disabled` | `B-ORACLE-FREEZE` | NEG-024, NEG-037 | unsupported oracle configuration actions |
| `S-011-UNDERSCORE` | CM-011 | `route` | `omitted` | none | NEG-016, NEG-024 | Underscore configuration actions |
| `S-012-AUCTION-VALUES` | CM-012 | `configuration` | `blocked` | `B-H04-PARAMS` | NEG-017 | auction parameter values |
| `S-013-REWARD-ACTIONS` | CM-013 | `route` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | launch reward, points, and emission actions |
| `S-014-COOLDOWN` | CM-014 | `configuration` | `required` | none | NEG-036 | named zero-cooldown deleverage posture (S4) |
| `S-014-INERT-ACTIONS` | CM-014 | `route` | `disabled` | `B-H04-PARAMS` | NEG-034, NEG-035, NEG-036 | HR, bond, and Lootbox unapproved actions |
| `S-015-RESERVED-SLOTS` | CM-015 | `registration` | `omitted` | none | NEG-024, NEG-037 | PriceDesk reserved slots 2-5 remain empty |
| `S-016-FEED-REG` | CM-016 | `registration` | `blocked` | `B-ORACLE-FREEZE` | NEG-024, NEG-037 | feed registration before exact freeze |
| `S-016-SOURCE-FALLBACK` | CM-016 | `route` | `omitted` | none | NEG-024 | unsupported price-source fallback |
| `S-016-WETH-FEED` | CM-016 | `registration` | `omitted` | `B-ORACLE-FREEZE` | NEG-024 | WETH feed; M0 selects none |
| `S-017-ARTIFACT` | CM-017 | `artifact` | `omitted` | none | NEG-016, NEG-024, NEG-037 | CurvePrices artifact and PD row |
| `S-017-BASERATE` | CM-017 | `route` | `required` | none | NEG-024 | CreditEngine named base-rate fallback when Curve is absent |
| `S-018-ARTIFACT` | CM-018 | `artifact` | `omitted` | none | NEG-016, NEG-024, NEG-037 | BlueChipYieldPrices artifact and PD row |
| `S-019-ARTIFACT` | CM-019 | `artifact` | `omitted` | none | NEG-016, NEG-024, NEG-037 | PythPrices artifact and PD row |
| `S-020-ARTIFACT` | CM-020 | `artifact` | `omitted` | none | NEG-016, NEG-024, NEG-037 | StorkPrices artifact and PD row |
| `S-021-STOCK-SLOT` | CM-021 | `registration` | `blocked` | `B-T8-M2`, `B-H05-PLAN` | NEG-021, NEG-031 | guarded Stock vault VaultBook placement |
| `S-022-GREEN` | CM-022 | `route` | `required` | none | NEG-033 | GREEN Stability Pool launch path |
| `S-022-STOCK-CUSTODY` | CM-022 | `route` | `disabled` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021, NEG-023 | Stock custody in the Stability Pool |
| `S-022-STOCK-SWAP` | CM-022 | `route` | `disabled` | `B-T8-M5` | NEG-023 | Stock swap in the Stability Pool |
| `S-022-REWARDS` | CM-022 | `route` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | Stability Pool launch reward routes |
| `S-023-GOV-DEPOSIT` | CM-023 | `route` | `required` | none | NEG-036 | RIPE governance deposit path |
| `S-023-REWARDS` | CM-023 | `route` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | governance-vault launch rewards |
| `S-024-LP-DEPOSIT` | CM-024 | `route` | `required` | `B-LP-ARTIFACTS` | NEG-022 | ordinary LP deposit-only routes with named zero LTV |
| `S-024-LP-BORROW` | CM-024 | `route` | `omitted` | none | NEG-022 | LP borrowing power; `ltv=0` |
| `S-024-STOCK-USE` | CM-024 | `route` | `blocked` | `B-T8-M2`, `B-T8-M5` | NEG-021 | AAPL/Stock use of the ordinary vault |
| `S-025-ARTIFACT` | CM-025 | `artifact` | `omitted` | none | NEG-016, NEG-021, NEG-031 | Rebase vault artifact, row, and route |
| `S-025-WRAPPER` | CM-025 | `configuration` | `omitted` | none | NEG-021 | positive-delta wrapper change |
| `S-026-AAPL-SETTLE` | CM-026 | `route` | `blocked` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021, NEG-023 | AAPL auction settlement |
| `S-026-STOCK-ROUTES` | CM-026 | `route` | `omitted` | none | NEG-021 | unsupported Stock auction routes |
| `S-027-INDEP-CAP` | CM-027 | `capability` | `omitted` | none | NEG-031 | independent unapproved NFT capability |
| `S-028-REWARD-PATH` | CM-028 | `route` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | Boardroom reward and allocation paths |
| `S-029-BONDS` | CM-029 | `route` | `disabled` | `B-H04-PARAMS` | NEG-034, NEG-035 | bond purchase, terms, and payment routes |
| `S-029-RIPE-CAP` | CM-029 | `capability` | `disabled` | `B-SECOPS-HANDOFF` | NEG-035, NEG-036 | BondRoom RIPE mint capability |
| `S-030-AAPL-BORROW` | CM-030 | `route` | `blocked` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021 | AAPL-backed borrowing |
| `S-030-STOCK-DEFICIT` | CM-030 | `route` | `disabled` | `B-T8-M3` | NEG-021, NEG-023 | Stock deficit/containment routes |
| `S-030-ORACLE-FALLBACK` | CM-030 | `route` | `omitted` | none | NEG-024 | unsupported oracle fallback |
| `S-031-CURVE` | CM-031 | `route` | `omitted` | none | NEG-016, NEG-024 | Endaoment Curve route |
| `S-031-BASE-DEX` | CM-031 | `route` | `omitted` | none | NEG-016, NEG-020 | Base DEX and partner routes |
| `S-031-YIELD` | CM-031 | `route` | `disabled` | `B-H04-PARAMS` | NEG-020 | Endaoment yield positions |
| `S-031-UNDERSCORE` | CM-031 | `route` | `omitted` | none | NEG-016, NEG-036 | Endaoment Underscore route |
| `S-031-STOCK` | CM-031 | `route` | `omitted` | none | NEG-021 | Endaoment Stock destination |
| `S-032-TEMPLATE` | CM-032 | `configuration` | `omitted` | none | NEG-034 | HR contributor template |
| `S-032-VESTING` | CM-032 | `route` | `omitted` | none | NEG-034 | HR vesting and payout routes |
| `S-032-RIPE-CAP` | CM-032 | `capability` | `disabled` | `B-SECOPS-HANDOFF` | NEG-034, NEG-036 | HumanResources RIPE mint capability |
| `S-033-REWARD-MINT` | CM-033 | `capability` | `disabled` | `B-REWARD-PROMOTION` | NEG-035, NEG-036 | Lootbox reward mint and points |
| `S-033-UNDERSCORE` | CM-033 | `route` | `omitted` | none | NEG-016, NEG-036 | Lootbox Underscore paths |
| `S-033-STOCK-REWARD` | CM-033 | `route` | `omitted` | none | NEG-021, NEG-035 | Stock reward accrual |
| `S-034-USDG-COLLATERAL` | CM-034 | `route` | `omitted` | none | NEG-017 | USDG as ordinary Teller collateral |
| `S-034-AAPL-TRUSTED` | CM-034 | `route` | `disabled` | `B-T8-M5` | NEG-021 | AAPL trusted deposit route |
| `S-034-AAPL-DEPT` | CM-034 | `route` | `disabled` | `B-T8-M5` | NEG-021 | AAPL Department bypass route |
| `S-034-EXACT-RECEIPT` | CM-034 | `configuration` | `blocked` | `B-T8-M1` | NEG-021 | Teller exact-receipt boundary change |
| `S-034-SGREEN-ROUTE` | CM-034 | `route` | `required` | none | NEG-033 | Teller-held sGREEN route |
| `S-038-BOOSTER-CFG` | CM-038 | `configuration` | `disabled` | `B-H04-PARAMS` | NEG-035 | bond booster configuration and user units |
| `S-043-STOCK-REDEEM` | CM-043 | `route` | `disabled` | `B-T8-M5` | NEG-022 | Stock `canRedeemCollateral`, named false |
| `S-043-UNDERSCORE` | CM-043 | `route` | `omitted` | none | NEG-016, NEG-036 | CreditRedeem Underscore route |
| `S-044-COOLDOWN` | CM-044 | `configuration` | `required` | none | NEG-036 | named zero-cooldown posture, unchanged (S4) |
| `S-044-UNDERSCORE` | CM-044 | `route` | `omitted` | none | NEG-016, NEG-036 | Deleverage Underscore path |
| `S-045-UNDERSCORE` | CM-045 | `route` | `omitted` | none | NEG-016, NEG-036 | TellerUtils Underscore getters fail closed |
| `S-046-PSM-ACTIVATION` | CM-046 | `permission` | `blocked` | `B-PSM-SEQUENCE` | NEG-018, NEG-019 | PSM activation authority; presence grants none |
| `S-046-ENDAOMENT-ACTIONS` | CM-046 | `route` | `disabled` | `B-H04-PARAMS` | NEG-020 | unsupported Endaoment/yield actions |
| `S-047-EXTERNAL` | CM-047 | `route` | `omitted` | none | NEG-016, NEG-020 | Base external, yield, and partner destinations |
| `S-047-STOCK` | CM-047 | `route` | `omitted` | none | NEG-021 | Stock destination |
| `S-048-MINT` | CM-048 | `capability` | `disabled` | `B-PSM-SEQUENCE` | NEG-018 | PSM `canMint`, false at construction |
| `S-048-REDEEM` | CM-048 | `capability` | `disabled` | `B-PSM-SEQUENCE` | NEG-019 | PSM `canRedeem`, false at construction |
| `S-048-HQ-GREEN-CAP` | CM-048 | `capability` | `disabled` | `B-PSM-SEQUENCE`, `B-SECOPS-HANDOFF` | NEG-018 | RipeHq GREEN mint capability, granted last |
| `S-048-AUTO-DEPOSIT` | CM-048 | `configuration` | `disabled` | `B-H04-PARAMS` | NEG-020 | auto-deposit default |
| `S-048-YIELD` | CM-048 | `route` | `disabled` | `B-H04-PARAMS` | NEG-020 | optional yield position |
| `S-048-APPROVAL` | CM-048 | `permission` | `disabled` | `B-H04-PARAMS` | NEG-020 | external approval surface |
| `S-048-UNDERSCORE` | CM-048 | `route` | `omitted` | none | NEG-016, NEG-020 | Underscore bypass |
| `S-048-TELLER-ROUTE` | CM-048 | `route` | `omitted` | none | NEG-017 | generic Teller collateral/asset route |
| `S-048-ACTIVATION` | CM-048 | `permission` | `blocked` | `B-PSM-SEQUENCE` | NEG-018, NEG-019 | launch activation, redemption-first then mint-last |
| `S-049-FALLBACK` | CM-049 | `configuration` | `omitted` | none | NEG-017 | Base/local address or value fallback |
| `S-049-ARTIFACT` | CM-049 | `artifact` | `blocked` | `B-H04-PARAMS` | NEG-017 | DefaultsRobinhood artifact; not created by H-03 |
| `S-051-ARTIFACT` | CM-051 | `artifact` | `deferred` | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | NEG-025 | GREEN CCIP pool artifact and HQ row |
| `S-052-ARTIFACT` | CM-052 | `artifact` | `deferred` | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | NEG-025 | RIPE CCIP pool artifact and HQ row |
| `S-053-REGISTRATION` | CM-053 | `registration` | `deferred` | `B-T1-CCIP` | NEG-025 | CCIP token-admin registration and remote config |
| `S-055-EXECUTION` | CM-055 | `route` | `omitted` | none | NEG-017 | execution, address, or default logic inside H-03 |
| `S-056-MANIFEST` | CM-056 | `artifact` | `blocked` | `B-H05-PLAN`, `B-H09-RELEASE` | NEG-016 | Robinhood manifest and history artifacts |
| `S-057-VERIFY` | CM-057 | `route` | `blocked` | `B-H09-RELEASE` | NEG-016 | RH ABI export and explorer verification |
| `S-058-TOOLCHAIN` | CM-058 | `artifact` | `deferred` | `B-T1-TOOLCHAIN` | NEG-025 | pinned Solidity build/test/deploy toolchain |
| `S-059-DEPLOY-TIER` | CM-059 | `route` | `blocked` | `B-H08-PROOF`, `B-H09-RELEASE` | NEG-016 | deployment, fork, and release test tiers |
| `S-060-RH-USE` | CM-060 | `configuration` | `omitted` | none | NEG-016, NEG-017 | DefaultsLocal use by the Robinhood graph |
| `S-035-POOL` | CM-035 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Base GREEN Curve pool address and route |
| `S-036-POOL` | CM-036 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Base RIPE Curve pool address and route |
| `S-037-POOL` | CM-037 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Base RIPE Aerodrome pool address and route |
| `S-039-FEED` | CM-039 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Base yield asset source and feed |
| `S-040-FEED` | CM-040 | `artifact` | `omitted` | none | NEG-016, NEG-024 | RedStone adapter and feed |
| `S-041-FEED` | CM-041 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Underscore vault price adapter |
| `S-042-VAULT` | CM-042 | `artifact` | `omitted` | none | NEG-016, NEG-021, NEG-024 | Underscore vault, wallet, and every route |
| `S-050-FEED` | CM-050 | `artifact` | `omitted` | none | NEG-016, NEG-024 | Aerodrome RIPE adapter and feed |
| `S-054-ADAPTER` | CM-054 | `artifact` | `deferred` | `B-ORACLE-FREEZE` | NEG-016, NEG-024 | GREEN/RIPE local price adapter and slot |
| `S-005-CONTRIBUTOR` | CM-005 | `artifact` | `omitted` | none | NEG-016, NEG-034 | Contributor instance, template, vesting, payout |
| `S-007-RH-USE` | CM-007 | `configuration` | `omitted` | none | NEG-016, NEG-017 | DefaultsBase use by the Robinhood graph |

### 6.6 Historical R1 component relations — superseded, non-normative

The 135-edge table below is retained only as supersession history. It neither
claims completeness nor authorizes an edge. Section 7A.3 is the sole current
relation graph and applies the narrower deployment/security inclusion rule
with approved `D-H03-005` typing.

`RelationPhase` is closed: `constructor`, `bootstrap`, `post_deployment_setup`,
`registration_order`, `runtime`. Every target is an exact declared CM ID. No
workflow or slice identifier and no prose target appears. The set is canonical
and complete: exactly 135 edges, no duplicates and no self-edges.

Counts by phase: `bootstrap` 3, `constructor` 35, `post_deployment_setup` 6, `registration_order` 33, `runtime` 58.
Components appearing as a relation source: 42. The
remaining components are omitted, external, or pending and correctly hold zero
relations; their replacement and future-release facts live in their
dispositions, blockers, downstream ownership, and negative assertions.

This is not an executable deployment order and not a claim of acyclicity.
CM-004 holds `constructor` edges to CM-001/002/003 while those three hold
`bootstrap` and `post_deployment_setup` edges back to CM-004. H-05 owns the
executable sequence.

| Source | Phase | Target | Exact basis |
| --- | --- | --- | --- |
| CM-004 | `constructor` | CM-001 | `RipeHq.__init__` takes `_greenToken` and registers it as ID 1 |
| CM-004 | `constructor` | CM-003 | `RipeHq.__init__` takes `_savingsGreen` and registers it as ID 2 |
| CM-004 | `constructor` | CM-002 | `RipeHq.__init__` takes `_ripeToken` and registers it as ID 3 |
| CM-001 | `bootstrap` | CM-004 | `Erc20Token.__init__` asserts `_ripeHq == empty(address)` when initial gov is set; hq is assigned later |
| CM-002 | `bootstrap` | CM-004 | same bootstrap rule as CM-001 |
| CM-003 | `bootstrap` | CM-004 | `Erc4626Token` follows the same deferred-hq bootstrap |
| CM-001 | `post_deployment_setup` | CM-004 | hq reference set through the governance path (`contracts/tokens/modules/Erc20Token.vy:441-473`) |
| CM-002 | `post_deployment_setup` | CM-004 | hq reference set through the governance path |
| CM-003 | `post_deployment_setup` | CM-004 | hq reference set through the governance path |
| CM-006 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-008 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-009 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-010 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-015 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-021 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-022 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-023 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-024 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-026 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-027 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-028 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-029 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-030 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-031 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-032 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-033 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-034 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-043 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-044 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-045 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-047 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-048 | `constructor` | CM-004 | department/registry constructor takes `_ripeHq` |
| CM-011 | `constructor` | CM-004 | Switchboard child constructor takes `_ripeHq` |
| CM-012 | `constructor` | CM-004 | Switchboard child constructor takes `_ripeHq` |
| CM-013 | `constructor` | CM-004 | Switchboard child constructor takes `_ripeHq` |
| CM-014 | `constructor` | CM-004 | Switchboard child constructor takes `_ripeHq` |
| CM-046 | `constructor` | CM-004 | Switchboard child constructor takes `_ripeHq` |
| CM-009 | `constructor` | CM-049 | `MissionControl.__init__(_ripeHq, _defaults)` takes the chain defaults artifact |
| CM-029 | `constructor` | CM-038 | `BondRoom.__init__(_ripeHq, _bondBooster)` takes the booster |
| CM-001 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-002 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-003 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-008 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-009 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-010 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-015 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-021 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-026 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-027 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-028 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-029 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-030 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-031 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-032 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-033 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-034 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-043 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-044 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-045 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-047 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-048 | `registration_order` | CM-004 | sequential RipeHq `AddressRegistry` row |
| CM-022 | `registration_order` | CM-021 | sequential VaultBook row |
| CM-023 | `registration_order` | CM-021 | sequential VaultBook row |
| CM-024 | `registration_order` | CM-021 | sequential VaultBook row |
| CM-016 | `registration_order` | CM-015 | sequential PriceDesk row (Chainlink at ID 1) |
| CM-011 | `registration_order` | CM-010 | sequential Switchboard row |
| CM-012 | `registration_order` | CM-010 | sequential Switchboard row |
| CM-013 | `registration_order` | CM-010 | sequential Switchboard row |
| CM-014 | `registration_order` | CM-010 | sequential Switchboard row |
| CM-046 | `registration_order` | CM-010 | sequential Switchboard row |
| CM-009 | `post_deployment_setup` | CM-008 | Ledger must exist before Mission Control configuration is meaningful |
| CM-049 | `post_deployment_setup` | CM-009 | defaults artifact supplies Mission Control's initial typed values |
| CM-006 | `post_deployment_setup` | CM-049 | launch-control policy classes are sourced from the chain defaults artifact |
| CM-034 | `runtime` | CM-021 | Teller routes deposits through VaultBook |
| CM-034 | `runtime` | CM-022 | Teller reaches Stability Pool via `STABILITY_POOL_ID = 1` |
| CM-034 | `runtime` | CM-023 | Teller reaches Ripe Gov Vault via `RIPE_GOV_VAULT_ID = 2` |
| CM-034 | `runtime` | CM-024 | Teller routes approved ordinary deposit assets to the Simple ERC20 vault |
| CM-034 | `runtime` | CM-008 | Teller writes user/action state through Ledger |
| CM-030 | `runtime` | CM-008 | CreditEngine reads and writes debt state through Ledger |
| CM-030 | `runtime` | CM-021 | CreditEngine resolves vaults through VaultBook |
| CM-030 | `runtime` | CM-022 | CreditEngine reaches Stability Pool via `STABILITY_POOL_ID = 1` |
| CM-030 | `runtime` | CM-026 | CreditEngine hands liquidations to Auction House |
| CM-030 | `runtime` | CM-017 | CreditEngine dynamic-rate path reads `CURVE_PRICES_ID = 2`; empty address returns the named base rate |
| CM-026 | `runtime` | CM-021 | Auction House settles against vault balances through VaultBook |
| CM-026 | `runtime` | CM-027 | Auction House uses the NFT artifact for auction positions |
| CM-043 | `runtime` | CM-021 | CreditRedeem resolves collateral through VaultBook |
| CM-043 | `runtime` | CM-022 | CreditRedeem reaches Stability Pool via `STABILITY_POOL_ID = 1` |
| CM-043 | `runtime` | CM-030 | CreditRedeem settles debt through CreditEngine |
| CM-044 | `runtime` | CM-021 | Deleverage resolves vaults through VaultBook |
| CM-044 | `runtime` | CM-030 | Deleverage settles debt through CreditEngine |
| CM-045 | `runtime` | CM-021 | TellerUtils reads vault state through VaultBook |
| CM-045 | `runtime` | CM-009 | TellerUtils reads configuration through Mission Control |
| CM-011 | `runtime` | CM-015 | SwitchboardAlpha reaches Price Desk via `PRICE_DESK_ID = 7` |
| CM-011 | `runtime` | CM-019 | SwitchboardAlpha addresses Pyth via `PYTH_PRICES_ID = 4`; slot stays empty for RH |
| CM-011 | `runtime` | CM-021 | SwitchboardAlpha configures vault settings through VaultBook |
| CM-012 | `runtime` | CM-026 | SwitchboardBravo governs auction parameters |
| CM-013 | `runtime` | CM-028 | SwitchboardCharlie governs Boardroom allocation surfaces |
| CM-013 | `runtime` | CM-033 | SwitchboardCharlie governs Lootbox reward surfaces |
| CM-014 | `runtime` | CM-029 | SwitchboardDelta governs bond surfaces |
| CM-014 | `runtime` | CM-032 | SwitchboardDelta governs HR surfaces |
| CM-014 | `runtime` | CM-033 | SwitchboardDelta governs Lootbox surfaces |
| CM-014 | `runtime` | CM-044 | SwitchboardDelta governs the deleverage cooldown (S4 zero-cooldown posture) |
| CM-046 | `runtime` | CM-048 | SwitchboardEcho is the governance surface for Endaoment PSM |
| CM-046 | `runtime` | CM-031 | SwitchboardEcho governs Endaoment surfaces |
| CM-016 | `runtime` | CM-015 | ChainlinkPrices is reached only through Price Desk |
| CM-015 | `runtime` | CM-016 | Price Desk resolves approved prices through the Chainlink source |
| CM-022 | `runtime` | CM-003 | Stability Pool values and holds sGREEN (`StabVault` `savingsGreen` reads) |
| CM-022 | `runtime` | CM-001 | Stability Pool operates on GREEN at launch |
| CM-023 | `runtime` | CM-002 | Ripe Gov Vault holds RIPE governance deposits |
| CM-033 | `runtime` | CM-023 | Lootbox reaches Ripe Gov Vault via `RIPE_GOV_VAULT_ID = 2` |
| CM-033 | `runtime` | CM-009 | Lootbox reads reward configuration through Mission Control |
| CM-029 | `runtime` | CM-023 | BondRoom reaches Ripe Gov Vault via `RIPE_GOV_VAULT_ID = 2` |
| CM-032 | `runtime` | CM-023 | HumanResources reaches Ripe Gov Vault via `RIPE_GOV_VAULT_ID = 2` |
| CM-032 | `runtime` | CM-009 | HumanResources reads configuration through Mission Control |
| CM-048 | `runtime` | CM-001 | PSM mints GREEN once its capability is granted |
| CM-048 | `runtime` | CM-003 | PSM exposes an sGREEN receipt option (`_wantsSavingsGreen`) |
| CM-048 | `runtime` | CM-016 | PSM depends on the approved USDG/USD feed through the Chainlink source |
| CM-048 | `runtime` | CM-031 | PSM operates within the Endaoment reserve boundary |
| CM-048 | `runtime` | CM-047 | PSM settles through Endaoment Funds |
| CM-031 | `runtime` | CM-015 | Endaoment values reserves through Price Desk |
| CM-031 | `runtime` | CM-047 | Endaoment moves funds through Endaoment Funds |
| CM-047 | `runtime` | CM-031 | Endaoment Funds acts for the Endaoment |
| CM-009 | `runtime` | CM-008 | Mission Control configuration is read alongside Ledger state |
| CM-024 | `runtime` | CM-021 | Simple ERC20 vault is reached through VaultBook |
| CM-025 | `runtime` | CM-021 | Rebase vault semantic slot is reserved in VaultBook; omitted for RH |
| CM-055 | `runtime` | CM-004 | deployment tooling targets the RipeHq topology it must not invent |
| CM-057 | `runtime` | CM-004 | ABI/export tooling exports the deployed topology artifacts |
| CM-059 | `runtime` | CM-004 | test profiles assert the deployed topology |
| CM-051 | `constructor` | CM-001 | GREEN CCIP pool would take the GREEN token address |
| CM-052 | `constructor` | CM-002 | RIPE CCIP pool would take the RIPE token address |
| CM-051 | `registration_order` | CM-004 | provisional HQ/23 semantic reservation only |
| CM-052 | `registration_order` | CM-004 | provisional HQ/24 semantic reservation only |
| CM-053 | `runtime` | CM-051 | token-admin registration acts on the GREEN pool |
| CM-053 | `runtime` | CM-052 | token-admin registration acts on the RIPE pool |
| CM-054 | `runtime` | CM-015 | any future local price adapter would be reached through Price Desk |

### 6.7 Historical R1 source crosswalk — superseded, non-normative

The component-wide table below is retained to show the R1 input to correction.
Its single state/class per component, undefined shorthand evidence references,
and incomplete tooling paths are not Phase B authority. Section 7A.4 is the
sole current per-path authority.

`SourceClass` is closed: `shared_contract`, `chain_specific_config`,
`external_integration`, `non_onchain_tooling`, `external_artifact`.
`SourcePathState` is closed: `existing`, `reviewed_planned`,
`external_pending`. All 60 rows are resolved here in Phase A; none is deferred
to Phase B. Broad globs are invalid. No row required a guess.

Counts by class: `chain_specific_config` 3, `external_artifact` 3, `external_integration` 5, `non_onchain_tooling` 4, `shared_contract` 45.
Counts by path state: `existing` 49, `external_pending` 10, `reviewed_planned` 1.

Resolved ambiguities: CM-049 uses the exact reviewed future path
`contracts/config/DefaultsRobinhood.vy` fixed by the integrated H-04/S6 brief
and is typed `reviewed_planned`; the file does not exist at this baseline and
this record does not claim it does. CM-051/052/058 are `external_pending` with
no fabricated package, path, or version. CM-008 cites the existing shared
`contracts/data/Ledger.vy` while its fresh Robinhood source remains blocked by
`B-S5-LEDGER`. CM-056 is `external_pending` because no Robinhood manifest or
history path is approved. CM-059 lists the seven exact integrated H-02/S1/S2
test files rather than a `tests/**` glob.

| CM | Source class | Path state | Exact repository-relative paths | Controlling authority |
| --- | --- | --- | --- | --- |
| CM-001 | `shared_contract` | `existing` | `contracts/tokens/GreenToken.vy`<br>`contracts/tokens/modules/Erc20Token.vy` | `E-SRC` repository source at baseline |
| CM-002 | `shared_contract` | `existing` | `contracts/tokens/RipeToken.vy`<br>`contracts/tokens/modules/Erc20Token.vy` | `E-SRC` repository source at baseline |
| CM-003 | `shared_contract` | `existing` | `contracts/tokens/SavingsGreen.vy`<br>`contracts/tokens/modules/Erc4626Token.vy` | `E-SRC` repository source at baseline |
| CM-004 | `shared_contract` | `existing` | `contracts/registries/RipeHq.vy`<br>`contracts/registries/modules/AddressRegistry.vy` | `E-SRC` repository source at baseline |
| CM-005 | `shared_contract` | `existing` | `contracts/modules/Contributor.vy` | `E-SRC` repository source at baseline |
| CM-006 | `shared_contract` | `existing` | `contracts/config/TrainingWheels.vy` | `E-SRC` repository source at baseline |
| CM-007 | `chain_specific_config` | `existing` | `contracts/config/DefaultsBase.vy` | `E-SRC` repository source at baseline |
| CM-008 | `shared_contract` | `existing` | `contracts/data/Ledger.vy` | `E-SRC` repository source at baseline; fresh RH source blocked by `B-S5-LEDGER` |
| CM-009 | `shared_contract` | `existing` | `contracts/data/MissionControl.vy` | `E-SRC` repository source at baseline |
| CM-010 | `shared_contract` | `existing` | `contracts/registries/Switchboard.vy` | `E-SRC` repository source at baseline |
| CM-011 | `shared_contract` | `existing` | `contracts/config/SwitchboardAlpha.vy` | `E-SRC` repository source at baseline |
| CM-012 | `shared_contract` | `existing` | `contracts/config/SwitchboardBravo.vy` | `E-SRC` repository source at baseline |
| CM-013 | `shared_contract` | `existing` | `contracts/config/SwitchboardCharlie.vy` | `E-SRC` repository source at baseline |
| CM-014 | `shared_contract` | `existing` | `contracts/config/SwitchboardDelta.vy` | `E-SRC` repository source at baseline |
| CM-015 | `shared_contract` | `existing` | `contracts/registries/PriceDesk.vy` | `E-SRC` repository source at baseline |
| CM-016 | `shared_contract` | `existing` | `contracts/priceSources/ChainlinkPrices.vy`<br>`contracts/priceSources/modules/PriceSourceData.vy` | `E-SRC` repository source at baseline |
| CM-017 | `shared_contract` | `existing` | `contracts/priceSources/CurvePrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-018 | `shared_contract` | `existing` | `contracts/priceSources/BlueChipYieldPrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-019 | `shared_contract` | `existing` | `contracts/priceSources/PythPrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-020 | `shared_contract` | `existing` | `contracts/priceSources/StorkPrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-021 | `shared_contract` | `existing` | `contracts/registries/VaultBook.vy` | `E-SRC` repository source at baseline |
| CM-022 | `shared_contract` | `existing` | `contracts/vaults/StabilityPool.vy`<br>`contracts/vaults/modules/StabVault.vy` | `E-SRC` repository source at baseline |
| CM-023 | `shared_contract` | `existing` | `contracts/vaults/RipeGov.vy` | `E-SRC` repository source at baseline |
| CM-024 | `shared_contract` | `existing` | `contracts/vaults/SimpleErc20.vy`<br>`contracts/vaults/modules/BasicVault.vy` | `E-SRC` repository source at baseline |
| CM-025 | `shared_contract` | `existing` | `contracts/vaults/RebaseErc20.vy`<br>`contracts/vaults/modules/SharesVault.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-026 | `shared_contract` | `existing` | `contracts/core/AuctionHouse.vy` | `E-SRC` repository source at baseline |
| CM-027 | `shared_contract` | `existing` | `contracts/core/AuctionHouseNFT.vy` | `E-SRC` repository source at baseline |
| CM-028 | `shared_contract` | `existing` | `contracts/core/Boardroom.vy` | `E-SRC` repository source at baseline |
| CM-029 | `shared_contract` | `existing` | `contracts/core/BondRoom.vy` | `E-SRC` repository source at baseline |
| CM-030 | `shared_contract` | `existing` | `contracts/core/CreditEngine.vy` | `E-SRC` repository source at baseline |
| CM-031 | `shared_contract` | `existing` | `contracts/core/Endaoment.vy` | `E-SRC` repository source at baseline |
| CM-032 | `shared_contract` | `existing` | `contracts/core/HumanResources.vy` | `E-SRC` repository source at baseline |
| CM-033 | `shared_contract` | `existing` | `contracts/core/Lootbox.vy` | `E-SRC` repository source at baseline |
| CM-034 | `shared_contract` | `existing` | `contracts/core/Teller.vy` | `E-SRC` repository source at baseline |
| CM-035 | `external_integration` | `external_pending` | none | `E-M0`; external Base Curve pool, omitted for RH, no repository source |
| CM-036 | `external_integration` | `external_pending` | none | `E-M0`; external Base Curve pool, omitted for RH, no repository source |
| CM-037 | `external_integration` | `external_pending` | none | `E-M0`; external Base Aerodrome pool, omitted for RH, no repository source |
| CM-038 | `shared_contract` | `existing` | `contracts/config/BondBooster.vy` | `E-SRC` repository source at baseline |
| CM-039 | `shared_contract` | `existing` | `contracts/priceSources/wsuperOETHbPrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-040 | `shared_contract` | `existing` | `contracts/priceSources/RedStone.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-041 | `shared_contract` | `existing` | `contracts/priceSources/UndyVaultPrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-042 | `external_integration` | `external_pending` | none | `E-M0`; external Underscore system, omitted for RH, no repository source |
| CM-043 | `shared_contract` | `existing` | `contracts/core/CreditRedeem.vy` | `E-SRC` repository source at baseline |
| CM-044 | `shared_contract` | `existing` | `contracts/core/Deleverage.vy` | `E-SRC` repository source at baseline |
| CM-045 | `shared_contract` | `existing` | `contracts/core/TellerUtils.vy` | `E-SRC` repository source at baseline |
| CM-046 | `shared_contract` | `existing` | `contracts/config/SwitchboardEcho.vy` | `E-SRC` repository source at baseline |
| CM-047 | `shared_contract` | `existing` | `contracts/core/EndaomentFunds.vy` | `E-SRC` repository source at baseline |
| CM-048 | `shared_contract` | `existing` | `contracts/core/EndaomentPSM.vy` | `E-SRC` repository source at baseline |
| CM-049 | `chain_specific_config` | `reviewed_planned` | `contracts/config/DefaultsRobinhood.vy` | integrated H-04/S6 brief fixes this exact path; the file does not exist at this baseline |
| CM-050 | `shared_contract` | `existing` | `contracts/priceSources/AeroRipePrices.vy` | `E-SRC` repository source at baseline; omitted for RH |
| CM-051 | `external_artifact` | `external_pending` | none | `E-T1` Track 1 CCIP authority; no artifact, package, or path selected; `B-T1-CCIP`/`B-T1-TOOLCHAIN` |
| CM-052 | `external_artifact` | `external_pending` | none | `E-T1` Track 1 CCIP authority; no artifact, package, or path selected; `B-T1-CCIP`/`B-T1-TOOLCHAIN` |
| CM-053 | `external_integration` | `external_pending` | none | `E-T1` Track 1 CCIP authority; registration action, not a repository artifact; `B-T1-CCIP` |
| CM-054 | `shared_contract` | `external_pending` | none | `E-T7`; no reviewed source or path exists; future oracle amendment |
| CM-055 | `non_onchain_tooling` | `existing` | `scripts/migrate.py`<br>`scripts/console.py`<br>`scripts/utils/deploy_args.py`<br>`scripts/utils/migration.py`<br>`scripts/utils/migration_helpers.py`<br>`scripts/utils/migration_runner.py`<br>`config/network_profiles.py` | `E-SRC` repository source at baseline; H-03 adds `config/robinhood_blueprint.py` only in Phase B |
| CM-056 | `non_onchain_tooling` | `external_pending` | none | `E-T7`; no Robinhood manifest or history path is approved; `B-H05-PLAN`, `B-H09-RELEASE` |
| CM-057 | `non_onchain_tooling` | `existing` | `scripts/export_abis.py`<br>`scripts/verify.py`<br>`scripts/utils/verify_etherscan.py` | `E-SRC` repository source at baseline; RH verifier adapter remains blocked by `B-H09-RELEASE` |
| CM-058 | `external_artifact` | `external_pending` | none | `E-T1` Track 1 CCIP authority; no Solidity toolchain package or version selected; `B-T1-TOOLCHAIN` |
| CM-059 | `non_onchain_tooling` | `existing` | `tests/deployment/test_network_profiles.py`<br>`tests/deployment/test_base_profile_regression.py`<br>`tests/deployment/test_secret_handling.py`<br>`tests/deployment/test_dependency_gate.py`<br>`tests/clock/test_clock_profiles.py`<br>`tests/inventory/test_block_clock_inventory.py`<br>`tests/utils/clock_profiles.py` | `E-SRC` repository source at baseline; H-03 adds its two owned test files only in Phase B |
| CM-060 | `chain_specific_config` | `existing` | `contracts/config/DefaultsLocal.vy` | `E-SRC` repository source at baseline; omitted from RH |

## 7. Historical R1 CM-001–060 table — superseded, non-normative

The table below preserves the pre-R4 dispositions and their supersession
history. It is not a Phase B record source. Section 7A.5 carries the canonical
R6 component authority with deterministic ownership and exact references.

Each registry cell uses `hard`, `order`, or `reserve` for
source-hard-coded, registration-order, or provisional-reservation authority.
“Disabled” cells identify exact inactive sub-surfaces and do not negate a
required artifact. `T8*` abbreviates blockers `B-T8-M1` through `B-T8-M5`.

### 7.1 CM-001–020

| ID / component | Deployment; symbolic inputs | Registry | Disabled or blocked sub-surfaces (Section 6.5) | Typed relations (Section 6.6) | Blockers; owners | Negative assertions | Downstream; controlling evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CM-001 `GreenToken` | required; `I-GREEN`, `I-GOV-HANDOFF`, `I-CLOCK-PARAMS` | HQ/1 `Green Token` hard | CCIP deferred; pool/direct capability absent; mint handoff blocked until setup proof | boot: 004; setup: 004; reg: 004 | H04/H05/SECOPS, T1 | NEG-017/025/031 | H04/H05/H08/H09; `E-CM`, `E-T7`, `E-M0`, `E-SRC-HQ` |
| CM-002 `RipeToken` | required; `I-RIPE`, `I-GOV-HANDOFF`, `I-CLOCK-PARAMS` | HQ/3 `Ripe Token` hard | CCIP deferred; pool/direct capability absent; mint handoff gated | boot: 004; setup: 004; reg: 004 | H04/H05/SECOPS, T1 | NEG-017/025/031 | H04/H05/H08/H09; same authorities |
| CM-003 `SavingsGreen` | required; `I-GREEN`, `I-SGREEN`, `I-CLOCK-PARAMS` | HQ/2 `Savings Green` hard | chain-native deposit/withdraw required; CCIP permanently omitted; launch rewards disabled | boot: 004; setup: 004; reg: 004 | H04/H05/H09 | NEG-031; revised NEG-033/036 | H04/H05/H08/H09; `E-M0`, `E-SRC-HQ`, `E-SRC-REG` supersede older `E-CM`/`E-T7` inert language |
| CM-004 `RipeHq` | required; `I-GREEN`, `I-SGREEN`, `I-RIPE`, `I-GOV-HANDOFF`, `I-CLOCK-PARAMS` | registry root | no capability before exact handoff; no placeholder/sparse-ID assumption | ctor: 001/002/003 | H04/H05/SECOPS | NEG-017/025/031/036 | H04/H05/H08/H09; `E-SRC-HQ`, `E-SRC-REG`, `E-T7` |
| CM-005 `Contributor` | omitted; no field | none | no blueprint deployment, instance, template, vesting, payout, or RIPE capability | none (Section 6.6) | future HR amendment | NEG-016/034 | later product review; `E-M0`, `E-VP`; older optional `E-CM` does not select launch HR |
| CM-006 `TrainingWheels` | required; `I-TRAINING-WHEELS`, `I-GOV-HANDOFF` | none | no guessed allowlist or private role | ctor: 004; setup: 049 | H04/SECOPS | NEG-017 | H04/H05/H08; `E-CM`, `E-T7` |
| CM-007 `DefaultsBase` | omitted; no field | none | no RH import, artifact, value, or fallback | none (Section 6.6) | none | NEG-016/017 | H03/H04; `E-CM`, `E-T7` |
| CM-008 `Ledger` | blocked; `I-LEDGER-BLOCK-SOURCE` | HQ/4 `Ledger` hard semantic; no row until artifact exists | no fresh RH deployment, provider fallback, or Base migration | ctor: 004; reg: 004 | `B-S5-LEDGER`; `OWN-S5` | NEG-017/031 | S5 then H05/H08/H09; `E-S5`, `E-SRC-HQ` |
| CM-009 `MissionControl` | required; `I-RH-DEFAULTS`, `I-ASSET-CONFIG-NONSTOCK`, `I-ASSET-CONFIG-STOCK`, `I-AUCTION-CREDIT-NONSTOCK`, `I-AUCTION-CREDIT-STOCK`, `I-STABILITY-CONFIG`, `I-RIPE-GOV-CONFIG` | HQ/5 `Mission Control` hard | all production values unresolved; unsupported asset/routes false | ctor: 004/049; setup: 008; reg: 004; rt: 008 | H04/H05, T8* | NEG-017/021–024/033–036 | H04/H05/H08/H09; `E-T7`, `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-010 `Switchboard` | required; `I-CLOCK-PARAMS`, `I-GOV-HANDOFF` | HQ/6 `Switchboard` hard; child registry | no unreviewed child or capability | ctor: 004; reg: 004 | H04/H05/SECOPS | NEG-017/031/036 | H04/H05/H08; `E-T7`, `E-SRC-HQ`, `E-SRC-SB` |
| CM-011 `SwitchboardAlpha` | required; `I-CLOCK-PARAMS`, oracle/vault config fields | SB/1 `Switchboard Alpha` hard | unsupported oracle/Underscore actions absent | ctor: 004; reg: 010; rt: 015/019/021 | H04/H05/ORACLE | NEG-024/031/037 | H04/H05/H08; `E-SRC-SB`, `E-SRC-PD` |
| CM-012 `SwitchboardBravo` | required; `I-CLOCK-PARAMS`, `I-AUCTION-CREDIT-NONSTOCK` | SB/2 `Switchboard Bravo` order | unapproved auction values blocked | ctor: 004; reg: 010; rt: 026 | H04/H05 | NEG-017/031 | H04/H05/H08; `E-T7`, `E-SRC-SB` |
| CM-013 `SwitchboardCharlie` | required; `I-CLOCK-PARAMS`, `I-LOOTBOX-CONFIG`, `I-REWARDS-PROMOTION` | SB/3 `Switchboard Charlie` order | all launch reward/points/emission actions disabled | ctor: 004; reg: 010; rt: 028/033 | `B-H04-PARAMS`, `B-REWARD-PROMOTION`; H04/REWARDS | NEG-035/036 | H04/H05/later promotion; `E-M0`, `E-S3`, `E-SRC-SB` |
| CM-014 `SwitchboardDelta` | required; `I-CLOCK-PARAMS` | SB/4 `Switchboard Delta` order | zero-cooldown assertion; HR/bond/Lootbox unapproved actions inert; no future nonzero proposal | ctor: 004; reg: 010; rt: 029/032/033/044 | H04/H05 | NEG-034–036 | H04/H05/H08; `E-S4`, `E-SRC-SB` |
| CM-015 `PriceDesk` | required; `I-CHAINLINK-CORE`, `I-CLOCK-PARAMS` | HQ/7 `Price Desk` hard; child registry | only approved Chainlink paths reachable; reserved slots stay empty | ctor: 004; reg: 004; rt: 016 | H04/H05/ORACLE | NEG-024/031/037 | H04/H05/H08; `E-SRC-HQ`, `E-SRC-PD` |
| CM-016 `ChainlinkPrices` | required; `I-CHAINLINK-CORE`, `I-AAPL-TOKEN`, `I-AAPL-FEED`, `I-USDG`, `I-USDG-FEED`, LP oracle fields | PD/1 `Chainlink` order | no feed registered before exact freeze; no unsupported source fallback; M0 selects no WETH feed, and any later RIPE/WETH LP oracle remains under `I-RIPE-WETH-LP` plus `B-ORACLE-FREEZE` | reg: 015; rt: 015 | `B-ORACLE-FREEZE`; ORACLE/H04/H05 | NEG-017/024/037 | H04/H05/H08; `E-M0`, `E-SRC-PD` |
| CM-017 `CurvePrices` | omitted; no field | PD/2 `Curve` hard semantic, empty reserved slot | no artifact/row/route; CreditEngine danger path must use named base-rate fallback | none (Section 6.6) | future oracle amendment only | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-018 `BlueChipYieldPrices` | omitted; no field | PD/3 `BlueChipYield` order constraint, empty reserved slot | no artifact/yield/row/route | none (Section 6.6) | future oracle amendment only | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-019 `PythPrices` | omitted; no field | PD/4 `Pyth` hard semantic, empty reserved slot | no artifact/network/row/feed/route | none (Section 6.6) | future oracle amendment only | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-020 `StorkPrices` | omitted; no field | PD/5 `Stork` order constraint, empty reserved slot | no artifact/network/row/feed/route | none (Section 6.6) | future oracle amendment only | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |

### 7.2 CM-021–040

| ID / component | Deployment; symbolic inputs | Registry | Disabled or blocked sub-surfaces (Section 6.5) | Typed relations (Section 6.6) | Blockers; owners | Negative assertions | Downstream; controlling evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CM-021 `VaultBook` | required; `I-CLOCK-PARAMS`, `I-AAPL-TOKEN`, `I-STOCK-VAULT-ARTIFACT`, `I-STOCK-VAULT-SLOT` | HQ/8 `Vault Book` hard; child registry | no Stock slot/route merely because registry exists | ctor: 004; reg: 004 | `B-T8-M2`, `B-H05-PLAN`; T8/H05 | NEG-021/031/036 | T8/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ`, `E-SRC-VB` |
| CM-022 `StabilityPool` | required; `I-SGREEN`, `I-STABILITY-CONFIG` | VB/1 `Stability Pool` hard | GREEN launch path required; every Stock custody/swap/reward route disabled | ctor: 004; reg: 021; rt: 001/003 | H04/T8*/H08 | NEG-021/023/033/036 | H04/T8/H05/H08; `E-M0`, `E-T8`, `E-SRC-VB` supersede old disabled scaffold |
| CM-023 `RipeGov` | required; `I-RIPE-GOV-CONFIG` | VB/2 `Ripe Gov Vault` hard | governance deposit path required; global launch rewards disabled | ctor: 004; reg: 021; rt: 002 | H04/H05/H08 | NEG-035/036 | H04/H05/H08; `E-M0`, `E-SRC-VB` |
| CM-024 `SimpleErc20` | required; `I-USDG`, `I-WETH`, `I-GREEN-USDG-LP`, `I-RIPE-WETH-LP`, `I-ASSET-CONFIG-NONSTOCK` | VB/3 `Simple ERC20 Vault` order | ordinary LP deposit-only routes required with named zero-LTV assertion; USDG and WETH are constituent identities for the blocked LP plans, not independently approved vault assets; AAPL/Stock use blocked | ctor: 004; reg: 021; rt: 021 | `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE`, T8*; H04/H05/T8 | NEG-017/021/022/023/031 | H04/H05/T8/H08; `E-M0`, `E-T8`, `E-SRC-VB` |
| CM-025 `RebaseErc20` / `SharesVault` | omitted; no field | VB/4 `Rebase ERC20 Vault` order constraint, empty reserved slot | no Stock selection, positive-delta wrapper change, artifact, row, or route | rt: 021 | future reviewed release only | NEG-016/021/031 | T8/H05/H08; `E-T8` rejects blanket shared/rebase change; `E-SRC-VB` preserves semantic slot |
| CM-026 `AuctionHouse` | required; `I-AAPL-TOKEN`, `I-AUCTION-CREDIT-NONSTOCK`, `I-AUCTION-CREDIT-STOCK`, `I-STOCK-VAULT-ARTIFACT` | HQ/9 `Auction House` hard | AAPL settlement blocked until M1–M5; unsupported Stock routes absent | ctor: 004; reg: 004; rt: 021/027 | T8*; T8/H04 | NEG-021/023/036 | T8/H04/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-027 `AuctionHouseNFT` | required; core constructor fields only | HQ/10 `Auction House NFT` hard | no independent unapproved capability | ctor: 004; reg: 004 | H04/H05 | NEG-031 | H05/H08; `E-CM`, `E-T7`, `E-SRC-HQ` |
| CM-028 `Boardroom` | required topology scaffold; `I-REWARDS-PROMOTION` | HQ/11 `Boardroom` hard | every launch reward/allocation path disabled | ctor: 004; reg: 004 | `B-REWARD-PROMOTION`; REWARDS/H04 | NEG-035/036 | H04/H05/later promotion; `E-M0`, `E-T7`, `E-SRC-HQ` |
| CM-029 `BondRoom` | required topology scaffold; bond config remains absent | HQ/12 `Bond Room` hard | bonds, terms, payments, RIPE capability, rewards disabled | ctor: 004/038; reg: 004; rt: 023 | H04/REWARDS | NEG-034–036 | H04/H05/H08; `E-M0`, `E-T7`, `E-SRC-HQ` |
| CM-030 `CreditEngine` | required; `I-AAPL-TOKEN`, `I-AUCTION-CREDIT-NONSTOCK`, `I-AUCTION-CREDIT-STOCK`, `I-STOCK-VAULT-ARTIFACT`, `I-AAPL-RISK` | HQ/13 `Credit Engine` hard | AAPL borrowing blocked until M1–M5; unsupported oracle/Stock deficit routes fail closed | ctor: 004; reg: 004; rt: 008/017/021/022/026 | T8*, S5, H04 | NEG-021–024/036 | T8/H04/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-031 `Endaoment` | required; reserve/native metadata fields | HQ/14 `Endaoment` hard | Curve, Base DEX, yield, partner, Stock, and Underscore routes disabled | ctor: 004; reg: 004; rt: 015/047 | H04/H05 | NEG-016/020/024/036 | H04/H05/H08; `E-M0`, `E-T7`, `E-SRC-HQ` |
| CM-032 `HumanResources` | required topology scaffold; no contributor input | HQ/15 `Human Resources` hard | operationally inert; no template, contributor, vesting, payout, or RIPE capability | ctor: 004; reg: 004; rt: 009/023 | H04/H05 | NEG-034/036 | H04/H05/H08; `E-M0`, `E-T7`, `E-SRC-HQ` |
| CM-033 `Lootbox` | required integrated S3 artifact; `I-LOOTBOX-CONFIG`, `I-REWARDS-PROMOTION` | HQ/16 `Lootbox` hard | launch reward mint/points and all Underscore paths disabled; no Stock rewards | ctor: 004; reg: 004; rt: 009/023 | H04/REWARDS | NEG-034–036 | H04/H05/H08/later promotion; `E-S3`, `E-M0`, `E-SRC-HQ` |
| CM-034 `Teller` | required; `I-SGREEN`, `I-AAPL-TOKEN`, `I-ASSET-CONFIG-NONSTOCK`, `I-ASSET-CONFIG-STOCK`, `I-STOCK-VAULT-ARTIFACT` | HQ/17 `Teller` hard | USDG not ordinary collateral; AAPL trusted/Department and all unsupported routes disabled; exact-receipt change blocked | ctor: 004; reg: 004; rt: 008/021/022/023/024 | `B-T8-M1`–`B-T8-M5`, H04 | NEG-017/021–023/033/036 | T8/H04/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-035 `GreenPool` | omitted; no field | none | no Base Curve pool/address/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-036 `RipePoolCurve` | omitted; no field | none | no Base Curve pool/address/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-037 `RipePoolAero` | omitted; no field | none | no Base Aerodrome pool/address/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-038 `BondBooster` | required inert dependency scaffold; no terms | none; constructor dependency of CM-029 | no booster config, user units, bond/reward authority | none (Section 6.6) | H04/REWARDS | NEG-035/036 | H04/H05/H08; `E-T7`, source constructor relation |
| CM-039 `wsuperOETHbPrices` | omitted; no field | no PD row | no Base yield asset/source/feed/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-040 `RedStone` | omitted; no field | no PD row | no adapter/feed/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |

### 7.3 CM-041–060

| ID / component | Deployment; symbolic inputs | Registry | Disabled or blocked sub-surfaces (Section 6.5) | Typed relations (Section 6.6) | Blockers; owners | Negative assertions | Downstream; controlling evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CM-041 `UndyVaultPrices` | omitted; no field | no PD row | no Underscore adapter/feed/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-042 `Underscore Vault` | omitted; no field | no VB row | no vault, wallet, price, reward, bypass, deleverage, approval, or route | none (Section 6.6) | none | NEG-016/021/024/033–036 | H08/H09; `E-M0`, `E-S4` |
| CM-043 `CreditRedeem` | required topology scaffold; `I-ASSET-CONFIG-STOCK` | HQ/19 `Credit Redeem` hard | Stock `canRedeemCollateral` named false; no Stock extraction or Underscore route | ctor: 004; reg: 004; rt: 021/022/030 | H04/T8/H08 | NEG-021/022/036 | H04/H05/T8/H08; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-044 `Deleverage` | required unchanged | HQ/18 `Deleverage` hard | named zero-cooldown posture; no Underscore path or future nonzero pending action | ctor: 004; reg: 004; rt: 021/030 | H04/H08 | NEG-036 | H04/H05/H08; `E-S4`, `E-SRC-HQ` |
| CM-045 `TellerUtils` | required | HQ/20 `Teller Utils` hard | Underscore getters/routes fail closed | ctor: 004; reg: 004; rt: 009/021 | H04/H08 | NEG-016/036 | H05/H08; `E-T7`, `E-M0`, `E-SRC-HQ` |
| CM-046 `SwitchboardEcho` | required; `I-PSM-CONFIG` | SB/5 `Switchboard Echo` order | topology/governance presence grants no PSM activation; unsupported Endaoment/yield actions disabled | ctor: 004; reg: 010; rt: 031/048 | `B-PSM-SEQUENCE`, H04/H05 | NEG-018–020/031/036 | H04/H05/H08; `E-M0`, `E-SRC-SB` |
| CM-047 `EndaomentFunds` | required | HQ/21 `Endaoment Funds` hard | no Base external, yield, partner, or Stock destination | ctor: 004; reg: 004; rt: 031 | H04/H05 | NEG-016/020/024/036 | H04/H05/H08; `E-M0`, `E-SRC-HQ` |
| CM-048 `EndaomentPSM` | required; `I-SGREEN`, `I-USDG`, `I-USDG-FEED`, `I-PSM-CONFIG` | HQ/22 `Endaoment PSM` hard | pre-activation mint/redeem/HQ GREEN capability disabled; auto-deposit, yield, approvals, Underscore, and ordinary Teller route disabled; launch activation blocked until sequence proof | ctor: 004; reg: 004; rt: 001/003/016/031/047 | `B-H04-PARAMS`, `B-PSM-SEQUENCE`, H05/H08/H09 | NEG-017–020/024/031/036 | H04/H05/H08/H09; `E-M0` supersedes old deferred outcome; source constructor and `E-SRC-HQ` prove staging |
| CM-049 `DefaultsRobinhood` | required chain-specific config artifact; `I-RH-DEFAULTS` | none | no Base/local/address/value fallback; artifact not created by H-03 | setup: 009 | `B-H04-PARAMS`; H04/S6 | NEG-017 | H04 then H05; `E-CM`, `E-T7`, current H04 brief |
| CM-050 `AeroRipePrices` | omitted; no field | no PD row | no Base Aerodrome adapter/feed/route | none (Section 6.6) | none | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-051 GREEN CCIP BurnMint pool | deferred; `I-CCIP-ARTIFACTS` | provisional HQ/23 semantic reservation only | no artifact/row/address/remote/capability at launch; promotion nonblocking | ctor: 001; reg: 004 | `B-T1-CCIP`, `B-T1-TOOLCHAIN`; T1 | NEG-016/025/031/036 | separate Track 1 promotion; `E-M0`, `E-T7` |
| CM-052 RIPE CCIP BurnMint pool | deferred; `I-CCIP-ARTIFACTS` | provisional HQ/24 semantic reservation only | no artifact/row/address/remote/capability at launch; promotion nonblocking | ctor: 002; reg: 004 | same | NEG-016/025/031/036 | separate Track 1 promotion; `E-M0`, `E-T7` |
| CM-053 CCIP token-admin registration | deferred; `I-CCIP-REGISTRATION` | none; cannot materialize reservations | no registration/admin/remote/capability/approval | rt: 051/052 | `B-T1-CCIP`; T1/SECOPS | NEG-016/025/036 | separate Track 1 promotion; `E-M0`, `E-T7` |
| CM-054 GREEN/RIPE local price adapter | deferred; no value-bearing field | no PD reservation assigned | no fabricated peg, adapter, artifact, slot, feed, or route | rt: 015 | ORACLE/security future release | NEG-016/024/037 | future oracle/H03 amendment; `E-CM`, `E-T7` |
| CM-055 Deployment, migration, and parameter-report tooling | required non-onchain; this H-03 API plus later `I-MIGRATION-PLAN` | none | no execution/address/default logic in H-03 | rt: 004 | `B-H04-PARAMS`, `B-H05-PLAN` | NEG-017/031 | H03/H04/H05; `E-T7`, `E-H03` |
| CM-056 Manifests and migration history | required later non-onchain; `I-MANIFEST-HISTORY` | none | no Phase A/B manifest, history, receipt, or address | none (Section 6.6) | `B-H05-PLAN`, `B-H09-RELEASE` | NEG-016/017 | H05/H09; `E-T7` |
| CM-057 ABI export and explorer verification | required later tooling; `I-VERIFY-EXPORT` | none | no Phase A/B ABI/export/verification; CCIP part deferred | rt: 004 | `B-H09-RELEASE`; T1 for CCIP | NEG-016 | later Track 7/Track 1; `E-T7` |
| CM-058 Solidity build/test/deploy toolchain | deferred; no selected package/version | none | no build/dependency/artifact/verification path | none (Section 6.6) | `B-T1-TOOLCHAIN`; T1/security | NEG-016/025 | separate Track 1/toolchain review; `E-T7`, `E-M0` |
| CM-059 Base/RH test profiles | required non-onchain; `I-RELEASE-PROOF` | none | H02/S1/S2 integrated; deployment/fork/release tiers remain blocked | rt: 004 | `B-H08-PROOF`, `B-H09-RELEASE` | all H03 negatives | H08/H09; `E-T7`, integrated H02/S1/S2 |
| CM-060 `DefaultsLocal` | omitted from RH; no field | none | no RH artifact/value/fallback; generic local tests remain unchanged | none (Section 6.6) | none | NEG-016/017 | H03/H04; `E-CM`, `E-T7` |

Primary-table completeness assertion: the IDs above are exactly the contiguous
set CM-001 through CM-060, each once.

## 7A. Canonical R6 Phase A authority

Sections 7A.1–7A.5 are the sole record inventories Phase B may encode. The
historical R1 tables in Sections 6.4–7 remain evidence of supersession only.
For each component, Phase B joins these exact inventories by stable ID:

- symbolic inputs by `consumers`;
- surfaces by `component_id`;
- relations by source component;
- source paths by component;
- registry expectations by Section 8 component ID; and
- owners, deployment, downstream slices, assertions, and evidence by
  Section 7A.5.

Any missing, extra, duplicate, unresolved, or differently classified record
requires a new reviewed Phase A amendment. Phase B may not infer an additional
record from prose.

Mechanical R6 inventory totals are: 21 evidence IDs, 11 owner IDs, 18
blockers, 48 symbolic inputs, 60 components (38 required, 16 omitted, 5
deferred, 1 blocked), 94 launch/security surfaces, 2 promotion actions, 288
explicit typed relation records with no grouped expansion, 103
component-qualified source-path records, 38 registry expectations (24
RipeHq, 4 VaultBook, 5 PriceDesk, 5 Switchboard), and 24 negative assertion
IDs. Each detailed section below states the mechanically reproduced
subtotals; every relation-table row is exactly one expanded record.

### 7A.1 Canonical symbolic inputs

Every owner is an exact Section 6.2 `OWN-*` ID. Empty co-owner tuples are shown
as `none`. In the consumer column, a slash-separated numeric suffix inherits
the leading `CM-` prefix: for example, `CM-001/003` means exactly CM-001 and
CM-003. Concrete values remain outside H-03. The canonical table contains
exactly 48 symbolic inputs.

| Field ID | Semantic class | Exact consumers | Primary owner | Co-owners | Deadline gate | Status; blockers |
| --- | --- | --- | --- | --- | --- | --- |
| `I-GREEN` | GREEN deployment identity | CM-001/003/004/022/048 | `OWN-H05` | `OWN-SECOPS` | before H-05 execution | required; `B-H05-PLAN`, `B-SECOPS-HANDOFF` |
| `I-RIPE` | RIPE deployment identity | CM-002/004/023/028/029/032/033 | `OWN-H05` | `OWN-SECOPS` | before H-05 execution | required; `B-H05-PLAN`, `B-SECOPS-HANDOFF` |
| `I-SGREEN` | chain-native sGREEN deployment identity | CM-003/004/022/034/048 | `OWN-H05` | `OWN-H04` | before H-05 execution | required; `B-H05-PLAN` |
| `I-GREEN-INITIAL-SUPPLY` | GREEN constructor initial-supply quantity | CM-001 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-GREEN-INITIAL-SUPPLY-RECIPIENT` | GREEN constructor initial-supply recipient | CM-001 | `OWN-SECOPS` | `OWN-H04`, `OWN-H05` | before H-05 execution | required; `B-SECOPS-HANDOFF` |
| `I-RIPE-INITIAL-SUPPLY` | RIPE constructor initial-supply quantity | CM-002 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-RIPE-INITIAL-SUPPLY-RECIPIENT` | RIPE constructor initial-supply recipient | CM-002 | `OWN-SECOPS` | `OWN-H04`, `OWN-H05` | before H-05 execution | required; `B-SECOPS-HANDOFF` |
| `I-SGREEN-INITIAL-SUPPLY` | sGREEN constructor initial-supply quantity | CM-003 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-SGREEN-INITIAL-SUPPLY-RECIPIENT` | sGREEN constructor initial-supply recipient | CM-003 | `OWN-SECOPS` | `OWN-H04`, `OWN-H05` | before H-05 execution | required; `B-SECOPS-HANDOFF` |
| `I-GOV-HANDOFF` | public governance/capability handoff references | CM-001/002/003/004/006/010/011/012/013/014/015/016/021/046 | `OWN-SECOPS` | `OWN-H05` | before testnet/production handoff | required; `B-SECOPS-HANDOFF` |
| `I-CLOCK-PARAMS` | registry/governance/config timing classes not separately enumerated below | CM-001/002/003/004/006/010/011/012/013/014/015/021 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-TRAINING-WHEELS` | launch-control policy, concrete target binding, and public authority classes | CM-006/009/013 | `OWN-H04` | `OWN-SECOPS` | before testnet | required; target unresolved under `B-H04-PARAMS`; authority handoff blocked by `B-SECOPS-HANDOFF` |
| `I-LEDGER-BLOCK-SOURCE` | fresh-Ledger action-block discriminator/provider | CM-008 | `OWN-S5` | `OWN-SECOPS` | before CM-008 enters H-05 | blocked; `B-S5-LEDGER` |
| `I-LEDGER-DEFAULTS` | Ledger constructor defaults dependency and initial allocation fields | CM-008/049 | `OWN-H04` | `OWN-S5`, `OWN-H05` | before CM-008 enters H-05 | blocked; `B-S5-LEDGER`, `B-H04-PARAMS` |
| `I-RH-DEFAULTS` | DefaultsRobinhood artifact identity and exhaustive typed manifest | CM-009/049 | `OWN-H04` | `OWN-H05` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-TELLER-INITIAL-PAUSE` | Teller constructor `_shouldPause` launch-safety state | CM-034 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before Teller enters the H-05 plan | blocked; `B-H04-PARAMS`, `B-H05-PLAN` |
| `I-CHAINLINK-CORE` | native/BTC sentinel metadata, feeds, decimals, and adapter constructor classes | CM-015/016 | `OWN-ORACLE` | `OWN-H04`, `OWN-H05` | before oracle plan freeze | required; `B-ORACLE-FREEZE` |
| `I-CHAINLINK-TIMELOCKS` | Chainlink min/max price-change timelocks and default stale-time classes | CM-016 | `OWN-H04` | `OWN-ORACLE`, `OWN-H05` | before oracle plan freeze | required; `B-H04-PARAMS`, `B-ORACLE-FREEZE` |
| `I-AAPL-TOKEN` | symbolic approved initial Stock identity | CM-016/021/026/030/034 | `OWN-T8` | `OWN-ORACLE`, `OWN-H04` | final pre-activation freeze | required; `B-T8-FREEZE` |
| `I-AAPL-FEED` | symbolic AAPL/USD feed identity and provenance | CM-016 | `OWN-ORACLE` | `OWN-T8`, `OWN-H04` | final pre-activation freeze | required; `B-T8-FREEZE`, `B-ORACLE-FREEZE` |
| `I-AAPL-RISK` | one-vault, exposure, LTV, cap, route, and review configuration | CM-009/021/026/030/034/043 | `OWN-T8` | `OWN-H04`, `OWN-ORACLE`, `OWN-SECOPS` | before M5 activation | blocked; `B-H04-PARAMS`, `B-T8-FREEZE`, `B-T8-M5` |
| `I-STOCK-VAULT-ARTIFACT` | isolated guarded-vault source/artifact/runtime | CM-021/026/030/034 | `OWN-T8` | `OWN-SECOPS` | before M2/M5 | blocked; `B-T8-M2` |
| `I-STOCK-VAULT-SLOT` | approved VaultBook placement/name | CM-021 | `OWN-T8` | `OWN-H05` | before M5/H-05 plan | blocked; `B-T8-M2`, `B-H05-PLAN` |
| `I-USDG` | symbolic canonical USDG identity | CM-016/024/048 | `OWN-T8` | `OWN-H05`, `OWN-ORACLE` | before PSM/LP plan freeze | required; `B-H05-PLAN` |
| `I-USDG-FEED` | symbolic USDG/USD feed identity and provenance | CM-016/048 | `OWN-ORACLE` | `OWN-T8`, `OWN-H04` | final pre-activation freeze | required; `B-ORACLE-FREEZE` |
| `I-PSM-CONFIG` | PSM reserve, intervals, fees, caps, allowlist, and no-yield classes | CM-046/048 | `OWN-H04` | `OWN-T8`, `OWN-SECOPS` | before PSM staging | required; `B-H04-PARAMS`, `B-PSM-SEQUENCE` |
| `I-ECHO-TIMELOCKS` | SwitchboardEcho temporary-governance and min/max configuration timelocks | CM-046 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before SwitchboardEcho deployment | required; `B-H04-PARAMS` |
| `I-WETH` | symbolic Robinhood WETH constituent identity | CM-024/031 | `OWN-H04` | `OWN-H05`, `OWN-ORACLE` | before LP/Endaoment plan freeze | required; `B-H05-PLAN` |
| `I-GREEN-USDG-LP` | LP artifact/runtime/oracle and ordinary-only Teller configuration | CM-016/024 | `OWN-H04` | `OWN-H05`, `OWN-ORACLE` | before launch plan close | blocked; `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` |
| `I-RIPE-WETH-LP` | LP artifact/runtime/oracle and ordinary-only Teller configuration | CM-016/024 | `OWN-H04` | `OWN-H05`, `OWN-ORACLE` | before launch plan close | blocked; `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` |
| `I-ASSET-CONFIG-NONSTOCK` | typed non-Stock asset/vault/LTV/route settings | CM-009/011/024/034 | `OWN-H04` | `OWN-T8`, `OWN-ORACLE` | before M5/H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-ASSET-CONFIG-STOCK` | typed initial-Stock asset/vault/LTV/route settings | CM-009/011/021/026/030/034/043 | `OWN-T8` | `OWN-H04`, `OWN-ORACLE` | before M5 activation | blocked; `B-H04-PARAMS`, `B-T8-M5` |
| `I-STABILITY-CONFIG` | GREEN Stability Pool launch config, Stock exclusions, and concrete `specialStabPoolId` binding | CM-009/011/012/022/026 | `OWN-H04` | `OWN-T8` | before M5/H-05 plan freeze | required; binding unresolved under `B-H04-PARAMS`; activation blocked by `B-T8-M5` |
| `I-RIPE-GOV-CONFIG` | RIPE governance-vault launch config | CM-009/011/023 | `OWN-H04` | `OWN-H05` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-AUCTION-CREDIT-NONSTOCK` | non-Stock auction/credit parameters | CM-009/012/026/030 | `OWN-H04` | `OWN-T8` | before M5/H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-AUCTION-CREDIT-STOCK` | Stock containment auction/credit settings | CM-009/012/026/030 | `OWN-T8` | `OWN-H04`, `OWN-SECOPS` | before M4/M5 | blocked; `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` |
| `I-LOOTBOX-CONFIG` | S3 constructor/configuration fields | CM-013/033 | `OWN-H04` | `OWN-REWARDS` | before H-05 plan freeze | required; `B-H04-PARAMS` |
| `I-REWARDS-PROMOTION` | possible later reward-promotion configuration, validation, monitoring, and kill package; launch-disabled state is represented separately | CM-009/013/022/023/028/029/033/038 | `OWN-REWARDS` | `OWN-SECOPS`, `OWN-H04` | `within_seven_day_separately_reviewed_reward_activation` | deferred; `B-REWARD-PROMOTION` |
| `I-BOND-ROOM-CONFIG` | BondRoom terms, payment, duration, and disabled-launch classes | CM-014/029 | `OWN-H04` | `OWN-REWARDS` | before any bond release | deferred; `B-H04-PARAMS`, `B-REWARD-PROMOTION` |
| `I-BOND-BOOSTER-CONFIG` | maximum boost ratio, maximum units, minimum lock duration, and booster rows | CM-014/029/038 | `OWN-H04` | `OWN-REWARDS` | before any bond release | deferred; `B-H04-PARAMS`, `B-REWARD-PROMOTION` |
| `I-HR-TIMELOCKS` | HumanResources min/max configuration timelocks | CM-014/032 | `OWN-H04` | `OWN-SECOPS` | before any HR release | deferred; `B-H04-PARAMS` |
| `I-ENDAOMENT-NATIVE-METADATA` | Endaoment WETH/native-token identities and reserve metadata | CM-031 | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | before Endaoment deployment | required; `B-H04-PARAMS`, `B-H05-PLAN` |
| `I-CCIP-ARTIFACTS` | GREEN/RIPE pool source/package/artifacts | CM-051/052 | `OWN-T1` | `OWN-SECOPS` | `within_seven_day_separately_reviewed_ccip_promotion` | deferred; `B-T1-CCIP`, `B-T1-TOOLCHAIN` |
| `I-CCIP-REGISTRATION` | admin, remote, rate/capability, supply, and promotion evidence | CM-053 | `OWN-T1` | `OWN-SECOPS` | `within_seven_day_separately_reviewed_ccip_promotion` | deferred; `B-T1-CCIP` |
| `I-MIGRATION-PLAN` | Robinhood namespace, exact order, receipts, and registry assertions | CM-055 | `OWN-H05` | `OWN-H04` | before any plan execution | blocked; `B-H05-PLAN` |
| `I-MANIFEST-HISTORY` | independent Robinhood manifest/history schema and roots | CM-056 | `OWN-H05` | `OWN-H09` | before rehearsal | blocked; `B-H05-PLAN`, `B-H09-RELEASE` |
| `I-VERIFY-EXPORT` | ABI/export/verifier adapter and evidence policy | CM-057 | `OWN-H09` | `OWN-H05`, `OWN-T1` | before verification | blocked; `B-H09-RELEASE`, `B-T1-TOOLCHAIN` where CCIP applies |
| `I-RELEASE-PROOF` | topology, clean deployment, adversarial, Base-regression, and release evidence | CM-059 | `OWN-H09` | `OWN-H08`, `OWN-SECOPS` | before testnet/production activation | blocked; `B-H08-PROOF`, `B-H09-RELEASE` |

Constructor completeness is source-backed: CM-003, CM-015, and CM-021 take
their temporary/initial governance inputs at
`contracts/tokens/SavingsGreen.vy:32-41`,
`contracts/registries/PriceDesk.vy:62-74`, and
`contracts/registries/VaultBook.vy:50-57`, respectively. GREEN, RIPE, and
sGREEN each take separate initial-supply and initial-supply-recipient values
at `contracts/tokens/GreenToken.vy:45-53`,
`contracts/tokens/RipeToken.vy:45-53`, and
`contracts/tokens/SavingsGreen.vy:32-41`. The six dedicated supply/recipient
records above prevent Phase B from inferring that any of those owner-owned
constructor fields are equal, zero, or interchangeable. Teller independently
takes `_shouldPause` at `contracts/core/Teller.vy:218-221`;
`I-TELLER-INITIAL-PAUSE` prevents Phase B from inferring that Boolean from
asset configuration or silently selecting a launch state.

### 7A.2 Canonical launch/security surface inventory

The exact set below contains 94 records. Ordinary absence on an omitted
component is intentionally represented only by that component's deployment
disposition and negative assertions. Counts and expected sets must be derived
from these rows, not from the historical R1 table.

The exact cardinalities are:

- kinds: 7 artifact, 18 capability, 43 route, 3 permission,
  7 configuration, 7 registration, and 9 behavioral-invariant records;
- dispositions: 10 required, 20 omitted, 29 disabled, 5 deferred, and
  30 blocked records; and
- lifecycle phases: 29 `deployed_initial_value`, 17
  `pre_activation_configuration`, 4 `atomic_stock_activation`, 6
  `within_seven_day_separately_reviewed_ccip_promotion`, 0
  `within_seven_day_separately_reviewed_reward_activation`, 5
  `post_launch_release`, 20 `omitted`, and 13 `blocked` records.

The zero reward-activation `SurfaceRecord` cardinality is correct and
required: that lifecycle value belongs only to
`P-REWARDS-SEVEN-DAY.promotion_phase`, while all seven reward surfaces retain
their launch-disabled `deployed_initial_value` state.

| Surface ID | Component | Kind | Semantic meaning | Disposition | Lifecycle phase | Blockers | Assertions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `S-001-CCIP-CAP` | CM-001 | `capability` | GREEN CCIP/direct mint-burn capability is disabled at launch and remains disabled continuously through the separately reviewed promotion checkpoint | `disabled` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-CCIP` | NEG-025 |
| `S-001-MINT-HANDOFF` | CM-001 | `capability` | GREEN mint capability handoff | `blocked` | `blocked` | `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-002-CCIP-CAP` | CM-002 | `capability` | RIPE CCIP/direct mint-burn capability is disabled at launch and remains disabled continuously through the separately reviewed promotion checkpoint | `disabled` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-CCIP` | NEG-025 |
| `S-002-MINT-HANDOFF` | CM-002 | `capability` | RIPE mint capability handoff | `blocked` | `blocked` | `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-003-DEPOSIT` | CM-003 | `route` | chain-native sGREEN deposit | `required` | `deployed_initial_value` | none | NEG-033 |
| `S-003-WITHDRAW` | CM-003 | `route` | chain-native sGREEN withdrawal | `required` | `deployed_initial_value` | none | NEG-033 |
| `S-003-CCIP` | CM-003 | `capability` | sGREEN CCIP enablement, permanently excluded | `omitted` | `omitted` | none | NEG-033 |
| `S-003-REWARDS` | CM-003 | `route` | sGREEN reward accrual is disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-004-GLOBAL-MINT-DISABLE` | CM-004 | `capability` | source initializes `mintEnabled=True`; an approved pre-activation action must set it `False` and global minting must remain disabled throughout staging | `disabled` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031/`NEG-H03-GLOBAL-MINT-SEQUENCE` |
| `S-004-GLOBAL-MINT-REENABLE` | CM-004 | `capability` | owner-approved final launch activation re-enables global minting only after exact tuple configuration, PSM redemption proof, the final PSM tuple mutation, and full re-verification; execution and proof remain blocked | `blocked` | `blocked` | `B-H05-PLAN`, `B-PSM-SEQUENCE`, `B-SECOPS-HANDOFF` | `NEG-H03-GLOBAL-MINT-SEQUENCE` |
| `S-004-SPARSE-ID` | CM-004 | `registration` | placeholder or sparse-ID registration | `omitted` | `omitted` | none | NEG-031/036 |
| `S-006-ALLOWLIST` | CM-006 | `configuration` | TrainingWheels allowlist and exit policy | `blocked` | `blocked` | `B-H04-PARAMS`, `B-SECOPS-HANDOFF` | NEG-017 |
| `S-008-RH-ARTIFACT` | CM-008 | `artifact` | fresh Robinhood Ledger deployable source | `blocked` | `pre_activation_configuration` | `B-S5-LEDGER` | NEG-017/031 |
| `S-008-NO-FALLBACK` | CM-008 | `behavioral_invariant` | action-block source has no provider or native-block fallback after selection | `required` | `deployed_initial_value` | `B-S5-LEDGER` | NEG-017 |
| `S-008-BASE-MIGRATION` | CM-008 | `route` | Base Ledger state migration | `omitted` | `omitted` | none | NEG-016 |
| `S-009-VALUES` | CM-009 | `configuration` | all production MissionControl values | `blocked` | `pre_activation_configuration` | `B-H04-PARAMS` | NEG-017 |
| `S-009-UNSUPPORTED-ASSET` | CM-009 | `route` | unsupported asset and route flags | `disabled` | `deployed_initial_value` | `B-T8-M5` | NEG-021/024 |
| `S-010-HQ-BLACKLIST-CAP` | CM-010 | `capability` | post-registration RipeHq target tuple is `canMintGreen=False`, `canMintRipe=False`, `canSetTokenBlacklist=True`; it is withheld until reviewed setup and handoff | `blocked` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-010-UNREVIEWED-CHILD` | CM-010 | `registration` | unreviewed Switchboard child registration | `omitted` | `omitted` | none | NEG-031/036 |
| `S-011-ORACLE-ACTIONS` | CM-011 | `route` | unsupported oracle configuration actions | `disabled` | `deployed_initial_value` | `B-ORACLE-FREEZE` | NEG-024/037 |
| `S-011-UNDERSCORE` | CM-011 | `route` | Underscore configuration actions | `omitted` | `omitted` | none | NEG-016/024 |
| `S-012-AUCTION-VALUES` | CM-012 | `configuration` | auction parameter values | `blocked` | `blocked` | `B-H04-PARAMS` | NEG-017 |
| `S-013-REWARD-ACTIONS` | CM-013 | `route` | reward, points, and emission actions are disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-014-COOLDOWN` | CM-014 | `behavioral_invariant` | S4 zero-cooldown launch posture | `required` | `deployed_initial_value` | none | NEG-036 |
| `S-014-INERT-ACTIONS` | CM-014 | `route` | HR, bond, and Lootbox unapproved actions | `disabled` | `deployed_initial_value` | `B-H04-PARAMS` | NEG-034/035/036 |
| `S-015-RESERVED-SLOTS` | CM-015 | `registration` | PriceDesk semantic slots 2–5 stay empty | `omitted` | `omitted` | none | NEG-024/037 |
| `S-016-FEED-REG` | CM-016 | `registration` | feed registration before exact freeze | `blocked` | `pre_activation_configuration` | `B-ORACLE-FREEZE` | NEG-024/037 |
| `S-016-SOURCE-FALLBACK` | CM-016 | `route` | unsupported price-source fallback | `omitted` | `omitted` | none | NEG-024 |
| `S-016-WETH-FEED` | CM-016 | `registration` | independent WETH feed not selected by M0 | `omitted` | `omitted` | none | NEG-024 |
| `S-021-HQ-RIPE-CAP` | CM-021 | `capability` | post-registration RipeHq target tuple is `canMintGreen=False`, `canMintRipe=True`, `canSetTokenBlacklist=False`; it is withheld until reviewed setup and handoff | `blocked` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-021-STOCK-SLOT` | CM-021 | `registration` | guarded Stock-vault VaultBook placement | `blocked` | `pre_activation_configuration` | `B-T8-M2`, `B-H05-PLAN` | NEG-021/031 |
| `S-022-GREEN` | CM-022 | `route` | GREEN Stability Pool launch path | `required` | `deployed_initial_value` | none | NEG-033 |
| `S-022-STOCK-CUSTODY` | CM-022 | `route` | Stock custody in Stability Pool | `disabled` | `deployed_initial_value` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021/023 |
| `S-022-STOCK-SWAP` | CM-022 | `route` | Stock Stability Pool swap | `disabled` | `deployed_initial_value` | `B-T8-M5` | NEG-023 |
| `S-022-REWARDS` | CM-022 | `route` | Stability Pool reward accrual is disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-023-GOV-DEPOSIT` | CM-023 | `route` | RIPE governance deposit | `required` | `deployed_initial_value` | none | NEG-036 |
| `S-023-REWARDS` | CM-023 | `route` | governance-vault reward accrual is disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-024-LP-DEPOSIT` | CM-024 | `route` | both approved LP deposit-only routes are launch requirements and block launch-plan closure until proved | `blocked` | `blocked` | `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` | `NEG-H03-LP-ZERO-LTV`/`NEG-H03-LP-ORDINARY-ONLY` |
| `S-024-LP-ORDINARY-ONLY` | CM-024 | `behavioral_invariant` | each approved LP permits only Teller `deposit`/`depositMany`; `depositFromTrusted` and every Department/direct-vault bypass are excluded for that LP asset | `blocked` | `blocked` | `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` | `NEG-H03-LP-ORDINARY-ONLY` |
| `S-024-LP-ZERO-LTV` | CM-024 | `configuration` | both approved LP assets require an explicit legitimate `ltv=0` configuration; a missing LTV field is not equivalent | `blocked` | `pre_activation_configuration` | `B-H04-PARAMS`, `B-LP-ARTIFACTS` | `NEG-H03-LP-ZERO-LTV` |
| `S-024-LP-BORROW` | CM-024 | `route` | LP borrowing power and borrowing route | `omitted` | `omitted` | none | `NEG-H03-LP-ZERO-LTV` |
| `S-024-STOCK-USE` | CM-024 | `route` | AAPL/Stock use of the ordinary vault | `blocked` | `atomic_stock_activation` | `B-T8-M2`, `B-T8-M5` | NEG-021 |
| `S-026-HQ-GREEN-CAP` | CM-026 | `capability` | post-registration RipeHq target tuple is `canMintGreen=True`, `canMintRipe=False`, `canSetTokenBlacklist=False`; it is withheld until reviewed setup and handoff | `blocked` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-026-AAPL-SETTLE` | CM-026 | `route` | AAPL auction settlement | `blocked` | `atomic_stock_activation` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021/023 |
| `S-026-STOCK-ROUTES` | CM-026 | `route` | unsupported Stock auction routes | `omitted` | `omitted` | none | NEG-021 |
| `S-028-REWARD-PATH` | CM-028 | `route` | Boardroom rewards and allocations are disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-029-BONDS` | CM-029 | `route` | bonds, terms, and payment routes | `disabled` | `post_launch_release` | `B-H04-PARAMS`, `B-REWARD-PROMOTION` | NEG-034/035 |
| `S-029-RIPE-CAP` | CM-029 | `capability` | BondRoom RIPE mint capability | `disabled` | `post_launch_release` | `B-SECOPS-HANDOFF`, `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-030-HQ-GREEN-CAP` | CM-030 | `capability` | post-registration RipeHq target tuple is `canMintGreen=True`, `canMintRipe=False`, `canSetTokenBlacklist=False`; it is withheld until reviewed setup and handoff | `blocked` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-030-AAPL-BORROW` | CM-030 | `route` | AAPL-backed borrowing | `blocked` | `atomic_stock_activation` | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | NEG-021 |
| `S-030-STOCK-DEFICIT` | CM-030 | `route` | Stock deficit/containment path | `blocked` | `atomic_stock_activation` | `B-T8-M3` | NEG-021/023 |
| `S-030-CURVE-ABSENT-BASE-RATE` | CM-030 | `behavioral_invariant` | absent Curve source returns the named base rate without a Curve call | `required` | `deployed_initial_value` | none | NEG-024 |
| `S-031-HQ-GREEN-CAP` | CM-031 | `capability` | post-registration RipeHq target tuple is `canMintGreen=True`, `canMintRipe=False`, `canSetTokenBlacklist=False`; it is withheld until reviewed setup and handoff | `blocked` | `pre_activation_configuration` | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | NEG-017/031 |
| `S-031-YIELD` | CM-031 | `route` | Endaoment yield positions | `disabled` | `deployed_initial_value` | `B-H04-PARAMS` | NEG-020 |
| `S-031-STOCK` | CM-031 | `route` | Endaoment Stock destination | `omitted` | `omitted` | none | NEG-021 |
| `S-032-HR-ACTIVATION` | CM-032 | `capability` | contributor creation, vesting, payout, and RIPE minting | `disabled` | `post_launch_release` | `B-H04-PARAMS`, `B-SECOPS-HANDOFF` | NEG-034/036 |
| `S-033-REWARD-MINT` | CM-033 | `capability` | Lootbox reward mint and points are disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | NEG-035/036 |
| `S-033-UNDERSCORE` | CM-033 | `route` | Lootbox Underscore paths | `omitted` | `omitted` | none | NEG-016/036 |
| `S-033-STOCK-REWARD` | CM-033 | `route` | Stock depositor/borrower reward accrual is disabled at launch | `disabled` | `deployed_initial_value` | `B-REWARD-PROMOTION` | `NEG-H03-STOCK-REWARD-DISABLED` |
| `S-034-USDG-COLLATERAL` | CM-034 | `route` | USDG as ordinary Teller collateral | `omitted` | `omitted` | none | `NEG-H03-USDG-ROUTE` |
| `S-034-AAPL-TRUSTED` | CM-034 | `route` | AAPL trusted deposit route | `disabled` | `deployed_initial_value` | `B-T8-M5` | NEG-021 |
| `S-034-AAPL-DEPT` | CM-034 | `route` | AAPL Department bypass route | `disabled` | `deployed_initial_value` | `B-T8-M5` | NEG-021 |
| `S-034-INITIAL-PAUSE` | CM-034 | `configuration` | Teller constructor `_shouldPause` is a required symbolic launch-safety choice and must not be inferred from asset settings or defaulted | `blocked` | `pre_activation_configuration` | `B-H04-PARAMS`, `B-H05-PLAN` | NEG-017 |
| `S-034-EXACT-RECEIPT` | CM-034 | `behavioral_invariant` | every external and trusted Teller producer requires `R == Q`, `vaultResult == Q`, exact-length reads, one mutex policy, and atomic rollback | `blocked` | `pre_activation_configuration` | `B-T8-M1` | `NEG-H03-TELLER-EXACT-RECEIPT` |
| `S-034-SGREEN-ROUTE` | CM-034 | `route` | Teller-held sGREEN route | `required` | `deployed_initial_value` | none | NEG-033 |
| `S-038-BOOSTER-CFG` | CM-038 | `configuration` | booster limits, rows, and user units | `disabled` | `post_launch_release` | `B-H04-PARAMS`, `B-REWARD-PROMOTION` | NEG-035 |
| `S-043-STOCK-REDEEM` | CM-043 | `route` | Stock `canRedeemCollateral` remains false | `disabled` | `deployed_initial_value` | `B-T8-M5` | NEG-022 |
| `S-044-COOLDOWN` | CM-044 | `behavioral_invariant` | Deleverage zero-cooldown launch posture | `required` | `deployed_initial_value` | none | NEG-036 |
| `S-044-UNDERSCORE` | CM-044 | `route` | Deleverage Underscore path | `omitted` | `omitted` | none | NEG-016/036 |
| `S-045-UNDERSCORE` | CM-045 | `behavioral_invariant` | Underscore getters and routes fail closed | `omitted` | `omitted` | none | NEG-016/036 |
| `S-046-PSM-ACTIVATION` | CM-046 | `permission` | governance presence grants no PSM activation | `blocked` | `blocked` | `B-PSM-SEQUENCE` | NEG-018/019 |
| `S-046-ENDAOMENT-ACTIONS` | CM-046 | `route` | unsupported Endaoment/yield actions | `disabled` | `deployed_initial_value` | `B-H04-PARAMS` | NEG-020 |
| `S-047-EXTERNAL` | CM-047 | `route` | Base external, yield, and partner destinations | `omitted` | `omitted` | none | NEG-016/020 |
| `S-047-STOCK` | CM-047 | `route` | Stock destination | `omitted` | `omitted` | none | NEG-021 |
| `S-048-MINT` | CM-048 | `capability` | PSM mint begins false | `disabled` | `pre_activation_configuration` | `B-PSM-SEQUENCE` | NEG-018 |
| `S-048-REDEEM` | CM-048 | `capability` | PSM redeem begins false and must be proved before mint | `disabled` | `pre_activation_configuration` | `B-PSM-SEQUENCE` | NEG-019/`NEG-H03-PSM-REDEEM-FIRST` |
| `S-048-HQ-GREEN-CAP` | CM-048 | `capability` | RipeHq GREEN mint capability is a launch requirement granted only as the final capability-tuple mutation before full re-verification and final global-mint re-enable | `blocked` | `blocked` | `B-PSM-SEQUENCE`, `B-SECOPS-HANDOFF` | NEG-018/`NEG-H03-PSM-MINT-LAST`/`NEG-H03-GLOBAL-MINT-SEQUENCE` |
| `S-048-AUTO-DEPOSIT` | CM-048 | `configuration` | source deploys with auto-deposit `True`; launch requires an approved pre-activation action setting it to `False` | `disabled` | `pre_activation_configuration` | `B-H04-PARAMS`, `B-PSM-SEQUENCE` | NEG-020 |
| `S-048-YIELD` | CM-048 | `route` | optional yield position remains absent | `disabled` | `deployed_initial_value` | `B-H04-PARAMS` | NEG-020 |
| `S-048-APPROVAL` | CM-048 | `permission` | external approval surface remains disabled | `disabled` | `deployed_initial_value` | `B-H04-PARAMS` | NEG-020 |
| `S-048-UNDERSCORE` | CM-048 | `route` | Underscore bypass | `omitted` | `omitted` | none | NEG-016/020 |
| `S-048-TELLER-ROUTE` | CM-048 | `route` | generic Teller collateral/asset route | `omitted` | `omitted` | none | `NEG-H03-USDG-ROUTE` |
| `S-048-ACTIVATION` | CM-048 | `permission` | PSM redemption-first then mint-last activation is required before launch-plan closure | `blocked` | `blocked` | `B-PSM-SEQUENCE` | `NEG-H03-PSM-REDEEM-FIRST`/`NEG-H03-PSM-MINT-LAST` |
| `S-049-FALLBACK` | CM-049 | `behavioral_invariant` | no Base/local address or value fallback | `omitted` | `omitted` | none | NEG-017 |
| `S-049-ARTIFACT` | CM-049 | `artifact` | DefaultsRobinhood artifact created only by H-04 | `blocked` | `pre_activation_configuration` | `B-H04-PARAMS` | NEG-017 |
| `S-051-ARTIFACT` | CM-051 | `artifact` | GREEN CCIP pool artifact and eventual HQ row | `deferred` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | NEG-025 |
| `S-052-ARTIFACT` | CM-052 | `artifact` | RIPE CCIP pool artifact and eventual HQ row | `deferred` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | NEG-025 |
| `S-053-REGISTRATION` | CM-053 | `registration` | token-admin registration and remote configuration | `deferred` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-CCIP` | NEG-025 |
| `S-054-ADAPTER` | CM-054 | `artifact` | any future local GREEN/RIPE price adapter | `deferred` | `post_launch_release` | `B-ORACLE-FREEZE` | NEG-016/024 |
| `S-055-NO-EXECUTION` | CM-055 | `behavioral_invariant` | H-03 contains no execution, address, or default-value logic | `required` | `deployed_initial_value` | none | NEG-017 |
| `S-056-MANIFEST` | CM-056 | `artifact` | Robinhood manifest and history artifacts | `blocked` | `blocked` | `B-H05-PLAN`, `B-H09-RELEASE` | NEG-016 |
| `S-057-VERIFY` | CM-057 | `route` | Robinhood ABI export and explorer verification | `blocked` | `blocked` | `B-H09-RELEASE` | NEG-016 |
| `S-058-TOOLCHAIN` | CM-058 | `artifact` | pinned Solidity CCIP toolchain | `deferred` | `within_seven_day_separately_reviewed_ccip_promotion` | `B-T1-TOOLCHAIN` | NEG-025 |
| `S-059-DEPLOY-TIER` | CM-059 | `route` | deployment, fork, and release test tiers | `blocked` | `blocked` | `B-H08-PROOF`, `B-H09-RELEASE` | NEG-016 |

#### 7A.2.1 Canonical promotion-action inventory

This inventory contains exactly two `PromotionRecord` values. Neither is a
launch surface or alters any referenced surface disposition. The seven reward
rows remain `disabled` at `deployed_initial_value`; the six CCIP rows retain
their recorded disabled/deferred launch dispositions. Specifically,
`S-001-CCIP-CAP` and `S-002-CCIP-CAP` are disabled from launch continuously
through the CCIP-promotion checkpoint; the other four CCIP members remain
deferred. Each record preserves one distinct separately reviewed action that
may be proposed within seven days. Mechanical promotion cardinalities are two
`deferred` records: one CCIP-promotion phase referencing six surfaces and one
reward-activation phase referencing seven surfaces.

| Promotion ID | Exact surface IDs | Promotion phase | Disposition | Primary owner | Co-owners | Blockers | Assertions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P-CCIP-SEVEN-DAY` | `S-001-CCIP-CAP`/`S-002-CCIP-CAP`/`S-051-ARTIFACT`/`S-052-ARTIFACT`/`S-053-REGISTRATION`/`S-058-TOOLCHAIN` | `within_seven_day_separately_reviewed_ccip_promotion` | `deferred` | `OWN-T1` | `OWN-SECOPS` | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | NEG-025 |
| `P-REWARDS-SEVEN-DAY` | `S-003-REWARDS`/`S-013-REWARD-ACTIONS`/`S-022-REWARDS`/`S-023-REWARDS`/`S-028-REWARD-PATH`/`S-033-REWARD-MINT`/`S-033-STOCK-REWARD` | `within_seven_day_separately_reviewed_reward_activation` | `deferred` | `OWN-REWARDS` | `OWN-SECOPS`, `OWN-H04` | `B-REWARD-PROMOTION` | NEG-035/036/`NEG-H03-STOCK-REWARD-DISABLED` |

Validation requires both exact surface sets above, deferred dispositions, the
action-specific lifecycle phases, every named blocker, and the continuous
launch-disabled state of `S-001-CCIP-CAP` and `S-002-CCIP-CAP`. Deleting a
referenced launch-disabled/deferred surface, leaving either token capability
unspecified or enabled at launch, moving a reward launch state to the
reward-activation phase, cross-assigning either promotion's surfaces,
promoting only a subset, omitting a blocker, or treating elapsed time as
approval fails closed.

### 7A.3 Canonical R6 typed relation graph

Only deployment construction/bootstrap/setup/order and launch/security
relations are included. This is not a complete runtime call graph. Every row
below is one canonical relation record; no grouped row, slash expansion, or
Cartesian product exists. Its identity is the exact tuple
`(relation_id, source_component, relation_kind, relation_phase,
target_component)`. This permits a source/target pair to have both a direct
and a separately proved indirect security relation without conflation.

The graph implements approved owner decision `D-H03-005`:

1. `direct_execution` uses operational caller to callee direction.
2. `authority_dependency` points from the governed contract to the authority
   registry or controller on which its security check depends.
3. A controller points to a target only when source proves a direct call.
4. Configuration writers do not point to downstream consumers merely because
   those consumers read the resulting state.
5. Registry membership is represented by `registration_order_dependency`
   and Section 8 expectations, never by a fictitious runtime call.
6. `indirect_security_dependency` is permitted only with a complete
   multi-source proof tuple covering every hop.
7. Selected sources may point to omitted targets when the direct source route
   is required to prove launch-disabled or fail-closed behavior.

The deterministic counting method is: parse each table body row whose first
cell is an `R-*` ID; count it once; group the `Phase` and `Kind` cells; and
reject duplicate identity tuples. This yields **288 explicit
relation records**: 37 constructor,
3 bootstrap, 3
post-deployment setup, 31 registration-order,
and 214 runtime-security. Runtime-security kinds
are 165 direct execution,
39 authority dependency, and
10 indirect security dependency.
Because every row is already expanded, the grouped-row and expanded-edge
counts are both **288** when “row” means an explicit typed record; there are
no multi-edge grouped rows. Collapsing the relation kind produces 284 unique
phase-qualified source-target triples because four triples have separately
proved direct and indirect semantics.

The relation table contains **712 proof references** covering
**415 unique source ranges in 46 files**.
Full Section 7A.3, including the correction explanation and explicit no-edge
determinations, contains **735 proof references** covering **434 unique
source ranges in 62 files**.
All references were parsed with a hyphen-safe path grammar and validated
against the source file's real line count. The R4a/R4b 163/153 and 186/175
proof scopes are superseded with the rejected grouped graph.

| Relation | Source | Kind | Phase | Target | Exact source proof tuple | Semantic reason | Evidence authority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `R-001` | `CM-003` | `construction_dependency` | `constructor` | `CM-001` | `contracts/tokens/SavingsGreen.vy:32-41` | SavingsGreen takes GREEN as its ERC-4626 underlying asset. | `E-SRC`, `E-SRC-HQ` |
| `R-002` | `CM-004` | `construction_dependency` | `constructor` | `CM-001` | `contracts/registries/RipeHq.vy:100-127` | RipeHq takes and registers this canonical launch token. | `E-SRC-HQ` |
| `R-003` | `CM-004` | `construction_dependency` | `constructor` | `CM-002` | `contracts/registries/RipeHq.vy:100-127` | RipeHq takes and registers this canonical launch token. | `E-SRC-HQ` |
| `R-004` | `CM-004` | `construction_dependency` | `constructor` | `CM-003` | `contracts/registries/RipeHq.vy:100-127` | RipeHq takes and registers this canonical launch token. | `E-SRC-HQ` |
| `R-005` | `CM-006` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/TrainingWheels.vy:29-31` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-006` | `CM-008` | `construction_dependency` | `constructor` | `CM-004` | `contracts/data/Ledger.vy:187-194` | The artifact takes RipeHq at construction. | `E-SRC-HQ`, `E-S5` |
| `R-007` | `CM-008` | `construction_dependency` | `constructor` | `CM-049` | `contracts/data/Ledger.vy:187-194` | The artifact reads the chain defaults artifact at construction. | `E-H04`, `E-S5` |
| `R-008` | `CM-009` | `construction_dependency` | `constructor` | `CM-004` | `contracts/data/MissionControl.vy:218-257` | The artifact takes RipeHq at construction. | `E-SRC-HQ`, `E-S5` |
| `R-009` | `CM-009` | `construction_dependency` | `constructor` | `CM-049` | `contracts/data/MissionControl.vy:218-257` | The artifact reads the chain defaults artifact at construction. | `E-H04`, `E-S5` |
| `R-010` | `CM-010` | `construction_dependency` | `constructor` | `CM-004` | `contracts/registries/Switchboard.vy:41-50` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-011` | `CM-011` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/SwitchboardAlpha.vy:412-420` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-012` | `CM-012` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/SwitchboardBravo.vy:188-196` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-013` | `CM-013` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/SwitchboardCharlie.vy:413-421` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-014` | `CM-014` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/SwitchboardDelta.vy:458-466` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-015` | `CM-015` | `construction_dependency` | `constructor` | `CM-004` | `contracts/registries/PriceDesk.vy:62-76` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-016` | `CM-016` | `construction_dependency` | `constructor` | `CM-004` | `contracts/priceSources/ChainlinkPrices.vy:122-137` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-017` | `CM-021` | `construction_dependency` | `constructor` | `CM-004` | `contracts/registries/VaultBook.vy:50-59` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-018` | `CM-022` | `construction_dependency` | `constructor` | `CM-004` | `contracts/vaults/StabilityPool.vy:58-65` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-019` | `CM-023` | `construction_dependency` | `constructor` | `CM-004` | `contracts/vaults/RipeGov.vy:117-124` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-020` | `CM-024` | `construction_dependency` | `constructor` | `CM-004` | `contracts/vaults/SimpleErc20.vy:41-47` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-021` | `CM-026` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/AuctionHouse.vy:221-228` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-022` | `CM-027` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/AuctionHouseNFT.vy:20-24` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-023` | `CM-028` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/Boardroom.vy:20-24` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-024` | `CM-029` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/BondRoom.vy:108-115` | BondRoom initializes RipeHq. | `E-SRC` |
| `R-025` | `CM-029` | `construction_dependency` | `constructor` | `CM-038` | `contracts/core/BondRoom.vy:108-115` | BondRoom takes BondBooster. | `E-SRC` |
| `R-026` | `CM-030` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/CreditEngine.vy:190-197` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-027` | `CM-031` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/Endaoment.vy:156-164` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-028` | `CM-032` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/HumanResources.vy:131-139` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-029` | `CM-033` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/Lootbox.vy:197-205` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-030` | `CM-034` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/Teller.vy:219-226` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-031` | `CM-038` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/BondBooster.vy:55-63` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-032` | `CM-043` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/CreditRedeem.vy:115-122` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-033` | `CM-044` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/Deleverage.vy:199-206` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-034` | `CM-045` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/TellerUtils.vy:92-99` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-035` | `CM-046` | `construction_dependency` | `constructor` | `CM-004` | `contracts/config/SwitchboardEcho.vy:445-452` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-036` | `CM-047` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/EndaomentFunds.vy:38-45` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-037` | `CM-048` | `construction_dependency` | `constructor` | `CM-004` | `contracts/core/EndaomentPSM.vy:167-199` | The selected artifact initializes its RipeHq reference. | `E-SRC-HQ`, `E-SRC` |
| `R-038` | `CM-001` | `bootstrap_dependency` | `bootstrap` | `CM-004` | `contracts/tokens/modules/Erc20Token.vy:113-137` | Initial token governance requires an empty HQ and defers HQ installation. | `E-SRC-HQ` |
| `R-039` | `CM-002` | `bootstrap_dependency` | `bootstrap` | `CM-004` | `contracts/tokens/modules/Erc20Token.vy:113-137` | Initial token governance requires an empty HQ and defers HQ installation. | `E-SRC-HQ` |
| `R-040` | `CM-003` | `bootstrap_dependency` | `bootstrap` | `CM-004` | `contracts/tokens/SavingsGreen.vy:32-41`<br>`contracts/tokens/modules/Erc20Token.vy:109-137` | SavingsGreen inherits the deferred-HQ token bootstrap. | `E-SRC-HQ` |
| `R-041` | `CM-001` | `setup_dependency` | `post_deployment_setup` | `CM-004` | `contracts/tokens/modules/Erc20Token.vy:441-473` | The governed post-deployment path installs the HQ reference. | `E-SRC-HQ` |
| `R-042` | `CM-002` | `setup_dependency` | `post_deployment_setup` | `CM-004` | `contracts/tokens/modules/Erc20Token.vy:441-473` | The governed post-deployment path installs the HQ reference. | `E-SRC-HQ` |
| `R-043` | `CM-003` | `setup_dependency` | `post_deployment_setup` | `CM-004` | `contracts/tokens/modules/Erc20Token.vy:441-473` | The governed post-deployment path installs the HQ reference. | `E-SRC-HQ` |
| `R-044` | `CM-001` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:40`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-045` | `CM-002` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:42`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-046` | `CM-003` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:41`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-047` | `CM-008` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:43`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-048` | `CM-009` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:44`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-049` | `CM-010` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:45`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-050` | `CM-011` | `registration_order_dependency` | `registration_order` | `CM-010` | `migrations/base-mainnet/1006_Switchboard.py:27-28`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The exact migration row and sequential registry implementation fix this Switchboard child ID. | `E-SRC-SB`, `E-SRC-REG` |
| `R-051` | `CM-012` | `registration_order_dependency` | `registration_order` | `CM-010` | `migrations/base-mainnet/1006_Switchboard.py:37-38`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The exact migration row and sequential registry implementation fix this Switchboard child ID. | `E-SRC-SB`, `E-SRC-REG` |
| `R-052` | `CM-013` | `registration_order_dependency` | `registration_order` | `CM-010` | `migrations/base-mainnet/1006_Switchboard.py:47-48`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The exact migration row and sequential registry implementation fix this Switchboard child ID. | `E-SRC-SB`, `E-SRC-REG` |
| `R-053` | `CM-014` | `registration_order_dependency` | `registration_order` | `CM-010` | `migrations/base-mainnet/1006_Switchboard.py:57-58`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The exact migration row and sequential registry implementation fix this Switchboard child ID. | `E-SRC-SB`, `E-SRC-REG` |
| `R-054` | `CM-015` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:46`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-055` | `CM-016` | `registration_order_dependency` | `registration_order` | `CM-015` | `migrations/base-mainnet/1007_PriceDesk.py:41-42`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The migration and sequential registry implementation fix Chainlink at PriceDesk ID 1. | `E-SRC-PD`, `E-SRC-REG` |
| `R-056` | `CM-021` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:47`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-057` | `CM-022` | `registration_order_dependency` | `registration_order` | `CM-021` | `migrations/base-mainnet/1008_VaultBook.py:38-39`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The migration and sequential registry implementation fix this VaultBook row. | `E-SRC-VB`, `E-SRC-REG` |
| `R-058` | `CM-023` | `registration_order_dependency` | `registration_order` | `CM-021` | `migrations/base-mainnet/1008_VaultBook.py:41-42`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The migration and sequential registry implementation fix this VaultBook row. | `E-SRC-VB`, `E-SRC-REG` |
| `R-059` | `CM-024` | `registration_order_dependency` | `registration_order` | `CM-021` | `migrations/base-mainnet/1008_VaultBook.py:44-45`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The migration and sequential registry implementation fix this VaultBook row. | `E-SRC-VB`, `E-SRC-REG` |
| `R-060` | `CM-026` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:48`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-061` | `CM-027` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:49`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-062` | `CM-028` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:50`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-063` | `CM-029` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:51`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-064` | `CM-030` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:52`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-065` | `CM-031` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:53`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-066` | `CM-032` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:54`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-067` | `CM-033` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:55`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-068` | `CM-034` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:56`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-069` | `CM-043` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:58`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-070` | `CM-044` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:57`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-071` | `CM-045` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:59`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-072` | `CM-046` | `registration_order_dependency` | `registration_order` | `CM-010` | `migrations/base-mainnet/2025120200_New_Switchboards.py:71-72`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The exact migration row and sequential registry implementation fix this Switchboard child ID. | `E-SRC-SB`, `E-SRC-REG` |
| `R-073` | `CM-047` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:60`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-074` | `CM-048` | `registration_order_dependency` | `registration_order` | `CM-004` | `contracts/modules/Addys.vy:61`<br>`contracts/registries/RipeHq.vy:135-147`<br>`contracts/registries/modules/AddressRegistry.vy:138-139`<br>`contracts/registries/modules/AddressRegistry.vy:175-198` | The source-hard HQ ID and sequential registry semantics fix this member's HQ row. | `E-SRC-HQ`, `E-SRC-REG` |
| `R-075` | `CM-001` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/tokens/GreenToken.vy:57-64`<br>`contracts/tokens/modules/Erc20Token.vy:401-424`<br>`contracts/tokens/modules/Erc20Token.vy:441-524` | GREEN mint, blacklist, burn, and governance checks depend on RipeHq. | `E-SRC-HQ` |
| `R-076` | `CM-002` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/tokens/RipeToken.vy:57-64`<br>`contracts/tokens/modules/Erc20Token.vy:401-424`<br>`contracts/tokens/modules/Erc20Token.vy:441-524` | RIPE mint, blacklist, burn, and governance checks depend on RipeHq. | `E-SRC-HQ` |
| `R-077` | `CM-003` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/tokens/SavingsGreen.vy:32-41`<br>`contracts/tokens/modules/Erc4626Token.vy:46-116` | GREEN custody and accounting are the SavingsGreen underlying asset. | `E-M0`, `E-SRC` |
| `R-078` | `CM-003` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/tokens/SavingsGreen.vy:32-41`<br>`contracts/tokens/modules/Erc20Token.vy:401-424`<br>`contracts/tokens/modules/Erc20Token.vy:441-524` | sGREEN inherited blacklist and governance checks depend on RipeHq. | `E-SRC-HQ` |
| `R-079` | `CM-004` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/registries/RipeHq.vy:310-344`<br>`contracts/registries/VaultBook.vy:59` | RipeHq directly validates VaultBook's RIPE-mint capability. | `E-SRC-HQ`, `E-M0` |
| `R-080` | `CM-004` | `direct_execution` | `runtime_security` | `CM-026` | `contracts/registries/RipeHq.vy:310-344`<br>`contracts/core/AuctionHouse.vy:223` | RipeHq directly validates AuctionHouse's GREEN-mint capability. | `E-SRC-HQ`, `E-M0` |
| `R-081` | `CM-004` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/registries/RipeHq.vy:310-344`<br>`contracts/core/CreditEngine.vy:192` | RipeHq directly validates CreditEngine's GREEN-mint capability. | `E-SRC-HQ`, `E-M0` |
| `R-082` | `CM-004` | `direct_execution` | `runtime_security` | `CM-031` | `contracts/registries/RipeHq.vy:310-344`<br>`contracts/core/Endaoment.vy:158` | RipeHq directly validates Endaoment's GREEN-mint capability. | `E-SRC-HQ`, `E-M0` |
| `R-083` | `CM-004` | `direct_execution` | `runtime_security` | `CM-048` | `contracts/registries/RipeHq.vy:310-344`<br>`contracts/core/EndaomentPSM.vy:179` | RipeHq directly validates the PSM's GREEN-mint capability. | `E-SRC-HQ`, `E-M0` |
| `R-084` | `CM-006` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/config/TrainingWheels.vy:29-31`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-085` | `CM-008` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/data/Ledger.vy:187-194`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-086` | `CM-009` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/data/MissionControl.vy:725-793` | MissionControl resolves liquidation vault data through VaultBook; the special StabilityPool binding remains unresolved. | `E-H04`, `E-SRC-VB` |
| `R-087` | `CM-009` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/data/MissionControl.vy:218-220`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-088` | `CM-010` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/registries/Switchboard.vy:120-139`<br>`contracts/tokens/modules/Erc20Token.vy:401-410` | Switchboard directly dispatches the token blacklist setter implemented by GREEN. | `E-SRC-HQ`, `E-H04` |
| `R-089` | `CM-010` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/registries/Switchboard.vy:120-139`<br>`contracts/tokens/modules/Erc20Token.vy:401-410` | Switchboard directly dispatches the token blacklist setter implemented by RIPE. | `E-SRC-HQ`, `E-H04` |
| `R-090` | `CM-010` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/registries/Switchboard.vy:120-139`<br>`contracts/tokens/modules/Erc20Token.vy:401-410` | Switchboard directly dispatches the token blacklist setter inherited by sGREEN. | `E-SRC-HQ`, `E-H04` |
| `R-091` | `CM-010` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/registries/Switchboard.vy:41-50`<br>`contracts/modules/LocalGov.vy:139-158` | Switchboard LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-092` | `CM-011` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/config/SwitchboardAlpha.vy:623-676`<br>`contracts/config/SwitchboardAlpha.vy:728-1055`<br>`contracts/config/SwitchboardAlpha.vy:1191-1264`<br>`contracts/config/SwitchboardAlpha.vy:1340-1595` | Alpha directly reads and writes launch-critical MissionControl policy. | `E-H04`, `E-M0` |
| `R-093` | `CM-011` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/config/SwitchboardAlpha.vy:463-481`<br>`contracts/config/SwitchboardAlpha.vy:1302-1322` | Alpha directly validates PriceDesk rows and resolves price sources. | `E-SRC-PD`, `E-H04` |
| `R-094` | `CM-011` | `direct_execution` | `runtime_security` | `CM-016` | `contracts/config/SwitchboardAlpha.vy:1319-1322`<br>`migrations/base-mainnet/1007_PriceDesk.py:41-42`<br>`contracts/priceSources/ChainlinkPrices.vy:243-245` | Alpha's snapshot call resolves to the selected Chainlink PriceDesk row. | `E-SRC-PD`, `E-H04` |
| `R-095` | `CM-011` | `direct_execution` | `runtime_security` | `CM-019` | `contracts/config/SwitchboardAlpha.vy:475-481`<br>`contracts/config/SwitchboardAlpha.vy:1545`<br>`migrations/base-mainnet/1007_PriceDesk.py:82-83` | The retained Pyth configuration call proves the omitted route must fail closed. | `E-SRC-PD`, `E-H04` |
| `R-096` | `CM-011` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/config/SwitchboardAlpha.vy:469`<br>`contracts/config/SwitchboardAlpha.vy:1262-1264` | Alpha directly validates VaultBook IDs used in priority configuration. | `E-SRC-VB`, `E-H04` |
| `R-097` | `CM-011` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/config/SwitchboardAlpha.vy:475`<br>`contracts/config/SwitchboardAlpha.vy:1535-1540` | Alpha directly configures CreditEngine dynamic debt parameters. | `E-H04`, `E-T8` |
| `R-098` | `CM-011` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/config/SwitchboardAlpha.vy:412-420`<br>`contracts/modules/LocalGov.vy:139-158` | Alpha LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-099` | `CM-012` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/config/SwitchboardBravo.vy:249`<br>`contracts/config/SwitchboardBravo.vy:361-516`<br>`contracts/config/SwitchboardBravo.vy:751-793` | Bravo directly validates and writes MissionControl asset/liquidation configuration. | `E-H04`, `E-T8` |
| `R-100` | `CM-012` | `direct_execution` | `runtime_security` | `CM-010` | `contracts/config/SwitchboardBravo.vy:490-492` | Bravo directly resolves the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-101` | `CM-012` | `direct_execution` | `runtime_security` | `CM-011` | `contracts/config/SwitchboardBravo.vy:490-492` | Bravo directly asks Alpha to validate auction parameters. | `E-SRC-SB`, `E-H04` |
| `R-102` | `CM-012` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/config/SwitchboardBravo.vy:377-389`<br>`contracts/config/SwitchboardBravo.vy:449-481` | Bravo directly validates configured vault IDs through VaultBook. | `E-SRC-VB`, `E-H04` |
| `R-103` | `CM-012` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/config/SwitchboardBravo.vy:188-196`<br>`contracts/modules/LocalGov.vy:139-158` | Bravo LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-104` | `CM-013` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/config/SwitchboardCharlie.vy:482`<br>`contracts/config/SwitchboardCharlie.vy:574` | Charlie directly applies Ledger account locks. | `E-S3`, `E-H04` |
| `R-105` | `CM-013` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/config/SwitchboardCharlie.vy:432-448`<br>`contracts/config/SwitchboardCharlie.vy:1034-1082`<br>`contracts/config/SwitchboardCharlie.vy:1144-1179` | Charlie directly reads and writes MissionControl control and reward policy. | `E-H04`, `E-S3` |
| `R-106` | `CM-013` | `direct_execution` | `runtime_security` | `CM-010` | `contracts/config/SwitchboardCharlie.vy:563-564` | Charlie directly dispatches blacklist changes through Switchboard. | `E-SRC-SB`, `E-H04` |
| `R-107` | `CM-013` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/config/SwitchboardCharlie.vy:476`<br>`contracts/config/SwitchboardCharlie.vy:724-741` | Charlie directly resolves vault identities through VaultBook for reward updates. | `E-SRC-VB`, `E-S3` |
| `R-108` | `CM-013` | `direct_execution` | `runtime_security` | `CM-026` | `contracts/config/SwitchboardCharlie.vy:442`<br>`contracts/config/SwitchboardCharlie.vy:762-791`<br>`contracts/config/SwitchboardCharlie.vy:1015-1030` | Charlie directly validates, starts, and pauses AuctionHouse auctions. | `E-H04`, `E-T8` |
| `R-109` | `CM-013` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/config/SwitchboardCharlie.vy:464`<br>`contracts/config/SwitchboardCharlie.vy:589-601` | Charlie directly refreshes CreditEngine debt. | `E-H04`, `E-T8` |
| `R-110` | `CM-013` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/config/SwitchboardCharlie.vy:470`<br>`contracts/config/SwitchboardCharlie.vy:617-741`<br>`contracts/config/SwitchboardCharlie.vy:1056-1066` | Charlie directly executes the launch-disabled Lootbox reward actions. | `E-S3`, `E-M0` |
| `R-111` | `CM-013` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/config/SwitchboardCharlie.vy:413-421`<br>`contracts/modules/LocalGov.vy:139-158` | Charlie LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-112` | `CM-014` | `direct_execution` | `runtime_security` | `CM-005` | `contracts/config/SwitchboardDelta.vy:808-832`<br>`contracts/config/SwitchboardDelta.vy:1271-1276` | Delta directly calls the omitted Contributor artifact family; disabled HR actions must fail closed. | `E-H04`, `E-M0` |
| `R-113` | `CM-014` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/config/SwitchboardDelta.vy:503`<br>`contracts/config/SwitchboardDelta.vy:777-793`<br>`contracts/config/SwitchboardDelta.vy:1300`<br>`contracts/config/SwitchboardDelta.vy:1343-1353` | Delta directly validates and writes Ledger HR, debt, and allocation state. | `E-H04`, `E-S5` |
| `R-114` | `CM-014` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/config/SwitchboardDelta.vy:477-487`<br>`contracts/config/SwitchboardDelta.vy:928-931`<br>`contracts/config/SwitchboardDelta.vy:1235-1295`<br>`contracts/config/SwitchboardDelta.vy:1358-1363` | Delta directly reads and writes MissionControl HR, bond, and Underscore policy. | `E-H04`, `E-M0` |
| `R-115` | `CM-014` | `direct_execution` | `runtime_security` | `CM-029` | `contracts/config/SwitchboardDelta.vy:515`<br>`contracts/config/SwitchboardDelta.vy:917`<br>`contracts/config/SwitchboardDelta.vy:1127-1166`<br>`contracts/config/SwitchboardDelta.vy:1305-1317` | Delta directly controls BondRoom epochs and booster binding. | `E-H04`, `E-M0` |
| `R-116` | `CM-014` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/config/SwitchboardDelta.vy:521`<br>`contracts/config/SwitchboardDelta.vy:1324-1338` | Delta directly resets Lootbox point state. | `E-S3`, `E-H04` |
| `R-117` | `CM-014` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/config/SwitchboardDelta.vy:509`<br>`contracts/config/SwitchboardDelta.vy:538-550` | Delta directly routes deleverage execution through Teller. | `E-S4`, `E-H04` |
| `R-118` | `CM-014` | `direct_execution` | `runtime_security` | `CM-038` | `contracts/config/SwitchboardDelta.vy:1088`<br>`contracts/config/SwitchboardDelta.vy:1127-1166`<br>`contracts/config/SwitchboardDelta.vy:1310-1317` | Delta directly validates and configures BondBooster. | `E-H04`, `E-M0` |
| `R-119` | `CM-014` | `direct_execution` | `runtime_security` | `CM-044` | `contracts/config/SwitchboardDelta.vy:527`<br>`contracts/config/SwitchboardDelta.vy:556`<br>`contracts/config/SwitchboardDelta.vy:1368-1383` | Delta directly invokes and configures Deleverage. | `E-S4`, `E-H04` |
| `R-120` | `CM-014` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/config/SwitchboardDelta.vy:458-466`<br>`contracts/modules/LocalGov.vy:139-158` | Delta LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-121` | `CM-015` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/registries/PriceDesk.vy:86-151`<br>`contracts/registries/PriceDesk.vy:333-336` | PriceDesk directly obtains global price and external-registry policy from MissionControl. | `E-SRC-PD`, `E-H04` |
| `R-122` | `CM-015` | `direct_execution` | `runtime_security` | `CM-016` | `contracts/registries/PriceDesk.vy:178-230`<br>`contracts/registries/PriceDesk.vy:313-324`<br>`migrations/base-mainnet/1007_PriceDesk.py:41-42` | PriceDesk directly calls the selected Chainlink source for valuation and snapshots. | `E-SRC-PD`, `E-M0` |
| `R-123` | `CM-015` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/registries/PriceDesk.vy:62-76`<br>`contracts/modules/LocalGov.vy:139-158` | PriceDesk LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-124` | `CM-015` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/registries/PriceDesk.vy:62-76`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-125` | `CM-016` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/priceSources/ChainlinkPrices.vy:261-291`<br>`contracts/priceSources/ChainlinkPrices.vy:526-528` | Chainlink directly obtains the configured stale-time policy from MissionControl. | `E-SRC-PD`, `E-H04` |
| `R-126` | `CM-016` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/priceSources/ChainlinkPrices.vy:122-137`<br>`contracts/modules/LocalGov.vy:139-158` | ChainlinkPrices LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-127` | `CM-021` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/registries/VaultBook.vy:161` | VaultBook directly mints RIPE for StabilityPool claims. | `E-SRC-VB`, `E-M0` |
| `R-128` | `CM-021` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/registries/VaultBook.vy:162` | VaultBook directly decrements Ledger reward accounting after a StabilityPool claim. | `E-SRC-VB`, `E-S5` |
| `R-129` | `CM-021` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/registries/VaultBook.vy:147`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | VaultBook directly checks the selected StabilityPool before disabling its row. | `E-SRC-VB`, `E-M0` |
| `R-130` | `CM-021` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/registries/VaultBook.vy:147`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | VaultBook directly checks the selected RipeGov vault before disabling its row. | `E-SRC-VB`, `E-M0` |
| `R-131` | `CM-021` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/registries/VaultBook.vy:147`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | VaultBook directly checks the selected SimpleErc20 vault before disabling its row. | `E-SRC-VB`, `E-M0` |
| `R-132` | `CM-021` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/registries/VaultBook.vy:50-59`<br>`contracts/modules/LocalGov.vy:139-158` | VaultBook LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-133` | `CM-021` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/registries/VaultBook.vy:50-59`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-134` | `CM-022` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:265-313`<br>`contracts/vaults/modules/StabVault.vy:465-510`<br>`contracts/vaults/modules/StabVault.vy:936-973` | StabilityPool directly values, burns, deposits, and transfers GREEN. | `E-M0`, `E-SRC` |
| `R-135` | `CM-022` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:747-757` | StabilityPool directly handles RIPE approval and staking after reward minting. | `E-M0`, `E-SRC-VB` |
| `R-136` | `CM-022` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:265-313`<br>`contracts/vaults/modules/StabVault.vy:465-478`<br>`contracts/vaults/modules/StabVault.vy:936-970` | StabilityPool directly values and redeems sGREEN. | `E-M0`, `E-SRC` |
| `R-137` | `CM-022` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:747-752` | StabilityPool directly reads Ledger reward availability. | `E-S5`, `E-M0` |
| `R-138` | `CM-022` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:602-624`<br>`contracts/vaults/modules/StabVault.vy:860-866`<br>`contracts/vaults/modules/StabVault.vy:989-1011` | StabilityPool directly consumes MissionControl claims, redemption, and deposit policy. | `E-H04`, `E-M0` |
| `R-139` | `CM-022` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:265-313` | StabilityPool directly calls PriceDesk for non-GREEN valuation. | `E-SRC-PD`, `E-M0` |
| `R-140` | `CM-022` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:747-752` | StabilityPool directly asks VaultBook to mint and account RIPE claim rewards. | `E-SRC-VB`, `E-M0` |
| `R-141` | `CM-022` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/vaults/StabilityPool.vy:25-27`<br>`contracts/vaults/modules/StabVault.vy:651`<br>`contracts/vaults/modules/StabVault.vy:755-756`<br>`contracts/vaults/modules/StabVault.vy:866`<br>`contracts/vaults/modules/StabVault.vy:993-994` | StabilityPool directly uses Teller authorization and trusted-deposit routes. | `E-M1`, `E-M0` |
| `R-142` | `CM-022` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/vaults/StabilityPool.vy:58-65`<br>`contracts/vaults/modules/VaultData.vy:270-288`<br>`contracts/modules/Addys.vy:175-189` | Vault pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-SRC-VB` |
| `R-143` | `CM-022` | `indirect_security_dependency` | `runtime_security` | `CM-023` | `contracts/vaults/modules/StabVault.vy:747-756`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | StabilityPool routes RIPE rewards through Teller to the hard-coded RipeGov vault. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-144` | `CM-023` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/vaults/RipeGov.vy:131-176`<br>`contracts/vaults/RipeGov.vy:325-392` | RipeGov directly custodies and accounts the canonical RIPE token. | `E-M0`, `E-SRC-VB` |
| `R-145` | `CM-023` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/vaults/RipeGov.vy:223-286`<br>`contracts/vaults/RipeGov.vy:562-563` | RipeGov directly checks Ledger bad debt. | `E-S5`, `E-M0` |
| `R-146` | `CM-023` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/vaults/RipeGov.vy:172`<br>`contracts/vaults/RipeGov.vy:259`<br>`contracts/vaults/RipeGov.vy:335`<br>`contracts/vaults/RipeGov.vy:383`<br>`contracts/vaults/RipeGov.vy:494`<br>`contracts/vaults/RipeGov.vy:562` | RipeGov directly consumes MissionControl governance-vault policy. | `E-H04`, `E-M0` |
| `R-147` | `CM-023` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/vaults/RipeGov.vy:537-538`<br>`contracts/vaults/RipeGov.vy:576-577` | RipeGov directly resolves its VaultBook identity. | `E-SRC-VB`, `E-M0` |
| `R-148` | `CM-023` | `direct_execution` | `runtime_security` | `CM-028` | `contracts/vaults/RipeGov.vy:465-485` | RipeGov directly updates Boardroom governance power. | `E-M0`, `E-SRC` |
| `R-149` | `CM-023` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/vaults/RipeGov.vy:537-538`<br>`contracts/vaults/RipeGov.vy:576-577` | RipeGov directly updates Lootbox deposit points. | `E-S3`, `E-M0` |
| `R-150` | `CM-023` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/vaults/RipeGov.vy:117-124`<br>`contracts/vaults/modules/VaultData.vy:270-288`<br>`contracts/modules/Addys.vy:175-189` | Vault pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-SRC-VB` |
| `R-151` | `CM-024` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/vaults/SimpleErc20.vy:41-47`<br>`contracts/vaults/modules/VaultData.vy:270-288`<br>`contracts/modules/Addys.vy:175-189` | Vault pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-SRC-VB` |
| `R-152` | `CM-026` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/AuctionHouse.vy:1022-1159`<br>`contracts/core/AuctionHouse.vy:1265-1280` | AuctionHouse directly settles and mints/burns GREEN. | `E-M0`, `E-T8` |
| `R-153` | `CM-026` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/AuctionHouse.vy:687`<br>`contracts/core/AuctionHouse.vy:1244-1277` | AuctionHouse directly values and pays auction proceeds in sGREEN when selected. | `E-M0`, `E-T8` |
| `R-154` | `CM-026` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/AuctionHouse.vy:443-455`<br>`contracts/core/AuctionHouse.vy:856-999`<br>`contracts/core/AuctionHouse.vy:1095-1148`<br>`contracts/core/AuctionHouse.vy:1220` | AuctionHouse directly reads and writes Ledger liquidation and auction accounting. | `E-S5`, `E-T8` |
| `R-155` | `CM-026` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/AuctionHouse.vy:243-268`<br>`contracts/core/AuctionHouse.vy:823-836`<br>`contracts/core/AuctionHouse.vy:1104` | AuctionHouse directly consumes MissionControl liquidation and auction policy. | `E-H04`, `E-T8` |
| `R-156` | `CM-026` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/AuctionHouse.vy:687-689`<br>`contracts/core/AuctionHouse.vy:1244-1246` | AuctionHouse directly calls PriceDesk for liquidation and purchase valuation. | `E-SRC-PD`, `E-T8` |
| `R-157` | `CM-026` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/AuctionHouse.vy:883-888`<br>`contracts/core/AuctionHouse.vy:1123`<br>`contracts/core/AuctionHouse.vy:1401` | AuctionHouse directly resolves collateral vaults through VaultBook. | `E-SRC-VB`, `E-T8` |
| `R-158` | `CM-026` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/AuctionHouse.vy:645-755`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | AuctionHouse directly calls the selected StabilityPool for liquidation swaps. | `E-M0`, `E-SRC-VB` |
| `R-159` | `CM-026` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/AuctionHouse.vy:414`<br>`contracts/core/AuctionHouse.vy:496-510`<br>`contracts/core/AuctionHouse.vy:1193-1225`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | AuctionHouse's direct generic vault calls cover the selected RipeGov row. | `E-M0`, `E-SRC-VB` |
| `R-160` | `CM-026` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/AuctionHouse.vy:414`<br>`contracts/core/AuctionHouse.vy:496-510`<br>`contracts/core/AuctionHouse.vy:1193-1225`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | AuctionHouse's direct generic vault calls cover the selected SimpleErc20 row. | `E-M0`, `E-SRC-VB` |
| `R-161` | `CM-026` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/core/AuctionHouse.vy:300-370`<br>`contracts/core/AuctionHouse.vy:1142-1144` | AuctionHouse directly reduces debt through CreditEngine. | `E-T8`, `E-M1` |
| `R-162` | `CM-026` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/core/AuctionHouse.vy:1220-1221` | AuctionHouse directly updates Lootbox points after internal vault transfers. | `E-S3`, `E-T8` |
| `R-163` | `CM-026` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/AuctionHouse.vy:1110` | AuctionHouse directly uses Teller's delegated-user authorization. | `E-M1`, `E-T8` |
| `R-164` | `CM-026` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/AuctionHouse.vy:221-228`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-165` | `CM-026` | `indirect_security_dependency` | `runtime_security` | `CM-047` | `contracts/core/AuctionHouse.vy:645-755`<br>`contracts/vaults/modules/StabVault.vy:445-478`<br>`contracts/modules/Addys.vy:452-465`<br>`contracts/core/EndaomentFunds.vy:50-70` | AuctionHouse resolves EndaomentFunds, passes it through StabilityPool settlement, and the pool transfers non-GREEN proceeds into that custody target. | `E-M0`, `E-SRC` |
| `R-166` | `CM-027` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/AuctionHouseNFT.vy:20-24`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-167` | `CM-028` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/Boardroom.vy:20-24`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-168` | `CM-029` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/core/BondRoom.vy:217-226` | BondRoom directly mints and handles canonical RIPE bond payouts. | `E-M0`, `E-H04` |
| `R-169` | `CM-029` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/BondRoom.vy:154`<br>`contracts/core/BondRoom.vy:211-214`<br>`contracts/core/BondRoom.vy:238`<br>`contracts/core/BondRoom.vy:276-289` | BondRoom directly reads and writes Ledger bond and bad-debt accounting. | `E-S5`, `E-H04` |
| `R-170` | `CM-029` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/BondRoom.vy:137`<br>`contracts/core/BondRoom.vy:276`<br>`contracts/core/BondRoom.vy:331`<br>`contracts/core/BondRoom.vy:366-380` | BondRoom directly consumes MissionControl bond policy. | `E-H04`, `E-M0` |
| `R-171` | `CM-029` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/BondRoom.vy:205` | BondRoom directly values bond payments through PriceDesk. | `E-SRC-PD`, `E-H04` |
| `R-172` | `CM-029` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/BondRoom.vy:145`<br>`contracts/core/BondRoom.vy:221-224` | BondRoom directly uses Teller authorization and trusted staking. | `E-M1`, `E-M0` |
| `R-173` | `CM-029` | `direct_execution` | `runtime_security` | `CM-038` | `contracts/core/BondRoom.vy:176-183`<br>`contracts/core/BondRoom.vy:322` | BondRoom directly reads and updates BondBooster terms and units. | `E-H04`, `E-M0` |
| `R-174` | `CM-029` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/BondRoom.vy:108-115`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-175` | `CM-029` | `indirect_security_dependency` | `runtime_security` | `CM-023` | `contracts/core/BondRoom.vy:217-224`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | BondRoom routes RIPE bond payouts through Teller to the hard-coded RipeGov vault. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-176` | `CM-029` | `indirect_security_dependency` | `runtime_security` | `CM-047` | `contracts/core/BondRoom.vy:205-224`<br>`contracts/modules/Addys.vy:452-465`<br>`contracts/core/EndaomentFunds.vy:50-70` | BondRoom resolves EndaomentFunds and transfers bond-payment assets into that custody target. | `E-M0`, `E-SRC` |
| `R-177` | `CM-030` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/CreditEngine.vy:266-299`<br>`contracts/core/CreditEngine.vy:567-572` | CreditEngine directly mints, transfers, and burns GREEN for debt accounting. | `E-T8`, `E-M0` |
| `R-178` | `CM-030` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/CreditEngine.vy:1189-1211` | CreditEngine directly wraps GREEN into sGREEN for repayment refunds. | `E-M0`, `E-M1` |
| `R-179` | `CM-030` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/CreditEngine.vy:222-272`<br>`contracts/core/CreditEngine.vy:377-567`<br>`contracts/core/CreditEngine.vy:658-869`<br>`contracts/core/CreditEngine.vy:1142-1170`<br>`contracts/core/CreditEngine.vy:1233` | CreditEngine directly reads and writes Ledger debt and vault participation. | `E-S5`, `E-T8` |
| `R-180` | `CM-030` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/CreditEngine.vy:236-240`<br>`contracts/core/CreditEngine.vy:387`<br>`contracts/core/CreditEngine.vy:599-604`<br>`contracts/core/CreditEngine.vy:734`<br>`contracts/core/CreditEngine.vy:1055`<br>`contracts/core/CreditEngine.vy:1247` | CreditEngine directly consumes MissionControl borrow, repay, debt, and rate policy. | `E-H04`, `E-T8` |
| `R-181` | `CM-030` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/CreditEngine.vy:741`<br>`contracts/core/CreditEngine.vy:1253` | CreditEngine directly calls PriceDesk for collateral valuation. | `E-SRC-PD`, `E-T8` |
| `R-182` | `CM-030` | `direct_execution` | `runtime_security` | `CM-017` | `contracts/core/CreditEngine.vy:1047-1055` | CreditEngine's retained dynamic-rate route directly calls omitted CurvePrices and must fail closed. | `E-SRC-PD`, `E-M0` |
| `R-183` | `CM-030` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/CreditEngine.vy:717-729`<br>`contracts/core/CreditEngine.vy:1230-1253` | CreditEngine directly resolves collateral vaults through VaultBook. | `E-SRC-VB`, `E-T8` |
| `R-184` | `CM-030` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/CreditEngine.vy:717-741`<br>`contracts/core/CreditEngine.vy:1169-1174`<br>`contracts/core/CreditEngine.vy:1230-1253`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | CreditEngine's direct generic vault calls cover the selected StabilityPool row. | `E-SRC-VB`, `E-T8` |
| `R-185` | `CM-030` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/CreditEngine.vy:717-741`<br>`contracts/core/CreditEngine.vy:1169-1174`<br>`contracts/core/CreditEngine.vy:1230-1253`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | CreditEngine's direct generic vault calls cover the selected RipeGov row. | `E-SRC-VB`, `E-T8` |
| `R-186` | `CM-030` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/CreditEngine.vy:717-741`<br>`contracts/core/CreditEngine.vy:1169-1174`<br>`contracts/core/CreditEngine.vy:1230-1253`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | CreditEngine's direct generic vault calls cover the selected SimpleErc20 row. | `E-SRC-VB`, `E-T8` |
| `R-187` | `CM-030` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/core/CreditEngine.vy:269`<br>`contracts/core/CreditEngine.vy:568`<br>`contracts/core/CreditEngine.vy:1145`<br>`contracts/core/CreditEngine.vy:1171` | CreditEngine directly updates Lootbox borrow and deposit points. | `E-S3`, `E-T8` |
| `R-188` | `CM-030` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/CreditEngine.vy:240`<br>`contracts/core/CreditEngine.vy:604`<br>`contracts/core/CreditEngine.vy:1206-1208` | CreditEngine directly uses Teller authorization and trusted StabilityPool staking. | `E-M1`, `E-T8` |
| `R-189` | `CM-030` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/core/CreditEngine.vy:285-294` | CreditEngine governance-proceeds routing depends on RipeHq governance. | `E-SRC-HQ` |
| `R-190` | `CM-030` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/CreditEngine.vy:190-197`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-191` | `CM-030` | `indirect_security_dependency` | `runtime_security` | `CM-022` | `contracts/core/CreditEngine.vy:1189-1208`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | CreditEngine routes sGREEN repayment refunds through Teller to the hard-coded StabilityPool. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-192` | `CM-031` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/Endaoment.vy:747-780`<br>`contracts/core/Endaoment.vy:983-1093`<br>`contracts/core/Endaoment.vy:1176-1188` | Endaoment directly mints, burns, and transfers GREEN in retained stabilization paths. | `E-M0`, `E-H04` |
| `R-193` | `CM-031` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/Endaoment.vy:747-780`<br>`contracts/core/Endaoment.vy:848-937`<br>`contracts/core/Endaoment.vy:1033`<br>`contracts/core/Endaoment.vy:1084-1093`<br>`contracts/core/Endaoment.vy:1176-1188` | Endaoment directly reads and writes Ledger pool-debt accounting. | `E-S5`, `E-H04` |
| `R-194` | `CM-031` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/Endaoment.vy:1131-1134` | Endaoment directly reads MissionControl's disabled external-integration registry. | `E-H04`, `E-M0` |
| `R-195` | `CM-031` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/Endaoment.vy:187-191`<br>`contracts/core/Endaoment.vy:231-268`<br>`contracts/core/Endaoment.vy:552-584`<br>`contracts/core/Endaoment.vy:1057` | Endaoment directly values transfers and partner liquidity through PriceDesk. | `E-SRC-PD`, `E-H04` |
| `R-196` | `CM-031` | `direct_execution` | `runtime_security` | `CM-017` | `contracts/core/Endaoment.vy:749-750`<br>`contracts/core/Endaoment.vy:848-849`<br>`contracts/core/Endaoment.vy:916-917`<br>`contracts/core/Endaoment.vy:933-934` | Endaoment's retained stabilizer route directly calls omitted CurvePrices and must remain disabled. | `E-SRC-PD`, `E-M0` |
| `R-197` | `CM-031` | `direct_execution` | `runtime_security` | `CM-047` | `contracts/core/Endaoment.vy:1109-1111` | Endaoment directly calls EndaomentFunds custody release. | `E-M0`, `E-SRC` |
| `R-198` | `CM-031` | `direct_execution` | `runtime_security` | `CM-048` | `contracts/core/Endaoment.vy:249-268` | Endaoment directly resolves and transfers reserve assets to the PSM. | `E-M0`, `E-H04` |
| `R-199` | `CM-031` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/core/Endaoment.vy:182-191`<br>`contracts/core/Endaoment.vy:249-268` | Endaoment governance authorization and recipient routing depend on RipeHq. | `E-SRC-HQ` |
| `R-200` | `CM-031` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/Endaoment.vy:156-164`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-201` | `CM-032` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/core/HumanResources.vy:419-451` | HumanResources directly mints, stakes, and burns RIPE in retained disabled compensation paths. | `E-M0`, `E-H04` |
| `R-202` | `CM-032` | `direct_execution` | `runtime_security` | `CM-005` | `contracts/core/HumanResources.vy:208-234`<br>`contracts/core/HumanResources.vy:462-492` | HumanResources directly creates and queries the omitted Contributor artifact family; the disabled route must fail closed. | `E-H04`, `E-M0` |
| `R-203` | `CM-032` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/HumanResources.vy:175-234`<br>`contracts/core/HumanResources.vy:314-331`<br>`contracts/core/HumanResources.vy:389-492` | HumanResources directly reads and writes Ledger compensation and vault state. | `E-S5`, `E-H04` |
| `R-204` | `CM-032` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/HumanResources.vy:175-208`<br>`contracts/core/HumanResources.vy:314` | HumanResources directly consumes MissionControl HR policy. | `E-H04`, `E-M0` |
| `R-205` | `CM-032` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/HumanResources.vy:389-405`<br>`contracts/core/HumanResources.vy:447-448` | HumanResources directly resolves the RipeGov vault through VaultBook. | `E-SRC-VB`, `E-H04` |
| `R-206` | `CM-032` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/HumanResources.vy:389-405`<br>`contracts/core/HumanResources.vy:447-448` | HumanResources directly transfers contributor balances through the selected RipeGov vault. | `E-M0`, `E-H04` |
| `R-207` | `CM-032` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/core/HumanResources.vy:404-408` | HumanResources directly updates Lootbox points for transferred contributor balances. | `E-S3`, `E-H04` |
| `R-208` | `CM-032` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/HumanResources.vy:419-427` | HumanResources directly uses Teller's trusted RIPE staking route. | `E-M1`, `E-H04` |
| `R-209` | `CM-032` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/core/HumanResources.vy:131-139`<br>`contracts/modules/LocalGov.vy:139-158` | HumanResources LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-210` | `CM-032` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/HumanResources.vy:131-139`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-211` | `CM-032` | `indirect_security_dependency` | `runtime_security` | `CM-023` | `contracts/core/HumanResources.vy:419-427`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | HumanResources routes RIPE compensation through Teller to the hard-coded RipeGov vault. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-212` | `CM-033` | `direct_execution` | `runtime_security` | `CM-002` | `contracts/core/Lootbox.vy:1086-1166`<br>`contracts/core/Lootbox.vy:1217-1262` | Lootbox directly mints and transfers RIPE rewards. | `E-S3`, `E-M0` |
| `R-213` | `CM-033` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/Lootbox.vy:285-397`<br>`contracts/core/Lootbox.vy:574-648`<br>`contracts/core/Lootbox.vy:782-894`<br>`contracts/core/Lootbox.vy:957-1075`<br>`contracts/core/Lootbox.vy:1093-1262` | Lootbox directly reads and writes Ledger reward and point accounting. | `E-S3`, `E-S5` |
| `R-214` | `CM-033` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/Lootbox.vy:272-278`<br>`contracts/core/Lootbox.vy:375-418`<br>`contracts/core/Lootbox.vy:574-648`<br>`contracts/core/Lootbox.vy:767-788`<br>`contracts/core/Lootbox.vy:864-883`<br>`contracts/core/Lootbox.vy:994-1018`<br>`contracts/core/Lootbox.vy:1073-1093`<br>`contracts/core/Lootbox.vy:1217-1220` | Lootbox directly consumes MissionControl reward policy. | `E-S3`, `E-H04` |
| `R-215` | `CM-033` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/Lootbox.vy:812-844` | Lootbox directly calls PriceDesk for reward valuation. | `E-SRC-PD`, `E-S3` |
| `R-216` | `CM-033` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/Lootbox.vy:285-372`<br>`contracts/core/Lootbox.vy:468`<br>`contracts/core/Lootbox.vy:599-629`<br>`contracts/core/Lootbox.vy:768` | Lootbox directly resolves reward-bearing vaults through VaultBook. | `E-SRC-VB`, `E-S3` |
| `R-217` | `CM-033` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/Lootbox.vy:285-372`<br>`contracts/core/Lootbox.vy:468-648`<br>`contracts/core/Lootbox.vy:767-833`<br>`contracts/core/Lootbox.vy:1182`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | Lootbox's direct generic vault calls cover the selected StabilityPool row. | `E-SRC-VB`, `E-S3` |
| `R-218` | `CM-033` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/Lootbox.vy:285-372`<br>`contracts/core/Lootbox.vy:468-648`<br>`contracts/core/Lootbox.vy:767-833`<br>`contracts/core/Lootbox.vy:1182`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | Lootbox's direct generic vault calls cover the selected RipeGov row. | `E-SRC-VB`, `E-S3` |
| `R-219` | `CM-033` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/Lootbox.vy:285-372`<br>`contracts/core/Lootbox.vy:468-648`<br>`contracts/core/Lootbox.vy:767-833`<br>`contracts/core/Lootbox.vy:1182`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | Lootbox's direct generic vault calls cover the selected SimpleErc20 row. | `E-SRC-VB`, `E-S3` |
| `R-220` | `CM-033` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/Lootbox.vy:272-278`<br>`contracts/core/Lootbox.vy:1159-1161` | Lootbox directly uses Teller authorization and trusted RIPE staking. | `E-M1`, `E-S3` |
| `R-221` | `CM-033` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/Lootbox.vy:197-205`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-222` | `CM-033` | `indirect_security_dependency` | `runtime_security` | `CM-023` | `contracts/core/Lootbox.vy:1144-1161`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | Lootbox routes staked RIPE rewards through Teller to the hard-coded RipeGov vault. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-223` | `CM-034` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/Teller.vy:633-640`<br>`contracts/core/Teller.vy:1027-1038` | Teller directly transfers and wraps GREEN. | `E-M0`, `E-M1` |
| `R-224` | `CM-034` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/Teller.vy:633-640`<br>`contracts/core/Teller.vy:1027-1034` | Teller directly transfers and redeems sGREEN. | `E-M0`, `E-M1` |
| `R-225` | `CM-034` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/Teller.vy:291-308`<br>`contracts/core/Teller.vy:997` | Teller directly updates Ledger custody participation and last-touch accounting. | `E-S5`, `E-M1` |
| `R-226` | `CM-034` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/Teller.vy:369-373`<br>`contracts/core/Teller.vy:890-937`<br>`contracts/core/Teller.vy:994-995` | Teller directly consumes and writes MissionControl route and user policy. | `E-H04`, `E-M1` |
| `R-227` | `CM-034` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/Teller.vy:318`<br>`contracts/core/Teller.vy:388`<br>`contracts/core/Teller.vy:1000-1002` | Teller directly updates PriceDesk snapshots and resolves the fail-closed Curve row. | `E-SRC-PD`, `E-M1` |
| `R-228` | `CM-034` | `direct_execution` | `runtime_security` | `CM-017` | `contracts/core/Teller.vy:1000-1002` | Teller's retained snapshot route directly calls omitted CurvePrices and must fail closed. | `E-SRC-PD`, `E-M0` |
| `R-229` | `CM-034` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/Teller.vy:288`<br>`contracts/core/Teller.vy:660-720`<br>`contracts/core/Teller.vy:786-803` | Teller directly resolves custody routes through VaultBook. | `E-SRC-VB`, `E-M1` |
| `R-230` | `CM-034` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/Teller.vy:660-720`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | Teller directly calls the selected StabilityPool claim and redemption routes. | `E-M0`, `E-M1` |
| `R-231` | `CM-034` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/Teller.vy:288-304`<br>`contracts/core/Teller.vy:786-803`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | Teller directly calls the selected RipeGov deposit and lock routes. | `E-M0`, `E-M1` |
| `R-232` | `CM-034` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/Teller.vy:288-304`<br>`contracts/core/Teller.vy:369-388`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | Teller's direct generic vault deposit/withdraw calls cover the selected SimpleErc20 row. | `E-M0`, `E-M1` |
| `R-233` | `CM-034` | `direct_execution` | `runtime_security` | `CM-026` | `contracts/core/Teller.vy:559-613` | Teller directly calls AuctionHouse liquidation and purchase entrypoints. | `E-T8`, `E-M1` |
| `R-234` | `CM-034` | `direct_execution` | `runtime_security` | `CM-029` | `contracts/core/Teller.vy:822-824` | Teller directly calls BondRoom purchase settlement. | `E-H04`, `E-M0` |
| `R-235` | `CM-034` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/core/Teller.vy:478-496`<br>`contracts/core/Teller.vy:1007-1009` | Teller directly calls CreditEngine borrow, repay, and debt-refresh paths. | `E-T8`, `E-M1` |
| `R-236` | `CM-034` | `direct_execution` | `runtime_security` | `CM-033` | `contracts/core/Teller.vy:311`<br>`contracts/core/Teller.vy:385`<br>`contracts/core/Teller.vy:738-751` | Teller directly updates and claims Lootbox rewards. | `E-S3`, `E-M1` |
| `R-237` | `CM-034` | `direct_execution` | `runtime_security` | `CM-043` | `contracts/core/Teller.vy:504-538` | Teller directly calls CreditRedeem collateral redemption. | `E-T8`, `E-M1` |
| `R-238` | `CM-034` | `direct_execution` | `runtime_security` | `CM-044` | `contracts/core/Teller.vy:830-852` | Teller directly calls Deleverage execution. | `E-S4`, `E-M1` |
| `R-239` | `CM-034` | `direct_execution` | `runtime_security` | `CM-045` | `contracts/core/Teller.vy:288-292`<br>`contracts/core/Teller.vy:369-373`<br>`contracts/core/Teller.vy:771-800`<br>`contracts/core/Teller.vy:872-956`<br>`contracts/core/Teller.vy:1049` | Teller directly calls TellerUtils route and delegated-user validation. | `E-M1`, `E-M0` |
| `R-240` | `CM-034` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/Teller.vy:219-226`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-241` | `CM-038` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/config/BondBooster.vy:55-63`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-242` | `CM-043` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/CreditRedeem.vy:141-249`<br>`contracts/core/CreditRedeem.vy:275-297` | CreditRedeem directly receives, burns, refunds, and wraps GREEN. | `E-T8`, `E-M0` |
| `R-243` | `CM-043` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/CreditRedeem.vy:275-294` | CreditRedeem directly wraps GREEN into sGREEN for refunds. | `E-M0`, `E-M1` |
| `R-244` | `CM-043` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/CreditRedeem.vy:207` | CreditRedeem directly reads Ledger repayment accounting. | `E-S5`, `E-T8` |
| `R-245` | `CM-043` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/CreditRedeem.vy:198-204`<br>`contracts/core/CreditRedeem.vy:319`<br>`contracts/core/CreditRedeem.vy:362-365` | CreditRedeem directly consumes MissionControl redemption and delegation policy. | `E-H04`, `E-T8` |
| `R-246` | `CM-043` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/CreditRedeem.vy:239` | CreditRedeem directly calls PriceDesk for collateral redemption valuation. | `E-SRC-PD`, `E-T8` |
| `R-247` | `CM-043` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/CreditRedeem.vy:185-190` | CreditRedeem directly resolves collateral vaults through VaultBook. | `E-SRC-VB`, `E-T8` |
| `R-248` | `CM-043` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/CreditRedeem.vy:185-190`<br>`contracts/core/CreditRedeem.vy:244`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | CreditRedeem's direct generic vault/withdraw route covers the selected StabilityPool row. | `E-SRC-VB`, `E-T8` |
| `R-249` | `CM-043` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/CreditRedeem.vy:185-190`<br>`contracts/core/CreditRedeem.vy:244`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | CreditRedeem's direct generic vault/withdraw route covers the selected RipeGov row. | `E-SRC-VB`, `E-T8` |
| `R-250` | `CM-043` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/CreditRedeem.vy:185-190`<br>`contracts/core/CreditRedeem.vy:244`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | CreditRedeem's direct generic vault/withdraw route covers the selected SimpleErc20 row. | `E-SRC-VB`, `E-T8` |
| `R-251` | `CM-043` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/core/CreditRedeem.vy:210-249`<br>`contracts/core/CreditRedeem.vy:312` | CreditRedeem directly reads and reduces debt through CreditEngine. | `E-T8`, `E-M1` |
| `R-252` | `CM-043` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/CreditRedeem.vy:204`<br>`contracts/core/CreditRedeem.vy:292-293` | CreditRedeem directly uses Teller authorization and trusted StabilityPool deposits. | `E-M1`, `E-T8` |
| `R-253` | `CM-043` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/CreditRedeem.vy:115-122`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-254` | `CM-043` | `indirect_security_dependency` | `runtime_security` | `CM-022` | `contracts/core/CreditRedeem.vy:275-294`<br>`contracts/core/Teller.vy:288-304`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | CreditRedeem routes sGREEN refunds through Teller to the hard-coded StabilityPool. | `E-M1`, `E-SRC-VB`, `E-M0` |
| `R-255` | `CM-044` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/Deleverage.vy:863-866` | Deleverage directly burns GREEN during debt settlement. | `E-S4`, `E-M0` |
| `R-256` | `CM-044` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/Deleverage.vy:863-864` | Deleverage directly redeems sGREEN before burning GREEN. | `E-S4`, `E-M0` |
| `R-257` | `CM-044` | `direct_execution` | `runtime_security` | `CM-008` | `contracts/core/Deleverage.vy:679-729`<br>`contracts/core/Deleverage.vy:931-938` | Deleverage directly reads Ledger participation and user-vault accounting. | `E-S5`, `E-S4` |
| `R-258` | `CM-044` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/Deleverage.vy:218-280`<br>`contracts/core/Deleverage.vy:424-425`<br>`contracts/core/Deleverage.vy:491-528`<br>`contracts/core/Deleverage.vy:578-629`<br>`contracts/core/Deleverage.vy:961-1003` | Deleverage directly consumes MissionControl liquidation, debt, and delegation policy. | `E-H04`, `E-S4` |
| `R-259` | `CM-044` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/Deleverage.vy:444-448`<br>`contracts/core/Deleverage.vy:966`<br>`contracts/core/Deleverage.vy:1076`<br>`contracts/core/Deleverage.vy:1162-1177` | Deleverage directly calls PriceDesk for collateral and replacement valuation. | `E-SRC-PD`, `E-S4` |
| `R-260` | `CM-044` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/Deleverage.vy:417-420`<br>`contracts/core/Deleverage.vy:497-501`<br>`contracts/core/Deleverage.vy:931-938`<br>`contracts/core/Deleverage.vy:1199` | Deleverage directly resolves withdrawal and deposit vaults through VaultBook. | `E-SRC-VB`, `E-S4` |
| `R-261` | `CM-044` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/Deleverage.vy:500-502`<br>`contracts/core/Deleverage.vy:679-786`<br>`contracts/core/Deleverage.vy:938-973`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | Deleverage's direct generic vault calls cover the selected StabilityPool row. | `E-SRC-VB`, `E-S4` |
| `R-262` | `CM-044` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/Deleverage.vy:500-502`<br>`contracts/core/Deleverage.vy:679-786`<br>`contracts/core/Deleverage.vy:938-973`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | Deleverage's direct generic vault calls cover the selected RipeGov row. | `E-SRC-VB`, `E-S4` |
| `R-263` | `CM-044` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/Deleverage.vy:500-502`<br>`contracts/core/Deleverage.vy:679-786`<br>`contracts/core/Deleverage.vy:938-973`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | Deleverage's direct generic vault calls cover the selected SimpleErc20 row. | `E-SRC-VB`, `E-S4` |
| `R-264` | `CM-044` | `direct_execution` | `runtime_security` | `CM-026` | `contracts/core/Deleverage.vy:433-437`<br>`contracts/core/Deleverage.vy:1065` | Deleverage directly calls AuctionHouse vault-withdrawal settlement. | `E-S4`, `E-T8` |
| `R-265` | `CM-044` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/core/Deleverage.vy:280-317`<br>`contracts/core/Deleverage.vy:348-386`<br>`contracts/core/Deleverage.vy:491`<br>`contracts/core/Deleverage.vy:615-644`<br>`contracts/core/Deleverage.vy:996` | Deleverage directly reads and repays debt through CreditEngine. | `E-S4`, `E-T8` |
| `R-266` | `CM-044` | `direct_execution` | `runtime_security` | `CM-034` | `contracts/core/Deleverage.vy:455-460` | Deleverage directly uses Teller's trusted redeposit and housekeeping path. | `E-M1`, `E-S4` |
| `R-267` | `CM-044` | `direct_execution` | `runtime_security` | `CM-048` | `contracts/core/Deleverage.vy:218-266`<br>`contracts/core/Deleverage.vy:355`<br>`contracts/core/Deleverage.vy:580` | Deleverage directly reads the PSM yield-position identity for recipient routing. | `E-M0`, `E-S4` |
| `R-268` | `CM-044` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/core/Deleverage.vy:414-460` | Deleverage's governance-only collateral replacement depends on RipeHq governance. | `E-SRC-HQ` |
| `R-269` | `CM-044` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/Deleverage.vy:199-206`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-270` | `CM-044` | `indirect_security_dependency` | `runtime_security` | `CM-047` | `contracts/core/Deleverage.vy:218-264`<br>`contracts/core/Deleverage.vy:802-895`<br>`contracts/modules/Addys.vy:452-465`<br>`contracts/core/EndaomentFunds.vy:50-70` | Deleverage resolves EndaomentFunds and transfers configured collateral proceeds into that custody target. | `E-S4`, `E-M0` |
| `R-271` | `CM-045` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/TellerUtils.vy:118-129`<br>`contracts/core/TellerUtils.vy:220`<br>`contracts/core/TellerUtils.vy:248`<br>`contracts/core/TellerUtils.vy:281-408` | TellerUtils directly consumes MissionControl deposit, withdrawal, and Underscore policy. | `E-H04`, `E-M1` |
| `R-272` | `CM-045` | `direct_execution` | `runtime_security` | `CM-021` | `contracts/core/TellerUtils.vy:248-263` | TellerUtils directly resolves vault addresses and IDs through VaultBook. | `E-SRC-VB`, `E-M1` |
| `R-273` | `CM-045` | `direct_execution` | `runtime_security` | `CM-022` | `contracts/core/TellerUtils.vy:143`<br>`contracts/core/TellerUtils.vy:248-263`<br>`migrations/base-mainnet/1008_VaultBook.py:38-39` | TellerUtils's direct generic vault validation covers the selected StabilityPool row. | `E-SRC-VB`, `E-M1` |
| `R-274` | `CM-045` | `direct_execution` | `runtime_security` | `CM-023` | `contracts/core/TellerUtils.vy:143`<br>`contracts/core/TellerUtils.vy:248-263`<br>`migrations/base-mainnet/1008_VaultBook.py:41-42` | TellerUtils's direct generic vault validation covers the selected RipeGov row. | `E-SRC-VB`, `E-M1` |
| `R-275` | `CM-045` | `direct_execution` | `runtime_security` | `CM-024` | `contracts/core/TellerUtils.vy:143`<br>`contracts/core/TellerUtils.vy:248-263`<br>`migrations/base-mainnet/1008_VaultBook.py:44-45` | TellerUtils's direct generic vault validation covers the selected SimpleErc20 row. | `E-SRC-VB`, `E-M1` |
| `R-276` | `CM-045` | `direct_execution` | `runtime_security` | `CM-030` | `contracts/core/TellerUtils.vy:220-223` | TellerUtils directly calls CreditEngine withdrawal-limit validation. | `E-T8`, `E-M1` |
| `R-277` | `CM-045` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/TellerUtils.vy:92-99`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-278` | `CM-046` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/config/SwitchboardEcho.vy:475` | Echo directly resolves MissionControl for lite-action governance. | `E-H04`, `E-M0` |
| `R-279` | `CM-046` | `direct_execution` | `runtime_security` | `CM-031` | `contracts/config/SwitchboardEcho.vy:481`<br>`contracts/config/SwitchboardEcho.vy:499-563`<br>`contracts/config/SwitchboardEcho.vy:1069-1099` | Echo directly executes retained Endaoment governance actions. | `E-H04`, `E-M0` |
| `R-280` | `CM-046` | `direct_execution` | `runtime_security` | `CM-048` | `contracts/config/SwitchboardEcho.vy:487`<br>`contracts/config/SwitchboardEcho.vy:576-594`<br>`contracts/config/SwitchboardEcho.vy:1104-1164` | Echo directly configures the selected launch-disabled PSM. | `E-H04`, `E-M0` |
| `R-281` | `CM-046` | `authority_dependency` | `runtime_security` | `CM-004` | `contracts/config/SwitchboardEcho.vy:445-452`<br>`contracts/modules/LocalGov.vy:139-158` | Echo LocalGov authority depends on RipeHq governance. | `E-SRC-HQ` |
| `R-282` | `CM-047` | `authority_dependency` | `runtime_security` | `CM-031` | `contracts/core/EndaomentFunds.vy:57-60`<br>`contracts/modules/Addys.vy:356-359` | EndaomentFunds admits only the exact Endaoment address resolved through Addys and RipeHq. | `E-SRC-HQ`, `E-M0` |
| `R-283` | `CM-048` | `direct_execution` | `runtime_security` | `CM-001` | `contracts/core/EndaomentPSM.vy:249-270`<br>`contracts/core/EndaomentPSM.vy:407-439` | PSM directly mints and burns GREEN. | `E-M0`, `E-H04` |
| `R-284` | `CM-048` | `direct_execution` | `runtime_security` | `CM-003` | `contracts/core/EndaomentPSM.vy:249-265`<br>`contracts/core/EndaomentPSM.vy:393-397` | PSM directly deposits to and redeems from sGREEN. | `E-M0`, `E-H04` |
| `R-285` | `CM-048` | `direct_execution` | `runtime_security` | `CM-009` | `contracts/core/EndaomentPSM.vy:708-732` | PSM directly reads MissionControl's disabled external-integration registry. | `E-H04`, `E-M0` |
| `R-286` | `CM-048` | `direct_execution` | `runtime_security` | `CM-015` | `contracts/core/EndaomentPSM.vy:249`<br>`contracts/core/EndaomentPSM.vy:293`<br>`contracts/core/EndaomentPSM.vy:407`<br>`contracts/core/EndaomentPSM.vy:455` | PSM directly calls PriceDesk for reserve valuation. | `E-SRC-PD`, `E-M0` |
| `R-287` | `CM-048` | `authority_dependency` | `runtime_security` | `CM-010` | `contracts/core/EndaomentPSM.vy:167-199`<br>`contracts/modules/DeptBasics.vy:63-83`<br>`contracts/modules/Addys.vy:175-189` | Pause and recovery authority resolves admitted controllers through the Switchboard registry. | `E-SRC-SB`, `E-H04` |
| `R-288` | `CM-048` | `indirect_security_dependency` | `runtime_security` | `CM-047` | `contracts/core/EndaomentPSM.vy:676-693`<br>`contracts/modules/Addys.vy:452-465`<br>`contracts/core/EndaomentFunds.vy:50-70` | PSM resolves EndaomentFunds and transfers reserve assets into that custody target. | `E-M0`, `E-SRC` |

#### R6 relation correction from the rejected R4b and R5 graphs

R6 preserves R5's full regeneration under `D-H03-005` and changes only the
unsupported `R-282` triple and proof tuple. The rejected R4b graph used
invariant-enforcer orientation and grouped Cartesian expansion. R6
materializes every record above directly.

Relative to rejected R5, relation records remain 288, phase-qualified triples
remain 284, `authority_dependency` records remain 39, and the 34-source /
26-no-edge partition is unchanged. Exactly one canonical triple changes:
`CM-047→CM-010` becomes `CM-047→CM-031`. Its proof tuple changes from three
unsupported references to the two source-correct references shown in
`R-282`; canonical relation-table proof references therefore change from 713
to 712, and full-Section-7A.3 proof references change from 736 to 735.

Mechanically expanding the rejected R4b groups produces 267 phase-qualified
source-target triples. R6 contains 288 typed records over 284 phase-qualified
source-target triples: 231 retained, 53 added, and 36 removed. The four-record
difference between the R6 typed-record and triple counts is intentional:
`CM-030→CM-022`, `CM-032→CM-023`, `CM-033→CM-023`, and
`CM-043→CM-022` each have separately proved `direct_execution` and
`indirect_security_dependency` semantics. Their typed identities are unique.
The complete mechanically derived triple delta is:

| Change | Source | Phase | Targets |
| --- | --- | --- | --- |
| added | `CM-006` | `runtime_security` | `CM-010` |
| added | `CM-008` | `runtime_security` | `CM-010` |
| added | `CM-010` | `runtime_security` | `CM-004` |
| added | `CM-011` | `runtime_security` | `CM-004`, `CM-016` |
| added | `CM-012` | `runtime_security` | `CM-004`, `CM-010` |
| added | `CM-013` | `runtime_security` | `CM-004` |
| added | `CM-014` | `runtime_security` | `CM-004`, `CM-005` |
| added | `CM-015` | `runtime_security` | `CM-004`, `CM-010` |
| added | `CM-016` | `runtime_security` | `CM-004` |
| added | `CM-021` | `runtime_security` | `CM-004`, `CM-010`, `CM-022`, `CM-023`, `CM-024` |
| added | `CM-022` | `runtime_security` | `CM-010`, `CM-023` |
| added | `CM-023` | `runtime_security` | `CM-010` |
| added | `CM-024` | `runtime_security` | `CM-010` |
| added | `CM-026` | `runtime_security` | `CM-010`, `CM-023`, `CM-024` |
| added | `CM-027` | `runtime_security` | `CM-010` |
| added | `CM-028` | `runtime_security` | `CM-010` |
| added | `CM-029` | `runtime_security` | `CM-010` |
| added | `CM-030` | `runtime_security` | `CM-010`, `CM-023`, `CM-024` |
| added | `CM-031` | `runtime_security` | `CM-010` |
| added | `CM-032` | `runtime_security` | `CM-004`, `CM-005`, `CM-010` |
| added | `CM-033` | `runtime_security` | `CM-010`, `CM-022`, `CM-024` |
| added | `CM-034` | `runtime_security` | `CM-010` |
| added | `CM-038` | `runtime_security` | `CM-010` |
| added | `CM-043` | `runtime_security` | `CM-010`, `CM-023`, `CM-024` |
| added | `CM-044` | `runtime_security` | `CM-010`, `CM-022`, `CM-023`, `CM-024` |
| added | `CM-045` | `runtime_security` | `CM-010`, `CM-022`, `CM-023`, `CM-024` |
| added | `CM-046` | `runtime_security` | `CM-004` |
| added | `CM-048` | `runtime_security` | `CM-010` |
| removed | `CM-004` | `runtime_security` | `CM-010`, `CM-029`, `CM-032`, `CM-033` |
| removed | `CM-008` | `runtime_security` | `CM-021`, `CM-026`, `CM-029`, `CM-030`, `CM-031`, `CM-032`, `CM-033`, `CM-034` |
| removed | `CM-009` | `runtime_security` | `CM-002`, `CM-034` |
| removed | `CM-012` | `runtime_security` | `CM-001`, `CM-003`, `CM-026` |
| removed | `CM-013` | `runtime_security` | `CM-006` |
| removed | `CM-014` | `runtime_security` | `CM-032` |
| removed | `CM-016` | `runtime_security` | `CM-015` |
| removed | `CM-022` | `runtime_security` | `CM-026`, `CM-030` |
| removed | `CM-023` | `runtime_security` | `CM-026`, `CM-030`, `CM-032`, `CM-034` |
| removed | `CM-024` | `runtime_security` | `CM-026`, `CM-030`, `CM-034` |
| removed | `CM-026` | `runtime_security` | `CM-044` |
| removed | `CM-030` | `runtime_security` | `CM-026`, `CM-043`, `CM-044` |
| removed | `CM-038` | `runtime_security` | `CM-029` |
| removed | `CM-045` | `runtime_security` | `CM-034` |
| removed | `CM-048` | `runtime_security` | `CM-016` |

All 231 retained triples are also changed structurally: the former grouped
row implication is replaced by an explicit relation ID, exact kind, exact
phase, per-edge proof list, semantic basis, and authority list. No final count
inherits a provisional reviewer estimate.

The seven reviewer-identified direct omissions are present with exact proof:
`CM-011→CM-016`, `CM-014→CM-005`,
`CM-021→CM-022/023/024`, and `CM-026→CM-023/024`. The analogous
`CM-032→CM-005`, `CM-033→CM-022/024`, and generic selected-vault direct
calls in CreditEngine, CreditRedeem, Deleverage, and TellerUtils are also
materialized rather than inferred.

The unsupported `CM-016→CM-015` runtime edge is removed: ChainlinkPrices
calls MissionControl at `contracts/priceSources/ChainlinkPrices.vy:526-528`
and never calls PriceDesk. `CM-012→CM-026` and `CM-014→CM-032` are removed
because they were configuration-writer-to-consumer edges forbidden by
`D-H03-005`; Delta's actual Contributor calls are
`CM-014→CM-005`. `CM-048→CM-016` is removed because PSM calls PriceDesk,
not Chainlink; the exact valuation boundary is `CM-048→CM-015` plus
`CM-015→CM-016`. None is relabeled as direct.

The unsupported reverse caller-admission edges from Ledger, MissionControl,
vaults, and BondBooster are removed. Source-proved operational callers remain
caller-to-callee records. Switchboard pause/recovery authority is represented
consistently as each actual governed Department or vault pointing to `CM-010`
via `authority_dependency`; no reverse admission fan-out remains.
EndaomentFunds is the source-proved exception: it initializes only Addys and
its `transfer()` admits only the exact Endaoment address resolved through
RipeHq, so `R-282` is the reciprocal `CM-047→CM-031`
`authority_dependency`, distinct from direct call `CM-031→CM-047`. All ten
selected LocalGov inheritors point to `CM-004`, alongside the token and
explicit RipeHq-governed dependencies.

The former `G-011` proof is corrected to
`migrations/base-mainnet/1007_PriceDesk.py:41-42` plus AddressRegistry's
sequential implementation. The former `G-012` expansion is replaced by five
records using the exact per-child migration pairs, including
`migrations/base-mainnet/2025120200_New_Switchboards.py:71-72` for Echo.

`CM-013→CM-006` is not asserted: Charlie accepts an arbitrary TrainingWheels
address at `contracts/config/SwitchboardCharlie.vy:860-887`, while the
launch binding remains an unresolved `B-H04-PARAMS` input. No concrete
special-StabilityPool edge is asserted from Bravo, MissionControl, or
AuctionHouse: `specialStabPoolId` is a configurable valid VaultBook ID at
`contracts/config/SwitchboardBravo.vy:441-481` and is resolved dynamically
at `contracts/data/MissionControl.vy:774-793`. H-04 must bind both before
H-05; ambiguity is not converted into a canonical relation.

#### Complete runtime-security coverage determination

Exactly **34 components have outbound runtime-security
records** and **26 have explicit no-edge determinations**
below. Exactly **34 components have an outbound relation
across all five phases**. The runtime source set and no-edge set partition all
60 components without duplication.

| Component | Source/path reviewed | Why no outbound runtime-security relation is required | Evidence authority |
| --- | --- | --- | --- |
| `CM-005` | `contracts/modules/Contributor.vy:1-549` | Contributor is omitted. The selected HR and Delta callers carry direct fail-closed edges to this artifact family; dormant Contributor source has no selected outbound launch authority. | `E-SRC`, `E-M0` |
| `CM-007` | `contracts/config/DefaultsBase.vy:1-1276` | Base defaults are omitted; their values and addresses cannot become Robinhood runtime dependencies. | `E-CM`, `E-H04` |
| `CM-017` | `contracts/priceSources/CurvePrices.vy:1-1132` | CurvePrices is omitted. Selected callers carry direct fail-closed edges to it; the undeployed adapter has no outbound launch authority. | `E-CM`, `E-SRC-PD` |
| `CM-018` | `contracts/priceSources/BlueChipYieldPrices.vy:1-997` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-SRC-PD` |
| `CM-019` | `contracts/priceSources/PythPrices.vy:1-608` | PythPrices is omitted. Alpha carries the direct disabled-route edge; the undeployed adapter has no outbound launch authority. | `E-CM`, `E-SRC-PD` |
| `CM-020` | `contracts/priceSources/StorkPrices.vy:1-528` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-SRC-PD` |
| `CM-025` | `contracts/vaults/RebaseErc20.vy:1-158`<br>`contracts/vaults/modules/SharesVault.vy:1-268` | RebaseErc20/SharesVault is omitted; it has no selected VaultBook row or runtime route. | `E-CM`, `E-SRC-VB` |
| `CM-035` | `migrations/base-mainnet/2001_CurvePools.py:1-111` | The Base GreenPool integration is omitted and has no Robinhood artifact or route. | `E-CM`, `E-M0` |
| `CM-036` | `migrations/base-mainnet/2001_CurvePools.py:1-111` | The Base RipePoolCurve integration is omitted and has no Robinhood artifact or route. | `E-CM`, `E-M0` |
| `CM-037` | `migrations/base-mainnet/2025082000_AeroPrices.py:1-21` | The Base RipePoolAero integration is omitted and has no Robinhood artifact or route. | `E-CM`, `E-M0` |
| `CM-039` | `contracts/priceSources/wsuperOETHbPrices.vy:1-176` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-M0` |
| `CM-040` | `contracts/priceSources/RedStone.vy:1-570` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-M0` |
| `CM-041` | `contracts/priceSources/UndyVaultPrices.vy:1-774` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-M0` |
| `CM-042` | `migrations/base-mainnet/2025102200_UnderscoreVault.py:1-14` | Underscore Vault is omitted; retained callers fail closed and no concrete selected outbound vault binding exists. | `E-M0`, `E-S4` |
| `CM-049` | Section 7A.4 reviewed-planned contracts/config/DefaultsRobinhood.vy record | DefaultsRobinhood is a constructor/configuration input, not a deployed runtime authority. | `E-H04`, `E-CM` |
| `CM-050` | `contracts/priceSources/AeroRipePrices.vy:1-465` | The adapter is omitted and no selected launch route consumes it. | `E-CM`, `E-M0` |
| `CM-051` | Section 7A.4 literal absent-path marker | The GREEN CCIP pool is deferred and has no package, constructor, address, HQ row, or runtime artifact. | `E-T1`, `E-M0` |
| `CM-052` | Section 7A.4 literal absent-path marker | The RIPE CCIP pool is deferred and has no package, constructor, address, HQ row, or runtime artifact. | `E-T1`, `E-M0` |
| `CM-053` | Section 7A.4 literal absent-path marker | CCIP token-admin registration is deferred and has no materialized registration or runtime route. | `E-T1`, `E-M0` |
| `CM-054` | Section 7A.4 literal absent-path marker | The local GREEN/RIPE price adapter is absent and deferred; no launch artifact exists. | `E-T7`, `E-CM` |
| `CM-055` | Section 7A.4 exact tooling-path tuple | Deployment/migration tooling is non-onchain and cannot be a protocol runtime relation. | `E-T7`, `E-H03` |
| `CM-056` | Section 7A.4 exact tooling-path tuple | Manifest/history tooling is non-onchain and cannot be a protocol runtime relation. | `E-H02`, `E-T7` |
| `CM-057` | Section 7A.4 exact tooling-path tuple | ABI/export verification tooling is non-onchain and cannot be a protocol runtime relation. | `E-T7`, `E-CM` |
| `CM-058` | Section 7A.4 literal absent-path marker | The Solidity toolchain is external-pending and non-onchain; no launch artifact exists. | `E-T1` |
| `CM-059` | Section 7A.4 exact test-path tuple | Test profiles are non-onchain and cannot be a protocol runtime relation. | `E-T7`, `E-H03` |
| `CM-060` | `contracts/config/DefaultsLocal.vy:1-156` | Local defaults are omitted; their values and addresses cannot become Robinhood runtime dependencies. | `E-CM`, `E-H04` |

Explicit exclusion rule: an omitted or deferred component does not receive an
outbound edge merely because dormant source could call another contract if it
were deployed. The selected caller carries any required direct fail-closed
edge. Non-onchain tooling is not a protocol relation. Generic target
parameters without a source-bound CM identity are excluded or blocked; they
do not become a concrete CM relation until both source and reviewed
configuration bind the parameter to one exact component. Until then, the
unresolved binding remains excluded from the relation graph or is represented
through its owning blocker. TrainingWheels and special Stability Pool bindings
therefore remain `B-H04-PARAMS` facts, not invented relations.

### 7A.4 Canonical per-path source authority

Each `<path>; <kind>; <state>; <class>; <evidence>` entry is one
`SourcePathRecord`. Exact directory paths are allowed and are not globs.
`none` is a literal absent-path marker paired with `path_kind=none`.
The canonical table contains exactly 103 component-qualified path records;
the same repository path may appear under two tooling components only when
both components consume it. This applies to `scripts/utils/json_file.py` and
`config/network_profiles.py` for CM-055/056.

Mechanical cardinalities are: path kinds 92 `file`, 6 `directory`, and 5
`none`; path states 91 `existing`, 7 `reviewed_planned`, 4
`external_pending`, and 1 `absent`; source classes 53 `shared_contract`, 35
`non_onchain_tooling`, 9 `external_integration`, 3
`chain_specific_config`, and 3 `external_artifact`. Each list sums to 103.

| Component | Exact source-path records |
| --- | --- |
| CM-001 | `contracts/tokens/GreenToken.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/tokens/modules/Erc20Token.vy`; file; existing; shared_contract; `E-SRC` |
| CM-002 | `contracts/tokens/RipeToken.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/tokens/modules/Erc20Token.vy`; file; existing; shared_contract; `E-SRC` |
| CM-003 | `contracts/tokens/SavingsGreen.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/tokens/modules/Erc4626Token.vy`; file; existing; shared_contract; `E-SRC` |
| CM-004 | `contracts/registries/RipeHq.vy`; file; existing; shared_contract; `E-SRC-HQ`<br>`contracts/registries/modules/AddressRegistry.vy`; file; existing; shared_contract; `E-SRC-REG` |
| CM-005 | `contracts/modules/Contributor.vy`; file; existing; shared_contract; `E-SRC` |
| CM-006 | `contracts/config/TrainingWheels.vy`; file; existing; shared_contract; `E-SRC` |
| CM-007 | `contracts/config/DefaultsBase.vy`; file; existing; chain_specific_config; `E-CM` |
| CM-008 | `contracts/data/Ledger.vy`; file; existing; shared_contract; `E-S5` |
| CM-009 | `contracts/data/MissionControl.vy`; file; existing; shared_contract; `E-SRC` |
| CM-010 | `contracts/registries/Switchboard.vy`; file; existing; shared_contract; `E-SRC-SB` |
| CM-011 | `contracts/config/SwitchboardAlpha.vy`; file; existing; shared_contract; `E-SRC-SB` |
| CM-012 | `contracts/config/SwitchboardBravo.vy`; file; existing; shared_contract; `E-SRC-SB` |
| CM-013 | `contracts/config/SwitchboardCharlie.vy`; file; existing; shared_contract; `E-SRC-SB` |
| CM-014 | `contracts/config/SwitchboardDelta.vy`; file; existing; shared_contract; `E-S4` |
| CM-015 | `contracts/registries/PriceDesk.vy`; file; existing; shared_contract; `E-SRC-PD` |
| CM-016 | `contracts/priceSources/ChainlinkPrices.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/priceSources/modules/PriceSourceData.vy`; file; existing; shared_contract; `E-SRC` |
| CM-017 | `contracts/priceSources/CurvePrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-018 | `contracts/priceSources/BlueChipYieldPrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-019 | `contracts/priceSources/PythPrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-020 | `contracts/priceSources/StorkPrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-021 | `contracts/registries/VaultBook.vy`; file; existing; shared_contract; `E-SRC-VB` |
| CM-022 | `contracts/vaults/StabilityPool.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/vaults/modules/StabVault.vy`; file; existing; shared_contract; `E-SRC` |
| CM-023 | `contracts/vaults/RipeGov.vy`; file; existing; shared_contract; `E-SRC` |
| CM-024 | `contracts/vaults/SimpleErc20.vy`; file; existing; shared_contract; `E-SRC`<br>`contracts/vaults/modules/BasicVault.vy`; file; existing; shared_contract; `E-SRC` |
| CM-025 | `contracts/vaults/RebaseErc20.vy`; file; existing; shared_contract; `E-CM`<br>`contracts/vaults/modules/SharesVault.vy`; file; existing; shared_contract; `E-CM` |
| CM-026 | `contracts/core/AuctionHouse.vy`; file; existing; shared_contract; `E-T8` |
| CM-027 | `contracts/core/AuctionHouseNFT.vy`; file; existing; shared_contract; `E-SRC` |
| CM-028 | `contracts/core/Boardroom.vy`; file; existing; shared_contract; `E-SRC` |
| CM-029 | `contracts/core/BondRoom.vy`; file; existing; shared_contract; `E-SRC` |
| CM-030 | `contracts/core/CreditEngine.vy`; file; existing; shared_contract; `E-T8` |
| CM-031 | `contracts/core/Endaoment.vy`; file; existing; shared_contract; `E-SRC` |
| CM-032 | `contracts/core/HumanResources.vy`; file; existing; shared_contract; `E-SRC` |
| CM-033 | `contracts/core/Lootbox.vy`; file; existing; shared_contract; `E-S3` |
| CM-034 | `contracts/core/Teller.vy`; file; existing; shared_contract; `E-SRC` |
| CM-035 | `migrations/base-mainnet/2001_CurvePools.py`; file; existing; external_integration; `E-CM`<br>`migration_history/base-mainnet/v1/current-manifest.json`; file; existing; external_integration; `E-CM` |
| CM-036 | `migrations/base-mainnet/2001_CurvePools.py`; file; existing; external_integration; `E-CM`<br>`migration_history/base-mainnet/v1/current-manifest.json`; file; existing; external_integration; `E-CM` |
| CM-037 | `migrations/base-mainnet/2025082000_AeroPrices.py`; file; existing; external_integration; `E-CM`<br>`migration_history/base-mainnet/v1/current-manifest.json`; file; existing; external_integration; `E-CM` |
| CM-038 | `contracts/config/BondBooster.vy`; file; existing; shared_contract; `E-SRC` |
| CM-039 | `contracts/priceSources/wsuperOETHbPrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-040 | `contracts/priceSources/RedStone.vy`; file; existing; shared_contract; `E-CM` |
| CM-041 | `contracts/priceSources/UndyVaultPrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-042 | `migrations/base-mainnet/2025102200_UnderscoreVault.py`; file; existing; external_integration; `E-M0`<br>`migration_history/base-mainnet/v1/current-manifest.json`; file; existing; external_integration; `E-M0` |
| CM-043 | `contracts/core/CreditRedeem.vy`; file; existing; shared_contract; `E-T8` |
| CM-044 | `contracts/core/Deleverage.vy`; file; existing; shared_contract; `E-S4` |
| CM-045 | `contracts/core/TellerUtils.vy`; file; existing; shared_contract; `E-SRC` |
| CM-046 | `contracts/config/SwitchboardEcho.vy`; file; existing; shared_contract; `E-SRC-SB` |
| CM-047 | `contracts/core/EndaomentFunds.vy`; file; existing; shared_contract; `E-M0` |
| CM-048 | `contracts/core/EndaomentPSM.vy`; file; existing; shared_contract; `E-M0` |
| CM-049 | `contracts/config/DefaultsRobinhood.vy`; file; reviewed_planned; chain_specific_config; `E-H04` |
| CM-050 | `contracts/priceSources/AeroRipePrices.vy`; file; existing; shared_contract; `E-CM` |
| CM-051 | none; none; external_pending; external_artifact; `E-T1` |
| CM-052 | none; none; external_pending; external_artifact; `E-T1` |
| CM-053 | none; none; external_pending; external_integration; `E-T1` |
| CM-054 | none; none; absent; shared_contract; `E-T7` |
| CM-055 | `config/BluePrint.py`; file; existing; non_onchain_tooling; `E-CM`<br>`config/network_profiles.py`; file; existing; non_onchain_tooling; `E-T7`<br>`config/robinhood_blueprint.py`; file; reviewed_planned; non_onchain_tooling; `E-H03`<br>`scripts/migrate.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/console.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/deploy_args.py`; file; existing; non_onchain_tooling; `E-CM`<br>`scripts/utils/json_file.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration_helpers.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration_runner.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/params`; directory; existing; non_onchain_tooling; `E-CM`<br>`migrations/base-mainnet`; directory; existing; non_onchain_tooling; `E-CM`<br>`migrations/robinhood`; directory; reviewed_planned; non_onchain_tooling; `E-T7` |
| CM-056 | `migration_history/base-mainnet/v1`; directory; existing; non_onchain_tooling; `E-H02`<br>`migration_history/robinhood-mainnet/v1`; directory; reviewed_planned; non_onchain_tooling; `E-H02`<br>`migration_history/robinhood-testnet/v1`; directory; reviewed_planned; non_onchain_tooling; `E-H02`<br>`config/network_profiles.py`; file; existing; non_onchain_tooling; `E-H02`<br>`scripts/utils/json_file.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration_helpers.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/migration_runner.py`; file; existing; non_onchain_tooling; `E-T7` |
| CM-057 | `scripts/export_abis.py`; file; existing; non_onchain_tooling; `E-CM`<br>`scripts/verify.py`; file; existing; non_onchain_tooling; `E-T7`<br>`scripts/utils/verify_etherscan.py`; file; existing; non_onchain_tooling; `E-CM` |
| CM-058 | none; none; external_pending; external_artifact; `E-T1` |
| CM-059 | `tests/conf_core.py`; file; existing; non_onchain_tooling; `E-CM`<br>`tests/conf_utils.py`; file; existing; non_onchain_tooling; `E-CM`<br>`tests/deployment/test_network_profiles.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/deployment/test_base_profile_regression.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/deployment/test_secret_handling.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/deployment/test_dependency_gate.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/clock/test_clock_profiles.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/inventory/test_block_clock_inventory.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/utils/clock_profiles.py`; file; existing; non_onchain_tooling; `E-T7`<br>`tests/deployment/test_robinhood_blueprint.py`; file; reviewed_planned; non_onchain_tooling; `E-H03`<br>`tests/deployment/test_robinhood_omissions.py`; file; reviewed_planned; non_onchain_tooling; `E-H03` |
| CM-060 | `contracts/config/DefaultsLocal.vy`; file; existing; chain_specific_config; `E-CM` |

CM-056's history roots are exact H-02 profile data, not inferred namespace
aliases: `config/network_profiles.py:387` declares the existing Base root,
line 427 declares the proposed Robinhood mainnet root, and line 450 declares
the distinct proposed Robinhood testnet root. The source file itself is
therefore a CM-056 authority record as well as a CM-055 deployment-tooling
record. Neither proposed Robinhood directory is claimed to exist.

### 7A.5 Canonical component ownership and disposition authority

Names and deployments below are exact. `none` is the empty tuple. Source
paths, surfaces, relations, and symbolic inputs join from Sections
7A.1–7A.4; registry tuples join from Section 8 by component ID. This table is
the sole authority for component owners, negative assertions, downstream
slices, and controlling evidence. Each component's exact `blocker_ids` tuple
is the sorted, duplicate-free union of blocker IDs on its joined symbolic
inputs and surfaces; no prose or downstream reference may add another blocker.
Within a negative-assertion cell, a slash-separated numeric suffix inherits
the leading `NEG-` prefix, while every `NEG-H03-*` ID is written in full; this
is the only permitted abbreviation rule. Controlling evidence is always an
explicit tuple of declared Section 6.1 `E-*` IDs and never prose.

| Component / name | Deployment | Primary owner | Co-owners | Negative assertions | Downstream slices; controlling evidence |
| --- | --- | --- | --- | --- | --- |
| CM-001 `GreenToken` | `required` | `OWN-H04` | `OWN-H05`, `OWN-SECOPS`, `OWN-T1` | NEG-017/025/031 | H04/H05/H08/H09/T1; `E-CM`, `E-M0`, `E-T1`, `E-SRC-HQ` |
| CM-002 `RipeToken` | `required` | `OWN-H04` | `OWN-H05`, `OWN-SECOPS`, `OWN-T1` | NEG-017/025/031 | H04/H05/H08/H09/T1; `E-CM`, `E-M0`, `E-T1`, `E-SRC-HQ` |
| CM-003 `SavingsGreen` | `required` | `OWN-H04` | `OWN-H05`, `OWN-H09` | NEG-031/033/036 | H04/H05/H08/H09; `E-M0`, `E-SRC-HQ`, `E-SRC-REG` |
| CM-004 `RipeHq` | `required` | `OWN-H05` | `OWN-SECOPS`, `OWN-H08` | NEG-017/025/031/036/`NEG-H03-GLOBAL-MINT-SEQUENCE` | H05/H08/H09; `E-SRC-HQ`, `E-SRC-REG` |
| CM-005 `Contributor` | `omitted` | `OWN-H04` | `OWN-SECOPS`, `OWN-H08` | NEG-016/034 | post-launch HR amendment; `E-M0`, `E-VP` |
| CM-006 `TrainingWheels` | `required` | `OWN-SECOPS` | `OWN-H04`, `OWN-H05` | NEG-017 | H04/H05/H08; `E-CM`, `E-T7` |
| CM-007 `DefaultsBase` | `omitted` | `OWN-H04` | `OWN-H03`, `OWN-H08` | NEG-016/017 | H03/H04/H08; `E-CM`, `E-H04` |
| CM-008 `Ledger` | `blocked` | `OWN-S5` | `OWN-H04`, `OWN-H05`, `OWN-SECOPS` | NEG-017/031 | S5/H05/H08/H09; `E-S5`, `E-SRC-HQ` |
| CM-009 `MissionControl` | `required` | `OWN-H04` | `OWN-H05`, `OWN-T8`, `OWN-SECOPS` | NEG-017/021/022/023/024/033/034/035/036 | H04/H05/H08/H09/T8; `E-T7`, `E-M0`, `E-T8` |
| CM-010 `Switchboard` | `required` | `OWN-H05` | `OWN-H04`, `OWN-SECOPS` | NEG-017/031/036 | H04/H05/H08; `E-T7`, `E-SRC-HQ`, `E-SRC-SB` |
| CM-011 `SwitchboardAlpha` | `required` | `OWN-H04` | `OWN-ORACLE`, `OWN-H05` | NEG-024/031/037 | H04/H05/H08; `E-SRC-SB`, `E-SRC-PD` |
| CM-012 `SwitchboardBravo` | `required` | `OWN-H04` | `OWN-H05`, `OWN-T8` | NEG-017/031 | H04/H05/H08; `E-T7`, `E-SRC-SB` |
| CM-013 `SwitchboardCharlie` | `required` | `OWN-REWARDS` | `OWN-H04`, `OWN-H05` | NEG-035/036 | H04/H05/reward promotion; `E-M0`, `E-S3`, `E-SRC-SB` |
| CM-014 `SwitchboardDelta` | `required` | `OWN-H04` | `OWN-H05`, `OWN-REWARDS` | NEG-034/035/036 | H04/H05/H08; `E-S4`, `E-SRC-SB` |
| CM-015 `PriceDesk` | `required` | `OWN-ORACLE` | `OWN-H04`, `OWN-H05` | NEG-024/031/037 | H04/H05/H08; `E-SRC-HQ`, `E-SRC-PD` |
| CM-016 `ChainlinkPrices` | `required` | `OWN-ORACLE` | `OWN-H04`, `OWN-H05`, `OWN-T8` | NEG-017/024/037 | H04/H05/H08; `E-M0`, `E-SRC-PD` |
| CM-017 `CurvePrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-018 `BlueChipYieldPrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-019 `PythPrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-020 `StorkPrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024/037 | H08/H09; `E-CM`, `E-T7`, `E-SRC-PD` |
| CM-021 `VaultBook` | `required` | `OWN-H05` | `OWN-T8`, `OWN-H08` | NEG-021/031/036 | T8/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ`, `E-SRC-VB` |
| CM-022 `StabilityPool` | `required` | `OWN-H04` | `OWN-T8`, `OWN-H05`, `OWN-H08` | NEG-021/023/033/036 | H04/T8/H05/H08; `E-M0`, `E-T8`, `E-SRC-VB` |
| CM-023 `RipeGov` | `required` | `OWN-H04` | `OWN-H05`, `OWN-H08` | NEG-035/036 | H04/H05/H08; `E-M0`, `E-SRC-VB` |
| CM-024 `SimpleErc20` | `required` | `OWN-H04` | `OWN-H05`, `OWN-ORACLE`, `OWN-T8` | NEG-017/021/023/031/`NEG-H03-LP-ZERO-LTV`/`NEG-H03-LP-ORDINARY-ONLY` | H04/H05/T8/H08; `E-M0`, `E-T8`, `E-SRC-VB` |
| CM-025 `RebaseErc20` / inherited `SharesVault` | `omitted` | `OWN-T8` | `OWN-H05`, `OWN-H08` | NEG-016/021/031 | T8/H05/H08; `E-T8`, `E-SRC-VB` |
| CM-026 `AuctionHouse` | `required` | `OWN-T8` | `OWN-H04`, `OWN-H05`, `OWN-SECOPS` | NEG-021/023/036 | T8/H04/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-027 `AuctionHouseNFT` | `required` | `OWN-H05` | `OWN-H08` | NEG-031 | H05/H08; `E-CM`, `E-T7` |
| CM-028 `Boardroom` | `required` | `OWN-REWARDS` | `OWN-H04`, `OWN-H05` | NEG-035/036 | H04/H05/reward promotion; `E-M0`, `E-T7` |
| CM-029 `BondRoom` | `required` | `OWN-REWARDS` | `OWN-H04`, `OWN-H05`, `OWN-SECOPS` | NEG-034/035/036 | H04/H05/post-launch bond release; `E-M0`, `E-T7` |
| CM-030 `CreditEngine` | `required` | `OWN-T8` | `OWN-H04`, `OWN-S5`, `OWN-SECOPS` | NEG-021/022/023/024/036 | T8/H04/H05/H08/H09; `E-M0`, `E-T8`, `E-SRC-HQ` |
| CM-031 `Endaoment` | `required` | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | NEG-016/020/021/024/036 | H04/H05/H08; `E-M0`, `E-T7`, `E-SRC-HQ` |
| CM-032 `HumanResources` | `required` | `OWN-H04` | `OWN-SECOPS`, `OWN-H05` | NEG-034/036 | H04/H05/H08/post-launch HR release; `E-M0`, `E-T7` |
| CM-033 `Lootbox` | `required` | `OWN-REWARDS` | `OWN-H04`, `OWN-H05` | NEG-034/035/036/`NEG-H03-STOCK-REWARD-DISABLED` | H04/H05/H08/reward promotion; `E-S3`, `E-M0` |
| CM-034 `Teller` | `required` | `OWN-T8` | `OWN-H04`, `OWN-H05`, `OWN-SECOPS` | NEG-017/021/022/023/033/036/`NEG-H03-USDG-ROUTE`/`NEG-H03-TELLER-EXACT-RECEIPT` | T8/H04/H05/H08/H09; `E-M0`, `E-M1` |
| CM-035 `GreenPool` | `omitted` | `OWN-H03` | `OWN-ORACLE`, `OWN-H08` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-036 `RipePoolCurve` | `omitted` | `OWN-H03` | `OWN-ORACLE`, `OWN-H08` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-037 `RipePoolAero` | `omitted` | `OWN-H03` | `OWN-ORACLE`, `OWN-H08` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-038 `BondBooster` | `required` | `OWN-REWARDS` | `OWN-H04`, `OWN-H05` | NEG-035/036 | H04/H05/H08/post-launch bond release; `E-T7`, `E-SRC` |
| CM-039 `wsuperOETHbPrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-040 `RedStone` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-041 `UndyVaultPrices` | `omitted` | `OWN-ORACLE` | `OWN-T8`, `OWN-H08` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-042 `Underscore Vault` | `omitted` | `OWN-T8` | `OWN-H08`, `OWN-H09` | NEG-016/021/024/033/034/035/036 | H08/H09; `E-M0`, `E-S4` |
| CM-043 `CreditRedeem` | `required` | `OWN-T8` | `OWN-H04`, `OWN-H08` | NEG-021/022/036 | H04/H05/T8/H08; `E-M0`, `E-T8` |
| CM-044 `Deleverage` | `required` | `OWN-H04` | `OWN-H05`, `OWN-H08` | NEG-036 | H04/H05/H08; `E-S4` |
| CM-045 `TellerUtils` | `required` | `OWN-H05` | `OWN-H04`, `OWN-H08` | NEG-016/036 | H05/H08; `E-T7`, `E-M0` |
| CM-046 `SwitchboardEcho` | `required` | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | NEG-018/019/020/031/036/`NEG-H03-PSM-REDEEM-FIRST`/`NEG-H03-PSM-MINT-LAST` | H04/H05/H08; `E-M0`, `E-SRC-SB` |
| CM-047 `EndaomentFunds` | `required` | `OWN-H04` | `OWN-H05`, `OWN-SECOPS` | NEG-016/020/021/024/036 | H04/H05/H08; `E-M0` |
| CM-048 `EndaomentPSM` | `required` | `OWN-H04` | `OWN-T8`, `OWN-H05`, `OWN-SECOPS`, `OWN-H09` | NEG-017/018/019/020/024/031/036/`NEG-H03-GLOBAL-MINT-SEQUENCE`/`NEG-H03-USDG-ROUTE`/`NEG-H03-PSM-REDEEM-FIRST`/`NEG-H03-PSM-MINT-LAST` | H04/H05/H08/H09; `E-M0` |
| CM-049 `DefaultsRobinhood` | `required` | `OWN-H04` | `OWN-H05` | NEG-017 | H04/H05; `E-CM`, `E-H04` |
| CM-050 `AeroRipePrices` | `omitted` | `OWN-ORACLE` | `OWN-H08`, `OWN-H09` | NEG-016/024 | H08/H09; `E-CM`, `E-M0` |
| CM-051 GREEN CCIP BurnMint pool | `deferred` | `OWN-T1` | `OWN-SECOPS`, `OWN-H05` | NEG-016/025/031/036 | Track 1 fast follow/H08/H09; `E-M0`, `E-T1` |
| CM-052 RIPE CCIP BurnMint pool | `deferred` | `OWN-T1` | `OWN-SECOPS`, `OWN-H05` | NEG-016/025/031/036 | Track 1 fast follow/H08/H09; `E-M0`, `E-T1` |
| CM-053 CCIP token-admin registration | `deferred` | `OWN-T1` | `OWN-SECOPS` | NEG-016/025/036 | Track 1 fast follow; `E-M0`, `E-T1` |
| CM-054 GREEN/RIPE local price adapter | `deferred` | `OWN-ORACLE` | `OWN-H03`, `OWN-SECOPS` | NEG-016/024/037 | post-launch oracle/H03 amendment; `E-CM`, `E-T7` |
| CM-055 Deployment, migration, and parameter-report tooling | `required` | `OWN-H05` | `OWN-H03`, `OWN-H04` | NEG-017/031 | H03/H04/H05; `E-T7`, `E-H03` |
| CM-056 Manifests and migration history | `required` | `OWN-H05` | `OWN-H09` | NEG-016/017 | H05/H09; `E-H02`, `E-T7` |
| CM-057 ABI export and explorer verification | `required` | `OWN-H09` | `OWN-H05`, `OWN-T1` | NEG-016 | later Track 7/Track 1; `E-T7` |
| CM-058 Solidity build/test/deploy toolchain | `deferred` | `OWN-T1` | `OWN-SECOPS` | NEG-016/025 | Track 1 fast follow; `E-T1` |
| CM-059 Base/RH test profiles | `required` | `OWN-H09` | `OWN-H08`, `OWN-H03` | `NEG-016`, `NEG-017`, `NEG-018`, `NEG-019`, `NEG-020`, `NEG-021`, `NEG-022`, `NEG-023`, `NEG-024`, `NEG-025`, `NEG-031`, `NEG-033`, `NEG-034`, `NEG-035`, `NEG-036`, `NEG-037`, `NEG-H03-GLOBAL-MINT-SEQUENCE`, `NEG-H03-LP-ORDINARY-ONLY`, `NEG-H03-LP-ZERO-LTV`, `NEG-H03-USDG-ROUTE`, `NEG-H03-PSM-REDEEM-FIRST`, `NEG-H03-PSM-MINT-LAST`, `NEG-H03-STOCK-REWARD-DISABLED`, `NEG-H03-TELLER-EXACT-RECEIPT` | H03/H08/H09; `E-T7`, `E-H02`, `E-S1`, `E-S2` |
| CM-060 `DefaultsLocal` | `omitted` | `OWN-H04` | `OWN-H03`, `OWN-H08` | NEG-016/017 | H03/H04/H08; `E-CM`, `E-H04` |

## 8. Registry topology

`AddressRegistry` starts at ID 1, assigns the current `numAddrs`, then
increments it. It rejects an empty or non-contract new address. The source has
no sparse insertion operation. Therefore an omitted early semantic row cannot
be replaced by zero or an unrelated contract without shifting every later
registration-order result.

### 8.1 RipeHq

`contracts/modules/Addys.vy` compiles all IDs 1–22 into consumers. RipeHq's
constructor also directly creates IDs 1–3 in the stated order.

| ID | Semantic name / component | Authority | Phase A constraint |
| ---: | --- | --- | --- |
| 1 | Green Token / CM-001 | source-hard-coded | required |
| 2 | Savings Green / CM-003 | source-hard-coded and constructor-confirmed | required, active chain-native, never CCIP |
| 3 | Ripe Token / CM-002 | source-hard-coded and constructor-confirmed | required |
| 4 | Ledger / CM-008 | source-hard-coded | semantic reserved; deployment blocked by S5; no placeholder |
| 5 | Mission Control / CM-009 | source-hard-coded | required after CM-008 |
| 6 | Switchboard / CM-010 | source-hard-coded | required |
| 7 | Price Desk / CM-015 | source-hard-coded | required |
| 8 | Vault Book / CM-021 | source-hard-coded | required |
| 9 | Auction House / CM-026 | source-hard-coded | required |
| 10 | Auction House NFT / CM-027 | source-hard-coded | required |
| 11 | Boardroom / CM-028 | source-hard-coded | required topology artifact; rewards disabled |
| 12 | Bond Room / CM-029 | source-hard-coded | required topology artifact; bonds/capability disabled |
| 13 | Credit Engine / CM-030 | source-hard-coded | required; Stock route blocked |
| 14 | Endaoment / CM-031 | source-hard-coded | required; unsupported routes disabled |
| 15 | Human Resources / CM-032 | source-hard-coded | required inert topology artifact; HR disabled |
| 16 | Lootbox / CM-033 | source-hard-coded | required integrated S3 artifact; rewards/Underscore disabled |
| 17 | Teller / CM-034 | source-hard-coded | required; Stock trusted routes disabled |
| 18 | Deleverage / CM-044 | source-hard-coded | required unchanged; named zero-cooldown posture |
| 19 | Credit Redeem / CM-043 | source-hard-coded | required topology artifact; Stock redeem disabled |
| 20 | Teller Utils / CM-045 | source-hard-coded | required |
| 21 | Endaoment Funds / CM-047 | source-hard-coded | required; external/yield routes disabled |
| 22 | Endaoment PSM / CM-048 | source-hard-coded | required; disabled staging then gated launch activation |
| 23 | GREEN CCIP BurnMint pool / CM-051 | provisional reservation | no row, artifact, address, or capability |
| 24 | RIPE CCIP BurnMint pool / CM-052 | provisional reservation | no row, artifact, address, or capability |

### 8.2 VaultBook

| ID | Semantic name / component | Authority | Phase A constraint |
| ---: | --- | --- | --- |
| 1 | Stability Pool / CM-022 | source-hard-coded in Teller/CreditEngine/CreditRedeem consumers | required and active for GREEN; Stock excluded |
| 2 | Ripe Gov Vault / CM-023 | source-hard-coded in Teller/BondRoom/HR/Lootbox and vault consumers | required and active |
| 3 | Simple ERC20 Vault / CM-024 | Base-precedent registration-order constraint | required for approved ordinary deposit assets; no Stock inference |
| 4 | Rebase ERC20 Vault / CM-025 | Base-precedent registration-order semantic constraint | empty reserved semantic slot; CM-025 omitted |

Track 8 has not approved a VaultBook ID for the proposed guarded Stock vault.
H-03 must not silently call it ID 3 or 4, reserve a new numeric ID, or
renumber CM-024/025. `I-STOCK-VAULT-SLOT` remains blocked for Track 8/H-05.

### 8.3 PriceDesk

| ID | Semantic name / component | Authority | Phase A constraint |
| ---: | --- | --- | --- |
| 1 | Chainlink / CM-016 | Base-precedent registration-order constraint | required; only approved feeds |
| 2 | Curve / CM-017 | source-hard-coded in Teller/CreditEngine/Endaoment | empty reserved semantic slot |
| 3 | BlueChipYield / CM-018 | Base-precedent registration-order constraint | empty reserved semantic slot |
| 4 | Pyth / CM-019 | source-hard-coded in SwitchboardAlpha | empty reserved semantic slot |
| 5 | Stork / CM-020 | Base-precedent registration-order constraint | empty reserved semantic slot |

The sequential registry cannot skip an omitted adapter. No later source may
occupy IDs 2–5. Adding another source requires a separately reviewed topology
solution; CM-054 receives no guessed slot.

### 8.4 Switchboard

| ID | Semantic name / component | Authority | Phase A constraint |
| ---: | --- | --- | --- |
| 1 | Switchboard Alpha / CM-011 | source-hard-coded in SwitchboardBravo | required |
| 2 | Switchboard Bravo / CM-012 | Base-precedent registration-order constraint | required |
| 3 | Switchboard Charlie / CM-013 | Base-precedent registration-order constraint | required; launch rewards disabled |
| 4 | Switchboard Delta / CM-014 | Base-precedent registration-order constraint | required unchanged; S4 zero-cooldown assertion |
| 5 | Switchboard Echo / CM-046 | Base-precedent registration-order constraint | required for PSM governance; presence does not activate PSM |

H-05 owns the actual registration order and must stop before submission if any
next ID differs. H-08 later proves deployed topology. H-03 owns only the
immutable declarative constraints and their synthetic mutation tests.

## 9. SavingsGreen omission-versus-inert proof

Complete omission is not feasible with canonical source:

1. `RipeHq.__init__` requires a `_savingsGreen` contract input between GREEN
   and RIPE.
2. It immediately registers that contract as semantic ID 2 and asserts the
   result.
3. `AddressRegistry` rejects an empty or non-contract input and provides no
   sparse-ID insertion.
4. `Addys.vy` compiles ID 2 into shared consumers.

An unrelated or zero placeholder would violate both source validation and
semantic topology. An inert real SavingsGreen artifact was the older
minimum-source-change fallback while product disposition was open.

The later controlling M0 decision removes that product ambiguity: chain-native
sGREEN deposit and withdrawal is required at launch, with Stability Pool
enabled and sGREEN permanently excluded from CCIP. Therefore CM-003 is
`required`, not omitted, blocked, deferred, or an inert scaffold. Concrete
identity/configuration and deployed lifecycle proof remain owned by
H-04/H-05/H-08/H-09; launch rewards remain disabled.

No source change or owner question is necessary for this conclusion.

## 10. PSM omission-versus-disabled-staging proof

Complete omission is incompatible with current authority and unsafe for future
topology:

1. M0 selects canonical USDG PSM mint and redeem as a launch target.
2. `Addys.vy` compiles Endaoment PSM as RipeHq semantic ID 22.
3. A later CCIP reservation at 23/24 cannot be materialized after omitting 22
   without shifting sequential IDs.
4. Switchboard Echo is the order-constrained governance surface for ID 22 and
   does not itself activate the PSM.

Canonical PSM construction starts mint and redeem false but sets
`shouldAutoDeposit=True` at `contracts/core/EndaomentPSM.vy:181-199`. The
governed setter at `contracts/core/EndaomentPSM.vy:923-928` can change it
without a production source modification. The minimum-change staging contract
is therefore:

- CM-048 deployment is `required`;
- before activation, PSM mint, redeem, and RipeHq GREEN capability are
  `disabled`;
- an approved pre-activation governance action sets auto-deposit to `False`;
  yield position, Underscore bypass, external approval, and generic Teller
  collateral/asset routes remain `disabled`;
- USDG is PSM/LP-only;
- activation and launch-plan closure are `blocked` until exact
  artifact/config/runtime evidence;
- redemption is enabled and proved first; GREEN mint capability is the final
  capability-tuple mutation but not the final launch action; and
- no Curve or unsupported oracle dependency is introduced.

The typed no-yield posture is a named assertion. It is not represented in H-03
by an address or a numeric placeholder. PSM launch selection does not authorize
its production identity, constructor values, migration, deployment, or
activation.

### R6 approval-provenance amendment block

**Current state:** R6 Phase A approved, corrected, and integrated; current
lifecycle/provenance correction pending complete-file review.

- **Approved decision ID:** `D-H03-004-R6`
- **Approval actor/role:** Owner
- **Approval date:** 26 July 2026
- **Reviewed brief candidate SHA-256:**
  `f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`
- **Reviewed evidence candidate SHA-256:**
  `9b8bc27522c24ed40cfadb2e594e450ffab2e4f947c036affac7cf9bdacd46ad`
- **Publication commit:**
  `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`
- **Chronology correction commit:**
  `d65e4dbd6ab832cc65265b9bda443cd8031b20e4`
- **R6 integration merge:**
  `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`
- **Integrated chronology-corrected evidence SHA-256:**
  `ed81dad7aaad41150ee49d20134916c9660e283ac77f85a2b0e5fe757ab2036c`
- **Final controlling `rh`:**
  `7098211db5693f986b65ec7a9e897f3518e9538c`
- **Final controlling `rh` tree:**
  `c07329ed9fcc2dc99afbef3f7888f478024d1ede`

The current lifecycle/provenance correction is deliberately outside the
historical self-hash chain above. Its exact complete-file hash must be reported
externally, independently reviewed, and owner-approved before an evidence-only
commit, reconciliation, or integration. Any non-lifecycle/provenance
difference voids this correction and requires a new substantive Phase A
review.

### 10.1 Owner-approved terminal global-mint sequence

Source initializes `RipeHq.mintEnabled=True` at
`contracts/registries/RipeHq.vy:95-127`, checks that circuit breaker in
`canMintGreen`/`canMintRipe` at lines 378-399, and exposes the
governance-only `setMintingEnabled` operation at lines 419-424. Source proves
the mechanism but does not select Robinhood's terminal state or launch order.

Owner decision `D-H03-006` approves this exact order:

1. immediately after the required HQ bootstrap permits governance action,
   call `setMintingEnabled(False)` before any capability-tuple mutation;
2. while global minting is false, configure and verify the exact launch tuple
   set:
   - CM-010 Switchboard `(False, False, True)`;
   - CM-021 VaultBook `(False, True, False)`;
   - CM-026 AuctionHouse `(True, False, False)`;
   - CM-030 CreditEngine `(True, False, False)`;
   - CM-031 Endaoment `(True, False, False)`; and
   - every other registered row `(False, False, False)`, including CM-048
     during staging;
3. configure and prove PSM redemption, auto-deposit-off, no-yield, reserve,
   feed, and all other launch prerequisites while global minting remains false;
4. mutate CM-048 EndaomentPSM to `(True, False, False)` as the final
   capability-tuple mutation;
5. re-read and verify the complete tuple set, PSM redemption behavior, and all
   disabled/omitted routes; and
6. call `setMintingEnabled(True)` as the final launch activation, after which
   no capability, registry, route, or parameter mutation remains in that
   launch plan.

The pre-PSM tuples above are the five exact selected target tuples already
encoded by `S-010-HQ-BLACKLIST-CAP`, `S-021-HQ-RIPE-CAP`,
`S-026-HQ-GREEN-CAP`, `S-030-HQ-GREEN-CAP`, and
`S-031-HQ-GREEN-CAP`. CM-048 is the sixth and final target tuple. BondRoom,
HumanResources, and Lootbox advertise RIPE-mint compatibility in their
Department source but remain false in HQ at launch because their mint/reward
surfaces are disabled. Execution and proof remain blocked by `B-H05-PLAN`,
`B-PSM-SEQUENCE`, and `B-SECOPS-HANDOFF`; approval of the sequence supplies no
address, tuple transaction, role, signer, parameter, deployment, or
activation. Any later owner change requires a reviewed Phase A amendment
before Phase B.

## 11. Track 8 M0 and Stock reconciliation

M0 is truthfully represented as owner-closed. That fact does not close any
post-M0 implementation or release gate.

| Surface | H-03 Phase A representation |
| --- | --- |
| Initial Stock set | AAPL symbolic identity only; every additional Stock Token omitted pending a token-specific review |
| Production identity/feed/caps | Symbolic fields `I-AAPL-TOKEN`, `I-AAPL-FEED`, `I-AAPL-RISK`; no value copied; final revalidation/freeze blocked |
| Stock vault | `I-STOCK-VAULT-ARTIFACT` and `I-STOCK-VAULT-SLOT` blocked; no new CM ID or VaultBook ID guessed |
| Ordinary vault CM-024 | Required for approved LP assets only through Teller `deposit`/`depositMany`; `depositFromTrusted` and Department/direct-vault bypasses are excluded; does not imply AAPL compatibility |
| Rebase CM-025 | Omitted; its semantic slot cannot be repurposed |
| Deposit/borrow/settlement | Desired AAPL launch lifecycle remains blocked by M1–M5 |
| CreditRedeem | Stock route disabled |
| Stability Pool | GREEN active; Stock custody/swaps disabled |
| Trusted/Department routes | AAPL/Stock disabled |
| Rewards | Globally disabled at launch; separate promotion |
| Unsupported routes | Endaoment, Curve, Aerodrome, Underscore, yield, Base-only, and every unnamed Stock route absent |
| Base | Unchanged; no migration/convergence implied |

The proposed guarded vault is a required future artifact but is not one of the
stable CM-001–060 identities. The smallest H-03 representation is two typed
symbolic inputs with distinct scopes, not a fabricated component ID and not a
redefinition of CM-024 or CM-025: `I-STOCK-VAULT-ARTIFACT` is consumed by
CM-021/026/030/034, while `I-STOCK-VAULT-SLOT` is consumed only by CM-021.
Checkpoint decision `D-H03-001` ratifies that boundary.

### 11.1 Approved LP ordinary-only Teller invariant

For each exact symbolic LP identity, `I-GREEN-USDG-LP` and
`I-RIPE-WETH-LP`, the allowed Teller entrypoint set is exactly
`{deposit, depositMany}` and the trusted entrypoint set is empty. Teller's
ordinary entrypoints are source-distinct from `depositFromTrusted` at
`contracts/core/Teller.vy:231-268`; the latter validates a Ripe caller and
passes `_didAlreadyValidateSender=True`, so the phrase "deposit-only" does not
exclude it by itself.

`NEG-H03-LP-ORDINARY-ONLY` therefore requires, for both LP assets:

- an ordinary CM-034-to-CM-024 deposit route only;
- no `depositFromTrusted` route for any producer, vault ID, lock duration, or
  supplied `Addys`;
- no Department-specific or direct-vault route that bypasses the ordinary
  Teller path; and
- separate satisfaction of `NEG-H03-LP-ZERO-LTV`; a zero LTV does not prove
  ordinary-only routing.

The complete retained trusted-producer universe is seven components and eight
source call sites:
CM-022 at `contracts/vaults/modules/StabVault.vy:750-756` and
`contracts/vaults/modules/StabVault.vy:980-995`; CM-029 at
`contracts/core/BondRoom.vy:217-224`; CM-030 at
`contracts/core/CreditEngine.vy:1201-1208`; CM-032 at
`contracts/core/HumanResources.vy:420-427`; CM-033 at
`contracts/core/Lootbox.vy:1154-1161`; CM-043 at
`contracts/core/CreditRedeem.vy:287-294`; and CM-044 at
`contracts/core/Deleverage.vy:450-457`.

The mutation family changes each LP independently and must reject: adding
`depositFromTrusted` to its allowed routes; mapping the LP asset through any
one of the seven producers or eight call-site classes; adding a new trusted
producer; enabling a Department/direct-vault bypass; dropping the assertion
from `S-024-LP-DEPOSIT`, `S-024-LP-ORDINARY-ONLY`, CM-024, or CM-059; and
claiming that the separate zero-LTV/borrow-omission rows imply this invariant.
All such mutations fail with `H03_TRACK8_GATE` or
`H03_OMISSION_SURFACE`.

## 12. Address-shaped literal and Base-comparison strategy

Phase B module validation recursively visits every dataclass field and nested
tuple. It rejects any string matching a case-insensitive address-shaped token:
the hexadecimal prefix followed by exactly forty hexadecimal characters,
bounded so a substring of a longer hexadecimal token cannot pass. A separate
validation rule rejects any value-bearing symbolic field, zero/local/Base
fallback, URL, environment reference, or concrete production parameter.

Tests do not copy any address into an H-03 file. At test time only:

1. import the existing read-only `ADDYS`, `CORE_TOKENS`, `WHALES`, and
   `YIELD_TOKENS` dictionaries from `config/BluePrint.py`;
2. parse the committed Base current manifest read-only;
3. recursively derive the set of address-shaped strings from those sources;
4. recursively derive strings from the synthetic H-03 blueprint;
5. assert empty intersection; and
6. assert the Base blueprint and manifest hashes are unchanged after the
   comparison.

The zero-placeholder mutation constructs its synthetic candidate from pieces
at runtime rather than storing an address-shaped literal. This dynamic
comparison belongs only in tests; importing or validating the H-03 module
never reads Base files.

## 13. Negative and mutation test design

### 13.1 Validation-plan negative cases

The canonical assertion set contains exactly 24 stable IDs: 16 validation-plan
IDs and eight H-03-specific IDs.

| Case / Phase B test | Declarative H-03 proof |
| --- | --- |
| NEG-016 `test_omitted_component_has_no_surface` | inject an artifact/registry/capability/permission/approval/route/manifest expectation into an omitted row; validation fails |
| NEG-017 `test_zero_is_not_placeholder` | missing required symbolic field and a runtime-built zero-shaped candidate both fail; named legitimate-zero assertions remain distinct |
| NEG-018 `test_psm_mint_disabled` | pre-activation CM-048 mint and HQ GREEN capability must be disabled |
| NEG-019 `test_psm_redeem_disabled` | pre-activation CM-048 redeem must be disabled |
| NEG-020 `test_psm_no_auto_deposit_or_yield` | source auto-deposit `True` must be changed to `False` by an approved pre-activation action; yield/approval/Underscore surfaces remain disabled |
| NEG-021 `test_stock_asset_not_enabled_before_track8` | M0 closure alone cannot remove M1–M5 blockers or enable an AAPL route |
| NEG-022 `test_stock_credit_redeem_false` | Stock CreditRedeem surface remains disabled |
| NEG-023 `test_stock_stability_swap_false` | Stock Stability custody/swap surface remains disabled |
| NEG-024 `test_unsupported_oracle_unreachable` | CM-017–020/039–041/050 have no row/feed/route; semantic slots remain reserved |
| NEG-025 `test_ccip_capability_withheld_until_complete` | the exact six CCIP surfaces remain disabled/deferred and are referenced only by deferred `P-CCIP-SEVEN-DAY`; `S-001-CCIP-CAP` and `S-002-CCIP-CAP` are explicitly disabled at launch and remain disabled continuously through the promotion checkpoint; CM-051–053 reservations have no row/capability, incomplete evidence cannot promote a subset, and elapsed time never activates CCIP |
| NEG-031 H-03-owned `test_registry_semantic_ids_cannot_shift` | mutate every hard/order/reserve mapping and fail closed; H-08 keeps its later exact test |
| NEG-033 revised `test_sgreen_required_chain_native_and_never_ccip` | current authority requires active chain-native sGREEN and forbids CCIP; the old inert-without-approval premise is superseded |
| NEG-034 `test_hr_scaffold_has_no_contributors_or_rewards` | CM-032 remains topology-only; CM-005 omitted; no HR/template/vesting/payout/capability |
| NEG-035 `test_bond_and_reward_paths_stay_disabled` | CM-028/029/033/038 exist only with launch reward/bond surfaces disabled |
| NEG-036 `test_slot_scaffolds_have_exact_disabled_capabilities` | required scaffolds enumerate exact inactive surfaces; CM-003 is no longer an inert target |
| NEG-037 H-03-owned `test_pricedesk_reservations_cannot_be_repurposed` | IDs 2–5 cannot be shifted or filled by another semantic; H-08 keeps its later exact test |
| `NEG-H03-GLOBAL-MINT-SEQUENCE` `test_global_mint_reenable_is_final_launch_activation` | owner-approved `D-H03-006` requires global disable, five exact pre-PSM target tuples with all unlisted bits false, PSM redemption/prerequisite proof, final CM-048 tuple mutation, complete re-verification, then global re-enable as the final launch activation; execution and proof remain blocked |
| `NEG-H03-LP-ORDINARY-ONLY` `test_lp_assets_exclude_every_trusted_teller_route` | both approved LP identities allow only Teller `deposit`/`depositMany`; `depositFromTrusted` is empty across all seven producers/eight call sites and no Department/direct-vault bypass exists |
| `NEG-H03-LP-ZERO-LTV` `test_lp_assets_are_deposit_only_with_zero_ltv` | any approved LP route is deposit-only, has exact zero LTV/no borrowing power, and cannot be promoted by vault presence |
| `NEG-H03-USDG-ROUTE` `test_usdg_is_psm_or_lp_only` | USDG may participate only in the PSM and approved LP; ordinary Teller collateral/deposit routes remain absent |
| `NEG-H03-PSM-REDEEM-FIRST` `test_psm_redeem_precedes_mint_capability` | redemption must be configured, enabled, and proved before GREEN mint capability can be granted |
| `NEG-H03-PSM-MINT-LAST` `test_psm_green_mint_capability_is_last` | every prerequisite is proved before the final GREEN capability-tuple mutation; reversed or early order fails, and the later final global re-enable remains separately governed by `NEG-H03-GLOBAL-MINT-SEQUENCE` |
| `NEG-H03-STOCK-REWARD-DISABLED` `test_stock_rewards_start_disabled_but_are_promotion_eligible` | Stock reward surfaces are launch-disabled at `deployed_initial_value`, not permanently omitted; the separate deferred promotion record references them without changing launch state |
| `NEG-H03-TELLER-EXACT-RECEIPT` `test_teller_exact_receipt_policy_covers_every_producer` | M1 success requires `R == Q`, `vaultResult == Q`, exact-length return reads, one mutex policy, and atomic rollback for the external route and all eight `depositFromTrusted` call sites across CM-022/029/030/032/033/043/044; short, zero, excess, malformed, reentrant, and downstream-failure mutations fail closed |

NEG-018/019 describe disabled setup state, not final rejection of the
owner-selected launch target. NEG-033 and CM-003's old NEG-036 premise require
the explicit supersession approved in `D-H03-002`.

### 13.2 Blueprint and mutation matrix

| Test/mutation | Expected diagnostic |
| --- | --- |
| exact two H-02 profiles return the same object; other/case/alias IDs rejected | `H03_PROFILE_EXACT` |
| missing CM row, extra row, duplicate ID, noncontiguous ID | `H03_COMPONENT_SET` |
| replace tuple/nested tuple with list/dict/set or attempt attribute mutation | `H03_IMMUTABLE` |
| collapse required deployment plus disabled surface into one optimistic state | `H03_DISPOSITION` |
| remove symbolic field owner, deadline, semantic class, or blocker | `H03_SYMBOLIC_FIELD` / `H03_BLOCKER` |
| set any symbolic input's `consumers` to an empty tuple or an unknown CM ID | `H03_SYMBOLIC_FIELD` |
| add or remove a known CM consumer relative to Section 7A.1's exact consumer tuples | `H03_SYMBOLIC_FIELD` |
| inject address-shaped, Base-derived, local-derived, URL, environment, or value-bearing string | `H03_ADDRESS_LITERAL` / `H03_SYMBOLIC_FIELD` |
| replace missing field with runtime-built zero-shaped candidate | `H03_ADDRESS_LITERAL` |
| delete a whole canonical surface record while every remaining record stays internally valid | `H03_SURFACE_SET` |
| duplicate a `surface_id`, use an unknown `SurfaceKind`, or drop a surface field | `H03_SURFACE_SET` |
| add or remove a canonical surface relative to the Section 7A.2 expected set | `H03_SURFACE_SET` |
| omit semantic meaning or lifecycle phase, use a lifecycle value outside H-04's exact eight-value enum, or move a surface to the wrong phase | `H03_SURFACE_SET` / `H03_DISPOSITION` |
| delete/duplicate either canonical promotion, change or cross-assign either exact surface set, remove either GREEN/RIPE CCIP capability's continuous launch-disabled invariant, move a reward launch state to reward activation, use either superseded lifecycle value, remove a blocker, or treat elapsed time as approval | `H03_PROMOTION_SET` / `H03_DISPOSITION` |
| delete a whole canonical relation edge | `H03_RELATION` |
| point a relation at an unknown CM ID, a workflow/slice identifier, or prose | `H03_RELATION` |
| use an unknown phase, or move an edge to the wrong phase (phase confusion) | `H03_RELATION` |
| add or remove an edge relative to the Section 7A.3 expected set, duplicate one, or omit its source proof | `H03_RELATION` |
| remove any of the seven producer-to-Teller relations, omit either CM-022 call-site proof, or add a trusted producer not governed by the same exact-receipt assertion | `H03_RELATION` / `H03_TRACK8_GATE` |
| drop a source-path record, invent a path, use a broad glob, assign a wrong kind/class/evidence ID, or claim `existing` with no exact path | `H03_SOURCE_AUTHORITY` |
| mark a `reviewed_planned` path as `existing`, or the reverse | `H03_SOURCE_AUTHORITY` |
| give a blocker no primary owner, no deadline gate, an unknown owner, or a duplicate ID | `H03_BLOCKER` |
| use `same`, `T8*`, slash-prose, or an undeclared owner in any symbolic input or component | `H03_SYMBOLIC_FIELD` / `H03_BLOCKER` |
| leave a blocker orphaned, or delete one that a surface or component still references | `H03_BLOCKER` |
| give a symbolic input a mixed or multiple status | `H03_SYMBOLIC_FIELD` |
| close a blocker merely because a concrete value now exists | `H03_BLOCKER` |
| remove Track 8 M1–M5 blocker because M0 is closed | `H03_TRACK8_GATE` |
| enable AAPL ordinary/trusted/Department, CreditRedeem, Stability, reward, or unsupported route | `H03_TRACK8_GATE` / `H03_OMISSION_SURFACE` |
| give omitted component a source artifact, registry row, capability, permission, route, or manifest record | `H03_OMISSION_SURFACE` |
| move a hard-coded ID, relabel an order constraint hard-coded, assign a reservation row, or reuse an empty semantic slot | `H03_REGISTRY_TOPOLOGY` |
| delete blocker provenance from deferred/blocked row | `H03_BLOCKER` |
| enable CCIP or PSM from topology presence alone | `H03_DISPOSITION` / `H03_TRACK8_GATE` |
| encode PSM auto-deposit `False` as a deployed initial value, omit the source `True` state, or omit the required pre-activation action | `H03_SURFACE_SET` / `H03_DISPOSITION` |
| give either approved LP positive LTV/borrow power or permit a deposit route before artifact/oracle proof | `H03_DISPOSITION` / `H03_TRACK8_GATE` |
| allow either approved LP through `depositFromTrusted`, any of the seven trusted producers/eight call sites, a new trusted producer, or a Department/direct-vault bypass | `H03_TRACK8_GATE` / `H03_OMISSION_SURFACE` |
| route USDG through ordinary Teller collateral/deposit handling | `H03_OMISSION_SURFACE` / `H03_TRACK8_GATE` |
| grant PSM GREEN mint capability before redemption proof, omit either ordering assertion, or reverse the sequence | `H03_TRACK8_GATE` |
| re-enable global minting before tuple/prerequisite verification, mutate a tuple after CM-048, omit post-CM-048 re-verification, or place any launch mutation after global re-enable | `H03_TRACK8_GATE` / `H03_DISPOSITION` |
| treat Stock rewards as permanently omitted or launch-enabled | `H03_DISPOSITION` / `H03_TRACK8_GATE` |
| accept a Teller receipt where `R != Q`, `vaultResult != Q`, return data is not exact length, the mutex is bypassed/reentered, or any producer-side/downstream failure does not roll back atomically | `H03_TRACK8_GATE` |
| make sGREEN omitted/inert/CCIP-enabled or Stability launch-disabled | `H03_DISPOSITION` |
| mutate Base blueprint during test comparison | Base byte-hash assertion fails |
| import with RPC/key/account variables absent while spies cover environment/filesystem/Git/socket/Boa | import-purity assertion fails on any side effect |

The tests use synthetic immutable record replacements. They do not deploy a
contract, build a migration fixture, claim an integration result, initialize
Boa, or contact a network.

### 13.3 Exact lifecycle and seven-day promotion assertions

H-04's exact lifecycle vocabulary applies without compression:
`deployed_initial_value`, `pre_activation_configuration`,
`atomic_stock_activation`,
`within_seven_day_separately_reviewed_ccip_promotion`,
`within_seven_day_separately_reviewed_reward_activation`,
`post_launch_release`, `omitted`, or `blocked`. H-03 records the phase, never
the concrete value.

| Assertion | Exact content |
| --- | --- |
| GREEN/RIPE CCIP promotion | separate `P-CCIP-SEVEN-DAY` record at `within_seven_day_separately_reviewed_ccip_promotion`, referencing exactly `S-001-CCIP-CAP`, `S-002-CCIP-CAP`, `S-051-ARTIFACT`, `S-052-ARTIFACT`, `S-053-REGISTRATION`, and `S-058-TOOLCHAIN`; deferred, separately reviewed, and nonautomatic |
| GREEN/RIPE CCIP launch state | `S-001-CCIP-CAP` and `S-002-CCIP-CAP` are `disabled` at `deployed_initial_value` and remain disabled continuously through the CCIP-promotion checkpoint; their promotion-phase label identifies the controlling reviewed action rather than an absent launch state |
| CCIP incompleteness | incomplete or late evidence leaves CCIP disabled; disabled CCIP preserves M0 state-independence |
| sGREEN and CCIP | sGREEN is permanently excluded from CCIP; this is not a fast-follow item |
| Rewards at launch | all seven exact reward surfaces use `deployed_initial_value`; globally disabled |
| Rewards promotion | separate `P-REWARDS-SEVEN-DAY` record at `within_seven_day_separately_reviewed_reward_activation`, retaining exactly its seven reward surfaces; deferred, blocked, and separately reviewed; it does not change launch-state rows, so zero reward-activation `SurfaceRecord` values is correct and required |
| AAPL activation | `atomic_stock_activation` only after every M1–M5 blocker closes |
| LP deposit targets | both approved LP ordinary-only routes are launch requirements; unresolved artifact/oracle, zero-LTV, or trusted-route exclusion proof keeps `S-024-LP-DEPOSIT` and `S-024-LP-ORDINARY-ONLY` blocked and prevents launch-plan closure |
| PSM target | PSM mint/redeem is a launch requirement; unresolved pre-activation, redemption-first, auto-deposit-off, final-tuple, and global-mint-sequence proof keeps activation blocked and prevents launch-plan closure |
| Global mint terminal state | owner-approved final re-enable only after full staging and verification; execution and proof remain blocked |
| Later Stock Tokens, HR, bonds, and unselected oracle work | `post_launch_release` unless a new reviewed authority says otherwise |
| Neither target is authorization | a deadline, target date, elapsed seven-day window, or prewritten alternate value never promotes a setting into the active manifest; each promotion is a new reviewed release |

Phase B must assert that the CCIP-promotion lifecycle appears only on the exact
six named CCIP surfaces; `S-001-CCIP-CAP` and `S-002-CCIP-CAP` are disabled
from `deployed_initial_value` continuously through the CCIP-promotion
checkpoint; the reward-activation lifecycle appears only on the separate
reward promotion action; CM-051/052/053 remain `deferred`; all seven reward
surfaces remain launch-disabled at `deployed_initial_value`; zero
reward-activation `SurfaceRecord` values remains a required cardinality; both
promotions remain separate deferred records; and elapsed time alone changes
no disposition. `S-003-CCIP` remains permanently `omitted`. The superseded R5
lifecycle spellings are invalid and absent from the closed enum.

## 14. Exact file boundary and diff plan

The published R6 Phase A package changed exactly two documentation paths:
this evidence record and the controlling H-03 brief. It is preserved in
feature commit `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`. The evidence-only
chronology correction is preserved in commit
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4`; merge
`8e4a965f034dc3d11b60fbb674ebbb4095b57d98` integrated the corrected R6
package into `rh`.

This lifecycle/provenance correction changes only this evidence record and
keeps the approved brief byte-identical. Complete-file independent exact-hash
review and fresh owner approval of its exact hash must precede a separately
authorized evidence-only commit, reconciliation, and integration. This
correction does not authorize Phase B.

After this one-file correction is approved and integrated, the Phase B
implementation ceiling remains exactly three files:

| Phase | File | Purpose |
| --- | --- | --- |
| B | `config/robinhood_blueprint.py` | immutable symbolic schema, complete record tuple, lookup, and validation |
| C | `tests/deployment/test_robinhood_blueprint.py` | identity, completeness, immutability, purity, topology, address/Base comparison, and mutation tests |
| D | `tests/deployment/test_robinhood_omissions.py` | H-03-owned negative/disabled/deferred/blocked surface tests |

If Phase B is later separately authorized, implementation must remain
unstaged and uncommitted through independent Gate 1 review. Only a later,
separately authorized Gate 1 provenance package may add this corrected
evidence record as a fourth path; it may not change the approved model.
The complete non-relation inventories and R6 explicit typed relation graph
already exist in Phase A and may not be derived, regrouped, or appended in
Phase B. Approved `D-H03-005` and `D-H03-006` must be encoded exactly. No
consumer change is needed. `config/BluePrint.py`,
`config/network_profiles.py`, H-02 tests, defaults, migrations, histories,
manifests, H-08's future topology checker, contracts, interfaces, ABIs,
generated artifacts, and every other file remain outside the ceiling.

The published package completed these historical steps:

1. complete-file independent exact-hash review of the clarified R6 candidate;
2. exact-hash owner approval of `D-H03-004-R6` and the complete package;
3. the authorized provenance-only amendment;
4. independent exact-diff/hash confirmation of the post-amendment bytes; and
5. the authorized two-document feature commit and push at `2c8468a…`.

The current lifecycle correction opens a narrower documentation gate, not the
substantive R6 decision. Required order from this candidate is:

1. complete-file independent exact-hash review of this revised evidence and
   confirmation that the brief remains exactly
   `f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`;
2. fresh owner approval of the revised evidence hash before any follow-up
   commit or integration;
3. separately authorized evidence-only commit;
4. current-`rh` reconciliation and a fresh re-hash of every cited
   integrated authority, while every mutable cross-track worktree artifact
   remains explicitly non-authoritative;
5. separately authorized integration of this one-file lifecycle correction
   into current `rh`;
6. fresh H-03 Phase B exact-lock validation against that corrected integrated
   baseline;
7. complete only the Phase B implementation-boundary reviews required by the
   owner, security, and deployment-tooling reviewers, without flattening or
   closing any of the 18 typed downstream blockers or making their owning
   workstreams implementation prerequisites;
8. separate explicit owner authorization to begin the exact three-file
   Phase B implementation;
9. add only the immutable module and two test files, leaving all three
   unstaged and uncommitted; and
10. run the complete H-03 validation serially and stop for independent Gate 1
    review without staging, commit, push, merge, deployment, or activation.
    Gate 1 re-derives the Phase A
    source-path and relation authorities and treats any ambiguity, invented
    path, class disagreement, or source-proof mismatch as a stop.

## 15. Unresolved facts and downstream deadlines

These facts are intentionally not H-03 owner decisions:

| Fact | Owner | Deadline/effect |
| --- | --- | --- |
| Fresh Ledger action-block implementation/provider/source and proof | S5 | Before CM-008 and every later sequential HQ row can enter an H-05 plan |
| Every concrete default, cadence, timelock, fee, cap, reward, LTV, oracle, and risk value | H-04/S6 plus affected product/risk/security owner | Before H-05 plan freeze; never supplied by H-03 |
| Concrete TrainingWheels launch binding | H-04/S6 plus security/operations | `B-H04-PARAMS`; Charlie accepts an arbitrary target, so no CM-013→CM-006 edge is asserted before binding |
| Concrete `specialStabPoolId` binding by asset | H-04/S6 plus product/risk/security | `B-H04-PARAMS`; any valid VaultBook ID is source-permitted, so no concrete Bravo/MissionControl/AuctionHouse target edge is asserted before binding |
| Exact public deployment/governance/capability handoff references | security/governance/deployment/operations | Before testnet/prod handoff |
| Guarded Stock vault source/artifact/ABI/runtime | Track 8 M2 | Before Stock deployment |
| Guarded Stock vault VaultBook semantic placement | Track 8 plus H-05/protocol review | Before M5/H-05 plan; H-03 assigns no ID |
| Teller and CreditEngine changes | Track 8 M1/M3 | Before M4 composed proof |
| AAPL final identity/feed/runtime/cap freeze and route config | Track 8/oracle/H-04 | Before M5 activation |
| Exact LP artifacts, venue, oracle, and composed proof | product/risk/oracle/H-04/H-05 | Before launch plan can close |
| PSM artifact/runtime/config and activation sequence proof | H-04/H-05/Track 8/risk/security | Before PSM launch activation |
| Rewards validation/monitoring/kill package | rewards/economics/security/operations | `within_seven_day_separately_reviewed_reward_activation`; separate nonautomatic promotion |
| CCIP source/toolchain/registration/remote/capability/supply evidence | Track 1/security/operations | `within_seven_day_separately_reviewed_ccip_promotion`; separate nonautomatic promotion, disabled if incomplete |
| Migration namespaces, order, resume behavior, and registry transactions | H-05 | Before any execution plan |
| Deployed topology and negative reachability | H-08 | After approved deployment fixtures/artifacts exist |
| Clean deployment, exact-token, adversarial, Base regression, smoke/soak, release proof | H-09/independent release reviewers | Before testnet/prod activation |

## 16. Authority conflicts and prohibited-file questions

| Conflict | Controlling resolution |
| --- | --- |
| Historical H-03 status said H-02 was not integrated | The controlling brief now records H-02 integrated and reviewed; no H-02 audit remains an H-03 blocker |
| H-03 brief and older U-015 prose say M0 is open | Current M0 owner packet closes M0; M1–M5 remain open |
| Component matrix/support spec/NEG-033 treat sGREEN inclusion as open or inert | Current M0 requires active chain-native sGREEN and Stability; source makes a real ID-2 artifact mandatory |
| Support spec treats Stability Pool as disabled scaffold | Current M0 requires GREEN Stability Pool active; Stock exclusions remain disabled |
| Component matrix/support spec treat PSM as deferred or launch-disabled | Current M0 selects launch mint/redeem; safe setup remains disabled until redemption-first/mint-last proof |
| Older NEG-036 names CM-003 among disabled scaffolds | CM-003 is removed from that scaffold mutation set and receives a required/no-CCIP assertion |
| Validation-plan NEG-031/NEG-037 assign later H-08 tests in `tests/deployment/test_registry_topology.py`, while H-03 needs pre-deployment schema checks | H-03 owns the differently named schema-mutation analogues in Section 13.1 and does not create or edit the H-08 file; H-08 retains the exact validation-plan names and later deployed/topology proof |
| Older Stock rows consider Simple/Rebase containment | Current Track 8 proposes an isolated guarded vault and rejects a blanket Rebase/shared-module change; the artifact and ID remain blocked |
| Older CCIP wording calls it a launch target | Current M0 makes it nonblocking and separately promoted; CM-051–053/058 remain deferred and disabled if incomplete |
| Integrated Track 8 M1 brief at `332ae2bc…` still carries pre-approval status text, while the owner approved M1 decisions and authorized Phase A | H-03 records only the integrated brief and dated owner provenance. Mutable/untracked M1 evidence is non-authoritative, its current conclusions are unknown to H-03, and `B-T8-M1` remains open |
| Former `ComponentRecord.dependencies` mixed deployment order, replacement facts, and workflow identifiers | Superseded by the `relations` model in Section 7A.3; replacement and future-release facts live in dispositions, blockers, downstream ownership, and evidence |
| `D-H03-004` and R1-R5 schemas/inventories were invalidated or superseded by successive deep reviews | All are superseded by approved `D-H03-004-R6` at the published exact hashes in Section 17; the current status-correction bytes require fresh exact-hash approval, and no earlier inventory is Phase B authority |
| R3 CM-056 used `migration_history/base-mainnet` and invented `migration_history/robinhood` aliases | R6 preserves the exact H-02 roots `migration_history/base-mainnet/v1`, `migration_history/robinhood-mainnet/v1`, and `migration_history/robinhood-testnet/v1`, with `config/network_profiles.py:387`, `:427`, and `:450` as source authority |
| R4a/R4b selected invariant-enforcer orientation and grouped Cartesian expansion | Approved `D-H03-005` requires explicit typed caller-to-callee records, governed-contract-to-authority dependencies, no configuration-writer fan-out, and complete proof for separately typed indirect assertions; Section 7A.3 is fully regenerated |
| R5 `R-282` asserted unsupported EndaomentFunds pause/recovery authority through Switchboard | R6 proves `EndaomentFunds.transfer()` admits only the exact Endaoment address resolved by `Addys._getEndaomentAddr()` through RipeHq, so `R-282` is `CM-047→CM-031` `authority_dependency`; `CM-031→CM-047` remains the separate direct call |
| Source defines global mint construction and setter behavior but no terminal Robinhood state/order | Approved `D-H03-006` fixes the exact Section 10.1 sequence; execution and proof remain blocked and no production action is approved |
| R3 encoded launch-disabled reward surfaces with a seven-day lifecycle | R6 launch-disabled reward rows use `deployed_initial_value`; the possible reward action is separate `P-REWARDS-SEVEN-DAY` at `within_seven_day_separately_reviewed_reward_activation` |
| R5 used two superseded lifecycle values and omitted the CCIP promotion record | R6 uses the exact integrated H-04 eight-value vocabulary, applies `within_seven_day_separately_reviewed_ccip_promotion` only to the six exact CCIP surfaces, and records separate `P-CCIP-SEVEN-DAY` and `P-REWARDS-SEVEN-DAY` actions |
| TrainingWheels and special-StabilityPool source accept configurable addresses/IDs | R6 does not guess concrete relations; both launch bindings remain `B-H04-PARAMS` facts in Section 15 |
| Existing PSM source uses historical reserve-token naming and deploys with auto-deposit `True` | H-03 records only symbolic USDG identity, exact no-yield assertions, and the required governed pre-activation action setting auto-deposit `False`; H-04/H-05/Track 8 must prove compatibility and sequencing without an H-03 source change |

No prohibited file is required to complete the proposed H-03 schema/tests. A
prohibited authority-file revision becomes necessary only if reviewers demand:

- a new CM identity for the guarded Stock vault;
- a concrete VaultBook ID reservation for that artifact;
- restoration of the superseded inert-sGREEN test semantics; or
- a production value or executable consumer mapping in H-03.

In any of those cases, do not begin Phase B; authorize the owning component
matrix/Track 8/H-05/validation-plan revision separately.

## 17. Checkpoint decision dispositions, ordered by blast radius

This table records the final R6 decision dispositions and their exact
boundaries. The current lifecycle correction requests no new substantive H-03
schema decision. All production values and downstream deployment decisions
remain with their owners.

| Decision ID | Disposition / blast radius | Approved or historical content | Current effect |
| --- | --- | --- | --- |
| `D-H03-001` | **APPROVED — High — component and VaultBook identity** | Represent the proposed guarded Stock vault without inventing a CM ID, changing CM-024/025, or assigning a VaultBook ID: `I-STOCK-VAULT-ARTIFACT` is consumed by CM-021/026/030/034, while `I-STOCK-VAULT-SLOT` is consumed only by CM-021 | Track 8/component-matrix/H-05 authority still owns any artifact or ID; Phase B remains unauthorized |
| `D-H03-002` | **APPROVED — High — launch graph and negative tests** | Current-authority launch disposition: CM-003/022 required active; CM-013 launch reward/points/emission actions disabled; CM-048 required with disabled staging and gated launch activation; stale NEG-033 semantics replaced and CM-003 removed from NEG-036's inert-scaffold set. This decision alone owns whether CM-048 is required and how its activation is gated. | No silent use of older inert/deferred language; execution, configuration, activation, and Phase B remain unauthorized |
| `D-H03-003` | **APPROVED — Medium — topology-preserving deployment** | Required artifacts plus exact disabled sub-surfaces for HQ hard-coded rows 11, 12, 15, 16, and 19; required inert BondBooster dependency; required Switchboard Echo; and, because CM-048 is required by `D-H03-002`, preservation of its HQ row 22 semantic and disabled pre-activation topology. This decision cannot authorize, omit, or activate CM-048 and does not override `D-H03-002`. No zero/unrelated placeholder or sparse-registry assumption is allowed. | A shared-source/topology redesign still requires separate authority; Phase B remains unauthorized |
| `D-H03-004` | **SUPERSEDED** | Original schema/API decision. Its still-valid singleton/API/error/address-comparison conclusions are carried into R6; its invalidated schema and crosswalk boundary are not authority | See `D-H03-004-R6` |
| `D-H03-004-R1` | **SUPERSEDED, NEVER APPROVED** | Historical correction proposal containing the overbroad 112-surface, 135-relation, component-wide source-state, and compressed lifecycle designs | See `D-H03-004-R6` |
| `D-H03-004-R2` | **SUPERSEDED, NEVER APPROVED** | Historical 85-surface/130-relation/99-path proposal rejected for mutable M1 authority, PSM/LP lifecycle errors, missing exact-receipt producer coverage, missing constructor/path inputs, inexact proof refs, contradictory evidence fields, and fail-open baseline/drift handling | See `D-H03-004-R6` |
| `D-H03-004-R3` | **SUPERSEDED, NEVER APPROVED** | Historical 92-surface/136-relation/101-path candidate rejected for the incomplete relation graph, inexact CM-056 histories, missing LP trusted-route exclusion, undefined terminal global-mint state, conflated reward lifecycle, stale M0/PSM brief instructions, and impossible approval-hash continuity | See `D-H03-004-R6` |
| `D-H03-004-R4` | **SUPERSEDED, NEVER APPROVED** | R4a/R4b carried 94 surfaces, 103 paths, and other non-relation corrections, but its 43-group/267-edge graph used an unapproved orientation, ambiguous Cartesian proof expansion, reverse admission/configuration edges, omitted direct calls and authority dependencies, and unsupported relations. Rejected brief/evidence hashes are frozen in Sections 3.2 and 18. | See `D-H03-004-R6` |
| `D-H03-005` | **APPROVED — High blast radius, relation schema semantics** | Direct execution/call relations use caller→callee; governed contract→authority uses `authority_dependency`; controller→target requires a proved direct call; configuration writes do not create downstream-consumer edges; registry admission stays in registry records; operational callers remain direct; indirect assertions require a separately typed complete multi-source proof. | R6 encodes the decision; any semantic deviation requires a new owner decision and Phase A review |
| `D-H03-006` | **APPROVED — Critical launch-control ordering** | Disable global minting during staging; configure and verify exact Department tuples; make the PSM grant the final capability-tuple mutation; re-verify; then re-enable global minting only as the final launch activation. | Execution/proof remain blocked; the decision supplies no value, address, role, transaction, deployment, or activation authority |
| `D-H03-004-R5` | **SUPERSEDED, REJECTED, NEVER APPROVED** | R5 carried 94 surfaces, 288 typed relations, and one reward promotion, but independent review rejected unsupported `R-282`, the truncated canonical exclusion rule, and drift from integrated H-04 lifecycle/promotion authority. Rejected hashes are frozen in Sections 3.2 and 18. | See `D-H03-004-R6` |
| `D-H03-004-R6` | **APPROVED AND INTEGRATED — High blast radius, H-03 executable schema and scope boundary** | The owner approved: (a) exact CM-001–060 deployment dispositions, registry constraints, 94 launch/security surfaces, two separate promotion actions with exact CCIP/reward surface sets, deterministic blocker/owner/evidence references, 103 component-qualified path records, 48 symbolic inputs, 24 assertion IDs, and 288 explicit typed relation records; (b) mutable/uncommitted M1 evidence stays non-authoritative and M1 unknown/blocked; (c) LP deposits and PSM activation are launch-blocking, LP zero-LTV/borrow omission/ordinary-only trusted-route exclusion are distinct, source HQ mint and PSM auto-deposit defaults require reviewed staging actions, Teller initial pause remains symbolic, and exact receipt has its own mutation family; (d) the Section 5.2 closed enums/frozen schemas, including the exact continuous launch-disabled convention for the two token CCIP capabilities and zero reward-activation `SurfaceRecord` cardinality; (e) Sections 7A.1–7A.5 and Section 8; (f) approved `D-H03-005` and `D-H03-006` representation, inclusion/exclusion, and proof rules; (g) the corrected brief; (h) the exact-hash/provenance gates and three-file Phase B ceiling with a later conditional Gate 1 evidence path; and (i) retention of `D-H03-001`–`D-H03-003` only where unchanged | Approval controls the exact brief/evidence hashes recorded in the provenance block; publication `2c8468a…`, correction `d65e4db…`, and merge `8e4a965…` establish integration. They do not authorize H-03 Phase B exact-lock status, downstream closure, implementation, or Phase B, and they do not automatically approve this lifecycle correction candidate. |

`D-H03-001` through `D-H03-003` remain approved because their exact
artifact/slot, launch-graph, and topology-preservation conclusions remain
unchanged. R6 changes the schema and representation around those conclusions,
not the conclusions themselves. The owner approved `D-H03-005` and
`D-H03-006`, then approved `D-H03-004-R6` and the complete R6 package at the
exact candidate hashes recorded in the provenance block. Independent review
confirmed the post-amendment evidence hash, and the exact two-document package
was published in feature commit `2c8468a…`.

Like the M1 decision provenance, the `D-H03-005` and `D-H03-006` approvals are
owner-attested authority supplied to this workstream; they are not
independently derivable or verifiable from repository bytes. A cold reviewer
must verify that R6 scopes and represents those attestations correctly, not
claim that Git history proves the approvals.

No substantive `D-H03-004-R6` decision remains open for the approved and
integrated package. The current lifecycle correction is a new byte candidate
because it changes status text outside the former provenance-only block. Its
exact revised hash requires complete-file independent review and fresh owner
approval before any follow-up commit, reconciliation, or integration. That
fresh byte approval must not be
construed as approval of an address, contract artifact, migration, registry
transaction, parameter, role, signer, deployment, configuration, activation,
exact-lock completion, downstream blocker closure, or Phase B.

## 18. Phase A publication status and remaining gates

The substantive R6 Phase A approval checkpoint closed for the published
package. The owner approved `D-H03-004-R6`, including the approved
representations of `D-H03-005` and `D-H03-006`, at brief SHA-256
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`
and pre-provenance evidence SHA-256
`9b8bc27522c24ed40cfadb2e594e450ffab2e4f947c036affac7cf9bdacd46ad`.
The authorized provenance-only amendment and its independent exact-diff/hash
review produced approved post-amendment evidence SHA-256
`c9724a4b85ff0d8e26505133f845a78cf573910a991a2548e1d8e96afeaa592c`.
The exact two-document package was committed and pushed to the R6 feature
branch in commit `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`, tree
`59210354b205f17c996fcdfe6e8af6a7cb756532`, with local/tracking/live feature
parity.

Post-publication review found stale pre-approval status text in the published
evidence. Correcting it necessarily changes bytes outside the designated
provenance-only block. The complete-file correction received independent
exact-hash review and fresh owner approval, was committed and pushed in
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4`, and was integrated through `rh`
merge `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. The approved brief remained
byte-identical, and the published commit was preserved without amendment,
rewrite, or force-push.

Completed historical R6 publication gates:

1. complete-file independent exact-hash review of the clarified R6 candidate;
2. exact-hash owner approval of `D-H03-004-R6` and the complete Phase A
   package;
3. the authorized provenance-only amendment;
4. independent exact-diff/hash confirmation of the post-amendment bytes; and
5. the authorized two-document feature commit and feature-branch push.

Completed 26 July chronology-correction and integration gates:

1. complete-file independent exact-hash review of the chronology-corrected
   evidence, including confirmation that no brief byte changed;
2. fresh owner approval of the corrected evidence hash;
3. evidence-only correction commit `d65e4db…` and feature-remote parity;
4. current-`rh` reconciliation; and
5. integration merge `8e4a965…`.

Final controlling `rh` is
`7098211db5693f986b65ec7a9e897f3518e9538c`, tree
`c07329ed9fcc2dc99afbef3f7888f478024d1ede`. It contains the final H-01
exception-retirement transition. Click, Pygments, and Pymdown Snippets
exceptions are retired; pytest and Pymdown b64 exceptions remain retained and
operative; no GitHub/Dependabot alert closure is claimed.

This lifecycle/provenance correction remains a new one-file candidate. Before
Phase B:

1. independently review its complete-file hash and confirm the brief hash;
2. obtain fresh owner approval of the exact corrected evidence hash;
3. separately authorize its one-file commit, reconciliation, and integration;
4. run fresh H-03 Phase B exact-lock validation on the corrected integrated
   baseline;
5. confirm all 18 blockers remain open and typed, with S5, M1, H-04, H-05,
   and H-06 Phase B remaining non-prerequisites to encoding the model; and
6. obtain separate explicit owner authorization for the exact three-file
   implementation, which must remain unstaged and uncommitted through
   independent Gate 1 review.

Approval of the R6 artifact, feature publication, follow-up correction,
documentation integration, exact-lock validation, downstream review
disposition, and Phase B authorization are distinct gates. None may be
inferred from another. S5, Track 8 M1–M5, H-04/H-05/H-08/H-09, rewards,
oracle, LP, CCIP, security/operations, and every other Section 6.3 blocker
remain open unless their owning review closes them separately.

The current lifecycle correction stops here. It changes only this evidence file and is
left unstaged and uncommitted; the brief remains byte-identical to
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`.
No follow-up commit, push, merge, integration, Phase B module/test, dependency
installation, exact-lock run, production address, endpoint, account,
credential, signer, signature, private role, concrete default/parameter,
migration, manifest, history, ABI, generated artifact, contract change, live
RPC observation, explorer submission, verification, governance action,
deployment, configuration, activation, or external-system write occurred in
this correction. Final controlling `rh` remains
`7098211db5693f986b65ec7a9e897f3518e9538c`, tree
`c07329ed9fcc2dc99afbef3f7888f478024d1ede`.

## 19. Final post-S5 lifecycle reconciliation — 27 July 2026

This section is the controlling post-S5 current-state addendum. It supersedes
only stale lifecycle, provenance, baseline, and S5-status language above. All
pre-existing bytes remain the approved historical record at their stated
baselines; in particular, Sections 5–13, the Section 6.3 blocker register,
Sections 7A.1–7A.5, and the Section 17 substantive owner decisions are not
amended or reinterpreted.

### 19.1 Final integrated authority and reconciliation topology

| Authority | Exact identity and current effect |
| --- | --- |
| final H-01 retirement integration | commit `7098211db5693f986b65ec7a9e897f3518e9538c`, tree `c07329ed9fcc2dc99afbef3f7888f478024d1ede`; dependency gate SHA-256 `8860b81b694d0fd8f1a6bb886b819c13b4817f7f4522ab74a712cad03dbe2582` |
| published H-03 lifecycle correction | commit `6c07396fb9f140328f643ff6672ab62cc19af948`, tree `404da037961c2b15808e81fc1efba677fa9a040e`; evidence SHA-256 `a91c45923450218dc2c52830071d4258bda286187d0275eb429dd46ba5dbf48a` |
| final S5 Gate 2 approval and integration | controlling `rh` commit `81478fe33dfa47a8e135682a047b64949650cb29`, tree `4eb1e5ae690694b3bc1f6248b6e92d8ebb4d2f53`; Ledger SHA-256 `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3`; implementation-record SHA-256 `6ce94f25f00e6924b540378f09ed1a84ce401e6474863b2eae6820437b2f847b` |
| local post-S5 H-03 reconciliation | signed merge `db2beb6ddf7f17b1b5beb2390d3df481e4332cdf`, tree `eae67897cb5e762121a2534a1d0bdf91d5e491b6`; parents, in order, `6c07396fb9f140328f643ff6672ab62cc19af948` and `81478fe33dfa47a8e135682a047b64949650cb29` |

The owner-supplied final S5 Gate 2 approval and integration status controls
this reconciliation. It supersedes only the S5 implementation record's
contemporaneous statements that Gate 2 approval or integration remained
pending; it does not convert source, test, or local validation into deployment
or live-network proof.

The reconciliation merge imported exactly the 24-path S5 delta from the
`7098211…` merge base. That delta has no path overlap with this evidence file
or the controlling H-03 brief. The merge was normal Git ancestry with no
rebase, squash, cherry-pick, amendment, conflict, or history rewrite.

### 19.2 Integrated Ledger source and action-block behavior

Integrated `contracts/data/Ledger.vy` now supplies the approved shared Ledger
implementation:

1. constructor
   `__init__(_ripeHq, _defaults, _actionBlockSource)` accepts only the zero
   address or exact `0x0000000000000000000000000000000000000064`;
2. the selected value is the public immutable `ACTION_BLOCK_SOURCE`;
3. zero selects native `block.number` and makes no external source call;
4. exact `0x64` selects a static raw call to the fixed
   `arbBlockNumber()` selector, captures up to 65 bytes, requires exactly
   32 returned bytes, and decodes one `uint256`;
5. missing code, revert, short, oversized, or incompatible return data fails
   closed at construction and runtime, with no native fallback, `chain.id`
   branch, arbitrary provider, mutable source, or separate mode field; and
6. `checkAndUpdateLastTouch` reads the selected action-block identity once,
   applies the existing equality rejection when `_shouldCheck` is true, writes
   that identity, and then applies the existing locked-account assertion.

The current source locations are
`contracts/data/Ledger.vy:130-134`,
`contracts/data/Ledger.vy:189-205`, and
`contracts/data/Ledger.vy:211-248`. The S5 insertion moved the historical
Ledger constructor proof range used by `R-006`, `R-007`, and `R-085` without
changing any of those three relationships. Their current-source equivalents
are `contracts/data/Ledger.vy:189-200` for `R-006`,
`contracts/data/Ledger.vy:189-205` for `R-007`, and
`contracts/data/Ledger.vy:189-200` plus the unchanged DeptBasics/Addys proofs
for `R-085`. This provenance crosswalk does not add, remove, retype, or amend
a canonical relation record.

### 19.3 `B-S5-LEDGER` disposition

`B-S5-LEDGER` remains open as one of the approved 18 blockers. S5 integration
changes the truth of one historical predicate, but it does not close the
composite blocker:

| S5 dimension | Final post-S5 disposition |
| --- | --- |
| shared Ledger source implementation | satisfied by the integrated Ledger SHA-256 above |
| source architecture and Robinhood provider decision | satisfied at the design level: the only external source is exact `0x64`, and Robinhood must use that source without fallback |
| final Robinhood constructor/provider binding | open: the future H-05 deployment plan and H-06 manifest must bind and verify exact `0x64`, RipeHq/default constructor inputs, the immutable getter, compiler input, creation/runtime identities, and registry placement |
| authentic action-block and deployment proof | open: deployment-time ArbSys/version and receipt agreement, sequencer/multi-transaction behavior, paused registration, empty-state/topology checks, activation boundary, monitoring, and abort/containment evidence remain downstream gates |
| final deployment and release authority | open: no deployment, registration, configuration, activation, signer, transaction, migration execution, or release action is approved |

Accordingly, the Section 6.3 sentence that source implementation and all S5
proof are absent is historical pre-S5 state. Only its source-implementation
subcondition is now satisfied. The blocker ID, owner/co-owner allocation,
deadline, canonical row, CM-008 `blocked` disposition, symbolic
`I-LEDGER-BLOCK-SOURCE`, omitted provider fallback, and no-Base-migration
decision remain unchanged because final binding and downstream proof are not
complete. Closing or retyping that blocker would require a separately
authorized substantive Phase A owner decision.

Every other Section 6.3 blocker is unaffected by S5 and remains open under its
existing owner, deadline, and downstream effect.

### 19.4 H-03 authority and remaining gates

H-03 Phase A remains the controlling immutable model: 60 components,
94 surfaces, 103 source-path records, 288 relations, 18 blockers, 48 symbolic
inputs, 38 registry expectations, 24 negative assertions, and two promotion
records. No topology, PSM, global-mint, LP, Teller, reward, CCIP, registry,
blocker, or substantive owner-decision byte changes in this reconciliation.

H-03 Phase B remains unauthorized and unstarted. Before Phase B, this
one-file append-only evidence candidate requires complete-file independent
exact-hash review, fresh owner approval, and separately authorized
commit/push/integration. Fresh H-03 exact-lock validation against the final
integrated authority and separate file-exact owner authorization for only the
three Phase B implementation paths remain mandatory. Any implementation must
remain unstaged and uncommitted through independent Gate 1 review.

This post-S5 amendment is left unstaged and uncommitted. It authorizes no H-03
implementation, push, `rh` integration, dependency installation, RPC or
secret access, signing, broadcast, migration, deployment, registration,
configuration, activation, governance, or external-system change.
