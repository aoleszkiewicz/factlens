# ROCm viability for RDNA4 (gfx1200) fine-tuning on Arch Linux

Research for issue [#3](https://github.com/aoleszkiewicz/factlens/issues/3). Investigated 2026-08-10.
This field moves fast — every claim below is dated and sourced; re-check anything older than a few months
before acting on it.

> Placement note: the repo had no research-notes convention (only `docs/agents/` and the `docs/adr/` referenced
> by the map). Findings go in `docs/research/`, numbered like ADRs. This is a *findings* document, not a
> decision record — if the recommendation is accepted it should be restated as an ADR.

## Recommendation

**Train locally on ROCm.** The RX 9060 XT (gfx1200) is a first-class supported ROCm target as of
ROCm 6.4.1 (May 2025) and is explicitly listed in the current ROCm 7.14 support matrix; Arch `extra`
ships a coherent ROCm 7.2.4 stack *and* a `python-pytorch-rocm` built with gfx1200 kernels; and the
upstream pytorch.org ROCm wheels also compile gfx1200/gfx1201 kernels. **No `HSA_OVERRIDE_GFX_VERSION`
and no source build are required.** A `base`-size encoder at seq 512 / batch 16 fits in 16 GB with
several GB to spare.

Keep Colab as a *contingency*, not the primary plan: use it only if local training hits one of the
known RDNA4 instabilities (below) that blocks progress for more than a day.

### The recipe

Two viable routes. Prefer route A (fewer moving parts on Arch); fall back to B if the Arch package lags.

**Route A — Arch `extra` packages (system Python, no venv wheels):**

```bash
sudo pacman -S rocm-hip-sdk rocminfo rocm-smi-lib python-pytorch-rocm
sudo usermod -a -G video,render "$LOGNAME"   # log out/in afterwards
rocminfo | grep -i 'Marketing Name'          # expect: AMD Radeon RX 9060 XT
python -c "import torch; p=torch.cuda.get_device_properties(0); print(torch.__version__, p.gcnArchName, p.total_memory//1024**2, 'MB')"
```

Expect `gfx1200` and **~16000 MB** (not ~7900 — see the VRAM-cap bug below; if you see 8 GB, stop and update).

**Route B — upstream wheels in a venv (does not need system ROCm at all; the wheels bundle it):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.2
```

Do **not** mix route A and route B in the same environment (system ROCm headers/libs + wheel-bundled ROCm
is a documented source of breakage — ROCm issue #6506, comment from AMD: *"in general we don't recommend
mixing system installs with venv installs"*).

**Env vars — only these, and only if needed:**

| Variable | Why |
|---|---|
| *(none required)* | gfx1200 is natively compiled. **Do not set `HSA_OVERRIDE_GFX_VERSION`** — it would misidentify the card. |
| `PYTORCH_HIP_ALLOC_CONF=expandable_segments:True` | reduces allocator fragmentation on long training runs |
| `TORCH_BLAS_PREFER_HIPBLASLT=1` | hipBLASLt has gfx1200 Tensile kernels on Arch; reported as the more stable path by RDNA4 users |
| `MIOPEN_FIND_MODE=FAST` | shortens MIOpen kernel autotuning on first run |

**Training config for `transformers` + `accelerate`:** `bf16=True`, `attn_implementation="sdpa"`.
Do **not** install the `flash-attn` package and do **not** use `attn_implementation="flash_attention_2"`.

## Findings

### 1. ROCm support for gfx1200/gfx1201

- **First support: ROCm 6.4.1** (May 2025) — "introduces support for the RDNA4 architecture-based
  Radeon AI PRO R9700, Radeon RX 9070, RX 9070 XT, RX 9070 GRE, and **Radeon RX 9060 XT**".
  ([ROCm 6.4.1 release notes](https://rocm.docs.amd.com/en/docs-6.4.1/about/release-notes.html))
- **Current: ROCm 7.14.0**, released 2026-07-15, explicitly lists RX 9060 XT / RX 9060 as **gfx1200** and
  the RX 9070 family / AI PRO R9700 as **gfx1201**.
  ([release notes](https://rocm.docs.amd.com/en/latest/about/release-notes.html),
  [system requirements](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html))
- **Two parallel version streams — do not confuse them.** AMD now ships (a) the classic distro packages,
  currently **7.2.4** (this is what Arch mirrors and what pytorch.org builds against), and (b) the new
  modular "TheRock" Core SDK, currently **7.14.0**, distributed as Python wheels from
  `https://repo.amd.com/rocm/whl-multi-arch/`. The 7.14 docs are the ones with the fullest RDNA4 story.
- **Arch is not an officially supported distro.** AMD's support matrix lists only Ubuntu 24.04.4 / 22.04.5 /
  RHEL 10.1 / RHEL 9.7 for the Radeon consumer cards. In practice Arch packages the same sources; this is a
  *support-policy* gap, not a technical one, but it means AMD will not take a bug report from Arch.
- **Data types:** AMD's precision matrix lists RDNA4 as supporting **fp16 and bf16 in matrix cores**,
  fp32/fp64 in compute units, and **no tf32**.
  ([precision support](https://rocm.docs.amd.com/en/latest/compatibility/precision-support.html))
  → `bf16` mixed precision is the right choice; there is no tf32 fast path to lose.

### 2. What Arch `extra` ships (verified 2026-08-10)

| Package | Version |
|---|---|
| `rocm-hip-sdk`, `rocm-hip-runtime`, `rocm-ml-libraries`, `rocminfo`, `hipblas`, `rocfft`, `rccl` | 7.2.4 |
| `rocblas` | 7.2.4-2 |
| `hipblaslt` | (built 2026-06-02) |
| `python-pytorch-rocm` | **2.13.0-4** (built 2026-07-14, 1.5 GB installed) |

([Arch package search](https://archlinux.org/packages/?q=rocm),
[python-pytorch-rocm](https://archlinux.org/packages/extra/x86_64/python-pytorch-rocm/))

**gfx1200 kernels are actually present** — verified by inspecting package file lists rather than trusting docs:

- `rocblas` package contains **20 files** matching `gfx1200` (and 56 matching `gfx1201`) — Tensile libraries.
- `hipblaslt` contains **287 files** matching `gfx1200`, **297** matching `gfx1201`.

**The Arch PyTorch build targets gfx1200.** `PKGBUILD` line 323 sets
`export PYTORCH_ROCM_ARCH="$(rocm-supported-gfx -e gfx950)"`, and `rocm-supported-gfx`
(from the `rocm-toolchain` package, [source](https://gitlab.archlinux.org/tpkessler/rocm-toolchain))
enumerates a list that includes **`gfx1200`** and **`gfx1201`**. So Arch's `python-pytorch-rocm` has native
gfx1200 code objects.

### 3. Upstream PyTorch ROCm wheels

- `https://download.pytorch.org/whl/` currently exposes ROCm indexes up to **`rocm7.2`**, containing
  **torch 2.13.0+rocm7.2** (also 2.12.x).
- The manywheel builder for the 2.13 release sets
  `PYTORCH_ROCM_ARCH="gfx900;gfx906;gfx908;gfx90a;gfx942;gfx1030;gfx1100;gfx1101;gfx1102;gfx1103;gfx1200;gfx1201;gfx950;gfx1150;gfx1151"`
  ([`.ci/docker/manywheel/build.sh` line 98, release/2.13](https://github.com/pytorch/pytorch/blob/release/2.13/.ci/docker/manywheel/build.sh)).
  → **the official wheels contain gfx1200 kernels.** No override, no source build.
- AMD additionally publishes device-specific wheels: `torch[device-gfx1200]==2.12.0+rocm7.14.0` from
  `https://repo.amd.com/rocm/whl-multi-arch/`
  ([AMD PyTorch install docs](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html)).
  Only worth using if you specifically need ROCm 7.14 features.

Note the CI *test* images build only `gfx90a;gfx942;gfx950;gfx1100` — i.e. **gfx1200 is compiled but not
CI-tested upstream**. That is exactly why the bugs in section 5 exist.

### 4. transformers + accelerate

- **bf16 mixed precision:** supported by the hardware (matrix-core bf16, see §1) and is the standard
  ROCm path. Prefer `bf16` over `fp16` — no loss-scaling fragility, and RDNA4 has native bf16 matrix ops.
- **Attention: use SDPA.** Transformers defaults to SDPA on torch ≥ 2.1.1 and it works on ROCm. On gfx12
  PyTorch routes SDPA's flash backend through **AOTriton**; `strings libaotriton_v2.so` on the shipped
  wheels confirms gfx1201 code objects exist (pytorch#188113).
- **Do not use `flash_attention_2`.** Hugging Face's own docs state: *"FlashAttention2 support is currently
  limited to Instinct MI210, Instinct MI250 and Instinct MI300"*
  ([HF GPU inference docs](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one)).
  One user *did* build Dao-AILab flash-attention's CK backend for gfx1200 successfully
  ([ROCm#6506](https://github.com/ROCm/ROCm/issues/6506), 2026-07-23) — ~1837 compilation units,
  `MAX_JOBS` auto-set to 1, multiple missing-header detours. Not worth it for a 512-token encoder.
- **CK SDPA backend is broken on RDNA4** ([pytorch#188113](https://github.com/pytorch/pytorch/issues/188113),
  open, 2026-06-24): the `kentry_pt` launch guard asserts *"Attempting to call a CK SDPA kernel on
  unsupported hardware"* on gfx1200/gfx1201, and the codegen only emits XDL (gfx9) instances, not the WMMA
  ones RDNA4 needs. Fix PR [#188114](https://github.com/pytorch/pytorch/pull/188114) is open, not merged.
  **Consequence: never call `torch.backends.cuda.preferred_rocm_fa_library("ck")`.** The default
  (AOTriton) path is the supported one and needs no action.

### 5. Known breakages to watch for

| Symptom | Status | Action |
|---|---|---|
| **`total_memory` reports ~7915 MB instead of 16 GB on RX 9060 XT; segfault (not OOM) past the cap.** Card also misnamed "AMD Radeon Graphics". ([pytorch#184880](https://github.com/pytorch/pytorch/issues/184880), 2026-05-22, **still open**; duplicate [ROCm#6295](https://github.com/ROCm/ROCm/issues/6295), **closed 2026-06-08**) | Root-caused to KFD memory-bank enumeration for the 9060 XT's two 8 GB modules; fixed in [rocm-systems#5204](https://github.com/ROCm/rocm-systems/pull/5204). AMD engineer reproduced the *fix* on a 9060 XT: "reported 16 GB as expected". | **Check `total_memory` before the first training run.** If 8 GB, update ROCm/torch. Highest-impact risk to this whole plan. |
| AOTriton v0.11.2 runtime bug breaks MHA on gfx1201; fixed in AOTriton 0.12.0 but some nightlies pinned 0.11.2 (pytorch#188113) | Fixed upstream | Use a release wheel (2.13.0+rocm7.2), not a nightly. Workaround if hit: `need_weights=True` bypasses SDPA dispatch. |
| RDNA4 users report distorted outputs / whole-system crashes on recent torch (comments on pytorch#184880, 9070 XT) | Anecdotal, inference/ComfyUI workloads, unresolved | Watch for it. Reported-stable config from that thread: `TORCH_BLAS_PREFER_HIPBLASLT=1`, `MIOPEN_FIND_MODE=FAST`. |
| `TensileLibrary_lazy_gfx1201.dat: No such file` → `HIPBLAS_STATUS_INVALID_VALUE` (AMD engineer, in a nightly container, pytorch#188113) | Environment-specific | Not applicable to Arch: `hipblaslt` in `extra` ships the gfx1200/1201 Tensile libraries (verified, §2). |
| Full-system hard hang under rocBLAS GEMM on a 9060 XT ([ROCm#6397](https://github.com/ROCm/ROCm/issues/6397)) | **Closed by the reporter** — reproduced on Vulkan too, so hardware/kernel, not ROCm | Discount it. |

Overall shape of the risk: **RDNA4 is compiled-for and shipped, but not CI-tested upstream.** Expect
occasional papercuts, not a wall.

### 6. Memory headroom at seq 512 / batch 16

Using Hugging Face's accounting — mixed-precision AdamW costs **18 bytes/parameter**
(6 weights + 8 optimizer + 4 gradients) plus activations
([Model memory anatomy](https://huggingface.co/docs/transformers/main/en/model_memory_anatomy)).
The activation figures below are **my own arithmetic**, not measurements — treat them as ±30% and
confirm with `torch.cuda.max_memory_allocated()` on the first run.

| Model | Params | States (18 B/p) | Activations, bs 16 × seq 512, bf16 | Est. peak | Verdict on 16 GB |
|---|---|---|---|---|---|
| BERT/RoBERTa **base** | ~110–125 M | ~2.0–2.3 GB | ~2.7 GB (+~1–2 GB if attention matrices are materialised, i.e. eager attention) | **~6–9 GB** | **Comfortable.** Could go to batch 32. |
| DeBERTa-v3-base | ~184 M (incl. large embedding) | ~3.3 GB | ~2.7 GB | ~8–10 GB | Fits; embeddings inflate the state term. |
| RoBERTa **large** | ~355 M | ~6.4 GB | ~7.2 GB | **~14–16 GB** | **Marginal.** Needs batch 8 + grad-accum 2, or gradient checkpointing, or both. |
| **LoRA on large** | ~1–5 M trainable | ~0.1 GB + ~1.4 GB frozen bf16 weights | ~7.2 GB | ~9 GB | Comfortable — LoRA removes the optimizer/gradient term, which is what actually hurts. |

Working notes on the activation term: per transformer layer, roughly 18 tensors of size
`batch × seq × hidden` are cached for backward → `16 × 512 × 768 × 2 B × 18 ≈ 227 MB/layer`,
×12 layers ≈ 2.7 GB for base; `hidden=1024`, ×24 layers ≈ 7.2 GB for large. Eager attention adds
`batch × heads × seq² × 2 B ≈ 100 MB/layer` (×2 for the dropout mask) — **this is what SDPA saves you**,
and it is why SDPA matters more than raw speed here.

**Practical guidance:** a `base` encoder at 512/16 is not close to the limit. Reserve ~2 GB headroom for the
desktop compositor if the card also drives the display, and for allocator fragmentation.

### 7. The Colab fallback

- **Free tier:** GPU type and availability *"vary over time"*; max VM lifetime ~12 h with idle timeouts;
  Google explicitly declines to publish limits because they fluctuate
  ([Colab FAQ](https://research.google.com/colaboratory/faq.html)).
- **Paid:** Colab Pro ≈ **$9.99/mo** for 100 compute units; Pro+ ≈ **$49.99/mo** for 500 CU with background
  execution (up to 24 h continuous). Pay-as-you-go ≈ $9.99 per 100 CU. *(Pricing could not be read from
  Google's own signup page — it requires sign-in — so these figures are from secondary sources and should be
  re-checked at purchase time. Polish pricing may differ.)*
- **Real costs beyond money:** no persistent filesystem (dataset re-upload or Drive mounting every session),
  disconnects mid-run, notebook-shaped workflow fighting a ports-and-adapters codebase, and no ability to
  demo the trained system offline at the defence.
- **The honest comparison:** for a `base` encoder, a T4/L4 session and the 9060 XT are the same order of
  magnitude in wall-clock. Colab buys reliability and costs reproducibility; local buys reproducibility and
  costs a few debugging days. For a thesis whose deliverable is *a runnable application*, local wins.

## What I could not verify

- **No hands-on confirmation on this exact card.** Everything here is from docs, package contents, build
  scripts, and issue trackers — this session ran on macOS, with no gfx1200 to test against.
- Whether the 8 GB VRAM-cap fix (rocm-systems#5204) has landed in **Arch's** 7.2.4 packages specifically.
  ROCm#6295 was closed after AMD verified the fix in their nightly, and Arch's ROCm predates the 7.14 line.
  **This is the single check to run first** (`total_memory` should print ~16000 MB).
- Whether MIOpen on Arch has pre-tuned gfx1200 kernel databases (the `miopen-hip` file list has only
  100 entries and no `gfx*` matches — the kernel DB is likely fetched/tuned at runtime). Expect a slow
  first iteration; irrelevant for encoders, which are GEMM-bound rather than conv-bound.
- Whether `python-pytorch-rocm` 2.13.0 was built with `USE_ROCM_CK_SDPA` on or off. Doesn't matter if CK is
  never selected, but it's why the "don't touch `preferred_rocm_fa_library`" rule is stated absolutely.
- No first-party benchmark of BERT-base fine-tuning throughput on gfx1200 was found. Expect to measure it
  yourself; there is no published number to plan a schedule against.
- Arch Wiki's GPGPU page could not be fetched (bot protection), so the group-membership step is cited from
  AMD's own prerequisites page instead.

## Sources

Primary, in order of weight:

1. [ROCm system requirements / GPU support matrix](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html) — gfx1200 = RX 9060 XT, supported
2. [ROCm 7.14.0 release notes](https://rocm.docs.amd.com/en/latest/about/release-notes.html) — 2026-07-15
3. [ROCm 6.4.1 release notes](https://rocm.docs.amd.com/en/docs-6.4.1/about/release-notes.html) — first RDNA4 support
4. [ROCm precision support matrix](https://rocm.docs.amd.com/en/latest/compatibility/precision-support.html) — RDNA4 bf16 yes, tf32 no
5. [ROCm install prerequisites](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/prerequisites.html) — `sudo usermod -a -G video,render $LOGNAME`
6. [AMD PyTorch install (AI ecosystem)](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html) — `torch[device-gfx1200]`
7. [pytorch/pytorch `release/2.13` `.ci/docker/manywheel/build.sh`](https://github.com/pytorch/pytorch/blob/release/2.13/.ci/docker/manywheel/build.sh) — wheel arch list
8. [download.pytorch.org/whl/rocm7.2](https://download.pytorch.org/whl/rocm7.2) — torch 2.13.0+rocm7.2
9. [Arch `python-pytorch` PKGBUILD](https://gitlab.archlinux.org/archlinux/packaging/packages/python-pytorch) + [`rocm-supported-gfx`](https://gitlab.archlinux.org/tpkessler/rocm-toolchain) — gfx1200 in Arch's build
10. [Arch package search: rocm](https://archlinux.org/packages/?q=rocm) — versions as of 2026-08-10
11. [pytorch#184880](https://github.com/pytorch/pytorch/issues/184880) / [ROCm#6295](https://github.com/ROCm/ROCm/issues/6295) — 8 GB VRAM cap
12. [pytorch#188113](https://github.com/pytorch/pytorch/issues/188113) + [PR#188114](https://github.com/pytorch/pytorch/pull/188114) — CK SDPA broken on RDNA4
13. [ROCm#6506](https://github.com/ROCm/ROCm/issues/6506) — FlashAttention-2 CK built on a 9060 XT
14. [ROCm#6397](https://github.com/ROCm/ROCm/issues/6397) — hard hang, withdrawn by reporter
15. [HF model memory anatomy](https://huggingface.co/docs/transformers/main/en/model_memory_anatomy) — 18 B/param
16. [HF GPU inference docs](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one) — FA2 limited to MI2xx/MI3xx
17. [Google Colab FAQ](https://research.google.com/colaboratory/faq.html) — limits vary, 12 h VM lifetime

Secondary (flagged as such in the text): Colab Pro/Pro+ price points.
