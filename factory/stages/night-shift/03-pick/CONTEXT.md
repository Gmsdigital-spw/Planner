# 03 Pick: the build list and missions (rooms "bridge", "mission")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/database-fields.md` | "products", "missions" | Field shapes |
| Spec | `../../../specs/cover-styles.md` | Newest section (Oct 24, 2026: Grayson's Atlas covers) | The cover standard |
| Tool | `assets/atlas-pack/README.md` ("Etsy" table) + `place.py` docstring | scene names: planner, clipboard, christmas, frame | Pick coverLook.scene |
| Tool | `tools/fun_covers.py` THEMES keys (grep "^    \"" in THEMES) | names only | style.theme, a palette name for the pages and pins (the card itself is retired) |
| Database | products (newest 3 published): coverLook, style | | Rotation |
| Database | products (stage queued, building, copy, sentback), briefs (approved, no productId) | | What to build |
| Database | missions (newest 20), sales, stats (newest 2), bills | | Missions from real numbers |

## Process
1. Set crew/atlas working ("Picking builds"). Build list, in this order, up to
   settings.buildsPerRun (default 2). NO PROOF, NO BUILD (Grayson, Oct 24, 2026, replaces the
   "invitations first" exception): EVERY product, his own orders included, passes the MARKET
   PROOF GATE below on ITEM-level reviews (an opened listing page; a search card's or shop's total
   never counts). The invitation briefs went back to "proposed" until a 100+ item-review invite
   rival is found. (a) products in stage "inspection" scoring 80 to 91 with retries under 4 and market 12 or more (market 11 or less = scrap it, see 07; one exception: prod-xmas-murder-mystery-8 gets ONE final finish try on the Oct 25, 2026 night run (moved from Oct 24 for Grayson's invitations) with its staged v2 fixes, then is scrapped if still under 92),
   highest score first (a near-miss is the fastest way to a live listing: the Builder
   reworks it against its inspect note and preflight.md), then products in stage queued,
   building, copy or sentback that have no file or were sent back (finish them first); (b) briefs with status "approved"
   that have no productId; (c) only when settings.autoApprove is false: briefs "proposed" with
   total 20 or more, highest first, skipping anything Grayson rejected. Holiday Mode share
   applies to new builds (product-floor spec). If nothing to build, log it and go to stage 09.
   V8 (Oct 24, 2026; specs/etsy-v8.md sections 3 and 4): until 10 Christmas listings are live,
   at least one of tonight's builds is a Christmas product (bundles $8 to $14 first; a Christmas
   near-miss finished from inspection counts; on a night the invitation briefs above fill
   buildsPerRun, the Christmas build takes the first slot the next night and the Report's
   CHRISTMAS line says so); after the
   three Oct 24 invitation briefs, Scout files and the list includes a wedding invitation and a
   bridal party invitation brief (opened competitor proof as always) so all five occasions
   (birthday, wedding, bridal shower, bridal party, baby shower) are live by Nov 15.
   MARKET PROOF GATE (Oct 23, 2026): a brief is built only if it names 3 opened Etsy
   listings (links, review counts as shown, at least one 100+) and our gap, as
   `../references/preflight.md` "Market" says. A brief without them goes back to status
   "proposed" with note "needs opened competitor proof" and the next brief takes its place.
2. For each chosen brief create products/<id> {title, briefId, lane -> kind, stage "building",
   summary, createdAt, source "Night Shift <day>"} and set the brief's status "built" and
   productId.
3. Choose now and save: product.style = {palette (gs palette for the pages), coverStyle (the
   PDF cover style: band / frame / split), pageFrame (rule / stripe / band / none), theme (a
   tools/fun_covers.py THEMES key, now only a palette name for the pages and pins), kit:"gm_kit_v4"} and
   product.coverLook = {tool:"atlas", scene (planner / clipboard / christmas / frame, by product
   kind: cover-styles.md Oct 24), crop (Lens fills it when it builds), labelPos, labelColour}.
   Rotation: the scene must differ from the last product built (etsy-v8.md section 1: never the
   same scene on two products back to back) and labelPos and labelColour from the last 3
   published products' coverLook, and no two products built tonight share a scene, palette,
   pageFrame or coverStyle.
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
| Variety | No product uses the Atlas scene of the last product built, or the label position + colour (coverLook) of the last 3 published |
| Missions | At most 1 new, status planned, with a numeric verify |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Products to build | products/<id> | stage building, style set |
| Missions | missions/<id> | spec shape |
| Run notes | `../output/<day key>-run.md` | "## Build list" |
