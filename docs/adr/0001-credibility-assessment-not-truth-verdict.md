# FactLens assesses credibility; it does not adjudicate truth

The thesis title names *dezinformacja* — false information spread with intent to deceive — but no supervised classifier over article text can infer intent, and no available corpus label encodes it. Every candidate corpus offers a proxy instead: publisher provenance, a fact-checker's verdict on a single claim, or a crowd credibility rating. We therefore define the system's output as a **calibrated Credibility Score** over **Unreliable Content**, presented as a **Screening Aid**, and we name and measure the **Label Gap** explicitly in the dataset chapter rather than papering over it.

## Considered options

**Claim the label is disinformation.** Simplest, and matches the title literally. Rejected: it is not defensible under questioning, and the first examiner to ask "so a fabricated story written in wire-service style is *Real*?" would be correct.

**Retrieval-based fact verification** (extract claims, retrieve evidence, judge entailment). This genuinely addresses truth, but it is a different task and a thesis of its own; the brief asks for fine-tuning a classifier.

**Credibility assessment, stated honestly.** Chosen. The model, pipeline and interface are identical to the naive framing — the difference is the vocabulary used throughout and one chapter of analysis. It satisfies the brief's task 3, which makes dataset selection and its justification a graded deliverable in its own right.

## Consequences

The distinction has to survive contact with the interface, not just the prose: a Credibility Score is never shown bare, a **Verdict Band** governs how strongly a result may be phrased, and caveats are inline rather than relegated to an About page. `CredibilityScore` owns the threshold→band mapping in the domain layer, so the framing is enforced in code rather than in a paragraph someone can forget.

It also changes what counts as a good result. Under this framing a near-perfect benchmark score is evidence of **Register Leakage**, not of success — which is why the saturated ISOT result (F1 ≈ 0.99 from TF-IDF + logistic regression) is retained as a **Contrast Experiment** and the primary evaluation uses a **Source-Disjoint Split**.
