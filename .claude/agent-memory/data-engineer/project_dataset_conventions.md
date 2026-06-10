---
name: dataset conventions (factlens)
description: Label convention and kept columns for the ISOT fake-news dataset in this project
type: project
---

**Binary label convention:** `1 = True`, `0 = Fake`. Confirmed by user 2026-04-14.

**Training input:** pure article `text` only. `title`, `subject`, `date` are dropped as leakage-prone. `title` may be reintroduced later as a separate feature (user's future idea: early-stop marker for potential-fake flagging), but not now.

**Why:** Keep a clean separation between exploratory and pipeline-facing work. Current work lives in `notebooks/explore/` and `notebooks/report/` (the prior `*_temp/` archive dirs have been removed).

**How to apply:** When cleaning or modeling, feed only `text` + `label`. Don't surface `title`/`subject`/`date` columns into processed outputs.
