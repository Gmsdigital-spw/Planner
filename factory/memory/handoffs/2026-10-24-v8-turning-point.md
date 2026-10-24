# Handoff: V8 "The Turning Point" (built Oct 24, 2026, on branch claude/new-session-mhoaoj)

_Everything the session that built V8 knew that the crews and the next session should start from. Facts only; where a thing is unverified it says so. Read this once; MEMORY.md carries the short version._

## What was built, per phase
0. Backups: dated copies of both apps' pages (`factory/page/gm-agency-v7-2026-10-24-pre-v8.html`; Ridgeline `office/page/backups/`) and zips sent to Grayson. Rollback = republish the backup page to the same artifact.
1. Ridgeline Cold Call Kit (`office/call_kit/`, the Office "Calls" screen with 15 real businesses and real AI-check results) and automatic messages (reply desk Lane G sends call follow-ups and free checks itself; hands off only price talk and angry replies). Live in the Office; Lane G sends after the merge.
2. The Medic: `medic/medic.py` (Planner) and `office/medic/medic.py` (Ridgeline; a copy, never a link), `medic/lanes.json`, `medic/schema.sql`, `.github/workflows/medic.yml` (every 30 min, free). Detect, fix (dispatch, rerun, rebuild, next slot), check, learn (3 hits = a rule), tickets to the Mechanic (`medic/queue/`), report (`medic/public/medic_report.json`). Verified with selftests, dry runs and real passes on fresh clones. Starts on the schedule after the merge. The Mechanic's V8 prompt is proposed (`factory/stages/mechanic/references/v8-medic-prompt-2026-10-24.md`), not applied.
3. The new look: Atlas Hub (`factory/page/atlas-hub.html`, live as artifact version 64: Today, Work, Agents, More; navy; dark mode; the same database and the same write payloads as before) and Ridgeline Local (`office/page/ridgeline-office.html`, live as Office version 10; green). Tested in a real browser at light and dark; every tap verified to write the legacy payloads. The Mechanic's old sweep will FAIL on the new page until the branch merges (new `factory/qa/sweep.py`).
4. Shorts overhaul: `studio/quality_gates.py` (scorecard 85, cover check 92, commercial blueprint), the gate inside `yt-build.yml`, `make_short.py` metadata, `specs/studio-floor-v8.md`, every Studio stage file and skill updated (research first via the free YouTube API through Make, hook in 1.5 s, 7 to 12 lines, 20 to 45 s, real motion on line 1 and the twist, the last 7 posted, kill list, notebook lines, title scoring only with 5+ credits). The Medic counts only Shorts that passed.
5. Etsy: `specs/etsy-v8.md`; Lens runs the cover uniqueness check; Inspect records `score.coverGate`; rebuild never skip; Christmas by Nov 7; five invitations by Nov 15; Quill writes `listing_fixes`, Bolt applies 2 a day (title and tags only); Herald follows the commercial blueprint; Nov 7 judgement.
6. Website: V8 green design, "any local business, anywhere", CTA inside the first phone screen, tested at 320/390/1280.
7. Trading: paper labels and the crypto paper bot already on the Atlas Hub's Paper trading row; the floor stays $20 (V8 said $25: a wording slip); weekly grading rules in both workspaces; every skill file carries the agent header.

## Verified for real (not assumed)
- Both Medic engines: selftest, dry run, real pass on a fresh clone of main.
- Atlas Hub and Ridgeline Local: Playwright at 390 px light and dark, every tab and drawer, no sideways scroll, write payloads identical to the old pages (stubbed database).
- Shorts gate on ep11 to ep16 (scores above); cover gate on the 17 Atlas covers (distances above).
- Free research path: two Make `ytapi` executions (search, videos), 0 credits.
- vidIQ balance read: 2 credits.
- Website at three widths: no console errors, no horizontal scroll.

## Open items (need Grayson)
- Merge `claude/new-session-mhoaoj` to main in Planner and ridgelinehq.github.io (or say "push to main"): until then the crews run the old rules, the Medic Action does not run, Lane G does not send, the website stays the old look, and the Mechanic reports a page FAIL.
- Unpause the Studio task after the merge (one tap), then set `gmula_shorts.paused` false in `medic/lanes.json`.
- Approve the Mechanic's V8 prompt (text in `factory/stages/mechanic/references/v8-medic-prompt-2026-10-24.md`); it is applied with update_trigger, prompt only.
- vidIQ credits: 2 until Nov 19. Title scoring and vidIQ research sleep until then unless he adds credits (paid: his call; the crew never buys).
- The "$25 floor" wording in V8 vs the coded $20 floor: his call; nothing changed.

## Gotchas learned building this
- Artifact publish refuses to replace a live page until the session has read every line of the live source; keep the saved source and publish from your own file.
- ArtifactData batch: per-doc files for big writes; nested where-filters refused; `if_version` on every doc update.
- Playwright: inject the `window.claude` stub as an inline script before the page script; `addInitScript` was not visible to the page. Python Playwright needs `PW_CHROMIUM=/opt/pw-browsers/chromium` when its driver is newer than the installed browser.
- `renderPage` targets `<section id="p-<page>">`: a page with no section renders nothing.
- GitHub: `workflow_dispatch` only for workflows on the default branch; pushes by GITHUB_TOKEN never trigger workflows; the Actions runs list covers about 2.5 h per 100 runs, so query per workflow.
- A `cd` inside one shell command can reset the next command's working directory: absolute paths and `git -C`.
- The Make `ytapi` lane proxies any YouTube Data API GET; `videoDuration=short` means under 4 minutes.
- Cloudflare image "NSFW" false positives: retry once.
