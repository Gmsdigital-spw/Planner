# Bolt publish steps (verbatim rules; shop_id 68605457)

a. Claim: update products/<id> with {stage:"publishing", etsy:{...existing etsy fields,
   claimedAt:now, claimedBy:"Bolt"}, updatedAt:now} using if_version.
b. Files: Artifact read the cover, every preview and the PDF (file.assetId). Check each image
   opens (python PIL) and is at least 1000 px on its long side; if any image is broken or tiny,
   or the PDF is missing or under 10 KB, stop this product (go to f).
   Copy the images to /home/claude/planner/listing-photos/auto/<product id>/<n>.jpg (convert
   PNG to JPG quality 88, long side at most 2400 px; n = 1 for the cover, then 2.. for
   previews in order). Copy the PDF to /home/claude/planner/dl-temp/<16 random hex chars>/
   <slug of the title, max 60 chars>.pdf. Commit and push both together. Wait until every raw
   URL answers 200 (curl -sI, retry every 15 s, give up after 3 minutes and go to f).
c. Create the draft ONLY if the product has no etsy.listingId: gateway etsy op POST
   /shops/68605457/listings with body {quantity:999, title:copy.title, description:
   copy.description, price:Number(copy.price), who_made:"i_did", when_made:"2020_2026",
   taxonomy_id: 1350 if the title or category mentions game, party, santa, trivia, bingo or
   exchange, else 354, type:"download", tags:copy.tags first 13, materials:["Digital
   download","PDF"], is_supply:false, should_auto_renew:true}. Save etsy {listingId,
   state:"draft", createdAt, images:0, file:false, claimedAt, claimedBy:"Bolt"} to the product
   IMMEDIATELY (if_version) so a crash can resume instead of making a duplicate.
d. Photos and PDF: job 1 = GET /listings/<listingId>/images and GET /shops/68605457/listings/
   <listingId>/files (one job). Job 2 = an etsy_upload op for every image n not yet on the
   listing (rank n missing; fileName "<slug>-<n>.jpg"; fields {"rank":"<n>","alt_text": a
   plain description; for the cover use copy.title cut to 250 chars}) plus, if no file is there
   yet, the PDF etsy_upload (field "file", fields {"rank":"1","name":<pdf file name>}). After
   job 2, update etsy.images and etsy.file from the results. Any failed upload: retry it once
   in a new job; if it fails again go to f.
e. Verify, then publish: one gateway job with GET /listings/<listingId>?includes=Images and
   GET /shops/68605457/listings/<listingId>/files; check images count >= 1 + previews count,
   at least one file, and a title. Only then a second job: PATCH /shops/68605457/listings/
   <listingId> body {"state":"active"}. Require the answer's state "active". Then:
   - update products/<id> {stage:"published", publishedAt:now, updatedAt:now, etsy:{listingId,
     state:"active", url (from Etsy, else https://www.etsy.com/listing/<id>), images,
     file:true, publishedAt:now, publishedBy:"Bolt (cloud autopilot)"}} (drop claimedAt);
   - append to spend/<month key>.entries {date:now, listing:product title, kind:"listing",
     cost:0.2, listingId, by:"Bolt"} (read first; create {month, entries:[]} if missing; skip
     if an entry with that listingId exists; keep the newest 500);
   - set link = the listing url on every pins doc with productId == this product and no link;
   - if every product in a batch (batches collection, productIds) is now published or active,
     update that batch {status:"published", publishedAt:now};
   - delete the dl-temp/<random>/ folder for this product, commit and push ("remove temp
     download"). Keep the listing photos.
f. On any failure: update the product {stage:"batched", updatedAt:now, etsy:{...keep
   listingId/images/file, lastError:{at:now, code, message (Etsy's words, under 300 chars),
   step, by:"Bolt"}}} (drop claimedAt) so the next run resumes the same draft. Delete its
   dl-temp folder if you made one. Never publish a listing that failed a check.

Fallback (shared/gateway.md "Etsy", Bolt only): Make scenario 6676353 for the same Etsy call,
at most 12 calls in a run, and the message to Grayson says the free gateway needs a look.
Never Make for Pinterest.
