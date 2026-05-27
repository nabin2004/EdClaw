"""Build ``sft_dataset.jsonl`` from local ``dataset/`` (delegates to training package)."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    repo_root = here.parents[4]  # .../EdClaw (parents: new_automanim, automanim, educlaw, src)
    sys.path.insert(0, str(repo_root / "training" / "automanim"))

    from automanim_sft.build_dataset import (
        build_automanim_jsonl,
        print_build_summary,
    )

    summary = build_automanim_jsonl(
        dataset_dir=here / "dataset",
        output_file=here / "sft_dataset.jsonl",
        require_generated_code=True,
        include_failures=True,
        verbose_every=10,
    )
    print_build_summary(summary)


if __name__ == "__main__":
    main()
