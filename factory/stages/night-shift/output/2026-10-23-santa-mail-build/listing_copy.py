import json
title = "6 Editable Letters from Santa Printable Bundle, Nice List Certificate, Dear Santa Wish List, Gift Tags, Type-In PDF, No Canva"
tags = ["letter from santa", "santa letter", "letters from santa", "santa nice list", "santa certificate",
        "dear santa wish list", "christmas wish list", "santa gift tags", "north pole mail", "santa letter pdf",
        "first christmas", "new big sister gift", "santa letter kids"]
desc = """Six letters from Santa for six different kinds of year, ready to type and print before Christmas Eve. Made for parents and grandparents of kids ages 2 to 9 who want a real North Pole letter without paying for a custom one or opening a Canva account.

Every letter is fully written and different. You type the child's name, the date, three good things they did this year and the P.S., then print. That is it.

WHAT'S INCLUDED (13 pages, US Letter, one editable PDF)
1. Cover with the full contents
2. How-to page: which letter fits which child, plus Christmas Eve delivery ideas
3. Letter 1, The Nice List: the classic letter for any child
4. Letter 2, Baby's First Christmas: a keepsake for a baby or toddler
5. Letter 3, New Big Sibling: for a child who became a big brother or sister this year
6. Letter 4, The Kindness Star: for a child who shared, helped or included others
7. Letter 5, A Hard Year, Done Well: for a move, a loss, an illness or a big change, handled bravely
8. Letter 6, A New Home: for a family that moved before Christmas
9. Official Nice List certificate with type-in name, elf note, signature and date
10. Santa's Nice List 2026: 14 type-in rows with "checked once" and "checked twice" tick boxes
11. Dear Santa wish list for the child: name, age, a kind thing they did, 6 wishes and a drawing box
12. 4 North Pole Express envelope labels with type-in name and address
13. 12 From Santa gift tags with type-in names
Plus a thank-you page at the end.

HOW EDITING WORKS
Open the PDF in the free Adobe Acrobat Reader on a computer (best), or the Adobe Acrobat Reader app on a phone or tablet. Click a pale green box and type. Sample words are already in every box, so you can keep them or type over them. No Canva account, no app sign-up, no waiting for an email. Fonts and colors are fixed so every page prints the way you see it. Other phone viewers may not show the type-in boxes.

PRINTING
Print at home at 100% on plain paper, or on cream or parchment cardstock for a real North Pole look. US Letter size; choose Fit to page for A4. Sign the letter in gold or red pen and seal it with a North Pole label.

THIS IS A DIGITAL DOWNLOAD
Nothing will be shipped. After you buy, go to You > Purchases on Etsy and tap Download Files. For personal use only.

This design was created with AI assistance under the creative direction of the seller."""
bad = ["elevate", "unlock", "seamless", "game-changer", "dive into", "whether you're", "look no further", "in today's", "—"]
assert len(title) <= 140, len(title)
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [(t, len(t)) for t in tags]
assert len(desc) >= 300 and desc.rstrip().endswith("This design was created with AI assistance under the creative direction of the seller.")
assert not any(b in (title + desc).lower() for b in bad)
copy = dict(title=title, tags=tags, description=desc, price=8.99, category="Paper & Party Supplies > Paper > Stationery > Letters", materials=["Digital download", "PDF"],
            coverHeadline="Letters from *Santa*", autocompleteChecked=False,
            searchSource="Etsy search pages opened Oct 23: etsy.com/market/letters_from_santa_printable and etsy.com/market/letter_from_santa_editable (no autocomplete available via WebSearch)",
            writtenAt="2026-10-23T12:20:00Z")
json.dump(copy, open("/home/claude/build/santa/copy.json", "w"), indent=1)
print(len(title), len(tags), len(desc))
