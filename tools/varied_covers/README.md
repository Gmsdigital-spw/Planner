# Varied covers (Oct 23, 2026)

The first covers built to Grayson's Oct 23 rule (specs/cover-styles.md, Oct 23 section): five
different layout families, the product as the hero, no shared template. Live since Oct 23 on
5 listings (Santa letters, scavenger hunt, advent activities, Thanksgiving host planner,
gingerbread contest). Use these functions as WORKED EXAMPLES of each family, not as a new
single template: every new cover must still differ from the last 5 and pass the side-by-side test.

| Function in covers.py | Layout family |
|---|---|
| santa() | hero page close-up: one real page big and readable, two fanned behind |
| scavenger() | contents collage: many real cards edge to edge under a title banner |
| advent() | bright grid: all cards in a calendar grid with a giant number |
| thanksgiving() | device dashboard: real pages on a tablet + phone |
| gingerbread() | flat-lay: printed sheets on a tablecloth, top-down, pencil |

extract.py cuts flat page renders out of existing listing photos (used because the product PDFs
in gw/vault are encrypted). Fresh PDF renders are sharper when the PDF is available.
Set COVERS_OUT to a working folder; source crops are read from $COVERS_OUT/src/x/.
Known weak spots: text on cut-out pages is a bit soft up close; Thanksgiving and Gingerbread
are a step below top sellers (no photographed props).
