PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders (
  client_order_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL UNIQUE,
  fingerprint TEXT NOT NULL,
  proposal_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN ('buy','sell')),
  notional_usd TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  trading_day TEXT NOT NULL,
  broker_json TEXT,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_day ON orders(trading_day, side);
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY,
  at TEXT NOT NULL,
  trading_day TEXT NOT NULL,
  equity_usd TEXT NOT NULL,
  cash_usd TEXT NOT NULL,
  exposure_usd TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  at TEXT NOT NULL,
  kind TEXT NOT NULL,
  detail_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY,
  at TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  evidence_ref TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unverified'
    CHECK(status = 'unverified')
);
