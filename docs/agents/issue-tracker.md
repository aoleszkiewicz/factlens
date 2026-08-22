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

| Column | Set it when | Invariant that must hold while it sits there |
|---|---|---|
| `Backlog` | The ticket is created and nothing stops it being picked up. | No open blocker. |
| `Sprint` | It meets the Definition of Ready and is next up. | No open blocker. |
| `In Progress` | You start it. Two task cards here at once, at most. | The issue is open. |
| `Review` | Evidence exists: a commit, a PR, or the written file. | The issue is open. |
| `Blocked` | It has an open blocker, or waits on something outside your control. | A recorded `blocked_by` edge, or a comment saying what and since when. |
| `Done` | The acceptance checkboxes are ticked **and the issue is closed**. | The issue is closed. |

The human overrides any of these by dragging a card. Treat the board's current value as the true
one and work from it, rather than re-asserting the value you last wrote.

**`Backlog` means startable.** The column answers "what may I pick up next?", so anything with an
open blocker belongs in `Blocked`, not in `Backlog`. This is the rule that keeps the board readable:
a card in `Backlog` or `Sprint` needs no further reasoning before work begins.

**`Done` and closed are one move, not two.** A card in `Done` whose issue is still open is the drift
that hollows the board out: the epic's sub-issue progress bar reads it as outstanding, the `Done`
column grows without bound, and the count of remaining work is wrong everywhere it is quoted. Close
the issue with a comment pointing at the evidence in the same breath as you move the card.

### Parents follow their children

An EPIC and a US are containers. Their status is **derived**, never set by hand, and re-derived
every time a child moves. First rule that matches wins:

| The parent shows | When |
|---|---|
| `Blocked` | It has an open blocker of its own, or every unfinished child is `Blocked`. |
| `Done` | Every child is `Done` **and** its own acceptance checkboxes are ticked. |
| `In Progress` | Any child is `Done`, `Sprint`, `In Progress` or `Review`, and work remains. |
| `Backlog` | Otherwise. |

A parent whose children are all `Done` but whose own acceptance criteria are not all ticked is
`In Progress`, not `Done` — the unticked box is real remaining work, and closing over it is how a
criterion gets quietly lost. Leave the box unticked, say in a comment what is missing, and let the
column say `In Progress`.

### Blocking is recorded, not narrated

A dependency written in prose in a body — "after #10 is settled" — is invisible to every query and
to the board. Record it as a **native GitHub dependency**, which surfaces as the live
`issue_dependencies_summary.blocked_by` gate and on the card itself:

```bash
BLOCKER=$(gh api repos/aoleszkiewicz/factlens/issues/<blocker> --jq .id)   # database id
gh api --method POST repos/aoleszkiewicz/factlens/issues/<blocked>/dependencies/blocked_by \
  -F issue_id=$BLOCKER
gh api repos/aoleszkiewicz/factlens/issues/<blocked>/dependencies/blocked_by --jq '[.[].number]'
```

Remove one with `DELETE …/dependencies/blocked_by/<blocker-db-id>`.

Both US↔US and TASK↔TASK edges are in scope. Two rules keep the edges useful rather than decorative:

1. **Record the edge at the narrowest level that is true.** If one task of a story is startable
   today, the story is not blocked — block the specific task instead. A story-level edge that
   freezes startable children makes the board *less* readable, not more.
2. **The blocker must be a ticket, not a wish.** If the thing being waited on has no issue, open one
   first. `Blocked` with nothing to point at is indistinguishable from forgotten.

When a blocker closes, its dependents become startable: move them out of `Blocked` in the same pass.

### Reading the board

- **`Blocked`** is the plan: what is coming, and what has to land first.
- **`Backlog` and `Sprint`** are the offer: everything there can be started right now.
- **`In Progress` and `Review`** are today, held to two task cards.
- **`Done`** is closed issues only, and the epics' progress bars agree with it.

The board carries both work tracks. Scrum nodes are typed `EPIC` / `User Story` / `Task` and labelled
`epic` / `user-story` / `task`; the exploratory `/wayfinder` track keeps its `wayfinder:*` labels and
is typed `Task` (its map is typed `EPIC`). Filter by label to see one track alone. Nothing in the
repo stays off the board — an issue that is not on it is invisible to every count the board reports,
including as somebody else's blocker.

### Audit before you trust it

The invariants above decay silently. `scripts/board_audit.py` checks all of them — cards in `Done`
with open issues, parents disagreeing with their children, open blockers outside `Blocked`, `Blocked`
cards with no blocker, `status:*` labels out of step, unticked boxes under `Done`, issues missing
from the board, and the WIP limit:

```bash
python3 scripts/board_audit.py       # report; exits 1 when anything drifted
```

Run it at the start of a session that touches the tracker and again before you hand work back. It
only reads, and it walks one issue at a time, so a full pass takes a couple of minutes — start it in
the background and read the report when it lands. Fix what it names rather than explaining it away.

**It also runs itself.** `.claude/settings.json` registers `scripts/board_audit_hook.sh` as an
async `Stop` hook, so the session that wrote to the board is the one that gets audited — the drift is
agent-generated, and catching it at the end of the session that caused it is cheaper than finding a
pile of it months later. Being async, it never delays session exit. It throttles to one run per 30
minutes, skips silently when `gh` is missing or logged out, and always exits 0 so a tracker check can
never block a session. The report lands in `.claude/board-audit.log` (gitignored); a session that
ends with findings says so on the way out.

### Definition of Ready — the bar for `Sprint`

1. Acceptance criteria are written as checkboxes.
2. Every dependency is recorded as a `blocked_by` edge, and every one of them is closed. An open
   blocker means the card belongs in `Blocked` instead.
3. It fits in one sprint. Split it first if it does not.
4. The evidence of completion is named: a file, a PR, a passing test.

### Definition of Done — the bar for `Done`

1. Every acceptance checkbox is ticked. A box that cannot honestly be ticked keeps the card out of
   `Done` — split the remainder into its own ticket rather than closing over it.
2. The change is on `main`.
3. The vocabulary is `CONTEXT.md`'s — the `_Avoid_` lists say which words to keep out.
4. A change to the domain model leaves `CONTEXT.md`, `CONTEXT-MAP.md` and the ADRs agreeing.
5. The issue is closed with a comment pointing at the evidence — in the same move as the card
   reaches `Done`, never later.
6. Anything this ticket was blocking is re-examined: dependents that are now startable leave
   `Blocked`, and the parent's status is re-derived.

## Wayfinding operations

Used by `/wayfinder`. The **map** is one issue labelled `wayfinder:map` holding the Notes /
Decisions-so-far / Fog body; tickets are its sub-issues, labelled `wayfinder:<type>`
(`research` / `prototype` / `grilling` / `task`).

- **Blocking**: the same native dependencies as the Scrum track — see
  [Blocking is recorded, not narrated](#blocking-is-recorded-not-narrated).
- **Frontier query**: the map's open children, minus any with an open blocker or an assignee; first
  in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolve**: comment the answer, close, then append a context pointer to the map's Decisions-so-far.
