---
name: dataset conventions (factlens)
description: Label convention, kept columns, and temp-dir semantics for the ISOT fake-news dataset in this project
type: project
---

**Binary label convention:** `1 = True`, `0 = Fake`. Confirmed by user 2026-04-14.

**Training input:** pure article `text` only. `title`, `subject`, `date` are dropped as leakage-prone. `title` may be reintroduced later as a separate feature (user's future idea: early-stop marker for potential-fake flagging), but not now.

**`notebooks/explore_temp/` and `notebooks/report_temp/`** are intentionally kept as scratch/archive from a previous iteration. Do not delete, do not promote — treat as read-only historical reference.

**Why:** User wants clean separation between prior iteration's exploratory work (kept for reference) and current pipeline. Current work goes in `notebooks/explore/` and later `notebooks/report/`.

**How to apply:** When cleaning or modeling, feed only `text` + `label`. Don't surface `title`/`subject`/`date` columns into processed outputs. When looking for prior EDA context, check `*_temp/` dirs but don't modify them.
