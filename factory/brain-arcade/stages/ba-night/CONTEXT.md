# ba-night: research, build, check (daily 3:22 AM Central)

Goal: by morning, up to 2 products PASSED (92+, answer key PASS) and ready for the publisher,
plus fresh niche knowledge. Never more than 2 builds a night. Season first (lane.json season_order,
knowledge/seasons.md "Live by").

## Inputs
| What | Where |
|---|---|
| Lane rules | ../../CLAUDE.md, ../../lane.json, ../../LESSONS.md, ../../notebook.md |
| Build order | ../../products/queue.json |
| Skills acting tonight | ../../skills/{joystick,compass,domino,crayon,chalk,penny,ruler}/SKILL.md |
| Rubric + slop check | references/rubric-ba.md |
| Knowledge | ../../knowledge/*.md (only the files the step names) |

## Process
0. Joystick: grade each agent's last prediction; status doc "working" (ops/room.md).
1. Compass (max 20 minutes, WebSearch/WebFetch): for tonight's product type + grade + season, open 2+ Etsy
   item pages with 100+ ITEM reviews; fill knowledge/competitors.md, prices.md, tags.md, complaints.md
   with dated, sourced lines. No proof found = do not build that idea; take the next queue item.
2. Joystick picks: (a) a product stuck in "inspection" from last night, (b) the next "queued" queue item
   in season, (c) a new idea from Compass with proof. Bundle only after all its parts are live.
3. Domino writes spec.json (structured math) and Chalk writes listing.json, then ONE command:
   `python3 tools/pipeline.py <slug>` (build + answer key + photos + copy + duplicate guard + QA sheet).
   Use the separate tools below only to fix whatever the pipeline reports.
   Domino builds alone: `python3 tools/games.py products/<slug>/spec.json /tmp/ba/<slug>`.
   Missing builder for the type = add build_<type>() + checker rules in the same run (bug rule), test
   on this product AND re-run the escape room so nothing else broke.
4. Crayon: photos come from the REAL PDF pages. Covers rotate between layouts (tools/photos.py LAYOUTS):
   "clipboard" (the page on Grayson's clipboard photo scene, assets/atlas-pack, with one label card),
   "fanned" (real pages fanned on the bold theme colour), "christmas" (the holiday-table scene, Nov 1 -
   Dec 25 only). Never the same layout as the lane's last 3 covers; the pipeline picks it. Never drawn
   hands, rooms, 3D stickers, emoji, badges or AI-generated pictures. Side-by-side + 300 px test on
   qa-sheet.png.
5. Chalk: products/<slug>/listing.json (limits checked by code). If Grayson's starter doc is linked in
   queue.json doc_link, use HIS title/tags/description/price for the starter items.
6. Penny: price with evidence (knowledge/prices.md).
7. Ruler: answer_check PASS (else FAIL, no score) -> slop check -> six scores -> up to 3 fix rounds.
   92+ = queue status "passed"; under 92 = "inspection" with the exact next fixes; retries 4 = "scrapped".
   One line per scored product in scores.jsonl {"d","agent":"ruler","item","score","answerKey":"PASS"}.
8. Notes: `tools/ba_log.py note` for every build, score, idea, error and fix. Joystick writes each acting
   agent's "What I've learned" line (number + change + prediction).
9. Commit + push (never a PDF). Run-log line. Status doc. Notify Grayson only if something failed or
   needs him.
