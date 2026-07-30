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

test("primary entrypoints bind the current subject and lifecycle facts", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  for (const document of [
    documents.start,
    documents.agent,
    documents.readiness,
    documents.readme,
  ]) {
    assert.match(document, new RegExp(status.snapshot.program_subject_commit));
    assert.match(document, new RegExp(status.snapshot.program_subject_tree));
    assert.match(document, /PR #61.*integrated/is);
    assert.match(document, /PR #61.*merged and closed/is);
    assert.match(document, /Ready to begin deployment preparation\./);
    assert.match(document, /nothing\s+(?:is|has been)\s+deployed|no .*deployment/is);
    assert.match(document, /DefaultsRobinhood\.vy.*absent.*fail-closed/is);
    assert.match(document, /H-05.*deterministic/is);
    assert.match(document, /H-06.*class|H-06.*operator\/storage/is);
  }
  for (const control of status.post_freeze_reconciliation.deleverage_parameter_gap.controls) {
    for (const document of [
      documents.start,
      documents.agent,
      documents.readiness,
      documents.readme,
    ]) {
      assert.match(document, new RegExp(control));
    }
  }
});

test("counts and current priority boundaries remain consistent", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  assert.equal(status.owner_priority_overlay.parked_lanes.length, status.counts.parked_lanes);
  assert.equal((documents.priorities.match(/^### \d+\./gm) ?? []).length, status.counts.parked_lanes);
  assert.match(documents.priorities, /CCIP.*parked/is);
  assert.match(documents.priorities, /zero-backing settlement.*bad-debt policy.*parked/is);
  assert.match(
    documents.priorities,
    /does not authorize production-contract\s+edits.*testnet or production actions/is,
  );
  assert.match(documents.readiness, /Smart-contract reassessment/is);
  assert.match(
    documents.readiness,
    /Robinhood fork and external-integration qualification/is,
  );
  assert.match(documents.agent, new RegExp(`${status.counts.workstreams} workstreams`));
  assert.match(documents.agent, new RegExp(`${status.counts.rh_d_decisions}\\s+RH-D decisions`));
  assert.match(documents.agent, new RegExp(`All ${status.counts.h03_blockers} H-03 blockers remain open`));
});

test("canonical register records the post-freeze H-04, H-05, H-06, and S4 lifecycle", async () => {
  const { register } = await readAll();
  const statuses = new Map(
    [...register.matchAll(/^### (RH-D\d{3}) — .+?\n\n\*\*Status:\*\* ([\s\S]*?)(?=\n\n)/gm)]
      .map((match) => [match[1], match[2].replace(/\n/g, " ")]),
  );
  assert.match(statuses.get("RH-D011"), /zero-cooldown.*closed.*corrected PR #61.*integrated/i);
  assert.match(statuses.get("RH-D015"), /schema v2 integrated.*20 decisions approved.*zero open/i);
  assert.match(statuses.get("RH-D016"), /deterministic blocked planning integrated.*execution.*unauthorized/i);
  assert.match(statuses.get("RH-D017"), /candidate macOS\/APFS operator\/storage-class qualification integrated/i);
});

test("the private dashboard remains an optional repository-derived mirror", async () => {
  const documents = await readAll();
  const status = YAML.parse(documents.status);
  for (const document of [documents.start, documents.agent, documents.register, documents.summary]) {
    assert.match(document, new RegExp(status.publication.dashboard_url.replaceAll(".", "\\.")));
  }
  assert.match(documents.readme, /YAML ledger is the sole current\s+machine-readable authority/i);
  assert.match(documents.readme, /generated files are validation output only/i);
  assert.match(documents.readme, /do not edit, stage,\s+or commit them/i);
});
