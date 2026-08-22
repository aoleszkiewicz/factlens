# Issue tracker: GitHub

Issues and PRDs live as GitHub issues in `aoleszkiewicz/factlens`. Use the `gh` CLI; it infers the
repo inside a clone.

**When a skill says "publish to the issue tracker"**, create a GitHub issue. **When it says "fetch
the relevant ticket"**, run `gh issue view <number> --comments`.

**PRs as a request surface: no.** _(Set to `yes` to run external PRs through the same labels and
states as issues, via the `gh pr` equivalents.)_ GitHub shares one number space across issues and
PRs, so a bare `#42` may be either — resolve with `gh pr view 42`, fall back to `gh issue view 42`.

## Scrum: EPIC → US → TASK

Every ticket is one of three node types, and the type is written in three places because three
different consumers read it: the title prefix (a human scanning a list), a label (issue filters),
and the board's `Typ` field (slicing the kanban).

| Type | Title prefix | Label | Board `Typ` | Role |
|---|---|---|---|---|
| Epic | `[EPIC][Obszar]` | `epic` | `EPIC` | Root node. Stays out of `In Progress`; closes when its stories close. |
| User Story | `[US][Obszar]` | `user-story` | `User Story` | Unit of value and of sprint planning. A container. |
| Task | `[TASK][Obszar]` | `task` | `Task` | Unit of execution — the cards that move daily. |

Titles are Polish, infinitive verb first:
`[TASK][Domena] Napisać testy rdzenia oparte o atrapy portów`.

A story's body carries `Jako … chcę … aby …`, a context paragraph, and acceptance criteria as
checkboxes. A task's body carries `**Opis.**` and `**DoD:**`. Every child opens with its parents:
`**User Story:** #N · **EPIC:** #M`.

Worked examples of all three live in the issues themselves — #16 is the epic, #17 a story, #50 a task.

### Hierarchy is native sub-issues

```bash
ID=$(gh api repos/aoleszkiewicz/factlens/issues/<child> --jq .id)   # database id, not #number
gh api --method POST repos/aoleszkiewicz/factlens/issues/<parent>/sub_issues -F sub_issue_id=$ID
```

This drives the epic's progress bar and the board's `Parent issue` field, which a markdown checklist
leaves empty. Read a parent's children back with `gh api repos/…/issues/<n>/sub_issues`.

### Labels

- **Type**: `epic` / `user-story` / `task`
- **Area** (swimlane): `area:domain`, `area:corpus`, `area:training`, `area:screening`,
  `area:thesis`, `area:infra`
- **Status**: `status:*` mirrors the board and survives as a fallback filter in the issues list.
  Read progress from the board, which is where status is authoritative.
- **Triage**: see [`triage-labels.md`](./triage-labels.md)

## The board

<https://github.com/users/aoleszkiewicz/projects/1> — user-scoped, project number `1`.

```
PROJECT   PVT_kwHOBAmRbM4BhI2X
Status    PVTSSF_lAHOBAmRbM4BhI2XzhgFv1I
          Backlog f9ffdeb8 · Sprint e3c76637 · In Progress 5ea7c66c
          Review db0919d2 · Blocked 77f6a12f · Done d124879b
Typ       PVTSSF_lAHOBAmRbM4BhI2XzhgFwXo
          EPIC 52132196 · User Story 0d4761fe · Task 77205ad9
```

```bash
gh project item-add 1 --owner aoleszkiewicz --url <issue-url> --format json   # → item id
gh project item-edit --id <item> --project-id PVT_kwHOBAmRbM4BhI2X \
  --field-id PVTSSF_lAHOBAmRbM4BhI2XzhgFv1I --single-select-option-id <option>
gh project item-list 1 --owner aoleszkiewicz --limit 100 --format json
```

Each edit is a round-trip of roughly two seconds, so a pass over forty cards runs for minutes: run it
in the background and checkpoint the issue→item mapping to a file, or a timeout loses it.

### Moving cards

Set the status yourself as the work moves, at the moment it moves:

| Column | Set it when |
|---|---|
| `Backlog` | The ticket is created. |
| `Sprint` | It meets the Definition of Ready and is next up. |
| `In Progress` | You start it. Two cards here at once, at most. |
| `Review` | Evidence exists: a commit, a PR, or the written file. |
| `Blocked` | It waits on something outside your control — and comment on the issue with what, and since when. |
| `Done` | The acceptance checkboxes are ticked. Close the issue in the same move. |

The human overrides any of these by dragging a card. Treat the board's current value as the true
one and work from it, rather than re-asserting the value you last wrote.

### Definition of Ready — the bar for `Sprint`

1. Acceptance criteria are written as checkboxes.
2. Dependencies are closed, or named in the body.
3. It fits in one sprint. Split it first if it does not.
4. The evidence of completion is named: a file, a PR, a passing test.

### Definition of Done — the bar for `Done`

1. Every acceptance checkbox is ticked.
2. The change is on `main`.
3. The vocabulary is `CONTEXT.md`'s — the `_Avoid_` lists say which words to keep out.
4. A change to the domain model leaves `CONTEXT.md`, `CONTEXT-MAP.md` and the ADRs agreeing.
5. The issue is closed with a comment pointing at the evidence.

## Wayfinding operations

Used by `/wayfinder`. The **map** is one issue labelled `wayfinder:map` holding the Notes /
Decisions-so-far / Fog body; tickets are its sub-issues, labelled `wayfinder:<type>`
(`research` / `prototype` / `grilling` / `task`).

- **Blocking**: GitHub's native issue dependencies —
  `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`,
  where the blocker's id is its numeric **database id**. GitHub reports open blockers as
  `issue_dependencies_summary.blocked_by`, which is the live gate.
- **Frontier query**: the map's open children, minus any with an open blocker or an assignee; first
  in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolve**: comment the answer, close, then append a context pointer to the map's Decisions-so-far.
