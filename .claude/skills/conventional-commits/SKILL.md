---
name: conventional-commits
description: Write a git commit message, amend one, or check a commit or PR title against this repo's Conventional Commits format.
---

# Conventional Commits

This repo's variant of the Conventional Commits spec. Nothing enforces it — no commitlint, no
commit-msg hook — so this file is the format's only source of truth.

## Subject

```
type(scope)!: summary
```

Under 72 characters. Lowercase after the colon, imperative mood, no trailing period.

| Type       | Use for                                                          |
| ---------- | ---------------------------------------------------------------- |
| `feature`  | New behaviour, including new domain vocabulary or docs that define it |
| `fix`      | Corrects behaviour that was wrong                                |
| `refactor` | Same behaviour, different shape                                  |
| `docs`     | Reports, presentations, README — prose that isn't the domain model |
| `test`     | Tests only                                                       |
| `chore`    | Tooling, config, dependencies, agent workflow files              |
| `ci`       | `.github/workflows` and the checks they run                      |

Write `feature`, not the spec's `feat` — this repo spells it out, and `git log` is the tiebreaker
for anything this table leaves open.

**Scope** is optional and lowercase. Use the owning Bounded Context (`corpus`, `training`,
`screening`) when the change belongs to one; use `domain` for changes to the model itself —
`CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`. Otherwise name the area (`data`, `ci`, `notebooks`).

`!` before the colon marks a breaking change, and the body then carries a `BREAKING CHANGE: `
footer saying what breaks and what callers do instead.

## Body

Wrap at 72 columns. Say **why** — the subject already says what. A one-line change to a threshold
with a paragraph of reasoning behind it is a good commit; the reasoning is the part that can't be
recovered from the diff.

Name domain concepts with the terms defined in `CONTEXT.md`, capitalised as the glossary
capitalises them. A commit that introduces a term the glossary doesn't have yet is a signal for
`/domain-modeling`, not a licence to coin one in the log.

Close issues with a trailer on its own line, so the tracker and the board stay in step:

```
Resolves #54
```

Use `Refs #54` when the commit advances an issue without closing it. Prose may also mention the
issue for context, but the closing keyword has to stand alone to fire.

## Done when

- The subject parses as `type(scope): summary` with a type from the table above
- The body says why, in glossary vocabulary
- Every issue the change closes appears in a `Resolves` trailer
- The message ends at its last content line — authorship is the git author field, and the log
  carries no agent attribution or session links
