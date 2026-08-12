# FactLens

A screening system that assesses how strongly a piece of internet text exhibits the characteristics of unreliable or disinformative content, and shows the reader which parts of the text drove that assessment.

## Language

### The assessment

**Article Text**:
The body of a piece of internet writing submitted for assessment, stripped of surrounding page furniture. The only input the system reasons over.
_Avoid_: Document, content, input, post

**Credibility Score**:
A calibrated probability that a given Article Text belongs to the unreliable class of the corpus the model was trained on. Bounded, calibrated, and never presented on its own.
_Avoid_: Confidence, truth score, fakeness, probability

**Verdict Band**:
The qualitative range a Credibility Score falls into, which governs how strongly the interface is permitted to phrase the result. The band, not the raw score, is what the reader is meant to act on.
_Avoid_: Label, class, prediction, verdict

**Assessment**:
The complete result of analysing one Article Text: its Credibility Score, its Verdict Band, and its Token Attributions. Derived and never mutated. Held only for the lifetime of the reader's session — the Article Text it was derived from is never retained at all.
_Avoid_: Result, analysis, report, judgement

**Token Attribution**:
A signed weight assigned to one token of the Article Text, indicating how much that token pushed the Credibility Score toward or away from the unreliable class.
_Avoid_: Explanation, importance, highlight, saliency

**Calibration**:
The adjustment that makes a Credibility Score mean what it claims — so that texts scored 0.8 are unreliable roughly 80% of the time. Distinct from accuracy: a model can be accurate and badly calibrated.

### The subject matter

**Disinformation**:
False information deliberately created and spread to deceive. The concept named by the thesis title — and, critically, **not** what any corpus label encodes. FactLens never claims to detect it directly.
_Avoid_: Fake news, misinformation, hoax

**Unreliable Content**:
Text bearing the stylistic and structural characteristics of publications with poor editorial standards. This is what the model is actually trained to recognise, and what a Credibility Score refers to.
_Avoid_: Fake, false, untrue

**Label Gap**:
The distance between what a corpus label encodes (publisher provenance, a fact-checker's verdict, a crowd rating) and Disinformation as the thesis title names it. Every corpus has one; FactLens measures and states its own rather than hiding it.

**Screening Aid**:
The role FactLens is designed to occupy — a tool that directs a reader's attention toward text worth checking. It is explicitly not an arbiter of truth, and the interface is built to keep that distinction visible.

### The reader's session

**Fast Path**:
The synchronous half of an assessment — one forward pass yielding a Credibility Score and its Verdict Band, answered before any attribution work begins. What the reader sees immediately.
_Avoid_: Quick scan, preview, first pass

**Attribution Job**:
The asynchronous half — the Integrated Gradients computation that produces Token Attributions, costing tens of passes and streamed to the reader as it progresses. Its failure costs the explanation but never the Assessment.
_Avoid_: Task, background job, worker

**Ephemeral Store**:
Where an Assessment waits between its Attribution Job finishing and the reader collecting it. Keyed by a hash of the Article Text, bounded by a short TTL, gone on restart — and never holding the Article Text itself.
_Avoid_: Cache, database, persistence layer

### The corpus

**Source-Disjoint Split**:
A partition of a corpus in which no publisher appears in more than one of the training, validation and test sets. Forces generalisation to unseen outlets, rather than to a familiar house style.
_Avoid_: Random split, stratified split

**Register Leakage**:
The failure in which a classifier separates classes by recognising a publisher's editorial conventions — datelines, wire-service phrasing, image-credit templates — rather than by anything about the content. The reason a saturated benchmark score is a warning rather than a result.
_Avoid_: Overfitting, data leakage, bias

**Contrast Experiment**:
A deliberately flawed evaluation kept and reported because its failure is informative — in FactLens, the ISOT result, retained to demonstrate what Register Leakage does to a benchmark.
