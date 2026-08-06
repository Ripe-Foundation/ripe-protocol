import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import YAML from "yaml";

const here = dirname(fileURLToPath(import.meta.url));
const workflowPath = resolve(
  here,
  "../../../../../.github/workflows/rh-handoff-dashboard.yml",
);
const checkoutSha = "11d5960a326750d5838078e36cf38b85af677262";
const setupNodeSha = "49933ea5288caeca8642d1e84afbd3f7d6820020";

test("path-scoped CI enforces the complete handoff validation contract", async () => {
  const workflowText = await readFile(workflowPath, "utf8");
  const workflow = YAML.parse(workflowText);
  const expectedPaths = [
    "docs/chains/rh/**",
    "docs/chains/rh-summary.md",
    ".github/workflows/rh-handoff-dashboard.yml",
  ];
  const steps = workflow.jobs.validate.steps;

  assert.deepEqual(workflow.on.workflow_dispatch, {});
  assert.deepEqual(workflow.on.pull_request.paths, expectedPaths);
  assert.deepEqual(workflow.on.push.branches, ["rh"]);
  assert.deepEqual(workflow.on.push.paths, expectedPaths);
  assert.deepEqual(workflow.permissions, { contents: "read" });
  assert.equal(workflow.jobs.validate["timeout-minutes"], 10);
  assert.equal(
    workflow.jobs.validate.defaults.run["working-directory"],
    "docs/chains/rh/dashboard",
  );

  assert.equal(
    steps.find(
      (step) => step.uses === `actions/checkout@${checkoutSha}`,
    ).with[
      "fetch-depth"
    ],
    0,
  );
  assert.match(
    steps.find((step) => step.name === "Refresh the integration reference").run,
    /refs\/heads\/rh:refs\/remotes\/origin\/rh/,
  );
  assert.equal(
    steps.find(
      (step) => step.uses === `actions/setup-node@${setupNodeSha}`,
    ).with[
      "node-version"
    ],
    "22.13.0",
  );
  assert.equal(
    steps.filter((step) => step.uses?.startsWith("actions/")).length,
    2,
  );
  for (const step of steps.filter((entry) => entry.uses?.startsWith("actions/"))) {
    assert.match(
      step.uses,
      /^actions\/[^@]+@[a-f0-9]{40}$/,
      `${step.name} must use a full immutable commit SHA`,
    );
  }
  assert.match(
    workflowText,
    new RegExp(`actions/checkout@${checkoutSha.replaceAll(".", "\\.")} # v4`),
  );
  assert.match(
    workflowText,
    new RegExp(`actions/setup-node@${setupNodeSha.replaceAll(".", "\\.")} # v4`),
  );
  assert.ok(steps.some((step) => step.run === "npm ci"));
  assert.ok(steps.some((step) => step.run === "npm test"));
  assert.ok(steps.some((step) => step.run === "npm run lint"));
});
