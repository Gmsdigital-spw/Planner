# 03 Schedule pins on Pinterest (through Zernio, free; the Make poster stays off)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/gateway.md` | "Protocol", "Zernio" | Op shapes, idem, 409 handling |
| Shared | `../../../shared/accounts.md` | "Pinterest" | Board ids by keyword; the 6 daily slots |
| Reference | `../references/pin-rules.md` | Full file | Selection, order, spread, due dates |
| Database | pins (via out_dir + script: id, productId, status, link, image, auto, style, day, title) | | What to confirm and schedule |
| Previous stage | the active list on disk + anything published this run | listing ids | Only pins for ACTIVE listings |

## Process
1. Confirm earlier pins: pins with status "queued" and auto.zernioPostId whose auto.due is in
   the past: one gateway job (prefix bolt, step "pinchk") with a zernio GET /posts/<id> per pin
   (max 25). Pinterest platform status "published" -> update the pin {status:"posted",
   postedAt:<publishedAt or now>, pinterestId:<platformPostId>, auto:{...existing,
   postUrl:<platformPostUrl>}}. "failed" -> update {auto:{...existing, error:<reason, under
   300 chars>}}, leave it queued, count it for the message.
2. New pins to schedule (6 a day, varied looks): follow pin-rules.md for selection (at most 18
   per run), order, spread, image hosting, due slots and boards.
3. One gateway job (step "pins") with one zernio POST /posts op per pin (idem "pin-<pin id>",
   body shape in gateway.md "Pinterest body", content = the pin description max 500 chars,
   title max 100 chars, link = the listing link). On 201 or 200 update pins/<id>
   {status:"queued", auto:{imageUrl, zernioPostId:<post._id>, via:"zernio", queuedAt:now,
   due, board:<board id>}}. A 409 duplicate: store existingPostId as zernioPostId the same way.
4. Count: confirmed, failed, newly queued, for stage 04.

## Audit

| Check | Pass condition |
|-------|---------------|
| Active only | Every scheduled pin links to an ACTIVE listing |
| Spread | No date over 6 pins; no two pins of one product on a date; no two same-style pins back to back |
| Images | Every imageUrl answered 200 before the POST |
| Retired untouched | No pin with status retired was read into the schedule |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Scheduled pins | pins/<id> | status queued, auto {...} |
| Confirmed pins | pins/<id> | status posted |
