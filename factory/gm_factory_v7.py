#!/usr/bin/env python3
# ===========================================================================================
#  GM FACTORY V7.0 — "SIMPLE SHIP" — ONE FILE. DROP THIS INTO A BUILD SESSION AND SAY "BUILD IT".
#  Part A (BUILD_PROMPT, right below) = the full instructions.
#  Part B (the code)                  = the rules the page and the scheduled tasks must follow.
#  Run:  python3 gm_factory_v7.py              self-test + demo Marketing board
#        python3 gm_factory_v7.py --plan       print the cut / keep plan
# ===========================================================================================
from __future__ import annotations

BUILD_PROMPT = r"""
# GM FACTORY V7.0 — "SIMPLE SHIP" — Master Build Prompt

You are updating my artifact **GM Factory** (https://claude.ai/artifact/U91MrX9kzLUxLu9pnmgP5X).
The attached file `gm_factory_v7.py` holds the rules and data shapes. Read it first.
I work 100% from my phone. Goal of V7: **fewer businesses, clearer screens, everything I keep runs smooth.**
Business #2 (Ridgeline) is NOT part of V7. It gets its own session later.

## 0. HARD RULES
1. Backup first: save a dated copy of the page and send it to me before any edit.
2. Nothing that I keep may break (Etsy, Pinterest, the 4 shop socials, Gmula Shorts, Trading, Mechanic).
3. Pausing is not deleting: cut lanes are switched OFF and hidden, their data and files stay, one word brings them back.
4. Real numbers only. Unknown = "unknown", never 0, never a guess.
5. No new paid services, no new accounts, no ads.

## 1. CUT (switch off + hide)
- **Gumroad**: remove STEP 4c from the Bolt task (no more copying, publishing or sales checks on Gumroad). Hide Gumroad from every screen. Leave existing Gumroad products alone (do not delete or unpublish them).
- **Funnel Floor**: disable the "Funnel · daily Reel" scheduled task. Hide the Funnel floor/bay. Keep the @digitalcreationsbyridge account untouched for a future business.
- **Clutter**: hide Ridgeline, Frontier Nav and any other not-running lane from Today and the map. They stay reachable under More → "Parked".

## 2. KEEP (the whole ship after V7)
`KEEP` in the code: Etsy shop · Marketing (Pinterest + Instagram + Facebook + TikTok + shop YouTube + Gmula Shorts) · Trading · Mechanic.
Bottom tabs: **Today · Shop · Marketing · Trading · More**.

## 3. NEW: MARKETING TAB (see everything at a glance, no paragraphs)
One screen. One card per channel in `CHANNELS` (order as listed). Each card:
- channel icon + name + status light (🟢 posted today / 🟡 scheduled, nothing out yet / 🔴 failed or disconnected / ⚪ unknown) — use `channel_status()`.
- the **latest post as a picture** (pin image, Reel cover, Short thumbnail), its time, and its real numbers if we have them (views, saves, clicks); "stats not wired yet" in small grey text where we don't.
- "Next: <time>" for the next scheduled post.
- 7-day count of posts that actually went out.
Tap a card → a scrolling **gallery** of that channel's last 20 posts (picture, date, status, numbers, open-link). Tap a picture → full size.
Top of the tab: one line "This week: N posts out · N failed · best: <channel> (<views>)".
Data (read-only): `pins` (Pinterest), `social` (instagram/facebook/youtube/tiktok, platform field), `modules/youtube/pipeline` + `modules/youtube/episodes` (Gmula Shorts), `signal/main` (connections). Shapes in `ChannelPost` below.

## 4. TRADING: SMOOTHER
- GitHub's every-5-minutes schedule really fires about every 40 minutes. Fix: give the autopilot workflow its **own** concurrency group (`trading-autopilot`, not the shared `starship-gw`, so it never cancels a waiting gateway job), add `push` trigger on `factory/trading/kick/**`, and have the hourly Trading scans push `factory/trading/kick/<day>-<HHMM>.txt` each run so the bot is guaranteed to wake at least hourly on top of the schedule. The autopilot's save step must `git pull --rebase` and retry its push up to 3 times.
- Trading tab shows "Bot last checked: <time>" in red if older than 70 minutes during market hours (`autopilot_late()`).
- Money rules, the $20 floor, paper mode: unchanged.

## 5. TODAY SCREEN: 4 LIGHTS STAY
Listings · Pins · Posts · Trades. "Posts" now counts all channels in the Marketing tab. Nothing else added.

## 6. DONE MEANS
- Sweep (factory/qa/sweep.py) all "ok", no sideways scroll at 375px, screenshots of Today, Marketing and Trading checked.
- Bolt, Mechanic and the Trading scans updated to match; Funnel task disabled.
- Tell me in 3 lines what changed.
"""

# ------------------------------------------------------------------------------------------
# Part B — rules and data shapes
# ------------------------------------------------------------------------------------------
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import sys

KEEP = ["etsy", "marketing", "trading", "mechanic"]
CUT = {
    "gumroad": "Bolt STEP 4c removed; hidden. Existing Gumroad products left alone.",
    "funnel": "'Funnel · daily Reel' task disabled; floor hidden; @digitalcreationsbyridge kept for later.",
}
PARKED = ["ridgeline", "frontier_nav", "brain_arcade"]   # hidden from Today/map, reachable under More → Parked
TABS = ["Today", "Shop", "Marketing", "Trading", "More"]

CHANNELS = [  # (id, label, source collection, business)
    ("pinterest", "Pinterest", "pins", "etsy"),
    ("instagram", "Instagram", "social", "etsy"),
    ("facebook", "Facebook", "social", "etsy"),
    ("tiktok", "TikTok", "social", "etsy"),
    ("youtube_shop", "Shop YouTube", "social", "etsy"),
    ("gmula", "Gmula Shorts", "modules/youtube/pipeline", "youtube"),
]

@dataclass
class ChannelPost:
    channel: str
    status: str                      # "posted" | "queued" | "failed" | "ready" | "other"
    at: Optional[datetime] = None    # posted time, or due time when queued
    image: Optional[str] = None      # picture to show
    url: Optional[str] = None        # open-link
    title: str = ""
    views: Optional[int] = None      # None = not wired / unknown (never shown as 0)
    saves: Optional[int] = None
    clicks: Optional[int] = None

def normalize(doc: Dict, collection: str) -> Optional[ChannelPost]:
    """Turn a db document into a ChannelPost. Returns None if it doesn't belong to a channel."""
    def ts(v):
        if not v: return None
        try: return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError: return None
    if collection == "pins":
        auto = doc.get("auto") or {}
        st = doc.get("status", "other")
        st = st if st in ("posted", "queued", "ready") else ("failed" if auto.get("error") else "other")
        return ChannelPost("pinterest", st, ts(doc.get("postedAt") or auto.get("due")),
                           auto.get("imageUrl"), auto.get("postUrl") or doc.get("link"), doc.get("title", ""),
                           (doc.get("stats") or {}).get("impressions"), (doc.get("stats") or {}).get("saves"),
                           (doc.get("stats") or {}).get("clicks"))
    if collection == "social":
        plat = {"youtube": "youtube_shop"}.get(doc.get("platform"), doc.get("platform"))
        if plat not in {c[0] for c in CHANNELS}: return None
        m = doc.get("metrics") or {}
        avail = m.get("availability") == "available"
        st = {"posted": "posted", "approved": "queued", "queued": "queued", "failed": "failed",
              "qc_failed": "failed"}.get(doc.get("status"), "other")
        media = doc.get("media") or {}
        return ChannelPost(plat, st, ts(doc.get("postedAt") or doc.get("due")),
                           media.get("cover") or (media.get("images") or [None])[0],
                           doc.get("postUrl") or doc.get("link"), doc.get("productTitle", ""),
                           m.get("views") if avail else None, m.get("saves") if avail else None,
                           m.get("clicks") if avail else None)
    if collection == "modules/youtube/pipeline":
        launch = doc.get("launch") or {}
        vid = doc.get("videoId")
        st = "posted" if vid else ("failed" if (doc.get("qc") or {}).get("failed") else "other")
        stats = doc.get("stats") or {}
        return ChannelPost("gmula", st, ts(launch.get("publishAt")),
                           f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None,
                           f"https://youtube.com/shorts/{vid}" if vid else None,
                           doc.get("videoTitle", ""), stats.get("views"), None, None)
    return None

def channel_status(posts: List[ChannelPost], now: datetime, connected: Optional[bool] = True) -> str:
    """🟢 posted in the last 24h · 🟡 something scheduled, nothing out yet · 🔴 failed in 24h or disconnected · ⚪ unknown."""
    if connected is False: return "red"
    day_ago = now - timedelta(hours=24)
    recent = [p for p in posts if p.at and p.at >= day_ago]
    if any(p.status == "failed" for p in recent): return "red"
    if any(p.status == "posted" and p.at <= now for p in recent): return "green"
    if any(p.status in ("queued", "ready") for p in posts): return "yellow"
    return "grey" if not posts else "yellow"

def next_post(posts: List[ChannelPost], now: datetime) -> Optional[datetime]:
    due = sorted(p.at for p in posts if p.status == "queued" and p.at and p.at > now)
    return due[0] if due else None

def week_summary(by_channel: Dict[str, List[ChannelPost]], now: datetime) -> str:
    wk = now - timedelta(days=7)
    out = fail = 0; best = ("", -1)
    for ch, posts in by_channel.items():
        w = [p for p in posts if p.at and p.at >= wk]
        out += sum(p.status == "posted" for p in w)
        fail += sum(p.status == "failed" for p in w)
        v = sum(p.views or 0 for p in w if p.views is not None)
        if any(p.views is not None for p in w) and v > best[1]: best = (ch, v)
    label = dict((c[0], c[1]) for c in CHANNELS).get(best[0], "")
    tail = f" · best: {label} ({best[1]:,} views)" if best[1] >= 0 else ""
    return f"This week: {out} posts out · {fail} failed{tail}"

def autopilot_late(last_run_hhmm: Optional[str], now_ct: datetime) -> bool:
    """True when the trading bot hasn't checked in for 70+ min during market hours (8:30-15:00 CT, Mon-Fri)."""
    if now_ct.weekday() >= 5: return False
    open_, close = now_ct.replace(hour=8, minute=30), now_ct.replace(hour=15, minute=0)
    if not (open_ + timedelta(minutes=70) <= now_ct <= close): return False
    if not last_run_hhmm: return True
    h, m = map(int, last_run_hhmm.split(":"))
    return (now_ct - now_ct.replace(hour=h, minute=m)) > timedelta(minutes=70)

def kick_path(now_ct: datetime) -> str:
    return f"factory/trading/kick/{now_ct:%Y-%m-%d-%H%M}.txt"

# ------------------------------------------------------------------------------------------
def _selftest() -> None:
    now = datetime(2026, 10, 21, 18, 0, tzinfo=timezone.utc)
    pins = [normalize({"status": "posted", "postedAt": "2026-10-21T15:30:00Z", "auto": {"imageUrl": "a.jpg"}, "title": "Pin"}, "pins"),
            normalize({"status": "queued", "auto": {"due": "2026-10-21T19:30:00Z"}}, "pins")]
    ig = [normalize({"platform": "instagram", "status": "failed", "due": "2026-10-21T16:00:00Z"}, "social")]
    yt = [normalize({"videoId": "abc", "launch": {"publishAt": "2026-10-21T00:00:00Z"}, "stats": {"views": 812}}, "modules/youtube/pipeline")]
    assert channel_status(pins, now) == "green"
    assert channel_status(ig, now) == "red"
    assert channel_status([], now) == "grey"
    assert channel_status(pins, now, connected=False) == "red"
    assert next_post(pins, now) == datetime(2026, 10, 21, 19, 30, tzinfo=timezone.utc)
    assert normalize({"platform": "linkedin"}, "social") is None
    assert normalize({"platform": "instagram", "status": "posted", "metrics": {"availability": "unavailable", "views": 0}}, "social").views is None
    s = week_summary({"pinterest": pins, "instagram": ig, "gmula": yt}, now)
    assert "2 posts out" in s and "1 failed" in s and "Gmula Shorts (812 views)" in s, s
    ct = datetime(2026, 10, 21, 11, 0)
    assert autopilot_late("09:30", ct) and not autopilot_late("10:30", ct) and not autopilot_late("09:30", ct.replace(day=24))
    assert kick_path(ct) == "factory/trading/kick/2026-10-21-1100.txt"
    print("self-test ok ·", s)

if __name__ == "__main__":
    if "--plan" in sys.argv:
        print("KEEP:", ", ".join(KEEP)); print("CUT:"); [print(f"  - {k}: {v}") for k, v in CUT.items()]
        print("PARKED:", ", ".join(PARKED)); print("TABS:", " · ".join(TABS))
    else:
        _selftest()
