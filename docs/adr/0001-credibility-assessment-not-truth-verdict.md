# ADR-0001 — Credibility assessment, not a verdict on truth

**Status:** accepted

## Decision

The system outputs a calibrated **Credibility Score** over **Unreliable Content**, presented as a
**Screening Aid**. The **Label Gap** is named and measured in the dataset chapter rather than
papered over.

## Context

The thesis title names *dezinformacja* — false information spread with intent to deceive. Two
things block a literal reading:

- No supervised classifier over article text can infer intent.
- No available corpus label encodes it.

Every candidate corpus offers a proxy instead: publisher provenance, a fact-checker's verdict on a
single claim, or a crowd credibility rating.

## Considered options

| Option | Verdict |
|---|---|
| **Claim the label is disinformation** | Rejected. Not defensible under questioning. The first examiner to ask *"so a fabricated story written in wire-service style is Real?"* would be correct. |
| **Retrieval-based fact verification** — extract claims, retrieve evidence, judge entailment | Rejected. Genuinely addresses truth, but is a different task and a thesis of its own. The brief asks for fine-tuning a classifier. |
| **Credibility assessment, stated honestly** | **Chosen.** |

The model, pipeline and interface are identical under the naive framing and this one. The difference
is the vocabulary used throughout, plus one chapter of analysis. It also satisfies the brief's
task 3, which makes dataset selection and its justification a graded deliverable.

## Consequences

**The framing must survive contact with the interface, not just the prose.**

- A Credibility Score is never shown bare.
- A **Verdict Band** governs how strongly a result may be phrased.
- Caveats are inline, not relegated to an About page.
- `CredibilityScore` owns the threshold → band mapping in the domain layer, so the framing is
  enforced in code rather than in a paragraph someone can forget.

**It also changes what counts as a good result.** A near-perfect benchmark score becomes evidence of
**Register Leakage**, not of success. Hence the saturated ISOT result is retained as a **Contrast
Experiment**, and the primary evaluation uses a **Source-Disjoint Split**.

The ISOT figure is F1 ≈ 0.99 from TF-IDF + logistic regression, measured **after** Publisher
De-identification removed datelines, wire attributions and image credits. Leakage surviving that
removal is the point: stripping the obvious tells does not fix the benchmark, and only partitioning
on Publisher does.
