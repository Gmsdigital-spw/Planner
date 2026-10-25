# ba-publish: put PASSED products live on BrainArcadeGames (9:17 AM and 3:17 PM Central)

Golden rule (copied from Bolt): a listing never goes live unless ALL its photos and its PDF are on
Etsy. Max 2 new listings a day (count today's rows in listings.jsonl). Never a product that is not
"passed" in products/queue.json.

## Gates (stop at the first that fails; write why in the run log and the status doc)
1. lane.json paused -> stop.
2. Connection. If lane.json make.connection_id is null: list Make connections (team 3216895, type etsy);
   a NEW Etsy connection other than 11776426 = candidate. None -> outcome "waiting", needsYou
   "Tap the Brain Arcade Etsy link (lane.json make.credential_request_link)"; tell Grayson at most once
   a day. Do not create or change Make scenarios yourself: if scenario_id is null, needsYou
   "Brain Arcade Make scenario not built yet (open the Brain Arcade chat and say: build the scenario)".
3. Verify the shop (once): via the scenario GET /v3/application/users/me then /users/<user_id>/shops;
   save both answers; `python3 tools/shop_guard.py verify-connection me.json shops.json`.
   BLOCKED = tell Grayson NOW (it is GM's shop or the wrong account); nothing else runs.
   VERIFIED = write shop_id and verified_at into lane.json, commit.
4. Budget gate (ops/gateway.md).

## Publish one product (repeat for a second only if the cap and budget allow)
1. `python3 tools/shop_guard.py check-dupe products/<slug>/listing.json` (BLOCKED = alert, skip product).
2. Rebuild the PDF from spec.json into /tmp and re-run answer_check: must PASS.
3. Photos must exist in the pushed repo: curl -sI the raw URLs
   (https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/factory/brain-arcade/products/<slug>/photos/<f>) = 200.
4. taxonomy_id null -> GET /v3/application/seller-taxonomy/nodes once, pick the closest node for
   printable educational games (record id + path in listing.json and knowledge/README if new).
5. EVERY write below: `tools/shop_guard.py check-call --method <M> --url <url> [--creating <id>]` first.
   a. POST /v3/application/shops/<id>/listings (createDraftListing): quantity 999, title, description,
      price, who_made, when_made, taxonomy_id, tags, materials, type "download", is_supply false,
      should_auto_renew true. Save listing_id.
   b. 5 photos, ranks 1-5, with alt text (uploadurl).
   c. The PDF (upload, base64, fieldKey "file", nameKey "name", name = listing.json file_name).
   d. GET the listing's images and files: exactly 5 images and 1 file, else STOP (leave it as a draft,
      tell Grayson in one line).
   e. PATCH /v3/application/shops/<id>/listings/<listing_id> {"state":"active"}.
6. Append listings.jsonl {day, product_id, listing_id, title, state:"active", price, url}; queue.json
   status "live"; `tools/ba_log.py note --kind listing`; ops-ledger row; one Pinball pin plan
   (only if lane.json pinterest.status is "approved").
7. Tell Grayson in one line when a listing goes live (with its Etsy link). Run log + status doc.

Any Etsy error: record the exact words, tell Grayson if it stopped a listing, never retry more than once.
