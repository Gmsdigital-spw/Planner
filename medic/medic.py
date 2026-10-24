#!/usr/bin/env python3
"""The Medic (V8 "The Turning Point", Oct 24, 2026).

Finds what broke, fixes what it can for free, checks that the fix is really live, learns from it,
and only then asks for a human. Plain Python on GitHub's free minutes: no Claude usage, no money.

  python3 medic.py              one pass (what the Action runs every 30 minutes)
  python3 medic.py --dry-run    look and report, change nothing, dispatch nothing
  python3 medic.py --selftest   unit checks on synthetic fixtures (no network)
  python3 medic.py --board      print the current board from the last report

Everything it knows comes from lanes.json next to this file. The same file runs both businesses
(copied, never linked): the Agency repo and the Ridgeline repo each carry their own copy and their
own lanes.json. A copy must never read the other business's files.

What it can do on its own (free, inside GitHub Actions): start a workflow again (gateway job that
never ran, a Short that never built, a bot that stopped checking in, the engine), re-run a failed
Actions job once, ask GitHub Pages to rebuild the website. What it cannot do (rebuild a cover,
re-send a pin, change a listing, fire a Claude scheduled task) becomes a ticket in queue/ for the
Claude crew that owns that business. Grayson is asked only when neither can fix it.

Rules it keeps: fix each thing at most once per day (shared rules, "Fix-once"); never spend money;
never touch a parked lane; never invent a number (unknown stays unknown); the repo is public, so
nothing private goes in the report, the lessons or a ticket (ids only, never emails or phones).
"""
import argparse, json, os, re, sqlite3, subprocess, sys, time, datetime as dt, urllib.request, urllib.error
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

HERE = Path(__file__).resolve().parent
VERSION = "8.0"
UTC = dt.timezone.utc
HUMAN_ERRORS = {"auth_expired", "platform_block", "billing"}
LOCAL_STEPS = {"retry", "restart_bot", "redeploy", "rerun_failed"}        # the Medic does these itself
CREW_STEPS = {"rescore_rebuild", "rehost_images", "shrink_images", "shrink_video", "regenerate_asset",
              "backup_poster", "fallback_model", "next_slot", "fire_task", "resend"}   # a Claude crew does these

NOW_OVERRIDE = None
DRY = False
OFFLINE = False
LOG = []


def log(msg):
    line = f"[medic] {msg}"
    LOG.append(line)
    print(line, flush=True)


# ----------------------------------------------------------------------------- time

def now_utc():
    return NOW_OVERRIDE or dt.datetime.now(UTC)


def parse_iso(s):
    """ISO string -> aware UTC datetime, or None. Accepts Z, offsets and naive (treated as UTC)."""
    if not s or not isinstance(s, str):
        return None
    try:
        t = dt.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    return t.astimezone(UTC)


def iso(t=None):
    return (t or now_utc()).strftime("%Y-%m-%dT%H:%M:%SZ")


def age_min(s, ref=None):
    t = parse_iso(s) if isinstance(s, str) else s
    if not t:
        return None
    return ((ref or now_utc()) - t).total_seconds() / 60.0


class Clock:
    def __init__(self, tz):
        self.tz = ZoneInfo(tz) if ZoneInfo else UTC

    def local(self, t=None):
        return (t or now_utc()).astimezone(self.tz)

    def day_key(self, t=None):
        return self.local(t).strftime("%Y-%m-%d")

    def hhmm(self, t=None):
        return self.local(t).strftime("%H:%M")

    def in_window(self, win, t=None):
        """win = {"start":"08:40","end":"15:00","days":"weekdays"|"all"} in local time."""
        if not win:
            return True
        loc = self.local(t)
        if win.get("days") == "weekdays" and loc.weekday() >= 5:
            return False
        if win.get("days") == "mon-sat" and loc.weekday() == 6:
            return False
        hm = loc.strftime("%H:%M")
        return win.get("start", "00:00") <= hm <= win.get("end", "23:59")


# ----------------------------------------------------------------------------- files

def read_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def read_jsonl(p):
    out = []
    try:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return out


def git(root, *args, check=False):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120)
        if check and r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def commit_time(root, relpath):
    """When a file was last committed (UTC). Checkouts do not keep mtimes, so git is the truth."""
    out = git(root, "log", "-1", "--format=%ct", "--", relpath)
    if out and out.isdigit():
        return dt.datetime.fromtimestamp(int(out), UTC)
    try:
        return dt.datetime.fromtimestamp(Path(root, relpath).stat().st_mtime, UTC)
    except OSError:
        return None


def classify(detail):
    d = (detail or "").lower()
    if "insufficient_quota" in d or "payment" in d or "billing" in d or "exceeded your current quota" in d:
        return "billing"
    if "401" in d or "unauthorized" in d or "token" in d or "expired" in d or "invalid api key" in d or "invalid_api_key" in d:
        return "auth_expired"
    if "403" in d or "blocked" in d or "suspend" in d or "forbidden" in d or "doesn't allow you to save" in d:
        return "platform_block"
    if "413" in d or "too large" in d:
        return "too_large"
    if "score" in d:
        return "low_score"
    if "timeout" in d or "timed out" in d or "429" in d or "rate limit" in d or "503" in d or "502" in d:
        return "transient"
    return "unknown"


# ----------------------------------------------------------------------------- GitHub API (free, token from the Action)

class GitHub:
    def __init__(self, repo, ref):
        self.token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.repo = repo
        self.ref = ref
        self.calls = 0

    @property
    def ok(self):
        return bool(self.token and self.repo) and not OFFLINE

    def call(self, method, path, body=None):
        if not self.ok:
            return 0, {"error": "no GitHub token in this run"}
        self.calls += 1
        req = urllib.request.Request("https://api.github.com" + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "medic/" + VERSION)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode("utf-8", "replace"))
            except Exception:
                return e.code, {"error": f"HTTP {e.code}"}
        except Exception as e:
            return 0, {"error": f"{e.__class__.__name__}: {e}"}

    def dispatch(self, workflow_file, inputs=None):
        if DRY:
            log(f"DRY: would dispatch {workflow_file} inputs={inputs or {}} on {self.ref}")
            return False
        code, data = self.call("POST", f"/repos/{self.repo}/actions/workflows/{workflow_file}/dispatches",
                               {"ref": self.ref, "inputs": inputs or {}})
        log(f"dispatch {workflow_file} {inputs or ''} -> HTTP {code} {data.get('message', '') if isinstance(data, dict) else ''}")
        return code == 204

    def rerun_failed(self, run_id):
        if DRY:
            log(f"DRY: would re-run failed jobs of run {run_id}")
            return False
        code, data = self.call("POST", f"/repos/{self.repo}/actions/runs/{run_id}/rerun-failed-jobs")
        log(f"rerun-failed-jobs {run_id} -> HTTP {code}")
        return code == 201

    def runs(self, since, workflows=None):
        """Recent runs, one call per watched workflow (a busy repo has hundreds of runs a day; one page is not enough)."""
        if not self.ok:
            return None
        ts = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        out = []
        for wf in (workflows or [None]):
            path = (f"/repos/{self.repo}/actions/workflows/{wf}/runs?per_page=30&created=%3E%3D{ts}" if wf
                    else f"/repos/{self.repo}/actions/runs?per_page=100&created=%3E%3D{ts}")
            code, data = self.call("GET", path)
            if code == 404 and wf:
                continue                                   # that workflow file does not exist on this repo
            if code != 200 or not isinstance(data, dict):
                return out or None
            out += data.get("workflow_runs", [])
        return out

    def pages_build(self):
        if DRY:
            log("DRY: would request a GitHub Pages build")
            return False
        code, data = self.call("POST", f"/repos/{self.repo}/pages/builds")
        log(f"pages build -> HTTP {code}")
        return code in (201, 202)


def http_get(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "medic/" + VERSION, "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


# ----------------------------------------------------------------------------- the Medic

class Medic:
    def __init__(self, cfg_path, dry=False, offline=False):
        global DRY, OFFLINE
        DRY, OFFLINE = dry, offline
        self.cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
        self.home = Path(cfg_path).resolve().parent
        self.root = self._find_root()
        self.clock = Clock(self.cfg.get("tz", "America/Chicago"))
        self.gh = GitHub(os.environ.get("GITHUB_REPOSITORY") or self.cfg.get("repo", ""),
                         os.environ.get("GITHUB_REF_NAME") or self.cfg.get("branch", "main"))
        (self.home / "db").mkdir(exist_ok=True)
        # a dry run must leave no trace: history stays in memory, no tickets, no lessons, no report
        self.db = sqlite3.connect(":memory:") if DRY else sqlite3.connect(self.home / "db" / "history.sqlite")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((self.home / "schema.sql").read_text(encoding="utf-8"))
        self.board, self.crews, self.problems, self.fixed, self.needs, self.notes = [], [], [], [], [], []
        self.dispatches = 0
        self._fetched = False
        self._runlog = None
        self._runs_cache = None

    def _find_root(self):
        p = self.home
        for _ in range(5):
            if (p / ".git").exists():
                return p
            p = p.parent
        return self.home.parents[int(self.cfg.get("root_depth", 1)) - 1]

    # ---- helpers ---------------------------------------------------------------
    def day(self):
        return self.clock.day_key()

    def runlog(self):
        if self._runlog is None:
            self._runlog = read_jsonl(self.root / self.cfg.get("runlog", "factory/runlog.jsonl"))
        return self._runlog

    def runlog_task(self, task):
        return [r for r in self.runlog() if r.get("task") == task]

    def remote_fetch(self):
        if self._fetched or OFFLINE:
            return
        git(self.root, "fetch", "-q", "origin", self.gh.ref)
        self._fetched = True

    def remote_exists(self, relpath):
        self.remote_fetch()
        r = subprocess.run(["git", "-C", str(self.root), "cat-file", "-e", f"origin/{self.gh.ref}:{relpath}"],
                           capture_output=True)
        return r.returncode == 0

    def remote_json(self, relpath):
        self.remote_fetch()
        out = git(self.root, "show", f"origin/{self.gh.ref}:{relpath}")
        try:
            return json.loads(out) if out else None
        except Exception:
            return None

    def wait_for(self, check, seconds, every=20):
        """Poll check() until true or the budget is spent. Never waits in a dry run."""
        if DRY or OFFLINE:
            return False
        deadline = time.time() + seconds
        while time.time() < deadline:
            time.sleep(every)
            self._fetched = False
            try:
                if check():
                    return True
            except Exception:
                pass
        return False

    def tried_today(self, lane, step, key):
        row = self.db.execute("SELECT n FROM fix_attempts WHERE lane=? AND step=? AND key=? AND day=?",
                              (lane, step, key, self.day())).fetchone()
        return row["n"] if row else 0

    def note_try(self, lane, step, key):
        self.db.execute("INSERT INTO fix_attempts(lane, step, key, day, n, at) VALUES(?,?,?,?,1,?) "
                        "ON CONFLICT(lane, step, key, day) DO UPDATE SET n=n+1, at=excluded.at",
                        (lane, step, key, self.day(), iso()))

    # ---- signals -----------------------------------------------------------------
    def signal(self, lane, spec):
        kind = spec.get("signal", "manual")
        fn = getattr(self, "sig_" + kind, None)
        if not fn:
            return self.row(lane, spec, "unknown", detail=f"no reader for signal '{kind}'")
        try:
            return fn(lane, spec)
        except Exception as e:  # a broken reader is reported, never hidden
            return self.row(lane, spec, "unknown", detail=f"reader crashed: {e.__class__.__name__}: {e}")

    def row(self, lane, spec, status, done=None, goal=None, detail="", problems=None, **extra):
        r = {"lane": lane, "label": spec.get("label", lane), "biz": spec.get("biz", self.cfg.get("biz")),
             "status": status, "done": done, "goal": goal, "cap": spec.get("daily_max"), "detail": detail}
        r.update(extra)
        for p in problems or []:
            p.setdefault("lane", lane)
            p.setdefault("key", p["error"])
            self.problems.append(p)
        return r

    def goal_status(self, lane, spec, done, detail, problems=None, verified=True):
        """Daily-goal lanes: ok once the goal is met, 'late' until the goal hour, 'under_goal' after it."""
        problems = problems or []
        goal = spec.get("daily_min")
        win = spec.get("window")
        if win and not self.clock.in_window({"days": win.get("days", "all")}):
            return self.row(lane, spec, "off_day", done, goal, detail + " (no goal today)", problems, verified=verified)
        if goal is None:
            return self.row(lane, spec, "ok" if not problems else "failed", done, goal, detail, problems, verified=verified)
        if done is not None and done >= goal:
            return self.row(lane, spec, "ok" if not problems else "failed", done, goal, detail, problems, verified=verified)
        hour = self.clock.local().hour
        if hour >= spec.get("goal_hour", 20):
            problems.append({"error": "under_goal", "key": "under_goal-" + self.day(), "item": {},
                             "detail": f"{done if done is not None else 'unknown'} of {goal} by {spec.get('goal_hour', 20)}:00"})
            return self.row(lane, spec, "under_goal", done, goal, detail, problems, verified=verified)
        return self.row(lane, spec, "late" if problems else "pending", done, goal, detail, problems, verified=verified)

    def sig_manual(self, lane, spec):
        return self.row(lane, spec, "manual", detail=spec.get("note", "Grayson does this by hand; the Medic only reports."))

    def sig_paused(self, lane, spec):
        return self.row(lane, spec, "paused", detail=spec.get("note", "switched off on purpose"))

    def _gw_pairs(self, spec, day_only=True):
        """Yield (job, op, result) for every op of every gateway job that has an answer (today only by default)."""
        jobs_dir, out_dir = self.root / spec["jobs"], self.root / spec["out"]
        for outp in sorted(out_dir.glob("*.json")) if out_dir.exists() else []:
            out = read_json(outp)
            if not isinstance(out, dict):
                continue
            if day_only and self.clock.day_key(parse_iso(out.get("at")) or dt.datetime.fromtimestamp(0, UTC)) != self.day():
                continue
            job = read_json(jobs_dir / outp.name) or {}
            ops = job.get("ops") or []
            for idx, r in enumerate(out.get("results") or []):
                i = r.get("i", idx)
                op = ops[i] if isinstance(i, int) and i < len(ops) else {}
                yield job, op, r, out

    def sig_gw_count(self, lane, spec):
        """Count today's successful gateway ops matching the lane's filter (op, method, path, platform)."""
        gwspec = self.cfg["sources"]["gateway"]
        n, errs = 0, []
        want_op, want_method = spec.get("op"), spec.get("method")
        path_re = re.compile(spec["path_regex"]) if spec.get("path_regex") else None
        platform = spec.get("platform")
        for job, op, r, out in self._gw_pairs(gwspec):
            if want_op and r.get("op") != want_op:
                continue
            if want_method and (op.get("method") or "GET").upper() != want_method:
                continue
            if path_re and not path_re.search(op.get("path") or ""):
                continue
            if platform:
                plats = [p.get("platform") for p in ((op.get("body") or {}).get("platforms") or []) if isinstance(p, dict)]
                if platform not in plats:
                    continue
            if r.get("ok"):
                n += 1
            else:
                err = r.get("error") or json.dumps(r.get("data"))[:300]
                errs.append({"error": classify(err), "key": f"gw-{out.get('id')}-{r.get('i')}",
                             "item": {"ref": out.get("id"), "op": r.get("i")}, "detail": err[:300]})
        what = spec.get("unit", "ops")
        detail = f"{n} {what} today via the gateway" + (f", {len(errs)} failed" if errs else "")
        return self.goal_status(lane, spec, n, detail, errs, verified=spec.get("verified", False))

    def sig_videopins(self, lane, spec):
        st = read_json(self.root / spec["file"]) or {}
        today = [p for p in st.get("posted", []) if p.get("day") == self.day()]
        probs = []
        for p in today:
            if p.get("status") == "failed":
                probs.append({"error": classify(p.get("error")), "key": f"vpin-{p.get('day')}-{p.get('listingId')}",
                              "item": {"ref": p.get("listingId")}, "detail": (p.get("error") or "")[:300]})
        posted = sum(1 for p in today if p.get("status") in ("posted", "scheduled"))
        detail = f"{posted} video pin today ({', '.join(p.get('status', '?') for p in today) or 'none yet'})"
        return self.goal_status(lane, spec, posted, detail, probs, verified=any(p.get("status") == "posted" for p in today))

    def sig_gw_jobs(self, lane, spec):
        """The gateway itself: a job without an answer after stale_minutes never ran (the Action missed the push)."""
        jobs_dir, out_dir = self.root / spec["jobs"], self.root / spec["out"]
        stale, failed_today = [], 0
        for jp in sorted(jobs_dir.glob("*.json")) if jobs_dir.exists() else []:
            if (out_dir / jp.name).exists():
                continue
            ct = commit_time(self.root, str(jp.relative_to(self.root)))
            a = age_min(ct) if ct else None
            if a is not None and a > spec.get("stale_minutes", 25):
                stale.append((jp.stem, round(a)))
        probs = [{"error": "stale_job", "key": f"stale-{jid}", "item": {"ref": jid, "age_min": a},
                  "detail": f"job {jid} has no answer after {a} min"} for jid, a in stale[:10]]
        if spec.get("style") == "aicheck":
            # Ridgeline's AI check answers: results[].chatgpt / .gemini each carry ok + error
            for job, op, r, out in self._gw_pairs(spec):
                for model in ("chatgpt", "gemini"):
                    m = r.get(model) or {}
                    if m and not m.get("ok"):
                        failed_today += 1
                        err = str(m.get("error") or "")[:300]
                        probs.append({"error": classify(err), "key": f"aicheck-{out.get('id')}-{r.get('key')}-{model}",
                                      "item": {"ref": out.get("id"), "model": model}, "detail": f"{model}: {err}"})
        else:
            for job, op, r, out in self._gw_pairs(spec):
                if not r.get("ok"):
                    failed_today += 1
        n_out = len(list(out_dir.glob("*.json"))) if out_dir.exists() else 0
        detail = f"{n_out} answers on file; {len(stale)} job(s) waiting" + (f"; {failed_today} failed op(s) today" if failed_today else "")
        status = "failed" if stale else "ok"
        return self.row(lane, spec, status, detail=detail, problems=probs, verified=True)

    def sig_heartbeat_file(self, lane, spec):
        hb = read_json(self.root / spec["file"]) or {}
        at = hb.get("at") or hb.get("updatedAt")
        a = age_min(at)
        in_win = self.clock.in_window(spec.get("window"))
        probs = []
        err_file = spec.get("error_file")
        err = read_json(self.root / err_file) if err_file else None
        if isinstance(err, dict) and self.clock.day_key(parse_iso(err.get("at") or "") or dt.datetime.fromtimestamp(0, UTC)) == self.day():
            probs.append({"error": classify(json.dumps(err)[:400]), "key": "bot-error-" + self.day(),
                          "item": {"ref": err_file}, "detail": json.dumps(err)[:300]})
        if a is None:
            return self.row(lane, spec, "unknown", detail="no heartbeat file yet", problems=probs)
        detail = f"last check-in {round(a)} min ago ({hb.get('status', '?')}, {hb.get('mode', '')})".replace(", )", ")")
        if in_win and a > spec["heartbeat_minutes"] * 1.5:
            probs.append({"error": "missing", "key": "missing-" + self.day(), "item": {"ref": spec["file"]},
                          "detail": f"{round(a)} min since the last check-in; expected every {spec['heartbeat_minutes']}"})
            return self.row(lane, spec, "missing", detail=detail, problems=probs, verified=True, extra_at=at)
        return self.row(lane, spec, "ok" if in_win else "off_hours", detail=detail + ("" if in_win else "; outside its hours"),
                        problems=probs, verified=True, extra_at=at)

    def sig_yt_build(self, lane, spec):
        jobs, outs = self.root / spec["jobs"], self.root / spec["out"]
        missing, built_today, failed_gate = [], 0, []
        min_score = spec.get("min_score", 85)
        for jp in sorted(jobs.glob("*.json")) if jobs.exists() else []:
            if jp.name.endswith(".research.json"):
                continue
            mp4 = outs / (jp.stem + ".mp4")
            if mp4.exists():
                ct = commit_time(self.root, str(mp4.relative_to(self.root)))
                if ct and self.clock.day_key(ct) == self.day():
                    # V8: a Short built today counts only when its scorecard (yt/out/<id>.score.json) passed
                    sc = read_json(outs / (jp.stem + ".score.json")) or {}
                    if sc.get("pass") is False or (isinstance(sc.get("score"), (int, float)) and sc["score"] < min_score):
                        failed_gate.append((jp.stem, sc.get("score"), [str(x) for x in (sc.get("fixes") or [])][:3]))
                    else:
                        built_today += 1
                continue
            ct = commit_time(self.root, str(jp.relative_to(self.root)))
            a = age_min(ct) if ct else None
            if a is not None and a > spec.get("stale_minutes", 90):
                missing.append((jp.stem, round(a)))
        probs = [{"error": "build_missing", "key": f"build-{jid}", "item": {"ref": jid}, "detail": f"{jid} has no mp4 after {a} min"}
                 for jid, a in missing[:5]]
        probs += [{"error": "score_fail", "key": f"score-{jid}", "item": {"ref": jid, "score": sc, "fixes": fx},
                   "detail": f"{jid} scored {sc}/100, under {min_score}: redo " + (", ".join(fx) or "see yt/out/" + jid + ".score.json")}
                  for jid, sc, fx in failed_gate[:5]]
        if spec.get("paused"):
            r = self.row(lane, spec, "paused", built_today, spec.get("daily_min"),
                         spec.get("note", "paused on purpose") + (f"; {len(missing)} unbuilt job(s)" if missing else ""), probs)
            return r
        detail = f"{built_today} Short(s) built and passed today; {len(missing)} job(s) without a video" + (f"; {len(failed_gate)} under {min_score}" if failed_gate else "")
        return self.goal_status(lane, spec, built_today, detail, probs, verified=True)

    def sig_engine_report(self, lane, spec):
        rep = read_json(self.root / spec["file"]) or {}
        gen = rep.get("generated_at")
        a = age_min(gen)
        h = rep.get("health") or {}
        in_win = self.clock.in_window(spec.get("window"))
        probs = []
        if a is None:
            return self.row(lane, spec, "unknown", detail="no engine report yet")
        counts = h.get("counts") or {}
        detail = f"report {round(a)} min old; queued {counts.get('queued', '?')}, failed {counts.get('failed', '?')}"
        if h.get("kill"):
            probs.append({"error": "platform_block", "key": "engine-kill", "item": {}, "detail": "engine kill switch is on"})
        if in_win and a > spec.get("heartbeat_minutes", 150) * 1.5:
            probs.append({"error": "missing", "key": "missing-" + self.day(), "item": {"ref": spec["file"]},
                          "detail": f"no engine pass for {round(a)} min"})
            return self.row(lane, spec, "missing", detail=detail, problems=probs, verified=True)
        return self.row(lane, spec, "ok" if in_win else "off_hours", detail=detail, problems=probs, verified=True)

    def sig_runlog_count(self, lane, spec):
        """Daily goal read from the run log: sum of the number the regex finds in today's notes for the task."""
        lines = [r for r in self.runlog_task(spec["task"]) if r.get("day") == self.day() or
                 self.clock.day_key(parse_iso(r.get("started") or "") or dt.datetime.fromtimestamp(0, UTC)) == self.day()]
        rx = re.compile(spec["count_regex"], re.I) if spec.get("count_regex") else None
        n, probs = 0, []
        for r in lines:
            if r.get("outcome") == "failed":
                probs.append({"error": classify(r.get("note")), "key": f"run-{r.get('started')}", "item": {"ref": r.get("run") or r.get("started")},
                              "detail": (r.get("note") or "")[:300]})
            if rx:
                m = rx.search(r.get("note") or "")
                if m:
                    n += int(m.group(1))
            else:
                n += 1 if r.get("outcome") in ("done", "ok") else 0
        last = lines[-1] if lines else None
        detail = (f"{n} {spec.get('unit', 'done')} today across {len(lines)} run(s)" if lines else "no run today yet")
        if last and last.get("needsYou"):
            detail += f"; crew asks: {last['needsYou'][:120]}"
        return self.goal_status(lane, spec, n if lines else (0 if self.clock.local().hour >= spec.get("goal_hour", 20) else None), detail, probs, verified=True)

    def sig_runlog_heartbeat(self, lane, spec):
        lines = self.runlog_task(spec["task"])
        last = lines[-1] if lines else None
        in_win = self.clock.in_window(spec.get("window"))
        if not last:
            return self.row(lane, spec, "unknown", detail="no run-log line yet")
        a = age_min(last.get("finished") or last.get("started"))
        probs = []
        detail = f"last run {round(a)} min ago: {(last.get('note') or '')[:100]}"
        if last.get("outcome") == "failed":
            probs.append({"error": classify(last.get("note")), "key": f"run-{last.get('started')}", "item": {"ref": last.get("started")},
                          "detail": (last.get("note") or "")[:300]})
        if in_win and a is not None and a > spec["heartbeat_minutes"] * 1.5:
            probs.append({"error": "missing", "key": "missing-" + self.day(), "item": {"ref": spec["task"]},
                          "detail": f"{round(a)} min since the last run; expected every {spec['heartbeat_minutes']}"})
            return self.row(lane, spec, "missing", detail=detail, problems=probs, verified=True)
        return self.row(lane, spec, ("failed" if probs else "ok") if in_win else "off_hours", detail=detail, problems=probs, verified=True)

    def sig_http(self, lane, spec):
        if OFFLINE:
            return self.row(lane, spec, "unknown", detail="offline: website not checked")
        code, body = http_get(spec["url"])
        marker = spec.get("expect_text")
        if code == 0:                                      # no connection at all: the runner's network, not the site
            return self.row(lane, spec, "unknown", detail=f"could not reach {spec['url']} from here ({body[:80]})")
        ok = code == 200 and (not marker or marker in body)
        detail = f"HTTP {code}" + ("" if ok else (", marker missing" if code == 200 else "")) + f" for {spec['url']}"
        probs = [] if ok else [{"error": "down", "key": "down-" + self.day(), "item": {"ref": spec["url"]}, "detail": detail}]
        return self.row(lane, spec, "ok" if ok else "failed", detail=detail, problems=probs, verified=ok)

    def sig_actions_runs(self, lane, spec):
        """Failed GitHub Actions runs in the last day for the workflows we own (re-run once each)."""
        runs = self.gh.runs(now_utc() - dt.timedelta(hours=spec.get("hours", 24)), spec.get("workflows"))
        if runs is None:
            return self.row(lane, spec, "unknown", detail="Actions API not reachable in this run (no token or offline)")
        self._runs_cache = runs
        watch = set(spec.get("workflows", []))
        branches = {self.gh.ref, self.cfg.get("branch", "main")}
        probs, failed, total = [], 0, 0
        # a failure that a newer run of the same workflow already healed is history, not a problem
        latest_ok = {}
        for run in runs:
            if run.get("conclusion") == "success" and run.get("head_branch") in branches:
                wf = (run.get("path") or "").split("/")[-1]
                latest_ok[wf] = max(latest_ok.get(wf, ""), run.get("created_at") or "")
        for run in runs:
            wf = (run.get("path") or "").split("/")[-1]
            if watch and wf not in watch:
                continue
            if run.get("head_branch") not in branches:
                continue                                   # a feature branch's failure is not the business's
            if (run.get("created_at") or "") < latest_ok.get(wf, ""):
                total += 1
                continue
            total += 1
            if run.get("conclusion") in ("failure", "timed_out", "startup_failure"):
                failed += 1
                probs.append({"error": "run_failed", "key": f"run-{run.get('id')}", "item": {"ref": str(run.get("id")), "workflow": wf, "name": run.get("name")},
                              "detail": f"{run.get('name')} {run.get('conclusion')} at {run.get('created_at')}"})
        detail = f"{total} run(s) in {spec.get('hours', 24)} h, {failed} failed"
        return self.row(lane, spec, "failed" if failed else "ok", detail=detail, problems=probs[:8], verified=True)

    # ---- crews (Claude scheduled tasks: read-only here; a miss becomes a ticket) --------------------
    def check_crews(self):
        for task, spec in (self.cfg.get("crews") or {}).items():
            lines = self.runlog_task(task)
            last = lines[-1] if lines else None
            row = {"task": task, "label": spec.get("label", task), "status": "ok", "last": None, "age_h": None, "note": ""}
            if spec.get("paused"):
                row.update(status="paused", note=spec.get("note", "switched off on purpose"))
                self.crews.append(row)
                continue
            if not last:
                row.update(status="unknown", note="no run-log line yet")
                self.crews.append(row)
                continue
            fin = last.get("finished") or last.get("started")
            a = age_min(fin)
            row.update(last=fin, age_h=round(a / 60, 1) if a is not None else None, note=(last.get("note") or "")[:140])
            if last.get("outcome") == "failed":
                row["status"] = "failed"
                self.problems.append({"lane": "crew:" + task, "error": "crew_failed", "key": f"crew-failed-{fin}",
                                      "item": {"ref": task, "run": last.get("run")}, "detail": (last.get("note") or "")[:300]})
            every = spec.get("every_hours")
            in_win = self.clock.in_window(spec.get("window"))
            if every and in_win and a is not None and a > (every + spec.get("grace_hours", 2)) * 60:
                row["status"] = "late"
                self.problems.append({"lane": "crew:" + task, "error": "crew_missing", "key": f"crew-missing-{task}-{self.day()}",
                                      "item": {"ref": task, "trigger": spec.get("trigger")},
                                      "detail": f"no {spec.get('label', task)} run logged for {round(a / 60, 1)} h (expected every {every} h)"})
            if last.get("needsYou"):
                row["needsYou"] = last["needsYou"][:200]
            self.crews.append(row)

    # ---- fixing ------------------------------------------------------------------------------
    def ordered_playbook(self, lane, err, base):
        """Try what worked last time first. That's the 'gets smarter' part."""
        winners = [r["lesson"].split(" by ")[-1] for r in self.db.execute(
            "SELECT lesson FROM lessons WHERE lane=? AND lesson LIKE ? ORDER BY hits DESC", (lane, f"{err} fixed by %"))]
        return list(dict.fromkeys([w for w in winners if w in base] + list(base)))

    def spec_for(self, lane):
        if lane.startswith("crew:"):
            return self.cfg["crews"].get(lane[5:], {}), True
        return self.cfg["lanes"].get(lane, {}), False

    def fix(self, lane, p, inc):
        """Run the lane's playbook once per step per day. Returns (outcome, step, verified)."""
        spec, is_crew = self.spec_for(lane)
        err = p["error"]
        if err in HUMAN_ERRORS:
            return "needs_human", None, False
        base = spec.get("playbook") or (["fire_task"] if is_crew else [])
        tried = json.loads(inc["steps_tried"] or "[]")
        for step in self.ordered_playbook(lane, err, base):
            if step in LOCAL_STEPS:
                if self.tried_today(lane, step, p["key"]) >= 1 or self.dispatches >= self.cfg.get("max_dispatches_per_pass", 6):
                    continue
                self.note_try(lane, step, p["key"])
                tried.append(step)
                ok, verified = self.local_fix(lane, spec, step, p)
                if ok:
                    self.dispatches += 1                   # count real dispatches only; a step with nothing to do costs none
                self.db.execute("UPDATE incidents SET steps_tried=?, fix_step=?, fixed_at=? WHERE id=?",
                                (json.dumps(tried), step, iso() if ok else None, inc["id"]))
                if ok and verified:
                    return "fixed", step, True
                if ok:
                    return "pending_verify", step, False
            elif step in CREW_STEPS:
                if step in tried:
                    continue
                tried.append(step)
                self.db.execute("UPDATE incidents SET steps_tried=? WHERE id=?", (json.dumps(tried), inc["id"]))
                self.ticket(lane, p, inc, step, spec)
                return "ticketed", step, False
        return "exhausted", None, False

    def local_fix(self, lane, spec, step, p):
        """The fixes the Medic can do by itself. Each returns (started, verified_live)."""
        err, item = p["error"], p.get("item") or {}
        wf = spec.get("workflow")
        if err == "stale_job" and wf:                      # gateway job the Action never picked up
            ok = self.gh.dispatch(wf, {"job": item.get("ref", "")} if spec.get("job_input", True) else {})
            out = f"{spec['out']}/{item.get('ref')}.json"
            ver = ok and self.wait_for(lambda: self.remote_exists(out), spec.get("verify_seconds", 240))
            return ok, ver
        if err == "build_missing" and wf:                  # a Short that never built
            ok = self.gh.dispatch(wf, {"job": item.get("ref", "")})
            return ok, False                               # builds take 10+ min: verified on the next pass
        if err == "missing" and wf and step in ("retry", "restart_bot"):   # a bot or the engine stopped checking in
            before = (read_json(self.root / spec["file"]) or {}).get("at") or (read_json(self.root / spec["file"]) or {}).get("generated_at")
            ok = self.gh.dispatch(wf, {})

            def newer():
                j = self.remote_json(spec["file"]) or {}
                at = j.get("at") or j.get("generated_at")
                return bool(at) and at != before and (age_min(at) or 999) < spec.get("heartbeat_minutes", 30)
            ver = ok and self.wait_for(newer, spec.get("verify_seconds", 180))
            return ok, ver
        if err == "down" and step == "redeploy":           # the website
            ok = self.gh.pages_build()
            ver = ok and self.wait_for(lambda: http_get(spec["url"])[0] == 200, 180, every=30)
            return ok, ver
        if err == "run_failed" and step in ("retry", "rerun_failed"):
            ok = self.gh.rerun_failed(item.get("ref"))
            return ok, False                               # verified on the next pass when the run shows success
        if err == "missing" and step == "retry" and not wf:
            return False, False
        return False, False

    def ticket(self, lane, p, inc, step, spec):
        q = self.home / "queue"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{lane}--{p['key']}")[:120]
        if DRY:
            log(f"DRY: would open ticket {safe} ({p['error']}) for the crew")
            return
        q.mkdir(exist_ok=True)
        path = q / (safe + ".json")
        if path.exists():
            return
        t = {"id": safe, "biz": self.cfg.get("biz"), "lane": lane, "label": spec.get("label", lane), "error": p["error"],
             "item": p.get("item") or {}, "detail": p.get("detail", "")[:400], "suggested_steps": [s for s in (spec.get("playbook") or ["fire_task"]) if s in CREW_STEPS],
             "first_step": step, "opened_at": iso(), "for": self.cfg.get("crew_owner", "the crew"), "status": "open",
             "how_to_close": "do the fix, then set status to done with a one-line note; the Medic removes the file once the lane is green"}
        path.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        self.db.execute("UPDATE incidents SET ticket=? WHERE id=?", (safe, inc["id"]))
        log(f"ticket for {t['for']}: {safe} ({p['error']})")

    def learn(self, lane, lesson):
        row = self.db.execute("SELECT id, hits FROM lessons WHERE lane=? AND lesson=?", (lane, lesson)).fetchone()
        rule = False
        if row:
            hits = row["hits"] + 1
            rule = hits >= 3
            self.db.execute("UPDATE lessons SET hits=?, is_rule=? WHERE id=?", (hits, int(rule), row["id"]))
        else:
            self.db.execute("INSERT INTO lessons(lane, lesson, created_at) VALUES (?,?,?)", (lane, lesson, iso()))
        self.notes.append(f"learned: {lane}: {lesson}")
        if DRY:
            return
        d = self.home / "lessons"
        d.mkdir(exist_ok=True)
        with open(d / (re.sub(r"[^A-Za-z0-9_-]+", "-", lane) + ".md"), "a", encoding="utf-8") as f:
            f.write(f"- {self.day()}: {lesson}\n")
        if rule:
            with open(d / "RULES.md", "a", encoding="utf-8") as f:
                f.write(f"- {self.day()} RULE ({lane}): {lesson}; this fix is now tried first and the lane's crew should make it permanent.\n")

    def needs_human_msg(self, lane, p, tried):
        spec, _ = self.spec_for(lane)
        platform = spec.get("platform_label") or spec.get("label", lane)
        tpl = (self.cfg.get("needs_human") or {}).get(p["error"])
        if tpl:
            return tpl.format(platform=platform, lane=spec.get("label", lane), detail=p.get("detail", "")[:120])
        if p["error"] in ("missing", "crew_missing"):
            return (self.cfg.get("needs_human") or {}).get("missing", "{lane} has not run. Open the scheduled tasks list and tap Run.").format(
                platform=platform, lane=spec.get("label", lane), detail=p.get("detail", "")[:120])
        return f"{spec.get('label', lane)}: the Medic tried {', '.join(tried) or 'nothing it is allowed to'} and couldn't fix it ({p.get('detail', '')[:100]}). Open the app to see the details."

    # ---- one pass --------------------------------------------------------------------------------
    def run(self):
        t0 = time.time()
        log(f"pass {iso()} ({self.clock.hhmm()} {self.cfg.get('tz')}) biz={self.cfg.get('biz')} dry={DRY} offline={OFFLINE} token={'yes' if self.gh.ok else 'no'}")
        for lane, spec in self.cfg["lanes"].items():
            if spec.get("parked"):
                continue                                   # parked stays parked: never checked, never mentioned
            self.board.append(self.signal(lane, spec))
        self.check_crews()

        # incidents: open, fix, verify, close, learn
        seen = set()
        for p in self.problems:
            lane, key = p["lane"], p["key"]
            seen.add((lane, key))
            inc = self.db.execute("SELECT * FROM incidents WHERE lane=? AND key=? AND closed_at IS NULL", (lane, key)).fetchone()
            if not inc:
                self.db.execute("INSERT INTO incidents(lane, key, error_kind, item_ref, opened_at, last_seen, outcome, steps_tried) VALUES (?,?,?,?,?,?,?,?)",
                                (lane, key, p["error"], json.dumps(p.get("item") or {}), iso(), iso(), "open", "[]"))
                inc = self.db.execute("SELECT * FROM incidents WHERE lane=? AND key=? AND closed_at IS NULL", (lane, key)).fetchone()
            else:
                self.db.execute("UPDATE incidents SET last_seen=? WHERE id=?", (iso(), inc["id"]))
            if inc["fix_step"] and inc["outcome"] == "open" and inc["fixed_at"] and age_min(inc["fixed_at"]) < 15:
                continue                                   # a fix just started; give it a pass before judging
            outcome, step, verified = self.fix(lane, p, inc)
            tried = json.loads(self.db.execute("SELECT steps_tried FROM incidents WHERE id=?", (inc["id"],)).fetchone()["steps_tried"] or "[]")
            if outcome == "fixed":
                self.close(inc["id"], "fixed", step, verified=True)
                self.learn(lane, f"{p['error']} fixed by {step}")
                self.fixed.append({"lane": lane, "what": p.get("detail", "")[:140], "step": step, "at": iso(), "verified": True})
                seen.discard((lane, key))
            elif outcome == "needs_human":
                self.db.execute("UPDATE incidents SET outcome='needs_human' WHERE id=?", (inc["id"],))
                self.needs.append({"lane": lane, "msg": self.needs_human_msg(lane, p, tried), "since": inc["opened_at"], "error": p["error"]})
            elif outcome in ("exhausted", "ticketed", "pending_verify"):
                opened = parse_iso(inc["opened_at"])
                grace = self.cfg.get("ticket_grace_hours", 8) if outcome == "ticketed" or inc["ticket"] else self.cfg.get("human_after_hours", 2)
                if outcome == "exhausted" and not inc["ticket"] and p["error"] in ("under_goal",):
                    grace = self.cfg.get("under_goal_human_hours", 3)
                if opened and (now_utc() - opened).total_seconds() / 3600 >= grace and (tried or outcome == "exhausted"):
                    self.db.execute("UPDATE incidents SET outcome='needs_human' WHERE id=?", (inc["id"],))
                    self.needs.append({"lane": lane, "msg": self.needs_human_msg(lane, p, tried), "since": inc["opened_at"], "error": p["error"]})
        # problems that went away since the last pass
        for inc in self.db.execute("SELECT * FROM incidents WHERE closed_at IS NULL").fetchall():
            if (inc["lane"], inc["key"]) in seen:
                continue
            if inc["fix_step"]:
                self.close(inc["id"], "fixed", inc["fix_step"], verified=True)
                self.learn(inc["lane"], f"{inc['error_kind']} fixed by {inc['fix_step']}")
                self.fixed.append({"lane": inc["lane"], "what": f"{inc['error_kind']} ({inc['item_ref']})"[:140], "step": inc["fix_step"], "at": iso(), "verified": True})
            else:
                self.close(inc["id"], "recovered", None, verified=True)
            self.drop_ticket(inc["ticket"])

        self.snapshot_lanes()
        report = self.report()
        self.db.commit()
        log(f"done in {round(time.time() - t0, 1)} s: {len(self.problems)} problem(s), {len(self.fixed)} fixed, {len(self.needs)} need Grayson, {self.gh.calls} API call(s)")
        return report

    def close(self, inc_id, outcome, step, verified):
        self.db.execute("UPDATE incidents SET outcome=?, closed_at=?, fix_step=COALESCE(?, fix_step), verified=? WHERE id=?",
                        (outcome, iso(), step, int(bool(verified)), inc_id))

    def drop_ticket(self, ticket_id):
        if not ticket_id or DRY:
            return
        p = self.home / "queue" / (ticket_id + ".json")
        if p.exists():
            done = self.home / "queue" / "done"
            done.mkdir(exist_ok=True)
            try:
                t = read_json(p) or {}
                t["resolved_at"] = iso()
                (done / p.name).write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
                # keep done/ small: newest 40
                for old in sorted(done.glob("*.json"), key=lambda x: x.stat().st_mtime)[:-40]:
                    old.unlink()
            except Exception:
                pass
            p.unlink()

    def snapshot_lanes(self):
        for r in self.board:
            self.db.execute("INSERT INTO lane_days(day, lane, done, goal, status, detail, updated_at) VALUES (?,?,?,?,?,?,?) "
                            "ON CONFLICT(day, lane) DO UPDATE SET done=excluded.done, goal=excluded.goal, status=excluded.status, detail=excluded.detail, updated_at=excluded.updated_at",
                            (self.day(), r["lane"], r.get("done"), r.get("goal"), r["status"], r.get("detail", "")[:300], iso()))
            last = self.db.execute("SELECT status FROM runs WHERE lane=? AND date(started_at)=? ORDER BY id DESC LIMIT 1", (r["lane"], self.day())).fetchone()
            st = {"ok": "ok", "off_hours": "ok", "off_day": "ok", "pending": "ok", "late": "failed", "under_goal": "failed", "failed": "failed",
                  "missing": "missing", "paused": "ok", "manual": "ok", "unknown": "ok"}[r["status"]]
            if not last or last["status"] != st:
                self.db.execute("INSERT INTO runs(lane, started_at, status, item_ref, detail) VALUES (?,?,?,?,?)",
                                (r["lane"], iso(), st, None, r.get("detail", "")[:300]))

    def yesterday(self):
        y = self.clock.day_key(now_utc() - dt.timedelta(days=1))
        rows = self.db.execute("SELECT lane, done, goal, status FROM lane_days WHERE day=?", (y,)).fetchall()
        return {"day": y, "lanes": {r["lane"]: {"done": r["done"], "goal": r["goal"], "status": r["status"]} for r in rows}}

    def report(self):
        open_tickets = []
        for p in sorted((self.home / "queue").glob("*.json")):
            t = read_json(p) or {}
            open_tickets.append({"id": t.get("id", p.stem), "lane": t.get("lane"), "error": t.get("error"), "opened_at": t.get("opened_at"),
                                 "status": t.get("status", "open"), "for": t.get("for")})
        fixed_today = [dict(r) for r in self.db.execute(
            "SELECT lane, error_kind, fix_step, closed_at, verified FROM incidents WHERE outcome='fixed' AND date(closed_at)=date(?) ORDER BY id DESC LIMIT 20", (iso(),)).fetchall()]
        lessons_new = [dict(r) for r in self.db.execute("SELECT lane, lesson, hits, is_rule FROM lessons WHERE date(created_at)=date(?) LIMIT 20", (iso(),)).fetchall()]
        # dedupe needs-you by lane
        needs, seen = [], set()
        for n in self.needs:
            if n["lane"] in seen:
                continue
            seen.add(n["lane"])
            needs.append(n)
        red = [r for r in self.board if r["status"] in ("failed", "missing", "under_goal")]
        summary = (f"{len(self.board)} lanes: {sum(1 for r in self.board if r['status'] in ('ok', 'off_hours', 'off_day'))} fine, "
                   f"{len(red)} red, {sum(1 for r in self.board if r['status'] == 'paused')} paused; "
                   f"fixed today {len(fixed_today)}; needs you {len(needs)}; tickets open {len(open_tickets)}")
        rep = {"schema": 1, "medic": VERSION, "biz": self.cfg.get("biz"), "generated_at": iso(), "day": self.day(), "tz": self.cfg.get("tz"),
               "local_time": self.clock.hhmm(), "dry_run": DRY, "actions_api": self.gh.ok, "summary": summary,
               "board": self.board, "crews": self.crews, "fixed_today": fixed_today, "fixed_this_pass": self.fixed, "needs_you": needs,
               "tickets_open": open_tickets, "lessons_new": lessons_new, "yesterday": self.yesterday(), "notes": self.notes[:20],
               "honesty": "Numbers come from this repo's own files (run log, gateway answers, heartbeats, builds) and the GitHub Actions API. "
                          "Unknown stays unknown. A fix counts only when the Medic saw it live afterwards."}
        if not DRY:
            out = self.home / "public" / "medic_report.json"
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return rep


# ----------------------------------------------------------------------------- selftest

def selftest():
    import tempfile, shutil
    global NOW_OVERRIDE
    tmp = Path(tempfile.mkdtemp(prefix="medic-selftest-"))
    try:
        root = tmp / "repo"
        (root / ".git").mkdir(parents=True)
        med = root / "medic"
        med.mkdir()
        shutil.copy(HERE / "schema.sql", med / "schema.sql")
        NOW_OVERRIDE = dt.datetime(2026, 10, 24, 20, 30, tzinfo=UTC)   # 3:30 PM Central, a Saturday
        # run log: a reply-desk heartbeat that is late, a day-shift with 12 sent today, a failed task
        (root / "office").mkdir()
        lines = [
            {"task": "reply-desk", "day": "2026-10-24", "started": "2026-10-24T12:38:00Z", "finished": "2026-10-24T12:39:00Z", "outcome": "done", "note": "nothing new"},
            {"task": "day-shift", "day": "2026-10-24", "started": "2026-10-24T12:07:00Z", "finished": "2026-10-24T12:30:00Z", "outcome": "done", "note": "12 leads, 9 qualified, 12 sent"},
            {"task": "night-shift", "day": "2026-10-23", "started": "2026-10-23T06:55:00Z", "finished": "2026-10-23T07:25:00Z", "outcome": "done", "note": "built 2"},
            {"task": "bolt", "day": "2026-10-24", "started": "2026-10-24T12:13:00Z", "finished": "2026-10-24T12:16:00Z", "outcome": "failed", "note": "Etsy 401 token expired"},
        ]
        (root / "office" / "runlog.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        # gateway: one answered job today (2 pins scheduled, 1 listing created, 1 failed op), one stale job
        (root / "gw" / "jobs").mkdir(parents=True)
        (root / "gw" / "out").mkdir(parents=True)
        job = {"id": "bolt-1", "ops": [
            {"op": "zernio", "method": "POST", "path": "/posts", "body": {"platforms": [{"platform": "pinterest"}]}},
            {"op": "zernio", "method": "POST", "path": "/posts", "body": {"platforms": [{"platform": "pinterest"}]}},
            {"op": "etsy", "method": "POST", "path": "/shops/1/listings", "body": {}},
            {"op": "zernio", "method": "POST", "path": "/posts", "body": {"platforms": [{"platform": "instagram"}]}}]}
        (root / "gw" / "jobs" / "bolt-1.json").write_text(json.dumps(job))
        (root / "gw" / "out" / "bolt-1.json").write_text(json.dumps({"id": "bolt-1", "at": "2026-10-24T13:00:00Z", "ok": False, "results": [
            {"i": 0, "op": "zernio", "status": 201, "ok": True}, {"i": 1, "op": "zernio", "status": 201, "ok": True},
            {"i": 2, "op": "etsy", "status": 201, "ok": True}, {"i": 3, "op": "zernio", "status": 403, "ok": False, "error": "HTTP 403 forbidden: account disconnected"}]}))
        (root / "gw" / "jobs" / "stale-1.json").write_text(json.dumps({"id": "stale-1", "ops": []}))
        old = (NOW_OVERRIDE - dt.timedelta(minutes=50)).timestamp()
        os.utime(root / "gw" / "jobs" / "stale-1.json", (old, old))
        # heartbeats: crypto fresh, stock bot stale but it is Saturday (off hours)
        (root / "trading").mkdir()
        (root / "trading" / "crypto.json").write_text(json.dumps({"at": "2026-10-24T20:25:00Z", "status": "ok", "mode": "virtual"}))
        (root / "trading" / "auto.json").write_text(json.dumps({"at": "2026-10-23T21:56:00Z", "status": "closed", "mode": "paper"}))
        # yt: one built job, one unbuilt and old
        (root / "yt" / "jobs").mkdir(parents=True)
        (root / "yt" / "out").mkdir(parents=True)
        (root / "yt" / "jobs" / "ep1.json").write_text("{}")
        (root / "yt" / "out" / "ep1.mp4").write_bytes(b"x")
        (root / "yt" / "jobs" / "ep2.json").write_text("{}")
        os.utime(root / "yt" / "jobs" / "ep2.json", (old - 7200, old - 7200))
        cfg = {"version": VERSION, "biz": "test", "tz": "America/Chicago", "repo": "x/y", "branch": "main", "runlog": "office/runlog.jsonl",
               "crew_owner": "test crew", "ticket_grace_hours": 8, "max_dispatches_per_pass": 6,
               "sources": {"gateway": {"jobs": "gw/jobs", "out": "gw/out"}},
               "lanes": {
                   "etsy_listing": {"label": "Etsy listings", "signal": "gw_count", "op": "etsy", "method": "POST", "path_regex": r"^/shops/\d+/listings$", "unit": "listings", "daily_min": 1, "daily_max": 2, "goal_hour": 20, "playbook": ["retry", "rescore_rebuild", "next_slot"]},
                   "pinterest": {"label": "Pinterest", "signal": "gw_count", "op": "zernio", "method": "POST", "platform": "pinterest", "unit": "pins", "daily_min": 6, "goal_hour": 20, "playbook": ["retry", "rehost_images", "next_slot"]},
                   "instagram_shop": {"label": "Instagram", "signal": "gw_count", "op": "zernio", "method": "POST", "platform": "instagram", "unit": "posts", "daily_min": 1, "goal_hour": 20, "playbook": ["retry", "backup_poster"]},
                   "gateway": {"label": "Gateway", "signal": "gw_jobs", "jobs": "gw/jobs", "out": "gw/out", "stale_minutes": 25, "workflow": "gw.yml", "playbook": ["retry"]},
                   "crypto_paper": {"label": "Crypto bot", "signal": "heartbeat_file", "file": "trading/crypto.json", "heartbeat_minutes": 30, "workflow": "crypto.yml", "playbook": ["retry"]},
                   "trading_paper": {"label": "Stock bot", "signal": "heartbeat_file", "file": "trading/auto.json", "heartbeat_minutes": 15, "window": {"start": "08:40", "end": "15:00", "days": "weekdays"}, "workflow": "auto.yml", "playbook": ["retry"]},
                   "gmula_shorts": {"label": "Shorts", "signal": "yt_build", "jobs": "yt/jobs", "out": "yt/out", "stale_minutes": 90, "workflow": "yt.yml", "daily_min": 1, "playbook": ["retry", "rescore_rebuild"]},
                   "rl_outreach": {"label": "Outreach", "signal": "runlog_count", "task": "day-shift", "count_regex": r"(\d+) sent", "unit": "emails", "daily_min": 10, "goal_hour": 20, "window": {"days": "all"}, "playbook": ["retry", "next_slot"]},
                   "rl_replies": {"label": "Reply desk", "signal": "runlog_heartbeat", "task": "reply-desk", "heartbeat_minutes": 120, "window": {"start": "07:30", "end": "23:59", "days": "all"}, "playbook": ["fire_task"]},
                   "parked_one": {"label": "Gumroad", "signal": "manual", "parked": True},
                   "social_manual": {"label": "Ridgeline social", "signal": "manual", "note": "Grayson posts"}},
               "crews": {"night-shift": {"label": "Night Shift", "every_hours": 24, "grace_hours": 3}, "bolt": {"label": "Bolt", "every_hours": 8, "grace_hours": 2}},
               "needs_human": {"auth_expired": "Your {platform} login expired. Tap the reconnect link, then you're done.",
                               "platform_block": "{platform} paused posting. Open the {platform} app and clear the notice.",
                               "missing": "{lane} has not run. Open the scheduled tasks list and tap Run."}}
        (med / "lanes.json").write_text(json.dumps(cfg))
        for k in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_REPOSITORY", "GITHUB_REF_NAME"):
            os.environ.pop(k, None)
        m = Medic(med / "lanes.json", dry=False, offline=True)
        rep = m.run()
        b = {r["lane"]: r for r in rep["board"]}
        assert "parked_one" not in b, "parked lane must never be checked"
        assert b["etsy_listing"]["done"] == 1 and b["etsy_listing"]["status"] == "ok", b["etsy_listing"]
        assert b["pinterest"]["done"] == 2 and b["pinterest"]["status"] == "pending", b["pinterest"]
        assert b["instagram_shop"]["done"] == 0 and b["instagram_shop"]["status"] == "late", b["instagram_shop"]
        assert b["gateway"]["status"] == "failed" and "stale-1" in b["gateway"]["detail"] or "1 job(s) waiting" in b["gateway"]["detail"], b["gateway"]
        assert b["crypto_paper"]["status"] == "ok", b["crypto_paper"]
        assert b["trading_paper"]["status"] == "off_hours", b["trading_paper"]
        assert b["gmula_shorts"]["done"] == 1 and "1 job(s) without a video" in b["gmula_shorts"]["detail"], b["gmula_shorts"]
        assert b["rl_outreach"]["done"] == 12 and b["rl_outreach"]["status"] == "ok", b["rl_outreach"]
        assert b["rl_replies"]["status"] == "missing", b["rl_replies"]
        assert b["social_manual"]["status"] == "manual"
        crews = {c["task"]: c for c in rep["crews"]}
        assert crews["night-shift"]["status"] == "late", crews["night-shift"]
        assert crews["bolt"]["status"] == "failed", crews["bolt"]
        errs = {(p["lane"], p["error"]) for p in m.problems}
        assert ("instagram_shop", "platform_block") in errs, errs
        assert ("gateway", "stale_job") in errs and ("gmula_shorts", "build_missing") in errs, errs
        assert ("crew:bolt", "crew_failed") in errs and ("crew:night-shift", "crew_missing") in errs, errs
        # needs-you: the 403 is a human error (platform_block) -> message right away, with the tap
        msgs = {n["lane"]: n["msg"] for n in rep["needs_you"]}
        assert "Instagram paused posting" in msgs.get("instagram_shop", ""), msgs
        # tickets: crew problems and rl_replies (fire_task) became tickets; the gateway lane has no crew step (no ticket)
        tickets = {t["lane"] for t in rep["tickets_open"]}
        assert "rl_replies" in tickets and "crew:night-shift" in tickets and "crew:bolt" in tickets, tickets
        assert "gateway" not in tickets, tickets
        # fix-once: the dispatch attempt is recorded (offline it could not start), so a second pass will not try it again today
        assert m.tried_today("gateway", "retry", "stale-stale-1") == 1
        # a dry run leaves no files behind
        before = sorted(str(x) for x in med.rglob("*"))
        Medic(med / "lanes.json", dry=True, offline=True).run()
        assert sorted(str(x) for x in med.rglob("*")) == before, "dry run wrote files"
        # classify + time helpers
        assert classify("HTTP 401 Unauthorized") == "auth_expired" and classify("insufficient_quota") == "billing"
        assert classify("Pinterest: This site doesn't allow you to save Pins") == "platform_block" and classify("boom") == "unknown"
        assert m.clock.day_key() == "2026-10-24" and m.clock.in_window({"start": "08:40", "end": "15:00", "days": "weekdays"}) is False
        assert parse_iso("2026-10-24T00:42:27.258004-05:00").strftime("%H:%M") == "05:42"
        # a second pass closes nothing (problems persist) and keeps the incident count stable
        n1 = m.db.execute("SELECT COUNT(*) FROM incidents WHERE closed_at IS NULL").fetchone()[0]
        m2 = Medic(med / "lanes.json", dry=False, offline=True)
        m2.run()
        n2 = m2.db.execute("SELECT COUNT(*) FROM incidents WHERE closed_at IS NULL").fetchone()[0]
        assert n1 == n2, (n1, n2)
        # when a problem disappears after a fix was started, the incident closes as fixed and a lesson is learned
        (root / "gw" / "out" / "stale-1.json").write_text(json.dumps({"id": "stale-1", "at": "2026-10-24T20:29:00Z", "ok": True, "results": []}))
        m3 = Medic(med / "lanes.json", dry=False, offline=True)
        m3.db.execute("UPDATE incidents SET fix_step='retry', fixed_at=? WHERE lane='gateway'", (iso(now_utc() - dt.timedelta(minutes=40)),))
        m3.db.commit()
        rep3 = m3.run()
        row = m3.db.execute("SELECT outcome, verified FROM incidents WHERE lane='gateway'").fetchone()
        assert row["outcome"] == "fixed" and row["verified"] == 1, dict(row)
        assert any("stale_job fixed by retry" in l["lesson"] for l in rep3["lessons_new"]), rep3["lessons_new"]
        assert (med / "lessons" / "gateway.md").exists()
        print("medic selftest ok")
    finally:
        NOW_OVERRIDE = None
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(HERE / "lanes.json"))
    ap.add_argument("--dry-run", action="store_true", help="look and report; dispatch nothing, write no report")
    ap.add_argument("--offline", action="store_true", help="no network at all (no Actions API, no website checks, no git fetch)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--board", action="store_true", help="print the board from the last report and exit")
    ap.add_argument("--now", help="pretend it is this UTC time (tests)")
    a = ap.parse_args()
    global NOW_OVERRIDE
    if a.selftest:
        return selftest()
    if a.now:
        NOW_OVERRIDE = parse_iso(a.now)
    if a.board:
        rep = read_json(Path(a.config).resolve().parent / "public" / "medic_report.json") or {}
        for r in rep.get("board", []):
            print(f"{r['status']:>10}  {r['label']:<24} {r.get('done', '') if r.get('done') is not None else '—'}/{r.get('goal') or '—'}  {r.get('detail', '')}")
        for n in rep.get("needs_you", []):
            print("NEEDS YOU:", n["msg"])
        return
    m = Medic(a.config, dry=a.dry_run, offline=a.offline)
    rep = m.run()
    for r in rep["board"]:
        print(f"  {r['status']:>10}  {r['label']:<24} {r.get('done') if r.get('done') is not None else '—'}/{r.get('goal') or '—'}  {r.get('detail', '')[:110]}")
    for c in rep["crews"]:
        print(f"  crew {c['status']:>8}  {c['label']:<22} {c.get('age_h') if c.get('age_h') is not None else '—'} h  {c.get('note', '')[:90]}")
    for f in rep["fixed_this_pass"]:
        print("  FIXED:", f["lane"], f["step"], f["what"])
    for n in rep["needs_you"]:
        print("  NEEDS YOU:", n["lane"], "->", n["msg"])
    for t in rep["tickets_open"]:
        print("  ticket:", t["id"], t["status"])


if __name__ == "__main__":
    main()
