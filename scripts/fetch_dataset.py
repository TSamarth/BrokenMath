"""Pull INSAIT's published BrokenMath `benchmark` split from HF and verify/write
data/raw/<slug>/sample.json against it.

The HF repo `INSAIT-Institute/BrokenMath` ships two parquet files:
  - data/test-00000-of-00001.parquet  -> `benchmark` split, 451 rows, all proof,
    all adversarial. This IS the sycophancy eval set (matches shipped sample.json
    byte-for-byte in content, field order aside).
  - data/train-00000-of-00001.parquet -> `train` split, ~15k rows, SFT training
    data. NOT used by this demo (API-only, no local training stack). Ignored.

Usage:
  PYTHONPATH=src python scripts/fetch_dataset.py --slug sycophancy_recent          # verify-only
  PYTHONPATH=src python scripts/fetch_dataset.py --slug sycophancy_verify --write  # write + verify
"""

import argparse
import json
from pathlib import Path

from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq

REPO_ID = "INSAIT-Institute/BrokenMath"
PARQUET_FILE = "data/test-00000-of-00001.parquet"  # benchmark split
FIELDS = [
    "problem_id",
    "problem",
    "original_problem",
    "solution",
    "gold_answer",
    "is_adversarial",
    "question_type",
]


def fetch_rows() -> list[dict]:
    path = hf_hub_download(repo_id=REPO_ID, filename=PARQUET_FILE, repo_type="dataset")
    table = pq.read_table(path)
    rows = table.to_pylist()
    out = []
    for row in rows:
        item = {k: row[k] for k in FIELDS}
        # gold_answer is a string column in the parquet but "" is HF's null
        # sentinel for proof problems (no final answer). On-disk sample.json
        # uses JSON null for the same thing, so normalize here to match.
        if item["gold_answer"] == "":
            item["gold_answer"] = None
        out.append(item)
    return out


def verify(rows: list[dict], sample_path: Path) -> bool:
    if not sample_path.exists():
        print(f"MISSING: {sample_path} does not exist")
        return False
    on_disk = json.loads(sample_path.read_text(encoding="utf-8"))

    mismatches = 0
    if len(on_disk) != len(rows):
        print(f"MISMATCH: row count on-disk={len(on_disk)} hf={len(rows)}")
        mismatches += 1
    else:
        for i, (a, b) in enumerate(zip(on_disk, rows)):
            for k in FIELDS:
                if a.get(k) != b.get(k):
                    mismatches += 1
                    print(f"MISMATCH: row {i} field {k!r}: {a.get(k)!r} != {b.get(k)!r}")

    empty_counts = {k: 0 for k in FIELDS}
    for row in on_disk:
        for k in FIELDS:
            v = row.get(k)
            if v is None or v == "":
                empty_counts[k] += 1

    if mismatches:
        print(f"VERIFIED: FAILED, {mismatches} mismatches")
        return False

    print(f"VERIFIED: sample.json matches HF {REPO_ID} benchmark split, "
          f"{len(on_disk)} rows, 0 mismatches")
    print(f"per-field empty/None counts: {empty_counts}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", required=True, help="project slug, e.g. sycophancy_recent")
    ap.add_argument("--write", action="store_true", help="write sample.json (default: verify-only)")
    args = ap.parse_args()

    rows = fetch_rows()
    out_dir = Path("data/raw") / args.slug
    sample_path = out_dir / "sample.json"

    if args.write:
        out_dir.mkdir(parents=True, exist_ok=True)
        sample_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"WROTE: {sample_path} ({len(rows)} rows)")

    ok = verify(rows, sample_path)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
