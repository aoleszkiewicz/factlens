# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT-MAP.md`** at the repo root — which Bounded Context you are working in, and what
  has to be translated at its borders
- **`CONTEXT.md`** at the repo root
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

This repo has **three Bounded Contexts** — Corpus, Training and Screening — but they are **not yet
separate directories**. The target package layout is
[#10](https://github.com/aoleszkiewicz/factlens/issues/10), still open; until it settles, the
vocabulary for all three lives in one root `CONTEXT.md`, with its term groups tagged by owning
context.

```
/
├── CONTEXT-MAP.md          ← the three contexts and their relationships
├── CONTEXT.md              ← one glossary, groups tagged by context
├── docs/adr/
│   ├── 0001-....md
│   ├── 0002-....md
│   └── 0003-....md
└── src/                    ← still laid out by tier, not by context
```

So: read the map to work out which context your task sits in, then use that context's terms from
`CONTEXT.md`. Don't split the glossary into per-context files until #10 has chosen the paths.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
