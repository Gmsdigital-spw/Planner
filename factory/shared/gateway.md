# The free GitHub gateway

Canonical home for the gateway protocol and every op shape. Make's free plan has only 1,000
operations a month, so Etsy, Pinterest, TikTok (gateway runs) and Alpaca go through here.
Load only the service section your stage names.

## Protocol (every service)
1. Write `gw/jobs/<job id>.json` = {"id":"<job id>","stopOnError":false,"ops":[...]}.
   Job id = `<prefix>-<day key>-<step>-<4 random hex>`; unique every time. Prefixes: bolt,
   mech, medic, warden, price, vpin, trade, lab, art, covers, audit.
2. Commit, `git pull --rebase`, push (see `repo.md`). The Action "Starship free gateway" runs the
   job and pushes `gw/out/<job id>.json` in about 30 to 90 seconds (uploads: up to 3 minutes).
3. Poll: `git fetch origin main` + `git show origin/main:gw/out/<job id>.json` every 10 s. Give up
   after 5 minutes (8 minutes for a job with uploads): record "gateway down" in the run log and
   the crew doc, do not retry anything else this run (Bolt's Etsy fallback below is the one
   exception), and tell Grayson one line only if the stage says so.
4. Result: {"ok","results":[{"i","op","tag","status","ok","data","error"}]}. data = the API's
   JSON answer with token-like fields hidden. Put independent calls in ONE job; dependent calls
   go in the next job.
5. If the result says a secret is missing or a service is not authorized: skip that check, note
   "the free gateway needs a look" for Grayson, never move the work to Make (Etsy fallback below
   is the one exception, for Bolt only).

## Etsy (shop_id 68605457; paths are after /v3/application)
- Read / write: {"op":"etsy","method":"GET|POST|PUT|PATCH|DELETE","path":"<path>","body":{...},"tag":"..."}.
  Authorization and the API key are added by the gateway.
- Upload from a public link: {"op":"etsy_upload","path":"/shops/68605457/listings/<listingId>/images",
  "fileUrl":"<public https URL>","field":"image","fileName":"<name>.jpg",
  "fields":{"rank":"<n>","alt_text":"<text>"},"tag":"..."}.
  PDF: path ".../listings/<listingId>/files", field "file", fields {"rank":"1","name":"<file name>"}.
- Download listing photos for inspection (Warden): {"op":"fetch_images","dir":"<name>","items":[{"name":
  "<listing_id>-r<rank:02d>-<listing_image_id>.jpg","url":<url_570xN>}]} (max 110 items per op) ->
  saved under gw/out/files/<dir>/ on the next gateway push.
- Delete a listing image (Warden only, duplicates and replaced covers): {"op":"etsy","method":
  "DELETE","path":"/shops/68605457/listings/<listingId>/images/<listing_image_id>"}.
- Common reads: `/shops/68605457/listings/active?limit=100&includes=Images`, `/shops/68605457`,
  `/shops/68605457/listings?state=draft&limit=100`, `/listings/<id>/inventory`,
  `/shops/68605457/listings/<id>/files`, `/shops/68605457/transactions?limit=100`.
- Bolt's fallback only: if the gateway gives no result in 5 minutes, or the result says a
  secret is missing or Etsy is not authorized, or an etsy_upload op fails with an error that
  is not Etsy rejecting the file itself, the same Etsy call may go through Make scenario 6676353 (mcp__Make__scenarios_run,
  responsive:true, data {action:"api", method, url, body}; uploads data {action:"uploadurl",
  url, fileData, fileName, fieldKey, rank, nameKey, nameValue}); Etsy's answer is in
  outputs.tool_output.body; at most 12 calls in a run, and the message to Grayson says the
  free gateway needs a look. Never Make for Pinterest.

## Zernio (Pinterest and TikTok)
- Post: {"op":"zernio","method":"POST","path":"/posts","idem":"<idem>","body":{...},"tag":"..."}.
  Read: {"op":"zernio","method":"GET","path":"/posts/<zernio post id>"}.
  Accounts: {"op":"zernio","method":"GET","path":"/accounts"} (needsReconnection / isActive).
- Pinterest body: {"content":<description, max 500 chars>,"mediaItems":[{"type":"image"|"video",
  "url":<public URL>}],"scheduledFor":<UTC ISO>,"platforms":[{"platform":"pinterest",
  "accountId":"6ad7b245350e86dff5e25133","platformSpecificData":{"boardId":<board id>,
  "title":<max 100 chars>,"link":"https://www.etsy.com/listing/<listingId>"}}]}.
  Idem: "pin-<pin id>" for still pins (retries "pin-<pin id>-r<n>"), "vpin-<day key>" for the
  video pin. 201 or 200 = created (post._id); 409 = duplicate (use existingPostId).
- Published check: the Pinterest platform entry's status "published" gives platformPostId and
  platformPostUrl; "failed" gives a reason. Analytics come back on the same GET when available.
- TikTok (Herald, through Make's zernio_api action, not a gateway push): body
  {"content":<caption + hashtags, under 2200 chars>,"mediaItems":[{"type":"video","url":<under
  4.5 MB>}],"publishNow":true,"platforms":[{"platform":"tiktok","accountId":
  "6ad7a7ecea18e081fb3894d2","platformSpecificData":{"tiktokSettings":{"privacy_level":
  "PUBLIC_TO_EVERYONE","allow_comment":true,"allow_duet":true,"allow_stitch":true,
  "content_preview_confirmed":true,"express_consent_given":true}}}]}.
- Board ids are in `accounts.md`.

## Alpaca (paper account; the gateway enforces every money rule)
- Reads: {"op":"alpaca","path":"/bankroll"} (the account as Grayson's $25: use THIS equity and
  cash for every decision, never the $100k paper balance); /clock; /positions;
  /orders?status=open; bars {"op":"alpaca","data":true,"path":"/stocks/bars?symbols=SPY,QQQ
  &timeframe=5Min&limit=78&feed=iex"}; snapshots {"op":"alpaca","data":true,
  "path":"/stocks/snapshots?symbols=...&feed=iex"}.
- Buy (close run and emergencies only; the autopilot trades during the day):
  {"op":"alpaca","method":"POST","path":"/orders","tag":"buy-<SYM>","body":{"symbol":"<SYM>",
  "notional":"<dollars>","side":"buy","type":"market","time_in_force":"day",
  "protect":{"stop_price":"<price>","take_profit":"<price>"}}}. The gateway refuses any buy
  with no stop, over 40% of cash, outside 8:35 AM to 2:45 PM Central, not a day order, or at or
  below the $20 floor. A refusal is final: log it, never work around it.
- Exits: DELETE /orders/<stop id> then POST a market sell for the held qty. Trail = cancel and
  place a higher stop (never lower). Flatten everything: DELETE /orders then DELETE /positions.
