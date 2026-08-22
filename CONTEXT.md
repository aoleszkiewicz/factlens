# FactLens

A screening system that assesses how strongly a text exhibits the characteristics of unreliable
content, and shows the reader which parts of the text drove that assessment.

## How to read this glossary

- Terms are grouped by the Bounded Context that owns them. The boundaries are in
  [`CONTEXT-MAP.md`](./CONTEXT-MAP.md).
- **Framing** and **Kernel** are the two declared exceptions: terms owned by no single context.
- Terms marked _Supplied to Training_ are owned by Corpus and consumed by Training. Only Corpus
  may change them.
- **Unreliable Content** is defined twice, differently, under Corpus and under Screening. The
  distance between the two definitions is the **Label Gap**
  ([ADR-0001](docs/adr/0001-credibility-assessment-not-truth-verdict.md)).

---

## Framing — owned by no context

**Disinformation**:
False information created and spread deliberately to deceive. Named by the thesis title; encoded by
no corpus label, and never claimed as a direct output.
_Avoid_: Fake news, misinformation, hoax

**Screening Aid**:
The role the system occupies — directing a reader's attention toward text worth checking, rather
than arbitrating truth. What a Credibility Score is *for*, as opposed to what it is *of*.

---

## Kernel — shared by Corpus, Training and Screening

**Label Gap**:
The distance between what a corpus label encodes and Disinformation as the title names it. A
property of the corpus, so the same figure applies to every Assessment from a given Model Artifact.

| Context | Responsibility |
|---|---|
| Corpus | Measures it |
| Training | Publishes it inside the Model Artifact |
| Screening | States it to the reader |

All three must mean the same distance and the same number. A change on one side is a change on all
three.

---

## Corpus

**Publisher**:
The organisation that issued an article. The unit a Source-Disjoint Split partitions on, and the
thing the `misinfo-general` label describes.
_Avoid_: Source, domain, site, author

**Unreliable Content** _(Corpus sense)_:
An article issued by a Publisher on the corpus's unreliable list. A property of the Publisher, not
of the text — 43.5% of such articles in `misinfo-general` are clearly non-credible, and the
remainder is the Label Gap.
_Avoid_: Fake, false, untrue

**Label Semantics** _(Supplied to Training)_:
What a corpus's label encodes: publisher provenance, a fact-checker's verdict on one claim, or the
newsroom of origin. Declared by the Corpus Adapter, never assumed.
_Avoid_: Ground truth, target, class meaning

**Corpus Adapter**:
A translation of one external corpus into the system's own model, carrying that corpus's Label
Semantics and Label Gap with it.
_Avoid_: Loader, dataset, reader

**Normalisation Contract** _(Supplied to Training)_:
The reduction that turns raw input into Article Text — whitespace, markup, casing, and what the
tokeniser is fed. Authored by Corpus because Corpus produces the text a model is fitted on, and
carried onward in the Model Artifact so Screening applies it identically.
_Avoid_: Cleaning, preprocessing, sanitisation

**Publisher De-identification** _(Supplied to Training)_:
The removal of Publisher-identifying spans from an article, limited to declared structural
categories: datelines, wire attributions, image credits and site self-references. Necessary hygiene
and demonstrably insufficient on its own — the ISOT Contrast Experiment still reaches F1 ≈ 0.99 with
these spans removed. Distinct from the Normalisation Contract in both purpose and ownership.
_Avoid_: Masking, anonymisation, scrubbing

**Source-Disjoint Split** _(Supplied to Training)_:
A partition in which no Publisher appears in more than one of the train, validation and test sets.
Forces generalisation to unseen outlets rather than to a familiar house style.
_Avoid_: Random split, stratified split

**Split Manifest** _(Supplied to Training)_:
The Publisher-to-fold assignment that fixes a Source-Disjoint Split. Produced once, and asserted
against before any training run.
_Avoid_: Split config, fold map, seed

**Register Leakage**:
The failure in which a classifier separates classes by recognising a Publisher's editorial
conventions — datelines, wire phrasing, image-credit templates — rather than the content.
_Avoid_: Overfitting, data leakage, bias

**Contrast Experiment**:
An evaluation kept and reported because its failure is informative. Here: the ISOT result — F1 ≈ 0.99
from TF-IDF + logistic regression, measured **after** Publisher De-identification, on a
label-stratified rather than source-disjoint split.

---

## Training

**Fine-tuning**:
The supervised pass that adapts pre-trained ModernBERT weights to a corpus's labels. Standard
objective, standard loop.
_Avoid_: Training, retraining, transfer learning

**Calibration**:
The adjustment that makes a Credibility Score mean what it claims, so that texts scored 0.8 are
unreliable roughly 80% of the time. Fitted on the validation fold; carried into Screening as a
temperature.

**Evaluation Metrics**:
What is reported for a Model Artifact: MCC and F1 over the unreliable class as headline figures, the
Source-Disjoint Gap as the honesty check, and a reliability diagram for Calibration. Accuracy is
never reported alone.
_Avoid_: Accuracy, score, performance

**Source-Disjoint Gap**:
The drop in a metric between a random split and a Source-Disjoint Split of the same corpus. The size
of the drop is the size of the Register Leakage.
_Avoid_: Generalisation gap, overfitting gap

---

## Boundary — Training to Screening

**Model Artifact**:
What Training publishes and Screening consumes, as one unit.

| Contents | |
|---|---|
| Fine-tuned weights | |
| Tokeniser | |
| Normalisation Contract | defines Article Text |
| Publisher De-identification categories | structural only, no publisher names |
| Calibration temperature | |
| Verdict Band boundaries | derived |
| Label Gap | measured |

_Avoid_: Checkpoint, model file, weights

---

## Screening — the assessment

**Article Text**:
The body of a text submitted for assessment, stripped of page furniture and reduced by the
**Normalisation Contract**. The only input the system reasons over. Text reduced any other way falls
outside the distribution the model was fitted on, and Calibration no longer holds.
_Avoid_: Document, content, input, post, raw text

**Unreliable Content** _(Screening sense)_:
Text bearing the stylistic and structural characteristics of publications with poor editorial
standards. What a Credibility Score is hoped to be about.
_Avoid_: Fake, false, untrue

**Credibility Score**:
A calibrated probability that an Article Text resembles articles issued by Publishers with poor
editorial standards. Never presented alone, nor more strongly than its Verdict Band permits.
_Avoid_: Confidence, truth score, fakeness, probability

**Verdict Band**:
The qualitative range a Credibility Score falls into, governing how strongly the interface may
phrase the result. The band, not the raw score, is what the reader acts on.
_Avoid_: Label, class, prediction, verdict

**Assessment**:
The complete result of analysing one Article Text: Credibility Score, Verdict Band and Token
Attributions. Derived once, never mutated, and held only for the reader's session.
_Avoid_: Result, analysis, report, judgement

**Token Attribution**:
A signed weight on one token of the Article Text, indicating how far that token pushed the
Credibility Score toward or away from the unreliable class.
_Avoid_: Explanation, importance, highlight, saliency

---

## Screening — the reader's session

**Fast Path**:
The synchronous half of an assessment: one forward pass yielding a Credibility Score and its Verdict
Band, answered before attribution work begins.
_Avoid_: Quick scan, preview, first pass

**Attribution Job**:
The asynchronous half: the Integrated Gradients computation producing Token Attributions, streamed
as it progresses. Its failure costs the explanation, never the Assessment.
_Avoid_: Task, background job, worker

**Ephemeral Store**:
Where an Assessment waits between its Attribution Job finishing and the reader collecting it. Keyed
by a hash of the Article Text, bounded by a short TTL, gone on restart, and never holding the
Article Text itself.
_Avoid_: Cache, database, persistence layer
