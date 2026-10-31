# Foreman Strict Mode (Grayson, Oct 21, 2026)

_Standing instructions. Same authority as the other files in factory/specs/. Every crew that reads product-floor-v6.md or marketing-wing-v6.md reads this file too and follows it. Where this file is stricter than an older rule, this file wins._

## Why
The Factory has to pay for its own Claude plan or it gets shut off. A week in, nothing has sold. Most "AI starship" builds spread across ten businesses and none of them sell. We do the opposite: fewer lanes, harder standards, judged on real numbers.

## 1. Focus
- **Etsy is the money lane.** It gets first claim on every run's time and effort.
- **Trading is lane two.** It keeps improving on paper with the lab; no change to its money rules.
- **Every other lane** (Gmula Shorts, Funnel Floor, Ridgeline, Marketing extras) keeps running exactly as it is, but gets **no new features or new work** until the Etsy shop has 3 real sales. Grayson reviews them after this push. (Oct 23, 2026: the agent update in `shared/rules.md`, "Mission" and "The agent update", applies to every crew now; it sharpens how each agent works, it adds no lane feature.)

## 2. Judged on evidence, never on effort
- An agent's grade is what moved: Etsy views, favorites, visits from pins, sales. Not posts made, ideas typed or files written.
- Every claim of demand cites proof (a search result, bestseller reviews count, a competitor listing link). No proof = the idea is dropped.
- Never invent a number. "Unknown" beats a guess.

## 3. Quality gates (all must pass, or it does not ship)
- Product score 85+ with rulesPass and a clean slop check reaches drafts; 92+ is the aim (Oct 27, 2026). The slop check: "Would a top Etsy seller post this?" If not, it fails.
- Covers follow `cover-styles.md` Oct 23 (variety gate; fun_covers card at most 1 in 6) and pins follow `stages/night-shift/08-batch-pins` step 2 PIN STANDARD (Oct 27; fun_pins card at most 1 in 6). Product fills the frame, title readable at thumbnail size, no two listings or pin slots in a row alike. Wall art covers follow `wall-art.md`. (Updated Oct 27, 2026: this line used to force fun_covers/fun_pins on everything.)
- Every new product ships with a styled cover and **3 pins in 3 different layout families**, each with its own hook.

## 4. Volume where it counts
- Pinterest: 6 pins a day, spread across products and styles (Bolt schedules them).
- The pin queue must never drop below 1 day of pins; if it does, Pixel makes more pins for the best-viewed active listings before building anything new.

## 5. Weekly scorecard (Sunday, at the Foreman's review)
For every active listing, from the stats/<day> docs: views, favorites, sales over 7 and 14 days.
- **Working** (sales, or views rising with favorites): make more like it, more pins for it.
- **Looks, no sale** (views but no sales after 14 days): flag a better cover, title or price for Grayson's OK.
- **Dead** (under 5 views after 14 days): flag a retitle/retag for Grayson's OK, and stop building that niche.
- For every lane: a lane with no measurable result (views, clicks, sales) for 14 days is flagged to Grayson to pause. The Foreman never deletes or pauses a lane by itself.
- **Pay-for-itself scoreboard (Oct 23, 2026).** The Sunday review and every standup open with: verified income this month, fees and spend this month, the Claude plan ($250), recovery % (Night Shift stage 09 D), days left in the month, and per lane the number it moved this week (Etsy: listings live, views7, favorites7, sales; pins: out and clicks; posts: out and clicks to Etsy; Studio: Shorts posted and views; Trading: paper P/L and breaches). Numbers from the database and run logs only; unknown stays unknown.

## 6. Self-repair
- The Mechanic checks every lane 5 times a day and re-runs or re-sends what failed (once per day per thing). Crews write an exact blocker line when they stop, so the Mechanic can fix it.
- Grayson gets one morning report, and a message only when something red needs his tap.

## 7. The agent update (Grayson, Oct 23, 2026)
- Every agent is pushed to its best work every run: the cap reached with 92+ work, one measured test alive, one lesson with a number, one prediction graded. `shared/rules.md` ("Mission", "The agent update") is the canonical text; this file only says how the Foreman grades it.
- Grade "under" = any cap missed without a stated blocker, a product under 85, a missing or numberless learned line, or a prediction not graded. Three "under" grades in a row for one agent = the Foreman rewrites that agent's "Exact steps" from what worked (Sunday, surgical, with the evidence), and says so in the standup.
- The week's standing order (`specs/buyers-week-2026-10-31.md`, Oct 31 to Nov 7, 2026) sets the daily targets the standup grades against; its scoreboard is the standup's first line.
