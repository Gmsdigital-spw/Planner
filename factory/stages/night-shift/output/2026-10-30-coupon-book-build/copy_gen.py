import json
title = "Christmas Coupon Book Printable, Editable PDF: 30 Coupons for Partner, Kids and Family, 6 Blank Coupons and Gift Envelope"
tags = ["christmas coupon", "coupon book", "christmas coupons", "editable coupon book", "printable coupons",
        "love coupons", "coupon book for him", "coupon book for her", "kids coupon book", "stocking stuffer",
        "last minute gift", "gift for boyfriend", "christmas gift ideas"]
AI = "This design was created with AI assistance under the creative direction of the seller."
desc = """A printable Christmas coupon book with 30 ready-written coupons: 10 for a partner, 10 for kids and 10 for family, plus 6 blank coupons you fill in yourself. Easy to edit: type the names in the free Adobe Acrobat Reader, print tonight and you have a personal gift that fits in a stocking.

No Canva, no Templett, no account and no template that expires. Open the PDF, click a line, type, print.

WHAT'S INCLUDED (13-page PDF, US Letter: cover page, 11 pages, thank-you page)
- How to edit, print and assemble (1 page)
- 3 front covers: For My Love, For My Little Elf, For the Family, each with type-in TO and FROM lines (1 page)
- 3 back covers with the fine print and a type-in MADE WITH LOVE BY line (1 page)
- 10 partner coupons (2 pages): breakfast in bed, date night planned by me, sleep in pass and more
- 10 kids coupons (2 pages): stay up 30 minutes late, build a blanket fort, pajama day and more
- 10 family coupons (2 pages): family game night, Sunday dinner on me, help with any project and more
- 6 blank coupons: type your own title, two lines of detail and the names (1 page)
- Fold-up gift envelope with type-in TO and FROM (1 page)

WHAT YOU CAN EDIT
- 101 type-in fields: FOR and FROM on every coupon, TO and FROM on the covers and envelope, and every line of the 6 blank coupons
- The 30 written coupons have fixed wording; the fonts are fixed and cannot be changed
- Leave any line empty to write by hand after printing

HOW IT WORKS
This is a digital download. Nothing will be shipped. After purchase, go to You > Purchases on Etsy and download the PDF. Open it in Adobe Acrobat Reader (free) on a computer, type your names, save, then print at home or at a print shop on US Letter paper at 100%. Cardstock looks best. Each coupon is 6 x 1.6 in; cut on the corner marks, stack each book behind its cover and staple or tie with ribbon.

For personal use. Please do not resell or share the file.

""" + AI
cover_headline = "30 Christmas Coupons"
copy = {"title": title, "tags": tags, "description": desc, "price": 4.49,
        "priceNote": "$4.49 vs opened rivals $3.99 sale/$7.99 (1327740851, the 160-review leader), $3.00 for 11 coupons (701942880), $6.99 for 22 (669057885), $8.88 for 8 (570840297); inside the invitation lane $3.99-$7.99",
        "category": "Paper & Party Supplies > Paper > Stationery", "categoryNote": "not verified against Etsy's taxonomy tonight (no Etsy access in this worker); Bolt confirms at draft time",
        "materials": ["Digital download", "PDF"], "coverHeadline": cover_headline, "autocompleteChecked": False,
        "checkNote": "Phrase 'christmas coupon book': Etsy search (brief phraseCheck, 2026-10-29) 24 of top 25 titles carry it; not re-run tonight (no gateway write path for this worker).",
        "tagNote": "Tags from opened rival titles/slugs and buyer-voice ('stocking stuffer' 1327740851); not each gateway-checked tonight.",
        "writtenAt": "2026-10-30T07:53:00Z"}
assert len(title) <= 140 and title.startswith("Christmas Coupon Book Printable, Editable PDF")
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags)
assert len(desc) >= 300 and desc.endswith(AI)
assert len(cover_headline.split()) <= 4 and cover_headline.lower() not in title.lower()
for bad in ["elevate", "unlock", "seamless", "dive into", "whether you", "game-changer", "look no further", "—", "a4"]:
    assert bad not in desc.lower(), bad
json.dump({"copy": copy}, open("copy.json", "w"), indent=1)
print(len(title), len(tags), len(desc), repr(title[:40]))
