import argparse
import json
import urllib.error
import urllib.request

SYSTEM = """You paraphrase Manim fine-tuning instructions.
Return ONLY valid JSON: {"paraphrases": ["...", "...", "...", "...", "..."]}
Rules: same meaning as the original; keep class/method/backtick names exact; 5 diverse phrasings; clear and concise."""

DEFAULT_MODEL = "gemma4:e2b"
DEFAULT_URL = "http://localhost:11434/api/chat"
DEFAULT_INPUT = "output/manim_curriculum.jsonl"
DEFAULT_OUTPUT = "output/manim_curriculum_paraphrased.jsonl"
VARIANTS = 5


def load_jsonl(path):
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def resume_offset(output_path):
    try:
        with open(output_path, encoding="utf-8") as file:
            return sum(1 for _ in file) // VARIANTS
    except FileNotFoundError:
        return 0


def ollama_json(url, model, system, user):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["message"]["content"]
    return json.loads(content)


def paraphrase(url, model, instruction, row_index):
    try:
        data = ollama_json(url, model, SYSTEM, instruction)
        variants = data.get("paraphrases", [])
        if not isinstance(variants, list):
            raise ValueError("paraphrases is not a list")
        variants = [v for v in variants if isinstance(v, str) and v.strip()]
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"  row {row_index}: ollama/parse error ({exc}), using original instruction")
        variants = []

    while len(variants) < VARIANTS:
        variants.append(instruction)
    return variants[:VARIANTS]


def main():
    parser = argparse.ArgumentParser(description="Paraphrase Manim curriculum instructions via Ollama.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--limit", type=int, default=0, help="Max input rows to process (0 = all)")
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    start = resume_offset(args.output)
    end = len(rows) if args.limit <= 0 else min(start + args.limit, len(rows))

    if start:
        print(f"Resuming from row {start + 1} ({start} already done)")
    print(f"Processing rows {start + 1}-{end} of {len(rows)} with model {args.model!r}")

    with open(args.output, "a", encoding="utf-8") as out:
        for i in range(start, end):
            row = rows[i]
            variants = paraphrase(args.url, args.model, row["instruction"], i + 1)
            for instruction in variants:
                out.write(json.dumps({"instruction": instruction, "output": row["output"]}, ensure_ascii=False) + "\n")
            out.flush()
            if (i + 1) % 10 == 0 or i + 1 == end:
                print(f"  {i + 1}/{end} done")

    print(f"Wrote {(end - start) * VARIANTS} rows to {args.output}")


if __name__ == "__main__":
    main()

# python self_prepare.py --limit 5 --model gemma4:e2b   # smoke test
# python self_prepare.py --model gemma4:e2b             # full run (resumable)
