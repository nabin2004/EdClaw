# /// script
# dependencies = [
#   "trl>=0.12",
#   "peft>=0.13",
#   "datasets>=3.1",
#   "transformers>=4.46",
# ]
# ///
"""DPO pass on manibench-preference (chosen/rejected). Run on HF Jobs after Stage-B milestones."""

from __future__ import annotations

import argparse
import json
import os
import sys


def _load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _to_dpo_rows(rows):
    """TRL DPO expects prompt (str), chosen, rejected — flatten chat prompt."""
    out = []
    for r in rows:
        prompt_msgs = r.get("prompt") or r.get("messages")[:2]
        # Serialize prompt to single string for tokenizer if list
        if isinstance(prompt_msgs, list):
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in prompt_msgs)
        else:
            prompt = str(prompt_msgs)
        out.append(
            {
                "prompt": prompt,
                "chosen": r["chosen"],
                "rejected": r["rejected"],
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemma-4-E2B-it")
    ap.add_argument("--dataset-jsonl", type=str, required=True)
    ap.add_argument("--adapter-model", type=str, default=None, help="Hub LoRA from prior SFT")
    ap.add_argument("--hub-model-id", default="nabin2004/manibench-gemma4-dpo")
    ap.add_argument("--output-dir", default="dpo-out")
    ap.add_argument("--beta", type=float, default=0.1)
    args = ap.parse_args()

    from datasets import Dataset  # noqa: WPS433
    from peft import PeftModel  # noqa: WPS433
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: WPS433
    from trl import DPOConfig, DPOTrainer  # noqa: WPS433

    raw = _load_jsonl(args.dataset_jsonl)
    flat = _to_dpo_rows(raw)
    ds = Dataset.from_list(flat).train_test_split(test_size=0.05, seed=42)

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, trust_remote_code=True)
    ref = AutoModelForCausalLM.from_pretrained(args.model, trust_remote_code=True)

    if args.adapter_model:
        model = PeftModel.from_pretrained(model, args.adapter_model)

    trainer = DPOTrainer(
        model=model,
        ref_model=ref,
        args=DPOConfig(
            output_dir=args.output_dir,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=5e-6,
            beta=args.beta,
            push_to_hub=True,
            hub_model_id=args.hub_model_id,
            bf16=True,
            max_length=4096,
            max_prompt_length=2048,
            report_to=os.environ.get("REPORT_TO", "none"),
        ),
        train_dataset=ds["train"],
        eval_dataset=ds["test"],
        tokenizer=tokenizer,
    )
    trainer.train()
    trainer.push_to_hub()
    print("DPO done.", file=sys.stderr)


if __name__ == "__main__":
    main()
