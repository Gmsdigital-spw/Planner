# Criterion anchors: Inspection rubric 2 (Atlas, Night Shift stage 07)

For the reviewer (a FRESH worker that did not build the item). Grade each criterion in points with one line
of evidence you can point at (a page, a photo, a URL, a measured number). Do not look up or aim for a pass
mark: `python3 factory/learning/learn.py score` combines the points, applies the rubric's caps and decides.

## file (0 to 25)
- 25: every page full and framed, nothing within 0.25 in of a box edge, every answer key / uniqueness claim verified by code, fillable fields typed to max length and rendered clean, page count inside the lane range with the thank-you page last, no spoiler on a host-facing page.
- 22-23: one or two of: a page with an empty band over ~15% at the bottom, a footer or signature touching its box, a field that clips at max length, a cover page with an empty band (Oct 23: bingo 23, word search 23, Santa Mail 23, murder mystery 22).
- 18-20: a layout fault on several pages, a key not verified, or filler / repeated content on a page.
- under 18: the file is incomplete, does not open, or breaks the lane's file rules.

## copy (0 to 20)
- 20: title opens with a phrase shoppers really type (autocomplete checked and recorded), 13 real search-phrase tags, description opens with what it is and who it is for, an exact page list with counts, how to print/edit, the AI line last, no AI phrases, no em-dash runs.
- 18-19: one of: autocomplete not checked (phrase taken from a search page), a generic opening line, a tag that only describes one page, a claim the file does not back (Oct 23: 18, 18, 18, 19).
- 15-17: generic description without the page list, keyword soup, or a title that does not lead with the buyer phrase.
- under 15: a limit broken (title, tags, description) or an invented claim.

## images (0 to 20)
- 20: cover in a layout family not on the last 5 covers, real pages the biggest thing (about 40%+ of the centred square), title and count readable at 300 px, photos 2-5 each show something different with pages filling the frame, text inside x 260-1740.
- 17-19: photos 2-5 a little small or one repeats the cover's page; cover hero around 38-41% of the square (Oct 23: 17, 18, 18, 19).
- 14 at most: title or count not readable at 300 px, or overlap / clipped text / cramped spacing / a cheap-looking cover (rubric rule).
- 12 at most: the slop check failed on any line (rubric rule).

## market (0 to 15)
- 15: three opened Etsy item pages with 100+ item reviews each, prices and contents recorded, and one plain line naming the gap that is visible in our file, photos and copy.
- 13-14: two 100+ review rivals opened and a written gap (Oct 23 Santa Mail 13: the only no-Canva PDF rival had 58 reviews).
- 11-12: one 100+ rival or only search cards; the gap is asserted, not visible (Oct 23: bingo 11, murder mystery 11).
- 9-10: no opened 100+ review rival, non-Etsy links, a 'free everywhere' lane (Oct 23 word search 9).

## price (0 to 10)
- 10: inside the lane range, justified in one line against the three opened rivals' prices and contents.
- 8-9: inside the range but justified against fewer rivals or a thinner comparison (Oct 23: 8, 8, 9, 9).
- under 8: outside the lane range, or no justification at all.

## polish (0 to 10)
- 10: one font family and palette across every page, same margins everywhere, no cramped or half-empty page, cover and photos consistent with the pages.
- 8-9: one small inconsistency (a margin, a weight, one slightly tight block) (Oct 23: 8, 9, 9).
- 7 at most: any layout fault or a cheap-looking cover (rubric rule). 6 at most: the slop check failed.

## What the code checks on its own (you do not need to re-measure these)
File exists and is a real PDF; page count; thank-you page last; cover + 4 previews at 2000 px wide; no repeated photo;
cover title inside the centred square (edge-ink proxy); bold colour share; empty band at the bottom of a preview;
title / tags / description limits; the AI line last; AI phrases; em-dash runs; brand names; revenue claims; price
inside the lane range; market evidence present (opened item pages with review counts). Each check writes its
result next to your rating; a critical failure blocks acceptance whatever the total.

