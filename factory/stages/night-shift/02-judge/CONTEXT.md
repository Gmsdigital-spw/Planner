# 02 Judge: Atlas auto-approver (room "bridge")

Grayson turned this on Oct 18, 2026 so he no longer approves ideas by hand. Skip this stage
only if settings.autoApprove is false. His past rejectReasons and the active lessons are the
strongest signal of his taste. Never touch a brief Grayson decided himself (decidedBy anything
other than "Atlas auto-approver").

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Skill | `../../../skills/judge_ideas/SKILL.md` | Full file | The judge's checklist |
| Database | briefs (status proposed), lessons (active) | all fields | What to decide and what Grayson likes |
| Previous stage | ideas/<day key> | items (verdicts already given by the Idea Judge in stage 01) | Context only; this stage decides BRIEFS |
| Reference | `../references/wall-art.md` | "Auto-approver" section | Only for a wall art brief |

## Process
1. Set crew/atlas working ("Judging ideas"). Review every brief with status "proposed" (the new
   ones and older ones still waiting).
2. REJECT (status "rejected", decidedBy "Atlas auto-approver", decidedAt now, rejectReason one
   plain sentence) when any of these is true: it repeats a niche the shop already sells or a
   brief from the last 60 (same buyer + same use, even with a new name); it needs a brand,
   character, trademark, licensed phrase or medical/legal claim; it cannot be built well with
   text, tables, checklists and simple boxes (wall art judged by its own buildable rule); its
   selling window closes within 3 weeks; it has fewer than 2 evidence links that are real pages
   about the niche; or it smells like AI slop: a vague buyer ("anyone", "everyone"), a padded
   bundle ("500 pages", "ultimate mega bundle"), a gimmick with no clear problem, filler words
   in the title (ultimate, aesthetic, boho, minimalist, unlock, elevate) instead of what it does,
   or a flooded niche with no different angle.
3. APPROVE (status "approved", decidedBy "Atlas auto-approver", decidedAt now, approveReason one
   plain sentence naming the buyer, the problem and the evidence) only when no reject rule
   applies AND total is 21 or more AND demand, timing and buildable are each 4 or more AND
   shopFit is 3 or more AND you can name the one specific thing that beats the top 3 competing
   listings you saw. Approve at most settings.buildsPerRun (default 2) per run, best first; at
   most 1 wall art brief per run. Good ones over the limit stay "proposed".
4. Borderline (total 18 to 20, or one score at 3 where 4 is required): leave "proposed" with a
   note saying what would push it over. Under 18: reject with the reason.
5. Log one event per decision (crew "Atlas", e.g. "Auto-approved Friendsgiving Party Kit:
   hosts, 23/30, clear gap vs top 3") and count them. Set crew/atlas idle.

## Audit

| Check | Pass condition |
|-------|---------------|
| Grayson's calls untouched | No brief with a human decidedBy was changed |
| Cap | Approved this run <= buildsPerRun |
| Reasons | Every decision carries one plain sentence with the buyer and the evidence |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Decided briefs | briefs/<id> | approved / rejected / proposed + note |
| Events | events/<day key> | one line per decision |
| Run notes | `../output/<day key>-run.md` | "## Judge" section: approved titles, counts |
