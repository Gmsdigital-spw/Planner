# The free tech stack (Grayson, Oct 28, 2026)

Canonical home for which outside tools the Factory may use for the Etsy shop and its socials
(Pinterest, TikTok, Instagram, Facebook, shop YouTube, Studio YouTube). FREE TIERS ONLY. Atlas
Prime owns this list: the Sunday fleet review checks every tool below is still on its free
plan and still inside its limits, and proposes (never makes) any change.

## Rules
- Free tier only. Never upgrade a plan, add a card, start a trial that turns paid, or turn on
  pay-as-you-go. A tool that hits its free limit stops for the month; the run notes it.
- No account exists until Grayson makes it. A crew never signs up for anything. Until a tool's
  key is in the gateway secrets (`gateway.md`), the crew skips that tool and keeps working.
- Keys and tokens live only in GitHub Actions secrets or Make. Never in a file, commit, job
  file, caption or message (`rules.md`).
- The Factory database (`database.md`), the free GitHub gateway (`gateway.md`) and Make
  (`accounts.md`) stay the system of record. These tools sit beside them, never replace them.
- Limits below are the vendors' free plans as of Oct 2026. Re-check the pricing page before
  relying on a number; if a vendor cuts its free plan, stop using the tool and tell Grayson.

## Approved (free)

| Tool | Job for the shop | Free plan (Oct 2026) | Watch out |
|------|------------------|----------------------|-----------|
| GitHub | Version control, the free gateway Actions, GitHub Pages hosting | Free; Actions minutes are free on public repos | Keep this repo public or the gateway eats Actions minutes |
| Supabase | Optional Postgres for post logs, social stats history, link clicks | 2 projects, 500 MB database, 1 GB files | A free project pauses after 7 days with no traffic; any weekly run wakes it |
| Vercel | Preview deploys of the funnel and tool pages | Hobby plan, free | Hobby is non-commercial. Anything that sells (funnel, checkout, shop pages) lives on GitHub Pages or Cloudflare Pages, not Vercel |
| Cloudflare | DNS (only if a domain is ever bought), Pages hosting for commercial pages | DNS and Pages are free, commercial use allowed | Pages is the free home for anything that sells |
| Resend | Transactional email (freebie delivery, funnel email) | 3,000 emails a month, 100 a day, 1 domain | Needs a domain we own to send to customers; without one it only sends to Grayson. Parked until a domain exists |
| Clerk | Sign-in, only if a members page is ever built | Free plan (monthly-user cap on the pricing page) | Nothing needs sign-in today; do not add it to a page without a reason |
| PostHog | Clicks from every social bio and pin link to the funnel and shop (UTM per channel) | 1M events a month | Tag every link `utm_source=<pinterest|tiktok|instagram|facebook|youtube>`; this is how the scoreboard learns which channel sells |
| Sentry | Errors from gateway scripts, the autopilot and tools | Developer plan, 5,000 errors a month, 1 user | The Sentry connector can read issues; the Medic and Mechanic check it in the morning once it is set up |
| Upstash | Redis for dedupe and rate limits (never post the same pin, caption or video twice) | 500K commands a month, 256 MB | One key per post hash; expire after 30 days |
| Pinecone | Vector search over past listings, captions and pins (find near-duplicates, reuse what won) | Starter plan, free (one project, small index) | Index titles and captions only, never customer data |

## Not on the free list
- Namecheap domain ($12 a year): paid, so not set up. The shop does not need one (Etsy and
  GitHub Pages give free URLs). If Grayson ever wants one, it is a proposal for his go.
- Stripe: the shop does not need it, Etsy takes the payments. No monthly fee, but 2.9% plus 30
  cents a sale, so it is not "free"; never add a Stripe checkout to the shop or funnel.

## Which socials use what

| Channel | Account (`accounts.md`) | Stack pieces |
|---------|-------------------------|--------------|
| Etsy shop | shop_id 68605457 | Pinecone (duplicate check before a build), PostHog (traffic in), Sentry (gateway errors) |
| Pinterest | Zernio, 9 boards | Upstash (no repeat pins), PostHog (UTM per board), Pinecone (pin copy near-duplicates) |
| TikTok | Postproxy L2UJk4 | Upstash (no repeat videos), PostHog (bio link) |
| Instagram | @gmsdigitalcreations via Make | Upstash, PostHog (bio link) |
| Facebook | Gmsdigitalcreations page via Make | Upstash, PostHog |
| YouTube (shop and Studio) | UCBEMIih... and UCax9xpz... | Upstash (no repeat Shorts), PostHog (description links) |

## Setup Grayson does (once, phone, only when he wants the tool)
For each tool: sign up with the shop Gmail on the free plan, skip any card prompt, create one
API key, and add it at the repo's Settings > Secrets > Actions with the name below. The crews
start using the tool on the next run after the secret exists.

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `POSTHOG_PROJECT_KEY`, `SENTRY_DSN`,
`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `PINECONE_API_KEY`. (Vercel, Cloudflare,
Clerk and Resend need no secret until a page or domain needs them.)
