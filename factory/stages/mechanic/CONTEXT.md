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
