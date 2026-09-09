# RH hardening mutation-evidence protocol

This protocol controls S2 contract-source mutants and S3 deployment-profile
mutants in the RH hardening pass. Mutations are disposable evidence only. No
production source is edited.

## S2 contract-source criteria

Every claimed contract-source mutant must satisfy all of these checks in one
fresh test process:

1. The unmutated source passes the same scenario.
2. The mutation replaces exactly one intended construct; the test asserts the
   replacement count.
3. The mutated source compiles with the contract's source-governed optimization
   setting and `experimental_codegen=false`.
4. The mutant deploys and the scenario reaches the named invariant path.
5. The named test fails on its intended invariant assertion, rather than
   compilation, authorization, fixture, or unrelated revert noise.
6. The test records the mutated-source SHA-256 and a precise mutation
   description.

The committed test must fail if the mutant unexpectedly survives. Temporary
source copies and generated artifacts stay inside the test's private temporary
directory.

## S3 profile/harness criteria

Every claimed deployment-profile mutant must satisfy all of these checks:

1. The canonical unmodified profile passes its own gate.
2. Exactly one identified profile construct is mutated.
3. The mutated profile fails its own gate for the intended reason.
4. The test records a canonical mutation description and SHA-256.

S3 mutates the offline draft profile, never Ledger or Lootbox production
source. A profile that only fails because its test fixture is missing or
unauthorized does not satisfy S3.

## Execution isolation

Each pytest process explicitly unsets `PYTHON_DOTENV_DISABLED` and all listed
RPC/key variables, uses the exact-lock interpreter, and sets private mode-0700
Boa, XDG, Hypothesis, and pytest temporary directories. Baseline and mutant
scenarios execute in the same fresh process so mutation sensitivity is not
inferred from different environments.

## Evidence fields

The final report records, for every accepted mutation claim:

| Field | Required value |
| --- | --- |
| Work item | `T1`, `G1`, `C4`, `L3a`, or `L3b` |
| Subject | Exact contract or profile path |
| Mutation | Exact replaced construct and replacement |
| Replacement count | `1` |
| Mutated SHA-256 | SHA-256 of the complete mutated source/profile |
| Baseline test | Named passing scenario |
| Mutant test | Named failing scenario |
| Intended failure | The invariant assertion or profile gate that rejected |
| Criteria | Explicit S2 or S3 pass statement |
