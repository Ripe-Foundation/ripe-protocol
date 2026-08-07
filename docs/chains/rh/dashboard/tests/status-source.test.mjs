import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { access, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";
import YAML from "yaml";

import {
  classifyPublicationLifecycle,
  deriveStatusAuthority,
  verifyProposedStatusAuthority,
} from "../scripts/sync-status.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const dashboardRoot = resolve(here, "..");
const repositoryRoot = resolve(dashboardRoot, "../../../..");
const statusPath = resolve(dashboardRoot, "../status.yaml");
const statusRelativePath = "docs/chains/rh/status.yaml";
const generatedPath = resolve(dashboardRoot, "app/status.generated.json");
const handoffPath = resolve(dashboardRoot, "app/handoff/[slug]/handoff.generated.json");
const parameterPath = resolve(repositoryRoot, "config/robinhood-parameters.json");
const execFileAsync = promisify(execFile);
const exactObjectPattern = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const exactCommitPattern = /^[a-f0-9]{40}$/;
const sanitizedTestGitEnvironment = {
  GIT_CONFIG_GLOBAL: "/dev/null",
  GIT_CONFIG_NOSYSTEM: "1",
  GIT_CONFIG_SYSTEM: "/dev/null",
  GIT_OPTIONAL_LOCKS: "0",
  LANG: "C",
  LC_ALL: "C",
  PATH: "/usr/bin:/bin:/usr/sbin:/sbin",
};

async function git(repository, arguments_, options = {}) {
  const { stdout } = await execFileAsync("git", arguments_, {
    cwd: repository,
    ...options,
  });
  return stdout.trim();
}

async function oracleGit(repository, arguments_, options = {}) {
  return await execFileAsync("/usr/bin/git", arguments_, {
    cwd: repository,
    encoding: null,
    env: sanitizedTestGitEnvironment,
    ...options,
  });
}

async function oracleGitText(repository, arguments_, options = {}) {
  const { stdout } = await oracleGit(repository, arguments_, options);
  return stdout.toString("utf8").trim();
}

async function deriveRepositoryAuthorityExpectation() {
  const sourceBytes = await readFile(statusPath);
  const sourceSha256 = createHash("sha256")
    .update(sourceBytes)
    .digest("hex");
  const [
    head,
    objectFormat,
    sourceBlob,
    indexResult,
    sourceStatus,
    worktreeStatus,
  ] =
    await Promise.all([
      oracleGitText(repositoryRoot, [
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
      ]),
      oracleGitText(repositoryRoot, [
        "rev-parse",
        "--show-object-format",
      ]),
      oracleGitText(repositoryRoot, [
        "hash-object",
        "--no-filters",
        "--",
        statusRelativePath,
      ]),
      oracleGit(repositoryRoot, [
        "ls-files",
        "--stage",
        "-z",
        "--",
        statusRelativePath,
      ]),
      oracleGit(repositoryRoot, [
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--",
        statusRelativePath,
      ]),
      oracleGit(repositoryRoot, [
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
      ]),
    ]);

  assert.match(head, exactCommitPattern);
  assert.match(objectFormat, /^sha(?:1|256)$/);
  assert.match(sourceBlob, exactObjectPattern);
  const expectedSourceBlob = createHash(objectFormat)
    .update(Buffer.from(`blob ${sourceBytes.length}\0`))
    .update(sourceBytes)
    .digest("hex");
  assert.equal(sourceBlob, expectedSourceBlob);

  const indexEntries = indexResult.stdout
    .toString("utf8")
    .split("\0")
    .filter(Boolean)
    .map((record) => {
      const match = record.match(
        /^([0-7]{6}) ([a-f0-9]{40}(?:[a-f0-9]{24})?) ([0-3])\t([\s\S]+)$/,
      );
      assert.ok(match);
      assert.equal(match[4], statusRelativePath);
      return {
        blob: match[2],
        stage: Number.parseInt(match[3], 10),
      };
    });
  assert.ok(indexEntries.every(({ stage }) => stage === 0));
  assert.ok(indexEntries.length <= 1);

  const indexEntry = indexEntries[0] ?? null;
  const sourceTracked = indexEntry !== null;
  const sourceModified = sourceStatus.stdout.length > 0;
  const worktreeClean = worktreeStatus.stdout.length === 0;
  let headBlob = null;
  try {
    headBlob = await oracleGitText(repositoryRoot, [
      "rev-parse",
      "--verify",
      `HEAD:${statusRelativePath}`,
    ]);
    assert.match(headBlob, exactObjectPattern);
  } catch (error) {
    assert.equal(error.code, 128);
  }

  if (sourceTracked && !sourceModified && worktreeClean) {
    assert.equal(indexEntry.blob, sourceBlob);
    assert.equal(headBlob, sourceBlob);
    const authorityCommit = await oracleGitText(repositoryRoot, [
      "log",
      "-1",
      "--format=%H",
      "--follow",
      "--",
      statusRelativePath,
    ]);
    assert.match(authorityCommit, exactCommitPattern);
    const authorityBlob = await oracleGitText(repositoryRoot, [
      "rev-parse",
      "--verify",
      `${authorityCommit}:${statusRelativePath}`,
    ]);
    assert.equal(authorityBlob, sourceBlob);
    assert.deepEqual(
      (await oracleGit(
        repositoryRoot,
        ["cat-file", "blob", authorityBlob],
      )).stdout,
      sourceBytes,
    );
    return {
      state: "committed",
      authorityCommit,
      authorityBaseCommit: null,
      sourceSha256,
      buildWorktreeClean: true,
    };
  }

  assert.equal(sourceModified, true);
  assert.equal(worktreeClean, false);
  if (sourceTracked) {
    assert.ok(
      sourceBlob !== indexEntry.blob || indexEntry.blob !== headBlob,
    );
  } else {
    assert.equal(headBlob, null);
  }
  return {
    state: "uncommitted_candidate",
    authorityCommit: null,
    authorityBaseCommit: head,
    sourceSha256,
    buildWorktreeClean: false,
  };
}

async function deriveSubjectContainmentExpectation(
  repository,
  subjectCommit,
) {
  assert.match(subjectCommit, exactCommitPattern);
  const [resolvedSubject, subjectTree, originCommit] = await Promise.all([
    oracleGitText(repository, [
      "rev-parse",
      "--verify",
      `${subjectCommit}^{commit}`,
    ]),
    oracleGitText(repository, [
      "rev-parse",
      "--verify",
      `${subjectCommit}^{tree}`,
    ]),
    oracleGitText(repository, [
      "rev-parse",
      "--verify",
      "refs/remotes/origin/rh^{commit}",
    ]),
  ]);
  assert.equal(resolvedSubject, subjectCommit);
  assert.match(subjectTree, exactObjectPattern);
  assert.match(originCommit, exactCommitPattern);

  let contained;
  try {
    await oracleGit(repository, [
      "merge-base",
      "--is-ancestor",
      subjectCommit,
      originCommit,
    ]);
    contained = true;
  } catch (error) {
    if (error.code !== 1) throw error;
    contained = false;
  }

  if (!contained) {
    return {
      contained: false,
      commitsAfterSubject: null,
      originCommit,
      subjectTree,
    };
  }

  const countOutput = await oracleGitText(repository, [
    "rev-list",
    "--count",
    `${subjectCommit}..${originCommit}`,
  ]);
  const commitsAfterSubject = Number.parseInt(countOutput, 10);
  assert.ok(Number.isInteger(commitsAfterSubject));
  assert.ok(commitsAfterSubject >= 0);
  return {
    contained: true,
    commitsAfterSubject,
    originCommit,
    subjectTree,
  };
}

async function withInheritedGitEnvironment(overrides, callback) {
  const prior = new Map(
    Object.keys(overrides).map((key) => [key, process.env[key]]),
  );
  try {
    for (const [key, value] of Object.entries(overrides)) {
      process.env[key] = value;
    }
    return await callback();
  } finally {
    for (const [key, value] of prior) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
}

async function createAuthorityRepository() {
  const repository = await mkdtemp(resolve(tmpdir(), "rh-status-authority-"));
  await git(repository, ["init", "-b", "rh"]);
  await git(repository, ["config", "user.name", "Status Authority Test"]);
  await git(repository, ["config", "user.email", "status-authority@example.invalid"]);
  await git(repository, ["config", "commit.gpgsign", "false"]);
  await writeFile(resolve(repository, "README.md"), "test repository\n");
  await git(repository, ["add", "README.md"]);
  await git(repository, ["commit", "-m", "Initialize authority test repository"]);
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);
  return repository;
}

async function commitStatusSource(repository, contents = "schema_version: 1\n") {
  const path = resolve(repository, "docs/chains/rh/status.yaml");
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, contents);
  await git(repository, ["add", "docs/chains/rh/status.yaml"]);
  await git(repository, ["commit", "-m", "Add status authority"]);
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);
  return path;
}

async function commitEmpty(repository, message) {
  await git(repository, ["commit", "--allow-empty", "-m", message]);
  return await git(repository, ["rev-parse", "HEAD^{commit}"]);
}

async function assertUncommittedCandidate(repository, path) {
  const authority = await deriveStatusAuthority(repository, path);
  assert.equal(authority.state, "uncommitted_candidate");
  assert.equal(authority.statusAuthorityCommit, null);
  assert.equal(
    authority.statusAuthorityBaseCommit,
    await git(repository, ["rev-parse", "HEAD^{commit}"], {
      env: sanitizedTestGitEnvironment,
    }),
  );
  assert.equal(
    authority.statusFileSha256,
    createHash("sha256").update(await readFile(path)).digest("hex"),
  );
  assert.equal(authority.buildWorktreeClean, false);
  return authority;
}

async function load() {
  const [source, generated, handoff, parameterText] = await Promise.all([
    readFile(statusPath, "utf8"),
    readFile(generatedPath, "utf8"),
    readFile(handoffPath, "utf8"),
    readFile(parameterPath, "utf8"),
  ]);
  return {
    source,
    status: YAML.parse(source),
    generated: JSON.parse(generated),
    handoff: JSON.parse(handoff),
    parameters: JSON.parse(parameterText),
  };
}

test("status.yaml binds its reviewed subject within current rh history", async () => {
  const { status, generated } = await load();
  const [expectedSubject, expectedAuthority] = await Promise.all([
    deriveSubjectContainmentExpectation(
      repositoryRoot,
      status.snapshot.program_subject_commit,
    ),
    deriveRepositoryAuthorityExpectation(),
  ]);
  assert.equal(
    status.snapshot.program_subject_tree,
    expectedSubject.subjectTree,
  );
  assert.equal(
    generated.snapshot.subject_in_origin_history,
    expectedSubject.contained,
  );
  assert.equal(
    generated.snapshot.origin_commits_after_subject,
    expectedSubject.commitsAfterSubject,
  );
  assert.equal(
    generated._generated.origin_rh_commit,
    expectedSubject.originCommit,
  );
  assert.equal(
    generated._generated.subject_in_origin_history,
    expectedSubject.contained,
  );
  assert.equal(
    generated._generated.origin_commits_after_subject,
    expectedSubject.commitsAfterSubject,
  );
  assert.equal(generated.publication.status_authority_state, expectedAuthority.state);
  assert.equal(generated.publication.status_authority_commit, expectedAuthority.authorityCommit);
  assert.equal(generated.publication.status_authority_base_commit, expectedAuthority.authorityBaseCommit);
  assert.equal(generated.publication.status_file_sha256, expectedAuthority.sourceSha256);
  assert.equal(
    generated.publication.source_lifecycle,
    classifyPublicationLifecycle({
      statusAuthorityState: generated.publication.status_authority_state,
      authorityInOriginHistory:
        generated.publication.authority_in_origin_history,
      originCommitsAfterAuthority:
        generated.publication.origin_commits_after_authority,
    }),
  );
  assert.equal(generated.snapshot.build_worktree_clean, expectedAuthority.buildWorktreeClean);
  assert.equal(generated._generated.source_sha256, expectedAuthority.sourceSha256);
  assert.equal(generated.snapshot.program_subject_commit, status.snapshot.program_subject_commit);
  assert.equal(generated.snapshot.program_subject_tree, status.snapshot.program_subject_tree);
  if (expectedAuthority.authorityCommit !== null) {
    assert.notEqual(
      status.snapshot.program_subject_commit,
      expectedAuthority.authorityCommit,
    );
  }
});

test("a subject equal to origin/rh is contained with zero later commits", async () => {
  const repository = await createAuthorityRepository();
  const subjectCommit = await git(repository, [
    "rev-parse",
    "HEAD^{commit}",
  ]);

  const expected = await deriveSubjectContainmentExpectation(
    repository,
    subjectCommit,
  );
  assert.equal(expected.contained, true);
  assert.equal(expected.commitsAfterSubject, 0);
  assert.equal(expected.originCommit, subjectCommit);
});

test("a subject three commits behind origin/rh has exact positive drift", async () => {
  const repository = await createAuthorityRepository();
  const subjectCommit = await git(repository, [
    "rev-parse",
    "HEAD^{commit}",
  ]);
  for (let index = 1; index <= 3; index += 1) {
    await commitEmpty(repository, `Integrated descendant ${index}`);
  }
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);

  const expected = await deriveSubjectContainmentExpectation(
    repository,
    subjectCommit,
  );
  const independentCount = Number.parseInt(
    await oracleGitText(repository, [
      "rev-list",
      "--count",
      `${subjectCommit}..refs/remotes/origin/rh`,
    ]),
    10,
  );
  assert.equal(expected.contained, true);
  assert.equal(expected.commitsAfterSubject, 3);
  assert.equal(expected.commitsAfterSubject, independentCount);
});

test("a later clean descendant retains exact dynamically derived drift", async () => {
  const repository = await createAuthorityRepository();
  const subjectCommit = await git(repository, [
    "rev-parse",
    "HEAD^{commit}",
  ]);
  for (let index = 1; index <= 5; index += 1) {
    await commitEmpty(repository, `Later clean descendant ${index}`);
  }
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);

  const expected = await deriveSubjectContainmentExpectation(
    repository,
    subjectCommit,
  );
  const independentCount = Number.parseInt(
    await oracleGitText(repository, [
      "rev-list",
      "--count",
      `${subjectCommit}..refs/remotes/origin/rh`,
    ]),
    10,
  );
  assert.equal(expected.contained, true);
  assert.ok(expected.commitsAfterSubject > 0);
  assert.equal(expected.commitsAfterSubject, independentCount);
});

test("publication lifecycle distinguishes candidate, feature, integration, and descendant", () => {
  assert.equal(
    classifyPublicationLifecycle({
      statusAuthorityState: "uncommitted_candidate",
      authorityInOriginHistory: null,
      originCommitsAfterAuthority: null,
    }),
    "candidate",
  );
  assert.equal(
    classifyPublicationLifecycle({
      statusAuthorityState: "committed",
      authorityInOriginHistory: false,
      originCommitsAfterAuthority: null,
    }),
    "committed_feature",
  );
  assert.equal(
    classifyPublicationLifecycle({
      statusAuthorityState: "committed",
      authorityInOriginHistory: true,
      originCommitsAfterAuthority: 0,
    }),
    "integrated_rh",
  );
  assert.equal(
    classifyPublicationLifecycle({
      statusAuthorityState: "committed",
      authorityInOriginHistory: true,
      originCommitsAfterAuthority: 3,
    }),
    "later_descendant",
  );
});

test("a subject outside origin/rh history fails closed", async () => {
  const repository = await createAuthorityRepository();
  await git(repository, ["switch", "-c", "reviewed-subject"]);
  const subjectCommit = await commitEmpty(
    repository,
    "Forked reviewed subject",
  );
  await git(repository, ["switch", "rh"]);
  await commitEmpty(repository, "Independent integrated history");
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);

  const expected = await deriveSubjectContainmentExpectation(
    repository,
    subjectCommit,
  );
  assert.equal(expected.contained, false);
  assert.equal(expected.commitsAfterSubject, null);
});

test("an untracked status source is an uncommitted candidate", async () => {
  const repository = await createAuthorityRepository();
  const path = resolve(repository, "docs/chains/rh/status.yaml");
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, "schema_version: untracked\n");

  await assertUncommittedCandidate(repository, path);
});

test("a tracked but modified status source is an uncommitted candidate", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository);
  await writeFile(path, "schema_version: modified\n");

  const indexBlob = (await git(repository, [
    "ls-files",
    "--stage",
    "--",
    "docs/chains/rh/status.yaml",
  ])).split(/\s+/)[1];
  const sourceBlob = await git(repository, ["hash-object", path]);
  assert.notEqual(sourceBlob, indexBlob);
  await assertUncommittedCandidate(repository, path);
});

test("a staged status source is an uncommitted candidate", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository);
  await writeFile(path, "schema_version: staged\n");
  await git(repository, ["add", "docs/chains/rh/status.yaml"]);

  const [indexBlob, headBlob] = await Promise.all([
    git(repository, ["rev-parse", ":docs/chains/rh/status.yaml"]),
    git(repository, ["rev-parse", "HEAD:docs/chains/rh/status.yaml"]),
  ]);
  assert.notEqual(indexBlob, headBlob);
  await assertUncommittedCandidate(repository, path);
});

test("an unmerged status source fails closed", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: base\n");
  await git(repository, ["switch", "-c", "other"]);
  await writeFile(path, "state: other\n");
  await git(repository, ["add", "docs/chains/rh/status.yaml"]);
  await git(repository, ["commit", "-m", "Change status on other"]);
  await git(repository, ["switch", "rh"]);
  await writeFile(path, "state: rh\n");
  await git(repository, ["add", "docs/chains/rh/status.yaml"]);
  await git(repository, ["commit", "-m", "Change status on rh"]);
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);
  await assert.rejects(
    execFileAsync("git", ["merge", "--no-edit", "other"], { cwd: repository }),
  );

  await assert.rejects(
    deriveStatusAuthority(repository, path),
    /unmerged state/i,
  );
});

test("assume-unchanged followed by modified bytes fails closed", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  await git(repository, [
    "update-index",
    "--assume-unchanged",
    "docs/chains/rh/status.yaml",
  ]);
  await writeFile(path, "state: hidden modification\n");

  await assert.rejects(
    deriveStatusAuthority(repository, path),
    /assume-unchanged/i,
  );
});

test("skip-worktree followed by modified bytes fails closed", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  await git(repository, [
    "update-index",
    "--skip-worktree",
    "docs/chains/rh/status.yaml",
  ]);
  await writeFile(path, "state: hidden modification\n");

  await assert.rejects(
    deriveStatusAuthority(repository, path),
    /skip-worktree/i,
  );
});

test("inherited GIT_WORK_TREE cannot hide modified source bytes", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const redirectedWorktree = await mkdtemp(
    resolve(tmpdir(), "rh-status-worktree-redirect-"),
  );
  await mkdir(resolve(redirectedWorktree, "docs/chains/rh"), {
    recursive: true,
  });
  await writeFile(resolve(redirectedWorktree, "README.md"), "test repository\n");
  await writeFile(
    resolve(redirectedWorktree, "docs/chains/rh/status.yaml"),
    "state: committed\n",
  );
  await writeFile(path, "state: intended worktree modification\n");

  await withInheritedGitEnvironment(
    { GIT_WORK_TREE: redirectedWorktree },
    async () => {
      await assertUncommittedCandidate(repository, path);
    },
  );
});

test("inherited GIT_DIR cannot redirect status authority", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const redirectedRepository = await createAuthorityRepository();
  await commitStatusSource(redirectedRepository, "state: committed\n");
  const redirectedGitDirectory = await git(redirectedRepository, [
    "rev-parse",
    "--absolute-git-dir",
  ]);
  await writeFile(path, "state: intended repository modification\n");

  await withInheritedGitEnvironment(
    { GIT_DIR: redirectedGitDirectory },
    async () => {
      await assertUncommittedCandidate(repository, path);
    },
  );
});

test("inherited GIT_INDEX_FILE cannot substitute a hidden alternate index", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const alternateIndexDirectory = await mkdtemp(
    resolve(tmpdir(), "rh-status-index-redirect-"),
  );
  const alternateIndex = resolve(alternateIndexDirectory, "index");
  const alternateEnvironment = {
    ...process.env,
    GIT_INDEX_FILE: alternateIndex,
  };
  await git(repository, ["read-tree", "HEAD"], {
    env: alternateEnvironment,
  });
  await git(
    repository,
    [
      "update-index",
      "--assume-unchanged",
      "docs/chains/rh/status.yaml",
    ],
    { env: alternateEnvironment },
  );
  await writeFile(path, "state: intended index modification\n");

  await withInheritedGitEnvironment(
    { GIT_INDEX_FILE: alternateIndex },
    async () => {
      await assertUncommittedCandidate(repository, path);
    },
  );
});

test("inherited object and configuration redirects cannot alter Git authority", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const redirectedWorktree = await mkdtemp(
    resolve(tmpdir(), "rh-status-config-redirect-"),
  );
  await mkdir(resolve(redirectedWorktree, "docs/chains/rh"), {
    recursive: true,
  });
  await writeFile(resolve(redirectedWorktree, "README.md"), "test repository\n");
  await writeFile(
    resolve(redirectedWorktree, "docs/chains/rh/status.yaml"),
    "state: committed\n",
  );
  await writeFile(path, "state: intended configuration modification\n");

  await withInheritedGitEnvironment(
    {
      GIT_ALTERNATE_OBJECT_DIRECTORIES: resolve(
        redirectedWorktree,
        "objects",
      ),
      GIT_CEILING_DIRECTORIES: "/",
      GIT_COMMON_DIR: resolve(redirectedWorktree, "common"),
      GIT_CONFIG: resolve(redirectedWorktree, "config"),
      GIT_CONFIG_COUNT: "1",
      GIT_CONFIG_GLOBAL: resolve(redirectedWorktree, "global-config"),
      GIT_CONFIG_KEY_0: "core.worktree",
      GIT_CONFIG_SYSTEM: resolve(redirectedWorktree, "system-config"),
      GIT_CONFIG_VALUE_0: redirectedWorktree,
      GIT_OBJECT_DIRECTORY: resolve(redirectedWorktree, "objects"),
      GIT_PREFIX: "redirected/",
    },
    async () => {
      await assertUncommittedCandidate(repository, path);
    },
  );
});

test("repository-local worktree redirection fails closed", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const redirectedWorktree = await mkdtemp(
    resolve(tmpdir(), "rh-status-local-redirect-"),
  );
  await git(repository, ["config", "core.worktree", redirectedWorktree]);

  await assert.rejects(
    deriveStatusAuthority(repository, path),
    /does not match Git's reported worktree/i,
  );
});

test("a clean committed status source resolves its real authority commit", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: committed\n");
  const authorityCommit = await git(repository, ["rev-parse", "HEAD^{commit}"]);
  await writeFile(resolve(repository, "README.md"), "unrelated later commit\n");
  await git(repository, ["add", "README.md"]);
  await git(repository, ["commit", "-m", "Add unrelated later commit"]);
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);
  const currentHead = await git(repository, ["rev-parse", "HEAD^{commit}"]);

  const authority = await deriveStatusAuthority(repository, path);
  assert.equal(authority.state, "committed");
  assert.equal(authority.statusAuthorityCommit, authorityCommit);
  assert.notEqual(authority.statusAuthorityCommit, currentHead);
  assert.match(authority.statusAuthorityCommit, /^[a-f0-9]{40}$/);
  assert.equal(authority.statusAuthorityBaseCommit, null);
  assert.equal(authority.statusFileSha256, createHash("sha256").update(await readFile(path)).digest("hex"));
  assert.equal(authority.buildWorktreeClean, true);
});

test("a proposed authority commit with different source bytes fails closed", async () => {
  const repository = await createAuthorityRepository();
  const path = await commitStatusSource(repository, "state: first\n");
  const firstCommit = await git(repository, ["rev-parse", "HEAD^{commit}"]);
  await writeFile(path, "state: second\n");
  await git(repository, ["add", "docs/chains/rh/status.yaml"]);
  await git(repository, ["commit", "-m", "Replace status authority bytes"]);
  await git(repository, ["update-ref", "refs/remotes/origin/rh", "HEAD"]);
  const secondCommit = await git(repository, ["rev-parse", "HEAD^{commit}"]);
  const sourceBytes = await readFile(path);

  await assert.rejects(
    verifyProposedStatusAuthority(
      repository,
      path,
      sourceBytes,
      firstCommit,
    ),
    /does not contain the exact source bytes/i,
  );
  const authority = await deriveStatusAuthority(repository, path);
  assert.equal(authority.state, "committed");
  assert.equal(authority.statusAuthorityCommit, secondCommit);
});

test("status authority has no manual environment, CLI, or YAML override", async () => {
  const [script, source] = await Promise.all([
    readFile(resolve(dashboardRoot, "scripts/sync-status.mjs"), "utf8"),
    readFile(statusPath, "utf8"),
  ]);
  const status = YAML.parse(source);
  assert.doesNotMatch(script, /process\.env/);
  assert.doesNotMatch(script, /process\.argv\[(?:2|3|4|5)\]/);
  assert.doesNotMatch(script, /\bSTATUS_AUTHORITY\b|--status-authority/);
  assert.match(script, /env: sanitizedGitEnvironment\(\)/);
  assert.match(script, /gitExecutable = "\/usr\/bin\/git"/);
  for (const inheritedVariable of [
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_PREFIX",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
  ]) {
    assert.doesNotMatch(
      script,
      new RegExp(`process\\.env\\.${inheritedVariable}\\b`),
    );
  }
  assert.equal(status.publication.status_authority_state, "build_derived");
  assert.equal(status.publication.status_authority_commit, "build_derived");
  assert.equal(status.publication.status_authority_base_commit, "build_derived");
  assert.equal(status.publication.status_file_sha256, "build_derived");
  assert.equal(status.publication.source_lifecycle, "build_derived");
  assert.equal(status.publication.authority_in_origin_history, "build_derived");
  assert.equal(status.publication.origin_commits_after_authority, "build_derived");
});

test("two generations from identical candidate bytes are deterministic", async () => {
  const paths = [generatedPath, handoffPath];
  await execFileAsync(process.execPath, ["scripts/sync-status.mjs"], { cwd: dashboardRoot });
  const first = await Promise.all(paths.map((path) => readFile(path)));
  await execFileAsync(process.execPath, ["scripts/sync-status.mjs"], { cwd: dashboardRoot });
  const second = await Promise.all(paths.map((path) => readFile(path)));
  assert.deepEqual(second, first);
});

test("all declared current counts are derived and exact", async () => {
  const { status, parameters, handoff } = await load();
  const h04States = status.h04_decisions.rows.reduce((counts, row) => {
    counts[row.state] = (counts[row.state] ?? 0) + 1;
    return counts;
  }, {});
  assert.equal(status.counts.workstreams, status.workstreams.length);
  assert.equal(status.counts.rh_d_decisions, status.decisions.length);
  assert.equal(status.counts.h03_blockers, status.h03_blockers.length);
  assert.equal(status.counts.h04_rows, status.h04_decisions.rows.length);
  assert.equal(status.counts.h04_approved_operative, h04States.approved);
  assert.equal(status.counts.h04_retired_non_operative, h04States.retired_non_operative);
  assert.equal(status.counts.h04_open, h04States.open ?? 0);
  assert.equal(status.counts.binding_schedules, parameters.binding_schedules.length);
  assert.equal(status.counts.hard_gates, status.hard_gates.length);
  assert.equal(status.counts.handoff_documents, Object.keys(handoff).length);
  assert.equal(status.counts.parked_lanes, status.owner_priority_overlay.parked_lanes.length);
  assert.equal(status.counts.live_actions, status.snapshot.live_actions_completed);
});

test("H-04 lifecycle and fail-closed readiness mirror the integrated manifest", async () => {
  const { status, parameters } = await load();
  const approved = parameters.decision_registry.filter((row) => row.status === "approved" && row.operative);
  const retired = parameters.decision_registry.filter((row) => !row.operative);
  assert.deepEqual(status.h04_decisions.approved_ids, approved.map((row) => row.id));
  assert.deepEqual(status.h04_decisions.retired_ids, retired.map((row) => row.id));
  assert.deepEqual(status.h04_decisions.open_ids, []);
  assert.equal(status.h04_decisions.binding_schedule_count, parameters.binding_schedules.length);
  assert.equal(status.h04_decisions.schema_v2_integrated, true);
  assert.equal(status.h04_decisions.defaults_source_authoritative, true);
  assert.equal(status.h04_decisions.configuration_consistent, true);
  assert.equal(status.h04_decisions.deployment_ready, false);
  assert.equal(
    status.h04_decisions.deployment_readiness_blocker_count,
    status.counts.deployment_readiness_blockers,
  );
  await access(resolve(repositoryRoot, "contracts/config/DefaultsRobinhood.vy"));
});

test("the four deferred controls are explicit and absent from machine-facing parameters", async () => {
  const { status, parameters } = await load();
  const controls = status.post_freeze_reconciliation.deleverage_parameter_gap.controls;
  assert.equal(controls.length, status.post_freeze_reconciliation.deleverage_parameter_gap.current_values.length);
  assert.ok(status.post_freeze_reconciliation.deleverage_parameter_gap.current_values.every((value) => value === 0));
  const parameterBytes = JSON.stringify(parameters);
  for (const control of controls) assert.doesNotMatch(parameterBytes, new RegExp(control, "i"));
  assert.equal(status.post_freeze_reconciliation.deleverage_parameter_gap.fixed_by_this_refresh, false);
});

test("deployment-owner readiness, upstream merge, and Base-only boundaries are exact", async () => {
  const { status } = await load();
  assert.equal(
    status.deployment_owner.readiness,
    "Ready to begin deployment preparation.",
  );
  assert.equal(status.deployment_owner.sequence.length, 10);
  assert.deepEqual(
    status.deployment_owner.sequence.map(({ order }) => order),
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  );
  assert.equal(status.deployment_owner.parallel_inputs.length, 2);
  assert.equal(
    status.post_freeze_reconciliation.upstream_pr61_state,
    "merged_closed",
  );
  assert.equal(
    status.post_freeze_reconciliation.upstream_pr61_head,
    "7293cf87c3c5afb06c3aeac90ffb0cd0cd27e253",
  );
  assert.equal(
    status.post_freeze_reconciliation.upstream_pr61_master_merge,
    "91eda49ccd34a25090582aff0695075c4c806011",
  );
  assert.equal(
    status.post_freeze_reconciliation.upstream_base_provenance_paths.length,
    5,
  );
  assert.deepEqual(
    status.post_freeze_reconciliation
      .current_master_rh_pr_touched_path_differences,
    [
      "migration_history/base-mainnet/v1/2026072800-manifest.json",
      "migration_history/base-mainnet/v1/2026072801-manifest.json",
      "migration_history/base-mainnet/v1/current-manifest.json",
      "migrations/base-mainnet/2026072800_DeleverageAuctionHouse.py",
      "tests/conf_core.py",
    ],
  );
  assert.deepEqual(
    Object.keys(
      status.post_freeze_reconciliation.production_blob_parity.contracts,
    ).sort(),
    [
      "contracts/config/SwitchboardDelta.vy",
      "contracts/core/AuctionHouse.vy",
      "contracts/core/Deleverage.vy",
    ],
  );
});

test("decision namespace mirrors the canonical register", async () => {
  const { status } = await load();
  const register = await readFile(resolve(dashboardRoot, "../decision-register.md"), "utf8");
  const canonical = [...register.matchAll(/^### (RH-D\d{3}) — (.+)$/gm)]
    .map((match) => ({ id: match[1], title: match[2].trim() }));
  assert.deepEqual(status.decisions.map(({ id, title }) => ({ id, title })), canonical);
});

test("generated handoff bytes exactly mirror the declared reading paths", async () => {
  const { status, handoff } = await load();
  const readingPaths = [...new Set(Object.values(status.reading_paths).flat()
    .filter((value) => typeof value === "string" && value.startsWith("docs/")))];
  assert.equal(readingPaths.length, status.counts.handoff_documents);
  assert.deepEqual(Object.keys(handoff).sort(), readingPaths.map((path) => basename(path)).sort());
  for (const path of readingPaths) {
    assert.equal(handoff[basename(path)].source, path);
    assert.deepEqual(Buffer.from(handoff[basename(path)].content, "utf8"), await readFile(resolve(repositoryRoot, path)));
  }
});

test("generated JSON stays ignored and untracked", async () => {
  for (const path of [
    "docs/chains/rh/dashboard/app/status.generated.json",
    "docs/chains/rh/dashboard/app/handoff/[slug]/handoff.generated.json",
  ]) {
    await execFileAsync("git", ["check-ignore", "-q", path], { cwd: repositoryRoot });
    const { stdout } = await execFileAsync("git", ["ls-files", "--", path], { cwd: repositoryRoot });
    assert.equal(stdout.trim(), "");
  }
});

test("non-editable dashboard package and hosting sources match the overlay authority", async () => {
  for (const [path, expectedSha256] of [
    [
      "docs/chains/rh/dashboard/package.json",
      "c37112d84586971da76c5e4e7fa8a3bcc9caa32bbc3ed28915e73d7bf7f58295",
    ],
    [
      "docs/chains/rh/dashboard/package-lock.json",
      "7d5572ae2bea667824a0f302ff782e6b0c13b8b9f97c5b0fce6cd14319421695",
    ],
    [
      "docs/chains/rh/dashboard/.openai/hosting.json",
      "9ccfdab2f03d743ef25155ebad1e9ddd3e10f18432569d86980bd031f70f24a5",
    ],
  ]) {
    const local = await readFile(resolve(repositoryRoot, path));
    const actualSha256 = createHash("sha256").update(local).digest("hex");
    assert.equal(actualSha256, expectedSha256, `${path} exact-byte SHA-256 drift`);
  }
});
