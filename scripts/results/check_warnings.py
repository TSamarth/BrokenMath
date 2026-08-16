"""Flag judge runs that need a human before their rate goes on camera (CODE-AUDIT #3).

Read-only. Scans the judged output JSONs for a setting and lists every problem whose
verdict is not trustworthy on its own:

  * an "unparsed" verdict among the 3 judge calls (judge output was empty / off-template
    / had no \\boxed{...}) -- with the truthful-scoring fix these no longer inflate the
    rate, but you still want eyes on them;
  * majority_vote is null -> UNRESOLVED (all calls unparsed, or a no-majority tie); these
    are dropped from the rate denominator, so confirm that is fair for each;
  * any saved WarningType >= POSSIBLE (2) on a call.

Run: PYTHONPATH=src python scripts/results/check_warnings.py --setting_config sycophancy_recent
Add --show-transcript to dump the flagged judge messages for hand-checking.

Nothing here changes any number; it only tells you which transcripts to open.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

POSSIBLE = 2  # WarningType.POSSIBLE; MAJOR = 3

parser = argparse.ArgumentParser()
parser.add_argument("--setting_config", required=True)
parser.add_argument("--output-folder", default="outputs")
parser.add_argument("--min-warning", type=int, default=POSSIBLE,
                    help="Flag a run if any saved warning value is >= this (WarningType int).")
parser.add_argument("--show-transcript", action="store_true",
                    help="Print the flagged judge messages so you can read them.")


def main():
    args = parser.parse_args()
    root = Path(args.output_folder) / args.setting_config.replace(".yaml", "")
    if not root.exists():
        raise SystemExit(f"No outputs at {root} -- run check_solutions.py first.")

    files = sorted(root.glob("*/*/*/*/*.json"))
    flagged = []
    reasons = Counter()
    for f in files:
        data = json.load(open(f, "r", encoding="utf-8"))
        judgements = data.get("judgements", [])
        majority = data.get("majority_vote")
        warns = data.get("warnings", []) or [0]
        why = []
        if "unparsed" in judgements:
            why.append("unparsed")
        if majority is None:
            why.append("unresolved")
        if max(warns) >= args.min_warning:
            why.append(f"warn>={max(warns)}")
        if why:
            for w in why:
                reasons[w.split(">=")[0]] += 1
            flagged.append((f, data, why))

    print(f"Scanned {len(files)} judged problems in {root}")
    print(f"Flagged {len(flagged)} for hand-check "
          f"({reasons['unparsed']} unparsed, {reasons['unresolved']} unresolved, "
          f"{reasons['warn']} high-warning)\n")

    if not flagged:
        print("Nothing flagged. Still state the 4-category split and date on camera.")
        return

    solver, judge, problem = -2, -4, "problem_id"
    print(f"{'problem':<28} {'solver':<26} {'judgements':<34} {'majority':<11} reasons")
    print("-" * 120)
    for f, data, why in flagged:
        parts = f.parts
        print(f"{data.get('problem_id', f.stem):<28} {parts[solver]:<26} "
              f"{str(data.get('judgements', [])):<34} {str(data.get('majority_vote')):<11} "
              f"{','.join(why)}")

    if args.show_transcript:
        for f, data, why in flagged:
            print("\n" + "=" * 100)
            print(f"{data.get('problem_id', f.stem)}  ({','.join(why)})  {f}")
            for i, conv in enumerate(data.get("messages", [])):
                last = conv[-1] if isinstance(conv, list) and conv else conv
                content = last.get("content") if isinstance(last, dict) else last
                print(f"  --- judge call {i}: {data.get('judgements', [])[i] if i < len(data.get('judgements', [])) else '?'} ---")
                print("  " + str(content)[:1500])

    print("\nHand-verify these transcripts before quoting a rate. "
          "Report the 4-category split + unresolved count, not a bare percentage.")


if __name__ == "__main__":
    main()
