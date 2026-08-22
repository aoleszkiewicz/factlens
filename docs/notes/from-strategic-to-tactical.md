# From strategic to tactical

A working note, not an ADR. **Nothing here is decided.** It records what sits between the strategic
map ([`CONTEXT-MAP.md`](../../CONTEXT-MAP.md), ADR-0003) and the tactical work, plus the
Python-ecosystem choices that fit this project. Promote any of it to an ADR when it is chosen.

---

## CQRS does not fit

CQRS separates a write model from a read model. This system has no write model:

- `Article Text → Assessment` is a pure function.
- Nothing is persisted — the **Ephemeral Store** is a TTL cache keyed by a hash of the Article Text.
- [ADR-0002](../adr/0002-ports-and-adapters-without-tactical-ddd.md) already declined aggregates,
  repositories and domain events on the same reasoning.

Adding CQRS would repeat that ceremony one layer up: an `AssessArticleCommand`, a handler and a bus,
all doing what a function call does.

**The nearby thing that is real** is the **Fast Path** / **Attribution Job** split — synchronous
response, asynchronous continuation, streamed. That is a latency decomposition, not a read/write
decomposition. Calling it CQRS would send a reader looking for a write side that does not exist. Its
home is [#14](https://github.com/aoleszkiewicz/factlens/issues/14).

---

## What belongs in the gap

For a pure-function domain the strategic → tactical gap is thin. What fills it is contracts and
enforcement, not more patterns.

### 1. Two border contracts, as schemas, before any code

The map names five kinds of border. Two carry weight and currently exist only as prose.

**Split Manifest + Label Semantics — the Customer/Supplier contract.**

The failure mode is in `CONTEXT-MAP.md`: one `train_test_split(df, random_state=42)` in Training
re-partitions at the article level, publishers reappear on both sides, and nothing crashes or warns.
A supplier contract that lives only in prose *is* that failure.

It needs three things:

1. A file format for the publisher → fold assignment.
2. A declared `LabelSemantics` enum over the three encodings the map identifies — publisher
   provenance, a fact-checker's verdict on one claim, newsroom of origin.
3. One `assert_manifest_matches(dataset, manifest)` that runs before an epoch does.

Cheapest high-value artifact in the project.

**The Open Host Service protocol.**

FR-8's sequence `accepted → score → progress → attributions → done`, written as an OpenAPI document
plus an explicit schema per SSE event. Publishing it means it exists independently of the server that
serves it, and the frontend adapter is written against a document rather than against the API code.

### 2. Mechanical enforcement of the hexagon

ADR-0002 states the requirement outright: *"the import rule needs enforcing mechanically … because
'the domain does not import torch' degrades to a suggestion the moment it is only written down."*

Set the contract up while the layers are still empty and it is never violated. Add it after `src/` is
populated and it costs a day of untangling.

### 3. The application surface

Not commands, not a bus. Just the enumeration:

| Runtime | Offline |
|---|---|
| assess (Fast Path) | `build_split_manifest` |
| start attribution | `train` |
| stream progress | `evaluate` |
| collect Assessment | |

If the list stays this short — it does — no application layer is needed. The domain service
`CredibilityAssessor` plus adapters is enough. Worth a one-paragraph ADR in the same spirit as the
other omissions.

There is no EventStorming session worth running on a pure function, and no model-refinement step
left to do. That refinement is `CONTEXT.md`.

---

## Python ecosystem, filtered for this project

### Adopt

| Tool | Why |
|---|---|
| **`import-linter`** | The direct answer to ADR-0002's enforcement requirement. A `layers` contract (`api > domain`, `model > domain`) plus a `forbidden` contract (domain must not import `torch`, `fastapi`, `transformers`, `pandas`), failing in CI. |
| **`typing.Protocol` for ports**, not ABCs | Structural typing means `Classifier` is satisfied by the fine-tuned transformer, the TF-IDF baseline and a three-line test fake — no inheritance, no import from domain into adapters. This is what makes "swapped rather than reimplemented" cheap. |
| **Frozen dataclasses in the core; Pydantic only at the edge** | `frozen=True, slots=True`. `ArticleText` and `CredibilityScore` stay dependency-free; Pydantic lives in the web adapter and translates inbound. Otherwise the domain becomes a serialisation format with methods. |
| **`hypothesis`** | `CredibilityScore` owns the threshold → **Verdict Band** mapping. Property tests over `[0,1]` catch band-boundary off-by-ones that example-based tests miss, and score → band monotonicity is a one-line property. |
| **`pandera`** (or plain Pydantic row models) | At the **Corpus Adapter**. The ACL must reject a corpus that cannot declare its Label Semantics; schema validation at that border is the ACL made executable. |

### Know, with a caveat

**"Architecture Patterns with Python"** (Percival & Gregory — *Cosmic Python*, free online) is what
the Python community means by DDD.

- Chapters 2–4 — repository, ports, dependency inversion: useful vocabulary.
- Chapters 7–12 — aggregates, Unit of Work, events, message bus, CQRS: precisely the half ADR-0002
  refused.

A good book that would mislead if followed end to end.

### Skip

- `returns` / monadic error handling.
- DI containers (`dependency-injector`, `wired`). With three ports, wiring by hand in `main.py` is
  clearer and a reader can follow it.

---

## Ordering

```
#9 (stack) ─┐
            ├─→ #10 ─→ tactical work
#8 (corpus)─┘
```

**Not blocked by any of them:**

- The Split Manifest contract.
- The SSE contract.
- The **domain core** — value objects, ports, `CredibilityAssessor`. Per ADR-0002 it imports neither
  torch nor a framework, so neither the stack nor the corpus choice moves it. That half was bundled
  into #10 by accident and belongs to
  [#39](https://github.com/aoleszkiewicz/factlens/issues/39).

Neither depends on the framework choice, nor on corpus access
([#13](https://github.com/aoleszkiewicz/factlens/issues/13)) or GPU
([#15](https://github.com/aoleszkiewicz/factlens/issues/15)) having landed.

**`import-linter` is the exception.** An earlier version of this note had it as writable today. A
`forbidden` contract needs package paths to name, and those are chosen by #10's layout half — before
that it either errors on a package that does not exist, or passes vacuously. It is gated on #10, not
on #8 or #9.
