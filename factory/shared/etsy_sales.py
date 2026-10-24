#!/usr/bin/env python3
"""Turn Etsy receipts into sales docs for Atlas Hub (Grayson, Oct 24, 2026).

Usage:
  python3 factory/shared/etsy_sales.py <gateway out json> <existing sales dir> <writes out json>

- <gateway out json>: gw/out/<job id>.json from a job holding an etsy GET
  /shops/68605457/receipts?limit=100 op tagged "receipts".
- <existing sales dir>: the folder ArtifactData list/query(out_dir) saved the sales collection
  into (may be empty or missing).
- <writes out json>: written as {"writes":[...], "new":[{...summary}]} ready for one
  ArtifactData batch. Only receipts not already in the database become writes, so running it
  every Bolt run never double-counts. Real numbers only: gross = what the buyer paid for the
  items (receipt subtotal, after any sale discount), before Etsy fees.
"""
import json, os, sys, glob, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Chicago")


def money(m):
    if not isinstance(m, dict) or m.get("amount") is None:
        return None
    return round(m["amount"] / (m.get("divisor") or 100), 2)


def main(src, sales_dir, out):
    res = json.load(open(src))
    data = None
    for r in res.get("results", []):
        if r.get("tag") == "receipts" or "receipts" in str(r.get("op", "")):
            if not r.get("ok"):
                print("receipts call failed:", r.get("status"), r.get("error"))
                sys.exit(2)
            data = r.get("data") or {}
    if data is None:
        print("no receipts result in", src)
        sys.exit(2)

    have = set()
    for f in glob.glob(os.path.join(sales_dir, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        d = d.get("data", d)
        rid = d.get("receiptId")
        if rid:
            have.add(str(rid))
        have.add(os.path.splitext(os.path.basename(f))[0])

    writes, new = [], []
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for x in data.get("results", []):
        rid = str(x.get("receipt_id"))
        doc_id = "etsy-" + rid
        if rid in have or doc_id in have:
            continue
        if x.get("is_paid") is False or str(x.get("status", "")).lower() in ("canceled", "cancelled"):
            continue
        ts = x.get("create_timestamp") or x.get("created_timestamp")
        date = datetime.datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d") if ts else None
        tx = x.get("transactions") or []
        title = (tx[0].get("title") if tx else None) or "Etsy order"
        title = title.replace("&#39;", "'").replace("&quot;", '"').replace("&amp;", "&")
        if len(tx) > 1:
            title += " (+%d more)" % (len(tx) - 1)
        gross = money(x.get("subtotal"))
        if gross is None:
            gross = round(sum((money(t.get("price")) or 0) * (t.get("quantity") or 1) for t in tx), 2)
        refund = sum(money(r.get("amount")) or 0 for r in (x.get("refunds") or []))
        doc = {
            "date": date, "receiptId": rid,
            "listingId": str(tx[0].get("listing_id")) if tx else None,
            "listing": title[:140], "gross": gross,
            "listPrice": money(tx[0].get("price")) if tx else None,
            "items": sum((t.get("quantity") or 1) for t in tx),
            "refundAmount": round(refund, 2), "offsite": False, "verified": True,
            "source": "Etsy receipts (auto)", "by": "Bolt", "createdAt": now,
        }
        writes.append({"op": "set", "collection": "sales", "doc_id": doc_id, "data": doc})
        new.append({"id": doc_id, "date": date, "gross": gross, "listing": title[:60]})

    json.dump({"writes": writes, "new": new}, open(out, "w"), indent=1)
    print("%d receipts, %d new sale(s)" % (len(data.get("results", [])), len(new)))
    for n in new:
        print(" NEW", n["date"], "$%.2f" % (n["gross"] or 0), n["listing"])


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    main(*sys.argv[1:])
