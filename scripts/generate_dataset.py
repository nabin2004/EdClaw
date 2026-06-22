#!/usr/bin/env python3
"""
Bulk dataset generator: run the full pipeline across many topics to build a finetuning dataset.

Each run generates lecture markdown files + audio scripts + Manim scenes for one topic.
Output is a JSONL file where every line is one lecture record.

Two output formats:
  raw       – every field verbatim (markdown, audio_script JSON, SRT text, scene paths)
  sharegpt  – two conversations per lecture:
                1. user: "Write a lecture about X" → assistant: markdown
                2. user: "Convert this to audio script: ..." → assistant: JSON script

Usage:
  python scripts/generate_dataset.py --topics-file topics.txt --runs 1000
  python scripts/generate_dataset.py --topics "calculus,statistics,linear algebra" --runs 50
  python scripts/generate_dataset.py --runs 200 --workers 2 --no-automanim
  python scripts/generate_dataset.py --runs 500 --resume --dataset-out data/ds.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from educlaw.autocourse.pipeline import PipelineConfig, run_pipeline  # noqa: E402

# ---------------------------------------------------------------------------
# Default topic pool (used when no --topics / --topics-file is given)
# ---------------------------------------------------------------------------

_DEFAULT_TOPICS: list[str] = [
    # Mathematics
    "Introduction to Linear Algebra",
    "Calculus: Limits and Derivatives",
    "Calculus: Integrals and the Fundamental Theorem",
    "Multivariable Calculus",
    "Introduction to Probability Theory",
    "Statistics: Hypothesis Testing and Confidence Intervals",
    "Discrete Mathematics and Combinatorics",
    "Introduction to Real Analysis",
    "Differential Equations: First Order Methods",
    "Differential Equations: Systems and Phase Planes",
    "Number Theory and Modular Arithmetic",
    "Graph Theory and Network Analysis",
    "Topology: Spaces and Continuity",
    "Abstract Algebra: Groups and Rings",
    "Fourier Analysis and Signal Processing",
    "Numerical Methods and Approximation",
    "Optimization: Convex Functions and Gradient Descent",
    "Information Theory and Entropy",
    "Bayesian Inference and Probabilistic Models",
    "Markov Chains and Stochastic Processes",
    # Machine Learning / AI
    "Introduction to Machine Learning",
    "Supervised Learning: Regression and Classification",
    "Decision Trees and Ensemble Methods",
    "Support Vector Machines",
    "Unsupervised Learning and Clustering",
    "Dimensionality Reduction: PCA and t-SNE",
    "Neural Networks and Backpropagation",
    "Convolutional Neural Networks",
    "Recurrent Neural Networks and LSTMs",
    "Transformer Architecture and Attention",
    "Generative Adversarial Networks",
    "Reinforcement Learning: Q-Learning and Policy Gradient",
    "Natural Language Processing Fundamentals",
    "Large Language Models and Prompt Engineering",
    "Bias and Variance Tradeoff",
    "Regularization Techniques: L1, L2, and Dropout",
    "Gradient Descent Variants and Learning Rate Scheduling",
    "Batch Normalization and Layer Normalization",
    "Transfer Learning and Fine-Tuning",
    "Evaluation Metrics for Machine Learning",
    # Computer Science
    "Data Structures: Arrays, Stacks, and Queues",
    "Data Structures: Trees and Heaps",
    "Data Structures: Hash Tables and Graphs",
    "Sorting Algorithms and Complexity Analysis",
    "Dynamic Programming and Memoization",
    "Greedy Algorithms",
    "Divide and Conquer Algorithms",
    "Graph Algorithms: BFS, DFS, and Shortest Paths",
    "Operating Systems: Processes and Scheduling",
    "Memory Management and Virtual Memory",
    "Database Systems: Relational Model and SQL",
    "Database Systems: Indexing and Query Optimization",
    "Computer Networks: TCP/IP and Protocols",
    "Distributed Systems and Consensus",
    "Compilers: Lexing, Parsing, and Code Generation",
    "Theory of Computation and Automata",
    "Cryptography: Symmetric and Asymmetric Encryption",
    "Computer Architecture: CPU and Memory Hierarchy",
    "Concurrency and Parallel Programming",
    "Functional Programming Principles",
    # Physics
    "Classical Mechanics: Newton's Laws",
    "Classical Mechanics: Energy and Momentum",
    "Thermodynamics: Laws and Entropy",
    "Statistical Mechanics and the Boltzmann Distribution",
    "Electromagnetism: Electric Fields and Gauss's Law",
    "Electromagnetism: Magnetic Fields and Faraday's Law",
    "Quantum Mechanics: Wave-Particle Duality",
    "Quantum Mechanics: Schrödinger Equation",
    "Special Relativity: Time Dilation and Length Contraction",
    "Fluid Mechanics and the Navier-Stokes Equation",
    # Chemistry / Biology
    "Organic Chemistry: Reaction Mechanisms",
    "Thermochemistry and Gibbs Free Energy",
    "Cell Biology: Membrane Structure and Transport",
    "Molecular Biology: DNA Replication and Transcription",
    "Genetics: Mendelian Inheritance and Beyond",
    "Evolutionary Biology: Natural Selection",
    "Enzyme Kinetics and Michaelis-Menten Model",
    "Neuroscience: Action Potentials and Synaptic Transmission",
    # Data Science / Engineering
    "Introduction to Data Science and the Data Pipeline",
    "Exploratory Data Analysis and Visualization",
    "Feature Engineering for Machine Learning",
    "Time Series Analysis and Forecasting",
    "Causal Inference and A/B Testing",
    "Data Wrangling with Pandas",
    "SQL for Data Analysis",
    "Introduction to Apache Spark and Big Data",
    "Signal Processing: Sampling and Aliasing",
    "Control Theory: PID Controllers",
    # Economics / Social Science
    "Microeconomics: Supply, Demand, and Market Equilibrium",
    "Macroeconomics: GDP, Inflation, and Monetary Policy",
    "Game Theory: Nash Equilibria and Strategic Behavior",
    "Introduction to Behavioral Economics",
    "Financial Mathematics: Time Value of Money",
    "Portfolio Theory and Risk Management",
    "Introduction to Econometrics",
    "Network Effects and Platform Economics",
]

_TOPIC_TEMPLATES = [
    "{topic}",
    "Teach me about {topic}",
    "Introduction to {topic}",
    "{topic} for beginners",
    "Deep dive into {topic}",
]


def _expand_topics(base: list[str], target: int) -> list[str]:
    """Expand base topic list to at least `target` entries using templates."""
    expanded: list[str] = []
    for tmpl in _TOPIC_TEMPLATES:
        for t in base:
            expanded.append(tmpl.format(topic=t))
    # Cycle to reach target count
    out: list[str] = []
    while len(out) < target:
        out.extend(expanded)
    return out[:target]


def _load_topics_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    topics: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Try JSON-line with {"topic": "..."} format
        if line.startswith("{"):
            try:
                topics.append(json.loads(line)["topic"])
                continue
            except (json.JSONDecodeError, KeyError):
                pass
        topics.append(line)
    return topics


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "topic"


def _write_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _lecture_to_raw_record(run_id: str, topic: str, lecture_row: dict, out_root: Path) -> dict:
    record: dict = {
        "run_id": run_id,
        "topic": topic,
        "lecture_index": lecture_row.get("lecture_index"),
        "lecture_title": lecture_row.get("lecture_title"),
    }
    # Read markdown content
    md_rel = lecture_row.get("markdown")
    if md_rel:
        md_path = out_root / md_rel
        if md_path.is_file():
            record["markdown"] = md_path.read_text(encoding="utf-8")
    # Read audio script JSON
    script_rel = lecture_row.get("audio_script")
    if script_rel:
        sp = out_root / script_rel
        if sp.is_file():
            try:
                record["audio_script"] = json.loads(sp.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    # Read SRT
    srt_rel = lecture_row.get("audio_srt")
    if srt_rel:
        srtp = out_root / srt_rel
        if srtp.is_file():
            record["srt"] = srtp.read_text(encoding="utf-8")
    # Manim scenes
    if lecture_row.get("manim_scenes"):
        record["manim_scenes"] = lecture_row["manim_scenes"]
    return record


def _lecture_to_sharegpt_records(
    run_id: str, topic: str, lecture_row: dict, out_root: Path
) -> list[dict]:
    records: list[dict] = []
    lecture_title = lecture_row.get("lecture_title", "")

    md_rel = lecture_row.get("markdown")
    md_text: str | None = None
    if md_rel:
        md_path = out_root / md_rel
        if md_path.is_file():
            md_text = md_path.read_text(encoding="utf-8")

    script_rel = lecture_row.get("audio_script")
    script_text: str | None = None
    if script_rel:
        sp = out_root / script_rel
        if sp.is_file():
            script_text = sp.read_text(encoding="utf-8")

    base_meta = {
        "run_id": run_id,
        "topic": topic,
        "lecture_index": lecture_row.get("lecture_index"),
        "lecture_title": lecture_title,
    }

    # Conversation 1: generate lecture markdown
    if md_text:
        records.append({
            **base_meta,
            "type": "lecture_generation",
            "conversations": [
                {
                    "role": "user",
                    "value": (
                        f"You are an expert instructor. Write a complete lecture on the following topic "
                        f"as part of the course '{topic}'.\n\nLecture title: {lecture_title}\n\n"
                        "Write the lecture in Markdown with clear structure: hook, explanations, "
                        "worked example, recap, and check-your-understanding questions."
                    ),
                },
                {"role": "assistant", "value": md_text},
            ],
        })

    # Conversation 2: convert markdown to audio script
    if md_text and script_text:
        records.append({
            **base_meta,
            "type": "audio_script_generation",
            "conversations": [
                {
                    "role": "user",
                    "value": (
                        "Convert the following lecture Markdown into a structured audio narration "
                        "script as JSON. Write in natural spoken English only — no LaTeX, "
                        "no Markdown syntax. Each segment should feel natural when read aloud.\n\n"
                        f"--- MARKDOWN ---\n{md_text[:6000]}\n--- END ---"
                    ),
                },
                {"role": "assistant", "value": script_text},
            ],
        })

    return records


async def _run_one(
    run_idx: int,
    topic: str,
    cfg_kwargs: dict,
    out_root: Path,
    dataset_out: Path,
    fmt: str,
    sem: asyncio.Semaphore,
    resume: bool,
) -> bool:
    run_id = f"run-{run_idx:05d}"
    run_dir = out_root / run_id

    if resume and (run_dir / "pipeline-manifest.json").is_file():
        print(f"[{run_id}] Skipping (already done): {topic[:60]}")
        return True

    print(f"[{run_id}] Starting: {topic[:60]}")
    async with sem:
        try:
            cfg = PipelineConfig(
                topic=topic,
                out=run_dir,
                **cfg_kwargs,
            )
            exit_code, run_out = await run_pipeline(cfg)
            if exit_code != 0:
                print(f"[{run_id}] Pipeline returned exit_code={exit_code}")
                return False

            # Read manifest to extract per-lecture rows
            manifest_path = run_out / "pipeline-manifest.json"
            if not manifest_path.is_file():
                return False
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            lecture_rows: list[dict] = manifest.get("lectures") or []

            for lrow in lecture_rows:
                if lrow.get("error"):
                    continue
                if fmt == "sharegpt":
                    for rec in _lecture_to_sharegpt_records(run_id, topic, lrow, run_out):
                        _write_jsonl(dataset_out, rec)
                else:
                    rec = _lecture_to_raw_record(run_id, topic, lrow, run_out)
                    _write_jsonl(dataset_out, rec)

            print(f"[{run_id}] Done: {len(lecture_rows)} lectures written to dataset")
            return True
        except Exception:  # noqa: BLE001
            print(f"[{run_id}] ERROR for topic '{topic[:60]}':")
            traceback.print_exc()
            return False


async def _async_main(args: argparse.Namespace) -> int:
    # Build topic list
    if args.topics_file:
        base_topics = _load_topics_file(Path(args.topics_file))
    elif args.topics:
        base_topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    else:
        base_topics = _DEFAULT_TOPICS

    topics = _expand_topics(base_topics, args.runs)
    print(
        f"Dataset generation: {args.runs} runs, {args.lectures} lectures each, "
        f"{args.workers} worker(s), format={args.format}"
    )

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    dataset_out = Path(args.dataset_out).expanduser().resolve()
    dataset_out.parent.mkdir(parents=True, exist_ok=True)

    cfg_kwargs: dict = {
        "lectures": args.lectures,
        "enable_tts": not args.no_tts,
        "enable_automanim": not args.no_automanim,
        "enable_shield": not args.no_shield,
        "enable_audio_script": not args.no_audio_script,
        "continue_on_error": True,
    }

    sem = asyncio.Semaphore(args.workers)
    tasks = [
        _run_one(
            run_idx=i,
            topic=topic,
            cfg_kwargs=cfg_kwargs,
            out_root=out_root,
            dataset_out=dataset_out,
            fmt=args.format,
            sem=sem,
            resume=args.resume,
        )
        for i, topic in enumerate(topics[: args.runs], start=1)
    ]

    results = await asyncio.gather(*tasks)
    n_ok = sum(1 for r in results if r)
    n_fail = len(results) - n_ok
    print(f"\nFinished: {n_ok} succeeded, {n_fail} failed.")
    print(f"Dataset: {dataset_out}")
    return 0 if n_fail == 0 else 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--topics-file",
        metavar="FILE",
        default=None,
        help="Path to topics file (one per line, or JSONL with {\"topic\": \"...\"}).",
    )
    p.add_argument(
        "--topics",
        default=None,
        help="Comma-separated list of topics to use.",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=100,
        metavar="N",
        help="Total number of pipeline runs to execute (default: 100).",
    )
    p.add_argument(
        "--lectures",
        type=int,
        default=4,
        metavar="N",
        help="Lectures per run (2–8, default: 4).",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        metavar="N",
        help="Concurrent pipeline workers (default: 1). >1 useful with multiple GPUs.",
    )
    p.add_argument(
        "--out-root",
        default="content/ir/series",
        metavar="DIR",
        help="Root directory for all pipeline run outputs (default: content/ir/series).",
    )
    p.add_argument(
        "--dataset-out",
        default="dataset/dataset.jsonl",
        metavar="FILE",
        help="JSONL output file for the finetuning dataset (default: dataset/dataset.jsonl).",
    )
    p.add_argument(
        "--format",
        choices=("raw", "sharegpt"),
        default="sharegpt",
        help=(
            "Output format: 'raw' includes all fields verbatim; "
            "'sharegpt' produces conversation pairs for SFT (default: sharegpt)."
        ),
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Skip runs where pipeline-manifest.json already exists.",
    )
    p.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable TTS synthesis (audio script JSON still generated if LLM is available).",
    )
    p.add_argument(
        "--no-audio-script",
        action="store_true",
        help="Disable audio script generation; use raw text TTS instead.",
    )
    p.add_argument(
        "--no-automanim",
        action="store_true",
        help="Disable AutoManim scene generation.",
    )
    p.add_argument(
        "--no-shield",
        action="store_true",
        help="Disable Ollama Shield safety check.",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
