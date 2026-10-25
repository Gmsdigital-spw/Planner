# How this lane talks to Etsy

## Writes and private reads: Make scenario "Brain Arcade gateway" (lane.json make.scenario_id)
- Uses ONLY the BrainArcadeGames Etsy connection (lane.json make.connection_id). Never scenario
  6676353 / 6676393, never connection 11776426 (GM's Etsy).
- The scenario itself refuses any url containing /shops/68605457 (a filter inside Make), on top of
  tools/shop_guard.py.
- Call: mcp__Make__scenarios_run {scenarioId, responsive:true, data:{action, url, method, body, ...}};
  Etsy's answer is in outputs.tool_output.body.
  - action "api": {url:"/v3/application/<path>", method, body (JSON string)}
  - action "upload": base64 file {url:".../listings/<id>/files" or ".../images", fieldKey:"file"|"image",
    fileName, fileData:<base64>, rank, nameKey:"name"|"alt_text", nameValue}. Used for the PDF so the
    product never sits on a public URL.
  - action "uploadurl": {url:".../listings/<id>/images", fileData:<public https image URL>, fieldKey:"image",
    fileName, rank, nameKey:"alt_text", nameValue}
- Ops: about 3 per api/upload call, 4 per uploadurl. One listing = create 3 + 5 photos + PDF 3 +
  activate 3 + verify 3 = about 27.

## Budget gate (before EVERY Make call or batch)
1. mcp__Make__organizations_get {organizationId: 9329352} -> unusedOperations, lastReset, nextReset.
2. Sum ops-ledger.jsonl rows since lastReset = lane_used.
3. STOP (no call) if unusedOperations - planned < keep_free_for_main_crew (200), or lane_used + planned
   > lane_max_per_cycle (150). Tell Grayson once a day: "Brain Arcade paused: Make free plan nearly used
   (N ops left till <nextReset>). Main shop protected. Upgrade Make or wait."
4. After the calls: append {"day","task","ops":<estimate>,"what"} to ops-ledger.jsonl.

## Public reads (views, favorites): the free GitHub gateway, GET only
- ONLY once factory/brain-arcade is merged into main (the gateway Action runs on main). Until then,
  read views/favorites through the Make scenario GET once a day (budget gate first).
- Job gw/jobs/ba-<day key>-<step>-<4 hex>.json, ops ONLY {"op":"etsy","method":"GET","path":
  "/shops/<BA shop id>/listings/active?limit=100"} or "/listings/<BA listing id>". Never POST/PUT/PATCH/
  DELETE, never any other shop. Protocol: ../../shared/gateway.md "Protocol". This costs no Make ops.
- Sales (receipts) are private: Make action "api" GET /v3/application/shops/<id>/receipts?limit=25
  once a day in ba-learn, only after the first listing is live.
