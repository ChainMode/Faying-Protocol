import test from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import http from "node:http";
import { resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
import {
  FayingGuardianEngine,
  Grade,
  ROGUE_FAY_ACTION_FORBIDDEN,
  RogueFayError,
  createFayingHttpMiddleware,
  createFayingSigner,
  createGuardianClient,
  createGuardianDaemonServer,
  withFayingGuard,
  wrapMcpToolHandlers,
} from "../src/index.mjs";

const ROOT = resolve(import.meta.dirname, "..");

test("Default-deny ROGUE_FAY, FAYING_REQUEST non-self-activation, T2 Atomic Action wildcards rejected, and P7 finite TTL", async () => {
  let clockMs = 1_700_000_000_000;
  const engine = new FayingGuardianEngine({ nowMs: () => clockMs });
  const hpSigner = createFayingSigner("test-hp-seed-example-01");
  const ifayId = "ifay_alpha_worker";
  const hpId = "hid_alpha_human_prime";

  // 1. Default-deny ROGUE_FAY before any mandate
  assert.equal(engine.getStatus(ifayId).behaviorState, "ROGUE_FAY");

  const guardedTool = withFayingGuard(
    async (x) => ({ ok: true, x }),
    engine,
    {
      fayId: ifayId,
      domain: "calendar.api.example",
      action: "calendar:event:create",
      minGrade: Grade.G2_MODERATE,
    },
  );

  await assert.rejects(
    () => guardedTool({ title: "Board sync" }),
    (err) => err instanceof RogueFayError && err.code === ROGUE_FAY_ACTION_FORBIDDEN && err.protocolErrorCode === 1001,
  );

  // 2. iFay-submitted FAYING_REQUEST MUST NOT transition out of ROGUE_FAY without Human Prime witness
  const reqRes = engine.submitFayingRequest({
    initiatorFayId: ifayId,
    targetHumanPrime: hpId,
    proposedScope: { domains: ["calendar.api.example"], actions: ["calendar:event:create"] },
    proposedGrade: Grade.G2_MODERATE,
  });
  assert.equal(reqRes.ok, true);
  assert.equal(reqRes.behaviorState, "ROGUE_FAY");
  await assert.rejects(() => guardedTool({ title: "Still rogue" }), {
    code: ROGUE_FAY_ACTION_FORBIDDEN,
  });

  // 3. Wildcard action rejected (T2 Atomic Action) & infinite TTL rejected (P7)
  assert.equal(
    engine.initiateFaying({
      humanPrimeId: hpId,
      humanSigner: hpSigner,
      fayId: ifayId,
      scope: { domains: ["calendar.api.example"], actions: ["calendar:*"] },
    }).ok,
    false,
  );
  assert.equal(
    engine.initiateFaying({
      humanPrimeId: hpId,
      humanSigner: hpSigner,
      fayId: ifayId,
      ttlMs: Number.POSITIVE_INFINITY,
      scope: { domains: ["calendar.api.example"], actions: ["calendar:event:create"] },
    }).ok,
    false,
  );

  // 4. Explicit Human Prime Faying Action transitions to FAYING with invocation budget = 2
  const initRes = engine.initiateFaying({
    humanPrimeId: hpId,
    humanSigner: hpSigner,
    fayId: ifayId,
    grade: Grade.G2_MODERATE,
    ttlMs: 60_000,
    maxStalenessMs: 10_000,
    fayingRequestRef: reqRes.request.requestId,
    scope: {
      domains: ["calendar.api.example"],
      actions: ["calendar:event:create"],
      budget: { maxInvocations: 2 },
    },
  });
  assert.equal(initRes.ok, true);
  assert.equal(engine.getStatus(ifayId).behaviorState, "FAYING");

  const out1 = await guardedTool({ title: "Meeting 1" });
  assert.equal(out1.ok, true);
  const out2 = await guardedTool({ title: "Meeting 2" });
  assert.equal(out2.ok, true);

  // 3rd call exceeds maxInvocations=2 -> fails closed with ROGUE_FAY_ACTION_FORBIDDEN (1012 E_BUDGET_EXCEEDED)
  await assert.rejects(
    () => guardedTool({ title: "Meeting 3" }),
    (err) => err.code === ROGUE_FAY_ACTION_FORBIDDEN && err.protocolErrorCode === 1012,
  );

  // Out-of-scope action & higher-grade action fail closed
  await assert.rejects(
    () =>
      guardedTool(
        { title: "Delete all" },
        { action: "calendar:event:delete" },
      ),
    (err) => err.code === ROGUE_FAY_ACTION_FORBIDDEN && err.protocolErrorCode === 1003,
  );
  await assert.rejects(
    () =>
      guardedTool(
        { title: "High autonomy" },
        { minGrade: Grade.G4_AUTONOMOUS },
      ),
    (err) => err.code === ROGUE_FAY_ACTION_FORBIDDEN && err.protocolErrorCode === 1004,
  );

  // Human View feed recorded structured T3 disclosure fields
  const hv = engine.getHumanViewFeed({ fayId: ifayId });
  const disclosures = hv.filter((e) => e.eventType === "EXTERNAL_ACTION_DISCLOSURE");
  assert.equal(disclosures.length, 2);
  assert.equal(disclosures[0].action, "calendar:event:create");
  assert.deepEqual(disclosures[0].affectedResources, ["calendar.api.example"]);
  engine.shutdown();
});

test("Heartbeat freshness, Endorsed Mandate offline convergence & hard stop, and <5ms timer-driven heartbeat expiry abort", async () => {
  // Part A: Deterministic clock check for Endorsed Mandate window & hard stop
  let now = 2_000_000_000_000;
  const detEngine = new FayingGuardianEngine({ nowMs: () => now });
  const hpSigner = createFayingSigner("test-hp-endorsed-example");
  const ifayId = "ifay_drone_pilot";

  const engaged = detEngine.initiateFaying({
    humanPrimeId: "hp_pilot_01",
    humanSigner: hpSigner,
    fayId: ifayId,
    grade: Grade.G3_LOOSE,
    ttlMs: 120_000,
    maxStalenessMs: 5_000,
    scope: {
      domains: ["drone.flight.local"],
      actions: ["drone:waypoint:fly", "drone:rtl:hover"],
    },
    endorsement: {
      enabled: true,
      endorsedScope: {
        domains: ["drone.flight.local"],
        actions: ["drone:rtl:hover"],
      },
      endorsedGrade: Grade.G1_STRICT,
      endorsedLifetimeMs: 15_000,
      offlineRevocationPolicy: "stop-and-audit",
    },
  });
  assert.equal(engaged.ok, true);

  // Advance past maxStalenessMs (5s -> +8s): enters DISCONNECTED_ENDORSED
  now += 8_000;
  const stDisc = detEngine.getStatus(ifayId);
  assert.equal(stDisc.mandateState, "DISCONNECTED_ENDORSED");
  assert.equal(stDisc.effectiveGrade, Grade.G1_STRICT);

  // Non-endorsed action `drone:waypoint:fly` blocked during disconnection, endorsed `drone:rtl:hover` allowed!
  assert.equal(
    detEngine.authorizeExternalAction({
      fayId: ifayId,
      domain: "drone.flight.local",
      action: "drone:waypoint:fly",
    }).allowed,
    false,
  );
  assert.equal(
    detEngine.authorizeExternalAction({
      fayId: ifayId,
      domain: "drone.flight.local",
      action: "drone:rtl:hover",
      minGrade: Grade.G1_STRICT,
    }).allowed,
    true,
  );

  // Advance past endorsedLifetimeMs (15s) -> hard stop into ROGUE_FAY!
  now += 20_000;
  assert.equal(detEngine.getStatus(ifayId).behaviorState, "ROGUE_FAY");
  detEngine.shutdown();

  // Part B: Real wall-clock heartbeat expiry aborts an in-flight external tool automatically!
  const liveEngine = new FayingGuardianEngine();
  liveEngine.initiateFaying({
    humanPrimeId: "hp_live_timer",
    humanSigner: hpSigner,
    fayId: "ifay_live_timer",
    grade: Grade.G2_MODERATE,
    ttlMs: 10_000,
    maxStalenessMs: 60, // 60ms heartbeat window
    scope: { domains: ["api.live.example"], actions: ["stream:upload"] },
  });

  const guardedUpload = withFayingGuard(
    async (_input, { signal }) => {
      await new Promise((resolveDone, rejectDone) => {
        const t = setTimeout(resolveDone, 2000);
        signal.addEventListener("abort", () => {
          clearTimeout(t);
          rejectDone(signal.reason);
        });
      });
      return "unexpected";
    },
    liveEngine,
    { fayId: "ifay_live_timer", domain: "api.live.example", action: "stream:upload" },
  );

  const startMs = performance.now();
  await assert.rejects(
    () => guardedUpload({}),
    (err) => err instanceof RogueFayError && err.code === ROGUE_FAY_ACTION_FORBIDDEN && err.protocolErrorCode === 1005,
  );
  const elapsed = performance.now() - startMs;
  // Should trip right around the 60ms heartbeat deadline (far below the 2000ms handler timeout!)
  assert.ok(elapsed >= 45 && elapsed < 250, `Expected heartbeat abort near 60ms, got ${elapsed}ms`);
  liveEngine.shutdown();
});

test("1.1-cofay Delegated Stewardship, Dual-Signed Stewardship Transfer, and Upstream G0 Cascade", async () => {
  const engine = new FayingGuardianEngine();
  const hpASigner = createFayingSigner("steward-a-example-seed");
  const hpBSigner = createFayingSigner("steward-b-example-seed");
  const mgrASigner = createFayingSigner("mgr-a-example-seed");
  const mgrBSigner = createFayingSigner("mgr-b-example-seed");

  engine.initiateFaying({
    humanPrimeId: "hid_steward_a",
    humanSigner: hpASigner,
    fayId: "ifay_manager_a",
    grade: Grade.G3_LOOSE,
    ttlMs: 120_000,
    maxStalenessMs: 30_000,
    scope: {
      domains: ["support.portal.example", "billing.portal.example"],
      actions: ["ticket:respond", "refund:issue"],
    },
  });
  engine.initiateFaying({
    humanPrimeId: "hid_steward_b",
    humanSigner: hpBSigner,
    fayId: "ifay_manager_b",
    grade: Grade.G3_LOOSE,
    ttlMs: 120_000,
    maxStalenessMs: 30_000,
    scope: {
      domains: ["support.portal.example"],
      actions: ["ticket:respond"],
    },
  });

  // Hop > 1 and grade amplification rejected
  assert.equal(
    engine.delegateCoFayStewardship({
      managerFayId: "ifay_manager_a",
      managerSigner: mgrASigner,
      subjectCoFayId: "cofay_support_desk",
      stewardEntity: "org_support_coop",
      charterScope: { domains: ["support.portal.example"], actions: ["ticket:respond"] },
      scope: { domains: ["support.portal.example"], actions: ["ticket:respond"] },
      grade: Grade.G4_AUTONOMOUS, // > G3 manager grade
    }).ok,
    false,
  );

  // Valid single-hop stewardship
  const del = engine.delegateCoFayStewardship({
    managerFayId: "ifay_manager_a",
    managerSigner: mgrASigner,
    subjectCoFayId: "cofay_support_desk",
    stewardEntity: "org_support_coop",
    charterScope: { domains: ["support.portal.example"], actions: ["ticket:respond"] },
    scope: { domains: ["support.portal.example"], actions: ["ticket:respond"] },
    grade: Grade.G2_MODERATE,
  });
  assert.equal(del.ok, true);
  assert.equal(del.accountableHumanPrime, "hid_steward_a");

  // Atomic dual-signed transfer from steward A -> steward B
  const xfer = engine.transferCoFayStewardship({
    cofayId: "cofay_support_desk",
    fromSteward: "org_support_coop",
    fromHumanPrime: "hid_steward_a",
    fromStewardSigner: hpASigner,
    toSteward: "org_next_coop",
    toHumanPrime: "hid_steward_b",
    toStewardSigner: hpBSigner,
    nextManagerFayId: "ifay_manager_b",
  });
  assert.equal(xfer.ok, true);
  assert.equal(engine.getStatus("cofay_support_desk").accountableHumanPrime, "hid_steward_b");

  // Upstream G0 Emergency Brake on hid_steward_b cascades to both ifay_manager_b AND cofay_support_desk!
  const brake = engine.triggerG0EmergencyBrake({ targetId: "hid_steward_b" });
  assert.deepEqual(brake.haltedFays, ["cofay_support_desk", "ifay_manager_b"]);
  assert.equal(engine.getStatus("cofay_support_desk").behaviorState, "ROGUE_FAY");
  engine.shutdown();
});

test("Live Guardian HTTP+SSE Daemon, HTTP Middleware, MCP Tool Wrapper, and <5ms Cross-Endpoint G0 In-Flight Circuit Breaker", async () => {
  const daemon = createGuardianDaemonServer();
  const daemonInfo = await daemon.listen();
  const remoteClient = createGuardianClient({ url: daemonInfo.url });
  await remoteClient.connectPushStream();

  // Protect an Express-style HTTP server AND an MCP server tool registry with the remote GuardianClient
  const httpGuard = createFayingHttpMiddleware(remoteClient, {
    domain: "crm.internal.example",
    resolveAction: () => "crm:lead:update",
  });
  const apiServer = http.createServer((req, res) => {
    httpGuard(req, res, () => {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ ok: true, mandate: req.faying }));
    });
  });
  await new Promise((r) => apiServer.listen(0, "127.0.0.1", r));
  const apiBase = `http://127.0.0.1:${apiServer.address().port}`;

  const mcpTools = wrapMcpToolHandlers(
    {
      deployRelease: {
        action: "mcp:deploy:release",
        minGrade: Grade.G2_MODERATE,
        handler: async ({ tag }) => {
          await new Promise((r) => setTimeout(r, 3000).unref());
          return { deployed: tag };
        },
      },
      pingCluster: async () => ({ healthy: true }),
    },
    remoteClient,
    { fayId: "ifay_devops_bot", domain: "k8s.cluster.example" },
  );

  try {
    // 1. Blocked while ROGUE_FAY on both HTTP API (403) and MCP tool
    const blockedHttp = await fetch(`${apiBase}/leads`, {
      method: "POST",
      headers: { "x-faying-subject": "ifay_devops_bot" },
    });
    assert.equal(blockedHttp.status, 403);
    const blockedJson = await blockedHttp.json();
    assert.equal(blockedJson.error, ROGUE_FAY_ACTION_FORBIDDEN);

    await assert.rejects(() => mcpTools.pingCluster({}), {
      code: ROGUE_FAY_ACTION_FORBIDDEN,
    });

    // 2. Engage Faying State via HTTP daemon endpoint
    const engageHttp = await fetch(`${daemonInfo.url}/faying/engage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        humanPrimeId: "hid_devops_lead",
        humanSeed: "devops-lead-example-seed",
        fayId: "ifay_devops_bot",
        grade: Grade.G3_LOOSE,
        ttlMs: 120_000,
        maxStalenessMs: 20_000,
        scope: {
          domains: ["crm.internal.example", "k8s.cluster.example"],
          actions: ["crm:lead:update", "mcp:tool:pingCluster", "mcp:deploy:release"],
        },
      }),
    });
    assert.equal(engageHttp.status, 200);

    // HTTP route and fast MCP tool now succeed
    const okHttp = await fetch(`${apiBase}/leads`, {
      method: "POST",
      headers: { "x-faying-subject": "ifay_devops_bot" },
    });
    assert.equal(okHttp.status, 200);
    const pingRes = await mcpTools.pingCluster({});
    assert.equal(pingRes.healthy, true);

    // 3. Start long-running MCP deployment (3000ms) and trigger G0 Brake -> verify <5ms abort!
    const inFlightDeploy = mcpTools.deployRelease.handler({ tag: "v2.4.0" });
    await new Promise((r) => setTimeout(r, 30));

    const t0 = performance.now();
    daemon.engine.triggerG0EmergencyBrake({
      targetId: "ifay_devops_bot",
      reason: "Emergency production freeze",
    });

    let abortElapsedMs = 0;
    await assert.rejects(async () => {
      try {
        await inFlightDeploy;
      } finally {
        abortElapsedMs = performance.now() - t0;
      }
    }, { code: ROGUE_FAY_ACTION_FORBIDDEN });

    assert.ok(
      abortElapsedMs < 5,
      `Expected G0 SSE push circuit-breaker abort in <5ms, took ${abortElapsedMs.toFixed(2)}ms`,
    );

    // Subsequent call fails closed in <5ms too
    const tSub = performance.now();
    await assert.rejects(() => mcpTools.pingCluster({}), {
      code: ROGUE_FAY_ACTION_FORBIDDEN,
    });
    assert.ok(performance.now() - tSub < 5);
  } finally {
    await remoteClient.close();
    apiServer.closeAllConnections?.();
    await new Promise((r) => apiServer.close(r));
    await daemon.close();
  }
});

test("faying-guardian CLI binary: status, engage, heartbeat, human-view, and brake", async () => {
  const daemon = createGuardianDaemonServer();
  const info = await daemon.listen();
  const cliPath = resolve(ROOT, "bin/faying-guardian.mjs");

  async function runCli(args) {
    const { stdout } = await execFileAsync(process.execPath, [cliPath, ...args], {
      encoding: "utf8",
    });
    return JSON.parse(stdout);
  }

  try {
    const stBefore = await runCli(["status", "--fay", "ifay_cli_agent", "--url", info.url]);
    assert.equal(stBefore.status.behaviorState, "ROGUE_FAY");

    const engageOut = await runCli([
      "engage",
      "--hp",
      "hid_cli_human",
      "--fay",
      "ifay_cli_agent",
      "--domains",
      "files.local",
      "--actions",
      "file:read",
      "--url",
      info.url,
    ]);
    assert.equal(engageOut.behaviorState, "FAYING");

    const hbOut = await runCli(["heartbeat", "--fay", "ifay_cli_agent", "--url", info.url]);
    assert.equal(hbOut.ok, true);

    const hvOut = await runCli(["human-view", "--fay", "ifay_cli_agent", "--url", info.url]);
    assert.ok(hvOut.events.length >= 1);

    const brakeOut = await runCli(["brake", "--target", "ifay_cli_agent", "--url", info.url]);
    assert.equal(brakeOut.behaviorState, "ROGUE_FAY");
  } finally {
    await daemon.close();
  }
});
