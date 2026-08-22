# Three bounded contexts, and corpora enter through an anticorruption layer

FactLens is mapped as three Bounded Contexts — **Corpus**, **Training** and **Screening** — with
external corpora reaching Corpus through an **anticorruption layer** whose contract forces every
adapter to declare its Label Semantics and its Label Gap. The map is
[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md); this ADR records why the boundaries fall there and, just
as importantly, why several obvious candidates are *not* contexts.

The map exists to make the thesis's central claim visible rather than to organise code. That claim
is that **the label is not the phenomenon**, and a context map is the standard notation for exactly
that: the **Label Gap** is not a caveat in the dataset chapter, it is the measured cost of a
translation between two contexts that use "unreliable" to mean different things.

## Considered options

**Five contexts, following the pipeline** — Corpus, Training, Evaluation, Monitoring, and a UI or
backend context. Rejected. `Corpus → Training → Evaluation` is a dataflow; its arrows say "happens
after", never "translates into". Evaluation's vocabulary (MCC, F1-unreliable, the source-disjoint
gap, the reliability diagram) is continuous with Training's, so a boundary there separates nothing.
Monitoring is a Generic Subdomain: latency and queue depth mean the same thing here as anywhere, so
there is no model to protect. And the fact that the API had no obvious home on that map was the
diagnostic — it was a map of tiers, not of languages.

**One context, per ADR-0002's minimalism** — the domain is a pure function, so draw one box.
Rejected because `CONTEXT.md` already contained two glossaries stacked in one file: a reader-facing
vocabulary and a corpus-facing one, sharing the word *unreliable* while meaning different things by
it. That difference is the thesis.

**Conformist to `misinfo-general`, other corpora as one-off scripts.** Rejected. Three corpora serve
three different jobs simultaneously — primary, Contrast Experiment, transfer set — so multiple
adapters are a present requirement rather than speculative generality. The access risk on
[#13](https://github.com/aoleszkiewicz/factlens/issues/13) is hedged as a side effect, not as the
justification.

**A plain `(text, label)` corpus port.** Rejected as the most dangerous option on the list.
`misinfo-general` labels publisher provenance (43.5% of "unreliable"-publisher articles are clearly
non-credible), ISOT labels which of two newsrooms wrote the piece, ReCOVery labels a fact-checker's
verdict on a COVID claim. A port that makes those substitutable launders three incompatible concepts
into one type and hides the Label Gap inside the adapter — the precise failure ADR-0001 exists to
prevent.

**Corpus and Training as one context.** A defensible call: their languages do not actually conflict.
Split anyway, because the corpus decisions in
[#8](https://github.com/aoleszkiewicz/factlens/issues/8) are graded thesis deliverables and the
dataset chapter needs somewhere to stand.

## Consequences

Corpus and Training are joined by a **Shared Kernel** — the Split Manifest, the Label Semantics and
the masking rule must mean exactly the same thing on both sides. This is the most expensive
relationship in DDD and the discipline is entirely self-imposed here, but the failure it prevents is
silent: a single `train_test_split(df, random_state=42)` in Training re-partitions at the article
level, publishers reappear across folds, and every evaluation number becomes an ISOT number without
anything crashing. Training must assert against the manifest before an epoch runs.

The **Model Artifact** becomes a contract rather than a checkpoint path: weights, tokeniser,
calibration temperature, derived Verdict Band boundaries and the measured Label Gap travel together.
Only one consumer exists today, so "Published Language" is partly aspirational, and versioning it is
work that would otherwise be skipped.

The `Classifier` port is now named as the anticorruption layer, which sharpens ADR-0002 rather than
contradicting it: that ADR argued the strategic half of DDD earns its place while the tactical half
does not, and this is the strategic half being spent.

**Monitoring having no box does not remove the obligation.** NFR-1, NFR-2, NFR-3 and NFR-6 are
marked testable, and thesis task 7 requires demonstrating them; a p95 that was never recorded cannot
be reported. Monitoring is realised as instrumentation in Screening's adapter layer.

Two honest costs. Five boxes over roughly 800 lines of Python invites the charge of ceremony — the
map is defensible only because it explains a claim, not because it organises code. And the ACL makes
the *seam* cheap while leaving the *swap* expensive: changing the primary corpus invalidates the
Model Artifact, the temperature, the band boundaries and the whole evaluation chapter. The map must
not be read as promising a cheap migration.

The contexts are deliberately **not** yet separate directories. `src/` is laid out by tier and the
target package layout is [#10](https://github.com/aoleszkiewicz/factlens/issues/10), still open;
splitting the glossary into per-context files before then would mean guessing paths and moving them
again.

## Amendments

The reasoning above is left as it was decided. These entries record where it has since changed, and
why — the decisions, not the deliberation, are what `CONTEXT-MAP.md` reflects.

### 2026-08-21 — Corpus → Training is Customer/Supplier, not Shared Kernel

The consequences section drew this border as a Shared Kernel. That was the wrong pattern. A Shared
Kernel is a model **either side may change**, which is why it imposes a standing two-way veto and is
the most expensive relationship in DDD. Nothing in this design lets Training author a Split Manifest
or redefine Label Semantics: Corpus produces both, Training consumes them and asserts before an
epoch runs. The obligation runs one way.

**Customer/Supplier** says exactly that, and costs less. Training is not a Conformist either — its
needs are a budgeted obligation on Corpus's plan, not something it works around.

The failure the border exists to prevent is unchanged, and so is the assertion that prevents it.

### 2026-08-21 — the Corpus/Training split is a lifecycle boundary, not a language boundary

The option list above records the Corpus-and-Training-as-one-context alternative as *"a defensible
call: their languages do not actually conflict"*. That is now checked rather than asserted: no term
means two different things across that border. Every shared term is identical, and every unshared
term is simply absent on the other side.

So the split is a deliberate compromise — a context boundary drawn on a lifecycle-and-deliverable
seam rather than on a meaning seam — and it is kept for the reason originally given. Recording it
plainly matters, so that a reader does not assume the languages were believed to conflict.

The border that *does* carry a meaning conflict is Corpus↔Screening: **Unreliable Content** is a
property of the Publisher in one and a property of the text in the other. That conflict is now
visible as two glossary entries under the same name, which is where the argument for drawing more
than one box actually lives.

### 2026-08-21 — Training realises a Generic subdomain

This ADR presents all three contexts as peers without classifying the problem space. `CONTEXT-MAP.md`
now carries a subdomain table, and Training's row reads **Generic**: a standard fine-tune of an
upstream checkpoint plus one scalar of temperature scaling. Nothing in it is specific to FactLens.

Generic does not mean unimportant, and it does not mean the box goes away — Training remains a
Bounded Context and a required part of the system's lifecycle. It means the thinking is not spent
there. The two things that make the evaluation numbers trustworthy both sit upstream: the Split
Manifest that Corpus authors, and the Label Gap that Corpus measures.

Conceding this strengthens the thesis rather than weakening it. The likeliest challenge — *"you
fine-tuned a transformer, so did everyone"* — is answered by agreeing, and pointing at where the
work actually is.

### 2026-08-21 — the map does constrain the code layout

The opening of this ADR says the map exists *"to make the thesis's central claim visible rather than
to organise code."* That sentence was written to answer the ceremony charge — five boxes over
roughly 800 lines of Python — and it overcorrected.

Both purposes hold. The map makes the claim visible **and** it constrains the package layout: the
strategic model is settled first precisely so that the tactical refactor in
[#10](https://github.com/aoleszkiewicz/factlens/issues/10) has something to be refactored *toward*.
Read the original sentence as a rejection of maps drawn from tiers, not as a disclaimer of purpose.
