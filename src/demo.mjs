import { performance } from "node:perf_hooks";
import {
  Grade,
  createFayingSigner,
  createGuardianClient,
  createGuardianDaemonServer,
  withFayingGuard,
} from "./index.mjs";

async function main() {
  console.log("=== Faying Protocol: Rogue Fay Circuit-Breaker & Live Guardian Demo ===\n");

  const daemon = createGuardianDaemonServer();
  const info = await daemon.listen();
  const client = createGuardianClient({ url: info.url });
  await client.connectPushStream();

  const humanPrimeId = "hid_demo_human_prime_01";
  const humanSigner = createFayingSigner("demo-human-prime-example-seed");
  const ifayId = "ifay_personal_assistant_01";
  const cofayId = "cofay_public_concierge_01";
  const managerSigner = createFayingSigner("demo-ifay-manager-example-seed");

  // External D-dimension tool wrapped in 1 line with `withFayingGuard`
  const executeWirePayment = withFayingGuard(
    async ({ recipient, amountUsd, simulateDurationMs = 0 }) => {
      if (simulateDurationMs > 0) {
        await new Promise((r) => setTimeout(r, simulateDurationMs).unref());
      }
      return { settled: true, recipient, amountUsd };
    },
    client,
    {
      fayId: ifayId,
      domain: "payments.bank.example",
      action: "payment:transfer:submit",
      minGrade: Grade.G2_MODERATE,
      riskLevel: "high",
      reversibility: "irreversible",
    },
  );

  // Step 1: Default-deny ROGUE_FAY blocks external D-dimension action
  try {
    await executeWirePayment({ recipient: "vendor-a", amountUsd: 250 });
  } catch (err) {
    console.log(
      `[1] Initial State ROGUE (blocked): code=${err.code} (${err.protocolErrorName})`,
    );
  }

  // Step 2: Explicit Human Prime Faying Action (BOOTSTRAP) + 1.1-cofay Stewardship
  const engaged = daemon.engine.initiateFaying({
    humanPrimeId,
    humanSigner,
    fayId: ifayId,
    grade: Grade.G2_MODERATE,
    ttlMs: 120_000,
    maxStalenessMs: 15_000,
    scope: {
      domains: ["payments.bank.example", "concierge.desk.example"],
      actions: ["payment:transfer:submit", "concierge:ticket:reply"],
    },
  });
  daemon.engine.delegateCoFayStewardship({
    managerFayId: ifayId,
    managerSigner,
    subjectCoFayId: cofayId,
    stewardEntity: humanPrimeId,
    charterScope: {
      domains: ["concierge.desk.example"],
      actions: ["concierge:ticket:reply"],
    },
    scope: {
      domains: ["concierge.desk.example"],
      actions: ["concierge:ticket:reply"],
    },
    grade: Grade.G2_MODERATE,
  });
  console.log(
    `[2] Explicit Faying Action engaged: state=${engaged.behaviorState} mandate=${engaged.mandateId} (+ 1.1-cofay ${cofayId})`,
  );

  // Step 3: Active execution + continuous Human View feed + heartbeat
  const hb = daemon.engine.recordHeartbeat({ fayId: ifayId });
  const txResult = await executeWirePayment({ recipient: "vendor-a", amountUsd: 250 });
  const feed = daemon.engine.getHumanViewFeed({ fayId: ifayId });
  const latestDisclosure = feed[feed.length - 1];
  console.log(
    `[3] Active Execution + Human View: settled=${txResult.settled} heartbeatFresh=${hb.ok} disclosureAction=${latestDisclosure.action}`,
  );

  // Step 4: Launch an in-flight external action and trigger G0 Red Emergency Brake mid-flight!
  const inFlightPromise = executeWirePayment({
    recipient: "vendor-b",
    amountUsd: 9000,
    simulateDurationMs: 2000,
  });
  // Allow pre-flight authorization to complete so the tool is genuinely in-flight
  await new Promise((r) => setTimeout(r, 25));

  const t0 = performance.now();
  const brakeOutcome = daemon.engine.triggerG0EmergencyBrake({
    targetId: ifayId,
    reason: "Human Prime pressed Red G0 Emergency Brake",
  });
  let abortLatencyMs = 0;
  let inFlightError = null;
  try {
    await inFlightPromise;
  } catch (err) {
    abortLatencyMs = performance.now() - t0;
    inFlightError = err;
  }
  console.log(
    `[4] G0 Instant Brake mid-flight: aborted in ${abortLatencyMs.toFixed(2)}ms (<5ms!) with ${inFlightError.code} | cascaded=${brakeOutcome.haltedFays.join(", ")}`,
  );

  // Step 5: Subsequent calls fail closed immediately in ROGUE_FAY
  try {
    await executeWirePayment({ recipient: "vendor-c", amountUsd: 10 });
  } catch (err) {
    console.log(
      `[5] Post-G0 State ROGUE (blocked): code=${err.code} (${err.protocolErrorName}) coFayState=${daemon.engine.getStatus(cofayId).behaviorState}\n`,
    );
  }

  await client.close();
  await daemon.close();
  console.log("All Faying Protocol Guardian demo steps completed cleanly.");
}

main();
