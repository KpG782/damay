// =============================================================================
// Single source of truth for cross-cutting types. Consumed by apps/web
// (Next.js) and apps/api (FastAPI via pydantic codegen post-hackathon).
//
// Conventions:
//   - Postgres snake_case columns become camelCase fields here.
//   - All ISO timestamps are typed as `IsoDateTime` (string alias). Frontend
//     parses with `new Date(...)`. FastAPI emits RFC 3339.
//   - Money: `amountPhp` is whole Philippine pesos (integer). v1.0 uses
//     whole pesos to match the schema's INTEGER column. If sub-peso precision
//     is ever required, migrate to centavos in a new field and deprecate this.
//   - No `any`. Use `unknown` where the shape is genuinely opaque.
//   - String unions over enums: portable across Next.js RSC and Pydantic.
// =============================================================================

// -----------------------------------------------------------------------------
// Branded primitive aliases (documentation, not runtime guards)
// -----------------------------------------------------------------------------
export type Uuid = string;
export type IsoDateTime = string; // RFC 3339, e.g. "2026-05-23T12:34:56Z"
export type IsoDate = string;     // "YYYY-MM-DD"
export type E164 = string;        // "+639171234567"
export type StellarAccountId = string;  // G... 56 chars
export type StellarContractId = string; // C... 56 chars
export type StellarTxHash = string;     // 64 lowercase hex
export type TwilioSid = string;         // "SM..." / "MM..." / synthetic for dev

// -----------------------------------------------------------------------------
// Status enums — mirror schema.sql CHECK / enum constraints exactly.
// -----------------------------------------------------------------------------
export type RoundFrequency = "weekly" | "biweekly" | "monthly";
export type RoundStatus = "draft" | "active" | "completed" | "cancelled";
export type ContributionStatus = "pending" | "confirmed" | "failed";
export type PayoutStatus = "pending" | "confirmed" | "failed";
export type MessageDirection = "in" | "out";
export type ReputationEventType = "contribution" | "default" | "payout";

export type StellarJobType =
  | "deploy_paluwagan"
  | "add_member"
  | "contribute"
  | "distribute_payout"
  | "close_round"
  | "reputation_credit"
  | "reputation_default"
  | "reputation_payout_received";

export type StellarJobStatus =
  | "queued"
  | "in_flight"
  | "done"
  | "failed"
  | "dead_letter";

// -----------------------------------------------------------------------------
// Row types — one per table from schema.sql.
// All amounts in whole PHP (integer). Stellar tx hashes nullable until confirmed.
// -----------------------------------------------------------------------------
export interface Organizer {
  id: Uuid;
  email: string;
  phone: string | null;
  displayName: string;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface Member {
  id: Uuid;
  whatsappE164: E164;
  displayName: string;
  stellarAccount: StellarAccountId | null;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface Round {
  id: Uuid;
  organizerId: Uuid;
  name: string;
  code: string;
  /** Whole pesos. Schema column is INTEGER. */
  contributionAmountPhp: number;
  memberCount: number;
  frequency: RoundFrequency;
  startDate: IsoDate;
  status: RoundStatus;
  paluwaganContractId: StellarContractId | null;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface RoundMember {
  roundId: Uuid;
  memberId: Uuid;
  payoutPosition: number;
  joinedAt: IsoDateTime;
}

export interface Contribution {
  id: Uuid;
  roundId: Uuid;
  memberId: Uuid;
  cycleNumber: number;
  /** Whole pesos. */
  amountPhp: number;
  stellarTxHash: StellarTxHash | null;
  status: ContributionStatus;
  sourceMessageSid: TwilioSid | null;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface Payout {
  id: Uuid;
  roundId: Uuid;
  memberId: Uuid;
  cycleNumber: number;
  /** Whole pesos. */
  amountPhp: number;
  stellarTxHash: StellarTxHash | null;
  status: PayoutStatus;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

export interface Message {
  id: Uuid;
  memberId: Uuid | null;
  direction: MessageDirection;
  twilioSid: TwilioSid;
  body: string;
  createdAt: IsoDateTime;
}

export interface ReputationEvent {
  id: Uuid;
  memberId: Uuid;
  eventType: ReputationEventType;
  weight: number;
  stellarTxHash: StellarTxHash;
  /** JSONB payload mirrored from the on-chain event. Shape varies per event_type. */
  context: Record<string, unknown>;
  createdAt: IsoDateTime;
}

export interface IdempotencyKey {
  key: string;
  route: string;
  requestHash: string;
  responseStatus: number;
  responseBody: Record<string, unknown>;
  createdAt: IsoDateTime;
  expiresAt: IsoDateTime;
}

export interface StellarJob {
  id: Uuid;
  jobType: StellarJobType;
  payload: Record<string, unknown>;
  targetTable: string | null;
  targetId: Uuid | null;
  idempotencyKey: string | null;
  status: StellarJobStatus;
  attempts: number;
  lastError: string | null;
  stellarTxHash: StellarTxHash | null;
  scheduledFor: IsoDateTime;
  lockedUntil: IsoDateTime | null;
  createdAt: IsoDateTime;
  updatedAt: IsoDateTime;
}

// -----------------------------------------------------------------------------
// Error envelope. Flat shape: `{ code, message, requestId? }`.
// FastAPI wraps it under an `error` key in the JSON response body (see
// `ApiErrorResponse` below) but the canonical envelope clients consume is
// this flat object.
// -----------------------------------------------------------------------------
export interface ApiError {
  code: string;
  message: string;
  requestId?: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiError;
}

export type ApiErrorCode =
  | "VALIDATION_ERROR"
  | "UNAUTHENTICATED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "ROUND_NOT_FOUND"
  | "MEMBER_NOT_FOUND"
  | "MEMBER_EXISTS"
  | "POSITION_TAKEN"
  | "ROUND_FULL"
  | "ROUND_NOT_READY"
  | "ALREADY_ACTIVE"
  | "NOT_ACTIVE"
  | "CYCLES_REMAINING"
  | "CYCLE_NOT_DUE"
  | "CYCLE_ALREADY_PAID"
  | "CONTRIBUTIONS_INCOMPLETE"
  | "IDEMPOTENCY_CONFLICT"
  | "INVALID_SIGNATURE"
  | "RATE_LIMITED"
  | "UPSTREAM_UNAVAILABLE"
  | "INTERNAL_ERROR";

// -----------------------------------------------------------------------------
// Pagination
// -----------------------------------------------------------------------------
export interface CursorPage<T> {
  data: T[];
  nextCursor: string | null;
}

// =============================================================================
// API contracts — one <Verb><Resource>Request + <Verb><Resource>Response pair
// per endpoint in ARCHITECTURE.md §2.
// =============================================================================

// -----------------------------------------------------------------------------
// GET /v1/healthz                                                       PUBLIC
// -----------------------------------------------------------------------------
export type GetHealthzRequest = Record<string, never>;

export interface GetHealthzResponse {
  status: "ok" | "degraded" | "down";
  checks: {
    db: "ok" | "fail";
    horizon: "ok" | "fail";
    twilio: "ok" | "fail";
    soroban_rpc: "ok" | "fail";
  };
  version: string;
}

// Back-compat alias for earlier import sites.
export type HealthzResponse = GetHealthzResponse;

// -----------------------------------------------------------------------------
// POST /v1/rounds                                                JWT (organizer)
// -----------------------------------------------------------------------------
export interface PostRoundsRequest {
  name: string;
  contributionAmountPhp: number;
  memberCount: number;
  frequency: RoundFrequency;
  startDate: IsoDate;
}

export type PostRoundsResponse = Round;

// Back-compat aliases.
export type CreateRoundRequest = PostRoundsRequest;
export type CreateRoundResponse = PostRoundsResponse;

// -----------------------------------------------------------------------------
// GET /v1/rounds                                                JWT (organizer)
// -----------------------------------------------------------------------------
export interface GetRoundsRequest {
  status?: RoundStatus;
  limit?: number;
  cursor?: string;
}

export type GetRoundsResponse = CursorPage<Round>;

// Back-compat aliases.
export type ListRoundsQuery = GetRoundsRequest;
export type ListRoundsResponse = GetRoundsResponse;

// -----------------------------------------------------------------------------
// GET /v1/rounds/:id                                            JWT (organizer)
// -----------------------------------------------------------------------------
export interface GetRoundRequest {
  roundId: Uuid;
}

export interface RoundDetail extends Round {
  members: Array<RoundMember & { member: Member }>;
  contributions: Contribution[];
  payouts: Payout[];
}

export type GetRoundResponse = RoundDetail;

// -----------------------------------------------------------------------------
// POST /v1/rounds/:id/activate                                  JWT (organizer)
// -----------------------------------------------------------------------------
export interface PostRoundActivateRequest {
  roundId: Uuid;
}

export interface PostRoundActivateResponse {
  roundId: Uuid;
  jobId: Uuid;
  status: "activation_pending";
}

export type ActivateRoundResponse = PostRoundActivateResponse;

// -----------------------------------------------------------------------------
// POST /v1/rounds/:id/close                                     JWT (organizer)
// -----------------------------------------------------------------------------
export interface PostRoundCloseRequest {
  roundId: Uuid;
}

export interface PostRoundCloseResponse {
  jobId: Uuid;
  status: "close_pending";
}

export type CloseRoundResponse = PostRoundCloseResponse;

// -----------------------------------------------------------------------------
// POST /v1/members                                              JWT (organizer)
// -----------------------------------------------------------------------------
export interface PostMembersRequest {
  whatsappE164: E164;
  displayName: string;
}

export type PostMembersResponse = Member;

// Back-compat aliases.
export type CreateMemberRequest = PostMembersRequest;
export type CreateMemberResponse = PostMembersResponse;

// -----------------------------------------------------------------------------
// GET /v1/members/:id                                           JWT (organizer)
// -----------------------------------------------------------------------------
export interface GetMemberRequest {
  memberId: Uuid;
}

export type GetMemberResponse = Member;

// -----------------------------------------------------------------------------
// POST /v1/rounds/:id/members                                   JWT (organizer)
// -----------------------------------------------------------------------------
export interface PostRoundMembersRequest {
  roundId: Uuid;
  memberId: Uuid;
  payoutPosition: number;
}

export type PostRoundMembersResponse = RoundMember;

// Back-compat aliases.
export type AddMemberToRoundRequest = PostRoundMembersRequest;
export type AddMemberToRoundResponse = PostRoundMembersResponse;

// -----------------------------------------------------------------------------
// POST /v1/contributions                                                SERVICE
// -----------------------------------------------------------------------------
export interface PostContributionsRequest {
  roundId: Uuid;
  memberId: Uuid;
  cycleNumber: number;
  amountPhp: number;
  sourceMessageSid?: TwilioSid;
}

export interface PostContributionsResponse {
  contributionId: Uuid;
  status: "pending";
  jobId: Uuid;
}

// Back-compat aliases.
export type CreateContributionRequest = PostContributionsRequest;
export type CreateContributionResponse = PostContributionsResponse;

// -----------------------------------------------------------------------------
// GET /v1/contributions?round_id=&cycle=                        JWT (organizer)
// -----------------------------------------------------------------------------
export interface GetContributionsRequest {
  roundId: Uuid;
  cycle?: number;
}

export interface GetContributionsResponse {
  data: Contribution[];
}

// Back-compat aliases.
export type ListContributionsQuery = GetContributionsRequest;
export type ListContributionsResponse = GetContributionsResponse;

// -----------------------------------------------------------------------------
// POST /v1/payouts/:roundId/distribute                          JWT or SERVICE
// -----------------------------------------------------------------------------
export interface PostPayoutsDistributeRequest {
  roundId: Uuid;
  cycleNumber: number;
}

export interface PostPayoutsDistributeResponse {
  jobId: Uuid;
  status: "payout_pending";
}

// Back-compat aliases.
export type DistributePayoutRequest = PostPayoutsDistributeRequest;
export type DistributePayoutResponse = PostPayoutsDistributeResponse;

// -----------------------------------------------------------------------------
// GET /v1/reputation/:memberId                                  JWT (organizer)
// -----------------------------------------------------------------------------
export interface GetReputationRequest {
  memberId: Uuid;
}

export interface GetReputationResponse {
  memberId: Uuid;
  score: number;
  events: ReputationEvent[];
}

// -----------------------------------------------------------------------------
// POST /v1/webhooks/twilio                                          TWILIO_SIG
//   Twilio sends application/x-www-form-urlencoded. We type only the fields
//   we read. Response is TwiML (XML string) — represented as a string.
// -----------------------------------------------------------------------------
export interface PostWebhooksTwilioRequest {
  MessageSid: TwilioSid;
  From: string; // "whatsapp:+639..."
  To: string;   // "whatsapp:+1415..."
  Body: string;
  NumMedia?: string;
  ProfileName?: string;
  AccountSid?: string;
}

/** TwiML XML body. Empty string means "no synchronous reply". */
export type PostWebhooksTwilioResponse = string;

// Back-compat alias.
export type TwilioInboundWebhook = PostWebhooksTwilioRequest;

// -----------------------------------------------------------------------------
// POST /v1/dev/simulate-message                              JWT (dev env only)
// -----------------------------------------------------------------------------
export interface PostDevSimulateMessageRequest {
  from: E164;
  body: string;
  syntheticSid?: TwilioSid;
}

export interface PostDevSimulateMessageResponse {
  accepted: true;
  twilioSid: TwilioSid;
}

// Back-compat alias.
export type SimulateMessageRequest = PostDevSimulateMessageRequest;

// =============================================================================
// Supabase Realtime payloads
//   Channels: `public:contributions`, `public:payouts`, `public:reputation_events`.
// =============================================================================
export interface RealtimeChange<T> {
  schema: "public";
  table: string;
  eventType: "INSERT" | "UPDATE" | "DELETE";
  new: T | null;
  old: T | null;
  commitTimestamp: IsoDateTime;
}

export type ContributionRealtimeEvent = RealtimeChange<Contribution>;
export type PayoutRealtimeEvent = RealtimeChange<Payout>;
export type ReputationRealtimeEvent = RealtimeChange<ReputationEvent>;

// Back-compat aliases (previous naming).
export type ContributionChange = ContributionRealtimeEvent;
export type PayoutChange = PayoutRealtimeEvent;
export type ReputationEventChange = ReputationRealtimeEvent;

// =============================================================================
// End of file. No default export.
// =============================================================================
