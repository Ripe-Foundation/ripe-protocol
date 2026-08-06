import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import YAML from "yaml";
import { derivePublicationLifecycle } from "../app/status-view.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const dashboardRoot = resolve(here, "..");
const repositoryRoot = resolve(dashboardRoot, "../../../..");

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${Math.random()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(new URL(path, "http://localhost/"), { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

function normalizeText(value) {
  return value.replace(/<[^>]+>/g, " ").replaceAll("&#x27;", "'")
    .replaceAll("&quot;", '"').replaceAll("&amp;", "&")
    .replaceAll("&#x2F;", "/").replace(/\s+/g, " ").trim();
}

async function statusAndGenerated() {
  const [statusText, generatedText] = await Promise.all([
    readFile(resolve(dashboardRoot, "../status.yaml"), "utf8"),
    readFile(resolve(dashboardRoot, "app/status.generated.json"), "utf8"),
  ]);
  return { status: YAML.parse(statusText), generated: JSON.parse(generatedText) };
}

function assertRenderedStatusAuthority(text, publication) {
  assert.match(
    publication.status_authority_state,
    /^(?:committed|uncommitted_candidate)$/,
  );
  assert.match(publication.status_file_sha256, /^[a-f0-9]{64}$/);
  assert.ok(text.includes(publication.status_file_sha256));

  if (publication.status_authority_state === "uncommitted_candidate") {
    assert.equal(publication.status_authority_commit, null);
    assert.match(
      publication.status_authority_base_commit,
      /^[a-f0-9]{40}$/,
    );
    assert.ok(text.includes("Status authority Uncommitted candidate"));
    assert.ok(
      text.includes(
        `Base commit ${publication.status_authority_base_commit}`,
      ),
    );
    assert.doesNotMatch(text, /Status authority [a-f0-9]{7,12}\b/i);
    return;
  }

  assert.equal(publication.status_authority_state, "committed");
  assert.match(publication.status_authority_commit, /^[a-f0-9]{40}$/);
  assert.equal(publication.status_authority_base_commit, null);
  assert.ok(
    text.includes(
      `Status authority ${publication.status_authority_commit}`,
    ),
  );
  assert.doesNotMatch(text, /Status authority Uncommitted candidate/i);
  assert.doesNotMatch(text, /\bBase commit [a-f0-9]{40}\b/i);
}

test("renders metadata and the exact current posture from status.yaml", async () => {
  const [response, { status, generated }] = await Promise.all([render(), statusAndGenerated()]);
  assert.equal(response.status, 200);
  const html = await response.text();
  const text = normalizeText(html);
  assert.match(html, /<title>Ripe × Robinhood — Private Program Status<\/title>/i);
  assert.ok(text.includes(status.snapshot.hero_lead));
  assert.ok(text.includes(status.snapshot.hero_emphasis));
  assert.ok(text.includes(status.snapshot.launch_readiness));
  assert.ok(text.includes(status.snapshot.program_subject_commit.slice(0, 8)));
  assert.ok(
    text.includes(derivePublicationLifecycle(generated.publication).label),
  );
  assert.ok(text.includes(generated.snapshot.build_worktree_clean ? "Verified" : "Unverified"));
  assert.ok(text.includes("Status SHA-256"));
  assert.ok(
    text.includes(
      "Corrected PR #61 integration does not authorize deployment, migration execution, configuration, activation, or release.",
    ),
  );
  assert.ok(
    text.includes(
      "PR #61 is merged and closed on master; its production contract changes are integrated into rh.",
    ),
  );
  assertRenderedStatusAuthority(text, generated.publication);
});

test("renders every lifecycle row and current count", async () => {
  const [response, { status }] = await Promise.all([render(), statusAndGenerated()]);
  const text = normalizeText(await response.text());
  for (const value of Object.values(status.counts)) assert.ok(text.includes(String(value)));
  for (const row of status.workstreams) {
    for (const value of [row.id, row.name, row.plain_language_scope, row.why_it_matters,
      row.current_phase, row.implementation_state, row.integration_state, row.review_state,
      row.owner_decision_state, row.deployment_release_state, row.exact_next_action,
      row.authority, ...row.remaining_blockers]) {
      assert.ok(text.includes(normalizeText(value)), `${row.id} missing rendered value: ${value}`);
    }
  }
});

test("renders the data-derived critical path, hard gates, and parked lanes", async () => {
  const [response, { status }] = await Promise.all([render(), statusAndGenerated()]);
  const text = normalizeText(await response.text());
  for (const step of status.critical_path) {
    for (const value of [step.internal_reference, step.plain_language_scope, step.why_it_matters, step.detail]) {
      assert.ok(text.includes(normalizeText(value)));
    }
  }
  for (const gate of status.hard_gates) {
    for (const value of [gate.id, gate.plain_language_scope, gate.why_it_matters, gate.effect]) {
      assert.ok(text.includes(normalizeText(value)));
    }
  }
  assert.ok(text.includes(`${status.owner_priority_overlay.parked_lanes.length} lanes are parked and nonblocking.`));
  for (const lane of status.owner_priority_overlay.parked_lanes) assert.ok(text.includes(lane.id));
});

test("renders the complete deployment-owner sequence and parallel inputs", async () => {
  const [response, { status }] = await Promise.all([render(), statusAndGenerated()]);
  const text = normalizeText(await response.text());
  assert.ok(text.includes(status.deployment_owner.readiness));
  assert.ok(text.includes(normalizeText(status.deployment_owner.authority_boundary)));
  assert.equal(status.deployment_owner.sequence.length, 10);
  for (const step of status.deployment_owner.sequence) {
    for (const value of [step.label, step.owns, step.output, step.boundary]) {
      assert.ok(text.includes(normalizeText(value)));
    }
  }
  for (const input of status.deployment_owner.parallel_inputs) {
    assert.ok(text.includes(input.name));
    assert.ok(text.includes(input.gate_effect));
  }
});

test("renders H-04 lifecycle and the four-control machine gap", async () => {
  const [response, { status }] = await Promise.all([render(), statusAndGenerated()]);
  const text = normalizeText(await response.text());
  const approved = status.h04_decisions.rows.filter(({ state }) => state === "approved").length;
  const retired = status.h04_decisions.rows.filter(({ state }) => state === "retired_non_operative").length;
  const open = status.h04_decisions.rows.filter(({ state }) => state === "open").length;
  assert.ok(text.includes(`${status.h04_decisions.rows.length} H-04 rows: ${approved} approved, ${retired} retired, ${open} open.`));
  for (const row of status.h04_decisions.rows) assert.ok(text.includes(row.id));
  for (const path of status.h04_decisions.implementation_file_surface) assert.ok(text.includes(path));
  for (const control of status.post_freeze_reconciliation.deleverage_parameter_gap.controls) assert.ok(text.includes(control));
});

test("renders authorization boundaries, residuals, and every RH-D decision", async () => {
  const [response, { status }] = await Promise.all([render(), statusAndGenerated()]);
  const text = normalizeText(await response.text());
  for (const boundary of status.authorization_boundaries) assert.ok(text.includes(normalizeText(boundary)));
  for (const residual of status.accepted_residuals) assert.ok(text.includes(residual.id));
  for (const decision of status.decisions) {
    assert.ok(text.includes(decision.id));
    assert.ok(text.includes(decision.title));
    assert.ok(text.includes(normalizeText(decision.summary)));
  }
});

test("serves every declared local handoff document byte-for-byte", async () => {
  const { status } = await statusAndGenerated();
  const readingDocuments = [...new Set(Object.values(status.reading_paths).flat()
    .filter((value) => typeof value === "string" && value.startsWith("docs/")))];
  assert.equal(readingDocuments.length, status.counts.handoff_documents);
  for (const documentPath of readingDocuments) {
    const filename = basename(documentPath);
    const [response, sourceBytes] = await Promise.all([
      render(`/handoff/${encodeURIComponent(filename)}`),
      readFile(resolve(repositoryRoot, documentPath)),
    ]);
    assert.equal(response.status, 200);
    assert.deepEqual(Buffer.from(await response.arrayBuffer()), sourceBytes);
  }
});
