# Listing fixes: titles and tags on the best live listings (V8, Oct 24, 2026)

Grayson's V8 order: "Fix titles and tags on the best existing listings before adding more weak ones"
(specs/etsy-v8.md section 5). That is his go for TITLE and TAG edits on existing listings only. Price,
photos, description, category, state and deactivation stay on the "needs Grayson's go" list.

## When
The first Bolt run of the day (7:13 AM Central), in stage 02 BEFORE any new listing is published.
Dry run: list what would be applied, apply nothing.

## Steps (at most 2 fixes a day)
1. Read listing_fixes docs with status "ready" (database.md "listing_fixes"), oldest first. None = skip.
2. For each of the first 2: one gateway job with GET /listings/<listingId> (confirm it is live and
   that its current title equals title_before; if not, status "stale" with a note and skip it).
3. PATCH /shops/68605457/listings/<listingId> body {"title": title_after, "tags": tags_after}
   (13 tags, each 20 characters max, title 140 max; verify the limits in Python before the call).
4. GET the listing again; title and tags must equal the fix. Then update the doc {status:"applied",
   appliedAt:now, by:"Bolt", result:{title, tags}} with if_version, and append to products/<id>.notes
   (the product whose etsy.listingId matches, if one exists) {t:now, by:"Bolt", text:"title/tags fixed:
   <title_before> -> <title_after>"}.
5. A refused PATCH: {status:"failed", error:{at, code, message under 300 chars}}; no retry today; a
   lesson per bolt/CONTEXT.md "Learning" if the error is not a daily limit.
6. Log one line in the run notes and the run-log note: "fixes applied N (ids), failed M".

## Never
Change anything but title and tags; touch a listing fixed in the last 14 days; apply more than 2 a day;
apply a fix whose before-values no longer match the live listing; invent a title that promises a sale,
review or result.
