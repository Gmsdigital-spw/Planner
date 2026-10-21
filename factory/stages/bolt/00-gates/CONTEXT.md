# 00 Gates and the daily Etsy snapshot

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/gateway.md` | "Protocol", "Etsy" | How to reach Etsy |
| Shared | `../../../shared/repo.md` | "Getting it", "Committing", Bolt row of "Write paths" | Repo use |
| Skill | `../../../skills/bolt/SKILL.md` | Full file | Checklist and lessons |
| Database | settings/main, spend/<month key>, lessons (newest 10 with area etsy, pins or setup) | | Gates and lessons |

## Process
1. Repo: cd /home/claude/planner && git pull --rebase. Note the start time, day key, month key.
2. Read settings/main. Stop (no message) if paused is true. If dryRun is true: do this stage
   and stage 01 only, log one events line per candidate "DRY RUN: Bolt would publish
   <title>", then go straight to stage 04 (no publishing, no pins).
3. dailyCap = settings.dailyCap (default 2, never more than 2). monthlyFeeCap =
   settings.monthlyFeeCap (default 20). Read spend/<month key>: publishedToday = entries with
   kind "listing" whose date (Central) is today; feesThisMonth = sum of cost. A new listing
   costs $0.20. Stage 02 is skipped when publishedToday >= dailyCap or feesThisMonth + 0.20 >
   monthlyFeeCap (stage 03 still runs).
4. Read the newest 10 lessons for each area you touch (etsy, pins, setup) and apply them.
5. DAILY ETSY SNAPSHOT (the crew learns from this; every run, even dry runs). Skip only if
   stats/<day key> exists with source "etsy (Bolt)" written in the last 6 hours. One gateway
   job (prefix bolt, step "snap"): GET /shops/68605457/listings/active?limit=100&includes=Images,
   GET /shops/68605457, GET /shops/68605457/listings?state=draft&limit=100. Save the answers
   to disk; with Python write stats/<day key> (set; read first, pass if_version if it exists):
   {day, at:now, source:"etsy (Bolt)", listings:{<listing_id>:{title (unescape &#39; &quot;
   &amp;), price (amount/divisor), views, favs (num_favorers), photos (images count), tags
   (count), tagList (max 13), description (unescaped, first 3000 chars), url}}, shop:{title,
   reviews (review_count), sales (transaction_sold_count), favorers (num_favorers), active
   (listing_active_count)}}. Never invent a number; if a call fails, skip the snapshot and log
   it. Keep the active and draft lists on disk for stages 01 and 02 (if you skipped the
   snapshot, still fetch the active list with Images in one job).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Snapshot | stats/<day key> | shape above |
| Active + draft lists | local files for the next stages | gateway JSON |
| Gate results | local note: publishedToday, feesThisMonth, dryRun | |
