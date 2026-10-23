# Trading journal (Vault's nightly trade-journal review)

One file per trading day, `<day>.md` (day key = Central date), written by Vault in the close run after the
flatten and the ledger. Until Grayson adds `factory/trading/journal/` to the close task's write list, the close
run may only write `factory/skills/vault/journal-<day>.md`; the review reads both places. Rules: factory/specs/trading-floor-v6.md, "Vault: nightly trade-journal review".

Each file holds, from `factory/trading/auto/<day>.json` and the gateway only (never a number from memory):
1. The day's numbers: trades, wins/losses, net $, equity open → close, breaches.
2. A trade table: symbol, in, out, R, why (stop filled / target / no stop / trail refused), entry time.
3. "Recurring errors": anything that happened twice today or on 2 of the last 3 journals, with the times and
   symbols as evidence.
4. Exactly 3 rules for tomorrow. Each names the number it rests on and the check that proves it tomorrow.
   A rule may tighten, never loosen, a money rule or a LOCKED knob, and never tells the autopilot a price.
On a no-trade day the file says so (the day file's lastNote), carries yesterday's 3 rules forward and marks
each held / not held. Nothing is invented. Not financial advice: the account can lose money.
