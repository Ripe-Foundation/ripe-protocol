import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import YAML from "yaml";

const here = dirname(fileURLToPath(import.meta.url));
const rhDocs = resolve(here, "../..");
const paths = {
  start: resolve(rhDocs, "START-HERE.md"),
  agent: resolve(rhDocs, "AGENT-HANDOFF.md"),
  readiness: resolve(rhDocs, "deployment-owner-readiness.md"),
  quickstart: resolve(rhDocs, "deployment-owner-quickstart.md"),
  productionCorrection: resolve(rhDocs, "rh-production-vyper-remediation.md"),
  synthesis: resolve(rhDocs, "reassessment-and-qualification-synthesis.md"),
  curve: resolve(rhDocs, "curve-launch-activation.md"),
  curveMigration: resolve(rhDocs, "curve-launch-migration-handoff.md"),
  deleverage: resolve(rhDocs, "smart-contract-changes/deleverage.md"),
  priorities: resolve(rhDocs, "current-owner-priorities.md"),
  register: resolve(rhDocs, "decision-register.md"),
  summary: resolve(rhDocs, "../rh-summary.md"),
  readme: resolve(rhDocs, "dashboard/README.md"),
  status: resolve(rhDocs, "status.yaml"),
};

async function readAll() {
  return Object.fromEntries(await Promise.all(
    Object.entries(paths).map(async ([key, path]) => [key, await readFile(path, "utf8")]),
  ));
}

test("all local Markdown links in the durable handoff resolve", async () => {
  let checked = 0;
  for (const file of Object.values(paths).filter((path) => path.endsWith(".md"))) {
    const markdown = await readFile(file, "utf8");
    for (const match of markdown.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
      const target = match[1].split("#", 1)[0];
      if (!target || /^(https?:|mailto:)/.test(target)) continue;
      await access(resolve(dirname(file), decodeURIComponent(target)));
      checked += 1;
    }
  }
  assert.ok(checked > 0);
});

test("the canonical quick-start binds the current subject and lifecycle facts", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  for (const document of [
    documents.quickstart,
    documents.readme,
  ]) {
    assert.match(document, new RegExp(status.snapshot.program_subject_commit));
    assert.match(document, new RegExp(status.snapshot.program_subject_tree));
    assert.match(document, /Ready to begin deployment preparation\./);
    assert.match(document, /nothing\s+(?:is|has been)\s+deployed|no .*deployment/is);
    assert.match(document, /DefaultsRobinhood\.vy.*exists.*compiles/is);
    assert.match(document, /configuration_consistent=true/is);
    assert.match(document, /deployment_ready=false/is);
    assert.match(document, new RegExp(String(status.counts.h03_blockers)));
    assert.match(document, new RegExp(String(status.counts.deployment_readiness_blockers)));
    assert.match(document, /H-05.*deterministic/is);
    assert.match(document, /H-06.*class|H-06.*operator\/storage/is);
  }
});

test("source ownership gives constructor and immutable bindings precedence over getter exposure", async () => {
  const { quickstart } = await readAll();
  assert.match(
    quickstart,
    /constructor arguments, immutable identities, deployment-produced\s+addresses, and external address bindings are owned by `config\/BluePrint\.py`/i,
  );
  assert.match(quickstart, /even when a Defaults getter later returns them/i);
  assert.match(
    quickstart,
    /Product and configuration values encoded directly in Defaults getter bodies\s+are owned by `contracts\/config\/DefaultsRobinhood\.vy`/i,
  );
  assert.match(
    quickstart,
    /All other non-Defaults deployment inputs are owned by `config\/BluePrint\.py`/i,
  );
  for (const identity of [
    "ContributorTemplate",
    "TrainingWheels",
    "RIPE",
    "GREEN",
    "sGREEN",
    "USDG",
    "WETH",
  ]) {
    assert.match(quickstart, new RegExp(identity));
  }
  assert.match(quickstart, /Do not restore the historical SteakHouse USDG constructor input/i);
  assert.doesNotMatch(quickstart, /If a value is returned by a Defaults getter/i);
});

test("current accepted architecture matches the bounded Curve launch topology", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  assert.deepEqual(
    status.post_freeze_reconciliation.profile1_launch_input_reconciliation.price_desk_registry,
    {
      1: { semantic: "Chainlink", state: "selected" },
      2: { semantic: "Curve", state: "selected_green_only" },
      3: { semantic: "BlueChipYield", state: "blueprint_selected_but_not_deployed_by_candidate" },
      4: { semantic: "Pyth", state: "empty" },
      5: { semantic: "Stork", state: "empty" },
    },
  );
  assert.deepEqual(
    status.post_freeze_reconciliation.profile1_launch_input_reconciliation.priority_price_source_ids,
    [1, 2],
  );
  assert.match(documents.productionCorrection, /priority price sources are `\[1, 2\]`/i);
  assert.match(documents.productionCorrection, /BlueChipYield.*not deployed/is);
  assert.match(documents.quickstart, /USDG has no Curve feed/i);
  assert.match(
    documents.quickstart,
    /GREEN ->\s+Curve GREEN\/USDG -> PriceDesk -> Chainlink USDG/i,
  );
  const synthesisRole = status.document_roles.find(
    ({ file }) => file === "docs/chains/rh/reassessment-and-qualification-synthesis.md",
  );
  assert.match(synthesisRole.role, /Historical pre-remediation/i);
  const correctionRole = status.document_roles.find(
    ({ file }) => file === "docs/chains/rh/rh-production-vyper-remediation.md",
  );
  assert.match(correctionRole.role, /Current correction record/i);
});

test("the current Deleverage disposition preserves parked zero controls without stale Defaults claims", async () => {
  const { deleverage, status: statusSource } = await readAll();
  const status = YAML.parse(statusSource);
  assert.match(
    deleverage,
    new RegExp(status.post_freeze_reconciliation.corrected_pr61_integration_ancestor),
  );
  assert.match(
    deleverage,
    new RegExp(status.post_freeze_reconciliation.production_blob_parity.contracts["contracts/core/Deleverage.vy"]),
  );
  assert.match(deleverage, /DefaultsRobinhood\.vy.*exists.*compiles.*source-authoritative/is);
  assert.match(deleverage, /all four remain zero and deferred/is);
  assert.match(deleverage, /outside the\s+currently selected launch value projection/is);
  assert.match(deleverage, /No Deleverage configuration has\s+been applied onchain/is);
  assert.match(deleverage, /Every Deleverage task remains parked unless\s+an explicit owner instruction reopens it/is);
  assert.doesNotMatch(deleverage, /DefaultsRobinhood\.vy.*absent/is);
});

test("legacy entrypoints are redirects and the start page is only a router", async () => {
  const documents = await readAll();
  for (const document of [documents.agent, documents.readiness]) {
    assert.match(document, /sole canonical.*deployment-owner/is);
    assert.match(document, /deployment-owner-quickstart\.md/);
    assert.doesNotMatch(document, /[a-f0-9]{40}/);
    assert.doesNotMatch(document, /configuration_consistent|deployment_ready|blockers=|python /i);
  }
  assert.match(documents.start, /only a router/i);
  assert.match(documents.start, /deployment-owner-quickstart\.md/);
  assert.doesNotMatch(documents.start, /[a-f0-9]{40}/);
});

test("counts and current priority boundaries remain consistent", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  assert.equal(status.owner_priority_overlay.parked_lanes.length, status.counts.parked_lanes);
  assert.equal(status.owner_priority_overlay.effective_at, "2026-08-01");
  assert.match(documents.priorities, /\*\*Effective:\*\* 1 August 2026/);
  assert.equal((documents.priorities.match(/^### \d+\./gm) ?? []).length, status.counts.parked_lanes);
  assert.match(documents.priorities, /CCIP.*parked/is);
  assert.match(documents.priorities, /zero-backing settlement.*bad-debt policy.*parked/is);
  assert.match(
    documents.priorities,
    /does not authorize production-contract\s+edits.*testnet or production actions/is,
  );
  assert.match(documents.quickstart, new RegExp(`${status.counts.h04_rows} rows`));
  assert.match(documents.quickstart, new RegExp(`All ${status.counts.h03_blockers} canonical H-03 blockers`));
  assert.match(documents.quickstart, new RegExp(`${status.counts.deployment_readiness_blockers}`));
});

test("canonical register records the post-freeze H-04, H-05, H-06, and S4 lifecycle", async () => {
  const { register } = await readAll();
  const statuses = new Map(
    [...register.matchAll(/^### (RH-D\d{3}) — .+?\n\n\*\*Status:\*\* ([\s\S]*?)(?=\n\n)/gm)]
      .map((match) => [match[1], match[2].replace(/\n/g, " ")]),
  );
  assert.match(statuses.get("RH-D011"), /zero-cooldown.*closed.*corrected PR #61.*integrated/i);
  assert.match(statuses.get("RH-D015"), /source authority integrated.*21 decisions approved.*zero open/i);
  assert.match(statuses.get("RH-D016"), /eight-file imperative.*candidate.*review.*execution.*unauthorized/i);
  assert.match(statuses.get("RH-D017"), /candidate macOS\/APFS operator\/storage-class qualification integrated/i);
});

test("the private dashboard remains an optional repository-derived mirror", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  assert.match(status.publication.dashboard_url, /^https:\/\//);
  assert.match(documents.readme, /YAML ledger is the sole current\s+machine-readable authority/i);
  assert.match(documents.readme, /generated files are validation output only/i);
  assert.match(documents.readme, /do not edit, stage,\s+or commit them/i);
});
