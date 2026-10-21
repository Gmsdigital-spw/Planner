# Misses — problems found that the crew did NOT catch
The Warden reads this at the start of every run. Every line = a problem someone else spotted first,
plus the check added so it never slips through again. Newest last. Never delete a line.

| Date | Found by | What was wrong | Why we missed it | Check added |
|---|---|---|---|---|
| 2026-10-21 | Grayson | 18 listings had two covers in a row | A cover refresh uploaded new covers at #1 and never deleted the old ones; Warden only checked brightness | listing_audit.py TWO_COVERS (more than one 2000x1500 image); rule: upload + delete old = one fix |
| 2026-10-21 | Grayson | Same photo twice (Pink Christmas "Glory to God", No-Buy "What's Inside") | Nobody compared photos to each other | listing_audit.py DUP_PHOTO (picture fingerprint) |
| 2026-10-21 | Grayson | Covers bland and beige, "like it's for college professors"; no cookies on the cookie swap, no Santa on Secret Santa | Old spec said warm cream desk; nobody checked color or theme | listing_audit.py BLAND_COVER (needs 30%+ bold color); covers now built with tools/fun_covers.py; eyes-on contact sheet check for themed art |
| 2026-10-21 | Grayson | A cover on a listing it had nothing to do with | Warden never looked at the pictures | listing_audit.py COVER_MISMATCH (alt vs title words) + Warden must Read the contact sheet every run |
