# Accounts and ids

Canonical home for every id a crew needs. No secrets here, ever; the gateway and Make hold
credentials. These ids already appear in public gateway job files.

## Etsy
- Shop: GM's Digital Creations, shop_id 68605457. New listing fee $0.20. Caps in `rules.md`.
- Taxonomy: 1350 for games, party, santa, trivia, bingo, exchange; 354 for the rest; wall art
  category "Art & Collectibles > Prints > Digital Prints".

## Pinterest (Zernio account 6ad7b245350e86dff5e25133)
Board by name, else by keyword in the title; keywords are checked top to bottom and the
FIRST match wins; no match = the default:

| Board | Id | Keywords |
|-------|----|----------|
| Thanksgiving Ideas | 1096274802985595722 | thanksgiving, friendsgiving |
| New Year's Eve Party Ideas | 1096274802985595725 | new year, nye |
| Christmas Gift Ideas and Lists | 1096274802985595726 | gift, santa |
| Christmas Budget and Money Tips | 1096274802985595728 | budget, money, savings, debt |
| Holiday Hosting and Meal Planning | 1096274802985595732 | meal, menu, host |
| Family Christmas Activities | 1096274802985595734 | kid, family |
| Christmas Party Ideas | 1096274802985595723 | party, game |
| Christian Wall Art Printables | 1096274802985601133 | bible, verse, scripture, christian |
| Christmas Planning and Organization | 1096274802985595727 | (default) |

Still-pin slots per day (6): 13:30Z, 15:30Z, 17:30Z, 19:30Z, 21:30Z, 23:30Z. Video pin: 8:30 PM
Central.

## TikTok
- Postproxy profile L2UJk4 (@gmsdigitalcreatio), posted through the gateway op "postproxy" since
  Oct 24, 2026 (the old Zernio account 6ad7a7ecea18e081fb3894d2 is retired for TikTok). Post URL fallback
  https://www.tiktok.com/@gmsdigitalcreatio.

## Make (team 3216895, organization 9329352, free plan: 1,000 operations a month, resets on the 18th)
- Gateway scenario 6676353 (Instagram, Facebook, shop YouTube, TikTok via zernio_api, YouTube
  stats, Etsy fallback). The old "Starship Pinterest poster" scenario 6676393 stays OFF.
- Connections: 11830197 "Instagram GM" (@gmsdigitalcreations, 17841469346530680);
  11863175 "Facebook GM Page v2" (Gmsdigitalcreations, 1358210974045889; re-authorized Oct 21,
  2026 and wired into fb_reel/fb_photo; the old 11830277 is no longer used); 11830335 "YouTube SHOP"
  (GMsDigitalCreations, UCBEMIih_sKOxjZvQ9oeqYWw); 11830987 "Zernio TikTok GM".
  Connection 11806532 (@gmulaishere) belongs to the Studio floor and is never used for the shop.

## YouTube
- Shop channel: GMsDigitalCreations, UCBEMIih_sKOxjZvQ9oeqYWw (Herald, Make yt_short).
- Studio (Gmula) channel: @gmulaishere, UCax9xpzMhvy8DXeyBi0czBg (Vega; Make action "youtube").
- Posting windows (Gmula): weekdays 7:00 PM Central, weekends 11:30 AM Central.

## Instagram (shop): https://www.instagram.com/gmsdigitalcreations/
## Facebook reel URL: https://www.facebook.com/reel/<video_id>

## Trading (paper)
- Alpaca paper, bankroll $25, floor $20, daily loss limit $1.50, paperDaysRequired 2.
- Autopilot: GitHub Action "Trading autopilot" (factory/trading/autopilot.py), heartbeat at
  factory/trading/auto/heartbeat.json, day file factory/trading/auto/<day key>.json, errors at
  factory/trading/auto/last-error.json, watchlist at factory/trading/watchlist.json.

## Trading (live, Grayson's go Nov 2, 2026)
- Same Alpaca login, the LIVE brokerage account, funded with $20-25 by Grayson. Secrets ALPACA_LIVE_KEY_ID /
  ALPACA_LIVE_SECRET_KEY (never the paper pair); variables ALPACA_LIVE (1 = live, empty = paper),
  ALPACA_LIVE_ACCOUNT_ID (pins the account: the account number on the Alpaca dashboard or the API id; any other
  is refused), ALPACA_LIVE_FLOOR (optional override of the $5 floor, a plain number). ALPACA_LIVE_BUYS=1 is set only
  inside the Trading autopilot workflow; it is what lets a process send a live buy. Profile: factory/trading/profiles/live-aggressive.json ($5 floor, $5 daily loss, 100% of cash, one
  position, 6 entries, 13 leveraged ETFs). Runbook: factory/trading/LIVE_SETUP.md.
- The heartbeat and day files carry "mode": "live", "profile": "live-aggressive" and "accountId": the last 4
  characters of the account number. Never the whole number or id, never a key, in any file (the repo is public; the
  gateway answers GET /account with the hint view for that reason). /bankroll in live mode = real equity and cash.

## Scheduled task ids (for the Mechanic and the schedule sync only)
- Night Shift trig_01AKhkcKn5cgKDgpZavQEun1 (re-created Oct 21, 2026; the old trig_01AAr8ck2SDQBQUNtAvm58YF is disabled) · Bolt trig_01QWbpg22o89x2sFANkEcG67 ·
  Herald trig_01WukPSxb5DtW4tL2Zs9EKhu · Mechanic trig_01LjWHeBBnHMDPfAyT752hPJ ·
  Pricing trig_011d8uPA25L1BVvMwXAWGHfa · Video pin trig_01MQhG8MqAZ6F8ugWSoJjnmg ·
  Check-up trig_018st1EXDopgRYYnYQHVbhsY · Day Watch trig_01KHgYQk9YXzkiM7bsHjRNKH ·
  Trading scans trig_01JNSbroLibnR1QZNdLLPzML · close trig_01JpNg3pfdAwrz513eSWbH1i ·
  lab trig_01PsFJRYr7Yk3pamtWiQ15qR · Studio trig_01VNPpEQuRoSAGg9F9SAeWYo ·
  Atlas Prime trig_017MUdcGf8vPKHmxWFw2n4Gb.
- Parked (disabled on purpose, never re-fire): Funnel daily Reel trig_01AgFcWjDyZxg3PJcdb1HjaN
  and every task whose name contains "OLD" or "replaced".
