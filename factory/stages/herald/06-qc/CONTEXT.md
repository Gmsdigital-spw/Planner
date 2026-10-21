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
2. Score (qc.md B) only after the gate passes. Pass = signal/main.passScore (92). Below it: one
   rewrite, then "qc_failed" with notes.
3. Create each social/<idem> in the database now (query the idem first; never a second doc
   with the same idem) with status "awaiting_approval" or "approved" per qc.md (or
   "qc_failed") and qc {scores, notes, slopGate}.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Graded docs | social/<idem> (created here) | status + qc |
