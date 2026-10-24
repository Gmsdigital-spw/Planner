import json
title = "Pink Bow Birthday Invitation Editable, Cabana Stripe Palm Leaf Invite, Sweet 16, 21st, 30th Girl Birthday Party, 5x7 Printable PDF"
tags = ["pink bow invitation", "bow birthday invite", "editable invitation", "sweet 16 invitation", "girl birthday invite",
        "cabana birthday", "preppy birthday", "pink stripe invite", "palm leaf invitation", "21st birthday invite",
        "30th birthday invite", "coquette birthday", "printable invitation"]
desc = """Editable pink bow birthday invitation for a sweet 16, 21st, 30th or any girl's birthday party: soft pink cabana stripes, a cream scalloped card, a pink bow on top and green palm leaves in the corners. Type your details, print at home, and the invites are ready the same day.

WHAT YOU GET (one PDF, 7 pages)
- 5x7 invitation in pink cabana stripe (2 per page)
- 5x7 invitation in sage cabana stripe (2 per page)
- 5x7 matching details card in pink and in sage (what to wear, gifts, parking)
- How-to page with wording ideas for the name line
- 48 type-in lines: name, date, time, place, address, RSVP and every details line

HOW IT WORKS
1. Download the PDF from Etsy (You > Purchases > Download files) on a computer.
2. Open it in Adobe Acrobat Reader (free) and click the green text to type your own details.
3. Save, then print at 100% / Actual size on US Letter cardstock, at home or at a print shop.
4. Cut on the light corner marks. Each card is 5 x 7 inches and fits an A7 envelope.

GOOD TO KNOW
- This is a digital PDF download. No printed cards or envelopes are shipped.
- The headline "Let's Celebrate", the stripes, bow and leaves are part of the design. Fonts and colours cannot be changed.
- Each card on a page edits on its own, so you can make two versions on one sheet.
- Personal use only. Questions or a typo you can't fix? Message me and I'll help.

This design was created with AI assistance under the creative direction of the seller."""
copy = dict(title=title, tags=tags, description=desc, price=5.99, category="Paper & Party Supplies > Paper > Invitations & Announcements > Invitations",
            materials="Digital download, PDF", coverHeadline="Editable Bow Invite", categoryVerified=False, autocompleteChecked=False,
            phraseSource="WebSearch 'etsy pink bow birthday invitation editable' (no autocomplete returned) + brief niche 'pink bow birthday invitation editable'")
assert len(title) <= 140, len(title)
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert len(desc) >= 300 and desc.endswith("This design was created with AI assistance under the creative direction of the seller.")
bad = [w for w in ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you're", "—"] if w in (title + desc).lower()]
assert not bad, bad
print(len(title), title[:40], len(tags), len(desc))
json.dump(copy, open("copy.json", "w"), indent=1)
