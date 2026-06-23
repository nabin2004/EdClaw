#!/usr/bin/env python
# train_grpo_manim_modular.py

from peft import LoraConfig, PeftModel, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import GRPOConfig, GRPOTrainer

from manibench import build_dataset
from rewards import combined_reward

BASE_MODEL    = "unsloth/gemma-4-E2B-it"
SFT_LORA_PATH = "nabin2004/EduClaw-Gemma4-it"
OUTPUT_DIR    = "./grpo_manim_modular"


def load_model(base_model: str, sft_lora_path: str):
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype="auto", device_map="auto")

    # Frozen SFT adapter — kept in memory but not trained
    model = PeftModel.from_pretrained(model, sft_lora_path, adapter_name="sft")
    for name, param in model.named_parameters():
        if "sft" in name:
            param.requires_grad = False

    # Trainable Manim GRPO adapter
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model.add_adapter("manim", lora_config)
    model.set_adapter("manim")
    model.train()

    return model, tokenizer, lora_config


def make_training_args(output_dir: str) -> GRPOConfig:
    return GRPOConfig(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        learning_rate=1e-6,
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
        bf16=True,
        gradient_checkpointing=True,
        max_completion_length=1024,
        num_generations=4,
        temperature=0.8,
        top_p=0.9,
        use_vllm=False,
        beta=0.0,
        loss_type="dapo",
        scale_rewards="group",
    )


def main():
    dataset                      = build_dataset()
    model, tokenizer, lora_cfg   = load_model(BASE_MODEL, SFT_LORA_PATH)
    training_args                = make_training_args(OUTPUT_DIR)

    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        reward_funcs=combined_reward,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=lora_cfg,
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR, adapter_name="manim")
    print(f"Manim GRPO LoRA saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
