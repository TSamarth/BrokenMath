"""Seeded fixed subset of sycophancy_recent's sample.json, copied into both
sycophancy_recent/ and sycophancy_verify/ raw folders so both solver framings
(prove vs prove-or-disprove) run on the exact same problem IDs.

Usage:
    python scripts/sample_subset.py --n 120 --seed 42
"""
import argparse
import json
import random


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--source", default="data/raw/sycophancy_recent/sample.json")
    parser.add_argument(
        "--targets",
        nargs="+",
        default=[
            "data/raw/sycophancy_recent/sample_120.json",
            "data/raw/sycophancy_verify/sample_120.json",
        ],
    )
    args = parser.parse_args()

    data = json.load(open(args.source, encoding="utf-8"))
    data_sorted = sorted(data, key=lambda row: row["problem_id"])  # deterministic order before sampling
    subset = random.Random(args.seed).sample(data_sorted, args.n)

    for target in args.targets:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(subset, f, indent=2, ensure_ascii=False)
        print(f"wrote {len(subset)} rows -> {target}")


if __name__ == "__main__":
    main()
