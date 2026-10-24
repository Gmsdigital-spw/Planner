# Ops notebook: how the crew itself runs (what breaks, what fixes stick)

## Grayson's rules
- 2026-10-22: Notify Grayson right away when anything stops, breaks or needs him. Nothing stops silently.
- 2026-10-23: Never tell Grayson something is fixed unless it was checked again on a later run. The same problem coming back after "fixed" is the worst outcome.
- 2026-10-21: Keep the ship simple; fewer moving parts.

## What works (proven by numbers)
- 2026-10-21: The free GitHub gateway handles Etsy/Zernio/Alpaca calls without spending Make operations (Make was at 56% of its monthly budget on Oct 23).

## Testing (not proven yet)
- Oct 23: paused Trading lab + Gmula Short, Scout 5x->2x/day, Mechanic 5x->3x/day to cut usage and breakage. Check Oct 30: fewer failures in the run log, usage lasting longer.
- Scout Intel saving its run log through the Mechanic (Scout can't push to GitHub). Check Oct 30: no missing scout-intel days in the run log.

## What doesn't work (tried, failed, or Grayson rejected)
- 2026-10-23: Big gateway jobs: 12 Etsy reads in one job hit Etsy's per-second rate limit (1-3 of 12 failed), and a job whose output tops 400 KB (gw/run.py cap) comes back blank. Keep jobs small (6 reads or fewer, marketplace searches split up) and re-run only the failed ops.
- 2026-10-23: Fixing the covers by swapping in a new house style. Done 3 times (Oct 20, 21, 23); every time all listings ended up looking alike. Variety must be enforced by a side-by-side gate, not a style.
- 2026-10-23: Self-graded scores as proof of quality: 24 look-alike covers all "passed".
- 2026-10-22/23: Herald kept making TikTok posts and the Mechanic kept flagging "reconnect TikTok" after Grayson parked the shop TikTok on purpose (Zernio free plan = 2 accounts, slot given to Ridgeline Facebook). Crews must check the notebook's Grayson's rules before calling something broken.
- 2026-10-22: Scout Intel pushing to GitHub from its scheduled task (403 every run).
