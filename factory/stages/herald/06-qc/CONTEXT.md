# 06 Quality control (Atlas grades, not Herald)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/qc.md` | Full file | Slop gate, score, statuses |
| Previous stages | the videos and the four docs | | What to grade |

## Process
1. Slop gate first (qc.md A): extract 6 frames and Read every one plus the cover; a FAIL means
   fix and rebuild once (back to stage 04 for that product), then re-gate; a second FAIL sets
   every doc of today to "qc_failed", writes a lesson, and tells Grayson in one line.
2. Grade (qc.md B) only after the gate passes: points and one line of evidence per criterion
   (accuracy /25, fit /20, platform /15, hook_cta /10, visual /10, search_link /10, compliance /10),
   then decide with the tool, never by hand: `python3 factory/learning/learn.py score --scope shop
   --agent herald --rubric herald-post-v6 --channel <instagram|facebook|youtube_shop|tiktok>
   --copy '{"caption":"...","link":"<the Etsy URL>","title":"<YouTube title or empty>"}'
   --slop-gate <pass|fail> --facts-checked <true|false> --ratings ratings.json --job <day key>:<idem>`.
   It checks caption limits, the Etsy link, AI phrases, brands, invented claims, combines on the
   frozen post rubric (pass = signal/main.passScore, 92) and prints PASS/FAIL with the blockers.
   Below the bar: one rewrite, then score again with the same --job (the tool numbers the attempt;
   two repairs is the bound), then "qc_failed" with notes. Save qc {scores (the points), notes,
   slopGate, evaluation: the tool's recorded id}.
3. Create each social/<idem> in the database now (query the idem first; never a second doc
   with the same idem) with status "awaiting_approval" or "approved" per qc.md (or
   "qc_failed") and qc {scores, notes, slopGate}.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Graded docs | social/<idem> (created here) | status + qc |
