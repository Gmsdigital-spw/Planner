# The Notebook (Grayson, Oct 23, 2026)

Grayson's order: "start doing notes with everything we do and keep it so they get smarter and
smarter, even notes about posts, trades and my business, so they can make it more and more successful."

One notebook, one file per lane. Every crew READS its lane file before it works and follows it.
The Night Shift (daily) and Atlas Prime (Sundays) WRITE it from real results.

| File | Lane | Read by |
|------|------|---------|
| `business.md` | the big picture: goals, money, what Grayson wants | every crew, top section only |
| `etsy.md` | products, covers, photos, titles, tags, prices | Night Shift 01, 03-07, Warden, Bolt |
| `pins.md` | Pinterest pins and video pins | Night Shift 08, Pixel |
| `social.md` | Instagram, Facebook, TikTok, shop YouTube | Herald |
| `trading.md` | the paper trading floor | Trading scans, close, lab |
| `shorts.md` | Gmula YouTube Shorts | Studio Floor |
| `ops.md` | the crew itself: what breaks, what fixes stick | Mechanic, Night Shift review, every crew when a bug hits |
| `results.jsonl` | one line per thing we made, posted or traded, plus its numbers later | the notebook keepers |

## Every lane file has the same 4 sections
1. **Grayson's rules**: what he told us, word for word where possible, dated. Highest authority
   in the notebook. A correction from Grayson goes here THE SAME DAY and never gets retired by numbers.
2. **What works**: backed by real numbers. Each line: date, what works, the evidence (numbers),
   how many times it held. Never a "works" line without numbers.
3. **Testing**: ideas we are trying that are not proven yet, with what would prove or kill them
   and the date to check.
4. **What doesn't work**: anything tried that failed, flopped, broke, got refused by a platform,
   failed inspection for the same reason twice, or that Grayson rejected. A clear failure is a
   fact, so it goes in the same day (no waiting for 7 days of numbers). Kept forever so we never
   repeat it.

## Take notes on EVERYTHING (Grayson, Oct 23, 2026: "literally take notes for every single thing")
Not just listings and pins: ideas picked and dropped (and why), builds that failed inspection
(the reason), covers, titles, tags, prices, pins, posts, videos, Shorts, trades, price changes,
gateway or platform errors, fixes that held and fixes that didn't, and every Grayson correction.
If it happened and it could teach us something, it gets a results line or a notebook line.

## results.jsonl (the memory of everything we did)
One JSON line per item: {"day", "lane", "kind" (listing|cover|pin|post|video|short|trade|price|idea|build|fail|fix),
"id" (listing / pin / post / order id), "what" (one line), "tags" {layout, hook, price, theme,
time, symbol, setup...}, "outcome" (filled at 7 days: views, favs, sales, saves, clicks,
impressions, pnl), "checked" (day the outcome was filled)}.
Helper: `python3 factory/notebook/nb.py add|outcome|show|pending` (see `--help`).

## How a lesson gets made
1. Something gets made/posted/traded -> a results line with tags.
2. 7 days later the keeper fills its outcome from stats/, pinstats/, social stats, trading ledger.
3. When one tag clearly beats another (at least 2x, 3+ items each side, enough views to mean
   something) -> a Testing line, then "What works" when it holds again on a different week.
4. When new numbers contradict a "works" line -> move it to "What doesn't work" with the numbers.
6. A failure or a Grayson rejection -> "What doesn't work" the same day, with what happened.
5. Small data honesty: under 100 views on both sides = "too early", not a lesson.

## Honesty rules
- Our own inspection score is NOT a result. Results are what buyers did (views, favorites,
  sales, saves, clicks) or what the market did (trades' P/L).
- Say "unknown" when a number could not be read. Never invent or round up.
- Keep files short: each lane file under 120 lines. Merge duplicates; retire stale lines.
