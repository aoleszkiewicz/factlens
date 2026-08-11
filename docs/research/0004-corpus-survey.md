# Research 0004 — Corpus survey: article-level, multi-source disinformation datasets

Resolves the research question in [issue #4](https://github.com/aoleszkiewicz/factlens/issues/4).
Date: 2026-08-11. Author: research agent.

**This note does not make the call.** It ranks corpora and states what each one's label
actually encodes and which split protocol it can honestly support. The decision belongs to
[#8](https://github.com/aoleszkiewicz/factlens/issues/8).

Task: English **document-level** credibility classification, binary, evaluated under a
**source-disjoint** or **temporal** split. Motivating negative result: ISOT is saturated
(TF-IDF+LogReg F1 ≈ 0.99) because train and test share the same two outlets, so the model
learns Reuters register rather than credibility.

Everything marked **[measured]** was computed by this agent against the live distribution on
2026-08-11; the script inputs are the public CSVs / APIs named in each case. Everything else is
cited to a primary source. Section 9 separates verified from uncertain.

---

## 1. Ranked recommendation

| # | Corpus | Why | What it costs you | Split protocol it supports |
|---|---|---|---|---|
| **1** | **`misinfo-general`** (Verhoeven, Mishra & Shutova, *Computational Linguistics*, accepted Nov 2025) — 4.16 M articles, 488 publishers, 2017–2022, rebuilt from NELA-GT | The only corpus surveyed that **ships the split protocol itself**: seven pre-built train/test splits including *Publisher* (source-disjoint), *Time*, *Topic*, *Political Bias* and *Misinformation Type*. Publisher-identifying text is masked, duplicates removed. It also publishes the honest baseline the thesis needs to beat/contextualise: DeBERTa-v3 gets **MCC 0.46 uniform → 0.37 publisher-OoD**, F1-unreliable **0.57**. And it *quantifies the Label Gap directly* (§4.1) | Labels are **outlet-level MBFC**, not per-article verdicts. Gated (access request) + CC BY-NC-SA 4.0. 9.62 GB. Text carries `<copyright>` / `<twitter>` / `<url>` / `<selfref>` mask tokens | **Source-disjoint (pre-built), temporal (pre-built), topic, political-bias, misinfo-type.** Best-in-class |
| **2** | **NELA-GT-2018…2022** (raw) | Same underlying content, full control over splitting; 361–519 outlets per year, ~1.8 M articles/year, MBFC labels | **Availability is now the blocker** — all five Harvard Dataverse DOIs return zero released versions as of today **[measured]**. Also carries NELA's own `@`-token copyright masking. If you can obtain it, you must build the publisher-disjoint split and the de-duplication yourself, which is exactly the work `misinfo-general` already did | Source-disjoint and temporal, if you can get the files |
| **3** | **ReCOVery** (Zhou et al., CIKM 2020) | **Full `body_text` is distributed directly in the repo** — no crawl, no link rot. 2,029 articles, 55 publishers (22 reliable / 33 unreliable), so a source-disjoint split is genuinely constructible **[measured]**. Long documents: median 630 words **[measured]** | Tiny; single topic (COVID-19); **single year (2020)** so no temporal split is possible; outlet-level labels; 67/33 class imbalance | **Source-disjoint only.** Best used as a *secondary, out-of-domain transfer test set*, not as the training corpus |
| **4** | **FakeNewsNet / PolitiFact** | The only article-level set surveyed whose labels are **per-article fact-checker verdicts** (PolitiFact), and 301 distinct publishers behind 432 fake articles | Ships **headline + URL only** — `id,news_url,title,tweet_ids` **[measured]**; body text requires a crawl. **60 % of sampled fake-class URLs are unreachable today vs 37 % of real-class URLs [measured]** — the attrition is *correlated with the label*, which biases whatever survives. Social context needs a paid X API. 432+624 articles is too small to fine-tune on | Source-disjoint in principle; in practice the recoverable subset is too small and too biased |
| **5** | **LIAR** (Wang, ACL 2017) | 12.8 K PolitiFact statements, six-way veracity, a decade of coverage. Genuine per-claim expert verdicts | **Claim-level, not document-level** — single short statements, no article body. Cannot train the system the thesis specifies | **Contrast only.** Keep it for the "granularity contrast" argument: it shows what a *real* per-utterance verdict label looks like, and why document-level labels are necessarily a proxy |
| **6** | **Hyperpartisan News Detection** (SemEval-2019 Task 4) | Ships **both** label regimes for the same task: 754 K distant-supervised (publisher-level) articles and 1,273 **manually labelled at article level**. Best system reached only **0.822 accuracy** on the manual balanced set | Task is hyperpartisanship, not credibility; the by-article set is tiny | Useful as an **external, human-labelled article-level test set** to sanity-check a model trained on outlet labels |
| **7** | **CoAID** (Cui & Lee 2020) | — | **Do not use as a primary corpus.** It is an ISOT-shaped trap with different furniture (§5) | None that is honest |
| **8** | **GossipCop** (the other half of FakeNewsNet) | Larger (5,323 fake / 16,817 real **[measured]**) | Celebrity-gossip domain; "real" class is largely E!/entertainment-desk copy. Off-domain for a news-credibility screener and register-separable in the same way ISOT is | Not recommended |
| **9** | **ISOT** (already held) | — | Retain exactly as issue #2 already specifies: a **contrast experiment** demonstrating what a source-confounded split buys you | Same-source split (that is the point) |

**Suggested spine for #8, if it helps the decision:** train on `misinfo-general` under its
*Uniform* split and its *Publisher* split, report both, and use ReCOVery (+ optionally the
Hyperpartisan by-article set) as an untouched external transfer test. ISOT stays as the
cautionary contrast. That produces the exact table the thesis's evaluation chapter needs:
in-domain number, source-disjoint number, external-transfer number, and the saturated number.

---

## 2. The decisive axis: what the label actually encodes

Verhoeven et al. give the cleanest taxonomy, and it is the one to adopt in the thesis
([arXiv:2410.18122](https://arxiv.org/abs/2410.18122), §3.1):

1. **Claim** — experts fact-check individual complete statements in isolation. *LIAR.*
2. **Article** — experts label the *overall* veracity of whole documents, which may contain many
   claims "whose factuality need not be consistent with each other". *FakeNewsNet/PolitiFact,
   Hyperpartisan by-article.*
3. **Publisher** — experts label outlets "for their propensity for factual reporting, based on
   historical records and prescribed authorial intent. These labels are often used as a proxy for
   finer-grained labels. The articles produced by publishers do not necessarily have the same
   label as the publisher." *NELA-GT, `misinfo-general`, ReCOVery, CoAID's "real" class.*

Their blunt statement of the trade-off: "The more fine-grained annotation methods yield
high-quality labels, but can be prohibitively expensive to procure… the more coarse-grained
annotation methods run the risk of introducing noise into the labels, by assuming consistency
between finer-grained labels."

**Every article-level corpus large enough to fine-tune a transformer on uses publisher-level
labels.** That is not a flaw in the survey; it is the state of the field. It is also precisely
the Label Gap that ADR-0001 commits to naming rather than hiding.

### 2.1 The Label Gap, measured

Verhoeven et al. manually annotated 362 articles sampled from `misinfo-general`, stratified over
publisher and subjectivity level (§8.3):

- For **unreliable** publishers, **43.50 %** (95 % CI 36.62–50.37) of articles were "clear cases
  of non-credible news".
- For **reliable** publishers, **8.20 %** (95 % CI 4.07–12.32) were judged non-credible.
- "The odds of a non-credible article being published by an unreliable publisher are **8.62 times
  higher** than for a reliable publisher."

This is the single most useful number in the survey. It says: an outlet-level label is a real
signal (8.6× odds ratio) and simultaneously a *bad* article-level label (more than half of
"unreliable" articles are not non-credible). A thesis that quotes this can say honestly what its
classifier's positive prediction means — which is exactly the framing ADR-0001 mandates.

### 2.2 …and the counterpart: publishers are *not* trivially identifiable after masking

Verhoeven et al. also ran the obvious control (§8.1): replace the credibility label with a
publisher-identity label and re-train. Result: **MCC 0.18, micro-F1 0.14, macro-F1 0.04** — far
below the misinformation-label scores. Their conclusion: "while it is possible to predict the
publisher from an article with above random performance, this is only really possible for the most
prolific publishers, and this cannot entirely explain performance in misinformation
classification."

This is the answer to the ISOT objection. Register leakage is real but is *not* the whole story
once publisher-identifying text is masked and duplicates removed — provided the publisher pool is
large. Which brings us to:

### 2.3 Publisher diversity is the variable that controls the honest number

Verhoeven et al. §7.2 re-ran the *Publisher* split while restricting training to the top-*n* most
prolific publishers per label class:

- Full publisher pool: source-disjoint generalisation gap ≈ **0.10 MCC**.
- Top-1 publisher per class: gap rises to ≈ **0.50 MCC**.

Their conclusion: "the underestimation of the generalization gap will be especially egregious in
datasets with a small pool of publishers (e.g., those that sample from a single reliable source to
boost label balance)."

That sentence *is* the ISOT diagnosis, stated independently in a peer-reviewed venue, and it is
the criterion by which every corpus below should be judged: **how many distinct outlets stand
behind each class?**

---

## 3. Comparison table

| | `misinfo-general` | NELA-GT (2018–22) | ReCOVery | FakeNewsNet/PolitiFact | FakeNewsNet/GossipCop | CoAID | LIAR | Hyperpartisan | ISOT |
|---|---|---|---|---|---|---|---|---|---|
| **Label encodes** | Outlet (MBFC, scraped Oct 2024), binarised: Questionable Source / Conspiracy-Pseudoscience / Satire → unreliable | Outlet (MBFC), reliable/mixed/unreliable | Outlet ("extreme levels of credibility"), binary | **Per-article PolitiFact verdict** | Per-article GossipCop rating | Mixed: fake = fact-checked social posts; real = trusted-outlet list | **Per-claim PolitiFact verdict**, 6-way | *Both*: 754 K by-publisher, 1,273 **by-article human** | Outlet (Reuters vs a set of flagged sites) |
| **Granularity** | Full article text | Full article text | Full `body_text` | **Headline + URL only** | **Headline + URL only** | Title + partial `content` | Single short statement | Full article text | Full article text |
| **Distribution** | HF Hub + Dataverse, **gated** (access request), `.arrow` + `duckdb` metadata, 9.62 GB | Harvard Dataverse — **all five DOIs return no released version** [measured] | GitHub CSV, **text included** | GitHub CSV of URLs + crawler; text must be crawled | same | GitHub CSVs | HF / UCSB, direct | Zenodo (task data) | Kaggle CSV |
| **Licence** | CC BY-NC-SA 4.0 | not stated in repo README | `License.md` in repo; social data withheld under Twitter policy | "(C) 2019 Arizona Board of Regents on Behalf of ASU"; "Complete dataset cannot be distributed because of Twitter privacy policies and news publisher copy rights" | same | not stated on repo page | "unknown" on HF card | task licence | — |
| **Link rot** | none (text shipped) | none (text shipped) | none | **60 % of sampled fake URLs non-200; 37 % of real URLs non-200** [measured] | **32 % non-200** [measured] | n/a for shipped `content`; URLs are mostly social posts | none | none | none |
| **Distinct outlets** | **488** | 361 (2022) / 367 (2021) / 519 (2020) | **55** (22 reliable, 33 unreliable) [measured] | 301 publishers behind 432 fake pieces | 209 behind 6,048 fake pieces | real: 48 domains, **top 3 = 73 %**; fake: 517/925 are facebook.com [measured] | n/a (claims) | not verified | **2** |
| **Time span** | 2017–2022 | 2018–2022, ~1 yr per release | **2020 only** [measured] | ~2010s | ~2010s | May–Nov 2020 | 2007–2016 | 2018 | 2016–2017 |
| **Size** | **4.16 M** articles (from 7.24 M raw) | ~1.78 M (2022), ~1.86 M (2021), ~1.78 M (2020) | **2,029** [measured] | 432 fake / 624 real [measured] | 5,323 fake / 16,817 real [measured] | 925 fake-news rows / 4,532 real-news rows; 28 fake claims / 490 real claims [measured] | 12.8 K | 754 K + 1,273 | 44.9 K |
| **Class balance** | ~60 % reliable | skewed reliable | 1,364 / 665 = 67/33 [measured] | 41/59 | 24/76 | ~17/83, and the two classes differ in *kind* | 6 labels, 1,050 pants-fire | balanced by design in the by-article set | ~50/50 |
| **Language** | English | English | English | English | English | English | English | English | English |
| **Doc length** | long-form news | long-form news | **median 630 words; 76 % > 380 words (≈512 BPE)** [measured] | n/a (headline only) | n/a | fake median **18 words**, real median **74 words** [measured] | ~17 words | long-form | 44 % > 512 tokens (our own measurement, #6) |
| **Split protocol** | **publisher / time / topic / bias / type, pre-built** | publisher + temporal, DIY | publisher only | publisher, but sample too small | publisher | none honest | n/a | publisher → article transfer | same-source only |

---

## 4. `misinfo-general` — the headline candidate

**Primary sources.** Verhoeven, Mishra & Shutova, "Yesterday's News: Benchmarking
Multi-Dimensional Out-of-Distribution Generalization of Misinformation Detection Models",
*Computational Linguistics* (accepted 23 Nov 2025), [arXiv:2410.18122v4](https://arxiv.org/abs/2410.18122);
repo [github.com/ioverho/misinfo-general](https://github.com/ioverho/misinfo-general);
data [huggingface.co/datasets/ioverho/misinfo-general](https://huggingface.co/datasets/ioverho/misinfo-general).

**Provenance.** "All raw articles come from the various News Landscape (NELA) corpora produced by
the MELA lab… The corpora cover 2017–2022 (6 iterations) almost continuously… In their original
form, the 6 iterations together consist of 7.2 million long-form articles."

**Relabelling.** The authors did *not* trust NELA's shipped labels: "due to inconsistencies across
dataset iterations and the frequency of labelling errors, we chose to relabel the dataset
completely." They re-scraped MBFC as of Oct 2024, mapped URL domains to a consistent publisher set,
and identified **488 distinct publishers**, "many of which were falsely attributed in NELA's
original set of publishers". They also document 20 publishers whose MBFC rating changed
substantively during 2017–2024 (12 of 20 downgraded reliable→unreliable).

**Cleaning.** "Of the 6.7M re-labelled articles, roughly ≈ 22 % or 1.5M articles were duplicates."
After removing malformed articles too, "we remove approximately ≈ 43 % of all downloaded articles.
The final dataset contains 4.2 million cleaned articles." PII is masked; NELA's repeated `@`
copyright tokens are standardised into a `<copyright>` special token, alongside `<twitter>`,
`<url>` and `<selfref>`.

**Pre-built splits** (§5.1), all at 70/10/20 %:

0. *Uniform* — stratified random over articles (the dishonest baseline).
1. *Time* — train on one year, test on other years, publishers held constant.
2. *Event* — hold out all COVID-19 articles.
3. *Topic* — hold out the k smallest topic clusters (~20 % of articles).
4. ***Publisher* — hold out the k least frequent publishers (~20 % of articles). This is the
   source-disjoint split.**
5. *Political Bias* — train on Centre + one side, test on the other.
6. *Misinformation Type* — train on one of Questionable-Source / Conspiracy-Pseudoscience, test on
   the other.

**Published baseline** (DeBERTa-v3-base, article-level, Table 2 — MCC / F1-reliable / F1-unreliable):

| Split | MCC ID | MCC OoD | Δ | F1-unrel. ID | F1-unrel. OoD |
|---|---|---|---|---|---|
| Uniform | 0.46 | 0.46 | 0.00 | 0.57 | 0.57 |
| Time | 0.46 | 0.33 | **−0.13** | n/a | n/a |
| Event (COVID) | 0.43 | 0.46 | +0.03 | 0.52 | 0.55 |
| Topic | 0.46 | 0.38 | −0.08 | 0.56 | 0.50 |
| **Publisher** | 0.48 | **0.37** | **−0.10** | 0.58 | 0.53 |
| Political bias → Right | 0.56 | **0.19** | **−0.37** | 0.58 | 0.26 |
| Misinfo type → Questionable | 0.43 | 0.23 | −0.20 | 0.41 | 0.25 |

Two things to notice. First, **even the in-distribution number is modest** — MCC 0.46, F1 on the
unreliable class 0.57. The authors: "classification performance falls short of desired… classifying
unreliable articles is considerably more difficult — a trend that holds consistently across
generalization forms. This is especially surprising given the high accuracy scores reported for
similar models on other misinformation datasets." That is the honest ceiling this task has, and it
is the direct rebuttal to ISOT's 0.99. Second, the **political-bias axis (−0.37) hurts far more
than the publisher axis (−0.10)** — worth a paragraph in the thesis, since it is a fairness result,
not just a robustness one.

**Temporal behaviour** (Table 3, MCC by train-year × eval-year): models are "surprisingly robust"
across adjacent years (2019–2022 all land in 0.44–0.47 on each other), but 2017 is an outlier
(models not trained on 2017 score 0.26–0.34 on it). A train-on-earlier / test-on-later temporal
split is therefore viable but will produce a *small* gap unless the years are far apart.

**LLM comparison, useful for the thesis's "existing solutions" chapter (task 1):**
`llama-3-8b-instruct` zero-shot at 512 tokens manages **MCC 0.25** against the fine-tuned model's
0.46 ID / 0.33 OoD, and took ~70 h on an A100 for the corpus versus ~12.5 h to train *and* evaluate
the encoder. Reasoning models (Gemini 2.5 Flash Lite 0.46, DeepSeek Reasoner 0.52) beat the
fine-tuned model on a 28 K stratified subset — but the authors caution these "are likely not
directly comparable to the purely inductive, fine-tuned models", since the reasoning traces cite
publishers and entities known a priori.

**Costs and caveats.**
- Gated on both HF and Dataverse: "You need to agree to share your contact information to access
  this dataset"; access is granted after accepting the terms. **This needs to be requested early** —
  it is a human-in-the-loop step with unknown latency, and it blocks everything downstream.
- CC BY-NC-SA 4.0. Non-commercial is fine for a thesis; share-alike affects any derived corpus you
  publish.
- 9.62 GB; `.arrow` shards + a `duckdb` file of publisher metadata.
- The masking tokens are in the text. For fine-tuning this is mostly harmless, but for **Integrated
  Gradients displays in the UI it matters** — a `<copyright>` token will receive attribution and
  will look like a bug to a reader. Worth a note for #11.
- The authors are explicit that residual noise remains: "articles from the same publisher tend to
  contain unique by-lines, attribution messages, or donation requests."

---

## 5. CoAID — why it is a trap, in numbers

**[measured]** Parsing all four release folders of
[github.com/cuilimeng/CoAID](https://github.com/cuilimeng/CoAID) (05-01, 07-01, 09-01, 11-01-2020;
sums are over folders, not de-duplicated):

| | rows | rows with non-empty `content` | median words | distinct domains | top domains |
|---|---|---|---|---|---|
| `NewsFakeCOVID-19` | 925 | 416 | **18** | 160 | **facebook.com 517**, twitter.com 74, youtube.com 37, youtu.be 21, instagram.com 21 |
| `NewsRealCOVID-19` | 4,532 | 4,024 | **74** | 48 | **webmd.com 1,709**, cdc.gov 1,031, healthline.com 586, medicalnewstoday.com 463, sciencedaily.com 347, who.int 158 |
| `ClaimFakeCOVID-19` | 28 | 0 | — | 1 | medicalnewstoday.com |
| `ClaimRealCOVID-19` | 490 | 0 | — | 2 | who.int 452 |

Read that table as a classifier would. The "real news" class is 38 % WebMD and 23 % CDC — a single
institutional health-explainer register, median 74 words. The "fake news" class is 56 %
**Facebook post URLs**, median 18 words. A model separating these two classes is separating
*WebMD prose from Facebook captions*; it needs no notion of credibility whatsoever. This is ISOT's
failure mode with COVID furniture, and it is worse, because the two classes differ in medium, not
only in outlet.

Note also that CoAID's *fake* side genuinely is per-item fact-checked (each row carries a
`fact_check_url` to Health Feedback, PolitiFact, etc.) while its *real* side is a curated
trusted-source list. **The two classes therefore do not share a labelling procedure at all** — the
label is confounded with the annotation pipeline. Whatever the model learns, the "reliable" class
means "was on the trusted-source list", not "was checked and found accurate".

Verhoeven et al. name the general pattern (§3.3): "An unwanted side effect of having a small,
homogenous publisher set, is the introduction of a modelling shortcut; misinformation classifiers
no longer need to analyze the veracity or intent of input content, but rather simply discriminate
between a few publishers with unique idiosyncrasies."

CoAID's honest use in this thesis is as a **second worked example of the shortcut**, alongside
ISOT, in whatever chapter argues for the source-disjoint protocol. It is a better example than
ISOT, because the confound is visible in the *URL column* without training anything.

---

## 6. FakeNewsNet — the link-rot measurement

**Distribution.** The repo README is explicit: "Complete dataset cannot be distributed because of
Twitter privacy policies and news publisher copy rights." What ships is metadata only. **[measured]**
the CSV schema is `id,news_url,title,tweet_ids` — **headline and URL, no body text**. Body text
requires running the provided crawler over the `news_url` column; social context requires X/Twitter
API keys, which since 2023 are a paid product.

**Sizes [measured]** (row counts of the four CSVs on `master`, minus header):
PolitiFact 432 fake / 624 real; GossipCop 5,323 fake / 16,817 real.

**Publisher spread** (paper, §4): "there are in total 301 publishers publishing 432 fake news
pieces, among which 191 of all publishers only publish 1 piece of fake news… For Gossipcop, there
are in total 209 publishers publishing 6,048 fake news pieces."

**Link rot [measured].** I probed a systematic sample (every *k*-th URL, browser UA, 12 s timeout,
`curl -L`) of each file on 2026-08-11:

| File | sampled | HTTP 200 | 404 | 403 | conn. failure (`000`) | other | **non-200** |
|---|---|---|---|---|---|---|---|
| `politifact_fake` | 60 / 428 | 24 (**40 %**) | 11 | 6 | **17** | 2 | **60 %** |
| `politifact_real` | 60 / 567 | 38 (**63 %**) | 5 | 7 | 7 | 3 | **37 %** |
| `gossipcop_fake` | 60 / 5,067 | 41 (**68 %**) | 4 | 9 | 4 | 2 | **32 %** |

Two caveats on my own numbers: a `403` may be bot-blocking rather than removal (a real crawler with
a session might recover some), and a `200` may be a parked domain or a redirect to a homepage — so
**40 % is an upper bound on genuinely recoverable fake-class articles, not a lower bound**. The
`000` failures are DNS/connection failures, i.e. the domain itself is gone; there are 17 of 60 in
the PolitiFact fake class and 4 of 60 in the GossipCop fake class.

The important finding is not the absolute rate but the **differential**: for PolitiFact, 60 % of the
fake class is unreachable against 37 % of the real class. Fake-news domains die; nytimes.com does
not. Any corpus rebuilt by crawling FakeNewsNet today is therefore **biased by the label** — the
surviving fake articles are disproportionately those hosted on durable infrastructure (YouTube,
Facebook, long-lived partisan sites), which is a different population from the one PolitiFact
originally checked. This is a leakage risk in its own right and it compounds the small-sample
problem: after rot, PolitiFact/FakeNewsNet yields on the order of 170 fake articles.

**Reported baselines** (paper, Table 3) are worth quoting in the thesis precisely because they are
*low*: on PolitiFact, logistic regression 0.642 accuracy, CNN 0.629, best social-fusion model 0.691;
on GossipCop, 0.648 / 0.723 / 0.689. A serious article-level task does not score 0.99.

---

## 7. ReCOVery — small, but the only "just works" option

**Primary sources.** Zhou, Mulay, Ferrara & Zafarani, "ReCOVery: A Multimodal Repository for
COVID-19 News Credibility Research", CIKM 2020, [arXiv:2006.05557](https://arxiv.org/abs/2006.05557);
repo [github.com/apurvamulay/ReCOVery](https://github.com/apurvamulay/ReCOVery).

Method: ~2,000 publishers assessed, 60 retained "with extreme levels of credibility"; articles
inherit "the credibility of the media on which they were published" — outlet-level, and the paper
is upfront that this is "a trade-off between scalability and label accuracy".

**[measured]** on `dataset/recovery-news-data.csv`:

- 2,029 rows; columns `news_id, url, publisher, publish_date, author, title, image, body_text,
  political_bias, country, reliability`. **`body_text` is populated** — no crawl needed.
- `reliability`: 1,364 reliable (1) / 665 unreliable (0) → 67/33.
- **55 distinct publishers**: 22 on the reliable side, 33 on the unreliable side. (The repo says
  "22 reliable and 38 unreliable websites"; 33 distinct publisher *strings* appear in the data.)
- Top publishers: Chicago Sun-Times 322, Business Insider 158, Sputnik News 144, The Verge 139,
  USA Today 118, NPR 92, WorldHealth.Net 75, NYT 67, CBS 67, Reuters 67, Politico 66.
- All publish dates are in **2020** (2,014 of 2,029 parse to 2020; 15 blank).
- Document length: **median 630 words, mean 839; 76 % exceed 380 words** (~512 BPE tokens at the
  usual ~1.35 tokens/word ratio). Reliable median 636, unreliable median 617 — so length is *not*
  a class shortcut here, which is a point in ReCOVery's favour and worth stating.

Assessment: 55 outlets is enough for a source-disjoint split to mean something, and it is 27×
better than ISOT's two — but note §2.3: with a pool this small the measured generalisation gap is
still an underestimate. The single-year, single-topic scope rules out any temporal evaluation.
2,029 documents is too few to fine-tune a transformer from scratch on but ideal as a **held-out
transfer set** for a model trained on `misinfo-general`, and the 76 %-over-512-tokens figure makes
it a useful second data point for the long-document decision in #11 (our ISOT measurement was 44 %).

Note the concentration risk: Chicago Sun-Times alone is 16 % of the corpus. A source-disjoint split
here must be constructed carefully, not sampled at random.

---

## 8. NELA-GT availability — a live problem

The NELA-GT family (Horne et al. 2018; Nørregaard et al. 2019; Gruppi et al. 2020, 2021, 2022,
2023) is the standard publisher-labelled news corpus: ~1.78 M articles / 361 outlets (2022),
1.86 M / 367 (2021), 1.78 M / 519 (2020), MBFC labels per outlet, SQLite3 + JSON, distributed via
Harvard Dataverse.

**[measured] on 2026-08-11**, querying the Dataverse versions API
(`/api/datasets/:persistentId/versions`) with a browser user-agent:

| Dataset | DOI | released versions returned |
|---|---|---|
| NELA-GT-2018 | `10.7910/DVN/ULHLCB` | **none** |
| NELA-GT-2019 | `10.7910/DVN/O7FWPO` | **none** |
| NELA-GT-2020 | `10.7910/DVN/CHMUYZ` | **none** |
| NELA-GT-2021 | `10.7910/DVN/RBKVBM` | **none** |
| NELA-GT-2022 | `10.7910/DVN/AMCV2H` | **none** |
| NELA-PS (pink-slime) | `10.7910/DVN/YHWTFC` | 3 (v1.0 CC BY 4.0 → v1.2 CC BY-NC 4.0, **files now `restricted=True`**) |

The DOIs still resolve and return dataset records (publication dates 2023-03-16 for 2022,
2022-03-10 for 2021), but no version's file list is served — the signature of a **deaccessioned**
dataset. NELA-PS, queried identically, returns three versions and file listings, so this is not an
artefact of my query. A search of the Harvard Dataverse catalogue for "NELA-GT" also returns no
NELA-GT datasets (only NELA-PS). One secondary source encountered during this survey likewise notes
NELA-GT-2022 "appears to have been deaccessioned from its original location". I could not reach the
Dataverse HTML landing pages (Cloudflare interstitial), so **a human should confirm in a browser
before this is treated as settled** — but plan on it being true.

Also relevant even if the files are recoverable: NELA applies copyright masking to article text.
Per the repo README, "For articles with more than 200 tokens, we replace 7 tokens with `@` every
100 tokens. For articles with fewer than 200 tokens, we replace 5 consecutive tokens with `@` every
20 tokens." So NELA text is *already* lossy; `misinfo-general` inherits this and merely relabels the
mask token.

**Practical consequence.** `misinfo-general` is not merely the more convenient route to NELA
content — as of today it may be the *only* maintained route to it, and it is the one that already
did the relabelling, de-duplication and split construction. This raises it from "nice option" to
"first choice" on availability grounds alone.

---

## 9. What was verified vs. what is uncertain

**Verified by direct measurement (scripts run 2026-08-11 against live public endpoints):**
FakeNewsNet CSV row counts and schema; FakeNewsNet HTTP reachability rates on three systematic
60-URL samples; CoAID row counts, `content` occupancy, median word counts and domain distributions
across all four release folders; ReCOVery row count, class balance, publisher count, publish-year
distribution, body-text length distribution; Dataverse version/file status for six NELA DOIs.

**Verified by primary source (read directly):** all `misinfo-general` figures (arXiv:2410.18122v4,
§§3–8 and Tables 1–5); the misinfo-general HF/GitHub distribution terms, licence and size; the
NELA-GT per-year counts, label scheme and masking rule (MELALab README); FakeNewsNet's
non-distribution statement, licence line, publisher spread and Table 3 baselines (arXiv:1809.01286);
ReCOVery's methodology and repo schema; LIAR's size, source and statement-level granularity
(ACL P17-2067); SemEval-2019 Task 4 sizes and best score (ACL S19-2145).

**Uncertain / not verified:**

- **NELA-GT deaccession.** Strongly indicated by the API, not confirmed in a browser or by the
  authors. Someone should load one landing page manually or email MELALab.
- **CoAID totals** are sums over four release folders **without de-duplication**; the paper reports
  4,251 news items and the repo README says 5,216, against my sum of 5,457. The domain-distribution
  and length findings are robust to this; the exact totals are not.
- **ReCOVery licence text** — a `License.md` exists in the repo; I did not read its terms.
- **FakeNewsNet 403s** may partly be bot-blocking rather than true removal; my 40 %-reachable figure
  for the fake class is an upper bound on recoverability but the *differential* against the real
  class is the robust part.
- **LIAR split sizes** (commonly cited as 10,269 / 1,284 / 1,283) were not verified; the HF card is
  incomplete and licence is listed as "unknown".
- **Document-length distributions** for `misinfo-general` / NELA were not measured (gated download).
  They are described as "long-form articles" by both author groups; assume ISOT-like or longer.
- **Not surveyed in depth** (mentioned only for completeness, no primary source read): NELA-Local
  (arXiv:2203.08600), NELA-PS (arXiv:2403.13657, now access-restricted), FakeNewsCorpus / OpenSources,
  MuMiN, FakeHealth, MM-COVID, TruthSeeker, MCFEND. Of these, **NELA-Local** is the only one likely
  to change the ranking, and only if it offers a comparable publisher pool.

---

## 10. Sources

- Verhoeven, Mishra & Shutova (2025). *Yesterday's News: Benchmarking Multi-Dimensional
  Out-of-Distribution Generalization of Misinformation Detection Models.* Computational Linguistics
  (accepted). https://arxiv.org/abs/2410.18122 · https://github.com/ioverho/misinfo-general ·
  https://huggingface.co/datasets/ioverho/misinfo-general
- Gruppi, Horne & Adalı (2022). *NELA-GT-2022.* https://arxiv.org/abs/2203.05659 ·
  https://github.com/MELALab/nela-gt · Harvard Dataverse API, queried 2026-08-11
- Zhou, Mulay, Ferrara & Zafarani (2020). *ReCOVery.* CIKM. https://arxiv.org/abs/2006.05557 ·
  https://github.com/apurvamulay/ReCOVery
- Shu, Mahudeswaran, Wang, Lee & Liu (2018/2020). *FakeNewsNet.* https://arxiv.org/abs/1809.01286 ·
  https://github.com/KaiDMML/FakeNewsNet
- Cui & Lee (2020). *CoAID.* https://arxiv.org/abs/2006.00885 · https://github.com/cuilimeng/CoAID
- Wang (2017). *"Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection.* ACL.
  https://aclanthology.org/P17-2067/
- Kiesel et al. (2019). *SemEval-2019 Task 4: Hyperpartisan News Detection.*
  https://aclanthology.org/S19-2145/
