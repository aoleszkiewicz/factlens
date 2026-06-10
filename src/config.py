"""Project-wide configuration constants — the single source of truth.

`RANDOM_STATE` seeds every stochastic operation in the project (train/val/test
splits, DataFrame sampling, sklearn estimators) so results are reproducible.
Import it everywhere rather than hardcoding a seed:

    from src.config import RANDOM_STATE

It can be overridden by exporting ``RANDOM_STATE`` in the shell or CI (e.g. to
sweep seeds); it defaults to 42. Note: no `.env` file is auto-loaded, so an entry
in `example.env`/`.env` only takes effect once exported into the environment.
"""

import os

RANDOM_STATE = int(os.environ.get("RANDOM_STATE", "42"))
