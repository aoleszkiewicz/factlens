# From strategic to tactical

A working note, not an ADR. Nothing here is decided — it records what sits between the strategic
map ([`CONTEXT-MAP.md`](../../CONTEXT-MAP.md), ADR-0003) and the tactical work that
[#10](https://github.com/aoleszkiewicz/factlens/issues/10) will start, plus the Python-ecosystem
choices that fit this project. Promote any of it to an ADR when it is actually chosen.

## CQRS does not fit

CQRS separates a write model from a read model. FactLens has no write model. `Article Text →
Assessment` is a pure function, nothing is persisted (the **Ephemeral Store** is a TTL cache keyed
by a hash of the Article Text), and
[ADR-0002](../adr/0002-ports-and-adapters-without-tactical-ddd.md) already declined aggregates,
repositories and domain events on exactly this reasoning. Adding CQRS would repeat the cargo cult
ADR-0002 names, one layer up: an `AssessArticleCommand`, a handler and a bus, all doing what a
function call does.

The nearby thing that *is* real is the **Fast Path** / **Attribution Job** split — synchronous
response, asynchronous continuation, streamed. That is a latency decomposition, not a read/write
decomposition. Naming it CQRS would send a thesis reader looking for a write side that does not
exist. Its home is [#14](https://github.com/aoleszkiewicz/factlens/issues/14).

## What belongs in the gap

For a pure-function domain the strategic→tactical gap is thin, and what fills it is contracts and
enforcement rather than more patterns.

### 1. The two border contracts, as schemas, before any code

The map names five kinds of border. Two are load-bearing and currently exist only as prose.

**Split Manifest + Label Semantics — the Shared Kernel.** The highest-risk seam on the map, and the
failure mode is already written down in `CONTEXT-MAP.md`: one `train_test_split(df,
random_state=42)` in Training re-partitions at the article level, publishers reappear on both
sides, nothing crashes and nothing warns. A Shared Kernel that lives only in prose *is* that
failure. It needs a file format for the publisher→fold assignment, a declared `LabelSemantics` enum
over the three encodings the map identifies (publisher provenance / a fact-checker's verdict on one
claim / newsroom of origin), and one `assert_manifest_matches(dataset, manifest)` that runs before
an epoch does. Cheapest high-value artifact in the project.

**The Open Host Service protocol.** FR-8's sequence `accepted → score → progress → attributions →
done`, written as an OpenAPI document plus an explicit schema per SSE event. It is a Published
Language; publishing it means it exists independently of the server that happens to serve it, and
the frontend adapter is then written against a document rather than against the API code.

### 2. Mechanical enforcement of the hexagon

ADR-0002 states the requirement outright: *"the import rule needs enforcing mechanically … because
'the domain does not import torch' degrades to a suggestion the moment it is only written down."*
This is pre-code work. Set the contract up while the layers are still empty and it is never
violated; add it after `src/` is populated and it costs a day of untangling.

### 3. The application surface — the handful of entry points

Not commands, not a bus. Just the enumeration: assess (Fast Path), start attribution, stream
progress, collect Assessment; and offline, `build_split_manifest`, `train`, `evaluate`. If the list
stays this short — it does — that confirms no application layer is needed at all: the domain
service `CredibilityAssessor` plus adapters is enough. Worth recording as a one-paragraph ADR in
the same spirit as the other omissions.

There is no EventStorming session worth running on a pure function, and no model-refinement step
left to do — that refinement is `CONTEXT.md`.

## Python ecosystem, filtered for this project

### Adopt

- **`import-linter`** — the direct answer to ADR-0002's enforcement requirement. A `layers`
  contract (`api > domain`, `model > domain`) plus a `forbidden` contract (domain must not import
  `torch`, `fastapi`, `transformers`, `pandas`), failing in CI. Highest value per line of config
  here.
- **`typing.Protocol` for ports**, not ABCs. Structural typing means `Classifier` is satisfied by
  the fine-tuned transformer, the TF-IDF baseline and a three-line test fake, with no inheritance
  and no import from the domain into the adapters. This is what makes ADR-0002's "swapped rather
  than reimplemented" actually cheap.
- **Frozen dataclasses (`frozen=True, slots=True`) for value objects in the core; Pydantic only at
  the edge.** `ArticleText` and `CredibilityScore` stay dependency-free; Pydantic lives in the web
  adapter and translates inbound. Keeping it out of the core is the difference between a domain and
  a serialisation format with methods.
- **`hypothesis`** — earns its place rather than being fashion. `CredibilityScore` owns the
  threshold→**Verdict Band** mapping; property tests over `[0,1]` catch the band-boundary
  off-by-ones that example-based tests miss, and score→band monotonicity is a one-line property.
- **`pandera`** (or plain Pydantic row models) at the **Corpus Adapter** — the ACL has to reject a
  corpus that cannot declare its Label Semantics. Schema validation at that border is the ACL made
  executable.

### Know, with a caveat

- **"Architecture Patterns with Python"** (Percival & Gregory — *Cosmic Python*, free online) is
  what the Python community means by DDD. Chapters 2–4 (repository, ports, dependency inversion)
  are useful vocabulary; chapters 7–12 are aggregates, Unit of Work, events, message bus and CQRS —
  precisely the half ADR-0002 correctly refused. A good book that would mislead if followed
  end-to-end.

### Skip

`returns` / monadic error handling, and DI containers (`dependency-injector`, `wired`). With three
ports, wiring by hand in `main.py` is clearer, and a thesis reader can follow it.

## Ordering

[#9](https://github.com/aoleszkiewicz/factlens/issues/9) (stack) and
[#8](https://github.com/aoleszkiewicz/factlens/issues/8) (corpus and split protocol) gate
[#10](https://github.com/aoleszkiewicz/factlens/issues/10), and #10 gates the tactical work.

The three items above are **not** blocked by any of them. The Split Manifest contract, the SSE
contract and the `import-linter` setup are all writable today, and none depends on whether the
framework is FastAPI or on whether corpus access
([#13](https://github.com/aoleszkiewicz/factlens/issues/13)) and GPU
([#15](https://github.com/aoleszkiewicz/factlens/issues/15)) have landed. That is the work available
while those sit in someone else's queue.
