# Mechanic (self-fix + morning report): prompt-led, not yet moved

The Mechanic is a one-job task; its full instructions stay in the scheduled task's prompt
(saved copy: `references/legacy-prompt-2026-10-21.md`, plus the Oct 21 additions below).
Phase 3 of the workspace added three things to that prompt, nothing else:
1. The task list it checks now includes the Pricing agent and the Pixel video pin.
2. It runs `python3 factory/shared/runlog.py --status` and `--summary 7` each run; a task
   whose last logged run failed, or whose minutes are more than double its 7-day average,
   goes in "watching", and the morning report gets one clause: "crew: N runs logged, avg X
   min" when the numbers changed.
3. It writes its own run-log line at the end (shared/logging.md).

## V8 "The Turning Point" (Oct 24, 2026): the Medic is now two halves
1. **The machine half** lives in `medic/` at the repo root: plain Python on a GitHub Action every 30
   minutes (`.github/workflows/medic.yml`). It reads the run log, the gateway folders, the trading
   heartbeats, the video-pin state, the Shorts builds, the engine report and the Actions API; it
   restarts what it can for free, verifies the fix is live, learns (`medic/lessons/`), and writes
   `medic/public/medic_report.json` (the board the Today screen shows). Fix-once per thing per day.
2. **The crew half is you.** What the machine cannot do becomes a ticket in `medic/queue/*.json`
   (status `open`). On every run you work the tickets first (step 0 in the proposed prompt,
   `references/v8-medic-prompt-2026-10-24.md`), then carry the board into the morning report.
   Until Grayson applies that prompt, the tickets wait in the folder and the Medic's `needs_you`
   lines reach him through the Today screen only.

Never edit `medic/medic.py`, `medic/lanes.json`, `medic/db/` or `medic/public/`; the only Medic file a
crew touches is a ticket's `status`, `note`, `by`, `at`. Ticket statuses: `open` → `done` (you fixed
it), `handed` (another crew's next run does it; also listed in the database doc `medic/requests`),
`cannot` (say why). The Medic moves a resolved ticket to `medic/queue/done/` once the lane is green.
