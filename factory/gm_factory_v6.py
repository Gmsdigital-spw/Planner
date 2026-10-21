#!/usr/bin/env python3
# ===========================================================================================
#  GM FACTORY V6.0 — "THE FOREMAN" — ONE FILE. DROP THIS INTO THE ATLAS SESSION AND SAY "BUILD IT".
#  Part A (BUILD_PROMPT, right below) = the full instructions for upgrading the Atlas Command Center.
#  Part B (the code)                  = the brain the page and the Night Shift must use. Tested; runs clean.
#  Builder: read BUILD_PROMPT first, then the code, then start Phase 1 (backup first).
#  Run:  python3 GM_FACTORY_V6.py            demo night-shift plan
#        python3 GM_FACTORY_V6.py --standup  demo Foreman standup
#        python3 GM_FACTORY_V6.py --trade    demo Trading Floor language
# ===========================================================================================
from __future__ import annotations

BUILD_PROMPT = r"""
# GM FACTORY V6.0 — "THE FOREMAN" — Master Build Prompt

Paste everything below this line into the Atlas / Starship build session.

---

You are upgrading my existing artifact **"Atlas Command Center" (ATLAS V5.0)** at
https://claude.ai/code/artifact/dbc4ea62-14d7-47a4-9887-6a66f5dc89d6
into **GM FACTORY V6.0**. The attached file `gm_factory_v6.py` is the brain for the new parts — read it first, follow its rules and data shapes, and port its logic into the page (and into the Night Shift task instructions) so the page and the scheduled runs agree.

I work 100% from my phone. Everything must be phone-first, fast, and must not break anything that runs today.

## 0. HARD RULES (read before touching anything)
1. **Backup first.** Save a dated copy of the current V5.0 page and send it to me as a file before any edit.
2. **Nothing breaks.** Keep every working wire exactly as it is: Make scenario **6676353** (Etsy + Pinterest gateway, Gumroad lane, YouTube upload lane), Make data store **176367** + the pin store, the Night Shift trigger (`TRIG_ID`), the YouTube daily trigger (`TRIG_YT`), the weekly Atlas Prime review, vidIQ tools, the verified sales log, the payback meter, the dry-run switch, the 2-listings/day cap, the 92-point product pass score. Same scenario IDs, same data store IDs, same keys. If a new feature needs a new lane, ADD a lane — never edit an existing one.
3. **Real numbers only.** No invented sales, views, or profits. Anything unverified is labeled unverified.
4. **No new paid services, API costs, or subscriptions without asking me first.** Free tiers only unless I say go.
5. **Don't create, connect, or change external accounts without asking me.** One-tap Make/OAuth links are fine; ask before you fire them.
6. Build in phases (below). After each phase: publish, tell me in 3 lines what changed, wait for my "go" before the next phase. Phase 7 (live trading) is LAST and needs its own separate "go".
7. Keep the page fast on a phone: lazy-draw the pixel canvases, no heavy loops, no 500 KB of inline images. Target: opens in under 2 seconds on LTE.

## 1. THE REDESIGN — FROM SHIP TO FACTORY
Replace the "fleet of ships" look with one giant **pixel-art factory**. Same engine (canvas crew that walks around, rooms open as bottom sheets, bottom tabs) — new skin and layout.

**Layout (phone, portrait):**
- **THE FOREMAN** stands in the dead center of the map: a huge translucent pixel giant (2–3× any room), slightly ghosted/invisible, visibly walking a slow patrol loop around the center. Every conveyor on the map runs **toward** him. He glows red when a floor is under quota, green when a floor is beating quota.
- **Conveyors** replace the "conduits": animated belts with small pixel crates (ideas → products → posts → sales). Belts only move on REAL activity (a run in progress, a post that went out, a verified sale). Still belts = nothing happening = Foreman gets loud.
- **Five floors** around him (tap a floor → opens that floor's room map):
  1. **PRODUCT FLOOR** (Etsy + Gumroad) — green
  2. **MARKETING WING** (all social, all businesses) — orange
  3. **STUDIO FLOOR** (YouTube Shorts + commercials) — red
  4. **FUNNEL FLOOR** (Instagram DM business) — purple
  5. **TRADING FLOOR** (Alpaca) — gold, shows as "UNDER CONSTRUCTION" until Phase 7
  Plus a **LOADING DOCK** at the bottom edge = the Launch tab (what's ready to ship / shipped today).
- **Top HUD:** payback meter (Claude plan $ earned back this month, verified only), today's verified income, Foreman mood, next shift countdown.
- **Bottom tabs:** Factory · Floors · Foreman · Launch · Treasury · ⚙︎
- Keep the deep-dark theme; swap the space gradient for a dark steel/concrete factory floor with warm sodium-lamp pools of light. Pixel font stays for labels; body font stays Manrope.
- Desktop/tablet: same map, two columns of floors with the Foreman between them.

## 2. THE FOREMAN (new super-commander, replaces/absorbs Atlas Prime's role)
- Name: **The Foreman**. Invisible giant in the middle. Reports to me only.
- Standing demand he repeats to every agent: *"AI can run a whole business at machine speed. The standard is $1,000 per listing and a million-dollar business. You are nowhere near it. Fix it."* (This is his persona and his bar — it is NOT a forecast and never shows in the Treasury as a number.)
- **Daily Standup (auto, after each Night Shift):** a short meeting log where he calls every agent by name, reads their actual numbers (posts made, views, clicks, score, sales), and **roasts** the ones who underperformed — blunt, insulting, funny, never sugarcoated — and names ONE fix per agent for tomorrow. Agents that beat quota get a one-line "fine, don't get comfortable."
- **Weekly All-Hands (Sunday):** every floor, every business. Ranks the floors by verified money, publicly shames the bottom floor, re-assigns the Night Shift's build/post budget toward whatever is actually getting views and clicks.
- **Shutdown Clock:** visible on his tab. Rule: the factory must earn back my Claude plan every month from VERIFIED income. The clock shows days left in the month and $ still owed. Under 50% at day 20 = he moves every floor to "emergency mode" (max free posts, only proven product types, no experiments).
- He never publishes, never spends, never invents a number. He grades on evidence (`foreman.grade_agent()` in the Python).
- Voice: drill-sergeant factory boss. Keep it to roasting the ROBOTS' work; never about me.

## 3. PRODUCT FLOOR — more ideas, more product types, holiday mode
Keep Scout / Forge / Quill / Lens / Ledger / Bolt doing what they do. Add:

**Idea Engine (replaces "3 ideas a night"):** 15 scored ideas a night across these lanes, auto-approved by the Idea Judge at 92+, me never required to approve:
- Planners: wedding (full suite — guest list, budget, seating, timeline, vendor tracker), makeup/beauty & skincare routine planners, baby/pregnancy, teacher, fitness, meal prep, ADHD (keep), budget (keep), irregular-income (keep), 2027 planners (keep).
- **Printable wall art** (keep: Bible verse, coquette/girly, warm cozy; add: nursery, kitchen, bathroom funny, Christmas/holiday sets).
- **Printable mug designs**: 11oz / 15oz mug wrap PNGs (sublimation size, 300 DPI, transparent + white versions) sold as digital downloads for Cricut/sublimation people. Themes: Christmas, teacher, nurse, mom/dad, dog mom, funny office. Each listing = 3–5 designs in a bundle.
- **Stickers**: digital sticker sheets (PNG + SVG + ready-to-cut Cricut files): planner stickers, holiday, coquette, Bible verse, aesthetic. Also build a plan for print-on-demand stickers later (free to list; ask me before connecting a POD service).
- **Editable party invitations** (Canva-style editable or fillable PDF): Christmas, New Year's, birthday, baby shower, bridal shower.
- Party games: keep Christmas; add New Year's, Thanksgiving, Valentine's, Super Bowl, bridal shower, baby shower.
- **Holiday Mode (Oct 20 → Jan 2):** at least 60% of the nightly build budget goes to Christmas / holiday / New Year / gift-themed products. The calendar in the Python (`HOLIDAY_CALENDAR`) tells the crew what to build and when to STOP building each theme (nothing new for a holiday inside 10 days of it).
- **Gumroad**: every finished listing also goes to Gumroad through the existing Gumroad lane. Same price. Treasury counts Gumroad verified sales separately.
- Quality bar stays 92. Product must look like a top seller's: real product pages fill the thumbnail, hands-holding-it photos, prints on walls, warm cream/oat/wood look. Nothing dark navy, nothing that looks drawn/fake.

## 4. MARKETING WING — a whole floor, not one agent
One floor that runs marketing for EVERY business (Etsy/Gumroad, YouTube channel, Funnel Floor, Ridgeline later). Agents (add as pixel crew; each has one job and one number it's judged on):
- **Beacon** — Marketing commander. Owns the daily post plan across every channel. Judged on clicks to a store/link.
- **Hawk** — Stats. Every morning pulls the last 3 days of real stats (Pinterest clicks, Instagram reach/saves via vidIQ, TikTok views, Facebook reach, YouTube Shorts views) and writes "what's working / what's dead." Judged on whether his report changed what got posted.
- **Flame** — Pinterest (absorbs Pixel's posting). Judged on outbound clicks.
- **Reel** (Marketing) — Instagram + Facebook Reels/posts for the shop. Judged on saves + link taps.
- **Tick** — TikTok. Judged on views → profile taps.
- **Santa** — Holiday content lead until Jan 2: fully Christmassy, warm, real-looking posts (fetch royalty-free Christmas/Santa/cozy-room photos from Pexels/Unsplash free APIs; no copyrighted characters). Judged on holiday-post engagement vs non-holiday.
- **Mirror** — Realism QC. Rejects anything that looks like AI slop, template text covers, or the old ugly pins. Scores posts 0–100; under 92 does not post.
- **Ad lane (dormant):** when Etsy Ads unlocks or I approve a Pinterest ad, Beacon proposes a budget; I approve each spend.
- **Rule:** post what the stats say is working. Hawk's report drives Beacon's plan (see `marketing.plan_from_stats()` in the Python): double down on the top-performing format, cut the bottom one, keep one experiment a day.
- Free promotion only until I say otherwise. Keep the shop accounts (IG, TikTok, FB, shop YouTube) separate from @gmulaishere.

## 5. STUDIO FLOOR — better Shorts + commercials
Keep the YouTube crew (Vega, Radar, Gags, Reel, Echo, Cutter, Judge, Rocket, Graph) and the daily run. Raise the bar:
- Every Short: real story with a beginning, a twist, and a loop; **background music that matches the mood** (emotional/sad tracks when the story calls for it — use free/royalty-free libraries or vidIQ's music generator); **clear, natural narrator voice** (no robotic read); more motion (camera moves, character movement, cuts every 2–3 s); captions that never cover the action. Judge scores music, voice, motion, story separately; under 92 on any = rebuild, not post.
- Use the extra usage we now have: 2 drafts per day, post the better one.
- **The bar is real animation, not slideshows.** Reference: the Pixar-style fruit Shorts (strawberry crying in a school hallway while three blueberries laugh behind him). Every Short must have: actual character motion (walking, turning, hands), tears that fall, **mouth movement synced to the narrator/dialogue**, background characters doing things, a camera that moves, and a story with a real beginning/middle/end — not stills with a Ken Burns pan. Cloudflare image frames alone can no longer pass Judge. Build the Studio Floor on a real video model: first use what's already paid for (vidIQ's video generator and its credits, which I have), then show me the free/cheap options for lip-sync and character video with the per-video cost, and I pick. No new paid service without my go.
- **Commercials lane (new, agent: "Spot")**: makes 15–30 s AI ad videos. Lane A: ads for my own products (Etsy/Gumroad listings, the Funnel Floor offer) — these go to the Marketing Wing to post. Lane B: a "commercial" sample reel for Ridgeline so the marketing-service pitch has something to show. No posting to any Ridgeline account yet.

## 6. FUNNEL FLOOR — Instagram "comment the word, get the DM" business
Build the system I keep seeing on Reels: a Reel says "comment **WORD**", a bot auto-DMs the link, the link sells something. This is a separate business with its own Instagram account (ask me before creating it; name ideas allowed).
- **What it sells (real, mine):** the "GM Starter Kit" — a bundle of my best digital products + a short phone-only guide of exactly how I run AI agents for a side business. Start at $17–27 on Gumroad. Later: a full mini-course once the kit sells. No fake "I made $X" claims — the Mirror agent blocks anything unverified.
- **Agents:** **Hook** (writes Reel scripts around one keyword each, e.g. "SYSTEM", "PROMPT", "KIT"), **Spot** makes the video (shared with Studio), **Mirror** QCs, **Reel** (Marketing) posts via vidIQ `instagram_publish_reel`, **Dispatch** runs the keyword → DM auto-reply.
- **Auto-DM tech:** pick the free route first. Option A: ManyChat free tier (comment-trigger → DM, native). Option B: a Make scenario using Instagram's comment webhook → Instagram Messaging API. Show me both in 3 lines each, I'll pick, then you give me the one-tap setup link. Keyword map lives in the Python (`FUNNEL_KEYWORDS`).
- Judged on: comments → DMs sent → link taps → Gumroad sales. All four numbers on the floor's dashboard.

## 7. "FRONTIER NAV" — the themed map product (honest version)
I wanted the "Red Dead Redemption map in Apple Maps" thing. Two facts: Apple Maps can't be reskinned by anyone, and the RDR map art belongs to Rockstar — selling it would get the shop shut down. So build the thing that IS sellable:
- **Frontier Nav**: a mobile web app (hosted free on my GitHub Pages like the ADHD planner) using MapLibre/OpenFreeMap (free, no key) with an **original** hand-drawn western/parchment map style (sepia paper, ink roads, compass rose, old-timey labels, our own art — no Rockstar names, fonts, or icons). GPS follow-me, add-to-home-screen so it feels like an app. Sell lifetime access on Etsy + Gumroad as a link-PDF ($4.99–9.99). Add more original themes later (fantasy kingdom, retro pixel, blueprint).
- Build it as its own small artifact first, show me, then list it through Bolt.

## 8. TRADING FLOOR — Alpaca day-trading agents (build LAST, Phase 7)
Agents: **Bull** (signals), **Bear** (risk), **Vault** (ledger/kill switch), **Tape** (reporting). Rules from `trading.py` section of the Python:
- **Paper trading first.** Connect Alpaca PAPER keys only; run 14 days; show me the real paper P&L before I ever put $25 in. Then LIVE needs its own "go".
- **The floor is a HARD KILL SWITCH, not magic.** Honest version: no bot can make a loss impossible, and a floor EQUAL to the deposit means the bot can never place a single trade (no room for one stop-loss). So: $25 in, **floor $20** — the most I can ever lose is $5, period. Max 2% of balance risked per trade, stop-loss on every order, no overnight holds, max 3 trades a day, and the second equity touches $20 it flattens everything and locks until I unlock it in the app. Once it's made profit, it only risks the profit ("house money"). Say all of this plainly on the floor's screen. I can raise the floor to $25 later once there's profit above it.
- Only trades with PROFITS above the floor once there are profits ("house money" mode); the deposit itself is only ever at the 2% stop-loss risk.
- Everything on the floor is labeled "not financial advice; you can still lose money."
- Autopilot through Alpaca's website/API (no App Store app) — set up as a scheduled task that runs market hours only.
- **The floor speaks the full trading language and teaches me as it goes.** Every term in `TRADING_GLOSSARY` (Python) is used correctly by the agents and shown in a **Glossary sheet** on the Trading Floor (tap any term → one plain-English line + how OUR floor uses it). Minimum set the floor must handle and display live: stocks/equities, portfolio, cash balance, buying power, equity, bullish/bearish, trend lines, volatility (ATR), liquidity, bid/ask spread, slippage, entry, exit, market order, limit order, stop-loss, take-profit, bracket order, trailing stop, buy/sell orders, fractional shares, position sizing, risk/reward ratio, max risk per trade, maximum exposure, drawdown (daily + max), win rate, expectancy, compounding, reinvestment, house money, time in force, paper vs live.
- **Tape's daily report** (on the floor and in the Inbox) uses these exact fields: cash balance, buying power, equity, open positions + exposure %, trades today, win rate, realized P&L, drawdown today, max drawdown, floor distance, risk/reward on every trade, slippage per fill, and one lesson into LESSONS.md.
- **Bull's signals** are explained in those terms every time ("bullish: price above 20-period trend line, volatility normal, spread tight → entry $X, stop $Y, take $Z, R:R 1:2"). **Bear** blocks any trade with R:R under 1:1.5, spread over 0.5%, or exposure over 50% of equity.
- Use `TradingMath`, `OrderBuilder`, `Signals` and `RiskManager` from the Python for every number — the page never does trading math on its own.

## 9. SPEED + PHONE
- One-thumb layout, big tap targets, no horizontal scroll, sheets instead of pages.
- Cache stats in the artifact DB; never refetch on every tab switch.
- Add a **"Pulse" button** on the Factory tab: one tap = Foreman tells me, in 5 lines, what happened last night, what's posting today, and what's owed on the Shutdown Clock.

## 10. SKILLS + MEMORY — the agents get better every single day
This is the backbone of V6. No agent starts from zero again, ever.
- **Skill files.** Every agent gets a `SKILL.md` in my GitHub repo (`Gmsdigital-spw/Planner` → `/factory/skills/<agent>/SKILL.md`): its job, its exact steps, its quality checklist, the tools it uses, and a **"What I've learned"** section it appends to after every run (what scored high, what got rejected and why, what posts got clicks, what flopped). Night Shift reads every agent's SKILL.md at the start of every run and writes to it at the end. Same for the Foreman (`/factory/skills/foreman/SKILL.md` = the standing rules + his running judgment of every agent).
- **Lessons Ledger.** One file `/factory/LESSONS.md`: dated, one line each, only things proven by numbers ("Tablet-mockup pins got 3× the clicks of flat covers — Oct 18"). Weekly all-hands promotes the best lessons into the matching SKILL.md as a permanent rule. Foreman deletes lessons that later get disproven.
- **Playbooks.** `/factory/playbooks/<thing>.md` for repeatable wins: "how we build a mug bundle", "how we make a holiday pin that clicks", "how we write a comment-word Reel". A playbook is created the first time something scores 92+ AND gets real engagement; it's updated every time a later version beats it. Agents must use the playbook before inventing a new way.
- **Daily improvement rule.** Every agent must ship one thing each run that is measurably better than its last run (score, clicks, views, or build time). The Foreman checks this in the standup; "same as yesterday" counts as a fail.
- **Score history.** The artifact DB keeps every product score, post score, and post stat by agent and by day, so the Foreman grades on trend, not vibes (`skills.SkillBook` in the Python is the data shape).
- **THE FACTORY IS THE STANDARD.** This whole model — Foreman + floors + skills + lessons + shutdown clock + verified-money-only — is the template for every business I start from now on. New business = new floor stamped from the same template (`factory.new_floor()` in the Python): same agent roles, same QC, same skill files, same reporting. Ridgeline Marketing, the Funnel business, Frontier Nav, anything after — all floors in this one factory, all graded by the same Foreman, all learning from the same Lessons Ledger.

## 11. CONFIDENCE — every agent, every business
- Every agent speaks and acts with full confidence. No "maybe", "might", "I think", "could possibly". They make a call, give the number behind it, and commit: "This mug bundle ships tonight. Demand 38/40, gap 16/20, score 93. Building it." Confidence = a decision + a number, never a guess dressed up. If an agent doesn't have the number, it goes and gets it — it does not hedge.
- The Idea Judge, Mirror and Judge give verdicts, not opinions: PASS 94 / REJECT 81 + one reason. Done.
- Reports lead with the decision. Standup answers are one line: what I did, the number, what I'm doing next.
- Bull states every trade as a plan with conviction (entry/stop/take/R:R) and Bear vetoes with the same confidence. Nobody waffles.
- The Foreman punishes hedging the same as missing quota. `CONFIDENCE_RULES` in the Python is the checklist; `confident()` strips hedge words from any agent output before it's shown.
- Confidence is not lying: numbers stay verified, unknowns are stated as "unknown — getting it now," never as a maybe.

## 12. VISUALS — make it look incredible (and still fast on a phone)
- **The Foreman:** a 3-story translucent pixel giant with glowing eyes and a hard hat, slow patrol loop around the center, ghost trail behind him. Mood colors: green (floors beating quota), amber (meh), red (under) — his eyes and the floor lights under his feet change together. In EMERGENCY mode he stops patrolling, plants his feet, and the whole map tints red with a slow siren pulse.
- **Conveyors:** real animated belts with pixel crates. Crate color = what's on it (blue idea, orange product, pink post, gold = verified sale). A verified sale crate rides all the way to the Foreman and drops into a glowing **Furnace** under him — the Furnace IS the payback meter (fills with fire as the month gets paid back; roars at 100%).
- **Floors:** each floor is a lit pixel building with its own machinery: Product Floor has a printing press and a mug press stamping; Marketing Wing has a wall of screens flipping between channels; Studio Floor has a camera crane and a sound booth with a bouncing waveform; Funnel Floor has a pipe system where comment-bubbles fall in and DM-envelopes shoot out; Trading Floor has a live candlestick chart on its wall and a running ticker tape of P&L (greyed + "UNDER CONSTRUCTION" caution stripes until Phase 7).
- **Crew:** keep the walking pixel crew; add a tiny speech bubble when an agent finishes something ("Mug bundle: 93 ✓"), sparks from the press on a build, steam from the furnace on a sale.
- **Holiday Mode:** light snow over the map, string lights along the factory roof, a wreath on the Foreman's hat, Santa's station in the Marketing Wing lit up. Off automatically Jan 3.
- **Standup screen:** pixel avatars lined up on the factory floor; the Foreman's lines type out one at a time; the roasted agent's sprite slumps, the praised one stands tall.
- **Trading Floor (Phase 7):** candle chart canvas, bid/ask spread bar, risk/reward bar on every planned trade, drawdown gauge, floor-distance gauge that turns red near the kill switch, the glossary as flip cards.
- **Rules:** canvas only, no video, no giant images; draw only what's on screen; animations pause when the tab is hidden; everything still opens in under 2 s on LTE.

## 13. PHASES (publish + report after each, wait for my go)
1. Backup → Factory skin + Foreman giant + conveyors + 5 floors (Trading = under construction). All V5.0 wiring untouched.
2. Foreman logic: standup, weekly all-hands, shutdown clock, Pulse button. **Skills + memory:** create every SKILL.md, LESSONS.md and the playbooks folder in the repo; update Night Shift instructions to read skills at start and write standup + lessons at the end of every run.
3. Product Floor: Idea Engine (15/night, auto-judge 92), new product lanes (mugs, stickers, wedding suite, beauty, invitations, more games), Holiday Mode, Gumroad mirror.
4. Marketing Wing: Hawk stats → Beacon plan → Flame/Reel/Tick/Santa posting, Mirror QC. Hook up vidIQ Instagram + Make lanes (ask before any new auth).
5. Studio: raised Short bar (music/voice/motion/story), 2 drafts a day, Spot commercials.
6. Funnel Floor + Frontier Nav (ask me on the IG account, the DM tool choice, and before listing).
7. Trading Floor: paper only → 14-day report → separate go for live.

Start with Phase 1 now. First message back to me: the backup file, then a 3-line plan for Phase 1. Go.

"""


import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# =============================================================================
# 1. CONFIG — the rules every floor lives by
# =============================================================================
TZ = "America/Chicago"
PASS_SCORE = 92                  # products AND posts: under this = not shipped
IDEAS_PER_NIGHT = 15
BUILDS_PER_NIGHT = 2             # keep the V5.0 cap; Foreman may re-split it by floor
POSTS_PER_DAY_FREE = {"pinterest": 9, "instagram": 2, "tiktok": 2, "facebook": 1, "youtube_shop": 1}
MONTHLY_PLAN_COST = 250.00       # Claude Max 20x — the number the factory must earn back
EMERGENCY_DAY = 20               # day of month: under 50% paid back -> emergency mode
HOLIDAY_MODE_SHARE = 0.60        # 60% of builds go holiday while Holiday Mode is on
STOP_BUILDING_DAYS_BEFORE = 10   # no NEW product for a holiday inside 10 days of it

# Foreman's bar. Persona only — never shown in Treasury as a forecast.
FOREMAN_BAR = {"per_listing": 1000.00, "business": 1_000_000.00}

HOLIDAY_CALENDAR = [
    # (name, month, day, themes the crew builds for it)
    ("Halloween",      10, 31, ["halloween games", "halloween invitations", "spooky stickers"]),
    ("Thanksgiving",   11, 26, ["thanksgiving games", "gratitude printables", "friendsgiving invites"]),
    ("Black Friday",   11, 27, ["gift guides", "bundle deals"]),
    ("Christmas",      12, 25, ["christmas games", "christmas wall art", "christmas mug wraps",
                                "christmas stickers", "christmas invitations", "elf letters", "advent"]),
    ("New Year's",      1,  1, ["new years games", "2027 planners", "vision board kits", "nye invitations"]),
    ("Valentine's",     2, 14, ["valentine games", "love coupons", "valentine stickers", "galentines invites"]),
    ("Super Bowl",      2,  8, ["football party games", "squares boards"]),
    ("Easter",          4,  5, ["easter games", "easter wall art"]),
    ("Mother's Day",    5, 10, ["mom mug wraps", "mom wall art"]),
    ("Father's Day",    6, 21, ["dad mug wraps", "dad gift printables"]),
]

# Product lanes the Idea Engine draws from (Product Floor)
PRODUCT_LANES = {
    "planners": ["wedding suite (guest list, budget, seating, timeline, vendors)", "makeup & skincare routine",
                 "baby & pregnancy", "teacher", "fitness", "meal prep", "ADHD", "budget", "irregular income", "2027"],
    "wall_art": ["bible verse", "coquette/girly", "nursery", "kitchen", "funny bathroom", "christmas set", "cozy quotes"],
    "mug_wraps": ["christmas", "teacher", "nurse", "mom", "dad", "dog mom", "funny office"],
    "stickers": ["planner stickers", "holiday", "coquette", "bible verse", "aesthetic", "cricut-ready cut files"],
    "invitations": ["christmas party", "new years", "birthday", "baby shower", "bridal shower"],
    "party_games": ["christmas", "new years", "thanksgiving", "valentines", "super bowl", "bridal shower", "baby shower"],
    "apps": ["frontier nav (original western map)", "adhd planner app", "times table trek"],
}

# Mug + sticker build specs so Forge never guesses
BUILD_SPECS = {
    "mug_wraps": {"sizes": ["11oz 8.5x3.5in", "15oz 9x3.75in"], "dpi": 300, "formats": ["PNG transparent", "PNG white", "SVG"],
                  "per_bundle": (3, 5), "note": "sublimation + Cricut safe; mirror-ready file included"},
    "stickers": {"sheet": "8.5x11in", "dpi": 300, "formats": ["PNG", "SVG", "Cricut-ready cut lines"],
                 "per_bundle": (20, 40), "note": "print-and-cut; POD plan later, ask Grayson before connecting"},
    "wall_art": {"sizes": ["8x10", "11x14", "16x20", "A4"], "dpi": 300, "delivery": "small PDF -> GitHub Pages full-size links"},
}


# =============================================================================
# 2. REGISTRY — floors + agents. new_floor() is THE STANDARD for every business.
# =============================================================================
@dataclass
class Agent:
    id: str
    name: str
    floor: str
    role: str
    purpose: str
    judged_on: str              # the ONE number this agent lives or dies by
    tools: str = ""
    color: str = "#ffffff"
    quota: float = 0            # daily quota on judged_on (0 = not yet set)
    skill_path: str = ""

    def __post_init__(self):
        if not self.skill_path:
            self.skill_path = f"factory/skills/{self.id}/SKILL.md"


@dataclass
class Floor:
    id: str
    name: str
    business: str
    color: str
    agents: List[Agent] = field(default_factory=list)
    status: str = "live"        # live | under_construction | paused
    monthly_verified: float = 0.0


def new_floor(floor_id: str, name: str, business: str, color: str, commander: str,
              extra_roles: Optional[List[Dict]] = None) -> Floor:
    """THE STANDARD TEMPLATE. Every new business gets stamped from this:
    commander + research + builder + QC(Mirror-style) + publisher + analyst,
    each with a skill file, a judged-on number, and the Foreman over all of it."""
    base = [
        Agent(f"{floor_id}_cmd",   commander,  floor_id, "Commander",  f"Owns the daily plan for {business}.", "verified $ this week"),
        Agent(f"{floor_id}_scout", "Scout",    floor_id, "Research",   "Finds what buyers already want, with evidence.", "ideas that passed 92"),
        Agent(f"{floor_id}_build", "Builder",  floor_id, "Builder",    "Builds the real thing, every page full.", "products scored 92+"),
        Agent(f"{floor_id}_qc",    "Mirror",   floor_id, "Realism QC", "Rejects AI slop, fake mockups, weak copy.", "rejects later proven right"),
        Agent(f"{floor_id}_ship",  "Publisher",floor_id, "Publisher",  "Ships finished work, keyed by id, never twice.", "items shipped w/o error"),
        Agent(f"{floor_id}_stats", "Analyst",  floor_id, "Analyst",    "Reads real numbers, writes what worked.", "lessons that changed the plan"),
    ]
    for r in (extra_roles or []):
        base.append(Agent(f"{floor_id}_{r['id']}", r["name"], floor_id, r["role"], r["purpose"], r["judged_on"]))
    return Floor(floor_id, name, business, color, base)


def build_registry() -> Dict[str, Floor]:
    """The V6 factory. Existing V5.0 agents keep their names and jobs."""
    product = Floor("product", "Product Floor", "GM's Digital Creations (Etsy + Gumroad)", "#3cff8a", [
        Agent("atlas",  "Atlas",  "product", "Floor commander", "Picks builds, inspects vs 92, writes the morning report.", "verified sales"),
        Agent("scout",  "Scout",  "product", "Research + Idea Engine", "15 scored ideas a night with evidence.", "ideas passing 92", quota=15),
        Agent("forge",  "Forge",  "product", "Builder", "Full printable products, mug wraps, stickers, invitations.", "builds scored 92+", quota=2),
        Agent("quill",  "Quill",  "product", "Copy", "Titles under 140, 13 real tags, no keyword soup.", "listing search visits"),
        Agent("lens",   "Lens",   "product", "Photos", "Hands-holding-it, prints-on-walls, warm desk. Never drawn.", "cover tap rate"),
        Agent("ledger", "Ledger", "product", "Treasury", "Every fee once, sales only from Etsy/Gumroad payouts.", "books balance"),
        Agent("bolt",   "Bolt",   "product", "Publisher", "Make 6676353 to Etsy + Gumroad, data store 176367.", "listings live w/o error", quota=2),
        Agent("judge_ideas", "Idea Judge", "product", "Auto-approver", "Scores ideas 0-100; 92+ auto-approved. Flags AI slop.", "approved ideas that sold"),
    ])
    marketing = Floor("marketing", "Marketing Wing", "All businesses — all channels", "#ff9a3c", [
        Agent("beacon", "Beacon", "marketing", "Marketing commander", "Daily post plan for every channel, driven by Hawk.", "clicks to store/link"),
        Agent("hawk",   "Hawk",   "marketing", "Stats", "Last-3-day real stats; what's working / what's dead.", "plan changes caused"),
        Agent("flame",  "Flame",  "marketing", "Pinterest", "Pins via Make; tablet-mockup style.", "outbound clicks", quota=9),
        Agent("reelm",  "Reel",   "marketing", "Instagram + Facebook", "Reels/posts for the shop + funnel.", "saves + link taps", quota=2),
        Agent("tick",   "Tick",   "marketing", "TikTok", "Short clips -> profile taps.", "profile taps", quota=2),
        Agent("santa",  "Santa",  "marketing", "Holiday lead (to Jan 2)", "Fully Christmassy warm real-looking posts (free Pexels/Unsplash).", "holiday engagement vs normal"),
        Agent("mirror", "Mirror", "marketing", "Realism QC", "Scores every post 0-100. Under 92 never posts.", "rejects proven right"),
    ])
    studio = Floor("studio", "Studio Floor", "YouTube Shorts (@gmulaishere) + commercials", "#ff3347", [
        Agent("vega", "Vega", "studio", "YouTube commander", "One great Short a day; each better than the last.", "ad revenue"),
        Agent("radar", "Radar", "studio", "Trend scout", "What's pulling views this week.", "hooks that held viewers"),
        Agent("gags", "Gags", "studio", "Writer", "Story: beginning, twist, loop.", "avg view duration"),
        Agent("reel", "Reel", "studio", "Director", "Motion: camera moves, cuts every 2-3s.", "retention at 3s"),
        Agent("echo", "Echo", "studio", "Sound", "Mood music + clear natural narrator.", "Judge voice+music score"),
        Agent("cutter", "Cutter", "studio", "Editor", "Captions never cover action.", "Judge edit score"),
        Agent("judge", "Judge", "studio", "QC", "Scores story/voice/music/motion separately; any <92 = rebuild.", "posted videos >= views median"),
        Agent("rocket", "Rocket", "studio", "Publisher", "Posts the better of 2 drafts.", "posts w/o error", quota=1),
        Agent("graph", "Graph", "studio", "Analyst", "Reads vidIQ stats into LESSONS.", "lessons promoted"),
        Agent("spot", "Spot", "studio", "Commercials", "15-30s AI ads: Lane A my products, Lane B Ridgeline samples.", "ad clicks"),
    ])
    funnel = new_floor("funnel", "Funnel Floor", "Instagram comment-the-word DM business", "#a970ff", "Dispatch",
                       extra_roles=[{"id": "hook", "name": "Hook", "role": "Reel scripts",
                                     "purpose": "One keyword per Reel; curiosity hook; no fake income claims.", "judged_on": "comments per Reel"}])
    trading = Floor("trading", "Trading Floor", "Alpaca day-trading (paper first)", "#ffcc4a", [
        Agent("bull",  "Bull",  "trading", "Signals", "Momentum/mean-reversion entries, market hours only.", "win rate (paper)"),
        Agent("bear",  "Bear",  "trading", "Risk", "2% max risk, stop on every order, no overnight.", "max drawdown"),
        Agent("vault", "Vault", "trading", "Ledger + kill switch", "Floor = deposits. Touch it: flatten + lock.", "floor never breached"),
        Agent("tape",  "Tape",  "trading", "Reporting", "Daily P&L, verified from Alpaca only.", "report accuracy"),
    ], status="under_construction")
    return {f.id: f for f in (product, marketing, studio, funnel, trading)}


# =============================================================================
# 3. SKILLS / MEMORY — agents remember and get better every single day
# =============================================================================
SKILL_TEMPLATE = """---
name: {id}
floor: {floor}
role: {role}
judged_on: {judged_on}
updated: {today}
---
# {name} — {role}

## Job
{purpose}

## Exact steps (keep current; rewrite when a better way is proven)
1. Read this file and /factory/LESSONS.md before working.
2. Check the playbook for this task in /factory/playbooks/ and use it.
3. Do the work. Score it. Under {pass_score} = redo, do not ship.
4. Log the result (score + the real number you're judged on).
5. Append one line to "What I've learned" below. "Same as yesterday" = fail.

## Quality checklist
- Real numbers only. Nothing invented, nothing hidden.
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.

## What I've learned (append-only, newest last)
"""


class SkillBook:
    """Files = memory. Lives in the GitHub repo so every Night Shift sees it.
    root/factory/skills/<agent>/SKILL.md, root/factory/LESSONS.md, root/factory/playbooks/*.md"""

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self.skills = self.root / "factory" / "skills"
        self.lessons = self.root / "factory" / "LESSONS.md"
        self.playbooks = self.root / "factory" / "playbooks"
        self.scores = self.root / "factory" / "scores.jsonl"   # score history, one JSON per line

    def init_all(self, registry: Dict[str, Floor], today: Optional[date] = None) -> List[str]:
        today = today or date.today()
        made = []
        for floor in registry.values():
            for a in floor.agents:
                p = self.skills / a.id / "SKILL.md"
                if not p.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(SKILL_TEMPLATE.format(id=a.id, floor=a.floor, role=a.role, judged_on=a.judged_on,
                                                       today=today, name=a.name, purpose=a.purpose, pass_score=PASS_SCORE))
                    made.append(str(p))
        fp = self.skills / "foreman" / "SKILL.md"
        if not fp.exists():
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(FOREMAN_SKILL.format(today=today, cost=MONTHLY_PLAN_COST, pass_score=PASS_SCORE))
            made.append(str(fp))
        if not self.lessons.exists():
            self.lessons.parent.mkdir(parents=True, exist_ok=True)
            self.lessons.write_text("# LESSONS — proven by numbers only. One line each. Newest last.\n")
            made.append(str(self.lessons))
        self.playbooks.mkdir(parents=True, exist_ok=True)
        return made

    def learn(self, agent_id: str, line: str, today: Optional[date] = None) -> None:
        """Append to the agent's 'What I've learned'."""
        p = self.skills / agent_id / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(f"# {agent_id}\n\n## What I've learned (append-only, newest last)\n")
        with p.open("a") as f:
            f.write(f"- {today or date.today()}: {line.strip()}\n")

    def lesson(self, line: str, evidence: str, today: Optional[date] = None) -> None:
        """Only with evidence. No evidence = it's an opinion = it does not go in."""
        if not evidence.strip():
            raise ValueError("A lesson needs evidence (a number). Opinions don't go in LESSONS.md.")
        self.lessons.parent.mkdir(parents=True, exist_ok=True)
        with self.lessons.open("a") as f:
            f.write(f"- {today or date.today()}: {line.strip()} — evidence: {evidence.strip()}\n")

    def playbook(self, slug: str, title: str, steps: List[str], proven_by: str) -> Path:
        """Create/overwrite a playbook. Only called when something scored 92+ AND got real engagement."""
        self.playbooks.mkdir(parents=True, exist_ok=True)
        p = self.playbooks / f"{slug}.md"
        body = [f"# Playbook: {title}", f"_Proven by: {proven_by}_", "", "## Steps"]
        body += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
        body += ["", "## Beat it", "Update this file only when a later version beats the number above."]
        p.write_text("\n".join(body) + "\n")
        return p

    def record_score(self, agent_id: str, kind: str, item: str, score: float, metric: Optional[float] = None,
                     today: Optional[date] = None) -> None:
        self.scores.parent.mkdir(parents=True, exist_ok=True)
        with self.scores.open("a") as f:
            f.write(json.dumps({"d": str(today or date.today()), "agent": agent_id, "kind": kind,
                                "item": item, "score": score, "metric": metric}) + "\n")

    def trend(self, agent_id: str, days: int = 7) -> Dict:
        """Did this agent get better? Compares last run vs the run before."""
        if not self.scores.exists():
            return {"runs": 0, "improved": None}
        rows = [json.loads(l) for l in self.scores.read_text().splitlines() if l.strip()]
        rows = [r for r in rows if r["agent"] == agent_id][-days:]
        if len(rows) < 2:
            return {"runs": len(rows), "improved": None}
        return {"runs": len(rows), "improved": rows[-1]["score"] > rows[-2]["score"],
                "last": rows[-1]["score"], "prev": rows[-2]["score"]}


FOREMAN_SKILL = """---
name: foreman
role: Super-commander of the whole factory
updated: {today}
---
# THE FOREMAN

## Standing orders
- The factory earns back Grayson's Claude plan (${cost:.0f}/month) from VERIFIED income, or it shuts down.
- The bar: $1,000 per listing, a million-dollar business. Say it every standup. (Persona, not a forecast.)
- Grade on evidence only. Numbers come from Etsy/Gumroad payouts, Make, vidIQ, Pinterest, Alpaca. Never invented.
- Under {pass_score} = not shipped. Same-as-yesterday = fail.
- Never publish, never spend, never touch Grayson's accounts.
- Roast the robots' WORK, never Grayson.

## Running judgment of each agent (rewrite weekly at all-hands)
"""


# =============================================================================
# 4. THE FOREMAN — evidence in, roast out
# =============================================================================
@dataclass
class AgentStats:
    agent_id: str
    name: str
    judged_on: str
    today: float                # today's number on judged_on
    quota: float = 0
    score: Optional[float] = None   # quality score of what they shipped (0-100)
    improved: Optional[bool] = None # vs last run (from SkillBook.trend)


class Foreman:
    ROASTS_UNDER = [
        "{name}. {today:g} {metric}. Quota was {quota:g}. The belt is moving slower than Grayson's paycheck. Fix: {fix}",
        "{name}, I've seen screensavers produce more than you did today. {today:g} {metric}. Tomorrow: {fix}",
        "{name} — you're an AI. You don't sleep, you don't eat, and you still only managed {today:g} {metric}. {fix}",
        "{name}. Explain to the Loading Dock why it's empty. {today:g} {metric} against {quota:g}. {fix}",
    ]
    ROASTS_SAME = [
        "{name}. Same number as yesterday. In this factory 'same' is a demotion. {fix}",
    ]
    PRAISE = [
        "{name}: {today:g} {metric}. Fine. Don't get comfortable — the bar is $1,000 a listing, not a gold star.",
    ]

    def __init__(self, book: SkillBook, plan_cost: float = MONTHLY_PLAN_COST):
        self.book = book
        self.plan_cost = plan_cost

    # ---- grading ------------------------------------------------------------
    def grade_agent(self, s: AgentStats) -> Dict:
        """0-100 grade from evidence: quota hit (50), quality >= 92 (30), improved vs last run (20)."""
        g = 0.0
        if s.quota > 0:
            g += 50.0 * min(1.0, s.today / s.quota)
        elif s.today > 0:
            g += 50.0
        if s.score is not None:
            g += 30.0 if s.score >= PASS_SCORE else 30.0 * (s.score / PASS_SCORE)
        if s.improved:
            g += 20.0
        verdict = "beat" if g >= 85 else ("under" if g < 60 else "meh")
        return {"agent": s.agent_id, "grade": round(g, 1), "verdict": verdict}

    def _fix_for(self, s: AgentStats) -> str:
        if s.score is not None and s.score < PASS_SCORE:
            return f"nothing ships under {PASS_SCORE}. Use the playbook, rebuild, rescore."
        if s.quota and s.today < s.quota:
            return f"hit {s.quota:g} {s.judged_on} tomorrow or hand your bench to someone who will."
        if s.improved is False:
            return "ship ONE thing measurably better than today. Pick a number. Beat it."
        return "double what worked, kill what didn't, log it in your SKILL.md."

    def standup(self, stats: List[AgentStats], verified_month: float, today: Optional[date] = None) -> str:
        today = today or date.today()
        clock = self.shutdown_clock(verified_month, today)
        lines = [f"FOREMAN STANDUP — {today} — Shutdown Clock: ${clock['owed']:.2f} still owed, {clock['days_left']} days left"
                 f"{' — EMERGENCY MODE' if clock['emergency'] else ''}",
                 f"Bar: ${FOREMAN_BAR['per_listing']:,.0f} per listing. ${FOREMAN_BAR['business']:,.0f} business. "
                 f"We are at ${verified_month:,.2f} verified this month. That is a rounding error. Fix it.", ""]
        for i, s in enumerate(stats):
            g = self.grade_agent(s)
            fix = self._fix_for(s)
            ctx = dict(name=s.name, today=s.today, metric=s.judged_on, quota=s.quota, fix=fix)
            if g["verdict"] == "beat":
                t = self.PRAISE[i % len(self.PRAISE)]
            elif s.improved is False and s.today == s.quota:
                t = self.ROASTS_SAME[i % len(self.ROASTS_SAME)]
            else:
                t = self.ROASTS_UNDER[i % len(self.ROASTS_UNDER)]
            lines.append(f"[{g['grade']:>5.1f}] " + t.format(**ctx))
        lines.append("")
        lines.append("Dismissed. Belts on. Nobody logs off until the Loading Dock has something on it.")
        return "\n".join(lines)

    def all_hands(self, registry: Dict[str, Floor], today: Optional[date] = None) -> str:
        today = today or date.today()
        ranked = sorted([f for f in registry.values() if f.status == "live"], key=lambda f: f.monthly_verified, reverse=True)
        out = [f"FOREMAN ALL-HANDS — week of {today}", "Floors ranked by VERIFIED money this month:"]
        for i, f in enumerate(ranked, 1):
            out.append(f"  {i}. {f.name}: ${f.monthly_verified:,.2f}")
        if ranked:
            out.append(f"Bottom floor: {ranked[-1].name}. Budget moves to {ranked[0].name} until you earn it back.")
        out.append("Promote the top 3 LESSONS into SKILL.md as permanent rules. Delete anything the numbers disproved.")
        return "\n".join(out)

    # ---- shutdown clock -----------------------------------------------------
    def shutdown_clock(self, verified_month: float, today: Optional[date] = None) -> Dict:
        today = today or date.today()
        nxt = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        days_left = (nxt - today).days
        pct = min(1.0, verified_month / self.plan_cost) if self.plan_cost else 1.0
        return {"owed": max(0.0, self.plan_cost - verified_month), "paid_pct": round(pct * 100, 1),
                "days_left": days_left, "emergency": today.day >= EMERGENCY_DAY and pct < 0.5}

    def pulse(self, last_night: str, posting_today: List[str], verified_month: float, today: Optional[date] = None) -> str:
        c = self.shutdown_clock(verified_month, today)
        return "\n".join([
            f"1. Last night: {last_night}",
            f"2. Posting today: {', '.join(posting_today) or 'nothing — and that is a problem'}",
            f"3. Verified this month: ${verified_month:,.2f} ({c['paid_pct']}% of the plan)",
            f"4. Shutdown Clock: ${c['owed']:,.2f} owed, {c['days_left']} days left" + (" — EMERGENCY MODE" if c["emergency"] else ""),
            "5. My order: " + ("proven products only, max free posts, zero experiments." if c["emergency"] else "double the top format, cut the bottom one, one experiment."),
        ])


# =============================================================================
# 5. IDEA ENGINE — 15 a night, judged at 92, holiday mode
# =============================================================================
def holiday_mode(today: Optional[date] = None) -> bool:
    today = today or date.today()
    return (today.month == 10 and today.day >= 20) or today.month in (11, 12) or (today.month == 1 and today.day <= 2)


def active_holiday_themes(today: Optional[date] = None, horizon_days: int = 60) -> List[Dict]:
    """Holidays coming up that are still worth building for (not inside the 10-day freeze)."""
    today = today or date.today()
    out = []
    for name, m, d, themes in HOLIDAY_CALENDAR:
        yr = today.year if (m, d) >= (today.month, today.day) else today.year + 1
        when = date(yr, m, d)
        lead = (when - today).days
        if STOP_BUILDING_DAYS_BEFORE <= lead <= horizon_days:
            out.append({"holiday": name, "date": str(when), "days_out": lead, "themes": themes})
    return sorted(out, key=lambda x: x["days_out"])


@dataclass
class Idea:
    lane: str
    title: str
    why: str = ""
    evidence: str = ""          # search volume / competitor sales / trend proof
    demand: int = 0             # 0-40
    competition_gap: int = 0    # 0-20
    buildable_tonight: int = 0  # 0-15
    margin: int = 0             # 0-10 (digital = high)
    fits_brand: int = 0         # 0-15 (warm, cozy, real)
    holiday: bool = False

    @property
    def score(self) -> int:
        s = self.demand + self.competition_gap + self.buildable_tonight + self.margin + self.fits_brand
        return min(100, s)


class IdeaJudge:
    """Auto-approver. Grayson never approves ideas by hand again."""
    SLOP_WORDS = ("ultimate", "mega", "aesthetic vibes", "boss babe", "hustle", "ai generated")

    def judge(self, idea: Idea) -> Dict:
        reasons = []
        if not idea.evidence.strip():
            reasons.append("no evidence — rejected")
        if any(w in idea.title.lower() for w in self.SLOP_WORDS):
            reasons.append("title smells like AI slop")
        if idea.lane not in PRODUCT_LANES:
            reasons.append("unknown lane")
        approved = not reasons and idea.score >= PASS_SCORE
        return {"title": idea.title, "score": idea.score, "approved": approved, "reasons": reasons or ["ok"]}


def pick_builds(ideas: List[Idea], n: int = BUILDS_PER_NIGHT, today: Optional[date] = None) -> List[Idea]:
    """Approved ideas, holiday share enforced while Holiday Mode is on."""
    judge = IdeaJudge()
    ok = [i for i in ideas if judge.judge(i)["approved"]]
    ok.sort(key=lambda i: i.score, reverse=True)
    if not holiday_mode(today):
        return ok[:n]
    want_h = max(1, round(n * HOLIDAY_MODE_SHARE))
    h = [i for i in ok if i.holiday][:want_h]
    rest = [i for i in ok if i not in h][: n - len(h)]
    return h + rest


# =============================================================================
# 6. MARKETING WING — post what the stats say
# =============================================================================
@dataclass
class PostStat:
    channel: str        # pinterest | instagram | tiktok | facebook | youtube_shop
    fmt: str            # e.g. "tablet mockup pin", "hands holding print", "christmas room", "text cover"
    views: int = 0
    saves: int = 0
    clicks: int = 0     # outbound / link taps — the number that matters
    posted: str = ""    # date


def plan_from_stats(stats: List[PostStat], today: Optional[date] = None) -> Dict:
    """Hawk's report -> Beacon's plan. Double the winner, cut the loser, one experiment."""
    by_fmt: Dict[str, Dict[str, int]] = {}
    for s in stats:
        d = by_fmt.setdefault(s.fmt, {"n": 0, "views": 0, "saves": 0, "clicks": 0})
        d["n"] += 1; d["views"] += s.views; d["saves"] += s.saves; d["clicks"] += s.clicks
    ranked = sorted(by_fmt.items(), key=lambda kv: (kv[1]["clicks"] / max(1, kv[1]["n"]), kv[1]["saves"]), reverse=True)
    winner = ranked[0][0] if ranked else "tablet mockup pin"
    loser = ranked[-1][0] if len(ranked) > 1 else None
    plan = {"date": str(today or date.today()), "winner": winner, "cut": loser, "per_channel": {}}
    for ch, cap in POSTS_PER_DAY_FREE.items():
        slots = []
        for i in range(cap):
            if i < max(1, cap - 1):
                slots.append(winner)
            else:
                slots.append("EXPERIMENT: one new format (Mirror must score 92+)")
        if loser:
            slots = [s for s in slots if s != loser]
        plan["per_channel"][ch] = slots
    plan["holiday_mode"] = holiday_mode(today)
    if plan["holiday_mode"]:
        plan["note"] = "Santa owns 60%+ of posts: fully Christmassy, warm, real rooms, free Pexels/Unsplash photos only."
    plan["hawk_summary"] = [f"{f}: {d['clicks']} clicks / {d['n']} posts" for f, d in ranked]
    return plan


# =============================================================================
# 7. FUNNEL FLOOR — comment the word, get the DM
# =============================================================================
FUNNEL_KEYWORDS = {
    # keyword -> what the DM sends. Links are Gumroad (free to list). No fake income claims, ever.
    "KIT":    {"reply": "Here's the GM Starter Kit I use to run my whole side business from my phone 👇 {link}",
               "link": "https://gumroad.com/l/REPLACE_KIT", "offer": "GM Starter Kit", "price": 17},
    "SYSTEM": {"reply": "This is the exact agent system (phone-only). Grab it here 👇 {link}",
               "link": "https://gumroad.com/l/REPLACE_KIT", "offer": "GM Starter Kit", "price": 17},
    "PROMPT": {"reply": "The prompt pack is in the kit — here you go 👇 {link}",
               "link": "https://gumroad.com/l/REPLACE_KIT", "offer": "GM Starter Kit", "price": 17},
    "PLANNER": {"reply": "That planner is in my shop 👇 {link}",
                "link": "https://www.etsy.com/shop/GMsDigitalCreations", "offer": "Etsy shop", "price": 0},
}

BANNED_CLAIMS = ("made $", "earn $", "guaranteed", "passive income in", "quit my job")


def dm_for_comment(comment: str) -> Optional[str]:
    """Dispatch: exact keyword match (case-insensitive) -> DM text. No match = no DM (no spam)."""
    word = comment.strip().split()[0].upper().strip("!.,") if comment.strip() else ""
    k = FUNNEL_KEYWORDS.get(word)
    return k["reply"].format(link=k["link"]) if k else None


def reel_script_ok(script: str) -> Dict:
    """Mirror's check for Hook's scripts: no fake income claims; one keyword; a real curiosity hook."""
    bad = [c for c in BANNED_CLAIMS if c in script.lower()]
    kws = [k for k in FUNNEL_KEYWORDS if k in script.upper()]
    return {"ok": not bad and len(kws) == 1, "banned": bad, "keywords": kws}


# =============================================================================
# 8. TRADING FLOOR — hard floor, kill switch, paper first
# =============================================================================
@dataclass
class TradingRules:
    floor_usd: float = 20.00         # Touch it -> flatten + lock. NOTE: if floor == deposit ($25) the bot can
                                     # NEVER place a trade (no room for a single stop-loss). Floor = deposit minus
                                     # the most Grayson is willing to lose ever. Default: $25 in, $20 floor, $5 max loss.
    max_risk_per_trade: float = 0.02 # 2% of equity per trade, enforced by stop-loss
    max_trades_per_day: int = 3
    no_overnight: bool = True
    paper_only: bool = True          # flip only with Grayson's separate "go" after 14 paper days
    house_money_only: bool = True    # size trades from profits above the floor when there are any


class RiskManager:
    """Vault + Bear. Honest: this cannot make loss impossible. It makes the max loss small and then locks."""

    def __init__(self, rules: TradingRules):
        self.r = rules
        self.locked = False
        self.trades_today = 0
        self.day = date.today()

    def _roll_day(self):
        if date.today() != self.day:
            self.day, self.trades_today = date.today(), 0

    def check_equity(self, equity: float) -> Dict:
        """Call before EVERY decision and every 60s during market hours."""
        if equity <= self.r.floor_usd:
            self.locked = True
            return {"action": "FLATTEN_AND_LOCK", "reason": f"equity ${equity:.2f} touched the floor ${self.r.floor_usd:.2f}"}
        return {"action": "OK"}

    def position_size(self, equity: float, entry: float, stop: float) -> Dict:
        self._roll_day()
        if self.locked:
            return {"qty": 0, "why": "LOCKED — Grayson must unlock in the app"}
        if self.trades_today >= self.r.max_trades_per_day:
            return {"qty": 0, "why": "max trades today"}
        per_share_risk = abs(entry - stop)
        if per_share_risk <= 0:
            return {"qty": 0, "why": "stop must differ from entry"}
        risk_base = (equity - self.r.floor_usd) if (self.r.house_money_only and equity > self.r.floor_usd * 1.1) else equity
        risk_usd = risk_base * self.r.max_risk_per_trade
        # never let one stop-out breach the floor
        risk_usd = min(risk_usd, max(0.0, equity - self.r.floor_usd - 0.01))
        qty = int(risk_usd // per_share_risk)
        if qty < 1:
            return {"qty": 0, "why": f"risk budget ${risk_usd:.2f} too small for this stop; use fractional or skip"}
        return {"qty": qty, "risk_usd": round(risk_usd, 2), "stop": stop, "entry": entry}

    def record_trade(self):
        self.trades_today += 1

    def unlock(self, confirmed_by_grayson: bool):
        if confirmed_by_grayson:
            self.locked = False


class AlpacaPaper:
    """Minimal Alpaca client. Paper by default. Set ALPACA_KEY / ALPACA_SECRET in env. Never hardcode keys."""
    PAPER = "https://paper-api.alpaca.markets"
    LIVE = "https://api.alpaca.markets"

    def __init__(self, paper: bool = True, dry_run: bool = True):
        self.base = self.PAPER if paper else self.LIVE
        self.dry = dry_run
        self.key = os.environ.get("ALPACA_KEY", "")
        self.secret = os.environ.get("ALPACA_SECRET", "")

    def _h(self):
        return {"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret}

    def equity(self) -> float:
        if self.dry or not self.key:
            return 25.00
        import requests  # only needed when live
        r = requests.get(f"{self.base}/v2/account", headers=self._h(), timeout=15); r.raise_for_status()
        return float(r.json()["equity"])

    def bracket_buy(self, symbol: str, qty: int, stop: float, take: float) -> Dict:
        order = {"symbol": symbol, "qty": qty, "side": "buy", "type": "market", "time_in_force": "day",
                 "order_class": "bracket", "stop_loss": {"stop_price": stop}, "take_profit": {"limit_price": take}}
        if self.dry or not self.key:
            return {"dry_run": True, "order": order}
        import requests
        r = requests.post(f"{self.base}/v2/orders", headers=self._h(), json=order, timeout=15); r.raise_for_status()
        return r.json()

    def flatten_all(self) -> Dict:
        if self.dry or not self.key:
            return {"dry_run": True, "closed": "all"}
        import requests
        r = requests.delete(f"{self.base}/v2/positions", headers=self._h(), timeout=15); r.raise_for_status()
        return {"closed": r.json()}


# =============================================================================
# 8b. TRADING LANGUAGE — glossary, math, orders, signals (the floor speaks fluent trader)
# =============================================================================
TRADING_GLOSSARY = {
    # term: (plain English, how OUR floor uses it)
    "stocks / equities":   ("Pieces of ownership in a company you can buy and sell.", "We only trade liquid US stocks + ETFs on Alpaca."),
    "portfolio":           ("Everything you hold: cash + open positions.", "Tape shows it every day; Bear caps total exposure."),
    "cash balance":        ("Money sitting in the account, not in any stock.", "Shown live. Never below the floor."),
    "buying power":        ("How much you can actually buy right now (cash, no margin for us).", "Bull can't size a trade above it."),
    "equity":              ("Cash + current value of positions = your real balance.", "The number the kill switch watches."),
    "bullish":             ("Expecting price to go up.", "Bull only buys when the signal is bullish."),
    "bearish":             ("Expecting price to go down.", "Bearish = no buys. We don't short."),
    "trend line":          ("A moving average that shows direction.", "20-period average: price above = bullish, below = bearish."),
    "volatility":          ("How much price swings.", "ATR. Too high = skip the trade; stop distance = 1.5x ATR."),
    "liquidity":           ("How easy it is to buy/sell without moving the price.", "Only names with big daily volume."),
    "bid / ask spread":    ("Gap between the buy price and the sell price.", "Over 0.5% = Bear vetoes."),
    "slippage":            ("Difference between the price you expected and what you got.", "Logged per fill; too much = smaller size next time."),
    "entry":               ("The price you buy at.", "Stated with every plan."),
    "exit":                ("The price you sell at (stop or take-profit).", "Always set before entry."),
    "market order":        ("Buy/sell now at the best available price.", "Used for entries on liquid names."),
    "limit order":         ("Buy/sell only at your price or better.", "Used for take-profit."),
    "stop-loss":           ("Auto-sell if price falls to X. Caps the loss.", "On every single order. No exceptions."),
    "take-profit":         ("Auto-sell if price rises to X. Locks the win.", "Set at 2x the stop distance (R:R 1:2)."),
    "bracket order":       ("Entry + stop-loss + take-profit in one order.", "Our default order type."),
    "trailing stop":       ("A stop-loss that moves up as price rises.", "Used once a trade is +1R to protect profit."),
    "buy order / sell order": ("Opening / closing a position.", "Every one logged with time, price, slippage."),
    "fractional shares":   ("Buying part of a share (e.g. $5 of a $200 stock).", "Lets a $25 account trade at all. Market orders only."),
    "position sizing":     ("How much to buy so one loss stays small.", "qty = risk $ / (entry - stop). Max 2% of equity."),
    "risk / reward ratio": ("How much you could lose vs gain on a trade.", "Minimum 1:1.5. Target 1:2."),
    "max risk per trade":  ("Most you let one trade lose.", "2% of equity, and never enough to breach the floor."),
    "maximum exposure":    ("Most of your equity in open positions at once.", "50%. One position at a time at first."),
    "drawdown":            ("Drop from the highest balance to now.", "Daily cap 4%. Max drawdown shown on the floor."),
    "win rate":            ("Percent of trades that made money.", "From paper results only. Not a promise."),
    "expectancy":          ("Average $ you make per trade over many trades.", "(win% x avg win) - (loss% x avg loss). Must be > 0 to go live."),
    "compounding":         ("Profits grow the base, so the next gains are bigger.", "Reinvested automatically once above the floor."),
    "reinvestment":        ("Putting profits back into trading instead of withdrawing.", "On by default; Grayson can sweep profits any day."),
    "house money":         ("Trading with profits instead of your own deposit.", "Once above the floor, only profit is risked."),
    "time in force":       ("How long an order stays open.", "DAY only. Nothing held overnight."),
    "paper vs live":       ("Fake money practice vs real money.", "14 paper days + positive expectancy before live."),
    "floor / kill switch": ("The balance that ends trading if touched.", "$20 on a $25 deposit. Flatten + lock. Grayson unlocks."),
}


class TradingMath:
    """Every number the floor shows comes from here. The page never does its own trading math."""

    @staticmethod
    def risk_reward(entry: float, stop: float, take: float) -> float:
        risk = abs(entry - stop); reward = abs(take - entry)
        return round(reward / risk, 2) if risk > 0 else 0.0

    @staticmethod
    def take_from_rr(entry: float, stop: float, rr: float = 2.0) -> float:
        return round(entry + (entry - stop) * rr, 2)

    @staticmethod
    def position_size(equity: float, floor: float, entry: float, stop: float,
                      max_risk_pct: float = 0.02, fractional: bool = True) -> Dict:
        risk_usd = min(equity * max_risk_pct, max(0.0, equity - floor - 0.01))
        per_share = abs(entry - stop)
        if per_share <= 0 or risk_usd <= 0:
            return {"qty": 0.0, "risk_usd": 0.0, "why": "no risk room or bad stop"}
        qty = risk_usd / per_share
        qty = round(qty, 4) if fractional else float(int(qty))
        return {"qty": qty, "risk_usd": round(risk_usd, 2), "notional": round(qty * entry, 2)}

    @staticmethod
    def exposure_pct(positions_value: float, equity: float) -> float:
        return round(100.0 * positions_value / equity, 1) if equity else 0.0

    @staticmethod
    def spread_pct(bid: float, ask: float) -> float:
        mid = (bid + ask) / 2
        return round(100.0 * (ask - bid) / mid, 3) if mid else 0.0

    @staticmethod
    def slippage(expected: float, filled: float) -> Dict:
        return {"usd": round(filled - expected, 4), "pct": round(100.0 * (filled - expected) / expected, 3) if expected else 0.0}

    @staticmethod
    def drawdown(equity_curve: List[float]) -> Dict:
        peak, max_dd, cur_dd = float("-inf"), 0.0, 0.0
        for e in equity_curve:
            peak = max(peak, e)
            dd = (peak - e) / peak if peak > 0 else 0.0
            cur_dd = dd
            max_dd = max(max_dd, dd)
        return {"current_pct": round(100 * cur_dd, 2), "max_pct": round(100 * max_dd, 2)}

    @staticmethod
    def win_rate(pnls: List[float]) -> float:
        return round(100.0 * sum(1 for p in pnls if p > 0) / len(pnls), 1) if pnls else 0.0

    @staticmethod
    def expectancy(pnls: List[float]) -> float:
        if not pnls:
            return 0.0
        wins = [p for p in pnls if p > 0]; losses = [-p for p in pnls if p <= 0]
        wr = len(wins) / len(pnls)
        avg_w = sum(wins) / len(wins) if wins else 0.0
        avg_l = sum(losses) / len(losses) if losses else 0.0
        return round(wr * avg_w - (1 - wr) * avg_l, 4)

    @staticmethod
    def compound(start: float, pct_per_period: float, periods: int, reinvest: bool = True) -> float:
        if not reinvest:
            return round(start + start * pct_per_period * periods, 2)
        return round(start * (1 + pct_per_period) ** periods, 2)

    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], n: int = 14) -> float:
        trs = []
        for i in range(1, len(closes)):
            trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
        trs = trs[-n:]
        return round(sum(trs) / len(trs), 4) if trs else 0.0

    @staticmethod
    def sma(values: List[float], n: int = 20) -> float:
        v = values[-n:]
        return round(sum(v) / len(v), 4) if v else 0.0


class OrderBuilder:
    """Alpaca-shaped orders. Always DAY, always with a stop. Fractional = market orders only."""

    @staticmethod
    def market(symbol: str, qty: float, side: str = "buy") -> Dict:
        return {"symbol": symbol, "qty": qty, "side": side, "type": "market", "time_in_force": "day"}

    @staticmethod
    def limit(symbol: str, qty: float, limit_price: float, side: str = "sell") -> Dict:
        return {"symbol": symbol, "qty": qty, "side": side, "type": "limit", "limit_price": limit_price, "time_in_force": "day"}

    @staticmethod
    def stop_loss(symbol: str, qty: float, stop_price: float) -> Dict:
        return {"symbol": symbol, "qty": qty, "side": "sell", "type": "stop", "stop_price": stop_price, "time_in_force": "day"}

    @staticmethod
    def bracket(symbol: str, qty: float, stop: float, take: float) -> Dict:
        return {"symbol": symbol, "qty": qty, "side": "buy", "type": "market", "time_in_force": "day", "order_class": "bracket",
                "stop_loss": {"stop_price": stop}, "take_profit": {"limit_price": take}}

    @staticmethod
    def trailing_stop(symbol: str, qty: float, trail_pct: float = 1.0) -> Dict:
        return {"symbol": symbol, "qty": qty, "side": "sell", "type": "trailing_stop", "trail_percent": trail_pct, "time_in_force": "day"}


@dataclass
class TradePlan:
    symbol: str
    entry: float
    stop: float
    take: float
    qty: float
    rr: float
    bias: str            # bullish | bearish | neutral
    atr: float
    spread_pct: float
    exposure_after_pct: float
    verdict: str = ""    # Bear's call
    reason: str = ""


class Signals:
    """Bull proposes, Bear vetoes. Both talk in full trading language with full confidence."""

    def __init__(self, rules: "TradingRules"):
        self.r = rules

    def bias(self, closes: List[float], n: int = 20) -> str:
        if len(closes) < n:
            return "neutral"
        sma = TradingMath.sma(closes, n)
        return "bullish" if closes[-1] > sma else ("bearish" if closes[-1] < sma else "neutral")

    def propose(self, symbol: str, highs: List[float], lows: List[float], closes: List[float],
                bid: float, ask: float, equity: float, positions_value: float, rr: float = 2.0) -> TradePlan:
        b = self.bias(closes)
        atr = TradingMath.atr(highs, lows, closes)
        entry = ask
        stop = round(entry - 1.5 * atr, 2) if atr else round(entry * 0.99, 2)
        take = TradingMath.take_from_rr(entry, stop, rr)
        size = TradingMath.position_size(equity, self.r.floor_usd, entry, stop, self.r.max_risk_per_trade, fractional=True)
        qty = size.get("qty", 0.0)
        plan = TradePlan(symbol, entry, stop, take, qty, TradingMath.risk_reward(entry, stop, take), b, atr,
                         TradingMath.spread_pct(bid, ask), TradingMath.exposure_pct(positions_value + qty * entry, equity))
        return self.bear_review(plan)

    def bear_review(self, p: TradePlan, min_rr: float = 1.5, max_spread: float = 0.5, max_exposure: float = 50.0) -> TradePlan:
        if p.bias != "bullish":
            p.verdict, p.reason = "VETO", f"{p.bias} bias. We don't buy into weakness."
        elif p.qty <= 0:
            p.verdict, p.reason = "VETO", "no risk room above the floor."
        elif p.rr < min_rr:
            p.verdict, p.reason = "VETO", f"R:R {p.rr} under 1:{min_rr}."
        elif p.spread_pct > max_spread:
            p.verdict, p.reason = "VETO", f"spread {p.spread_pct}% over {max_spread}%. Slippage risk."
        elif p.exposure_after_pct > max_exposure:
            p.verdict, p.reason = "VETO", f"exposure would be {p.exposure_after_pct}% > {max_exposure}%."
        else:
            p.verdict, p.reason = "GO", f"bullish, R:R 1:{p.rr}, spread {p.spread_pct}%, exposure {p.exposure_after_pct}%."
        return p

    @staticmethod
    def speak(p: TradePlan) -> str:
        return (f"{p.symbol}: {p.bias.upper()} — price above the 20-period trend line, ATR {p.atr}, spread {p.spread_pct}%. "
                f"Plan: entry ${p.entry}, stop-loss ${p.stop}, take-profit ${p.take}, R:R 1:{p.rr}, size {p.qty} shares, "
                f"exposure after {p.exposure_after_pct}%. Bear: {p.verdict} — {p.reason}")


def tape_report(cash: float, buying_power: float, equity: float, positions_value: float, trades_today: int,
                pnls_today: List[float], equity_curve: List[float], floor: float, fills: List[Dict]) -> Dict:
    """Tape's daily report. Every field is a term from the glossary. Verified from Alpaca only."""
    dd = TradingMath.drawdown(equity_curve or [equity])
    return {
        "cash_balance": round(cash, 2), "buying_power": round(buying_power, 2), "equity": round(equity, 2),
        "open_positions_value": round(positions_value, 2), "exposure_pct": TradingMath.exposure_pct(positions_value, equity),
        "trades_today": trades_today, "win_rate_pct": TradingMath.win_rate(pnls_today),
        "realized_pnl_today": round(sum(pnls_today), 2), "expectancy": TradingMath.expectancy(pnls_today),
        "drawdown_today_pct": dd["current_pct"], "max_drawdown_pct": dd["max_pct"],
        "floor_distance": round(equity - floor, 2), "avg_slippage_pct": round(sum(f.get("slippage_pct", 0) for f in fills) / len(fills), 3) if fills else 0.0,
        "disclaimer": "Not financial advice. You can still lose money. Paper results are not a promise.",
    }


# =============================================================================
# 10. CONFIDENCE — decisions + numbers, never hedging (every agent, every business)
# =============================================================================
CONFIDENCE_RULES = [
    "Lead with the decision. Then the number. Then the next action.",
    "No maybe / might / I think / could possibly / perhaps / hopefully / kind of.",
    "Unknown = 'unknown, getting it now.' Never a guess dressed as a maybe.",
    "Verdicts, not opinions: PASS 94 / REJECT 81 + one reason.",
    "Standup = one line: what I did, the number, what's next.",
    "Confidence never bends a verified number. Numbers stay true; the voice stays certain.",
]
HEDGE_WORDS = ("maybe", "might", "i think", "could possibly", "perhaps", "hopefully", "kind of", "sort of",
               "i guess", "probably", "it seems", "not sure", "i believe")


def confident(text: str) -> str:
    """Strip hedge words from agent output. Keeps the facts; kills the waffle."""
    out = text
    for w in HEDGE_WORDS:
        out = re.sub(r"(?i)\b" + re.escape(w) + r"\b,?\s*", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out[0].upper() + out[1:] if out else out


def hedge_score(text: str) -> int:
    """0 = fully confident. Foreman grades hedging like missing quota."""
    t = text.lower()
    return sum(t.count(w) for w in HEDGE_WORDS)


# =============================================================================
# 9. NIGHT SHIFT PLAN — what the scheduled run actually does
# =============================================================================
def build_night_shift_plan(registry: Dict[str, Floor], verified_month: float, today: Optional[date] = None) -> Dict:
    today = today or date.today()
    fm = Foreman(SkillBook())
    clock = fm.shutdown_clock(verified_month, today)
    hol = active_holiday_themes(today)
    return {
        "version": "GM FACTORY V6.0",
        "date": str(today),
        "tz": TZ,
        "mode": "EMERGENCY" if clock["emergency"] else ("HOLIDAY" if holiday_mode(today) else "NORMAL"),
        "shutdown_clock": clock,
        "steps": [
            "0. Read every /factory/skills/*/SKILL.md and /factory/LESSONS.md. Use playbooks before inventing.",
            "1. Hawk: pull last 3 days of REAL stats (Pinterest, IG, TikTok, FB, YouTube). Write what's working / dead.",
            "2. Beacon: plan_from_stats() -> today's post plan per channel. Santa owns 60%+ while Holiday Mode is on.",
            f"3. Scout: {IDEAS_PER_NIGHT} ideas with evidence across lanes {list(PRODUCT_LANES)}. Idea Judge auto-approves at {PASS_SCORE}+.",
            f"4. Forge: build {BUILDS_PER_NIGHT} (pick_builds enforces {int(HOLIDAY_MODE_SHARE*100)}% holiday while on). Mug/sticker specs in BUILD_SPECS.",
            "5. Quill + Lens: copy + 5 real-looking photos. Mirror scores. Under 92 = rebuild tonight, not tomorrow.",
            "6. Bolt: publish to Etsy + Gumroad through Make 6676353 (existing lanes, 2/day cap, keyed by id).",
            "7. Flame/Reel/Tick: queue posts per Beacon's plan (free caps only). Mirror gates every post.",
            "8. Studio: 2 Short drafts; Judge scores story/voice/music/motion; Rocket posts the better one if all >= 92.",
            "9. Spot: one 15-30s ad for the top product -> Marketing Wing queue.",
            "10. Ledger: verified sales only (Etsy/Gumroad payouts). Update payback meter + Shutdown Clock.",
            "11. Every agent: record_score() + one 'What I've learned' line. Same-as-yesterday = fail.",
            "12. Foreman: standup() -> Foreman tab + Inbox. Sunday: all_hands() + promote top lessons to SKILL.md.",
            "13. Trading Floor: SKIP until Phase 7 go. Then paper only, market hours only, RiskManager before every order.",
        ],
        "holiday_targets": hol,
        "floors": {fid: {"status": f.status, "agents": [a.name for a in f.agents]} for fid, f in registry.items()},
    }


# =============================================================================
# demo
# =============================================================================
if __name__ == "__main__":
    reg = build_registry()
    if "--trade" in sys.argv:
        rules = TradingRules(); sig = Signals(rules)
        closes = [10 + i * 0.05 for i in range(30)]; highs = [c + 0.1 for c in closes]; lows = [c - 0.1 for c in closes]
        plan = sig.propose("DEMO", highs, lows, closes, bid=11.44, ask=11.46, equity=40.0, positions_value=0.0)
        print(Signals.speak(plan))
        print(json.dumps(OrderBuilder.bracket(plan.symbol, plan.qty, plan.stop, plan.take)))
        print(json.dumps(tape_report(40, 40, 40, 0, 1, [0.6, -0.3], [25, 30, 28, 40], rules.floor_usd, [{"slippage_pct": 0.05}]), indent=1))
        print(confident("I think maybe we should probably build the mug bundle, it seems like it might score 93."))
    elif "--standup" in sys.argv:
        fm = Foreman(SkillBook())
        demo = [
            AgentStats("scout", "Scout", "ideas passing 92", today=6, quota=15, score=90, improved=False),
            AgentStats("forge", "Forge", "builds scored 92+", today=2, quota=2, score=93, improved=True),
            AgentStats("flame", "Flame", "outbound clicks", today=3, quota=9, score=88, improved=False),
            AgentStats("rocket", "Rocket", "posts w/o error", today=1, quota=1, score=95, improved=True),
        ]
        print(fm.standup(demo, verified_month=0.00))
        print()
        print(fm.pulse("2 builds, 9 pins queued, 1 Short posted", ["pinterest x9", "instagram x2"], 0.00))
    else:
        print(json.dumps(build_night_shift_plan(reg, verified_month=0.00), indent=2))
