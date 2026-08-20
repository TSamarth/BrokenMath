"""Run the full solve->judge->results pipeline on the 120-item subset, one step
at a time, logging each step's full output to run_logs/ as it happens.

Does not silently continue past a failed step, and does not silently patch
config files — it verifies configs/projects/{PROJECT}.yaml's model_configs
already matches SOLVER_MODEL and refuses to proceed if not (that field is
hand-managed, see CLAUDE.md).

Edit the CONFIG block below, then:
    python scripts/run_experiment.py
"""
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — edit these per run
# ---------------------------------------------------------------------------
PROJECT = "sycophancy_recent"          # or "sycophancy_verify"
SOLVER_MODEL = "openai/gpt-5.6-luna"   # must match configs/projects/{PROJECT}.yaml model_configs (no .yaml suffix)
JUDGE_MODELS = ["opencode/deepseek-v4-flash"]   # --checker_configs, space-separated list
N_JUDGE_VOTES = 3                      # --n for check_solutions.py (majority vote)
FILE_NAME = "sample_120.json"          # 120-item subset, NOT sample.json (451 items)
SKIP_EXISTING = False                   # resume check_solutions.py without re-grading
SYNCHRONOUS_SOLVE = True              # --synchronous on solve.py (True = easier to read logs live, slower)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "run_logs"
RUN_ID = time.strftime("%Y%m%d_%H%M%S")


def verify_solver_model():
    project_yaml = ROOT / "configs" / "projects" / f"{PROJECT}.yaml"
    text = project_yaml.read_text(encoding="utf-8")
    expected = f'- "{SOLVER_MODEL}"'
    if expected not in text:
        print(f"[FAIL] {project_yaml} model_configs does not contain {expected!r}.")
        print(f"       Edit that file's model_configs to match SOLVER_MODEL before running.")
        sys.exit(1)
    print(f"[OK] {project_yaml} model_configs matches SOLVER_MODEL={SOLVER_MODEL!r}")


def run_step(name, cmd):
    log_path = LOG_DIR / f"{PROJECT}_{name}_{RUN_ID}.log"
    print(f"\n{'=' * 70}\nSTEP: {name}\nCMD:  {' '.join(cmd)}\nLOG:  {log_path}\n{'=' * 70}")

    with open(log_path, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in process.stdout:
            print(line, end="")
            log_file.write(line)
        process.wait()

    if process.returncode != 0:
        print(f"\n[FAIL] Step '{name}' exited {process.returncode}. Stopping. See {log_path}")
        sys.exit(process.returncode)
    print(f"[OK] Step '{name}' finished. Log: {log_path}")


def main():
    LOG_DIR.mkdir(exist_ok=True)    
    verify_solver_model()

    run_step("process", [
        sys.executable, "scripts/process.py",
        "--project", PROJECT,
        "--file-name", FILE_NAME,
    ])

    solve_cmd = [sys.executable, "scripts/solve.py", "--project", PROJECT]
    if SYNCHRONOUS_SOLVE:
        solve_cmd.append("--synchronous")
    run_step("solve", solve_cmd)

    run_step("postprocess", [
        sys.executable, "scripts/postprocess.py",
        "--project", PROJECT,
    ])

    check_cmd = [
        sys.executable, "scripts/check_solutions.py",
        "--checker_configs", *JUDGE_MODELS,
        "--setting_config", PROJECT,
        "--n", str(N_JUDGE_VOTES),
    ]
    if SKIP_EXISTING:
        check_cmd.append("--skip-existing")
    run_step("check_solutions", check_cmd)

    run_step("results", [
        sys.executable, "scripts/results/sycophancy_results.py",
        "--setting_config", PROJECT,
    ])

    print(f"\nDone. Project={PROJECT} solver={SOLVER_MODEL} judges={JUDGE_MODELS} n={N_JUDGE_VOTES}")
    print(f"Logs: {LOG_DIR}/{PROJECT}_*_{RUN_ID}.log")


if __name__ == "__main__":
    main()
