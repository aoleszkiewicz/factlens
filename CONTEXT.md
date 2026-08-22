# FactLens

A screening system that assesses how strongly a piece of internet text exhibits the characteristics
of unreliable content, and shows the reader which parts of the text drove that assessment.

## Language

Terms are grouped by the Bounded Context that owns them — see [`CONTEXT-MAP.md`](./CONTEXT-MAP.md).

A Ubiquitous Language belongs to *one* context. Two groups below are the exceptions, and both are
declared rather than incidental: **Framing** holds terms owned by no context, and **Kernel** holds
the one term all three contexts must mean identically.

**Unreliable Content** appears twice, under Corpus and under Screening, with different definitions.
That is not an error to be tidied away. The distance between those two entries is the **Label Gap**,
and naming it is what this project is for ([ADR-0001](docs/adr/0001-credibility-assessment-not-truth-verdict.md)).

### Framing — owned by no context

**Disinformation**:
False information deliberately created and spread to deceive. The concept named by the thesis title
— and, critically, **not** what any corpus label encodes. FactLens never claims to detect it
directly.
_Avoid_: Fake news, misinformation, hoax

**Screening Aid**:
The role FactLens is designed to occupy — a tool that directs a reader's attention toward text worth
checking. It is explicitly not an arbiter of truth, and the interface is built to keep that
distinction visible. What a Credibility Score is *for*, as distinct from what it is *of*.

### Kernel — shared by Corpus, Training and Screening

**Label Gap**:
The distance between what a corpus label encodes (publisher provenance, a fact-checker's verdict, a
crowd rating) and Disinformation as the thesis title names it. Every corpus has one; FactLens
measures and states its own rather than hiding it. A property of the corpus, not of any one article
— the same figure for every Assessment ever produced from a given Model Artifact.

Corpus measures it, Training publishes it inside the Model Artifact, Screening states it to the
reader. All three must mean the same distance and the same number by it; a change on any side is a
change on all three.

### The corpus — Corpus

Terms marked _Supplied to Training_ are owned here and consumed downstream: Corpus is the upstream
Supplier, Training the downstream Customer. Only Corpus may change them.

**Publisher**:
The organisation that issued an article. The unit a Source-Disjoint Split partitions on, and — in
`misinfo-general` — the thing the corpus label actually describes.
_Avoid_: Source, domain, site, author

**Unreliable Content** _(Corpus sense)_:
An article issued by a Publisher on the corpus's unreliable list. A property of the **Publisher**,
not of the article's text: 43.5% of such articles in `misinfo-general` are clearly non-credible, and
the remainder are the Label Gap. Compare the Screening entry of the same name.
_Avoid_: Fake, false, untrue

**Label Semantics** _(Supplied to Training)_:
What a given corpus's label actually encodes — publisher provenance, a fact-checker's verdict on one
claim, or the newsroom of origin. Declared by the Corpus Adapter that supplies it, never assumed.
_Avoid_: Ground truth, target, class meaning

**Corpus Adapter**:
A translation of one external corpus into FactLens's own model, carrying that corpus's Label
Semantics and Label Gap across the border with it.
_Avoid_: Loader, dataset, reader

**Source-Disjoint Split** _(Supplied to Training)_:
A partition of a corpus in which no Publisher appears in more than one of the training, validation
and test sets. Forces generalisation to unseen outlets, rather than to a familiar house style.
_Avoid_: Random split, stratified split

**Split Manifest** _(Supplied to Training)_:
The Publisher-to-fold assignment that fixes a Source-Disjoint Split. Produced once, and asserted
against before any training run — the agreement that keeps the split from being silently undone.
_Avoid_: Split config, fold map, seed

**Register Leakage**:
The failure in which a classifier separates classes by recognising a Publisher's editorial
conventions — datelines, wire-service phrasing, image-credit templates — rather than by anything
about the content. The reason a saturated benchmark score is a warning rather than a result.
_Avoid_: Overfitting, data leakage, bias

**Contrast Experiment**:
A deliberately flawed evaluation kept and reported because its failure is informative — in FactLens,
the ISOT result, retained to demonstrate what Register Leakage does to a benchmark.

### Building the model — Training

**Fine-tuning**:
The supervised pass that adapts pre-trained ModernBERT weights to a corpus's labels. Adopted
wholesale from the upstream — standard objective, standard loop, nothing about it specific to
FactLens.
_Avoid_: Training, retraining, transfer learning

**Calibration**:
The adjustment that makes a Credibility Score mean what it claims — so that texts scored 0.8 are
unreliable roughly 80% of the time. Distinct from accuracy: a model can be accurate and badly
calibrated. Fitted in Training on the validation fold, and carried into Screening as a temperature
inside the Model Artifact.

**Evaluation Metrics**:
What is reported for a Model Artifact: MCC and F1 over the unreliable class as the headline figures,
the Source-Disjoint Gap as the honesty check, and a reliability diagram for Calibration. Accuracy is
never reported on its own.
_Avoid_: Accuracy, score, performance

**Source-Disjoint Gap**:
The drop in a metric between a random split and a Source-Disjoint Split of the same corpus. The size
of the drop is the size of the Register Leakage.
_Avoid_: Generalisation gap, overfitting gap

### The boundary — Training to Screening

**Model Artifact**:
What Training publishes and Screening consumes, travelling as one unit: the fine-tuned weights, the
tokeniser, the Calibration temperature, the derived Verdict Band boundaries, and the measured Label
Gap.
_Avoid_: Checkpoint, model file, weights

### The assessment — Screening

**Article Text**:
The body of a piece of internet writing submitted for assessment, stripped of surrounding page
furniture. The only input the system reasons over.
_Avoid_: Document, content, input, post

**Unreliable Content** _(Screening sense)_:
Text bearing the stylistic and structural characteristics of publications with poor editorial
standards. What a Credibility Score is *hoped* to be about — the hope whose cost the Label Gap
measures and whose failure Register Leakage names. Compare the Corpus entry of the same name.
_Avoid_: Fake, false, untrue

**Credibility Score**:
A calibrated probability that an Article Text resembles articles issued by Publishers with poor
editorial standards — because Publisher provenance is what the corpus label encodes. That is what
the score is *of*; the Screening Aid role is what it is *for*. Bounded, calibrated, and never
presented on its own or more strongly than its Verdict Band permits.
_Avoid_: Confidence, truth score, fakeness, probability

**Verdict Band**:
The qualitative range a Credibility Score falls into, which governs how strongly the interface is
permitted to phrase the result. The band, not the raw score, is what the reader is meant to act on.
_Avoid_: Label, class, prediction, verdict

**Assessment**:
The complete result of analysing one Article Text: its Credibility Score, its Verdict Band, and its
Token Attributions. Derived and never mutated. Held only for the lifetime of the reader's session —
the Article Text it was derived from is never retained at all.
_Avoid_: Result, analysis, report, judgement

**Token Attribution**:
A signed weight assigned to one token of the Article Text, indicating how much that token pushed the
Credibility Score toward or away from the unreliable class.
_Avoid_: Explanation, importance, highlight, saliency

### The reader's session — Screening

**Fast Path**:
The synchronous half of an assessment — one forward pass yielding a Credibility Score and its
Verdict Band, answered before any attribution work begins. What the reader sees immediately.
_Avoid_: Quick scan, preview, first pass

**Attribution Job**:
The asynchronous half — the Integrated Gradients computation that produces Token Attributions,
costing tens of passes and streamed to the reader as it progresses. Its failure costs the
explanation but never the Assessment.
_Avoid_: Task, background job, worker

**Ephemeral Store**:
Where an Assessment waits between its Attribution Job finishing and the reader collecting it. Keyed
by a hash of the Article Text, bounded by a short TTL, gone on restart — and never holding the
Article Text itself.
_Avoid_: Cache, database, persistence layer
