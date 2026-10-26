# 00 Gates and the daily Etsy snapshot

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/gateway.md` | "Protocol", "Etsy" | How to reach Etsy |
| Shared | `../../../shared/repo.md` | "Getting it", "Committing", Bolt row of "Write paths" | Repo use |
| Skill | `../../../skills/bolt/SKILL.md` | Full file | Checklist and lessons |
| Database | settings/main, sales (ids only, for the sync), spend/<month key>, lessons (newest 10 with area etsy, pins or setup) | | Gates and lessons |

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
6. SALES SYNC (Grayson, Oct 24, 2026: every run, never skipped, even dry runs and paused-by-cap
   days). Add {"op":"etsy","method":"GET","path":"/shops/68605457/receipts?limit=100","tag":
   "receipts"} AND {"op":"etsy","method":"GET","path":"/shops/68605457/reviews?limit=100","tag":
   "reviews"} to the snapshot job (or, if the snapshot was skipped, to the active-list job).
   The reviews answer is only read later by the Night Shift (notebook/buyer_voice.py, Oct 26,
   2026); if it fails, note it in the run log and carry on: it never blocks a sale sync or a publish.
   Then: ArtifactData query collection "sales" (limit 300, out_dir <tmp>/sales), and run
   `python3 factory/shared/etsy_sales.py gw/out/<job id>.json <tmp>/sales <tmp>/sales-writes.json`.
   If it lists new sales, write the file's "writes" with ONE ArtifactData batch (new docs only,
   ids etsy-<receipt_id>, so it never double-counts), add one events/<day key> line per sale
   ("New Etsy sale: $<gross> · <title>") and keep the "new" list for stage 04, which messages
   Grayson (a new sale leads the message). If the receipts call fails, write
   needs-you "Etsy sales sync failed: <error>" in the run log and say it in stage 04's message
   so it never fails silently. Never type a sale in by hand; real receipts only.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Snapshot | stats/<day key> | shape above |
| New sales | sales/etsy-<receipt_id> + events line | etsy_sales.py output |
| Active + draft lists | local files for the next stages | gateway JSON |
| Gate results | local note: publishedToday, feesThisMonth, dryRun | |
