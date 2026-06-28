import argparse
from pathlib import Path

from manim_kb import build_knowledge_base, print_tree, write_json, write_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a structured Manim API knowledge base.")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for manim_kb.json and manim_kb.md (default: output)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed method signatures in the console tree",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    kb = build_knowledge_base()

    json_path = write_json(kb, output_dir / "manim_kb.json")
    md_path = write_markdown(kb, output_dir / "manim_kb.md")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print_tree(kb, verbose=args.verbose)


if __name__ == "__main__":
    main()
