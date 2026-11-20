export const ROGUE_FAY_ACTION_FORBIDDEN = "ROGUE_FAY_ACTION_FORBIDDEN";

export const Grade: Readonly<{
  G0_EMERGENCY: 0;
  G1_STRICT: 1;
  G2_MODERATE: 2;
  G3_LOOSE: 3;
  G4_AUTONOMOUS: 4;
}>;

export interface AtomicScope {
  domains: string[];
  actions: string[];
  terminals?: string[];
  budget?: {
    maxInvocations?: number;
    maxCostUnits?: number;
  };
}

export class RogueFayError extends Error {
  code: "ROGUE_FAY_ACTION_FORBIDDEN";
  protocolErrorCode: number;
  protocolErrorName: string;
  fayId: string | null;
  behaviorState: "ROGUE_FAY" | "FAYING";
  reason: string;
  httpStatus: 403;
  constructor(message: string, details?: Record<string, unknown>);
  toJSON(): Record<string, unknown>;
}

export function createFayingSigner(seedOrPassphrase?: Uint8Array | string): {
  alg: "Ed25519";
  publicKeyRaw: Buffer;
  publicKeyHex: string;
  signDomainJson(domainPrefix: string, obj: unknown): { alg: "Ed25519"; pubkey: string; sig: string };
};

export class FayingGuardianEngine {
  constructor(options?: { nowMs?: () => number; maxHumanViewEvents?: number });
  nowMs(): number;
  subscribe(listener: (event: Record<string, unknown>) => void): () => void;
  onRogueTransition(fayId: string, callback: (err: RogueFayError) => void): () => void;
  getStatus(fayId: string, evalMs?: number): Record<string, unknown>;
  submitFayingRequest(input: {
    initiatorFayId: string;
    targetHumanPrime: string;
    proposedScope: AtomicScope;
    proposedGrade?: number;
    reason?: string;
    reasonCode?: string;
  }): Record<string, unknown>;
  initiateFaying(input: {
    humanPrimeId: string;
    humanSigner: ReturnType<typeof createFayingSigner>;
    fayId: string;
    scope: AtomicScope;
    grade?: number;
    ttlMs?: number;
    maxStalenessMs?: number;
    signalTypes?: string[];
    onLoss?: string;
    endorsement?: Record<string, unknown> | null;
    fayingRequestRef?: string | null;
    nonce?: string;
  }): Record<string, unknown>;
  delegateCoFayStewardship(input: {
    managerFayId: string;
    managerSigner: ReturnType<typeof createFayingSigner>;
    subjectCoFayId: string;
    stewardEntity: string;
    charterId?: string;
    charterScope: AtomicScope;
    scope: AtomicScope;
    grade?: number;
    ttlMs?: number;
    maxStalenessMs?: number;
    hopCount?: number;
  }): Record<string, unknown>;
  transferCoFayStewardship(input: {
    cofayId: string;
    fromSteward: string;
    fromHumanPrime: string;
    fromStewardSigner: ReturnType<typeof createFayingSigner>;
    toSteward: string;
    toHumanPrime: string;
    toStewardSigner: ReturnType<typeof createFayingSigner>;
    nextManagerFayId: string;
    nonce?: string;
  }): Record<string, unknown>;
  recordHeartbeat(input: {
    fayId: string;
    nonce?: string;
    signalType?: string;
    deviceTampered?: boolean;
  }): Record<string, unknown>;
  triggerG0EmergencyBrake(input: {
    targetId: string;
    actorId?: string;
    reason?: string;
  }): Record<string, unknown>;
  authorizeExternalAction(input: {
    fayId: string;
    domain: string;
    action: string;
    minGrade?: number;
    costUnits?: number;
    riskLevel?: "low" | "normal" | "high" | "critical";
    reversibility?: "reversible" | "partially-reversible" | "irreversible";
    affectedResources?: string[];
    uncertaintyFlags?: string[];
    summary?: string;
  }):
    | { allowed: true; mandate: Record<string, unknown>; disclosure: Record<string, unknown> }
    | { allowed: false; error: RogueFayError };
  getHumanViewFeed(options?: { fayId?: string | null; limit?: number }): Array<Record<string, unknown>>;
  shutdown(): void;
}

export interface GuardianClient {
  mode: "in-process" | "remote-http-sse";
  authorizeExternalAction(input: Record<string, unknown>): Promise<
    | { allowed: true; mandate: Record<string, unknown>; disclosure: Record<string, unknown> }
    | { allowed: false; error: RogueFayError }
  >;
  onRogueTransition(fayId: string, callback: (err: RogueFayError) => void): () => void;
  close(): Promise<void>;
}

export function createGuardianDaemonServer(options?: {
  engine?: FayingGuardianEngine;
  host?: string;
  port?: number;
}): {
  engine: FayingGuardianEngine;
  server: import("node:http").Server;
  listen(): Promise<{ host: string; port: number; url: string }>;
  close(): Promise<void>;
};

export function createGuardianClient(
  target: FayingGuardianEngine | string | { url: string } | { engine: FayingGuardianEngine },
): GuardianClient;

export function withFayingGuard<TInput = unknown, TOutput = unknown>(
  handler: (
    input: TInput,
    context: {
      fayId: string;
      signal: AbortSignal;
      mandate: Record<string, unknown>;
      disclosure: Record<string, unknown>;
    },
  ) => TOutput | Promise<TOutput>,
  guardianClient: GuardianClient | FayingGuardianEngine | string,
  options?: {
    fayId?: string;
    domain?: string;
    action?: string;
    minGrade?: number;
    costUnits?: number;
    riskLevel?: "low" | "normal" | "high" | "critical";
    reversibility?: "reversible" | "partially-reversible" | "irreversible";
    affectedResources?: string[];
    uncertaintyFlags?: string[];
    summary?: string;
    describeAction?: (input: TInput) => string;
  },
): (input: TInput, runtimeContext?: Record<string, unknown>) => Promise<TOutput>;

export function createFayingHttpMiddleware(
  guardianClient: GuardianClient | FayingGuardianEngine | string,
  options?: Record<string, unknown>,
): {
  (req: unknown, res: unknown, next?: () => void): Promise<Record<string, unknown>>;
  protectFetch(
    handler: (req: Request, ctx: Record<string, unknown>) => Response | Promise<Response>,
  ): (req: Request) => Promise<Response>;
};

export function wrapMcpToolHandlers<T extends Record<string, unknown>>(
  toolsMap: T,
  guardianClient: GuardianClient | FayingGuardianEngine | string,
  options?: Record<string, unknown>,
): T;
