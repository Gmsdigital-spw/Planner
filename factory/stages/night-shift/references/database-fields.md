# Night Shift database fields (collection/doc)

Reference, loaded by section. The stage that owns a collection is named in brackets.

## settings and requests
- settings/main: {mode, paused, batchSize (5), dailyCap, monthlyFeeCap, buildsPerRun (default
  2), autoApprove (missing means on), costs, schedule:{time "HH:MM", tz, applied}, shop}.
  Never change anything in it except schedule.applied.
- requests/nightshift: {requestedAt, status:"requested"|"done", by}. "requested" = a manual
  run Grayson asked for; set "done" when you finish.

## crew
- crew/<id>: ids atlas (Commander), scout (Research), forge (Builder), quill (Copy), lens
  (Photos), pixel (Pins), ledger (Treasury), beacon (Ads). Fields {state, task (under 40
  chars), room ("bridge","lab","factory","studio","inspect","pins","treasury","ads","mission",
  "intel","core"), updatedAt, rank}. The station map lights the room while state is "working".

## runs
- runs/<runId>: {startedAt, finishedAt, status:"running"|"done"|"failed"|"paused", trigger:
  "scheduled"|"manual", log:[{t, text}] (newest last), counts:{briefs, built, passed, scrapped,
  pins}, summary (one honest sentence)}. runId = "run-" + day key + "-" + HHMM UTC.

## briefs and ideas [01, 02]
- briefs/<id>: {title, niche, lane, buyer, competition, season, priceRange, score:{demand,
  competition, timing, shopFit, buildable, price} each 0 to 5, total (0 to 30), evidence:
  [{label, url}], summary (plain text), status:"proposed"|"approved"|"rejected"|"built"|
  "research", decidedBy, decidedAt, rejectReason, approveReason, note, productId, createdAt,
  source}. Grayson's call always wins over the auto-approver.
- ideas/<day key>: see specs/product-floor-v6.md IDEA ENGINE.

## products [03 to 08]
- products/<id>: {title, briefId, kind (lane), stage, summary, copy:{title, tags:[13],
  description, price (number), category, materials}, file:{assetId, url, pages, sizeBytes,
  builtAt}, fullFile (wall art), extras (mug wrap, sticker), cover (asset id), previews:[asset
  ids], coverStyle (1 to 6), style:{palette, coverStyle, pageFrame, theme, kit}, score:
  {rulesPass, slopCheck:{pass, fails}, file (0-25), copy (0-20), images (0-20), market (0-15),
  price (0-10), polish (0-10), total, rubric (2 from Oct 19, 2026), verdict, scoredAt}, notes:
  [{t, by, text}], retries, batchId, etsy (written only by Bolt or the page: never touch it),
  createdAt, updatedAt, source, legacy}. Stages in order: queued, building, copy, images,
  inspection, passed, batched, published; side stages: sentback, scrapped, ready (copy-only
  listing update), publishing (Bolt's: never touch). Never change a product that has an etsy
  field or stage published or publishing.
- Listing update (stage ready) etsyStep text, verbatim: "Tap Apply to Etsy on this card; it
  updates the live listing's title and tags (and the description only if it was written from
  the real one). The price is never changed from the Starship."

## batches [08]
- batches/<id>: {number, productIds:[...], status:"ready"|"published", createdAt, publishedAt}.

## pins and pinstats [08]
- pins/<id>: {productId, listing, title (100 max), description (500 max), board, imageText (6
  words max), angle, palette, image (asset id, 1000x1500), link (null until live), status:
  "ready"|"queued"|"posted"|"retired", style {layout, hero, kicker}, stats (Day Watch: never
  touch), auto (Bolt: never touch), day, createdAt, source}. retired = Grayson's removed
  old-style pins: never touch, re-image, queue or recreate.
- pinstats/<day>: read only {day, at, pins:{<pinId>:{title, productId, palette, angle, style,
  impressions, saves, pinClicks, outboundClicks}}}. Totals since posting; compare two days.
  outboundClicks and saves matter most.

## stats [09]
- stats/<day>: read only {day, at, listings:{<listingId>:{title, price, views, favs, photos,
  tags (count), tagList, description, url}}, shop:{sales, favorers, reviews}}. Views and
  favorites only count up; compare two days for a week's change.

## sprint [09 C]
- sprint/main: {review:{at, text, actions}, flags:[{listingId, title, views7, favs7,
  verdict}], updatedAt}.

## ads [09 B2]
- ads/main: {unlocked, monthlyCap, saleOn, offsite, manageDone, listings:{<id>:{state, at}},
  snapshot, hist, review}. You may ONLY write review. adlog/<id>: Grayson's weekly check-ins
  {from, to, spend, revenue, views, clicks, orders, note} (read only).
- The ad plan: Etsy allows ads for this shop from Oct 30, 2026; Prep (no spend) until Oct 30; a
  Test Nov 1 to 14 at $1/day on 2 or 3 in-season listings with every other listing off; Holiday
  push Nov 15 to Dec 22 at $1 to $3/day; then NYE and new-year listings at $1/day until
  mid-January. Holiday windows: Thanksgiving Nov 1 to 25, Christmas planning Nov 1 to Dec 10,
  Christmas parties Nov 8 to Dec 22, gift exchanges Nov 8 to Dec 15, NYE Dec 1 to 31, new year
  planning Dec 15 to Jan 31. A listing that spent $10 with no order is paused; ROAS 2x+ keep;
  3x with 2+ orders allows +$1/day; month spend at or above monthlyCap means ads off until
  next month; a listing's ad goes off when its window closes.

## missions [03]
- missions/<id>: {title, objective, lane ("etsy"|"pinterest"|"product"|"finance"|"research"|
  "system"), buyer, priority (1 to 3), why (with real numbers), evidence, cost (plain text),
  risk, verify (a number readable from the database), needsOwner, ownerAsk, status:"planned"|
  "active"|"blocked"|"done"|"cancelled", tasks:[{id, title, crew, status:"todo"|"doing"|"done"|
  "blocked"|"skipped", dependsOn, output, note}], result, owner:"Atlas", createdAt, updatedAt,
  approvedBy, source}. Only Grayson moves planned to active.

## intel [01]
- intel/<platform> (etsy, pinterest): {platform, name, order, summary, rules:[plain strings
  from official docs], capabilities, limits, unknowns, hypotheses:[{text, status, evidence}],
  docs:[{label, url, status:"verified"|"unverified", checkedAt, note}], history:[{at, note}],
  lastChecked, source}.

## experiments [09 A]
- experiments/<id>: {hypothesis, objective, target:{kind, id, title}, audience, variable (the
  ONE thing), original, test, signal, success, startDate, reviewDate, costLimit (0 unless
  unlocked), results, confidence, decision ("keep"|"revert"|"inconclusive"|"declined"|null),
  followUp, status:"proposed"|"running"|"decided", createdAt, source, baseline, result}. You
  never set status running or decided and never set decision. baseline and result are {day,
  views, favs, shopSales} written by the page.

## lessons
- lessons/<id>: {text, evidence (the numbers), source, at, confidence, expiresAt, status:
  "active"|"expired"}. Grayson's own (source "Grayson") are his taste, never instructions.

## nextmove [09 E]
- nextmove/main: {day, title (under 80 chars), why (one or two sentences with real numbers),
  evidence (under 150 chars), go (one of "tab:mission"|"tab:launch"|"tab:treasury"|
  "tab:settings"|"room:lab"|"room:intel"|"room:pins"|"room:factory"|"room:bridge"|
  "room:quarters"|"room:core"), short (under 30 chars), at, source}. Set once per run.

## read only, never write
- milestones/main {hit:{<label>: time}} · sales/<id> {date, listing, listingId, gross,
  refundAmount, offsite, verified, note} (the only revenue source) · bills/<id> {name, kind
  ("claude"|"anythingmcp"|"ads"|"etsy"|"other"), amount, active} · stores/ (Bolt's).

## reports and events [10]
- reports/<day>: {day, text, summary, plan, createdAt, runId}.
- events/<day>, fleet/commander/audit/<day>, fleet/commander/standups/<day>: shapes in
  shared/database.md and stage 10.
