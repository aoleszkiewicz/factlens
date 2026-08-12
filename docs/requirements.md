# FactLens — Functional and Non-Functional Requirements

Thesis task 2. Resolved in [#7](https://github.com/aoleszkiewicz/factlens/issues/7).

Vocabulary is that of [`CONTEXT.md`](../CONTEXT.md) — Article Text, Credibility Score, Verdict Band,
Assessment, Token Attribution, Label Gap, Screening Aid. Framing is fixed by
[ADR-0001](adr/0001-credibility-assessment-not-truth-verdict.md); architecture by
[ADR-0002](adr/0002-ports-and-adapters-without-tactical-ddd.md).

`T` marks a requirement directly checkable by a functional test (thesis task 7).

## Functional requirements

### Ingestion and validation

- **FR-1** `T` — The system accepts an Article Text submitted as pasted plain text. Ingestion sits
  behind an `ArticleSource` port; a paste adapter is the only adapter delivered.
- **FR-2** `T` — An Article Text shorter than **100 words** is refused with an explicit
  `TEXT_TOO_SHORT` error. It is refused, not assessed with low confidence: too little evidence to
  score is a different condition from an uncertain score, and conflating them is the system's most
  dangerous failure mode.
- **FR-3** `T` — An Article Text exceeding the model's context window (**8192 tokens**, ≈6000 words)
  is refused with `TEXT_TOO_LONG`. The system never silently truncates: Token Attributions over a
  truncated text misrepresent what the model read.
- **FR-4** `T` — Language is detected before assessment. Non-English input is refused with
  `LANGUAGE_UNSUPPORTED`. An English-trained encoder returns a number for Polish input, and that
  number is noise.

### Assessment

- **FR-5** `T` — A submitted Article Text yields a Credibility Score and its Verdict Band
  synchronously, on a single forward pass, before any Token Attribution work begins.
- **FR-6** — The system defines exactly **three** Verdict Bands — *likely reliable* /
  *inconclusive* / *worth checking* — with a deliberately wide inconclusive middle. Band boundaries
  are derived from calibrated Credibility Scores against the validation split (task 4), not fixed as
  constants in code. Given a reported F1-unreliable near 0.57, most texts landing in the middle band
  is the correct behaviour of a Screening Aid, not a defect.
- **FR-7** — Token Attributions are computed asynchronously as a background job. Integrated
  Gradients costs roughly 32 forward-and-backward passes, which cannot sit on a synchronous request.
- **FR-8** `T` — Progress is delivered over Server-Sent Events in the sequence
  `accepted` → `score` → `progress` → `attributions` → `done`. The `progress` event carries the real
  Integrated Gradients step index; the system does not animate progress over an already-computed
  result.
- **FR-9** — The Assessment covers the entire submitted Article Text, or the interface states
  exactly which portion was omitted. Per-window `attributions` events are a permitted refinement if
  [#11](https://github.com/aoleszkiewicz/factlens/issues/11) selects a windowed strategy.
- **FR-10** `T` — If Token Attribution fails or times out, the Credibility Score and Verdict Band
  still render, and the interface states that attributions are unavailable. Losing the explanation
  never costs the reader the assessment.
- **FR-11** `T` — A dropped SSE connection reconnects and resumes the in-flight job within the store
  TTL. The client retains the submitted Article Text, so the view re-renders in full.
- **FR-12** `T` — Resubmitting an identical Article Text within the TTL returns the cached
  Assessment rather than recomputing it. Deduplication is keyed on the SHA-256 of the normalised
  text.
- **FR-13** `T` — Each failure mode renders as a distinct, named state: `TEXT_TOO_SHORT`,
  `TEXT_TOO_LONG`, `LANGUAGE_UNSUPPORTED`, `MODEL_UNAVAILABLE`, `TIMEOUT`, `QUEUE_FULL`. A generic
  error is not acceptable.

### Screening-aid enforcement

These requirements exist because ADR-0001's framing has to be enforced by the interface, not asserted
in a disclaimer.

- **FR-14** `T` — No view renders a bare Credibility Score. The Verdict Band is always primary; the
  numeric score is reachable only through explicit expansion.
- **FR-15** — Verdict Band names are phrased as reader actions ("worth checking"), never as
  properties of the content ("fake", "false", "unreliable article").
- **FR-16** — The inconclusive band renders with visual weight equal to the other two. It is a
  legitimate outcome, not a failure state, and must not be greyed out or de-emphasised.
- **FR-17** — Every Assessment view keeps the measured Label Gap and the model's honest evaluation
  figures within one interaction's reach.
- **FR-18** `T` — Red/green traffic-light colour coding is prohibited across all Assessment views;
  such coding reads as a verdict on truth.

## Non-functional requirements

### Performance

Stated against **reference hardware** — a single mid-range 16 GB GPU — so the requirements survive a
change of host. Host selection belongs to [#9](https://github.com/aoleszkiewicz/factlens/issues/9).

- **NFR-1** `T` — Credibility Score and Verdict Band: **p95 ≤ 1s** end-to-end for an Article Text of
  1000 words.
- **NFR-2** `T` — Token Attributions: **p95 ≤ 30s** for an Article Text at the full 8192-token
  context.
- **NFR-3** `T` — Hard per-job timeout of **120s**, after which the reader receives `TIMEOUT`. No
  request hangs indefinitely.
- **NFR-4** — Model inference is **never automatically retried**. Inference is deterministic: a retry
  reproduces the failure at double the cost.
- **NFR-5** `T` — The attribution queue is bounded (depth 8). A submission beyond the bound receives
  `QUEUE_FULL` (HTTP 503) rather than accumulating unbounded work.
- **NFR-6** `T` — Model cold start completes within **60s** and is excluded from NFR-1 and NFR-2. A
  readiness probe prevents the interface dispatching work to an unloaded model.
- **NFR-7** — One inference worker; requests are serialised. Concurrent multi-user throughput is not
  claimed, and the thesis states so rather than implying unmeasured capacity.

### Data handling

- **NFR-8** `T` — **Article Text is never persisted** — not to disk, not to a database, not to logs
  at any level. Only the derived Assessment (score, band, attribution weights, token offsets) is held.
- **NFR-9** — Job results live in an in-process TTL store (**30 minutes**) behind a `JobStore` port,
  and evaporate on restart. Redis or a database are later adapters, adopted when a requirement
  demands them rather than in anticipation.

### Accessibility

- **NFR-10** `T` — The interface conforms to **WCAG 2.1 AA**.
- **NFR-11** `T` — Token Attribution strength is conveyed by at least one channel besides colour —
  underline weight, a numeric value on focus, or an ordered list of top-contributing spans.

### Architecture

- **NFR-12** `T` — The domain core imports no framework or ML library. Enforceable as an import-lint
  test, per ADR-0002.
- **NFR-13** — The system is deployment-agnostic: no requirement names a specific host or cloud
  provider.

## Out of scope

Stated explicitly so the defence has a crisp answer to "why does it not do X?".

- **URL ingestion.** The `ArticleSource` port exists and a URL adapter is a later addition, but
  boilerplate stripping, paywalls, JS-rendered pages and SSRF are a body of work orthogonal to the
  thesis, whose failure modes would dominate discussion of a system that does not care about them.
- **Sharing or persisting Assessments.** No shareable result links, no history, no user accounts. A
  link opened by a second reader would carry a Credibility Score with no Article Text to attribute it
  over, which FR-14 forbids outright.
- **Bulk or batch submission.** The brief's "user application" is one reader assessing one article.
- **Multi-user concurrent throughput.** See NFR-7.
- **Polish-language input.** A named future extension, not a degraded mode — see FR-4.
