# Crew memory (read this first; under 60 lines; newest first)
_The GM Factory crew's shared long-term memory. Every run reads it at the start (CLAUDE.md "Memory rule"). Each line has a date; a source where there is one. No personal details, no secrets, ever: the repo is public._

## Standing truths (Oct 24, 2026)
- V8 "The Turning Point" (Oct 24): `specs/etsy-v8.md`, `specs/studio-floor-v8.md` and `studio/quality_gates.py` are Grayson's newest orders and win over older specs where they differ. The full build record: `memory/handoffs/2026-10-24-v8-turning-point.md`.
- Mission: make Grayson money; real numbers only; nothing ships under 92 (Etsy) or under Judge 7+ AND scorecard 85+ (Shorts); first sales before Christmas; stay free (approved money: $0.20 listing fees inside the cap, Ridgeline's $5 OpenAI credit).
- The crews read `main`. The V8 work sits on branch `claude/new-session-mhoaoj` until Grayson merges it; a crew that cannot find a V8 file on main is running before the merge, not broken.
- vidIQ credits: 2 (renewable 0 of 150, renews Nov 19, 2026). Every 5-credit vidIQ call is skipped until then. Research and stats go through the free YouTube Data API via Make scenario 6676353 (`ytapi`), verified Oct 24 (search + videos, 0 credits; filter to 60 s or less and English titles).
- The free Hugging Face animation lane works: ep16 lines 5 and 7 got real motion on Oct 22 (HF_TOKEN is set as a repo secret). The scorecard needs real motion on line 1 and the twist.
- The Studio scheduled task ("Studio Floor daily Short (Gmula)") is OFF on purpose until V8 merges; one tap by Grayson turns it on; then set `paused` false on `gmula_shorts` in `medic/lanes.json`.
- The Mechanic's page check runs the old Starship sweep until the branch merges: a FAIL on the Atlas Hub page before the merge is expected (the new `factory/qa/sweep.py` fixes it after).
- Shorts scorecard: the Atlas Hub reads `pipeline/<id>.scorecard.score`; the Medic reads `yt/out/<id>.score.json`; both come from `studio/quality_gates.py`. Real Oct 24 scores: ep16 70, ep14 50, ep11 to ep13 40 (still openings, slow beats, no title score).
- Covers: Grayson's own Atlas covers (Oct 24) are the standard: real pages on his scenes + one cream label card, no stickers, pills or emoji. Among his 17 covers, 7 pairs sit under phash distance 18 (closest 6: same scene and crop), so rotate scene, crop, label position and colour every time.
- Listing fixes: Grayson's V8 go covers TITLE and TAG edits on live listings only (2 a day, GET-verified, before new publishes). Price, photos, description, category and deactivation still need his go.
- Trading: paper only. The coded floor is $20 on a $25 deposit; V8's "$25 floor" wording was a slip. Only Grayson changes money rules.
- Parked, do not touch: TikTok (Grayson's), Gumroad, Funnel Floor, Frontier Nav, Brain Arcade.
- The Make free plan is an operations budget: the free gateway (`gw/jobs` -> Action -> `gw/out`) is the path for Etsy and Zernio; Make is only Bolt's Etsy fallback and the Studio's `ytapi`/`youtube` lanes.
- GitHub: pushes made with GITHUB_TOKEN never trigger other workflows; `workflow_dispatch` works only for workflows on the default branch; the yt-build Action resets to origin/main before saving outputs; the Medic Action commits its db, lessons, queue and public report every 30 minutes once merged.
- Cloudflare image "NSFW" refusals on family-friendly prompts are false positives: retry once before rewording.
- The Medic (`medic/medic.py`, Actions every 30 min after merge) fixes what it can (dispatch, rerun, rebuild), tickets the rest to the Mechanic in `medic/queue/`, and only tells Grayson what needs him. The Mechanic's V8 prompt is proposed in `factory/stages/mechanic/references/v8-medic-prompt-2026-10-24.md` and waits for his go.

## Gotchas that cost runs before
- Real speech runs 5 to 6 s longer than the fake-TTS dry run (plan words from the target seconds).
- Two-character prompts drew human faces: one character per scene prompt.
- Five builds in a row died at 73 to 85 for the same preflight faults: run `preflight.md` before inspection, every line.
- ArtifactData batch writes need per-doc files (file_path) for big batches; nested where-filters are refused.
- A `cd` in a shell command can reset the working directory for the next command: use absolute paths and `git -C`.

## Where memory lives
- This file (shared). `facts.md` (dated facts, append-only). `decisions.md` (Grayson's decisions index). `agents/<id>.md` (each agent's durable memory). `handoffs/` (session handoffs). `skills/<id>/SKILL.md` "What I've learned" (the nightly line). `LESSONS.md` and `notebook/` (numbers-backed lessons).
