# CLAUDE.md

## Agent skills

### Issue tracker

GitHub issues in `aoleszkiewicz/factlens`, via the `gh` CLI. Work is tracked in Scrum form — EPIC →
US → TASK as native sub-issues — on the kanban board at `users/aoleszkiewicz/projects/1`, where you
set a card's status as the work moves. Three rules the board depends on: `Done` and closing the
issue are one move; a parent's status is derived from its children, never set by hand; and every
dependency is a recorded `blocked_by` edge, which keeps `Backlog` meaning "startable". Verify with
`python3 scripts/board_audit.py`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Three Bounded Contexts — Corpus, Training, Screening — mapped in `CONTEXT-MAP.md`, with one
root `CONTEXT.md` and `docs/adr/` until #10 settles the package layout. See `docs/agents/domain.md`.
