# Analysis of Existing Solutions

**Research ticket:** [#5](https://github.com/aoleszkiewicz/factlens/issues/5) — thesis task 1
**Status:** draft for thesis chapter 2
**Date:** 2026-08-11
**Scope:** document-level automated credibility / "fake news" assessment for English text; academic
approaches, production systems, result presentation, and implementation stacks.

> **How to read this document.** It is written to be usable as a chapter draft, so the prose is
> continuous rather than bulleted where possible. Every quantitative claim is attributed. Claims I
> verified against the primary source (the paper or the vendor's own documentation) are stated
> plainly; claims I could only establish from secondary reporting are marked *(unverified)*.

---

## 1. Introduction and framing

The literature on automated detection of false or misleading online content is large, active, and —
as this chapter argues — systematically over-optimistic about its own results. Reported accuracies
above 0.95 are routine, yet no deployed production system makes a comparable claim; the commercial
tools surveyed in section 4 either avoid automated verdicts entirely or restrict themselves to
narrow, well-posed sub-tasks such as claim ranking. Understanding *why* that gap exists is the
purpose of this chapter, and it directly motivates the design decisions recorded in
[ADR-0001](../adr/0001-credibility-assessment-not-truth-verdict.md): FactLens outputs a calibrated
credibility assessment presented as a screening aid, not a verdict on truth.

Three questions organise the review:

1. What are the dominant modelling approaches, and what do they report? (§2)
2. What happens to those numbers when the evaluation is made honest — when the test set contains
   sources, events, or time periods unseen in training? (§3) **This is the central section.**
3. How do systems that actually face users handle the resulting uncertainty? (§4, §5)

Section 6 surveys implementation stacks in comparable open-source projects and offers candidate
stacks for the downstream decision ticket [#9](https://github.com/aoleszkiewicz/factlens/issues/9).

### 1.1 Task taxonomy

The phrase "fake news detection" covers at least four distinct machine-learning tasks, which are
routinely conflated and which have very different difficulty profiles:

| Task | Input | Label source | Difficulty |
| --- | --- | --- | --- |
| **A. Source-level credibility** | article text | publisher's reputation rating | tractable, but the label describes the *outlet*, not the article |
| **B. Claim-level fact verification** | a single claim + evidence corpus | fact-checker verdict | hard; requires retrieval and entailment |
| **C. Rumour / stance classification** | social-media thread | crowd or journalist annotation | hard; depends on propagation signals |
| **D. Machine-generated text detection** | article text | provenance (human vs. model) | distinct problem; not about veracity at all |

FactLens is a **task A** system: a document-level classifier over article text, with source-level
provenance labels. This is the task the thesis brief mandates (fine-tuning a pre-trained transformer
for classification), and it is explicitly *not* task B — retrieval-based fact verification is out of
scope per the map issue [#2](https://github.com/aoleszkiewicz/factlens/issues/2). The distinction
matters for the whole chapter: much of the strongest reported performance in the literature belongs
to task A, and much of the strongest *criticism* of the literature is that task A's labels are a
proxy that classifiers learn to shortcut.

---

## 2. Academic approaches to document-level credibility classification

### 2.1 The three generations

**Generation 1 — hand-crafted features with shallow classifiers.** Stylometric, psycholinguistic and
readability features (LIWC categories, POS-tag distributions, punctuation and capitalisation
statistics, sentiment) fed to SVMs, logistic regression or random forests. Horne, Nørregaard and
Adali's work on news veracity is the canonical example, and their conclusion is worth carrying
forward: hand-crafted *style* features are unusually robust to change in the news cycle, degrading
only slowly over time [Horne et al., 2019]. This generation is still relevant as a baseline, and its
strength is diagnostic — a strong TF-IDF result is now read as evidence that the corpus is separable
on register alone.

**Generation 2 — neural sequence encoders.** CNNs, LSTMs and BiLSTMs over word embeddings, often with
attention. These dominated 2017–2019 and are what most undergraduate replications still implement.
They rarely beat a well-tuned linear model by a wide margin on the saturated corpora.

**Generation 3 — pre-trained transformer encoders, fine-tuned.** BERT, RoBERTa, DeBERTa, and
domain-adapted variants (CT-BERT for COVID content, BERTweet for social text) with a single
classification head. This is now the default, and it is what the thesis brief mandates. The pivotal
methodological result is Pelrine, Danovitch and Rabbany's finding that *plain* fine-tuning of a
strong encoder — no graph module, no propagation model, no multimodal fusion — matches or beats
elaborate purpose-built architectures on most benchmarks [Pelrine et al., WWW 2021]. Their framing is
blunt: the field's architectural sophistication was not buying performance, and simple baselines had
been under-reported.

**Generation 3b — large language models, zero-/few-shot and as annotators.** Since 2023 a substantial
sub-literature prompts LLMs instead of fine-tuning encoders. The comparative evidence is mixed in a
consistent way: encoder models fine-tuned on in-domain data still win on raw classification metrics,
while LLMs are more robust to input perturbation and to domain shift [Liu et al., *Knowledge and
Information Systems*, 2024/2025, arXiv:2412.14276]. For a thesis whose deliverable is a
self-hosted, explainable, low-latency classifier, the encoder route remains the right one; the LLM
literature is relevant mainly as related work and as a source of the "distant/AI annotation" idea.

### 2.2 Architectures in practice

Across generation-3 papers the modelling recipe is remarkably uniform:

- a pre-trained encoder (110M–355M parameters), max sequence length 512;
- `[CLS]` pooling into a linear classification head, cross-entropy loss;
- 2–5 epochs, learning rate 1e-5 to 3e-5, batch 16–32;
- truncation for long documents, occasionally head+tail or chunk-and-aggregate.

Variations that recur: hierarchical encoders for long documents; auxiliary tasks (stance, emotion);
multi-task or adversarial *domain-invariant* representations for cross-domain settings; and fusion
with non-textual signals (propagation graphs, user features, images). The last category is out of
scope here — FactLens is text-only by decision in issue #2 — but it is worth noting *why* those
papers add social signals: text alone generalises poorly, which is precisely the subject of §3.

The 512-token limit is a real constraint for news articles and is already measured on this project's
own data (44% of articles exceed 512 tokens; truncation at 512 discards 27% of all tokens — issue
[#6](https://github.com/aoleszkiewicz/factlens/issues/6)). Modern long-context encoders (ModernBERT,
8192 tokens) remove the problem rather than working around it.

### 2.3 Benchmarks and the metrics they produce

| Corpus | Unit | Label origin | Task type (§1.1) | Typical reported ceiling |
| --- | --- | --- | --- | --- |
| **ISOT** | article | outlet (Reuters vs. flagged sites) | A | ≈0.99 F1, trivially |
| **LIAR** | short claim | PolitiFact 6-way verdict | B-ish | ≈0.27–0.45 accuracy |
| **FakeNewsNet** (PolitiFact / GossipCop) | article + social context | fact-checker verdict on the story | A/B | 92.8 / 85.0 macro-F1 (SOTA, per Pelrine et al.) |
| **PHEME** | tweet thread | journalist annotation per event | C | 51.3 macro-F1 cross-event SOTA |
| **NELA-GT** (2018–2022) | article | outlet-level, aggregated from several raters | A | ≈0.97 in-domain, ≈0.80 source-disjoint (§3.2) |
| **WELFake** | article | merged from four other corpora | A | high, but inherits every parent's artefacts |

Two observations for the thesis. First, the *spread* of reported ceilings across corpora — 0.27 to
0.99 — is far wider than the spread across architectures within any one corpus. The dataset, not the
model, dominates the headline number. Second, the corpora at the top of that range are exactly the
ones where the label is a property of the publisher rather than of the article, which is what makes
the near-perfect scores suspect.

This is the empirical justification for the project's own negative result: on ISOT, after removing
every leakage marker identified in `notebooks/explore/02_leakage.ipynb`, TF-IDF + logistic regression
still reaches F1 ≈ 0.99 and AUC ≈ 0.999, with a learning curve flat at the ceiling. That is not a
modelling success; it is a measurement of how separable *Reuters register* is from the register of
the flagged outlets. ISOT is therefore retained as a contrast experiment only.

---

## 3. The generalisation gap — the central finding

This section is the most important in the chapter, because the thesis's contribution is defined by
it. The claim, supported below by five independent lines of evidence, is:

> **Reported performance in document-level credibility classification is largely an artefact of
> evaluation protocol. When the test set is made disjoint from the training set along the axis that
> actually shifts in deployment — publisher, event, topic, or time — performance falls from the high
> 0.90s to somewhere between chance and 0.80, and in the hardest settings below what a purpose-built
> model achieves.**

### 3.1 Cross-event collapse: PHEME (verified)

Pelrine, Danovitch and Rabbany (WWW '21) fine-tuned nine language models on nine misinformation
benchmarks. On in-topic splits the transformers were competitive with or better than published SOTA.
On **PHEME5 Lc** — the leave-one-event-out split, training on four events and testing on the unseen
Charlie Hebdo event — the picture inverts (macro-F1):

| Model | PHEME5 cross-event macro-F1 |
| --- | --- |
| Published SOTA (Cheng et al., 2020) | **51.3** |
| RoBERTa (large, fine-tuned) | **29.0 ± 3.3** |
| CT-BERT | 27.9 |
| DeCLUTR | 30.2 |

*Verified against the paper's Table 2 via [ar5iv rendering of arXiv:2104.06952].* The authors'
own summary is that the datasets "fall on a spectrum": on in-topic tasks language models excel,
but "they perform poorly at cross-domain tasks", specifically the event-based splits where training
and test data concern unrelated topics.

Two things make this result load-bearing for the thesis. First, the *direction*: the general-purpose
fine-tuned transformer, which wins everywhere else, is beaten by roughly 20 macro-F1 points by a
task-specific model as soon as the topic shifts — the fine-tuned encoder had been winning by
memorising topic, not by learning deception. Second, the *absolute level*: 29.0 macro-F1 on a
three-way task is close to uninformative. A system reporting 0.95 on an in-domain split and behaving
like this in the field is not a marginal disappointment; it is a different system.

*Caveat to state in the thesis:* PHEME is short social-media text with thread structure, not
long-form news articles, and the 51.3 SOTA uses propagation signals FactLens will not have. The
result should be cited as evidence about *evaluation protocol*, not as a direct performance forecast
for a news-article classifier.

### 3.2 Source-disjoint collapse: NELA-GT (verified, and the closest analogue to FactLens)

Zhou, Elfardy, Christodoulopoulos, Butler and Bansal, *Hidden Biases in Unreliable News Detection
Datasets* (arXiv:2104.10130, April 2021) study exactly the setup FactLens uses: article text with
outlet-level labels. They compare a random split against a **source-disjoint** split in which no
publisher appears in both train and test (accuracy):

| Model / input | Random split | Source-disjoint split | Drop |
| --- | --- | --- | --- |
| Logistic regression | 77.5 | 67.2 | −10.3 |
| RoBERTa, title only | 85.2 | 70.4 | −14.8 |
| RoBERTa, title + article | **96.9** | **80.4** | **−16.5** |

Three consequences follow, all of which the thesis should adopt directly:

1. **The stronger the model, the larger the drop.** RoBERTa gains 19.4 points over logistic
   regression on the random split but only 13.2 on the source-disjoint one. Capacity is being spent
   partly on memorising outlets.
2. **A random split on outlet-labelled data is not an evaluation**, it is a source-identification
   test. The authors' recommendation is explicit: provide non-overlapping source and time splits, and
   run simple baselines as bias probes before drawing conclusions.
3. **80.4 is the realistic ceiling** for this task done honestly with a 2021-era encoder on
   NELA-scale data. Any FactLens result materially above that on a source-disjoint split should be
   treated as a bug hunt, not a triumph.

The paper also reports a control in which labels are permuted and the model still recovers much of
its accuracy, which they read as direct evidence of site memorisation. *(I am reporting this as
summarised from the paper's own description; I did not read the full experimental section, so the
exact protocol of that control should be checked before it is cited in the thesis.)*

Selection bias is a second, distinct mechanism they identify: FakeNewsNet inherits the coverage
priorities of fact-checking sites, which disproportionately cover sensational celebrity content, so
the "false" class carries topical fingerprints unrelated to reliability.

### 3.3 Cross-dataset transfer: near-total collapse

Transfer *between* corpora is worse than any within-corpus split. A recent comparative study reports a
model achieving essentially perfect F1 on ISOT scoring ≈23.9 on WELFake and ≈40.3 on LIAR
[*Fake News Detection: It's All in the Data!*, Applied Sciences 16(3):1585, 2026]. *(Numbers surfaced
via search result summaries; the MDPI page returned HTTP 403 to my fetch, so treat these figures as
**unverified** until the PDF is read. The qualitative pattern — legacy benchmarks such as ISOT
associated with near-perfect accuracy that does not survive transfer — is corroborated
independently by §3.1, §3.2 and §3.4.)*

If those figures hold, the ISOT→WELFake number is *below chance* for a balanced binary task, which
means the classifier is not merely uninformative off-distribution but anti-correlated — it has
learned a register mapping that is inverted in the target corpus. This is the strongest available
argument that within-corpus metrics carry almost no information about deployment behaviour, and it is
the most directly relevant result to this project, since ISOT is the corpus already in `data/raw/`.

### 3.4 Multi-axis OOD benchmarking: misinfo-general

Verhoeven, Mishra and Shutova, *Yesterday's News: Benchmarking Multi-Dimensional Out-of-Distribution
Generalization of Misinformation Detection Models*, accepted to *Computational Linguistics*
(23 November 2025; arXiv:2410.18122v4) is the most current framing of the problem and the most
useful for structuring the thesis's evaluation chapter. They introduce **misinfo-general**, a
benchmark built with distant (outlet-level) labelling, and identify six axes along which
generalisation must be tested:

**time, event, topic, publisher, political bias, and misinformation type.**

Their abstract states the motivation precisely: "Misinformation changes rapidly, much more quickly
than moderators can annotate at scale, resulting in a shift between the training and inference data
distributions. As a result, misinformation detectors need to be able to perform out-of-distribution
generalization, an attribute they currently lack."

Their most useful methodological point for FactLens: using article metadata they show how a standard
baseline "fails desiderata, which is not necessarily obvious from classification metrics" — i.e.
aggregate accuracy hides the failure mode, and per-axis breakdowns are required to see it. *(I
verified the abstract, authorship and venue directly on the arXiv listing; I could not extract the
results tables — ar5iv conversion fails and the PDF body did not render — so no numeric claims from
this paper are made here.)*

### 3.5 Dataset validity: many benchmarks cannot support the task at all

Pelrine's group returned to the problem in *A Guide to Misinformation Detection Data and Evaluation*
(KDD 2025; arXiv:2411.05060), auditing a large collection of misinformation datasets. Findings
relevant here:

- **Spurious keyword correlations** in six claim datasets (CoAID, IFND, MM-COVID, TruthSeeker2023,
  Twitter15, Twitter16) — e.g. in TruthSeeker2023 nearly all tweets mentioning politicians are
  labelled false, a shortcut with no generalisation value.
- **Spurious temporal correlations** in Twitter15/16 severe enough that the authors say the datasets
  should be disqualified without explicit remediation.
- **A feasibility problem**: they estimate at least half of the claims across 29 datasets cannot be
  validly assessed for veracity at all without evidence retrieval — the label is unanswerable from
  the text.
- They name **LIAR, PHEME, Twitter15/16, ISOT and BanFakeNews** among the criticised datasets, and
  propose **Evaluation Quality Assurance (EQA)**: a mandatory, documented data-suitability audit
  (at minimum, manual inspection of ~50 random examples) before experimental conclusions are drawn.

For a thesis, EQA is a gift: it makes the dataset-audit chapter (task 3) a citable methodological
contribution rather than housekeeping.

### 3.6 Temporal drift, and a dissenting data point

Not every axis collapses equally. Horne, Nørregaard and Adali (*Robust Fake News Detection Over Time
and Attack*, ACM TIST 11(1), 2019) find that unreliable- and hyperpartisan-news classifiers degrade
as the news cycle moves on, but "slower than expected", and that the degradation is largely
recoverable with online learning. Their explanation is that hand-crafted *style* features are fairly
stable properties of a publisher's writing.

This is a useful counterweight and should be reported honestly: the generalisation gap is severest
across **publisher** and **event/topic**, and comparatively mild across **short time horizons**.
Bozarth and Budak (ICWSM 2020) reach a compatible conclusion from a different angle — model
performance "varies considerably based on i) dataset, ii) evaluation archetype, and iii) performance
metrics", and, importantly for a system that will be shown to users, classifiers exhibit "a potential
bias against small and conservative-leaning credible news sites". That last finding is a fairness
result, not just an accuracy one: outlet-labelled training data teaches the model that *small and
unfamiliar* correlates with *unreliable*.

### 3.7 What this means for FactLens

| Implication | Consequence for the thesis |
| --- | --- |
| Random splits on outlet-labelled corpora measure source identification | Primary evaluation **must** be source-disjoint (already decided, ADR-0001) |
| Expect ≈0.75–0.85 on an honest split | Set expectations in the requirements chapter; a 0.99 is a defect signal |
| The in-domain/OOD delta is itself a result | Report both columns side by side; the *gap* is the contribution |
| Aggregate metrics hide per-axis failure | Add per-publisher and per-topic breakdowns (misinfo-general's six axes as a checklist) |
| Models are biased against small/unfamiliar outlets | Argue the screening-aid framing on fairness grounds, not only epistemic ones |
| Calibration matters more than accuracy | Temperature scaling + reliability diagram are the right instruments (already decided) |

---

## 4. Production and commercial systems

The striking fact about deployed systems is that **none of the credible ones ships an automated
truth verdict on arbitrary article text.** They fall into three groups: human-rated source
credibility, AI-assisted human fact-checking, and narrow automated sub-tasks.

### 4.1 NewsGuard — human ratings of *sources*, published as a transparent rubric

NewsGuard rates the reliability of news *outlets* — over 35,000 sources across websites, podcasts and
TV, covering outlets representing ~95% of online engagement in nine countries. Ratings are produced
by "a team of journalists and experienced editors", drafted by analysts, offered to the outlet for
comment, and reviewed by senior editors before publication.

The score is a weighted sum of **nine pass/fail journalistic criteria** (no partial credit),
totalling 100 points:

| Criterion | Points |
| --- | --- |
| Does not repeatedly publish false or egregiously misleading content | 22 |
| Gathers and presents information responsibly | 18 |
| Has effective practices for correcting errors | 12.5 |
| Handles the difference between news and opinion responsibly | 12.5 |
| Avoids deceptive headlines | 10 |
| Discloses ownership and financing | 7.5 |
| Clearly labels advertising | 7.5 |
| Reveals who is in charge, including possible conflicts of interest | 5 |
| Provides names of content creators, along with contact information | 5 |

Presentation is banded rather than a bare number: 100 "High Credibility", 75–99 "Generally
Credible", 60–74 "Credible with Exceptions", 40–59 "Proceed with Caution", 0–39 "Proceed with Maximum
Caution", plus non-scored **Satire** and **Platform** labels for humour sites and user-generated
platforms. Critically, NewsGuard is explicit that **ratings assess sources, not individual
articles**.

*Lessons FactLens should copy directly:* (a) a numeric score is always shown inside a named band with
an action-oriented verb ("proceed with caution"), never bare; (b) the criteria behind the score are
enumerated, so the user can disagree with a specific component; (c) the unit of assessment is stated
explicitly, so the user is not misled about what was judged; (d) some inputs are declared
out-of-scope (satire, platforms) rather than force-scored — the direct analogue of an abstain band.

### 4.2 Full Fact — AI as a claim *finder*, humans as the verdict

Full Fact (UK charity, fact-checking since 2010) builds **Full Fact AI**, used by 40+ fact-checking
organisations in 30 countries and three languages, processing roughly a third of a million sentences
on a typical weekday. The tool set is: data collection and media monitoring (news, TV, radio,
podcasts, social media, Hansard); **claim detection and classification** using a BERT-based
classifier that labels checkable claim types; **claim matching** against already-checked claims
(hybrid ML + generative models); and publishing with ClaimReview schema markup.

What the system deliberately does *not* do is decide truth. Their stated position:

> "Human experts aren't going anywhere anytime soon — and nor would we want them to be."

and

> "We are careful not to overstate our results. There are a lot of people who say that artificial
> intelligence is a panacea but we have been on the front line of fact checking since 2010 and we
> know first hand how difficult it is."

The actual checking is "undertaken offline by our team of expert fact-checking journalists". This is
the single most useful precedent for the ADR-0001 framing: the most experienced automated
fact-checking organisation in the UK scopes its AI to *triage and retrieval*, and treats verdict
generation as a human act.

### 4.3 ClaimBuster — an automated score that is explicitly not about truth

ClaimBuster (University of Texas at Arlington, IDIR lab; Hassan et al., KDD 2017 and a VLDB 2017
demo) scores sentences for **check-worthiness** — how much a sentence resembles a factual claim a
professional fact-checker would want to check — on a 0–1 scale, and exposes this through a public
API. Its design is the cleanest example in the field of *narrowing the claim to something a
classifier can actually learn*: the label is "would a fact-checker check this", which is an
annotatable property of the sentence, rather than "is this true", which is not.

*(I could not load the current ClaimBuster site — `idir.uta.edu/claimbuster/` redirects to
`idir.claimbuster.org`, which failed TLS verification from my environment, and the historical API doc
path 404s. The description above rests on the published papers and the system's long-standing
documented behaviour; the live API surface should be re-checked before it is cited as available.)*

### 4.4 Grover — machine-generated text detection, a different problem

Zellers et al., *Defending Against Neural Fake News* (NeurIPS 2019; arXiv:1905.12616) trained Grover,
a controllable news generator, and studied detection of its output. Headline numbers from the
abstract: the best existing discriminators separate neural from human-written news at **73%
accuracy** given moderate training data, while **Grover itself detects Grover output at 92%**.

Two cautions for the thesis. First, this is **task D**, provenance, not veracity: a Grover-detected
article may be true, and a human-written article may be fabricated. Conflating the two is a common
error in undergraduate literature reviews. Second, the result is now dated — it concerns a 2019
generator, and the detection-of-LLM-text literature since has repeatedly shown detectors that do not
transfer across generators, which is the same generalisation failure documented in §3, in a different
guise.

### 4.5 Logically — and what its collapse says about the market

Logically (founded 2017, UK) was the most prominent venture-funded "AI fact-checking" company,
combining ML with human analysts and selling to platforms and governments. In July 2025 it filed for
administration after losing contracts with Meta and TikTok as those platforms retreated from
third-party fact-checking; its technology, brand and key assets were bought by Kreatur Ltd in a
pre-pack administration deal. *(Sourced from trade press — Sifted, UKTN, BusinessCloud — not from
company filings I read directly; treat details as press-reported.)*

For the thesis this is context, not a technical result, but it is worth a paragraph: the commercial
viability of automated misinformation detection has depended almost entirely on platform demand, and
that demand proved politically contingent. It reinforces the decision to frame FactLens as a **user-facing
screening aid** — a tool that helps a reader think — rather than as moderation infrastructure.

### 4.6 Browser-based credibility tools

The browser-extension category is where credibility assessment has historically met end users, and
its design conventions are directly relevant even though FactLens ships as a web app with the
extension deferred behind an ingestion port (issue #2). The dominant pattern is **source-level
annotation at link level**: NewsGuard's extension paints a shield icon next to links and search
results, with the band and the nine-criterion breakdown available on click. Related tools in the same
space annotate outlets with bias/reliability ratings drawn from human-curated databases.

The important design observation is that essentially all of these tools annotate the **outlet**, and
those that annotate articles do so with retrieved fact-checks rather than model output. A tool that
scores an *arbitrary pasted text* with a model — which is what FactLens does — is therefore doing
something the deployed ecosystem largely avoids, and inherits a correspondingly larger duty to
communicate uncertainty. *(This subsection is the least primary-sourced in the chapter: I verified
NewsGuard's methodology directly but characterised the extension category from general knowledge and
search summaries rather than from each vendor's documentation. It should be tightened before the
chapter is submitted.)*

---

## 5. How results are surfaced: verdict, score, or signals

Three presentation modes appear in the systems above, in increasing order of epistemic honesty.

**Verdict.** A categorical label — *True / False / Fake / Real*. Used by human fact-checkers on
specific claims, where it is defensible because a person examined evidence for that claim. Used by an
automated classifier over article text it is indefensible, for the reasons set out in ADR-0001: the
model has no access to evidence and the training label encoded provenance, not truth.

**Score.** A continuous number, optionally banded. NewsGuard's 0–100 is the mature example, and its
key property is that the number is **never shown bare**: it always arrives inside a named band with
an action verb, and the band vocabulary ("proceed with caution") describes what the *reader* should
do rather than what the *content* is. ClaimBuster's 0–1 check-worthiness is the other mature example,
and it achieves honesty by redefining the quantity: it scores an annotatable property, so the number
means exactly what it says.

**Signals.** Decomposition into named, individually inspectable components — NewsGuard's nine
criteria are signals with weights. Signals are the strongest defence against overclaiming because
they let a user disagree locally ("it does label ads clearly") without having to accept or reject an
opaque aggregate.

### 5.1 Techniques the better systems use to avoid overclaiming

1. **Redefine the label to something learnable.** ClaimBuster scores check-worthiness, not truth;
   NewsGuard rates outlets, not articles. Both state the unit of assessment explicitly.
2. **Band the score and never show it bare.** Bands convert a false-precision number into a coarse,
   defensible statement.
3. **Use reader-directed language.** "Proceed with caution" is a recommendation about behaviour;
   "this is fake" is an assertion about the world.
4. **Enumerate the components.** Let users audit the aggregate.
5. **Keep a human in the loop for verdicts.** Full Fact's line in §4.2.
6. **Refuse to score out-of-scope inputs.** Satire and Platform labels; the analogue for FactLens is
   an explicit *abstain / insufficient text* band rather than a forced probability.
7. **State limitations inline, not on an About page.** ADR-0001 already commits to this.

### 5.2 Direct consequences for the FactLens interface

- The domain type is a `CredibilityScore` owning a threshold→`VerdictBand` mapping (already decided);
  §4.1 suggests the bands should carry **reader-directed verbs**, and §4.6 suggests an explicit
  out-of-scope band.
- Calibration is not a nicety. A banded score is a claim about probability; temperature scaling plus a
  published reliability diagram is what makes that claim honest.
- Integrated Gradients token attributions are the project's "signals" layer (§5, mode 3) — but they
  are attributions of the *model's* decision, not evidence about the world, and the UI copy must say
  so, or attributions will be read as highlighted "lies".
- The UI should surface which corpus and which split the model was trained and evaluated on, with the
  source-disjoint number, not the in-domain one, as the advertised performance figure.

---

## 6. Implementation stacks

### 6.1 What comparable open-source projects actually use

Surveying the `fake-news-detection` and related GitHub topics, the modal architecture for a
transformer-classifier-behind-a-web-UI project is strikingly consistent:

- **Backend:** FastAPI (occasionally Flask), serving the model **in-process** via
  `transformers` + PyTorch, run under Uvicorn/Gunicorn, packaged with Docker.
- **Model:** a fine-tuned BERT/RoBERTa/DistilBERT checkpoint loaded from a local directory or the
  Hugging Face Hub.
- **Frontend:** either a React SPA calling the API, or Streamlit/Gradio when the UI is a demo rather
  than a product.
- **Explainability:** SHAP or LIME most often; Captum where the project is PyTorch-native.

Representative example: `mihail911/fake-news` — RoBERTa via Hugging Face Transformers and PyTorch
Lightning, served by FastAPI + Gunicorn in Docker, with SHAP-based feature analysis and a Chrome
extension client. Others pair a FastAPI prediction endpoint with a React frontend that displays the
predicted class *and a confidence score*. *(Characterised from GitHub topic listings and repository
descriptions rather than by reading each repository's source; the pattern is consistent enough across
results to state confidently, individual details less so.)*

The practical conclusion is that there is no exotic infrastructure to discover here. A single-model,
stateless, English-text classifier is a solved deployment problem, and the interesting decisions are
about explainability latency and hardware, not about scale.

### 6.2 Serving frameworks — the live options

| Option | Fit for FactLens | Notes |
| --- | --- | --- |
| **FastAPI + `transformers` in-process** | **Strong** | Model loaded at startup, one process, no network hop. Gradients available, so Integrated Gradients works. Matches the ports-and-adapters plan: the model is an adapter behind an inference port. |
| **TorchServe** | **Rejected** | The `pytorch/serve` repository was **archived on 7 August 2025** and the docs carry a "Limited Maintenance" notice: no planned updates, bug fixes, features, or security patches. Not defensible in a 2027 thesis. |
| **BentoML / Ray Serve** | Overkill | Real strengths (adaptive batching, multi-model, autoscaling) address problems a stateless single-model demo does not have. Adds a dependency and a chapter of justification for no measurable gain. |
| **Hugging Face TGI** | Wrong tool | Built for autoregressive *generation*, not sequence classification. |
| **HF Text Embeddings Inference (TEI)** | Poor fit | Optimised Rust/Candle serving for embedding and reranker models; even where it supports classification heads it gives no gradient access, so IG could not run against it. *(I could not confirm its sequence-classification support from the official docs page I fetched — the index page covers embeddings only.)* |
| **ONNX Runtime / Optimum export** | Partial | Good for latency on CPU, but an exported graph is not differentiable in the way Captum needs. Would force a dual-path design: ONNX for scoring, PyTorch for explanations — two copies of the model and a consistency risk. |

**The decisive constraint is Integrated Gradients.** IG requires forward *and backward* passes through
the live model, which means PyTorch must be present at serving time and the model must be reachable
as a `torch.nn.Module`. Every "optimised inference server" option either removes that access or
forces a second model copy. This single requirement collapses the serving decision to: **run the
model in-process in the Python API**.

A second consequence is a latency budget worth measuring early. IG with the usual 32–50 integration
steps costs 32–50 forward+backward passes. On a long-context model over a full news article that is
not interactive-fast on CPU. The recommended shape is therefore **two endpoints**: a fast scoring
call that returns the calibrated `CredibilityScore` and band, and a separate, explicitly-requested
explanation call that returns token attributions — which also matches the UI story, where the score
appears immediately and "why?" is a deliberate second click.

### 6.3 Explainability libraries

- **Captum** (PyTorch/Meta, `pytorch/captum`) — the natural choice: PyTorch-native, ships Integrated
  Gradients, and `LayerIntegratedGradients` is the standard way to attribute to an embedding layer
  for transformer text models. Already the project's decision (issue #2).
- **SHAP / LIME** — model-agnostic and the most common choice in the surveyed repositories, but
  perturbation-based, so they cost many forward passes and give unstable attributions on long text.
- **`transformers-interpret`** — a thin Captum wrapper; convenient but an extra unmaintained-risk
  dependency for little benefit over calling Captum directly.

### 6.4 Frontend

Given "web app, paste-text primary, optional URL fetch, stateless" (issue #2), the realistic options
are:

| Option | Trade-off |
| --- | --- |
| **Server-rendered templates (Jinja2) from FastAPI** | Fewest moving parts, one deployable, no JS build. Weak for the interactive attribution highlighting the UI needs. |
| **Streamlit / Gradio** | Fastest to a demo, and Gradio in particular has built-in highlighted-text components that fit token attribution almost exactly. But it dictates the interaction model, is hard to shape around a `VerdictBand` presentation, and reads as a notebook demo rather than an application in a defence. |
| **React (or Svelte) SPA + FastAPI JSON API** | The modal choice in comparable projects; gives full control over banding, caveat placement and attribution rendering, and keeps the API as a clean port that a browser extension could later reuse. Costs a JS toolchain and a second thing to build and test (thesis task 7). |

The ports-and-adapters commitment argues for a clean JSON API regardless; the only real question is
whether the first UI adapter is templates or an SPA.

### 6.5 Hardware and training-time stack

Settled in issue [#3](https://github.com/aoleszkiewicz/factlens/issues/3): local training on RX 9060
XT (gfx1200) with Arch's `python-pytorch-rocm`, bf16 + SDPA. Nothing in this review changes that.
Worth noting for the serving side: **inference does not need the GPU**. A ~150M-parameter encoder
over a single document is comfortably CPU-servable, which removes ROCm from the deployment story
entirely and makes the app trivially runnable on the examiner's machine — a real advantage for the
functional-testing task.

---

## 7. Stack candidates for decision ticket #9

Three coherent bundles, in the order I would defend them.

### Candidate A — "Monolith" *(recommended)*

FastAPI + `transformers`/PyTorch in-process + Captum + Jinja2 templates (HTMX for the async
explanation call), single Docker image, CPU inference.

- **For:** one deployable, one language, no JS build; the API is still a clean port so an SPA or
  extension can be added later; IG works natively; easiest to demonstrate live at a defence; smallest
  surface for functional tests (task 7).
- **Against:** rich attribution highlighting is more awkward without a component framework; less
  impressive as a "full-stack" artefact.

### Candidate B — "Split" 

FastAPI JSON API (as above) + React/Vite SPA, two containers behind Docker Compose.

- **For:** best UI control for banding, inline caveats and attribution rendering; the API/UI seam is
  visible in the architecture chapter and demonstrates the ports-and-adapters claim; the extension
  story becomes obviously cheap.
- **Against:** a second toolchain, second test setup, and CORS/deployment friction, for a UI whose
  entire job is one text box and one result panel.

### Candidate C — "Demo-first"

Gradio (or Streamlit) app wrapping the model directly, with the domain logic in an importable Python
package.

- **For:** fastest path to something working; Gradio's `HighlightedText` renders token attributions
  out of the box; near-zero deployment effort.
- **Against:** the framework dictates the interaction model, making the ADR-0001 presentation
  commitments (bands, inline caveats, abstain) harder to honour; weakest fit with the ports-and-adapters
  architecture; likely to read as a prototype rather than an application.

**Cross-cutting recommendations regardless of candidate**

1. Serve the model **in-process under PyTorch** — non-negotiable given Integrated Gradients.
2. Do **not** adopt TorchServe (archived, unmaintained since August 2025).
3. Split scoring and explanation into two endpoints with separate latency budgets.
4. Keep ONNX/quantisation as a later optimisation, and only for the scoring path.
5. Pin the calibration (temperature) parameter as part of the model artefact, not the app config, so
   the served score and the reported reliability diagram cannot drift apart.

---

## 8. Open questions this review did not settle

- The ISOT→WELFake/LIAR transfer numbers in §3.3 are **unverified** (publisher returned 403). Read the
  PDF before citing in the thesis, or replace with a transfer experiment run on this project's own
  data — which would be a stronger contribution anyway.
- The `misinfo-general` results tables (§3.4) could not be extracted; if its six-axis protocol is
  adopted for the evaluation chapter, the paper needs a proper read.
- The permuted-label control in Zhou et al. (§3.2) is reported second-hand from the paper's own
  summary and should be checked.
- The browser-extension survey (§4.6) is the thinnest section; each vendor's own documentation should
  be consulted before submission.
- ClaimBuster's current live API surface could not be confirmed (§4.3).
- Whether the primary corpus is NELA-GT, a FakeNewsNet variant, or a custom source-disjoint build is a
  task-3 decision that this review informs but does not make.

---

## 9. References

Ordered by first use.

1. Pelrine, K., Danovitch, J., Rabbany, R. (2021). *The Surprising Performance of Simple Baselines for
   Misinformation Detection.* The Web Conference (WWW '21). arXiv:2104.06952.
   <https://arxiv.org/abs/2104.06952>
2. Zhou, X., Elfardy, H., Christodoulopoulos, C., Butler, T., Bansal, M. (2021). *Hidden Biases in
   Unreliable News Detection Datasets.* arXiv:2104.10130. <https://arxiv.org/abs/2104.10130>
3. Verhoeven, I., Mishra, P., Shutova, E. (2025). *Yesterday's News: Benchmarking Multi-Dimensional
   Out-of-Distribution Generalization of Misinformation Detection Models.* Accepted to *Computational
   Linguistics*, 23 Nov 2025. arXiv:2410.18122. <https://arxiv.org/abs/2410.18122>
4. Pelrine, K., et al. (2025). *A Guide to Misinformation Detection Data and Evaluation.* KDD 2025.
   arXiv:2411.05060. <https://arxiv.org/abs/2411.05060> — dataset collection at
   <https://misinfo-datasets.complexdatalab.com>
5. Horne, B. D., Nørregaard, J., Adali, S. (2019). *Robust Fake News Detection Over Time and Attack.*
   ACM TIST 11(1). <https://dl.acm.org/doi/10.1145/3363818>
6. Bozarth, L., Budak, C. (2020). *Toward a Better Performance Evaluation Framework for Fake News
   Classification.* ICWSM 14(1), 60–71. <https://ojs.aaai.org/index.php/ICWSM/article/view/7279>
7. Zellers, R., Holtzman, A., Rashkin, H., Bisk, Y., Farhadi, A., Roesner, F., Choi, Y. (2019).
   *Defending Against Neural Fake News.* NeurIPS 2019. arXiv:1905.12616.
   <https://arxiv.org/abs/1905.12616>
8. *Fake News Detection: Comparative Evaluation of BERT-like Models and Large Language Models with
   Generative AI-Annotated Data.* *Knowledge and Information Systems* (2024/2025). arXiv:2412.14276.
   <https://arxiv.org/abs/2412.14276>
9. *Fake News Detection: It's All in the Data!* *Applied Sciences* 16(3):1585 (2026).
   <https://www.mdpi.com/2076-3417/16/3/1585> — **numbers unverified, see §3.3**
10. NewsGuard. *Rating Process and Criteria.*
    <https://www.newsguardtech.com/ratings/rating-process-criteria/>
11. NewsGuard. *How It Works.* <https://www.newsguardtech.com/how-it-works/>
12. Full Fact. *Full Fact AI.* <https://fullfact.org/ai/>
13. Hassan, N., et al. (2017). *Toward Automated Fact-Checking: Detecting Check-worthy Factual Claims
    by ClaimBuster.* KDD 2017; and *ClaimBuster: The First-ever End-to-end Fact-checking System*,
    VLDB 2017 (demo). Project: <https://idir.claimbuster.org/>
14. Sifted / UKTN / BusinessCloud (July 2025). Reporting on Logically Ltd entering administration and
    the pre-pack sale of its assets to Kreatur Ltd.
    <https://sifted.eu/articles/logically-ai-fact-check-misinformation-trump-tiktok-meta>
15. PyTorch. *TorchServe — Limited Maintenance notice*; `pytorch/serve` archived 7 Aug 2025.
    <https://docs.pytorch.org/serve/> · <https://github.com/pytorch/serve>
16. Captum. *Introduction.* <https://captum.ai/docs/introduction> · <https://github.com/pytorch/captum>
17. Hugging Face. *Text Embeddings Inference.*
    <https://huggingface.co/docs/text-embeddings-inference/index>
18. `mihail911/fake-news` — RoBERTa + FastAPI + Docker + SHAP reference implementation.
    <https://github.com/mihail911/fake-news>

