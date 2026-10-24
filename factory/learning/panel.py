"""Dashboard numbers for the agent panels (factory/learning, Phase 9). Everything here is counted from the learning
rows; nothing is estimated. Unknown stays "unknown". Production and offline rows never mix; incompatible rubric ids
and workflow versions never share a row."""
from __future__ import annotations

import json
import typing as t
from datetime import timedelta

from .brain import AgentBrain, BUSINESS_SCOPES, _parse
from .rubric import RUBRICS, rubric_id_of

RUBRIC_NAMES = {rubric_id_of(r): r["name"] for r in RUBRICS.values()}


def _tokens_known(brain: AgentBrain) -> dict[str, dict]:
    """Known provider tokens / cost per engine agent (runs ↔ model_usage); unknown-cost calls are counted apart."""
    rows = brain.store.rows("SELECT r.agent_id a, SUM(COALESCE(u.tokens_in,0)+COALESCE(u.tokens_out,0)) tok, SUM(u.cost_usd) usd, "
                            "SUM(CASE WHEN u.cost_usd IS NULL THEN u.calls ELSE 0 END) unk, SUM(u.calls) calls "
                            "FROM model_usage u JOIN runs r ON u.run_id=r.id GROUP BY r.agent_id")
    return {r["a"]: {"calls": int(r["calls"] or 0), "tokens_known": int(r["tok"] or 0) if r["tok"] else None, "cost_usd_known": round(r["usd"], 4) if r["usd"] is not None else None,
                     "unknown_cost_calls": int(r["unk"] or 0)} for r in rows}


def agent_panel(brain: AgentBrain, scope: str, agent: str, mode: str = "production", days: int = 30) -> dict:
    since = (_parse(brain.now()) - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")
    groups = [g for g in brain.stats(scope, agent, mode) if g["kind"] == "score"]
    runs = [g for g in brain.stats(scope, agent, mode) if g["kind"] == "run"]
    errors = sum(g["errors"] for g in brain.stats(scope, agent, mode))
    scored = sum(g["scored"] for g in groups)
    weighted = sum((g["mean_score"] or 0) * g["scored"] for g in groups)
    by_rubric = [{"rubric_id": g["rubric"], "rubric": RUBRIC_NAMES.get(g["rubric"], g["rubric"] or "none"), "version": g["version"], "scored": g["scored"], "mean": g["mean_score"],
                  "pass_rate": g["pass_rate"], "aim_rate": g["aim_rate"], "target": g["target"], "aim": g["aim"], "last": g["last"] or None} for g in groups]
    losses = brain.losses(scope, agent, mode=mode, since=since)[:3]
    repeats = brain.repeated_failures(scope, agent, since=since)[:4]
    fresh = brain.freshness(scope, agent)
    tested = brain.store.rows("SELECT COUNT(*) n FROM memories WHERE status='active' AND verified=1 AND ((scope=? AND agent IN (?, '*')) OR scope='shared')", (scope, agent))[0]["n"]
    ideas = brain.ideas(scope, agent)
    exps = brain.experiments(scope, agent=agent)
    run_tokens = [d["payload"]["usage"].get("est_tokens_proxy") for d in brain.evaluations(scope, agent, mode=mode, kind="run", since=since, limit=500)
                  if isinstance(d.get("payload", {}).get("usage"), dict) and d["payload"]["usage"].get("est_tokens_proxy") not in (None, 0)]
    tok = _tokens_known(brain).get(agent, {})
    return {
        "scope": scope, "agent": agent, "mode": mode, "window_days": days,
        "final_items": sum(g["completed"] for g in groups), "scored_samples": scored, "mean_score": round(weighted / scored, 2) if scored else None,
        "pass_rate": (round(100.0 * sum(g["passed"] for g in groups) / sum(g["completed"] for g in groups), 1) if groups else None),
        "aim_rate_95": (round(100.0 * sum(round((g["aim_rate"] or 0) * g["scored"] / 100) for g in groups) / scored, 1) if scored else None),
        "by_rubric": by_rubric,
        "runs_logged": sum(g["completed"] for g in runs), "run_pass_rate": (round(100.0 * sum(g["passed"] for g in runs) / sum(g["completed"] for g in runs), 1) if runs else None),
        "errors_logged": errors,
        "weakest_criteria": [{"criterion": l["criterion"], "avg_lost_points": l["avg_lost"], "n": l["n"], "example": (l["evidence"] or [""])[0]} for l in losses],
        "repeated_failures": [{"pattern": r["pattern"], "count": r["count"], "last": r["last"]} for r in repeats],
        "memory": {k: fresh[k] for k in ("active", "verified", "expired", "superseded", "sources", "newest", "oldest_active", "retrieval_cost_chars_avg")},
        "tested_lessons": int(tested),
        "experiments": {"ideas_proposed": sum(1 for i in ideas if i["status"] == "proposed"), "running": sum(1 for e in exps if e["status"] == "running"),
                        "decided": sum(1 for e in exps if e["status"] == "decided"), "kept": sum(1 for e in exps if e.get("decision") == "keep")},
        "token_cost": {"est_tokens_proxy_avg": round(sum(run_tokens) / len(run_tokens)) if run_tokens else None, "runs_with_proxy": len(run_tokens),
                       "provider_tokens_known": tok.get("tokens_known"), "provider_cost_usd_known": tok.get("cost_usd_known"), "unknown_cost_calls": tok.get("unknown_cost_calls"),
                       "note": "proxy = loaded instruction bytes / 4 from the run log; the scheduled sessions do not expose real tokens"},
    }


def learning_section(brain: AgentBrain, days: int = 30) -> dict:
    """The `learning` block for public/report.json: production panels per (scope, agent), offline/test rows kept apart,
    open ideas and experiments, saved cases, contradictions and the honest unknowns."""
    agents = brain.store.rows("SELECT DISTINCT scope, agent FROM evaluations WHERE scope IN ('shop','studio','trading','crew') ORDER BY scope, agent")
    prod = [agent_panel(brain, r["scope"], r["agent"], "production", days) for r in agents]
    prod = [p for p in prod if p["scored_samples"] or p["runs_logged"] or p["errors_logged"]]
    offline = [agent_panel(brain, r["scope"], r["agent"], "offline", days) for r in agents]
    offline = [p for p in offline if p["scored_samples"] or p["runs_logged"] or p["errors_logged"]]
    cases = brain.eval_cases()
    contradictions = {s: brain.contradictions(s) for s in sorted(BUSINESS_SCOPES)}
    unknowns = ["real provider tokens and cost for scheduled sessions (only the loaded-bytes proxy exists)",
                "buyer outcomes for most scored items (results.jsonl outcomes fill at 7 days; the score is not a result)",
                "agent levels, revenue per agent, improvement percentages: not computed because no measured basis exists"]
    return {"generated_at": brain.now(), "window_days": days,
            "note": "counts from factory/engine/state/journal.jsonl (learning rows); production and offline rows are separate; rubric ids never mix; unknown stays unknown",
            "production": prod, "offline": offline,
            "ideas_open": [{"id": i["id"], "scope": i["scope"], "agent": i["agent"], "status": i["status"], "change": str(i["proposal"].get("change"))[:160],
                            "metric": str(i["proposal"].get("metric"))[:80], "created": i["created"]} for i in brain.ideas(status="proposed")[:10]],
            "experiments": [{"id": e["id"], "scope": e["scope"], "agent": e["agent"], "status": e["status"], "decision": e.get("decision"), "samples": e.get("samples", 0),
                             "metric": str(e.get("metric"))[:80], "conflicts": len(e.get("conflicts") or []), "updated": e.get("updated")} for e in brain.experiments()[:10]],
            "eval_cases": {"train": sum(1 for c in cases if c["split"] == "train"), "holdout": sum(1 for c in cases if c["split"] == "holdout")},
            "contradictions": {k: v[:5] for k, v in contradictions.items() if v},
            "worker": "no persistent worker: rows are written by the crews' own runs (nb.py show / runlog.py add / learn.py) and by the hourly GitHub engine worker's ingest step",
            "unknowns": unknowns}


def panel_text(p: dict) -> str:
    """One compact text block per agent for the CLI and the standup."""
    u = lambda v: "unknown" if v is None else v  # noqa: E731
    lines = [f"{p['scope']}/{p['agent']} ({p['mode']}, last {p['window_days']} days)",
             f"  items {p['final_items']} (scored {p['scored_samples']}, unscored {p['final_items'] - p['scored_samples']}) · mean {u(p['mean_score'])} · pass {u(p['pass_rate'])}% · 95+ {u(p['aim_rate_95'])}% · runs {p['runs_logged']} (ok {u(p['run_pass_rate'])}%) · errors {p['errors_logged']}"]
    for r in p["by_rubric"]:
        lines.append(f"  rubric {r['rubric'][:40]} v={r['version']}: n={r['scored']} mean {u(r['mean'])} pass {u(r['pass_rate'])}% aim {u(r['aim_rate'])}%")
    if p["weakest_criteria"]:
        lines.append("  weakest: " + ", ".join(f"{w['criterion']} -{w['avg_lost_points']} (n={w['n']})" for w in p["weakest_criteria"]))
    if p["repeated_failures"]:
        lines.append("  repeats: " + "; ".join(f"{r['pattern'][:50]} x{r['count']}" for r in p["repeated_failures"]))
    m = p["memory"]
    lines.append(f"  memory: {m['active']} active ({m['verified']} tested, {p['tested_lessons']} tested lessons incl. shared) · {m['expired']} expired · {m['superseded']} superseded · {m['sources']} sources · newest {u(m['newest'])} · avg retrieval {u(m['retrieval_cost_chars_avg'])} chars")
    e = p["experiments"]
    lines.append(f"  experiments: {e['ideas_proposed']} ideas open · {e['running']} running · {e['decided']} decided ({e['kept']} kept)")
    tc = p["token_cost"]
    lines.append(f"  tokens: proxy avg {u(tc['est_tokens_proxy_avg'])} over {tc['runs_with_proxy']} runs · provider tokens {u(tc['provider_tokens_known'])} · cost {u(tc['provider_cost_usd_known'])}")
    return "\n".join(lines)
