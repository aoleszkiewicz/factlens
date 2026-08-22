# ADR-0003 — Three bounded contexts, and corpora enter through an anticorruption layer

**Status:** accepted, with amendments (see below)

## Decision

Three Bounded Contexts — **Corpus**, **Training** and **Screening** — mapped in
[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md).

External corpora reach Corpus through an **anticorruption layer** whose contract forces every
adapter to declare its Label Semantics and its Label Gap.

## Context

The map exists to make the thesis's central claim visible: **the label is not the phenomenon**. A
context map is the standard notation for exactly that. The **Label Gap** is not a caveat in the
dataset chapter — it is the measured cost of translating between two contexts that use "unreliable"
to mean different things.

The map also constrains the package layout. The strategic model is settled first so that the
tactical work in [#10](https://github.com/aoleszkiewicz/factlens/issues/10) has something to be
refactored toward.

## Considered options

### Five contexts, following the pipeline

Corpus, Training, Evaluation, Monitoring, and a UI or backend context. **Rejected.**

- `Corpus → Training → Evaluation` is a dataflow. Its arrows say "happens after", never
  "translates into".
- Evaluation's vocabulary (MCC, F1-unreliable, the source-disjoint gap, the reliability diagram) is
  continuous with Training's, so a boundary there separates nothing.
- Monitoring is a Generic Subdomain: latency and queue depth mean the same here as anywhere.
- The API had no obvious home on that map. That was the diagnostic — it was a map of tiers, not of
  languages.

### One context, per ADR-0002's minimalism

The domain is a pure function, so draw one box. **Rejected.** `CONTEXT.md` already contained two
glossaries stacked in one file: a reader-facing vocabulary and a corpus-facing one, sharing the word
*unreliable* while meaning different things by it. That difference is the thesis.

### Conformist to `misinfo-general`, other corpora as one-off scripts

**Rejected.** Three corpora serve three jobs simultaneously — primary, Contrast Experiment, transfer
set — so multiple adapters are a present requirement rather than speculative generality. The access
risk on [#13](https://github.com/aoleszkiewicz/factlens/issues/13) is hedged as a side effect, not
as the justification.

### A plain `(text, label)` corpus port

**Rejected — the most dangerous option on the list.**

| Corpus | What its label encodes |
|---|---|
| `misinfo-general` | Publisher provenance (43.5% of "unreliable"-publisher articles are clearly non-credible) |
| ISOT | Which of two newsrooms wrote the piece |
| ReCOVery | A fact-checker's verdict on a COVID claim |

A port that makes those substitutable launders three incompatible concepts into one type and hides
the Label Gap inside the adapter — the precise failure ADR-0001 exists to prevent.

### Corpus and Training as one context

A defensible call: their languages do not conflict. **Split anyway**, because the corpus decisions
in [#8](https://github.com/aoleszkiewicz/factlens/issues/8) are graded thesis deliverables and the
dataset chapter needs somewhere to stand.

## Consequences

**Corpus and Training are joined by a Shared Kernel.** *(Superseded — see amendment 1. The third
item, the "masking rule", is open in [#54](https://github.com/aoleszkiewicz/factlens/issues/54).)*
The Split Manifest, the Label Semantics and the masking rule must mean the same thing on both sides. The
failure this prevents is silent: a single `train_test_split(df, random_state=42)` in Training
re-partitions at the article level, publishers reappear across folds, and every evaluation number
becomes an ISOT number without anything crashing. Training must assert against the manifest before
an epoch runs.

**The Model Artifact becomes a contract rather than a checkpoint path.** Weights, tokeniser,
calibration temperature, derived Verdict Band boundaries and the measured Label Gap travel together.
Only one consumer exists today, so "Published Language" is partly aspirational, and versioning it is
work that would otherwise be skipped.

**The `Classifier` port is named as the anticorruption layer.** This sharpens ADR-0002 rather than
contradicting it: that ADR argued the strategic half of DDD earns its place while the tactical half
does not, and this is the strategic half being spent.

**Monitoring having no box does not remove the obligation.** NFR-1, NFR-2, NFR-3 and NFR-6 are
marked testable, and thesis task 7 requires demonstrating them. A p95 that was never recorded cannot
be reported. Monitoring is realised as instrumentation in Screening's adapter layer.

### Two honest costs

1. **Ceremony.** Five boxes over roughly 800 lines of Python invites the charge. The map is
   defensible because it explains a claim, not because it organises code.
2. **The swap is not cheap.** The ACL makes the *seam* cheap while leaving the *swap* expensive.
   Changing the primary corpus invalidates the Model Artifact, the temperature, the band boundaries
   and the whole evaluation chapter. The map must not be read as promising a cheap migration.

### Directory layout

The contexts are deliberately **not** yet separate directories. `src/` is laid out by tier and the
target layout is [#10](https://github.com/aoleszkiewicz/factlens/issues/10), still open. Splitting
the glossary into per-context files before then would mean guessing paths and moving them again.

---

## Amendments

The reasoning above is left as it was decided. These entries record where it has since changed.
`CONTEXT-MAP.md` reflects the decisions, not the deliberation.

| # | Date | Change |
|---|---|---|
| 1 | 2026-08-21 | Corpus → Training is Customer/Supplier, not Shared Kernel |
| 2 | 2026-08-21 | The Corpus/Training split is a lifecycle boundary, not a language boundary |
| 3 | 2026-08-21 | Training realises a Generic subdomain |
| 4 | 2026-08-21 | The map does constrain the code layout |

### 1 — Customer/Supplier, not Shared Kernel

A Shared Kernel is a model **either side may change**, which imposes a standing two-way veto and is
the most expensive relationship in DDD.

Nothing in this design lets Training author a Split Manifest or redefine Label Semantics. Corpus
produces both; Training consumes them and asserts before an epoch runs. The obligation runs one way,
and **Customer/Supplier** says exactly that at lower cost.

Training is not a Conformist either — its needs are a budgeted obligation on Corpus's plan, not
something it works around.

The failure the border prevents is unchanged, and so is the assertion that prevents it.

### 2 — A lifecycle boundary, not a language boundary

The option list records the one-context alternative as *"a defensible call: their languages do not
actually conflict."* That is now checked rather than asserted: no term means two different things
across the border. Every shared term is identical; every unshared term is absent on the other side.

So the split is a deliberate compromise — a context boundary on a lifecycle-and-deliverable seam
rather than a meaning seam — kept for the reason originally given. Recorded plainly so no reader
assumes the languages were believed to conflict.

The border that *does* carry a meaning conflict is Corpus ↔ Screening: **Unreliable Content** is a
property of the Publisher in one and a property of the text in the other.

### 3 — Training realises a Generic subdomain

This ADR presents all three contexts as peers without classifying the problem space.
`CONTEXT-MAP.md` now carries a subdomain table, and Training's row reads **Generic**: a standard
fine-tune of an upstream checkpoint plus one scalar of temperature scaling.

Generic does not mean unimportant, and the box does not go away. Training remains a Bounded Context
and a required part of the lifecycle. It means the thinking is not spent there. The two things that
make the evaluation numbers trustworthy both sit upstream: the Split Manifest Corpus authors, and
the Label Gap Corpus measures.

Conceding this strengthens the thesis. The likeliest challenge — *"you fine-tuned a transformer, so
did everyone"* — is answered by agreeing, and pointing at where the work actually is.

### 4 — The map does constrain the code layout

The opening originally read: *"the map exists to make the thesis's central claim visible rather than
to organise code."* That sentence answered the ceremony charge and overcorrected.

Both purposes hold. Read the original as a rejection of maps drawn from tiers, not as a disclaimer
of purpose. The Context section above now states both.
