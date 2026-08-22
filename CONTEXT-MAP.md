# Context Map

The strategic map: where meaning changes, and what must be translated at each border. It says
nothing about packages, tiers or deployment — for the module layout see
[#10](https://github.com/aoleszkiewicz/factlens/issues/10).

| Decision | Recorded in |
|---|---|
| Framing — credibility, not truth | [ADR-0001](docs/adr/0001-credibility-assessment-not-truth-verdict.md) |
| Architecture — ports and adapters, no tactical DDD | [ADR-0002](docs/adr/0002-ports-and-adapters-without-tactical-ddd.md) |
| These boundaries | [ADR-0003](docs/adr/0003-three-bounded-contexts-and-the-corpus-anticorruption-layer.md) |

---

## Subdomains — the problem space

Subdomains are parts of the *problem*: they exist whether or not software is written, and
`Core` / `Supporting` / `Generic` says how much thinking each deserves. Bounded Contexts are parts
of the *solution*: boundaries drawn so that inside each one, every term has exactly one meaning.
The two need not line up, and here they do not.

| Subdomain | Kind | Realised in |
|---|---|---|
| **Credibility Framing** — the Label Gap, and what a Credibility Score may claim | **Core** | slices of **Corpus** *and* **Screening** |
| **Corpus Curation** — Source-Disjoint Split, Register Leakage, Contrast Experiment | Supporting | **Corpus** |
| **Model Production** — Fine-tuning, Calibration | Generic | **Training** |
| **Explanation** — Integrated Gradients → Token Attribution | Generic | **Screening** |
| **Reader Delivery** — Fast Path, Attribution Job, Ephemeral Store, HTTP + SSE | Generic | **Screening** |
| **Monitoring** — latency, duration, queue depth | Generic | **Screening** adapters |

**Why each classification:**

- **Credibility Framing is Core.** Fine-tuning a classifier is commodity work. Naming and measuring
  the gap between the label and the phenomenon is the contribution.
- **Corpus Curation is Supporting.** The techniques are known; their application here is specific
  and is a graded deliverable ([#8](https://github.com/aoleszkiewicz/factlens/issues/8)).
- **Model Production, Explanation, Reader Delivery and Monitoring are Generic.** A standard
  fine-tune, an off-the-shelf attribution method, a latency decomposition, and instrumentation.
  None is unique to this project.

Two consequences follow from the right-hand column. No context maps to exactly one subdomain, and
the Core subdomain is split across two — which is why **Label Gap** is kernel vocabulary rather than
the property of any single box. Training realises a Generic subdomain, which places the interesting
decisions upstream of the GPU: in the Split Manifest and the Label Gap that Corpus produces.

---

## Contexts — the solution space

| Context | Lifecycle | Owns |
|---|---|---|
| **Corpus** | Offline | Publisher, Unreliable Content *(Corpus sense)*, Label Semantics, Corpus Adapter, Normalisation Contract, Publisher De-identification, Source-Disjoint Split, Split Manifest, Register Leakage, Contrast Experiment |
| **Training** | Offline | Fine-tuning, Calibration, Evaluation Metrics, Source-Disjoint Gap; publishes the Model Artifact |
| **Screening** | Runtime | Article Text, Unreliable Content *(Screening sense)*, Credibility Score, Verdict Band, Assessment, Token Attribution, Fast Path, Attribution Job, Ephemeral Store |

Two groups sit outside every context and are declared as such in [`CONTEXT.md`](./CONTEXT.md):
**Framing** (Disinformation, Screening Aid) and **Kernel** (Label Gap).

**Unreliable Content is defined twice** — in Corpus as a property of the Publisher, in Screening as
a property of the text. The distance between the two is the **Label Gap**, and that difference is
why this map has more than one box.

---

## The map

```mermaid
flowchart TB

  subgraph SOURCES["OUTSIDE WORLD - upstreams we do not control"]
    MG[("misinfo-general<br/>primary corpus")]
    ISOT[("ISOT<br/>contrast experiment")]
    RECO[("ReCOVery<br/>transfer set")]
    HF["ModernBERT-base<br/>pre-trained weights"]
  end

  subgraph BUILD["OFFLINE - building the model"]
    CORPUS["CORPUS<br/>labels, splits, Label Gap"]
    TRAINING["TRAINING<br/>fine-tuning, calibration"]
  end

  subgraph SERVE["RUNTIME - one reader, one article"]
    SCREENING["SCREENING<br/>Article Text to Assessment"]
    READER(["Reader"])
  end

  LG{{"Label Gap<br/>kernel vocabulary"}}

  MG -->|ACL| CORPUS
  ISOT -->|ACL| CORPUS
  RECO -->|ACL| CORPUS
  HF -->|Conformist| TRAINING

  CORPUS -->|Customer/Supplier| TRAINING
  TRAINING -->|Model Artifact| SCREENING
  SCREENING -->|HTTP and SSE| READER

  CORPUS -.- LG
  TRAINING -.- LG
  SCREENING -.- LG

  classDef core fill:#e8f0fe,stroke:#4a6fa5,stroke-width:2px,color:#12233d
  classDef ext fill:#f5f1e8,stroke:#a8977a,stroke-width:1px,color:#3a3226
  classDef person fill:#eaf5ea,stroke:#6a9a6a,stroke-width:1px,color:#1e3a1e
  classDef kernel fill:#f7e9ec,stroke:#9c2f39,stroke-width:1.5px,color:#3d1216

  class CORPUS,TRAINING,SCREENING core
  class MG,ISOT,RECO,HF ext
  class READER person
  class LG kernel
```

### Legend

| On the map | Pattern | Meaning |
|---|---|---|
| `ACL` | Anticorruption Layer | Their model is translated into ours; their vocabulary never leaks in |
| `Conformist` | Conformist | Their model is adopted wholesale — tokeniser, context window, checkpoint format |
| `Customer/Supplier` | Customer/Supplier | Corpus is upstream Supplier, Training downstream Customer |
| `Model Artifact` | Published Language | One contract, published once, consumed as-is |
| `HTTP and SSE` | Open Host Service | A protocol Screening publishes for any client |
| dotted lines | Kernel vocabulary | One term all three contexts mean identically |

---

## Relationships

### External corpora → Corpus — Anticorruption Layer

Each corpus enters through a **Corpus Adapter** that translates it into the system's own model.

Three corpora serve three jobs at once:

| Corpus | Role |
|---|---|
| `misinfo-general` | Primary |
| ISOT | Contrast Experiment — F1 ≈ 0.99 survives de-identification |
| ReCOVery | External transfer set |

An adapter cannot yield articles without also declaring:

1. Its **Label Semantics**.
2. Its **Label Gap** — measured where measurable (43.5% for `misinfo-general`), stated where not.
3. Whether it can produce a **Source-Disjoint Split** at all.

ISOT structurally cannot produce one. That refusal is what makes it the Contrast Experiment rather
than a corpus that was split badly.

A port yielding a bare `(text, label)` stream would make three incompatible label meanings
substitutable and bury the Label Gap inside the adapter — hiding the one thing ADR-0001 exists to
name.

### ModernBERT → Training — Conformist

Tokeniser, 8192-token context window and checkpoint format are adopted as they are. There is nothing
to gain from resisting an upstream the project does not influence.

### Corpus → Training — Customer/Supplier

| Side | Role |
|---|---|
| Corpus | Authors the **Split Manifest** and the **Normalisation Contract**, declares the **Label Semantics** and the **Publisher De-identification** categories |
| Training | Consumes them, and asserts against the manifest before an epoch runs |

**The failure this prevents is silent.** One `train_test_split(df, random_state=42)` in Training
re-partitions at the article level. Publishers reappear on both sides, every evaluation number
quietly becomes an ISOT number, and nothing crashes or warns.

**Why not a Shared Kernel.** A Shared Kernel is a model either side may change, which imposes a
standing two-way veto. Nothing here lets Training author a manifest or redefine Label Semantics.
The obligation runs one way.

**Why not Conformist.** Training's needs are a budgeted obligation on Corpus's plan, not something
it works around. Training gets a voice, not a veto.

The two contexts share no conflicting terms: every shared term means the same on both sides, and
every unshared term is simply absent on the other. So this is a lifecycle boundary, not a boundary
of meaning. The border that does carry a meaning conflict is Corpus ↔ Screening.

**Two text-reduction terms cross this border, and they are not the same thing.**

| Term | Purpose | Reaches Screening? |
|---|---|---|
| **Normalisation Contract** | Produce Article Text — whitespace, markup, casing, tokeniser input | Yes, in full. Training and Screening must reduce identically or Calibration does not hold. |
| **Publisher De-identification** | Reduce **Register Leakage** — hygiene, not a sufficient control | Structural categories only. The publisher list stays in Corpus — Screening has no **Publisher** term and receives text without provenance. |

Both are authored by Corpus, because Corpus produces the text a model is fitted on, and both travel
onward inside the **Model Artifact**.

### Label Gap — kernel vocabulary across all three

| Context | Responsibility |
|---|---|
| Corpus | Measures it |
| Training | Publishes it inside the Model Artifact |
| Screening | States it to the reader |

Drawn as its own node because it belongs to the Core subdomain while sitting inside no single
context: it crosses every border without being translated at any of them. If it ever means three
different things in three places, the Core subdomain has dissolved.

### Training → Screening — Published Language, via an Anticorruption Layer

The **Model Artifact** crosses as one unit: weights, tokeniser, normalisation contract, Calibration
temperature, Verdict Band boundaries, the Publisher De-identification categories, and the
measured Label Gap.

The `Classifier` port is the ACL — the seam where *P(unreliable-publisher class)* becomes a
**Credibility Score**. This is where ADR-0001's framing becomes executable, and the Label Gap is the
measured cost of that translation.

The seam is cheap; the swap is not. Changing the primary corpus invalidates the Model Artifact, the
temperature, the band boundaries and every number in the evaluation chapter.

### Screening → Reader — Open Host Service

HTTP + SSE, in the sequence `accepted` → `score` → `progress` → `attributions` → `done` (FR-8).

---

## What is deliberately not a context

| Candidate | Why not |
|---|---|
| **The API / backend** | The Open Host Service of Screening, not a peer. A Bounded Context is a boundary of meaning; putting a tier on a map of languages draws one wrong. |
| **The UI** | An adapter, per ADR-0002. A client of the service. |
| **Evaluation** | MCC, F1-unreliable, the Source-Disjoint Gap and the reliability diagram are continuous with Training's vocabulary. A boundary there separates nothing. |
| **Monitoring** | A Generic Subdomain. Latency, duration and queue depth mean the same here as anywhere, so there is no model to protect. Realised as instrumentation in Screening's adapters. |
| **A pipeline** | `Corpus → Training → Evaluation` is a dataflow. Its arrows say "happens after", never "translates into". |

Dropping the Monitoring box does not drop the obligation: NFR-1, NFR-2, NFR-3 and NFR-6 are all
marked testable, and a p95 that was never recorded cannot be reported for thesis task 7.

---

## Repository layout

The contexts are **not yet separate directories**. `src/` is currently laid out by tier
(`data/`, `model/`, `api/`, `frontend/`); the target layout is
[#10](https://github.com/aoleszkiewicz/factlens/issues/10).

Until #10 settles: one root [`CONTEXT.md`](./CONTEXT.md) with term groups tagged by owning context,
and one `docs/adr/` for system-wide decisions. Splitting the glossary now would mean guessing paths
and moving them again.
