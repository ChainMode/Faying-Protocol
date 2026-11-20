import {
  FayingGuardianEngine,
  Grade,
  ROGUE_FAY_ACTION_FORBIDDEN,
  RogueFayError,
  createGuardianClient,
} from "./faying-guardian-engine.mjs";

function normalizeClient(guardianOrEngineOrUrl) {
  if (
    guardianOrEngineOrUrl &&
    typeof guardianOrEngineOrUrl.authorizeExternalAction === "function" &&
    typeof guardianOrEngineOrUrl.onRogueTransition === "function" &&
    !(guardianOrEngineOrUrl instanceof FayingGuardianEngine)
  ) {
    return guardianOrEngineOrUrl;
  }
  return createGuardianClient(guardianOrEngineOrUrl);
}

/**
 * Drop-in `Rogue Fay` Circuit-Breaker Guard Wrapper (`withFayingGuard(handler, guardianClient, options)`).
 *
 * Designed for LangChain tools, MCP tool servers, OpenAI/Gemini tool runners, and custom backends:
 * 1. Pre-flight checks active `Faying State` + atomic `action` & `domain` scope + `minGrade` + TTL + heartbeat freshness;
 * 2. Emits mandatory T3 `Human View` disclosure;
 * 3. Subscribes a per-invocation `AbortController` to the Guardian's real-time `ROGUE_TRANSITION` channel
 *    so if `Human Prime` triggers **G0 Emergency Brake** or heartbeat expires mid-execution, the in-flight
 *    call aborts and rejects in `<5ms` with `ROGUE_FAY_ACTION_FORBIDDEN`!
 */
export function withFayingGuard(handler, guardianClient, options = {}) {
  if (typeof handler !== "function") {
    throw new TypeError("withFayingGuard expects a function handler as its first argument");
  }
  const client = normalizeClient(guardianClient);

  return async function guardedExternalAction(input, runtimeContext = {}) {
    const fayId = String(
      runtimeContext.fayId ??
        (typeof input === "object" && input !== null ? input.fayId : undefined) ??
        options.fayId ??
        "",
    ).trim();

    if (!fayId) {
      throw new RogueFayError("Missing fayId for guarded external D-dimension action", {
        reason: "Every D-dimension external action must identify the acting iFay or coFay",
      });
    }

    const domain = String(runtimeContext.domain ?? options.domain ?? "external-tool");
    const action = String(
      runtimeContext.action ?? options.action ?? (handler.name ? `tool:${handler.name}` : "tool:invoke"),
    );
    const minGrade = runtimeContext.minGrade ?? options.minGrade ?? Grade.G1_STRICT;

    const abortController = new AbortController();
    let unsubscribe = () => {};

    const abortRacePromise = new Promise((_, rejectAbort) => {
      unsubscribe = client.onRogueTransition(fayId, (rogueErr) => {
        const finalErr =
          rogueErr instanceof RogueFayError
            ? rogueErr
            : new RogueFayError(String(rogueErr?.message ?? "G0 Emergency Halt"), { fayId });
        if (!abortController.signal.aborted) {
          abortController.abort(finalErr);
        }
        rejectAbort(finalErr);
      });
    });
    // Prevent unhandled rejection when normal completion wins Promise.race
    abortRacePromise.catch(() => {});

    try {
      const auth = await client.authorizeExternalAction({
        fayId,
        domain,
        action,
        minGrade,
        costUnits: options.costUnits ?? 1,
        riskLevel: options.riskLevel ?? "normal",
        reversibility: options.reversibility ?? "reversible",
        affectedResources: options.affectedResources ?? [domain],
        uncertaintyFlags: options.uncertaintyFlags ?? [],
        summary:
          typeof options.describeAction === "function"
            ? options.describeAction(input)
            : options.summary ?? `Invoking ${action} on ${domain}`,
      });

      if (!auth.allowed) {
        throw auth.error;
      }

      if (abortController.signal.aborted) {
        throw abortController.signal.reason;
      }

      const executionContext = {
        ...runtimeContext,
        fayId,
        signal: abortController.signal,
        mandate: auth.mandate,
        disclosure: auth.disclosure,
      };

      return await Promise.race([
        Promise.resolve().then(() => handler(input, executionContext)),
        abortRacePromise,
      ]);
    } finally {
      unsubscribe();
    }
  };
}

/**
 * Drop-in Node `http` / Express `(req, res, next)` & Fetch `protectFetch` middleware
 * enforcing `Faying State` before external HTTP routes execute.
 */
export function createFayingHttpMiddleware(guardianClient, options = {}) {
  const client = normalizeClient(guardianClient);

  async function middleware(req, res, next) {
    const rawHeader = req.headers?.["x-faying-subject"] ?? req.headers?.["x-fayid-presenter"];
    const fayId = String(
      (Array.isArray(rawHeader) ? rawHeader[0] : rawHeader) ?? options.fayId ?? "",
    ).trim();

    const domain =
      typeof options.resolveDomain === "function"
        ? options.resolveDomain(req)
        : options.domain ?? String(req.headers?.host ?? "http-api");
    const action =
      typeof options.resolveAction === "function"
        ? options.resolveAction(req)
        : options.action ?? `http:${String(req.method ?? "GET").toLowerCase()}:${String(req.url ?? "/").split("?")[0]}`;

    const auth = await client.authorizeExternalAction({
      fayId,
      domain,
      action,
      minGrade: options.minGrade ?? Grade.G1_STRICT,
      riskLevel: options.riskLevel ?? "normal",
      reversibility: options.reversibility ?? "reversible",
    });

    if (!auth.allowed) {
      const payload = auth.error.toJSON();
      if (res && typeof res.writeHead === "function") {
        res.writeHead(403, { "content-type": "application/json; charset=utf-8" });
        res.end(JSON.stringify(payload));
      }
      return payload;
    }

    req.faying = auth.mandate;
    req.fayingDisclosure = auth.disclosure;
    if (typeof next === "function") {
      next();
    }
    return { ok: true, mandate: auth.mandate };
  }

  middleware.protectFetch = function protectFetch(fetchHandler) {
    return async function guardedFetch(request) {
      const fayId =
        request.headers.get("x-faying-subject") ??
        request.headers.get("x-fayid-presenter") ??
        options.fayId ??
        "";
      const reqUrl = new URL(request.url);
      const domain = options.domain ?? reqUrl.host;
      const action =
        options.action ?? `http:${request.method.toLowerCase()}:${reqUrl.pathname}`;

      const guarded = withFayingGuard(
        (reqObj, ctx) => fetchHandler(reqObj, ctx),
        client,
        {
          fayId,
          domain,
          action,
          minGrade: options.minGrade ?? Grade.G1_STRICT,
        },
      );

      try {
        return await guarded(request, { fayId, domain, action });
      } catch (e) {
        if (e instanceof RogueFayError || e?.code === ROGUE_FAY_ACTION_FORBIDDEN) {
          const body = typeof e.toJSON === "function" ? e.toJSON() : { ok: false, error: ROGUE_FAY_ACTION_FORBIDDEN };
          return new Response(JSON.stringify(body), {
            status: 403,
            headers: { "content-type": "application/json; charset=utf-8" },
          });
        }
        throw e;
      }
    };
  };

  return middleware;
}

/**
 * Wraps a dictionary of MCP (`Model Context Protocol`) server tool handlers so every
 * `tools/call` invocation checks active `Faying State`, records `Human View` telemetry,
 * and aborts in `<5ms` with `ROGUE_FAY_ACTION_FORBIDDEN` upon `G0` or heartbeat expiry.
 */
export function wrapMcpToolHandlers(toolsMap, guardianClient, options = {}) {
  const client = normalizeClient(guardianClient);
  const serverDomain = options.domain ?? "mcp-server";
  const wrapped = {};

  for (const [toolName, entry] of Object.entries(toolsMap)) {
    const rawFn = typeof entry === "function" ? entry : entry.handler;
    const toolAction = (typeof entry === "object" && entry.action) || `mcp:tool:${toolName}`;
    const toolMinGrade = (typeof entry === "object" && entry.minGrade) ?? options.minGrade ?? Grade.G1_STRICT;

    const guardedFn = withFayingGuard(rawFn, client, {
      fayId: options.fayId,
      domain: serverDomain,
      action: toolAction,
      minGrade: toolMinGrade,
      riskLevel: (typeof entry === "object" && entry.riskLevel) || options.riskLevel || "normal",
    });

    if (typeof entry === "function") {
      wrapped[toolName] = guardedFn;
    } else {
      wrapped[toolName] = {
        ...entry,
        handler: guardedFn,
      };
    }
  }

  return wrapped;
}
