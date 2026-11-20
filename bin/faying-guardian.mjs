#!/usr/bin/env node
import { Grade, createGuardianDaemonServer } from "../src/index.mjs";

function parseArgs(argv) {
  const positional = [];
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg.startsWith("--")) {
      const eq = arg.indexOf("=");
      if (eq !== -1) {
        flags[arg.slice(2, eq)] = arg.slice(eq + 1);
      } else {
        const next = argv[i + 1];
        if (next && !next.startsWith("--")) {
          flags[arg.slice(2)] = next;
          i += 1;
        } else {
          flags[arg.slice(2)] = true;
        }
      }
    } else {
      positional.push(arg);
    }
  }
  return { cmd: positional[0] ?? "help", flags };
}

function getDaemonUrl(flags) {
  return String(
    flags.url ?? process.env.FAYING_GUARDIAN_URL ?? "http://127.0.0.1:4780",
  ).replace(/\/+$/, "");
}

function printUsage() {
  console.log(`faying-guardian — Live Faying State Guardian Daemon, Human View & G0 Red Emergency Brake

Usage:
  faying-guardian serve [--host 127.0.0.1] [--port 4780]
  faying-guardian status --fay <ifay_...|cofay_...> [--url http://127.0.0.1:4780]
  faying-guardian engage --hp <hid_...|hp_...> --fay <ifay_...> --domains <d1,d2> --actions <a1,a2> [--grade 2] [--ttl-ms 300000] [--heartbeat-ms 15000] [--url http://127.0.0.1:4780]
  faying-guardian heartbeat --fay <ifay_...|cofay_...> [--url http://127.0.0.1:4780]
  faying-guardian brake --target <ifay_...|cofay_...|hid_...> [--reason "Emergency stop"] [--url http://127.0.0.1:4780]
  faying-guardian human-view [--fay <ifay_...>] [--limit 20] [--url http://127.0.0.1:4780]
`);
}

async function main() {
  const { cmd, flags } = parseArgs(process.argv.slice(2));
  if (cmd === "help" || flags.help) {
    printUsage();
    return;
  }

  if (cmd === "serve") {
    const daemon = createGuardianDaemonServer({
      host: String(flags.host ?? "127.0.0.1"),
      port: Number(flags.port ?? 4780),
    });
    const info = await daemon.listen();
    console.log(
      JSON.stringify(
        {
          ok: true,
          service: "faying-guardian-daemon",
          url: info.url,
          sseStream: `${info.url}/events`,
        },
        null,
        2,
      ),
    );
    const shutdown = async () => {
      await daemon.close();
      process.exit(0);
    };
    process.on("SIGINT", shutdown);
    process.on("SIGTERM", shutdown);
    return;
  }

  const baseUrl = getDaemonUrl(flags);

  if (cmd === "status") {
    const fayId = encodeURIComponent(String(flags.fay ?? ""));
    const res = await fetch(`${baseUrl}/status?fayId=${fayId}`);
    const json = await res.json();
    console.log(JSON.stringify(json, null, 2));
    if (!res.ok) process.exitCode = 1;
    return;
  }

  if (cmd === "engage") {
    const domains = String(flags.domains ?? "external-tool")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const actions = String(flags.actions ?? "tool:invoke")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const res = await fetch(`${baseUrl}/faying/engage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        humanPrimeId: String(flags.hp ?? "hp_demo_prime"),
        humanSeed: String(flags["hp-seed"] ?? "cli-human-prime-example-seed"),
        fayId: String(flags.fay ?? ""),
        grade: Number(flags.grade ?? Grade.G2_MODERATE),
        ttlMs: Number(flags["ttl-ms"] ?? 300_000),
        maxStalenessMs: Number(flags["heartbeat-ms"] ?? 15_000),
        scope: { domains, actions },
      }),
    });
    const json = await res.json();
    console.log(JSON.stringify(json, null, 2));
    if (!res.ok || !json.ok) process.exitCode = 1;
    return;
  }

  if (cmd === "heartbeat") {
    const res = await fetch(`${baseUrl}/faying/heartbeat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ fayId: String(flags.fay ?? "") }),
    });
    const json = await res.json();
    console.log(JSON.stringify(json, null, 2));
    if (!res.ok || !json.ok) process.exitCode = 1;
    return;
  }

  if (cmd === "brake") {
    const res = await fetch(`${baseUrl}/faying/brake`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        targetId: String(flags.target ?? flags.fay ?? ""),
        reason: String(flags.reason ?? "CLI G0 Red Emergency Brake"),
      }),
    });
    const json = await res.json();
    console.log(JSON.stringify(json, null, 2));
    if (!res.ok || !json.ok) process.exitCode = 1;
    return;
  }

  if (cmd === "human-view") {
    const params = new URLSearchParams();
    if (flags.fay) params.set("fayId", String(flags.fay));
    if (flags.limit) params.set("limit", String(flags.limit));
    const res = await fetch(`${baseUrl}/human-view?${params.toString()}`);
    const json = await res.json();
    console.log(JSON.stringify(json, null, 2));
    if (!res.ok) process.exitCode = 1;
    return;
  }

  printUsage();
  process.exitCode = 1;
}

main();
