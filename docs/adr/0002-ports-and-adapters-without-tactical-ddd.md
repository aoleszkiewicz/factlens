# ADR-0002 — Ports and adapters, without aggregates or domain events

**Status:** accepted

## Decision

A hexagonal architecture: a domain core with no imports from PyTorch, the web framework or any I/O
library, surrounded by adapters behind explicit ports.

DDD's tactical patterns are deliberately **omitted**. There are no aggregates, no repositories and
no domain events.

## Context

The domain is a pure function: `Article Text → Assessment`.

## Why the tactical patterns are omitted

| Pattern | What it solves | Why it does not apply |
|---|---|---|
| **Aggregate** | A consistency boundary — several objects that must change together under an invariant, enforced transactionally | An **Assessment** is derived once and never mutated. No lifecycle, no state transition, no second object that could drift out of agreement. The root would guard nothing. |
| **Repository** | Fetching persisted state | The system is stateless. Nothing is stored, so there is nothing to fetch. |
| **Domain events** | Decoupling a producer from subscribers | There are no subscribers. |

## What does earn its place

- **Value objects, where they constrain something.** `ArticleText` enforces non-empty, length bounds
  and normalisation in one place, so no adapter can smuggle a raw string into the core.
  `CredibilityScore` enforces its bounds and owns the threshold → **Verdict Band** mapping — the
  place where ADR-0001's framing becomes executable.
- **Ports** — `Classifier`, `Explainer`, `ArticleIngestor` — so the domain depends on interfaces
  rather than on torch or HTTP.
- **A stateless domain service**, `CredibilityAssessor`, orchestrating them.
- **A ubiquitous language**, maintained in `CONTEXT.md`.

## Consequences

**The `Classifier` port makes the comparison chapter cheap.** The fine-tuned transformer and the
TF-IDF baseline implement the same interface, so they are swapped rather than reimplemented, and a
fake adapter makes the domain unit-testable without loading a model.

**The `ArticleIngestor` port keeps a browser extension a later second adapter** rather than a
rewrite, even though building one is out of scope.

**The import rule needs mechanical enforcement** — a lint rule or import-linter contract. "The
domain does not import torch" degrades to a suggestion the moment it is only written down.

**Recording the omission matters as much as the choice.** A reader who sees hexagonal architecture
and expects aggregates should find the reasoning here rather than assume they were forgotten.
Tactical DDD exists to tame rich, mutable, concurrently-modified domains; applying it to a pure
function would be ceremony.
