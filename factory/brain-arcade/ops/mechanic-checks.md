# Mechanic checks for the Brain Arcade lane (run at every Mechanic run)

1. Scheduled tasks "Brain Arcade · Night Build", "Brain Arcade · Publisher", "Brain Arcade · Learn":
   last_run FAILED or a daily window missed by 2+ hours -> fire_trigger ONCE per day (same refired
   rule as the other tasks).
2. `python3 factory/brain-arcade/tools/ba_log.py status`: a newest line with outcome failed or blocked,
   or a needsYou -> red light "arcade", one line in needsYou (the exact tap).
3. Guard: any runlog note or results row today containing "BLOCKED" -> red, report it (never re-fire
   the publisher to retry a blocked post).
4. lane.json make.connection_id null for more than 24 h after Oct 25, 2026 -> needsYou
   "Tap the Brain Arcade Etsy link: <lane.json make.credential_request_link>".
5. Self-fix (once a day): a Brain Arcade tool error in the run log -> re-run that tool's selftest
   (answer_check.py --selftest, shop_guard.py selftest); a FAIL goes in needsYou for the next
   Night Build to fix under the bug rule. The Mechanic never edits Brain Arcade files.
6. Never touches this lane's Make scenario, listings or lane.json.
