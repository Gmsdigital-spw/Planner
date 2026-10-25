# 03 Pick: the build list and missions (rooms "bridge", "mission")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/database-fields.md` | "products", "missions" | Field shapes |
| Spec | `../../../specs/cover-styles.md` | Newest section (Oct 21, 4 PM) | The cover standard |
| Tool | `tools/fun_covers.py` | docstring and the THEMES keys (grep "^    \"" in THEMES) | Pick style.theme |
| Tool | `ls tools/img3d` and `tools/art.py` function names | | Pick coverLook.art |
| Database | products (newest 3 published): coverLook, style | | Rotation |
| Database | products (stage queued, building, copy, sentback), briefs (approved, no productId) | | What to build |
| Database | missions (newest 20), sales, stats (newest 2), bills | | Missions from real numbers |

## Process
1. Set crew/atlas working ("Picking builds"). Build list, in this order, up to
   settings.buildsPerRun (default 2). NO PROOF, NO BUILD (Grayson, Oct 24, 2026, replaces the
   "invitations first" exception): EVERY product, his own orders included, passes the MARKET
   PROOF GATE below on ITEM-level reviews (an opened listing page; a search card's or shop's total
   never counts), or passes its OPEN NICHE path (Oct 24, 2026). Invitation briefs qualify through
   the open-niche path when 2+ rivals have 100+ favorites and our gap is written. (a) products in stage "inspection" scoring 80 to 91 with retries under 4 and market 12 or more (market 11 or less = scrap it unless open niche, see 07; one exception: prod-xmas-murder-mystery-8 gets ONE final finish try on the Oct 25, 2026 night run (moved from Oct 24 for Grayson's invitations) with its staged v2 fixes, then is scrapped if still under 92),
   highest score first (a near-miss is the fastest way to a live listing: the Builder
   reworks it against its inspect note and preflight.md), then products in stage queued,
   building, copy or sentback that have no file or were sent back (finish them first); (b) briefs with status "approved"
   that have no productId; (c) only when settings.autoApprove is false: briefs "proposed" with
   total 20 or more, highest first, skipping anything Grayson rejected. Holiday Mode share
   applies to new builds (product-floor spec). If nothing to build, log it and go to stage 09.
   MARKET PROOF GATE (Oct 23, 2026): a brief is built only if it names 3 opened Etsy
   listings (links, review counts as shown, at least one 100+) and our gap, as
   `../references/preflight.md` "Market" says. A brief without them goes back to status
   "proposed" with note "needs opened competitor proof" and the next brief takes its place.
2. For each chosen brief create products/<id> {title, briefId, lane -> kind, stage "building",
   summary, createdAt, source "Night Shift <day>"} and set the brief's status "built" and
   productId.
3. Choose now and save: product.style = {palette (gs palette for the pages), coverStyle (the
   PDF cover style: band / frame / split), pageFrame (rule / stripe / band / none), theme (a
   tools/fun_covers.py THEMES key that fits the product), kit:"gm_kit_v4"} and
   product.coverLook = {tool:"fun_covers", theme, art:[the 3D art names planned]}. Rotation:
   theme and art must differ from the last 3 published products' coverLook, and no two
   products built tonight share a palette, pageFrame or coverStyle.
4. Missions (room "mission"). (a) For each mission with status active or blocked: mark its
   tasks doing/done as this run completes them, record outputs; set a task blocked with a
   note when it cannot proceed; if Grayson must act set needsOwner true and ownerAsk to one
   plain sentence; when the verify criterion is met by real data set status done with result.
   (b) If no mission is planned or active, create exactly ONE from real numbers: the first
   mission is always "Get the first verified sale" until the sales collection has an entry;
   after that, missions aim at the subscription-recovery number (the active bill with kind
   "claude"). Status "planned" (Grayson approves). Tasks name a crew member and dependsOn, and
   are things this crew can do in a run or Grayson can do in one tap. Never more than 1 new
   mission per run, never more than 3 active. Missions never promise sales; verify criteria
   are numbers readable from the database.
5. Set crew/atlas idle. Write the build list to `../output/<day key>-run.md` ("## Build list").

## Audit

| Check | Pass condition |
|-------|---------------|
| Cap | Build list <= buildsPerRun |
| Variety | No product repeats the theme + art (coverLook) of the last 3 published |
| Missions | At most 1 new, status planned, with a numeric verify |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Products to build | products/<id> | stage building, style set |
| Missions | missions/<id> | spec shape |
| Run notes | `../output/<day key>-run.md` | "## Build list" |
