# Research 0006 — Transformer candidates and the >512-token problem

Resolves the research question in [issue #6](https://github.com/aoleszkiewicz/factlens/issues/6).
Date: 2026-08-10. Author: research agent.

**This note does not make the call.** It ranks options and states the VRAM/latency
consequences of each. The decision belongs to #9 (stack) and #11 (long-document strategy).

Target hardware: Radeon RX 9060 XT 16 GB (RDNA4, `gfx1200`), Arch Linux + ROCm, Colab fallback.
Task: English document-level credibility classification, binary, with Integrated Gradients
token attribution and temperature scaling.

---

## 1. Ranked recommendation

| # | Option | Why | Cost |
|---|---|---|---|
| **1** | **ModernBERT-base @ 1024–2048 tokens**, head truncation | Best NLU quality per parameter at BASE size (GLUE 88.4, beats DeBERTaV3-base 88.1 and RoBERTa-base 86.4); native 8192 context so *no* chunking machinery is needed; most memory-efficient encoder measured (max batch 1604 @512, 98 @8192 on a 24 GB RTX 4090); IG stays a single contiguous attribution over the whole article | 149 M params; ~2.7 GB optimizer+weights in mixed precision; **flag:** peak throughput depends on FlashAttention 2/3 + `torch.compile`, both CUDA-first — expect the SDPA fallback on ROCm |
| **2** | **RoBERTa-base @ 512, head+tail truncation** | The safest, most defensible thesis baseline; the strategy with the most direct evidence (Sun et al. head+tail is best of six strategies on IMDb *and* on a news corpus); fastest short-context encoder after BERT (179.9k tok/s @512); IG over 512 tokens is trivial and cheap | 125 M params; ~2.3 GB states; loses 27 % of ISOT tokens and truncates 44 % of articles |
| **3** | **ModernBERT-base @ 8192** (whole article, no truncation at all) | Covers 99.98 % of ISOT articles end to end; removes the truncation caveat from the thesis entirely | Long-context throughput drops to ~123.7k tok/s (fixed) from 148.1k @512; max batch 98 vs 1604 — i.e. ~16× smaller batches. IG cost scales with `n_steps × seq_len`, so a 8192-token IG pass is ~16× a 512-token one |
| **4** | **DeBERTa-v3-base @ 512, head+tail** | Strongest *classical* 512-token encoder (GLUE 88.1); the standard "serious baseline" in 2023-era papers | Disentangled attention is expensive: 183 M params, **70.2k tok/s vs RoBERTa's 179.9k (2.6× slower)** and max batch 236 vs 664. Costs the most per point of quality on a 16 GB card |
| **5** | **Chunking + aggregation (mean/max/attention over chunk logits)** | Only strategy that uses 100 % of the text with a 512-token backbone | Evidence is *against* it: hierarchical/ToBERT variants lost to plain truncation on 4 of 6 datasets and on the news dataset specifically (89.54 vs 92.00); 1.7× inference time; and it fractures IG into per-chunk attributions that are not comparable across chunks (see §5) |
| **6** | **Longformer-base @ 4096** | The one option with a *positive* result on a news corpus: best model on Hyperpartisan in an independent reproduction (95.69 vs BERT-512 92.00), and 94.8 vs RoBERTa 87.4 in its own paper | **~12× training and ~12× inference time vs BERT-512, and 32 GB GPU memory in the only measurement we have — over the 16 GB budget.** Superseded by ModernBERT on both quality and efficiency |
| **7** | **BigBird** | Same family as Longformer, no advantage found for classification | Same costs, less evidence for news classification; no controlled classification result located |
| **8** | **ELECTRA-base** | Efficient pretraining, BERT-base-sized | No verified head-to-head advantage over RoBERTa/DeBERTa-v3 on document classification in any primary source read here; 512-token cap. No reason to prefer it |

**LoRA/PEFT: not needed.** Full fine-tuning of any *base*-size encoder fits 16 GB with room to
spare (§6). LoRA only becomes interesting if a `large` model at long context is attempted.

**Suggested experimental spine for #11:** one 512-token head+tail baseline (option 2 or 4) as the
thesis's control, one ModernBERT run at extended length (option 1) as the treatment, and report the
delta. That is a clean, cheap ablation that directly answers "does truncation cost us anything on
this corpus" — which no cited paper can answer for *our* corpus.

---

## 2. Candidate encoders — measured numbers

All figures below are from Warner et al. 2024 (ModernBERT), Tables 1 and 2, which is the only
source read here that benchmarks all the short-context candidates under one protocol.
Efficiency was measured on **a single NVIDIA RTX 4090** — a 24 GB consumer card, so the numbers
transfer in *shape* to a 16 GB consumer card, but not in absolute value.

**Quality (Table 1, GLUE average — higher is better):**

| Model | Params | GLUE avg | Max context |
|---|---|---|---|
| BERT-base | 110 M | 84.7 | 512 |
| RoBERTa-base | 125 M | 86.4 | 512 |
| DeBERTaV3-base | 183 M | 88.1 | 512 |
| NomicBERT | 137 M | 84.0 | 8192 |
| GTE-en-MLM-base | 137 M | 85.6 | 8192 |
| **ModernBERT-base** | **149 M** | **88.4** | **8192** |
| RoBERTa-large | 355 M | 88.9 | 512 |
| DeBERTaV3-large | 434 M | **91.4** | 512 |
| ModernBERT-large | 395 M | 90.4 | 8192 |

The paper's own framing: *"ModernBERT-base surpasses all existing base models, including
DeBERTaV3-base, becoming the first MLM-trained model to do so."* DeBERTaV3-large remains the GLUE
champion at LARGE size.

**Efficiency (Table 2 — thousands of tokens/sec, and BS = max batch size, RTX 4090, 10-run average):**

| Model | Params | Short BS | Short fixed | Short variable | Long BS | Long fixed | Long variable |
|---|---|---|---|---|---|---|---|
| BERT-base | 110 M | 1096 | 180.4 | 90.2 | – | – | – |
| RoBERTa-base | 125 M | 664 | 179.9 | 89.9 | – | – | – |
| DeBERTaV3-base | 183 M | 236 | **70.2** | **35.1** | – | – | – |
| GTE-en-MLM-base | 137 M | 640 | 123.7 | 61.8 | 38 | 46.8 | 23.4 |
| **ModernBERT-base** | 149 M | **1604** | 148.1 | **147.3** | **98** | **123.7** | **133.8** |
| RoBERTa-large | 355 M | 460 | 42.0 | 21.0 | – | – | – |
| DeBERTaV3-large | 434 M | 134 | 24.6 | 12.3 | – | – | – |
| ModernBERT-large | 395 M | 770 | 52.3 | 52.9 | 48 | 46.8 | 49.8 |

"Short" = documents of 512 tokens, "long" = 8192; "variable" = normally-distributed lengths
(realistic), where ModernBERT's unpadding gives it a large edge — 147.3 vs RoBERTa's 89.9.
News articles are variable-length, so the *variable* column is the one that matters for us.

Two practical readings:

- **DeBERTa-v3-base is the expensive option.** 2.6× slower than RoBERTa-base at 512 tokens and
  under half the batch size, for +1.7 GLUE. On a 16 GB card that is the worst trade in the table.
- **ModernBERT-base is Pareto-dominant among base models** *provided* its kernels are available.

Architecture notes (Warner et al. §2.1.2): every third layer uses global attention (RoPE theta
160 000), the rest use a **128-token local sliding window** (theta 10 000). Consequence for us:
`classifier_pooling` defaults to `"cls"`, and the HF config documents that *"in local attention
layers, the CLS token doesn't attend to all tokens on long sequences"* — so at long context,
`classifier_pooling="mean"` deserves an ablation in #11.

**Long-context specialists.**
Longformer (Beltagy et al. 2020) combines local windowed attention with task-motivated global
attention, scales linearly, and is pretrained to 4096 tokens. BigBird (Zaheer et al. 2020) uses a
sparse pattern with O(1) global tokens (e.g. CLS), handles "up to 8x" the length of BERT on similar
hardware, and is a universal approximator/Turing complete. Both predate ModernBERT and neither is
competitive with it on the efficiency table above.

---

## 3. How much data is actually truncated at 512?

### 3.1 Measured on this repo's corpus (ISOT, `data/raw/`)

Computed for this ticket by tokenizing `title + ". " + text` for all 44 898 ISOT articles with
each model's own tokenizer, no truncation. Script: `scripts/` was not used — the one-off lives in
the ticket's scratch; the numbers are reproducible from `data/raw/{Fake,True}.csv`.

| Tokenizer | mean | median | p90 | p95 | p99 | max | **% > 512** | % > 1024 | % > 4096 | % > 8192 |
|---|---|---|---|---|---|---|---|---|---|---|
| roberta-base | 536.1 | 475 | 972 | 1177 | 1927 | 12 841 | **43.7 %** | 8.5 % | 0.21 % | 0.03 % |
| deberta-v3-base | 507.9 | 452 | 920 | 1113 | 1824 | 13 502 | **39.1 %** | 6.9 % | 0.17 % | 0.03 % |
| modernbert-base | 544.0 | 484 | 980 | 1186 | 1948 | 11 523 | **44.9 %** | 8.7 % | 0.21 % | 0.02 % |

Fraction of the corpus's *total tokens* retained by head truncation (roberta-base):

| Limit | Tokens kept | Articles fully covered |
|---|---|---|
| 512 | **72.6 %** | 56.3 % |
| 1024 | 92.5 % | 91.5 % |
| 4096 | 99.3 % | 99.8 % |
| 8192 | 99.9 % | 99.97 % |

Chunking at 512 would produce **1.57 chunks per article on average**, 4 at p99 — i.e. the
per-article inference cost of chunking is only ~1.6× the truncated cost, but the aggregation
machinery has to exist for all articles.

Three conclusions:

1. **The problem is real but modest.** ~44 % of articles are truncated at 512, and roughly a
   quarter of all text is discarded. This is enough to be worth a paragraph in the thesis and an
   ablation, not enough to justify a 12×-cost architecture on its own.
2. **1024 tokens buys most of the benefit.** Going 512 → 1024 raises token retention from 72.6 %
   to 92.5 % and fully covers 91.5 % of articles. Going 1024 → 8192 buys the last 7 %.
   The distribution has a long thin tail, not a fat one.
3. **4096 is effectively "the whole corpus"** (99.3 % of tokens). Above that there is nothing left
   to win, which argues against paying for 8192 at training time.

Caveat: ISOT is retained as a *contrast* experiment (see #2, #8), not the primary corpus. The
distribution should be recomputed on whatever #8 selects. The shape — median ~450–500, long thin
right tail — is typical of newswire and unlikely to move much.

### 3.2 Published news-corpus statistics

Park et al. 2022, Table 1, on **Hyperpartisan news detection** (SemEval-2019 Task 4):
**744.2 ± 677.9 BERT tokens on average, 53.5 % of documents over 512.** Very close to what we
measure on ISOT (mean 536, 44 % over 512), with a wider spread.

Sun et al. 2019, Table 1: IMDb averages 292 tokens with a 12.69 % exceeding ratio; **Sogou News
averages 737 tokens with a 46.23 % exceeding ratio** — again the news genre lands near 45–50 %.

So "roughly half of news articles exceed 512 tokens" is a well-supported statement across three
independent corpora.

---

## 4. Long-document strategies — what the evidence says

### 4.1 Truncation variants (Sun et al. 2019, "How to Fine-Tune BERT for Text Classification?", Table 2)

Test **error rates** (%), BERT-base:

| Method | IMDb | Sogou News |
|---|---|---|
| head-only (first 510) | 5.63 | 2.58 |
| tail-only (last 510) | 5.44 | 3.17 |
| **head+tail (first 128 + last 382)** | **5.42** | **2.43** |
| hierarchical, mean pooling | 5.89 | 2.83 |
| hierarchical, max pooling | 5.71 | 2.47 |
| hierarchical, self-attention | 5.49 | 2.65 |

Findings that matter:

- **head+tail wins on both datasets**, including the news one, and the authors adopt it for all
  subsequent experiments.
- **All three hierarchical (chunk + pool) variants lose to head+tail** on both datasets. Mean
  pooling is the *worst* of the six methods on IMDb.
- **The spread is tiny** — 5.42 to 5.89 on IMDb is 0.47 pp across every strategy tested. Compare
  with the same paper's within-task further pretraining, which moves IMDb error from 5.42 to
  ~4.4 (Figure 3). Continued MLM pretraining on in-domain text is worth roughly 2× what the
  entire truncation-strategy question is worth. That is a load-bearing finding for #11 and #9.

### 4.2 Long-context models vs truncation (Park et al. 2022, ACL, Tables 2 and 3)

Accuracy / micro-F1, average of 5 seeds:

| Model | Hyperpartisan (news) | 20NewsGroups | EURLEX | Inverted EURLEX | Book Summary | Paired Summary |
|---|---|---|---|---|---|---|
| BERT (truncate @512) | 92.00 | 84.79 | 73.09 | 70.53 | 58.18 | 52.24 |
| BERT+TextRank | 91.15 | 84.99 | 72.87 | 71.30 | 58.94 | 55.99 |
| BERT+Random | 89.23 | 84.65 | **73.22** | **71.47** | **59.36** | 56.58 |
| **Longformer (4096)** | **95.69** | 83.39 | 54.53 | 56.47 | 56.53 | **57.76** |
| ToBERT (chunk + transformer) | 89.54 | **85.52** | 67.57 | 67.31 | 58.16 | 57.08 |
| CogLTX (key sentences) | 94.77 | 84.63 | 70.13 | 70.80 | 58.27 | 55.91 |

Cost, relative to BERT-512 (Table 3, Hyperpartisan, seconds/epoch):

| Model | Train time | Inference time | GPU memory |
|---|---|---|---|
| BERT | 1.00 | 1.00 | **< 16 GB** |
| +TextRank | 1.96 | 1.96 | 16 GB |
| +Random | 1.98 | 2.00 | 16 GB |
| **Longformer** | **12.05** | **11.92** | **32 GB** |
| ToBERT | 1.19 | 1.70 | **32 GB** |
| CogLTX | 104.52 | 12.53 | < 16 GB |

The paper's headline conclusion is that *"more sophisticated models are often outperformed by
simpler models (often including a BERT baseline) and yield inconsistent performance across
datasets."*

But read the news column honestly — this is the nuance that matters for FactLens:

- **On the one news dataset, Longformer really does win**, by +3.7 points over truncated BERT, and
  CogLTX is second. This is consistent with Beltagy et al.'s own Table 7 (Hyperpartisan F1:
  RoBERTa-base 87.4 → Longformer-base 94.8; IMDB 95.3 → 95.7). Two independent runs agreeing is
  meaningful evidence that **news classification is one of the genres where reading past 512
  tokens helps**. Hyperpartisan is a very small dataset (variance is high), so don't overweight it.
- **Chunk-and-aggregate (ToBERT) is the worst option on that same news dataset** — 89.54, *below*
  plain truncation — while still needing 32 GB. Chunking is not the safe middle ground it looks
  like. This matches Sun et al.'s hierarchical results.
- **Longformer's 32 GB and 12× cost do not fit the RX 9060 XT.** The Longformer/ToBERT runs in
  that paper were done on an A100-40GB while the baselines ran on a V100-16GB, precisely because
  of this. ModernBERT is the modern way to buy Longformer's benefit without Longformer's bill.

### 4.3 Synthesis

The evidence supports, in order:
**native long context (if cheap) > head+tail truncation ≈ head truncation > chunk-and-pool.**

Chunking is the option that combines the weakest empirical support, extra memory, extra latency,
*and* the explainability problem in §5. That is an unusual clean sweep against an option.

---

## 5. Interaction with Integrated Gradients

How IG is done here (Captum's own BERT tutorial is the reference implementation):

```python
lig = LayerIntegratedGradients(forward_func, model.bert.embeddings)
ref_input_ids = [cls_token_id] + [ref_token_id] * len(text_ids) + [sep_token_id]  # ref_token_id = PAD
attributions = attributions.sum(dim=-1).squeeze(0)
attributions = attributions / torch.norm(attributions)
```

`LayerIntegratedGradients` *"approximates the integral of gradients of the model's output with
respect to the inputs along the path (straight line) from given baselines / references to inputs"*;
`n_steps` defaults to 50, and cost scales linearly with it (each step is a forward + backward).
`internal_batch_size` chunks those steps to bound memory.

**Cost model.** One explanation ≈ `n_steps` (default 50) forward+backward passes over the input.
At 512 tokens that is cheap. At 8192 tokens it is ~16× the tokens *and* attention cost grows
superlinearly for dense-attention models — this is the single biggest latency item in the user-facing
request path, and it is the reason a serving-side sequence cap exists at all. Mitigations that
don't change the model: lower `n_steps` (20–32 is commonly adequate for a UI heatmap), set
`internal_batch_size`, and run attribution only when the user asks for it.

**Per strategy:**

- **Head / head+tail truncation.** IG is clean: one baseline, one forward function, one contiguous
  attribution vector, completeness holds for the actual scored input. The honest UI consequence is
  that the explanation covers *only the scored span*. head+tail is slightly worse for the UI than
  head-only, because the highlighted regions are two disjoint spans with an unexplained gap in the
  middle, which needs explicit visual treatment ("… middle of article not scored …").
- **Native long context (ModernBERT @ N).** Best explainability story by a distance: **one model
  call, one baseline, one attribution vector covering the whole article**, and completeness
  (attributions sum to `F(x) − F(baseline)`) holds for the document the user actually pasted.
  No stitching, no renormalisation, nothing to justify in the thesis.
- **Chunking + aggregation.** This is where it hurts, and it deserves to be stated plainly for #11:
  1. **Attributions are per-chunk and not comparable across chunks.** Each chunk has its own
     baseline and its own `F(x_i) − F(baseline_i)`. Normalising each chunk by its own norm (as the
     Captum tutorial does) destroys cross-chunk comparability outright; not normalising leaves
     chunks on different scales.
  2. **The aggregation layer must itself be differentiated through.** Mean pooling over chunk
     logits is linear and *can* be handled — chunk attributions can be scaled by 1/k and
     concatenated, and completeness survives. **Max pooling cannot**: the document score comes from
     one chunk, so IG legitimately attributes zero to every other chunk and the user sees an
     article with one highlighted paragraph and the rest blank. **Attention pooling** is
     differentiable but means the explanation is a product of two attributions (token→chunk-logit
     and chunk→document), which is no longer a single IG run with a completeness guarantee.
  3. **Cost multiplies.** IG per chunk × 1.57 chunks/article (measured, §3.1) × `n_steps`.
  4. **Boundary artefacts.** A token near a chunk seam has a truncated context, so its attribution
     depends on where the chunker happened to cut — an explanation instability that is hard to
     defend in a thesis about *explainable* screening.
  If chunking is nevertheless chosen in #11, **mean pooling is the only aggregation that keeps a
  coherent single explanation**, and that constraint should be recorded as a decision driver, not
  discovered later. Note this is also the aggregation Sun et al. measured as the *worst* performer.

**Calibration interaction.** Temperature scaling is a monotone rescaling of the logit and does not
change the ranking of IG attributions. But under chunking the temperature must be fitted on the
*aggregated document logit*, not on chunk logits, or the reliability diagram describes a quantity
the user is never shown. Another reason chunking costs more than it looks.

---

## 6. VRAM budget on 16 GB, and whether LoRA is needed

Per-parameter training cost in mixed precision (HF "Model training anatomy"): 6 bytes/param for
weights (fp16 + fp32 master copy) + 8 bytes/param Adam states + 4 bytes/param fp32 gradients =
**18 bytes/param**, plus activations that scale with batch × seq_len × depth × hidden.

Static cost (weights + gradients + Adam), *excluding* activations — arithmetic from the above:

| Model | Params | 18 B/param |
|---|---|---|
| RoBERTa-base | 125 M | ~2.3 GB |
| ModernBERT-base | 149 M | ~2.7 GB |
| Longformer-base | 149 M | ~2.7 GB |
| DeBERTaV3-base | 183 M | ~3.3 GB |
| RoBERTa-large | 355 M | ~6.4 GB |
| ModernBERT-large | 395 M | ~7.1 GB |
| DeBERTaV3-large | 434 M | ~7.8 GB |

So **every base model leaves 12+ GB for activations, and even the large models leave 8+ GB**.
The binding constraint is activations (batch × sequence length), not parameters — which is exactly
what Park et al. observed empirically: BERT-512 fit under 16 GB, Longformer-4096 and ToBERT needed
32 GB.

**Verdict on LoRA/PEFT: not justified for a base-size encoder here.** LoRA's claims are about
scale — *"reduce the number of trainable parameters by 10,000 times and the GPU memory requirement
by 3 times"* relative to GPT-3 175B with Adam, while performing *"on-par or better than fine-tuning
… on RoBERTa, DeBERTa, GPT-2, and GPT-3"* with *"no additional inference latency"*. A 3× saving on
a 2.7 GB static footprint saves ~1.8 GB out of 16 GB — irrelevant. Full fine-tuning is also the
stronger thesis claim (task 4 says "fine-tune a pre-trained transformer"; full fine-tuning is the
least-caveated reading of that).

LoRA becomes worth reconsidering only if #11 lands on **a large model at long context** (e.g.
ModernBERT-large @ 4096+), where activations dominate. Cheaper levers to reach for first, in order:
gradient accumulation, gradient checkpointing, then reduced sequence length, then LoRA.

Practical knobs if OOM appears: `per_device_train_batch_size` down + `gradient_accumulation_steps`
up (identical effective batch), `gradient_checkpointing=True` (trades compute for activation
memory), bf16 autocast.

---

## 7. CUDA-only / ROCm risk flags

Ticket #3 owns ROCm viability; these are only the model-choice-relevant flags.

- **ROCm officially supports `gfx1200` (RX 9060 XT)** as of ROCm 7.0.2 / 7.2 — the card is in AMD's
  compatibility matrix. **Arch Linux is not** in AMD's supported-OS list (only Ubuntu 24.04/22.04
  and RHEL 9/10 for RDNA4 devices). That is a #3 problem, but it makes Colab a realistic fallback,
  and Colab is CUDA — so *don't pick a model that only works on one of the two backends*.
- **ModernBERT's efficiency numbers assume FlashAttention 2/3 + `torch.compile`** (Warner et al.
  §2.1.2: FA3 for global layers, FA2 for local; torch.compile gives "a 10 percent improvement in
  throughput"). Both are NVIDIA-first. Current HF docs state ModernBERT *"no longer defaults to
  FlashAttention2"* and demonstrate `attn_implementation="sdpa"`, so **ModernBERT is functionally
  fine on ROCm via SDPA** — but expect to lose the unpadding advantage (padding-free training
  "requires `flash_attention_2`") and some of the throughput lead in the "variable" column.
  This is a *performance* risk, not a *correctness* risk. It should be measured in #3, not assumed.
- **Longformer/BigBird** use custom sliding-window/sparse kernels (Longformer's TVM kernel path in
  particular) that are least likely to be well-supported on ROCm. Another mark against them.
- **RoBERTa / DeBERTa-v3 / ELECTRA** are plain dense-attention models with no custom kernels —
  the lowest-risk choices on non-CUDA hardware. This is a genuine argument for option 2 over
  option 1 that the quality table alone does not show.
- **bitsandbytes** (8-bit Adam, QLoRA) has partial/forked ROCm support. Since §6 concludes PEFT
  isn't needed, this dependency can simply be avoided — which is itself a reason not to build the
  plan around LoRA.

---

## 8. Open questions handed to #9 and #11

1. Recompute §3.1's length distribution on the corpus #8 actually selects; the 44 %/72.6 % figures
   are ISOT-specific.
2. Decide the serving-side sequence cap. It sets the IG latency budget, and the IG pass — not the
   classification pass — is the dominant cost.
3. If ModernBERT @ long context is chosen, ablate `classifier_pooling="cls"` vs `"mean"` — the CLS
   token does not attend globally in local-attention layers.
4. Sun et al.'s within-task further MLM pretraining (5.42 → ~4.4 error) outweighs the entire
   truncation-strategy question. Decide explicitly whether domain-adaptive pretraining is in or out
   of scope for the thesis; it is currently in neither the map nor any ticket.
5. Whether the truncated middle of an article is disclosed in the UI (§5) — this is the
   "long-document handling in the UI" item already listed as unspecified in #2.

---

## 9. Sources

Primary, read directly (papers read as PDF, not summaries):

- Warner et al. 2024, *Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder…*
  (ModernBERT). arXiv:2412.13663 — Tables 1 and 2, §2.1.2, §2.2, §4.
- Park, Vyas, Shah 2022, *Efficient Classification of Long Documents Using Transformers*,
  ACL 2022 (short). arXiv:2203.11258 — Tables 1, 2, 3; §3, §4, Appendix A.
- Sun et al. 2019, *How to Fine-Tune BERT for Text Classification?* arXiv:1905.05583 —
  Tables 1, 2, 3; Figure 3.
- Beltagy, Peters, Cohan 2020, *Longformer: The Long-Document Transformer*. arXiv:2004.05150 —
  abstract + text-classification results (IMDB 95.7 vs RoBERTa 95.3; Hyperpartisan 94.8 vs 87.4).
- Zaheer et al. 2020, *Big Bird: Transformers for Longer Sequences*. arXiv:2007.14062 — abstract.
- Clark et al. 2020, *ELECTRA*. arXiv:2003.10555 — abstract.
- Hu et al. 2021, *LoRA: Low-Rank Adaptation of Large Language Models*. arXiv:2106.09685 — abstract.
- Captum, `LayerIntegratedGradients` API reference — https://captum.ai/api/layer.html
- Captum, *Interpreting BERT Models* tutorial — https://captum.ai/tutorials/Bert_SQUAD_Interpret
- HuggingFace Transformers, ModernBERT model doc —
  https://huggingface.co/docs/transformers/en/model_doc/modernbert
- HuggingFace Transformers, *Model training anatomy* —
  https://huggingface.co/docs/transformers/en/model_memory_anatomy
- AMD ROCm, *System requirements (Linux)* —
  https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html

Measured for this ticket: §3.1, computed over `data/raw/Fake.csv` + `data/raw/True.csv`
(44 898 articles) with the `roberta-base`, `microsoft/deberta-v3-base` and
`answerdotai/ModernBERT-base` tokenizers, no truncation.

Explicitly *not* verified here: ELECTRA's GLUE/SQuAD numbers (abstract only — no head-to-head
against RoBERTa/DeBERTa-v3 on document classification was located), and BigBird's classification
results (no controlled comparison found). Both are ranked low partly for that absence of evidence.
