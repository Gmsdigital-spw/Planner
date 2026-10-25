# The Brain Arcade room (its own page, separate from the GM Agency page)

Room page: lane.json "room.url" (an artifact with its own database). Crews write ONLY these docs
with ArtifactData (read first, pass if_version):
- status/main  {at, lights:{build,publish,learn,shop}, shopVerified, listedToday, listedTotal, views, favs,
                sales, topLesson, nextMove, needsYou:[...], lastRun:{task,outcome,note,at}}
- crew/<agent id>  {state:"working"|"idle"|"waiting", task, updatedAt}   (ids from crew.json)
- products/<slug>  {title, grade, kind, status, score, answerKey, price, listingId, url, updatedAt}
- events/<day key> {items:[{t, who, text}]}  newest 100
The page reads them live. Never put secrets, buyer names or emails there.
