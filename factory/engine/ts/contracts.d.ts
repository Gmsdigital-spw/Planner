// Generated from factory/engine/contracts.py — do not edit by hand.
// Regenerate: python -m factory.engine export-ts
export const SCHEMA_VERSION = 1;

export type TaskStatus = "queued" | "running" | "needs_approval" | "succeeded" | "failed" | "cancelled";
export type AgentRole = "orchestrator" | "research" | "product_factory" | "quality" | "distribution" | "channel_adapter" | "publishing" | "analytics" | "model_cost" | "engineering";
export type Capability = "publish_public" | "spend_money" | "change_credentials" | "destructive_change" | "trade_live";
export type Channel = "etsy" | "pinterest" | "instagram" | "facebook" | "tiktok" | "youtube_shop" | "gmula";
export type ApprovalStatus = "proposed" | "approved" | "declined" | "expired";
export type IntegrationState = "connected" | "mocked" | "missing" | "unverified";

export interface ErrorPolicy {
  max_retries?: number;
  backoff_base_s?: number;
  backoff_cap_s?: number;
  timeout_s?: number;
  stalled_after_s?: number;
  retry_on?: string[];
}

export interface Budget {
  max_calls_per_task?: number | null;
  max_tokens_per_task?: number | null;
  max_usd_per_task?: number | null;
  max_usd_per_day?: number | null;
}

export interface AgentContract {
  id: string;
  name: string;
  role: AgentRole;
  responsibilities: string[];
  inputs: string[];
  outputs: string[];
  tools: string[];
  capabilities?: Capability[];
  error_policy?: ErrorPolicy;
  budget?: Budget;
  skill_path?: string | null;
  version?: number;
}

export interface TaskSpec {
  agent_id: string;
  kind: string;
  input_ref: string;
  tools?: string[];
  capabilities?: Capability[];
  idempotency_key?: string | null;
  depends_on?: string[];
  priority?: number;
  model_hint?: string | null;
  meta?: Record<string, unknown>;
}

export interface Task {
  id: string;
  spec: TaskSpec;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  attempts?: number;
  run_ids?: string[];
  approval_id?: string | null;
  last_error?: string | null;
  checkpoint?: Record<string, unknown>;
  next_eligible_at?: string | null;
  output_ref?: string | null;
}

export interface ModelUsage {
  provider: string;
  model: string;
  tokens_in?: number | null;
  tokens_out?: number | null;
  cost_usd?: number | null;
  cached?: boolean;
  calls?: number;
}

export interface Run {
  id: string;
  task_id: string;
  agent_id: string;
  attempt: number;
  started_at: string;
  finished_at?: string | null;
  status?: TaskStatus | null;
  model?: string | null;
  usage?: ModelUsage | null;
  validation?: Record<string, unknown>;
  output_ref?: string | null;
  error?: string | null;
  error_class?: string | null;
  recovery?: string | null;
  heartbeat_at?: string | null;
  runner?: string | null;
}

export interface Approval {
  id: string;
  task_id: string | null;
  capability: Capability;
  title: string;
  why: string;
  status?: ApprovalStatus;
  requested_at?: string;
  decided_at?: string | null;
  decided_by?: string | null;
  expires_at?: string | null;
  cost?: string | null;
  risk?: string | null;
}

export interface AuditEvent {
  id: string;
  at: string;
  who: string;
  action: string;
  subject: string;
  detail?: string;
}

export interface FileRef {
  path: string;
  sha256: string;
  bytes: number;
  format: string;
}

export interface ProductManifest {
  product_id: string;
  version: number;
  created_at: string;
  files: FileRef[];
  format: string;
  title: string;
  lane: string;
  validation?: Record<string, unknown>;
  known_limitations?: string[];
  listing_status?: string;
  distribution_status?: string;
  supersedes?: number | null;
}

export interface DistributionPlan {
  id: string;
  product_id: string;
  product_version: number;
  target_customer: string;
  evidence: string[];
  channels: Channel[];
  channel_reasons: Record<string, unknown>;
  assets?: Record<string, unknown>;
  destination_url?: string | null;
  cta?: string | null;
  schedule?: Record<string, unknown>[];
  timezone?: string;
  hypothesis?: string;
  success_criteria?: string;
  approval_id?: string | null;
  status?: string;
  tracking?: Record<string, unknown>;
  results?: Record<string, unknown>;
  next_action?: string | null;
}

export interface IntegrationHealth {
  id: string;
  state: IntegrationState;
  last_ok_at?: string | null;
  last_error?: string | null;
  checked_at?: string | null;
  note?: string;
}
