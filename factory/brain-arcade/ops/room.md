# The Brain Arcade room (its own page, separate from the GM Agency page)

Room page: lane.json "room.url" (an artifact with its own database). Crews write ONLY these docs
with ArtifactData (read first, pass if_version):
- status/main  {at, lights:{build,publish,learn,shop}, shopVerified, listedToday, listedTotal, views, favs,
                sales, topLesson, nextMove, needsYou:[...], lastRun:{task,outcome,note,at}}
- crew/<agent id>  {state:"working"|"idle"|"waiting", task, updatedAt}   (ids from crew.json)
- products/<slug>  {title, grade, kind, status, score, answerKey, price, listingId, url, updatedAt}
- events/<day key> {items:[{t, who, text}]}  newest 100
The page reads them live. Never put secrets, buyer names or emails there.

## The Atlas Hub "Shop 2" tab (added Oct 25, 2026, Grayson asked for one tab per shop)
The main hub (https://claude.ai/artifact/U91MrX9kzLUxLu9pnmgP5X) shows this lane from ONE doc:
shops/brainarcade {at, shopVerified, listedToday, listedTotal, views, favs, salesMonth, salesTotal,
crew:[{name, role, state, task}] (only agents working/waiting/stuck), nextMove, needsYou:[{text, link}],
roomUrl}. Today's line "Shop 1: X sales · Shop 2: X sales" reads salesMonth. Built by
tools/status_sync.py; never write any other hub doc.
