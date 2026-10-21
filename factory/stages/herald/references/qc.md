# Quality control (stage 06; Atlas grades, not Herald)

## A. Slop gate (pass/fail, before any score)
Extract 6 frames spread across the video and Read every one, plus the cover. FAIL if ANY
frame: shows a flat solid-colour card or template slide instead of real pages on the desk;
reuses an Etsy listing or preview image; has text cut off, overlapping the page title, or
unreadable at phone size; has more than 3 caption lines; looks like generic AI art (fake
hands, warped text, plastic people); or if the audio is silent (volumedetect mean_volume below
-30 dB). Ask honestly: "Would a top Etsy seller post this?" If not, FAIL. On FAIL: fix and
rebuild once, re-run the gate; a second FAIL = status "qc_failed" for all of today's docs, a
lesson, and one line to Grayson. Write qc.slopGate "pass" or "fail" plus which frame failed.
(A Spot commercial's cartoon scenes are allowed in the skit part: judge them on consistent
characters, no garbled faces or text; the pages tail still has to be real pages on the desk.)

## B. Score (only after the gate passes), out of 100
Factual accuracy 25, product and audience fit 20, platform-native quality 15, hook and call
to action 10, visual clarity 10, search and link relevance 10, compliance and rights 10. A
wrong fact, broken or non-Etsy link, invented claim or anything against platform rules is an
automatic fail. Pass = signal/main.passScore (92). Below it: one rewrite, then drop it
(status "qc_failed" with notes). Never approve your own work without this check.

## Status after passing
"awaiting_approval" if signal/main.firstApprovedAt is null; "approved" if firstApprovedAt is
set and autoApprove is true. Save each as social/<id> (id = idem).
