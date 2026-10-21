# 01 Post what is due (first thing every run)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/posting-lane.md` | "Posting lane", "Posting what is due" | Actions and the rules |
| Shared | `../../../shared/gateway.md` | "Zernio" (TikTok body only) | The TikTok body |
| Database | social (status approved or queued, due <= now, no postId), signal/main | | What to post |

## Process
Skip when signal/main.live is false or firstApprovedAt is null.
1. For each due doc whose channel is connected and not paused and whose qc.slopGate is
   "pass": set status "queued" (if_version), call the matching action, record postId and
   postUrl, status "posted" (postedAt now) only when an id came back. On error: check the
   Make executions, retry once after 60 s, then status "failed" with error (under 300 chars).
2. One failed channel never stops the others. Max one post per channel per day. A doc with a
   postId is never posted again.

## Audit

| Check | Pass condition |
|-------|---------------|
| No duplicates | Every doc posted had no postId before and a unique idem |
| Gate | Every doc posted had qc.slopGate pass |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Posted docs | social/<id> | status posted / failed |
