# Ports and adapters, without aggregates or domain events

FactLens is built as a hexagonal architecture — a domain core with no imports from PyTorch, the web framework, or any I/O library, surrounded by adapters behind explicit ports. It deliberately **omits** DDD's tactical patterns: there are no aggregates, no repositories and no domain events. The domain is a pure function, `Article Text → Assessment`, and those patterns solve problems it does not have.

## Why the tactical patterns are omitted

An aggregate is a consistency boundary: a cluster of objects that must change together under an invariant, enforced transactionally by a root. The test is whether an invariant spans several objects and must hold at every commit under concurrent modification. In this domain an **Assessment** is derived once and never mutated; there is no lifecycle, no state transition, and no second object that could drift out of agreement with the first. An aggregate here would be a struct in costume, and its root would guard nothing.

**Repositories** follow from persistence, and FactLens is stateless — nothing is stored, so there is nothing to fetch. **Domain events** decouple a producer from subscribers; there are no subscribers.

What does earn its place is the strategic half of DDD, plus the parts of the tactical half that carry real invariants:

- **Value objects** where they constrain something. `ArticleText` enforces non-empty, length bounds and normalisation in one place, so no adapter can smuggle a raw string into the core. `CredibilityScore` enforces its bounds and owns the threshold→**Verdict Band** mapping — genuine domain logic, and the place where ADR-0001's framing becomes executable.
- **Ports** — `Classifier`, `Explainer`, `ArticleIngestor` — so the domain depends on interfaces rather than on torch or HTTP.
- **A stateless domain service**, `CredibilityAssessor`, orchestrating them.
- **A ubiquitous language**, maintained in `CONTEXT.md`.

## Consequences

The `Classifier` port is what makes the thesis's comparison chapter cheap: the fine-tuned transformer and the existing TF-IDF baseline implement the same interface, so they are swapped rather than reimplemented, and a fake adapter makes the domain unit-testable without loading a model. The `ArticleIngestor` port likewise keeps a browser extension a later second adapter rather than a rewrite, even though building one is out of scope.

The import rule needs enforcing mechanically — a lint rule or import-linter contract — because "the domain does not import torch" degrades to a suggestion the moment it is only written down.

Recording the omission matters as much as the choice. A reader who sees hexagonal architecture and expects aggregates should find the reasoning here rather than assume they were forgotten. Tactical DDD exists to tame rich, mutable, concurrently-modified domains; applying it to a pure function would be cargo cult.
