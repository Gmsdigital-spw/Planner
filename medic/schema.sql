-- The Medic's history log (SQLite). Created on first run; committed by the Medic Action.
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lane TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL CHECK (status IN ('ok','failed','missing','fixed')),
  item_ref TEXT,
  verified_url TEXT,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lane TEXT NOT NULL,
  key TEXT NOT NULL DEFAULT '',
  error_kind TEXT NOT NULL,
  item_ref TEXT,
  opened_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen TEXT,
  closed_at TEXT,
  outcome TEXT CHECK (outcome IN ('fixed','needs_human','open','recovered')) DEFAULT 'open',
  steps_tried TEXT,
  fix_step TEXT,
  fixed_at TEXT,
  verified INTEGER NOT NULL DEFAULT 0,
  ticket TEXT
);
CREATE INDEX IF NOT EXISTS incidents_open ON incidents(lane, key, closed_at);
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lane TEXT NOT NULL,
  lesson TEXT NOT NULL,
  is_rule INTEGER NOT NULL DEFAULT 0,
  hits INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lane TEXT NOT NULL,
  item_ref TEXT NOT NULL,
  score INTEGER NOT NULL,
  passed INTEGER NOT NULL,
  notes TEXT,
  scored_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- fix-once: one attempt per step per thing per day (shared rules, "Fix-once")
CREATE TABLE IF NOT EXISTS fix_attempts (
  lane TEXT NOT NULL,
  step TEXT NOT NULL,
  key TEXT NOT NULL,
  day TEXT NOT NULL,
  n INTEGER NOT NULL DEFAULT 1,
  at TEXT,
  PRIMARY KEY (lane, step, key, day)
);
-- one row per lane per day: what got done against the goal (the morning report reads yesterday's)
CREATE TABLE IF NOT EXISTS lane_days (
  day TEXT NOT NULL,
  lane TEXT NOT NULL,
  done INTEGER,
  goal INTEGER,
  status TEXT,
  detail TEXT,
  updated_at TEXT,
  PRIMARY KEY (day, lane)
);
-- Today's scoreboard for the home screen
CREATE VIEW IF NOT EXISTS today_board AS
SELECT lane,
       SUM(status IN ('ok','fixed')) AS done,
       SUM(status IN ('failed','missing')) AS broken
FROM runs WHERE date(started_at) = date('now')
GROUP BY lane;
