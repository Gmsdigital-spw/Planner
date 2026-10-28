# Pre-flight: check BEFORE inspection (added Oct 23, 2026)

Why: the last 5 builds failed at 85, 73, 75, 83 and 85, every time for the same few faults
(Grayson, Oct 23: "make them stronger so this doesn't happen"). The Builder runs every line
below on its own product and fixes what fails BEFORE setting stage "inspection". Inspect
(07) uses the same list for its fix rounds. Each line names the fault that cost points.

## Market (lost 3 to 6 points every time)
- [ ] The brief or product notes list 3 Etsy listings that were actually OPENED, each with a
      link, its review count as shown, price, and what it includes. At least 1 with 100+
      reviews. No opened evidence = no build (03 sends the brief back to Scout).
- [ ] One plain line says our gap against those 3 (more items, bigger print, editable with
      no Canva account, lower price for more, a format they lack). The gap is real and visible
      in our file, photos and copy.
- [ ] Avoid crowded "free everywhere" lanes (word search, plain coloring pages) unless the
      gap is strong; they cap market at about 9.

## File (lost 1 to 3)
- [ ] Content pages inside the lane's range (6 to 16 for most lanes) planned BEFORE drawing;
      thank-you page last.
- [ ] Every page full and framed: no empty band over about 15% of the page height at the
      bottom, nothing touching a box edge (at least 0.25 in inside every box), signatures and
      footers inside their boxes.
- [ ] Every answer key and uniqueness claim checked by code; fillable fields tested by filling
      them and rendering the page.
- [ ] Render EVERY page to PNG and look at a contact sheet (Read it) before going on.

## Images (lost 3 to 9)
- [ ] Cover: layout family not on the last 5 covers; title (and count badge, if any) fully inside the square, nothing clipped, readable at 300 px
      (save gs.thumb_check and Read it). Real pages are the biggest thing, about 40%+ of the
      square.
- [ ] Cover theme + art differ from the last 3 published (read their coverLook).
- [ ] Photos 2 to 5: the real pages fill most of the frame width (no small page floating in
      empty space); each photo shows something different (inside pages, the key or extras,
      a "what's included" grid, the how-to). Text inside x 260 to 1740.

## Copy (lost 2 to 4)
- [ ] Title leads with the phrase shoppers type (checked with WebSearch; autocompleteChecked
      true only when really checked), 140 characters max, then count, then buyer/occasion.
- [ ] Description: first line says what it is and who it is for; exact page list with counts;
      how to print/edit; no AI phrases (elevate, unlock, seamless, dive into, whether you're),
      no em-dash runs; the AI line last exactly as rules.md says.
- [ ] 13 real tags, no duplicates, 20 characters max each.

## Price and polish (lost 1 to 3)
- [ ] Price inside the lane range and justified in one line against the 3 opened listings.
- [ ] One font family and palette across all pages; same margins on every page.

## Faults that cost points on Oct 23, 2026 (check every one)
- [ ] Spoilers: a game's host guide, photos or copy never name the answer or culprit (Murder Mystery lost file points).
- [ ] Photos and copy only claim what the file really has (a photo said "US Letter + A4", the PDF was Letter only).
- [ ] No photo repeats a page the cover already shows.
- [ ] Fillable fields auto-size: type the longest real name/line into every field and render it; nothing clips at max length.
- [ ] Cover hero crop never cuts a page's footer or edge text.
- [ ] Search phrase checked for real (Oct 28, 2026): suggest/autocomplete is blocked in night runs, so
      the check is Etsy's own search through the free gateway: GET /listings/active?keywords=<phrase>
      &sort_on=score&limit=25 and the phrase must appear in the titles of 3+ of the top 25 results,
      or an Etsy market page (etsy.com/market/<phrase>) opened this run. Name it in "## Copy". This
      counts as checked; a blocked autocomplete is never a fail by itself, and no copy point is
      taken for it. An unverified phrase still loses the point.

## Proven by the passes (copy what scored 19/20)
- Photo 2: the 6 most important pages in a 3x2 grid, each about 470 px wide, with a short headline. Never 8 small pages.
- Photo 4: 3 real pages fanned big, not one small page in empty space. Photo 5: centered, no empty band over about 15%.
- Gap visible everywhere: the one thing we beat rivals on is on the cover, photo 2, the title and the description's first line.

## Fresh eyes (last step before stage "inspection")
Start ONE fresh worker (Agent tool, general-purpose) that did not build the product. Give it only
the contact sheet of every page, the 5 photos, the title and description. Its job: list every fault
a picky buyer or a top seller would spot (spoilers, clipping, half-empty space, claims the file
doesn't back, typos, anything that looks AI-made). It does not score. Fix every fault it lists,
then hand to 07. Faults found here cost nothing; faults found by 07 cost points and a whole night.

If a line cannot be fixed (a tool bug outside your write paths), fix what you can, say which
line failed in the run notes, and still hand over: 07 decides.
